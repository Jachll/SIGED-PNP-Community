export const LAYER_CACHE_LIMIT = 2;
export const FULL_DETAIL_ZOOM_BY_LAYER = Object.freeze({
  regiones: 12,
  divisiones: 13,
  jurisdicciones: 15,
  sectores: 16
});

const VIEWPORT_BBOX_LAYER_IDS = new Set(["jurisdicciones", "sectores"]);

export function getDefaultDetailForLayer(layerId, { isFocus = false, viewportZoom = 0 } = {}) {
  if (layerId === "comisarias") {
    return "full";
  }

  if (isFocus) {
    return "full";
  }

  const threshold = FULL_DETAIL_ZOOM_BY_LAYER[layerId];
  if (typeof threshold === "number" && viewportZoom >= threshold) {
    return "full";
  }

  return "simplified";
}

export function getScopedLayerDetail(layerId, scope = {}, viewportZoom = 0) {
  if (layerId === "jurisdicciones" && !scope.jurisdiccion) {
    return "simplified";
  }

  if (layerId === "sectores" && !scope.sector) {
    return "simplified";
  }

  return getDefaultDetailForLayer(layerId, { viewportZoom });
}

export function getViewportBboxForLayer(layerId, viewportBbox, { isViewportAligned = true } = {}) {
  if (!VIEWPORT_BBOX_LAYER_IDS.has(layerId) || !isViewportAligned) {
    return "";
  }

  return typeof viewportBbox === "string" && viewportBbox.trim() ? viewportBbox.trim() : "";
}

export function buildLayerRetentionKey(layerId, filters) {
  return [
    layerId,
    filters.region || "",
    filters.division || "",
    filters.comisaria_id || "",
    filters.comisaria || "",
    filters.jurisdiccion || "",
    filters.sector || ""
  ].join("::");
}

export function buildLayerRequestKey(layerId, filters) {
  return [
    layerId,
    filters.region || "",
    filters.division || "",
    filters.comisaria_id || "",
    filters.comisaria || "",
    filters.jurisdiccion || "",
    filters.sector || "",
    filters.bbox || "",
    filters.detail || "auto"
  ].join("::");
}

export function findLayerCacheEntry(cacheByLayerId, layerId, requestKey) {
  const entries = cacheByLayerId[layerId];
  if (!Array.isArray(entries)) {
    return null;
  }

  return entries.find((entry) => entry.requestKey === requestKey) ?? null;
}

export function getLatestLayerCacheEntry(cacheByLayerId, layerId, retentionKey = "") {
  const entries = cacheByLayerId[layerId];
  if (!Array.isArray(entries) || !entries.length) {
    return null;
  }

  if (!retentionKey) {
    return entries[0];
  }

  return entries.find((entry) => entry.retentionKey === retentionKey) ?? null;
}

export function resolveRenderableLayerCacheEntry(cacheByLayerId, layerId, requestKey, retentionKey, hasError = false) {
  const currentEntry = findLayerCacheEntry(cacheByLayerId, layerId, requestKey);
  if (currentEntry) {
    return currentEntry;
  }

  if (hasError) {
    return null;
  }

  return getLatestLayerCacheEntry(cacheByLayerId, layerId, retentionKey);
}

export function shouldRetainStaleGeometry(layerId) {
  return layerId !== "comisarias";
}

export function upsertLayerCacheEntry(cacheByLayerId, layerId, nextEntry) {
  const currentEntries = Array.isArray(cacheByLayerId[layerId]) ? cacheByLayerId[layerId] : [];
  const nextEntries = [
    nextEntry,
    ...currentEntries.filter((entry) => entry.requestKey !== nextEntry.requestKey)
  ].slice(0, LAYER_CACHE_LIMIT);

  return {
    ...cacheByLayerId,
    [layerId]: nextEntries
  };
}

export function removeLayerCacheEntry(cacheByLayerId, layerId, requestKey) {
  const currentEntries = Array.isArray(cacheByLayerId[layerId]) ? cacheByLayerId[layerId] : [];
  const nextEntries = currentEntries.filter((entry) => entry.requestKey !== requestKey);

  if (nextEntries.length === currentEntries.length) {
    return cacheByLayerId;
  }

  if (!nextEntries.length) {
    const nextCache = { ...cacheByLayerId };
    delete nextCache[layerId];
    return nextCache;
  }

  return {
    ...cacheByLayerId,
    [layerId]: nextEntries
  };
}

export function clearLayerLoadingState(loadingRequestKeyByLayerId, layerId, requestKey) {
  if (loadingRequestKeyByLayerId[layerId] !== requestKey) {
    return loadingRequestKeyByLayerId;
  }

  const nextLoadingState = { ...loadingRequestKeyByLayerId };
  delete nextLoadingState[layerId];
  return nextLoadingState;
}
