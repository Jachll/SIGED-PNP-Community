# AGENTS.md

Guia operativa para agentes y colaboradores que trabajen en `SIGED-PNP`.

## 1. Objetivo del repositorio

`SIGED-PNP` es un sistema de inteligencia geoespacial del delito para la instituciones territoriales. El proyecto combina:

- backend `FastAPI` con arquitectura por capas
- base `PostgreSQL 18 + PostGIS`
- frontend `React + Vite + Leaflet + Chart.js`
- scripts Python para carga, limpieza y soporte operativo

El trabajo debe priorizar estabilidad operativa, claridad de cambios y compatibilidad con el flujo territorial ya documentado.

## 2. Estructura que debes respetar

- `backend/app/api/routers/`: rutas HTTP, validacion superficial y respuesta
- `backend/app/services/`: casos de uso y orquestacion
- `backend/app/repositories/`: SQL y acceso a datos con `psycopg2`
- `backend/app/schemas/`: contratos de entrada y salida
- `frontend/src/pages/`: vistas de nivel pagina
- `frontend/src/components/`: componentes reutilizables
- `frontend/src/hooks/`: logica compartida de React
- `frontend/src/services/`: acceso HTTP y helpers de integracion
- `database/sql/`: scripts SQL numerados y ordenados por despliegue
- `scripts/`: utilidades operativas y QA local

No introduzcas ORM ni muevas logica SQL fuera de `repositories/` sin una razon fuerte.

## 3. Comandos base de trabajo

### Backend

Desde `backend/`:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Pruebas backend:

```powershell
cd backend
pytest
```

Chequeo rapido de compilacion:

```powershell
cd backend
python -m compileall app tests ../scripts
```

### Frontend

Desde `frontend/`:

```powershell
npm ci
npm run dev
```

Validaciones frontend:

```powershell
cd frontend
npm run lint
npm run test
npm run build
```

Chequeo conjunto del frontend:

```powershell
cd frontend
npm run check
```

### Arranque rapido en Windows

Desde la raiz:

```powershell
.\start-dev.ps1
```

## 4. Regla de validacion por tipo de cambio

- Si tocas `backend/`, corre al menos `cd backend && pytest`.
- Si tocas `frontend/src/`, corre al menos `cd frontend && npm run build`.
- Si tocas componentes, hooks, utilidades o auth del frontend, intenta tambien `cd frontend && npm run test`.
- Si tocas scripts Python en `scripts/` o `backend/scripts/`, corre `python -m compileall app tests ../scripts` desde `backend/`.
- Si cambias flujos territoriales o despliegue, revisa `docs/migracion_territorial_postgis.md` y `docs/backend_release_checklist.md`.
- Si cambias UX territorial del mapa, valida runtime real ademas de build: region sin checkbox, jurisdiccion/sector con foco, y comisaria con puntos de incidencia visibles.

## 5. Archivos y salidas que no deben entrar en commits

Nunca agregues al repo archivos locales o generados como:

- `backend/.env`
- `backend/.venv/`
- `backend/uploads/`
- `backend/*.log`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/test-results/`
- `frontend/runtime-artifacts/`
- `scripts/logs/`
- `database/backups/`
- `salida_geojson/`
- archivos `.env` locales
- Excel/CSV reales o de origen incierto
- GeoJSON, shapefiles o geopackages privados
- imágenes institucionales con derechos inciertos

Importante: `salida_geojson/` existe como respaldo operativo y fuente legacy temporal. No lo borres ni lo regenres sin revisar primero la documentacion territorial.

## 6. Convenciones de implementacion

### Backend

- Mantener routers delgados.
- Mover reglas de negocio a `services/`.
- Mantener SQL y acceso a base en `repositories/`.
- Reutilizar `schemas/` para contratos claros.
- Respetar variables de entorno ya definidas en `backend/.env.example`.

### Frontend

- Mantener acceso HTTP centralizado en `frontend/src/services/api.js` y `apiBase.js`.
- Evitar duplicar logica de filtros, viewport o jerarquia territorial; revisar primero `hooks/` y `utils/`.
- Mantener separacion entre paginas, componentes y estado local.
- Mantener desacoplados seleccion territorial, checkbox de capa visible, foco del mapa, loading de geometria y puntos de incidencia.
- El checkbox debe ser la unica fuente de verdad para renderizar delimitaciones persistentes; el foco temporal no debe activar overlays visibles por si solo.
- No muestres loading de capa visible si solo se esta refrescando o enfocando con geometria renderizable ya disponible.

### Base de datos y territorial

- Los scripts de `database/sql/` tienen orden numerico de despliegue y no deben reordenarse arbitrariamente.
- Si agregas SQL nuevo, sigue la numeracion existente y documenta el impacto.
- Antes de tocar runtime territorial o fallbacks GeoJSON, valida impacto en migracion y rollback.
- Cuando exista alcance territorial (`region`, `division`, `comisaria`, `jurisdiccion`, `sector`), evita tratar IDs de catalogo operativo como filtros directos de `eventos_delictivos.id_comisaria` sin comprobar su semantica.
- Para comisarias, usa geometria territorial de jurisdicciones o sectores como alcance espacial cuando corresponda; no asumas que la capa de comisarias contiene poligonos.

## 7. Seguridad y configuracion

- Nunca commits secretos ni valores reales en `.env`.
- `ALLOW_BOOTSTRAP_ADMIN=true` solo debe usarse temporalmente para bootstrap inicial.
- `ENABLE_API_DOCS=true` es aceptable en desarrollo, no debe asumirse para entornos productivos.
- Si cambias auth, roles o permisos, revisa backend y frontend juntos.

## 8. Criterio de cambios

- Prefiere cambios pequenos, localizados y faciles de validar.
- Si cambias comportamiento visible, actualiza tambien documentacion relevante.
- Si una decision afecta despliegue, datos territoriales o seguridad, documenta el riesgo y la forma de verificarlo.
- Antes de cerrar una tarea, deja claro que validaste y que no pudiste validar.

## 9. Documentos de referencia del proyecto

- `README.md`
- `docs/migracion_territorial_postgis.md`
- `docs/backend_release_checklist.md`
- `backend/.env.example`
- `.github/workflows/backend-ci.yml`

## 10. Nota para futuros agentes

Este repositorio es Windows-first para desarrollo local, pero el CI corre en Ubuntu. Evita depender de rutas locales fijas, shells no portables o pasos manuales no documentados si el cambio va a terminar en integracion continua.
