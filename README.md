# SIGED-PNP Community

[![CI](https://github.com/Jachll/SIGED-PNP-Community/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Jachll/SIGED-PNP-Community/actions/workflows/backend-ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)](backend/)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-646cff.svg)](frontend/)

SIGED-PNP Community es una base open source para inteligencia geoespacial del delito, analítica territorial operativa y visualización de eventos en mapas. Esta edición pública incluye código, documentación, pruebas, CI y datos sintéticos mínimos.

El repositorio público no incluye mapas institucionales privados, capas territoriales reales, datos policiales reales, archivos geográficos no públicos ni imágenes con derechos inciertos.

## Why SIGED-PNP?

Los equipos territoriales necesitan convertir registros dispersos en señales operativas: concentración espacial, horarios críticos, evolución temporal, carga por jurisdicción y recomendaciones de patrullaje. SIGED-PNP ofrece una base mantenible para construir ese flujo con herramientas abiertas y una arquitectura clara.

## Features

- Backend `FastAPI` organizado por `routers`, `services`, `repositories` y `schemas`.
- SQL directo con `psycopg2`, sin ORM.
- Soporte `PostgreSQL + PostGIS`.
- Carga CSV/XLSX por lotes con staging, validación y promoción controlada.
- Autenticación JWT con roles `admin`, `analista` y `consulta`.
- Frontend `React + Vite + Leaflet + Chart.js`.
- Dashboard operacional, analítica temporal, mapa, filtros y recomendaciones.
- Flujo territorial por región, división, comisaría, jurisdicción y sector.
- Pruebas backend con `pytest`, pruebas frontend con `node --test` y CI en GitHub Actions.

## Architecture

```text
CSV/XLSX sintetico
    -> scripts Python o API /cargas/lotes
    -> staging_eventos + lotes_carga
    -> validacion y promocion
    -> eventos_delictivos
    -> FastAPI
    -> React + Leaflet + Chart.js
```

Backend:

- `backend/app/api/routers/`: rutas HTTP y seguridad.
- `backend/app/services/`: casos de uso y reglas de negocio.
- `backend/app/repositories/`: SQL y acceso a datos.
- `backend/app/schemas/`: contratos de entrada y salida.
- `backend/app/etl/`: pipeline tabular y asignación territorial.

Frontend:

- `frontend/src/pages/`: vistas principales.
- `frontend/src/components/`: mapa, filtros, overlays y paneles.
- `frontend/src/hooks/`: jerarquía territorial, capas y modelos compartidos.
- `frontend/src/services/api.js`: cliente HTTP centralizado.

## Public Data Policy

- `database/sample_data/` contiene únicamente datos sintéticos de demostración.
- No se incluyen datos policiales reales ni información operativa real.
- `salida_geojson/` está ignorado y debe cargarse localmente.
- Cada institución debe aportar sus propias capas territoriales y validar su permiso de uso.
- No publiques GeoJSON, shapefiles, geopackages, Excel, CSV o imágenes institucionales si su origen no es explícitamente público o sintético.

## Quickstart

### Backend

```powershell
cd SIGED-PNP-Community\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd SIGED-PNP-Community\frontend
npm ci
npm run dev
```

### Database

Sigue [`docs/database.md`](docs/database.md) para crear `siged_pnp`, ejecutar las migraciones `database/sql/` y cargar datos sintéticos.

Ejemplo de carga:

```powershell
cd SIGED-PNP-Community
.\backend\.venv\Scripts\python.exe .\scripts\import_csv_lotes.py --input .\database\sample_data\eventos_delictivos_sample.csv --observaciones "Carga sintética inicial"
```

## Testing

Backend:

```powershell
cd backend
python -m compileall app tests scripts ../scripts
python -m pytest
```

Las pruebas que requieren una base PostgreSQL/PostGIS real se ejecutan solo si defines `RUN_DB_INTEGRATION_TESTS=1`.

Frontend:

```powershell
cd frontend
npm run lint
npm run test
npm run build
```

## Screenshots

Esta edición no incluye capturas con mapas o activos institucionales. Para publicar screenshots, usa datos sintéticos y mapas/capas con permiso explícito de publicación.

## Open Source Status

Este proyecto está en fase `v0.2.0-alpha`: útil para evaluación, demostración y colaboración técnica, pero requiere revisión de seguridad, despliegue y datos antes de cualquier uso operativo real.

## Roadmap

Consulta [`ROADMAP.md`](ROADMAP.md).

## Contributing

Lee [`CONTRIBUTING.md`](CONTRIBUTING.md). Las contribuciones deben respetar la arquitectura por capas, mantener SQL en repositories y evitar cambios no validados en el flujo territorial.

## Security

Reporta vulnerabilidades siguiendo [`SECURITY.md`](SECURITY.md). No abras issues públicos con secretos, tokens, datos reales, rutas internas, coordenadas sensibles o información policial real.

## License

Distribuido bajo licencia [Apache-2.0](LICENSE).
