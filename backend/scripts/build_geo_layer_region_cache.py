import json
from pathlib import Path

from app.geo_layers import (
    GEO_LAYER_DEFINITIONS,
    _get_layer_path,
    _get_region_cache_root,
    _iter_geojson_features,
    _normalize_value,
    _slugify_scope_value,
)


def _clean_layer_cache_directory(layer_cache_dir: Path) -> None:
    layer_cache_dir.mkdir(parents=True, exist_ok=True)
    for cached_file in layer_cache_dir.glob("*.geojson"):
        cached_file.unlink()


def build_region_cache() -> None:
    cache_root = _get_region_cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)

    for layer in GEO_LAYER_DEFINITIONS:
        layer_path = _get_layer_path(layer)
        layer_cache_dir = cache_root / layer["id"]
        _clean_layer_cache_directory(layer_cache_dir)

        print(f"[cache] procesando {layer['id']} desde {layer_path.name}")
        writers: dict[str, Path] = {}
        file_handles: dict[str, object] = {}
        feature_counts: dict[str, int] = {}

        for feature in _iter_geojson_features(layer_path):
            properties = feature.get("properties") or {}
            region = _normalize_value(properties.get(layer["region_property"]))
            if not region:
                continue

            if region not in file_handles:
                cache_file = layer_cache_dir / f"{_slugify_scope_value(region)}.geojson"
                writers[region] = cache_file
                handle = cache_file.open("w", encoding="utf-8")
                handle.write('{"type":"FeatureCollection","features":[\n')
                file_handles[region] = handle
                feature_counts[region] = 0

            handle = file_handles[region]

            if feature_counts[region] > 0:
                handle.write(",\n")

            handle.write(json.dumps(feature, ensure_ascii=False))
            feature_counts[region] += 1

        for region, handle in file_handles.items():
            handle.write("\n]}\n")
            handle.close()
            print(
                f"[cache]   {layer['id']} -> {region}: {feature_counts[region]} features "
                f"({writers[region].name})"
            )


if __name__ == "__main__":
    build_region_cache()
