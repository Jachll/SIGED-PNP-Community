from datetime import datetime

from fastapi import HTTPException

from app.api.routers import cargas as cargas_router


def _lote_resumen() -> dict:
    return {
        "id_lote": 10,
        "nombre_archivo": "lote_demo.csv",
        "estado_lote": "COMPLETADO",
        "total_filas": 5,
        "filas_validas": 5,
        "filas_error": 0,
        "filas_promovidas": 5,
        "fecha_inicio": datetime(2026, 1, 5, 9, 0, 0),
        "fecha_fin": datetime(2026, 1, 5, 9, 5, 0),
    }


def _lote_detalle() -> dict:
    payload = _lote_resumen()
    payload.update(
        {
            "ruta_archivo": "backend/uploads/lote_demo.csv",
            "observaciones": "Carga de prueba",
            "errores": [],
        }
    )
    return payload


def test_get_lotes_success(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(cargas_router, "list_lotes", lambda estado, limite, offset: [_lote_resumen()])

    response = client.get("/cargas/lotes?limite=10&offset=5")

    assert response.status_code == 200
    assert response.json()[0]["id_lote"] == 10


def test_get_lote_detail_propagates_not_found(client, set_current_user, monkeypatch):
    set_current_user("analista")

    def _raise_not_found(id_lote: int):
        raise HTTPException(status_code=404, detail=f"No existe el lote {id_lote}.")

    monkeypatch.setattr(cargas_router, "get_lote", _raise_not_found)

    response = client.get("/cargas/lotes/99")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_create_lote_returns_created(client, set_current_user, monkeypatch):
    set_current_user("analista")
    monkeypatch.setattr(cargas_router, "create_lote_from_upload", lambda archivo, observaciones, sheet: _lote_detalle())

    response = client.post(
        "/cargas/lotes",
        data={"observaciones": "demo"},
        files={
            "archivo": (
                "datos.csv",
                b"fecha,hora,id_delito,distrito,direccion,latitud,longitud,id_comisaria,fuente_registro,descripcion\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["estado_lote"] == "COMPLETADO"
