# Reflexión — Reto M2

## Qué funcionó

**Especificar antes de generar.** Los 22 criterios de aceptación con su código
HTTP exacto convirtieron cada prompt de código en algo verificable. "Haz pasar
CA-05" no deja espacio para interpretar; "agrega validaciones" sí. Al pedirle a la
IA que **señalara ambigüedades** de la especificación (P-13), apareció el choque
entre CA-19 y CA-20 (`done → done`) antes de que se convirtiera en un bug.

**Skeleton-first atrapó bugs que no costaron nada.** Revisar el esqueleto
*ejecutando* el schema con casos límite (P-05) encontró dos errores, el título de
puros espacios y `priority: true`, cuando corregirlos costaba dos líneas.

**Test-first con predicción.** Predecir qué tests iban a fallar antes de correrlos
(P-08) sirvió como chequeo de diseño: el rojo coincidió con lo previsto (solo
fallaron los de dominio), lo que confirmó que schema y servicio se repartían bien
las responsabilidades.

**Hipótesis antes que parche.** En el bug de zona horaria (P-18), pedir 2 o 3
hipótesis con su forma de confirmarlas evitó el parche obvio y equivocado
(cambiar `<` por `<=`), que habría "arreglado" las noches rompiendo la frontera
de CA-06.

## Qué no funcionó a la primera

**La cobertura del 100 % no significaba una suite confiable.** Tres veces el
código estaba cubierto al 100 % y aun así había huecos:

1. El orden "revisar la llave antes de validar" no lo protegía ningún test (P-12).
2. El bug de zona horaria vivía en la única función que los tests reemplazaban
   (P-18).
3. Después de refactorizar, un mutante sobrevivió porque la máquina de pruebas
   estaba en la misma zona horaria que el negocio (P-22). El problema no estaba en
   el código: estaba en la suite.

La herramienta que encontró el tercero fue `mutmut`, no la cobertura.

**El entorno.** La red bloqueaba PyPI y se perdió tiempo antes de poder correr la
primera prueba. La solución fue descargar los paquetes en otra máquina e
instalarlos sin conexión. Lección para el siguiente reto: verificar el entorno
(instalar y correr la suite base) **antes** de empezar a especificar.

## Decisiones de criterio (no delegables a la IA)

Estas decisiones las propuso la IA con sus alternativas, pero son de negocio o de
diseño y requieren validación humana. Están registradas en `docs/prompts.md`:

- Las 5 decisiones de diseño de la especificación (422 para responsable
  inexistente, 201 en el reintento, no reservar la llave, PATCH idempotente,
  "hoy" permitido).
- Que gane CA-19 sobre CA-20 en `done → done`.
- Corregir el bug de zona horaria con una zona **configurable** y no con UTC
  ni con la hora local del servidor.
- Rechazar la propuesta de quitar el reloj fijo del conftest (P-19) y clasificar 2
  hallazgos del code review como falsos positivos (P-20).

## Qué mejoraría

1. Un **hook** de Claude Code que corra `pytest` en cada edición, y `mutmut` en
   CI para `tasks/`: en este reto lo corrí a mano.
2. Escribir el test de "la zona horaria del servidor es distinta" **desde la
   especificación**: cualquier regla con "hoy" merece un criterio explícito de
   zona horaria.
3. Guardar la **respuesta original** en la idempotencia, en lugar de devolver la
   tarea en su estado actual. Hoy un reintento después de un cambio de estado
   devuelve el estado nuevo; para clientes estrictos convendría devolver
   exactamente la respuesta original.
4. Proponer al equipo del repo base el parámetro `feminine` de `not_found`, o
   un mensaje neutro, para no depender de la concordancia en el catálogo.
