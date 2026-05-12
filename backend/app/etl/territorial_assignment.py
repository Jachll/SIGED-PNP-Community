from dataclasses import dataclass
import json
import logging
from typing import Any

from app.etl.tabular import TabularValidationError
from app.geo_layers import find_region_for_point, get_geo_layer_data
from app.repositories.territorial_repository import (
    _territorial_assignment_columns_ready,
    fetch_region_catalog_status,
    refresh_territorial_dimension_if_available,
    resolve_official_comisaria,
    upsert_official_comisaria,
    upsert_official_zona,
)
from app.territorial import normalize_territory_name

logger = logging.getLogger("siged.etl.territorial")

TERRITORIAL_STATE_JURISDICTION = "ASIGNADO_POR_JURISDICCION"
TERRITORIAL_STATE_SECTOR = "ASIGNADO_POR_SECTOR"
TERRITORIAL_STATE_NO_MATCH = "SIN_COINCIDENCIA_TERRITORIAL"
TERRITORIAL_STATE_CONFLICT = "CONFLICTO_ID_COMISARIA_VS_GEOMETRIA"
TERRITORIAL_RULE_JURISDICTION = "JURISDICCION_OFICIAL"
TERRITORIAL_RULE_SECTOR = "SECTOR_OFICIAL"
TERRITORIAL_RULE_MANUAL = "REVISION_MANUAL"
MIGRATION_HINT = "15_etl_asignacion_territorial.sql"


@dataclass(frozen=True)
class TerritorialLookupResult:
    estado_territorial: str
    regla_territorial: str
    id_comisaria_resuelta: int | None
    nombre_comisaria_resuelta: str | None
    distrito_resuelto: str | None
    motivo_territorial: str | None
    conflicto_territorial: bool


def ensure_official_territorial_catalog_ready(cur) -> None:
    if not _territorial_assignment_columns_ready(cur):
        raise TabularValidationError(
            (
                "El ETL territorial requiere la migracion "
                f"{MIGRATION_HINT} en la base activa antes de procesar lotes."
            )
        )


def ensure_region_territorial_catalog_ready(
    cur,
    *,
    latitud: float,
    longitud: float,
    region_cache: set[str],
) -> str | None:
    detected_region = _detect_region_for_point(cur, latitud=latitud, longitud=longitud)
    if not detected_region:
        return None

    if detected_region in region_cache:
        return detected_region

    current_status = fetch_region_catalog_status(cur, detected_region)
    if _region_catalog_is_ready(current_status):
        region_cache.add(detected_region)
        return detected_region

    summary = sync_region_territorial_catalog(cur, detected_region)
    refresh_territorial_dimension_if_available(cur)
    refreshed_status = fetch_region_catalog_status(cur, detected_region)

    if not _region_catalog_is_ready(refreshed_status):
        raise TabularValidationError(
            (
                "No se pudo preparar el catalogo territorial oficial para la region "
                f"{detected_region}."
            )
        )

    region_cache.add(detected_region)
    logger.info(
        "Catalogo territorial regional sincronizado region=%s comisarias=%s jurisdicciones=%s sectores=%s",
        detected_region,
        summary["comisarias_upserted"],
        summary["jurisdicciones_upserted"],
        summary["sectores_upserted"],
    )
    return detected_region


def sync_region_territorial_catalog(cur, region: str) -> dict[str, int]:
    district_by_code: dict[str, str] = {}
    summary = {
        "comisarias_upserted": 0,
        "jurisdicciones_upserted": 0,
        "sectores_upserted": 0,
    }

    cur.execute(
        """
        UPDATE zonas_operativas z
        SET
            estado_zona = 'INACTIVA',
            updated_at = NOW()
        FROM comisarias c
        WHERE c.id_comisaria = z.id_comisaria
          AND c.region_policial = %s
          AND z.tipo_zona IN ('JURISDICCION', 'SECTOR');
        """,
        (normalize_territory_name(region),),
    )

    for feature in _iter_region_layer_features("comisarias", region):
        payload = _build_comisaria_payload(feature)
        if payload is None:
            continue

        district_by_code[payload["codigo_cpnp"]] = payload["distrito"]
        upsert_official_comisaria(cur, payload)
        summary["comisarias_upserted"] += 1

    for feature in _iter_region_layer_features("jurisdicciones", region):
        payload = _build_zone_payload(
            feature,
            tipo_zona="JURISDICCION",
            district_by_code=district_by_code,
        )
        if payload is None:
            continue
        upsert_official_zona(cur, payload)
        summary["jurisdicciones_upserted"] += 1

    for feature in _iter_region_layer_features("sectores", region):
        payload = _build_zone_payload(
            feature,
            tipo_zona="SECTOR",
            district_by_code=district_by_code,
        )
        if payload is None:
            continue
        upsert_official_zona(cur, payload)
        summary["sectores_upserted"] += 1

    return summary


def apply_territorial_assignment(cur, clean_row: dict[str, Any]) -> dict[str, Any]:
    original_id = clean_row.get("id_comisaria_original")
    resolution = _resolve_by_priority(cur, latitud=clean_row["latitud"], longitud=clean_row["longitud"])
    original_id_note = _build_original_id_note(clean_row)

    if resolution.id_comisaria_resuelta is None:
        clean_row["id_comisaria"] = None
        clean_row["id_comisaria_resuelta"] = None
        clean_row["nombre_comisaria_resuelta"] = None
        clean_row["estado_territorial"] = resolution.estado_territorial
        clean_row["regla_territorial"] = resolution.regla_territorial
        clean_row["motivo_territorial"] = _join_reason(resolution.motivo_territorial, original_id_note)
        clean_row["conflicto_territorial"] = False
        return clean_row

    clean_row["id_comisaria"] = resolution.id_comisaria_resuelta
    clean_row["id_comisaria_resuelta"] = resolution.id_comisaria_resuelta
    clean_row["nombre_comisaria_resuelta"] = resolution.nombre_comisaria_resuelta
    clean_row["distrito"] = normalize_territory_name(resolution.distrito_resuelto or clean_row["distrito"])
    clean_row["regla_territorial"] = resolution.regla_territorial
    clean_row["conflicto_territorial"] = False

    if original_id is not None and original_id != resolution.id_comisaria_resuelta:
        clean_row["estado_territorial"] = TERRITORIAL_STATE_CONFLICT
        clean_row["conflicto_territorial"] = True
        clean_row["motivo_territorial"] = _join_reason(
            (
                "El id_comisaria entrante no coincide con la geometria oficial. "
                f"Entrante={original_id}, resuelto={resolution.id_comisaria_resuelta}."
            ),
            original_id_note,
        )
        return clean_row

    clean_row["estado_territorial"] = resolution.estado_territorial
    clean_row["motivo_territorial"] = _join_reason(resolution.motivo_territorial, original_id_note)
    return clean_row


def _resolve_by_priority(cur, *, latitud: float, longitud: float) -> TerritorialLookupResult:
    jurisdiction_matches = resolve_official_comisaria(
        cur,
        latitud=latitud,
        longitud=longitud,
        tipo_zona="JURISDICCION",
    )

    if len(jurisdiction_matches) == 1:
        match = jurisdiction_matches[0]
        return TerritorialLookupResult(
            estado_territorial=TERRITORIAL_STATE_JURISDICTION,
            regla_territorial=TERRITORIAL_RULE_JURISDICTION,
            id_comisaria_resuelta=int(match["id_comisaria"]),
            nombre_comisaria_resuelta=str(match["nombre_comisaria"]),
            distrito_resuelto=str(match["distrito"]),
            motivo_territorial="Asignacion automatica por jurisdiccion oficial.",
            conflicto_territorial=False,
        )

    if len(jurisdiction_matches) > 1:
        return TerritorialLookupResult(
            estado_territorial=TERRITORIAL_STATE_NO_MATCH,
            regla_territorial=TERRITORIAL_RULE_MANUAL,
            id_comisaria_resuelta=None,
            nombre_comisaria_resuelta=None,
            distrito_resuelto=None,
            motivo_territorial="Se detectaron multiples coincidencias en jurisdiccion oficial.",
            conflicto_territorial=False,
        )

    sector_matches = resolve_official_comisaria(
        cur,
        latitud=latitud,
        longitud=longitud,
        tipo_zona="SECTOR",
    )

    if len(sector_matches) == 1:
        match = sector_matches[0]
        return TerritorialLookupResult(
            estado_territorial=TERRITORIAL_STATE_SECTOR,
            regla_territorial=TERRITORIAL_RULE_SECTOR,
            id_comisaria_resuelta=int(match["id_comisaria"]),
            nombre_comisaria_resuelta=str(match["nombre_comisaria"]),
            distrito_resuelto=str(match["distrito"]),
            motivo_territorial="Asignacion automatica por sector oficial.",
            conflicto_territorial=False,
        )

    if len(sector_matches) > 1:
        return TerritorialLookupResult(
            estado_territorial=TERRITORIAL_STATE_NO_MATCH,
            regla_territorial=TERRITORIAL_RULE_MANUAL,
            id_comisaria_resuelta=None,
            nombre_comisaria_resuelta=None,
            distrito_resuelto=None,
            motivo_territorial="Se detectaron multiples coincidencias en sector oficial.",
            conflicto_territorial=False,
        )

    return TerritorialLookupResult(
        estado_territorial=TERRITORIAL_STATE_NO_MATCH,
        regla_territorial=TERRITORIAL_RULE_MANUAL,
        id_comisaria_resuelta=None,
        nombre_comisaria_resuelta=None,
        distrito_resuelto=None,
        motivo_territorial="No se encontro coincidencia territorial oficial para las coordenadas.",
        conflicto_territorial=False,
    )


def _build_comisaria_payload(feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry")
    codigo_cpnp = _normalize_code(properties.get("cod_cpnp"))
    nombre_comisaria = normalize_territory_name(properties.get("comisaria"))
    distrito = normalize_territory_name(properties.get("distrito"))

    if not geometry or not codigo_cpnp or not nombre_comisaria or not distrito:
        return None

    return {
        "codigo_cpnp": codigo_cpnp,
        "nombre_comisaria": nombre_comisaria,
        "distrito": distrito,
        "direccion": None,
        "codigo_unidad": _normalize_code(properties.get("cod_uni")),
        "region_policial": normalize_territory_name(properties.get("regionpol")) or None,
        "division_policial": normalize_territory_name(properties.get("divpol_divopus")) or None,
        "geom_geojson": json.dumps(geometry, ensure_ascii=True),
    }


def _build_zone_payload(
    feature: dict[str, Any],
    *,
    tipo_zona: str,
    district_by_code: dict[str, str],
) -> dict[str, Any] | None:
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry")
    codigo_cpnp = _normalize_code(properties.get("cod_cpnp"))

    if not geometry or not codigo_cpnp:
        return None

    distrito = district_by_code.get(codigo_cpnp)
    if not distrito:
        return None

    nombre_comisaria = normalize_territory_name(properties.get("comisaria"))
    object_id = _normalize_code(properties.get("objectid"))
    sector_code = _normalize_code(properties.get("cod_sector"))

    if tipo_zona == "JURISDICCION":
        codigo_zona = f"JUR-{codigo_cpnp}-{object_id or 'SIN_OBJECTID'}"
        nombre_zona = f"JURISDICCION {nombre_comisaria}".strip()
        descripcion = properties.get("resolucion")
    else:
        fallback_code = f"{codigo_cpnp}-{object_id or 'SIN_OBJECTID'}"
        codigo_zona = f"SEC-{sector_code or fallback_code}"
        sector = _normalize_code(properties.get("sector")) or "SIN SECTOR"
        nombre_zona = f"SECTOR {sector} {nombre_comisaria}".strip()
        descripcion = properties.get("label") or properties.get("clas_sector")

    return {
        "codigo_zona": codigo_zona,
        "nombre_zona": nombre_zona[:150],
        "tipo_zona": tipo_zona,
        "distrito": distrito,
        "codigo_cpnp": codigo_cpnp,
        "descripcion": (str(descripcion).strip() if descripcion is not None else "") or None,
        "geom_geojson": json.dumps(geometry, ensure_ascii=True),
    }


def _iter_region_layer_features(layer_id: str, region: str):
    feature_collection = get_geo_layer_data(
        layer_id,
        region=region,
        detail="full",
        enforce_scope=False,
    )
    features = feature_collection.get("features") or []
    if not features:
        raise TabularValidationError(
            f"La capa territorial oficial para la region {region} no esta disponible en este entorno."
        )

    yield from features


def _detect_region_for_point(cur, *, latitud: float, longitud: float) -> str | None:
    return find_region_for_point(latitud=latitud, longitud=longitud, cur=cur)


def _normalize_code(value: object) -> str:
    return str(value or "").strip()


def _region_catalog_is_ready(status: dict[str, int]) -> bool:
    return status.get("total_jurisdicciones", 0) > 0 and status.get("total_sectores", 0) > 0


def _build_original_id_note(clean_row: dict[str, Any]) -> str | None:
    if clean_row.get("id_comisaria_original_invalido"):
        return "El id_comisaria entrante fue ignorado porque no era un valor numerico valido."
    return None


def _join_reason(primary: str | None, secondary: str | None) -> str | None:
    reasons = [item for item in (primary, secondary) if item]
    if not reasons:
        return None
    return " ".join(reasons)
