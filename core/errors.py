"""Catálogo de errores de la API.

Todas las rutas deben levantar errores a través de estas funciones, para que los
códigos de estado y el formato de la respuesta sean consistentes en todo el
proyecto. No usar `HTTPException` directamente en las rutas.
"""
from fastapi import HTTPException, status


def not_found(resource: str, identifier: object, *, feminine: bool = False) -> HTTPException:
    """404 — el recurso pedido no existe.

    `feminine=True` concuerda el mensaje con recursos femeninos ("tarea no encontrada").
    """
    found = "encontrada" if feminine else "encontrado"
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} no {found}: {identifier}",
    )


def invalid_request(message: str) -> HTTPException:
    """422 — la petición llegó bien formada pero no es válida a nivel de dominio."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=message,
    )


def already_exists(resource: str, identifier: object) -> HTTPException:
    """409 — el recurso que se quiere crear ya existe."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{resource} ya existe: {identifier}",
    )


def conflict(message: str) -> HTTPException:
    """409 — la petición choca con el estado actual del recurso.

    Para conflictos que no son "ya existe": reutilizar una llave de idempotencia
    con otro cuerpo, o una transición de estado no permitida.
    """
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message,
    )
