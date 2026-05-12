export default function AppThemeToggle({
  theme,
  onToggle
}) {
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      className={`app-theme-toggle ${isDark ? "is-dark" : "is-light"}`}
      aria-label={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      aria-pressed={isDark}
      onClick={onToggle}
    >
      {isDark ? <MoonIcon /> : <SunIcon />}
      <span className="sr-only">{isDark ? "Modo oscuro" : "Modo claro"}</span>
    </button>
  );
}

function MoonIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <path d="M20.2 14.3A7.6 7.6 0 0 1 9.7 3.8a8.6 8.6 0 1 0 10.5 10.5Z" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <circle cx="12" cy="12" r="3.6" />
      <path d="M12 2.8v2.1M12 19.1v2.1M4.6 4.6l1.5 1.5M17.9 17.9l1.5 1.5M2.8 12h2.1M19.1 12h2.1M4.6 19.4l1.5-1.5M17.9 6.1l1.5-1.5" />
    </svg>
  );
}
