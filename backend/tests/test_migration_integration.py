import os
from uuid import uuid4

import pytest

from app.database import get_cursor
from app.repositories.auth_repository import auth_tables_ready
from app.repositories.query_utils import clear_schema_cache
from app.security import hash_password


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION_TESTS") != "1",
    reason="requiere RUN_DB_INTEGRATION_TESTS=1 y una base PostgreSQL/PostGIS local",
)


def _create_temp_user(*, role_code: str = "admin") -> tuple[int, str, str]:
    username = f"it_{uuid4().hex[:12]}"
    password = f"Tmp-{uuid4().hex}!"
    password_hash = hash_password(password)

    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO auth_usuarios (
                username,
                nombre_completo,
                password_hash,
                rol_codigo,
                activo
            ) VALUES (%s, %s, %s, %s, TRUE)
            RETURNING id_usuario;
            """,
            (username, "Usuario Integracion", password_hash, role_code),
        )
        user_id = int(cur.fetchone()["id_usuario"])

    return user_id, username, password


def _delete_temp_user(user_id: int) -> None:
    with get_cursor() as cur:
        cur.execute("DELETE FROM auth_usuarios WHERE id_usuario = %s;", (user_id,))


def test_auth_migrations_enable_real_login_and_me_flow(client):
    clear_schema_cache()
    assert auth_tables_ready() is True

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT codigo
            FROM auth_roles
            ORDER BY codigo;
            """
        )
        role_codes = [row["codigo"] for row in cur.fetchall()]

    assert role_codes == ["admin", "analista", "consulta"]

    user_id, username, password = _create_temp_user(role_code="admin")

    try:
        login_response = client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert login_response.status_code == 200

        login_payload = login_response.json()
        assert login_payload["user"]["username"] == username
        assert login_payload["user"]["rol_codigo"] == "admin"
        assert login_payload["access_token"]

        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {login_payload['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["id_usuario"] == user_id
        assert me_response.json()["username"] == username
        assert me_response.json()["rol_codigo"] == "admin"
    finally:
        _delete_temp_user(user_id)


def test_territorial_migrations_keep_real_views_consistent():
    clear_schema_cache()

    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM eventos_delictivos;")
        eventos_total = int(cur.fetchone()["total"])

        cur.execute("SELECT COUNT(*) AS total FROM vw_eventos_territoriales;")
        vista_total = int(cur.fetchone()["total"])

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM vw_eventos_territoriales
            WHERE codigo_distrito IS NULL
               OR BTRIM(codigo_distrito) = ''
               OR distrito IS NULL
               OR BTRIM(distrito) = '';
            """
        )
        eventos_sin_distrito_canonico = int(cur.fetchone()["total"])

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM eventos_delictivos
            WHERE id_comisaria IS NOT NULL
              AND id_territorio_distrito IS NULL;
            """
        )
        eventos_sin_territorio = int(cur.fetchone()["total"])

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM zonas_operativas
            WHERE id_territorio IS NULL
               OR id_territorio_distrito IS NULL;
            """
        )
        zonas_sin_territorio = int(cur.fetchone()["total"])

        cur.execute("SELECT COUNT(*) AS total FROM vw_territorial_inconsistencias;")
        inconsistencias = int(cur.fetchone()["total"])

    assert eventos_total > 0
    assert vista_total == eventos_total
    assert eventos_sin_distrito_canonico == 0
    assert eventos_sin_territorio == 0
    assert zonas_sin_territorio == 0
    assert inconsistencias == 0
