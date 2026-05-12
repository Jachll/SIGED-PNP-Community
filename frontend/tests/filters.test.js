import test from "node:test";
import assert from "node:assert/strict";
import {
  applyTerritorialFilterChange,
  clearTerritorialHierarchyFilters
} from "../src/utils/filters.js";

test("clearTerritorialHierarchyFilters limpia solo los filtros jerarquicos", () => {
  const nextFilters = clearTerritorialHierarchyFilters({
    fecha_inicio: "2026-04-01",
    fecha_fin: "2026-04-14",
    id_delito: "7",
    id_comisaria: "25",
    region: "REGION DEMO NORTE",
    division: "DISTRITO DEMO PUERTO",
    comisaria: "CENTRO",
    jurisdiccion: "J1",
    sector: "S2"
  });

  assert.deepEqual(nextFilters, {
    fecha_inicio: "2026-04-01",
    fecha_fin: "2026-04-14",
    id_delito: "7",
    id_comisaria: "25",
    region: "",
    division: "",
    comisaria: "",
    jurisdiccion: "",
    sector: ""
  });
});

test("clearTerritorialHierarchyFilters reutiliza el objeto si no hay nada que limpiar", () => {
  const previousFilters = {
    fecha_inicio: "",
    fecha_fin: "",
    id_delito: "",
    id_comisaria: "",
    region: "",
    division: "",
    comisaria: "",
    jurisdiccion: "",
    sector: ""
  };

  assert.equal(clearTerritorialHierarchyFilters(previousFilters), previousFilters);
});

test("applyTerritorialFilterChange conserva filtros de datos al cambiar sector", () => {
  const previousFilters = {
    fecha_inicio: "2026-04-01",
    fecha_fin: "2026-04-14",
    id_delito: "7",
    id_comisaria: "25",
    region: "REGION SIGED",
    division: "DIVISION UNO",
    comisaria: "COMISARIA UNO",
    jurisdiccion: "J1",
    sector: "S1"
  };

  assert.deepEqual(applyTerritorialFilterChange(previousFilters, "sector", "S2"), {
    fecha_inicio: "2026-04-01",
    fecha_fin: "2026-04-14",
    id_delito: "7",
    id_comisaria: "25",
    region: "REGION SIGED",
    division: "DIVISION UNO",
    comisaria: "COMISARIA UNO",
    jurisdiccion: "J1",
    sector: "S2"
  });
});

test("applyTerritorialFilterChange limpia descendientes sin tocar filtros no territoriales", () => {
  const previousFilters = {
    fecha_inicio: "2026-04-01",
    fecha_fin: "2026-04-14",
    id_delito: "7",
    id_comisaria: "25",
    region: "REGION SIGED",
    division: "DIVISION UNO",
    comisaria: "COMISARIA UNO",
    jurisdiccion: "J1",
    sector: "S1"
  };

  assert.deepEqual(applyTerritorialFilterChange(previousFilters, "region", "REGION DOS"), {
    fecha_inicio: "2026-04-01",
    fecha_fin: "2026-04-14",
    id_delito: "7",
    id_comisaria: "",
    region: "REGION DOS",
    division: "",
    comisaria: "",
    jurisdiccion: "",
    sector: ""
  });
});
