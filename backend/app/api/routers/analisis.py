from datetime import date

from fastapi import APIRouter, Depends, Query

from app.schemas import AgregadoEspacialResponse, HotspotResponse, ZonaCriticaResponse
from app.security import require_roles
from app.security_policy import OPERATIONAL_ROLES
from app.services.analisis_service import (
    list_agregados_espaciales,
    list_hotspots,
    list_zonas_criticas,
)

router = APIRouter(
    tags=["analisis"],
    dependencies=[Depends(require_roles(*OPERATIONAL_ROLES))],
)


@router.get("/analisis/agregados-espaciales", response_model=list[AgregadoEspacialResponse])
def get_agregados_espaciales(
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
    tamano_celda_metros: int = Query(default=300, ge=50, le=5000),
    min_eventos: int = Query(default=2, ge=1, le=100),
    limite: int = Query(default=200, ge=1, le=2000),
) -> list[AgregadoEspacialResponse]:
    return list_agregados_espaciales(
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
        tamano_celda_metros=tamano_celda_metros,
        min_eventos=min_eventos,
        limite=limite,
    )


@router.get("/analisis/zonas-criticas", response_model=list[ZonaCriticaResponse])
def get_zonas_criticas(
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
    agrupado_por: str = Query(default="distrito"),
    min_eventos: int = Query(default=3, ge=1, le=1000),
    limite: int = Query(default=10, ge=1, le=100),
) -> list[ZonaCriticaResponse]:
    return list_zonas_criticas(
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
        agrupado_por=agrupado_por,
        min_eventos=min_eventos,
        limite=limite,
    )


@router.get("/analisis/hotspots", response_model=list[HotspotResponse])
def get_hotspots(
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
    estado: str | None = Query(default=None, min_length=3, max_length=20),
    limite: int = Query(default=50, ge=1, le=200),
) -> list[HotspotResponse]:
    return list_hotspots(
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
        estado=estado,
        limite=limite,
    )
