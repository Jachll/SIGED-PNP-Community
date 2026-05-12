from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.schemas import LoteCargaDetalle, LoteCargaResumen
from app.security import require_roles
from app.security_policy import OPERATIONAL_ROLES
from app.services.cargas_service import create_lote_from_upload, get_lote, list_lotes

router = APIRouter(
    prefix="/cargas",
    tags=["cargas"],
    dependencies=[Depends(require_roles(*OPERATIONAL_ROLES))],
)


@router.get("/lotes", response_model=list[LoteCargaResumen])
def get_lotes(
    estado: str | None = Query(default=None, min_length=3, max_length=30),
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=100000),
) -> list[LoteCargaResumen]:
    return list_lotes(estado=estado, limite=limite, offset=offset)


@router.get("/lotes/{id_lote}", response_model=LoteCargaDetalle)
def get_lote_detail(id_lote: int) -> LoteCargaDetalle:
    return get_lote(id_lote)


@router.post("/lotes", response_model=LoteCargaDetalle, status_code=status.HTTP_201_CREATED)
def create_lote(
    archivo: UploadFile = File(...),
    sheet: str | None = Form(default=None),
    observaciones: str | None = Form(default=None),
) -> LoteCargaDetalle:
    return create_lote_from_upload(archivo=archivo, observaciones=observaciones, sheet=sheet)
