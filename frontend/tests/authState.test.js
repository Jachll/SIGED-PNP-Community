import test from "node:test";
import assert from "node:assert/strict";
import {
  buildAuthMessage,
  getAuthEventMessage,
  resolveRestoreSessionErrorState
} from "../src/auth/authState.js";

test("buildAuthMessage devuelve null cuando no hay texto", () => {
  assert.equal(buildAuthMessage(""), null);
});

test("getAuthEventMessage prioriza expiracion y permisos", () => {
  assert.deepEqual(getAuthEventMessage({ reason: "expired" }), {
    text: "Tu sesion expiro. Inicia sesion nuevamente.",
    tone: "warning"
  });

  assert.deepEqual(
    getAuthEventMessage({ status: 403, message: "No tienes permisos para completar esta accion." }),
    {
      text: "No tienes permisos para completar esta accion.",
      tone: "warning"
    }
  );
});

test("resolveRestoreSessionErrorState cierra la sesion ante 401/403", () => {
  const storedSession = {
    accessToken: "token",
    expiresAt: Date.now() + 60_000,
    user: {
      username: "consulta.qa",
      rol_codigo: "consulta"
    }
  };

  assert.deepEqual(
    resolveRestoreSessionErrorState({ status: 403, message: "Sin permisos." }, storedSession),
    {
      status: "unauthenticated",
      session: null,
      message: {
        text: "Sin permisos.",
        tone: "warning"
      }
    }
  );
});

test("resolveRestoreSessionErrorState conserva la sesion ante errores transitorios", () => {
  const storedSession = {
    accessToken: "token",
    expiresAt: Date.now() + 60_000,
    user: {
      username: "admin.qa",
      rol_codigo: "admin"
    }
  };

  assert.deepEqual(
    resolveRestoreSessionErrorState(new Error("network"), storedSession),
    {
      status: "authenticated",
      session: storedSession,
      message: {
        text: "No se pudo verificar la sesion con el backend. Reintenta si ves datos desactualizados.",
        tone: "warning"
      }
    }
  );
});
