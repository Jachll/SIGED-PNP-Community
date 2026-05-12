import { useEffect, useMemo, useRef, useState } from "react";
import { useTerritorialHierarchy } from "./useTerritorialHierarchy";
import { fetchCatalogosFiltros } from "../services/api";
import { buildLoadErrorState } from "../utils/loadState";
import { cloneInitialFilters, isDateRangeValid, isTerritorialFilterName } from "../utils/filters";

function formatTime(value) {
  if (!value) {
    return "Sin sincronizacion";
  }

  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(value);
}

export function useProtectedCatalogView({
  loadViewData,
  initialViewData,
  isViewDataEmpty,
  enableTerritorialHierarchy = true,
  invalidDateMessage = "La fecha inicio no puede ser mayor que la fecha fin",
  bootstrapErrorMessage = "No se pudo inicializar la vista",
  refreshErrorMessage = "No se pudo actualizar la vista"
}) {
  const [filters, setFilters] = useState(() => cloneInitialFilters());
  const [catalogoDelitos, setCatalogoDelitos] = useState([]);
  const [catalogoComisarias, setCatalogoComisarias] = useState([]);
  const [viewData, setViewData] = useState(initialViewData);
  const [errorState, setErrorState] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const activeViewDataRequestRef = useRef(null);
  const activeViewDataRequestSequenceRef = useRef(0);

  const {
    territorialContext,
    territorialMode,
    isTerritorialLoading,
    pendingTerritorialContextSignature,
    territorialError,
    handleTerritorialChange
  } = useTerritorialHierarchy({
    filters,
    setFilters,
    clearError,
    enabled: enableTerritorialHierarchy
  });

  const hasData = !isViewDataEmpty(viewData);
  const isEmpty = !isBootstrapping && !hasData;
  const isBusy = isBootstrapping || isRefreshing;

  useEffect(() => {
    let isMounted = true;

    async function bootstrap() {
      setIsBootstrapping(true);
      setErrorState(null);

      try {
        const [catalogos, protectedData] = await Promise.all([fetchCatalogosFiltros(), loadViewData()]);

        if (!isMounted) {
          return;
        }

        setCatalogoDelitos(catalogos.delitos);
        setCatalogoComisarias(catalogos.comisarias);
        setViewData(protectedData);
        setLastUpdated(new Date());
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        setErrorState(buildLoadErrorState(requestError, bootstrapErrorMessage));
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
  }, [bootstrapErrorMessage, loadViewData]);

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

    setFilters((previousFilters) => ({
      ...previousFilters,
      [name]: value
    }));
  }

  async function loadProtectedData(activeFilters, fallbackMessage = refreshErrorMessage) {
    if (!isDateRangeValid(activeFilters.fecha_inicio, activeFilters.fecha_fin)) {
      setErrorState({
        kind: "validation",
        tone: "warning",
        status: 0,
        message: invalidDateMessage
      });
      return false;
    }

    activeViewDataRequestRef.current?.abort?.();
    const requestSequence = activeViewDataRequestSequenceRef.current + 1;
    activeViewDataRequestSequenceRef.current = requestSequence;
    const requestController = new AbortController();
    activeViewDataRequestRef.current = requestController;
    setIsRefreshing(true);
    setErrorState(null);

    try {
      const protectedData = await loadViewData(activeFilters, {
        signal: requestController.signal
      });

      if (activeViewDataRequestSequenceRef.current !== requestSequence) {
        return false;
      }

      setViewData(protectedData);
      setLastUpdated(new Date());
      return true;
    } catch (requestError) {
      if (requestError?.name === "AbortError") {
        return false;
      }

      if (activeViewDataRequestSequenceRef.current !== requestSequence) {
        return false;
      }

      setErrorState(buildLoadErrorState(requestError, fallbackMessage));
      return false;
    } finally {
      if (activeViewDataRequestRef.current === requestController) {
        activeViewDataRequestRef.current = null;
      }

      if (activeViewDataRequestSequenceRef.current === requestSequence) {
        setIsRefreshing(false);
      }
    }
  }

  function applyFilters() {
    void loadProtectedData(filters);
  }

  function applyExactFilters(nextFilters, fallbackMessage = refreshErrorMessage) {
    setFilters(nextFilters);
    void loadProtectedData(nextFilters, fallbackMessage);
  }

  function setDraftFilters(nextFilters) {
    if (errorState) {
      clearError();
    }

    setFilters(nextFilters);
  }

  function clearFilters() {
    const resetFilters = cloneInitialFilters();
    setFilters(resetFilters);
    void loadProtectedData(resetFilters);
  }

  function reload() {
    void loadProtectedData(filters, bootstrapErrorMessage);
  }

  const statusText = useMemo(() => {
    if (isBootstrapping) {
      return "Cargando catalogos y datos protegidos...";
    }

    if (isRefreshing) {
      return "Actualizando resultados con los filtros activos...";
    }

    if (hasData) {
      return `Ultima sincronizacion: ${formatTime(lastUpdated)}`;
    }

    return "Sin datos para los filtros actuales.";
  }, [hasData, isBootstrapping, isRefreshing, lastUpdated]);

  useEffect(() => () => {
    activeViewDataRequestRef.current?.abort?.();
  }, []);

  return {
    filters,
    catalogoDelitos,
    catalogoComisarias,
    viewData,
    error: errorState?.message ?? "",
    errorKind: errorState?.kind ?? "",
    errorTone: errorState?.tone ?? "error",
    isBootstrapping,
    isRefreshing,
    isBusy,
    isEmpty,
    hasData,
    lastUpdated,
    statusText,
    territorialContext,
    territorialMode,
    isTerritorialLoading,
    pendingTerritorialContextSignature,
    territorialError,
    handleTerritorialChange,
    clearError,
    handleFilterChange,
    applyFilters,
    applyExactFilters,
    setDraftFilters,
    clearFilters,
    reload
  };
}
