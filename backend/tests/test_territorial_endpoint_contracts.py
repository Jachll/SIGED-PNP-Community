from contextlib import contextmanager
from types import SimpleNamespace

from fastapi import HTTPException
import pytest

import app.geo_layers as geo_layers
from app.api.routers import geo_layers as geo_layers_router
from app.api.routers import territorio as territorio_router
from app.security import get_current_user


@contextmanager
def _fake_cursor():
    yield None


def test_territorio_context_contract_supports_incomplete_and_complete_hierarchy(
    client,
    set_current_user,
    monkeypatch,
):
    set_current_user("consulta")
    monkeypatch.setattr(geo_layers, "get_cursor", _fake_cursor)
    monkeypatch.setattr(geo_layers, "_should_use_postgis_source", lambda cur=None: False)
    monkeypatch.setattr(geo_layers, "_get_region_options_cached", lambda: ("REGION DEMO CENTRO", "REGION DEMO COSTA"))
    monkeypatch.setattr(
        geo_layers,
        "_get_division_options_cached",
        lambda region: ("DIVISION DEMO ESTE",) if region == "REGION DEMO CENTRO" else (),
    )
    monkeypatch.setattr(
        geo_layers,
        "_get_comisaria_options_cached",
        lambda region, division: ((22, "COMISARIA DEMO 10", "COM-DEMO-22"),)
        if region == "REGION DEMO CENTRO" and division == "DIVISION DEMO ESTE"
        else (),
    )

    def _fake_geo_layer_data(layer_id, **filters):
        if layer_id == "jurisdicciones":
            assert filters["region"] == "REGION DEMO CENTRO"
            assert filters["division"] == "DIVISION DEMO ESTE"
            assert filters["comisaria"] == "COMISARIA DEMO 10"
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "objectid": "4011",
                            "comisaria": "COMISARIA DEMO 10",
                        },
                    }
                ],
            }

        if layer_id == "sectores":
            assert filters["region"] == "REGION DEMO CENTRO"
            assert filters["division"] == "DIVISION DEMO ESTE"
            assert filters["comisaria"] == "COMISARIA DEMO 10"
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "cod_sector": "209501",
                            "label": "SECTOR 01",
                        },
                    }
                ],
            }

        raise AssertionError(f"Capa no esperada: {layer_id}")

    monkeypatch.setattr(geo_layers, "get_geo_layer_data", _fake_geo_layer_data)

    empty_scope_response = client.get("/territorio/contexto")
    assert empty_scope_response.status_code == 200
    assert empty_scope_response.json() == {
        "regions": ["REGION DEMO CENTRO", "REGION DEMO COSTA"],
        "divisions": [],
        "comisarias": [],
        "jurisdicciones": [],
        "sectores": [],
    }

    partial_scope_response = client.get("/territorio/contexto?region=REGION%20DEMO%20CENTRO&division=DIVISION%20DEMO%20ESTE")
    assert partial_scope_response.status_code == 200
    assert partial_scope_response.json() == {
        "regions": ["REGION DEMO CENTRO", "REGION DEMO COSTA"],
        "divisions": ["DIVISION DEMO ESTE"],
        "comisarias": [{"id": 22, "value": "22", "label": "COMISARIA DEMO 10", "code": "COM-DEMO-22", "parent_id": None}],
        "jurisdicciones": [],
        "sectores": [],
    }

    full_scope_response = client.get(
        "/territorio/contexto?region=REGION%20DEMO%20CENTRO&division=DIVISION%20DEMO%20ESTE&comisaria=COMISARIA%20DEMO%2010"
    )
    assert full_scope_response.status_code == 200
    assert full_scope_response.json() == {
        "regions": ["REGION DEMO CENTRO", "REGION DEMO COSTA"],
        "divisions": ["DIVISION DEMO ESTE"],
        "comisarias": [{"id": 22, "value": "22", "label": "COMISARIA DEMO 10", "code": "COM-DEMO-22", "parent_id": None}],
        "jurisdicciones": [{"id": None, "value": "4011", "label": "JURISDICCION COMISARIA DEMO 10", "code": None, "parent_id": None}],
        "sectores": [{"id": None, "value": "209501", "label": "SECTOR 01", "code": None, "parent_id": None}],
    }


def test_territorio_context_uses_controlled_fallback_when_nested_layers_fail(
    client,
    set_current_user,
    monkeypatch,
):
    set_current_user("consulta")
    monkeypatch.setattr(geo_layers, "get_cursor", _fake_cursor)
    monkeypatch.setattr(geo_layers, "_should_use_postgis_source", lambda cur=None: False)
    monkeypatch.setattr(geo_layers, "_get_region_options_cached", lambda: ("REGION DEMO CENTRO",))
    monkeypatch.setattr(geo_layers, "_get_division_options_cached", lambda region: ("DIVISION DEMO ESTE",))
    monkeypatch.setattr(
        geo_layers,
        "_get_comisaria_options_cached",
        lambda region, division: ((22, "COMISARIA DEMO 10", "COM-DEMO-22"),),
    )
    monkeypatch.setattr(
        geo_layers,
        "get_geo_layer_data",
        lambda layer_id, **filters: (_ for _ in ()).throw(
            HTTPException(status_code=503, detail=f"fallback controlado {layer_id}")
        ),
    )

    response = client.get(
        "/territorio/contexto?region=REGION%20DEMO%20CENTRO&division=DIVISION%20DEMO%20ESTE&comisaria=COMISARIA%20DEMO%2010"
    )

    assert response.status_code == 200
    assert response.json() == {
        "regions": ["REGION DEMO CENTRO"],
        "divisions": ["DIVISION DEMO ESTE"],
        "comisarias": [{"id": 22, "value": "22", "label": "COMISARIA DEMO 10", "code": "COM-DEMO-22", "parent_id": None}],
        "jurisdicciones": [],
        "sectores": [],
    }


@pytest.mark.parametrize(
    ("path", "expected_layer_id", "expected_filters"),
    [
        (
            "/territorio/regiones/geojson?region_id=5&region=REGION%20DEMO%20CENTRO&detail=full&bbox=-77.2,-12.2,-76.8,-11.8",
            "regiones",
            {
                "region_id": 5,
                "region": "REGION DEMO CENTRO",
                "detail": "full",
                "bbox": "-77.2,-12.2,-76.8,-11.8",
            },
        ),
        (
            "/territorio/divisiones/geojson?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE&detail=simplified",
            "divisiones",
            {
                "region_id": 5,
                "region": "REGION DEMO CENTRO",
                "division_id": 10,
                "division": "DIVISION DEMO ESTE",
                "detail": "simplified",
            },
        ),
        (
            "/territorio/comisarias/geojson?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE&comisaria_id=22&comisaria=COMISARIA%20DEMO%2010",
            "comisarias",
            {
                "region_id": 5,
                "region": "REGION DEMO CENTRO",
                "division_id": 10,
                "division": "DIVISION DEMO ESTE",
                "comisaria_id": 22,
                "comisaria": "COMISARIA DEMO 10",
            },
        ),
        (
            "/territorio/jurisdicciones/geojson?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE&comisaria_id=22&comisaria=COMISARIA%20DEMO%2010&jurisdiccion=4011&detail=full",
            "jurisdicciones",
            {
                "region_id": 5,
                "region": "REGION DEMO CENTRO",
                "division_id": 10,
                "division": "DIVISION DEMO ESTE",
                "comisaria_id": 22,
                "comisaria": "COMISARIA DEMO 10",
                "jurisdiccion": "4011",
                "detail": "full",
            },
        ),
        (
            "/territorio/sectores/geojson?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE&comisaria_id=22&comisaria=COMISARIA%20DEMO%2010&sector=209501&detail=auto",
            "sectores",
            {
                "region_id": 5,
                "region": "REGION DEMO CENTRO",
                "division_id": 10,
                "division": "DIVISION DEMO ESTE",
                "comisaria_id": 22,
                "comisaria": "COMISARIA DEMO 10",
                "sector": "209501",
                "detail": "auto",
            },
        ),
    ],
)
def test_territorio_geojson_contract_forwards_hierarchical_filters(
    client,
    set_current_user,
    monkeypatch,
    path,
    expected_layer_id,
    expected_filters,
):
    set_current_user("consulta")
    captured_call = {}

    def _fake_get_geo_layer_data(layer_id, **filters):
        captured_call["layer_id"] = layer_id
        captured_call["filters"] = filters
        return {"type": "FeatureCollection", "features": []}

    monkeypatch.setattr(territorio_router, "get_geo_layer_data", _fake_get_geo_layer_data)

    response = client.get(path)

    assert response.status_code == 200
    assert response.json() == {"type": "FeatureCollection", "features": []}
    assert captured_call["layer_id"] == expected_layer_id
    for key, value in expected_filters.items():
        assert captured_call["filters"][key] == value


def test_legacy_geojson_contract_forwards_full_filters_and_marks_deprecation(
    client,
    set_current_user,
    monkeypatch,
):
    set_current_user("consulta")
    captured_call = {}

    def _fake_get_geo_layer_data(layer_id, **filters):
        captured_call["layer_id"] = layer_id
        captured_call["filters"] = filters
        return {"type": "FeatureCollection", "features": []}

    monkeypatch.setattr(geo_layers_router, "get_geo_layer_data", _fake_get_geo_layer_data)

    response = client.get(
        "/capas/geojson/sectores?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE"
        "&comisaria_id=22&comisaria=COMISARIA%20DEMO%2010&sector=209501&detail=simplified"
        "&bbox=-77.2,-12.2,-76.8,-11.8"
    )

    assert response.status_code == 200
    assert response.json() == {"type": "FeatureCollection", "features": []}
    assert captured_call["layer_id"] == "sectores"
    assert captured_call["filters"] == {
        "region_id": 5,
        "region": "REGION DEMO CENTRO",
        "division_id": 10,
        "division": "DIVISION DEMO ESTE",
        "comisaria_id": 22,
        "comisaria": "COMISARIA DEMO 10",
        "jurisdiccion": None,
        "sector": "209501",
        "detail": "simplified",
        "bbox": "-77.2,-12.2,-76.8,-11.8",
    }
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == geo_layers_router.LEGACY_GEOJSON_SUNSET
    assert response.headers["X-SIGED-Deprecated-Route"] == geo_layers_router.LEGACY_GEOJSON_REPLACEMENT


@pytest.mark.parametrize(
    "path",
    [
        "/territorio/comisarias/geojson?region=REGION%20DEMO%20CENTRO",
        "/capas/geojson/divisiones?region=REGION%20DEMO%20CENTRO",
    ],
)
def test_geojson_routes_allow_empty_feature_collections(client, set_current_user, monkeypatch, path):
    set_current_user("consulta")

    def _empty_feature_collection(layer_id, **filters):
        return {"type": "FeatureCollection", "features": []}

    monkeypatch.setattr(territorio_router, "get_geo_layer_data", _empty_feature_collection)
    monkeypatch.setattr(geo_layers_router, "get_geo_layer_data", _empty_feature_collection)

    response = client.get(path)

    assert response.status_code == 200
    assert response.json() == {"type": "FeatureCollection", "features": []}


@pytest.mark.parametrize(
    ("path", "expected_detail"),
    [
        ("/territorio/divisiones/geojson", "Selecciona una region policial antes de cargar esta capa."),
        (
            "/territorio/jurisdicciones/geojson?region=REGION%20DEMO%20CENTRO",
            "Selecciona una comisaria antes de cargar jurisdicciones o sectores.",
        ),
        (
            "/territorio/sectores/geojson?region=REGION%20DEMO%20CENTRO",
            "Selecciona una comisaria antes de cargar jurisdicciones o sectores.",
        ),
    ],
)
def test_territorio_geojson_rejects_incomplete_required_scope(
    client,
    set_current_user,
    path,
    expected_detail,
):
    set_current_user("consulta")

    response = client.get(path)

    assert response.status_code == 400
    assert response.json()["detail"] == expected_detail


def test_territorial_routes_return_403_for_disallowed_role(client, app):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        username="externo_user",
        rol_codigo="externo",
    )

    context_response = client.get("/territorio/contexto")
    geojson_response = client.get("/territorio/regiones/geojson?region=REGION%20DEMO%20CENTRO")

    assert context_response.status_code == 403
    assert context_response.json()["error"]["code"] == "forbidden"
    assert geojson_response.status_code == 403
    assert geojson_response.json()["error"]["code"] == "forbidden"
