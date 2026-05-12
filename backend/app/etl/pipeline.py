from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any

from psycopg2.extras import RealDictCursor

from app.etl.territorial_assignment import (
    apply_territorial_assignment,
    ensure_official_territorial_catalog_ready,
    ensure_region_territorial_catalog_ready,
)
from app.etl.tabular import (
    TabularValidationError,
    build_error_entry,
    read_tabular_source,
    register_row_fingerprint,
    validate_required_columns,
    validate_row,
)
from app.repositories.cargas_repository import (
    create_lote,
    fetch_lote_summary,
    finalize_lote,
    has_event_lote_fk_column,
    insert_staging_row,
    list_valid_staging_rows,
    mark_lote_failed,
    mark_staging_error,
    mark_staging_promoted,
    mark_staging_valid,
    promote_evento,
)
from app.repositories.territorial_repository import refresh_territorial_dimension_if_available

logger = logging.getLogger("siged.etl")


@dataclass(frozen=True)
class LoteImportResult:
    id_lote: int
    nombre_archivo: str
    ruta_archivo: str
    estado_lote: str
    summary: dict[str, int]
    errors: list[dict[str, Any]] = field(default_factory=list)


def import_tabular_file_to_lote(
    conn,
    *,
    managed_path: Path,
    original_filename: str,
    observaciones: str | None = None,
    sheet_name: str | None = None,
) -> LoteImportResult:
    normalized_observaciones = (observaciones or "").strip() or None
    id_lote: int | None = None
    errors: list[dict[str, Any]] = []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            id_lote = create_lote(
                cur,
                nombre_archivo=original_filename or managed_path.name,
                ruta_archivo=str(managed_path),
                observaciones=normalized_observaciones,
            )
        conn.commit()

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            include_lote_fk = has_event_lote_fk_column(cur)
            ensure_official_territorial_catalog_ready(cur)
            fieldnames, row_iterator = read_tabular_source(managed_path, sheet_name=sheet_name)
            validate_required_columns(fieldnames)

            seen_fingerprints: dict[tuple[object, ...], int] = {}
            territorial_regions_ready: set[str] = set()
            promoted_rows = 0

            for line_number, raw_row in row_iterator:
                id_staging = insert_staging_row(cur, id_lote, line_number, raw_row)

                try:
                    clean_row = validate_row(raw_row)
                    clean_row = apply_territorial_assignment(cur, clean_row)
                    if clean_row.get("estado_territorial") == "SIN_COINCIDENCIA_TERRITORIAL":
                        ensure_region_territorial_catalog_ready(
                            cur,
                            latitud=float(clean_row["latitud"]),
                            longitud=float(clean_row["longitud"]),
                            region_cache=territorial_regions_ready,
                        )
                        clean_row = apply_territorial_assignment(cur, clean_row)
                    duplicate_line = register_row_fingerprint(
                        seen_fingerprints,
                        clean_row,
                        line_number,
                    )

                    if duplicate_line is not None:
                        message = (
                            "Fila duplicada dentro del archivo. "
                            f"Coincide con la fila {duplicate_line}."
                        )
                        mark_staging_error(cur, id_staging, "ERROR_DUPLICADO", message)
                        errors.append(
                            build_error_entry(
                                line_number,
                                "ERROR_DUPLICADO",
                                message,
                                raw_row,
                            )
                        )
                        continue

                    mark_staging_valid(cur, id_staging, clean_row)
                except TabularValidationError as exc:
                    error_code = getattr(exc, "code", "ERROR_VALIDACION")
                    trace_payload = getattr(exc, "staging_payload", None) or {
                        "id_comisaria_original": None,
                        "id_comisaria_resuelta": None,
                        "nombre_comisaria_resuelta": None,
                        "estado_territorial": "SIN_COINCIDENCIA_TERRITORIAL",
                        "regla_territorial": "REVISION_MANUAL",
                        "motivo_territorial": (
                            "No se pudo completar la evaluacion territorial por un error "
                            "de validacion del registro."
                        ),
                        "conflicto_territorial": False,
                    }
                    mark_staging_error(
                        cur,
                        id_staging,
                        error_code,
                        str(exc),
                        trace_payload=trace_payload,
                    )
                    errors.append(
                        build_error_entry(
                            line_number,
                            error_code,
                            str(exc),
                            raw_row,
                        )
                    )

            for row in list_valid_staging_rows(cur, id_lote):
                promoted_rows += _promote_validated_row(
                    cur,
                    row=row,
                    id_lote=id_lote,
                    include_lote_fk=include_lote_fk,
                    errors=errors,
                )

            _refresh_territorial_dimension_if_available(cur, promoted_rows=promoted_rows)
            summary = fetch_lote_summary(cur, id_lote)
            estado_lote = get_final_status(summary)
            finalize_lote(cur, id_lote, summary, estado_lote)
        conn.commit()

        return LoteImportResult(
            id_lote=id_lote,
            nombre_archivo=original_filename or managed_path.name,
            ruta_archivo=str(managed_path),
            estado_lote=estado_lote,
            summary=summary,
            errors=errors,
        )
    except TabularValidationError as exc:
        conn.rollback()
        if id_lote is None:
            raise

        errors.append(
            build_error_entry(
                1,
                "ERROR_ARCHIVO",
                str(exc),
                context=managed_path.name,
            )
        )
        return _finalize_failed_lote(
            conn,
            id_lote=id_lote,
            nombre_archivo=original_filename or managed_path.name,
            ruta_archivo=str(managed_path),
            observaciones=normalized_observaciones,
            reason=str(exc),
            errors=errors,
        )
    except Exception:
        logger.exception("Fallo inesperado importando el lote %s", original_filename)
        conn.rollback()
        if id_lote is None:
            raise

        errors.append(
            build_error_entry(
                1,
                "ERROR_PROCESO",
                "Error interno procesando el lote.",
                context=managed_path.name,
            )
        )
        return _finalize_failed_lote(
            conn,
            id_lote=id_lote,
            nombre_archivo=original_filename or managed_path.name,
            ruta_archivo=str(managed_path),
            observaciones=normalized_observaciones,
            reason="Error interno procesando el lote.",
            errors=errors,
        )


def get_final_status(summary: dict[str, int]) -> str:
    if summary["filas_error"] == 0:
        return "COMPLETADO"
    return "COMPLETADO_CON_ERRORES"


def _finalize_failed_lote(
    conn,
    *,
    id_lote: int,
    nombre_archivo: str,
    ruta_archivo: str,
    observaciones: str | None,
    reason: str,
    errors: list[dict[str, Any]],
) -> LoteImportResult:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        mark_lote_failed(cur, id_lote, _merge_observaciones(observaciones, f"Fallo del proceso: {reason}"))
        summary = fetch_lote_summary(cur, id_lote)
    conn.commit()

    return LoteImportResult(
        id_lote=id_lote,
        nombre_archivo=nombre_archivo,
        ruta_archivo=ruta_archivo,
        estado_lote="FALLIDO",
        summary=summary,
        errors=errors,
    )


def _merge_observaciones(base: str | None, extra: str) -> str:
    return f"{base}\n{extra}" if base else extra


def _refresh_territorial_dimension_if_available(cur, *, promoted_rows: int) -> bool:
    if promoted_rows <= 0:
        return False

    if not refresh_territorial_dimension_if_available(cur):
        return False

    logger.info(
        "Dimension territorial refrescada tras lote con %s filas promovidas",
        promoted_rows,
    )
    return True


def _promote_validated_row(
    cur,
    *,
    row: dict[str, Any],
    id_lote: int,
    include_lote_fk: bool,
    errors: list[dict[str, Any]],
) -> int:
    cur.execute("SAVEPOINT siged_promote_evento")

    try:
        id_evento = promote_evento(cur, row, id_lote, include_lote_fk)
        mark_staging_promoted(cur, row["id_staging"], id_evento)
        cur.execute("RELEASE SAVEPOINT siged_promote_evento")
        return 1
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT siged_promote_evento")
        cur.execute("RELEASE SAVEPOINT siged_promote_evento")
        logger.exception(
            "No se pudo promover la fila %s del lote %s",
            row["numero_fila"],
            id_lote,
        )
        message = "No se pudo promover la fila por un error interno."
        mark_staging_error(cur, row["id_staging"], "ERROR_PROMOCION", message)
        errors.append(
            build_error_entry(
                int(row["numero_fila"]),
                "ERROR_PROMOCION",
                message,
                context=f"id_staging={row['id_staging']}",
            )
        )
        return 0
