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
