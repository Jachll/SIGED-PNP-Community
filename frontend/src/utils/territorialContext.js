export const EMPTY_TERRITORIAL_CONTEXT = Object.freeze({
  regions: [],
  divisions: [],
  comisarias: [],
  jurisdicciones: [],
  sectores: []
});

function normalizeStringList(items) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items.filter((item) => typeof item === "string" && item.trim());
}

function normalizeScopedOptions(items) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .map((item) => {
      if (typeof item === "string" && item.trim()) {
        return {
          id: null,
          value: item,
          label: item,
          code: null,
          parent_id: null
        };
      }

      if (typeof item?.value !== "string" || typeof item?.label !== "string") {
        return null;
      }

      return {
        id: Number.isFinite(Number(item.id)) ? Number(item.id) : null,
        value: item.value,
        label: item.label,
        code: typeof item.code === "string" && item.code.trim() ? item.code : null,
        parent_id: Number.isFinite(Number(item.parent_id)) ? Number(item.parent_id) : null
      };
    })
    .filter(Boolean);
}

export function normalizeTerritorialContext(response) {
  return {
    regions: normalizeStringList(response?.regions),
    divisions: normalizeStringList(response?.divisions),
    comisarias: normalizeScopedOptions(response?.comisarias),
    jurisdicciones: normalizeScopedOptions(response?.jurisdicciones),
    sectores: normalizeScopedOptions(response?.sectores)
  };
}
