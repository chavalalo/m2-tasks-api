"""Almacén en memoria del recurso `tasks`.

Igual que `users/repository.py`: imita la API de un repositorio real para que
`service.py` no note la diferencia cuando se cambie por una base de datos.
También guarda las llaves de idempotencia ya usadas.
"""
from tasks.schemas import Task, TaskStatus

_tasks: dict[int, Task] = {}
_idempotency_keys: dict[str, tuple[str, int]] = {}
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
    tasks = sorted(_tasks.values(), key=lambda task: task.id)
    if status is not None:
        tasks = [task for task in tasks if task.status == status]
    if assignee_id is not None:
        tasks = [task for task in tasks if task.assignee_id == assignee_id]
    if priority is not None:
        tasks = [task for task in tasks if task.priority == priority]
    return tasks


def save(task: Task) -> Task:
    """Reemplaza una tarea existente (cambios de estado)."""
    _tasks[task.id] = task
    return task


def find_by_idempotency_key(key: str) -> tuple[str, int] | None:
    """`(huella_del_cuerpo, task_id)` asociada a la llave, o `None` si no se ha usado."""
    return _idempotency_keys.get(key)


def remember_idempotency_key(key: str, fingerprint: str, task_id: int) -> None:
    """Asocia la llave con la huella del cuerpo y la tarea creada."""
    _idempotency_keys[key] = (fingerprint, task_id)


def reset() -> None:
    """Vacía el almacén y las llaves de idempotencia. Se usa entre tests."""
    global _next_id
    _tasks.clear()
    _idempotency_keys.clear()
    _next_id = 1
