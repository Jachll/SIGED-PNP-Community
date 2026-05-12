from datetime import date

from app.observability import observe_operation
from app.repositories.estadisticas_repository import (
    fetch_estadisticas_por_dia,
    fetch_estadisticas_por_dia_semana,
    fetch_estadisticas_por_hora,
    fetch_estadisticas_por_mes,
)
from app.schemas import EstadisticaDia, EstadisticaDiaSemana, EstadisticaHora, EstadisticaMes
from app.services.common_service import raise_query_error, validate_date_range


def get_estadisticas_por_hora(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
) -> list[EstadisticaHora]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "estadisticas.por_hora",
            details={
                "id_delito": id_delito,
                "distrito": distrito,
                "id_comisaria": id_comisaria,
                "region": region,
                "division": division,
                "comisaria": comisaria,
                "jurisdiccion": jurisdiccion,
                "sector": sector,
            },
        ):
            rows = fetch_estadisticas_por_hora(
                fecha_inicio,
                fecha_fin,
                id_delito,
                distrito,
                id_comisaria,
                region,
                division,
                comisaria,
                jurisdiccion,
                sector,
            )
            return [EstadisticaHora(**row) for row in rows]
    except Exception as exc:
        raise_query_error("estadisticas por hora", exc)


def get_estadisticas_por_dia(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
) -> list[EstadisticaDia]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "estadisticas.por_dia",
            details={
                "id_delito": id_delito,
                "distrito": distrito,
                "id_comisaria": id_comisaria,
                "region": region,
                "division": division,
                "comisaria": comisaria,
                "jurisdiccion": jurisdiccion,
                "sector": sector,
            },
        ):
            rows = fetch_estadisticas_por_dia(
                fecha_inicio,
                fecha_fin,
                id_delito,
                distrito,
                id_comisaria,
                region,
                division,
                comisaria,
                jurisdiccion,
                sector,
            )
            return [EstadisticaDia(**row) for row in rows]
    except Exception as exc:
        raise_query_error("estadisticas por dia", exc)


def get_estadisticas_por_mes(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
) -> list[EstadisticaMes]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "estadisticas.por_mes",
            details={
                "id_delito": id_delito,
                "distrito": distrito,
                "id_comisaria": id_comisaria,
                "region": region,
                "division": division,
                "comisaria": comisaria,
                "jurisdiccion": jurisdiccion,
                "sector": sector,
            },
        ):
            rows = fetch_estadisticas_por_mes(
                fecha_inicio,
                fecha_fin,
                id_delito,
                distrito,
                id_comisaria,
                region,
                division,
                comisaria,
                jurisdiccion,
                sector,
            )
            return [EstadisticaMes(**row) for row in rows]
    except Exception as exc:
        raise_query_error("estadisticas por mes", exc)


def get_estadisticas_por_dia_semana(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
) -> list[EstadisticaDiaSemana]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "estadisticas.por_dia_semana",
            details={
                "id_delito": id_delito,
                "distrito": distrito,
                "id_comisaria": id_comisaria,
                "region": region,
                "division": division,
                "comisaria": comisaria,
                "jurisdiccion": jurisdiccion,
                "sector": sector,
            },
        ):
            rows = fetch_estadisticas_por_dia_semana(
                fecha_inicio,
                fecha_fin,
                id_delito,
                distrito,
                id_comisaria,
                region,
                division,
                comisaria,
                jurisdiccion,
                sector,
            )
            return [EstadisticaDiaSemana(**row) for row in rows]
    except Exception as exc:
        raise_query_error("estadisticas por dia de semana", exc)
