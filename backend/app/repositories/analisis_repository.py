from datetime import date
import logging
from typing import Any

from app.database import get_cursor
from app.repositories.query_utils import (
    append_geo_scope_filter_conditions,
    build_event_filter_conditions,
    build_period_overlap_conditions,
    build_where_clause,
    get_canonical_district_code_select,
    get_canonical_district_select,
    get_existing_tables,
    is_schema_compatibility_error,
    table_has_column,
)
from app.territorial import normalize_territory_name

logger = logging.getLogger("siged.repositories.analisis")


def fetch_hotspots(
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
    estado: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    existing_tables = get_existing_tables(["hotspots", "zonas_operativas"])

    if "hotspots" in existing_tables:
        try:
            persisted_rows = _fetch_hotspots_from_table(
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
                estado=estado,
                limite=limite,
                has_zones="zonas_operativas" in existing_tables,
            )
            if persisted_rows:
                return persisted_rows
        except Exception as exc:
            if not is_schema_compatibility_error(exc):
                raise

            logger.warning(
                "La tabla hotspots existe pero no es compatible con la consulta actual; se usara el fallback desde eventos.",
                exc_info=exc,
            )

    return _fetch_hotspots_from_events(
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
        estado=estado,
        limite=limite,
    )


def fetch_zonas_criticas(
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
    agrupado_por: str,
    min_eventos: int,
    limite: int,
) -> list[dict[str, Any]]:
    if agrupado_por == "distrito":
        return _fetch_zonas_criticas_por_distrito(
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
            min_eventos=min_eventos,
            limite=limite,
        )

    if agrupado_por == "comisaria":
        return _fetch_zonas_criticas_por_comisaria(
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
            min_eventos=min_eventos,
            limite=limite,
        )

    if "zonas_operativas" not in get_existing_tables(["zonas_operativas"]):
        raise ValueError(
            "No se puede agrupar por zona_operativa porque la tabla zonas_operativas no existe"
        )

    return _fetch_zonas_criticas_por_zona_operativa(
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
        min_eventos=min_eventos,
        limite=limite,
    )


def fetch_agregados_espaciales(
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
    tamano_celda_metros: int,
    min_eventos: int,
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
    district_join, district_select = get_canonical_district_select(
        "e",
        table_name="eventos_delictivos",
        territory_alias="td",
    )

    query = f"""
        WITH eventos_filtrados AS (
            SELECT
                e.id_evento,
                e.id_delito,
                d.nombre_delito,
                {district_select} AS distrito,
                e.latitud::FLOAT AS latitud,
                e.longitud::FLOAT AS longitud,
                FLOOR(ST_X(ST_Transform(e.geom, 3857)) / %s)::BIGINT AS celda_x,
                FLOOR(ST_Y(ST_Transform(e.geom, 3857)) / %s)::BIGINT AS celda_y
            FROM eventos_delictivos e
            INNER JOIN delitos d
                ON d.id_delito = e.id_delito
            {district_join}
            {where_clause}
        ),
        resumen_celdas AS (
            SELECT
                ef.celda_x,
                ef.celda_y,
                COUNT(*)::INT AS total_eventos,
                COUNT(*)::FLOAT AS intensidad,
                AVG(ef.latitud)::FLOAT AS lat,
                AVG(ef.longitud)::FLOAT AS lng,
                ARRAY[
                    MIN(ef.latitud)::FLOAT,
                    MIN(ef.longitud)::FLOAT,
                    MAX(ef.latitud)::FLOAT,
                    MAX(ef.longitud)::FLOAT
                ] AS bbox,
                COUNT(DISTINCT ef.distrito)::INT AS total_distritos,
                COUNT(DISTINCT ef.id_delito)::INT AS total_delitos
            FROM eventos_filtrados ef
            GROUP BY ef.celda_x, ef.celda_y
            HAVING COUNT(*) >= %s
        ),
        distritos_celda AS (
            SELECT
                ef.celda_x,
                ef.celda_y,
                ef.distrito,
                COUNT(*)::INT AS total_distrito
            FROM eventos_filtrados ef
            GROUP BY ef.celda_x, ef.celda_y, ef.distrito
        ),
        distrito_principal AS (
            SELECT DISTINCT ON (dc.celda_x, dc.celda_y)
                dc.celda_x,
                dc.celda_y,
                dc.distrito AS distrito_principal
            FROM distritos_celda dc
            ORDER BY dc.celda_x, dc.celda_y, dc.total_distrito DESC, dc.distrito
        ),
        delitos_celda AS (
            SELECT
                ef.celda_x,
                ef.celda_y,
                ef.id_delito,
                ef.nombre_delito,
                COUNT(*)::INT AS total_delito
            FROM eventos_filtrados ef
            GROUP BY ef.celda_x, ef.celda_y, ef.id_delito, ef.nombre_delito
        ),
        delito_principal AS (
            SELECT DISTINCT ON (dc.celda_x, dc.celda_y)
                dc.celda_x,
                dc.celda_y,
                dc.id_delito AS id_delito_principal,
                dc.nombre_delito AS delito_principal
            FROM delitos_celda dc
            ORDER BY dc.celda_x, dc.celda_y, dc.total_delito DESC, dc.nombre_delito
        )
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    rc.total_eventos DESC,
                    rc.celda_y,
                    rc.celda_x
            )::INT AS id_agregado,
            'grid' AS tipo_agregado,
            %s::INT AS tamano_celda_metros,
            rc.total_eventos,
            rc.intensidad,
            rc.lat,
            rc.lng,
            rc.bbox,
            dp.distrito_principal,
            dlp.id_delito_principal,
            dlp.delito_principal,
            rc.total_distritos,
            rc.total_delitos
        FROM resumen_celdas rc
        LEFT JOIN distrito_principal dp
            ON dp.celda_x = rc.celda_x
           AND dp.celda_y = rc.celda_y
        LEFT JOIN delito_principal dlp
            ON dlp.celda_x = rc.celda_x
           AND dlp.celda_y = rc.celda_y
        ORDER BY
            rc.total_eventos DESC,
            rc.celda_y,
            rc.celda_x
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(
            query,
            [
                tamano_celda_metros,
                tamano_celda_metros,
                *params,
                min_eventos,
                tamano_celda_metros,
                limite,
            ],
        )
        return cur.fetchall()


def _fetch_hotspots_from_table(
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
    estado: str | None,
    limite: int,
    has_zones: bool,
) -> list[dict[str, Any]]:
    conditions, params = build_period_overlap_conditions(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        start_column="periodo_inicio",
        end_column="periodo_fin",
        table_alias="h",
    )

    if id_delito:
        conditions.append("h.id_delito = %s")
        params.append(id_delito)

    if distrito:
        normalized_district = normalize_territory_name(distrito)
        if table_has_column("hotspots", "distrito_normalizado"):
            conditions.append("h.distrito_normalizado = %s")
        else:
            conditions.append("UPPER(h.distrito) = %s")
        params.append(normalized_district)

    if id_comisaria:
        if has_zones:
            conditions.append("z.id_comisaria = %s")
            params.append(id_comisaria)
        elif table_has_column("hotspots", "id_comisaria"):
            conditions.append("h.id_comisaria = %s")
            params.append(id_comisaria)

    if estado:
        conditions.append("UPPER(h.estado_hotspot) = UPPER(%s)")
        params.append(estado.strip())

    append_geo_scope_filter_conditions(
        conditions,
        params,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        table_alias="h",
        table_name="hotspots",
    )

    where_clause = build_where_clause(conditions)
    district_join, district_select = get_canonical_district_select(
        "h",
        table_name="hotspots",
        territory_alias="hd",
    )

    zone_columns = """
            z.nombre_zona,
            z.id_comisaria,
            c.nombre_comisaria,
    """ if has_zones else """
            NULL::VARCHAR(150) AS nombre_zona,
            NULL::SMALLINT AS id_comisaria,
            NULL::VARCHAR(150) AS nombre_comisaria,
    """

    zone_joins = """
        LEFT JOIN zonas_operativas z
            ON z.id_zona = h.id_zona
        LEFT JOIN comisarias c
            ON c.id_comisaria = z.id_comisaria
    """ if has_zones else ""

    query = f"""
        SELECT
            h.id_hotspot,
            h.periodo_inicio,
            h.periodo_fin,
            h.fecha_deteccion,
            h.id_delito,
            d.nombre_delito,
            {district_select} AS distrito,
            h.id_zona,
            {zone_columns}
            h.nivel_riesgo,
            h.intensidad::FLOAT AS intensidad,
            h.conteo_eventos::INT AS conteo_eventos,
            h.latitud::FLOAT AS latitud,
            h.longitud::FLOAT AS longitud,
            h.radio_metros::INT AS radio_metros,
            h.fuente_analisis,
            h.estado_hotspot,
            h.observaciones,
            'tabla_hotspots' AS origen_datos
        FROM hotspots h
        LEFT JOIN delitos d
            ON d.id_delito = h.id_delito
        {district_join}
        {zone_joins}
        {where_clause}
        ORDER BY
            CASE h.nivel_riesgo
                WHEN 'CRITICO' THEN 4
                WHEN 'ALTO' THEN 3
                WHEN 'MEDIO' THEN 2
                WHEN 'BAJO' THEN 1
                ELSE 0
            END DESC,
            h.conteo_eventos DESC,
            h.intensidad DESC,
            h.fecha_deteccion DESC
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*params, limite])
        return cur.fetchall()


def _fetch_hotspots_from_events(
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
    estado: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    if estado and estado.strip().upper() != "ACTIVO":
        return []

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
        WITH hotspots_agrupados AS (
            SELECT
                MIN(e.fecha) AS periodo_inicio,
                MAX(e.fecha) AS periodo_fin,
                MAX(e.fecha)::timestamp AS fecha_deteccion,
                e.id_delito,
                d.nombre_delito,
                {district_select} AS distrito,
                COUNT(*)::INT AS conteo_eventos,
                COUNT(*)::FLOAT AS intensidad,
                AVG(e.latitud)::FLOAT AS latitud,
                AVG(e.longitud)::FLOAT AS longitud
            FROM eventos_delictivos e
            INNER JOIN delitos d
                ON d.id_delito = e.id_delito
            {district_join}
            {where_clause}
            GROUP BY
                ROUND(e.latitud::numeric, 3),
                ROUND(e.longitud::numeric, 3),
                e.id_delito,
                d.nombre_delito,
                {district_select}
        )
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    h.conteo_eventos DESC,
                    h.periodo_fin DESC,
                    h.distrito,
                    h.nombre_delito
            )::BIGINT AS id_hotspot,
            h.periodo_inicio,
            h.periodo_fin,
            h.fecha_deteccion,
            h.id_delito,
            h.nombre_delito,
            h.distrito,
            NULL::BIGINT AS id_zona,
            NULL::VARCHAR(150) AS nombre_zona,
            NULL::SMALLINT AS id_comisaria,
            NULL::VARCHAR(150) AS nombre_comisaria,
            CASE
                WHEN h.conteo_eventos >= 10 THEN 'CRITICO'
                WHEN h.conteo_eventos >= 6 THEN 'ALTO'
                WHEN h.conteo_eventos >= 3 THEN 'MEDIO'
                ELSE 'BAJO'
            END AS nivel_riesgo,
            h.intensidad,
            h.conteo_eventos,
            h.latitud,
            h.longitud,
            250 AS radio_metros,
            'EVENTOS_AGRUPADOS' AS fuente_analisis,
            'ACTIVO' AS estado_hotspot,
            'Hotspot calculado automaticamente desde eventos_delictivos' AS observaciones,
            'calculado_desde_eventos' AS origen_datos
        FROM hotspots_agrupados h
        ORDER BY
            h.conteo_eventos DESC,
            h.periodo_fin DESC,
            h.distrito,
            h.nombre_delito
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*params, limite])
        return cur.fetchall()


def _build_risk_case(count_expression: str) -> str:
    return f"""
        CASE
            WHEN {count_expression} >= 15 THEN 'CRITICO'
            WHEN {count_expression} >= 8 THEN 'ALTO'
            WHEN {count_expression} >= 4 THEN 'MEDIO'
            ELSE 'BAJO'
        END
    """


def _build_priority_case(count_expression: str) -> str:
    return f"""
        CASE
            WHEN {count_expression} >= 15 THEN 'CRITICA'
            WHEN {count_expression} >= 8 THEN 'ALTA'
            WHEN {count_expression} >= 4 THEN 'MEDIA'
            ELSE 'BAJA'
        END
    """


def _fetch_zonas_criticas_por_distrito(
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
    min_eventos: int,
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
    riesgo_case = _build_risk_case("COUNT(*)")
    prioridad_case = _build_priority_case("COUNT(*)")
    district_join, district_select = get_canonical_district_select(
        "e",
        table_name="eventos_delictivos",
        territory_alias="td",
    )
    code_join, district_code = get_canonical_district_code_select(
        "e",
        table_name="eventos_delictivos",
        territory_alias="td",
        fallback_expression="'DIST-' || UPPER(REPLACE(e.distrito, ' ', '_'))",
    )
    district_join_clause = district_join or code_join

    query = f"""
        WITH total_periodo AS (
            SELECT COUNT(*)::INT AS total_eventos_periodo
            FROM eventos_delictivos e
            {where_clause}
        ),
        zonas_agrupadas AS (
            SELECT
                NULL::BIGINT AS id_zona,
                {district_code} AS codigo_zona,
                {district_select} AS nombre_zona,
                'DISTRITO' AS tipo_zona,
                {district_select} AS distrito,
                NULL::SMALLINT AS id_comisaria,
                NULL::VARCHAR(150) AS nombre_comisaria,
                {prioridad_case} AS prioridad_operativa,
                'ACTIVA' AS estado_zona,
                0::INT AS total_hotspots,
                COUNT(*)::INT AS total_eventos,
                COUNT(*)::FLOAT AS intensidad_total,
                {riesgo_case} AS nivel_riesgo,
                AVG(e.latitud)::FLOAT AS latitud,
                AVG(e.longitud)::FLOAT AS longitud,
                MIN(e.fecha) AS periodo_inicio,
                MAX(e.fecha) AS periodo_fin
            FROM eventos_delictivos e
            {district_join_clause}
            {where_clause}
            GROUP BY {district_select}, {district_code}
            HAVING COUNT(*) >= %s
        )
        SELECT
            za.id_zona,
            za.codigo_zona,
            za.nombre_zona,
            za.tipo_zona,
            za.distrito,
            za.id_comisaria,
            za.nombre_comisaria,
            za.prioridad_operativa,
            za.estado_zona,
            za.total_hotspots,
            za.total_eventos,
            tp.total_eventos_periodo,
            CASE
                WHEN tp.total_eventos_periodo > 0 THEN ROUND((za.total_eventos::NUMERIC * 100.0 / tp.total_eventos_periodo), 2)::FLOAT
                ELSE 0::FLOAT
            END AS porcentaje_total,
            za.intensidad_total,
            za.nivel_riesgo,
            za.latitud,
            za.longitud,
            'eventos_por_distrito' AS origen_datos,
            'distrito' AS agrupado_por,
            za.periodo_inicio,
            za.periodo_fin
        FROM zonas_agrupadas za
        CROSS JOIN total_periodo tp
        ORDER BY
            CASE za.nivel_riesgo
                WHEN 'CRITICO' THEN 4
                WHEN 'ALTO' THEN 3
                WHEN 'MEDIO' THEN 2
                ELSE 1
            END DESC,
            za.total_eventos DESC,
            za.nombre_zona
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*params, min_eventos, limite])
        return cur.fetchall()


def _fetch_zonas_criticas_por_comisaria(
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
    min_eventos: int,
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
    conditions.append("e.id_comisaria IS NOT NULL")
    where_clause = build_where_clause(conditions)
    riesgo_case = _build_risk_case("COUNT(*)")
    prioridad_case = _build_priority_case("COUNT(*)")

    query = f"""
        WITH total_periodo AS (
            SELECT COUNT(*)::INT AS total_eventos_periodo
            FROM eventos_delictivos e
            {where_clause}
        ),
        zonas_agrupadas AS (
            SELECT
                NULL::BIGINT AS id_zona,
                'COM-' || e.id_comisaria::TEXT AS codigo_zona,
                COALESCE(c.nombre_comisaria, 'Comisaria ' || e.id_comisaria::TEXT) AS nombre_zona,
                'COMISARIA' AS tipo_zona,
                COALESCE(c.distrito, e.distrito) AS distrito,
                e.id_comisaria,
                c.nombre_comisaria,
                {prioridad_case} AS prioridad_operativa,
                'ACTIVA' AS estado_zona,
                0::INT AS total_hotspots,
                COUNT(*)::INT AS total_eventos,
                COUNT(*)::FLOAT AS intensidad_total,
                {riesgo_case} AS nivel_riesgo,
                AVG(e.latitud)::FLOAT AS latitud,
                AVG(e.longitud)::FLOAT AS longitud,
                MIN(e.fecha) AS periodo_inicio,
                MAX(e.fecha) AS periodo_fin
            FROM eventos_delictivos e
            LEFT JOIN comisarias c
                ON c.id_comisaria = e.id_comisaria
            {where_clause}
            GROUP BY
                e.id_comisaria,
                c.nombre_comisaria,
                COALESCE(c.distrito, e.distrito)
            HAVING COUNT(*) >= %s
        )
        SELECT
            za.id_zona,
            za.codigo_zona,
            za.nombre_zona,
            za.tipo_zona,
            za.distrito,
            za.id_comisaria,
            za.nombre_comisaria,
            za.prioridad_operativa,
            za.estado_zona,
            za.total_hotspots,
            za.total_eventos,
            tp.total_eventos_periodo,
            CASE
                WHEN tp.total_eventos_periodo > 0 THEN ROUND((za.total_eventos::NUMERIC * 100.0 / tp.total_eventos_periodo), 2)::FLOAT
                ELSE 0::FLOAT
            END AS porcentaje_total,
            za.intensidad_total,
            za.nivel_riesgo,
            za.latitud,
            za.longitud,
            'eventos_por_comisaria' AS origen_datos,
            'comisaria' AS agrupado_por,
            za.periodo_inicio,
            za.periodo_fin
        FROM zonas_agrupadas za
        CROSS JOIN total_periodo tp
        ORDER BY
            CASE za.nivel_riesgo
                WHEN 'CRITICO' THEN 4
                WHEN 'ALTO' THEN 3
                WHEN 'MEDIO' THEN 2
                ELSE 1
            END DESC,
            za.total_eventos DESC,
            za.nombre_zona
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*params, min_eventos, limite])
        return cur.fetchall()


def _fetch_zonas_criticas_por_zona_operativa(
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
    min_eventos: int,
    limite: int,
) -> list[dict[str, Any]]:
    event_conditions, event_params = build_event_filter_conditions(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=None,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        table_alias="e",
        table_name="eventos_delictivos",
    )
    event_where_clause = build_where_clause(event_conditions)

    zone_conditions = ["z.estado_zona = 'ACTIVA'"]
    zone_params: list[Any] = []
    if distrito:
        normalized_district = normalize_territory_name(distrito)
        if table_has_column("zonas_operativas", "distrito_normalizado"):
            zone_conditions.append("z.distrito_normalizado = %s")
        else:
            zone_conditions.append("UPPER(z.distrito) = %s")
        zone_params.append(normalized_district)

    if id_comisaria:
        zone_conditions.append("z.id_comisaria = %s")
        zone_params.append(id_comisaria)

    zone_where_clause = build_where_clause(zone_conditions)
    riesgo_case = _build_risk_case("COUNT(DISTINCT ef.id_evento)")

    query = f"""
        WITH eventos_filtrados AS (
            SELECT
                e.id_evento,
                e.fecha,
                e.geom
            FROM eventos_delictivos e
            {event_where_clause}
        ),
        zonas_agrupadas AS (
            SELECT
                z.id_zona,
                z.codigo_zona,
                z.nombre_zona,
                z.tipo_zona,
                z.distrito,
                z.id_comisaria,
                c.nombre_comisaria,
                z.prioridad_operativa,
                z.estado_zona,
                0::INT AS total_hotspots,
                COUNT(DISTINCT ef.id_evento)::INT AS total_eventos,
                COUNT(DISTINCT ef.id_evento)::FLOAT AS intensidad_total,
                {riesgo_case} AS nivel_riesgo,
                ST_Y(ST_Centroid(z.geom))::FLOAT AS latitud,
                ST_X(ST_Centroid(z.geom))::FLOAT AS longitud,
                MIN(ef.fecha) AS periodo_inicio,
                MAX(ef.fecha) AS periodo_fin
            FROM zonas_operativas z
            LEFT JOIN comisarias c
                ON c.id_comisaria = z.id_comisaria
            LEFT JOIN eventos_filtrados ef
                ON ST_Intersects(ef.geom, z.geom)
            {zone_where_clause}
            GROUP BY
                z.id_zona,
                z.codigo_zona,
                z.nombre_zona,
                z.tipo_zona,
                z.distrito,
                z.id_comisaria,
                c.nombre_comisaria,
                z.prioridad_operativa,
                z.estado_zona,
                z.geom
            HAVING COUNT(DISTINCT ef.id_evento) >= %s
        ),
        total_periodo AS (
            SELECT COUNT(DISTINCT ef.id_evento)::INT AS total_eventos_periodo
            FROM zonas_operativas z
            INNER JOIN eventos_filtrados ef
                ON ST_Intersects(ef.geom, z.geom)
            {zone_where_clause}
        )
        SELECT
            za.id_zona,
            za.codigo_zona,
            za.nombre_zona,
            za.tipo_zona,
            za.distrito,
            za.id_comisaria,
            za.nombre_comisaria,
            za.prioridad_operativa,
            za.estado_zona,
            za.total_hotspots,
            za.total_eventos,
            tp.total_eventos_periodo,
            CASE
                WHEN tp.total_eventos_periodo > 0 THEN ROUND((za.total_eventos::NUMERIC * 100.0 / tp.total_eventos_periodo), 2)::FLOAT
                ELSE 0::FLOAT
            END AS porcentaje_total,
            za.intensidad_total,
            za.nivel_riesgo,
            za.latitud,
            za.longitud,
            'zonas_operativas+eventos' AS origen_datos,
            'zona_operativa' AS agrupado_por,
            za.periodo_inicio,
            za.periodo_fin
        FROM zonas_agrupadas za
        CROSS JOIN total_periodo tp
        ORDER BY
            CASE za.nivel_riesgo
                WHEN 'CRITICO' THEN 4
                WHEN 'ALTO' THEN 3
                WHEN 'MEDIO' THEN 2
                ELSE 1
            END DESC,
            za.total_eventos DESC,
            za.nombre_zona
        LIMIT %s;
    """

    with get_cursor() as cur:
        cur.execute(query, [*event_params, *zone_params, min_eventos, *zone_params, limite])
        return cur.fetchall()
