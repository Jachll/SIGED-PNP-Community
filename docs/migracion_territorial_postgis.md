# Migracion territorial a PostGIS

## Objetivo

Mover la fuente principal de capas territoriales desde archivos GeoJSON locales hacia tablas PostGIS, sin romper la jerarquia que ya consumen Dashboard, Analisis Temporal, Analitica Operativa y los mapas Leaflet.

## Estado por fase

### Fase 1. Base PostGIS

Artefactos principales:

- `database/sql/16_territorio_capas_postgis.sql`
- `backend/scripts/import_territorial_layers_postgis.py`
- `backend/scripts/sync_operational_territorial_catalog.py`

La base territorial queda modelada en:

- `territorio_regiones`
- `territorio_divisiones`
- `territorio_comisarias`
- `territorio_jurisdicciones`
- `territorio_sectores`

Cada tabla conserva:

- PK propia
- FKs jerarquicas
- columnas `geom` y `geom_simplified` cuando aplica
- `source_properties` para trazabilidad del GeoJSON original
- indices GIST y indices de nombres normalizados

### Fase 2. Endpoints backend

Endpoints jerarquicos principales:

- `GET /territorio/regiones`
- `GET /territorio/divisiones?region=...`
- `GET /territorio/comisarias?region=...&division=...`
- `GET /territorio/jurisdicciones?region=...&division=...&comisaria=...`
- `GET /territorio/sectores?region=...&division=...&comisaria=...`

Endpoints GeoJSON por capa:

- `GET /territorio/regiones/geojson`
- `GET /territorio/divisiones/geojson`
- `GET /territorio/comisarias/geojson`
- `GET /territorio/jurisdicciones/geojson`
- `GET /territorio/sectores/geojson`

Compatibilidad temporal:

- `GET /territorio/contexto`
- `GET /territorio/capas`
- `GET /territorio/capas/{layer_id}`
- `GET /capas/geojson/*`

Politica de acceso vigente:

- lectura territorial (`/territorio/contexto`, `/territorio/*/geojson`, `/territorio/capas*` y `/capas/geojson/*`): `admin`, `analista`, `consulta`
- analitica operativa y persistencia: `admin`, `analista`

### Fase 3. Frontend React

La UI mantiene el mismo contrato logico:

- `regions`
- `divisions`
- `comisarias`
- `jurisdicciones`
- `sectores`

La capa de servicios del frontend ya usa:

- endpoints jerarquicos para armar el contexto territorial
- endpoints `GET /territorio/*/geojson` para cargar geometria por capa

Esto evita volver a depender del namespace legado `/capas/geojson/*`.

### Fase 4. Documentacion y cierre de migracion

La migracion no debe considerarse cerrada hasta:

1. ejecutar SQL e importacion sobre una base PostGIS real
2. validar filtros y mapas en las tres vistas operativas
3. comparar resultados entre fuente vieja y fuente nueva
4. retirar el fallback a archivos cuando produccion quede estable

## Componentes deprecated

Deprecated durante la transicion:

- router legado `/capas/geojson/*`
- lectura directa de GeoJSON desde `backend/app/geo_layers.py` como fuente principal
- caches regionales en `salida_geojson/_cache_by_region/` como fuente de runtime

Se mantienen solo como compatibilidad temporal y respaldo operativo.

## Orden recomendado de despliegue

1. Ejecutar `02_enable_postgis.sql` si el entorno aun no tiene PostGIS.
2. Ejecutar `15_etl_asignacion_territorial.sql`.
3. Ejecutar `16_territorio_capas_postgis.sql`.
4. Correr `backend/scripts/import_territorial_layers_postgis.py`.
5. Si hace falta completar o reejecutar solo la sincronizacion operativa oficial sin reimportar capas, correr `backend/scripts/sync_operational_territorial_catalog.py`.
6. Reiniciar backend.
7. Validar endpoints `/territorio/*`.
8. Validar frontend con build y smoke manual.
9. Mantener `/capas/geojson/*` solo hasta terminar la observacion en produccion.

## Validacion minima

### SQL y carga

```powershell
cd "SIGED-PNP-Community"

psql -U postgres -d postgres -f .\database\sql\15_etl_asignacion_territorial.sql
psql -U postgres -d postgres -f .\database\sql\16_territorio_capas_postgis.sql
.\backend\.venv\Scripts\python.exe .\backend\scripts\import_territorial_layers_postgis.py
.\backend\.venv\Scripts\python.exe .\backend\scripts\sync_operational_territorial_catalog.py
```

### Backend

```powershell
cd "SIGED-PNP-Community\backend"
.\.venv\Scripts\python.exe -m pytest tests\test_geo_layers_routes.py tests\test_territorio_routes.py tests\test_territorial_endpoint_contracts.py tests\test_territorial_support.py tests\test_eventos_routes.py tests\test_estadisticas_routes.py tests\test_analisis_routes.py
```

### Frontend

```powershell
cd "SIGED-PNP-Community\frontend"
npm run build
```

### Validacion funcional manual

1. Abrir Dashboard Operacional, Analisis Temporal y Analitica Operativa.
2. Validar cascada `region -> division -> comisaria -> jurisdiccion/sector`.
3. Activar capas de mapa y confirmar que regiones y divisiones cargan rapido.
4. Seleccionar una jurisdiccion o sector y confirmar que el foco usa la geometria completa.
5. Cargar un lote ETL con coordenadas conocidas y verificar la asignacion territorial resultante.
6. Ejecutar `scripts/benchmark_backend.py` para guardar baseline del entorno.
7. Ejecutar `scripts/cleanup_validation_lotes.py SIGED_E2E_SMOKE_QA` para retirar lotes del smoke y validar integridad referencial de cierre.

### Contrato cubierto por pruebas

`tests/test_territorial_endpoint_contracts.py` deja cubiertos:

- contrato de `/territorio/contexto` con jerarquia incompleta y completa
- forwarding de filtros en `/territorio/*/geojson`
- respuestas vacias tipo `FeatureCollection`
- rechazo controlado de scopes incompletos
- fallback controlado a listas vacias cuando la resolucion de jurisdicciones/sectores falla
- `403` explicito para roles fuera de politica

## Decisiones de cierre

Estado definido el 9 de abril de 2026:

- `GET /territorio/contexto` queda como endpoint estable de conveniencia. No se marca deprecated en esta fase.
- `/capas/geojson/*` queda formalmente deprecated desde el 9 de abril de 2026.
- La fecha objetivo de retiro de `/capas/geojson/*` queda fijada para el 30 de abril de 2026, condicionada a que no aparezcan regresiones en produccion.
- El fallback a archivos en `backend/app/geo_layers.py` queda solo como contingencia operativa hasta el 15 de mayo de 2026. Despues de esa fecha debe retirarse si la fuente PostGIS sigue estable.
- El siguiente paso de optimizacion aprobado es activar `bbox` desde frontend. No bloquea el cierre de esta migracion, pero queda como siguiente iteracion tecnica despues del 15 de mayo de 2026 o antes si se prioriza rendimiento por viewport.
- los endpoints territoriales de lectura quedan habilitados para `consulta`; no se extiende ese permiso a `analisis/*`, `recomendaciones/*` ni `cargas/*`

## Estado final del cierre

Checklist 9 queda cerrado con esta politica:

- ruta nueva estable: `/territorio/*`
- endpoint de conveniencia estable: `/territorio/contexto`
- ruta legacy deprecated: `/capas/geojson/*`
- fuente principal de runtime: PostGIS
- siguiente mejora aprobada: `bbox` desde frontend

## Checklist 10. Rollback y observacion

Checklist 10 queda cerrado con estas garantias, vigentes desde el 9 de abril de 2026:

- `/capas/geojson/*` sigue habilitado durante la ventana de observacion.
- `salida_geojson/` y `salida_geojson/_cache_by_region/` no deben eliminarse antes del 15 de mayo de 2026.
- El backend puede forzar temporalmente la fuente legacy con `GEO_LAYERS_FORCE_LEGACY=true`.
- Cualquier diferencia funcional detectada durante la observacion debe registrarse antes de retirar compatibilidad.

### Rollback operativo temporal

Usar este rollback solo si falla la fuente territorial PostGIS y la base principal sigue disponible. No reemplaza un plan de contingencia ante caida total de PostgreSQL.

1. Editar `backend/.env` y fijar `GEO_LAYERS_FORCE_LEGACY=true`.
2. Reiniciar el backend.
3. Validar al menos:
   - `GET /territorio/capas`
   - `GET /territorio/contexto`
   - `GET /capas/geojson/contexto`
4. Mantener el frontend apuntando al mismo backend. Los endpoints `/territorio/*` seguiran respondiendo, pero servidos desde GeoJSON local.
5. Registrar en la bitacora operativa cualquier diferencia de conteo, nombres, geometria o rendimiento observada durante el incidente.
6. Cuando la fuente PostGIS quede estable otra vez, volver a `GEO_LAYERS_FORCE_LEGACY=false`, reiniciar backend y repetir las validaciones minimas.

### Diferencias registradas al cierre

Al 9 de abril de 2026 no se detectaron diferencias funcionales en:

- conteos por capa
- nombres expuestos al frontend
- geometria validada en los spot-checks de control

La unica diferencia observada fue positiva para PostGIS:

- menor tiempo de respuesta
- menor payload en capas pesadas

## Troubleshooting territorial

### La region se dibuja sin marcar checkbox

Revisar:

- `GeoBoundaryLayerOverlays` no debe renderizar `focusLayer` si la capa no esta en `visibleLayers`.
- El filtro territorial no debe modificar `selectedLayerIds`.
- El foco del mapa debe tratarse como contexto temporal y no como overlay persistente.

### Al seleccionar comisaria desaparecen los puntos

Revisar:

- El request debe conservar `region`, `division`, `comisaria` e `id_comisaria` coherentes.
- El backend no debe aplicar `eventos_delictivos.id_comisaria = id_comisaria` cuando ya existe alcance territorial.
- La geometria de jurisdicciones o sectores debe usarse como filtro espacial cuando corresponda.

### Jurisdiccion o sector muestra loading aunque solo enfoca

Revisar:

- `isLoading` solo debe activarse si la capa esta seleccionada y no existe geometria renderizable.
- `isRefreshing` debe representar refrescos sobre geometria ya disponible.
- La clave de retencion no debe invalidar la geometria general por elegir un elemento puntual de la misma capa.

### Forzar fallback legacy temporal

Si PostGIS presenta una incidencia y necesitas mantener operativo el frontend:

1. Fijar `GEO_LAYERS_FORCE_LEGACY=true` en `backend/.env`.
2. Reiniciar backend.
3. Validar `GET /territorio/capas`, `GET /territorio/contexto` y `GET /capas/geojson/contexto`.
4. Registrar diferencias funcionales o de rendimiento antes de volver a PostGIS.
