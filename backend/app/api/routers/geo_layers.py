from fastapi import APIRouter, Depends, Query, Response

from app.geo_layers import get_geo_layer_context, get_geo_layer_data, list_available_geo_layers
from app.observability import observe_operation
from app.schemas import GeoLayerCatalogItem, GeoLayerContextResponse
from app.security import require_roles
from app.security_policy import TERRITORIAL_READ_ROLES

router = APIRouter(
    tags=["capas_geo"],
    dependencies=[Depends(require_roles(*TERRITORIAL_READ_ROLES))],
)

LEGACY_GEOJSON_SUNSET = "Thu, 30 Apr 2026 23:59:59 GMT"
LEGACY_GEOJSON_REPLACEMENT = "Usa /territorio/* en lugar de /capas/geojson/*."


def _operation_details(**details: object) -> dict[str, object]:
    return {key: value for key, value in details.items() if value not in (None, "")}


def _mark_legacy_geojson_response(response: Response) -> None:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = LEGACY_GEOJSON_SUNSET
    response.headers["X-SIGED-Deprecated-Route"] = LEGACY_GEOJSON_REPLACEMENT


@router.get("/capas/geojson", response_model=list[GeoLayerCatalogItem])
def get_geo_layers_catalog(response: Response) -> list[GeoLayerCatalogItem]:
    with observe_operation("territorio.legacy.catalogo"):
        _mark_legacy_geojson_response(response)
        return [GeoLayerCatalogItem(**layer) for layer in list_available_geo_layers()]


@router.get("/capas/geojson/contexto", response_model=GeoLayerContextResponse)
def get_geo_layers_scope_context(
    response: Response,
    region: str | None = Query(default=None, min_length=2, max_length=120),
    division: str | None = Query(default=None, min_length=2, max_length=180),
    comisaria_id: int | None = Query(default=None, ge=1),
    comisaria: str | None = Query(default=None, min_length=2, max_length=180),
) -> GeoLayerContextResponse:
    with observe_operation(
        "territorio.legacy.contexto",
        details=_operation_details(region=region, division=division, comisaria_id=comisaria_id, comisaria=comisaria),
    ):
        _mark_legacy_geojson_response(response)
        return GeoLayerContextResponse(
            **get_geo_layer_context(
                region=region,
                division=division,
                comisaria=comisaria,
                comisaria_id=comisaria_id,
            )
        )


@router.get("/capas/geojson/{layer_id}")
def get_geo_layer(
    layer_id: str,
    response: Response,
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
    with observe_operation(
        "territorio.legacy.capa",
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
        _mark_legacy_geojson_response(response)
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
