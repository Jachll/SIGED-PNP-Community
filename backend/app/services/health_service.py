import logging

from fastapi import HTTPException, status
from psycopg2 import errors as psycopg_errors

from app.observability import observe_operation
from app.repositories.health_repository import fetch_postgis_version
from app.schemas import HealthResponse

logger = logging.getLogger("siged.health")


def get_health_status() -> HealthResponse:
    try:
        with observe_operation("health.check"):
            fetch_postgis_version()
    except psycopg_errors.UndefinedFunction as exc:
        logger.exception("PostGIS no esta habilitado en la base activa")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "PostGIS no esta habilitado en la base activa. "
                "Ejecuta la migracion 02_enable_postgis.sql y vuelve a validar el backend."
            ),
        ) from exc
    except Exception as exc:
        logger.exception("No se pudo verificar la conexion con PostGIS")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No se pudo verificar PostgreSQL/PostGIS en la base activa. "
                "Revisa DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD y la migracion 02_enable_postgis.sql."
            ),
        ) from exc

    return HealthResponse(status="ok", service="siged-pnp-backend", database="postgis")
