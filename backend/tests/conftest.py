from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.auth import CurrentUser
from app.security import get_current_user


@pytest.fixture()
def app():
    application = create_app()
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def set_current_user(app):
    def _set(role: str = "admin") -> CurrentUser:
        user = CurrentUser(
            id_usuario=1,
            username=f"{role}_user",
            nombre_completo=f"Usuario {role}",
            rol_codigo=role,
            activo=True,
            ultimo_login=None,
            created_at=datetime(2026, 1, 1, 10, 0, 0),
        )
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    return _set
