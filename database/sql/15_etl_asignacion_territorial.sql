-- archivo: database/sql/15_etl_asignacion_territorial.sql
\connect siged_pnp;

ALTER TABLE comisarias
    ADD COLUMN IF NOT EXISTS codigo_cpnp VARCHAR(20),
    ADD COLUMN IF NOT EXISTS codigo_unidad VARCHAR(20),
    ADD COLUMN IF NOT EXISTS region_policial VARCHAR(120),
    ADD COLUMN IF NOT EXISTS division_policial VARCHAR(150),
    ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);

CREATE UNIQUE INDEX IF NOT EXISTS uq_comisarias_codigo_cpnp
    ON comisarias (codigo_cpnp);

CREATE INDEX IF NOT EXISTS idx_comisarias_geom_gist
    ON comisarias
    USING GIST (geom)
    WHERE geom IS NOT NULL;

ALTER TABLE staging_eventos
    ADD COLUMN IF NOT EXISTS id_comisaria_original SMALLINT,
    ADD COLUMN IF NOT EXISTS id_comisaria_resuelta SMALLINT,
    ADD COLUMN IF NOT EXISTS nombre_comisaria_resuelta VARCHAR(150),
    ADD COLUMN IF NOT EXISTS estado_territorial VARCHAR(50) NOT NULL DEFAULT 'SIN_EVALUAR',
    ADD COLUMN IF NOT EXISTS regla_territorial VARCHAR(50),
    ADD COLUMN IF NOT EXISTS motivo_territorial TEXT,
    ADD COLUMN IF NOT EXISTS conflicto_territorial BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE staging_eventos
    DROP CONSTRAINT IF EXISTS chk_staging_estado_territorial;

ALTER TABLE staging_eventos
    ADD CONSTRAINT chk_staging_estado_territorial
        CHECK (
            estado_territorial IN (
                'SIN_EVALUAR',
                'ASIGNADO_POR_JURISDICCION',
                'ASIGNADO_POR_SECTOR',
                'SIN_COINCIDENCIA_TERRITORIAL',
                'COORDENADAS_INVALIDAS',
                'COORDENADAS_INCOMPLETAS',
                'CONFLICTO_ID_COMISARIA_VS_GEOMETRIA'
            )
        );

CREATE INDEX IF NOT EXISTS idx_staging_lote_estado_territorial
    ON staging_eventos (id_lote, estado_territorial);

CREATE INDEX IF NOT EXISTS idx_staging_lote_conflicto_territorial
    ON staging_eventos (id_lote, conflicto_territorial);
