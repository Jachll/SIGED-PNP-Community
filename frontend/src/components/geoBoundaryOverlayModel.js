export function getBoundaryOverlayRenderState(visibleLayers = [], focusLayer = null) {
  const safeVisibleLayers = Array.isArray(visibleLayers) ? visibleLayers : [];
  const hasLoadedFocusLayer = Boolean(
    focusLayer &&
    focusLayer.renderData &&
    !focusLayer.error
  );
  const shouldRenderFocusLayer = Boolean(
    hasLoadedFocusLayer &&
    safeVisibleLayers.some((layer) => layer.id === focusLayer.id)
  );

  return {
    shouldRenderFocusLayer,
    renderedVisibleLayers: shouldRenderFocusLayer
      ? safeVisibleLayers.filter((layer) => layer.id !== focusLayer.id)
      : safeVisibleLayers
  };
}
