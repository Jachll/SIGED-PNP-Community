import { useEffect, useMemo, useRef, useState } from "react";
import { fetchTerritoryContext, fetchTerritoryLayerData, fetchTerritoryLayersCatalog } from "../services/api";
import { normalizeTerritorialContext } from "../utils/territorialContext";
import {
  buildLayerRetentionKey,
  buildLayerRequestKey,
  clearLayerLoadingState,
  findLayerCacheEntry,
  getDefaultDetailForLayer,
  getScopedLayerDetail,
  getViewportBboxForLayer,
  removeLayerCacheEntry,
  resolveRenderableLayerCacheEntry,
  shouldRetainStaleGeometry,
  upsertLayerCacheEntry
} from "./geoBoundaryLayerModel";

const HIERARCHY_ORDER = ["regiones", "divisiones", "comisarias", "jurisdicciones", "sectores"];

function resolveComisariaSelection(options, rawValue) {
  const selectedValue = String(rawValue ?? "").trim();
  if (!selectedValue) {
    return null;
  }

  return (
    (options ?? []).find((option) => String(option?.id ?? option?.value ?? "") === selectedValue) ??
    null
  );
}

function buildScopeViewportSignature(scope) {
  return [
    scope.region || "",
    scope.division || "",
    scope.id_comisaria || "",
    scope.comisaria || "",
    scope.jurisdiccion || "",
    scope.sector || ""
  ].join("::");
}

function getFocusLayerId(scope) {
  if (scope.sector) {
    return "sectores";
  }

  if (scope.jurisdiccion) {
    return "jurisdicciones";
  }

  if (scope.comisaria || scope.id_comisaria) {
    return "comisarias";
  }

  if (scope.division) {
    return "divisiones";
  }

  if (scope.region) {
    return "regiones";
  }

  return "";
}

function getFocusLayerFilters(scope, viewportZoom = 0) {
  if (scope.sector) {
    return {
      region: scope.region,
      division: scope.division,
      comisaria_id: scope.id_comisaria,
      comisaria: scope.comisaria,
      sector: scope.sector,
      detail: getDefaultDetailForLayer("sectores", { isFocus: true, viewportZoom })
    };
  }

  if (scope.jurisdiccion) {
    return {
      region: scope.region,
      division: scope.division,
      comisaria_id: scope.id_comisaria,
      comisaria: scope.comisaria,
      jurisdiccion: scope.jurisdiccion,
      detail: getDefaultDetailForLayer("jurisdicciones", { isFocus: true, viewportZoom })
    };
  }

  if (scope.comisaria || scope.id_comisaria) {
    return {
      region: scope.region,
      division: scope.division,
      comisaria_id: scope.id_comisaria,
      comisaria: scope.comisaria,
      jurisdiccion: "",
      sector: "",
      detail: getDefaultDetailForLayer("comisarias", { isFocus: true, viewportZoom })
    };
  }

  if (scope.division) {
    return {
      region: scope.region,
      division: scope.division,
      detail: getDefaultDetailForLayer("divisiones", { isFocus: true, viewportZoom })
    };
  }

  if (scope.region) {
    return {
      region: scope.region,
      detail: getDefaultDetailForLayer("regiones", { isFocus: true, viewportZoom })
    };
  }

  return {};
}

function getLayerFilters(layerId, scope, viewportZoom = 0) {
  if (layerId === "regiones") {
    return {
      region: scope.region,
      detail: getScopedLayerDetail("regiones", scope, viewportZoom)
    };
  }

  if (layerId === "divisiones") {
    return {
      region: scope.region,
      division: scope.division,
      detail: getScopedLayerDetail("divisiones", scope, viewportZoom)
    };
  }

  if (layerId === "comisarias") {
    return {
      region: scope.region,
      division: scope.division,
      comisaria_id: scope.id_comisaria,
      comisaria: scope.comisaria,
      jurisdiccion: "",
      sector: "",
      detail: getScopedLayerDetail("comisarias", scope, viewportZoom)
    };
  }

  if (layerId === "jurisdicciones") {
    return {
      region: scope.region,
      division: scope.division,
      comisaria_id: scope.id_comisaria,
      comisaria: scope.comisaria,
      jurisdiccion: scope.jurisdiccion,
      sector: "",
      detail: getScopedLayerDetail("jurisdicciones", scope, viewportZoom)
    };
  }

  if (layerId === "sectores") {
    return {
      region: scope.region,
      division: scope.division,
      comisaria_id: scope.id_comisaria,
      comisaria: scope.comisaria,
      jurisdiccion: "",
      sector: scope.sector,
      detail: getScopedLayerDetail("sectores", scope, viewportZoom)
    };
  }

  return {
    region: scope.region,
    division: scope.division,
    comisaria_id: scope.id_comisaria,
    comisaria: scope.comisaria,
    jurisdiccion: scope.jurisdiccion,
    sector: scope.sector,
    detail: getScopedLayerDetail(layerId, scope, viewportZoom)
  };
}

function normalizeViewportBbox(viewportBbox) {
  return typeof viewportBbox === "string" && viewportBbox.trim() ? viewportBbox.trim() : "";
}

function getDisabledReason(layer, scope) {
  if (layer.requires_region && !scope.region) {
    return "Selecciona una region policial para habilitar esta capa.";
  }

  if (layer.requires_comisaria && !scope.comisaria && !scope.id_comisaria) {
    return "Selecciona una comisaria para habilitar esta capa.";
  }

  return "";
}

export function useGeoBoundaryLayers(controlledOptions = {}) {
  const isDisabled = Boolean(controlledOptions.disabled);
  const [catalog, setCatalog] = useState([]);
  const [catalogError, setCatalogError] = useState("");
  const [isCatalogLoading, setIsCatalogLoading] = useState(true);
  const [internalScope, setInternalScope] = useState({
    region: "",
    division: "",
    id_comisaria: "",
    comisaria: "",
    jurisdiccion: "",
    sector: ""
  });
  const [internalContext, setInternalContext] = useState({
    regions: [],
    divisions: [],
    comisarias: [],
    jurisdicciones: [],
    sectores: []
  });
  const [internalContextError, setInternalContextError] = useState("");
  const [internalContextLoading, setInternalContextLoading] = useState(false);
  const [selectedLayerIds, setSelectedLayerIds] = useState([]);
  const [layerDataCacheByLayerId, setLayerDataCacheByLayerId] = useState({});
  const [loadingRequestKeyByLayerId, setLoadingRequestKeyByLayerId] = useState({});
  const [layerErrorCacheByLayerId, setLayerErrorCacheByLayerId] = useState({});
  const inflightRequestKeyByLayerIdRef = useRef({});
  const latestRequestKeyByLayerIdRef = useRef({});
  const requestControllersByLayerIdRef = useRef({});
  const previousScopeViewportSignatureRef = useRef("");
  const previousViewportBboxRef = useRef("");
  const isControlled = Boolean(
    controlledOptions.scope &&
    controlledOptions.context &&
    typeof controlledOptions.updateScope === "function"
  );
  const viewportZoom = Number(controlledOptions.viewportZoom ?? 0);
  const viewportBbox = normalizeViewportBbox(controlledOptions.viewportBbox);
  const scope = isControlled ? controlledOptions.scope : internalScope;
  const context = isControlled ? controlledOptions.context : internalContext;
  const contextError = isControlled ? (controlledOptions.contextError ?? "") : internalContextError;
  const isContextLoading = isControlled ? Boolean(controlledOptions.isContextLoading) : internalContextLoading;
  const isScopeTransitionPending = Boolean(controlledOptions.isScopeTransitionPending);
  const scopeViewportSignature = buildScopeViewportSignature(scope);
  const [bboxReadyScopeSignature, setBboxReadyScopeSignature] = useState("");

  useEffect(() => {
    if (previousScopeViewportSignatureRef.current === scopeViewportSignature) {
      return;
    }

    previousScopeViewportSignatureRef.current = scopeViewportSignature;
    setBboxReadyScopeSignature("");
  }, [scopeViewportSignature]);

  useEffect(() => {
    if (!viewportBbox) {
      previousViewportBboxRef.current = viewportBbox;
      return;
    }

    if (previousViewportBboxRef.current === viewportBbox) {
      return;
    }

    previousViewportBboxRef.current = viewportBbox;
    setBboxReadyScopeSignature(scopeViewportSignature);
  }, [scopeViewportSignature, viewportBbox]);

  useEffect(() => {
    if (isDisabled) {
      setCatalog([]);
      setCatalogError("");
      setIsCatalogLoading(false);
      return undefined;
    }

    let isMounted = true;

    async function loadCatalog() {
      setIsCatalogLoading(true);
      setCatalogError("");

      try {
        const catalogResponse = await fetchTerritoryLayersCatalog();
        if (!isMounted) {
          return;
        }

        const orderedCatalog = (Array.isArray(catalogResponse) ? catalogResponse : []).sort(
          (leftLayer, rightLayer) => HIERARCHY_ORDER.indexOf(leftLayer.id) - HIERARCHY_ORDER.indexOf(rightLayer.id)
        );
        setCatalog(orderedCatalog);
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        setCatalogError(
          requestError?.status === 403
            ? ""
            : requestError?.message || "No se pudo cargar el catalogo de capas geograficas."
        );
      } finally {
        if (isMounted) {
          setIsCatalogLoading(false);
        }
      }
    }

    void loadCatalog();

    return () => {
      isMounted = false;
    };
  }, [isDisabled]);

  useEffect(() => {
    if (isDisabled) {
      setInternalContext({
        regions: [],
        divisions: [],
        comisarias: [],
        jurisdicciones: [],
        sectores: []
      });
      setInternalContextError("");
      setInternalContextLoading(false);
      return undefined;
    }

    let isMounted = true;

    async function loadContext() {
      setInternalContextLoading(true);
      setInternalContextError("");

      try {
        const contextResponse = await fetchTerritoryContext({
          region: scope.region,
          division: scope.division,
          comisaria_id: scope.id_comisaria,
          comisaria: scope.comisaria
        });

        if (!isMounted) {
          return;
        }

        setInternalContext(normalizeTerritorialContext(contextResponse));
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        setInternalContextError(
          requestError?.status === 403
            ? ""
            : requestError?.message || "No se pudo cargar la jerarquia territorial."
        );
      } finally {
        if (isMounted) {
          setInternalContextLoading(false);
        }
      }
    }

    if (!isControlled) {
      void loadContext();
    }

    return () => {
      isMounted = false;
    };
  }, [isControlled, isDisabled, scope.comisaria, scope.division, scope.id_comisaria, scope.region]);

  useEffect(() => {
    if (isDisabled) {
      setSelectedLayerIds([]);
      return;
    }

    if (scope.region) {
      return;
    }

    if (!isControlled) {
      setInternalScope({
        region: "",
        division: "",
        id_comisaria: "",
        comisaria: "",
        jurisdiccion: "",
        sector: ""
      });
    }
    setSelectedLayerIds([]);
  }, [isControlled, isDisabled, scope.region]);

  useEffect(() => {
    if (isDisabled) {
      return;
    }

    if (!scope.region) {
      return;
    }

    setSelectedLayerIds((current) =>
      (scope.comisaria || scope.id_comisaria)
        ? current
        : current.filter((layerId) => !["jurisdicciones", "sectores"].includes(layerId))
    );
  }, [isDisabled, scope.comisaria, scope.id_comisaria, scope.region]);

  useEffect(() => {
    if (isDisabled) {
      return;
    }

    if (!scope.division || (!scope.comisaria && !scope.id_comisaria)) {
      return;
    }

    if (!context.comisarias.some((item) =>
      String(item?.id ?? item?.value ?? "") === String(scope.id_comisaria ?? "") ||
      item?.label === scope.comisaria
    )) {
      updateScope("comisaria", "");
    }
  }, [context.comisarias, isDisabled, scope.comisaria, scope.division, scope.id_comisaria]);

  useEffect(() => {
    if (isDisabled) {
      return;
    }

    if ((!scope.comisaria && !scope.id_comisaria) || !scope.jurisdiccion) {
      return;
    }

    if (!context.jurisdicciones.some((item) => item.value === scope.jurisdiccion)) {
      updateScope("jurisdiccion", "");
    }
  }, [context.jurisdicciones, isDisabled, scope.comisaria, scope.id_comisaria, scope.jurisdiccion]);

  useEffect(() => {
    if (isDisabled) {
      return;
    }

    if ((!scope.comisaria && !scope.id_comisaria) || !scope.sector) {
      return;
    }

    if (!context.sectores.some((item) => item.value === scope.sector)) {
      updateScope("sector", "");
    }
  }, [context.sectores, isDisabled, scope.comisaria, scope.id_comisaria, scope.sector]);

  function updateScope(name, value) {
    if (isControlled) {
      controlledOptions.updateScope(name, value);
      return;
    }

    setInternalScope((current) => {
      if (name === "region") {
        return {
          region: value,
          division: "",
          id_comisaria: "",
          comisaria: "",
          jurisdiccion: "",
          sector: ""
        };
      }

      if (name === "division") {
        return {
          ...current,
          division: value,
          id_comisaria: "",
          comisaria: "",
          jurisdiccion: "",
          sector: ""
        };
      }

      if (name === "comisaria") {
        const selectedComisaria = resolveComisariaSelection(context.comisarias, value);
        return {
          ...current,
          id_comisaria: selectedComisaria ? String(selectedComisaria.id ?? selectedComisaria.value ?? "") : "",
          comisaria: selectedComisaria?.label ?? "",
          jurisdiccion: "",
          sector: ""
        };
      }

      if (name === "jurisdiccion") {
        return {
          ...current,
          jurisdiccion: value,
          sector: ""
        };
      }

      return {
        ...current,
        [name]: value
      };
    });
  }

  useEffect(() => () => {
    Object.values(requestControllersByLayerIdRef.current).forEach((controller) => {
      controller?.abort?.();
    });
  }, []);

  useEffect(() => {
    if (!isScopeTransitionPending) {
      return;
    }

    Object.values(requestControllersByLayerIdRef.current).forEach((controller) => {
      controller?.abort?.();
    });
    requestControllersByLayerIdRef.current = {};
    inflightRequestKeyByLayerIdRef.current = {};
    setLoadingRequestKeyByLayerId({});
    console.info("[geo-boundary-layers]", {
      event: "layer_requests_paused_for_scope_transition",
      scopeViewportSignature
    });
  }, [isScopeTransitionPending, scopeViewportSignature]);

  async function ensureLayerLoaded(layer, filters) {
    const requestKey = buildLayerRequestKey(layer.id, filters);
    const retentionKey = buildLayerRetentionKey(layer.id, filters);

    if (
      findLayerCacheEntry(layerDataCacheByLayerId, layer.id, requestKey) ||
      loadingRequestKeyByLayerId[layer.id] === requestKey ||
      inflightRequestKeyByLayerIdRef.current[layer.id] === requestKey
    ) {
      return;
    }

    requestControllersByLayerIdRef.current[layer.id]?.abort?.();
    const requestController = new AbortController();
    requestControllersByLayerIdRef.current[layer.id] = requestController;
    inflightRequestKeyByLayerIdRef.current[layer.id] = requestKey;
    latestRequestKeyByLayerIdRef.current[layer.id] = requestKey;
    console.info("[geo-boundary-layers]", {
      event: "layer_request_started",
      layerId: layer.id,
      requestKey,
      filters
    });
    setLoadingRequestKeyByLayerId((current) => ({
      ...current,
      [layer.id]: requestKey
    }));
    setLayerErrorCacheByLayerId((current) => removeLayerCacheEntry(current, layer.id, requestKey));

    try {
      const layerData = await fetchTerritoryLayerData(layer.id, filters, {
        signal: requestController.signal
      });

      if (latestRequestKeyByLayerIdRef.current[layer.id] !== requestKey) {
        return;
      }

      setLayerDataCacheByLayerId((current) =>
        upsertLayerCacheEntry(current, layer.id, {
          requestKey,
          retentionKey,
          value: layerData
        })
      );
      setLayerErrorCacheByLayerId((current) => removeLayerCacheEntry(current, layer.id, requestKey));
      console.info("[geo-boundary-layers]", {
        event: "layer_request_succeeded",
        layerId: layer.id,
        requestKey
      });
    } catch (requestError) {
      if (requestError?.name === "AbortError") {
        console.info("[geo-boundary-layers]", {
          event: "layer_request_aborted",
          layerId: layer.id,
          requestKey
        });
        return;
      }

      if (latestRequestKeyByLayerIdRef.current[layer.id] !== requestKey) {
        return;
      }

      setLayerErrorCacheByLayerId((current) =>
        upsertLayerCacheEntry(current, layer.id, {
          requestKey,
          retentionKey,
          value: requestError?.message || `No se pudo cargar la capa ${layer.label}.`
        })
      );
      console.info("[geo-boundary-layers]", {
        event: "layer_request_failed",
        layerId: layer.id,
        requestKey,
        status: requestError?.status ?? 0,
        message: requestError?.message || "No error message"
      });
    } finally {
      if (requestControllersByLayerIdRef.current[layer.id] === requestController) {
        delete requestControllersByLayerIdRef.current[layer.id];
      }
      if (inflightRequestKeyByLayerIdRef.current[layer.id] === requestKey) {
        delete inflightRequestKeyByLayerIdRef.current[layer.id];
      }
      setLoadingRequestKeyByLayerId((current) => clearLayerLoadingState(current, layer.id, requestKey));
    }
  }

  const layers = useMemo(
    () =>
      catalog.map((layer) => {
        const isViewportAligned = bboxReadyScopeSignature === scopeViewportSignature;
        const focusLayerId = getFocusLayerId(scope);
        const isSelected = selectedLayerIds.includes(layer.id);
        const layerViewportBbox = layer.id === focusLayerId
          ? ""
          : getViewportBboxForLayer(layer.id, viewportBbox, { isViewportAligned });
        const baseFilters = layer.id === focusLayerId && isSelected
          ? getFocusLayerFilters(scope, viewportZoom)
          : getLayerFilters(layer.id, scope, viewportZoom);
        const filters = {
          ...baseFilters,
          bbox: layerViewportBbox
        };
        const requestKey = buildLayerRequestKey(layer.id, filters);
        const retentionKey = buildLayerRetentionKey(layer.id, filters);
        const disabledReason = getDisabledReason(layer, scope);
        const layerDataEntry = findLayerCacheEntry(layerDataCacheByLayerId, layer.id, requestKey);
        const layerErrorEntry = findLayerCacheEntry(layerErrorCacheByLayerId, layer.id, requestKey);
        const renderDataEntry = shouldRetainStaleGeometry(layer.id)
          ? resolveRenderableLayerCacheEntry(
              layerDataCacheByLayerId,
              layer.id,
              requestKey,
              retentionKey,
              Boolean(layerErrorEntry)
            )
          : layerDataEntry;
        const hasRenderableGeometry = Boolean(renderDataEntry?.value);
        const isCurrentRequestLoading = loadingRequestKeyByLayerId[layer.id] === requestKey;

        return {
          ...layer,
          filters,
          requestKey,
          retentionKey,
          renderRequestKey: renderDataEntry?.requestKey ?? requestKey,
          disabledReason,
          isSelected,
          isLoading: Boolean(isSelected && isCurrentRequestLoading && !hasRenderableGeometry),
          isRefreshing: Boolean(isSelected && isCurrentRequestLoading && hasRenderableGeometry),
          error: isSelected ? (layerErrorEntry?.value ?? "") : "",
          data: layerDataEntry?.value ?? null,
          renderData: renderDataEntry?.value ?? null,
          isStaleData: Boolean(renderDataEntry && renderDataEntry.requestKey !== requestKey)
        };
      }),
    [
      catalog,
      layerDataCacheByLayerId,
      layerErrorCacheByLayerId,
      loadingRequestKeyByLayerId,
      scope,
      selectedLayerIds,
      bboxReadyScopeSignature,
      scopeViewportSignature,
      viewportBbox,
      viewportZoom
    ]
  );

  useEffect(() => {
    if (isDisabled || isScopeTransitionPending) {
      return;
    }

    layers.forEach((layer) => {
      if (layer.isSelected && !layer.disabledReason && !layer.data && !layer.error && !layer.isLoading) {
        void ensureLayerLoaded(layer, layer.filters);
      }
    });
  }, [isDisabled, isScopeTransitionPending, layers]);

  const focusLayer = useMemo(() => {
    const focusLayerId = getFocusLayerId(scope);
    if (!focusLayerId) {
      return null;
    }

    const baseLayer = layers.find((layer) => layer.id === focusLayerId);
    if (!baseLayer) {
      return null;
    }

    const filters = getFocusLayerFilters(scope, viewportZoom);
    const requestKey = buildLayerRequestKey(baseLayer.id, filters);
    const retentionKey = buildLayerRetentionKey(baseLayer.id, filters);
    const layerDataEntry = findLayerCacheEntry(layerDataCacheByLayerId, baseLayer.id, requestKey);
    const layerErrorEntry = findLayerCacheEntry(layerErrorCacheByLayerId, baseLayer.id, requestKey);
    const renderDataEntry = layerDataEntry;

    return {
      ...baseLayer,
      filters,
      requestKey,
      retentionKey,
      renderRequestKey: renderDataEntry?.requestKey ?? requestKey,
      isSelected: true,
      isLoading: loadingRequestKeyByLayerId[baseLayer.id] === requestKey,
      error: layerErrorEntry?.value ?? "",
      data: layerDataEntry?.value ?? null,
      renderData: renderDataEntry?.value ?? null,
      isStaleData: Boolean(renderDataEntry && renderDataEntry.requestKey !== requestKey)
    };
  }, [layerDataCacheByLayerId, layerErrorCacheByLayerId, layers, loadingRequestKeyByLayerId, scope, viewportZoom]);

  useEffect(() => {
    if (isDisabled || isScopeTransitionPending) {
      return;
    }

    if (
      !focusLayer ||
      focusLayer.disabledReason ||
      focusLayer.data ||
      focusLayer.error ||
      focusLayer.isLoading
    ) {
      return;
    }

    void ensureLayerLoaded(focusLayer, focusLayer.filters);
  }, [focusLayer, isDisabled, isScopeTransitionPending]);

  function toggleLayer(layerId) {
    const targetLayer = layers.find((layer) => layer.id === layerId);
    if (!targetLayer || targetLayer.disabledReason) {
      return;
    }

    setSelectedLayerIds((current) =>
      current.includes(layerId)
        ? current.filter((item) => item !== layerId)
        : [...current, layerId]
    );
  }

  const visibleLayers = useMemo(
    () => layers.filter((layer) => layer.isSelected),
    [layers]
  );

  return {
    layers,
    visibleLayers,
    focusLayer,
    scope,
    context,
    isCatalogLoading,
    isContextLoading,
    catalogError,
    contextError,
    toggleLayer,
    updateScope
  };
}
