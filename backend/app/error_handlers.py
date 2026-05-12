import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.observability import get_request_id

logger = logging.getLogger("siged.errors")

STATUS_CODE_TO_ERROR_CODE = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_error",
    status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
}


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        message = _sanitize_http_message(exc.status_code, exc.detail)
        details = _sanitize_http_details(exc.status_code, exc.detail)
        payload = _build_error_payload(
            status_code=exc.status_code,
            message=message,
            request=request,
            details=details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        payload = _build_error_payload(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Solicitud invalida.",
            request=request,
            details=_format_validation_errors(exc.errors()),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Excepcion no controlada en %s %s",
            request.method,
            request.url.path,
        )
        payload = _build_error_payload(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Ocurrio un error interno. Intenta nuevamente.",
            request=request,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload,
        )


def _build_error_payload(
    *,
    status_code: int,
    message: str,
    request: Request,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "detail": message,
        "error": {
            "code": STATUS_CODE_TO_ERROR_CODE.get(status_code, "http_error"),
            "message": message,
        },
    }

    request_id = get_request_id(request)
    if request_id:
        payload["error"]["request_id"] = request_id

    if details:
        payload["error"]["details"] = details

    return payload


def _sanitize_http_message(status_code: int, detail: Any) -> str:
    if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        return "Ocurrio un error interno. Intenta nuevamente."

    if isinstance(detail, str) and detail.strip():
        return detail

    return HTTPStatus(status_code).phrase


def _sanitize_http_details(status_code: int, detail: Any) -> list[dict[str, Any]] | None:
    if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        return None

    if isinstance(detail, list):
        return [{"message": str(item)} for item in detail]

    if isinstance(detail, dict):
        return [{"message": str(value)} for value in detail.values()]

    return None


def _format_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted_errors: list[dict[str, Any]] = []

    for error in errors:
        location = ".".join(str(part) for part in error.get("loc", ()))
        formatted_errors.append(
            {
                "field": location or "body",
                "message": error.get("msg", "Valor invalido."),
            }
        )

    return formatted_errors
