from pydantic import BaseModel


class TerritoryNodeItem(BaseModel):
    id: int
    code: str | None = None
    name: str
    parent_id: int | None = None
    region_id: int | None = None


class TerritoryScopedOption(BaseModel):
    id: int
    value: str
    label: str
    code: str | None = None
    parent_id: int | None = None
