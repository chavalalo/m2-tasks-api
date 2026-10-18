"""Reloj del recurso `tasks`.

La lógica de negocio pide la fecha de "hoy" a este módulo en lugar de llamar a
`date.today()` directamente. Así los tests pueden fijar el día con `monkeypatch`
y no dependen de cuándo se ejecutan.
"""
from datetime import date, datetime


def today() -> date:
    """Fecha actual (UTC) usada para validar fechas límite."""
    raise NotImplementedError


def now() -> datetime:
    """Momento actual (UTC, con zona horaria) usado para `created_at`, `updated_at` e historial."""
    raise NotImplementedError

