import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock
from time import perf_counter
from uuid import uuid4

from fastapi import Request

from app.config import settings

REQUEST_ID_HEADER = "X-Request-ID"

_request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
_request_path_context: ContextVar[str | None] = ContextVar("request_path", default=None)
_request_method_context: ContextVar[str | None] = ContextVar("request_method", default=None)

_metrics_lock = Lock()
_metrics: dict[str, dict[str, float | int]] = {}


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def ensure_request_id(request: Request) -> str:
    incoming_request_id = request.headers.get(REQUEST_ID_HEADER, "").strip()
    request_id = incoming_request_id or uuid4().hex
    request.state.request_id = request_id
    return request_id


def bind_request_context(request: Request, request_id: str) -> list[object]:
    return [
        _request_id_context.set(request_id),
        _request_path_context.set(request.url.path),
        _request_method_context.set(request.method),
    ]


def clear_request_context(tokens: list[object]) -> None:
    _request_id_context.reset(tokens[0])
    _request_path_context.reset(tokens[1])
    _request_method_context.reset(tokens[2])


def get_request_id(request: Request | None = None) -> str | None:
    if request is not None:
        return getattr(request.state, "request_id", None)
    return _request_id_context.get()


def _get_request_path() -> str | None:
    return _request_path_context.get()


def _get_request_method() -> str | None:
    return _request_method_context.get()


def _structured_payload(event: str, **payload: object) -> str:
    base_payload: dict[str, object] = {"event": event}
    request_id = get_request_id()
    if request_id:
        base_payload["request_id"] = request_id

    request_path = _get_request_path()
    request_method = _get_request_method()
    if request_path:
        base_payload["path"] = request_path
    if request_method:
        base_payload["method"] = request_method

    for key, value in payload.items():
        if value is not None:
            base_payload[key] = value

    return json.dumps(base_payload, ensure_ascii=True, sort_keys=True, default=str)


def log_structured(
    logger_name: str,
    event: str,
    *,
    level: int = logging.INFO,
    **payload: object,
) -> None:
    logging.getLogger(logger_name).log(level, _structured_payload(event, **payload))


def _record_metric(name: str, duration_ms: float, errored: bool) -> None:
    with _metrics_lock:
        metric = _metrics.setdefault(
            name,
            {
                "count": 0,
                "errors": 0,
                "total_ms": 0.0,
                "max_ms": 0.0,
            },
        )
        metric["count"] += 1
        metric["total_ms"] += duration_ms
        metric["max_ms"] = max(metric["max_ms"], duration_ms)
        if errored:
            metric["errors"] += 1


def get_metrics_snapshot() -> dict[str, dict[str, float | int]]:
    with _metrics_lock:
        return {
            key: {
                **value,
                "avg_ms": round(float(value["total_ms"]) / int(value["count"]), 2)
                if int(value["count"]) > 0
                else 0.0,
            }
            for key, value in _metrics.items()
        }


def observe_request(
    *,
    request: Request,
    status_code: int,
    duration_ms: float,
    errored: bool,
) -> None:
    metric_name = f"request:{request.method}:{request.url.path}"
    _record_metric(metric_name, duration_ms, errored)

    log_structured(
        "siged.request",
        "request_completed",
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        slow=duration_ms >= settings.request_slow_log_ms,
        client_ip=request.client.host if request.client else None,
    )


def observe_query(
    *,
    statement: str,
    duration_ms: float,
    rowcount: int | None,
    errored: bool,
) -> None:
    metric_name = f"query:{statement[:80]}"
    _record_metric(metric_name, duration_ms, errored)

    if errored or duration_ms >= settings.query_slow_log_ms:
        log_structured(
            "siged.query",
            "query_executed",
            level=logging.WARNING if errored else logging.INFO,
            statement=statement,
            duration_ms=round(duration_ms, 2),
            rowcount=rowcount,
            errored=errored,
        )


@contextmanager
def observe_operation(name: str, *, details: dict[str, object] | None = None):
    started_at = perf_counter()
    errored = False

    try:
        yield
    except Exception:
        errored = True
        raise
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        metric_name = f"operation:{name}"
        _record_metric(metric_name, duration_ms, errored)

        if errored or duration_ms >= settings.operation_slow_log_ms:
            log_structured(
                "siged.operation",
                "operation_completed",
                level=logging.WARNING if errored else logging.INFO,
                operation=name,
                duration_ms=round(duration_ms, 2),
                errored=errored,
                details=details,
            )


def audit_event(
    action: str,
    outcome: str,
    *,
    request: Request | None = None,
    actor: str | None = None,
    target: str | None = None,
    details: dict[str, object] | None = None,
) -> None:
    payload: dict[str, object] = {
        "action": action,
        "outcome": outcome,
    }

    request_id = get_request_id(request)
    if request_id:
        payload["request_id"] = request_id

    if actor:
        payload["actor"] = actor

    if target:
        payload["target"] = target

    if request is not None:
        payload["method"] = request.method
        payload["path"] = request.url.path
        payload["client_ip"] = request.client.host if request.client else None

    if details:
        payload["details"] = details

    logging.getLogger("siged.audit").info(
        "audit_event=%s",
        json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str),
    )
