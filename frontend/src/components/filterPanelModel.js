export function resolveFilterPanelMode(territorialMode) {
  return territorialMode === "hierarchy" ? "hierarchy" : "simple";
}

export function formatComisariaOptionLabel(comisaria) {
  if (comisaria?.region && comisaria?.division) {
    return `${comisaria.nombre} · ${comisaria.distrito || comisaria.division}`;
  }

  if (comisaria?.distrito) {
    return `${comisaria.nombre} · ${comisaria.distrito}`;
  }

  return comisaria?.nombre || "";
}
