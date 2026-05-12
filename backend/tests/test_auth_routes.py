from datetime import datetime

from fastapi import HTTPException

from app.api.routers import auth as auth_router
from app.schemas.auth import TokenResponse, UserSummary


def _token_payload(username: str = "admin") -> TokenResponse:
    return TokenResponse(
        access_token="token-demo",
        token_type="bearer",
        expires_in=3600,
        user=UserSummary(
            id_usuario=1,
            username=username,
            nombre_completo="Administrador Demo",
            rol_codigo="admin",
            activo=True,
            ultimo_login=None,
            created_at=datetime(2026, 1, 1, 8, 0, 0),
        ),
    )


def test_login_success(client, monkeypatch):
    monkeypatch.setattr(auth_router, "authenticate_user", lambda username, password: _token_payload())

    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "supersecreto"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "token-demo"
    assert payload["user"]["username"] == "admin"


def test_login_failure_returns_sanitized_error(client, monkeypatch):
    def _raise_invalid_credentials(username, password):
        raise HTTPException(status_code=401, detail="Credenciales invalidas.")

    monkeypatch.setattr(auth_router, "authenticate_user", _raise_invalid_credentials)

    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "incorrecta"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["detail"] == "Credenciales invalidas."
    assert payload["error"]["code"] == "unauthorized"


def test_get_me_returns_current_user(client, set_current_user):
    user = set_current_user("consulta")

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == user.username


def test_get_roles_for_analytics_user(client, set_current_user, monkeypatch):
    set_current_user("consulta")
    monkeypatch.setattr(
        auth_router,
        "list_roles",
        lambda: [
            {"codigo": "admin", "nombre": "Administrador", "descripcion": "Control total"},
            {"codigo": "consulta", "nombre": "Consulta", "descripcion": "Solo lectura"},
        ],
    )

    response = client.get("/auth/roles")

    assert response.status_code == 200
    assert len(response.json()) == 2
