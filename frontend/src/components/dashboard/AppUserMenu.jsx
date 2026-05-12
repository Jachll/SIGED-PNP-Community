export default function AppUserMenu({
  user,
  roleMeta,
  onLogout
}) {
  return (
    <div className="session-card app-user-card" aria-label="Usuario actual">
      <div className="app-user-summary">
        <strong>{user.nombre_completo}</strong>
        <span>{roleMeta.label}</span>
      </div>
      <button type="button" className="app-logout-button" onClick={onLogout}>
        Cerrar sesion
      </button>
    </div>
  );
}
