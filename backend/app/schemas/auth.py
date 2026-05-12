from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RoleCode = Literal["admin", "analista", "consulta"]
VALID_ROLE_CODES: tuple[RoleCode, ...] = ("admin", "analista", "consulta")


class RoleResponse(BaseModel):
    codigo: RoleCode
    nombre: str
    descripcion: str | None = None


class UserSummary(BaseModel):
    id_usuario: int
    username: str
    nombre_completo: str
    rol_codigo: RoleCode
    activo: bool
    ultimo_login: datetime | None = None
    created_at: datetime


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class BootstrapAdminRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    nombre_completo: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    nombre_completo: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    rol_codigo: RoleCode


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class CurrentUser(BaseModel):
    id_usuario: int
    username: str
    nombre_completo: str
    rol_codigo: RoleCode
    activo: bool
    ultimo_login: datetime | None = None
    created_at: datetime

