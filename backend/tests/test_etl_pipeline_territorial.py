from pathlib import Path

from app.etl.pipeline import import_tabular_file_to_lote
from app.etl.tabular import validate_required_columns


class _FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def cursor(self, cursor_factory=None):
        return _FakeCursor()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_import_pipeline_handles_mixed_batch_with_territorial_states(monkeypatch):
    valid_rows: list[dict] = []
    staging_errors: list[dict] = []

    mixed_rows = [
        (
            2,
            {
                "fecha": "2026-03-01",
                "hora": "17:40",
                "id_delito": "4",
                "distrito": "DISTRITO DEMO PUERTO",
                "direccion": "Fila valida",
                "latitud": "-9.088735",
                "longitud": "-78.579524",
                "fuente_registro": "Operacion policial",
                "descripcion": "Caso valido",
            },
        ),
        (
            3,
            {
                "fecha": "2026-03-01",
                "hora": "22:45",
                "id_delito": "4",
                "distrito": "DISTRITO DEMO NUEVO",
                "direccion": "Fila invalida",
                "latitud": "",
                "longitud": "-78.520418",
                "fuente_registro": "Operacion policial",
                "descripcion": "Caso invalido",
            },
        ),
        (
            4,
            {
                "fecha": "2026-03-03",
                "hora": "20:20",
                "id_delito": "6",
                "distrito": "DISTRITO DEMO PUERTO",
                "direccion": "Fila conflicto",
                "latitud": "-9.081566",
                "longitud": "-78.606620",
                "id_comisaria": "999",
                "fuente_registro": "Denuncia ciudadana",
                "descripcion": "Caso conflicto",
            },
        ),
    ]

    monkeypatch.setattr("app.etl.pipeline.create_lote", lambda cur, nombre_archivo, ruta_archivo, observaciones: 91)
    monkeypatch.setattr("app.etl.pipeline.has_event_lote_fk_column", lambda cur: False)
    monkeypatch.setattr("app.etl.pipeline.ensure_official_territorial_catalog_ready", lambda cur: None)
    monkeypatch.setattr(
        "app.etl.pipeline.read_tabular_source",
        lambda managed_path, sheet_name=None: (
            [
                "fecha",
                "hora",
                "id_delito",
                "distrito",
                "direccion",
                "latitud",
                "longitud",
                "id_comisaria",
                "fuente_registro",
                "descripcion",
            ],
            iter(mixed_rows),
        ),
    )
    monkeypatch.setattr("app.etl.pipeline.validate_required_columns", validate_required_columns)
    monkeypatch.setattr("app.etl.pipeline.insert_staging_row", lambda cur, id_lote, line_number, raw_row: line_number)

    def _apply_assignment(cur, clean_row):
        if clean_row["direccion"] == "Fila conflicto":
            clean_row["id_comisaria"] = 33
            clean_row["id_comisaria_resuelta"] = 33
            clean_row["nombre_comisaria_resuelta"] = "COMISARIA DEMO 21"
            clean_row["estado_territorial"] = "CONFLICTO_ID_COMISARIA_VS_GEOMETRIA"
            clean_row["regla_territorial"] = "JURISDICCION_OFICIAL"
            clean_row["motivo_territorial"] = "Entrante=999, resuelto=33."
            clean_row["conflicto_territorial"] = True
            return clean_row

        clean_row["id_comisaria"] = 33
        clean_row["id_comisaria_resuelta"] = 33
        clean_row["nombre_comisaria_resuelta"] = "COMISARIA DEMO 21"
        clean_row["estado_territorial"] = "ASIGNADO_POR_JURISDICCION"
        clean_row["regla_territorial"] = "JURISDICCION_OFICIAL"
        clean_row["motivo_territorial"] = "Asignacion automatica por jurisdiccion oficial."
        clean_row["conflicto_territorial"] = False
        return clean_row

    monkeypatch.setattr("app.etl.pipeline.apply_territorial_assignment", _apply_assignment)

    def _mark_valid(cur, id_staging, clean_row):
        valid_rows.append({**clean_row, "id_staging": id_staging, "numero_fila": id_staging})

    monkeypatch.setattr("app.etl.pipeline.mark_staging_valid", _mark_valid)
    monkeypatch.setattr(
        "app.etl.pipeline.mark_staging_error",
        lambda cur, id_staging, estado_registro, mensaje_error, trace_payload=None: staging_errors.append(
            {
                "id_staging": id_staging,
                "estado_registro": estado_registro,
                "mensaje_error": mensaje_error,
                "trace_payload": trace_payload or {},
            }
        ),
    )
    monkeypatch.setattr("app.etl.pipeline.list_valid_staging_rows", lambda cur, id_lote: list(valid_rows))
    monkeypatch.setattr("app.etl.pipeline._promote_validated_row", lambda cur, row, id_lote, include_lote_fk, errors: 1)
    monkeypatch.setattr(
        "app.etl.pipeline.fetch_lote_summary",
        lambda cur, id_lote: {
            "total_filas": 3,
            "filas_validas": 2,
            "filas_error": 1,
            "filas_promovidas": 2,
        },
    )
    monkeypatch.setattr("app.etl.pipeline.finalize_lote", lambda cur, id_lote, summary, estado_lote: None)
    monkeypatch.setattr("app.etl.pipeline._refresh_territorial_dimension_if_available", lambda cur, promoted_rows: False)

    result = import_tabular_file_to_lote(
        _FakeConnection(),
        managed_path=Path("demo.csv"),
        original_filename="demo.csv",
        observaciones="prueba",
    )

    assert result.summary["total_filas"] == 3
    assert result.summary["filas_validas"] == 2
    assert result.summary["filas_error"] == 1
    assert result.summary["filas_promovidas"] == 2
    assert len(valid_rows) == 2
    assert valid_rows[0]["estado_territorial"] == "ASIGNADO_POR_JURISDICCION"
    assert valid_rows[1]["estado_territorial"] == "CONFLICTO_ID_COMISARIA_VS_GEOMETRIA"
    assert staging_errors[0]["trace_payload"]["estado_territorial"] == "COORDENADAS_INCOMPLETAS"
