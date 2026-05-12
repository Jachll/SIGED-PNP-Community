export const VIEWPORT_BBOX_DECIMALS = 4;
export const VIEWPORT_DEBOUNCE_MS = 300;
export const VIEWPORT_BBOX_ABSOLUTE_TOLERANCE = 0.0015;
export const VIEWPORT_BBOX_RELATIVE_TOLERANCE = 0.03;

function roundCoordinate(value) {
  return Number(Number(value).toFixed(VIEWPORT_BBOX_DECIMALS));
}

export function serializeViewportBounds(bounds) {
  if (!bounds || typeof bounds.pad !== "function") {
    return "";
  }

  const paddedBounds = bounds.pad(0.12);
  const southWest = paddedBounds.getSouthWest();
  const northEast = paddedBounds.getNorthEast();

  return [
    southWest.lng,
    southWest.lat,
    northEast.lng,
    northEast.lat
  ].map((value) => roundCoordinate(value).toFixed(VIEWPORT_BBOX_DECIMALS)).join(",");
}

export function parseViewportBbox(viewportBbox) {
  if (typeof viewportBbox !== "string" || !viewportBbox.trim()) {
    return null;
  }

  const coordinates = viewportBbox
    .split(",")
    .map((item) => Number(item.trim()))
    .filter((value) => Number.isFinite(value));

  if (coordinates.length !== 4) {
    return null;
  }

  return coordinates;
}

export function isViewportBboxWithinTolerance(previousBbox, nextBbox) {
  if (previousBbox === nextBbox) {
    return true;
  }

  const previousCoordinates = parseViewportBbox(previousBbox);
  const nextCoordinates = parseViewportBbox(nextBbox);

  if (!previousCoordinates || !nextCoordinates) {
    return false;
  }

  const lngSpan = Math.max(
    Math.abs(nextCoordinates[2] - nextCoordinates[0]),
    Math.abs(previousCoordinates[2] - previousCoordinates[0])
  );
  const latSpan = Math.max(
    Math.abs(nextCoordinates[3] - nextCoordinates[1]),
    Math.abs(previousCoordinates[3] - previousCoordinates[1])
  );
  const lngTolerance = Math.max(VIEWPORT_BBOX_ABSOLUTE_TOLERANCE, lngSpan * VIEWPORT_BBOX_RELATIVE_TOLERANCE);
  const latTolerance = Math.max(VIEWPORT_BBOX_ABSOLUTE_TOLERANCE, latSpan * VIEWPORT_BBOX_RELATIVE_TOLERANCE);

  return (
    Math.abs(previousCoordinates[0] - nextCoordinates[0]) <= lngTolerance &&
    Math.abs(previousCoordinates[1] - nextCoordinates[1]) <= latTolerance &&
    Math.abs(previousCoordinates[2] - nextCoordinates[2]) <= lngTolerance &&
    Math.abs(previousCoordinates[3] - nextCoordinates[3]) <= latTolerance
  );
}

export function shouldCommitViewportChange(previousViewport, nextViewport) {
  if (!previousViewport) {
    return true;
  }

  if (previousViewport.zoom !== nextViewport.zoom) {
    return true;
  }

  return !isViewportBboxWithinTolerance(previousViewport.bbox, nextViewport.bbox);
}
