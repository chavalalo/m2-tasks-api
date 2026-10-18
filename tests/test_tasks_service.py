"""Tests unitarios de `tasks/service.py` y `tasks/clock.py` (sin HTTP).

A diferencia de tests/test_tasks.py (integración con TestClient), aquí se llama al
servicio directamente y se reemplazan sus dependencias con mocks: el reloj y
`users.service.user_exists`. Así se verifica no solo QUÉ devuelve el servicio,
sino también CON QUIÉN habla y en qué orden.
"""
from datetime import date, datetime, timezone
from itertools import product
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from tasks import clock, repository, service
from tasks.schemas import TaskCreate, TaskStatus, TaskStatusUpdate
from users import service as users_service

UTC = timezone.utc
NOON = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


@pytest.fixture
def user_exists(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock de `users.service.user_exists`: por defecto el usuario existe."""
    mock = MagicMock(return_value=True)
    monkeypatch.setattr(users_service, "user_exists", mock)
    return mock


@pytest.fixture
def fixed_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    monkeypatch.setattr(clock, "now", lambda: NOON)
    return NOON


# --- create_task ------------------------------------------------------------------


def test_create_task_sin_responsable_no_consulta_users(user_exists: MagicMock) -> None:
    data = TaskCreate(title="Revisar logs")

    service.create_task(data)

    user_exists.assert_not_called()


def test_create_task_consulta_users_con_el_id_del_responsable(user_exists: MagicMock) -> None:
    data = TaskCreate(title="Revisar logs", assignee_id=42)

    task = service.create_task(data)

    user_exists.assert_called_once_with(42)
    assert task.assignee_id == 42


def test_create_task_responsable_inexistente_levanta_422(user_exists: MagicMock) -> None:
    user_exists.return_value = False
    data = TaskCreate(title="Revisar logs", assignee_id=42)

    with pytest.raises(HTTPException) as exc:
        service.create_task(data)

    assert exc.value.status_code == 422
    assert exc.value.detail == "El responsable no existe: 42"


def test_create_task_invalida_no_reserva_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """La validación ocurre antes de pedir un id al repositorio."""
    next_id = MagicMock(side_effect=AssertionError("no debió pedirse un id"))
    monkeypatch.setattr(repository, "next_id", next_id)
    data = TaskCreate(title="Revisar logs", due_date=date(2026, 10, 17))

    with pytest.raises(HTTPException) as exc:
        service.create_task(data)

    assert exc.value.status_code == 422
    next_id.assert_not_called()


def test_create_task_usa_un_solo_instante_para_las_fechas(fixed_now: datetime) -> None:
    task = service.create_task(TaskCreate(title="Revisar logs"))

    assert task.created_at == task.updated_at == task.status_history[0].changed_at == fixed_now


def test_create_task_reintento_no_vuelve_a_validar(user_exists: MagicMock) -> None:
    """Un reintento idempotente devuelve la original sin consultar dependencias."""
    data = TaskCreate(title="Revisar logs", assignee_id=1)
    original = service.create_task(data, idempotency_key="k1")
    user_exists.reset_mock()

    retry = service.create_task(data, idempotency_key="k1")

    assert retry == original
    user_exists.assert_not_called()


def test_create_task_misma_llave_otro_cuerpo_levanta_409() -> None:
    service.create_task(TaskCreate(title="Revisar logs"), idempotency_key="k1")

    with pytest.raises(HTTPException) as exc:
        service.create_task(TaskCreate(title="Otra cosa"), idempotency_key="k1")

    assert exc.value.status_code == 409


# --- change_status ----------------------------------------------------------------

ALL_PAIRS = list(product(TaskStatus, TaskStatus))


@pytest.mark.parametrize(
    ("current", "target"), ALL_PAIRS, ids=[f"{a.value}->{b.value}" for a, b in ALL_PAIRS]
)
def test_change_status_tabla_completa_de_transiciones(
    current: TaskStatus, target: TaskStatus
) -> None:
    """Las 9 combinaciones: mismo estado → sin cambio; permitida → cambia; resto → 409."""
    task = service.create_task(TaskCreate(title="Revisar logs"))
    if current is not TaskStatus.PENDING:
        task = service.change_status(task.id, TaskStatusUpdate(status=current))
    allowed = target in service.ALLOWED_TRANSITIONS[current]

    if target is current or allowed:
        result = service.change_status(task.id, TaskStatusUpdate(status=target))
        assert result.status is target
        expected_history = len(task.status_history) + (0 if target is current else 1)
        assert len(result.status_history) == expected_history
    else:
        with pytest.raises(HTTPException) as exc:
            service.change_status(task.id, TaskStatusUpdate(status=target))
        assert exc.value.status_code == 409


def test_change_status_no_muta_la_tarea_original() -> None:
    task = service.create_task(TaskCreate(title="Revisar logs"))

    service.change_status(task.id, TaskStatusUpdate(status=TaskStatus.DONE))

    assert task.status is TaskStatus.PENDING
    assert len(task.status_history) == 1


def test_change_status_tarea_inexistente_levanta_404() -> None:
    with pytest.raises(HTTPException) as exc:
        service.change_status(999, TaskStatusUpdate(status=TaskStatus.DONE))

    assert exc.value.status_code == 404


def test_done_es_estado_final() -> None:
    assert service.ALLOWED_TRANSITIONS[TaskStatus.DONE] == frozenset()


# --- clock ------------------------------------------------------------------------


def test_clock_now_es_utc_con_zona_horaria() -> None:
    now = clock.now()

    assert now.tzinfo is timezone.utc


def test_clock_today_se_deriva_de_now(monkeypatch: pytest.MonkeyPatch) -> None:
    """`today()` usa la fecha UTC de `now()` (no la hora local del servidor)."""
    monkeypatch.undo()  # quita el reloj fijo del conftest para probar el real
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc))

    assert clock.today() == date(2026, 12, 31)


# --- Bug: "hoy" calculado en UTC (ver docs/prompts.md, P-17 a P-19) -------------------


@pytest.mark.parametrize(
    ("utc_instant", "expected_local_day"),
    [
        pytest.param(datetime(2026, 10, 19, 1, 0, tzinfo=UTC), date(2026, 10, 18), id="19h"),
        pytest.param(datetime(2026, 10, 19, 5, 59, tzinfo=UTC), date(2026, 10, 18), id="23h59"),
        pytest.param(datetime(2026, 10, 19, 6, 0, tzinfo=UTC), date(2026, 10, 19), id="0h"),
    ],
)
def test_clock_today_usa_la_zona_horaria_del_negocio(
    monkeypatch: pytest.MonkeyPatch, utc_instant: datetime, expected_local_day: date
) -> None:
    """Regresión: a las 19:00 en CDMX (01:00 UTC del día siguiente) "hoy" sigue siendo hoy."""
    monkeypatch.undo()
    monkeypatch.setattr(clock, "now", lambda: utc_instant)

    assert clock.today() == expected_local_day


def test_crear_tarea_para_hoy_en_la_tarde_de_cdmx_es_valido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regresión del reporte: due_date = hoy, creada a las 19:00 hora de CDMX → se acepta."""
    monkeypatch.undo()
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 10, 19, 1, 0, tzinfo=timezone.utc))
    data = TaskCreate(title="Cerrar turno", due_date=date(2026, 10, 18))

    task = service.create_task(data)

    assert task.due_date == date(2026, 10, 18)
