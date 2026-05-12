# Prioridad 3 Backend: Modelo Territorial, Performance y Observabilidad

## 1. Aplicar migraciones incrementales

Ejecutar despues de `12_staging_estado_duplicado.sql`:

```powershell
psql -U postgres -d postgres -f .\database\sql\13_dim_territorio.sql
psql -U postgres -d postgres -f .\database\sql\14_performance_territorial.sql
```

Estas migraciones:

- crean `dim_territorios` y `territorio_aliases`
- agregan columnas normalizadas y FKs territoriales en `comisarias`, `eventos_delictivos`, `zonas_operativas` y `hotspots`
- crean la vista `vw_territorial_inconsistencias`
- crean la vista `vw_eventos_territoriales`
- agregan indices para filtros territoriales, fechas, comisarias y lotes

## 2. Migracion y refresco de datos existentes

`13_dim_territorio.sql` ya ejecuta un primer:

```sql
SELECT siged_refresh_territorial_dimension();
```

Usar ese mismo refresco cuando:

- se carguen nuevos distritos por ETL
- se editen comisarias
- se registren nuevas zonas operativas o jurisdicciones

Validacion recomendada despues del refresco:

```sql
SELECT *
FROM vw_territorial_inconsistencias;
```

Si la consulta devuelve filas, existen registros con distrito inconsistente respecto a su comisaria o zona relacionada.

## 3. Compatibilidad y criterio de jerarquia

La jerarquia queda soportada en una sola dimension:

- `PAIS`
- `DEPARTAMENTO`
- `PROVINCIA`
- `DISTRITO`
- `JURISDICCION_POLICIAL`
- `COMISARIA`
- `ZONA_OPERATIVA` / `SECTOR`

Para no romper ETAPA 2:

- `distrito` se conserva
- se agrega `distrito_normalizado` para filtros e indices
- se agrega `id_territorio_distrito` como clave de join robusta
- `id_comisaria` y `id_zona` siguen vigentes

Los distritos historicos se cargan bajo una provincia y departamento `NO DEFINIDA` hasta que exista un catalogo institucional mas completo. Esto evita migraciones destructivas y deja una ruta clara para ubigeo o catalogos PNP posteriores.

## 4. Baseline simple de rendimiento

Script operativo:

```powershell
cd "SIGED-PNP-Community"
.\backend\.venv\Scripts\python.exe .\scripts\benchmark_backend.py --iterations 3
```

Consulta y mide:

- `eventos_listado`
- `eventos_heatmap`
- `estadisticas_por_dia`
- `analisis_agregados_espaciales`
- `analisis_zonas_criticas_distrito`
- `analisis_hotspots`
- `recomendaciones_patrullaje`

Salida:

- resumen por consola
- reporte JSON en `scripts/logs/perf_baseline_YYYYMMDD_HHMMSS.json`

## 4.1 QA real asociado a scripts

Los scripts de QA no quedan huerfanos:

- `benchmark_backend.py` forma parte del flujo real de validacion manual con base activa y del CI como verificacion de contrato CLI (`--help`).
- `cleanup_validation_lotes.py` se usa para cerrar el smoke funcional de cargas y tambien queda validado en CI por su contrato CLI (`--help`).
- el workflow `.github/workflows/backend-ci.yml` sigue ejecutando `pytest` completo y ahora valida que ambos entrypoints existan y arranquen correctamente.

Secuencia recomendada en QA con base activa:

```powershell
cd "SIGED-PNP-Community"
.\backend\.venv\Scripts\python.exe .\scripts\benchmark_backend.py --iterations 3
.\backend\.venv\Scripts\python.exe .\scripts\cleanup_validation_lotes.py SIGED_E2E_SMOKE_QA
```

## 5. Nota operativa

Despues de aplicar migraciones territoriales, reiniciar el backend para limpiar caches de introspeccion de esquema y reabrir el pool de conexiones con el nuevo modelo.
