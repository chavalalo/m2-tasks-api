"""Schemas Pydantic del recurso `tasks`.

Contrato de entrada y salida de la API (ver `docs/especificacion.md`). Las
validaciones de **forma** (longitudes, rangos, tipos) viven aquí; las de **dominio**
(fecha en el pasado, responsable inexistente, transiciones) viven en `service.py`.
"""
from datetime import date, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, StrictInt, StringConstraints

# Título: se recortan espacios ANTES de medir, así "   " queda vacío y falla (CA-03).
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=120)]

# Prioridad 1 (baja) a 5 (crítica). StrictInt rechaza `true` o `2.0` en vez de convertirlos
# (CA-04).
Priority = Annotated[StrictInt, Field(ge=1, le=5)]


class TaskStatus(str, Enum):
    """Estados posibles de una tarea."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Cuerpo de entrada para crear una tarea (CA-01…CA-07)."""

    title: Title
    description: str | None = Field(default=None, max_length=1000)
    priority: Priority = 3
    due_date: date | None = None
    assignee_id: int | None = None


class TaskStatusUpdate(BaseModel):
    """Cuerpo de entrada para cambiar el estado de una tarea (CA-18…CA-21)."""

    status: TaskStatus


class StatusChange(BaseModel):
    """Una entrada del historial de estados (trazabilidad)."""

    status: TaskStatus
    changed_at: datetime


class Task(BaseModel):
    """Tarea tal como la devuelve la API."""

    id: int
    title: str
    description: str | None
    priority: int
    due_date: date | None
    assignee_id: int | None
    status: TaskStatus
    status_history: list[StatusChange]
    created_at: datetime
    updated_at: datetime
