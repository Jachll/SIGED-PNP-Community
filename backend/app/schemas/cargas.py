from datetime import datetime

from pydantic import BaseModel, Field


class LoteCargaResumen(BaseModel):
    id_lote: int
    nombre_archivo: str
    estado_lote: str
    total_filas: int
    filas_validas: int
    filas_error: int
    filas_promovidas: int
    fecha_inicio: datetime
    fecha_fin: datetime | None = None


class LoteCargaError(BaseModel):
    id_staging: int
    numero_fila: int
    estado_registro: str
    mensaje_error: str | None = None
    estado_territorial: str | None = None
    regla_territorial: str | None = None
    motivo_territorial: str | None = None
    conflicto_territorial: bool = False
    id_comisaria_original: int | None = None
    id_comisaria_resuelta: int | None = None
    nombre_comisaria_resuelta: str | None = None
    valores: dict[str, str | None] = Field(default_factory=dict)


class LoteCargaDetalle(LoteCargaResumen):
    ruta_archivo: str | None = None
    observaciones: str | None = None
    errores: list[LoteCargaError] = Field(default_factory=list)
