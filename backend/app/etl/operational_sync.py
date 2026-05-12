import logging

from app.etl.territorial_assignment import sync_region_territorial_catalog
from app.repositories.territorial_repository import refresh_territorial_dimension_if_available

logger = logging.getLogger("siged.etl.operational_sync")


def sync_operational_catalog_for_regions(cur, region_names: list[str]) -> list[dict[str, object]]:
    region_summaries: list[dict[str, object]] = []

    for region_name in region_names:
        summary = sync_region_territorial_catalog(cur, region_name)
        region_summaries.append(
            {
                "region": region_name,
                **summary,
            }
        )

    return region_summaries


def try_refresh_territorial_dimension(cur) -> tuple[bool, str | None]:
    cur.execute("SAVEPOINT siged_refresh_dim_territorial;")

    try:
        refreshed = refresh_territorial_dimension_if_available(cur)
    except Exception as exc:
        cur.execute("ROLLBACK TO SAVEPOINT siged_refresh_dim_territorial;")
        cur.execute("RELEASE SAVEPOINT siged_refresh_dim_territorial;")
        logger.warning("No se pudo refrescar dim_territorios: %s", exc)
        return False, str(exc)

    cur.execute("RELEASE SAVEPOINT siged_refresh_dim_territorial;")
    return refreshed, None
