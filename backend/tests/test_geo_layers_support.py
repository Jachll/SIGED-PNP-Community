from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app import geo_layers


@contextmanager
def _fake_cursor():
    yield None


def test_get_geo_layer_data_rejects_unbounded_full_detail_for_heavy_layers(monkeypatch):
    monkeypatch.setattr(geo_layers, "_should_use_postgis_source", lambda cur=None: True)

    with pytest.raises(HTTPException) as exc_info:
        geo_layers.get_geo_layer_data(
            "sectores",
            region="REGION DEMO NORTE",
            comisaria="COMISARIA DEMO ALTO",
            detail="full",
        )

    assert exc_info.value.status_code == 422
    assert "requiere un sector especifico o un bbox vigente" in str(exc_info.value.detail)


def test_get_geo_layer_data_ignores_stale_bbox_when_scope_excludes_selected_comisaria(monkeypatch):
    captured_filters: dict[str, object] = {}

    monkeypatch.setattr(geo_layers, "_should_use_postgis_source", lambda cur=None: True)
    monkeypatch.setattr(geo_layers, "get_cursor", _fake_cursor)
    monkeypatch.setattr(geo_layers, "scope_bbox_matches_comisaria", lambda **kwargs: False)

    def _fake_fetch_layer_feature_collection(layer_id, **filters):
        captured_filters["layer_id"] = layer_id
        captured_filters.update(filters)
        return {"type": "FeatureCollection", "features": []}

    monkeypatch.setattr(geo_layers, "fetch_layer_feature_collection", _fake_fetch_layer_feature_collection)

    payload = geo_layers.get_geo_layer_data(
        "jurisdicciones",
        region="REGION DEMO NORTE",
        comisaria="COMISARIA DEMO ALTO",
        detail="simplified",
        bbox="-78.6150,-9.0797,-78.5846,-9.0666",
    )

    assert payload["features"] == []
    assert captured_filters["layer_id"] == "jurisdicciones"
    assert captured_filters["bbox"] is None
