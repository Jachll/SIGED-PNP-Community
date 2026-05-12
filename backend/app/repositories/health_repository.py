from app.database import get_cursor


def fetch_postgis_version() -> str | None:
    with get_cursor() as cur:
        cur.execute("SELECT PostGIS_Version() AS version;")
        row = cur.fetchone()
        return row["version"] if row else None
