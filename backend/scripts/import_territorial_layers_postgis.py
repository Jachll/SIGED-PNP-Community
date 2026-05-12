import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import get_cursor
from app.etl.operational_sync import sync_operational_catalog_for_regions, try_refresh_territorial_dimension
from app.geo_layers import _build_layer_path, _iter_geojson_features
from app.territorial import normalize_territory_name

SIMPLIFICATION_TOLERANCES = {
    "regiones": 0.0020,
    "divisiones": 0.0010,
    "jurisdicciones": 0.00025,
    "sectores": 0.00010,
}

TERRITORY_TABLES = (
    "territorio_regiones",
    "territorio_divisiones",
    "territorio_comisarias",
    "territorio_jurisdicciones",
    "territorio_sectores",
)


def _mark_layers_inactive(cur) -> None:
    for table_name in TERRITORY_TABLES:
        cur.execute(f"UPDATE {table_name} SET activo = FALSE, updated_at = NOW();")


def _upsert_region(cur, properties: dict, geometry: dict) -> int:
    cur.execute(
        """
        INSERT INTO territorio_regiones (
            source_objectid,
            codigo_region,
            nombre_region,
            nombre_normalizado,
            macroregion_codigo,
            macroregion_nombre,
            area_km2,
            perimetro_km,
            activo,
            source_properties,
            geom,
            geom_simplified,
            updated_at
        ) VALUES (
            %(source_objectid)s,
            %(codigo_region)s,
            %(nombre_region)s,
            %(nombre_normalizado)s,
            %(macroregion_codigo)s,
            %(macroregion_nombre)s,
            %(area_km2)s,
            %(perimetro_km)s,
            TRUE,
            %(source_properties)s::jsonb,
            ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)), 3)),
            ST_Multi(
                ST_CollectionExtract(
                    ST_SimplifyPreserveTopology(
                        ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)),
                        %(tolerance)s
                    ),
                    3
                )
            ),
            NOW()
        )
        ON CONFLICT (codigo_region)
        DO UPDATE
        SET
            source_objectid = EXCLUDED.source_objectid,
            nombre_region = EXCLUDED.nombre_region,
            nombre_normalizado = EXCLUDED.nombre_normalizado,
            macroregion_codigo = EXCLUDED.macroregion_codigo,
            macroregion_nombre = EXCLUDED.macroregion_nombre,
            area_km2 = EXCLUDED.area_km2,
            perimetro_km = EXCLUDED.perimetro_km,
            activo = TRUE,
            source_properties = EXCLUDED.source_properties,
            geom = EXCLUDED.geom,
            geom_simplified = EXCLUDED.geom_simplified,
            updated_at = NOW()
        RETURNING id_region;
        """,
        {
            "source_objectid": properties.get("objectid"),
            "codigo_region": str(properties.get("cod_regpol") or properties.get("objectid")),
            "nombre_region": normalize_territory_name(properties.get("regionpol")),
            "nombre_normalizado": normalize_territory_name(properties.get("regionpol")),
            "macroregion_codigo": properties.get("cod_macroregpol"),
            "macroregion_nombre": properties.get("macroregpol"),
            "area_km2": properties.get("area_km2"),
            "perimetro_km": properties.get("perimetro_km"),
            "source_properties": json.dumps(properties, ensure_ascii=False),
            "geom_geojson": json.dumps(geometry, ensure_ascii=True),
            "tolerance": SIMPLIFICATION_TOLERANCES["regiones"],
        },
    )
    return int(cur.fetchone()["id_region"])


def _upsert_division(cur, properties: dict, geometry: dict, *, region_id: int) -> int:
    cur.execute(
        """
        INSERT INTO territorio_divisiones (
            id_region,
            source_objectid,
            codigo_division,
            nombre_division,
            nombre_normalizado,
            area_km2,
            perimetro_km,
            activo,
            source_properties,
            geom,
            geom_simplified,
            updated_at
        ) VALUES (
            %(id_region)s,
            %(source_objectid)s,
            %(codigo_division)s,
            %(nombre_division)s,
            %(nombre_normalizado)s,
            %(area_km2)s,
            %(perimetro_km)s,
            TRUE,
            %(source_properties)s::jsonb,
            ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)), 3)),
            ST_Multi(
                ST_CollectionExtract(
                    ST_SimplifyPreserveTopology(
                        ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)),
                        %(tolerance)s
                    ),
                    3
                )
            ),
            NOW()
        )
        ON CONFLICT (codigo_division)
        DO UPDATE
        SET
            id_region = EXCLUDED.id_region,
            source_objectid = EXCLUDED.source_objectid,
            nombre_division = EXCLUDED.nombre_division,
            nombre_normalizado = EXCLUDED.nombre_normalizado,
            area_km2 = EXCLUDED.area_km2,
            perimetro_km = EXCLUDED.perimetro_km,
            activo = TRUE,
            source_properties = EXCLUDED.source_properties,
            geom = EXCLUDED.geom,
            geom_simplified = EXCLUDED.geom_simplified,
            updated_at = NOW()
        RETURNING id_division;
        """,
        {
            "id_region": region_id,
            "source_objectid": properties.get("objectid"),
            "codigo_division": str(properties.get("cod_divpol_divopus") or properties.get("objectid")),
            "nombre_division": normalize_territory_name(properties.get("divpol_divopus")),
            "nombre_normalizado": normalize_territory_name(properties.get("divpol_divopus")),
            "area_km2": properties.get("area_km2"),
            "perimetro_km": properties.get("perimetro_km"),
            "source_properties": json.dumps(properties, ensure_ascii=False),
            "geom_geojson": json.dumps(geometry, ensure_ascii=True),
            "tolerance": SIMPLIFICATION_TOLERANCES["divisiones"],
        },
    )
    return int(cur.fetchone()["id_division"])


def _upsert_comisaria(cur, properties: dict, geometry: dict, *, region_id: int, division_id: int) -> int:
    cur.execute(
        """
        INSERT INTO territorio_comisarias (
            id_region,
            id_division,
            source_objectid,
            codigo_cpnp,
            codigo_unidad,
            nombre_comisaria,
            nombre_normalizado,
            tipo_comisaria,
            codigo_inei,
            departamento,
            provincia,
            distrito,
            activo,
            source_properties,
            geom,
            updated_at
        ) VALUES (
            %(id_region)s,
            %(id_division)s,
            %(source_objectid)s,
            %(codigo_cpnp)s,
            %(codigo_unidad)s,
            %(nombre_comisaria)s,
            %(nombre_normalizado)s,
            %(tipo_comisaria)s,
            %(codigo_inei)s,
            %(departamento)s,
            %(provincia)s,
            %(distrito)s,
            TRUE,
            %(source_properties)s::jsonb,
            ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326),
            NOW()
        )
        ON CONFLICT (codigo_cpnp)
        DO UPDATE
        SET
            id_region = EXCLUDED.id_region,
            id_division = EXCLUDED.id_division,
            source_objectid = EXCLUDED.source_objectid,
            codigo_unidad = EXCLUDED.codigo_unidad,
            nombre_comisaria = EXCLUDED.nombre_comisaria,
            nombre_normalizado = EXCLUDED.nombre_normalizado,
            tipo_comisaria = EXCLUDED.tipo_comisaria,
            codigo_inei = EXCLUDED.codigo_inei,
            departamento = EXCLUDED.departamento,
            provincia = EXCLUDED.provincia,
            distrito = EXCLUDED.distrito,
            activo = TRUE,
            source_properties = EXCLUDED.source_properties,
            geom = EXCLUDED.geom,
            updated_at = NOW()
        RETURNING id_territorio_comisaria;
        """,
        {
            "id_region": region_id,
            "id_division": division_id,
            "source_objectid": properties.get("objectid"),
            "codigo_cpnp": str(properties.get("cod_cpnp") or properties.get("objectid")),
            "codigo_unidad": properties.get("cod_uni"),
            "nombre_comisaria": normalize_territory_name(properties.get("comisaria")),
            "nombre_normalizado": normalize_territory_name(properties.get("comisaria")),
            "tipo_comisaria": properties.get("tipo_comi"),
            "codigo_inei": properties.get("cod_inei"),
            "departamento": normalize_territory_name(properties.get("departamento")) or None,
            "provincia": normalize_territory_name(properties.get("provincia")) or None,
            "distrito": normalize_territory_name(properties.get("distrito")) or None,
            "source_properties": json.dumps(properties, ensure_ascii=False),
            "geom_geojson": json.dumps(geometry, ensure_ascii=True),
        },
    )
    return int(cur.fetchone()["id_territorio_comisaria"])


def _upsert_jurisdiccion(cur, properties: dict, geometry: dict, *, region_id: int, division_id: int, comisaria_id: int) -> None:
    object_id = str(properties.get("objectid") or "")
    codigo_cpnp = str(properties.get("cod_cpnp") or "")
    nombre_comisaria = normalize_territory_name(properties.get("comisaria"))
    cur.execute(
        """
        INSERT INTO territorio_jurisdicciones (
            id_region,
            id_division,
            id_territorio_comisaria,
            source_objectid,
            codigo_jurisdiccion,
            nombre_jurisdiccion,
            nombre_normalizado,
            tipo_cobertura,
            codigo_inei,
            codigo_unidad,
            sectores_referencia,
            area_km2,
            activo,
            source_properties,
            geom,
            geom_simplified,
            updated_at
        ) VALUES (
            %(id_region)s,
            %(id_division)s,
            %(id_territorio_comisaria)s,
            %(source_objectid)s,
            %(codigo_jurisdiccion)s,
            %(nombre_jurisdiccion)s,
            %(nombre_normalizado)s,
            %(tipo_cobertura)s,
            %(codigo_inei)s,
            %(codigo_unidad)s,
            %(sectores_referencia)s,
            %(area_km2)s,
            TRUE,
            %(source_properties)s::jsonb,
            ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)), 3)),
            ST_Multi(
                ST_CollectionExtract(
                    ST_SimplifyPreserveTopology(
                        ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)),
                        %(tolerance)s
                    ),
                    3
                )
            ),
            NOW()
        )
        ON CONFLICT (codigo_jurisdiccion)
        DO UPDATE
        SET
            id_region = EXCLUDED.id_region,
            id_division = EXCLUDED.id_division,
            id_territorio_comisaria = EXCLUDED.id_territorio_comisaria,
            source_objectid = EXCLUDED.source_objectid,
            nombre_jurisdiccion = EXCLUDED.nombre_jurisdiccion,
            nombre_normalizado = EXCLUDED.nombre_normalizado,
            tipo_cobertura = EXCLUDED.tipo_cobertura,
            codigo_inei = EXCLUDED.codigo_inei,
            codigo_unidad = EXCLUDED.codigo_unidad,
            sectores_referencia = EXCLUDED.sectores_referencia,
            area_km2 = EXCLUDED.area_km2,
            activo = TRUE,
            source_properties = EXCLUDED.source_properties,
            geom = EXCLUDED.geom,
            geom_simplified = EXCLUDED.geom_simplified,
            updated_at = NOW();
        """,
        {
            "id_region": region_id,
            "id_division": division_id,
            "id_territorio_comisaria": comisaria_id,
            "source_objectid": properties.get("objectid"),
            "codigo_jurisdiccion": f"JUR-{codigo_cpnp or 'SINCOMISARIA'}-{object_id or 'SINOBJECTID'}",
            "nombre_jurisdiccion": f"JURISDICCION {nombre_comisaria}".strip(),
            "nombre_normalizado": f"JURISDICCION {nombre_comisaria}".strip(),
            "tipo_cobertura": properties.get("tipo_cobertura"),
            "codigo_inei": properties.get("cod_inei"),
            "codigo_unidad": properties.get("cod_uni"),
            "sectores_referencia": properties.get("sectores"),
            "area_km2": properties.get("area_km2"),
            "source_properties": json.dumps(properties, ensure_ascii=False),
            "geom_geojson": json.dumps(geometry, ensure_ascii=True),
            "tolerance": SIMPLIFICATION_TOLERANCES["jurisdicciones"],
        },
    )


def _upsert_sector(cur, properties: dict, geometry: dict, *, region_id: int, division_id: int, comisaria_id: int) -> None:
    object_id = str(properties.get("objectid") or "")
    codigo_sector = str(properties.get("cod_sector") or "") or f"SEC-SINCOD-{object_id or 'SINOBJECTID'}"
    sector_code = str(properties.get("sector") or "")
    label = (
        str(properties.get("label") or "").strip()
        or f"SECTOR {sector_code}".strip()
        or f"SECTOR {object_id}".strip()
    )
    cur.execute(
        """
        INSERT INTO territorio_sectores (
            id_region,
            id_division,
            id_territorio_comisaria,
            source_objectid,
            codigo_sector,
            sector_codigo,
            label_sector,
            label_normalizado,
            clase_sector,
            codigo_unidad,
            codigo_inei,
            area_km2,
            activo,
            source_properties,
            geom,
            geom_simplified,
            updated_at
        ) VALUES (
            %(id_region)s,
            %(id_division)s,
            %(id_territorio_comisaria)s,
            %(source_objectid)s,
            %(codigo_sector)s,
            %(sector_codigo)s,
            %(label_sector)s,
            %(label_normalizado)s,
            %(clase_sector)s,
            %(codigo_unidad)s,
            %(codigo_inei)s,
            %(area_km2)s,
            TRUE,
            %(source_properties)s::jsonb,
            ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)), 3)),
            ST_Multi(
                ST_CollectionExtract(
                    ST_SimplifyPreserveTopology(
                        ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_geojson)s), 4326)),
                        %(tolerance)s
                    ),
                    3
                )
            ),
            NOW()
        )
        ON CONFLICT (codigo_sector)
        DO UPDATE
        SET
            id_region = EXCLUDED.id_region,
            id_division = EXCLUDED.id_division,
            id_territorio_comisaria = EXCLUDED.id_territorio_comisaria,
            source_objectid = EXCLUDED.source_objectid,
            sector_codigo = EXCLUDED.sector_codigo,
            label_sector = EXCLUDED.label_sector,
            label_normalizado = EXCLUDED.label_normalizado,
            clase_sector = EXCLUDED.clase_sector,
            codigo_unidad = EXCLUDED.codigo_unidad,
            codigo_inei = EXCLUDED.codigo_inei,
            area_km2 = EXCLUDED.area_km2,
            activo = TRUE,
            source_properties = EXCLUDED.source_properties,
            geom = EXCLUDED.geom,
            geom_simplified = EXCLUDED.geom_simplified,
            updated_at = NOW();
        """,
        {
            "id_region": region_id,
            "id_division": division_id,
            "id_territorio_comisaria": comisaria_id,
            "source_objectid": properties.get("objectid"),
            "codigo_sector": codigo_sector,
            "sector_codigo": sector_code or None,
            "label_sector": label[:150],
            "label_normalizado": normalize_territory_name(label)[:150],
            "clase_sector": properties.get("clas_sector"),
            "codigo_unidad": properties.get("cod_uni"),
            "codigo_inei": properties.get("cod_inei"),
            "area_km2": properties.get("area_km2"),
            "source_properties": json.dumps(properties, ensure_ascii=False),
            "geom_geojson": json.dumps(geometry, ensure_ascii=True),
            "tolerance": SIMPLIFICATION_TOLERANCES["sectores"],
        },
    )


def _import_regions(cur) -> dict[str, int]:
    layer_path = _build_layer_path("6_region_policial.geojson")
    region_index: dict[str, int] = {}

    total = 0
    for feature in _iter_geojson_features(layer_path):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        if not geometry:
            continue

        region_id = _upsert_region(cur, properties, geometry)
        region_name = normalize_territory_name(properties.get("regionpol"))
        region_code = str(properties.get("cod_regpol") or properties.get("objectid") or "")
        if region_name:
            region_index[region_name] = region_id
        if region_code:
            region_index[region_code] = region_id
        total += 1

    print(f"[territorio] regiones importadas: {total}")
    return region_index


def _import_divisions(cur, region_index: dict[str, int]) -> dict[str, tuple[int, int]]:
    layer_path = _build_layer_path("5_divisiones_policiales.geojson")
    division_index: dict[str, tuple[int, int]] = {}

    total = 0
    for feature in _iter_geojson_features(layer_path):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        if not geometry:
            continue

        region_key = str(properties.get("cod_regpol") or "")
        region_name = normalize_territory_name(properties.get("regionpol"))
        region_id = region_index.get(region_key) or region_index.get(region_name)
        if region_id is None:
            continue

        division_id = _upsert_division(cur, properties, geometry, region_id=region_id)
        division_name = normalize_territory_name(properties.get("divpol_divopus"))
        division_code = str(properties.get("cod_divpol_divopus") or properties.get("objectid") or "")
        if division_name:
            division_index[division_name] = (division_id, region_id)
        if division_code:
            division_index[division_code] = (division_id, region_id)
        total += 1

    print(f"[territorio] divisiones importadas: {total}")
    return division_index


def _import_comisarias(cur, region_index: dict[str, int], division_index: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int, int]]:
    layer_path = _build_layer_path("2_comisarias_basicas.geojson")
    comisaria_index: dict[str, tuple[int, int, int]] = {}

    total = 0
    for feature in _iter_geojson_features(layer_path):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        if not geometry:
            continue

        region_name = normalize_territory_name(properties.get("regionpol"))
        division_code = str(properties.get("cod_divpol_divopus") or "")
        division_name = normalize_territory_name(properties.get("divpol_divopus"))
        region_id = region_index.get(str(properties.get("cod_regpol") or "")) or region_index.get(region_name)
        division_info = division_index.get(division_code) or division_index.get(division_name)
        if region_id is None or division_info is None:
            continue

        division_id = division_info[0]
        comisaria_id = _upsert_comisaria(cur, properties, geometry, region_id=region_id, division_id=division_id)
        codigo_cpnp = str(properties.get("cod_cpnp") or properties.get("objectid") or "")
        comisaria_name = normalize_territory_name(properties.get("comisaria"))
        if codigo_cpnp:
            comisaria_index[codigo_cpnp] = (comisaria_id, region_id, division_id)
        if comisaria_name:
            comisaria_index[comisaria_name] = (comisaria_id, region_id, division_id)
        total += 1

    print(f"[territorio] comisarias importadas: {total}")
    return comisaria_index


def _import_jurisdicciones(cur, comisaria_index: dict[str, tuple[int, int, int]]) -> int:
    layer_path = _build_layer_path("4_jurisdicciones_comisarias_basicas.geojson")
    total = 0

    for feature in _iter_geojson_features(layer_path):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        if not geometry:
            continue

        comisaria_info = comisaria_index.get(str(properties.get("cod_cpnp") or "")) or comisaria_index.get(
            normalize_territory_name(properties.get("comisaria"))
        )
        if comisaria_info is None:
            continue

        comisaria_id, region_id, division_id = comisaria_info
        _upsert_jurisdiccion(
            cur,
            properties,
            geometry,
            region_id=region_id,
            division_id=division_id,
            comisaria_id=comisaria_id,
        )
        total += 1

    print(f"[territorio] jurisdicciones importadas: {total}")
    return total


def _import_sectores(cur, comisaria_index: dict[str, tuple[int, int, int]]) -> int:
    layer_path = _build_layer_path("3_sectores_comisarias_basicas.geojson")
    total = 0

    for feature in _iter_geojson_features(layer_path):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        if not geometry:
            continue

        comisaria_info = comisaria_index.get(str(properties.get("cod_cpnp") or "")) or comisaria_index.get(
            normalize_territory_name(properties.get("comisaria"))
        )
        if comisaria_info is None:
            continue

        comisaria_id, region_id, division_id = comisaria_info
        _upsert_sector(
            cur,
            properties,
            geometry,
            region_id=region_id,
            division_id=division_id,
            comisaria_id=comisaria_id,
        )
        total += 1

    print(f"[territorio] sectores importados: {total}")
    return total


def _sync_operational_catalog(cur, region_index: dict[str, int]) -> None:
    region_names = sorted(name for name in region_index if not name[:1].isdigit() and "-" not in name)
    for summary in sync_operational_catalog_for_regions(cur, region_names):
        print(
            "[territorio] sync region=%s comisarias=%s jurisdicciones=%s sectores=%s"
            % (
                summary["region"],
                summary["comisarias_upserted"],
                summary["jurisdicciones_upserted"],
                summary["sectores_upserted"],
            )
        )


def run_import(*, sync_operational_catalog: bool) -> None:
    with get_cursor() as cur:
        _mark_layers_inactive(cur)
        region_index = _import_regions(cur)
        division_index = _import_divisions(cur, region_index)
        comisaria_index = _import_comisarias(cur, region_index, division_index)
        _import_jurisdicciones(cur, comisaria_index)
        _import_sectores(cur, comisaria_index)

        if sync_operational_catalog:
            _sync_operational_catalog(cur, region_index)
            dimension_refreshed, dimension_refresh_error = try_refresh_territorial_dimension(cur)
            if dimension_refresh_error:
                print(f"[territorio] warning dimension_refresh_error={dimension_refresh_error}")
            elif dimension_refreshed:
                print("[territorio] dimension territorial refrescada")


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa capas territoriales GeoJSON a PostGIS.")
    parser.add_argument(
        "--skip-operational-sync",
        action="store_true",
        help="No sincroniza comisarias/zonas_operativas despues de cargar las nuevas tablas territoriales.",
    )
    args = parser.parse_args()
    run_import(sync_operational_catalog=not args.skip_operational_sync)


if __name__ == "__main__":
    main()
