from app.api.routers import estadisticas as estadisticas_router


def test_estadisticas_por_hora_success(client, set_current_user, monkeypatch):
    set_current_user("consulta")
    monkeypatch.setattr(
        estadisticas_router,
        "get_estadisticas_por_hora",
        lambda fecha_inicio, fecha_fin, id_delito, distrito, id_comisaria, region, division, comisaria, jurisdiccion, sector: [{"hora": 8, "total": 12}],
    )

    response = client.get("/estadisticas/por-hora")

    assert response.status_code == 200
    assert response.json() == [{"hora": 8, "total": 12}]


def test_estadisticas_por_dia_semana_success(client, set_current_user, monkeypatch):
    set_current_user("consulta")
    monkeypatch.setattr(
        estadisticas_router,
        "get_estadisticas_por_dia_semana",
        lambda fecha_inicio, fecha_fin, id_delito, distrito, id_comisaria, region, division, comisaria, jurisdiccion, sector: [
            {"dia_semana_numero": 1, "dia_semana": "Lunes", "total": 7}
        ],
    )

    response = client.get("/estadisticas/por-dia-semana")

    assert response.status_code == 200
    assert response.json()[0]["dia_semana"] == "Lunes"
