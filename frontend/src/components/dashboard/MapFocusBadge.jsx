function getActiveTerritorialFocus(scope = {}) {
  if (scope.sector) {
    return { label: "Sector", value: scope.sector };
  }

  if (scope.jurisdiccion) {
    return { label: "Jurisdiccion", value: scope.jurisdiccion };
  }

  if (scope.comisaria || scope.id_comisaria) {
    return { label: "Comisaria", value: scope.comisaria || scope.id_comisaria };
  }

  if (scope.division) {
    return { label: "Division", value: scope.division };
  }

  if (scope.region) {
    return { label: "Region", value: scope.region };
  }

  return null;
}

export default function MapFocusBadge({
  scope,
  isPending = false
}) {
  const activeFocus = getActiveTerritorialFocus(scope);

  return (
    <div className="map-focus-badge" role="status" aria-live="polite" aria-atomic="true">
      <span className="map-focus-badge-label">Foco territorial</span>
      <strong>{activeFocus ? activeFocus.label : "Sin foco"}</strong>
      <span>{isPending ? "Actualizando contexto" : activeFocus?.value || "Seleccion libre"}</span>
    </div>
  );
}
