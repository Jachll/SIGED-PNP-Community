import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, Pane, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import GeoBoundaryLayerControls from "./GeoBoundaryLayerControls";
import GeoBoundaryLayerOverlays from "./GeoBoundaryLayerOverlays";
import MapViewportSync from "./MapViewportSync";
import { getRenderableEventMarkers } from "./eventMapModel";
import MapFocusBadge from "./dashboard/MapFocusBadge";
import MapLegend from "./dashboard/MapLegend";
import MapStatusBar from "./dashboard/MapStatusBar";
import { useGeoBoundaryLayers } from "../hooks/useGeoBoundaryLayers";
import { fetchEventoDetalle } from "../services/api";

const COMMUNITY_MAP_CENTER = [0.011, -0.011];
const EVENT_HEATMAP_PANE = "event-heatmap-pane";
const EVENT_MARKERS_PANE = "event-markers-pane";

function createEventMarkerIcon(isSelected = false) {
  return L.divIcon({
    className: `event-map-marker ${isSelected ? "event-map-marker-active" : ""}`.trim(),
    html: '<span class="event-map-marker-dot" aria-hidden="true"></span>',
    iconSize: [18, 18],
    iconAnchor: [9, 9]
  });
}

const EVENT_MARKER_ICON = createEventMarkerIcon(false);
const EVENT_MARKER_ACTIVE_ICON = createEventMarkerIcon(true);

function HeatmapLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points.length) {
      return undefined;
    }

    const heat = L.heatLayer(
      points.map((point) => [point.lat, point.lng, point.intensidad || 1]),
      {
        pane: EVENT_HEATMAP_PANE,
        radius: 25,
        blur: 18,
        maxZoom: 17
      }
    );

    heat.addTo(map);

    return () => {
      map.removeLayer(heat);
    };
  }, [map, points]);

  return null;
}

export default function EventMap({
  eventos,
  heatmapData,
  showHeatmap,
  enableGeoBoundaryLayers = true,
  onHierarchyChange,
  territorialScope = null,
  territorialContext = null,
  isTerritorialLoading = false,
  isTerritorialScopePending = false,
  territorialError = "",
  onTerritorialChange = null,
  center = COMMUNITY_MAP_CENTER,
  zoom = 11
}) {
  const [mapZoom, setMapZoom] = useState(zoom);
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
    enableGeoBoundaryLayers && territorialScope && territorialContext && onTerritorialChange
        ? {
          scope: territorialScope,
          context: territorialContext,
          isContextLoading: isTerritorialLoading,
          contextError: territorialError,
          isScopeTransitionPending: isTerritorialScopePending,
          updateScope: onTerritorialChange,
          viewportZoom: mapZoom,
          viewportBbox
        }
      : {
          viewportZoom: mapZoom,
          viewportBbox,
          disabled: !enableGeoBoundaryLayers
        }
  );
  const [detailByEventId, setDetailByEventId] = useState({});
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [selectedEventSnapshot, setSelectedEventSnapshot] = useState(null);
  const eventMarkers = getRenderableEventMarkers(eventos);
  const selectedEvent = useMemo(() => {
    if (!selectedEventId) {
      return null;
    }

    return eventos.find((evento) => evento.id_evento === selectedEventId) ?? selectedEventSnapshot;
  }, [eventos, selectedEventId, selectedEventSnapshot]);
  const selectedEventDetailState = selectedEventId ? detailByEventId[selectedEventId] ?? null : null;
  const isGeoBusy = isCatalogLoading || isContextLoading || layers.some((layer) => layer.isLoading);
  const heatmapActive = Boolean(showHeatmap && heatmapData.length);

  useEffect(() => {
    if (enableGeoBoundaryLayers && typeof onHierarchyChange === "function") {
      onHierarchyChange({
        scope,
        context
      });
    }
  }, [context, enableGeoBoundaryLayers, onHierarchyChange, scope]);

  useEffect(() => {
    if (!selectedEventId) {
      setSelectedEventSnapshot(null);
      return;
    }

    const currentSelectedEvent = eventos.find((evento) => evento.id_evento === selectedEventId);
    if (currentSelectedEvent) {
      setSelectedEventSnapshot(currentSelectedEvent);
    }
  }, [eventos, selectedEventId]);

  function loadEventDetail(idEvento) {
    const currentState = detailByEventId[idEvento];
    if (currentState?.status === "loading" || currentState?.status === "success") {
      return;
    }

    setDetailByEventId((current) => ({
      ...current,
      [idEvento]: {
        status: "loading",
        data: current[idEvento]?.data ?? null,
        error: ""
      }
    }));

    void fetchEventoDetalle(idEvento).then(
      (detail) => {
        setDetailByEventId((current) => ({
          ...current,
          [idEvento]: {
            status: "success",
            data: detail,
            error: ""
          }
        }));
      },
      (requestError) => {
        setDetailByEventId((current) => ({
          ...current,
          [idEvento]: {
            status: "error",
            data: current[idEvento]?.data ?? null,
            error: requestError?.message || "No se pudo cargar el detalle del evento."
          }
        }));
      }
    );
  }

  function handleSelectEvent(idEvento) {
    const snapshot = eventos.find((evento) => evento.id_evento === idEvento) ?? null;
    setSelectedEventId(idEvento);
    setSelectedEventSnapshot(snapshot);
    loadEventDetail(idEvento);
  }

  return (
    <div className="analytics-map-shell" aria-busy={isGeoBusy}>
      <div className="map-operational-strip">
        <MapStatusBar
          eventCount={eventMarkers.length}
          heatmapActive={heatmapActive}
          visibleLayers={visibleLayers}
          isBusy={isGeoBusy}
        />
        <MapFocusBadge
          scope={scope}
          isPending={isTerritorialScopePending || isContextLoading}
        />
      </div>

      <div className="event-map-frame" role="region" aria-label="Mapa operativo de eventos">
        <MapContainer center={center} zoom={zoom} className="mapa" preferCanvas>
          <MapViewportSync
            onViewportChange={(nextZoom, nextBbox) => {
              setMapZoom(nextZoom);
              setViewportBbox(nextBbox);
            }}
          />
          <Pane name={EVENT_HEATMAP_PANE} style={{ zIndex: 405, pointerEvents: "none" }} />
          <Pane name={EVENT_MARKERS_PANE} style={{ zIndex: 760 }} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {enableGeoBoundaryLayers ? (
            <GeoBoundaryLayerOverlays visibleLayers={visibleLayers} focusLayer={focusLayer} />
          ) : null}
          {showHeatmap ? <HeatmapLayer points={heatmapData} /> : null}

          {eventMarkers.map((evento) => (
            <EventMarker
              key={evento.id_evento}
              evento={evento}
              isSelected={evento.id_evento === selectedEventId}
              onSelectEvent={handleSelectEvent}
            />
          ))}
        </MapContainer>

        {selectedEvent ? (
          <EventDetailPanel
            evento={selectedEvent}
            detailState={selectedEventDetailState}
            onClose={() => {
              setSelectedEventId(null);
              setSelectedEventSnapshot(null);
            }}
          />
        ) : null}
      </div>

      <MapLegend
        eventCount={eventMarkers.length}
        heatmapActive={heatmapActive}
        visibleLayers={visibleLayers}
      />

      {enableGeoBoundaryLayers ? (
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
      ) : null}
    </div>
  );
}

function EventMarker({ evento, isSelected, onSelectEvent }) {
  return (
    <Marker
      position={[evento.latitud, evento.longitud]}
      pane={EVENT_MARKERS_PANE}
      icon={isSelected ? EVENT_MARKER_ACTIVE_ICON : EVENT_MARKER_ICON}
      keyboard
      bubblingMouseEvents={false}
      zIndexOffset={isSelected ? 2600 : 2000}
      riseOnHover
      eventHandlers={{
        click: () => onSelectEvent(evento.id_evento)
      }}
    />
  );
}

function EventDetailPanel({ evento, detailState, onClose }) {
  const detail = detailState?.data;
  const relatedEvents = detail?.contexto_lugar?.eventos_recientes ?? [];
  const territorialReference = detail?.referencia_territorial;

  return (
    <aside className="event-detail-panel">
      <div className="event-detail-panel-header">
        <div>
          <strong>{detail?.nombre_delito || evento.nombre_delito}</strong>
          <p>
            {detail?.fecha || evento.fecha} {detail?.hora || evento.hora}
          </p>
        </div>
        <button
          type="button"
          className="event-detail-close"
          onClick={onClose}
          aria-label="Cerrar detalle del evento"
        >
          ×
        </button>
      </div>

      <div className="event-detail-panel-body">
        <p>{detail?.direccion || evento.direccion}</p>
        <p>{detail?.nombre_comisaria || evento.nombre_comisaria || "Comisaria no disponible"}</p>
        <p>{detail?.distrito || evento.distrito}</p>

        {territorialReference?.region ? <p>Region: {territorialReference.region}</p> : null}
        {territorialReference?.division ? <p>Division: {territorialReference.division}</p> : null}
        {territorialReference?.jurisdiccion ? <p>Jurisdiccion: {territorialReference.jurisdiccion}</p> : null}
        {territorialReference?.sector ? <p>Sector: {territorialReference.sector}</p> : null}
        {detail?.descripcion || evento.descripcion ? <p>{detail?.descripcion || evento.descripcion}</p> : null}

        {detailState?.status === "loading" ? (
          <p className="event-detail-status">Cargando contexto del lugar...</p>
        ) : null}
        {detailState?.status === "error" ? (
          <p className="event-detail-status error">{detailState.error}</p>
        ) : null}

        {detail?.contexto_lugar ? (
          <div className="event-detail-history">
            <strong>Historico cercano</strong>
            <p>Radio: {detail.contexto_lugar.radio_metros} m</p>
            <p>Total historico: {detail.contexto_lugar.total_eventos_historicos}</p>
            <p>Ultimos 30 dias: {detail.contexto_lugar.total_eventos_30_dias}</p>
            <p>Ultimos 90 dias: {detail.contexto_lugar.total_eventos_90_dias}</p>

            {relatedEvents.length ? (
              <div className="event-detail-related">
                <strong>Recientes</strong>
                {relatedEvents.map((item) => (
                  <p key={item.id_evento}>
                    {item.fecha} {item.hora} · {item.nombre_delito}
                    {typeof item.distancia_metros === "number" ? ` · ${item.distancia_metros} m` : ""}
                  </p>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </aside>
  );
}
