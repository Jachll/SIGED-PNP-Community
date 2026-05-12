export default function PanelNotice({
  title,
  message,
  tone = "neutral",
  actionLabel,
  onAction,
  compact = false
}) {
  const classes = ["panel-notice", tone, compact ? "compact" : ""].filter(Boolean).join(" ");
  const accessibilityRole = tone === "warning" || tone === "danger" || tone === "error" ? "alert" : "status";
  const ariaLive = accessibilityRole === "alert" ? "assertive" : "polite";

  return (
    <div className={classes} role={accessibilityRole} aria-live={ariaLive} aria-atomic="true">
      {title ? <strong>{title}</strong> : null}
      {message ? <p>{message}</p> : null}
      {actionLabel && onAction ? (
        <button type="button" className="secundario" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
