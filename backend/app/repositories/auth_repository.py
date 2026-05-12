from typing import Any

from app.database import get_cursor
from app.repositories.query_utils import get_existing_tables

AUTH_TABLE_NAMES = ("auth_roles", "auth_usuarios")


def auth_tables_ready() -> bool:
    return set(AUTH_TABLE_NAMES).issubset(get_existing_tables(AUTH_TABLE_NAMES))


def count_users() -> int:
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM auth_usuarios;")
        row = cur.fetchone()
        return int(row["total"])


def fetch_roles() -> list[dict[str, Any]]:
    query = """
        SELECT
            codigo,
            nombre,
            descripcion
        FROM auth_roles
        ORDER BY codigo;
    """

    with get_cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def fetch_role(codigo: str) -> dict[str, Any] | None:
    query = """
        SELECT
            codigo,
            nombre,
            descripcion
        FROM auth_roles
        WHERE codigo = %s;
    """

    with get_cursor() as cur:
        cur.execute(query, (codigo,))
        return cur.fetchone()


def fetch_user_by_username(username: str) -> dict[str, Any] | None:
    query = """
        SELECT
            id_usuario,
            username,
            nombre_completo,
            password_hash,
            rol_codigo,
            activo,
            ultimo_login,
            created_at
        FROM auth_usuarios
        WHERE LOWER(username) = LOWER(%s)
        LIMIT 1;
    """

    with get_cursor() as cur:
        cur.execute(query, (username,))
        return cur.fetchone()


def fetch_user_by_id(user_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            id_usuario,
            username,
            nombre_completo,
            password_hash,
            rol_codigo,
            activo,
            ultimo_login,
            created_at
        FROM auth_usuarios
        WHERE id_usuario = %s
        LIMIT 1;
    """

    with get_cursor() as cur:
        cur.execute(query, (user_id,))
        return cur.fetchone()


def fetch_active_user_by_id(user_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            id_usuario,
            username,
            nombre_completo,
            password_hash,
            rol_codigo,
            activo,
            ultimo_login,
            created_at
        FROM auth_usuarios
        WHERE id_usuario = %s
          AND activo = TRUE
        LIMIT 1;
    """

    with get_cursor() as cur:
        cur.execute(query, (user_id,))
        return cur.fetchone()


def fetch_users() -> list[dict[str, Any]]:
    query = """
        SELECT
            id_usuario,
            username,
            nombre_completo,
            rol_codigo,
            activo,
            ultimo_login,
            created_at
        FROM auth_usuarios
        ORDER BY username;
    """

    with get_cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def create_user(
    username: str,
    nombre_completo: str,
    password_hash: str,
    rol_codigo: str,
) -> dict[str, Any]:
    query = """
        INSERT INTO auth_usuarios (
            username,
            nombre_completo,
            password_hash,
            rol_codigo
        ) VALUES (%s, %s, %s, %s)
        RETURNING
            id_usuario,
            username,
            nombre_completo,
            rol_codigo,
            activo,
            ultimo_login,
            created_at;
    """

    with get_cursor() as cur:
        cur.execute(query, (username, nombre_completo, password_hash, rol_codigo))
        return cur.fetchone()


def update_last_login(user_id: int) -> None:
    query = """
        UPDATE auth_usuarios
        SET
            ultimo_login = NOW(),
            updated_at = NOW()
        WHERE id_usuario = %s;
    """

    with get_cursor() as cur:
        cur.execute(query, (user_id,))
