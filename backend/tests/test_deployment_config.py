import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

import pytest

CONFIG_PATH = Path(__file__).resolve().parents[1] / "app" / "config.py"
MANAGED_ENV_KEYS = (
    "APP_ENV",
    "JWT_SECRET_KEY",
    "ENABLE_API_DOCS",
    "ALLOW_BOOTSTRAP_ADMIN",
    "DB_PASSWORD",
    "CORS_ALLOW_ORIGINS",
    "CORS_ALLOW_CREDENTIALS",
    "PASSWORD_HASH_ITERATIONS",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "GEO_LAYERS_FORCE_LEGACY",
)


def _load_config_module(monkeypatch, **overrides):
    for key in MANAGED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    base_env = {
        "APP_ENV": "development",
        "JWT_SECRET_KEY": "x" * 48,
        "ALLOW_BOOTSTRAP_ADMIN": "false",
        "DB_PASSWORD": "deploy-secret",
        "CORS_ALLOW_ORIGINS": "http://localhost:5173",
        "CORS_ALLOW_CREDENTIALS": "true",
        "PASSWORD_HASH_ITERATIONS": "390000",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    }

    for key, value in base_env.items():
        monkeypatch.setenv(key, value)

    for key, value in overrides.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    module_name = f"_test_config_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_config_normalizes_production_alias_and_disables_docs_by_default(monkeypatch):
    config_module = _load_config_module(monkeypatch, APP_ENV="prod")

    assert config_module.settings.app_env == "production"
    assert config_module.settings.is_production is True
    assert config_module.settings.api_docs_enabled is False


def test_config_rejects_unknown_app_env(monkeypatch):
    with pytest.raises(RuntimeError, match="APP_ENV"):
        _load_config_module(monkeypatch, APP_ENV="qa")


def test_config_rejects_public_docs_in_deployment_env(monkeypatch):
    with pytest.raises(RuntimeError, match="ENABLE_API_DOCS"):
        _load_config_module(monkeypatch, APP_ENV="staging", ENABLE_API_DOCS="true")


def test_config_rejects_bootstrap_admin_in_deployment_env(monkeypatch):
    with pytest.raises(RuntimeError, match="ALLOW_BOOTSTRAP_ADMIN"):
        _load_config_module(monkeypatch, APP_ENV="production", ALLOW_BOOTSTRAP_ADMIN="true")


def test_config_rejects_wildcard_cors_when_credentials_are_enabled(monkeypatch):
    with pytest.raises(RuntimeError, match="CORS_ALLOW_ORIGINS"):
        _load_config_module(monkeypatch, CORS_ALLOW_ORIGINS="*", CORS_ALLOW_CREDENTIALS="true")


def test_config_accepts_geo_layers_force_legacy_flag(monkeypatch):
    config_module = _load_config_module(monkeypatch, GEO_LAYERS_FORCE_LEGACY="true")

    assert config_module.settings.geo_layers_force_legacy is True
