import test from "node:test";
import assert from "node:assert/strict";
import {
  isViewportBboxWithinTolerance,
  serializeViewportBounds,
  shouldCommitViewportChange
} from "../src/utils/mapViewport.js";

function buildBounds([west, south, east, north]) {
  return {
    pad(paddingRatio) {
      const lngPad = (east - west) * paddingRatio;
      const latPad = (north - south) * paddingRatio;

      return {
        getSouthWest() {
          return { lng: west - lngPad, lat: south - latPad };
        },
        getNorthEast() {
          return { lng: east + lngPad, lat: north + latPad };
        }
      };
    }
  };
}

test("serializeViewportBounds aplica padding y cuantiza coordenadas", () => {
  const bbox = serializeViewportBounds(buildBounds([-77.1, -12.2, -76.9, -12.0]));

  assert.equal(bbox, "-77.1240,-12.2240,-76.8760,-11.9760");
});

test("isViewportBboxWithinTolerance ignora desplazamientos pequenos", () => {
  assert.equal(
    isViewportBboxWithinTolerance(
      "-77.1240,-12.2240,-76.8760,-11.9760",
      "-77.1231,-12.2232,-76.8752,-11.9751"
    ),
    true
  );
});

test("shouldCommitViewportChange exige recarga cuando cambia mucho el bbox o el zoom", () => {
  assert.equal(
    shouldCommitViewportChange(
      { zoom: 12, bbox: "-77.1240,-12.2240,-76.8760,-11.9760" },
      { zoom: 12, bbox: "-77.1150,-12.2150,-76.8670,-11.9670" }
    ),
    true
  );

  assert.equal(
    shouldCommitViewportChange(
      { zoom: 12, bbox: "-77.1240,-12.2240,-76.8760,-11.9760" },
      { zoom: 13, bbox: "-77.1235,-12.2235,-76.8765,-11.9765" }
    ),
    true
  );
});
