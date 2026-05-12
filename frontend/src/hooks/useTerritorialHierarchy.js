import { useEffect, useRef, useState } from "react";
import { fetchTerritoryContext } from "../services/api";
import { TERRITORIAL_MODE_HIERARCHY, TERRITORIAL_MODE_SIMPLE } from "../config/roleAccess";
import { applyTerritorialFilterChange, clearTerritorialHierarchyFilters } from "../utils/filters";
import { EMPTY_TERRITORIAL_CONTEXT } from "../utils/territorialContext";
import { buildTerritorialFailureState, reconcileTerritorialFilters } from "./territorialHierarchyModel";

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

function buildTerritorialContextSignature(filters) {
  return [
    filters?.region ?? "",
    filters?.division ?? "",
    filters?.id_comisaria ?? "",
    filters?.comisaria ?? ""
  ].join("::");
}

export function useTerritorialHierarchy({
  filters,
  setFilters,
  clearError,
  enabled = true
}) {
  const [context, setContext] = useState(() => (enabled ? EMPTY_TERRITORIAL_CONTEXT : null));
  const [mode, setMode] = useState(() => (enabled ? TERRITORIAL_MODE_HIERARCHY : TERRITORIAL_MODE_SIMPLE));
  const [isLoading, setIsLoading] = useState(Boolean(enabled));
  const [error, setError] = useState("");
  const [errorStatus, setErrorStatus] = useState(0);
  const [pendingContextSignature, setPendingContextSignature] = useState(() =>
    enabled ? buildTerritorialContextSignature(filters) : ""
  );
  const latestContextSignatureRef = useRef(pendingContextSignature);
  const contextRequestControllerRef = useRef(null);
  const contextRegions = context?.regions ?? EMPTY_TERRITORIAL_CONTEXT.regions;
  const contextDivisions = context?.divisions ?? EMPTY_TERRITORIAL_CONTEXT.divisions;
  const contextComisarias = context?.comisarias ?? EMPTY_TERRITORIAL_CONTEXT.comisarias;
  const contextJurisdicciones = context?.jurisdicciones ?? EMPTY_TERRITORIAL_CONTEXT.jurisdicciones;
  const contextSectores = context?.sectores ?? EMPTY_TERRITORIAL_CONTEXT.sectores;

  useEffect(() => {
    if (!enabled) {
      contextRequestControllerRef.current?.abort?.();
      contextRequestControllerRef.current = null;
      latestContextSignatureRef.current = "";
      setMode(TERRITORIAL_MODE_SIMPLE);
      setContext(null);
      setIsLoading(false);
      setError("");
      setErrorStatus(0);
      setPendingContextSignature("");
      setFilters((currentFilters) => clearTerritorialHierarchyFilters(currentFilters));
      return undefined;
    }

    let isMounted = true;
    const requestSignature = buildTerritorialContextSignature(filters);
    latestContextSignatureRef.current = requestSignature;
    setPendingContextSignature(requestSignature);
    contextRequestControllerRef.current?.abort?.();
    const requestController = new AbortController();
    contextRequestControllerRef.current = requestController;

    async function loadContext() {
      console.info("[territorial-hierarchy]", {
        event: "load_context_started",
        requestSignature,
        enabled,
        filters: {
          region: filters.region,
          division: filters.division,
          comisaria_id: filters.id_comisaria,
          comisaria: filters.comisaria
        }
      });
      setMode(TERRITORIAL_MODE_HIERARCHY);
      setIsLoading(true);
      setError("");
      setErrorStatus(0);

      try {
        const response = await fetchTerritoryContext({
          region: filters.region,
          division: filters.division,
          comisaria_id: filters.id_comisaria,
          comisaria: filters.comisaria
        }, {
          signal: requestController.signal
        });

        if (!isMounted || latestContextSignatureRef.current !== requestSignature) {
          return;
        }

        setContext(response);
        setMode(TERRITORIAL_MODE_HIERARCHY);
        console.info("[territorial-hierarchy]", {
          event: "load_context_succeeded",
          requestSignature,
          filters: {
            region: filters.region,
            division: filters.division,
            comisaria_id: filters.id_comisaria,
            comisaria: filters.comisaria
          }
        });
      } catch (requestError) {
        if (requestError?.name === "AbortError") {
          console.info("[territorial-hierarchy]", {
            event: "load_context_aborted",
            requestSignature,
            filters: {
              region: filters.region,
              division: filters.division,
              comisaria_id: filters.id_comisaria,
              comisaria: filters.comisaria
            }
          });
          return;
        }

        if (!isMounted || latestContextSignatureRef.current !== requestSignature) {
          return;
        }

        const failureState = buildTerritorialFailureState(requestError);
        setErrorStatus(failureState.errorStatus);
        setMode(failureState.mode);
        setContext(failureState.context);
        setError(failureState.errorMessage);

        if (failureState.mode === TERRITORIAL_MODE_SIMPLE) {
          setFilters((currentFilters) => clearTerritorialHierarchyFilters(currentFilters));
        }
        console.info("[territorial-hierarchy]", {
          event: "load_context_failed",
          requestSignature,
          filters: {
            region: filters.region,
            division: filters.division,
            comisaria_id: filters.id_comisaria,
            comisaria: filters.comisaria
          },
          status: requestError?.status ?? 0,
          message: requestError?.message || "No error message"
        });
      } finally {
        if (
          isMounted &&
          latestContextSignatureRef.current === requestSignature
        ) {
          if (contextRequestControllerRef.current === requestController) {
            contextRequestControllerRef.current = null;
          }
          setPendingContextSignature("");
          setIsLoading(false);
        }
      }
    }

    void loadContext();

    return () => {
      isMounted = false;
      if (contextRequestControllerRef.current === requestController) {
        requestController.abort();
        contextRequestControllerRef.current = null;
      }
    };
  }, [enabled, filters.comisaria, filters.division, filters.id_comisaria, filters.region, setFilters]);

  useEffect(() => {
    if (mode !== TERRITORIAL_MODE_HIERARCHY || isLoading || !context) {
      return;
    }

    setFilters((currentFilters) => reconcileTerritorialFilters(currentFilters, context));
  }, [
    contextComisarias,
    contextDivisions,
    contextJurisdicciones,
    contextRegions,
    contextSectores,
    isLoading,
    setFilters
  ]);

  function handleTerritorialChange(nameOrEvent, directValue) {
    const name = typeof nameOrEvent === "string" ? nameOrEvent : nameOrEvent?.target?.name;
    const value = typeof nameOrEvent === "string" ? directValue : nameOrEvent?.target?.value;

    if (!name) {
      return;
    }

    if (typeof clearError === "function") {
      clearError();
    }

    let nextFilters;

    if (name !== "comisaria") {
      nextFilters = applyTerritorialFilterChange(filters, name, value ?? "");
    } else {
      const selectedComisaria = resolveComisariaSelection(contextComisarias, value);
      nextFilters = {
        ...applyTerritorialFilterChange(
          filters,
          "comisaria",
          selectedComisaria?.label ?? ""
        ),
        id_comisaria: selectedComisaria ? String(selectedComisaria.id ?? selectedComisaria.value ?? "") : ""
      };
    }

    if (name === "region" || name === "division" || name === "comisaria") {
      const nextRequestSignature = buildTerritorialContextSignature(nextFilters);
      latestContextSignatureRef.current = nextRequestSignature;
      setPendingContextSignature(nextRequestSignature);
    }

    setFilters(nextFilters);
  }

  return {
    territorialContext: context,
    territorialMode: mode,
    isTerritorialLoading: isLoading,
    pendingTerritorialContextSignature: pendingContextSignature,
    territorialError: error,
    territorialErrorStatus: errorStatus,
    handleTerritorialChange
  };
}
