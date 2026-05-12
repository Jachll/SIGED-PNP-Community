from fastapi import APIRouter, Depends, HTTPException, Request

from app.observability import audit_event
from app.schemas import CreateUserRequest, CurrentUser, UserSummary
from app.security import require_roles
from app.security_policy import ADMIN_ROLES
from app.services.auth_service import create_user_service, list_users_service

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)


@router.get("/usuarios", response_model=list[UserSummary])
def get_users() -> list[UserSummary]:
    return list_users_service()


@router.post("/usuarios", response_model=UserSummary, status_code=201)
def create_user(
    payload: CreateUserRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_roles(*ADMIN_ROLES)),
) -> UserSummary:
    target_username = payload.username.strip().lower()

    try:
        user = create_user_service(payload)
    except HTTPException as exc:
        audit_event(
            "admin.user.create",
            "failure",
            request=request,
            actor=current_user.username,
            target=target_username,
            details={"status_code": exc.status_code},
        )
        raise

    audit_event(
        "admin.user.create",
        "success",
        request=request,
        actor=current_user.username,
        target=user.username,
        details={"assigned_role": user.rol_codigo},
    )
    return user
