"""Rutas HTTP del recurso `tasks`.

Sigue el patrón de `users/routes.py`: `response_model=` siempre y delegación total
en `service.py`.
"""
from fastapi import APIRouter, Header, Query, status

from tasks import service
from tasks.schemas import Task, TaskCreate, TaskStatus, TaskStatusUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    assignee_id: int | None = Query(default=None),
    priority: int | None = Query(default=None, ge=1, le=5),
) -> list[Task]:
    return service.list_tasks(status=status_filter, assignee_id=assignee_id, priority=priority)


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    return service.get_task(task_id)


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    idempotency_key: str | None = Header(default=None, min_length=1, max_length=100),
) -> Task:
    return service.create_task(data, idempotency_key)


@router.patch("/{task_id}/status", response_model=Task)
def change_task_status(task_id: int, data: TaskStatusUpdate) -> Task:
    return service.change_status(task_id, data)
