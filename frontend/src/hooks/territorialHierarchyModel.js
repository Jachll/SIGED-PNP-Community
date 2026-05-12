import { TERRITORIAL_MODE_HIERARCHY, TERRITORIAL_MODE_SIMPLE } from "../config/roleAccess.js";
import { applyTerritorialFilterChange } from "../utils/filters.js";
import { EMPTY_TERRITORIAL_CONTEXT } from "../utils/territorialContext.js";

function matchesComisariaOption(option, filters) {
  const optionId = option?.id ?? option?.value ?? "";
  const selectedId = filters.id_comisaria ?? "";

  if (selectedId && String(optionId) === String(selectedId)) {
    return true;
  }

  return option?.label === filters.comisaria || option?.value === filters.comisaria;
}

export function buildTerritorialFailureState(requestError) {
  const status = requestError?.status ?? 0;

  if (status === 403) {
    return {
      mode: TERRITORIAL_MODE_SIMPLE,
      context: null,
      errorStatus: status,
      errorMessage: "La jerarquia territorial no esta disponible para tu perfil actual. Usa el filtro simple por comisaria."
    };
  }

  return {
    mode: TERRITORIAL_MODE_HIERARCHY,
    context: EMPTY_TERRITORIAL_CONTEXT,
    errorStatus: status,
    errorMessage: requestError?.message || "No se pudo cargar la jerarquia territorial."
  };
}

export function reconcileTerritorialFilters(currentFilters, context) {
  let nextFilters = currentFilters;
  const matchingComisaria = (context.comisarias ?? []).find((option) => matchesComisariaOption(option, currentFilters));

  if (currentFilters.region && !context.regions.includes(currentFilters.region)) {
    nextFilters = applyTerritorialFilterChange(nextFilters, "region", "");
  } else if (currentFilters.division && !context.divisions.includes(currentFilters.division)) {
    nextFilters = applyTerritorialFilterChange(nextFilters, "division", "");
  } else if (
    currentFilters.comisaria &&
    !matchingComisaria
  ) {
    nextFilters = applyTerritorialFilterChange(nextFilters, "comisaria", "");
  } else if (currentFilters.comisaria && !currentFilters.id_comisaria && matchingComisaria?.id) {
    nextFilters = {
      ...nextFilters,
      id_comisaria: String(matchingComisaria.id)
    };
  } else if (
    currentFilters.jurisdiccion &&
    !context.jurisdicciones.some((item) => item.value === currentFilters.jurisdiccion)
  ) {
    nextFilters = applyTerritorialFilterChange(nextFilters, "jurisdiccion", "");
  } else if (
    currentFilters.sector &&
    !context.sectores.some((item) => item.value === currentFilters.sector)
  ) {
    nextFilters = applyTerritorialFilterChange(nextFilters, "sector", "");
  }

  return nextFilters;
}
