from datetime import date
import logging

from fastapi import HTTPException, status
from psycopg2 import errors as psycopg_errors

logger = logging.getLogger("siged.services")


def validate_date_range(fecha_inicio: date | None, fecha_fin: date | None) -> None:
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(status_code=400, detail="fecha_inicio no puede ser mayor que fecha_fin")


def raise_query_error(recurso: str, exc: Exception) -> None:
    logger.exception("Error consultando %s", recurso)

    if isinstance(exc, (psycopg_errors.UndefinedTable, psycopg_errors.UndefinedColumn)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"La consulta de {recurso} no esta disponible porque faltan tablas o columnas requeridas "
                "en la base activa. Revisa las migraciones del modulo correspondiente y, para analitica "
                "territorial, verifica 13_dim_territorio.sql y 14_performance_territorial.sql."
            ),
        ) from exc

    if isinstance(exc, psycopg_errors.UndefinedFunction):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"La consulta de {recurso} requiere funciones de base de datos no disponibles en este entorno. "
                "Verifica PostGIS y las migraciones geoespaciales activas."
            ),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No se pudo completar la consulta solicitada.",
    ) from exc
