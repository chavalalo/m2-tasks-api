# Bitácora de prompts — Reto M2

Registro de **todos los prompts** usados para construir el recurso `tasks`, en el
orden en que se usaron. Cada uno está listo para copiarse en Claude Code (en la
raíz del repo, para que lea `CLAUDE.md` automáticamente).

**Cómo leer cada entrada**

- **Fase**: sección de la plantilla de entrega a la que corresponde (1–5).
- **Técnica**: patrón o técnica de prompting aplicada (vistas en M1-C2 y M2-C1…C4).
- **Contexto**: archivos referenciados con `@archivo`.
- **Resultado**: qué produjo la IA y cómo se verificó.
- **Decisión**: aceptado / ajustado / rechazado, y por qué.

## Índice

| ID | Fase | Objetivo | Técnica | Decisión |
|----|------|----------|---------|----------|
| P-01 | 1 | Explorar el repo base antes de proponer nada | Prompt chaining (paso 1), sin cambios | Aceptado |
| P-02 | 1 | Criterios de aceptación de la feature | Rol + formato estructurado + anti-invención | Pendiente de confirmar |
| P-03 | 1 | Actualizar `CLAUDE.md` para el recurso nuevo | Contexto persistente, restricciones explícitas | Aceptado |
| P-04 | 2 | Esqueleto del recurso (firmas + docstrings, sin lógica) | Skeleton-first · referencia a patrón existente con `@archivo` | Aceptado |
| P-05 | 2 | Revisar el esqueleto contra la especificación | Rol revisor · verificación ejecutable · anti-complacencia | Ajustado (2 hallazgos) |

---

## P-01 · Explorar el repo base (sin cambiar nada)

**Fase:** 1 · Especificación y contexto
**Técnica:** prompt chaining (primer eslabón) · "no cambies nada"
**Contexto:** `@CLAUDE.md` `@users/routes.py` `@users/service.py` `@users/schemas.py`
`@users/repository.py` `@core/errors.py` `@tests/test_users.py` `@tests/conftest.py`

```text
Voy a agregar un recurso nuevo a este proyecto. Antes de proponer nada,
léelo y dame un mapa:
1. Las capas de @users/ y qué responsabilidad tiene cada una.
2. Cómo se levantan y formatean los errores (@core/errors.py).
3. Cómo están escritos los tests (@tests/test_users.py, @tests/conftest.py):
   fixtures, estilo, nombres.
4. Las convenciones de @CLAUDE.md que un recurso nuevo debe respetar.
5. Qué NO está permitido tocar.
No escribas ni modifiques ningún archivo.
```

**Resultado:** mapa de 4 capas (`routes → service → repository`, `schemas`),
errores solo desde `core/errors.py` con formato `{"detail": ...}`, tests AAA con
`TestClient` y reset del almacén en `conftest.py`, prohibido tocar `migrations/` y
`legacy/`.
**Hallazgos útiles para el diseño:**

- El catálogo solo tiene `not_found` (404), `invalid_request` (422) y
  `already_exists` (409, mensaje "X ya existe"). Para la idempotencia y las
  transiciones de estado hace falta un 409 con **mensaje libre** → habrá que
  extender el catálogo (decisión registrada en P-02).
- `not_found` produce "`<recurso>` no encontrado": para "tarea" quedará
  "tarea no encontrado" (concordancia de género). Se anota como posible mejora,
  no se cambia porque los tests de `users` dependen del texto actual.

**Decisión:** aceptado.

---

## P-02 · Criterios de aceptación

**Fase:** 1 · Especificación
**Técnica:** rol (Product Owner + QA) · formato de salida estructurado · "si algo
no está en la historia, márcalo como supuesto"
**Contexto:** historia de usuario del plan del reto + mapa de P-01

```text
Actúa como Product Owner junto con un QA exigente.
<historia>
App interna de Gestión de Tareas de Equipo (API REST). Objetivo del sprint:
reducir pérdidas de trabajo no registrado y mejorar la trazabilidad de tareas
operativas. Casos límite que pide el líder técnico: título inválido, fecha
pasada, prioridad fuera de rango, idempotencia.
</historia>
Escribe docs/especificacion.md para un recurso nuevo `tasks` en este repo con:
1. Historia de usuario en formato Como/Quiero/Para.
2. Alcance: tabla incluido / fuera de alcance.
3. Modelo de datos con tipo y regla de validación por campo.
4. Criterios de aceptación numerados CA-01..CA-nn en formato Dado/Cuando/Entonces,
   con el código HTTP exacto y el texto de `detail` cuando sea un error de dominio.
   Cubre: crear, listar con filtros, consultar por id y cambiar estado.
5. Requisitos no funcionales (convenciones de @CLAUDE.md, cobertura, linting).
Reglas: usa SOLO los códigos que existen en @core/errors.py o di explícitamente
cuál hay que agregar; marca como "SUPUESTO" cualquier regla que no venga de la
historia. No escribas código.
```

**Resultado:** especificación con 22 criterios (`docs/especificacion.md`).

**Decisiones de diseño con alternativas** (la IA las planteó al redactar; quedan
**pendientes de confirmación del autor** antes de generar código):

| Punto | Alternativa descartada | Elegida | Razón |
|-------|------------------------|---------|-------|
| Responsable inexistente | 404 | **422** | El 404 es para el recurso de la URL; aquí `/tasks` existe y el problema es un dato del cuerpo |
| Reintento idempotente | 200 | **201 con la misma tarea** | Quien reintenta recibe la misma respuesta que la original (criterio del borrador IETF de `Idempotency-Key`) |
| Petición fallida con llave | Reservar la llave | **No reservarla** (CA-11) | Si no, el reintento corregido quedaría bloqueado para siempre |
| Cambio al mismo estado | 409 | **200 sin cambios** (CA-19) | PATCH idempotente, coherente con el objetivo del sprint |
| Fecha límite | "Solo futura" | **Hoy sí se permite** (CA-06) | Se fija la frontera explícitamente: ahí suelen aparecer los off-by-one |

**Supuestos aceptados** (no estaban en la historia): prioridad 1–5 con 3 por
defecto; título 3–120 caracteres; transiciones `pending → in_progress → done`,
`in_progress → pending`, `pending → done`; `done` es final.

---

## P-03 · Actualizar `CLAUDE.md` para el recurso nuevo

**Fase:** 1 · Contexto
**Técnica:** contexto persistente · restricciones explícitas · "solo agrega,
no reescribas"
**Contexto:** `@CLAUDE.md` `@docs/especificacion.md`

```text
Actualiza @CLAUDE.md para que cualquier sesión futura pueda trabajar en el
recurso tasks sin que yo repita instrucciones. Solo AGREGA; no reescribas ni
reordenes lo que ya existe. Incluye:
- dónde vive el recurso y que @docs/especificacion.md es la fuente de verdad;
- reglas propias: el reloj inyectable, la idempotencia (cuándo se guarda la
  llave), que tasks/ valida responsables a través de users/service.py y no del
  repositorio de users;
- convenciones de tests (AAA, nombres, parametrize, unitarios vs integración,
  reloj fijo);
- comandos de cobertura con ramas y de mutation testing;
- dónde documentar (docstrings, CHANGELOG, docs/prompts.md).
Mantén el archivo por debajo de 100 líneas.
```

**Resultado:** `CLAUDE.md` pasó de 41 a 75 líneas; secciones nuevas
"Reglas del recurso `tasks`", "Tests" y "Documentación"; comandos de cobertura
y `mutmut`.
**Verificación:** `git diff --stat CLAUDE.md` → 32 líneas agregadas y 1 modificada
(el título pasó a "API de usuarios y tareas"); las convenciones originales quedaron
intactas.

**Decisión:** aceptado.

---

## P-04 · Esqueleto del recurso `tasks` (skeleton-first)

**Fase:** 2 · Generación de código
**Técnica:** skeleton-first (Clase 1, M2) · "imita este archivo" con `@archivo` ·
prohibido implementar lógica
**Contexto:** `@CLAUDE.md` `@docs/especificacion.md` `@users/routes.py`
`@users/service.py` `@users/schemas.py` `@users/repository.py` `@core/errors.py` `@main.py`

```text
Vamos a construir el recurso tasks con el patrón skeleton-first.
Crea SOLO el esqueleto, sin lógica: cada función con su firma tipada, su
docstring en español (qué hace, qué errores levanta y qué CA-xx de
@docs/especificacion.md cubre) y `raise NotImplementedError` en el cuerpo.
Archivos:
- tasks/schemas.py: modelos Pydantic completos (estos SÍ con sus validaciones
  de forma: longitudes, rangos, tipos), imitando @users/schemas.py.
- tasks/repository.py: almacén en memoria + llaves de idempotencia, imitando
  @users/repository.py.
- tasks/service.py: create_task, get_task, list_tasks, change_status, y la
  tabla de transiciones permitidas como constante.
- tasks/routes.py: las 4 rutas, imitando @users/routes.py.
- tasks/clock.py: today() y now() para poder fijar la fecha en los tests.
Además: monta el router en @main.py y, si el catálogo de @core/errors.py no
tiene un 409 con mensaje libre, propón agregarlo (no reutilices
already_exists para algo que no es "ya existe").
Al terminar corre `ruff check .`. No escribas tests todavía.
```

**Resultado:** 6 archivos nuevos en `tasks/`, función `conflict()` agregada al
catálogo de errores, router montado en `main.py` (versión 0.2.0). `ruff`: sin
errores.

**Decisión de diseño aceptada:** se agregó `errors.conflict(message)` en lugar de
reutilizar `already_exists()`. Este último genera "X ya existe: Y", que no
describe ni una llave de idempotencia reutilizada ni una transición inválida.
Extender el catálogo respeta la convención "toda respuesta de error sale de
`core/errors.py`".

**Decisión:** aceptado.

---

## P-05 · Revisar el esqueleto contra la especificación

**Fase:** 2 · Revisión → refinamiento
**Técnica:** rol de revisor exigente · verificación **ejecutando** código, no
leyendo · "si no hay hallazgos, dilo"
**Contexto:** `@tasks/schemas.py` `@docs/especificacion.md`

```text
Actúa como QA. Antes de implementar la lógica, revisa @tasks/schemas.py contra
los criterios CA-01..CA-07 de @docs/especificacion.md. No leas el código y
supongas: instancia TaskCreate con casos límite y reporta cuáles se aceptan y
cuáles se rechazan. Incluye al menos: título de solo espacios, título con
espacios alrededor, 2/3/120/121 caracteres, prioridad 0/6/true/2.0/"3".
Para cada caso que contradiga la especificación, di qué criterio rompe y
propón el cambio mínimo. Si todo cumple, dilo; no inventes hallazgos.
```

**Resultado:** dos hallazgos reales, confirmados ejecutando el schema:

| Caso | Antes | Criterio roto | Corrección |
|------|-------|---------------|------------|
| `title="   "` (3 espacios) | **Aceptado** (mide 3) | CA-03 | `StringConstraints(strip_whitespace=True, ...)`: recorta antes de medir |
| `priority=true` | **Aceptado como `1`** (modo flexible de Pydantic) | CA-04 | `StrictInt`: rechaza `true`, `2.0` y `"3"` en lugar de convertirlos |

Después de la corrección: los 6 casos inválidos se rechazan y
`"  Revisar backups  "` se guarda recortado como `"Revisar backups"`.

**Ajuste derivado:** el docstring de `create_task` decía que el servicio
validaba el título vacío. Como ahora lo hace el schema, se corrigió para no
documentar algo falso. Los dos `ruff` (orden de imports y una línea de 103
caracteres) se arreglaron antes del commit.

**Lección:** revisar el esqueleto antes de escribir la lógica atrapó dos bugs
cuyo costo fue cambiar 2 líneas. Si se hubieran descubierto con los tests
de integración, habría que haber depurado a través de 3 capas.

**Decisión:** ajustado (2 hallazgos corregidos).
