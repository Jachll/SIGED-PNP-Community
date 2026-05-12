# Arquitectura

SIGED-PNP Community usa una arquitectura cliente-servidor con frontend React y backend FastAPI.

## Vista general

```text
Usuario
  -> React + Vite + Leaflet + Chart.js
  -> frontend/src/services/api.js
  -> FastAPI routers
  -> services
  -> repositories con SQL directo
  -> PostgreSQL/PostGIS
```

Flujo de carga:

```text
CSV sintetico
  -> ETL tabular
  -> staging_eventos + lotes_carga
  -> validacion
  -> promocion
  -> eventos_delictivos
  -> dashboard y analitica
```

## Frontend

El frontend está construido con:

- React.
- Vite.
- Leaflet y React Leaflet.
- Chart.js.

Rutas relevantes:

- `frontend/src/pages/`: vistas principales.
- `frontend/src/components/`: mapa, filtros, overlays y paneles.
- `frontend/src/hooks/`: estado compartido y jerarquía territorial.
- `frontend/src/services/api.js`: cliente HTTP centralizado.

Regla de mantenimiento: no mover llamadas HTTP fuera de `frontend/src/services/api.js`.

## Backend

El backend está organizado por capas:

- `backend/app/api/routers/`: rutas HTTP, dependencias y respuestas.
- `backend/app/services/`: reglas de negocio y orquestación.
- `backend/app/repositories/`: SQL directo con `psycopg2`.
- `backend/app/schemas/`: contratos de entrada y salida.
- `backend/app/etl/`: lectura tabular, validación y asignación territorial.

Reglas de mantenimiento:

- Mantener routers delgados.
- Mantener lógica de negocio en `services`.
- Mantener SQL en `repositories`.
- Mantener contratos en `schemas`.
- No introducir ORM.
- No cambiar endpoints existentes sin discusión previa.

## Base de datos

La base usa PostgreSQL/PostGIS. Los scripts SQL están en `database/sql/` y se ejecutan por orden numérico.

PostGIS permite operar con geometrías territoriales cuando cada instalación carga sus propias capas locales.

## ETL por lotes

El ETL recibe archivos tabulares, normaliza columnas, registra filas en staging y promueve solo registros validados.

Componentes principales:

- `scripts/import_csv_lotes.py`.
- `backend/app/etl/tabular.py`.
- `backend/app/etl/pipeline.py`.
- `backend/app/etl/territorial_assignment.py`.

## Autenticación y roles

La autenticación usa JWT. Los roles principales son:

- `admin`.
- `analista`.
- `consulta`.

Los permisos se validan en backend y se reflejan en frontend.

## Flujo territorial

El flujo territorial contempla:

- Regiones.
- Divisiones.
- Comisarías.
- Jurisdicciones.
- Sectores.

La edición pública mantiene el código para este flujo, pero no publica capas reales. Las capas deben cargarse localmente en PostGIS o en rutas ignoradas por Git.

## Principios del proyecto

- Cambios pequeños y revisables.
- Datos públicos solo si son sintéticos o explícitamente publicables.
- Separación clara entre UI, API, servicios y datos.
- CI como señal mínima de salud del repositorio.
