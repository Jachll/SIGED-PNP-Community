from fastapi import APIRouter

from app.api.routers import admin, analisis, auth, cargas, catalogos, estadisticas, eventos, geo_layers, health, recomendaciones, territorio

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(cargas.router)
api_router.include_router(eventos.router)
api_router.include_router(estadisticas.router)
api_router.include_router(catalogos.router)
api_router.include_router(analisis.router)
api_router.include_router(recomendaciones.router)
api_router.include_router(geo_layers.router)
api_router.include_router(territorio.router)
