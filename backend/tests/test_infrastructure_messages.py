from fastapi.security import HTTPAuthorizationCredentials
import pytest
from psycopg2 import errors as psycopg_errors

from app.security import get_current_user
from app.services import auth_service, cargas_service, common_service, health_service


def test_auth_storage_ready_message_is_explicit(monkeypatch):
    monkeypatch.setattr(auth_service, "auth_tables_ready", lambda: False)

    with pytest.raises(Exception) as exc_info:
        auth_service.ensure_auth_storage_ready()

    assert exc_info.value.status_code == 503
    assert "11_auth_minima.sql" in exc_info.value.detail


def test_cargas_storage_ready_message_is_explicit(monkeypatch):
    monkeypatch.setattr(cargas_service, "cargas_tables_ready", lambda: False)

    with pytest.raises(Exception) as exc_info:
        cargas_service.ensure_cargas_storage_ready()

    assert exc_info.value.status_code == 503
    assert "06_lotes_staging.sql" in exc_info.value.detail
    assert "07_eventos_lote_fk.sql" in exc_info.value.detail
    assert "15_etl_asignacion_territorial.sql" in exc_info.value.detail


def test_cargas_storage_ready_requires_territorial_assignment_columns(monkeypatch):
    monkeypatch.setattr(cargas_service, "cargas_tables_ready", lambda: True)
    monkeypatch.setattr(cargas_service, "territorial_assignment_columns_ready", lambda: False)

    with pytest.raises(Exception) as exc_info:
        cargas_service.ensure_cargas_storage_ready()

    assert exc_info.value.status_code == 503
    assert "15_etl_asignacion_territorial.sql" in exc_info.value.detail


def test_security_message_is_explicit_when_auth_tables_are_missing(monkeypatch):
    monkeypatch.setattr("app.security.auth_tables_ready", lambda: False)

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-demo")

    with pytest.raises(Exception) as exc_info:
        get_current_user(credentials)

    assert exc_info.value.status_code == 503
    assert "11_auth_minima.sql" in exc_info.value.detail


def test_health_message_is_explicit_for_missing_postgis(monkeypatch):
    def _raise_missing_postgis():
        raise psycopg_errors.UndefinedFunction("PostGIS_Version does not exist")

    monkeypatch.setattr(health_service, "fetch_postgis_version", _raise_missing_postgis)

    with pytest.raises(Exception) as exc_info:
        health_service.get_health_status()

    assert exc_info.value.status_code == 503
    assert "02_enable_postgis.sql" in exc_info.value.detail


def test_query_error_mentions_required_migrations():
    with pytest.raises(Exception) as exc_info:
        common_service.raise_query_error("analisis de hotspots", psycopg_errors.UndefinedTable("tabla faltante"))

    assert exc_info.value.status_code == 503
    assert "13_dim_territorio.sql" in exc_info.value.detail
