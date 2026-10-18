"""Almacén en memoria del recurso `tasks`.

Igual que `users/repository.py`: imita la API de un repositorio real para que
`service.py` no note la diferencia cuando se cambie por una base de datos.
También guarda las llaves de idempotencia ya usadas.
"""
from typing import NamedTuple

from tasks.schemas import Task, TaskStatus


class IdempotencyRecord(NamedTuple):
    """Lo que se recuerda de una llave de idempotencia ya usada."""

    fingerprint: str  # huella del cuerpo de la petición original
    task_id: int  # tarea que creó esa petición


_tasks: dict[int, Task] = {}
_idempotency_keys: dict[str, IdempotencyRecord] = {}
_next_id: int = 1


def next_id() -> int:
    """Devuelve el siguiente `id` disponible y lo reserva."""
    global _next_id
    task_id = _next_id
    _next_id += 1
    return task_id


def add(task: Task) -> Task:
    """Guarda una tarea nueva (el servicio ya le asignó `id`)."""
    _tasks[task.id] = task
    return task


def get(task_id: int) -> Task | None:
    """Tarea por `id`, o `None` si no existe."""
    return _tasks.get(task_id)


def list_all(
    *,
    status: TaskStatus | None = None,
    assignee_id: int | None = None,
    priority: int | None = None,
) -> list[Task]:
    """Tareas que cumplen todos los filtros dados, ordenadas por `id`."""
    def matches(task: Task) -> bool:
        return (
            (status is None or task.status == status)
            and (assignee_id is None or task.assignee_id == assignee_id)
            and (priority is None or task.priority == priority)
        )

    return sorted((task for task in _tasks.values() if matches(task)), key=lambda t: t.id)


def save(task: Task) -> Task:
    """Reemplaza una tarea existente (cambios de estado)."""
    _tasks[task.id] = task
    return task


def find_by_idempotency_key(key: str) -> IdempotencyRecord | None:
    """Registro asociado a la llave, o `None` si no se ha usado."""
    return _idempotency_keys.get(key)


def remember_idempotency_key(key: str, fingerprint: str, task_id: int) -> None:
    """Asocia la llave con la huella del cuerpo y la tarea creada."""
    _idempotency_keys[key] = IdempotencyRecord(fingerprint, task_id)


def reset() -> None:
    """Vacía el almacén y las llaves de idempotencia. Se usa entre tests."""
    global _next_id
    _tasks.clear()
    _idempotency_keys.clear()
    _next_id = 1
