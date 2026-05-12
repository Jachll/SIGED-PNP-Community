from datetime import date, datetime

from pydantic import BaseModel, Field


class RecomendacionVentanaHoraria(BaseModel):
    turno: str
    hora_inicio: str
    hora_fin: str


class RecomendacionZonaInfo(BaseModel):
    id_zona: int | None
    codigo_zona: str
    nombre_zona: str
    tipo_zona: str
    distrito: str
    id_comisaria: int | None
    nombre_comisaria: str | None
    latitud: float
    longitud: float


class RecomendacionMetricas(BaseModel):
    total_eventos_franja: int
    total_eventos_zona: int
    promedio_diario_franja: float
    participacion_franja: float
    indice_concentracion: float


class RecomendacionCriterios(BaseModel):
    minimo_eventos: int
    minimo_participacion_franja: float
    minimo_indice_concentracion: float


class RecomendacionRecursos(BaseModel):
    cantidad_efectivos: int
    cantidad_unidades: int


class RecomendacionPatrullajeItem(BaseModel):
    id_recomendacion: int | None = None
    persistida: bool = False
    origen_datos: str
    regla_codigo: str
    regla_nombre: str
    prioridad: str
    tipo_recomendacion: str
    fecha_generacion: datetime
    fecha_operativa: date
    periodo_inicio: date
    periodo_fin: date
    dias_analizados: int
    ventana_horaria: RecomendacionVentanaHoraria
    zona: RecomendacionZonaInfo
    metricas: RecomendacionMetricas
    criterios_regla: RecomendacionCriterios
    detalle_operativo: str
    justificacion: list[str]
    recursos_sugeridos: RecomendacionRecursos


class RecomendacionPatrullajeResponse(BaseModel):
    fecha_generacion: datetime
    fecha_operativa: date
    periodo_inicio: date | None
    periodo_fin: date | None
    total_recomendaciones: int
    reglas_evaluadas: list[str]
    recomendaciones: list[RecomendacionPatrullajeItem]


class RecomendacionPatrullajeRequest(BaseModel):
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    fecha_operativa: date | None = None
    id_delito: int | None = Field(default=None, ge=1)
    distrito: str | None = Field(default=None, min_length=2, max_length=100)
    id_comisaria: int | None = Field(default=None, ge=1)
    region: str | None = Field(default=None, min_length=2, max_length=100)
    division: str | None = Field(default=None, min_length=2, max_length=150)
    comisaria: str | None = Field(default=None, min_length=2, max_length=150)
    jurisdiccion: str | None = Field(default=None, min_length=1, max_length=120)
    sector: str | None = Field(default=None, min_length=1, max_length=120)
    turno: str | None = Field(default=None, min_length=4, max_length=20)
    limite: int = Field(default=20, ge=1, le=100)
    guardar: bool = False
