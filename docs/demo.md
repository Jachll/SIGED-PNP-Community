# Demo local

Esta guía permite correr una demo local de SIGED-PNP Community usando solo datos sintéticos.

## Qué incluye la demo

- Backend FastAPI.
- Frontend React/Vite.
- Carga CSV sintética desde `database/sample_data/`.
- Dashboard operacional y vistas de análisis.
- Flujo territorial preparado para capas locales, sin publicar mapas privados.

## Requisitos

- Python 3.13 o compatible.
- Node.js 20 o compatible.
- PostgreSQL con PostGIS.
- `psql` disponible en `PATH`.

## 1. Instalar backend

```powershell
cd SIGED-PNP-Community\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 2. Preparar base de datos

Sigue `docs/database.md` para crear `siged_pnp` y ejecutar las migraciones numeradas en `database/sql/`.

La edición pública no incluye capas territoriales reales. Si no cargas capas locales en PostGIS o `salida_geojson/`, algunas vistas territoriales funcionarán como estructura de demo o fallback, pero no como mapa operativo real.

## 3. Cargar datos sintéticos

```powershell
cd SIGED-PNP-Community
.\backend\.venv\Scripts\python.exe .\scripts\import_csv_lotes.py --input .\database\sample_data\eventos_delictivos_sample.csv --observaciones "Carga sintética inicial"
```

Los archivos de `database/sample_data/` son sintéticos y no contienen información policial real.

## 4. Instalar frontend

```powershell
cd SIGED-PNP-Community\frontend
npm ci
npm run dev
```

Abre la URL local que muestre Vite.

## 5. Vistas a revisar

- Login y sesión por rol.
- Dashboard Operacional.
- Analítica Temporal.
- Analítica Operativa.
- Carga de Datos.
- Estados vacíos o fallbacks cuando no existan capas territoriales locales.

## 6. Validaciones recomendadas

Frontend:

```powershell
cd frontend
npm run lint
npm run test
npm run build
```

Backend:

```powershell
cd backend
python -m compileall app tests scripts ../scripts
python -m pytest
```

Las pruebas con PostgreSQL/PostGIS real se activan con `RUN_DB_INTEGRATION_TESTS=1`.

## Capas territoriales

`salida_geojson/` está ignorado por Git. Cada institución debe cargar sus propias capas localmente y validar permisos, clasificación y anonimización.

No subas al repositorio:

- Mapas privados.
- GeoJSON reales.
- Shapefiles.
- Geopackages.
- Zips de capas.
- Screenshots con información operativa real.

## Limitaciones de la edición pública

- No incluye datos reales.
- No incluye mapas o capas institucionales.
- No incluye configuración productiva.
- No reemplaza una revisión de seguridad, privacidad o cumplimiento.
