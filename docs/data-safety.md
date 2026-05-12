# Seguridad de datos

SIGED-PNP Community es una edición pública limpia. Su regla principal es simple: si no puedes confirmar que un archivo es sintético, público o publicable, no lo agregues.

## No publicar

- Datos policiales reales.
- Mapas institucionales privados.
- `salida_geojson/`.
- GeoJSON reales o privados.
- Shapefiles (`.shp`, `.dbf`, `.prj`, `.cpg`, `.qpj`).
- Geopackages (`.gpkg`).
- Excel/CSV reales o de origen incierto.
- Zips de capas, backups o cargas operativas.
- `.env`, secretos, tokens, logs, uploads, backups, `dist`, `node_modules` o `.venv`.
- Screenshots con coordenadas sensibles, rutas internas, usuarios reales o información operativa.

## Datos sintéticos

Los datos públicos de demo deben vivir en `database/sample_data/` y cumplir estas reglas:

- Nombre claro, por ejemplo `eventos_delictivos_sample.csv`.
- Contenido ficticio.
- Coordenadas sintéticas o irrelevantes.
- Sin nombres de personas.
- Sin direcciones reales sensibles.
- Sin referencias operativas reales.
- Documentados en `database/sample_data/README.md`.

## Manejo de datos locales

Para pruebas institucionales o privadas:

- Usa carpetas ignoradas por Git.
- Mantén `.env` fuera del repositorio.
- Carga capas territoriales desde rutas locales.
- Separa muestras públicas de datos reales.
- Revisa `git status --ignored` antes de cualquier commit.

## Si se subió algo sensible por error

1. No abras más PRs con ese archivo.
2. Pausa el push o release si todavía no se publicó.
3. Notifica al maintainer por canal privado.
4. Elimina el archivo del árbol de trabajo.
5. Si llegó al historial Git, no basta con borrarlo en un commit nuevo.
6. Prepara un repositorio público limpio sin historial sensible o reescribe historial con una herramienta adecuada.
7. Rota credenciales si hubo secretos.

## Recomendación para publicación pública

Si un repositorio pudo contener mapas privados, capas reales, Excel/CSV de origen incierto o credenciales, crea una copia pública limpia sin conservar historial Git anterior. Esta edición Community sigue ese enfoque.
