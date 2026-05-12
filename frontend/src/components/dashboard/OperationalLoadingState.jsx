export default function OperationalLoadingState({
  title,
  message,
  compact = false
}) {
  const classes = ["operational-state", "loading", compact ? "compact" : ""].filter(Boolean).join(" ");

  return (
    <div className={classes} role="status" aria-live="polite" aria-atomic="true">
      <span className="operational-state-loader" aria-hidden="true" />
      <div className="operational-state-copy">
        {title ? <strong>{title}</strong> : null}
        {message ? <p>{message}</p> : null}
      </div>
    </div>
  );
}
