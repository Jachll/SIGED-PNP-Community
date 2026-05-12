# Open Source Readiness

Checklist de madurez para SIGED-PNP Community.

## Estado actual

- [x] Copia pública sin historial Git anterior.
- [x] Datos de ejemplo sintéticos.
- [x] `salida_geojson/` ignorado.
- [x] Licencia open source.
- [x] Guía de contribución.
- [x] Política de seguridad inicial.
- [x] Roadmap público.
- [x] Changelog inicial.
- [x] Templates de issues y pull requests.
- [x] CI backend/frontend.

## Antes de publicar

- [ ] Revisar `git ls-files` antes del primer push.
- [ ] Confirmar que no hay `.env`, logs, uploads, backups, `.venv`, `node_modules` ni `dist`.
- [ ] Confirmar que no hay Excel/CSV reales o de origen incierto.
- [ ] Confirmar que no hay GeoJSON, shapefiles, geopackages ni capas territoriales privadas.
- [ ] Confirmar que no hay imágenes institucionales con derechos inciertos.
- [ ] Configurar descripción y topics del repositorio.
- [ ] Crear release `v0.2.0-alpha`.
- [ ] Verificar CI verde en GitHub.

## Reglas de datos

Si no puedes confirmar que un archivo es sintético, público o publicable, no lo agregues al repositorio.
