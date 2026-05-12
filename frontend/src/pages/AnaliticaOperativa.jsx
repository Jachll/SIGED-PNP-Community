import FilterPanel from "../components/FilterPanel";
import OperationalInsightsMap from "../components/OperationalInsightsMap";
import PanelNotice from "../components/PanelNotice";
import StatusBanner from "../components/StatusBanner";
import { useOperationalAnalyticsView } from "../hooks/useOperationalAnalyticsView";
import { getBlockingErrorNotice } from "../utils/loadState";

const HOTSPOT_STATE_OPTIONS = [
  { value: "ACTIVO", label: "Activos" },
  { value: "", label: "Todos" }
];

const GROUP_OPTIONS = [
  { value: "distrito", label: "Distrito" },
  { value: "comisaria", label: "Comisaria" },
  { value: "zona_operativa", label: "Zona operativa" }
];

const TURNO_OPTIONS = [
  { value: "", label: "Todos los turnos" },
  { value: "MADRUGADA", label: "Madrugada" },
  { value: "MANANA", label: "Manana" },
  { value: "TARDE", label: "Tarde" },
  { value: "NOCHE", label: "Noche" }
];

function formatDate(value) {
  if (!value) {
    return "No disponible";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "medium"
  }).format(parsed);
}

function formatDateTime(value) {
  if (!value) {
    return "No disponible";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(parsed);
}

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function getRiskTone(value) {
  const normalized = String(value || "").toUpperCase();

  if (normalized.includes("CRIT") || normalized.includes("MUY_ALTO") || normalized.includes("ALTO")) {
    return "danger";
  }

  if (normalized.includes("MED")) {
    return "warning";
  }

  if (normalized.includes("BAJ")) {
    return "success";
  }

  return "info";
}

function getPriorityTone(value) {
  const normalized = String(value || "").toUpperCase();

  if (normalized.includes("CRIT")) {
    return "danger";
  }

  if (normalized.includes("ALTA")) {
    return "warning";
  }

  if (normalized.includes("MEDIA")) {
    return "info";
  }

  return "neutral";
}

function getOperationalSummaryStatus(isBootstrapping, isRefreshing, hasData) {
  if (isBootstrapping) {
    return "Cargando datos...";
  }

  if (isRefreshing) {
    return "Actualizando datos...";
  }

  return hasData ? "Valor operativo disponible" : "Sin resultados";
}

export default function AnaliticaOperativa() {
  const {
    filters,
    options,
    catalogoDelitos,
    catalogoComisarias,
    territorialContext,
    territorialMode,
    isTerritorialLoading,
    territorialError,
    viewData,
    error,
    errorKind,
    errorTone,
    isBootstrapping,
    isRefreshing,
    isBusy,
    hasData,
    statusText,
    clearError,
    handleFilterChange,
    handleOptionChange,
    handleTerritorialChange,
    applyFilters,
    clearFilters,
    resetOperationalOptions,
    reload
  } = useOperationalAnalyticsView();

  const hotspots = Array.isArray(viewData.hotspots) ? viewData.hotspots : [];
  const zonasCriticas = Array.isArray(viewData.zonasCriticas) ? viewData.zonasCriticas : [];
  const recomendaciones = Array.isArray(viewData.recomendaciones?.recomendaciones)
    ? viewData.recomendaciones.recomendaciones
    : [];
  const reglasEvaluadas = Array.isArray(viewData.recomendaciones?.reglas_evaluadas)
    ? viewData.recomendaciones.reglas_evaluadas
    : [];
  const fechaOperativa = viewData.recomendaciones?.fecha_operativa ?? options.fecha_operativa;
  const blockingErrorNotice = !(hotspots.length || zonasCriticas.length || recomendaciones.length)
    ? getBlockingErrorNotice(
        error ? { kind: errorKind, message: error } : null,
        "Error cargando la analitica operativa"
      )
    : null;

  return (
    <>
      <section className="panel filtros">
        <FilterPanel
          filters={filters}
          catalogoDelitos={catalogoDelitos}
          catalogoComisarias={catalogoComisarias}
          onFilterChange={handleFilterChange}
          onApply={applyFilters}
          onClear={clearFilters}
          territorialContext={territorialContext}
          territorialMode={territorialMode}
          isTerritorialLoading={isTerritorialLoading}
          territorialError={territorialError}
          disabled={isBusy}
          busy={isBusy}
          statusText={statusText}
        />
      </section>

      <section className="panel filtros operational-filters">
        <div className="filtro-group">
          <label htmlFor="estado_hotspot">Estado hotspot</label>
          <select
            id="estado_hotspot"
            name="estado_hotspot"
            value={options.estado_hotspot}
            disabled={isBusy}
            onChange={handleOptionChange}
          >
            {HOTSPOT_STATE_OPTIONS.map((item) => (
              <option key={item.value || "todos"} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filtro-group">
          <label htmlFor="agrupado_por">Agrupar zonas por</label>
          <select
            id="agrupado_por"
            name="agrupado_por"
            value={options.agrupado_por}
            disabled={isBusy}
            onChange={handleOptionChange}
          >
            {GROUP_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filtro-group">
          <label htmlFor="turno">Turno sugerido</label>
          <select
            id="turno"
            name="turno"
            value={options.turno}
            disabled={isBusy}
            onChange={handleOptionChange}
          >
            {TURNO_OPTIONS.map((item) => (
              <option key={item.value || "todos"} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filtro-group">
          <label htmlFor="fecha_operativa">Fecha operativa</label>
          <input
            id="fecha_operativa"
            name="fecha_operativa"
            type="date"
            value={options.fecha_operativa}
            disabled={isBusy}
            onChange={handleOptionChange}
          />
        </div>

        <div className="filtro-group">
          <label htmlFor="min_eventos_zona">Minimo eventos zona</label>
          <input
            id="min_eventos_zona"
            name="min_eventos_zona"
            type="number"
            min="1"
            max="100"
            value={options.min_eventos_zona}
            disabled={isBusy}
            onChange={handleOptionChange}
          />
        </div>

        <div className="acciones filter-actions">
          <button type="button" disabled={isBusy} onClick={applyFilters}>
            {isBusy ? "Actualizando..." : "Actualizar modulos"}
          </button>
          <button type="button" className="secundario" disabled={isBusy} onClick={resetOperationalOptions}>
            Restablecer modulos
          </button>
        </div>
      </section>

      <StatusBanner
        message={error}
        tone={errorTone}
        actionLabel="Ocultar"
        onAction={clearError}
      />

      <section className="panel">
        <div className="subtitulo">
          <h2>Resumen analitico</h2>
          <span>{getOperationalSummaryStatus(isBootstrapping, isRefreshing, hasData)}</span>
        </div>

        {blockingErrorNotice ? (
          <PanelNotice
            title={blockingErrorNotice.title}
            message={blockingErrorNotice.message}
            tone={blockingErrorNotice.tone}
            actionLabel="Reintentar"
            onAction={reload}
          />
        ) : isBootstrapping && !hasData ? (
          <PanelNotice
            title="Cargando analitica avanzada"
            message="Consultando hotspots, zonas criticas y recomendaciones de patrullaje sobre la sesion actual."
            tone="info"
          />
        ) : (
          <div className="metric-grid">
            <article className="metric-card">
              <strong>Hotspots</strong>
              <span data-testid="analytics-hotspots-count">{hotspots.length}</span>
            </article>
            <article className="metric-card">
              <strong>Zonas criticas</strong>
              <span data-testid="analytics-zonas-count">{zonasCriticas.length}</span>
            </article>
            <article className="metric-card">
              <strong>Recomendaciones</strong>
              <span data-testid="analytics-recomendaciones-count">{recomendaciones.length}</span>
            </article>
            <article className="metric-card">
              <strong>Reglas evaluadas</strong>
              <span>{reglasEvaluadas.length}</span>
            </article>
          </div>
        )}
      </section>

      <section className="panel mapa-panel">
        <div className="subtitulo">
          <h2>Mapa analitico operativo</h2>
          <span>{hotspots.length + zonasCriticas.length + recomendaciones.length} elementos geograficos</span>
        </div>

        {hotspots.length || zonasCriticas.length || recomendaciones.length ? (
          <OperationalInsightsMap
            hotspots={hotspots}
            zonasCriticas={zonasCriticas}
            recomendaciones={recomendaciones}
            territorialScope={filters}
            territorialContext={territorialContext}
            isTerritorialLoading={isTerritorialLoading}
            territorialError={territorialError}
            onTerritorialChange={handleTerritorialChange}
          />
        ) : blockingErrorNotice ? (
          <PanelNotice
            title={blockingErrorNotice.title}
            message={blockingErrorNotice.message}
            actionLabel="Reintentar"
            onAction={reload}
            tone={blockingErrorNotice.tone}
          />
        ) : (
          <PanelNotice
            title="Sin elementos geograficos"
            message="Ajusta filtros o recarga la analitica para visualizar hotspots, zonas y recomendaciones en el mapa."
            actionLabel="Reintentar"
            onAction={reload}
          />
        )}
      </section>

      <section className="page-grid operational-modules-grid">
        <div className="panel info-card">
          <div className="subtitulo">
            <h2>Hotspots operativos</h2>
            <span>{hotspots.length} detectados</span>
          </div>

          {hotspots.length ? (
            <div className="operational-list" data-testid="hotspots-list">
              {hotspots.map((hotspot) => (
                <article key={hotspot.id_hotspot} className="operational-card">
                  <div className="operational-card-header">
                    <strong>{hotspot.nombre_zona || hotspot.distrito}</strong>
                    <span className={`status-pill ${getRiskTone(hotspot.nivel_riesgo)}`}>
                      {hotspot.nivel_riesgo}
                    </span>
                  </div>
                  <p>{hotspot.nombre_delito || "Sin delito principal"} en {hotspot.distrito}</p>
                  <div className="operational-meta">
                    <span>{hotspot.conteo_eventos} eventos</span>
                    <span>Radio: {hotspot.radio_metros} m</span>
                    <span>Estado: {hotspot.estado_hotspot}</span>
                  </div>
                  <p className="inline-note">
                    Detectado el {formatDateTime(hotspot.fecha_deteccion)}.
                  </p>
                </article>
              ))}
            </div>
          ) : (
            <PanelNotice
              title="Sin hotspots"
              message="No se encontraron hotspots activos para los filtros operativos seleccionados."
              compact
            />
          )}
        </div>

        <div className="panel info-card">
          <div className="subtitulo">
            <h2>Zonas criticas</h2>
            <span>{zonasCriticas.length} priorizadas</span>
          </div>

          {zonasCriticas.length ? (
            <div className="operational-list" data-testid="zonas-list">
              {zonasCriticas.map((zona) => (
                <article key={`${zona.codigo_zona}-${zona.agrupado_por}`} className="operational-card">
                  <div className="operational-card-header">
                    <strong>{zona.nombre_zona}</strong>
                    <span className={`status-pill ${getPriorityTone(zona.prioridad_operativa)}`}>
                      {zona.prioridad_operativa}
                    </span>
                  </div>
                  <p>{zona.distrito} · {zona.nombre_comisaria || "Sin comisaria asociada"}</p>
                  <div className="operational-meta">
                    <span>{zona.total_eventos} eventos</span>
                    <span>{zona.total_hotspots} hotspots</span>
                    <span>Riesgo: {zona.nivel_riesgo}</span>
                  </div>
                  <p className="inline-note">
                    {formatPercent(zona.porcentaje_total)} del total del periodo · agrupado por {zona.agrupado_por}.
                  </p>
                </article>
              ))}
            </div>
          ) : (
            <PanelNotice
              title="Sin zonas criticas"
              message="No se generaron rankings de zonas criticas con el umbral configurado."
              compact
            />
          )}
        </div>

        <div className="panel recommendations-panel">
          <div className="subtitulo">
            <h2>Recomendaciones de patrullaje</h2>
            <span>{recomendaciones.length} sugerencias</span>
          </div>

          {recomendaciones.length ? (
            <>
              <p className="inline-note">
                Fecha operativa: <strong>{formatDate(fechaOperativa)}</strong>.
              </p>
              <div className="recommendations-list" data-testid="recommendations-list">
                {recomendaciones.map((item, index) => (
                  <article
                    key={item.id_recomendacion ?? `${item.regla_codigo}-${item.zona?.codigo_zona ?? index}-${index}`}
                    className="recommendation-card"
                  >
                    <div className="operational-card-header">
                      <strong>{item.zona?.nombre_zona || "Zona sin nombre"}</strong>
                      <span className={`status-pill ${getPriorityTone(item.prioridad)}`}>
                        {item.prioridad || "Sin prioridad"}
                      </span>
                    </div>

                    <p>
                      {item.tipo_recomendacion || "Sin accion sugerida"} · {item.ventana_horaria?.turno || "Sin turno"} (
                      {item.ventana_horaria?.hora_inicio || "--"} - {item.ventana_horaria?.hora_fin || "--"})
                    </p>

                    <div className="operational-meta">
                      <span>{item.zona?.distrito || "Distrito no disponible"}</span>
                      <span>{item.metricas?.total_eventos_franja ?? 0} eventos franja</span>
                      <span>{item.metricas?.total_eventos_zona ?? 0} eventos zona</span>
                    </div>

                    <p className="recommendation-detail">{item.detalle_operativo || "Sin detalle operativo adicional."}</p>

                    <ul className="justification-list">
                      {(item.justificacion ?? []).map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>

                    <div className="recommendation-footer">
                      <span>{item.recursos_sugeridos?.cantidad_efectivos ?? 0} efectivos</span>
                      <span>{item.recursos_sugeridos?.cantidad_unidades ?? 0} unidades</span>
                      <span>Participacion: {formatPercent(item.metricas?.participacion_franja)}</span>
                    </div>
                  </article>
                ))}
              </div>
            </>
          ) : (
            <PanelNotice
              title="Sin recomendaciones"
              message="No se encontraron recomendaciones operativas para la fecha y turno seleccionados."
            />
          )}
        </div>
      </section>
    </>
  );
}
