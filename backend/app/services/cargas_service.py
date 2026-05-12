import logging

from fastapi import HTTPException, UploadFile, status

from app.database import create_connection
from app.etl import TabularValidationError, import_tabular_file_to_lote, store_upload_file
from app.observability import observe_operation
from app.repositories.cargas_repository import (
    cargas_tables_ready,
    fetch_lote_by_id,
    fetch_lote_errors,
    fetch_lotes,
)
from app.repositories.territorial_repository import territorial_assignment_columns_ready
from app.schemas.cargas import LoteCargaDetalle, LoteCargaError, LoteCargaResumen

logger = logging.getLogger("siged.cargas")


def ensure_cargas_storage_ready() -> None:
    if not cargas_tables_ready() or not territorial_assignment_columns_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El subsistema de cargas no esta disponible en este entorno. "
                "Ejecuta las migraciones 06_lotes_staging.sql, 07_eventos_lote_fk.sql "
                "y 15_etl_asignacion_territorial.sql en la base activa."
            ),
        )


def list_lotes(estado: str | None, limite: int, offset: int) -> list[LoteCargaResumen]:
    ensure_cargas_storage_ready()
    with observe_operation(
        "cargas.listar_lotes",
        details={"estado": estado, "limite": limite, "offset": offset},
    ):
        rows = fetch_lotes(
            estado=estado.strip().upper() if estado else None,
            limite=limite,
            offset=offset,
        )
        return [LoteCargaResumen(**row) for row in rows]


def get_lote(id_lote: int) -> LoteCargaDetalle:
    ensure_cargas_storage_ready()
    with observe_operation("cargas.obtener_lote", details={"id_lote": id_lote}):
        row = fetch_lote_by_id(id_lote)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe el lote {id_lote}.",
            )

        errores = [_build_lote_error(item) for item in fetch_lote_errors(id_lote)]
        return LoteCargaDetalle(**row, errores=errores)


def create_lote_from_upload(
    archivo: UploadFile,
    observaciones: str | None = None,
    sheet: str | None = None,
) -> LoteCargaDetalle:
    ensure_cargas_storage_ready()

    conn = None
    try:
        with observe_operation(
            "cargas.crear_lote",
            details={"archivo": archivo.filename, "sheet": sheet},
        ):
            managed_path = store_upload_file(archivo)
            conn = create_connection()
            result = import_tabular_file_to_lote(
                conn,
                managed_path=managed_path,
                original_filename=archivo.filename or managed_path.name,
                observaciones=observaciones,
                sheet_name=sheet,
            )
    except TabularValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error interno procesando el lote %s", archivo.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo procesar el lote de carga.",
        ) from exc
    finally:
        if conn is not None:
            conn.close()
        archivo.file.close()

    return get_lote(result.id_lote)


def _build_lote_error(row: dict) -> LoteCargaError:
    return LoteCargaError(
        id_staging=int(row["id_staging"]),
        numero_fila=int(row["numero_fila"]),
        estado_registro=str(row["estado_registro"]),
        mensaje_error=str(row["mensaje_error"]) if row.get("mensaje_error") is not None else None,
        estado_territorial=str(row["estado_territorial"]) if row.get("estado_territorial") is not None else None,
        regla_territorial=str(row["regla_territorial"]) if row.get("regla_territorial") is not None else None,
        motivo_territorial=str(row["motivo_territorial"]) if row.get("motivo_territorial") is not None else None,
        conflicto_territorial=bool(row.get("conflicto_territorial") or False),
        id_comisaria_original=(
            int(row["id_comisaria_original"]) if row.get("id_comisaria_original") is not None else None
        ),
        id_comisaria_resuelta=(
            int(row["id_comisaria_resuelta"]) if row.get("id_comisaria_resuelta") is not None else None
        ),
        nombre_comisaria_resuelta=(
            str(row["nombre_comisaria_resuelta"])
            if row.get("nombre_comisaria_resuelta") is not None
            else None
        ),
        valores={
            "fecha": row.get("fecha_raw"),
            "hora": row.get("hora_raw"),
            "id_delito": row.get("id_delito_raw"),
            "distrito": row.get("distrito_raw"),
            "direccion": row.get("direccion_raw"),
            "latitud": row.get("latitud_raw"),
            "longitud": row.get("longitud_raw"),
            "id_comisaria": row.get("id_comisaria_raw"),
            "fuente_registro": row.get("fuente_registro_raw"),
            "descripcion": row.get("descripcion_raw"),
        },
    )
