from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.observability import audit_event
from app.schemas import (
    BootstrapAdminRequest,
    CurrentUser,
    LoginRequest,
    RoleResponse,
    TokenResponse,
)
from app.security import get_current_user, require_roles
from app.security_policy import ANALYTICS_ROLES
from app.services.auth_service import authenticate_user, bootstrap_admin, list_roles

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/bootstrap-admin",
    response_model=TokenResponse,
    include_in_schema=settings.allow_bootstrap_admin,
)
def create_initial_admin(payload: BootstrapAdminRequest, request: Request) -> TokenResponse:
    username = payload.username.strip().lower()

    try:
        response = bootstrap_admin(payload)
    except HTTPException as exc:
        audit_event(
            "auth.bootstrap_admin",
            "failure",
            request=request,
            actor=username,
            target=username,
            details={"status_code": exc.status_code},
        )
        raise

    audit_event(
        "auth.bootstrap_admin",
        "success",
        request=request,
        actor=response.user.username,
        target=response.user.username,
        details={"role": response.user.rol_codigo},
    )
    return response


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request) -> TokenResponse:
    username = payload.username.strip().lower()

    try:
        response = authenticate_user(payload.username, payload.password)
    except HTTPException as exc:
        audit_event(
            "auth.login",
            "failure",
            request=request,
            actor=username,
            target=username,
            details={"status_code": exc.status_code},
        )
        raise

    audit_event(
        "auth.login",
        "success",
        request=request,
        actor=response.user.username,
        target=response.user.username,
        details={"role": response.user.rol_codigo},
    )
    return response


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user


@router.get("/roles", response_model=list[RoleResponse])
def get_roles(
    _current_user: CurrentUser = Depends(require_roles(*ANALYTICS_ROLES)),
) -> list[RoleResponse]:
    return list_roles()
