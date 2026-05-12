from datetime import date

from fastapi import HTTPException

from app.observability import observe_operation
from app.repositories.analisis_repository import (
    fetch_agregados_espaciales,
    fetch_hotspots,
    fetch_zonas_criticas,
)
from app.schemas import AgregadoEspacialResponse, HotspotResponse, ZonaCriticaResponse
from app.services.common_service import raise_query_error, validate_date_range


def list_agregados_espaciales(
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
    tamano_celda_metros: int,
    min_eventos: int,
    limite: int,
) -> list[AgregadoEspacialResponse]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "analisis.agregados_espaciales",
            details={
                "limite": limite,
                "min_eventos": min_eventos,
                "tamano_celda_metros": tamano_celda_metros,
            },
        ):
            rows = fetch_agregados_espaciales(
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
            return [AgregadoEspacialResponse(**row) for row in rows]
    except Exception as exc:
        raise_query_error("agregados espaciales", exc)


def list_hotspots(
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
    estado: str | None,
    limite: int,
) -> list[HotspotResponse]:
    validate_date_range(fecha_inicio, fecha_fin)

    try:
        with observe_operation(
            "analisis.hotspots",
            details={
                "limite": limite,
                "estado": estado,
                "distrito": distrito,
                "id_comisaria": id_comisaria,
                "region": region,
                "division": division,
                "comisaria": comisaria,
                "jurisdiccion": jurisdiccion,
                "sector": sector,
            },
        ):
            rows = fetch_hotspots(
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
            return [HotspotResponse(**row) for row in rows]
    except Exception as exc:
        raise_query_error("analisis de hotspots", exc)


def list_zonas_criticas(
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
    agrupado_por: str,
    min_eventos: int,
    limite: int,
) -> list[ZonaCriticaResponse]:
    validate_date_range(fecha_inicio, fecha_fin)

    agrupado_por_normalizado = agrupado_por.strip().lower()
    if agrupado_por_normalizado not in {"distrito", "comisaria", "zona_operativa"}:
        raise HTTPException(
            status_code=400,
            detail="agrupado_por debe ser uno de: distrito, comisaria, zona_operativa",
        )

    try:
        with observe_operation(
            "analisis.zonas_criticas",
            details={
                "agrupado_por": agrupado_por_normalizado,
                "limite": limite,
                "min_eventos": min_eventos,
            },
        ):
            rows = fetch_zonas_criticas(
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
                agrupado_por=agrupado_por_normalizado,
                min_eventos=min_eventos,
                limite=limite,
            )
            return [ZonaCriticaResponse(**row) for row in rows]
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="El agrupamiento solicitado no esta disponible en este entorno.",
        ) from exc
    except Exception as exc:
        raise_query_error("zonas criticas", exc)
