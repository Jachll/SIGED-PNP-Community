import { useEffect, useRef } from "react";
import { useMapEvents } from "react-leaflet";
import {
  serializeViewportBounds,
  shouldCommitViewportChange,
  VIEWPORT_DEBOUNCE_MS
} from "../utils/mapViewport";

export default function MapViewportSync({
  onViewportChange,
  debounceMs = VIEWPORT_DEBOUNCE_MS
}) {
  const debounceTimeoutRef = useRef(null);
  const lastViewportRef = useRef(null);

  const map = useMapEvents({
    zoomend() {
      scheduleViewportCommit();
    },
    moveend() {
      scheduleViewportCommit();
    }
  });

  function clearPendingViewportCommit() {
    if (debounceTimeoutRef.current) {
      window.clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }
  }

  function commitViewportChange() {
    const nextViewport = {
      zoom: map.getZoom(),
      bbox: serializeViewportBounds(map.getBounds())
    };

    if (!shouldCommitViewportChange(lastViewportRef.current, nextViewport)) {
      return;
    }

    lastViewportRef.current = nextViewport;
    onViewportChange(nextViewport.zoom, nextViewport.bbox);
  }

  function scheduleViewportCommit() {
    clearPendingViewportCommit();
    debounceTimeoutRef.current = window.setTimeout(() => {
      debounceTimeoutRef.current = null;
      commitViewportChange();
    }, debounceMs);
  }

  useEffect(() => {
    commitViewportChange();

    return () => {
      clearPendingViewportCommit();
    };
  }, [debounceMs, map, onViewportChange]);

  return null;
}
