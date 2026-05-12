# archivo: backend/app/config.py
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

APP_ENV_ALIASES = {
    "development": "development",
    "dev": "development",
    "local": "development",
    "testing": "testing",
    "test": "testing",
    "staging": "staging",
    "stage": "staging",
    "production": "production",
    "prod": "production",
}
DEVELOPMENT_ENVS = {"development"}
NON_PRODUCTION_ENVS = {"development", "testing"}
DEPLOYMENT_ENVS = {"staging", "production"}
MIN_JWT_SECRET_LENGTH = 32
MIN_PASSWORD_HASH_ITERATIONS = 390000
INSECURE_JWT_SECRET_VALUES = {
    "",
    "SIGED_PNP_DEV_SECRET_CHANGE_ME",
}


def _get_env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_env_int(name: str, default: int) -> int:
    raw_value = _get_env_str(name, str(default))
    return int(raw_value)


def _get_env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def _resolve_app_env() -> str:
    raw_value = (_get_env_str("APP_ENV", "development").lower() or "development")
    normalized_value = APP_ENV_ALIASES.get(raw_value)

    if normalized_value is None:
        allowed_values = ", ".join(sorted(set(APP_ENV_ALIASES.values())))
        raise RuntimeError(
            f"APP_ENV='{raw_value}' no es valido. Usa uno de: {allowed_values}."
        )

    return normalized_value


APP_ENV = _resolve_app_env()
IS_PRODUCTION = APP_ENV == "production"
IS_DEPLOYMENT_ENV = APP_ENV in DEPLOYMENT_ENVS
DEFAULT_CORS_ORIGINS = (
    ("http://localhost:5173", "http://127.0.0.1:5173")
    if APP_ENV in NON_PRODUCTION_ENVS
    else ()
)


def _resolve_jwt_secret() -> tuple[str, bool]:
    configured_secret = _get_env_str("JWT_SECRET_KEY")

    if (
        configured_secret
        and configured_secret not in INSECURE_JWT_SECRET_VALUES
        and len(configured_secret) >= MIN_JWT_SECRET_LENGTH
    ):
        return configured_secret, False

    if IS_PRODUCTION:
        raise RuntimeError(
            "JWT_SECRET_KEY debe configurarse con al menos 32 caracteres en produccion."
        )

    return secrets.token_urlsafe(48), True


JWT_SECRET_KEY, JWT_SECRET_IS_GENERATED = _resolve_jwt_secret()


def _resolve_api_docs_enabled() -> bool:
    enabled = _get_env_bool("ENABLE_API_DOCS", APP_ENV in NON_PRODUCTION_ENVS)

    if IS_DEPLOYMENT_ENV and enabled:
        raise RuntimeError(
            "ENABLE_API_DOCS debe permanecer deshabilitado en staging/production."
        )

    return enabled


def _resolve_geojson_layers_dir() -> Path:
    configured_path = _get_env_str(
        "GEOJSON_LAYERS_DIR",
        str(BASE_DIR.parent / "salida_geojson"),
    )
    return Path(configured_path).expanduser().resolve()


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    app_env: str = APP_ENV
    is_production: bool = IS_PRODUCTION
    is_deployment_env: bool = IS_DEPLOYMENT_ENV
    db_host: str = _get_env_str("DB_HOST", "localhost")
    db_port: int = _get_env_int("DB_PORT", 5432)
    db_name: str = _get_env_str("DB_NAME", "siged_pnp")
    db_user: str = _get_env_str("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_connect_timeout_seconds: int = _get_env_int("DB_CONNECT_TIMEOUT_SECONDS", 5)
    db_statement_timeout_ms: int = _get_env_int("DB_STATEMENT_TIMEOUT_MS", 15000)
    db_lock_timeout_ms: int = _get_env_int("DB_LOCK_TIMEOUT_MS", 3000)
    db_idle_in_transaction_timeout_ms: int = _get_env_int(
        "DB_IDLE_IN_TRANSACTION_TIMEOUT_MS",
        10000,
    )
    db_pool_min_size: int = _get_env_int("DB_POOL_MIN_SIZE", 1)
    db_pool_max_size: int = _get_env_int("DB_POOL_MAX_SIZE", 10)
    db_application_name: str = _get_env_str("DB_APPLICATION_NAME", "siged-pnp-backend")
    backend_host: str = _get_env_str("BACKEND_HOST", "0.0.0.0")
    backend_port: int = _get_env_int("BACKEND_PORT", 8000)
    jwt_secret_key: str = JWT_SECRET_KEY
    jwt_secret_is_generated: bool = JWT_SECRET_IS_GENERATED
    jwt_algorithm: str = _get_env_str("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = _get_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    password_hash_iterations: int = _get_env_int("PASSWORD_HASH_ITERATIONS", 390000)
    allow_bootstrap_admin: bool = _get_env_bool("ALLOW_BOOTSTRAP_ADMIN", False)
    api_docs_enabled: bool = _resolve_api_docs_enabled()
    cors_allow_origins: tuple[str, ...] = _get_env_list(
        "CORS_ALLOW_ORIGINS",
        DEFAULT_CORS_ORIGINS,
    )
    cors_allow_methods: tuple[str, ...] = _get_env_list(
        "CORS_ALLOW_METHODS",
        ("GET", "POST", "OPTIONS"),
    )
    cors_allow_headers: tuple[str, ...] = _get_env_list(
        "CORS_ALLOW_HEADERS",
        ("Authorization", "Content-Type", "X-Request-ID"),
    )
    cors_allow_credentials: bool = _get_env_bool("CORS_ALLOW_CREDENTIALS", True)
    eventos_default_limit: int = _get_env_int("EVENTOS_DEFAULT_LIMIT", 5000)
    eventos_max_limit: int = _get_env_int("EVENTOS_MAX_LIMIT", 5000)
    heatmap_default_limit: int = _get_env_int("HEATMAP_DEFAULT_LIMIT", 10000)
    heatmap_max_limit: int = _get_env_int("HEATMAP_MAX_LIMIT", 10000)
    request_slow_log_ms: int = _get_env_int("REQUEST_SLOW_LOG_MS", 800)
    query_slow_log_ms: int = _get_env_int("QUERY_SLOW_LOG_MS", 250)
    operation_slow_log_ms: int = _get_env_int("OPERATION_SLOW_LOG_MS", 400)
    geojson_layers_dir: Path = _resolve_geojson_layers_dir()
    geo_layers_force_legacy: bool = _get_env_bool("GEO_LAYERS_FORCE_LEGACY", False)


def _validate_settings(current_settings: Settings) -> None:
    if current_settings.access_token_expire_minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES debe ser mayor a 0.")

    if current_settings.password_hash_iterations <= 0:
        raise RuntimeError("PASSWORD_HASH_ITERATIONS debe ser mayor a 0.")

    if (
        current_settings.is_deployment_env
        and current_settings.password_hash_iterations < MIN_PASSWORD_HASH_ITERATIONS
    ):
        raise RuntimeError(
            "PASSWORD_HASH_ITERATIONS es demasiado bajo para staging/production."
        )

    if current_settings.cors_allow_credentials and "*" in current_settings.cors_allow_origins:
        raise RuntimeError(
            "CORS_ALLOW_ORIGINS no puede incluir '*' cuando CORS_ALLOW_CREDENTIALS=true."
        )

    if current_settings.is_deployment_env and current_settings.allow_bootstrap_admin:
        raise RuntimeError(
            "ALLOW_BOOTSTRAP_ADMIN debe permanecer false en staging/production."
        )

    if current_settings.is_deployment_env and not current_settings.db_password:
        raise RuntimeError(
            "DB_PASSWORD debe configurarse en staging/production."
        )


settings = Settings()
_validate_settings(settings)
