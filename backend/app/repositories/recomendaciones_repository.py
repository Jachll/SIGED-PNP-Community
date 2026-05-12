from datetime import date
from typing import Any

from app.database import get_cursor
from app.repositories.query_utils import (
    build_event_filter_conditions,
    build_where_clause,
    get_existing_tables,
    is_schema_compatibility_error,
)


def fetch_patrol_recommendation_candidates(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
    turno: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    existing_tables = get_existing_tables(["zonas_operativas"])

    if "zonas_operativas" in existing_tables:
        try:
            rows = _fetch_candidates_from_zones(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                id_delito=id_delito,
                distrito=distrito,
                id_comisaria=id_comisaria,
                region=region,
                division=division,
                comisaria=comisaria,
                jurisdiccion=jurisdiccion,
                sector=sector,
                turno=turno,
                limite=limite,
            )
            if rows:
                return rows
        except Exception as exc:
            if not is_schema_compatibility_error(exc):
                raise

    return _fetch_candidates_from_events(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        turno=turno,
        limite=limite,
    )


def save_patrol_recommendations(records: list[dict[str, Any]]) -> list[int]:
    if not records:
        return []

    existing_tables = get_existing_tables(["recomendaciones_patrullaje"])
    if "recomendaciones_patrullaje" not in existing_tables:
        raise RuntimeError(
            "La tabla recomendaciones_patrullaje no existe. Ejecuta database/sql/10_recomendaciones_patrullaje.sql antes de guardar recomendaciones."
        )

    query = """
        INSERT INTO recomendaciones_patrullaje (
            fecha_operativa,
            turno,
            id_hotspot,
            id_zona,
            id_comisaria,
            distrito,
            prioridad,
            tipo_recomendacion,
            detalle_operativo,
            cantidad_efectivos,
            cantidad_unidades,
            estado_recomendacion,
            observaciones
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'PENDIENTE',
            %s
        )
        RETURNING id_recomendacion;
    """

    inserted_ids: list[int] = []
    with get_cursor() as cur:
        for record in records:
            cur.execute(
                query,
                [
                    record["fecha_operativa"],
                    record["turno"],
                    record.get("id_hotspot"),
                    record.get("id_zona"),
                    record.get("id_comisaria"),
                    record["distrito"],
                    record["prioridad"],
                    record["tipo_recomendacion"],
                    record["detalle_operativo"],
                    record["cantidad_efectivos"],
                    record["cantidad_unidades"],
                    record["observaciones"],
                ],
            )
            inserted_ids.append(cur.fetchone()["id_recomendacion"])

    return inserted_ids


def _fetch_candidates_from_zones(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
    turno: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    event_conditions, event_params = build_event_filter_conditions(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        table_alias="e",
    )
    event_where_clause = build_where_clause(event_conditions)

    final_conditions: list[str] = []
    final_params: list[Any] = []

    if turno:
        final_conditions.append("rz.turno = %s")
        final_params.append(turno)

    if id_comisaria:
        final_conditions.append("rz.id_comisaria = %s")
        final_params.append(id_comisaria)

    final_where_clause = build_where_clause(final_conditions)

    query = f"""
        WITH eventos_filtrados AS (
            SELECT
                e.id_evento,
                e.fecha,
                e.hora,
                e.geom
            FROM eventos_delictivos e
            {event_where_clause}
        ),
        periodo_analizado AS (
            SELECT
                MIN(ef.fecha) AS periodo_inicio,
                MAX(ef.fecha) AS periodo_fin,
                CASE
                    WHEN COUNT(*) = 0 THEN 0
                    ELSE (MAX(ef.fecha) - MIN(ef.fecha) + 1)
                END::INT AS dias_analizados
            FROM eventos_filtrados ef
        ),
        resumen_zona_turno AS (
            SELECT
                z.id_zona,
                z.codigo_zona,
                z.nombre_zona,
                z.tipo_zona,
                z.distrito,
                z.id_comisaria,
                c.nombre_comisaria,
                ST_Y(ST_Centroid(z.geom))::FLOAT AS latitud,
                ST_X(ST_Centroid(z.geom))::FLOAT AS longitud,
                CASE
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 0 AND 5 THEN 'MADRUGADA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 6 AND 11 THEN 'MANANA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 12 AND 17 THEN 'TARDE'
                    ELSE 'NOCHE'
                END AS turno,
                COUNT(*)::INT AS total_eventos_franja
            FROM zonas_operativas z
            INNER JOIN eventos_filtrados ef
                ON ST_Intersects(ef.geom, z.geom)
            LEFT JOIN comisarias c
                ON c.id_comisaria = z.id_comisaria
            GROUP BY
                z.id_zona,
                z.codigo_zona,
                z.nombre_zona,
                z.tipo_zona,
                z.distrito,
                z.id_comisaria,
                c.nombre_comisaria,
                z.geom,
                CASE
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 0 AND 5 THEN 'MADRUGADA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 6 AND 11 THEN 'MANANA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 12 AND 17 THEN 'TARDE'
                    ELSE 'NOCHE'
                END
        ),
        total_zona AS (
            SELECT
                rzt.id_zona,
                SUM(rzt.total_eventos_franja)::INT AS total_eventos_zona
            FROM resumen_zona_turno rzt
            GROUP BY rzt.id_zona
        )
        SELECT
            rz.id_zona,
            rz.codigo_zona,
            rz.nombre_zona,
            rz.tipo_zona,
            rz.distrito,
            rz.id_comisaria,
            rz.nombre_comisaria,
            rz.latitud,
            rz.longitud,
            rz.turno,
            rz.total_eventos_franja,
            tz.total_eventos_zona,
            (rz.total_eventos_franja::FLOAT / NULLIF(tz.total_eventos_zona, 0))::FLOAT AS participacion_franja,
            (rz.total_eventos_franja::FLOAT / NULLIF(pa.dias_analizados, 0))::FLOAT AS promedio_diario_franja,
            (rz.total_eventos_franja::FLOAT / NULLIF(tz.total_eventos_zona::FLOAT / 4.0, 0))::FLOAT AS indice_concentracion,
            pa.periodo_inicio,
            pa.periodo_fin,
            pa.dias_analizados,
            'zonas_operativas' AS origen_datos
        FROM resumen_zona_turno rz
        INNER JOIN total_zona tz
            ON tz.id_zona = rz.id_zona
        CROSS JOIN periodo_analizado pa
        {final_where_clause}
        ORDER BY
            rz.total_eventos_franja DESC,
            participacion_franja DESC,
            rz.nombre_zona,
            rz.turno
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*event_params, *final_params, limite])
        return cur.fetchall()


def _fetch_candidates_from_events(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
    turno: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    conditions, params = build_event_filter_conditions(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        table_alias="e",
    )
    where_clause = build_where_clause(conditions)

    final_conditions: list[str] = []
    final_params: list[Any] = []

    if turno:
        final_conditions.append("rz.turno = %s")
        final_params.append(turno)

    final_where_clause = build_where_clause(final_conditions)

    query = f"""
        WITH eventos_filtrados AS (
            SELECT
                e.id_evento,
                e.fecha,
                e.hora,
                e.distrito,
                e.id_comisaria,
                e.latitud,
                e.longitud
            FROM eventos_delictivos e
            {where_clause}
        ),
        periodo_analizado AS (
            SELECT
                MIN(ef.fecha) AS periodo_inicio,
                MAX(ef.fecha) AS periodo_fin,
                CASE
                    WHEN COUNT(*) = 0 THEN 0
                    ELSE (MAX(ef.fecha) - MIN(ef.fecha) + 1)
                END::INT AS dias_analizados
            FROM eventos_filtrados ef
        ),
        resumen_zona_turno AS (
            SELECT
                NULL::BIGINT AS id_zona,
                COALESCE(
                    'COM-' || ef.id_comisaria::TEXT,
                    'DIST-' || UPPER(REPLACE(ef.distrito, ' ', '_'))
                ) AS codigo_zona,
                COALESCE(c.nombre_comisaria, ef.distrito) AS nombre_zona,
                CASE
                    WHEN ef.id_comisaria IS NOT NULL THEN 'COMISARIA'
                    ELSE 'DISTRITO'
                END AS tipo_zona,
                ef.distrito,
                ef.id_comisaria,
                c.nombre_comisaria,
                AVG(ef.latitud)::FLOAT AS latitud,
                AVG(ef.longitud)::FLOAT AS longitud,
                CASE
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 0 AND 5 THEN 'MADRUGADA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 6 AND 11 THEN 'MANANA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 12 AND 17 THEN 'TARDE'
                    ELSE 'NOCHE'
                END AS turno,
                COUNT(*)::INT AS total_eventos_franja
            FROM eventos_filtrados ef
            LEFT JOIN comisarias c
                ON c.id_comisaria = ef.id_comisaria
            GROUP BY
                ef.distrito,
                ef.id_comisaria,
                c.nombre_comisaria,
                CASE
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 0 AND 5 THEN 'MADRUGADA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 6 AND 11 THEN 'MANANA'
                    WHEN EXTRACT(HOUR FROM ef.hora) BETWEEN 12 AND 17 THEN 'TARDE'
                    ELSE 'NOCHE'
                END
        ),
        total_zona AS (
            SELECT
                rzt.codigo_zona,
                SUM(rzt.total_eventos_franja)::INT AS total_eventos_zona
            FROM resumen_zona_turno rzt
            GROUP BY rzt.codigo_zona
        )
        SELECT
            rz.id_zona,
            rz.codigo_zona,
            rz.nombre_zona,
            rz.tipo_zona,
            rz.distrito,
            rz.id_comisaria,
            rz.nombre_comisaria,
            rz.latitud,
            rz.longitud,
            rz.turno,
            rz.total_eventos_franja,
            tz.total_eventos_zona,
            (rz.total_eventos_franja::FLOAT / NULLIF(tz.total_eventos_zona, 0))::FLOAT AS participacion_franja,
            (rz.total_eventos_franja::FLOAT / NULLIF(pa.dias_analizados, 0))::FLOAT AS promedio_diario_franja,
            (rz.total_eventos_franja::FLOAT / NULLIF(tz.total_eventos_zona::FLOAT / 4.0, 0))::FLOAT AS indice_concentracion,
            pa.periodo_inicio,
            pa.periodo_fin,
            pa.dias_analizados,
            'eventos_delictivos' AS origen_datos
        FROM resumen_zona_turno rz
        INNER JOIN total_zona tz
            ON tz.codigo_zona = rz.codigo_zona
        CROSS JOIN periodo_analizado pa
        {final_where_clause}
        ORDER BY
            rz.total_eventos_franja DESC,
            participacion_franja DESC,
            rz.nombre_zona,
            rz.turno
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*params, *final_params, limite])
        return cur.fetchall()
