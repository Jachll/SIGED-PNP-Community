export default function MapStatusBar({
  eventCount = 0,
  heatmapActive = false,
  visibleLayers = [],
  isBusy = false
}) {
  const selectedLayers = Array.isArray(visibleLayers) ? visibleLayers : [];
  const visibleLayerNames = selectedLayers
    .map((layer) => layer.label || layer.id)
    .filter(Boolean)
    .join(", ");

  return (
    <div className="map-status-bar" aria-label="Estado del Mapa de Incidencias">
      <div className="map-status-item primary">
        <span>Eventos visibles</span>
        <strong>{eventCount}</strong>
      </div>
      <div className="map-status-item">
        <span>Capas visibles</span>
        <strong>{selectedLayers.length}</strong>
      </div>
      <div className="map-status-item">
        <span>Heatmap</span>
        <strong>{heatmapActive ? "Activo" : "Inactivo"}</strong>
      </div>
      <div className="map-status-item wide">
        <span>Delimitaciones</span>
        <strong>{visibleLayerNames || "Sin capas persistentes"}</strong>
      </div>
      {isBusy ? (
        <div className="map-status-item busy" role="status" aria-live="polite">
          <span>Estado</span>
          <strong>Sincronizando mapa</strong>
        </div>
      ) : null}
    </div>
  );
}
