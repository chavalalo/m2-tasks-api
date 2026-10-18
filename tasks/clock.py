"""Reloj del recurso `tasks`.

La lógica de negocio pide la fecha de "hoy" a este módulo en lugar de llamar a
`date.today()` directamente. Así los tests pueden fijar el día con `monkeypatch`
y no dependen de cuándo se ejecutan.

Dos conceptos distintos:
  - `now()`: un **instante**. Siempre en UTC; se usa para `created_at`,
    `updated_at` y el historial.
  - `today()`: un **día de calendario del negocio**. Depende de la zona horaria
    del equipo (variable de entorno `TASKS_TIMEZONE`, por defecto
    `America/Mexico_City`); se usa para validar fechas límite.
"""
import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

BUSINESS_TIMEZONE = ZoneInfo(os.environ.get("TASKS_TIMEZONE", "America/Mexico_City"))


def today() -> date:
    """Fecha de hoy en la zona horaria del negocio (no la del servidor ni UTC)."""
    return now().astimezone(BUSINESS_TIMEZONE).date()


def now() -> datetime:
    """Momento actual (UTC, con zona horaria) usado para `created_at`, `updated_at` e historial."""
    return datetime.now(timezone.utc)
