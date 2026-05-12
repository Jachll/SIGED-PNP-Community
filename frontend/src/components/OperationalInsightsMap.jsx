import { useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import GeoBoundaryLayerControls from "./GeoBoundaryLayerControls";
import GeoBoundaryLayerOverlays from "./GeoBoundaryLayerOverlays";
import MapViewportSync from "./MapViewportSync";
import { useGeoBoundaryLayers } from "../hooks/useGeoBoundaryLayers";

const DEFAULT_CENTER = [-12.0464, -77.0428];
const DEFAULT_ZOOM = 12;

function hasValidCoordinates(latitud, longitud) {
  return Number.isFinite(Number(latitud)) && Number.isFinite(Number(longitud));
}

function getMapCenter(hotspots, zonasCriticas, recomendaciones) {
  const allPoints = [
    ...hotspots
      .filter((item) => hasValidCoordinates(item.latitud, item.longitud))
      .map((item) => [Number(item.latitud), Number(item.longitud)]),
    ...zonasCriticas
      .filter((item) => hasValidCoordinates(item.latitud, item.longitud))
      .map((item) => [Number(item.latitud), Number(item.longitud)]),
    ...recomendaciones
      .filter((item) => hasValidCoordinates(item.zona?.latitud, item.zona?.longitud))
      .map((item) => [Number(item.zona.latitud), Number(item.zona.longitud)])
  ];

  if (!allPoints.length) {
    return DEFAULT_CENTER;
  }

  const total = allPoints.reduce(
    (accumulator, [lat, lng]) => ({
      lat: accumulator.lat + lat,
      lng: accumulator.lng + lng
    }),
    { lat: 0, lng: 0 }
  );

  return [total.lat / allPoints.length, total.lng / allPoints.length];
}

function getPriorityRadius(priority) {
  const normalized = String(priority || "").toUpperCase();

  if (normalized.includes("CRIT")) {
    return 11;
  }

  if (normalized.includes("ALTA")) {
    return 9;
  }

  if (normalized.includes("MED")) {
    return 8;
  }

  return 7;
}

function getHotspotRadius(conteoEventos) {
  return Math.min(18, Math.max(7, 5 + Math.ceil(Number(conteoEventos || 0) / 2)));
}

function getZoneRadius(totalEventos) {
  return Math.min(18, Math.max(8, 6 + Math.ceil(Number(totalEventos || 0) / 15)));
}

export default function OperationalInsightsMap({
  hotspots,
  zonasCriticas,
  recomendaciones,
  territorialScope = null,
  territorialContext = null,
  isTerritorialLoading = false,
  territorialError = "",
  onTerritorialChange = null
}) {
  const [mapZoom, setMapZoom] = useState(DEFAULT_ZOOM);
  const [viewportBbox, setViewportBbox] = useState("");
  const {
    layers,
    visibleLayers,
    focusLayer,
    scope,
    context,
    isCatalogLoading,
    isContextLoading,
    catalogError,
    contextError,
    toggleLayer,
    updateScope
  } = useGeoBoundaryLayers(
    territorialScope && territorialContext && onTerritorialChange
        ? {
          scope: territorialScope,
          context: territorialContext,
          isContextLoading: isTerritorialLoading,
          contextError: territorialError,
          updateScope: onTerritorialChange,
          viewportZoom: mapZoom,
          viewportBbox
        }
      : {
          viewportZoom: mapZoom,
          viewportBbox
        }
  );
  const hotspotMarkers = hotspots.filter((item) => hasValidCoordinates(item.latitud, item.longitud));
  const zoneMarkers = zonasCriticas.filter((item) => hasValidCoordinates(item.latitud, item.longitud));
  const recommendationMarkers = recomendaciones.filter((item) =>
    hasValidCoordinates(item.zona?.latitud, item.zona?.longitud)
  );
  const center = getMapCenter(hotspots, zonasCriticas, recomendaciones);
  const mapKey = `${center[0].toFixed(4)}-${center[1].toFixed(4)}-${hotspotMarkers.length}-${zoneMarkers.length}-${recommendationMarkers.length}`;
  const isGeoBusy = isCatalogLoading || isContextLoading || layers.some((layer) => layer.isLoading);

  return (
    <div className="analytics-map-shell" aria-busy={isGeoBusy}>
      <div className="analytics-map-legend">
        <span className="legend-item hotspot">Hotspots ({hotspotMarkers.length})</span>
        <span className="legend-item zona">Zonas criticas ({zoneMarkers.length})</span>
        <span className="legend-item recomendacion">Recomendaciones ({recommendationMarkers.length})</span>
      </div>

      <GeoBoundaryLayerControls
        layers={layers}
        scope={scope}
        context={context}
        isCatalogLoading={isCatalogLoading}
        isContextLoading={isContextLoading}
        catalogError={catalogError}
        contextError={contextError}
        toggleLayer={toggleLayer}
        updateScope={updateScope}
      />

      <div role="region" aria-label="Mapa analitico operativo">
        <MapContainer key={mapKey} center={center} zoom={DEFAULT_ZOOM} className="mapa" preferCanvas>
          <MapViewportSync
            onViewportChange={(nextZoom, nextBbox) => {
              setMapZoom(nextZoom);
              setViewportBbox(nextBbox);
            }}
          />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <GeoBoundaryLayerOverlays visibleLayers={visibleLayers} focusLayer={focusLayer} />

          {hotspotMarkers.map((hotspot) => (
            <CircleMarker
              key={`hotspot-${hotspot.id_hotspot}`}
              center={[Number(hotspot.latitud), Number(hotspot.longitud)]}
              radius={getHotspotRadius(hotspot.conteo_eventos)}
              pathOptions={{ color: "#8c1f1f", fillColor: "#c53a3a", fillOpacity: 0.85 }}
            >
              <Popup>
                <strong>{hotspot.nombre_zona || hotspot.distrito}</strong>
                <br />
                Hotspot: {hotspot.nivel_riesgo}
                <br />
                Eventos: {hotspot.conteo_eventos}
                <br />
                Delito: {hotspot.nombre_delito || "Sin clasificar"}
                <br />
                Estado: {hotspot.estado_hotspot}
              </Popup>
            </CircleMarker>
          ))}

          {zoneMarkers.map((zona) => (
            <CircleMarker
              key={`zona-${zona.codigo_zona}`}
              center={[Number(zona.latitud), Number(zona.longitud)]}
              radius={getZoneRadius(zona.total_eventos)}
              pathOptions={{ color: "#1f5d82", fillColor: "#2c7fb4", fillOpacity: 0.75 }}
            >
              <Popup>
                <strong>{zona.nombre_zona}</strong>
                <br />
                Prioridad: {zona.prioridad_operativa}
                <br />
                Riesgo: {zona.nivel_riesgo}
                <br />
                Eventos: {zona.total_eventos}
                <br />
                Hotspots: {zona.total_hotspots}
              </Popup>
            </CircleMarker>
          ))}

          {recommendationMarkers.map((item, index) => (
            <CircleMarker
              key={`recomendacion-${item.id_recomendacion ?? `${item.regla_codigo}-${index}`}`}
              center={[Number(item.zona.latitud), Number(item.zona.longitud)]}
              radius={getPriorityRadius(item.prioridad)}
              pathOptions={{ color: "#256642", fillColor: "#37a16b", fillOpacity: 0.78 }}
            >
              <Popup>
                <strong>{item.zona?.nombre_zona || "Zona sin nombre"}</strong>
                <br />
                Prioridad: {item.prioridad || "Sin prioridad"}
                <br />
                Turno: {item.ventana_horaria?.turno || "Sin turno"}
                <br />
                Accion: {item.tipo_recomendacion || "Sin accion"}
                <br />
                Recursos: {item.recursos_sugeridos?.cantidad_efectivos ?? 0} efectivos / {item.recursos_sugeridos?.cantidad_unidades ?? 0} unidades
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
