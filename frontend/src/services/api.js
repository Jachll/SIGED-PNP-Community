import {
  clearStoredAuthSession,
  isAuthSessionExpired,
  readStoredAuthSession
} from "../auth/storage";
import { resolveApiBaseUrl } from "./apiBase";
import { normalizeTerritorialContext } from "../utils/territorialContext";

const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL, {
  isDev: import.meta.env.DEV
});
const TERRITORY_LAYER_GEOJSON_PATHS = Object.freeze({
  regiones: "/territorio/regiones/geojson",
  divisiones: "/territorio/divisiones/geojson",
  comisarias: "/territorio/comisarias/geojson",
  jurisdicciones: "/territorio/jurisdicciones/geojson",
  sectores: "/territorio/sectores/geojson"
});

const authEventListeners = new Set();
let diagnosticRequestSequence = 0;

export class ApiError extends Error {
  constructor(message, { status = 0, path = "", payload = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.path = path;
    this.payload = payload;
  }
}

function buildQuery(filters = {}) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      params.append(key, value);
    }
  });

  const query = params.toString();
  return query ? `?${query}` : "";
}

function emitAuthEvent(event) {
  authEventListeners.forEach((listener) => {
    try {
      listener(event);
    } catch {
      // noop: los listeners no deben romper el cliente HTTP
    }
  });
}

function getUnauthorizedError(message, path, reason = "rejected") {
  return new ApiError(message, {
    status: 401,
    path,
    payload: { reason }
  });
}

function getStoredToken(path) {
  const session = readStoredAuthSession();

  if (!session) {
    throw getUnauthorizedError("Debes iniciar sesion para continuar.", path, "missing");
  }

  if (isAuthSessionExpired(session)) {
    clearStoredAuthSession();
    emitAuthEvent({
      status: 401,
      reason: "expired",
      path,
      message: "Tu sesion expiro. Inicia sesion nuevamente."
    });
    throw getUnauthorizedError("Tu sesion expiro. Inicia sesion nuevamente.", path, "expired");
  }

  return session.accessToken;
}

function getErrorMessage(status, payload, fallbackMessage, path = "") {
  const detail = typeof payload?.detail === "string" ? payload.detail.trim() : "";
  const normalizedDetail = detail.toLowerCase();

  if (
    normalizedDetail.includes("subsistema de autenticacion") ||
    normalizedDetail.includes("tablas de autenticacion")
  ) {
    return "Faltan las migraciones de autenticacion en la base activa. Ejecuta 11_auth_minima.sql y vuelve a intentarlo.";
  }

  if (normalizedDetail.includes("subsistema de cargas")) {
    return "Faltan las migraciones de cargas en la base activa. Ejecuta 06_lotes_staging.sql y 07_eventos_lote_fk.sql.";
  }

  if (normalizedDetail.includes("postgis") || normalizedDetail.includes("postgresql")) {
    return "El backend no pudo validar PostgreSQL/PostGIS. Revisa DB_* y ejecuta 02_enable_postgis.sql si corresponde.";
  }

  if (
    (status === 500 || status === 503) &&
    pathSupportsAnalytics(path)
  ) {
    return "La base activa no tiene completo el esquema analitico requerido. Revisa 08_zonas_operativas.sql, 09_hotspots.sql, 10_recomendaciones_patrullaje.sql, 13_dim_territorio.sql y 14_performance_territorial.sql.";
  }

  if (typeof payload?.detail === "string" && payload.detail.trim()) {
    return payload.detail;
  }

  if (status === 401) {
    return "Tu sesion ya no es valida. Inicia sesion nuevamente.";
  }

  if (status === 403) {
    return "No tienes permisos para acceder a este recurso.";
  }

  return fallbackMessage || "No se pudo completar la solicitud";
}

function pathSupportsAnalytics(path) {
  return typeof path === "string" && ["/eventos", "/estadisticas", "/analisis", "/recomendaciones"].some((prefix) => path.startsWith(prefix));
}

function shouldLogDiagnosticRequest(path) {
  return typeof path === "string" && ["/territorio", "/eventos", "/estadisticas", "/analisis", "/recomendaciones"].some((prefix) => path.startsWith(prefix));
}

function logDiagnosticRequest(event, payload = {}) {
  console.info("[api-diagnostic]", {
    event,
    ...payload
  });
}

async function parsePayload(response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  if (response.status === 204) {
    return null;
  }

  try {
    const text = await response.text();
    return text ? { detail: text } : null;
  } catch {
    return null;
  }
}

async function apiRequest(
  path,
  { filters, errorMessage, method = "GET", body, headers: customHeaders = {}, requiresAuth = true, signal } = {}
) {
  const headers = { ...customHeaders };
  const requestId = `${Date.now()}-${++diagnosticRequestSequence}`;
  const fullPath = `${path}${buildQuery(filters)}`;
  const shouldLog = shouldLogDiagnosticRequest(path);

  if (requiresAuth) {
    headers.Authorization = `Bearer ${getStoredToken(path)}`;
  }

  const requestBody = body && !(body instanceof FormData) ? JSON.stringify(body) : body;

  if (requestBody && !(body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (shouldLog) {
    logDiagnosticRequest("request_started", {
      requestId,
      method,
      path,
      fullPath,
      filters: filters ?? null
    });
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${fullPath}`, {
      method,
      headers,
      body: requestBody,
      signal
    });
  } catch (requestError) {
    if (shouldLog) {
      logDiagnosticRequest("request_failed", {
        requestId,
        method,
        path,
        fullPath,
        errorName: requestError?.name || "Error",
        errorMessage: requestError?.message || "No request error message"
      });
    }
    throw requestError;
  }

  if (shouldLog) {
    logDiagnosticRequest("request_completed", {
      requestId,
      method,
      path,
      fullPath,
      status: response.status
    });
  }

  const payload = await parsePayload(response);

  if (!response.ok) {
    const message = getErrorMessage(response.status, payload, errorMessage, path);
    const error = new ApiError(message, {
      status: response.status,
      path,
      payload
    });

    if (response.status === 401 || response.status === 403) {
      if (response.status === 401) {
        clearStoredAuthSession();
      }

      emitAuthEvent({
        status: response.status,
        reason: response.status === 401 ? "rejected" : "forbidden",
        path,
        message
      });

      throw error;
    }

    throw error;
  }

  return payload;
}

export function subscribeToAuthEvents(listener) {
  authEventListeners.add(listener);

  return () => {
    authEventListeners.delete(listener);
  };
}

export async function loginRequest(credentials) {
  return apiRequest("/auth/login", {
    method: "POST",
    body: credentials,
    requiresAuth: false,
    errorMessage: "No se pudo iniciar sesion"
  });
}

export async function fetchCurrentUser() {
  return apiRequest("/auth/me", {
    errorMessage: "No se pudo verificar la sesion"
  });
}

export async function fetchEventos(filters = {}, options = {}) {
  return apiRequest("/eventos", {
    filters,
    signal: options.signal,
    errorMessage: "No se pudo obtener eventos"
  });
}

export async function fetchHeatmap(filters = {}, options = {}) {
  return apiRequest("/eventos/heatmap", {
    filters,
    signal: options.signal,
    errorMessage: "No se pudo obtener datos de heatmap"
  });
}

export async function fetchEventoDetalle(idEvento, filters = {}) {
  return apiRequest(`/eventos/${idEvento}`, {
    filters,
    errorMessage: "No se pudo obtener el detalle del evento"
  });
}

export async function fetchEstadisticasPorHora(filters = {}, options = {}) {
  return apiRequest("/estadisticas/por-hora", {
    filters,
    signal: options.signal,
    errorMessage: "No se pudo obtener estadisticas por hora"
  });
}

export async function fetchEstadisticasPorDia(filters = {}) {
  return apiRequest("/estadisticas/por-dia", {
    filters,
    errorMessage: "No se pudo obtener estadisticas por dia"
  });
}

export async function fetchEstadisticasPorMes(filters = {}) {
  return apiRequest("/estadisticas/por-mes", {
    filters,
    errorMessage: "No se pudo obtener estadisticas por mes"
  });
}

export async function fetchEstadisticasPorDiaSemana(filters = {}) {
  return apiRequest("/estadisticas/por-dia-semana", {
    filters,
    errorMessage: "No se pudo obtener estadisticas por dia de semana"
  });
}

export async function fetchCatalogoDelitos() {
  return apiRequest("/catalogos/delitos", {
    errorMessage: "No se pudo obtener el catalogo de delitos"
  });
}

export async function fetchCatalogoDistritos() {
  return apiRequest("/catalogos/distritos", {
    errorMessage: "No se pudo obtener el catalogo de distritos"
  });
}

export async function fetchCatalogoComisarias() {
  return apiRequest("/catalogos/comisarias", {
    errorMessage: "No se pudo obtener el catalogo de comisarias"
  });
}

export async function fetchHealth() {
  return apiRequest("/health", {
    requiresAuth: false,
    errorMessage: "No se pudo obtener el estado del backend"
  });
}

export async function fetchTerritoryLayersCatalog() {
  return apiRequest("/territorio/capas", {
    errorMessage: "No se pudo obtener el catalogo territorial"
  });
}

export async function fetchTerritoryRegions() {
  return apiRequest("/territorio/regiones", {
    errorMessage: "No se pudo obtener la lista de regiones policiales"
  });
}

export async function fetchTerritoryDivisions(filters = {}) {
  return apiRequest("/territorio/divisiones", {
    filters,
    errorMessage: "No se pudo obtener la lista de divisiones policiales"
  });
}

export async function fetchTerritoryComisarias(filters = {}) {
  return apiRequest("/territorio/comisarias", {
    filters,
    errorMessage: "No se pudo obtener la lista de comisarias"
  });
}

export async function fetchTerritoryJurisdicciones(filters = {}) {
  return apiRequest("/territorio/jurisdicciones", {
    filters,
    errorMessage: "No se pudo obtener la lista de jurisdicciones"
  });
}

export async function fetchTerritorySectores(filters = {}) {
  return apiRequest("/territorio/sectores", {
    filters,
    errorMessage: "No se pudo obtener la lista de sectores"
  });
}

export async function fetchTerritoryContext(filters = {}, options = {}) {
  const response = await apiRequest("/territorio/contexto", {
    filters: {
      region: filters.region,
      division: filters.division,
      comisaria_id: filters.comisaria_id,
      comisaria: filters.comisaria
    },
    signal: options.signal,
    errorMessage: "No se pudo cargar la jerarquia territorial"
  });

  return normalizeTerritorialContext(response);
}

export async function fetchTerritoryLayerData(layerId, filters = {}, options = {}) {
  const path = TERRITORY_LAYER_GEOJSON_PATHS[layerId] ?? `/territorio/capas/${layerId}`;

  return apiRequest(path, {
    filters,
    signal: options.signal,
    errorMessage: `No se pudo obtener la capa territorial ${layerId}`
  });
}

export async function fetchGeoLayersCatalog() {
  return fetchTerritoryLayersCatalog();
}

export async function fetchGeoLayerContext(filters = {}) {
  return fetchTerritoryContext(filters);
}

export async function fetchGeoLayerData(layerId, filters = {}) {
  return fetchTerritoryLayerData(layerId, filters);
}

export async function fetchLotesCarga({ estado, limite = 15 } = {}) {
  return apiRequest("/cargas/lotes", {
    filters: { estado, limite },
    errorMessage: "No se pudo obtener el historial de lotes"
  });
}

export async function fetchLoteCarga(idLote) {
  return apiRequest(`/cargas/lotes/${idLote}`, {
    errorMessage: `No se pudo obtener el lote ${idLote}`
  });
}

export async function uploadLoteCarga({ archivo, sheet, observaciones }) {
  const formData = new FormData();
  formData.append("archivo", archivo);

  if (sheet?.trim()) {
    formData.append("sheet", sheet.trim());
  }

  if (observaciones?.trim()) {
    formData.append("observaciones", observaciones.trim());
  }

  return apiRequest("/cargas/lotes", {
    method: "POST",
    body: formData,
    errorMessage: "No se pudo procesar el archivo de carga"
  });
}

export async function fetchCatalogosFiltros() {
  const [delitos, comisarias] = await Promise.all([fetchCatalogoDelitos(), fetchCatalogoComisarias()]);

  return {
    delitos: delitos
      .map((item) => ({
        id: item.id_delito,
        nombre: item.nombre_delito
      }))
      .sort((a, b) => a.nombre.localeCompare(b.nombre)),
    comisarias: comisarias
      .map((item) => ({
        id: item.id_comisaria,
        nombre: item.nombre_comisaria,
        distrito: item.distrito,
        direccion: item.direccion ?? ""
      }))
      .sort((a, b) => {
        const districtComparison = (a.distrito || "").localeCompare(b.distrito || "");
        return districtComparison || a.nombre.localeCompare(b.nombre);
      })
  };
}

export async function fetchRecomendacionesPatrullaje(filters = {}) {
  return apiRequest("/recomendaciones/patrullaje", {
    filters,
    errorMessage: "No se pudo obtener recomendaciones de patrullaje"
  });
}

export async function generarRecomendacionesPatrullaje(payload) {
  return apiRequest("/recomendaciones/patrullaje/generar", {
    method: "POST",
    body: payload,
    errorMessage: "No se pudo generar recomendaciones de patrullaje"
  });
}

export async function fetchDashboardOperacional(filters = {}, options = {}) {
  const [eventos, heatmap, statsPorHora] = await Promise.all([
    fetchEventos(filters, options),
    fetchHeatmap(filters, options),
    fetchEstadisticasPorHora(filters, options)
  ]);

  return {
    eventos,
    heatmap,
    statsPorHora
  };
}

export async function fetchAnalisisTemporal(filters = {}) {
  const [statsPorHora, statsPorDia, statsPorMes, statsPorDiaSemana] = await Promise.all([
    fetchEstadisticasPorHora(filters),
    fetchEstadisticasPorDia(filters),
    fetchEstadisticasPorMes(filters),
    fetchEstadisticasPorDiaSemana(filters)
  ]);

  return {
    statsPorHora,
    statsPorDia,
    statsPorMes,
    statsPorDiaSemana
  };
}

export async function fetchHotspots(filters = {}) {
  return apiRequest("/analisis/hotspots", {
    filters,
    errorMessage: "No se pudo obtener hotspots operativos"
  });
}

export async function fetchZonasCriticas(filters = {}) {
  return apiRequest("/analisis/zonas-criticas", {
    filters,
    errorMessage: "No se pudo obtener zonas criticas"
  });
}

export async function fetchAnaliticaOperativa(filters = {}, options = {}) {
  const {
    estado_hotspot = "ACTIVO",
    agrupado_por = "distrito",
    min_eventos_zona = 3,
    turno = "",
    fecha_operativa = "",
    limite_hotspots = 12,
    limite_zonas = 8,
    limite_recomendaciones = 6
  } = options;

  const baseFilters = {
    fecha_inicio: filters.fecha_inicio,
    fecha_fin: filters.fecha_fin,
    id_delito: filters.id_delito,
    id_comisaria: filters.id_comisaria,
    region: filters.region,
    division: filters.division,
    comisaria: filters.comisaria,
    jurisdiccion: filters.jurisdiccion,
    sector: filters.sector
  };

  const moduleRequests = [
    {
      key: "hotspots",
      label: "hotspots",
      fallbackValue: [],
      request: () =>
        fetchHotspots({
          ...baseFilters,
          estado: estado_hotspot,
          limite: limite_hotspots
        })
    },
    {
      key: "zonasCriticas",
      label: "zonas criticas",
      fallbackValue: [],
      request: () =>
        fetchZonasCriticas({
          ...baseFilters,
          agrupado_por,
          min_eventos: min_eventos_zona,
          limite: limite_zonas
        })
    },
    {
      key: "recomendaciones",
      label: "recomendaciones de patrullaje",
      fallbackValue: null,
      request: () =>
        fetchRecomendacionesPatrullaje({
          ...baseFilters,
          fecha_operativa,
          turno,
          limite: limite_recomendaciones
        })
    }
  ];

  const settledResults = await Promise.allSettled(moduleRequests.map((moduleRequest) => moduleRequest.request()));
  const analytics = {
    hotspots: [],
    zonasCriticas: [],
    recomendaciones: null,
    moduleErrors: []
  };

  settledResults.forEach((result, index) => {
    const moduleRequest = moduleRequests[index];

    if (result.status === "fulfilled") {
      analytics[moduleRequest.key] = result.value;
      return;
    }

    analytics[moduleRequest.key] = moduleRequest.fallbackValue;
    analytics.moduleErrors.push({
      key: moduleRequest.key,
      label: moduleRequest.label,
      message: result.reason?.message || `No se pudo cargar ${moduleRequest.label}.`,
      status: result.reason?.status ?? 0
    });
  });

  if (analytics.moduleErrors.length === moduleRequests.length) {
    throw settledResults.find((result) => result.status === "rejected")?.reason;
  }

  return analytics;
}

export { API_BASE_URL };
