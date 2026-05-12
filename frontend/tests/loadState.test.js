import test from "node:test";
import assert from "node:assert/strict";
import {
  LOAD_ERROR_KIND,
  buildLoadErrorState,
  getBlockingErrorNotice
} from "../src/utils/loadState.js";

test("buildLoadErrorState diferencia permisos de errores de carga", () => {
  assert.deepEqual(
    buildLoadErrorState({ status: 403 }, "No se pudo cargar el recurso"),
    {
      kind: LOAD_ERROR_KIND.FORBIDDEN,
      tone: "warning",
      status: 403,
      message: "No tienes permisos para acceder a este recurso."
    }
  );

  assert.deepEqual(
    buildLoadErrorState({ status: 500, message: "Backend caido." }, "No se pudo cargar el recurso"),
    {
      kind: LOAD_ERROR_KIND.LOAD,
      tone: "error",
      status: 500,
      message: "Backend caido."
    }
  );
});

test("getBlockingErrorNotice devuelve copy especifico para permisos", () => {
  assert.deepEqual(
    getBlockingErrorNotice({
      kind: LOAD_ERROR_KIND.FORBIDDEN,
      message: "No tienes permisos para acceder a este recurso."
    }),
    {
      title: "Sin permisos",
      tone: "warning",
      message: "No tienes permisos para acceder a este recurso."
    }
  );
});
