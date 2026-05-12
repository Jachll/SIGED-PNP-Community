export const TERRITORIAL_MODE_HIERARCHY = "hierarchy";
export const TERRITORIAL_MODE_SIMPLE = "simple";

export const ROLE_ACCESS = Object.freeze({
  admin: Object.freeze({
    label: "Administrador",
    tone: "success",
    pageIds: ["dashboard-operacional", "analisis-temporal", "analitica-operativa", "carga-datos"],
    territorialMode: TERRITORIAL_MODE_HIERARCHY
  }),
  analista: Object.freeze({
    label: "Analista",
    tone: "info",
    pageIds: ["dashboard-operacional", "analisis-temporal", "analitica-operativa", "carga-datos"],
    territorialMode: TERRITORIAL_MODE_HIERARCHY
  }),
  consulta: Object.freeze({
    label: "Consulta",
    tone: "neutral",
    pageIds: ["dashboard-operacional", "analisis-temporal"],
    territorialMode: TERRITORIAL_MODE_SIMPLE
  })
});

export const DEFAULT_ROLE_ACCESS = Object.freeze({
  label: "Sin rol",
  tone: "neutral",
  pageIds: [],
  territorialMode: TERRITORIAL_MODE_SIMPLE
});

export function getRoleAccess(roleCode) {
  return ROLE_ACCESS[roleCode] ?? DEFAULT_ROLE_ACCESS;
}
