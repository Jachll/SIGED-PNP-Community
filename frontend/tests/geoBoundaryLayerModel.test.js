import test from "node:test";
import assert from "node:assert/strict";
import {
  buildLayerRetentionKey,
  buildLayerRequestKey,
  clearLayerLoadingState,
  findLayerCacheEntry,
  getDefaultDetailForLayer,
  getScopedLayerDetail,
  getViewportBboxForLayer,
  removeLayerCacheEntry,
  resolveRenderableLayerCacheEntry,
  shouldRetainStaleGeometry,
  upsertLayerCacheEntry
} from "../src/hooks/geoBoundaryLayerModel.js";

test("getViewportBboxForLayer restringe bbox a jurisdicciones y sectores", () => {
  assert.equal(getViewportBboxForLayer("regiones", "-77.1,-12.2,-76.9,-12.0"), "");
  assert.equal(getViewportBboxForLayer("divisiones", "-77.1,-12.2,-76.9,-12.0"), "");
  assert.equal(getViewportBboxForLayer("comisarias", "-77.1,-12.2,-76.9,-12.0"), "");
  assert.equal(
    getViewportBboxForLayer("jurisdicciones", "-77.1,-12.2,-76.9,-12.0"),
    "-77.1,-12.2,-76.9,-12.0"
  );
  assert.equal(
    getViewportBboxForLayer("sectores", "-77.1,-12.2,-76.9,-12.0"),
    "-77.1,-12.2,-76.9,-12.0"
  );
  assert.equal(
    getViewportBboxForLayer("sectores", "-77.1,-12.2,-76.9,-12.0", { isViewportAligned: false }),
    ""
  );
});

test("buildLayerRequestKey distingue la comisaria por id y buildLayerRetentionKey ignora bbox", () => {
  assert.equal(
    buildLayerRequestKey("divisiones", {
      region: "REGION DEMO",
      division: "DIVISION DEMO CENTRO",
      detail: "simplified"
    }),
    "divisiones::REGION DEMO::DIVISION DEMO CENTRO::::::::::::simplified"
  );

  assert.equal(
    buildLayerRequestKey("sectores", {
      region: "REGION DEMO",
      division: "DIVISION DEMO CENTRO",
      comisaria_id: "39",
      comisaria: "COMISARIA DEMO SUR",
      sector: "S-1",
      bbox: "-77.1,-12.2,-76.9,-12.0",
      detail: "full"
    }),
    "sectores::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::S-1::-77.1,-12.2,-76.9,-12.0::full"
  );

  assert.equal(
    buildLayerRetentionKey("sectores", {
      region: "REGION DEMO",
      division: "DIVISION DEMO CENTRO",
      comisaria_id: "39",
      comisaria: "COMISARIA DEMO SUR",
      sector: "S-1",
      bbox: "-77.1,-12.2,-76.9,-12.0",
      detail: "full"
    }),
    "sectores::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::S-1"
  );
});

test("getDefaultDetailForLayer retrasa el salto a full en capas poligonales", () => {
  assert.equal(getDefaultDetailForLayer("regiones", { viewportZoom: 11 }), "simplified");
  assert.equal(getDefaultDetailForLayer("regiones", { viewportZoom: 12 }), "full");
  assert.equal(getDefaultDetailForLayer("divisiones", { viewportZoom: 12 }), "simplified");
  assert.equal(getDefaultDetailForLayer("divisiones", { viewportZoom: 13 }), "full");
  assert.equal(getDefaultDetailForLayer("jurisdicciones", { viewportZoom: 14 }), "simplified");
  assert.equal(getDefaultDetailForLayer("jurisdicciones", { viewportZoom: 15 }), "full");
  assert.equal(getDefaultDetailForLayer("sectores", { viewportZoom: 15 }), "simplified");
  assert.equal(getDefaultDetailForLayer("sectores", { viewportZoom: 16 }), "full");
  assert.equal(getDefaultDetailForLayer("comisarias", { viewportZoom: 20 }), "full");
  assert.equal(getDefaultDetailForLayer("sectores", { isFocus: true, viewportZoom: 10 }), "full");
});

test("getScopedLayerDetail mantiene simplificado cuando jurisdiccion o sector estan en Todas", () => {
  assert.equal(
    getScopedLayerDetail("jurisdicciones", { comisaria: "COMISARIA DEMO PUERTO", jurisdiccion: "" }, 18),
    "simplified"
  );
  assert.equal(
    getScopedLayerDetail("sectores", { comisaria: "COMISARIA DEMO PUERTO", sector: "" }, 18),
    "simplified"
  );
  assert.equal(
    getScopedLayerDetail("jurisdicciones", { comisaria: "COMISARIA DEMO PUERTO", jurisdiccion: "J-1" }, 15),
    "full"
  );
  assert.equal(
    getScopedLayerDetail("sectores", { comisaria: "COMISARIA DEMO PUERTO", sector: "S-1" }, 16),
    "full"
  );
});

test("upsertLayerCacheEntry mantiene un LRU pequeno por capa", () => {
  let cache = {};

  cache = upsertLayerCacheEntry(cache, "sectores", {
    requestKey: "sectores::1",
    value: { features: [1] }
  });
  cache = upsertLayerCacheEntry(cache, "sectores", {
    requestKey: "sectores::2",
    value: { features: [2] }
  });
  cache = upsertLayerCacheEntry(cache, "sectores", {
    requestKey: "sectores::3",
    value: { features: [3] }
  });

  assert.deepEqual(cache, {
    sectores: [
      { requestKey: "sectores::3", value: { features: [3] } },
      { requestKey: "sectores::2", value: { features: [2] } }
    ]
  });
  assert.equal(findLayerCacheEntry(cache, "sectores", "sectores::2")?.value.features[0], 2);
  assert.equal(findLayerCacheEntry(cache, "sectores", "sectores::1"), null);
});

test("resolveRenderableLayerCacheEntry conserva la geometria previa mientras llega la nueva", () => {
  const cache = {
    sectores: [
      {
        requestKey: "sectores::viewport-nuevo",
        retentionKey: "sectores::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
        value: { features: ["nuevo"] }
      },
      {
        requestKey: "sectores::viewport-anterior",
        retentionKey: "sectores::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
        value: { features: ["anterior"] }
      }
    ],
    jurisdicciones: [
      {
        requestKey: "jurisdicciones::viewport-anterior",
        retentionKey: "jurisdicciones::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
        value: { features: ["anterior"] }
      }
    ]
  };

  assert.deepEqual(
    resolveRenderableLayerCacheEntry(
      cache,
      "sectores",
      "sectores::viewport-nuevo",
      "sectores::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
      false
    ),
    {
      requestKey: "sectores::viewport-nuevo",
      retentionKey: "sectores::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
      value: { features: ["nuevo"] }
    }
  );
  assert.deepEqual(
    resolveRenderableLayerCacheEntry(
      cache,
      "jurisdicciones",
      "jurisdicciones::viewport-nuevo",
      "jurisdicciones::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
      false
    ),
    {
      requestKey: "jurisdicciones::viewport-anterior",
      retentionKey: "jurisdicciones::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
      value: { features: ["anterior"] }
    }
  );
  assert.equal(
    resolveRenderableLayerCacheEntry(
      cache,
      "jurisdicciones",
      "jurisdicciones::viewport-nuevo",
      "jurisdicciones::REGION DEMO::DIVISION DEMO CENTRO::39::COMISARIA DEMO SUR::::",
      true
    ),
    null
  );
  assert.equal(
    resolveRenderableLayerCacheEntry(
      cache,
      "jurisdicciones",
      "jurisdicciones::otra-comisaria",
      "jurisdicciones::REGION DEMO::DIVISION DEMO CENTRO::41::COMISARIA DEMO NORTE::::",
      false
    ),
    null
  );
});

test("shouldRetainStaleGeometry conserva fondo pero no inmoviliza comisarias", () => {
  assert.equal(shouldRetainStaleGeometry("jurisdicciones"), true);
  assert.equal(shouldRetainStaleGeometry("sectores"), true);
  assert.equal(shouldRetainStaleGeometry("comisarias"), false);
});

test("removeLayerCacheEntry y clearLayerLoadingState limpian solo la request activa", () => {
  const cache = {
    sectores: [
      { requestKey: "sectores::2", value: { features: [2] } },
      { requestKey: "sectores::1", value: { features: [1] } }
    ]
  };

  assert.deepEqual(removeLayerCacheEntry(cache, "sectores", "sectores::2"), {
    sectores: [{ requestKey: "sectores::1", value: { features: [1] } }]
  });

  assert.deepEqual(
    clearLayerLoadingState(
      {
        sectores: "sectores::2",
        jurisdicciones: "jurisdicciones::1"
      },
      "sectores",
      "sectores::2"
    ),
    {
      jurisdicciones: "jurisdicciones::1"
    }
  );
});
