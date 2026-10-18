"""Lógica de negocio del recurso `users`.

Las rutas no acceden al repositorio directamente: pasan por aquí. Esta capa es la
única que conoce `repository.py` y la que decide cuándo algo es un error de
dominio (usando `core.errors`).
"""
from core import errors
from users import repository
from users.schemas import User, UserCreate


def get_user(user_id: int) -> User:
    user = repository.get(user_id)
    if user is None:
        raise errors.not_found("usuario", user_id)
    return user


def user_exists(user_id: int) -> bool:
    """Indica si existe un usuario con ese `id`. Lo usan otros recursos (p. ej. `tasks`)."""
    return repository.get(user_id) is not None


def list_users() -> list[User]:
    return repository.list_all()


def create_user(data: UserCreate) -> User:
    if repository.find_by_email(str(data.email)) is not None:
        raise errors.already_exists("usuario", data.email)
    return repository.add(name=data.name, email=str(data.email))
