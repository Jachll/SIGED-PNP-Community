from app.schemas.auth import (
    BootstrapAdminRequest,
    CreateUserRequest,
    CurrentUser,
    LoginRequest,
    RoleResponse,
    TokenResponse,
    UserSummary,
)
from app.schemas.analisis import AgregadoEspacialResponse, HotspotResponse, ZonaCriticaResponse
from app.schemas.catalogos import ComisariaCatalogo, DelitoCatalogo, DistritoCatalogo
from app.schemas.cargas import LoteCargaDetalle, LoteCargaError, LoteCargaResumen
from app.schemas.estadisticas import (
    EstadisticaDia,
    EstadisticaDiaSemana,
    EstadisticaHora,
    EstadisticaMes,
)
from app.schemas.eventos import (
    EventoDetalleResponse,
    EventoLugarContexto,
    EventoRelacionadoResponse,
    EventoResponse,
    EventoTerritorialReferencia,
    HeatmapPoint,
)
from app.schemas.geo_layers import GeoLayerCatalogItem, GeoLayerContextOption, GeoLayerContextResponse
from app.schemas.health import HealthResponse
from app.schemas.recomendaciones import (
    RecomendacionCriterios,
    RecomendacionMetricas,
    RecomendacionPatrullajeItem,
    RecomendacionPatrullajeRequest,
    RecomendacionPatrullajeResponse,
    RecomendacionRecursos,
    RecomendacionVentanaHoraria,
    RecomendacionZonaInfo,
)
from app.schemas.territorio import TerritoryNodeItem, TerritoryScopedOption

__all__ = [
    "BootstrapAdminRequest",
    "AgregadoEspacialResponse",
    "ComisariaCatalogo",
    "CreateUserRequest",
    "CurrentUser",
    "DelitoCatalogo",
    "DistritoCatalogo",
    "EstadisticaDia",
    "EstadisticaDiaSemana",
    "EstadisticaHora",
    "EstadisticaMes",
    "EventoDetalleResponse",
    "EventoLugarContexto",
    "EventoRelacionadoResponse",
    "EventoResponse",
    "EventoTerritorialReferencia",
    "GeoLayerCatalogItem",
    "GeoLayerContextOption",
    "GeoLayerContextResponse",
    "HeatmapPoint",
    "HealthResponse",
    "HotspotResponse",
    "LoginRequest",
    "LoteCargaDetalle",
    "LoteCargaError",
    "LoteCargaResumen",
    "RecomendacionCriterios",
    "RecomendacionMetricas",
    "RecomendacionPatrullajeItem",
    "RecomendacionPatrullajeRequest",
    "RecomendacionPatrullajeResponse",
    "RecomendacionRecursos",
    "RecomendacionVentanaHoraria",
    "RecomendacionZonaInfo",
    "RoleResponse",
    "TokenResponse",
    "TerritoryNodeItem",
    "TerritoryScopedOption",
    "UserSummary",
    "ZonaCriticaResponse",
]
