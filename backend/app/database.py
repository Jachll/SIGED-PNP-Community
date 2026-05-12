# archivo: backend/app/database.py
from contextlib import contextmanager
import logging
from threading import Lock
from time import perf_counter

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from app.config import settings
from app.observability import log_structured, observe_query

logger = logging.getLogger("siged.database")

_pool_lock = Lock()
_connection_pool: ThreadedConnectionPool | None = None


def _build_connection_options() -> str:
    return " ".join(
        [
            f"-c statement_timeout={max(settings.db_statement_timeout_ms, 1000)}",
            f"-c lock_timeout={max(settings.db_lock_timeout_ms, 500)}",
            "-c timezone=UTC",
            (
                "-c idle_in_transaction_session_timeout="
                f"{max(settings.db_idle_in_transaction_timeout_ms, 1000)}"
            ),
        ]
    )


def _build_connection_kwargs() -> dict[str, object]:
    return {
        "host": settings.db_host,
        "port": settings.db_port,
        "dbname": settings.db_name,
        "user": settings.db_user,
        "password": settings.db_password,
        "connect_timeout": max(settings.db_connect_timeout_seconds, 1),
        "application_name": settings.db_application_name,
        "options": _build_connection_options(),
    }


def _configure_connection(
    conn: psycopg2.extensions.connection,
    *,
    autocommit: bool,
) -> psycopg2.extensions.connection:
    conn.autocommit = autocommit
    return conn


def _summarize_query(query: object) -> str:
    normalized = " ".join(str(query).split())
    return normalized[:180] or "SQL"


def _pool_snapshot(pool: ThreadedConnectionPool) -> dict[str, int | None]:
    available = len(getattr(pool, "_pool", []) or [])
    in_use = len(getattr(pool, "_used", {}) or {})
    max_size = getattr(pool, "maxconn", None)
    if max_size is None:
        max_size = getattr(pool, "_maxconn", None)

    return {
        "pool_available": available,
        "pool_in_use": in_use,
        "pool_max": int(max_size) if isinstance(max_size, int) else None,
    }


class ObservedRealDictCursor(RealDictCursor):
    def execute(self, query, vars=None):
        started_at = perf_counter()
        errored = False

        try:
            return super().execute(query, vars)
        except Exception:
            errored = True
            raise
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            observe_query(
                statement=_summarize_query(query),
                duration_ms=duration_ms,
                rowcount=self.rowcount,
                errored=errored,
            )


def _get_connection_pool() -> ThreadedConnectionPool:
    global _connection_pool

    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                min_size = max(settings.db_pool_min_size, 1)
                max_size = max(settings.db_pool_max_size, min_size)
                _connection_pool = ThreadedConnectionPool(
                    minconn=min_size,
                    maxconn=max_size,
                    **_build_connection_kwargs(),
                )
                logger.info(
                    "Pool PostgreSQL inicializado min=%s max=%s",
                    min_size,
                    max_size,
                )

    return _connection_pool


def create_connection(*, autocommit: bool = False) -> psycopg2.extensions.connection:
    conn = psycopg2.connect(**_build_connection_kwargs())
    return _configure_connection(conn, autocommit=autocommit)


@contextmanager
def get_connection(*, autocommit: bool = False):
    pool = _get_connection_pool()
    try:
        conn = pool.getconn()
    except Exception as exc:
        log_structured(
            "siged.database",
            "pool_connection_acquire_failed",
            level=logging.ERROR,
            autocommit=autocommit,
            error_type=type(exc).__name__,
            **_pool_snapshot(pool),
        )
        raise

    log_structured(
        "siged.database",
        "pool_connection_acquired",
        autocommit=autocommit,
        connection_id=id(conn),
        **_pool_snapshot(pool),
    )

    try:
        yield _configure_connection(conn, autocommit=autocommit)
    finally:
        try:
            conn.autocommit = False
        finally:
            pool.putconn(conn)
            log_structured(
                "siged.database",
                "pool_connection_released",
                autocommit=autocommit,
                connection_id=id(conn),
                **_pool_snapshot(pool),
            )


@contextmanager
def get_cursor(*, autocommit: bool = False):
    with get_connection(autocommit=autocommit) as conn:
        try:
            with conn.cursor(cursor_factory=ObservedRealDictCursor) as cur:
                yield cur
            if not autocommit:
                conn.commit()
        except Exception:
            if not autocommit:
                conn.rollback()
            raise


def close_connection_pool() -> None:
    global _connection_pool

    if _connection_pool is not None:
        with _pool_lock:
            if _connection_pool is not None:
                _connection_pool.closeall()
                _connection_pool = None
                logger.info("Pool PostgreSQL cerrado")
