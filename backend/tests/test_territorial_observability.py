import app.observability as observability
from app.api.routers import geo_layers as geo_layers_router
from app.api.routers import territorio as territorio_router


def _clear_metrics() -> None:
    with observability._metrics_lock:
        observability._metrics.clear()


def test_territorio_context_records_operation_metric(client, set_current_user, monkeypatch):
    _clear_metrics()
    set_current_user("consulta")
    monkeypatch.setattr(
        territorio_router,
        "get_geo_layer_context",
        lambda region=None, division=None, comisaria=None, comisaria_id=None: {
            "regions": ["REGION DEMO CENTRO"],
            "divisions": [],
            "comisarias": [],
            "jurisdicciones": [],
            "sectores": [],
        },
    )

    response = client.get("/territorio/contexto?region=REGION%20DEMO%20CENTRO")

    snapshot = observability.get_metrics_snapshot()

    assert response.status_code == 200
    assert snapshot["operation:territorio.contexto"]["count"] == 1
    assert snapshot["request:GET:/territorio/contexto"]["count"] == 1
    _clear_metrics()


def test_legacy_geojson_records_operation_metric(client, set_current_user, monkeypatch):
    _clear_metrics()
    set_current_user("consulta")
    monkeypatch.setattr(
        geo_layers_router,
        "get_geo_layer_data",
        lambda layer_id, **filters: {"type": "FeatureCollection", "features": []},
    )

    response = client.get("/capas/geojson/regiones?region=REGION%20DEMO%20CENTRO")

    snapshot = observability.get_metrics_snapshot()

    assert response.status_code == 200
    assert snapshot["operation:territorio.legacy.capa"]["count"] == 1
    assert snapshot["request:GET:/capas/geojson/regiones"]["count"] == 1
    _clear_metrics()
