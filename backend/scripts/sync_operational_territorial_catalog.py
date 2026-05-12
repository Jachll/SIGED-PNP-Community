import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import get_cursor
from app.etl.operational_sync import sync_operational_catalog_for_regions, try_refresh_territorial_dimension
from app.repositories.territorial_repository import (
    fetch_official_catalog_status,
)
from app.repositories.territory_layers_repository import fetch_regions, territory_layers_source_ready
from app.territorial import normalize_territory_name


def _resolve_regions_to_sync(cur, region: str | None) -> list[str]:
    if not territory_layers_source_ready(cur):
        raise RuntimeError(
            "Las tablas territorio_* no estan listas. Ejecuta primero la importacion PostGIS de capas territoriales."
        )

    available_regions = [str(row["name"]) for row in fetch_regions(cur=cur)]
    normalized_region = normalize_territory_name(region) or None

    if normalized_region is None:
        return available_regions

    if normalized_region not in available_regions:
        raise RuntimeError(f"La region territorial '{normalized_region}' no existe o no esta activa.")

    return [normalized_region]


def run_sync(*, region: str | None = None) -> dict[str, object]:
    with get_cursor() as cur:
        regions_to_sync = _resolve_regions_to_sync(cur, region)
        region_summaries = sync_operational_catalog_for_regions(cur, regions_to_sync)

        for region_summary in region_summaries:
            print(
                "[territorio] sync-only region=%s comisarias=%s jurisdicciones=%s sectores=%s"
                % (
                    region_summary["region"],
                    region_summary["comisarias_upserted"],
                    region_summary["jurisdicciones_upserted"],
                    region_summary["sectores_upserted"],
                )
            )

        dimension_refreshed, dimension_refresh_error = try_refresh_territorial_dimension(cur)
        official_status = fetch_official_catalog_status(cur)

    return {
        "regions": region_summaries,
        "dimension_refreshed": dimension_refreshed,
        "dimension_refresh_error": dimension_refresh_error,
        "official_status": official_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sincroniza comisarias y zonas_operativas desde territorio_* sin reimportar capas PostGIS."
    )
    parser.add_argument(
        "--region",
        help="Sincroniza solo una region policial activa. Si se omite, sincroniza todas.",
    )
    args = parser.parse_args()

    result = run_sync(region=args.region)
    official_status = result["official_status"]
    print(
        "[territorio] sync-only complete regiones=%s dimension_refreshed=%s comisarias_oficiales=%s jurisdicciones_oficiales=%s sectores_oficiales=%s"
        % (
            len(result["regions"]),
            "yes" if result["dimension_refreshed"] else "no",
            official_status["total_comisarias_oficiales"],
            official_status["total_jurisdicciones"],
            official_status["total_sectores"],
        )
    )
    if result["dimension_refresh_error"]:
        print(f"[territorio] warning dimension_refresh_error={result['dimension_refresh_error']}")


if __name__ == "__main__":
    main()
