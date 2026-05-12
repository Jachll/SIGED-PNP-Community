# archivo: backend/app/main.py
from contextlib import asynccontextmanager
import logging
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.database import close_connection_pool
from app.error_handlers import install_exception_handlers
from app.observability import (
    REQUEST_ID_HEADER,
    bind_request_context,
    clear_request_context,
    configure_logging,
    ensure_request_id,
    observe_request,
)
from app.startup_repairs import ensure_database_repairs


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    ensure_database_repairs()
    try:
        yield
    finally:
        close_connection_pool()


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="SIGED-PNP API",
        version="0.2.0",
        lifespan=app_lifespan,
        docs_url="/docs" if settings.api_docs_enabled else None,
        redoc_url="/redoc" if settings.api_docs_enabled else None,
        openapi_url="/openapi.json" if settings.api_docs_enabled else None,
    )

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_allow_origins),
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=list(settings.cors_allow_methods),
            allow_headers=list(settings.cors_allow_headers),
        )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = ensure_request_id(request)
        context_tokens = bind_request_context(request, request_id)
        started_at = perf_counter()
        status_code = 500
        errored = False

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        except Exception:
            errored = True
            raise
        finally:
            observe_request(
                request=request,
                status_code=status_code,
                duration_ms=(perf_counter() - started_at) * 1000,
                errored=errored,
            )
            clear_request_context(context_tokens)

    install_exception_handlers(app)

    if settings.jwt_secret_is_generated:
        logging.getLogger("siged.startup").warning(
            "JWT_SECRET_KEY no configurado o inseguro. Se genero una clave efimera para este entorno."
        )

    app.include_router(api_router)
    return app


app = create_app()
