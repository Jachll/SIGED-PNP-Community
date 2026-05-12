from app.api.routers import geo_layers as geo_layers_router
from app.api.routers import territorio as territorio_router


def test_auth_roles_requires_auth(client):
    response = client.get("/auth/roles")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_admin_usuarios_requires_admin_role(client, set_current_user):
    set_current_user("consulta")

    response = client.get("/admin/usuarios")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_cargas_requires_operational_role(client, set_current_user):
    set_current_user("consulta")

    response = client.get("/cargas/lotes")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_estadisticas_requires_auth(client):
    response = client.get("/estadisticas/por-hora")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_catalogos_requires_auth(client):
    response = client.get("/catalogos/delitos")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_analisis_requires_operational_role(client, set_current_user):
    set_current_user("consulta")

    response = client.get("/analisis/hotspots")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_recomendaciones_requires_operational_role(client, set_current_user):
    set_current_user("consulta")

    response = client.get("/recomendaciones/patrullaje")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_territorio_read_endpoints_allow_consulta(client, set_current_user, monkeypatch):
    set_current_user("consulta")
    monkeypatch.setattr(territorio_router, "list_territory_regions", lambda: [])

    response = client.get("/territorio/regiones")

    assert response.status_code == 200


def test_legacy_geo_layers_allow_consulta(client, set_current_user, monkeypatch):
    set_current_user("consulta")
    monkeypatch.setattr(geo_layers_router, "list_available_geo_layers", lambda: [])

    response = client.get("/capas/geojson")

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
