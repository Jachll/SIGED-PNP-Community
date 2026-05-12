from datetime import date
from typing import Any

from app.database import get_cursor
from app.repositories.query_utils import (
    build_event_filter_conditions,
    build_where_clause,
    get_canonical_district_select,
    get_existing_tables,
    table_has_column,
)


def fetch_eventos(
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
    limite: int,
    offset: int,
) -> list[dict[str, Any]]:
    conditions, params = build_event_filter_conditions(
        fecha_inicio,
        fecha_fin,
        id_delito,
        distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        table_alias="e",
        table_name="eventos_delictivos",
    )
    where_clause = build_where_clause(conditions)
    district_join, district_select = get_canonical_district_select(
        "e",
        table_name="eventos_delictivos",
        territory_alias="td",
    )

    query = f"""
        SELECT
            e.id_evento,
            e.fecha,
            e.hora,
            e.id_delito,
            d.nombre_delito,
            {district_select} AS distrito,
            e.direccion,
            e.latitud,
            e.longitud,
            e.id_comisaria,
            c.nombre_comisaria,
            e.fuente_registro,
            e.descripcion
        FROM eventos_delictivos e
        INNER JOIN delitos d
            ON d.id_delito = e.id_delito
        LEFT JOIN comisarias c
            ON c.id_comisaria = e.id_comisaria
        {district_join}
        {where_clause}
        ORDER BY e.fecha DESC, e.hora DESC
        LIMIT %s
        OFFSET %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*params, limite, offset])
        return cur.fetchall()


def fetch_eventos_heatmap(
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
    limite: int,
) -> list[dict[str, Any]]:
    conditions, params = build_event_filter_conditions(
        fecha_inicio,
        fecha_fin,
        id_delito,
        distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        table_alias="e",
        table_name="eventos_delictivos",
    )
    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT
            e.latitud AS lat,
            e.longitud AS lng,
            1 AS intensidad
        FROM eventos_delictivos e
        {where_clause}
        ORDER BY e.fecha DESC, e.hora DESC
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*params, limite])
        return cur.fetchall()


def fetch_evento_detalle(
    id_evento: int,
    *,
    radio_metros: int = 150,
    limite_relacionados: int = 5,
) -> dict[str, Any] | None:
    has_zones = "zonas_operativas" in get_existing_tables(["zonas_operativas"])
    has_region_column = table_has_column("comisarias", "region_policial")
    has_division_column = table_has_column("comisarias", "division_policial")
    district_join, district_select = get_canonical_district_select(
        "e",
        table_name="eventos_delictivos",
        territory_alias="td",
    )

    region_select = "c.region_policial AS region" if has_region_column else "NULL::VARCHAR(120) AS region"
    division_select = "c.division_policial AS division" if has_division_column else "NULL::VARCHAR(150) AS division"
    zone_joins = ""
    jurisdiccion_select = "NULL::VARCHAR(150) AS jurisdiccion"
    sector_select = "NULL::VARCHAR(150) AS sector"

    if has_zones:
        zone_joins = """
        LEFT JOIN LATERAL (
            SELECT z.nombre_zona
            FROM zonas_operativas z
            WHERE z.estado_zona = 'ACTIVA'
              AND z.tipo_zona = 'JURISDICCION'
              AND ST_Covers(z.geom, ST_SetSRID(ST_MakePoint(e.longitud, e.latitud), 4326))
            ORDER BY z.id_zona
            LIMIT 1
        ) jurisdiccion_zona ON TRUE
        LEFT JOIN LATERAL (
            SELECT z.nombre_zona
            FROM zonas_operativas z
            WHERE z.estado_zona = 'ACTIVA'
              AND z.tipo_zona = 'SECTOR'
              AND ST_Covers(z.geom, ST_SetSRID(ST_MakePoint(e.longitud, e.latitud), 4326))
            ORDER BY z.id_zona
            LIMIT 1
        ) sector_zona ON TRUE
        """
        jurisdiccion_select = "jurisdiccion_zona.nombre_zona AS jurisdiccion"
        sector_select = "sector_zona.nombre_zona AS sector"

    detail_query = f"""
        SELECT
            e.id_evento,
            e.fecha,
            e.hora,
            e.id_delito,
            d.nombre_delito,
            {district_select} AS distrito,
            e.direccion,
            e.latitud,
            e.longitud,
            e.id_comisaria,
            c.nombre_comisaria,
            e.fuente_registro,
            e.descripcion,
            {region_select},
            {division_select},
            {jurisdiccion_select},
            {sector_select}
        FROM eventos_delictivos e
        INNER JOIN delitos d
            ON d.id_delito = e.id_delito
        LEFT JOIN comisarias c
            ON c.id_comisaria = e.id_comisaria
        {district_join}
        {zone_joins}
        WHERE e.id_evento = %s
        LIMIT 1;
    """

    contexto_totales_query = """
        WITH evento_base AS (
            SELECT
                e.id_evento,
                e.fecha,
                ST_SetSRID(ST_MakePoint(e.longitud, e.latitud), 4326) AS anchor_geom
            FROM eventos_delictivos e
            WHERE e.id_evento = %s
        )
        SELECT
            COUNT(e2.id_evento)::INT AS total_eventos_historicos,
            COUNT(e2.id_evento) FILTER (
                WHERE e2.fecha BETWEEN (eb.fecha - INTERVAL '30 days') AND eb.fecha
            )::INT AS total_eventos_30_dias,
            COUNT(e2.id_evento) FILTER (
                WHERE e2.fecha BETWEEN (eb.fecha - INTERVAL '90 days') AND eb.fecha
            )::INT AS total_eventos_90_dias
        FROM evento_base eb
        LEFT JOIN eventos_delictivos e2
            ON e2.id_evento <> eb.id_evento
           AND ST_DWithin(
                ST_SetSRID(ST_MakePoint(e2.longitud, e2.latitud), 4326)::geography,
                eb.anchor_geom::geography,
                %s
           );
    """

    relacionados_query = """
        WITH evento_base AS (
            SELECT
                e.id_evento,
                ST_SetSRID(ST_MakePoint(e.longitud, e.latitud), 4326) AS anchor_geom
            FROM eventos_delictivos e
            WHERE e.id_evento = %s
        )
        SELECT
            e2.id_evento,
            e2.fecha,
            e2.hora,
            d.nombre_delito,
            e2.direccion,
            c.nombre_comisaria,
            ROUND(
                ST_Distance(
                    ST_SetSRID(ST_MakePoint(e2.longitud, e2.latitud), 4326)::geography,
                    eb.anchor_geom::geography
                )
            )::INT AS distancia_metros
        FROM evento_base eb
        INNER JOIN eventos_delictivos e2
            ON e2.id_evento <> eb.id_evento
           AND ST_DWithin(
                ST_SetSRID(ST_MakePoint(e2.longitud, e2.latitud), 4326)::geography,
                eb.anchor_geom::geography,
                %s
           )
        INNER JOIN delitos d
            ON d.id_delito = e2.id_delito
        LEFT JOIN comisarias c
            ON c.id_comisaria = e2.id_comisaria
        ORDER BY e2.fecha DESC, e2.hora DESC, e2.id_evento DESC
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(detail_query, (id_evento,))
        detail_row = cur.fetchone()
        if not detail_row:
            return None

        cur.execute(contexto_totales_query, (id_evento, radio_metros))
        contexto_row = cur.fetchone() or {}

        cur.execute(relacionados_query, (id_evento, radio_metros, limite_relacionados))
        relacionados = cur.fetchall()

    detail_row["referencia_territorial"] = {
        "region": detail_row.pop("region", None),
        "division": detail_row.pop("division", None),
        "comisaria": detail_row.get("nombre_comisaria"),
        "jurisdiccion": detail_row.pop("jurisdiccion", None),
        "sector": detail_row.pop("sector", None),
    }
    detail_row["contexto_lugar"] = {
        "radio_metros": radio_metros,
        "total_eventos_historicos": int(contexto_row.get("total_eventos_historicos", 0)),
        "total_eventos_30_dias": int(contexto_row.get("total_eventos_30_dias", 0)),
        "total_eventos_90_dias": int(contexto_row.get("total_eventos_90_dias", 0)),
        "eventos_recientes": relacionados,
    }

    return detail_row
