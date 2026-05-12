import { useEffect, useMemo, useState } from "react";
import { useTerritorialHierarchy } from "./useTerritorialHierarchy";
import { fetchAnaliticaOperativa, fetchCatalogosFiltros } from "../services/api";
import { buildLoadErrorState } from "../utils/loadState";
import { cloneInitialFilters, isDateRangeValid, isTerritorialFilterName } from "../utils/filters";

const DEFAULT_OPERATIONAL_OPTIONS = Object.freeze({
  estado_hotspot: "ACTIVO",
  agrupado_por: "distrito",
  min_eventos_zona: "3",
  turno: "",
  fecha_operativa: ""
});

function buildModuleErrorMessage(moduleErrors = []) {
  if (!Array.isArray(moduleErrors) || !moduleErrors.length) {
    return "";
  }

  if (moduleErrors.length === 1) {
    return moduleErrors[0].message;
  }

  return `Algunos modulos no se pudieron cargar: ${moduleErrors
    .map((moduleError) => moduleError.label)
    .join(", ")}.`;
}

function formatTime(value) {
  if (!value) {
    return "Sin sincronizacion";
  }

  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(value);
}

function cloneOperationalOptions() {
  return { ...DEFAULT_OPERATIONAL_OPTIONS };
}

function buildRequestOptions(options) {
  return {
    estado_hotspot: options.estado_hotspot || "ACTIVO",
    agrupado_por: options.agrupado_por || "distrito",
    min_eventos_zona: Number(options.min_eventos_zona || 3),
    turno: options.turno,
    fecha_operativa: options.fecha_operativa,
    limite_hotspots: 12,
    limite_zonas: 8,
    limite_recomendaciones: 6
  };
}

export function useOperationalAnalyticsView() {
  const [filters, setFilters] = useState(() => cloneInitialFilters());
  const [options, setOptions] = useState(() => cloneOperationalOptions());
  const [catalogoDelitos, setCatalogoDelitos] = useState([]);
  const [catalogoComisarias, setCatalogoComisarias] = useState([]);
  const [viewData, setViewData] = useState({
    hotspots: [],
    zonasCriticas: [],
    recomendaciones: null,
    moduleErrors: []
  });
  const [errorState, setErrorState] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const {
    territorialContext,
    territorialMode,
    isTerritorialLoading,
    territorialError,
    handleTerritorialChange
  } = useTerritorialHierarchy({
    filters,
    setFilters,
    clearError
  });

  const hasData =
    Boolean(viewData.hotspots?.length) ||
    Boolean(viewData.zonasCriticas?.length) ||
    Boolean(viewData.recomendaciones?.recomendaciones?.length);
  const isBusy = isBootstrapping || isRefreshing;

  useEffect(() => {
    let isMounted = true;

    async function bootstrap() {
      setIsBootstrapping(true);
      setErrorState(null);

      try {
        const [catalogos, analytics] = await Promise.all([
          fetchCatalogosFiltros(),
          fetchAnaliticaOperativa(cloneInitialFilters(), buildRequestOptions(DEFAULT_OPERATIONAL_OPTIONS))
        ]);

        if (!isMounted) {
          return;
        }

        setCatalogoDelitos(catalogos.delitos);
        setCatalogoComisarias(catalogos.comisarias);
        setViewData(analytics);
        const moduleErrorMessage = buildModuleErrorMessage(analytics.moduleErrors);
        setErrorState(
          moduleErrorMessage
            ? {
                kind: "partial_load",
                tone: "warning",
                status: 0,
                message: moduleErrorMessage
              }
            : null
        );
        setLastUpdated(new Date());
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        setErrorState(buildLoadErrorState(requestError, "No se pudo cargar la analitica operativa"));
      } finally {
        if (isMounted) {
          setIsBootstrapping(false);
        }
      }
    }

    void bootstrap();

    return () => {
      isMounted = false;
    };
  }, []);

  function clearError() {
    setErrorState(null);
  }

  function handleFilterChange(event) {
    const { name, value } = event.target;

    if (isTerritorialFilterName(name)) {
      handleTerritorialChange(event);
      return;
    }

    if (errorState) {
      clearError();
    }

    setFilters((currentFilters) => ({
      ...currentFilters,
      [name]: value
    }));
  }

  function handleOptionChange(event) {
    const { name, value } = event.target;

    if (errorState) {
      clearError();
    }

    setOptions((currentOptions) => ({
      ...currentOptions,
      [name]: value
    }));
  }

  async function loadOperationalAnalytics(
    activeFilters = filters,
    activeOptions = options,
    fallbackMessage = "No se pudo actualizar la analitica operativa"
  ) {
    if (!isDateRangeValid(activeFilters.fecha_inicio, activeFilters.fecha_fin)) {
      setErrorState({
        kind: "validation",
        tone: "warning",
        status: 0,
        message: "La fecha inicio no puede ser mayor que la fecha fin"
      });
      return false;
    }

    setIsRefreshing(true);
    setErrorState(null);

    try {
      const analytics = await fetchAnaliticaOperativa(activeFilters, buildRequestOptions(activeOptions));
      setViewData(analytics);
      const moduleErrorMessage = buildModuleErrorMessage(analytics.moduleErrors);
      setErrorState(
        moduleErrorMessage
          ? {
              kind: "partial_load",
              tone: "warning",
              status: 0,
              message: moduleErrorMessage
            }
          : null
      );
      setLastUpdated(new Date());
      return true;
    } catch (requestError) {
      setErrorState(buildLoadErrorState(requestError, fallbackMessage));
      return false;
    } finally {
      setIsRefreshing(false);
    }
  }

  function applyFilters() {
    void loadOperationalAnalytics(filters, options);
  }

  function clearFilters() {
    const resetFilters = cloneInitialFilters();
    setFilters(resetFilters);
    void loadOperationalAnalytics(resetFilters, options);
  }

  function resetOperationalOptions() {
    const resetOptions = cloneOperationalOptions();
    setOptions(resetOptions);
    void loadOperationalAnalytics(filters, resetOptions);
  }

  function reload() {
    void loadOperationalAnalytics(filters, options, "No se pudo recargar la analitica operativa");
  }

  const statusText = useMemo(() => {
    if (isBootstrapping) {
      return "Cargando hotspots, zonas criticas y recomendaciones...";
    }

    if (isRefreshing) {
      return "Actualizando modulos analiticos con los filtros operativos...";
    }

    if (hasData) {
      return `Ultima sincronizacion: ${formatTime(lastUpdated)}`;
    }

    return "No hay resultados analiticos para la seleccion actual.";
  }, [hasData, isBootstrapping, isRefreshing, lastUpdated]);

  return {
    filters,
    options,
    catalogoDelitos,
    catalogoComisarias,
    viewData,
    error: errorState?.message ?? "",
    errorKind: errorState?.kind ?? "",
    errorTone: errorState?.tone ?? "error",
    isBootstrapping,
    isRefreshing,
    isBusy,
    hasData,
    statusText,
    territorialContext,
    territorialMode,
    isTerritorialLoading,
    territorialError,
    handleTerritorialChange,
    clearError,
    handleFilterChange,
    handleOptionChange,
    applyFilters,
    clearFilters,
    resetOperationalOptions,
    reload
  };
}
