from pathlib import Path
from types import SimpleNamespace

import app.geo_layers as geo_layers


def test_should_use_postgis_source_short_circuits_when_legacy_is_forced(monkeypatch):
    monkeypatch.setattr(
        geo_layers,
        "settings",
        SimpleNamespace(
            geojson_layers_dir=Path("."),
            geo_layers_force_legacy=True,
        ),
    )

    def _unexpected_readiness_check(cur=None):
        raise AssertionError("No debe consultar disponibilidad PostGIS cuando legacy esta forzado.")

    monkeypatch.setattr(geo_layers, "territory_layers_source_ready", _unexpected_readiness_check)

    assert geo_layers._should_use_postgis_source() is False


def test_list_available_geo_layers_uses_geojson_files_when_legacy_is_forced(monkeypatch, tmp_path):
    layer_path = tmp_path / "6_region_policial.geojson"
    layer_path.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    monkeypatch.setattr(
        geo_layers,
        "settings",
        SimpleNamespace(
            geojson_layers_dir=tmp_path,
            geo_layers_force_legacy=True,
        ),
    )
    monkeypatch.setattr(
        geo_layers,
        "territory_layers_source_ready",
        lambda cur=None: True,
    )

    layers = geo_layers.list_available_geo_layers()

    assert [layer["id"] for layer in layers] == ["regiones"]
    assert layers[0]["size_bytes"] == layer_path.stat().st_size
    assert layers[0]["heavy"] is False
