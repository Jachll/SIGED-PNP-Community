export function getRenderableEventMarkers(eventos = [], boundaryState = null) {
  void boundaryState;

  return Array.isArray(eventos) ? eventos : [];
}
