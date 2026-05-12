from typing import Any

from app.database import get_cursor
from app.repositories.query_utils import (
    get_canonical_district_select,
    get_existing_tables,
    table_has_column,
)


def fetch_delitos() -> list[dict[str, Any]]:
    query = """
        SELECT
            d.id_delito,
            d.nombre_delito,
            d.descripcion
        FROM delitos d
        ORDER BY d.nombre_delito;
    """

    with get_cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def fetch_comisarias() -> list[dict[str, Any]]:
    district_join, district_select = get_canonical_district_select(
        "c",
        table_name="comisarias",
        territory_alias="td",
    )

    query = f"""
        SELECT
            c.id_comisaria,
            c.nombre_comisaria,
            {district_select} AS distrito,
            c.direccion
        FROM comisarias c
        {district_join}
        ORDER BY {district_select}, c.nombre_comisaria;
    """

    with get_cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def fetch_distritos() -> list[dict[str, Any]]:
    existing_tables = get_existing_tables(
        ["dim_territorios", "eventos_delictivos", "comisarias", "zonas_operativas", "hotspots"]
    )

    if "dim_territorios" in existing_tables:
        query = """
            SELECT
                dt.nombre_territorio AS distrito
            FROM dim_territorios dt
            WHERE dt.tipo_territorio = 'DISTRITO'
              AND dt.estado_territorio = 'ACTIVO'
            ORDER BY dt.nombre_territorio;
        """

        with get_cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            if rows:
                return rows

    sources: list[str] = []

    if "eventos_delictivos" in existing_tables:
        event_district_column = (
            "COALESCE(e.distrito_normalizado, TRIM(UPPER(e.distrito)))"
            if table_has_column("eventos_delictivos", "distrito_normalizado")
            else "TRIM(UPPER(e.distrito))"
        )
        sources.append(
            f"""
            SELECT {event_district_column} AS distrito
            FROM eventos_delictivos e
            WHERE TRIM(COALESCE(e.distrito, '')) <> ''
            """
        )

    if "comisarias" in existing_tables:
        comisaria_district_column = (
            "COALESCE(c.distrito_normalizado, TRIM(UPPER(c.distrito)))"
            if table_has_column("comisarias", "distrito_normalizado")
            else "TRIM(UPPER(c.distrito))"
        )
        sources.append(
            f"""
            SELECT {comisaria_district_column} AS distrito
            FROM comisarias c
            WHERE TRIM(COALESCE(c.distrito, '')) <> ''
            """
        )

    if "zonas_operativas" in existing_tables:
        zonas_district_column = (
            "COALESCE(z.distrito_normalizado, TRIM(UPPER(z.distrito)))"
            if table_has_column("zonas_operativas", "distrito_normalizado")
            else "TRIM(UPPER(z.distrito))"
        )
        sources.append(
            f"""
            SELECT {zonas_district_column} AS distrito
            FROM zonas_operativas z
            WHERE TRIM(COALESCE(z.distrito, '')) <> ''
            """
        )

    if "hotspots" in existing_tables:
        hotspots_district_column = (
            "COALESCE(h.distrito_normalizado, TRIM(UPPER(h.distrito)))"
            if table_has_column("hotspots", "distrito_normalizado")
            else "TRIM(UPPER(h.distrito))"
        )
        sources.append(
            f"""
            SELECT {hotspots_district_column} AS distrito
            FROM hotspots h
            WHERE TRIM(COALESCE(h.distrito, '')) <> ''
            """
        )

    if not sources:
        return []

    query = f"""
        SELECT base.distrito
        FROM (
            {" UNION ".join(sources)}
        ) AS base
        GROUP BY base.distrito
        ORDER BY base.distrito;
    """

    with get_cursor() as cur:
        cur.execute(query)
        return cur.fetchall()
