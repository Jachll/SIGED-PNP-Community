import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import { GeoJSON, Pane, useMap } from "react-leaflet";
import { getBoundaryOverlayRenderState } from "./geoBoundaryOverlayModel";

const LAYER_PANES = Object.freeze({
  regiones: { name: "geo-regiones-pane", zIndex: 410 },
  divisiones: { name: "geo-divisiones-pane", zIndex: 420 },
  sectores: { name: "geo-sectores-pane", zIndex: 430 },
  jurisdicciones: { name: "geo-jurisdicciones-pane", zIndex: 440 },
  focus: { name: "geo-focus-pane", zIndex: 460 },
  comisarias: { name: "geo-comisarias-pane", zIndex: 680 }
});

const COMISARIA_ICON = L.icon({
  iconUrl: "/icons/community-marker.svg",
  iconRetinaUrl: "/icons/community-marker.svg",
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -28],
  tooltipAnchor: [0, -26],
  className: "geo-comisaria-icon"
});

function getFeatureLabel(layerLabel, properties = {}) {
  return (
    properties.label ||
    properties.nombre ||
    properties.name ||
    properties.nombre_comisaria ||
    properties.comisaria ||
    properties.divpol_divopus ||
    properties.regionpol ||
    properties.sector ||
    properties.sectores ||
    properties.jurisdiccion ||
    properties.division ||
    properties.region ||
    layerLabel
  );
}

function getLayerVisualStyle(layer) {
  if (layer.id === "regiones") {
    return {
      color: layer.stroke_color,
      weight: 4,
      opacity: 1,
      fillColor: layer.fill_color,
      fillOpacity: 0.02
    };
  }

  if (layer.id === "divisiones") {
    return {
      color: layer.stroke_color,
      weight: 3,
      opacity: 0.95,
      fillColor: layer.fill_color,
      fillOpacity: 0.02
    };
  }

  if (layer.id === "jurisdicciones") {
    return {
      color: layer.stroke_color,
      weight: 3.2,
      opacity: 1,
      dashArray: "8 4",
      fillColor: layer.fill_color,
      fillOpacity: 0.01
    };
  }

  if (layer.id === "sectores") {
    return {
      color: layer.stroke_color,
      weight: 2,
      opacity: 0.9,
      dashArray: "5 4",
      fillColor: layer.fill_color,
      fillOpacity: 0.004
    };
  }

  return {
    color: layer.stroke_color,
    weight: 2.5,
    opacity: 0.95,
    fillColor: layer.fill_color,
    fillOpacity: 0.03
  };
}

function getFocusVisualStyle(layer) {
  const baseStyle = getLayerVisualStyle(layer);

  return {
    ...baseStyle,
    weight: Number(baseStyle.weight || 2) + 1.5,
    opacity: 1,
    fillOpacity: Math.max(Number(baseStyle.fillOpacity || 0), 0.05)
  };
}

function getGeometryRenderOptions(layer, { isFocus = false } = {}) {
  const isFullDetailLayer = layer.filters?.detail === "full";

  if (isFocus || isFullDetailLayer) {
    return {
      smoothFactor: 0,
      noClip: true
    };
  }

  return {
    smoothFactor: 0.75,
    noClip: false
  };
}

function getPreferredMaxZoom(layerId) {
  if (layerId === "comisarias") {
    return 14;
  }

  if (layerId === "divisiones") {
    return 13;
  }

  if (layerId === "regiones") {
    return 11;
  }

  return 14;
}

function buildViewportTargetKey(targetLayers) {
  return targetLayers
    .map((layer) =>
      [
        layer.id,
        layer.filters?.region || "",
        layer.filters?.division || "",
        layer.filters?.comisaria || "",
        layer.filters?.jurisdiccion || "",
        layer.filters?.sector || "",
        layer.data?.features?.length ?? 0
      ].join("::")
    )
    .join("|");
}

function GeoBoundaryViewportController({ visibleLayers, focusLayer }) {
  const map = useMap();
  const lastAppliedViewportKeyRef = useRef("");

  const targetLayers = useMemo(() => {
    if (focusLayer && focusLayer.data && !focusLayer.error && !focusLayer.isLoading) {
      return [focusLayer];
    }

    return [];
  }, [focusLayer]);

  const viewportTargetKey = useMemo(
    () => buildViewportTargetKey(targetLayers),
    [targetLayers]
  );

  useEffect(() => {
    if (!targetLayers.length) {
      lastAppliedViewportKeyRef.current = "";
      return;
    }

    if (!viewportTargetKey || lastAppliedViewportKeyRef.current === viewportTargetKey) {
      return;
    }

    const bounds = L.latLngBounds([]);

    targetLayers.forEach((layer) => {
      const layerBounds = L.geoJSON(layer.data).getBounds();
      if (layerBounds.isValid()) {
        bounds.extend(layerBounds);
      }
    });

    if (bounds.isValid()) {
      const targetLayer = targetLayers[0];
      const southWest = bounds.getSouthWest();
      const northEast = bounds.getNorthEast();
      const isSinglePoint = southWest.lat === northEast.lat && southWest.lng === northEast.lng;

      if (isSinglePoint) {
        map.setView(bounds.getCenter(), getPreferredMaxZoom(targetLayer.id), {
          animate: true
        });
        lastAppliedViewportKeyRef.current = viewportTargetKey;
        return;
      }

      map.fitBounds(bounds.pad(0.08), {
        animate: true,
        maxZoom: getPreferredMaxZoom(targetLayer.id)
      });
      lastAppliedViewportKeyRef.current = viewportTargetKey;
    }
  }, [map, targetLayers, viewportTargetKey]);

  return null;
}

function GeoBoundaryPanes() {
  return (
    <>
      {Object.entries(LAYER_PANES).map(([layerId, pane]) => (
        <Pane
          key={pane.name}
          name={pane.name}
          style={{
            zIndex: pane.zIndex,
            pointerEvents: layerId === "comisarias" ? "auto" : "none"
          }}
        />
      ))}
    </>
  );
}

function getLayerPaneName(layerId) {
  return LAYER_PANES[layerId]?.name;
}

function buildBoundaryLayerNode(layer, { paneName, style, keyPrefix = "" }) {
  const geometryRenderOptions = getGeometryRenderOptions(layer, {
    isFocus: keyPrefix === "focus::"
  });
  const isInteractiveLayer = layer.id === "comisarias";

  return (
    <GeoJSON
      key={`${keyPrefix}${layer.renderRequestKey || layer.requestKey}`}
      data={layer.renderData}
      pane={paneName}
      interactive={isInteractiveLayer}
      style={() => style}
      smoothFactor={geometryRenderOptions.smoothFactor}
      noClip={geometryRenderOptions.noClip}
      pointToLayer={(feature, latlng) => {
        if (layer.id === "comisarias") {
          return L.marker(latlng, {
            icon: COMISARIA_ICON,
            pane: paneName,
            riseOnHover: true,
            title: getFeatureLabel(layer.label, feature?.properties ?? {})
          });
        }

        return L.circleMarker(latlng, {
          radius: 5,
          pane: paneName,
          color: layer.stroke_color,
          weight: 2,
          opacity: 1,
          fillColor: layer.fill_color,
          fillOpacity: 0.9
        });
      }}
      onEachFeature={(feature, featureLayer) => {
        if (!isInteractiveLayer) {
          return;
        }

        const label = getFeatureLabel(layer.label, feature?.properties ?? {});

        featureLayer.bindPopup(`
          <div>
            <strong>${label}</strong><br/>
            Capa: ${layer.label}
          </div>
        `);

        if (layer.id === "comisarias" && typeof featureLayer.bindTooltip === "function") {
          featureLayer.bindTooltip(label, {
            direction: "top",
            sticky: true,
            className: "geo-comisaria-tooltip"
          });
        }

        if (typeof featureLayer.setStyle === "function") {
          featureLayer.on("mouseover", () => {
            featureLayer.setStyle({
              weight: Number(style.weight || 2) + 1.5,
              opacity: 1,
              fillOpacity: Math.max(Number(style.fillOpacity || 0), 0.05)
            });

            if (typeof featureLayer.bringToFront === "function") {
              featureLayer.bringToFront();
            }
          });

          featureLayer.on("mouseout", () => {
            featureLayer.setStyle(style);
          });
        }
      }}
    />
  );
}

export default function GeoBoundaryLayerOverlays({ visibleLayers, focusLayer }) {
  const { shouldRenderFocusLayer, renderedVisibleLayers } = getBoundaryOverlayRenderState(visibleLayers, focusLayer);

  return (
    <>
      <GeoBoundaryPanes />
      <GeoBoundaryViewportController visibleLayers={visibleLayers} focusLayer={focusLayer} />

      {renderedVisibleLayers.map((layer) => {
        if (!layer.renderData || layer.error) {
          return null;
        }

        return buildBoundaryLayerNode(layer, {
          paneName: getLayerPaneName(layer.id),
          style: getLayerVisualStyle(layer)
        });
      })}

      {shouldRenderFocusLayer
        ? buildBoundaryLayerNode(focusLayer, {
            paneName: LAYER_PANES.focus.name,
            style: getFocusVisualStyle(focusLayer),
            keyPrefix: "focus::"
          })
        : null}
    </>
  );
}
