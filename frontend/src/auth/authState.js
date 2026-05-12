export function buildAuthMessage(text, tone = "info") {
  if (!text) {
    return null;
  }

  return {
    text,
    tone
  };
}

export function getAuthEventMessage(event) {
  if (event?.reason === "expired") {
    return buildAuthMessage("Tu sesion expiro. Inicia sesion nuevamente.", "warning");
  }

  if (event?.status === 403) {
    return buildAuthMessage(
      event?.message || "No tienes permisos para completar esta accion.",
      "warning"
    );
  }

  return buildAuthMessage(
    event?.message || "Tu sesion ya no es valida. Inicia sesion nuevamente.",
    "warning"
  );
}

export function resolveRestoreSessionErrorState(requestError, storedSession) {
  if (requestError?.status === 401 || requestError?.status === 403) {
    return {
      status: "unauthenticated",
      session: null,
      message: buildAuthMessage(
        requestError.message || "Tu sesion ya no es valida. Inicia sesion nuevamente.",
        "warning"
      )
    };
  }

  return {
    status: "authenticated",
    session: storedSession,
    message: buildAuthMessage(
      "No se pudo verificar la sesion con el backend. Reintenta si ves datos desactualizados.",
      "warning"
    )
  };
}
