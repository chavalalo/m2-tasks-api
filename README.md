# API de usuarios y tareas de equipo

API REST con FastAPI y Pydantic v2 para la **gestión de tareas de equipo**: registrar
tareas con prioridad, responsable y fecha límite, y rastrear sus cambios de estado.
El objetivo es que ningún trabajo operativo quede sin registrar.

Parte del repo base del curso
[`next-gen-coding/m2-api-base`](https://github.com/next-gen-coding/m2-api-base)
(recurso `users`) y le agrega el recurso **`tasks`**, desarrollado con IA para el
**Reto del Módulo 2**.

| Calidad | Resultado |
|---------|-----------|
| Tests | **99 passed** (unitarios + integración) |
| Cobertura (líneas y ramas) | **100 %** |
| Mutation testing (`mutmut`, `tasks/`) | **126/126 mutantes muertos** |
| Linter (`ruff check .`) | sin errores |

## Requisitos

- Python **3.10 o superior**
- (Recomendado) Claude Code, para trabajar con las convenciones de `CLAUDE.md`

## Instalación

```bash
git clone https://github.com/chavalalo/m2-tasks-api.git
cd m2-tasks-api
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
uvicorn main:app --reload          # http://127.0.0.1:8000  ·  Swagger en /docs
```

### Endpoints

| Método | Ruta | Descripción | Respuestas |
|--------|------|-------------|------------|
| GET | `/health` | Estado del servicio | 200 |
| GET | `/users` · `/users/{id}` | Usuarios (repo base) | 200 · 404 |
| POST | `/users` | Crea un usuario (repo base) | 201 · 409 · 422 |
| **POST** | **`/tasks`** | Crea una tarea (admite `Idempotency-Key`) | 201 · 409 · 422 |
| **GET** | **`/tasks`** | Lista tareas; filtros `status`, `assignee_id`, `priority` | 200 · 422 |
| **GET** | **`/tasks/{id}`** | Una tarea con su historial | 200 · 404 |
| **PATCH** | **`/tasks/{id}/status`** | Cambia el estado | 200 · 404 · 409 · 422 |

### Ejemplos

Crear una tarea asignada a un usuario, de forma idempotente:

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"title": "Rotar credenciales del VPN", "priority": 5,
       "due_date": "2026-10-31", "assignee_id": 2}'
```

```json
{
  "id": 1,
  "title": "Rotar credenciales del VPN",
  "description": null,
  "priority": 5,
  "due_date": "2026-10-31",
  "assignee_id": 2,
  "status": "pending",
  "status_history": [{"status": "pending", "changed_at": "2026-10-18T16:00:00Z"}],
  "created_at": "2026-10-18T16:00:00Z",
  "updated_at": "2026-10-18T16:00:00Z"
}
```

Si el cliente pierde la respuesta y **reintenta con la misma llave**, recibe la
misma tarea (`id: 1`) en lugar de crear una duplicada.

Cambiar el estado y filtrar:

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1/status \
  -H "Content-Type: application/json" -d '{"status": "in_progress"}'

curl "http://127.0.0.1:8000/tasks?status=in_progress&assignee_id=2"
```

Errores (siempre con `detail` en español):

```text
POST /tasks con due_date de ayer          → 422 {"detail": "La fecha límite no puede estar en el pasado"}
PATCH de una tarea "done" a "pending"     → 409 {"detail": "Transición de estado no permitida: done → pending"}
```

### Reglas de negocio

- **Título:** 3 a 120 caracteres; se recortan los espacios alrededor.
- **Prioridad:** entero de 1 (baja) a 5 (crítica); por defecto 3.
- **Fecha límite:** opcional; **hoy** se permite, antes de hoy no. "Hoy" se calcula
  en la zona horaria del negocio (ver Configuración).
- **Responsable:** opcional; debe ser un usuario existente.
- **Estados:** `pending → in_progress | done`, `in_progress → pending | done`.
  `done` es final.
- **Idempotencia:** `Idempotency-Key` es un token sin espacios (1 a 100 caracteres).
  Misma llave y mismo cuerpo → la tarea original; misma llave y otro cuerpo → 409.
  Una petición rechazada no reserva la llave.

La especificación completa, con 23 criterios de aceptación (CA-01…CA-22 y CA-11b),
está en [`docs/especificacion.md`](docs/especificacion.md).

### Configuración

| Variable | Por defecto | Para qué |
|----------|-------------|----------|
| `TASKS_TIMEZONE` | `America/Mexico_City` | Zona horaria del equipo para decidir qué es "hoy" en la validación de fechas límite. Las marcas de tiempo (`created_at`, historial) siempre se guardan en UTC. |

## Tests y calidad

```bash
pytest                                                    # toda la suite
pytest --cov=tasks --cov-branch --cov-report=term-missing # cobertura de líneas y ramas
ruff check .                                              # linter
mutmut run && mutmut results                              # mutation testing de tasks/
```

| Archivo | Tipo | Qué prueba |
|---------|------|------------|
| `tests/test_tasks.py` | Integración (`TestClient`) | Cada criterio CA-xx por HTTP |
| `tests/test_tasks_service.py` | Unitario (mocks) | Reglas del servicio, transiciones y reloj |
| `tests/test_users.py` | Integración | Recurso base `users` (sin cambios) |
| `tests/test_main.py` | Integración | `/health` y rutas publicadas en OpenAPI |

El día de "hoy" está **fijo en 2026-10-18** para toda la suite (`tests/conftest.py`):
ningún test depende del día en que se ejecuta.

## Estructura

```
├── main.py               # app FastAPI y routers
├── core/errors.py        # catálogo de errores (404, 409, 422)
├── users/                # recurso base del curso
├── tasks/                # recurso nuevo
│   ├── routes.py         #   rutas HTTP (sin lógica)
│   ├── service.py        #   reglas de negocio, idempotencia y transiciones
│   ├── repository.py     #   almacén en memoria + llaves de idempotencia
│   ├── schemas.py        #   modelos Pydantic (validaciones de forma)
│   └── clock.py          #   reloj inyectable (hoy / ahora)
├── tests/
├── docs/
│   ├── especificacion.md # historia de usuario y criterios de aceptación
│   ├── prompts.md        # todos los prompts usados, con resultado y decisión
│   ├── reflexion.md      # aprendizajes del proceso
│   └── evidencia/        # logs de rojo/verde, cobertura y mutmut
├── CLAUDE.md             # convenciones para trabajar con IA en este repo
└── CHANGELOG.md
```

## Para quien llega al proyecto

1. Lee `CLAUDE.md` (convenciones) y `docs/especificacion.md` (qué debe hacer `tasks`).
2. Corre `pytest`: todo debe estar en verde antes de tocar nada.
3. Un endpoint nuevo sigue el camino `schemas → service → routes`, con sus errores
   desde `core/errors.py` y sus tests en el archivo del recurso.

## Limitaciones conocidas

- **Almacén en memoria:** los datos se pierden al reiniciar (herencia del repo base).
- **Llaves de idempotencia sin caducidad:** se guardan para siempre en memoria. Con
  una base de datos real deberían expirar (p. ej. a las 24 h).
- **Sin autenticación ni paginación:** fuera del alcance de este sprint.
- `migrations/` y `legacy/` son del repo base y no se modificaron.
