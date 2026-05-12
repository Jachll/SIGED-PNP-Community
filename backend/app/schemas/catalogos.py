from pydantic import BaseModel


class DelitoCatalogo(BaseModel):
    id_delito: int
    nombre_delito: str
    descripcion: str | None


class ComisariaCatalogo(BaseModel):
    id_comisaria: int
    nombre_comisaria: str
    distrito: str
    direccion: str | None


class DistritoCatalogo(BaseModel):
    distrito: str
