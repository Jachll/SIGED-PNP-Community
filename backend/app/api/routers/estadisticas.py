from datetime import date

from fastapi import APIRouter, Depends, Query

from app.schemas import EstadisticaDia, EstadisticaDiaSemana, EstadisticaHora, EstadisticaMes
from app.security import require_roles
from app.security_policy import ANALYTICS_ROLES
from app.services.estadisticas_service import (
    get_estadisticas_por_dia,
    get_estadisticas_por_dia_semana,
    get_estadisticas_por_hora,
    get_estadisticas_por_mes,
)

router = APIRouter(
    tags=["estadisticas"],
    dependencies=[Depends(require_roles(*ANALYTICS_ROLES))],
)


@router.get("/estadisticas/por-hora", response_model=list[EstadisticaHora])
def estadisticas_por_hora(
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    id_delito: int | None = Query(default=None, ge=1),
    distrito: str | None = Query(default=None, min_length=2, max_length=100),
    id_comisaria: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=100),
    division: str | None = Query(default=None, min_length=2, max_length=150),
    comisaria: str | None = Query(default=None, min_length=2, max_length=150),
    jurisdiccion: str | None = Query(default=None, min_length=1, max_length=120),
    sector: str | None = Query(default=None, min_length=1, max_length=120),
) -> list[EstadisticaHora]:
    return get_estadisticas_por_hora(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
    )


@router.get("/estadisticas/por-dia", response_model=list[EstadisticaDia])
def estadisticas_por_dia(
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    id_delito: int | None = Query(default=None, ge=1),
    distrito: str | None = Query(default=None, min_length=2, max_length=100),
    id_comisaria: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=100),
    division: str | None = Query(default=None, min_length=2, max_length=150),
    comisaria: str | None = Query(default=None, min_length=2, max_length=150),
    jurisdiccion: str | None = Query(default=None, min_length=1, max_length=120),
    sector: str | None = Query(default=None, min_length=1, max_length=120),
) -> list[EstadisticaDia]:
    return get_estadisticas_por_dia(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
    )


@router.get("/estadisticas/por-mes", response_model=list[EstadisticaMes])
def estadisticas_por_mes(
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    id_delito: int | None = Query(default=None, ge=1),
    distrito: str | None = Query(default=None, min_length=2, max_length=100),
    id_comisaria: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=100),
    division: str | None = Query(default=None, min_length=2, max_length=150),
    comisaria: str | None = Query(default=None, min_length=2, max_length=150),
    jurisdiccion: str | None = Query(default=None, min_length=1, max_length=120),
    sector: str | None = Query(default=None, min_length=1, max_length=120),
) -> list[EstadisticaMes]:
    return get_estadisticas_por_mes(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
    )


@router.get("/estadisticas/por-dia-semana", response_model=list[EstadisticaDiaSemana])
def estadisticas_por_dia_semana(
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    id_delito: int | None = Query(default=None, ge=1),
    distrito: str | None = Query(default=None, min_length=2, max_length=100),
    id_comisaria: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=100),
    division: str | None = Query(default=None, min_length=2, max_length=150),
    comisaria: str | None = Query(default=None, min_length=2, max_length=150),
    jurisdiccion: str | None = Query(default=None, min_length=1, max_length=120),
    sector: str | None = Query(default=None, min_length=1, max_length=120),
) -> list[EstadisticaDiaSemana]:
    return get_estadisticas_por_dia_semana(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
    )
