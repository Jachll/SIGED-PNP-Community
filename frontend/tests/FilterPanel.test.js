import test from "node:test";
import assert from "node:assert/strict";
import {
  formatComisariaOptionLabel,
  resolveFilterPanelMode
} from "../src/components/filterPanelModel.js";

test("resolveFilterPanelMode expone solo dos modos canonicos", () => {
  assert.equal(resolveFilterPanelMode("hierarchy"), "hierarchy");
  assert.equal(resolveFilterPanelMode("simple"), "simple");
  assert.equal(resolveFilterPanelMode("otro"), "simple");
});

test("formatComisariaOptionLabel muestra el distrito cuando esta disponible", () => {
  assert.equal(
    formatComisariaOptionLabel({
      nombre: "Comisaria Centro",
      distrito: "Distrito Demo Centro"
    }),
    "Comisaria Centro · Distrito Demo Centro"
  );
});

test("formatComisariaOptionLabel cae al nombre simple cuando no hay contexto", () => {
  assert.equal(formatComisariaOptionLabel({ nombre: "Comisaria Norte" }), "Comisaria Norte");
});
