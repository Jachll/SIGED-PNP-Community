import logging

from app.database import get_cursor

logger = logging.getLogger("siged.startup")

TERRITORIAL_TRIGGER_REPAIR_SQL = """
CREATE OR REPLACE FUNCTION siged_validate_territorial_consistency()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_new_data JSONB;
    v_comisaria_distrito_id BIGINT;
    v_zona_distrito_id BIGINT;
    v_id_comisaria BIGINT;
    v_id_zona BIGINT;
    v_id_territorio_distrito BIGINT;
BEGIN
    v_new_data := to_jsonb(NEW);
    v_id_comisaria := NULLIF(v_new_data ->> 'id_comisaria', '')::BIGINT;
    v_id_zona := NULLIF(v_new_data ->> 'id_zona', '')::BIGINT;
    v_id_territorio_distrito := NULLIF(v_new_data ->> 'id_territorio_distrito', '')::BIGINT;

    IF TG_TABLE_NAME = 'eventos_delictivos' THEN
        IF v_id_comisaria IS NOT NULL THEN
            SELECT c.id_territorio_distrito
            INTO v_comisaria_distrito_id
            FROM comisarias c
            WHERE c.id_comisaria = v_id_comisaria
            LIMIT 1;

            IF v_comisaria_distrito_id IS NOT NULL THEN
                IF v_id_territorio_distrito IS NULL THEN
                    NEW.id_territorio_distrito := v_comisaria_distrito_id;
                ELSIF v_id_territorio_distrito <> v_comisaria_distrito_id THEN
                    RAISE EXCEPTION 'El distrito del evento no coincide con la comisaria %', v_id_comisaria;
                END IF;
            END IF;
        END IF;
    ELSIF TG_TABLE_NAME = 'zonas_operativas' THEN
        IF v_id_comisaria IS NOT NULL THEN
            SELECT c.id_territorio_distrito
            INTO v_comisaria_distrito_id
            FROM comisarias c
            WHERE c.id_comisaria = v_id_comisaria
            LIMIT 1;

            IF v_comisaria_distrito_id IS NOT NULL
               AND v_id_territorio_distrito IS NOT NULL
               AND v_id_territorio_distrito <> v_comisaria_distrito_id THEN
                RAISE EXCEPTION 'La zona operativa no coincide con el distrito de la comisaria %', v_id_comisaria;
            END IF;
        END IF;
    ELSIF TG_TABLE_NAME = 'hotspots' THEN
        IF v_id_zona IS NOT NULL THEN
            SELECT z.id_territorio_distrito
            INTO v_zona_distrito_id
            FROM zonas_operativas z
            WHERE z.id_zona = v_id_zona
            LIMIT 1;

            IF v_zona_distrito_id IS NOT NULL THEN
                IF v_id_territorio_distrito IS NULL THEN
                    NEW.id_territorio_distrito := v_zona_distrito_id;
                ELSIF v_id_territorio_distrito <> v_zona_distrito_id THEN
                    RAISE EXCEPTION 'El distrito del hotspot no coincide con la zona %', v_id_zona;
                END IF;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;
"""


def ensure_database_repairs() -> None:
    try:
        with get_cursor() as cur:
            cur.execute(TERRITORIAL_TRIGGER_REPAIR_SQL)
        logger.info("Funcion territorial siged_validate_territorial_consistency verificada en startup")
    except Exception:
        logger.exception("No se pudo verificar la compatibilidad del trigger territorial en startup")
