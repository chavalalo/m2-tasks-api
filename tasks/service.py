"""Lógica de negocio del recurso `tasks`.

Única capa que habla con `tasks/repository.py` y que decide los errores de
dominio (con `core.errors`). Valida al responsable a través de `users.service`,
nunca del repositorio de usuarios.
"""
import hashlib

from core import errors
from tasks import clock, repository
from tasks.schemas import StatusChange, Task, TaskCreate, TaskStatus, TaskStatusUpdate
from users import service as users_service

# Transiciones permitidas: estado actual -> estados a los que puede pasar.
ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.IN_PROGRESS, TaskStatus.DONE}),
    TaskStatus.IN_PROGRESS: frozenset({TaskStatus.PENDING, TaskStatus.DONE}),
    TaskStatus.DONE: frozenset(),
}


def create_task(data: TaskCreate, idempotency_key: str | None = None) -> Task:
    """Crea una tarea en estado `pending`.

    Errores:
      - 422 si `due_date` es anterior a hoy (CA-05) o si el responsable no existe (CA-07).
        (Título y prioridad inválidos los rechaza el schema antes de llegar aquí.)
      - 409 si `idempotency_key` ya se usó con otro cuerpo (CA-09).
    Si la llave ya se usó con el mismo cuerpo, devuelve la tarea original (CA-08).
    """
    fingerprint = _fingerprint(data)
    if idempotency_key is not None:
        previous = repository.find_by_idempotency_key(idempotency_key)
        if previous is not None:
            return _replay(idempotency_key, previous, fingerprint)

    _validate_new_task(data)
    created_at = clock.now()
    task = Task(
        id=repository.next_id(),
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        assignee_id=data.assignee_id,
        status=TaskStatus.PENDING,
        status_history=[StatusChange(status=TaskStatus.PENDING, changed_at=created_at)],
        created_at=created_at,
        updated_at=created_at,
    )
    repository.add(task)
    if idempotency_key is not None:
        # Solo se recuerda la llave cuando la tarea se creó (CA-11).
        repository.remember_idempotency_key(idempotency_key, fingerprint, task.id)
    return task


def _fingerprint(data: TaskCreate) -> str:
    """Huella del cuerpo ya normalizado (título recortado, defaults aplicados)."""
    return hashlib.sha256(data.model_dump_json().encode()).hexdigest()


def _replay(key: str, previous: tuple[str, int], fingerprint: str) -> Task:
    """Respuesta a un reintento: la tarea original, o 409 si el cuerpo cambió (CA-08/CA-09)."""
    previous_fingerprint, task_id = previous
    if previous_fingerprint != fingerprint:
        raise errors.conflict(f"La llave de idempotencia ya se usó con otro contenido: {key}")
    return get_task(task_id)


def _validate_new_task(data: TaskCreate) -> None:
    """Reglas de dominio de una tarea nueva. Se validan ANTES de reservar un `id`."""
    if data.due_date is not None and data.due_date < clock.today():
        raise errors.invalid_request("La fecha límite no puede estar en el pasado")
    if data.assignee_id is not None and not users_service.user_exists(data.assignee_id):
        raise errors.invalid_request(f"El responsable no existe: {data.assignee_id}")


def get_task(task_id: int) -> Task:
    """Tarea por `id`. 404 si no existe (CA-17)."""
    task = repository.get(task_id)
    if task is None:
        raise errors.not_found("tarea", task_id)
    return task


def list_tasks(
    *,
    status: TaskStatus | None = None,
    assignee_id: int | None = None,
    priority: int | None = None,
) -> list[Task]:
    """Tareas que cumplen los filtros, ordenadas por `id` (CA-12…CA-14)."""
    raise NotImplementedError


def change_status(task_id: int, data: TaskStatusUpdate) -> Task:
    """Cambia el estado de una tarea y lo registra en su historial.

    - Mismo estado: devuelve la tarea sin cambios (CA-19).
    - Transición no permitida: 409 (CA-20).
    - Tarea inexistente: 404 (CA-22).
    """
    raise NotImplementedError
