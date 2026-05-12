from fastapi import HTTPException

from app.api.routers import analisis as analisis_router


def test_hotspots_success(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(
        analisis_router,
        "list_hotspots",
        lambda fecha_inicio, fecha_fin, id_delito, distrito, id_comisaria, region, division, comisaria, jurisdiccion, sector, estado, limite: [
            {
                "id_hotspot": 1,
                "periodo_inicio": "2026-01-01",
                "periodo_fin": "2026-01-07",
                "fecha_deteccion": "2026-01-07T08:00:00",
                "id_delito": 2,
                "nombre_delito": "Hurto",
                "distrito": "REGION DEMO",
                "id_zona": None,
                "nombre_zona": None,
                "id_comisaria": None,
                "nombre_comisaria": None,
                "nivel_riesgo": "ALTO",
                "intensidad": 10.5,
                "conteo_eventos": 11,
                "latitud": -12.1,
                "longitud": -77.1,
                "radio_metros": 250,
                "fuente_analisis": "EVENTOS_AGRUPADOS",
                "estado_hotspot": "ACTIVO",
                "observaciones": "Hotspot demo",
                "origen_datos": "calculado_desde_eventos",
            }
        ],
    )

    response = client.get("/analisis/hotspots")

    assert response.status_code == 200
    assert response.json()[0]["nivel_riesgo"] == "ALTO"


def test_zonas_criticas_bad_request(client, set_current_user, monkeypatch):
    set_current_user("analista")

    def _raise_bad_request(*args, **kwargs):
        raise HTTPException(
            status_code=400,
            detail="El agrupamiento solicitado no esta disponible en este entorno.",
        )

    monkeypatch.setattr(analisis_router, "list_zonas_criticas", _raise_bad_request)

    response = client.get("/analisis/zonas-criticas?agrupado_por=zona_operativa")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"
