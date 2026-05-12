from app.observability import observe_operation
from app.repositories.catalogos_repository import fetch_comisarias, fetch_delitos, fetch_distritos
from app.schemas import ComisariaCatalogo, DelitoCatalogo, DistritoCatalogo
from app.services.common_service import raise_query_error


def list_delitos() -> list[DelitoCatalogo]:
    try:
        with observe_operation("catalogos.delitos"):
            rows = fetch_delitos()
            return [DelitoCatalogo(**row) for row in rows]
    except Exception as exc:
        raise_query_error("catalogo de delitos", exc)


def list_comisarias() -> list[ComisariaCatalogo]:
    try:
        with observe_operation("catalogos.comisarias"):
            rows = fetch_comisarias()
            return [ComisariaCatalogo(**row) for row in rows]
    except Exception as exc:
        raise_query_error("catalogo de comisarias", exc)


def list_distritos() -> list[DistritoCatalogo]:
    try:
        with observe_operation("catalogos.distritos"):
            rows = fetch_distritos()
            return [DistritoCatalogo(**row) for row in rows]
    except Exception as exc:
        raise_query_error("catalogo de distritos", exc)
