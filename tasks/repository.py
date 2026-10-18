"""Almacén en memoria del recurso `tasks`.

Igual que `users/repository.py`: imita la API de un repositorio real para que
`service.py` no note la diferencia cuando se cambie por una base de datos.
También guarda las llaves de idempotencia ya usadas.
"""
from tasks.schemas import Task, TaskStatus


def add(task: Task) -> Task:
    """Guarda una tarea nueva (el servicio ya le asignó `id`)."""
    raise NotImplementedError


def next_id() -> int:
    """Devuelve el siguiente `id` disponible y lo reserva."""
    raise NotImplementedError


def get(task_id: int) -> Task | None:
    """Tarea por `id`, o `None` si no existe."""
    raise NotImplementedError


def list_all(
    *,
    status: TaskStatus | None = None,
    assignee_id: int | None = None,
    priority: int | None = None,
) -> list[Task]:
    """Tareas que cumplen todos los filtros dados, ordenadas por `id`."""
    raise NotImplementedError


def save(task: Task) -> Task:
    """Reemplaza una tarea existente (cambios de estado)."""
    raise NotImplementedError


def find_by_idempotency_key(key: str) -> tuple[str, int] | None:
    """`(huella_del_cuerpo, task_id)` asociada a la llave, o `None` si no se ha usado."""
    raise NotImplementedError


def remember_idempotency_key(key: str, fingerprint: str, task_id: int) -> None:
    """Asocia la llave con la huella del cuerpo y la tarea creada."""
    raise NotImplementedError


def reset() -> None:
    """Vacía el almacén y las llaves de idempotencia. Se usa entre tests."""
    raise NotImplementedError
