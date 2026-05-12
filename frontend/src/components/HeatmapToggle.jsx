export default function HeatmapToggle({ checked, onChange, disabled = false }) {
  return (
    <div className="acciones heatmap-control">
      <label className="heatmap-toggle" aria-label="Control del heatmap del mapa operativo">
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
        />
        Mostrar heatmap
      </label>
    </div>
  );
}
