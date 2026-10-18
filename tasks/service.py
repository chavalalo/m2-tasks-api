"""Lógica de negocio del recurso `tasks`.

Única capa que habla con `tasks/repository.py` y que decide los errores de
dominio (con `core.errors`). Valida al responsable a través de `users.service`,
nunca del repositorio de usuarios.
"""
from tasks.schemas import Task, TaskCreate, TaskStatus, TaskStatusUpdate

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
    raise NotImplementedError


def get_task(task_id: int) -> Task:
    """Tarea por `id`. 404 si no existe (CA-17)."""
    raise NotImplementedError


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
