export const REQUIRED_UPLOAD_COLUMNS = [
  "fecha",
  "hora",
  "id_delito",
  "distrito",
  "direccion",
  "latitud",
  "longitud",
  "id_comisaria",
  "fuente_registro",
  "descripcion"
];

export function createInitialCargaDatosState() {
  return {
    form: {
      archivo: null,
      sheet: "",
      observaciones: ""
    },
    loadingHealth: true,
    health: null,
    healthError: "",
    loadingLotes: false,
    submitting: false,
    error: "",
    errorStatus: 0,
    lotes: [],
    loteDetalle: null,
    selectedLoteId: null
  };
}
