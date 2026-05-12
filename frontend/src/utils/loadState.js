export const LOAD_ERROR_KIND = Object.freeze({
  FORBIDDEN: "forbidden",
  LOAD: "load_error"
});

export function buildLoadErrorState(requestError, fallbackMessage, {
  forbiddenMessage = "No tienes permisos para acceder a este recurso."
} = {}) {
  const status = requestError?.status ?? 0;

  if (status === 403) {
    return {
      kind: LOAD_ERROR_KIND.FORBIDDEN,
      tone: "warning",
      status,
      message: requestError?.message || forbiddenMessage
    };
  }

  return {
    kind: LOAD_ERROR_KIND.LOAD,
    tone: "error",
    status,
    message: requestError?.message || fallbackMessage
  };
}

export function getBlockingErrorNotice(errorState, fallbackTitle = "Error de carga") {
  if (!errorState?.message) {
    return null;
  }

  if (errorState.kind === LOAD_ERROR_KIND.FORBIDDEN) {
    return {
      title: "Sin permisos",
      tone: "warning",
      message: errorState.message
    };
  }

  return {
    title: fallbackTitle,
    tone: "warning",
    message: errorState.message
  };
}
