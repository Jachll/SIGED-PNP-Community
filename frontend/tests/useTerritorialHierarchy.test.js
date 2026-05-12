import test from "node:test";
import assert from "node:assert/strict";
import { TERRITORIAL_MODE_HIERARCHY, TERRITORIAL_MODE_SIMPLE } from "../src/config/roleAccess.js";
import { EMPTY_TERRITORIAL_CONTEXT } from "../src/utils/territorialContext.js";
import {
  buildTerritorialFailureState,
  reconcileTerritorialFilters
} from "../src/hooks/territorialHierarchyModel.js";

test("buildTerritorialFailureState activa fallback simple en 403", () => {
  const failureState = buildTerritorialFailureState({ status: 403 });

  assert.deepEqual(failureState, {
    mode: TERRITORIAL_MODE_SIMPLE,
    context: null,
    errorStatus: 403,
    errorMessage:
      "La jerarquia territorial no esta disponible para tu perfil actual. Usa el filtro simple por comisaria."
  });
});

test("buildTerritorialFailureState conserva jerarquia en errores de carga", () => {
  const failureState = buildTerritorialFailureState({
    status: 503,
    message: "No se pudo cargar la jerarquia territorial."
  });

  assert.deepEqual(failureState, {
    mode: TERRITORIAL_MODE_HIERARCHY,
    context: EMPTY_TERRITORIAL_CONTEXT,
    errorStatus: 503,
    errorMessage: "No se pudo cargar la jerarquia territorial."
  });
});

test("reconcileTerritorialFilters limpia la comisaria invalida y sus dependencias", () => {
  const previousFilters = {
    fecha_inicio: "",
    fecha_fin: "",
    id_delito: "",
    id_comisaria: "42",
    region: "REGION DEMO",
    division: "DIVISION CENTRO",
    comisaria: "COMISARIA OBSOLETA",
    jurisdiccion: "J-99",
    sector: "S-99"
  };

  const nextFilters = reconcileTerritorialFilters(previousFilters, {
    regions: ["REGION DEMO"],
    divisions: ["DIVISION CENTRO"],
    comisarias: [{ id: 40, value: "40", label: "COMISARIA CENTRO" }],
    jurisdicciones: [{ value: "J-1", label: "Jurisdiccion 1" }],
    sectores: [{ value: "S-1", label: "Sector 1" }]
  });

  assert.deepEqual(nextFilters, {
    fecha_inicio: "",
    fecha_fin: "",
    id_delito: "",
    id_comisaria: "",
    region: "REGION DEMO",
    division: "DIVISION CENTRO",
    comisaria: "",
    jurisdiccion: "",
    sector: ""
  });
});

test("reconcileTerritorialFilters reutiliza el objeto cuando la seleccion sigue valida", () => {
  const previousFilters = {
    fecha_inicio: "",
    fecha_fin: "",
    id_delito: "",
    id_comisaria: "40",
    region: "REGION DEMO",
    division: "DIVISION CENTRO",
    comisaria: "COMISARIA CENTRO",
    jurisdiccion: "J-1",
    sector: "S-1"
  };

  const nextFilters = reconcileTerritorialFilters(previousFilters, {
    regions: ["REGION DEMO"],
    divisions: ["DIVISION CENTRO"],
    comisarias: [{ id: 40, value: "40", label: "COMISARIA CENTRO" }],
    jurisdicciones: [{ value: "J-1", label: "Jurisdiccion 1" }],
    sectores: [{ value: "S-1", label: "Sector 1" }]
  });

  assert.equal(nextFilters, previousFilters);
});
