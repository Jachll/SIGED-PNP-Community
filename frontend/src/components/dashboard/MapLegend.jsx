export default function MapLegend({
  eventCount = 0,
  heatmapActive = false,
  visibleLayers = []
}) {
  const selectedLayers = Array.isArray(visibleLayers) ? visibleLayers : [];

  return (
    <div className="map-legend" aria-label="Leyenda del Mapa de Incidencias">
      <div className="map-legend-item">
        <span className="map-legend-symbol incidence" aria-hidden="true" />
        <span>Puntos de incidencia</span>
        <strong>{eventCount}</strong>
      </div>
      <div className={`map-legend-item ${heatmapActive ? "" : "muted"}`}>
        <span className="map-legend-symbol heatmap" aria-hidden="true" />
        <span>Heatmap</span>
        <strong>{heatmapActive ? "Activo" : "Inactivo"}</strong>
      </div>
      <div className={`map-legend-item ${selectedLayers.length ? "" : "muted"}`}>
        <span className="map-legend-symbol boundary" aria-hidden="true" />
        <span>Capas visibles</span>
        <strong>{selectedLayers.length}</strong>
      </div>
      {!eventCount ? (
        <div className="map-legend-item muted">
          <span className="map-legend-symbol empty" aria-hidden="true" />
          <span>Sin puntos para la seleccion actual</span>
        </div>
      ) : null}
    </div>
  );
}
