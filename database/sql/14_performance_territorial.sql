-- archivo: database/sql/14_performance_territorial.sql
\connect siged_pnp;

CREATE INDEX IF NOT EXISTS idx_comisarias_distrito_normalizado
    ON comisarias (distrito_normalizado);

CREATE INDEX IF NOT EXISTS idx_comisarias_id_territorio
    ON comisarias (id_territorio);

CREATE INDEX IF NOT EXISTS idx_comisarias_id_territorio_distrito
    ON comisarias (id_territorio_distrito);

CREATE INDEX IF NOT EXISTS idx_eventos_distrito_normalizado
    ON eventos_delictivos (distrito_normalizado);

CREATE INDEX IF NOT EXISTS idx_eventos_territorio_distrito_fecha
    ON eventos_delictivos (id_territorio_distrito, fecha DESC);

CREATE INDEX IF NOT EXISTS idx_eventos_comisaria_fecha
    ON eventos_delictivos (id_comisaria, fecha DESC)
    WHERE id_comisaria IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_eventos_fecha_hora
    ON eventos_delictivos (fecha DESC, hora DESC);

CREATE INDEX IF NOT EXISTS idx_zonas_id_territorio
    ON zonas_operativas (id_territorio);

CREATE INDEX IF NOT EXISTS idx_zonas_id_territorio_distrito
    ON zonas_operativas (id_territorio_distrito);

CREATE INDEX IF NOT EXISTS idx_zonas_distrito_normalizado
    ON zonas_operativas (distrito_normalizado);

CREATE INDEX IF NOT EXISTS idx_hotspots_distrito_normalizado
    ON hotspots (distrito_normalizado);

CREATE INDEX IF NOT EXISTS idx_hotspots_id_territorio_distrito
    ON hotspots (id_territorio_distrito);

CREATE INDEX IF NOT EXISTS idx_lotes_fecha_inicio_estado
    ON lotes_carga (fecha_inicio DESC, estado_lote);

CREATE OR REPLACE VIEW vw_eventos_territoriales AS
SELECT
    e.id_evento,
    e.fecha,
    e.hora,
    e.id_delito,
    e.id_lote_carga,
    COALESCE(dt.codigo_territorio, 'DIST-' || siged_slug(e.distrito)) AS codigo_distrito,
    COALESCE(dt.nombre_territorio, e.distrito) AS distrito,
    pr.nombre_territorio AS provincia,
    dp.nombre_territorio AS departamento,
    e.id_comisaria,
    c.nombre_comisaria,
    ct.codigo_territorio AS codigo_comisaria,
    e.direccion,
    e.latitud,
    e.longitud,
    e.geom,
    e.fuente_registro,
    e.descripcion
FROM eventos_delictivos e
LEFT JOIN dim_territorios dt
    ON dt.id_territorio = e.id_territorio_distrito
LEFT JOIN dim_territorios pr
    ON pr.id_territorio = dt.id_territorio_padre
LEFT JOIN dim_territorios dp
    ON dp.id_territorio = pr.id_territorio_padre
LEFT JOIN comisarias c
    ON c.id_comisaria = e.id_comisaria
LEFT JOIN dim_territorios ct
    ON ct.id_territorio = c.id_territorio;
