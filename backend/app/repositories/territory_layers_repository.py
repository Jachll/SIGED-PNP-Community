import json
from contextlib import contextmanager
from typing import Any

from app.database import get_cursor
from app.observability import log_structured
from app.territorial import normalize_territory_name

POLYGON_LAYER_IDS = {"regiones", "divisiones", "jurisdicciones", "sectores"}
LAYER_TABLES = {
    "regiones": "territorio_regiones",
    "divisiones": "territorio_divisiones",
    "comisarias": "territorio_comisarias",
    "jurisdicciones": "territorio_jurisdicciones",
    "sectores": "territorio_sectores",
}


@contextmanager
def _cursor_context(cur=None):
    if cur is not None:
        log_structured(
            "siged.territory.repository",
            "territory_cursor_context",
            mode="reuse",
        )
        yield cur
        return

    log_structured(
        "siged.territory.repository",
        "territory_cursor_context",
        mode="managed_open",
    )
    with get_cursor() as managed_cur:
        yield managed_cur
    log_structured(
        "siged.territory.repository",
        "territory_cursor_context",
        mode="managed_close",
    )


def territory_layers_source_ready(cur=None) -> bool:
    log_structured(
        "siged.territory.repository",
        "territory_layers_source_ready_started",
        managed_cursor=cur is None,
    )
    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT
                to_regclass('public.territorio_regiones') IS NOT NULL AS has_regiones,
                to_regclass('public.territorio_divisiones') IS NOT NULL AS has_divisiones,
                to_regclass('public.territorio_comisarias') IS NOT NULL AS has_comisarias,
                to_regclass('public.territorio_jurisdicciones') IS NOT NULL AS has_jurisdicciones,
                to_regclass('public.territorio_sectores') IS NOT NULL AS has_sectores;
            """
        )
        availability = active_cur.fetchone() or {}

        if not all(bool(availability.get(key)) for key in availability):
            return False

        active_cur.execute(
            """
            SELECT
                EXISTS (SELECT 1 FROM territorio_regiones WHERE activo = TRUE) AS regiones_ok,
                EXISTS (SELECT 1 FROM territorio_divisiones WHERE activo = TRUE) AS divisiones_ok,
                EXISTS (SELECT 1 FROM territorio_comisarias WHERE activo = TRUE) AS comisarias_ok,
                EXISTS (SELECT 1 FROM territorio_jurisdicciones WHERE activo = TRUE) AS jurisdicciones_ok,
                EXISTS (SELECT 1 FROM territorio_sectores WHERE activo = TRUE) AS sectores_ok;
            """
        )
        readiness = active_cur.fetchone() or {}
        ready = all(bool(readiness.get(key)) for key in readiness)
        log_structured(
            "siged.territory.repository",
            "territory_layers_source_ready_finished",
            managed_cursor=cur is None,
            ready=ready,
            availability=availability,
            readiness=readiness,
        )
        return ready


def fetch_layer_storage_stats(cur=None) -> dict[str, dict[str, int]]:
    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT
                c.relname AS table_name,
                pg_total_relation_size(c.oid)::BIGINT AS size_bytes,
                COALESCE(s.n_live_tup, 0)::BIGINT AS feature_count
            FROM pg_class c
            LEFT JOIN pg_stat_user_tables s
                ON s.relid = c.oid
            WHERE c.relkind = 'r'
              AND c.relname = ANY(%s);
            """,
            (list(LAYER_TABLES.values()),),
        )
        rows = active_cur.fetchall()
        return {
            row["table_name"]: {
                "size_bytes": int(row.get("size_bytes", 0) or 0),
                "feature_count": int(row.get("feature_count", 0) or 0),
            }
            for row in rows
        }


def fetch_regions(cur=None) -> list[dict[str, Any]]:
    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT
                r.id_region AS id,
                r.codigo_region AS code,
                r.nombre_region AS name
            FROM territorio_regiones r
            WHERE r.activo = TRUE
            ORDER BY r.nombre_region;
            """
        )
        return active_cur.fetchall()


def fetch_divisions(
    *,
    region_id: int | None = None,
    region: str | None = None,
    cur=None,
) -> list[dict[str, Any]]:
    normalized_region = normalize_territory_name(region) or None

    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT
                d.id_division AS id,
                d.codigo_division AS code,
                d.nombre_division AS name,
                d.id_region AS parent_id
            FROM territorio_divisiones d
            INNER JOIN territorio_regiones r
                ON r.id_region = d.id_region
            WHERE d.activo = TRUE
              AND r.activo = TRUE
              AND (%s IS NULL OR d.id_region = %s)
              AND (%s IS NULL OR r.nombre_normalizado = %s)
            ORDER BY d.nombre_division;
            """,
            (region_id, region_id, normalized_region, normalized_region),
        )
        return active_cur.fetchall()


def fetch_comisarias(
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    cur=None,
) -> list[dict[str, Any]]:
    normalized_region = normalize_territory_name(region) or None
    normalized_division = normalize_territory_name(division) or None

    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT
                c.id_territorio_comisaria AS id,
                c.codigo_cpnp AS code,
                c.nombre_comisaria AS name,
                c.id_division AS parent_id,
                c.id_region AS region_id
            FROM territorio_comisarias c
            INNER JOIN territorio_divisiones d
                ON d.id_division = c.id_division
            INNER JOIN territorio_regiones r
                ON r.id_region = c.id_region
            WHERE c.activo = TRUE
              AND d.activo = TRUE
              AND r.activo = TRUE
              AND (%s IS NULL OR c.id_region = %s)
              AND (%s IS NULL OR r.nombre_normalizado = %s)
              AND (%s IS NULL OR c.id_division = %s)
              AND (%s IS NULL OR d.nombre_normalizado = %s)
            ORDER BY c.nombre_comisaria;
            """,
            (
                region_id,
                region_id,
                normalized_region,
                normalized_region,
                division_id,
                division_id,
                normalized_division,
                normalized_division,
            ),
        )
        return active_cur.fetchall()


def scope_bbox_matches_comisaria(
    *,
    bbox: tuple[float, float, float, float] | None,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
    cur=None,
) -> bool:
    if bbox is None:
        return True

    normalized_region = normalize_territory_name(region) or None
    normalized_division = normalize_territory_name(division) or None
    normalized_comisaria = normalize_territory_name(comisaria) or None
    min_lng, min_lat, max_lng, max_lat = bbox

    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM territorio_comisarias c
                INNER JOIN territorio_divisiones d
                    ON d.id_division = c.id_division
                INNER JOIN territorio_regiones r
                    ON r.id_region = c.id_region
                WHERE c.activo = TRUE
                  AND d.activo = TRUE
                  AND r.activo = TRUE
                  AND (%s IS NULL OR c.id_region = %s)
                  AND (%s IS NULL OR r.nombre_normalizado = %s)
                  AND (%s IS NULL OR c.id_division = %s)
                  AND (%s IS NULL OR d.nombre_normalizado = %s)
                  AND (%s IS NULL OR c.id_territorio_comisaria = %s)
                  AND (%s IS NULL OR c.nombre_normalizado = %s)
                  AND ST_Intersects(
                        c.geom,
                        ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                      )
            ) AS matches;
            """,
            (
                region_id,
                region_id,
                normalized_region,
                normalized_region,
                division_id,
                division_id,
                normalized_division,
                normalized_division,
                comisaria_id,
                comisaria_id,
                normalized_comisaria,
                normalized_comisaria,
                min_lng,
                min_lat,
                max_lng,
                max_lat,
            ),
        )
        row = active_cur.fetchone() or {}
        return bool(row.get("matches"))


def fetch_jurisdicciones(
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
    cur=None,
) -> list[dict[str, Any]]:
    normalized_region = normalize_territory_name(region) or None
    normalized_division = normalize_territory_name(division) or None
    normalized_comisaria = normalize_territory_name(comisaria) or None

    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT
                j.id_jurisdiccion AS id,
                COALESCE(j.source_objectid::TEXT, j.codigo_jurisdiccion) AS value,
                j.nombre_jurisdiccion AS label,
                j.id_territorio_comisaria AS parent_id,
                j.codigo_jurisdiccion AS code
            FROM territorio_jurisdicciones j
            INNER JOIN territorio_comisarias c
                ON c.id_territorio_comisaria = j.id_territorio_comisaria
            INNER JOIN territorio_divisiones d
                ON d.id_division = j.id_division
            INNER JOIN territorio_regiones r
                ON r.id_region = j.id_region
            WHERE j.activo = TRUE
              AND c.activo = TRUE
              AND d.activo = TRUE
              AND r.activo = TRUE
              AND (%s IS NULL OR j.id_region = %s)
              AND (%s IS NULL OR r.nombre_normalizado = %s)
              AND (%s IS NULL OR j.id_division = %s)
              AND (%s IS NULL OR d.nombre_normalizado = %s)
              AND (%s IS NULL OR j.id_territorio_comisaria = %s)
              AND (%s IS NULL OR c.nombre_normalizado = %s)
            ORDER BY j.nombre_jurisdiccion, value;
            """,
            (
                region_id,
                region_id,
                normalized_region,
                normalized_region,
                division_id,
                division_id,
                normalized_division,
                normalized_division,
                comisaria_id,
                comisaria_id,
                normalized_comisaria,
                normalized_comisaria,
            ),
        )
        return active_cur.fetchall()


def fetch_sectores(
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
    cur=None,
) -> list[dict[str, Any]]:
    normalized_region = normalize_territory_name(region) or None
    normalized_division = normalize_territory_name(division) or None
    normalized_comisaria = normalize_territory_name(comisaria) or None

    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT
                s.id_sector AS id,
                COALESCE(s.codigo_sector, s.sector_codigo, s.source_objectid::TEXT) AS value,
                s.label_sector AS label,
                s.id_territorio_comisaria AS parent_id,
                s.codigo_sector AS code
            FROM territorio_sectores s
            INNER JOIN territorio_comisarias c
                ON c.id_territorio_comisaria = s.id_territorio_comisaria
            INNER JOIN territorio_divisiones d
                ON d.id_division = s.id_division
            INNER JOIN territorio_regiones r
                ON r.id_region = s.id_region
            WHERE s.activo = TRUE
              AND c.activo = TRUE
              AND d.activo = TRUE
              AND r.activo = TRUE
              AND (%s IS NULL OR s.id_region = %s)
              AND (%s IS NULL OR r.nombre_normalizado = %s)
              AND (%s IS NULL OR s.id_division = %s)
              AND (%s IS NULL OR d.nombre_normalizado = %s)
              AND (%s IS NULL OR s.id_territorio_comisaria = %s)
              AND (%s IS NULL OR c.nombre_normalizado = %s)
            ORDER BY s.label_sector, value;
            """,
            (
                region_id,
                region_id,
                normalized_region,
                normalized_region,
                division_id,
                division_id,
                normalized_division,
                normalized_division,
                comisaria_id,
                comisaria_id,
                normalized_comisaria,
                normalized_comisaria,
            ),
        )
        return active_cur.fetchall()


def find_region_for_point(*, latitud: float, longitud: float, cur=None) -> str | None:
    with _cursor_context(cur) as active_cur:
        active_cur.execute(
            """
            SELECT r.nombre_region
            FROM territorio_regiones r
            WHERE r.activo = TRUE
              AND ST_Covers(
                    COALESCE(r.geom_simplified, r.geom),
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                  )
            ORDER BY r.id_region
            LIMIT 1;
            """,
            (longitud, latitud),
        )
        row = active_cur.fetchone() or {}
        return row.get("nombre_region")


def fetch_layer_feature_collection(
    layer_id: str,
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
    jurisdiccion: str | None = None,
    sector: str | None = None,
    detail: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    cur=None,
) -> dict[str, Any]:
    rows = _fetch_layer_rows(
        layer_id,
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        detail=detail,
        bbox=bbox,
        cur=cur,
    )

    features = []
    for row in rows:
        geometry_geojson = row.get("geometry_geojson")
        if not geometry_geojson:
            continue

        properties = row.get("source_properties") or {}
        if isinstance(properties, str):
            properties = json.loads(properties)

        features.append(
            {
                "type": "Feature",
                "id": row["feature_id"],
                "geometry": json.loads(geometry_geojson),
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def _fetch_layer_rows(
    layer_id: str,
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
    jurisdiccion: str | None = None,
    sector: str | None = None,
    detail: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    cur=None,
) -> list[dict[str, Any]]:
    normalized_region = normalize_territory_name(region) or None
    normalized_division = normalize_territory_name(division) or None
    normalized_comisaria = normalize_territory_name(comisaria) or None
    normalized_jurisdiccion = str(jurisdiccion or "").strip() or None
    normalized_sector = str(sector or "").strip() or None
    detail_mode = (detail or "auto").strip().lower()

    geom_alias = "geom"
    use_simplified = detail_mode != "full" and layer_id in POLYGON_LAYER_IDS

    if layer_id == "regiones":
        query = _build_regions_query(use_simplified=use_simplified, has_bbox=bbox is not None)
        params = _build_bbox_params(
            region_id=region_id,
            region=normalized_region,
            bbox=bbox,
        )
    elif layer_id == "divisiones":
        query = _build_divisiones_query(use_simplified=use_simplified, has_bbox=bbox is not None)
        params = _build_bbox_params(
            region_id=region_id,
            region=normalized_region,
            division_id=division_id,
            division=normalized_division,
            bbox=bbox,
        )
    elif layer_id == "comisarias":
        query = _build_comisarias_query(has_bbox=bbox is not None)
        params = _build_bbox_params(
            region_id=region_id,
            region=normalized_region,
            division_id=division_id,
            division=normalized_division,
            comisaria_id=comisaria_id,
            comisaria=normalized_comisaria,
            bbox=bbox,
        )
    elif layer_id == "jurisdicciones":
        query = _build_jurisdicciones_query(use_simplified=use_simplified, has_bbox=bbox is not None)
        params = _build_bbox_params(
            region_id=region_id,
            region=normalized_region,
            division_id=division_id,
            division=normalized_division,
            comisaria_id=comisaria_id,
            comisaria=normalized_comisaria,
            jurisdiccion=normalized_jurisdiccion,
            bbox=bbox,
        )
    elif layer_id == "sectores":
        query = _build_sectores_query(use_simplified=use_simplified, has_bbox=bbox is not None)
        params = _build_bbox_params(
            region_id=region_id,
            region=normalized_region,
            division_id=division_id,
            division=normalized_division,
            comisaria_id=comisaria_id,
            comisaria=normalized_comisaria,
            sector=normalized_sector,
            sector_normalized=normalize_territory_name(normalized_sector) or None,
            bbox=bbox,
        )
    else:
        return []

    with _cursor_context(cur) as active_cur:
        active_cur.execute(query, params)
        return active_cur.fetchall()


def _build_bbox_params(**kwargs) -> dict[str, Any]:
    bbox = kwargs.pop("bbox", None)
    params = {**kwargs}
    if bbox is None:
        params.update(
            {
                "bbox_min_lng": None,
                "bbox_min_lat": None,
                "bbox_max_lng": None,
                "bbox_max_lat": None,
            }
        )
        return params

    min_lng, min_lat, max_lng, max_lat = bbox
    params.update(
        {
            "bbox_min_lng": min_lng,
            "bbox_min_lat": min_lat,
            "bbox_max_lng": max_lng,
            "bbox_max_lat": max_lat,
        }
    )
    return params


def _bbox_condition(geom_expression: str) -> str:
    return f"""
      AND (
            %(bbox_min_lng)s IS NULL
            OR ST_Intersects(
                {geom_expression},
                ST_MakeEnvelope(
                    %(bbox_min_lng)s,
                    %(bbox_min_lat)s,
                    %(bbox_max_lng)s,
                    %(bbox_max_lat)s,
                    4326
                )
            )
          )
    """


def _build_regions_query(*, use_simplified: bool, has_bbox: bool) -> str:
    geom_expression = "COALESCE(r.geom_simplified, r.geom)" if use_simplified else "r.geom"
    bbox_clause = _bbox_condition(geom_expression) if has_bbox else ""
    return f"""
        SELECT
            r.id_region AS feature_id,
            r.source_properties,
            ST_AsGeoJSON({geom_expression}, 6) AS geometry_geojson
        FROM territorio_regiones r
        WHERE r.activo = TRUE
          AND (%(region_id)s IS NULL OR r.id_region = %(region_id)s)
          AND (%(region)s IS NULL OR r.nombre_normalizado = %(region)s)
          {bbox_clause}
        ORDER BY r.nombre_region;
    """


def _build_divisiones_query(*, use_simplified: bool, has_bbox: bool) -> str:
    geom_expression = "COALESCE(d.geom_simplified, d.geom)" if use_simplified else "d.geom"
    bbox_clause = _bbox_condition(geom_expression) if has_bbox else ""
    return f"""
        SELECT
            d.id_division AS feature_id,
            d.source_properties,
            ST_AsGeoJSON({geom_expression}, 6) AS geometry_geojson
        FROM territorio_divisiones d
        INNER JOIN territorio_regiones r
            ON r.id_region = d.id_region
        WHERE d.activo = TRUE
          AND r.activo = TRUE
          AND (%(region_id)s IS NULL OR d.id_region = %(region_id)s)
          AND (%(region)s IS NULL OR r.nombre_normalizado = %(region)s)
          AND (%(division_id)s IS NULL OR d.id_division = %(division_id)s)
          AND (%(division)s IS NULL OR d.nombre_normalizado = %(division)s)
          {bbox_clause}
        ORDER BY d.nombre_division;
    """


def _build_comisarias_query(*, has_bbox: bool) -> str:
    bbox_clause = _bbox_condition("c.geom") if has_bbox else ""
    return f"""
        SELECT
            c.id_territorio_comisaria AS feature_id,
            c.source_properties,
            ST_AsGeoJSON(c.geom, 6) AS geometry_geojson
        FROM territorio_comisarias c
        INNER JOIN territorio_divisiones d
            ON d.id_division = c.id_division
        INNER JOIN territorio_regiones r
            ON r.id_region = c.id_region
        WHERE c.activo = TRUE
          AND d.activo = TRUE
          AND r.activo = TRUE
          AND (%(region_id)s IS NULL OR c.id_region = %(region_id)s)
          AND (%(region)s IS NULL OR r.nombre_normalizado = %(region)s)
          AND (%(division_id)s IS NULL OR c.id_division = %(division_id)s)
          AND (%(division)s IS NULL OR d.nombre_normalizado = %(division)s)
          AND (%(comisaria_id)s IS NULL OR c.id_territorio_comisaria = %(comisaria_id)s)
          AND (%(comisaria)s IS NULL OR c.nombre_normalizado = %(comisaria)s)
          {bbox_clause}
        ORDER BY c.nombre_comisaria;
    """


def _build_jurisdicciones_query(*, use_simplified: bool, has_bbox: bool) -> str:
    geom_expression = "COALESCE(j.geom_simplified, j.geom)" if use_simplified else "j.geom"
    bbox_clause = _bbox_condition(geom_expression) if has_bbox else ""
    return f"""
        SELECT
            j.id_jurisdiccion AS feature_id,
            j.source_properties,
            ST_AsGeoJSON({geom_expression}, 6) AS geometry_geojson
        FROM territorio_jurisdicciones j
        INNER JOIN territorio_comisarias c
            ON c.id_territorio_comisaria = j.id_territorio_comisaria
        INNER JOIN territorio_divisiones d
            ON d.id_division = j.id_division
        INNER JOIN territorio_regiones r
            ON r.id_region = j.id_region
        WHERE j.activo = TRUE
          AND c.activo = TRUE
          AND d.activo = TRUE
          AND r.activo = TRUE
          AND (%(region_id)s IS NULL OR j.id_region = %(region_id)s)
          AND (%(region)s IS NULL OR r.nombre_normalizado = %(region)s)
          AND (%(division_id)s IS NULL OR j.id_division = %(division_id)s)
          AND (%(division)s IS NULL OR d.nombre_normalizado = %(division)s)
          AND (%(comisaria_id)s IS NULL OR j.id_territorio_comisaria = %(comisaria_id)s)
          AND (%(comisaria)s IS NULL OR c.nombre_normalizado = %(comisaria)s)
          AND (
                %(jurisdiccion)s IS NULL
                OR COALESCE(j.source_objectid::TEXT, '') = %(jurisdiccion)s
                OR j.codigo_jurisdiccion = %(jurisdiccion)s
              )
          {bbox_clause}
        ORDER BY j.nombre_jurisdiccion;
    """


def _build_sectores_query(*, use_simplified: bool, has_bbox: bool) -> str:
    geom_expression = "COALESCE(s.geom_simplified, s.geom)" if use_simplified else "s.geom"
    bbox_clause = _bbox_condition(geom_expression) if has_bbox else ""
    return f"""
        SELECT
            s.id_sector AS feature_id,
            s.source_properties,
            ST_AsGeoJSON({geom_expression}, 6) AS geometry_geojson
        FROM territorio_sectores s
        INNER JOIN territorio_comisarias c
            ON c.id_territorio_comisaria = s.id_territorio_comisaria
        INNER JOIN territorio_divisiones d
            ON d.id_division = s.id_division
        INNER JOIN territorio_regiones r
            ON r.id_region = s.id_region
        WHERE s.activo = TRUE
          AND c.activo = TRUE
          AND d.activo = TRUE
          AND r.activo = TRUE
          AND (%(region_id)s IS NULL OR s.id_region = %(region_id)s)
          AND (%(region)s IS NULL OR r.nombre_normalizado = %(region)s)
          AND (%(division_id)s IS NULL OR s.id_division = %(division_id)s)
          AND (%(division)s IS NULL OR d.nombre_normalizado = %(division)s)
          AND (%(comisaria_id)s IS NULL OR s.id_territorio_comisaria = %(comisaria_id)s)
          AND (%(comisaria)s IS NULL OR c.nombre_normalizado = %(comisaria)s)
          AND (
                %(sector)s IS NULL
                OR COALESCE(s.codigo_sector, '') = %(sector)s
                OR COALESCE(s.sector_codigo, '') = %(sector)s
                OR COALESCE(s.source_objectid::TEXT, '') = %(sector)s
                OR COALESCE(s.label_normalizado, '') = %(sector_normalized)s
              )
          {bbox_clause}
        ORDER BY s.label_sector;
    """
