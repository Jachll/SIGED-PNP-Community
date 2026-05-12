from datetime import date
from typing import Any

from app.database import get_cursor
from app.repositories.query_utils import build_event_filter_conditions, build_where_clause


def fetch_estadisticas_por_hora(
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
    )
    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT
            EXTRACT(HOUR FROM e.hora)::INT AS hora,
            COUNT(*)::INT AS total
        FROM eventos_delictivos e
        {where_clause}
        GROUP BY hora
        ORDER BY hora;
    """

    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_estadisticas_por_dia(
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
    )
    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT
            e.fecha,
            COUNT(*)::INT AS total
        FROM eventos_delictivos e
        {where_clause}
        GROUP BY e.fecha
        ORDER BY e.fecha;
    """

    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_estadisticas_por_mes(
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
    )
    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT
            TO_CHAR(DATE_TRUNC('month', e.fecha), 'YYYY-MM') AS periodo,
            EXTRACT(YEAR FROM DATE_TRUNC('month', e.fecha))::INT AS anio,
            EXTRACT(MONTH FROM DATE_TRUNC('month', e.fecha))::INT AS mes,
            COUNT(*)::INT AS total
        FROM eventos_delictivos e
        {where_clause}
        GROUP BY DATE_TRUNC('month', e.fecha)
        ORDER BY DATE_TRUNC('month', e.fecha);
    """

    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_estadisticas_por_dia_semana(
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
    )
    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT
            EXTRACT(ISODOW FROM e.fecha)::INT AS dia_semana_numero,
            CASE EXTRACT(ISODOW FROM e.fecha)::INT
                WHEN 1 THEN 'Lunes'
                WHEN 2 THEN 'Martes'
                WHEN 3 THEN 'Miercoles'
                WHEN 4 THEN 'Jueves'
                WHEN 5 THEN 'Viernes'
                WHEN 6 THEN 'Sabado'
                WHEN 7 THEN 'Domingo'
            END AS dia_semana,
            COUNT(*)::INT AS total
        FROM eventos_delictivos e
        {where_clause}
        GROUP BY 1, 2
        ORDER BY 1;
    """

    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()
