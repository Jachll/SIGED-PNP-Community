import pytest

from app.etl.pipeline import _refresh_territorial_dimension_if_available
from app.etl.tabular import TabularValidationError
from app.etl.territorial_assignment import (
    MIGRATION_HINT,
    TERRITORIAL_STATE_CONFLICT,
    TERRITORIAL_STATE_JURISDICTION,
    TERRITORIAL_STATE_NO_MATCH,
    TERRITORIAL_STATE_SECTOR,
    _iter_region_layer_features,
    apply_territorial_assignment,
    ensure_official_territorial_catalog_ready,
    ensure_region_territorial_catalog_ready,
)
from app.territorial import build_territory_code, normalize_territory_name


def test_normalize_territory_name_collapses_spaces_and_uppercases():
    assert normalize_territory_name("  Distrito   Demo  Largo ") == "DISTRITO DEMO LARGO"


def test_build_territory_code_generates_stable_slug():
    assert build_territory_code("DIST", "Distrito Demo Largo") == "DIST-DISTRITO_DEMO_LARGO"


def test_apply_territorial_assignment_uses_jurisdiction_priority(monkeypatch):
    clean_row = {
        "latitud": -9.08,
        "longitud": -78.58,
        "distrito": "DISTRITO DEMO PUERTO",
        "id_comisaria_original": 12,
        "id_comisaria_original_invalido": False,
    }

    monkeypatch.setattr(
        "app.etl.territorial_assignment.resolve_official_comisaria",
        lambda cur, latitud, longitud, tipo_zona: (
            [
                {
                    "id_comisaria": 12,
                    "nombre_comisaria": "COMISARIA DEMO 21",
                    "distrito": "DISTRITO DEMO PUERTO",
                    "codigo_zona": "JUR-4886-2662",
                    "nombre_zona": "JURISDICCION DEMO 21",
                }
            ]
            if tipo_zona == "JURISDICCION"
            else []
        ),
    )

    result = apply_territorial_assignment(None, clean_row)

    assert result["estado_territorial"] == TERRITORIAL_STATE_JURISDICTION
    assert result["id_comisaria"] == 12
    assert result["id_comisaria_resuelta"] == 12
    assert result["nombre_comisaria_resuelta"] == "COMISARIA DEMO 21"


def test_apply_territorial_assignment_falls_back_to_sector(monkeypatch):
    clean_row = {
        "latitud": -9.13,
        "longitud": -78.52,
        "distrito": "DISTRITO DEMO NUEVO",
        "id_comisaria_original": None,
        "id_comisaria_original_invalido": False,
    }

    monkeypatch.setattr(
        "app.etl.territorial_assignment.resolve_official_comisaria",
        lambda cur, latitud, longitud, tipo_zona: (
            []
            if tipo_zona == "JURISDICCION"
            else [
                {
                    "id_comisaria": 31,
                    "nombre_comisaria": "COMISARIA DEMO SUR",
                    "distrito": "DISTRITO DEMO NUEVO",
                    "codigo_zona": "SEC-310101",
                    "nombre_zona": "SECTOR DEMO SUR 01",
                }
            ]
        ),
    )

    result = apply_territorial_assignment(None, clean_row)

    assert result["estado_territorial"] == TERRITORIAL_STATE_SECTOR
    assert result["id_comisaria"] == 31
    assert result["nombre_comisaria_resuelta"] == "COMISARIA DEMO SUR"


def test_apply_territorial_assignment_marks_no_match(monkeypatch):
    clean_row = {
        "latitud": -9.50,
        "longitud": -78.90,
        "distrito": "DISTRITO DEMO PUERTO",
        "id_comisaria_original": None,
        "id_comisaria_original_invalido": False,
    }

    monkeypatch.setattr(
        "app.etl.territorial_assignment.resolve_official_comisaria",
        lambda cur, latitud, longitud, tipo_zona: [],
    )

    result = apply_territorial_assignment(None, clean_row)

    assert result["estado_territorial"] == TERRITORIAL_STATE_NO_MATCH
    assert result["id_comisaria"] is None
    assert result["regla_territorial"] == "REVISION_MANUAL"


def test_apply_territorial_assignment_marks_conflict_against_geometry(monkeypatch):
    clean_row = {
        "latitud": -9.08,
        "longitud": -78.58,
        "distrito": "DISTRITO DEMO PUERTO",
        "id_comisaria_original": 999,
        "id_comisaria_original_invalido": False,
    }

    monkeypatch.setattr(
        "app.etl.territorial_assignment.resolve_official_comisaria",
        lambda cur, latitud, longitud, tipo_zona: (
            [
                {
                    "id_comisaria": 12,
                    "nombre_comisaria": "COMISARIA DEMO 21",
                    "distrito": "DISTRITO DEMO PUERTO",
                    "codigo_zona": "JUR-4886-2662",
                    "nombre_zona": "JURISDICCION DEMO 21",
                }
            ]
            if tipo_zona == "JURISDICCION"
            else []
        ),
    )

    result = apply_territorial_assignment(None, clean_row)

    assert result["estado_territorial"] == TERRITORIAL_STATE_CONFLICT
    assert result["id_comisaria"] == 12
    assert result["conflicto_territorial"] is True
    assert "Entrante=999" in result["motivo_territorial"]


def test_ensure_official_catalog_requires_migration(monkeypatch):
    monkeypatch.setattr(
        "app.etl.territorial_assignment._territorial_assignment_columns_ready",
        lambda cur: False,
    )

    with pytest.raises(TabularValidationError) as exc_info:
        ensure_official_territorial_catalog_ready(None)

    assert MIGRATION_HINT in str(exc_info.value)


def test_ensure_region_catalog_fails_when_geometry_is_unavailable(monkeypatch):
    statuses = [
        {"total_jurisdicciones": 0, "total_sectores": 0},
        {"total_jurisdicciones": 0, "total_sectores": 0},
    ]

    monkeypatch.setattr(
        "app.etl.territorial_assignment._detect_region_for_point",
        lambda cur, latitud, longitud: "REGION DEMO NORTE",
    )
    monkeypatch.setattr(
        "app.etl.territorial_assignment.fetch_region_catalog_status",
        lambda cur, region: statuses.pop(0),
    )
    monkeypatch.setattr(
        "app.etl.territorial_assignment.sync_region_territorial_catalog",
        lambda cur, region: {
            "comisarias_upserted": 0,
            "jurisdicciones_upserted": 0,
            "sectores_upserted": 0,
        },
    )
    monkeypatch.setattr(
        "app.etl.territorial_assignment.refresh_territorial_dimension_if_available",
        lambda cur: False,
    )

    with pytest.raises(TabularValidationError) as exc_info:
        ensure_region_territorial_catalog_ready(None, latitud=-9.08, longitud=-78.58, region_cache=set())

    assert "catalogo territorial oficial" in str(exc_info.value)


def test_iter_region_layer_features_relaxes_scope_validation_for_internal_sync(monkeypatch):
    captured_calls: list[dict] = []

    def _fake_get_geo_layer_data(layer_id, **kwargs):
        captured_calls.append({"layer_id": layer_id, **kwargs})
        return {"features": [{"type": "Feature", "properties": {"demo": True}}]}

    monkeypatch.setattr(
        "app.etl.territorial_assignment.get_geo_layer_data",
        _fake_get_geo_layer_data,
    )

    features = list(_iter_region_layer_features("jurisdicciones", "REGION DEMO NORTE"))

    assert len(features) == 1
    assert captured_calls[0]["layer_id"] == "jurisdicciones"
    assert captured_calls[0]["region"] == "REGION DEMO NORTE"
    assert captured_calls[0]["detail"] == "full"
    assert captured_calls[0]["enforce_scope"] is False


class _FakeCursor:
    def __init__(self, availability):
        self.availability = availability
        self.executed: list[str] = []

    def execute(self, query, params=None):
        self.executed.append(" ".join(str(query).split()))

    def fetchone(self):
        return self.availability


def test_refresh_territorial_dimension_runs_when_available():
    cur = _FakeCursor({"has_dimension": True, "has_refresh_function": True})

    refreshed = _refresh_territorial_dimension_if_available(cur, promoted_rows=3)

    assert refreshed is True
    assert any("siged_refresh_territorial_dimension" in query for query in cur.executed)


def test_refresh_territorial_dimension_skips_when_not_available():
    cur = _FakeCursor({"has_dimension": False, "has_refresh_function": False})

    refreshed = _refresh_territorial_dimension_if_available(cur, promoted_rows=2)

    assert refreshed is False
    assert len(cur.executed) == 1


def test_refresh_territorial_dimension_skips_without_promoted_rows():
    cur = _FakeCursor({"has_dimension": True, "has_refresh_function": True})

    refreshed = _refresh_territorial_dimension_if_available(cur, promoted_rows=0)

    assert refreshed is False
    assert cur.executed == []
