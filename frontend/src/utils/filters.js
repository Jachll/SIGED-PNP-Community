export const INITIAL_FILTERS = Object.freeze({
  fecha_inicio: "",
  fecha_fin: "",
  id_delito: "",
  id_comisaria: "",
  region: "",
  division: "",
  comisaria: "",
  jurisdiccion: "",
  sector: ""
});

const TERRITORIAL_DEPENDENCIES = Object.freeze({
  region: ["division", "comisaria", "jurisdiccion", "sector"],
  division: ["comisaria", "jurisdiccion", "sector"],
  comisaria: ["jurisdiccion", "sector"],
  jurisdiccion: ["sector"],
  sector: []
});

export function cloneInitialFilters() {
  return { ...INITIAL_FILTERS };
}

export function isTerritorialFilterName(name) {
  return Object.prototype.hasOwnProperty.call(TERRITORIAL_DEPENDENCIES, name);
}

export function applyTerritorialFilterChange(previousFilters, name, value) {
  if (!isTerritorialFilterName(name)) {
    return {
      ...previousFilters,
      [name]: value
    };
  }

  const nextFilters = {
    ...previousFilters,
    [name]: value
  };

  if (name === "region" || name === "division" || name === "comisaria") {
    nextFilters.id_comisaria = "";
  }

  TERRITORIAL_DEPENDENCIES[name].forEach((childField) => {
    nextFilters[childField] = "";
  });

  return nextFilters;
}

export function clearTerritorialHierarchyFilters(previousFilters) {
  const nextFilters = {
    ...previousFilters,
    region: "",
    division: "",
    comisaria: "",
    jurisdiccion: "",
    sector: ""
  };

  const changed = ["region", "division", "comisaria", "jurisdiccion", "sector"].some(
    (field) => nextFilters[field] !== previousFilters[field]
  );

  return changed ? nextFilters : previousFilters;
}

export function isDateRangeValid(fechaInicio, fechaFin) {
  if (!fechaInicio || !fechaFin) {
    return true;
  }

  return new Date(fechaInicio) <= new Date(fechaFin);
}
