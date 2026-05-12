from pathlib import Path

import pytest
from openpyxl import Workbook

from app.etl.tabular import (
    TabularValidationError,
    read_tabular_source,
    register_row_fingerprint,
    validate_required_columns,
    validate_row,
)


def test_validate_row_normalizes_values():
    clean_row = validate_row(
        {
            "fecha": "2026-01-01",
            "hora": "08:30",
            "id_delito": "2",
            "distrito": " distrito demo ",
            "direccion": " Av. Demo 123 ",
                "latitud": "0.0101",
                "longitud": "-0.0101",
            "id_comisaria": "5",
            "fuente_registro": " 911 ",
            "descripcion": " Hecho demo ",
        }
    )

    assert clean_row["distrito"] == "DISTRITO DEMO"
    assert clean_row["id_delito"] == 2
    assert clean_row["id_comisaria"] is None
    assert clean_row["id_comisaria_original"] == 5


def test_validate_row_accepts_missing_id_comisaria_column():
    clean_row = validate_row(
        {
            "fecha": "2026-01-01",
            "hora": "08:30",
            "id_delito": "2",
            "distrito": " lima ",
            "direccion": " Av. Demo 123 ",
            "latitud": "-12.04",
            "longitud": "-77.03",
            "fuente_registro": " 911 ",
            "descripcion": " Hecho demo ",
        }
    )

    assert clean_row["id_comisaria_original"] is None
    assert clean_row["id_comisaria"] is None


def test_validate_required_columns_detects_missing_columns():
    with pytest.raises(TabularValidationError):
        validate_required_columns(["fecha", "hora"])


def test_read_tabular_source_csv(tmp_path):
    csv_path = tmp_path / "demo.csv"
    csv_path.write_text(
        "fecha,hora,id_delito,distrito,direccion,latitud,longitud,fuente_registro,descripcion\n"
        "2026-01-01,08:30,2,DISTRITO DEMO,Av Demo,0.0101,-0.0101,911,Hecho demo\n",
        encoding="utf-8",
    )

    fieldnames, iterator = read_tabular_source(csv_path)
    rows = list(iterator)

    assert "descripcion" in fieldnames
    assert rows[0][0] == 2
    assert rows[0][1]["distrito"] == "DISTRITO DEMO"


def test_read_tabular_source_xlsx(tmp_path):
    xlsx_path = tmp_path / "demo.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(
        [
            "fecha",
            "hora",
            "id_delito",
            "distrito",
            "direccion",
            "latitud",
            "longitud",
            "fuente_registro",
            "descripcion",
        ]
    )
    worksheet.append(["2026-01-01", "08:30", 2, "DISTRITO DEMO", "Av Demo", 0.0101, -0.0101, "911", "Hecho"])
    workbook.save(xlsx_path)

    fieldnames, iterator = read_tabular_source(xlsx_path)
    rows = list(iterator)

    assert fieldnames[0] == "fecha"
    assert rows[0][1]["id_delito"] == "2"


def test_register_row_fingerprint_detects_duplicates():
    clean_row = validate_row(
        {
            "fecha": "2026-01-01",
            "hora": "08:30",
            "id_delito": "2",
            "distrito": "REGION DEMO",
            "direccion": "Av Demo",
            "latitud": "-12.04",
            "longitud": "-77.03",
            "id_comisaria": "5",
            "fuente_registro": "911",
            "descripcion": "Hecho demo",
        }
    )
    seen_rows: dict[tuple[object, ...], int] = {}

    assert register_row_fingerprint(seen_rows, clean_row, 2) is None
    assert register_row_fingerprint(seen_rows, clean_row, 8) == 2


def test_validate_row_marks_incomplete_coordinates():
    with pytest.raises(TabularValidationError) as exc_info:
        validate_row(
            {
                "fecha": "2026-01-01",
                "hora": "08:30",
                "id_delito": "2",
                "distrito": "REGION DEMO",
                "direccion": "Av Demo",
                "latitud": "",
                "longitud": "-77.03",
                "fuente_registro": "911",
                "descripcion": "Hecho demo",
            }
        )

    assert exc_info.value.staging_payload["estado_territorial"] == "COORDENADAS_INCOMPLETAS"


def test_validate_row_marks_invalid_coordinates():
    with pytest.raises(TabularValidationError) as exc_info:
        validate_row(
            {
                "fecha": "2026-01-01",
                "hora": "08:30",
                "id_delito": "2",
                "distrito": "REGION DEMO",
                "direccion": "Av Demo",
                "latitud": "abc",
                "longitud": "-77.03",
                "fuente_registro": "911",
                "descripcion": "Hecho demo",
            }
        )

    assert exc_info.value.staging_payload["estado_territorial"] == "COORDENADAS_INVALIDAS"


def test_validate_row_marks_out_of_range_coordinates():
    with pytest.raises(TabularValidationError) as exc_info:
        validate_row(
            {
                "fecha": "2026-01-01",
                "hora": "08:30",
                "id_delito": "2",
                "distrito": "REGION DEMO",
                "direccion": "Av Demo",
                "latitud": "91",
                "longitud": "-77.03",
                "fuente_registro": "911",
                "descripcion": "Hecho demo",
            }
        )

    assert exc_info.value.staging_payload["estado_territorial"] == "COORDENADAS_INVALIDAS"
