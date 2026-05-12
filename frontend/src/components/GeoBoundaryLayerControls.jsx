function formatFileSize(sizeBytes) {
  const size = Number(sizeBytes || 0);

  if (!Number.isFinite(size) || size <= 0) {
    return "";
  }

  if (size >= 1024 * 1024 * 1024) {
    return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function getScopeSummary(scope) {
  if (scope.sector) {
    return `Alcance: ${getScopePath(scope)}`;
  }

  if (scope.jurisdiccion) {
    return `Alcance: ${getScopePath(scope)}`;
  }

  if (scope.comisaria || scope.id_comisaria) {
    return `Alcance: ${getScopePath(scope)}`;
  }

  if (scope.division) {
    return `Alcance: ${getScopePath(scope)}`;
  }

  if (scope.region) {
    return `Alcance: ${getScopePath(scope)}`;
  }

  return "Selecciona una región policial para iniciar.";
}

function getLoadingSummary(scope) {
  if (!scope.region) {
    return "Cargando filtros territoriales: regiones...";
  }

  if (!scope.comisaria && !scope.id_comisaria) {
    return "Cargando filtros territoriales: divisiones y comisarías...";
  }

  return "Cargando filtros territoriales: jurisdicciones y sectores...";
}

function getScopePath(scope) {
  const segments = [
    scope.region,
    scope.division,
    scope.comisaria,
    scope.jurisdiccion,
    scope.sector
  ].filter(Boolean);

  return segments.length ? segments.join(" / ") : "Sin región seleccionada";
}

function getFieldClassName(isLocked, hasValue) {
  return [
    "filtro-group",
    "geo-scope-field",
    isLocked ? "locked" : "ready",
    hasValue ? "selected" : ""
  ].filter(Boolean).join(" ");
}

function getLayerDisabledSummary(layer) {
  const reason = layer.disabledReason.toLowerCase();

  if (reason.includes("comisaria") || reason.includes("comisaría")) {
    return "Requiere comisaría";
  }

  if (reason.includes("region") || reason.includes("región")) {
    return "Requiere región";
  }

  return "No disponible";
}

function getLayerDisabledTitle(layer) {
  const reason = layer.disabledReason.toLowerCase();

  if (reason.includes("comisaria") || reason.includes("comisaría")) {
    return "Selecciona una comisaría para habilitar esta capa.";
  }

  if (reason.includes("region") || reason.includes("región")) {
    return "Selecciona una región policial para habilitar esta capa.";
  }

  return layer.disabledReason || "No disponible";
}

function getLayerState(layer) {
  if (layer.disabledReason) {
    return {
      className: "disabled",
      label: getLayerDisabledSummary(layer),
      title: getLayerDisabledTitle(layer)
    };
  }

  if (layer.isSelected) {
    return {
      className: "active",
      label: "Activa",
      title: layer.isRefreshing ? "Actualizando geometría filtrada." : "Capa activa"
    };
  }

  return {
    className: "available",
    label: "Disponible",
    title: "Disponible"
  };
}

function formatActiveLayerCount(count, zeroLabel = "Sin capas activas") {
  if (!count) {
    return zeroLabel;
  }

  return count === 1 ? "1 capa activa" : `${count} capas activas`;
}

export default function GeoBoundaryLayerControls({
  layers,
  scope,
  context,
  isCatalogLoading,
  isContextLoading,
  catalogError,
  contextError,
  toggleLayer,
  updateScope
}) {
  const isBusy = isCatalogLoading || isContextLoading;
  const hasCatalogData = Array.isArray(layers) && layers.length > 0;
  const selectedLayerCount = layers.filter((layer) => layer.isSelected).length;
  const availableLayerCount = layers.filter((layer) => !layer.disabledReason).length;
  const scopePath = getScopePath(scope);
  const scopeSummary = isCatalogLoading
    ? "Cargando catálogo de capas territoriales..."
    : isContextLoading
      ? getLoadingSummary(scope)
      : getScopeSummary(scope);
  const hasRegion = Boolean(scope.region);
  const hasComisaria = Boolean(scope.comisaria || scope.id_comisaria);
  const selectedComisariaLabel = scope.comisaria ||
    context.comisarias.find((comisaria) =>
      String(comisaria.id ?? comisaria.value ?? "") === String(scope.id_comisaria ?? "")
    )?.label ||
    "";
  const selectedJurisdiccionLabel = (context.jurisdicciones ?? []).find((item) => item.value === scope.jurisdiccion)?.label ||
    scope.jurisdiccion ||
    "";
  const selectedSectorLabel = (context.sectores ?? []).find((item) => item.value === scope.sector)?.label ||
    scope.sector ||
    "";

  return (
    <div className={`geo-layer-panel ${hasRegion ? "has-scope" : "is-initial"}`} aria-label="Alcance territorial y capas persistentes" aria-busy={isBusy}>
      <div className="geo-layer-panel-header">
        <div className="geo-layer-title-block">
          <span>Jerarquía territorial</span>
          <strong>Alcance Territorial</strong>
        </div>
        <div className="geo-layer-status-row" role="status" aria-live="polite" aria-atomic="true">
          <span className="geo-status-chip active-count" title={formatActiveLayerCount(selectedLayerCount)}>
            {formatActiveLayerCount(selectedLayerCount)}
          </span>
          <span
            className={`geo-status-chip ${hasRegion ? "ready" : "attention"}`}
            title={hasRegion ? `Región definida: ${scope.region}` : "Región requerida"}
          >
            {hasRegion ? "Región definida" : "Región requerida"}
          </span>
        </div>
      </div>

      <div className={`geo-layer-guidance ${hasRegion ? "ready" : "attention"}`}>
        <span className="geo-guidance-marker" aria-hidden="true" />
        <span className="geo-guidance-text" title={hasRegion ? scopePath : scopeSummary}>{scopeSummary}</span>
      </div>

      {catalogError ? <p className="geo-layer-error" role="alert">{catalogError}</p> : null}
      {contextError ? <p className="geo-layer-error" role="alert">{contextError}</p> : null}
      {!isCatalogLoading && !catalogError && !hasCatalogData ? (
        <p className="geo-layer-error" role="status" aria-live="polite">
          No hay capas territoriales disponibles para esta vista.
        </p>
      ) : null}

      <section className="geo-layer-section scope" aria-labelledby="geo-scope-title">
        <div className="geo-layer-section-header">
          <div>
            <h3 id="geo-scope-title">Selección territorial</h3>
            <p>{hasRegion ? "Ajusta niveles sin cambiar capas persistentes." : "Selecciona región para abrir niveles."}</p>
          </div>
          <span className="geo-section-badge" title={hasRegion ? scopePath : "Paso inicial"}>
            {hasRegion ? "Jerarquía activa" : "Paso inicial"}
          </span>
        </div>

        <div className="geo-scope-grid">
          <div className={getFieldClassName(isBusy, Boolean(scope.region))}>
            <label htmlFor="geo-region">Región policial</label>
            <select
              id="geo-region"
              value={scope.region}
              disabled={isBusy}
              aria-describedby="geo-region-help"
              title={scope.region || "Selecciona región policial"}
              onChange={(event) => updateScope("region", event.target.value)}
            >
              <option value="">{context.regions.length ? "Selecciona región policial" : "Cargando regiones..."}</option>
              {context.regions.map((region) => (
                <option key={region} value={region} title={region}>
                  {region}
                </option>
              ))}
            </select>
            <span id="geo-region-help" className="geo-field-help">
              Punto de partida del alcance.
            </span>
          </div>

          <div className={getFieldClassName(isBusy || !scope.region, Boolean(scope.division))}>
            <label htmlFor="geo-division">División policial</label>
            <select
              id="geo-division"
              value={scope.division}
              disabled={isBusy || !scope.region}
              aria-describedby="geo-division-help"
              title={scope.division || (scope.region ? "Todas las divisiones" : "Primero región")}
              onChange={(event) => updateScope("division", event.target.value)}
            >
              <option value="">
                {!scope.region
                  ? "Primero región"
                  : context.divisions.length
                    ? "Todas las divisiones"
                    : "Sin divisiones disponibles"}
              </option>
              {context.divisions.map((division) => (
                <option key={division} value={division} title={division}>
                  {division}
                </option>
              ))}
            </select>
            <span id="geo-division-help" className="geo-field-help">
              {scope.region ? "Opcional dentro de la región." : "Requiere región."}
            </span>
          </div>

          <div className={getFieldClassName(isBusy || !scope.region, Boolean(scope.id_comisaria))}>
            <label htmlFor="geo-comisaria">Comisaría</label>
            <select
              id="geo-comisaria"
              value={scope.id_comisaria ?? ""}
              disabled={isBusy || !scope.region}
              aria-describedby="geo-comisaria-help"
              title={selectedComisariaLabel || (scope.region ? "Todas las comisarías" : "Primero región")}
              onChange={(event) => updateScope("comisaria", event.target.value)}
            >
              <option value="">
                {!scope.region
                  ? "Primero región"
                  : context.comisarias.length
                    ? "Todas las comisarías"
                    : "Sin comisarías disponibles"}
              </option>
              {context.comisarias.map((comisaria) => (
                <option
                  key={comisaria.id ?? comisaria.value}
                  value={comisaria.id ?? comisaria.value}
                  title={comisaria.label}
                >
                  {comisaria.label}
                </option>
              ))}
            </select>
            <span id="geo-comisaria-help" className="geo-field-help">
              {scope.region ? "Habilita jurisdicción y sector." : "Requiere región."}
            </span>
          </div>

          <div className={getFieldClassName(isBusy || !hasComisaria, Boolean(scope.jurisdiccion))}>
            <label htmlFor="geo-jurisdiccion">Jurisdicción</label>
            <select
              id="geo-jurisdiccion"
              value={scope.jurisdiccion}
              disabled={isBusy || !hasComisaria}
              aria-describedby="geo-jurisdiccion-help"
              title={selectedJurisdiccionLabel || (hasComisaria ? "Todas las jurisdicciones" : "Primero comisaría")}
              onChange={(event) => updateScope("jurisdiccion", event.target.value)}
            >
              <option value="">
                {hasComisaria
                  ? (context.jurisdicciones ?? []).length
                    ? "Todas las jurisdicciones"
                    : "Sin jurisdicciones disponibles"
                  : "Primero comisaría"}
              </option>
              {(context.jurisdicciones ?? []).map((item) => (
                <option key={item.value} value={item.value} title={item.label}>
                  {item.label}
                </option>
              ))}
            </select>
            <span id="geo-jurisdiccion-help" className="geo-field-help">
              {hasComisaria ? "Opcional en la comisaría." : "Requiere comisaría."}
            </span>
          </div>

          <div className={getFieldClassName(isBusy || !hasComisaria, Boolean(scope.sector))}>
            <label htmlFor="geo-sector">Sector</label>
            <select
              id="geo-sector"
              value={scope.sector}
              disabled={isBusy || !hasComisaria}
              aria-describedby="geo-sector-help"
              title={selectedSectorLabel || (hasComisaria ? "Todos los sectores" : "Primero comisaría")}
              onChange={(event) => updateScope("sector", event.target.value)}
            >
              <option value="">
                {hasComisaria
                  ? (context.sectores ?? []).length
                    ? "Todos los sectores"
                    : "Sin sectores disponibles"
                  : "Primero comisaría"}
              </option>
              {(context.sectores ?? []).map((item) => (
                <option key={item.value} value={item.value} title={item.label}>
                  {item.label}
                </option>
              ))}
            </select>
            <span id="geo-sector-help" className="geo-field-help">
              {hasComisaria ? "Opcional para sector." : "Requiere comisaría."}
            </span>
          </div>
        </div>
      </section>

      <section className="geo-layer-section layers" aria-labelledby="geo-layers-title">
        <div className="geo-layer-section-header">
          <div>
            <h3 id="geo-layers-title">Capas persistentes</h3>
            <p>
              {hasRegion
                ? `${availableLayerCount} disponibles para esta selección.`
                : "Elige una región para habilitarlas."}
            </p>
          </div>
        </div>

        <div className="geo-layer-options hierarchy">
          {layers.map((layer) => {
            const layerState = getLayerState(layer);
            const layerMeta = [
              formatFileSize(layer.size_bytes),
              layer.heavy ? "capa pesada" : ""
            ].filter(Boolean).join(" · ");
            const optionClasses = [
              "geo-layer-option",
              layerState.className,
              layer.isLoading || layer.isRefreshing ? "loading" : "",
              layer.error ? "error" : ""
            ].filter(Boolean).join(" ");

            return (
              <label key={layer.id} className={optionClasses}>
                <span className="geo-layer-check">
                  <input
                    type="checkbox"
                    checked={layer.isSelected}
                    disabled={Boolean(layer.disabledReason)}
                    onChange={() => toggleLayer(layer.id)}
                  />
                </span>
                <span className="geo-layer-copy">
                  <span className="geo-layer-card-top">
                    <span className="geo-layer-name">
                      <span className="geo-layer-swatch" style={{ backgroundColor: layer.stroke_color }} />
                      <strong title={layer.label}>{layer.label}</strong>
                    </span>
                    <span className={`geo-layer-state ${layerState.className}`} title={layerState.title}>
                      {layerState.label}
                    </span>
                  </span>
                  {layer.isLoading ? <span className="geo-layer-note" title="Cargando geometría filtrada.">Cargando...</span> : null}
                  {layer.error ? <span className="geo-layer-note error" title={layer.error}>{layer.error}</span> : null}
                  {layerMeta ? <span className="geo-layer-meta" title={layerMeta}>{layerMeta}</span> : null}
                </span>
              </label>
            );
          })}
        </div>
      </section>
    </div>
  );
}
