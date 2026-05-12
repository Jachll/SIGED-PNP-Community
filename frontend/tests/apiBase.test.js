import test from "node:test";
import assert from "node:assert/strict";
import { resolveApiBaseUrl } from "../src/services/apiBase.js";

test("usa same-origin en produccion cuando no se define VITE_API_BASE_URL", () => {
  assert.equal(resolveApiBaseUrl("", { isDev: false }), "");
});

test("mantiene fallback local en desarrollo cuando no hay variable definida", () => {
  assert.equal(resolveApiBaseUrl("", { isDev: true }), "http://localhost:8000");
});

test("respeta una URL explicita de API", () => {
  assert.equal(resolveApiBaseUrl("https://api.siged.example", { isDev: false }), "https://api.siged.example");
});
