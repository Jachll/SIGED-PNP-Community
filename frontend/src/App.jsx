import { useEffect, useState } from "react";
import { useAuth } from "./auth/AuthContext";
import AppTopbar from "./components/dashboard/AppTopbar";
import StatusBanner from "./components/StatusBanner";
import DashboardOperacional from "./pages/DashboardOperacional";
import AnalisisTemporal from "./pages/AnalisisTemporal";
import AnaliticaOperativa from "./pages/AnaliticaOperativa";
import CargaDatos from "./pages/CargaDatos";
import LoginPage from "./pages/LoginPage";
import { TERRITORIAL_MODE_HIERARCHY, getRoleAccess } from "./config/roleAccess";

const THEME_STORAGE_KEY = "siged-pnp-theme";
const TOPBAR_MONTHS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."];

const PAGE_DEFINITIONS = [
  {
    id: "dashboard-operacional",
    label: "Dashboard Operacional",
    description: "Mantiene el flujo actual del mapa, filtros, heatmap y grafico horario sobre API protegida.",
    component: DashboardOperacional
  },
  {
    id: "analisis-temporal",
    label: "Analisis Temporal",
    description: "Prepara la capa analitica para series temporales y comparativas con sesion operativa.",
    component: AnalisisTemporal
  },
  {
    id: "analitica-operativa",
    label: "Analitica Operativa",
    description: "Expone hotspots, zonas criticas y recomendaciones de patrullaje sobre la misma sesion protegida.",
    component: AnaliticaOperativa
  },
  {
    id: "carga-datos",
    label: "Carga de Datos",
    description: "Permite cargar CSV o Excel, revisar lotes y corregir errores de validacion sin token manual.",
    component: CargaDatos
  }
];

function getInitialTheme() {
  if (typeof window === "undefined") {
    return "dark";
  }

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);

  return storedTheme === "light" || storedTheme === "dark" ? storedTheme : "dark";
}

function formatTopbarUpdate(value) {
  const updatedAt = value instanceof Date ? value : new Date(value);

  if (Number.isNaN(updatedAt.getTime())) {
    return {
      date: "Sin fecha",
      time: "--:--:--"
    };
  }

  const day = String(updatedAt.getDate()).padStart(2, "0");
  const month = TOPBAR_MONTHS[updatedAt.getMonth()] ?? "";
  const year = updatedAt.getFullYear();

  return {
    date: `${day} ${month} ${year}`,
    time: new Intl.DateTimeFormat("es-PE", {
      hour: "2-digit",
      hour12: false,
      minute: "2-digit",
      second: "2-digit"
    }).format(updatedAt)
  };
}

export default function App() {
  const {
    authMessage,
    authMessageTone,
    clearAuthMessage,
    isAuthenticated,
    isRestoring,
    logout,
    user
  } = useAuth();
  const [activePageId, setActivePageId] = useState("dashboard-operacional");
  const [lastUpdatedAt, setLastUpdatedAt] = useState(() => new Date());
  const [theme, setTheme] = useState(getInitialTheme);
  const roleAccess = getRoleAccess(user?.rol_codigo);
  const allowedPages = PAGE_DEFINITIONS.filter((page) => roleAccess.pageIds.includes(page.id));
  const activePage = allowedPages.find((page) => page.id === activePageId) ?? allowedPages[0];
  const ActivePageComponent = activePage?.component;
  const roleMeta = user ? roleAccess : {
    label: user?.rol_codigo ?? "Sin rol",
    tone: "neutral"
  };
  const territorialStatus = roleAccess.territorialMode === TERRITORIAL_MODE_HIERARCHY
    ? "Jerarquia territorial habilitada"
    : "Filtro simple por comisaria";
  const lastUpdatedStatus = formatTopbarUpdate(lastUpdatedAt);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    setLastUpdatedAt(new Date());
  }, [activePageId]);

  useEffect(() => {
    if (!user) {
      if (activePageId !== "dashboard-operacional") {
        setActivePageId("dashboard-operacional");
      }
      return;
    }

    const availablePageIds = getRoleAccess(user.rol_codigo).pageIds;

    if (!availablePageIds.includes(activePageId)) {
      setActivePageId(availablePageIds[0] ?? "dashboard-operacional");
    }
  }, [activePageId, user]);

  if (isRestoring) {
    return (
      <main className="app loading-shell" role="main">
        <section className="panel loading-panel">
          <div className="subtitulo">
            <h2>Restaurando sesion</h2>
            <span>Validando JWT</span>
          </div>
          <p className="empty-state">
            Se esta verificando la sesion guardada para reconectar el frontend con la API protegida.
          </p>
        </section>
      </main>
    );
  }

  if (!isAuthenticated || !ActivePageComponent) {
    return <LoginPage />;
  }

  return (
    <div className="app">
      <AppTopbar
        activePage={activePage}
        activePageId={activePageId}
        pages={allowedPages}
        roleMeta={roleMeta}
        lastUpdatedStatus={lastUpdatedStatus}
        territorialStatus={territorialStatus}
        theme={theme}
        user={user}
        onLogout={() => logout("Sesion cerrada correctamente.")}
        onPageChange={setActivePageId}
        onThemeToggle={() => setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"))}
      />

      <StatusBanner
        message={authMessage}
        tone={authMessageTone}
        actionLabel="Ocultar"
        onAction={clearAuthMessage}
        className="dismissible-alert"
      />

      <main id="app-main" role="main">
        <ActivePageComponent access={roleAccess} />
      </main>
    </div>
  );
}
