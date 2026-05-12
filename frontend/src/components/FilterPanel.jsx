import { formatComisariaOptionLabel, resolveFilterPanelMode } from "./filterPanelModel";

export default function FilterPanel({
  filters,
  catalogoDelitos,
  catalogoComisarias,
  onFilterChange,
  onApply,
  onClear,
  territorialContext = null,
  territorialMode = "hierarchy",
  isTerritorialLoading = false,
  territorialError = "",
  comisariaFieldName = "id_comisaria",
  disabled = false,
  busy = false,
  statusText = ""
}) {
  const selectedComisaria = filters[comisariaFieldName] ?? "";
  const hasTerritorialHierarchy = resolveFilterPanelMode(territorialMode) === "hierarchy";
  const divisions = territorialContext?.divisions ?? [];
  const comisarias = territorialContext?.comisarias ?? [];
  const jurisdicciones = territorialContext?.jurisdicciones ?? [];
  const sectores = territorialContext?.sectores ?? [];
  const territorialStatusText = isTerritorialLoading
    ? "Cargando filtros territoriales..."
    : territorialError;
  const territorialStatusRole = territorialError ? "alert" : "status";
  const territorialStatusLive = territorialError ? "assertive" : "polite";

  return (
    <>
      <div className="filtro-group">
        <label htmlFor="fecha_inicio">Fecha inicio</label>
        <input
          id="fecha_inicio"
          name="fecha_inicio"
          type="date"
          value={filters.fecha_inicio}
          disabled={disabled}
          onChange={onFilterChange}
        />
      </div>

      <div className="filtro-group">
        <label htmlFor="fecha_fin">Fecha fin</label>
        <input
          id="fecha_fin"
          name="fecha_fin"
          type="date"
          value={filters.fecha_fin}
          disabled={disabled}
          onChange={onFilterChange}
        />
      </div>

      <div className="filtro-group">
        <label htmlFor="id_delito">Tipo de delito</label>
        <select
          id="id_delito"
          name="id_delito"
          value={filters.id_delito}
          disabled={disabled}
          onChange={onFilterChange}
        >
          <option value="">Todos</option>
          {catalogoDelitos.map((delito) => (
            <option key={delito.id} value={delito.id}>
              {delito.nombre}
            </option>
          ))}
        </select>
      </div>

      {hasTerritorialHierarchy ? (
        <>
          <div className="filtro-group">
            <label htmlFor="region">Region policial</label>
            <select
              id="region"
              name="region"
              value={filters.region}
              disabled={disabled || isTerritorialLoading}
              onChange={onFilterChange}
            >
              <option value="">Todas</option>
              {(territorialContext?.regions ?? []).map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
          </div>

          <div className="filtro-group">
            <label htmlFor="division">Division policial</label>
            <select
              id="division"
              name="division"
              value={filters.division}
              disabled={disabled || isTerritorialLoading || !filters.region}
              onChange={onFilterChange}
            >
              <option value="">
                {!filters.region
                  ? "Selecciona primero una region"
                  : divisions.length
                    ? "Todas"
                    : "Sin divisiones disponibles"}
              </option>
              {divisions.map((division) => (
                <option key={division} value={division}>
                  {division}
                </option>
              ))}
            </select>
          </div>

          <div className="filtro-group">
            <label htmlFor="comisaria">Comisaria</label>
            <select
              id="comisaria"
              name="comisaria"
              value={filters.id_comisaria}
              disabled={disabled || isTerritorialLoading || !filters.region}
              onChange={onFilterChange}
            >
              <option value="">
                {!filters.region
                  ? "Selecciona primero una region"
                  : comisarias.length
                    ? "Todas"
                    : "Sin comisarias disponibles"}
              </option>
              {comisarias.map((comisaria) => (
                <option key={comisaria.id ?? comisaria.value} value={comisaria.id ?? comisaria.value}>
                  {comisaria.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filtro-group">
            <label htmlFor="jurisdiccion">Jurisdiccion de comisaria</label>
            <select
              id="jurisdiccion"
              name="jurisdiccion"
              value={filters.jurisdiccion}
              disabled={disabled || isTerritorialLoading || (!filters.comisaria && !filters.id_comisaria)}
              onChange={onFilterChange}
            >
              <option value="">
                {(!filters.comisaria && !filters.id_comisaria)
                  ? "Selecciona primero una comisaria"
                  : jurisdicciones.length
                    ? "Todas"
                    : "Sin jurisdicciones disponibles"}
              </option>
              {jurisdicciones.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filtro-group">
            <label htmlFor="sector">Sector de comisaria</label>
            <select
              id="sector"
              name="sector"
              value={filters.sector}
              disabled={disabled || isTerritorialLoading || (!filters.comisaria && !filters.id_comisaria)}
              onChange={onFilterChange}
            >
              <option value="">
                {(!filters.comisaria && !filters.id_comisaria)
                  ? "Selecciona primero una comisaria"
                  : sectores.length
                    ? "Todos"
                    : "Sin sectores disponibles"}
              </option>
              {sectores.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {territorialStatusText ? (
            <span
              className="filter-status-text"
              role={territorialStatusRole}
              aria-live={territorialStatusLive}
              aria-atomic="true"
            >
              {territorialStatusText}
            </span>
          ) : null}
        </>
      ) : (
        <>
          <div className="filtro-group">
            <label htmlFor={comisariaFieldName}>Comisaria</label>
            <select
              id={comisariaFieldName}
              name={comisariaFieldName}
              value={selectedComisaria}
              disabled={disabled}
              onChange={onFilterChange}
            >
              <option value="">Todos</option>
              {catalogoComisarias.map((comisaria) => (
                <option key={comisaria.id} value={comisaria.id}>
                  {formatComisariaOptionLabel(comisaria)}
                </option>
              ))}
            </select>
          </div>

          {territorialStatusText ? (
            <span
              className="filter-status-text"
              role={territorialStatusRole}
              aria-live={territorialStatusLive}
              aria-atomic="true"
            >
              {territorialStatusText}
            </span>
          ) : null}
        </>
      )}

      <div className="acciones filter-actions">
        <button type="button" disabled={disabled} onClick={onApply}>
          {busy ? "Actualizando..." : "Aplicar filtros"}
        </button>
        <button type="button" className="secundario" disabled={disabled} onClick={onClear}>
          Limpiar
        </button>
        {statusText ? (
          <span className="filter-status-text" role="status" aria-live="polite" aria-atomic="true">
            {statusText}
          </span>
        ) : null}
      </div>
    </>
  );
}
