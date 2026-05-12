import FilterPanel from "../components/FilterPanel";
import HourChart from "../components/HourChart";
import PanelNotice from "../components/PanelNotice";
import StatusBanner from "../components/StatusBanner";
import { TERRITORIAL_MODE_HIERARCHY } from "../config/roleAccess";
import { useProtectedCatalogView } from "../hooks/useProtectedCatalogView";
import { fetchAnalisisTemporal } from "../services/api";
import { getBlockingErrorNotice } from "../utils/loadState";

const INITIAL_ANALYSIS_DATA = {
  statsPorHora: [],
  statsPorDia: [],
  statsPorMes: [],
  statsPorDiaSemana: []
};

function formatDateLabel(value) {
  const parsedDate = new Date(`${value}T00:00:00`);

  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(parsedDate);
}

function formatMonthLabel(item) {
  const parsedMonth = new Date(item.anio, item.mes - 1, 1);

  return new Intl.DateTimeFormat("es-PE", {
    month: "long",
    year: "numeric"
  }).format(parsedMonth);
}

function totalize(items) {
  return items.reduce((accumulator, item) => accumulator + item.total, 0);
}

function isAnalysisEmpty(data) {
  return (
    !data?.statsPorHora?.length &&
    !data?.statsPorDia?.length &&
    !data?.statsPorMes?.length &&
    !data?.statsPorDiaSemana?.length
  );
}

function getTemporalStatusLabel(isBootstrapping, isRefreshing, totalEvents) {
  if (isBootstrapping) {
    return "Cargando datos...";
  }

  if (isRefreshing) {
    return "Actualizando datos...";
  }

  return `${totalEvents} eventos agregados`;
}

export default function AnalisisTemporal({ access }) {
  const enableTerritorialHierarchy = access
    ? access.territorialMode === TERRITORIAL_MODE_HIERARCHY
    : true;
  const {
    filters,
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
    statusText,
    clearError,
    handleFilterChange,
    applyFilters,
    clearFilters,
    reload
  } = useProtectedCatalogView({
    loadViewData: fetchAnalisisTemporal,
    initialViewData: INITIAL_ANALYSIS_DATA,
    isViewDataEmpty: isAnalysisEmpty,
    enableTerritorialHierarchy,
    bootstrapErrorMessage: "No se pudo inicializar el analisis temporal",
    refreshErrorMessage: "No se pudo cargar el analisis temporal"
  });

  const statsHora = viewData.statsPorHora ?? [];
  const statsPorDia = viewData.statsPorDia ?? [];
  const statsPorMes = viewData.statsPorMes ?? [];
  const statsPorDiaSemana = viewData.statsPorDiaSemana ?? [];
  const recentDays = [...statsPorDia].slice(-7).reverse();
  const recentMonths = [...statsPorMes].slice(-6).reverse();
  const topWeekdays = [...statsPorDiaSemana].sort((left, right) => right.total - left.total);
  const hasAnyData = Boolean(statsHora.length || statsPorDia.length || statsPorMes.length || statsPorDiaSemana.length);
  const blockingErrorNotice = !hasAnyData
    ? getBlockingErrorNotice(
        error ? { kind: errorKind, message: error } : null,
        "Error cargando el analisis temporal"
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

      <StatusBanner
        message={error}
        tone={errorTone}
        actionLabel="Ocultar"
        onAction={clearError}
      />

      <section className="page-grid analytics-grid">
        <div className="panel grafico-panel">
          <div className="subtitulo">
            <h2>Distribucion por hora</h2>
            <span>{getTemporalStatusLabel(isBootstrapping, isRefreshing, totalize(statsHora))}</span>
          </div>

          {blockingErrorNotice ? (
            <PanelNotice
              title={blockingErrorNotice.title}
              message={blockingErrorNotice.message}
              tone={blockingErrorNotice.tone}
              actionLabel="Reintentar"
              onAction={reload}
            />
          ) : isBootstrapping && !statsHora.length ? (
            <PanelNotice
              title="Cargando analisis protegido"
              message="Estamos calculando la distribucion horaria desde la API autenticada."
              tone="info"
            />
          ) : statsHora.length ? (
            <>
              <HourChart statsHora={statsHora} label="Eventos por hora" />
              {isRefreshing ? (
                <p className="inline-note">Actualizando la lectura temporal con los filtros aplicados.</p>
              ) : null}
            </>
          ) : (
            <PanelNotice
              title="Sin distribucion horaria"
              message="No hay datos agregados por hora para la combinacion de filtros actual."
              actionLabel="Reintentar"
              onAction={reload}
              compact
            />
          )}
        </div>

        <div className="panel info-card">
          <div className="subtitulo">
            <h2>Tendencia diaria</h2>
            <span>{statsPorDia.length} dias</span>
          </div>
          {recentDays.length ? (
            <ul className="insight-list">
              {recentDays.map((item) => (
                <li key={item.fecha}>
                  <strong>{formatDateLabel(item.fecha)}</strong>
                  <span>{item.total} eventos</span>
                </li>
              ))}
            </ul>
          ) : (
            <PanelNotice
              title="Sin tendencia diaria"
              message="No hay dias con eventos para la seleccion actual."
              compact
            />
          )}
        </div>

        <div className="panel info-card">
          <div className="subtitulo">
            <h2>Acumulado mensual</h2>
            <span>{statsPorMes.length} periodos</span>
          </div>
          {recentMonths.length ? (
            <ul className="insight-list">
              {recentMonths.map((item) => (
                <li key={item.periodo}>
                  <strong>{formatMonthLabel(item)}</strong>
                  <span>{item.total} eventos</span>
                </li>
              ))}
            </ul>
          ) : (
            <PanelNotice
              title="Sin acumulado mensual"
              message="Todavia no hay series mensuales disponibles para esta consulta."
              compact
            />
          )}
        </div>

        <div className="panel info-card">
          <div className="subtitulo">
            <h2>Patron semanal</h2>
            <span>{statsPorDiaSemana.length} dias</span>
          </div>
          {topWeekdays.length ? (
            <ul className="insight-list">
              {topWeekdays.map((item) => (
                <li key={item.dia_semana_numero}>
                  <strong>{item.dia_semana}</strong>
                  <span>{item.total} eventos</span>
                </li>
              ))}
            </ul>
          ) : (
            <PanelNotice
              title="Sin patron semanal"
              message="Todavia no hay patrones semanales para mostrar con los filtros actuales."
              compact
            />
          )}
        </div>
      </section>
    </>
  );
}
