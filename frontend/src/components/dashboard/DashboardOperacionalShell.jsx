export default function DashboardOperacionalShell({
  filters,
  alerts = null,
  map,
  analytics,
  summary
}) {
  return (
    <div className="dashboard-command-shell">
      {alerts ? <div className="dashboard-command-alerts">{alerts}</div> : null}
      {summary ? <div className="dashboard-command-secondary">{summary}</div> : null}
      <div className="dashboard-command-workspace">
        <div className="dashboard-command-map-zone">{map}</div>
        <aside className="dashboard-command-analytics-zone" aria-label="Analítica Operativa">
          <div className="dashboard-command-filters">{filters}</div>
          {analytics}
        </aside>
      </div>
    </div>
  );
}
