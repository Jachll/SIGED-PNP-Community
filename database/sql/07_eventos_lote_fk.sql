-- archivo: database/sql/07_eventos_lote_fk.sql
\connect siged_pnp;

ALTER TABLE eventos_delictivos
    ADD COLUMN IF NOT EXISTS id_lote_carga BIGINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_eventos_lote_carga'
    ) THEN
        ALTER TABLE eventos_delictivos
            ADD CONSTRAINT fk_eventos_lote_carga
            FOREIGN KEY (id_lote_carga)
            REFERENCES lotes_carga (id_lote);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_eventos_id_lote_carga
    ON eventos_delictivos (id_lote_carga);
