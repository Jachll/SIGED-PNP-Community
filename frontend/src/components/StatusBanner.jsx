const TONE_CLASS_NAME = {
  error: "alerta-error",
  warning: "alerta-warning",
  success: "alerta-success",
  info: "alerta-info"
};

function getA11yToneMeta(tone) {
  if (tone === "error" || tone === "warning") {
    return {
      role: "alert",
      ariaLive: "assertive"
    };
  }

  return {
    role: "status",
    ariaLive: "polite"
  };
}

export default function StatusBanner({
  message,
  tone = "info",
  actionLabel,
  onAction,
  className = ""
}) {
  if (!message) {
    return null;
  }

  const toneClassName = TONE_CLASS_NAME[tone] ?? TONE_CLASS_NAME.info;
  const classes = [toneClassName, "status-banner", className].filter(Boolean).join(" ");
  const accessibilityMeta = getA11yToneMeta(tone);

  return (
    <div
      className={classes}
      role={accessibilityMeta.role}
      aria-live={accessibilityMeta.ariaLive}
      aria-atomic="true"
    >
      <span>{message}</span>
      {actionLabel && onAction ? (
        <button type="button" className="terciario" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
