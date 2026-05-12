# Open Source Readiness

Checklist de madurez para SIGED-PNP Community.

## Estado actual

- [x] Copia pública sin historial Git anterior.
- [x] Datos de ejemplo sintéticos.
- [x] `salida_geojson/` ignorado.
- [x] Licencia open source.
- [x] `SECURITY.md` presente.
- [x] `CONTRIBUTING.md` presente.
- [x] `ROADMAP.md` presente.
- [x] `CHANGELOG.md` presente.
- [x] Guía de contribución.
- [x] Política de seguridad inicial.
- [x] Roadmap público.
- [x] Changelog inicial.
- [x] Templates de issues y pull requests.
- [x] CI backend/frontend.
- [x] Checklist de seguridad de datos.
- [x] Guía de demo local.
- [x] Guía de arquitectura.
- [x] Sin secretos versionados detectados.
- [x] Sin mapas privados versionados detectados.

## Antes de publicar

- [x] Revisar `git ls-files` antes del primer push.
- [x] Confirmar que no hay `.env`, logs, uploads, backups, `.venv`, `node_modules` ni `dist`.
- [x] Confirmar que no hay Excel/CSV reales o de origen incierto.
- [x] Confirmar que no hay GeoJSON, shapefiles, geopackages ni capas territoriales privadas.
- [x] Confirmar que no hay imágenes institucionales con derechos inciertos.
- [ ] Configurar descripción y topics del repositorio.
- [ ] Crear release `v0.2.0-alpha`.
- [ ] Verificar CI verde en GitHub.
- [ ] Crear issues iniciales.
- [ ] Configurar branch protection, si aplica.
- [ ] Agregar screenshots sintéticos, si son seguros.

## Reglas de datos

Si no puedes confirmar que un archivo es sintético, público o publicable, no lo agregues al repositorio.
