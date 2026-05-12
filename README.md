# SIGED-PNP Community

[![CI](https://github.com/Jachll/SIGED-PNP-Community/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Jachll/SIGED-PNP-Community/actions/workflows/backend-ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)](backend/)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-646cff.svg)](frontend/)

SIGED-PNP Community is an open-source geospatial crime intelligence platform built with FastAPI, PostgreSQL/PostGIS, React, Leaflet and Chart.js.

Esta edición pública sirve como base técnica para análisis territorial operativo, carga tabular por lotes, dashboard geoespacial y colaboración open source. Incluye código, documentación, pruebas, CI y datos sintéticos mínimos.

**Importante:** este repositorio no incluye datos policiales reales, mapas institucionales privados, capas territoriales reales, GeoJSON/shapefiles/geopackages privados, credenciales ni imágenes con derechos inciertos.

## Why SIGED-PNP?

Los equipos territoriales necesitan convertir registros dispersos en señales operativas: concentración espacial, horarios críticos, evolución temporal, carga por jurisdicción y recomendaciones. SIGED-PNP Community ofrece una base mantenible para construir ese flujo con herramientas abiertas y reglas claras de seguridad de datos.

## Features

- Backend `FastAPI` organizado por `routers`, `services`, `repositories` y `schemas`.
- SQL directo con `psycopg2`, sin ORM.
- Soporte `PostgreSQL + PostGIS`.
- Carga CSV/XLSX por lotes con staging, validación y promoción controlada.
- Autenticación JWT con roles `admin`, `analista` y `consulta`.
- Frontend `React + Vite + Leaflet + Chart.js`.
- Dashboard operacional, analítica temporal, mapa, filtros y recomendaciones.
- Flujo territorial por región, división, comisaría, jurisdicción y sector.
- Pruebas backend/frontend y CI en GitHub Actions.

## Architecture

```text
CSV sintetico
    -> scripts Python o API /cargas/lotes
    -> staging_eventos + lotes_carga
    -> validacion y promocion
    -> eventos_delictivos
    -> FastAPI
    -> React + Leaflet + Chart.js
```

Detalles: [`docs/architecture.md`](docs/architecture.md).

## Public Data Policy

- `database/sample_data/` contiene únicamente datos sintéticos de demostración.
- `salida_geojson/` está ignorado y debe cargarse localmente.
- Cada institución debe aportar sus propias capas territoriales y validar permisos de uso.
- No publiques datos reales, mapas privados, GeoJSON, shapefiles, geopackages, Excel/CSV de origen incierto ni imágenes institucionales dudosas.

Guía completa: [`docs/data-safety.md`](docs/data-safety.md).

## Quickstart

Backend:

```powershell
cd SIGED-PNP-Community\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd SIGED-PNP-Community\frontend
npm ci
npm run dev
```

Base de datos y carga sintética:

```powershell
cd SIGED-PNP-Community
.\backend\.venv\Scripts\python.exe .\scripts\import_csv_lotes.py --input .\database\sample_data\eventos_delictivos_sample.csv --observaciones "Carga sintética inicial"
```

Demo paso a paso: [`docs/demo.md`](docs/demo.md). Base de datos: [`docs/database.md`](docs/database.md).

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

## Documentation

- Demo local: [`docs/demo.md`](docs/demo.md)
- Arquitectura: [`docs/architecture.md`](docs/architecture.md)
- Seguridad de datos: [`docs/data-safety.md`](docs/data-safety.md)
- API y roles: [`docs/api.md`](docs/api.md)
- Base de datos: [`docs/database.md`](docs/database.md)
- Readiness open source: [`docs/open-source-readiness.md`](docs/open-source-readiness.md)
- Checklist GitHub: [`docs/github-publication-checklist.md`](docs/github-publication-checklist.md)
- Issues iniciales sugeridas: [`docs/initial-issues.md`](docs/initial-issues.md)

## Screenshots

No se incluyen capturas con mapas o activos institucionales. Para agregar screenshots:

- Usa solo datos sintéticos.
- Usa mapas/capas propias, sintéticas o explícitamente públicas.
- Verifica que no aparezcan rutas internas, usuarios, coordenadas sensibles ni información operativa real.

## Open Source Status

`v0.2.0-alpha` es una edición pública inicial para evaluación, demo y colaboración técnica. Requiere revisión de seguridad, despliegue y datos antes de cualquier uso operativo real.

## Roadmap

Consulta [`ROADMAP.md`](ROADMAP.md).

## Contributing

Lee [`CONTRIBUTING.md`](CONTRIBUTING.md). Las contribuciones deben respetar la arquitectura por capas, mantener SQL en repositories y evitar cambios no validados en el flujo territorial.

## Security

Reporta vulnerabilidades siguiendo [`SECURITY.md`](SECURITY.md). No abras issues públicos con secretos, tokens, datos reales, rutas internas, coordenadas sensibles o información policial real.

## License

Distribuido bajo licencia [Apache-2.0](LICENSE).
