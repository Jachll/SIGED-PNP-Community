from app.api.routers import territorio as territorio_router


def test_territorio_catalog_returns_available_layers(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(
        territorio_router,
        "list_available_geo_layers",
        lambda: [
            {
                "id": "regiones",
                "label": "Regiones Policiales",
                "file_name": "6_region_policial.geojson",
                "geometry_type": "poligono",
                "stroke_color": "#be123c",
                "fill_color": "#fda4af",
                "fill_opacity": 0.04,
                "recommended_zoom": 9,
                "size_bytes": 1024,
                "heavy": False,
                "requires_region": True,
                "requires_division": False,
                "requires_comisaria": False,
            }
        ],
    )

    response = client.get("/territorio/capas")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "regiones"


def test_territorio_context_preserves_hierarchy_shape(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(
        territorio_router,
        "get_geo_layer_context",
        lambda region=None, division=None, comisaria=None, comisaria_id=None: {
            "regions": ["REGION DEMO CENTRO"],
            "divisions": ["DIVISION DEMO ESTE"] if region else [],
            "comisarias": [{"id": 22, "value": "22", "label": "COMISARIA DEMO 10"}] if region else [],
            "jurisdicciones": [{"id": 4011, "value": "4011", "label": "JURISDICCION DEMO 10"}] if (comisaria or comisaria_id) else [],
            "sectores": [{"id": 209501, "value": "209501", "label": "SECTOR 01"}] if (comisaria or comisaria_id) else [],
        },
    )

    response = client.get("/territorio/contexto?region=REGION%20DEMO%20CENTRO&division=DIVISION%20DEMO%20ESTE")

    assert response.status_code == 200
    payload = response.json()
    assert payload["regions"] == ["REGION DEMO CENTRO"]
    assert payload["divisions"] == ["DIVISION DEMO ESTE"]
    assert payload["comisarias"] == [{"id": 22, "value": "22", "label": "COMISARIA DEMO 10", "code": None, "parent_id": None}]


def test_territorio_list_endpoints_return_hierarchy_nodes(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(
        territorio_router,
        "list_territory_regions",
        lambda: [
            {"id": 5, "code": "13", "name": "REGION DEMO CENTRO"},
        ],
    )
    monkeypatch.setattr(
        territorio_router,
        "list_territory_divisions",
        lambda region_id=None, region=None: [
            {"id": 10, "code": "13R1K", "name": "DIVISION DEMO ESTE", "parent_id": region_id}
        ],
    )
    monkeypatch.setattr(
        territorio_router,
        "list_territory_comisarias",
        lambda region_id=None, region=None, division_id=None, division=None: [
            {"id": 22, "code": "COM-DEMO-22", "name": "COMISARIA DEMO 10", "parent_id": division_id, "region_id": region_id}
        ],
    )
    monkeypatch.setattr(
        territorio_router,
        "list_territory_jurisdicciones",
        lambda region_id=None, region=None, division_id=None, division=None, comisaria_id=None, comisaria=None: [
            {
                "id": 4011,
                "value": "4011",
                "label": "JURISDICCION DEMO 10",
                "code": "JUR-4011",
                "parent_id": comisaria_id,
            }
        ],
    )
    monkeypatch.setattr(
        territorio_router,
        "list_territory_sectores",
        lambda region_id=None, region=None, division_id=None, division=None, comisaria_id=None, comisaria=None: [
            {
                "id": 209501,
                "value": "209501",
                "label": "SECTOR 01",
                "code": "SEC-01",
                "parent_id": comisaria_id,
            }
        ],
    )

    regions_response = client.get("/territorio/regiones")
    divisions_response = client.get("/territorio/divisiones?region_id=5&region=REGION%20DEMO%20CENTRO")
    comisarias_response = client.get(
        "/territorio/comisarias?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE"
    )
    jurisdicciones_response = client.get(
        "/territorio/jurisdicciones?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE&comisaria_id=22&comisaria=COMISARIA%20DEMO%2010"
    )
    sectores_response = client.get(
        "/territorio/sectores?region_id=5&region=REGION%20DEMO%20CENTRO&division_id=10&division=DIVISION%20DEMO%20ESTE&comisaria_id=22&comisaria=COMISARIA%20DEMO%2010"
    )

    assert regions_response.status_code == 200
    assert regions_response.json()[0]["name"] == "REGION DEMO CENTRO"

    assert divisions_response.status_code == 200
    assert divisions_response.json()[0]["parent_id"] == 5

    assert comisarias_response.status_code == 200
    assert comisarias_response.json()[0]["name"] == "COMISARIA DEMO 10"

    assert jurisdicciones_response.status_code == 200
    assert jurisdicciones_response.json()[0]["value"] == "4011"

    assert sectores_response.status_code == 200
    assert sectores_response.json()[0]["label"] == "SECTOR 01"


def test_territorio_list_endpoints_and_geojson_forward_filters(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(
        territorio_router,
        "list_territory_divisions",
        lambda region_id=None, region=None: [
            {"id": 10, "code": "13R1K", "name": "DIVISION DEMO ESTE", "parent_id": region_id}
        ],
    )
    monkeypatch.setattr(
        territorio_router,
        "get_geo_layer_data",
        lambda layer_id, **filters: {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "layer_id": layer_id,
                        "region": filters.get("region"),
                        "detail": filters.get("detail"),
                    },
                }
            ],
        },
    )

    list_response = client.get("/territorio/divisiones?region_id=5&region=REGION%20DEMO%20CENTRO")
    geojson_response = client.get("/territorio/divisiones/geojson?region=REGION%20DEMO%20CENTRO&detail=simplified")

    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "DIVISION DEMO ESTE"

    assert geojson_response.status_code == 200
    geojson_payload = geojson_response.json()
    assert geojson_payload["features"][0]["properties"]["layer_id"] == "divisiones"
    assert geojson_payload["features"][0]["properties"]["detail"] == "simplified"
