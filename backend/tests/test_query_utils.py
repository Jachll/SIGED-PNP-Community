from app.repositories import query_utils


def test_append_geo_scope_filter_conditions_uses_latlon_point_when_available(monkeypatch):
    conditions = []
    params = []

    monkeypatch.setattr(
        query_utils,
        "_get_scope_geometries",
        lambda **kwargs: [{"type": "Point", "coordinates": [-77.0, -12.0]}],
    )
    monkeypatch.setattr(
        query_utils,
        "table_has_column",
        lambda table_name, column_name: column_name in {"latitud", "longitud"},
    )

    query_utils.append_geo_scope_filter_conditions(
        conditions,
        params,
        region="REGION DEMO CENTRO",
        division=None,
        comisaria=None,
        jurisdiccion=None,
        sector=None,
        table_alias="e",
        table_name="eventos_delictivos",
    )

    assert "ST_SetSRID(ST_MakePoint(e.longitud, e.latitud), 4326)" in conditions[0]
    assert len(params) == 1


def test_append_geo_scope_filter_conditions_falls_back_to_geom_when_latlon_is_unavailable(monkeypatch):
    conditions = []
    params = []

    monkeypatch.setattr(
        query_utils,
        "_get_scope_geometries",
        lambda **kwargs: [{"type": "Polygon", "coordinates": []}],
    )
    monkeypatch.setattr(
        query_utils,
        "table_has_column",
        lambda table_name, column_name: False,
    )

    query_utils.append_geo_scope_filter_conditions(
        conditions,
        params,
        region="REGION DEMO CENTRO",
        division=None,
        comisaria=None,
        jurisdiccion=None,
        sector=None,
        table_alias="e",
        table_name="tabla_sin_latlon",
    )

    assert "ST_Intersects(e.geom" in conditions[0]
    assert len(params) == 1
