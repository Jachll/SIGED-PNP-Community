from datetime import date, time

from pydantic import BaseModel


class EventoResponse(BaseModel):
    id_evento: int
    fecha: date
    hora: time
    id_delito: int
    nombre_delito: str
    distrito: str
    direccion: str
    latitud: float
    longitud: float
    id_comisaria: int | None
    nombre_comisaria: str | None
    fuente_registro: str
    descripcion: str | None


class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    intensidad: int


class EventoTerritorialReferencia(BaseModel):
    region: str | None = None
    division: str | None = None
    comisaria: str | None = None
    jurisdiccion: str | None = None
    sector: str | None = None


class EventoRelacionadoResponse(BaseModel):
    id_evento: int
    fecha: date
    hora: time
    nombre_delito: str
    direccion: str
    nombre_comisaria: str | None = None
    distancia_metros: int | None = None


class EventoLugarContexto(BaseModel):
    radio_metros: int
    total_eventos_historicos: int
    total_eventos_30_dias: int
    total_eventos_90_dias: int
    eventos_recientes: list[EventoRelacionadoResponse]


class EventoDetalleResponse(EventoResponse):
    referencia_territorial: EventoTerritorialReferencia
    contexto_lugar: EventoLugarContexto | None = None
