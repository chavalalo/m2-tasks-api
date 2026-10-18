# Changelog

Todos los cambios relevantes de este proyecto. Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[versionado semántico](https://semver.org/lang/es/).

## [0.2.0] - 2026-10-18

Recurso **`tasks`** (gestión de tareas de equipo). Especificación en
`docs/especificacion.md`.

### Agregado

- `POST /tasks`: crear tareas con título, descripción, prioridad (1–5), fecha
  límite y responsable.
- Encabezado `Idempotency-Key` en `POST /tasks`: un reintento con la misma llave y
  el mismo cuerpo devuelve la tarea original; con otro cuerpo responde 409.
- `GET /tasks` con filtros combinables `status`, `assignee_id` y `priority`.
- `GET /tasks/{task_id}`, con el historial de estados (`status_history`).
- `PATCH /tasks/{task_id}/status` con transiciones validadas; `done` es un estado final.
- `core.errors.conflict(message)`: error 409 con mensaje libre.
- `users.service.user_exists(user_id)` para que otros recursos validen usuarios
  sin acceder al repositorio de `users`.
- Variable de entorno `TASKS_TIMEZONE` (por defecto `America/Mexico_City`).
- Tests: integración (`tests/test_tasks.py`), unitarios con mocks
  (`tests/test_tasks_service.py`) y app (`tests/test_main.py`). Cobertura del
  100 % en líneas y ramas.
- Configuración de `mutmut` en `pyproject.toml` (126/126 mutantes muertos).
- Documentación: `docs/especificacion.md`, `docs/prompts.md`, `docs/reflexion.md`,
  `docs/evidencia/`; README con ejemplos; secciones nuevas en `CLAUDE.md`.

### Cambiado

- `core.errors.not_found` acepta `feminine=True` ("tarea no encontrada"). Es
  opcional y keyword-only: los mensajes de `users` no cambian.
- Título de la app: "API de usuarios y tareas", versión 0.2.0.
- `requirements.txt`: se agregan `tzdata` (zonas horarias en Windows) y `mutmut`.

### Corregido

- La validación de fecha límite calculaba "hoy" en UTC: desde las 18:00 en
  Ciudad de México rechazaba tareas con fecha de hoy. Ahora usa la zona horaria
  del negocio.
- `Idempotency-Key` aceptaba valores de solo espacios; ahora debe ser un token
  sin espacios de 1 a 100 caracteres.

## [0.1.0]

Versión del repo base del curso (`next-gen-coding/m2-api-base`): recurso `users`
(`GET /users`, `GET /users/{id}`, `POST /users`) y `GET /health`.
