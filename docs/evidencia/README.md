# Evidencia del proceso

Logs guardados durante el desarrollo, en orden. Cada uno se cita en `docs/prompts.md`.

| Archivo | Prompt | Qué muestra |
|---------|--------|-------------|
| `it1_rojo.log` / `it1_verde.log` | P-06 / P-07 | Iteración 1 (crear y consultar): 12 errores → 12 passed |
| `it2_rojo.log` / `it2_verde.log` | P-08 / P-09 | Iteración 2 (validaciones): 3 failed (los previstos) → 35 passed |
| `it3_rojo.log` / `it3_verde.log` | P-10 / P-12 | Iteración 3 (idempotencia): 3 failed → 43 passed |
| `it4_rojo.log` / `it4_verde.log` | P-13 / P-14 | Iteración 4 (listar y estados): 18 failed → 66 passed |
| `it4_cobertura.log` | P-14 | Cobertura del 99 % antes de los tests unitarios |
| `cobertura_final.log` | P-15 | Cobertura del 100 % en líneas y ramas (89 tests) |
| `mutmut.log` | P-16 | 125/125 mutantes muertos + verificación manual del mutante de frontera |
| `bug_tz_rojo.log` / `bug_tz_verde.log` | P-19 | Bug de zona horaria: traceback en rojo → 93 passed |
| `mutmut_refactor.log` | P-21 / P-22 | Tras refactorizar: 1 sobreviviente (`astimezone(None)`) → 123/123 |
| `fix_menores_rojo.log` / `fix_menores_verde.log` | P-23 | Llave con espacios y "no encontrada": 3 failed → 99 passed |
| `final_pytest.log`, `final_cobertura.log`, `final_ruff.log`, `final_mutmut.log` | P-24 | Estado final: 99 passed · 100 % líneas y ramas · ruff limpio · 126/126 mutantes |
