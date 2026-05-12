from fastapi import APIRouter, Depends, Query

from app.geo_layers import (
    get_geo_layer_context,
    get_geo_layer_data,
    list_available_geo_layers,
    list_territory_comisarias,
    list_territory_divisions,
    list_territory_jurisdicciones,
    list_territory_regions,
    list_territory_sectores,
)
from app.observability import log_structured, observe_operation
from app.schemas import (
    GeoLayerCatalogItem,
    GeoLayerContextResponse,
    TerritoryNodeItem,
    TerritoryScopedOption,
)
from app.security import require_roles
from app.security_policy import TERRITORIAL_READ_ROLES

router = APIRouter(
    tags=["territorio"],
    dependencies=[Depends(require_roles(*TERRITORIAL_READ_ROLES))],
)


def _operation_details(**details: object) -> dict[str, object]:
    return {key: value for key, value in details.items() if value not in (None, "")}


def _log_territory_endpoint(endpoint: str, **details: object) -> None:
    log_structured(
        "siged.territorio.endpoint",
        "territorial_endpoint_invoked",
        endpoint=endpoint,
        details=_operation_details(**details),
    )


def _get_layer_payload(
    layer_id: str,
    *,
    region_id: int | None = None,
    region: str | None = None,
    division_id: int | None = None,
    division: str | None = None,
    comisaria_id: int | None = None,
    comisaria: str | None = None,
    jurisdiccion: str | None = None,
    sector: str | None = None,
    detail: str | None = None,
    bbox: str | None = None,
) -> dict:
    return get_geo_layer_data(
        layer_id,
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        detail=detail,
        bbox=bbox,
    )


@router.get("/territorio/capas", response_model=list[GeoLayerCatalogItem])
def get_territory_layers_catalog() -> list[GeoLayerCatalogItem]:
    _log_territory_endpoint("territorio.capas")
    with observe_operation("territorio.catalogo"):
        return [GeoLayerCatalogItem(**layer) for layer in list_available_geo_layers()]


@router.get("/territorio/contexto", response_model=GeoLayerContextResponse)
def get_territory_context(
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
) -> GeoLayerContextResponse:
    _log_territory_endpoint(
        "territorio.contexto",
        region=region,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
    )
    with observe_operation(
        "territorio.contexto",
        details=_operation_details(region=region, division=division, comisaria_id=comisaria_id, comisaria=comisaria),
    ):
        return GeoLayerContextResponse(
            **get_geo_layer_context(region=region, division=division, comisaria=comisaria, comisaria_id=comisaria_id)
        )


@router.get("/territorio/regiones", response_model=list[TerritoryNodeItem])
def get_territory_regions() -> list[TerritoryNodeItem]:
    _log_territory_endpoint("territorio.regiones")
    with observe_operation("territorio.regiones"):
        return [TerritoryNodeItem(**item) for item in list_territory_regions()]


@router.get("/territorio/divisiones", response_model=list[TerritoryNodeItem])
def get_territory_divisions(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
) -> list[TerritoryNodeItem]:
    _log_territory_endpoint("territorio.divisiones", region_id=region_id, region=region)
    with observe_operation(
        "territorio.divisiones",
        details=_operation_details(region_id=region_id, region=region),
    ):
        return [TerritoryNodeItem(**item) for item in list_territory_divisions(region_id=region_id, region=region)]


@router.get("/territorio/comisarias", response_model=list[TerritoryNodeItem])
def get_territory_comisarias(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
) -> list[TerritoryNodeItem]:
    _log_territory_endpoint(
        "territorio.comisarias",
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
    )
    with observe_operation(
        "territorio.comisarias",
        details=_operation_details(
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
        ),
    ):
        return [
            TerritoryNodeItem(**item)
            for item in list_territory_comisarias(
                region_id=region_id,
                region=region,
                division_id=division_id,
                division=division,
            )
        ]


@router.get("/territorio/jurisdicciones", response_model=list[TerritoryScopedOption])
def get_territory_jurisdicciones(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
) -> list[TerritoryScopedOption]:
    _log_territory_endpoint(
        "territorio.jurisdicciones",
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
    )
    with observe_operation(
        "territorio.jurisdicciones",
        details=_operation_details(
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
        ),
    ):
        return [
            TerritoryScopedOption(**item)
            for item in list_territory_jurisdicciones(
                region_id=region_id,
                region=region,
                division_id=division_id,
                division=division,
                comisaria_id=comisaria_id,
                comisaria=comisaria,
            )
        ]


@router.get("/territorio/sectores", response_model=list[TerritoryScopedOption])
def get_territory_sectores(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
) -> list[TerritoryScopedOption]:
    _log_territory_endpoint(
        "territorio.sectores",
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
    )
    with observe_operation(
        "territorio.sectores",
        details=_operation_details(
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
        ),
    ):
        return [
            TerritoryScopedOption(**item)
            for item in list_territory_sectores(
                region_id=region_id,
                region=region,
                division_id=division_id,
                division=division,
                comisaria_id=comisaria_id,
                comisaria=comisaria,
            )
        ]


@router.get("/territorio/capas/{layer_id}")
def get_territory_layer(
    layer_id: str,
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
    jurisdiccion: str | None = Query(default=None, min_length=1, max_length=120),
    sector: str | None = Query(default=None, min_length=1, max_length=120),
    detail: str | None = Query(default="auto", pattern="^(auto|simplified|full)$"),
    bbox: str | None = Query(default=None, min_length=7, max_length=120),
) -> dict:
    _log_territory_endpoint(
        "territorio.capa",
        layer_id=layer_id,
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        detail=detail,
        bbox=bbox,
    )
    with observe_operation(
        "territorio.capa",
        details=_operation_details(
            layer_id=layer_id,
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            jurisdiccion=jurisdiccion,
            sector=sector,
            detail=detail,
        ),
    ):
        return _get_layer_payload(
            layer_id,
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            jurisdiccion=jurisdiccion,
            sector=sector,
            detail=detail,
            bbox=bbox,
        )


@router.get("/territorio/regiones/geojson")
def get_regions_geojson(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    detail: str | None = Query(default="auto", pattern="^(auto|simplified|full)$"),
    bbox: str | None = Query(default=None, min_length=7, max_length=120),
) -> dict:
    _log_territory_endpoint(
        "territorio.geojson.regiones",
        region_id=region_id,
        region=region,
        detail=detail,
        bbox=bbox,
    )
    with observe_operation(
        "territorio.geojson.regiones",
        details=_operation_details(region_id=region_id, region=region, detail=detail),
    ):
        return _get_layer_payload("regiones", region_id=region_id, region=region, detail=detail, bbox=bbox)


@router.get("/territorio/divisiones/geojson")
def get_divisions_geojson(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    detail: str | None = Query(default="auto", pattern="^(auto|simplified|full)$"),
    bbox: str | None = Query(default=None, min_length=7, max_length=120),
) -> dict:
    _log_territory_endpoint(
        "territorio.geojson.divisiones",
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        detail=detail,
        bbox=bbox,
    )
    with observe_operation(
        "territorio.geojson.divisiones",
        details=_operation_details(
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            detail=detail,
        ),
    ):
        return _get_layer_payload(
            "divisiones",
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            detail=detail,
            bbox=bbox,
        )


@router.get("/territorio/comisarias/geojson")
def get_comisarias_geojson(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
    detail: str | None = Query(default="auto", pattern="^(auto|simplified|full)$"),
    bbox: str | None = Query(default=None, min_length=7, max_length=120),
) -> dict:
    _log_territory_endpoint(
        "territorio.geojson.comisarias",
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
        detail=detail,
        bbox=bbox,
    )
    with observe_operation(
        "territorio.geojson.comisarias",
        details=_operation_details(
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            detail=detail,
        ),
    ):
        return _get_layer_payload(
            "comisarias",
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            detail=detail,
            bbox=bbox,
        )


@router.get("/territorio/jurisdicciones/geojson")
def get_jurisdicciones_geojson(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
    jurisdiccion: str | None = Query(default=None, min_length=1, max_length=120),
    detail: str | None = Query(default="auto", pattern="^(auto|simplified|full)$"),
    bbox: str | None = Query(default=None, min_length=7, max_length=120),
) -> dict:
    _log_territory_endpoint(
        "territorio.geojson.jurisdicciones",
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        detail=detail,
        bbox=bbox,
    )
    with observe_operation(
        "territorio.geojson.jurisdicciones",
        details=_operation_details(
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            jurisdiccion=jurisdiccion,
            detail=detail,
        ),
    ):
        return _get_layer_payload(
            "jurisdicciones",
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            jurisdiccion=jurisdiccion,
            detail=detail,
            bbox=bbox,
        )


@router.get("/territorio/sectores/geojson")
def get_sectores_geojson(
    region_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division_id: int | None = Query(default=None, ge=1),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
    sector: str | None = Query(default=None, min_length=1, max_length=120),
    detail: str | None = Query(default="auto", pattern="^(auto|simplified|full)$"),
    bbox: str | None = Query(default=None, min_length=7, max_length=120),
) -> dict:
    _log_territory_endpoint(
        "territorio.geojson.sectores",
        region_id=region_id,
        region=region,
        division_id=division_id,
        division=division,
        comisaria_id=comisaria_id,
        comisaria=comisaria,
        sector=sector,
        detail=detail,
        bbox=bbox,
    )
    with observe_operation(
        "territorio.geojson.sectores",
        details=_operation_details(
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            sector=sector,
            detail=detail,
        ),
    ):
        return _get_layer_payload(
            "sectores",
            region_id=region_id,
            region=region,
            division_id=division_id,
            division=division,
            comisaria_id=comisaria_id,
            comisaria=comisaria,
            sector=sector,
            detail=detail,
            bbox=bbox,
        )
