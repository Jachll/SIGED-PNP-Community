export default function PanelCard({
  children,
  className = "",
  ariaLabel = "",
  as: Component = "section"
}) {
  const classes = ["panel", "dashboard-panel-card", className].filter(Boolean).join(" ");

  return (
    <Component className={classes} aria-label={ariaLabel || undefined}>
      {children}
    </Component>
  );
}
