import test from "node:test";
import assert from "node:assert/strict";
import {
  TERRITORIAL_MODE_HIERARCHY,
  TERRITORIAL_MODE_SIMPLE,
  getRoleAccess
} from "../src/config/roleAccess.js";

test("consulta queda limitada a vistas de lectura con fallback simple territorial", () => {
  const access = getRoleAccess("consulta");

  assert.deepEqual(access.pageIds, ["dashboard-operacional", "analisis-temporal"]);
  assert.equal(access.territorialMode, TERRITORIAL_MODE_SIMPLE);
});

test("admin mantiene vistas operativas y jerarquia territorial", () => {
  const access = getRoleAccess("admin");

  assert.deepEqual(access.pageIds, [
    "dashboard-operacional",
    "analisis-temporal",
    "analitica-operativa",
    "carga-datos"
  ]);
  assert.equal(access.territorialMode, TERRITORIAL_MODE_HIERARCHY);
});
