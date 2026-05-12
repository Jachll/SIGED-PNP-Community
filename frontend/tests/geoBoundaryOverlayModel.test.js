import test from "node:test";
import assert from "node:assert/strict";
import { getBoundaryOverlayRenderState } from "../src/components/geoBoundaryOverlayModel.js";

function buildLayer(id, overrides = {}) {
  return {
    id,
    renderData: { features: [{ id: `${id}-feature` }] },
    error: "",
    ...overrides
  };
}

test("el foco territorial no renderiza delimitacion persistente sin checkbox activo", () => {
  const focusLayer = buildLayer("sectores");
  const renderState = getBoundaryOverlayRenderState([], focusLayer);

  assert.equal(renderState.shouldRenderFocusLayer, false);
  assert.deepEqual(renderState.renderedVisibleLayers, []);
});

test("el foco solo reemplaza la capa persistente cuando el checkbox de esa capa esta activo", () => {
  const selectedLayer = buildLayer("sectores", {
    renderData: { features: [{ id: "sector-general" }] }
  });
  const focusLayer = buildLayer("sectores", {
    renderData: { features: [{ id: "sector-en-foco" }] }
  });
  const renderState = getBoundaryOverlayRenderState([selectedLayer], focusLayer);

  assert.equal(renderState.shouldRenderFocusLayer, true);
  assert.deepEqual(renderState.renderedVisibleLayers, []);
});

test("desactivar una capa elimina solo esa delimitacion persistente", () => {
  const focusLayer = buildLayer("jurisdicciones");
  const renderState = getBoundaryOverlayRenderState([], focusLayer);

  assert.equal(renderState.shouldRenderFocusLayer, false);
  assert.deepEqual(renderState.renderedVisibleLayers, []);
});

test("un foco cargado no reemplaza otras capas persistentes activas", () => {
  const visibleLayer = buildLayer("regiones");
  const focusLayer = buildLayer("sectores");
  const renderState = getBoundaryOverlayRenderState([visibleLayer], focusLayer);

  assert.equal(renderState.shouldRenderFocusLayer, false);
  assert.deepEqual(renderState.renderedVisibleLayers, [visibleLayer]);
});
