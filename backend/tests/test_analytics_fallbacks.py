from psycopg2 import errors as psycopg_errors

from app.repositories import analisis_repository, recomendaciones_repository


def test_fetch_hotspots_falls_back_to_events_when_persisted_schema_is_incomplete(monkeypatch):
    fallback_rows = [{"id_hotspot": 99}]

    monkeypatch.setattr(
        analisis_repository,
        "get_existing_tables",
        lambda names: {"hotspots", "zonas_operativas"},
    )

    def _raise_incompatible_schema(**kwargs):
        raise psycopg_errors.UndefinedColumn("columna faltante")

    monkeypatch.setattr(analisis_repository, "_fetch_hotspots_from_table", _raise_incompatible_schema)
    monkeypatch.setattr(
        analisis_repository,
        "_fetch_hotspots_from_events",
        lambda **kwargs: fallback_rows,
    )

    result = analisis_repository.fetch_hotspots(
        fecha_inicio=None,
        fecha_fin=None,
        id_delito=None,
        distrito=None,
        id_comisaria=None,
        region=None,
        division=None,
        comisaria=None,
        jurisdiccion=None,
        sector=None,
        estado="ACTIVO",
        limite=12,
    )

    assert result == fallback_rows


def test_fetch_recommendations_fall_back_to_events_when_zone_schema_is_incomplete(monkeypatch):
    fallback_rows = [{"codigo_zona": "DIST-DISTRITO DEMO OESTE"}]

    monkeypatch.setattr(
        recomendaciones_repository,
        "get_existing_tables",
        lambda names: {"zonas_operativas"},
    )

    def _raise_incompatible_schema(**kwargs):
        raise psycopg_errors.UndefinedFunction("funcion faltante")

    monkeypatch.setattr(
        recomendaciones_repository,
        "_fetch_candidates_from_zones",
        _raise_incompatible_schema,
    )
    monkeypatch.setattr(
        recomendaciones_repository,
        "_fetch_candidates_from_events",
        lambda **kwargs: fallback_rows,
    )

    result = recomendaciones_repository.fetch_patrol_recommendation_candidates(
        fecha_inicio=None,
        fecha_fin=None,
        id_delito=None,
        distrito="DISTRITO DEMO OESTE",
        id_comisaria=None,
        region=None,
        division=None,
        comisaria=None,
        jurisdiccion=None,
        sector=None,
        turno=None,
        limite=6,
    )

    assert result == fallback_rows
