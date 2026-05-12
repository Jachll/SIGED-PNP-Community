from datetime import date, time

from app.repositories import eventos_repository


class _FakeCursor:
    def __init__(self):
        self.executed: list[str] = []
        self.fetchone_responses = [
            {
                "id_evento": 7,
                "fecha": date(2026, 4, 9),
                "hora": time(10, 30),
                "id_delito": 2,
                "nombre_delito": "Hurto",
                "distrito": "DISTRITO DEMO PUERTO",
                "direccion": "Av. Demo 123",
                "latitud": -9.1,
                "longitud": -78.5,
                "id_comisaria": 12,
                "nombre_comisaria": "COMISARIA DEMO 21",
                "fuente_registro": "911",
                "descripcion": "Evento demo",
                "region": "REGION DEMO NORTE",
                "division": "DIVISION DEMO DISTRITO DEMO PUERTO",
                "jurisdiccion": "JURISDICCION DEMO 21",
                "sector": "SECTOR 01",
            },
            {
                "total_eventos_historicos": 4,
                "total_eventos_30_dias": 2,
                "total_eventos_90_dias": 3,
            },
        ]
        self.fetchall_responses = [
            [
                {
                    "id_evento": 8,
                    "fecha": date(2026, 4, 8),
                    "hora": time(9, 15),
                    "nombre_delito": "Hurto",
                    "direccion": "Av. Cercana 456",
                    "nombre_comisaria": "COMISARIA DEMO 21",
                    "distancia_metros": 33,
                }
            ]
        ]

    def execute(self, query, params=None):
        self.executed.append(" ".join(str(query).split()))

    def fetchone(self):
        return self.fetchone_responses.pop(0)

    def fetchall(self):
        return self.fetchall_responses.pop(0)


class _FakeCursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        return False


def test_fetch_evento_detalle_anchors_popup_context_to_latlon(monkeypatch):
    fake_cursor = _FakeCursor()

    monkeypatch.setattr(eventos_repository, "get_existing_tables", lambda table_names: {"zonas_operativas"})
    monkeypatch.setattr(eventos_repository, "table_has_column", lambda table_name, column_name: True)
    monkeypatch.setattr(
        eventos_repository,
        "get_canonical_district_select",
        lambda table_alias, table_name="eventos_delictivos", territory_alias="td": ("", f"{table_alias}.distrito"),
    )
    monkeypatch.setattr(
        eventos_repository,
        "get_cursor",
        lambda: _FakeCursorContext(fake_cursor),
    )

    detail = eventos_repository.fetch_evento_detalle(7, radio_metros=200, limite_relacionados=3)

    assert detail is not None
    assert detail["contexto_lugar"]["total_eventos_historicos"] == 4
    assert detail["contexto_lugar"]["eventos_recientes"][0]["id_evento"] == 8
    assert detail["referencia_territorial"]["jurisdiccion"] == "JURISDICCION DEMO 21"
    assert any("ST_Covers(z.geom, ST_SetSRID(ST_MakePoint(e.longitud, e.latitud), 4326))" in query for query in fake_cursor.executed)
    assert any("ST_MakePoint(e2.longitud, e2.latitud)" in query for query in fake_cursor.executed)
    assert any("eb.anchor_geom" in query for query in fake_cursor.executed)
