from pydantic import BaseModel


class GeoLayerCatalogItem(BaseModel):
    id: str
    label: str
    file_name: str
    geometry_type: str
    stroke_color: str
    fill_color: str
    fill_opacity: float
    recommended_zoom: int
    size_bytes: int
    heavy: bool
    requires_region: bool
    requires_division: bool
    requires_comisaria: bool


class GeoLayerContextOption(BaseModel):
    value: str
    label: str
    id: int | None = None
    code: str | None = None
    parent_id: int | None = None


class GeoLayerContextResponse(BaseModel):
    regions: list[str]
    divisions: list[str]
    comisarias: list[GeoLayerContextOption] = []
    jurisdicciones: list[GeoLayerContextOption] = []
    sectores: list[GeoLayerContextOption] = []
