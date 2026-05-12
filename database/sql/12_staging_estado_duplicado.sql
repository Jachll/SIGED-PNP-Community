-- archivo: database/sql/12_staging_estado_duplicado.sql
\connect siged_pnp;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'staging_eventos'
    ) THEN
        ALTER TABLE staging_eventos
            DROP CONSTRAINT IF EXISTS chk_staging_estado;

        ALTER TABLE staging_eventos
            ADD CONSTRAINT chk_staging_estado
            CHECK (
                estado_registro IN (
                    'PENDIENTE',
                    'VALIDO',
                    'ERROR_VALIDACION',
                    'PROMOVIDO',
                    'ERROR_PROMOCION',
                    'ERROR_DUPLICADO'
                )
            );
    END IF;
END $$;
