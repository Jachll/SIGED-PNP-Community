from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config import settings
from app.observability import audit_event
from app.repositories.auth_repository import auth_tables_ready, fetch_active_user_by_id
from app.schemas.auth import CurrentUser

TOKEN_TYPE = "bearer"
PASSWORD_SCHEME = "pbkdf2_sha256"
bearer_scheme = HTTPBearer(auto_error=False)
WWW_AUTHENTICATE_HEADER = {"WWW-Authenticate": "Bearer"}


def normalize_username(username: str) -> str:
    return username.strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        settings.password_hash_iterations,
    )
    return f"{PASSWORD_SCHEME}${settings.password_hash_iterations}${salt}${derived_key.hex()}"


def verify_password(plain_password: str, stored_password_hash: str) -> bool:
    try:
        scheme, iteration_text, salt, expected_hash = stored_password_hash.split("$", maxsplit=3)
        iterations = int(iteration_text)
        salt_bytes = bytes.fromhex(salt)
    except ValueError:
        return False

    if scheme != PASSWORD_SCHEME:
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt_bytes,
        iterations,
    )
    return hmac.compare_digest(derived_key.hex(), expected_hash)


def create_access_token(user_id: int, username: str, role_code: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role_code,
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado.",
            headers=WWW_AUTHENTICATE_HEADER,
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
            headers=WWW_AUTHENTICATE_HEADER,
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un Bearer token.",
            headers=WWW_AUTHENTICATE_HEADER,
        )

    if credentials.scheme.lower() != TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El esquema de autenticacion debe ser Bearer.",
            headers=WWW_AUTHENTICATE_HEADER,
        )

    if not auth_tables_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Las tablas de autenticacion no estan disponibles. "
                "Ejecuta la migracion 11_auth_minima.sql en la base activa."
            ),
        )

    payload = decode_access_token(credentials.credentials)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
            headers=WWW_AUTHENTICATE_HEADER,
        ) from exc

    user = fetch_active_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no valido o inactivo.",
            headers=WWW_AUTHENTICATE_HEADER,
        )

    return CurrentUser(**user)


def require_roles(*allowed_roles: str):
    normalized_roles = {role.strip().lower() for role in allowed_roles if role and role.strip()}
    if not normalized_roles:
        raise ValueError("require_roles necesita al menos un rol permitido.")

    def dependency(
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.rol_codigo not in normalized_roles:
            audit_event(
                "authz.denied",
                "failure",
                request=request,
                actor=current_user.username,
                details={
                    "current_role": current_user.rol_codigo,
                    "allowed_roles": sorted(normalized_roles),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este recurso.",
            )
        return current_user

    return dependency
