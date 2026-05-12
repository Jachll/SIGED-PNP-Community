from typing import Any

from app.database import get_cursor
from app.repositories.query_utils import get_existing_tables

CARGAS_TABLE_NAMES = ("lotes_carga", "staging_eventos")

INSERT_LOTE_SQL = """
    INSERT INTO lotes_carga (
        nombre_archivo,
        ruta_archivo,
        estado_lote,
        observaciones
    ) VALUES (%s, %s, 'PROCESANDO', %s)
    RETURNING id_lote;
"""

INSERT_STAGING_SQL = """
    INSERT INTO staging_eventos (
        id_lote,
        numero_fila,
        fecha_raw,
        hora_raw,
        id_delito_raw,
        distrito_raw,
        direccion_raw,
        latitud_raw,
        longitud_raw,
        id_comisaria_raw,
        fuente_registro_raw,
        descripcion_raw
    ) VALUES (
        %(id_lote)s,
        %(numero_fila)s,
        %(fecha_raw)s,
        %(hora_raw)s,
        %(id_delito_raw)s,
        %(distrito_raw)s,
        %(direccion_raw)s,
        %(latitud_raw)s,
        %(longitud_raw)s,
        %(id_comisaria_raw)s,
        %(fuente_registro_raw)s,
        %(descripcion_raw)s
    )
    RETURNING id_staging;
"""

UPDATE_STAGING_VALID_SQL = """
    UPDATE staging_eventos
    SET
        fecha = %(fecha)s,
        hora = %(hora)s,
        id_delito = %(id_delito)s,
        distrito = %(distrito)s,
        direccion = %(direccion)s,
        latitud = %(latitud)s,
        longitud = %(longitud)s,
        id_comisaria_original = %(id_comisaria_original)s,
        id_comisaria = %(id_comisaria)s,
        id_comisaria_resuelta = %(id_comisaria_resuelta)s,
        nombre_comisaria_resuelta = %(nombre_comisaria_resuelta)s,
        estado_territorial = %(estado_territorial)s,
        regla_territorial = %(regla_territorial)s,
        motivo_territorial = %(motivo_territorial)s,
        conflicto_territorial = %(conflicto_territorial)s,
        fuente_registro = %(fuente_registro)s,
        descripcion = %(descripcion)s,
        estado_registro = 'VALIDO',
        mensaje_error = NULL,
        fecha_validacion = NOW(),
        updated_at = NOW()
    WHERE id_staging = %(id_staging)s;
"""

UPDATE_STAGING_ERROR_SQL = """
    UPDATE staging_eventos
    SET
        estado_registro = %(estado_registro)s,
        mensaje_error = %(mensaje_error)s,
        id_comisaria_original = COALESCE(%(id_comisaria_original)s, id_comisaria_original),
        id_comisaria_resuelta = COALESCE(%(id_comisaria_resuelta)s, id_comisaria_resuelta),
        nombre_comisaria_resuelta = COALESCE(%(nombre_comisaria_resuelta)s, nombre_comisaria_resuelta),
        estado_territorial = COALESCE(%(estado_territorial)s, estado_territorial),
        regla_territorial = COALESCE(%(regla_territorial)s, regla_territorial),
        motivo_territorial = COALESCE(%(motivo_territorial)s, motivo_territorial),
        conflicto_territorial = COALESCE(%(conflicto_territorial)s, conflicto_territorial),
        fecha_validacion = NOW(),
        updated_at = NOW()
    WHERE id_staging = %(id_staging)s;
"""

PROMOTE_EVENT_WITH_LOTE_SQL = """
    INSERT INTO eventos_delictivos (
        fecha,
        hora,
        id_delito,
        distrito,
        direccion,
        latitud,
        longitud,
        geom,
        id_comisaria,
        fuente_registro,
        descripcion,
        id_lote_carga
    ) VALUES (
        %(fecha)s,
        %(hora)s,
        %(id_delito)s,
        %(distrito)s,
        %(direccion)s,
        %(latitud)s,
        %(longitud)s,
        ST_SetSRID(ST_MakePoint(%(longitud)s, %(latitud)s), 4326),
        %(id_comisaria)s,
        %(fuente_registro)s,
        %(descripcion)s,
        %(id_lote_carga)s
    )
    RETURNING id_evento;
"""

PROMOTE_EVENT_SQL = """
    INSERT INTO eventos_delictivos (
        fecha,
        hora,
        id_delito,
        distrito,
        direccion,
        latitud,
        longitud,
        geom,
        id_comisaria,
        fuente_registro,
        descripcion
    ) VALUES (
        %(fecha)s,
        %(hora)s,
        %(id_delito)s,
        %(distrito)s,
        %(direccion)s,
        %(latitud)s,
        %(longitud)s,
        ST_SetSRID(ST_MakePoint(%(longitud)s, %(latitud)s), 4326),
        %(id_comisaria)s,
        %(fuente_registro)s,
        %(descripcion)s
    )
    RETURNING id_evento;
"""


def cargas_tables_ready() -> bool:
    return set(CARGAS_TABLE_NAMES).issubset(get_existing_tables(CARGAS_TABLE_NAMES))


def has_event_lote_fk_column(cur) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'eventos_delictivos'
              AND column_name = 'id_lote_carga'
        ) AS has_column;
        """
    )
    row = cur.fetchone()
    return bool(row["has_column"])


def create_lote(cur, nombre_archivo: str, ruta_archivo: str, observaciones: str | None) -> int:
    cur.execute(INSERT_LOTE_SQL, (nombre_archivo, ruta_archivo, observaciones))
    return int(cur.fetchone()["id_lote"])


def insert_staging_row(cur, id_lote: int, line_number: int, raw_row: dict[str, str]) -> int:
    payload = {
        "id_lote": id_lote,
        "numero_fila": line_number,
        "fecha_raw": raw_row.get("fecha"),
        "hora_raw": raw_row.get("hora"),
        "id_delito_raw": raw_row.get("id_delito"),
        "distrito_raw": raw_row.get("distrito"),
        "direccion_raw": raw_row.get("direccion"),
        "latitud_raw": raw_row.get("latitud"),
        "longitud_raw": raw_row.get("longitud"),
        "id_comisaria_raw": raw_row.get("id_comisaria"),
        "fuente_registro_raw": raw_row.get("fuente_registro"),
        "descripcion_raw": raw_row.get("descripcion"),
    }
    cur.execute(INSERT_STAGING_SQL, payload)
    return int(cur.fetchone()["id_staging"])


def mark_staging_valid(cur, id_staging: int, clean_row: dict[str, Any]) -> None:
    cur.execute(UPDATE_STAGING_VALID_SQL, {**clean_row, "id_staging": id_staging})


def mark_staging_error(
    cur,
    id_staging: int,
    estado_registro: str,
    mensaje_error: str,
    *,
    trace_payload: dict[str, Any] | None = None,
) -> None:
    payload = trace_payload or {}
    cur.execute(
        UPDATE_STAGING_ERROR_SQL,
        {
            "id_staging": id_staging,
            "estado_registro": estado_registro,
            "mensaje_error": mensaje_error,
            "id_comisaria_original": payload.get("id_comisaria_original"),
            "id_comisaria_resuelta": payload.get("id_comisaria_resuelta"),
            "nombre_comisaria_resuelta": payload.get("nombre_comisaria_resuelta"),
            "estado_territorial": payload.get("estado_territorial"),
            "regla_territorial": payload.get("regla_territorial"),
            "motivo_territorial": payload.get("motivo_territorial"),
            "conflicto_territorial": payload.get("conflicto_territorial"),
        },
    )


def list_valid_staging_rows(cur, id_lote: int) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT
            id_staging,
            fecha,
            hora,
            id_delito,
            distrito,
            direccion,
            latitud,
            longitud,
            id_comisaria,
            fuente_registro,
            descripcion,
            numero_fila
        FROM staging_eventos
        WHERE id_lote = %s
          AND estado_registro = 'VALIDO'
        ORDER BY numero_fila;
        """,
        (id_lote,),
    )
    return cur.fetchall()


def fetch_comisaria_context(cur, id_comisaria: int) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT
            id_comisaria,
            nombre_comisaria,
            distrito
        FROM comisarias
        WHERE id_comisaria = %s
        LIMIT 1;
        """,
        (id_comisaria,),
    )
    return cur.fetchone()


def promote_evento(cur, row: dict[str, Any], id_lote: int, include_lote_fk: bool) -> int:
    payload = {
        "fecha": row["fecha"],
        "hora": row["hora"],
        "id_delito": row["id_delito"],
        "distrito": row["distrito"],
        "direccion": row["direccion"],
        "latitud": row["latitud"],
        "longitud": row["longitud"],
        "id_comisaria": row["id_comisaria"],
        "fuente_registro": row["fuente_registro"],
        "descripcion": row["descripcion"],
        "id_lote_carga": id_lote,
    }
    query = PROMOTE_EVENT_WITH_LOTE_SQL if include_lote_fk else PROMOTE_EVENT_SQL
    cur.execute(query, payload)
    return int(cur.fetchone()["id_evento"])


def mark_staging_promoted(cur, id_staging: int, id_evento: int) -> None:
    cur.execute(
        """
        UPDATE staging_eventos
        SET
            estado_registro = 'PROMOVIDO',
            id_evento_final = %s,
            fecha_promocion = NOW(),
            updated_at = NOW()
        WHERE id_staging = %s;
        """,
        (id_evento, id_staging),
    )


def fetch_lote_summary(cur, id_lote: int) -> dict[str, int]:
    cur.execute(
        """
        SELECT
            COUNT(*)::INT AS total_filas,
            COUNT(*) FILTER (
                WHERE estado_registro IN ('VALIDO', 'PROMOVIDO', 'ERROR_PROMOCION')
            )::INT AS filas_validas,
            COUNT(*) FILTER (
                WHERE estado_registro IN ('ERROR_VALIDACION', 'ERROR_PROMOCION', 'ERROR_DUPLICADO')
            )::INT AS filas_error,
            COUNT(*) FILTER (
                WHERE estado_registro = 'PROMOVIDO'
            )::INT AS filas_promovidas
        FROM staging_eventos
        WHERE id_lote = %s;
        """,
        (id_lote,),
    )
    row = cur.fetchone()
    return {
        "total_filas": int(row["total_filas"]),
        "filas_validas": int(row["filas_validas"]),
        "filas_error": int(row["filas_error"]),
        "filas_promovidas": int(row["filas_promovidas"]),
    }


def finalize_lote(cur, id_lote: int, summary: dict[str, int], estado_lote: str) -> None:
    cur.execute(
        """
        UPDATE lotes_carga
        SET
            estado_lote = %s,
            total_filas = %s,
            filas_validas = %s,
            filas_error = %s,
            filas_promovidas = %s,
            fecha_fin = NOW()
        WHERE id_lote = %s;
        """,
        (
            estado_lote,
            summary["total_filas"],
            summary["filas_validas"],
            summary["filas_error"],
            summary["filas_promovidas"],
            id_lote,
        ),
    )


def mark_lote_failed(cur, id_lote: int, observaciones: str | None) -> None:
    cur.execute(
        """
        UPDATE lotes_carga
        SET
            estado_lote = 'FALLIDO',
            fecha_fin = NOW(),
            observaciones = %s
        WHERE id_lote = %s;
        """,
        (observaciones, id_lote),
    )


def fetch_lotes(estado: str | None, limite: int, offset: int) -> list[dict[str, Any]]:
    query = """
        SELECT
            id_lote,
            nombre_archivo,
            estado_lote,
            total_filas,
            filas_validas,
            filas_error,
            filas_promovidas,
            fecha_inicio,
            fecha_fin
        FROM lotes_carga
        WHERE (%s IS NULL OR estado_lote = %s)
        ORDER BY fecha_inicio DESC, id_lote DESC
        LIMIT %s
        OFFSET %s;
    """

    with get_cursor() as cur:
        cur.execute(query, (estado, estado, limite, offset))
        return cur.fetchall()


def fetch_lote_by_id(id_lote: int) -> dict[str, Any] | None:
    query = """
        SELECT
            id_lote,
            nombre_archivo,
            ruta_archivo,
            estado_lote,
            total_filas,
            filas_validas,
            filas_error,
            filas_promovidas,
            observaciones,
            fecha_inicio,
            fecha_fin
        FROM lotes_carga
        WHERE id_lote = %s
        LIMIT 1;
    """

    with get_cursor() as cur:
        cur.execute(query, (id_lote,))
        return cur.fetchone()


def fetch_lote_errors(id_lote: int, limite: int = 200) -> list[dict[str, Any]]:
    query = """
        SELECT
            id_staging,
            numero_fila,
            estado_registro,
            mensaje_error,
            id_comisaria_original,
            id_comisaria_resuelta,
            nombre_comisaria_resuelta,
            estado_territorial,
            regla_territorial,
            motivo_territorial,
            conflicto_territorial,
            fecha_raw,
            hora_raw,
            id_delito_raw,
            distrito_raw,
            direccion_raw,
            latitud_raw,
            longitud_raw,
            id_comisaria_raw,
            fuente_registro_raw,
            descripcion_raw
        FROM staging_eventos
        WHERE id_lote = %s
          AND (
                estado_registro IN ('ERROR_VALIDACION', 'ERROR_PROMOCION', 'ERROR_DUPLICADO')
                OR conflicto_territorial = TRUE
                OR estado_territorial IN (
                    'SIN_COINCIDENCIA_TERRITORIAL',
                    'COORDENADAS_INVALIDAS',
                    'COORDENADAS_INCOMPLETAS'
                )
          )
        ORDER BY numero_fila
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, (id_lote, limite))
        return cur.fetchall()
