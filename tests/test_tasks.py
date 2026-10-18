"""Tests de integración HTTP del recurso `tasks` (ver docs/especificacion.md).

Mismo estilo que tests/test_users.py: un caso por test, arrange / act / assert
separados por una línea en blanco. Cada test menciona el criterio CA-xx que cubre.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from tasks import clock


def _create(client: TestClient, **overrides: object) -> dict:
    """Crea una tarea válida (con los campos que se sobrescriban) y devuelve el cuerpo."""
    payload = {"title": "Revisar respaldos nocturnos", **overrides}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- POST /tasks · camino feliz -------------------------------------------------


def test_create_task_solo_titulo_aplica_defaults(client: TestClient) -> None:
    """CA-01."""
    payload = {"title": "Revisar respaldos nocturnos"}

    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "pending"
    assert body["priority"] == 3
    assert body["description"] is None
    assert body["due_date"] is None
    assert body["assignee_id"] is None
    assert [h["status"] for h in body["status_history"]] == ["pending"]
    assert body["created_at"] == body["updated_at"]


def test_create_task_con_todos_los_campos(client: TestClient) -> None:
    """CA-02: el responsable es un usuario semilla (integración con `users`)."""
    payload = {
        "title": "Rotar credenciales del VPN",
        "description": "Antes del cierre de mes",
        "priority": 5,
        "due_date": "2026-10-31",
        "assignee_id": 2,
    }

    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert {k: body[k] for k in payload} == payload


def test_create_task_recorta_espacios_del_titulo(client: TestClient) -> None:
    """CA-03 (normalización): el título se guarda sin espacios alrededor."""
    response = client.post("/tasks", json={"title": "   Revisar logs   "})

    assert response.status_code == 201
    assert response.json()["title"] == "Revisar logs"


def test_create_task_ids_consecutivos(client: TestClient) -> None:
    """CA-01: el servidor asigna ids consecutivos."""
    first = _create(client)

    second = _create(client)

    assert second["id"] == first["id"] + 1


# --- GET /tasks/{task_id} ------------------------------------------------------


def test_get_task_existente_devuelve_200(client: TestClient) -> None:
    """CA-16."""
    created = _create(client, title="Actualizar inventario de equipos")

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_task_inexistente_devuelve_404(client: TestClient) -> None:
    """CA-17."""
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "tarea no encontrado: 999"


# --- POST /tasks · validaciones --------------------------------------------------


@pytest.mark.parametrize(
    "title",
    [
        pytest.param("", id="vacio"),
        pytest.param("    ", id="solo-espacios"),
        pytest.param("ab", id="menos-de-3"),
        pytest.param("  ab  ", id="menos-de-3-tras-recortar"),
        pytest.param("x" * 121, id="mas-de-120"),
        pytest.param(123, id="no-es-texto"),
        pytest.param(None, id="nulo"),
    ],
)
def test_create_task_titulo_invalido_devuelve_422(client: TestClient, title: object) -> None:
    """CA-03."""
    response = client.post("/tasks", json={"title": title})

    assert response.status_code == 422


def test_create_task_sin_titulo_devuelve_422(client: TestClient) -> None:
    """CA-03: el título es obligatorio."""
    response = client.post("/tasks", json={"priority": 2})

    assert response.status_code == 422


@pytest.mark.parametrize("title", ["abc", "x" * 120], ids=["3-caracteres", "120-caracteres"])
def test_create_task_titulo_en_las_fronteras_es_valido(client: TestClient, title: str) -> None:
    """CA-03: 3 y 120 caracteres son los límites incluidos."""
    response = client.post("/tasks", json={"title": title})

    assert response.status_code == 201


@pytest.mark.parametrize(
    "priority",
    [
        pytest.param(0, id="cero"),
        pytest.param(6, id="seis"),
        pytest.param(-1, id="negativa"),
        pytest.param(2.5, id="decimal"),
        pytest.param(True, id="booleano"),
        pytest.param("3", id="texto"),
    ],
)
def test_create_task_prioridad_invalida_devuelve_422(
    client: TestClient, priority: object
) -> None:
    """CA-04."""
    response = client.post("/tasks", json={"title": "Revisar logs", "priority": priority})

    assert response.status_code == 422


@pytest.mark.parametrize("priority", [1, 5])
def test_create_task_prioridad_en_las_fronteras_es_valida(
    client: TestClient, priority: int
) -> None:
    """CA-04: 1 y 5 son los límites incluidos."""
    body = _create(client, priority=priority)

    assert body["priority"] == priority


def test_create_task_fecha_pasada_devuelve_422(client: TestClient) -> None:
    """CA-05: el reloj está fijo en 2026-10-18 (conftest); ayer es pasado."""
    payload = {"title": "Revisar logs", "due_date": "2026-10-17"}

    response = client.post("/tasks", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "La fecha límite no puede estar en el pasado"


def test_create_task_fecha_de_hoy_es_valida(client: TestClient) -> None:
    """CA-06: hoy es la frontera permitida."""
    body = _create(client, due_date="2026-10-18")

    assert body["due_date"] == "2026-10-18"


def test_create_task_fecha_con_formato_invalido_devuelve_422(client: TestClient) -> None:
    """CA-05 (forma): una fecha que no es ISO la rechaza el schema."""
    response = client.post("/tasks", json={"title": "Revisar logs", "due_date": "18/10/2026"})

    assert response.status_code == 422


def test_create_task_responsable_inexistente_devuelve_422(client: TestClient) -> None:
    """CA-07: integración con `users`."""
    payload = {"title": "Revisar logs", "assignee_id": 999}

    response = client.post("/tasks", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "El responsable no existe: 999"


def test_create_task_invalida_no_crea_nada(client: TestClient) -> None:
    """CA-05/CA-07: una petición rechazada no deja tareas ni consume ids."""
    client.post("/tasks", json={"title": "Revisar logs", "due_date": "2000-01-01"})
    client.post("/tasks", json={"title": "Revisar logs", "assignee_id": 999})

    created = _create(client)

    assert created["id"] == 1


# --- POST /tasks · idempotencia ---------------------------------------------------


def _post(client: TestClient, payload: dict, key: str | None = None):
    headers = {"Idempotency-Key": key} if key is not None else {}
    return client.post("/tasks", json=payload, headers=headers)


def test_reintento_con_misma_llave_y_mismo_cuerpo_devuelve_la_misma_tarea(
    client: TestClient,
) -> None:
    """CA-08: el reintento no duplica la tarea."""
    payload = {"title": "Revisar respaldos nocturnos", "priority": 4}
    first = _post(client, payload, key="req-001")

    retry = _post(client, payload, key="req-001")

    assert retry.status_code == 201
    assert retry.json() == first.json()
    assert client.get("/tasks/2").status_code == 404


def test_misma_llave_con_otro_cuerpo_devuelve_409(client: TestClient) -> None:
    """CA-09."""
    _post(client, {"title": "Revisar respaldos nocturnos"}, key="req-001")

    response = _post(client, {"title": "Otra tarea distinta"}, key="req-001")

    assert response.status_code == 409
    assert "req-001" in response.json()["detail"]
    assert "idempotencia" in response.json()["detail"]


def test_sin_llave_dos_peticiones_iguales_crean_dos_tareas(client: TestClient) -> None:
    """CA-10: la idempotencia es opcional y explícita."""
    payload = {"title": "Revisar respaldos nocturnos"}

    first = _post(client, payload)
    second = _post(client, payload)

    assert first.json()["id"] != second.json()["id"]


def test_llaves_distintas_con_el_mismo_cuerpo_crean_dos_tareas(client: TestClient) -> None:
    """CA-08 (contraejemplo): la llave, no el contenido, identifica el reintento."""
    payload = {"title": "Revisar respaldos nocturnos"}

    first = _post(client, payload, key="req-001")
    second = _post(client, payload, key="req-002")

    assert first.json()["id"] != second.json()["id"]


def test_peticion_fallida_no_reserva_la_llave(client: TestClient) -> None:
    """CA-11: el reintento corregido con la misma llave sí crea la tarea."""
    _post(client, {"title": "Revisar logs", "due_date": "2000-01-01"}, key="req-001")

    response = _post(client, {"title": "Revisar logs", "due_date": "2026-12-01"}, key="req-001")

    assert response.status_code == 201
    assert response.json()["id"] == 1


def test_reintento_equivalente_tras_normalizar_el_titulo_no_duplica(
    client: TestClient,
) -> None:
    """CA-08: "  X  " y "X" son el mismo cuerpo una vez recortado el título."""
    first = _post(client, {"title": "Revisar logs"}, key="req-001")

    retry = _post(client, {"title": "  Revisar logs  "}, key="req-001")

    assert retry.status_code == 201
    assert retry.json()["id"] == first.json()["id"]


def test_llave_de_idempotencia_vacia_devuelve_422(client: TestClient) -> None:
    """CA-08 (forma): una llave vacía no es una llave."""
    response = _post(client, {"title": "Revisar logs"}, key="")

    assert response.status_code == 422


def test_reintento_al_dia_siguiente_devuelve_la_original_aunque_la_fecha_ya_paso(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CA-08: la llave se revisa ANTES de validar; un reintento no se re-evalúa."""
    payload = {"title": "Revisar logs", "due_date": "2026-10-18"}
    first = _post(client, payload, key="req-001")
    monkeypatch.setattr(clock, "today", lambda: date(2026, 10, 19))

    retry = _post(client, payload, key="req-001")

    assert retry.status_code == 201
    assert retry.json()["id"] == first.json()["id"]
