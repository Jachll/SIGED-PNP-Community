# Base de datos y migraciones

Guía de base `PostgreSQL 18 + PostGIS`, orden de migraciones, variables de entorno y carga territorial para `SIGED-PNP Community`.

## Requisitos

- PostgreSQL 18
- PostGIS habilitado para PostgreSQL 18
- `psql` disponible en `PATH`

Si `psql` no se reconoce:

```powershell
$env:Path += ";C:\Program Files\PostgreSQL\18\bin"
psql --version
```

## Base objetivo

- Nombre de base: `siged_pnp`

## Orden de migraciones

Desde la raiz del proyecto:

```powershell
cd "SIGED-PNP-Community"
psql -U postgres -d postgres -f .\database\sql\01_create_database.sql
psql -U postgres -d postgres -f .\database\sql\02_enable_postgis.sql
psql -U postgres -d postgres -f .\database\sql\03_schema.sql
psql -U postgres -d postgres -f .\database\sql\04_indexes.sql
psql -U postgres -d postgres -f .\database\sql\05_seed_catalogs.sql
psql -U postgres -d postgres -f .\database\sql\06_lotes_staging.sql
psql -U postgres -d postgres -f .\database\sql\07_eventos_lote_fk.sql
psql -U postgres -d postgres -f .\database\sql\08_zonas_operativas.sql
psql -U postgres -d postgres -f .\database\sql\09_hotspots.sql
psql -U postgres -d postgres -f .\database\sql\10_recomendaciones_patrullaje.sql
psql -U postgres -d postgres -f .\database\sql\11_auth_minima.sql
psql -U postgres -d postgres -f .\database\sql\12_staging_estado_duplicado.sql
psql -U postgres -d postgres -f .\database\sql\13_dim_territorio.sql
psql -U postgres -d postgres -f .\database\sql\14_performance_territorial.sql
psql -U postgres -d postgres -f .\database\sql\15_etl_asignacion_territorial.sql
psql -U postgres -d postgres -f .\database\sql\16_territorio_capas_postgis.sql
```

Nota:

- `02_enable_postgis.sql` y los scripts siguientes usan `\connect siged_pnp`.

## Catalogo de scripts SQL

| Script | Proposito |
| --- | --- |
| `01_create_database.sql` | Crea la base `siged_pnp` si no existe. |
| `02_enable_postgis.sql` | Habilita la extension PostGIS. |
| `03_schema.sql` | Crea `delitos`, `comisarias` y `eventos_delictivos`. |
| `04_indexes.sql` | Crea indices base. |
| `05_seed_catalogs.sql` | Inserta catalogos iniciales. |
| `06_lotes_staging.sql` | Crea `lotes_carga` y `staging_eventos`. |
| `07_eventos_lote_fk.sql` | Relaciona eventos finales con lote de origen. |
| `08_zonas_operativas.sql` | Crea zonas operativas. |
| `09_hotspots.sql` | Crea tabla de hotspots. |
| `10_recomendaciones_patrullaje.sql` | Crea recomendaciones de patrullaje. |
| `11_auth_minima.sql` | Crea roles y usuarios para auth. |
| `12_staging_estado_duplicado.sql` | Ajusta estados de staging y duplicados. |
| `13_dim_territorio.sql` | Crea dimension territorial y vistas relacionadas. |
| `14_performance_territorial.sql` | Aplica optimizaciones e indices territoriales. |
| `15_etl_asignacion_territorial.sql` | Soporta asignacion territorial desde ETL. |
| `16_territorio_capas_postgis.sql` | Crea tablas PostGIS `territorio_*`. |

## Esquema funcional

Tablas base:

- `delitos`
- `comisarias`
- `eventos_delictivos`

Tablas operativas ETAPA 2:

- `lotes_carga`
- `staging_eventos`
- `zonas_operativas`
- `hotspots`
- `recomendaciones_patrullaje`
- `auth_roles`
- `auth_usuarios`

Tablas y vistas territoriales:

- `dim_territorios`
- `territorio_aliases`
- `territorio_regiones`
- `territorio_divisiones`
- `territorio_comisarias`
- `territorio_jurisdicciones`
- `territorio_sectores`
- `vw_territorial_inconsistencias`
- `vw_eventos_territoriales`

## Variables de entorno relevantes

Archivo base:

- [`backend/.env.example`](../backend/.env.example)

Variables principales:

```env
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=siged_pnp
DB_USER=postgres
DB_PASSWORD=
DB_CONNECT_TIMEOUT_SECONDS=5
DB_STATEMENT_TIMEOUT_MS=15000
DB_LOCK_TIMEOUT_MS=3000
DB_IDLE_IN_TRANSACTION_TIMEOUT_MS=10000
DB_POOL_MIN_SIZE=1
DB_POOL_MAX_SIZE=10
DB_APPLICATION_NAME=siged-pnp-backend
# Opcional. Si se omite, el backend usa ../salida_geojson desde backend/.
# GEOJSON_LAYERS_DIR=../salida_geojson
GEO_LAYERS_FORCE_LEGACY=false
```

Notas:

- `DB_PASSWORD` debe estar configurado en `staging` y `production`.
- `GEOJSON_LAYERS_DIR` debe apuntar a una carpeta local ignorada si se usa fallback legacy.
- `GEO_LAYERS_FORCE_LEGACY=true` fuerza temporalmente la fuente territorial legacy.
- El repositorio público no incluye capas territoriales reales, GeoJSON privados, shapefiles ni geopackages.

## Importacion territorial a PostGIS

Despues de ejecutar `16_territorio_capas_postgis.sql`:

```powershell
cd "SIGED-PNP-Community"
.\backend\.venv\Scripts\python.exe .\backend\scripts\import_territorial_layers_postgis.py
```

Para omitir sincronizacion operativa:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\scripts\import_territorial_layers_postgis.py --skip-operational-sync
```

Para sincronizar catalogo operativo sin reimportar capas:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\scripts\sync_operational_territorial_catalog.py
```

Para una sola region:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\scripts\sync_operational_territorial_catalog.py --region "REGION DEMO NORTE"
```

## Carga de datos de ejemplo

Script oficial:

- [`scripts/import_csv_lotes.py`](../scripts/import_csv_lotes.py)

Ejemplo:

```powershell
cd "SIGED-PNP-Community"
.\backend\.venv\Scripts\python.exe .\scripts\import_csv_lotes.py --input .\database\sample_data\eventos_delictivos_sample.csv --observaciones "Carga inicial"
```

Archivos de muestra sintéticos:

- `database/sample_data/eventos_delictivos_sample.csv`
- `database/sample_data/eventos_invalidos_prueba.csv`

Estos archivos no contienen información policial real. No publiques archivos tabulares de origen incierto.

## Capas territoriales

La carpeta `salida_geojson/` está ignorada por Git. Cada institución debe cargar localmente sus propias capas territoriales y validar permisos, clasificación y anonimización antes de usarlas.

No publiques en este repositorio:

- GeoJSON reales o privados.
- Shapefiles (`.shp`, `.dbf`, `.prj`, `.cpg`, `.qpj`).
- Geopackages (`.gpkg`).
- Zips de capas o backups.
- Mapas institucionales o activos visuales con derechos inciertos.

## Validacion minima

Despues de migrar e importar capas:

```powershell
cd "SIGED-PNP-Community\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest tests\test_migration_smoke.py tests\test_migration_integration.py tests\test_territorio_routes.py tests\test_geo_layers_routes.py
```

Validaciones utiles:

- `GET /health`
- `GET /territorio/regiones`
- `GET /territorio/regiones/geojson`
- `GET /auth/roles`

## Referencias

- API y auth: [`docs/api.md`](api.md)
- Runbook territorial: [`docs/migracion_territorial_postgis.md`](migracion_territorial_postgis.md)
- Release backend: [`docs/backend_release_checklist.md`](backend_release_checklist.md)
