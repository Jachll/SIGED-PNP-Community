# Backend Release Checklist

## Objetivo

Checklist operativo de salida para backend, con foco en estabilidad territorial, QA reproducible e higiene del repositorio.

## Gate duro

- `pytest` completo en verde.
- build del frontend en verde si el release mueve contratos consumidos por UI.
- migraciones y compatibilidad territorial verificadas en el entorno objetivo.

## Validaciones tecnicas no bloqueantes

Estas validaciones no deben romper el release por si solas, pero si deben quedar registradas:

- ejecutar `scripts/benchmark_backend.py --iterations 3` sobre una base representativa
- comparar el JSON generado con el baseline previo del mismo entorno
- anotar diferencias relevantes por endpoint y decidir si son aceptables

Razon:

- el benchmark depende de volumen de datos, hardware y estado real de PostgreSQL/PostGIS
- sirve como señal tecnica de degradacion, no como gate binario universal de CI

## QA operativo recomendado

1. Sembrar usuarios QA si el entorno no los tiene:
   `.\backend\.venv\Scripts\python.exe .\scripts\seed_validation_users.py`
2. Ejecutar benchmark no bloqueante:
   `.\backend\.venv\Scripts\python.exe .\scripts\benchmark_backend.py --iterations 3`
3. Ejecutar smoke funcional de cargas.
4. Limpiar residuos del smoke:
   `.\backend\.venv\Scripts\python.exe .\scripts\cleanup_validation_lotes.py SIGED_E2E_SMOKE_QA`

## Observabilidad territorial para Fase 3

Verificar que existan metricas y request ids para:

- `operation:territorio.contexto`
- `operation:territorio.regiones`
- `operation:territorio.divisiones`
- `operation:territorio.comisarias`
- `operation:territorio.jurisdicciones`
- `operation:territorio.sectores`
- `operation:territorio.geojson.*`
- `operation:territorio.legacy.*`

Adicionalmente revisar:

- `X-Request-ID` presente en respuestas y errores
- logs lentos por request, query y operation si superan thresholds configurados
- diferencias entre rutas nuevas `/territorio/*` y legacy `/capas/geojson/*`

## Higiene del repositorio

Antes de publicar o abrir PR, confirmar que no entren al flujo principal:

- `backend/.venv/`
- `backend/.pytest_cache/`
- `backend/uploads/`
- `backend/*.log`
- `scripts/logs/`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/test-results/`
- `__pycache__/`
- archivos locales `.env`
