from datetime import date

from pydantic import BaseModel


class EstadisticaHora(BaseModel):
    hora: int
    total: int


class EstadisticaDia(BaseModel):
    fecha: date
    total: int


class EstadisticaMes(BaseModel):
    periodo: str
    anio: int
    mes: int
    total: int


class EstadisticaDiaSemana(BaseModel):
    dia_semana_numero: int
    dia_semana: str
    total: int
