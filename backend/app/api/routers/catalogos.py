from fastapi import APIRouter, Depends

from app.schemas import ComisariaCatalogo, DelitoCatalogo, DistritoCatalogo
from app.security import require_roles
from app.security_policy import ANALYTICS_ROLES
from app.services.catalogos_service import list_comisarias, list_delitos, list_distritos

router = APIRouter(
    tags=["catalogos"],
    dependencies=[Depends(require_roles(*ANALYTICS_ROLES))],
)


@router.get("/catalogos/delitos", response_model=list[DelitoCatalogo])
def get_catalogo_delitos() -> list[DelitoCatalogo]:
    return list_delitos()


@router.get("/catalogos/comisarias", response_model=list[ComisariaCatalogo])
def get_catalogo_comisarias() -> list[ComisariaCatalogo]:
    return list_comisarias()


@router.get("/catalogos/distritos", response_model=list[DistritoCatalogo])
def get_catalogo_distritos() -> list[DistritoCatalogo]:
    return list_distritos()
