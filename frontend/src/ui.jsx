// Small shared presentational pieces used across all three module tabs.

export function StatCard({ label, value, accent }) {
  return (
    <div className="stat-card" style={accent ? { "--accent": accent } : undefined}>
      <p className="stat-value">{value}</p>
      <p className="stat-label">{label}</p>
    </div>
  );
}

export function MiniBar({ pct, color }) {
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div className="mini-bar-track">
      <div className="mini-bar-fill" style={{ width: `${clamped}%`, backgroundColor: color }} />
    </div>
  );
}

export function Spinner() {
  return <span className="spinner" aria-label="Loading" />;
}
