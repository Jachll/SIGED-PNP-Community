import { useEffect, useRef, useState } from "react";
import EventMap from "../components/EventMap";
import FilterPanel from "../components/FilterPanel";
import HeatmapToggle from "../components/HeatmapToggle";
import HourChart from "../components/HourChart";
import StatusBanner from "../components/StatusBanner";
import ActiveFiltersSummary from "../components/dashboard/ActiveFiltersSummary";
import DashboardOperacionalShell from "../components/dashboard/DashboardOperacionalShell";
import OperationalEmptyState from "../components/dashboard/OperationalEmptyState";
import OperationalLoadingState from "../components/dashboard/OperationalLoadingState";
import PanelCard from "../components/dashboard/PanelCard";
import PanelHeader from "../components/dashboard/PanelHeader";
import { TERRITORIAL_MODE_HIERARCHY } from "../config/roleAccess";
import { useProtectedCatalogView } from "../hooks/useProtectedCatalogView";
import { fetchDashboardOperacional } from "../services/api";
import { getBlockingErrorNotice } from "../utils/loadState";

const INITIAL_DASHBOARD_DATA = {
  eventos: [],
  heatmap: [],
  statsPorHora: []
};

function isDashboardEmpty(data) {
  return (
    !data?.eventos?.length &&
    !data?.heatmap?.length &&
    !data?.statsPorHora?.length
  );
}

function getDashboardPanelStatus(isBootstrapping, isRefreshing, count, label) {
  if (isBootstrapping) {
    return "Cargando datos...";
  }

  if (isRefreshing) {
    return "Actualizando datos...";
  }

  return `${count} ${label}`;
}

export default function DashboardOperacional({ access }) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  const previousTerritorialSignature = useRef("");
  const previousTerritorialContextSignature = useRef("");
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
    pendingTerritorialContextSignature,
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
    applyExactFilters,
    applyFilters,
    handleTerritorialChange,
    clearFilters,
    reload
  } = useProtectedCatalogView({
    loadViewData: fetchDashboardOperacional,
    initialViewData: INITIAL_DASHBOARD_DATA,
    isViewDataEmpty: isDashboardEmpty,
    enableTerritorialHierarchy,
    bootstrapErrorMessage: "No se pudo inicializar el dashboard operacional",
    refreshErrorMessage: "No se pudo actualizar el dashboard operacional"
  });

  const eventos = viewData.eventos ?? [];
  const heatmapData = viewData.heatmap ?? [];
  const statsHora = viewData.statsPorHora ?? [];
  const blockingErrorNotice = !eventos.length && !statsHora.length
    ? getBlockingErrorNotice(error ? { kind: errorKind, message: error } : null, "Error cargando el dashboard")
    : null;
  const territorialSignature = [
    filters.region,
    filters.division,
    filters.id_comisaria,
    filters.comisaria,
    filters.jurisdiccion,
    filters.sector
  ].join("::");
  const territorialContextSignature = [
    filters.region,
    filters.division,
    filters.id_comisaria,
    filters.comisaria
  ].join("::");
  const filterPanelStatusText = isBootstrapping || isRefreshing ? statusText : "";

  useEffect(() => {
    if (isBootstrapping) {
      return;
    }

    if (!previousTerritorialSignature.current) {
      previousTerritorialSignature.current = territorialSignature;
      previousTerritorialContextSignature.current = territorialContextSignature;
      return;
    }

    if (previousTerritorialSignature.current === territorialSignature) {
      return;
    }

    const contextScopeChanged =
      previousTerritorialContextSignature.current !== territorialContextSignature;

    if (contextScopeChanged && pendingTerritorialContextSignature) {
      console.info("[dashboard-operacional]", {
        event: "territorial_signature_deferred",
        territorialSignature,
        territorialContextSignature,
        pendingTerritorialContextSignature
      });
      return;
    }

    previousTerritorialSignature.current = territorialSignature;
    previousTerritorialContextSignature.current = territorialContextSignature;
    console.info("[dashboard-operacional]", {
      event: "territorial_signature_changed",
      territorialSignature,
      territorialContextSignature,
      deferred: false
    });
    applyExactFilters(filters);
  }, [
    applyExactFilters,
    filters,
    isBootstrapping,
    pendingTerritorialContextSignature,
    territorialContextSignature,
    territorialSignature
  ]);

  const filtersPanel = (
    <PanelCard className="dashboard-filter-card" ariaLabel="Filtros Operacionales">
      <PanelHeader
        eyebrow="Alcance Territorial"
        title="Filtros Operacionales"
        description="Definen el alcance de eventos, mapa, heatmap y analitica."
      />
      <div className="filtros dashboard-filter-grid">
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
          statusText={filterPanelStatusText}
        />
        <HeatmapToggle
          checked={showHeatmap}
          onChange={setShowHeatmap}
          disabled={isBusy || !heatmapData.length}
        />
      </div>
    </PanelCard>
  );
  const alertsPanel = (
    <StatusBanner
      message={error}
      tone={errorTone}
      actionLabel="Ocultar"
      onAction={clearError}
    />
  );
  const mapPanel = (
    <PanelCard className="mapa-panel dashboard-map-card" ariaLabel="Mapa Tactico">
      <PanelHeader
        eyebrow="Mapa Tactico"
        title="Mapa de Incidencias"
        description="Puntos de incidencia, heatmap y capas territoriales bajo el mismo alcance operativo."
        meta={(
          <span data-testid="dashboard-event-count">
            {getDashboardPanelStatus(isBootstrapping, isRefreshing, eventos.length, "eventos")}
          </span>
        )}
      />

      {blockingErrorNotice ? (
        <OperationalEmptyState
          title={blockingErrorNotice.title}
          message={blockingErrorNotice.message}
          tone={blockingErrorNotice.tone}
          actionLabel="Reintentar"
          onAction={reload}
        />
      ) : isBootstrapping && !eventos.length ? (
        <OperationalLoadingState
          title="Cargando mapa operacional"
          message="Consultando eventos, heatmap y catalogos con la sesion activa."
        />
      ) : (
        <>
          <EventMap
            eventos={eventos}
            heatmapData={heatmapData}
            showHeatmap={showHeatmap}
            enableGeoBoundaryLayers={territorialMode === TERRITORIAL_MODE_HIERARCHY}
            territorialScope={filters}
            territorialContext={territorialContext}
            isTerritorialLoading={isTerritorialLoading}
            isTerritorialScopePending={Boolean(pendingTerritorialContextSignature)}
            territorialError={territorialError}
            onTerritorialChange={handleTerritorialChange}
          />
          {!eventos.length ? (
            <OperationalEmptyState
              title="Sin eventos para mostrar"
              message="La seleccion actual no tiene eventos visibles todavia. Puedes seguir usando el mapa y la jerarquia territorial para cambiar de zona."
              actionLabel="Reintentar"
              onAction={reload}
              compact
            />
          ) : null}
          {isRefreshing ? (
            <p className="inline-note">Actualizando mapa y heatmap con los filtros operativos activos.</p>
          ) : null}
        </>
      )}
    </PanelCard>
  );
  const analyticsPanel = (
    <PanelCard className="grafico-panel dashboard-chart-card" ariaLabel="Analítica operativa">
      <PanelHeader
        eyebrow="Analítica operativa"
        title="Distribución horaria"
        description="Lectura por hora del turno operativo."
        meta={(
          <span data-testid="dashboard-hour-status">
            {isBootstrapping ? "Cargando datos..." : isRefreshing ? "Actualizando..." : "Vista actual"}
          </span>
        )}
      />

      {blockingErrorNotice ? (
        <OperationalEmptyState
          title={blockingErrorNotice.title}
          message={blockingErrorNotice.message}
          tone={blockingErrorNotice.tone}
          actionLabel="Reintentar"
          onAction={reload}
          compact
        />
      ) : isBootstrapping && !statsHora.length ? (
        <OperationalLoadingState
          title="Preparando grafico horario"
          message="Cargando la agregacion protegida por hora desde el backend."
          compact
        />
      ) : statsHora.length ? (
        <>
          <HourChart statsHora={statsHora} />
          {isRefreshing ? (
            <p className="inline-note">La distribución horaria se está recalculando con los filtros aplicados.</p>
          ) : null}
        </>
      ) : (
        <OperationalEmptyState
          title="Sin distribución horaria disponible"
          message="Todavía no hay datos agregados por hora para la selección actual."
          compact
        />
      )}
    </PanelCard>
  );
  const summaryPanel = (
    <PanelCard className="dashboard-summary-card" ariaLabel="Filtros Activos">
      <ActiveFiltersSummary
        filters={filters}
        catalogoDelitos={catalogoDelitos}
        catalogoComisarias={catalogoComisarias}
        heatmapEnabled={showHeatmap && Boolean(heatmapData.length)}
        isRefreshing={isRefreshing}
      />
    </PanelCard>
  );

  return (
    <DashboardOperacionalShell
      filters={filtersPanel}
      alerts={error ? alertsPanel : null}
      map={mapPanel}
      analytics={analyticsPanel}
      summary={summaryPanel}
    />
  );
}
