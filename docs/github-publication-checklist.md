# Checklist de publicación en GitHub

Acciones manuales recomendadas para el repositorio público.

## Metadata del repositorio

- [ ] Agregar descripción:

```text
Open-source geospatial crime intelligence platform built with FastAPI, PostgreSQL/PostGIS, React, Leaflet and Chart.js.
```

- [ ] Agregar topics:

```text
fastapi
postgis
react
leaflet
geospatial
crime-analysis
public-safety
dashboard
etl
open-source
```

## Release

- [ ] Verificar que Actions esté en verde.
- [ ] Crear release `v0.2.0-alpha`.
- [ ] Resumir que es una edición pública con datos sintéticos.
- [ ] Aclarar que no incluye mapas privados ni capas reales.

## Issues iniciales

- [ ] Crear issues desde `docs/initial-issues.md`.
- [ ] Etiquetar issues por área: `backend`, `frontend`, `docs`, `security`, `good first issue`, `help wanted`.

## Screenshots

- [ ] Agregar screenshots solo si usan datos sintéticos.
- [ ] Verificar que no aparezcan mapas privados.
- [ ] Verificar que no aparezcan coordenadas sensibles.
- [ ] Verificar que no aparezcan rutas internas, usuarios reales ni información operativa.

## Seguridad del repositorio

- [ ] Revisar `git ls-files` antes de publicar:

```powershell
git ls-files
```

- [ ] Confirmar que no hay `.env`, logs, uploads, backups, `.venv`, `node_modules` ni `dist`.
- [ ] Confirmar que no hay Excel/CSV reales o de origen incierto.
- [ ] Confirmar que no hay GeoJSON, shapefiles, geopackages ni zips de capas.
- [ ] Confirmar que solo existen datos sintéticos en `database/sample_data/`.

## Protección de rama

- [ ] Configurar branch protection para `main`, si aplica.
- [ ] Requerir CI verde antes de merge, si aplica.
- [ ] Requerir PR review para cambios sensibles, si aplica.
