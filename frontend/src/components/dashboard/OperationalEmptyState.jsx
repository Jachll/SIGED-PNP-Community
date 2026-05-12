export default function OperationalEmptyState({
  title,
  message,
  tone = "neutral",
  actionLabel = "",
  onAction = null,
  compact = false
}) {
  const classes = ["operational-state", tone, compact ? "compact" : ""].filter(Boolean).join(" ");
  const role = ["warning", "danger", "error"].includes(tone) ? "alert" : "status";
  const ariaLive = role === "alert" ? "assertive" : "polite";

  return (
    <div className={classes} role={role} aria-live={ariaLive} aria-atomic="true">
      <span className="operational-state-mark" aria-hidden="true" />
      <div className="operational-state-copy">
        {title ? <strong>{title}</strong> : null}
        {message ? <p>{message}</p> : null}
      </div>
      {actionLabel && onAction ? (
        <button type="button" className="secundario" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
