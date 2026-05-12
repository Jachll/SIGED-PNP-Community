import json
from datetime import date
from functools import lru_cache
from typing import Any, Iterable

from app.database import get_cursor
from app.territorial import normalize_territory_name
from psycopg2 import errors as psycopg_errors


def build_event_filter_conditions(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None = None,
    region: str | None = None,
    division: str | None = None,
    comisaria: str | None = None,
    jurisdiccion: str | None = None,
    sector: str | None = None,
    table_alias: str = "e",
    table_name: str = "eventos_delictivos",
) -> tuple[list[str], list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []

    if fecha_inicio:
        conditions.append(f"{table_alias}.fecha >= %s")
        params.append(fecha_inicio)

    if fecha_fin:
        conditions.append(f"{table_alias}.fecha <= %s")
        params.append(fecha_fin)

    if id_delito:
        conditions.append(f"{table_alias}.id_delito = %s")
        params.append(id_delito)

    has_geo_scope = any([region, division, comisaria, jurisdiccion, sector])

    if id_comisaria and not has_geo_scope:
        conditions.append(f"{table_alias}.id_comisaria = %s")
        params.append(id_comisaria)

    if distrito:
        normalized_district = normalize_territory_name(distrito)

        if table_has_column(table_name, "distrito_normalizado"):
            conditions.append(f"{table_alias}.distrito_normalizado = %s")
        else:
            conditions.append(f"UPPER({table_alias}.distrito) = %s")

        params.append(normalized_district)

    append_geo_scope_filter_conditions(
        conditions,
        params,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        table_alias=table_alias,
        table_name=table_name,
    )

    return conditions, params


def append_geo_scope_filter_conditions(
    conditions: list[str],
    params: list[Any],
    *,
    id_comisaria: int | None = None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
    table_alias: str = "e",
    table_name: str = "eventos_delictivos",
) -> None:
    if not any([region, division, comisaria, jurisdiccion, sector]):
        return

    geometries = _get_scope_geometries(
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
    )

    if not geometries:
        conditions.append("1 = 0")
        return

    geometry_expression = _build_table_geometry_expression(
        table_alias=table_alias,
        table_name=table_name,
    )
    geometry_conditions: list[str] = []
    for geometry in geometries:
        geometry_conditions.append(
            f"ST_Intersects({geometry_expression}, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))"
        )
        params.append(json.dumps(geometry, ensure_ascii=True))

    conditions.append("(" + " OR ".join(geometry_conditions) + ")")


def _get_scope_geometries(
    *,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
) -> list[dict[str, Any]]:
    from fastapi import HTTPException

    from app.geo_layers import get_geo_layer_data

    normalized_region = normalize_territory_name(region) if region else None
    normalized_division = normalize_territory_name(division) if division else None
    normalized_comisaria = normalize_territory_name(comisaria) if comisaria else None
    normalized_jurisdiccion = str(jurisdiccion or "").strip() or None
    normalized_sector = str(sector or "").strip() or None

    candidate_requests: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    if normalized_sector and (normalized_comisaria or id_comisaria):
        candidate_requests.append(
            (
                "sectores",
                {
                    "region": normalized_region or "",
                    "division": normalized_division or "",
                    "comisaria_id": id_comisaria,
                    "comisaria": normalized_comisaria or "",
                    "sector": normalized_sector,
                },
                {},
            )
        )
    elif normalized_jurisdiccion and (normalized_comisaria or id_comisaria):
        candidate_requests.append(
            (
                "jurisdicciones",
                {
                    "region": normalized_region or "",
                    "division": normalized_division or "",
                    "comisaria_id": id_comisaria,
                    "comisaria": normalized_comisaria or "",
                    "jurisdiccion": normalized_jurisdiccion,
                },
                {},
            )
        )
    elif normalized_comisaria or id_comisaria:
        common_comisaria_scope = {
            "region": normalized_region or "",
            "division": normalized_division or "",
            "comisaria_id": id_comisaria,
            "comisaria": normalized_comisaria or "",
        }
        candidate_requests.append(
            (
                "jurisdicciones",
                common_comisaria_scope,
                {"enforce_scope": False},
            )
        )
        candidate_requests.append(
            (
                "sectores",
                common_comisaria_scope,
                {"enforce_scope": False},
            )
        )
    elif normalized_division:
        candidate_requests.append(
            (
                "divisiones",
                {
                    "region": normalized_region or "",
                    "division": normalized_division,
                },
                {},
            )
        )
    elif normalized_region:
        candidate_requests.append(("regiones", {"region": normalized_region}, {}))

    for layer_id, filters, options in candidate_requests:
        try:
            feature_collection = get_geo_layer_data(
                layer_id,
                detail="full",
                enforce_scope=options.get("enforce_scope", True),
                **filters,
            )
        except HTTPException:
            continue

        features = feature_collection.get("features") or []
        geometries = [feature.get("geometry") for feature in features if feature.get("geometry")]
        if geometries:
            return geometries

    return []


def _build_table_geometry_expression(*, table_alias: str, table_name: str) -> str:
    qualified_point_expression = (
        f"ST_SetSRID(ST_MakePoint({table_alias}.longitud, {table_alias}.latitud), 4326)"
    )

    if table_has_column(table_name, "latitud") and table_has_column(table_name, "longitud"):
        return qualified_point_expression

    return f"{table_alias}.geom"


def build_period_overlap_conditions(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    start_column: str,
    end_column: str,
    table_alias: str = "h",
) -> tuple[list[str], list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []

    qualified_start = f"{table_alias}.{start_column}" if table_alias else start_column
    qualified_end = f"{table_alias}.{end_column}" if table_alias else end_column

    if fecha_inicio:
        conditions.append(f"{qualified_end} >= %s")
        params.append(fecha_inicio)

    if fecha_fin:
        conditions.append(f"{qualified_start} <= %s")
        params.append(fecha_fin)

    return conditions, params


def build_where_clause(conditions: list[str]) -> str:
    if not conditions:
        return ""

    return " WHERE " + " AND ".join(conditions)


def get_existing_tables(table_names: Iterable[str]) -> set[str]:
    normalized_names = sorted(
        {
            table_name.strip()
            for table_name in table_names
            if table_name and table_name.strip()
        }
    )

    if not normalized_names:
        return set()

    return set(_get_existing_tables_cached(tuple(normalized_names)))


@lru_cache(maxsize=32)
def _get_existing_tables_cached(normalized_names: tuple[str, ...]) -> frozenset[str]:
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = ANY(%s);
    """

    with get_cursor() as cur:
        cur.execute(query, (list(normalized_names),))
        rows = cur.fetchall()
        return frozenset(row["table_name"] for row in rows)


@lru_cache(maxsize=128)
def table_has_column(table_name: str, column_name: str) -> bool:
    if not table_name or not column_name:
        return False

    query = """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        ) AS has_column;
    """

    with get_cursor() as cur:
        cur.execute(query, (table_name, column_name))
        row = cur.fetchone()
        return bool(row["has_column"]) if row else False


def get_canonical_district_select(
    table_alias: str,
    *,
    table_name: str,
    territory_alias: str = "td",
) -> tuple[str, str]:
    if get_existing_tables(["dim_territorios"]) and table_has_column(table_name, "id_territorio_distrito"):
        return (
            f"""
        LEFT JOIN dim_territorios {territory_alias}
            ON {territory_alias}.id_territorio = {table_alias}.id_territorio_distrito
            AND {territory_alias}.tipo_territorio = 'DISTRITO'
            """.rstrip(),
            f"COALESCE({territory_alias}.nombre_territorio, {table_alias}.distrito)",
        )

    return "", f"{table_alias}.distrito"


def get_canonical_district_code_select(
    table_alias: str,
    *,
    table_name: str,
    territory_alias: str = "td",
    fallback_expression: str,
) -> tuple[str, str]:
    join_clause, _ = get_canonical_district_select(
        table_alias,
        table_name=table_name,
        territory_alias=territory_alias,
    )

    if join_clause:
        return join_clause, f"COALESCE({territory_alias}.codigo_territorio, {fallback_expression})"

    return "", fallback_expression


def clear_schema_cache() -> None:
    _get_existing_tables_cached.cache_clear()
    table_has_column.cache_clear()


def is_schema_compatibility_error(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            psycopg_errors.UndefinedTable,
            psycopg_errors.UndefinedColumn,
            psycopg_errors.UndefinedFunction,
        ),
    )
