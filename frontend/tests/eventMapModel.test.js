import test from "node:test";
import assert from "node:assert/strict";
import { getRenderableEventMarkers } from "../src/components/eventMapModel.js";

test("los puntos de incidencia dependen solo de eventos, no de capas visibles", () => {
  const eventos = [
    { id_evento: 101, latitud: -9.1, longitud: -78.5 },
    { id_evento: 102, latitud: -9.2, longitud: -78.6 }
  ];
  const boundaryState = {
    visibleLayers: [],
    focusLayer: {
      id: "sectores",
      renderData: { features: [{ id: "sector-en-foco" }] }
    }
  };

  assert.equal(getRenderableEventMarkers(eventos, boundaryState), eventos);
  assert.deepEqual(getRenderableEventMarkers(eventos, boundaryState).map((evento) => evento.id_evento), [101, 102]);
});

test("desactivar delimitaciones persistentes no elimina puntos de incidencia", () => {
  const eventos = [
    { id_evento: 201, latitud: -9.3, longitud: -78.7 },
    { id_evento: 202, latitud: -9.4, longitud: -78.8 }
  ];
  const markersBeforeLayerToggle = getRenderableEventMarkers(eventos, {
    visibleLayers: [{ id: "jurisdicciones" }]
  });
  const markersAfterLayerToggle = getRenderableEventMarkers(eventos, {
    visibleLayers: []
  });

  assert.deepEqual(markersAfterLayerToggle, markersBeforeLayerToggle);
});
