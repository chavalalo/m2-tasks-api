# Especificación — Recurso `tasks` (Gestión de Tareas de Equipo)

## Historia de usuario

> **Como** integrante del equipo de operaciones,
> **quiero** registrar las tareas que hago o asigno, con prioridad, fecha límite
> y responsable, y actualizar su estado,
> **para que** ningún trabajo quede sin registrar y se pueda rastrear quién hizo qué
> y cuándo.

**Producto:** App interna de Gestión de Tareas de Equipo (API REST).
**Objetivo del sprint:** reducir las pérdidas de trabajo no registrado y mejorar
la trazabilidad de las tareas operativas.
**Stakeholders:** Product Owner, Líder Técnico, Equipo de Desarrollo, Soporte Operativo.

## Alcance

| Incluido | Fuera de alcance |
|----------|------------------|
| `POST /tasks` con validaciones e idempotencia | Autenticación / permisos |
| `GET /tasks` con filtros por estado, responsable y prioridad | Paginación |
| `GET /tasks/{task_id}` | Borrado de tareas (la trazabilidad pide no perder registros) |
| `PATCH /tasks/{task_id}/status` con transiciones válidas e historial | Edición de título, prioridad o fecha |
| Integración con `users`: el responsable debe ser un usuario existente | Persistencia en base de datos (el repo usa almacén en memoria) |

## Modelo de datos

| Campo | Tipo | Regla |
|-------|------|-------|
| `id` | `int` | Asignado por el servidor, consecutivo desde 1 |
| `title` | `str` | Obligatorio; se recortan espacios; 3–120 caracteres después del recorte |
| `description` | `str \| null` | Opcional; máximo 1000 caracteres |
| `priority` | `int` | 1 (baja) a 5 (crítica); por defecto **3** |
| `due_date` | `date \| null` | Opcional; si viene, **no puede ser anterior a hoy** (hoy sí se permite) |
| `assignee_id` | `int \| null` | Opcional; si viene, debe existir en `users` |
| `status` | `"pending" \| "in_progress" \| "done"` | Nace en `pending` |
| `status_history` | lista de `{status, changed_at}` | Se agrega una entrada al crear y en cada cambio de estado |
| `created_at`, `updated_at` | `datetime` (UTC) | Asignados por el servidor |

## Criterios de aceptación

Formato: **Dado** (contexto) · **Cuando** (petición) · **Entonces** (respuesta).

### POST /tasks — crear tarea

| # | Dado / Cuando | Entonces |
|---|---------------|----------|
| CA-01 | Un cuerpo válido con solo `title` | **201**; `status="pending"`, `priority=3`, `id` nuevo, `status_history` con 1 entrada `pending` |
| CA-02 | Un cuerpo válido con todos los campos y `assignee_id` de un usuario existente | **201** con todos los campos tal como se enviaron |
| CA-03 | `title` vacío, solo espacios, de menos de 3 o más de 120 caracteres, o ausente | **422** |
| CA-04 | `priority` fuera de 1–5 (0, 6, -1) o que no sea entero | **422** |
| CA-05 | `due_date` anterior a hoy | **422** con `detail` "La fecha límite no puede estar en el pasado" |
| CA-06 | `due_date` igual a hoy | **201** (frontera permitida) |
| CA-07 | `assignee_id` de un usuario que no existe | **422** con `detail` "El responsable no existe: <id>" |
| CA-08 | Header `Idempotency-Key: K` repetido con **el mismo cuerpo** | **201** con **la misma tarea** (mismo `id`); no se crea una segunda tarea |
| CA-09 | Header `Idempotency-Key: K` repetido con **otro cuerpo** | **409** con `detail` que menciona la llave de idempotencia |
| CA-10 | Dos peticiones iguales **sin** `Idempotency-Key` | Dos tareas distintas (la idempotencia es opcional y explícita) |
| CA-11 | Una petición que falla por validación con `Idempotency-Key: K` | La llave **no** queda reservada: un reintento corregido con `K` crea la tarea |
| CA-11b | `Idempotency-Key` vacía, con espacios o de más de 100 caracteres | **422** (la llave es un token opaco, p. ej. un UUID) |

### GET /tasks — listar

| # | Dado / Cuando | Entonces |
|---|---------------|----------|
| CA-12 | Sin tareas | **200** con `[]` |
| CA-13 | Varias tareas | **200** ordenadas por `id` ascendente |
| CA-14 | Filtros `status`, `assignee_id`, `priority` (combinables) | **200** solo con las que cumplen todos los filtros |
| CA-15 | Filtro con un valor inválido (`status=foo`, `priority=9`) | **422** |

### GET /tasks/{task_id}

| # | Dado / Cuando | Entonces |
|---|---------------|----------|
| CA-16 | Tarea existente | **200** con la tarea |
| CA-17 | Tarea inexistente | **404** con `detail` "tarea no encontrada: <id>" (catálogo `core/errors.py`) |

### PATCH /tasks/{task_id}/status — cambiar estado

Transiciones permitidas:

```
pending ──► in_progress ──► done
   │            │
   │            └──► pending   (se devuelve a la cola)
   └──────────────► done
```

| # | Dado / Cuando | Entonces |
|---|---------------|----------|
| CA-18 | Una transición permitida | **200**; `status` nuevo, `updated_at` actualizado, nueva entrada en `status_history` |
| CA-19 | Cambiar al **mismo** estado en el que ya está | **200** sin cambios ni entrada nueva en el historial (operación idempotente) |
| CA-20 | Una tarea `done` a cualquier otro estado | **409** con `detail` "Transición de estado no permitida: done → <nuevo>" |
| CA-21 | Un estado que no existe (`"archived"`) | **422** |
| CA-22 | Tarea inexistente | **404** |

### Respuestas de error

Todas siguen el formato del proyecto: `{"detail": "<mensaje en español>"}` para
errores de dominio (lanzados con `core/errors.py`) y el formato estándar de FastAPI
para errores de validación de esquema (422).

## Requisitos no funcionales

- Seguir las convenciones de `CLAUDE.md`: capas `routes → service → repository`,
  `response_model=` en todas las rutas, errores desde `core/errors.py`.
- La fecha "de hoy" se obtiene de una dependencia reemplazable (reloj) para que los
  tests no dependan del día en que se corren.
- `ruff check .` sin errores; cobertura > 80 % de líneas y ramas (meta: > 90 %).
- No modificar `migrations/` ni `legacy/`.
