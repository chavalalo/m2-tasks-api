"""Rutas HTTP del recurso `tasks`.

Sigue el patrón de `users/routes.py`: `response_model=` siempre y delegación total
en `service.py`. Los docstrings de cada ruta aparecen como descripción en `/docs`.
"""
from fastapi import APIRouter, Header, Query, status

from tasks import service
from tasks.schemas import Task, TaskCreate, TaskStatus, TaskStatusUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

_ERROR = {"description": "Error con `detail` en español", "content": {"application/json": {}}}


@router.get("", response_model=list[Task])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    assignee_id: int | None = Query(default=None),
    priority: int | None = Query(default=None, ge=1, le=5),
) -> list[Task]:
    """Lista las tareas ordenadas por `id`.

    Filtros opcionales y combinables: `status`, `assignee_id`, `priority` (1–5).
    Ejemplo: `GET /tasks?status=pending&assignee_id=2`.
    """
    return service.list_tasks(status=status_filter, assignee_id=assignee_id, priority=priority)


@router.get("/{task_id}", response_model=Task, responses={404: _ERROR})
def get_task(task_id: int) -> Task:
    """Devuelve una tarea por su `id`, incluido su historial de estados."""
    return service.get_task(task_id)


@router.post(
    "",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses={409: _ERROR, 422: _ERROR},
)
def create_task(
    data: TaskCreate,
    # Token opaco sin espacios (p. ej. un UUID) generado por el cliente.
    idempotency_key: str | None = Header(default=None, max_length=100, pattern=r"^\S+$"),
) -> Task:
    """Crea una tarea en estado `pending`.

    - **422**: fecha límite en el pasado, responsable inexistente o datos inválidos.
    - **Idempotency-Key** (opcional): reintentar con la misma llave y el mismo cuerpo
      devuelve la misma tarea sin duplicarla; con otro cuerpo responde **409**.
    """
    return service.create_task(data, idempotency_key)


@router.patch("/{task_id}/status", response_model=Task, responses={404: _ERROR, 409: _ERROR})
def change_task_status(task_id: int, data: TaskStatusUpdate) -> Task:
    """Cambia el estado de una tarea y lo agrega a su historial.

    Transiciones: `pending → in_progress | done`, `in_progress → pending | done`.
    `done` es final (**409**). Pedir el estado actual responde 200 sin cambios.
    """
    return service.change_status(task_id, data)
