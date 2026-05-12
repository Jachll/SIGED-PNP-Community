import AppBrand from "./AppBrand";
import AppModuleIndicator from "./AppModuleIndicator";
import AppThemeToggle from "./AppThemeToggle";
import AppUserMenu from "./AppUserMenu";

export default function AppTopbar({
  activePage,
  activePageId,
  lastUpdatedStatus,
  pages,
  roleMeta,
  territorialStatus,
  theme,
  user,
  onLogout,
  onPageChange,
  onThemeToggle
}) {
  return (
    <div className="app-topbar-shell">
      <header className="app-topbar">
        <AppBrand />
        <AppModuleIndicator activePage={activePage} territorialStatus={territorialStatus} />
        <div className="app-topbar-status" aria-label="Estado operacional">
          <span className="app-live-badge">En vivo</span>
          <strong>Operativo</strong>
        </div>
        <div className="app-topbar-updated" aria-label="Ultima actualizacion">
          <span>Ultima actualizacion</span>
          <strong>{lastUpdatedStatus.time}</strong>
          <small>{lastUpdatedStatus.date}</small>
        </div>
        <div className="app-topbar-actions" aria-label="Acciones rapidas">
          <AppThemeToggle theme={theme} onToggle={onThemeToggle} />
        </div>
        <AppUserMenu user={user} roleMeta={roleMeta} onLogout={onLogout} />
      </header>

      <nav className="app-topbar-nav view-tabs" aria-label="Vistas principales">
        {pages.map((page) => (
          <button
            key={page.id}
            type="button"
            data-testid={`tab-${page.id}`}
            className={`tab-button ${page.id === activePageId ? "active" : ""}`}
            aria-current={page.id === activePageId ? "page" : undefined}
            onClick={() => onPageChange(page.id)}
          >
            {page.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
