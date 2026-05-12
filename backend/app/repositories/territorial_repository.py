from typing import Any

from app.database import get_cursor

OFFICIAL_ZONE_TYPES = ("JURISDICCION", "SECTOR")
REQUIRED_STAGING_COLUMNS = (
    "id_comisaria_original",
    "id_comisaria_resuelta",
    "nombre_comisaria_resuelta",
    "estado_territorial",
    "regla_territorial",
    "motivo_territorial",
    "conflicto_territorial",
)


def territorial_assignment_columns_ready() -> bool:
    with get_cursor() as cur:
        return _territorial_assignment_columns_ready(cur)


def _territorial_assignment_columns_ready(cur) -> bool:
    return _table_has_columns(cur, "comisarias", ("codigo_cpnp",)) and _table_has_columns(
        cur,
        "staging_eventos",
        REQUIRED_STAGING_COLUMNS,
    )


def _table_has_columns(cur, table_name: str, column_names: tuple[str, ...]) -> bool:
    cur.execute(
        """
        SELECT COUNT(*)::INT AS total
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND column_name = ANY(%s);
        """,
        (table_name, list(column_names)),
    )
    row = cur.fetchone() or {}
    return int(row.get("total", 0)) == len(column_names)


def fetch_official_catalog_status(cur) -> dict[str, Any]:
    cur.execute(
        """
        SELECT
            (
                SELECT COUNT(*)::INT
                FROM zonas_operativas z
                WHERE z.tipo_zona = 'JURISDICCION'
                  AND z.estado_zona = 'ACTIVA'
                  AND z.id_comisaria IS NOT NULL
            ) AS total_jurisdicciones,
            (
                SELECT COUNT(*)::INT
                FROM zonas_operativas z
                WHERE z.tipo_zona = 'SECTOR'
                  AND z.estado_zona = 'ACTIVA'
                  AND z.id_comisaria IS NOT NULL
            ) AS total_sectores,
            (
                SELECT COUNT(*)::INT
                FROM comisarias c
                WHERE c.codigo_cpnp IS NOT NULL
            ) AS total_comisarias_oficiales;
        """
    )
    row = cur.fetchone() or {}
    return {
        "total_jurisdicciones": int(row.get("total_jurisdicciones", 0)),
        "total_sectores": int(row.get("total_sectores", 0)),
        "total_comisarias_oficiales": int(row.get("total_comisarias_oficiales", 0)),
    }


def fetch_region_catalog_status(cur, region_policial: str) -> dict[str, int]:
    cur.execute(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE z.tipo_zona = 'JURISDICCION'
                  AND z.estado_zona = 'ACTIVA'
            )::INT AS total_jurisdicciones,
            COUNT(*) FILTER (
                WHERE z.tipo_zona = 'SECTOR'
                  AND z.estado_zona = 'ACTIVA'
            )::INT AS total_sectores
        FROM zonas_operativas z
        INNER JOIN comisarias c
            ON c.id_comisaria = z.id_comisaria
        WHERE c.region_policial = %s;
        """,
        (region_policial,),
    )
    row = cur.fetchone() or {}
    return {
        "total_jurisdicciones": int(row.get("total_jurisdicciones", 0)),
        "total_sectores": int(row.get("total_sectores", 0)),
    }


def upsert_official_comisaria(cur, payload: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO comisarias (
            codigo_cpnp,
            nombre_comisaria,
            distrito,
            direccion,
            codigo_unidad,
            region_policial,
            division_policial,
            geom
        ) VALUES (
            %(codigo_cpnp)s,
            %(nombre_comisaria)s,
            %(distrito)s,
            %(direccion)s,
            %(codigo_unidad)s,
            %(region_policial)s,
            %(division_policial)s,
            ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)
        )
        ON CONFLICT (codigo_cpnp)
        DO UPDATE
        SET
            nombre_comisaria = EXCLUDED.nombre_comisaria,
            distrito = EXCLUDED.distrito,
            direccion = COALESCE(EXCLUDED.direccion, comisarias.direccion),
            codigo_unidad = EXCLUDED.codigo_unidad,
            region_policial = EXCLUDED.region_policial,
            division_policial = EXCLUDED.division_policial,
            geom = EXCLUDED.geom;
        """,
        payload,
    )


def upsert_official_zona(cur, payload: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO zonas_operativas (
            codigo_zona,
            nombre_zona,
            tipo_zona,
            distrito,
            id_comisaria,
            prioridad_operativa,
            estado_zona,
            descripcion,
            geom,
            updated_at
        ) VALUES (
            %(codigo_zona)s,
            %(nombre_zona)s,
            %(tipo_zona)s,
            %(distrito)s,
            (
                SELECT c.id_comisaria
                FROM comisarias c
                WHERE c.codigo_cpnp = %(codigo_cpnp)s
                LIMIT 1
            ),
            'MEDIA',
            'ACTIVA',
            %(descripcion)s,
            ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)),
            NOW()
        )
        ON CONFLICT (codigo_zona)
        DO UPDATE
        SET
            nombre_zona = EXCLUDED.nombre_zona,
            tipo_zona = EXCLUDED.tipo_zona,
            distrito = EXCLUDED.distrito,
            id_comisaria = EXCLUDED.id_comisaria,
            prioridad_operativa = EXCLUDED.prioridad_operativa,
            estado_zona = EXCLUDED.estado_zona,
            descripcion = EXCLUDED.descripcion,
            geom = EXCLUDED.geom,
            updated_at = NOW();
        """,
        payload,
    )


def resolve_official_comisaria(cur, *, latitud: float, longitud: float, tipo_zona: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        WITH punto AS (
            SELECT ST_SetSRID(ST_MakePoint(%s, %s), 4326) AS geom
        )
        SELECT DISTINCT
            c.id_comisaria,
            c.nombre_comisaria,
            c.distrito,
            c.codigo_cpnp,
            z.codigo_zona,
            z.nombre_zona
        FROM punto p
        INNER JOIN zonas_operativas z
            ON z.tipo_zona = %s
           AND z.estado_zona = 'ACTIVA'
           AND z.id_comisaria IS NOT NULL
           AND ST_Covers(z.geom, p.geom)
        INNER JOIN comisarias c
            ON c.id_comisaria = z.id_comisaria
        ORDER BY c.id_comisaria, z.codigo_zona
        LIMIT 2;
        """,
        (longitud, latitud, tipo_zona),
    )
    return cur.fetchall()


def refresh_territorial_dimension_if_available(cur) -> bool:
    cur.execute(
        """
        SELECT
            EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'dim_territorios'
            ) AS has_dimension,
            EXISTS (
                SELECT 1
                FROM pg_proc p
                INNER JOIN pg_namespace n
                    ON n.oid = p.pronamespace
                WHERE n.nspname = 'public'
                  AND p.proname = 'siged_refresh_territorial_dimension'
            ) AS has_refresh_function;
        """
    )
    availability = cur.fetchone() or {}

    if not availability.get("has_dimension") or not availability.get("has_refresh_function"):
        return False

    cur.execute("SELECT siged_refresh_territorial_dimension();")
    return True
