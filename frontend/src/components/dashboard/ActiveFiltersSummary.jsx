function findById(items = [], id) {
  return items.find((item) => String(item.id) === String(id));
}

function getTerritorialChip(filters, selectedComisaria) {
  const levels = [
    { label: "Región", value: filters.region },
    { label: "División", value: filters.division },
    { label: "Comisaría", value: filters.comisaria || selectedComisaria?.nombre || filters.id_comisaria },
    { label: "Jurisdicción", value: filters.jurisdiccion },
    { label: "Sector", value: filters.sector }
  ].filter((level) => Boolean(level.value));

  if (!levels.length) {
    return null;
  }

  const activeLevel = levels[levels.length - 1];

  return {
    key: "territorio",
    label: "Territorio",
    value: activeLevel.value,
    title: levels.map((level) => `${level.label}: ${level.value}`).join(" / ")
  };
}

function buildFilterChips(filters, catalogoDelitos, catalogoComisarias) {
  const chips = [];
  const selectedDelito = filters.id_delito ? findById(catalogoDelitos, filters.id_delito) : null;
  const selectedComisaria = filters.id_comisaria ? findById(catalogoComisarias, filters.id_comisaria) : null;
  const territorialChip = getTerritorialChip(filters, selectedComisaria);

  if (filters.fecha_inicio) {
    chips.push({ key: "fecha_inicio", label: "Desde", value: filters.fecha_inicio });
  }

  if (filters.fecha_fin) {
    chips.push({ key: "fecha_fin", label: "Hasta", value: filters.fecha_fin });
  }

  if (filters.id_delito) {
    chips.push({ key: "id_delito", label: "Delito", value: selectedDelito?.nombre || filters.id_delito });
  }

  if (territorialChip) {
    chips.push(territorialChip);
  }

  return chips;
}

export default function ActiveFiltersSummary({
  filters,
  catalogoDelitos = [],
  catalogoComisarias = [],
  heatmapEnabled = false,
  isRefreshing = false
}) {
  const chips = buildFilterChips(filters, catalogoDelitos, catalogoComisarias);

  return (
    <div className="active-filters-summary" aria-label="Filtros Activos">
      <div className="active-filters-summary-copy">
        <strong>Filtros Activos</strong>
        <span>{isRefreshing ? "Actualizando lectura operacional" : "Eventos, territorio y mapa de calor"}</span>
      </div>
      <div className="active-filter-chips">
        {chips.length ? (
          chips.map((chip) => (
            <span className="active-filter-chip" key={chip.key} title={chip.title || `${chip.label}: ${chip.value}`}>
              <span>{chip.label}</span>
              <strong>{chip.value}</strong>
            </span>
          ))
        ) : (
          <span className="active-filter-chip muted">
            <span>Alcance</span>
            <strong>Sin filtros activos</strong>
          </span>
        )}
        <span className={`active-filter-chip ${heatmapEnabled ? "accent" : "muted"}`}>
          <span>Heatmap</span>
          <strong>{heatmapEnabled ? "Activo" : "Inactivo"}</strong>
        </span>
      </div>
    </div>
  );
}
