from datetime import date, datetime

from pydantic import BaseModel


class AgregadoEspacialResponse(BaseModel):
    id_agregado: int
    tipo_agregado: str
    tamano_celda_metros: int
    total_eventos: int
    intensidad: float
    lat: float
    lng: float
    bbox: list[float]
    distrito_principal: str | None
    id_delito_principal: int | None
    delito_principal: str | None
    total_distritos: int
    total_delitos: int


class ZonaCriticaResponse(BaseModel):
    id_zona: int | None
    codigo_zona: str
    nombre_zona: str
    tipo_zona: str
    distrito: str
    id_comisaria: int | None
    nombre_comisaria: str | None
    prioridad_operativa: str
    estado_zona: str
    total_hotspots: int
    total_eventos: int
    total_eventos_periodo: int
    porcentaje_total: float
    intensidad_total: float
    nivel_riesgo: str
    latitud: float
    longitud: float
    origen_datos: str
    agrupado_por: str
    periodo_inicio: date | None
    periodo_fin: date | None


class HotspotResponse(BaseModel):
    id_hotspot: int
    periodo_inicio: date
    periodo_fin: date
    fecha_deteccion: datetime
    id_delito: int | None
    nombre_delito: str | None
    distrito: str
    id_zona: int | None
    nombre_zona: str | None
    id_comisaria: int | None
    nombre_comisaria: str | None
    nivel_riesgo: str
    intensidad: float
    conteo_eventos: int
    latitud: float
    longitud: float
    radio_metros: int
    fuente_analisis: str
    estado_hotspot: str
    observaciones: str | None
    origen_datos: str
