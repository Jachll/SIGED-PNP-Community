export default function PanelHeader({
  title,
  eyebrow = "",
  meta = null,
  description = ""
}) {
  return (
    <div className="subtitulo dashboard-panel-header">
      <div className="dashboard-panel-title-block">
        {eyebrow ? <span className="dashboard-panel-eyebrow">{eyebrow}</span> : null}
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {meta ? <div className="dashboard-panel-meta">{meta}</div> : null}
    </div>
  );
}
