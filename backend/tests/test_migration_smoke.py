import os

import pytest

from app.database import get_cursor
from app.repositories.auth_repository import auth_tables_ready
from app.repositories.query_utils import clear_schema_cache, get_existing_tables, table_has_column

REQUIRED_TABLES = {
    "auth_roles",
    "auth_usuarios",
    "dim_territorios",
    "territorio_aliases",
}
REQUIRED_VIEWS = {
    "vw_eventos_territoriales",
    "vw_territorial_inconsistencias",
}


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION_TESTS") != "1",
    reason="requiere RUN_DB_INTEGRATION_TESTS=1 y una base PostgreSQL/PostGIS local",
)


def test_integration_smoke_requires_auth_and_territorial_migrations():
    clear_schema_cache()

    assert auth_tables_ready() is True
    assert get_existing_tables(REQUIRED_TABLES) == REQUIRED_TABLES
    assert table_has_column("eventos_delictivos", "id_territorio_distrito") is True
    assert table_has_column("zonas_operativas", "id_territorio") is True
    assert table_has_column("comisarias", "codigo_cpnp") is True
    assert table_has_column("staging_eventos", "estado_territorial") is True

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
              AND table_name = ANY(%s);
            """,
            (list(REQUIRED_VIEWS),),
        )
        existing_views = {row["table_name"] for row in cur.fetchall()}

    assert existing_views == REQUIRED_VIEWS
