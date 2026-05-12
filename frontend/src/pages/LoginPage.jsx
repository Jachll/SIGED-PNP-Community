import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import StatusBanner from "../components/StatusBanner";

const OPERATIONAL_METRICS = [
  {
    id: "eventos",
    value: "80",
    label: "Eventos",
    subtitle: "Monitoreo activo"
  },
  {
    id: "zonas",
    value: "5",
    label: "Zonas",
    subtitle: "Zonas críticas"
  },
  {
    id: "riesgo",
    value: "30%",
    label: "Riesgo",
    subtitle: "Nivel estimado"
  }
];

const OPERATIONAL_MODES = [
  {
    id: "prevencion",
    label: "Prevención"
  },
  {
    id: "inteligencia",
    label: "Inteligencia"
  },
  {
    id: "intervencion",
    label: "Intervención"
  }
];

function OperationalModeIcon({ type }) {
  if (type === "prevencion") {
    return (
      <svg className="login-mode-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3.2 5.5 5.6v5.1c0 4.2 2.7 7.9 6.5 9.1 3.8-1.2 6.5-4.9 6.5-9.1V5.6L12 3.2Z" />
        <path d="m9 12 2 2 4-5" />
      </svg>
    );
  }

  if (type === "inteligencia") {
    return (
      <svg className="login-mode-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="8.5" />
        <circle cx="12" cy="12" r="2.2" />
        <path d="M12 12 18 8" />
        <path d="M12 3.5v3" />
        <path d="M3.5 12h3" />
        <path d="M17.5 17.5 15.4 15.4" />
      </svg>
    );
  }

  return (
    <svg className="login-mode-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M13 2.8 4.6 13.2h6.2L10 21.2l9.4-11.6h-6.7L13 2.8Z" />
      <path d="M18 18.2h2.2" />
      <path d="M3.8 18.2H6" />
    </svg>
  );
}

export default function LoginPage() {
  const { authMessage, authMessageTone, clearAuthMessage, isAuthenticating, login } = useAuth();
  const [credentials, setCredentials] = useState({
    username: "",
    password: ""
  });
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const canSubmit =
    credentials.username.trim().length >= 3 &&
    credentials.password.length >= 8 &&
    !isAuthenticating;

  useEffect(() => {
    if (!authMessage || authMessageTone !== "success") {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      clearAuthMessage();
    }, 2000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [authMessage, authMessageTone, clearAuthMessage]);

  function handleChange(event) {
    const { name, value } = event.target;

    if (error) {
      setError("");
    }

    if (authMessage) {
      clearAuthMessage();
    }

    setCredentials((currentCredentials) => ({
      ...currentCredentials,
      [name]: value
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    clearAuthMessage();

    try {
      await login({
        username: credentials.username.trim(),
        password: credentials.password
      });
    } catch (requestError) {
      setError(requestError.message || "No se pudo iniciar sesion.");
    }
  }

  return (
    <main className="app login-shell" role="main">
      <section className="login-stage" aria-labelledby="login-title">
        <div className="login-visual">
          <div className="login-brand-block">
            <img
              className="login-badge"
              src="/icons/escudeo-pnp.png"
              alt="Escudo de la instituciones territoriales"
            />
            <div className="login-brand-copy">
              <h1 id="login-title">
                SIGED-<span>PNP</span>
              </h1>
              <p>Geoposición del delito</p>
            </div>
          </div>

          <div className="login-map-visual" aria-hidden="true">
            <img className="login-map-image" src="/icons/community-map.svg" alt="" />
            <span className="login-map-pulse pulse-primary" />
            <span className="login-map-pulse pulse-secondary" />
            <span className="login-map-pulse pulse-tertiary" />
          </div>

          <div className="login-hero-copy">
            <p className="login-hero-title">
              Monitoreo <span>inteligente</span> territorial.
            </p>
            <p className="login-hero-subtitle">
              Sistema de análisis geoespacial para decisiones operativas en tiempo real.
            </p>
          </div>

          <div className="login-operational-strip" aria-label="Indicadores operativos">
            {OPERATIONAL_METRICS.map((metric) => (
              <div className={`login-gauge ${metric.id}`} key={metric.id}>
                <div className="login-metric-copy">
                  <strong>{metric.value}</strong>
                  <span>{metric.label}</span>
                  <small>{metric.subtitle}</small>
                </div>
              </div>
            ))}
          </div>

          <div className="login-mode-row" aria-label="Modos operativos">
            {OPERATIONAL_MODES.map((mode) => (
              <span className={`login-mode-item ${mode.id}`} key={mode.id}>
                <OperationalModeIcon type={mode.id} />
                <span>{mode.label}</span>
              </span>
            ))}
          </div>
        </div>

        <aside className="login-form-wrap" aria-label="Formulario de inicio de sesión">
          <div className="login-form-header">
            <span className="login-access-pill">Acceso operativo</span>
            <h2>Iniciar sesión</h2>
            <p>Ingresa con tu cuenta institucional para continuar.</p>
          </div>

          <StatusBanner
            message={authMessage}
            tone={authMessageTone}
            actionLabel="Ocultar"
            onAction={clearAuthMessage}
          />
          <StatusBanner message={error} tone="error" />

          <form className="login-form" onSubmit={handleSubmit} aria-describedby="login-help-text">
            <div className="login-field">
              <label htmlFor="username">Usuario</label>
              <input
                data-testid="login-username"
                id="username"
                name="username"
                type="text"
                value={credentials.username}
                onChange={handleChange}
                autoComplete="username"
                placeholder="admin.siged"
              />
            </div>

            <div className="login-field">
              <div className="login-label-row">
                <label htmlFor="password">Contraseña</label>
                <span>Recuperar acceso</span>
              </div>
              <div className="login-password-control">
                <input
                  data-testid="login-password"
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={credentials.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  placeholder="Mínimo 8 caracteres"
                />
                <button
                  type="button"
                  className="password-toggle"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  aria-pressed={showPassword}
                  onClick={() => setShowPassword((currentValue) => !currentValue)}
                >
                  <span aria-hidden="true" />
                </button>
              </div>
            </div>

            <button className="login-submit-button" type="submit" disabled={!canSubmit} data-testid="login-submit">
              {isAuthenticating ? "Validando acceso..." : "Ingresar a SIGED"}
              <span aria-hidden="true">-&gt;</span>
            </button>
          </form>

          <div id="login-help-text" className="login-connection">
            <span className="connection-dot" aria-hidden="true" />
            <div>
              <strong>Estado de conexión</strong>
              <p>Sistema operativo en línea</p>
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
