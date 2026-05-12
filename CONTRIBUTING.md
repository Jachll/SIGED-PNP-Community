# Contribuir a SIGED-PNP Community

Gracias por ayudar a mejorar SIGED-PNP Community. Este proyecto prioriza cambios pequeños, revisables y seguros.

## Requisitos previos

- Python 3.13 o compatible con el backend.
- Node.js 20 o compatible con Vite.
- PostgreSQL con PostGIS.
- Git.

## Instalación local

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

## Tests y validación

Antes de enviar un PR, ejecuta lo que aplique:

```powershell
cd backend && python -m pytest
```

```powershell
cd frontend && npm run lint
cd frontend && npm run test
cd frontend && npm run build
```

Validación Python ampliada:

```powershell
cd backend
python -m compileall app tests scripts ../scripts
```

Las pruebas de integración que requieren PostgreSQL/PostGIS local están deshabilitadas por defecto. Para ejecutarlas, configura la base local y define `RUN_DB_INTEGRATION_TESTS=1`.

## Reglas de arquitectura

- No introducir ORM.
- No mover SQL fuera de `backend/app/repositories/`.
- Mantener routers delgados.
- Mantener reglas de negocio en `backend/app/services/`.
- No mover llamadas HTTP fuera de `frontend/src/services/api.js`.
- No cambiar endpoints existentes sin discusión previa.
- No modificar lógica territorial sin pruebas y revisión explícita.

## Flujo territorial

No rompas el flujo de regiones, divisiones, comisarías, jurisdicciones y sectores. Evita cambios no validados sobre selección de capas, foco de mapa, retención de capas o modelos de renderizado territorial.

## Datos sensibles

- No subas datos policiales reales.
- No subas Excel/CSV de origen incierto.
- No subas GeoJSON, shapefiles o geopackages privados.
- No subas mapas institucionales ni imágenes con derechos inciertos.
- No subas `.env`, secretos, tokens, uploads, backups, logs, `node_modules`, `dist` ni `.venv`.
- Si hay duda sobre el origen de un archivo, exclúyelo y explica el caso en el PR.

## Issues

Usa las plantillas de GitHub para reportar bugs, pedir mejoras o proponer cambios de documentación. No incluyas información sensible en issues públicos.

## Pull requests

Un PR debe incluir:

- Descripción clara del cambio.
- Alcance técnico.
- Comandos ejecutados.
- Capturas si cambia UI y solo con datos sintéticos.
- Riesgos o limitaciones conocidas.

Mantén los PRs pequeños. Si el cambio toca backend y frontend, explica el contrato entre ambos.
