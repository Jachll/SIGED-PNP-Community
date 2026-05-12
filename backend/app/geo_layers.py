import json
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Iterator
import unicodedata

from fastapi import HTTPException, status

from app.config import settings
from app.database import get_cursor
from app.observability import log_structured
from app.repositories.territory_layers_repository import (
    fetch_comisarias,
    fetch_divisions,
    fetch_jurisdicciones,
    fetch_layer_feature_collection,
    fetch_layer_storage_stats,
    fetch_regions,
    fetch_sectores,
    find_region_for_point as find_region_for_point_in_db,
    scope_bbox_matches_comisaria,
    territory_layers_source_ready,
)


GEO_LAYER_DEFINITIONS = (
    {
        "id": "regiones",
        "label": "Regiones Policiales",
        "file_name": "6_region_policial.geojson",
        "geometry_type": "poligono",
        "stroke_color": "#be123c",
        "fill_color": "#fda4af",
        "fill_opacity": 0.04,
        "recommended_zoom": 9,
        "region_property": "regionpol",
        "division_property": None,
        "comisaria_property": None,
        "requires_region": True,
        "requires_division": False,
        "requires_comisaria": False,
    },
    {
        "id": "divisiones",
        "label": "Divisiones Policiales",
        "file_name": "5_divisiones_policiales.geojson",
        "geometry_type": "poligono",
        "stroke_color": "#7c3aed",
        "fill_color": "#c4b5fd",
        "fill_opacity": 0.04,
        "recommended_zoom": 10,
        "region_property": "regionpol",
        "division_property": "divpol_divopus",
        "comisaria_property": None,
        "requires_region": True,
        "requires_division": False,
        "requires_comisaria": False,
    },
    {
        "id": "comisarias",
        "label": "Comisarias",
        "file_name": "2_comisarias_basicas.geojson",
        "geometry_type": "mixto",
        "stroke_color": "#0f5f8c",
        "fill_color": "#8cc7e8",
        "fill_opacity": 0.08,
        "recommended_zoom": 11,
        "region_property": "regionpol",
        "division_property": "divpol_divopus",
        "comisaria_property": "comisaria",
        "requires_region": True,
        "requires_division": False,
        "requires_comisaria": False,
    },
    {
        "id": "jurisdicciones",
        "label": "Jurisdicciones de Comisaria",
        "file_name": "4_jurisdicciones_comisarias_basicas.geojson",
        "geometry_type": "poligono",
        "stroke_color": "#256642",
        "fill_color": "#7cc89d",
        "fill_opacity": 0.05,
        "recommended_zoom": 12,
        "region_property": "regionpol",
        "division_property": "divpol_divopus",
        "comisaria_property": "comisaria",
        "requires_region": True,
        "requires_division": False,
        "requires_comisaria": True,
    },
    {
        "id": "sectores",
        "label": "Sectores de Comisaria",
        "file_name": "3_sectores_comisarias_basicas.geojson",
        "geometry_type": "poligono",
        "stroke_color": "#d97706",
        "fill_color": "#f7c66a",
        "fill_opacity": 0.05,
        "recommended_zoom": 13,
        "region_property": "regionpol",
        "division_property": "divpol_divopus",
        "comisaria_property": "comisaria",
        "requires_region": True,
        "requires_division": False,
        "requires_comisaria": True,
    },
)

TERRITORY_LAYER_TABLES = {
    "regiones": "territorio_regiones",
    "divisiones": "territorio_divisiones",
    "comisarias": "territorio_comisarias",
    "jurisdicciones": "territorio_jurisdicciones",
    "sectores": "territorio_sectores",
}


def _cursor_connection_id(cur) -> int | None:
    connection = getattr(cur, "connection", None)
    return id(connection) if connection is not None else None


def _log_territory_source(
    operation: str,
    *,
    source: str,
    layer_id: str | None = None,
    fallback_reason: str | None = None,
    cur=None,
    **details: object,
) -> None:
    payload = {
        "operation": operation,
        "source": source,
        "layer_id": layer_id,
        "fallback_reason": fallback_reason,
        "cursor_mode": "reuse" if cur is not None else "not_used",
        "connection_id": _cursor_connection_id(cur),
    }
    payload.update({key: value for key, value in details.items() if value not in (None, "", [], {})})
    log_structured(
        "siged.territory.source",
        "territory_source_selected",
        **payload,
    )


def _should_use_postgis_source(cur=None) -> bool:
    if settings.geo_layers_force_legacy:
        return False
    return territory_layers_source_ready(cur)


def _build_layer_path(file_name: str) -> Path:
    return settings.geojson_layers_dir / file_name


def _get_region_cache_root() -> Path:
    return settings.geojson_layers_dir / "_cache_by_region"


def _normalize_value(value: str | None) -> str:
    return " ".join((value or "").strip().upper().split())


def _stringify_value(value: Any) -> str:
    return str(value or "").strip()


def _slugify_scope_value(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    compact = re.sub(r"[^A-Za-z0-9]+", "_", normalized.strip().lower()).strip("_")
    return compact or "sin_valor"


def _get_layer_definition(layer_id: str) -> dict[str, Any]:
    normalized_layer_id = _normalize_value(layer_id).lower()

    for layer in GEO_LAYER_DEFINITIONS:
        if layer["id"] == normalized_layer_id:
            return layer

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="La capa geografica solicitada no existe.",
    )


def _get_layer_path(layer: dict[str, Any]) -> Path:
    layer_path = _build_layer_path(layer["file_name"])
    if not layer_path.exists() or not layer_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La capa geografica solicitada no esta disponible en este entorno.",
        )
    return layer_path


def _get_region_cache_path(layer: dict[str, Any], region: str | None) -> Path | None:
    if not region:
        return None

    cache_path = _get_region_cache_root() / layer["id"] / f"{_slugify_scope_value(region)}.geojson"
    return cache_path if cache_path.exists() and cache_path.is_file() else None


def _iter_geojson_features(layer_path: Path) -> Iterator[dict[str, Any]]:
    with layer_path.open("r", encoding="utf-8") as geojson_file:
        found_features_array = False
        inside_feature = False
        depth = 0
        in_string = False
        escape_next = False
        feature_buffer: list[str] = []

        for line in geojson_file:
            if not found_features_array:
                if '"features"' in line and "[" in line:
                    found_features_array = True
                continue

            for character in line:
                if not inside_feature:
                    if character == "{":
                        inside_feature = True
                        depth = 1
                        in_string = False
                        escape_next = False
                        feature_buffer = ["{"]
                    elif character == "]":
                        return
                    continue

                feature_buffer.append(character)

                if in_string:
                    if escape_next:
                        escape_next = False
                    elif character == "\\":
                        escape_next = True
                    elif character == '"':
                        in_string = False
                    continue

                if character == '"':
                    in_string = True
                elif character == "{":
                    depth += 1
                elif character == "}":
                    depth -= 1
                    if depth == 0:
                        inside_feature = False
                        yield json.loads("".join(feature_buffer))
                        feature_buffer = []


def _matches_scope(
    layer: dict[str, Any],
    feature: dict[str, Any],
    *,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
) -> bool:
    properties = feature.get("properties") or {}

    if region and layer["region_property"]:
        feature_region = _normalize_value(properties.get(layer["region_property"]))
        if feature_region != _normalize_value(region):
            return False

    if division and layer["division_property"]:
        feature_division = _normalize_value(properties.get(layer["division_property"]))
        if feature_division != _normalize_value(division):
            return False

    if comisaria and layer["comisaria_property"]:
        feature_comisaria = _normalize_value(properties.get(layer["comisaria_property"]))
        if feature_comisaria != _normalize_value(comisaria):
            return False

    if layer["id"] == "jurisdicciones" and jurisdiccion:
        feature_object_id = _stringify_value(properties.get("objectid"))
        if feature_object_id != _stringify_value(jurisdiccion):
            return False

    if layer["id"] == "sectores" and sector:
        selected_sector = _stringify_value(sector)
        candidate_values = {
            _stringify_value(properties.get("cod_sector")),
            _stringify_value(properties.get("sector")),
            _stringify_value(properties.get("label")),
            _stringify_value(properties.get("objectid")),
        }
        if selected_sector not in candidate_values:
            return False

    return True


def _validate_scope(
    layer: dict[str, Any],
    region: str | None,
    comisaria: str | None,
    *,
    comisaria_id: int | None = None,
) -> None:
    if layer["requires_region"] and not region:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selecciona una region policial antes de cargar esta capa.",
        )

    if layer["requires_comisaria"] and not (comisaria or comisaria_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selecciona una comisaria antes de cargar jurisdicciones o sectores.",
        )


def _parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    if not bbox:
        return None

    try:
        coordinates = tuple(float(item.strip()) for item in bbox.split(","))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El bbox debe tener el formato minLng,minLat,maxLng,maxLat.",
        ) from exc

    if len(coordinates) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El bbox debe tener exactamente cuatro coordenadas.",
        )

    min_lng, min_lat, max_lng, max_lat = coordinates
    if min_lng >= max_lng or min_lat >= max_lat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El bbox enviado no es valido.",
        )

    return min_lng, min_lat, max_lng, max_lat


def _is_full_detail_request(detail: str | None) -> bool:
    return (detail or "auto").strip().lower() == "full"


def _validate_heavy_layer_detail_request(
    layer_id: str,
    *,
    detail: str | None,
    bbox: tuple[float, float, float, float] | None,
    jurisdiccion: str | None,
    sector: str | None,
) -> None:
    if not _is_full_detail_request(detail):
        return

    if layer_id == "jurisdicciones" and not jurisdiccion and bbox is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La capa de jurisdicciones en detalle completo requiere una jurisdiccion especifica "
                "o un bbox vigente. Usa detalle simplificado mientras cambia la comisaria."
            ),
        )

    if layer_id == "sectores" and not sector and bbox is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La capa de sectores en detalle completo requiere un sector especifico "
                "o un bbox vigente. Usa detalle simplificado mientras cambia la comisaria."
            ),
        )


def _resolve_effective_bbox(
    layer_id: str,
    *,
    bbox: tuple[float, float, float, float] | None,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
) -> tuple[float, float, float, float] | None:
    if bbox is None or layer_id not in {"jurisdicciones", "sectores"}:
        return bbox

    if not (comisaria_id or comisaria):
        return bbox

    if scope_bbox_matches_comisaria(
        bbox=bbox,
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
    ):
        return bbox

    return None


def list_available_geo_layers() -> list[dict[str, Any]]:
    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                _log_territory_source("catalog", source="postgis", cur=cur)
                storage_stats = fetch_layer_storage_stats(cur=cur)
                layers: list[dict[str, Any]] = []

                for layer in GEO_LAYER_DEFINITIONS:
                    table_name = TERRITORY_LAYER_TABLES[layer["id"]]
                    layer_stats = storage_stats.get(table_name, {})
                    size_bytes = int(layer_stats.get("size_bytes", 0) or 0)
                    layers.append(
                        {
                            **layer,
                            "size_bytes": size_bytes,
                            "heavy": size_bytes >= 100 * 1024 * 1024,
                        }
                    )

                return layers
            _log_territory_source(
                "catalog",
                source="file_fallback",
                fallback_reason="postgis_not_ready",
                cur=cur,
            )
    else:
        _log_territory_source(
            "catalog",
            source="file_fallback",
            fallback_reason="forced_legacy",
        )

    layers: list[dict[str, Any]] = []

    for layer in GEO_LAYER_DEFINITIONS:
        layer_path = _build_layer_path(layer["file_name"])
        if not layer_path.exists() or not layer_path.is_file():
            continue

        layers.append(
            {
                **layer,
                "size_bytes": layer_path.stat().st_size,
                "heavy": layer_path.stat().st_size >= 100 * 1024 * 1024,
            }
        )

    return layers


def _build_context_option(layer_id: str, feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties") or {}

    if layer_id == "jurisdicciones":
        value = _stringify_value(properties.get("objectid"))
        comisaria = _normalize_value(properties.get("comisaria"))
        label = f"JURISDICCION {comisaria}".strip() if comisaria else "JURISDICCION"
        if not value:
            return None
        return {
            "value": value,
            "label": label,
        }

    if layer_id == "sectores":
        label = (
            _stringify_value(properties.get("label"))
            or (
                f"SECTOR {_stringify_value(properties.get('sector'))}".strip()
                if _stringify_value(properties.get("sector"))
                else ""
            )
        )
        value = (
            _stringify_value(properties.get("cod_sector"))
            or _stringify_value(properties.get("sector"))
            or _stringify_value(properties.get("objectid"))
            or label
        )
        if not value or not label:
            return None
        return {
            "value": value,
            "label": label,
        }

    return None


def _build_context_options(layer_id: str, feature_collection: dict[str, Any]) -> list[dict[str, Any]]:
    options_by_value: dict[str, dict[str, Any]] = {}

    for feature in feature_collection.get("features") or []:
        option = _build_context_option(layer_id, feature)
        if option is None:
            continue
        options_by_value[option["value"]] = option

    return sorted(options_by_value.values(), key=lambda item: (_normalize_value(item["label"]), item["value"]))


@lru_cache(maxsize=1)
def _get_region_options_cached() -> tuple[str, ...]:
    layer = _get_layer_definition("regiones")
    layer_path = _get_layer_path(layer)
    regions = {
        _normalize_value((feature.get("properties") or {}).get(layer["region_property"]))
        for feature in _iter_geojson_features(layer_path)
    }
    return tuple(sorted(region for region in regions if region))


@lru_cache(maxsize=64)
def _get_division_options_cached(region: str) -> tuple[str, ...]:
    layer = _get_layer_definition("divisiones")
    layer_path = _get_region_cache_path(layer, region) or _get_layer_path(layer)
    normalized_region = _normalize_value(region)
    divisions = {
        _normalize_value((feature.get("properties") or {}).get(layer["division_property"]))
        for feature in _iter_geojson_features(layer_path)
        if _normalize_value((feature.get("properties") or {}).get(layer["region_property"])) == normalized_region
    }
    return tuple(sorted(division for division in divisions if division))


@lru_cache(maxsize=256)
def _get_comisaria_options_cached(region: str, division: str) -> tuple[tuple[int, str, str | None], ...]:
    layer = _get_layer_definition("comisarias")
    layer_path = _get_region_cache_path(layer, region) or _get_layer_path(layer)
    normalized_region = _normalize_value(region)
    normalized_division = _normalize_value(division)
    comisarias_by_id: dict[int, tuple[int, str, str | None]] = {}
    for feature in _iter_geojson_features(layer_path):
        properties = feature.get("properties") or {}
        if _normalize_value(properties.get(layer["region_property"])) != normalized_region:
            continue
        if normalized_division and _normalize_value(properties.get(layer["division_property"])) != normalized_division:
            continue

        name = _normalize_value(properties.get(layer["comisaria_property"]))
        if not name:
            continue

        option_id = int(properties.get("objectid") or len(comisarias_by_id) + 1)
        comisarias_by_id[option_id] = (
            option_id,
            name,
            _stringify_value(properties.get("cod_cpnp")) or None,
        )

    return tuple(sorted(comisarias_by_id.values(), key=lambda item: (item[1], item[0])))


def get_geo_layer_context(
    region: str | None = None,
    division: str | None = None,
    comisaria: str | None = None,
    comisaria_id: int | None = None,
) -> dict[str, Any]:
    normalized_region = _normalize_value(region)
    normalized_division = _normalize_value(division)
    normalized_comisaria = _normalize_value(comisaria)

    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                _log_territory_source(
                    "context",
                    source="postgis",
                    cur=cur,
                    region=normalized_region or None,
                    division=normalized_division or None,
                    comisaria_id=comisaria_id,
                    comisaria=normalized_comisaria or None,
                )
                regions = [row["name"] for row in fetch_regions(cur=cur)]
                divisions = (
                    [row["name"] for row in fetch_divisions(region=normalized_region or None, cur=cur)]
                    if normalized_region
                    else []
                )
                comisarias = (
                    [
                        {
                            "id": int(row["id"]),
                            "value": str(row["id"]),
                            "label": str(row["name"]),
                            "code": str(row["code"]) if row.get("code") else None,
                        }
                        for row in fetch_comisarias(
                            region=normalized_region or None,
                            division=normalized_division or None,
                            cur=cur,
                        )
                    ]
                    if normalized_region
                    else []
                )
                jurisdicciones = (
                    [
                        {
                            "id": int(row["id"]),
                            "value": str(row["value"]),
                            "label": str(row["label"]),
                            "code": str(row["code"]) if row.get("code") else None,
                            "parent_id": int(row["parent_id"]) if row.get("parent_id") is not None else None,
                        }
                        for row in fetch_jurisdicciones(
                            region=normalized_region or None,
                            division=normalized_division or None,
                            comisaria_id=comisaria_id,
                            comisaria=normalized_comisaria or None,
                            cur=cur,
                        )
                    ]
                    if normalized_region and (normalized_comisaria or comisaria_id)
                    else []
                )
                sectores = (
                    [
                        {
                            "id": int(row["id"]),
                            "value": str(row["value"]),
                            "label": str(row["label"]),
                            "code": str(row["code"]) if row.get("code") else None,
                            "parent_id": int(row["parent_id"]) if row.get("parent_id") is not None else None,
                        }
                        for row in fetch_sectores(
                            region=normalized_region or None,
                            division=normalized_division or None,
                            comisaria_id=comisaria_id,
                            comisaria=normalized_comisaria or None,
                            cur=cur,
                        )
                    ]
                    if normalized_region and (normalized_comisaria or comisaria_id)
                    else []
                )

                return {
                    "regions": regions,
                    "divisions": divisions,
                    "comisarias": comisarias,
                    "jurisdicciones": jurisdicciones,
                    "sectores": sectores,
                }
            _log_territory_source(
                "context",
                source="file_fallback",
                fallback_reason="postgis_not_ready",
                cur=cur,
                region=normalized_region or None,
                division=normalized_division or None,
                comisaria_id=comisaria_id,
                comisaria=normalized_comisaria or None,
            )
    else:
        _log_territory_source(
            "context",
            source="file_fallback",
            fallback_reason="forced_legacy",
            region=normalized_region or None,
            division=normalized_division or None,
            comisaria_id=comisaria_id,
            comisaria=normalized_comisaria or None,
        )

    jurisdicciones = []
    sectores = []

    if normalized_region and normalized_comisaria:
        try:
            jurisdicciones = _build_context_options(
                "jurisdicciones",
                get_geo_layer_data(
                    "jurisdicciones",
                    region=normalized_region,
                    division=normalized_division or None,
                    comisaria=normalized_comisaria,
                ),
            )
        except HTTPException:
            jurisdicciones = []

        try:
            sectores = _build_context_options(
                "sectores",
                get_geo_layer_data(
                    "sectores",
                    region=normalized_region,
                    division=normalized_division or None,
                    comisaria=normalized_comisaria,
                ),
            )
        except HTTPException:
            sectores = []

    return {
        "regions": list(_get_region_options_cached()),
        "divisions": list(_get_division_options_cached(normalized_region)) if normalized_region else [],
        "comisarias": (
            [
                {
                    "id": option_id,
                    "value": str(option_id),
                    "label": name,
                    "code": code,
                }
                for option_id, name, code in _get_comisaria_options_cached(normalized_region, normalized_division)
            ]
            if normalized_region
            else []
        ),
        "jurisdicciones": jurisdicciones,
        "sectores": sectores,
    }


@lru_cache(maxsize=48)
def _get_filtered_geo_layer_cached(
    layer_id: str,
    region: str,
    division: str,
    comisaria: str,
    jurisdiccion: str,
    sector: str,
) -> dict[str, Any]:
    layer = _get_layer_definition(layer_id)
    layer_path = _get_region_cache_path(layer, region) or _get_layer_path(layer)
    features = [
        feature
        for feature in _iter_geojson_features(layer_path)
        if _matches_scope(
            layer,
            feature,
            region=region or None,
            division=division or None,
            comisaria=comisaria or None,
            jurisdiccion=jurisdiccion or None,
            sector=sector or None,
        )
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_geo_layer_data(
    layer_id: str,
    *,
    region: str | None = None,
    division: str | None = None,
    comisaria: str | None = None,
    jurisdiccion: str | None = None,
    sector: str | None = None,
    region_id: int | None = None,
    division_id: int | None = None,
    comisaria_id: int | None = None,
    detail: str | None = None,
    bbox: str | None = None,
    enforce_scope: bool = True,
) -> dict[str, Any]:
    layer = _get_layer_definition(layer_id)
    normalized_region = _normalize_value(region)
    normalized_division = _normalize_value(division)
    normalized_comisaria = _normalize_value(comisaria)
    normalized_jurisdiccion = _stringify_value(jurisdiccion)
    normalized_sector = _stringify_value(sector)
    parsed_bbox = _parse_bbox(bbox)

    if enforce_scope:
        _validate_scope(
            layer,
            normalized_region or None,
            normalized_comisaria or None,
            comisaria_id=comisaria_id,
        )

    effective_bbox = _resolve_effective_bbox(
        layer["id"],
        bbox=parsed_bbox,
        region_id=region_id,
        region=normalized_region or None,
        division_id=division_id,
        division=normalized_division or None,
        comisaria_id=comisaria_id,
        comisaria=normalized_comisaria or None,
    )
    if enforce_scope:
        _validate_heavy_layer_detail_request(
            layer["id"],
            detail=detail,
            bbox=effective_bbox,
            jurisdiccion=normalized_jurisdiccion or None,
            sector=normalized_sector or None,
        )

    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                _log_territory_source(
                    "geojson",
                    layer_id=layer["id"],
                    source="postgis",
                    cur=cur,
                    region=normalized_region or None,
                    division=normalized_division or None,
                    comisaria_id=comisaria_id,
                    comisaria=normalized_comisaria or None,
                    jurisdiccion=normalized_jurisdiccion or None,
                    sector=normalized_sector or None,
                    detail=detail,
                    bbox=effective_bbox,
                )
                return fetch_layer_feature_collection(
                    layer["id"],
                    region_id=region_id,
                    region=normalized_region or None,
                    division_id=division_id,
                    division=normalized_division or None,
                    comisaria_id=comisaria_id,
                    comisaria=normalized_comisaria or None,
                    jurisdiccion=normalized_jurisdiccion or None,
                    sector=normalized_sector or None,
                    detail=detail,
                    bbox=effective_bbox,
                    cur=cur,
                )
            _log_territory_source(
                "geojson",
                layer_id=layer["id"],
                source="file_fallback",
                fallback_reason="postgis_not_ready",
                cur=cur,
                region=normalized_region or None,
                division=normalized_division or None,
                comisaria_id=comisaria_id,
                comisaria=normalized_comisaria or None,
                jurisdiccion=normalized_jurisdiccion or None,
                sector=normalized_sector or None,
                detail=detail,
                bbox=effective_bbox,
            )
    else:
        _log_territory_source(
            "geojson",
            layer_id=layer["id"],
            source="file_fallback",
            fallback_reason="forced_legacy",
            region=normalized_region or None,
            division=normalized_division or None,
            comisaria_id=comisaria_id,
            comisaria=normalized_comisaria or None,
            jurisdiccion=normalized_jurisdiccion or None,
            sector=normalized_sector or None,
            detail=detail,
            bbox=effective_bbox,
        )

    return _get_filtered_geo_layer_cached(
        layer["id"],
        normalized_region,
        normalized_division,
        normalized_comisaria,
        normalized_jurisdiccion,
        normalized_sector,
    )


def list_territory_regions() -> list[dict[str, Any]]:
    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                return fetch_regions(cur=cur)

    layer = _get_layer_definition("regiones")
    regions = []
    for feature in _iter_geojson_features(_get_layer_path(layer)):
        properties = feature.get("properties") or {}
        region_name = _normalize_value(properties.get("regionpol"))
        if not region_name:
            continue
        regions.append(
            {
                "id": int(properties.get("objectid") or len(regions) + 1),
                "code": _stringify_value(properties.get("cod_regpol")) or None,
                "name": region_name,
            }
        )
    regions_by_name = {row["name"]: row for row in regions}
    return sorted(regions_by_name.values(), key=lambda row: row["name"])


def list_territory_divisions(
    *,
    region_id: int | None = None,
    region: str | None = None,
) -> list[dict[str, Any]]:
    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                return fetch_divisions(region_id=region_id, region=region, cur=cur)

    normalized_region = _normalize_value(region)
    layer = _get_layer_definition("divisiones")
    divisions_by_name: dict[str, dict[str, Any]] = {}
    for feature in _iter_geojson_features(_get_region_cache_path(layer, normalized_region) or _get_layer_path(layer)):
        properties = feature.get("properties") or {}
        if normalized_region and _normalize_value(properties.get("regionpol")) != normalized_region:
            continue
        name = _normalize_value(properties.get("divpol_divopus"))
        if not name:
            continue
        divisions_by_name[name] = {
            "id": int(properties.get("objectid") or len(divisions_by_name) + 1),
            "code": _stringify_value(properties.get("cod_divpol_divopus")) or None,
            "name": name,
            "parent_id": None,
        }
    return sorted(divisions_by_name.values(), key=lambda row: row["name"])


def list_territory_comisarias(
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
) -> list[dict[str, Any]]:
    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                return fetch_comisarias(
                    region_id=region_id,
                    region=region,
                    division_id=division_id,
                    division=division,
                    cur=cur,
                )

    normalized_region = _normalize_value(region)
    normalized_division = _normalize_value(division)
    layer = _get_layer_definition("comisarias")
    comisarias_by_name: dict[str, dict[str, Any]] = {}
    for feature in _iter_geojson_features(_get_region_cache_path(layer, normalized_region) or _get_layer_path(layer)):
        properties = feature.get("properties") or {}
        if normalized_region and _normalize_value(properties.get("regionpol")) != normalized_region:
            continue
        if normalized_division and _normalize_value(properties.get("divpol_divopus")) != normalized_division:
            continue
        name = _normalize_value(properties.get("comisaria"))
        if not name:
            continue
        comisarias_by_name[name] = {
            "id": int(properties.get("objectid") or len(comisarias_by_name) + 1),
            "code": _stringify_value(properties.get("cod_cpnp")) or None,
            "name": name,
            "parent_id": None,
        }
    return sorted(comisarias_by_name.values(), key=lambda row: row["name"])


def list_territory_jurisdicciones(
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
) -> list[dict[str, Any]]:
    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                return fetch_jurisdicciones(
                    region_id=region_id,
                    region=region,
                    division_id=division_id,
                    division=division,
                    comisaria_id=comisaria_id,
                    comisaria=comisaria,
                    cur=cur,
                )

    if not region or not comisaria:
        return []
    return [
        {
            "id": index + 1,
            "code": None,
            "parent_id": None,
            "value": item["value"],
            "label": item["label"],
        }
        for index, item in enumerate(get_geo_layer_context(region=region, division=division, comisaria=comisaria)["jurisdicciones"])
    ]


def list_territory_sectores(
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
) -> list[dict[str, Any]]:
    if not settings.geo_layers_force_legacy:
        with get_cursor() as cur:
            if _should_use_postgis_source(cur):
                return fetch_sectores(
                    region_id=region_id,
                    region=region,
                    division_id=division_id,
                    division=division,
                    comisaria_id=comisaria_id,
                    comisaria=comisaria,
                    cur=cur,
                )

    if not region or not comisaria:
        return []
    return [
        {
            "id": index + 1,
            "code": None,
            "parent_id": None,
            "value": item["value"],
            "label": item["label"],
        }
        for index, item in enumerate(get_geo_layer_context(region=region, division=division, comisaria=comisaria)["sectores"])
    ]


def _geometry_covers_point(cur, *, geometry_geojson: str, latitud: float, longitud: float) -> bool:
    cur.execute(
        """
        SELECT ST_Covers(
            ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        ) AS matches;
        """,
        (geometry_geojson, longitud, latitud),
    )
    row = cur.fetchone() or {}
    return bool(row.get("matches"))


def find_region_for_point(*, latitud: float, longitud: float, cur=None) -> str | None:
    if _should_use_postgis_source(cur):
        return find_region_for_point_in_db(latitud=latitud, longitud=longitud, cur=cur)

    if cur is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No hay una fuente territorial PostGIS disponible y se requiere un cursor para el fallback GeoJSON.",
        )

    region_cache_root = _get_region_cache_root() / "regiones"
    for region_file in sorted(region_cache_root.glob("*.geojson")):
        for feature in _iter_geojson_features(region_file):
            geometry = feature.get("geometry")
            if not geometry:
                continue

            if _geometry_covers_point(
                cur,
                geometry_geojson=json.dumps(geometry, ensure_ascii=True),
                latitud=latitud,
                longitud=longitud,
            ):
                properties = feature.get("properties") or {}
                return _normalize_value(properties.get("regionpol")) or _normalize_value(region_file.stem)

    return None
