from app.api.routers import geo_layers as geo_layers_router


def test_geo_layers_catalog_returns_available_layers(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(
        geo_layers_router,
        "list_available_geo_layers",
        lambda: [
            {
                "id": "comisarias",
                "label": "Comisarias",
                "file_name": "2_comisarias_basicas.geojson",
                "geometry_type": "poligono",
                "stroke_color": "#0f5f8c",
                "fill_color": "#8cc7e8",
                "fill_opacity": 0.08,
                "recommended_zoom": 11,
                "size_bytes": 1345302,
                "heavy": False,
                "requires_region": True,
                "requires_division": False,
                "requires_comisaria": False,
            }
        ],
    )

    response = client.get("/capas/geojson")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "comisarias"
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == geo_layers_router.LEGACY_GEOJSON_SUNSET
    assert response.headers["X-SIGED-Deprecated-Route"] == geo_layers_router.LEGACY_GEOJSON_REPLACEMENT


def test_geo_layers_context_returns_region_hierarchy(client, set_current_user, monkeypatch):
    set_current_user("analista")

    monkeypatch.setattr(
        geo_layers_router,
        "get_geo_layer_context",
        lambda region=None, division=None, comisaria=None, comisaria_id=None: {
            "regions": ["REGION DEMO CENTRO"],
            "divisions": ["DIVISION DEMO ESTE"] if region else [],
            "comisarias": [{"id": 22, "value": "22", "label": "COMISARIA DEMO 10"}] if division else [],
            "jurisdicciones": [{"id": 4011, "value": "4011", "label": "JURISDICCION DEMO 10"}] if (comisaria or comisaria_id) else [],
            "sectores": [{"id": 209501, "value": "209501", "label": "SECTOR 01"}] if (comisaria or comisaria_id) else [],
        },
    )

    response = client.get("/capas/geojson/contexto?region=REGION%20DEMO%20CENTRO&division=DIVISION%20DEMO%20ESTE")

    assert response.status_code == 200
    assert response.json()["divisions"] == ["DIVISION DEMO ESTE"]
    assert response.json()["comisarias"] == [{"id": 22, "value": "22", "label": "COMISARIA DEMO 10", "code": None, "parent_id": None}]
    assert response.headers["Deprecation"] == "true"


def test_geo_layer_returns_filtered_geojson(client, set_current_user, monkeypatch):
    set_current_user("analista")

    monkeypatch.setattr(
        geo_layers_router,
        "get_geo_layer_data",
        lambda layer_id, region=None, division=None, comisaria=None, jurisdiccion=None, sector=None, **kwargs: {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "layer_id": layer_id,
                        "region": region,
                        "division": division,
                        "comisaria": comisaria,
                        "jurisdiccion": jurisdiccion,
                        "sector": sector,
                    },
                }
            ],
        },
    )

    response = client.get(
        "/capas/geojson/jurisdicciones?region=REGION%20DEMO%20CENTRO&division=DIVISION%20DEMO%20ESTE&comisaria=COMISARIA%20DEMO%2010"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["properties"]["comisaria"] == "COMISARIA DEMO 10"
    assert response.headers["Deprecation"] == "true"
