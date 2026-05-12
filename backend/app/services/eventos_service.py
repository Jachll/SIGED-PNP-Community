from datetime import date

from fastapi import HTTPException

from app.observability import observe_operation
from app.repositories.eventos_repository import fetch_evento_detalle, fetch_eventos, fetch_eventos_heatmap
from app.schemas import EventoDetalleResponse, EventoResponse, HeatmapPoint
from app.services.common_service import raise_query_error, validate_date_range


def list_eventos(
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
    limite: int,
    offset: int,
) -> list[EventoResponse]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "eventos.listar",
            details={
                "limite": limite,
                "offset": offset,
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
            rows = fetch_eventos(
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
                limite,
                offset,
            )
            return [EventoResponse(**row) for row in rows]
    except Exception as exc:
        raise_query_error("eventos", exc)


def list_eventos_heatmap(
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
    limite: int,
) -> list[HeatmapPoint]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "eventos.heatmap",
            details={
                "limite": limite,
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
            rows = fetch_eventos_heatmap(
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
                limite,
            )
            return [HeatmapPoint(**row) for row in rows]
    except Exception as exc:
        raise_query_error("heatmap de eventos", exc)


def get_evento_detalle(
    id_evento: int,
    *,
    radio_metros: int = 150,
    limite_relacionados: int = 5,
) -> EventoDetalleResponse:
    try:
        with observe_operation(
            "eventos.detalle",
            details={
                "id_evento": id_evento,
                "radio_metros": radio_metros,
                "limite_relacionados": limite_relacionados,
            },
        ):
            row = fetch_evento_detalle(
                id_evento,
                radio_metros=radio_metros,
                limite_relacionados=limite_relacionados,
            )
            if row is None:
                raise HTTPException(status_code=404, detail="El evento solicitado no existe.")
            return EventoDetalleResponse(**row)
    except HTTPException:
        raise
    except Exception as exc:
        raise_query_error("detalle del evento", exc)
