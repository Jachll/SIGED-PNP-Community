from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.observability import audit_event
from app.schemas import CurrentUser, RecomendacionPatrullajeRequest, RecomendacionPatrullajeResponse
from app.security import require_roles
from app.security_policy import OPERATIONAL_ROLES
from app.services.recomendaciones_service import generate_patrol_recommendations

router = APIRouter(
    tags=["recomendaciones"],
    dependencies=[Depends(require_roles(*OPERATIONAL_ROLES))],
)


@router.get("/recomendaciones/patrullaje", response_model=RecomendacionPatrullajeResponse)
def get_recomendaciones_patrullaje(
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    fecha_operativa: date | None = Query(default=None),
    id_delito: int | None = Query(default=None, ge=1),
    distrito: str | None = Query(default=None, min_length=2, max_length=100),
    id_comisaria: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None, min_length=2, max_length=100),
    division: str | None = Query(default=None, min_length=2, max_length=150),
    comisaria: str | None = Query(default=None, min_length=2, max_length=150),
    jurisdiccion: str | None = Query(default=None, min_length=1, max_length=120),
    sector: str | None = Query(default=None, min_length=1, max_length=120),
    turno: str | None = Query(default=None, min_length=4, max_length=20),
    limite: int = Query(default=20, ge=1, le=100),
) -> RecomendacionPatrullajeResponse:
    return generate_patrol_recommendations(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        fecha_operativa=fecha_operativa,
        id_delito=id_delito,
        distrito=distrito,
        id_comisaria=id_comisaria,
        region=region,
        division=division,
        comisaria=comisaria,
        jurisdiccion=jurisdiccion,
        sector=sector,
        turno=turno,
        limite=limite,
        guardar=False,
    )


@router.post("/recomendaciones/patrullaje/generar", response_model=RecomendacionPatrullajeResponse)
def post_recomendaciones_patrullaje(
    payload: RecomendacionPatrullajeRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_roles(*OPERATIONAL_ROLES)),
) -> RecomendacionPatrullajeResponse:
    try:
        response = generate_patrol_recommendations(
            fecha_inicio=payload.fecha_inicio,
            fecha_fin=payload.fecha_fin,
            fecha_operativa=payload.fecha_operativa,
            id_delito=payload.id_delito,
            distrito=payload.distrito,
            id_comisaria=payload.id_comisaria,
            region=payload.region,
            division=payload.division,
            comisaria=payload.comisaria,
            jurisdiccion=payload.jurisdiccion,
            sector=payload.sector,
            turno=payload.turno,
            limite=payload.limite,
            guardar=payload.guardar,
        )
    except HTTPException as exc:
        if payload.guardar:
            audit_event(
                "recomendaciones.patrullaje.persist",
                "failure",
                request=request,
                actor=current_user.username,
                details={"status_code": exc.status_code},
            )
        raise

    if payload.guardar:
        audit_event(
            "recomendaciones.patrullaje.persist",
            "success",
            request=request,
            actor=current_user.username,
            details={
                "fecha_operativa": response.fecha_operativa,
                "total_recomendaciones": response.total_recomendaciones,
                "turno": payload.turno or "TODOS",
            },
        )

    return response
