import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import PanelNotice from "../components/PanelNotice";
import StatusBanner from "../components/StatusBanner";
import {
  API_BASE_URL,
  fetchHealth,
  fetchLoteCarga,
  fetchLotesCarga,
  uploadLoteCarga
} from "../services/api";
import { REQUIRED_UPLOAD_COLUMNS, createInitialCargaDatosState } from "../state/cargaDatosState";
import { LOAD_ERROR_KIND, buildLoadErrorState, getBlockingErrorNotice } from "../utils/loadState";

const STATUS_META = {
  PENDIENTE: { label: "Pendiente", tone: "neutral" },
  PROCESANDO: { label: "Procesando", tone: "info" },
  COMPLETADO: { label: "Completado", tone: "success" },
  COMPLETADO_CON_ERRORES: { label: "Completado con errores", tone: "warning" },
  FALLIDO: { label: "Fallido", tone: "danger" }
};

const ROLE_LABELS = {
  admin: "Administrador",
  analista: "Analista",
  consulta: "Consulta"
};

function getStatusMeta(status) {
  return STATUS_META[status] ?? {
    label: status || "Sin estado",
    tone: "neutral"
  };
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

function formatFileSize(size = 0) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export default function CargaDatos() {
  const { user } = useAuth();
  const [state, setState] = useState(createInitialCargaDatosState);
  const [fileInputKey, setFileInputKey] = useState(0);

  const selectedFile = state.form.archivo;
  const isExcelSelected = selectedFile?.name?.toLowerCase().endsWith(".xlsx") ?? false;
  const canSubmit = Boolean(selectedFile) && !state.submitting && !state.loadingLotes;
  const selectedStatus = useMemo(
    () => getStatusMeta(state.loteDetalle?.estado_lote),
    [state.loteDetalle?.estado_lote]
  );
  const currentRoleLabel = ROLE_LABELS[user?.rol_codigo] ?? user?.rol_codigo ?? "Sin rol";
  const errorTone = state.errorStatus === 403 ? "warning" : "error";
  const blockingErrorNotice = getBlockingErrorNotice(
    state.error
      ? {
          kind: state.errorStatus === 403 ? LOAD_ERROR_KIND.FORBIDDEN : LOAD_ERROR_KIND.LOAD,
          message: state.error
        }
      : null,
    "Error cargando lotes"
  );

  useEffect(() => {
    async function bootstrap() {
      setState((previousState) => ({
        ...previousState,
        loadingHealth: true,
        healthError: ""
      }));

      try {
        const response = await fetchHealth();
        setState((previousState) => ({
          ...previousState,
          loadingHealth: false,
          health: response,
          healthError: ""
        }));
      } catch (requestError) {
        setState((previousState) => ({
          ...previousState,
          loadingHealth: false,
          healthError: requestError.message || "No se pudo validar el backend"
        }));
      }

      void refreshLotes();
    }

    void bootstrap();
  }, []);

  function clearError() {
    setState((previousState) => ({
      ...previousState,
      error: "",
      errorStatus: 0
    }));
  }

  async function refreshLotes(preferredLoteId = null) {
    setState((previousState) => ({
      ...previousState,
      loadingLotes: true,
      error: "",
      errorStatus: 0
    }));

    try {
      const lotes = await fetchLotesCarga({ limite: 12 });
      const requestedLoteId = preferredLoteId ?? state.selectedLoteId;
      const selectedLoteId = lotes.some((item) => item.id_lote === requestedLoteId)
        ? requestedLoteId
        : lotes[0]?.id_lote ?? null;
      const loteDetalle = selectedLoteId ? await fetchLoteCarga(selectedLoteId) : null;

      setState((previousState) => ({
        ...previousState,
        loadingLotes: false,
        lotes,
        selectedLoteId,
        loteDetalle,
        error: "",
        errorStatus: 0
      }));
      return true;
    } catch (requestError) {
      const nextError = buildLoadErrorState(requestError, "No se pudo actualizar el historial de lotes");
      setState((previousState) => ({
        ...previousState,
        loadingLotes: false,
        error: nextError.message,
        errorStatus: nextError.status
      }));
      return false;
    }
  }

  async function loadLoteDetalle(idLote) {
    setState((previousState) => ({
      ...previousState,
      loadingLotes: true,
      error: "",
      errorStatus: 0
    }));

    try {
      const loteDetalle = await fetchLoteCarga(idLote);
      setState((previousState) => ({
        ...previousState,
        loadingLotes: false,
        selectedLoteId: idLote,
        loteDetalle,
        error: "",
        errorStatus: 0
      }));
    } catch (requestError) {
      const nextError = buildLoadErrorState(requestError, `No se pudo cargar el lote ${idLote}`);
      setState((previousState) => ({
        ...previousState,
        loadingLotes: false,
        error: nextError.message,
        errorStatus: nextError.status
      }));
    }
  }

  function handleFileChange(event) {
    const archivo = event.target.files?.[0] ?? null;

    setState((previousState) => ({
      ...previousState,
      form: {
        ...previousState.form,
        archivo,
        sheet: archivo?.name?.toLowerCase().endsWith(".xlsx") ? previousState.form.sheet : ""
      }
    }));
  }

  function handleFieldChange(event) {
    const { name, value } = event.target;
    setState((previousState) => ({
      ...previousState,
      form: {
        ...previousState.form,
        [name]: value
      }
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!selectedFile) {
      setState((previousState) => ({
        ...previousState,
        error: "Selecciona un archivo CSV o Excel para iniciar la carga.",
        errorStatus: 0
      }));
      return;
    }

    setState((previousState) => ({
      ...previousState,
      submitting: true,
      error: "",
      errorStatus: 0
    }));

    try {
      const loteDetalle = await uploadLoteCarga({
        archivo: selectedFile,
        sheet: state.form.sheet,
        observaciones: state.form.observaciones
      });

      const lotes = await fetchLotesCarga({ limite: 12 });
      setState((previousState) => ({
        ...previousState,
        submitting: false,
        lotes,
        loteDetalle,
        selectedLoteId: loteDetalle.id_lote,
        form: {
          archivo: null,
          sheet: "",
          observaciones: ""
        },
        error: "",
        errorStatus: 0
      }));
      setFileInputKey((previousKey) => previousKey + 1);
    } catch (requestError) {
      const nextError = buildLoadErrorState(requestError, "No se pudo procesar la carga");
      setState((previousState) => ({
        ...previousState,
        submitting: false,
        error: nextError.message,
        errorStatus: nextError.status
      }));
    }
  }

  return (
    <>
      <StatusBanner
        message={state.error}
        tone={errorTone}
        actionLabel="Ocultar"
        onAction={clearError}
      />

      <section className="page-grid data-upload-layout">
        <div className="panel upload-panel">
          <div className="subtitulo">
            <h2>Nueva carga</h2>
            <span>{state.submitting ? "Procesando lote..." : "CSV o Excel"}</span>
          </div>

          <form className="upload-form" onSubmit={handleSubmit}>
            <div className="filtro-group">
              <label>Sesion operativa</label>
              <div className="session-summary">
                <strong>{user?.nombre_completo ?? "Usuario autenticado"}</strong>
                <span>@{user?.username ?? "sin-usuario"}</span>
                <span>Rol: {currentRoleLabel}</span>
              </div>
              <p className="field-help">
                El bearer se envia automaticamente en las rutas protegidas de carga.
              </p>
            </div>

            <div className="filtro-group">
              <label htmlFor="archivo_lote">Archivo del lote</label>
              <input
                data-testid="upload-input"
                key={fileInputKey}
                id="archivo_lote"
                name="archivo_lote"
                type="file"
                accept=".csv,.xlsx"
                disabled={state.submitting}
                onChange={handleFileChange}
              />
              <p className="field-help">Formatos admitidos: `.csv` y `.xlsx`.</p>
              {selectedFile ? (
                <div className="file-meta">
                  <strong>{selectedFile.name}</strong>
                  <span>{formatFileSize(selectedFile.size)}</span>
                </div>
              ) : null}
            </div>

            {isExcelSelected ? (
              <div className="filtro-group">
                <label htmlFor="sheet">Hoja Excel</label>
                <input
                  id="sheet"
                  name="sheet"
                  type="text"
                  value={state.form.sheet}
                  disabled={state.submitting}
                  onChange={handleFieldChange}
                  placeholder="Opcional: deja vacio para usar la primera hoja"
                />
              </div>
            ) : null}

            <div className="filtro-group">
              <label htmlFor="observaciones">Observaciones del lote</label>
              <textarea
                data-testid="upload-observaciones"
                id="observaciones"
                name="observaciones"
                rows="3"
                value={state.form.observaciones}
                disabled={state.submitting}
                onChange={handleFieldChange}
                placeholder="Ejemplo: lote patrullaje abril, fuente manual de comisaria, etc."
              />
            </div>

            <div className="upload-actions">
              <button type="submit" disabled={!canSubmit} data-testid="upload-submit">
                {state.submitting ? "Cargando..." : "Cargar archivo"}
              </button>
              <button
                type="button"
                className="secundario"
                disabled={state.loadingLotes || state.submitting}
                onClick={() => void refreshLotes()}
              >
                {state.loadingLotes ? "Actualizando..." : "Actualizar historial"}
              </button>
            </div>
          </form>
        </div>

        <div className="panel info-card">
          <div className="subtitulo">
            <h2>Estado operativo</h2>
            <span>
              {state.loadingHealth
                ? "Consultando..."
                : state.health?.status ?? "Sin sincronizacion"}
            </span>
          </div>

          {state.loadingHealth ? (
            <PanelNotice
              title="Validando backend"
              message="Comprobando conectividad y disponibilidad del servicio antes de operar la carga."
              tone="info"
              compact
            />
          ) : state.healthError ? (
            <PanelNotice
              title="No se pudo validar el backend"
              message={state.healthError}
              tone="warning"
              compact
            />
          ) : (
            <ul className="status-list">
              <li>
                <strong>Servicio</strong>
                <span>{state.health?.service ?? "Sin respuesta"}</span>
              </li>
              <li>
                <strong>Base de datos</strong>
                <span>{state.health?.database ?? "Sin respuesta"}</span>
              </li>
              <li>
                <strong>API</strong>
                <span>{API_BASE_URL}</span>
              </li>
              <li>
                <strong>Autorizacion</strong>
                <span>{user ? `${currentRoleLabel} autenticado` : "Pendiente"}</span>
              </li>
            </ul>
          )}

          <div className="subsection-copy">
            <h3>Columnas esperadas</h3>
            <div className="tag-row">
              {REQUIRED_UPLOAD_COLUMNS.map((column) => (
                <span key={column} className="tag">
                  {column}
                </span>
              ))}
            </div>
          </div>

          <div className="subsection-copy">
            <h3>UX esperada</h3>
            <ol className="roadmap-list">
              <li>Iniciar sesion, seleccionar archivo y confirmar la carga.</li>
              <li>Procesar el lote y consolidar resumen de validaciones.</li>
              <li>Revisar cantidad de registros validos, con error y promovidos.</li>
              <li>Entrar al detalle del lote para corregir filas observadas.</li>
            </ol>
          </div>
        </div>
      </section>

      <section className="page-grid data-results-grid">
        <div className="panel batch-summary-panel">
          <div className="subtitulo">
            <h2>Lote seleccionado</h2>
            <span>{state.loteDetalle ? `#${state.loteDetalle.id_lote}` : "Sin seleccion"}</span>
          </div>

          {state.loadingLotes && !state.loteDetalle ? (
            <PanelNotice
              title="Sincronizando lotes"
              message="Consultando el historial protegido y el detalle del lote mas reciente."
              tone="info"
            />
          ) : blockingErrorNotice && !state.loteDetalle ? (
            <PanelNotice
              title={blockingErrorNotice.title}
              message={blockingErrorNotice.message}
              tone={blockingErrorNotice.tone}
              actionLabel="Reintentar"
              onAction={() => void refreshLotes()}
            />
          ) : state.loteDetalle ? (
            <>
              <div className="summary-header">
                <div>
                  <h3 data-testid="selected-batch-file">{state.loteDetalle.nombre_archivo}</h3>
                  <p>{formatDateTime(state.loteDetalle.fecha_inicio)}</p>
                </div>
                <span className={`status-pill ${selectedStatus.tone}`} data-testid="selected-batch-status">{selectedStatus.label}</span>
              </div>

              <div className="metric-grid">
                <article className="metric-card">
                  <strong data-testid="selected-batch-id">#{state.loteDetalle.id_lote}</strong>
                  <span>Total</span>
                  <span data-testid="selected-batch-total">{state.loteDetalle.total_filas}</span>
                </article>
                <article className="metric-card">
                  <strong>Validos</strong>
                  <span data-testid="selected-batch-validos">{state.loteDetalle.filas_validas}</span>
                </article>
                <article className="metric-card">
                  <strong>Con error</strong>
                  <span data-testid="selected-batch-errores">{state.loteDetalle.filas_error}</span>
                </article>
                <article className="metric-card">
                  <strong>Promovidos</strong>
                  <span data-testid="selected-batch-promovidos">{state.loteDetalle.filas_promovidas}</span>
                </article>
              </div>

              <ul className="status-list summary-list">
                <li>
                  <strong>Ruta registrada</strong>
                  <span>{state.loteDetalle.ruta_archivo || "No registrada"}</span>
                </li>
                <li>
                  <strong>Fecha fin</strong>
                  <span>{formatDateTime(state.loteDetalle.fecha_fin)}</span>
                </li>
              </ul>

              {state.loteDetalle.observaciones ? (
                <div className="summary-note">
                  <strong>Observaciones</strong>
                  <p>{state.loteDetalle.observaciones}</p>
                </div>
              ) : null}
            </>
          ) : (
            <PanelNotice
              title="Sin lote seleccionado"
              message="Selecciona un lote del historial o carga un archivo para ver el resumen operativo."
            />
          )}
        </div>

        <div className="panel history-panel">
          <div className="subtitulo">
            <h2>Historial reciente</h2>
            <span>{state.loadingLotes ? "Actualizando..." : `${state.lotes.length} lotes`}</span>
          </div>

          {state.loadingLotes && !state.lotes.length ? (
            <PanelNotice
              title="Cargando historial"
              message="Recuperando los lotes recientes permitidos para tu sesion actual."
              tone="info"
              compact
            />
          ) : blockingErrorNotice && !state.lotes.length ? (
            <PanelNotice
              title={blockingErrorNotice.title}
              message={blockingErrorNotice.message}
              tone={blockingErrorNotice.tone}
              actionLabel="Reintentar"
              onAction={() => void refreshLotes()}
              compact
            />
          ) : state.lotes.length ? (
            <div className="history-list">
              {state.lotes.map((lote) => {
                const statusMeta = getStatusMeta(lote.estado_lote);
                const isActive = lote.id_lote === state.selectedLoteId;

                return (
                  <button
                    key={lote.id_lote}
                    type="button"
                    className={`history-item ${isActive ? "active" : ""}`}
                    onClick={() => void loadLoteDetalle(lote.id_lote)}
                  >
                    <div className="history-header">
                      <div>
                        <strong>#{lote.id_lote}</strong>
                        <span>{lote.nombre_archivo}</span>
                      </div>
                      <span className={`status-pill ${statusMeta.tone}`}>{statusMeta.label}</span>
                    </div>
                    <div className="history-meta">
                      <span>{formatDateTime(lote.fecha_inicio)}</span>
                      <span>{lote.total_filas} filas</span>
                    </div>
                    <div className="history-stats">
                      <span>Validos: {lote.filas_validas}</span>
                      <span>Errores: {lote.filas_error}</span>
                      <span>Promovidos: {lote.filas_promovidas}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <PanelNotice
              title="Sin historial disponible"
              message="Todavia no hay lotes registrados en el backend para este entorno."
              compact
            />
          )}
        </div>
      </section>

      <section className="panel validation-panel">
        <div className="subtitulo">
          <h2>Errores de validacion</h2>
          <span>{state.loteDetalle?.errores?.length ?? 0} filas observadas</span>
        </div>

        {state.loadingLotes && !state.loteDetalle?.errores?.length ? (
          <PanelNotice
            title="Revisando validaciones"
            message="Cargando el detalle del lote seleccionado y sus observaciones."
            tone="info"
            compact
          />
        ) : state.loteDetalle?.errores?.length ? (
          <div className="error-table-wrap">
            <table className="error-table">
              <thead>
                <tr>
                  <th>Fila</th>
                  <th>Error</th>
                  <th>Fecha</th>
                  <th>Hora</th>
                  <th>Delito</th>
                  <th>Distrito</th>
                  <th>Lat / Lng</th>
                </tr>
              </thead>
              <tbody>
                {state.loteDetalle.errores.map((errorRow) => (
                  <tr key={errorRow.id_staging}>
                    <td>{errorRow.numero_fila}</td>
                    <td>{errorRow.mensaje_error || errorRow.estado_registro}</td>
                    <td>{errorRow.valores.fecha || "-"}</td>
                    <td>{errorRow.valores.hora || "-"}</td>
                    <td>{errorRow.valores.id_delito || "-"}</td>
                    <td>{errorRow.valores.distrito || "-"}</td>
                    <td>{`${errorRow.valores.latitud || "-"} / ${errorRow.valores.longitud || "-"}`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : blockingErrorNotice && !state.loteDetalle ? (
          <PanelNotice
            title={blockingErrorNotice.title}
            message={blockingErrorNotice.message}
            tone={blockingErrorNotice.tone}
            actionLabel="Reintentar"
            onAction={() => void refreshLotes()}
            compact
          />
        ) : (
          <PanelNotice
            title={state.loteDetalle ? "Sin errores de validacion" : "Detalle pendiente"}
            message={
              state.loteDetalle
                ? "Este lote no tiene errores de validacion registrados."
                : "El detalle de errores aparecera aqui cuando selecciones o cargues un lote."
            }
            compact
          />
        )}
      </section>
    </>
  );
}
