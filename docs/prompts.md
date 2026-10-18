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
| P-06 | 2–3 | Iteración 1 · tests de crear y consultar (rojo) | Test-first · few-shot de estilo con `@tests/test_users.py` | Aceptado |
| P-07 | 2 | Iteración 1 · implementación mínima (verde) | Incremental · "lo mínimo para pasar" | Aceptado |
| P-08 | 3 | Iteración 2 · tests de validaciones y fronteras (rojo) | Test-first · enumerar clases de casos · parametrize | Aceptado |
| P-09 | 2 | Iteración 2 · validaciones de dominio (verde) | Incremental · restricción de orden ("validar antes de reservar id") | Aceptado |
| P-10 | 3 | Iteración 3 · tests de idempotencia (rojo) | Test-first · contraejemplos explícitos | Aceptado |
| P-11 | 2 | Iteración 3 · idempotencia (verde) | Incremental · pedir el orden de operaciones razonado | Aceptado |
| P-12 | 3 | Caso límite de orden: reintento al día siguiente + mutación manual | Pregunta "¿qué pasa si…?" · mutación a mano (Clase 2 M2) | Aceptado |
| P-13 | 3 | Iteración 4 · tests de listar, filtrar y cambiar estado (rojo) | Test-first · tabla de casos con parametrize · resolver ambigüedades de la especificación | Aceptado |
| P-14 | 2 | Iteración 4 · listado y transiciones (verde) + cobertura | Incremental · modelos inmutables (`model_copy`) | Aceptado |
| P-15 | 3 | Tests unitarios del servicio con mocks | Separar unitario vs integración · mocks que verifican interacciones | Aceptado |
| P-16 | 3 | Mutation testing con `mutmut` + verificación del resultado | Desconfiar de un 100 % · reproducir un mutante a mano | Ajustado (config deprecada) |

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

---

## P-06 · Iteración 1 — tests primero: crear y consultar (rojo)

**Fase:** 2–3 · Generación + tests
**Técnica:** test-first (TDD) · few-shot de estilo (los tests de `users` como
ejemplo) · un criterio por test
**Contexto:** `@docs/especificacion.md` `@tests/test_users.py` `@tests/conftest.py`
`@tasks/clock.py`

```text
Iteración 1 (test-first). Escribe SOLO tests, no implementes nada.
1. En @tests/conftest.py agrega: el reset del almacén de tasks entre tests, y un
   fixture autouse que fije tasks.clock.today() en date(2026, 10, 18) con
   monkeypatch (ningún test debe depender del día real).
2. Crea tests/test_tasks.py con el MISMO estilo que @tests/test_users.py
   (nombre en español, arrange/act/assert separados por línea en blanco) para:
   CA-01 (solo título → defaults), CA-02 (todos los campos, responsable = usuario
   semilla 2), recorte de espacios del título, ids consecutivos, CA-16 y CA-17.
   Cada test lleva en su docstring el CA que cubre.
3. Corre pytest y muéstrame que fallan por NotImplementedError (no por errores de
   import o de sintaxis).
```

**Resultado:** 6 tests nuevos; la suite completa en **rojo** (12 errores), incluidos los
6 de `users`, porque el fixture llama a `tasks.repository.reset()`, que todavía
era un esqueleto. Evidencia: `docs/evidencia/it1_rojo.log`.

**Lectura del rojo:** que fallaran los tests de `users` no era una regresión. Era
la confirmación de que el fixture nuevo sí se ejecuta en toda la suite.

---

## P-07 · Iteración 1 — implementación mínima (verde)

**Fase:** 2 · Generación de código
**Técnica:** incremental · "el mínimo código que pone en verde estos tests" ·
dejar el resto como `NotImplementedError`
**Contexto:** `@tasks/service.py` `@tasks/repository.py` `@tasks/clock.py`
`@users/repository.py`

```text
Implementa lo MÍNIMO para que pasen los tests de la iteración 1:
- tasks/clock.py: today() y now() en UTC (today se deriva de now).
- tasks/repository.py: next_id, add, get y reset, imitando @users/repository.py.
  Deja list_all, save y las funciones de idempotencia con NotImplementedError.
- tasks/service.py: create_task (sin validaciones de dominio ni idempotencia
  todavía; vienen en la iteración 2 y 3) y get_task con errors.not_found.
created_at, updated_at y la primera entrada de status_history deben usar el
MISMO instante (una sola llamada a clock.now()).
Corre pytest y ruff check .
```

**Resultado:** **12 passed**, `ruff` limpio. Evidencia: `docs/evidencia/it1_verde.log`.

**Detalle revisado:** usar una sola llamada a `clock.now()` hace que
`created_at == updated_at` en una tarea nueva. El test CA-01 lo verifica; con dos
llamadas, la prueba habría fallado de forma intermitente por microsegundos.

**Decisión:** aceptado.

---

## P-08 · Iteración 2 — tests de validaciones y fronteras (rojo)

**Fase:** 3 · Tests
**Técnica:** test-first · **enumerar las clases de casos** (técnica de la Clase 2 de
M1 para generar tests: camino feliz, cada rama, fronteras, entradas inválidas) ·
`parametrize` con `id` legible
**Contexto:** `@docs/especificacion.md` `@tests/test_tasks.py` `@tests/conftest.py`

```text
Iteración 2 (test-first). Agrega a @tests/test_tasks.py tests para CA-03 a CA-07.
Enumera explícitamente estas clases de casos; no te quedes en el camino feliz:
- Título: vacío, solo espacios, 2 caracteres, 2 tras recortar, 121, no-texto,
  null, ausente; y las fronteras válidas 3 y 120.
- Prioridad: 0, 6, -1, 2.5, true, "3"; y las fronteras válidas 1 y 5.
- Fecha: ayer (422 con el detail exacto), HOY (201, frontera), formato no ISO.
  Recuerda que el reloj está fijo en 2026-10-18 por el fixture.
- Responsable inexistente (422 con el detail exacto).
- Una petición rechazada no debe crear tarea ni consumir un id.
Usa pytest.mark.parametrize con ids legibles para cada familia. Corre pytest y
dime cuáles fallan y por qué; antes de correrlo, predice cuáles van a fallar.
```

**Predicción antes de correr:** fallarían solo los de **dominio** (fecha pasada,
responsable inexistente, no consumir id); los de **forma** (título, prioridad,
formato de fecha) deberían pasar ya, gracias a la corrección del schema en P-05.

**Resultado:** 29 tests nuevos (con parametrize); **3 failed, 32 passed**, tal como
se predijo (`docs/evidencia/it2_rojo.log`). La predicción confirma que el schema y
el servicio reparten bien las responsabilidades (forma vs. dominio).

---

## P-09 · Iteración 2 — validaciones de dominio (verde)

**Fase:** 2 · Generación
**Técnica:** incremental · restricción de orden explícita · reutilizar en lugar de
duplicar
**Contexto:** `@tasks/service.py` `@users/service.py` `@core/errors.py` `@CLAUDE.md`

```text
Haz pasar los 3 tests en rojo de la iteración 2:
- En tasks/service.py, una función privada _validate_new_task(data) con las dos
  reglas de dominio (fecha < clock.today() → invalid_request con el texto de la
  especificación; responsable inexistente → invalid_request).
- Las validaciones van ANTES de pedir un id al repositorio (hay un test que lo
  exige).
- Para saber si el responsable existe NO importes users.repository (lo prohíbe
  @CLAUDE.md). Agrega a @users/service.py una función pública user_exists(user_id)
  -> bool sin cambiar nada de lo que ya existe, y úsala.
Corre pytest completo (los tests de users deben seguir verdes) y ruff.
```

**Resultado:** **35 passed** (`docs/evidencia/it2_verde.log`), `ruff` limpio.

**Decisiones revisadas:**

- **`user_exists()` en vez de capturar la excepción de `get_user()`.** Alternativa
  considerada: llamar a `users_service.get_user()` y atrapar el 404. Se descartó
  porque usaría una excepción HTTP como control de flujo entre servicios, y un
  404 de *usuario* se podía filtrar como respuesta de *tarea*.
- **`users/service.py` solo ganó una función nueva.** Ningún comportamiento de
  `users` cambió: sus 6 tests siguen verdes (integración sin conflictos).
- `ruff --fix` reordenó un import (`users` después de `tasks`, por orden
  alfabético).

**Decisión:** aceptado.

---

## P-10 · Iteración 3 — tests de idempotencia (rojo)

**Fase:** 3 · Tests
**Técnica:** test-first · contraejemplos (casos que deben **no** comportarse como
reintento)
**Contexto:** `@docs/especificacion.md` (CA-08 a CA-11) `@tests/test_tasks.py`

```text
Iteración 3 (test-first): idempotencia de POST /tasks con el header
Idempotency-Key. Escribe tests para CA-08, CA-09, CA-10 y CA-11, y además estos
contraejemplos y bordes:
- llaves distintas con el mismo cuerpo → dos tareas (la llave identifica el
  reintento, no el contenido);
- "  Revisar logs  " y "Revisar logs" con la misma llave → mismo reintento
  (el cuerpo se compara ya normalizado);
- llave vacía → 422.
Para comprobar que el reintento no duplicó, verifica que no exista la tarea 2
(todavía no hay GET /tasks). Corre y explica cada rojo.
```

**Resultado:** 7 tests nuevos; **3 failed, 39 passed**
(`docs/evidencia/it3_rojo.log`). Los 4 que pasaron sin implementar nada eran
esperables: CA-10, llaves distintas y llave vacía ya se cumplían (el último por
`Header(min_length=1)` del esqueleto). CA-11 pasaba "por accidente", porque
todavía no se guardaba ninguna llave. Se mantuvo para que siga protegiendo el
comportamiento cuando sí se guarden.

---

## P-11 · Iteración 3 — idempotencia (verde)

**Fase:** 2 · Generación
**Técnica:** incremental · pedir el **orden de las operaciones razonado** antes del
código (chain-of-thought para auditar)
**Contexto:** `@tasks/service.py` `@tasks/repository.py` `@core/errors.py`

```text
Implementa la idempotencia para que pasen los tests de la iteración 3.
Antes de escribir código, dime en qué ORDEN harás estos pasos dentro de
create_task y por qué: calcular la huella del cuerpo, buscar la llave,
validar reglas de dominio, reservar id, guardar la tarea, guardar la llave.
Después impleméntalo:
- huella = sha256 del cuerpo ya normalizado (model_dump_json);
- llave conocida + misma huella → devolver la tarea original;
- llave conocida + otra huella → errors.conflict con un mensaje que mencione
  la llave;
- guardar la llave SOLO si la tarea se creó.
```

**Orden propuesto y aceptado:**

1. Calcular la huella.
2. Si hay llave **y ya se usó**: responder el reintento (original o 409) **sin
   validar**.
3. Validar reglas de dominio.
4. Reservar id y guardar la tarea.
5. Guardar la llave (solo aquí, por CA-11).

**Por qué el paso 2 va antes del 3:** un reintento debe recibir lo mismo que la
petición original. Si se validara primero, un reintento al día siguiente de una
tarea con fecha "hoy" recibiría 422 por "fecha en el pasado", aunque la tarea sí
se creó.

**Resultado:** **42 passed**, `ruff` limpio.

---

## P-12 · Caso límite de orden: reintento al día siguiente + mutación manual

**Fase:** 3 · Tests (calidad de la suite)
**Técnica:** "¿qué pasa si…?" sobre la decisión de P-11 · **mutación manual**
(Clase 2 del M2: romper el código a propósito y ver si algún test se da cuenta)
**Contexto:** `@tasks/service.py` `@tests/test_tasks.py` `@tests/conftest.py`

```text
El orden "revisar llave antes de validar" de create_task es una decisión
importante, pero ningún test la protege: si alguien lo invierte, la suite
seguiría verde. Escribe un test que lo fije: crear una tarea con due_date de
hoy y una llave; mover el reloj al día siguiente con monkeypatch; reintentar
con la misma llave → 201 con la tarea original.
Luego demuéstrame que el test sirve: invierte temporalmente el orden en
create_task, corre la suite, confirma que SOLO ese test falla y restaura el
código.
```

**Resultado:**

| Paso | Suite |
|------|-------|
| Test nuevo con el código correcto | **43 passed** |
| Mutante: `_validate_new_task` movido antes de revisar la llave | **1 failed** (justo el test nuevo), 42 passed |
| Código restaurado | **43 passed** |

**Lección:** tener cobertura de líneas no basta para saber si un test protege algo. El
orden ya estaba **cubierto** (todas las líneas se ejecutaban), pero ningún test
**detectaba** que se invirtiera. Es justo la diferencia entre cobertura y mutation
testing de la Clase 2.

**Decisión:** aceptado.

---

## P-13 · Iteración 4 — tests de listar, filtrar y cambiar estado (rojo)

**Fase:** 3 · Tests
**Técnica:** test-first · tabla de casos con `parametrize` · pedir a la IA que
**señale ambigüedades** de la especificación antes de escribir tests
**Contexto:** `@docs/especificacion.md` (CA-12 a CA-22) `@tests/test_tasks.py`

```text
Iteración 4 (test-first): GET /tasks con filtros y PATCH /tasks/{id}/status.
Primero dime si encuentras ambigüedades o reglas que choquen entre sí en
CA-12..CA-22; no las resuelvas tú, solo señálalas.
Después escribe los tests:
- un helper que siembre 3 tareas con estado, responsable y prioridad
  distintos, y un parametrize para los filtros (uno por uno, combinados, sin
  coincidencias) y para los filtros inválidos;
- un parametrize con TODAS las transiciones permitidas, verificando el
  historial completo;
- updated_at y changed_at con el reloj fijado por monkeypatch;
- mismo estado, done → otro estado, estado inexistente, tarea inexistente, y
  que el cambio persista al consultar después.
```

**Ambigüedad que señaló la IA:** CA-19 ("mismo estado → 200") y CA-20 ("desde
`done` → 409") chocan en el caso **`done → done`**. Se resolvió: **gana CA-19**,
porque un cliente que reintenta "marcar como terminada" no debe recibir un error.
Quedó fijado con su propio test
(`test_change_status_done_a_done_es_idempotente`).

**Resultado:** 23 tests nuevos (con parametrize); **18 failed, 48 passed**
(`docs/evidencia/it4_rojo.log`). Los que pasaron sin implementar fueron los de
validación de forma (estado y filtros inválidos → 422, rechazados por el schema
y por `Query(ge=1, le=5)`) y el 404 de tarea inexistente, que reutiliza
`get_task`.

---

## P-14 · Iteración 4 — listado y transiciones (verde) + cobertura

**Fase:** 2 · Generación · 3 · Cobertura
**Técnica:** incremental · usar la tabla `ALLOWED_TRANSITIONS` del esqueleto como
única fuente de verdad · modelos inmutables
**Contexto:** `@tasks/service.py` `@tasks/repository.py`

```text
Haz pasar los tests de la iteración 4:
- repository.list_all con filtros combinables y orden por id; repository.save.
- service.list_tasks delega; service.change_status: mismo estado → devolver
  sin cambios; transición fuera de ALLOWED_TRANSITIONS → errors.conflict con el
  texto exacto de la especificación; si no, crear una COPIA de la tarea
  (model_copy) con el nuevo estado, la entrada nueva del historial y
  updated_at, y guardarla. No mutes el objeto guardado en el repositorio.
Después corre la cobertura con ramas para tasks, core, users y main, y dime qué
líneas quedan sin cubrir y si vale la pena cubrirlas.
```

**Resultado:** **66 passed**. Cobertura de **99 %** en líneas y ramas
(`docs/evidencia/it4_cobertura.log`): `tasks/service.py` y `tasks/repository.py`
al 100 %, con todas sus ramas.

**Líneas sin cubrir y decisión:**

| Línea | Por qué no se cubre | Decisión |
|-------|---------------------|----------|
| `tasks/clock.py:12` (`today()`) | Los tests siempre la reemplazan con el reloj fijo | Cubrirla con un test unitario del reloj (P-15) |
| `main.py:18` (`/health`) | Código del repo base sin test | Agregar un test mínimo, porque es barato y mejora el proyecto base |

**Por qué `model_copy` y no mutar:** si `change_status` modificara el objeto que
devuelve el repositorio, un error a la mitad dejaría una tarea guardada a medias
(por ejemplo, con el estado nuevo pero sin entrada en el historial). Con la copia,
el repositorio solo cambia en el `save()` final.

**Decisión:** aceptado.

---

## P-15 · Tests unitarios del servicio con mocks

**Fase:** 3 · Tests (unitarios)
**Técnica:** separar unitario (sin HTTP) de integración (`TestClient`) · mocks
con `MagicMock` que verifican **interacciones** (con quién habla el servicio),
no solo resultados · tabla exhaustiva con `itertools.product`
**Contexto:** `@tasks/service.py` `@tasks/clock.py` `@users/service.py`
`@tests/conftest.py` `@CLAUDE.md` (sección Tests)

```text
Crea tests/test_tasks_service.py con tests UNITARIOS de tasks/service.py (sin
TestClient). Reemplaza dependencias con mocks:
- users.service.user_exists con un MagicMock: verifica que NO se llama si no hay
  responsable, que se llama una vez con el id correcto, y que un reintento
  idempotente tampoco lo llama.
- repository.next_id con un MagicMock que falle si se llama: demuestra que una
  tarea inválida no reserva id.
- clock.now fijo: created_at == updated_at == primera entrada del historial.
- Las 9 combinaciones de estados (product(TaskStatus, TaskStatus)) contra
  ALLOWED_TRANSITIONS, y que change_status no muta la tarea original.
- Cubre también clock.today() (hoy no lo cubre nadie porque el conftest lo
  reemplaza) y agrega tests/test_main.py para /health y para comprobar que las
  rutas de tasks aparecen en /openapi.json.
Arrange/act/assert separados, igual que el resto de la suite.
```

**Resultado:** 23 tests nuevos → **89 passed**. Cobertura: **100 % de líneas y
100 % de ramas** en `tasks`, `core`, `users` y `main`
(`docs/evidencia/cobertura_final.log`).

**Por qué importan los mocks aquí:** los tests de integración comprueban *qué*
responde la API. Los unitarios comprueban decisiones internas que la API no deja
ver; por ejemplo, que un reintento **no** vuelve a consultar `users`
(`assert_not_called`). Si alguien moviera la validación antes de la revisión de
la llave, este test fallaría aunque el código HTTP siguiera siendo 201.

**Detalle técnico revisado:** el test de `clock.today()` usa `monkeypatch.undo()`
para quitar el reloj fijo del `conftest` y probar el real. Se verificó que no
afecta a otros tests, porque `monkeypatch` es por test.

---

## P-16 · Mutation testing con `mutmut` + verificación del resultado

**Fase:** 3 · Calidad de la suite
**Técnica:** mutation testing (Clase 2 del M2) · **desconfiar de un resultado
perfecto** · confirmar reproduciendo un mutante a mano
**Contexto:** `@pyproject.toml` `@tasks/`

```text
Configura mutmut en @pyproject.toml para mutar solo tasks/ (los demás módulos
se copian pero no se mutan) y córrelo. Dame el resumen por estado y por módulo.
Si sobreviven mutantes, muéstrame cada uno con `mutmut show` y escribe el test
que lo mata.
Si NO sobrevive ninguno, no lo celebres todavía: demuéstrame que las muertes
son reales y no producto de errores de importación o configuración. Muéstrame
2 mutantes con `mutmut show` y reproduce a mano el más importante (el operador
de la fecha límite, < → <=) para ver qué test lo detecta.
```

**Resultado:**

| Métrica | Valor |
|---------|-------|
| Mutantes generados | 125 (`service` 98, `repository` 26, `clock` 1) |
| Matados | **125 (100 %)** |
| Sobrevivientes | 0 |

**Verificación de que el 100 % es real** (`docs/evidencia/mutmut.log`):

- `mutmut show` de mutantes concretos: `and → or` en la validación de fecha,
  `<` → `<=`, mensajes alterados (`"XX…XX"`, minúsculas, mayúsculas, `None`).
  Son cambios reales de comportamiento.
- Mutante de frontera reproducido a mano (`<` → `<=`): lo detectan
  `test_create_task_fecha_de_hoy_es_valida` (CA-06) y
  `test_reintento_al_dia_siguiente_…` (P-12) → **2 failed, 87 passed**.
- Los mutantes de **mensajes** mueren porque los tests comparan el `detail`
  completo (`==`), no con `in`. En una suite que solo revisara el código de
  estado, habrían sobrevivido.

**Ajuste:** la primera configuración usaba `paths_to_mutate` y `tests_dir`, que
`mutmut 3.8` marca como **deprecados** (warnings en la salida). Se cambió a
`source_paths` y se quitó `tests_dir` (por defecto ya es `tests/`); se volvió a
correr y dio el mismo resultado, ya sin warnings.

**Reflexión:** el 100 % de mutantes no salió "de la nada". Salió de tres
decisiones anteriores: probar las **fronteras** explícitas (P-08), comparar
**mensajes exactos** y fijar el **orden** de operaciones con un test (P-12). Sin
esas decisiones, los mutantes `<=`, de mensajes y de orden habrían sobrevivido,
aunque la cobertura de líneas ya era del 100 %.

**Decisión:** ajustado (configuración) y aceptado.
