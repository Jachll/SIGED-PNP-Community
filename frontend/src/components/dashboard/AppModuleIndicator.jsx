export default function AppModuleIndicator({
  activePage,
  territorialStatus
}) {
  return (
    <section className="app-module-indicator" aria-label="Modulo activo">
      <span>Modulo activo</span>
      <h2>{activePage.label}</h2>
      <p>{activePage.description}</p>
      <small>{territorialStatus}</small>
    </section>
  );
}
