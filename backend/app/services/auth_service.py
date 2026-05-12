from fastapi import HTTPException, status

from app.config import settings
from app.repositories.auth_repository import (
    auth_tables_ready,
    count_users,
    create_user,
    fetch_role,
    fetch_roles,
    fetch_user_by_username,
    fetch_users,
    update_last_login,
)
from app.schemas.auth import (
    BootstrapAdminRequest,
    CreateUserRequest,
    RoleResponse,
    TokenResponse,
    UserSummary,
)
from app.security import create_access_token, hash_password, normalize_username, verify_password


def ensure_auth_storage_ready() -> None:
    if not auth_tables_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El subsistema de autenticacion no esta disponible en este entorno. "
                "Ejecuta la migracion 11_auth_minima.sql en la base activa."
            ),
        )


def list_roles() -> list[RoleResponse]:
    ensure_auth_storage_ready()
    rows = fetch_roles()
    return [RoleResponse(**row) for row in rows]


def list_users_service() -> list[UserSummary]:
    ensure_auth_storage_ready()
    rows = fetch_users()
    return [UserSummary(**row) for row in rows]


def bootstrap_admin(payload: BootstrapAdminRequest) -> TokenResponse:
    ensure_auth_storage_ready()

    if not settings.allow_bootstrap_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El bootstrap administrativo esta deshabilitado. "
                "Habilita ALLOW_BOOTSTRAP_ADMIN solo durante la provision inicial."
            ),
        )

    if count_users() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario administrador inicial ya fue creado.",
        )

    user = _create_user_record(
        username=payload.username,
        nombre_completo=payload.nombre_completo,
        password=payload.password,
        rol_codigo="admin",
    )
    return _build_token_response(user)


def authenticate_user(username: str, password: str) -> TokenResponse:
    ensure_auth_storage_ready()

    normalized_username = normalize_username(username)
    user = fetch_user_by_username(normalized_username)

    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
        )

    if not user["activo"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario esta inactivo.",
        )

    update_last_login(int(user["id_usuario"]))
    fresh_user = fetch_user_by_username(normalized_username)
    return _build_token_response(fresh_user)


def create_user_service(payload: CreateUserRequest) -> UserSummary:
    ensure_auth_storage_ready()
    return UserSummary(
        **_create_user_record(
            username=payload.username,
            nombre_completo=payload.nombre_completo,
            password=payload.password,
            rol_codigo=payload.rol_codigo,
        )
    )


def _create_user_record(
    username: str,
    nombre_completo: str,
    password: str,
    rol_codigo: str,
) -> dict:
    normalized_username = normalize_username(username)

    if fetch_user_by_username(normalized_username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El username '{normalized_username}' ya existe.",
        )

    if not fetch_role(rol_codigo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El rol '{rol_codigo}' no existe.",
        )

    password_hash = hash_password(password)
    return create_user(
        username=normalized_username,
        nombre_completo=nombre_completo.strip(),
        password_hash=password_hash,
        rol_codigo=rol_codigo,
    )


def _build_token_response(user: dict) -> TokenResponse:
    user_summary = UserSummary(**user)
    token = create_access_token(
        user_id=user_summary.id_usuario,
        username=user_summary.username,
        role_code=user_summary.rol_codigo,
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_summary,
    )
