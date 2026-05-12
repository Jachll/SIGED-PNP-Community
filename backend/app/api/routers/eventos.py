from datetime import date

from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.schemas import EventoDetalleResponse, EventoResponse, HeatmapPoint
from app.security import require_roles
from app.security_policy import ANALYTICS_ROLES
from app.services.eventos_service import get_evento_detalle, list_eventos, list_eventos_heatmap

router = APIRouter(
    tags=["eventos"],
    dependencies=[Depends(require_roles(*ANALYTICS_ROLES))],
)


@router.get("/eventos", response_model=list[EventoResponse])
def get_eventos(
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
    limite: int = Query(default=settings.eventos_default_limit, ge=1, le=settings.eventos_max_limit),
    offset: int = Query(default=0, ge=0, le=100000),
) -> list[EventoResponse]:
    return list_eventos(
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
        limite=limite,
        offset=offset,
    )


@router.get("/eventos/heatmap", response_model=list[HeatmapPoint])
def get_eventos_heatmap(
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
    limite: int = Query(default=settings.heatmap_default_limit, ge=1, le=settings.heatmap_max_limit),
) -> list[HeatmapPoint]:
    return list_eventos_heatmap(
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
        limite=limite,
    )


@router.get("/eventos/{id_evento}", response_model=EventoDetalleResponse)
def get_evento_by_id(
    id_evento: int,
    radio_metros: int = Query(default=150, ge=50, le=1000),
    limite_relacionados: int = Query(default=5, ge=1, le=20),
) -> EventoDetalleResponse:
    return get_evento_detalle(
        id_evento,
        radio_metros=radio_metros,
        limite_relacionados=limite_relacionados,
    )
