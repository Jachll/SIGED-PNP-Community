# Seguridad

## Reporte de vulnerabilidades

Por ahora usa un canal privado del maintainer para reportar vulnerabilidades. Si el repositorio público aún no tiene contacto de seguridad configurado, abre un issue sin detalles sensibles solicitando un canal privado de reporte.

Placeholder recomendado: `security@example.org`.

## No incluir en issues públicos

No publiques:

- Secretos, tokens, contraseñas o `.env`.
- Datos policiales reales.
- Coordenadas, rutas, mapas o capas territoriales no públicas.
- Logs con usuarios, IPs, trazas internas o rutas locales.
- Archivos CSV/XLSX/GeoJSON/shapefile/geopackage de origen incierto.
- Detalles explotables de una vulnerabilidad antes de coordinar la corrección.

## Manejo de secretos

- Usa variables de entorno locales.
- Mantén `backend/.env` fuera de Git.
- Configura `JWT_SECRET_KEY` con al menos 32 caracteres en entornos persistentes.
- Mantén `ALLOW_BOOTSTRAP_ADMIN=false` fuera del bootstrap inicial.
- Desactiva documentación interactiva en `staging` y `production`.

## Datos reales

La edición pública no debe contener datos reales. Los datos de ejemplo deben ser sintéticos o anonimizados de forma verificable. Si no puedes demostrarlo, no los publiques.

## Alcance inicial

El alcance inicial cubre:

- Backend FastAPI.
- Autenticación JWT y roles.
- Carga tabular por lotes.
- Integración PostgreSQL/PostGIS.
- Frontend React/Vite.
- Scripts operativos incluidos en el repositorio.

No incluye capas privadas, infraestructura institucional, despliegues de terceros ni datasets externos.
