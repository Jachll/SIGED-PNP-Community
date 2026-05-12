-- archivo: database/sql/04_indexes.sql
\connect siged_pnp;

CREATE INDEX IF NOT EXISTS idx_eventos_fecha
    ON eventos_delictivos (fecha);

CREATE INDEX IF NOT EXISTS idx_eventos_id_delito
    ON eventos_delictivos (id_delito);

CREATE INDEX IF NOT EXISTS idx_eventos_distrito
    ON eventos_delictivos (distrito);

CREATE INDEX IF NOT EXISTS idx_eventos_fecha_delito
    ON eventos_delictivos (fecha, id_delito);

CREATE INDEX IF NOT EXISTS idx_eventos_geom_gist
    ON eventos_delictivos
    USING GIST (geom);
