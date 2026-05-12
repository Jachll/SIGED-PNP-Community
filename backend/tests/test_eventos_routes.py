from datetime import date, time

from app.api.routers import eventos as eventos_router


def test_get_eventos_requires_auth(client):
    response = client.get("/eventos")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_get_eventos_success(client, set_current_user, monkeypatch):
    set_current_user("consulta")
    monkeypatch.setattr(
        eventos_router,
        "list_eventos",
        lambda fecha_inicio, fecha_fin, id_delito, distrito, id_comisaria, region, division, comisaria, jurisdiccion, sector, limite, offset: [
            {
                "id_evento": 1,
                "fecha": date(2026, 1, 1),
                "hora": time(10, 0),
                "id_delito": 2,
                "nombre_delito": "Hurto",
                "distrito": "REGION DEMO",
                "direccion": "Av. Demo 123",
                "latitud": -12.0,
                "longitud": -77.0,
                "id_comisaria": 4,
                "nombre_comisaria": "Comisaria Centro",
                "fuente_registro": "911",
                "descripcion": "Evento demo",
            }
        ],
    )

    response = client.get("/eventos?limite=5&offset=10")

    assert response.status_code == 200
    assert response.json()[0]["nombre_delito"] == "Hurto"


def test_get_evento_detalle_success(client, set_current_user, monkeypatch):
    set_current_user("consulta")
    monkeypatch.setattr(
        eventos_router,
        "get_evento_detalle",
        lambda id_evento, radio_metros=150, limite_relacionados=5: {
            "id_evento": id_evento,
            "fecha": date(2026, 1, 1),
            "hora": time(10, 0),
            "id_delito": 2,
            "nombre_delito": "Hurto",
            "distrito": "REGION DEMO",
            "direccion": "Av. Demo 123",
            "latitud": -12.0,
            "longitud": -77.0,
            "id_comisaria": 4,
            "nombre_comisaria": "Comisaria Centro",
            "fuente_registro": "911",
            "descripcion": "Evento demo",
            "referencia_territorial": {
                "region": "REGION DEMO CENTRO",
                "division": "DIVISION DEMO CENTRO",
                "comisaria": "Comisaria Centro",
                "jurisdiccion": "JURISDICCION COMISARIA CENTRO",
                "sector": "SECTOR 01"
            },
            "contexto_lugar": {
                "radio_metros": radio_metros,
                "total_eventos_historicos": 3,
                "total_eventos_30_dias": 2,
                "total_eventos_90_dias": 3,
                "eventos_recientes": []
            }
        },
    )

    response = client.get("/eventos/1?radio_metros=200")

    assert response.status_code == 200
    assert response.json()["referencia_territorial"]["region"] == "REGION DEMO CENTRO"


def test_get_eventos_invalid_limit_returns_validation_error(client, set_current_user):
    set_current_user("consulta")

    response = client.get("/eventos?limite=999999")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_get_eventos_invalid_offset_returns_validation_error(client, set_current_user):
    set_current_user("consulta")

    response = client.get("/eventos?offset=-1")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
