# API de usuarios y tareas — guía del proyecto

API REST de ejemplo (FastAPI + Pydantic v2). Almacén en memoria, sin base de datos:
el proyecto corre sin infraestructura.

## Estructura

- `main.py` — crea la app y monta los routers.
- `users/` — recurso de ejemplo. Cada recurso sigue el mismo patrón:
  - `routes.py` — rutas HTTP. Sin lógica de negocio: delega en `service.py`.
  - `service.py` — lógica de negocio. Única capa que habla con `repository.py`.
  - `schemas.py` — modelos Pydantic de entrada (`*Create`) y salida.
  - `repository.py` — acceso a datos (aquí, un `dict` en memoria).
- `tasks/` — recurso de tareas de equipo (mismo patrón que `users/`). Especificación y
  criterios de aceptación en `docs/especificacion.md`: **léela antes de tocar `tasks/`**.
  - `tasks/clock.py` — reloj inyectable (`today()`); los tests lo reemplazan.
- `core/errors.py` — catálogo de errores. Toda respuesta de error sale de aquí.
- `tests/` — un archivo por recurso: `test_<recurso>.py`.

## Convenciones

- Las rutas declaran `response_model=` y devuelven modelos Pydantic, nunca `dict` crudos.
- Los errores se levantan con las funciones de `core/errors.py`
  (`not_found`, `invalid_request`, `already_exists`), no con `HTTPException` a mano.
- La ruta delega en `service.py`; la lógica y las decisiones de error viven ahí.
- Identificadores en inglés y `snake_case`, sin abreviaturas. Mensajes de error en español.
- Cada endpoint nuevo lleva su test en el archivo del recurso, con al menos un caso
  feliz y un caso de error.
- Rutas específicas antes que rutas con parámetro: `/users/search` debe declararse
  **antes** de `/users/{user_id}`.

## Reglas del recurso `tasks`

- `tasks/service.py` **solo** usa `users/service.py` (nunca `users/repository.py`) para
  validar el responsable: cada recurso es dueño de su almacén.
- La fecha de "hoy" sale de `tasks/clock.py`, nunca de `date.today()` directo.
- Idempotencia: la llave (`Idempotency-Key`) se guarda **solo** si la tarea se creó;
  una petición que falla no reserva la llave (CA-11).
- Cada criterio `CA-xx` de la especificación debe tener al menos un test que lo
  mencione en su nombre o docstring.

## Tests

- Estructura arrange / act / assert separada por líneas en blanco (ver `tests/test_users.py`).
- Nombres de test en español y descriptivos: `test_<qué>_<condición>_<resultado>`.
- Unitarios del servicio en `tests/test_tasks_service.py` (sin HTTP; reloj con `monkeypatch`).
  Integración HTTP con `TestClient` en `tests/test_tasks.py`.
- Usa `pytest.mark.parametrize` para familias de casos inválidos (títulos, prioridades).
- No uses la fecha real en los tests: fija el reloj.

## Cómo ejecutar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload          # API en http://127.0.0.1:8000  ·  /docs para el Swagger
pytest                             # tests
pytest --cov=. --cov-report=term-missing   # cobertura
pytest --cov=tasks --cov-branch --cov-report=term-missing --cov-fail-under=90  # meta del reto
ruff check .                       # linter
mutmut run                         # mutation testing de tasks/ (config en pyproject.toml)
```

## Fuera de límites

- `migrations/` y `legacy/` — no modificar.
- No cambies el comportamiento de los endpoints de `users` (sus tests deben seguir verdes).

## Documentación

- Docstring en español en cada función pública de `tasks/` (qué hace, errores que levanta).
- Cambios relevantes en `CHANGELOG.md` (formato Keep a Changelog).
- Prompts usados durante el desarrollo: `docs/prompts.md`.
