import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const URGENCY_LABELS = {
  expired: "Expired",
  urgent: "Urgent",
  near_expiry: "Near expiry",
  watch: "Watch",
  ok: "OK",
};

const URGENCY_COLORS = {
  expired: "#8e0000",
  urgent: "#c62828",
  near_expiry: "#ed6c02",
  watch: "#f9a825",
  ok: "#2e7d32",
};

function emptyForm() {
  return { sku: "", name: "", expiry_date: "", quantity: "", unit_price: "" };
}

function ScanForm({ onScanned }) {
  const [form, setForm] = useState(emptyForm());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      Object.entries(form).forEach(([k, v]) => formData.append(k, v));
      const res = await fetch(`${API_URL}/secondserve/scan`, { method: "POST", body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
      setForm(emptyForm());
      onScanned?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = form.name && form.expiry_date && form.quantity !== "" && form.unit_price !== "";

  return (
    <section className="panel">
      <h2>Scan an inventory item</h2>
      <form onSubmit={handleSubmit} className="stack-form">
        <input
          type="text"
          placeholder="SKU (optional)"
          value={form.sku}
          onChange={(e) => update("sku", e.target.value)}
          className="text-input"
        />
        <input
          type="text"
          placeholder="Product name"
          value={form.name}
          onChange={(e) => update("name", e.target.value)}
          className="text-input"
        />
        <label className="field-label">
          Expiry date
          <input
            type="date"
            value={form.expiry_date}
            onChange={(e) => update("expiry_date", e.target.value)}
            className="text-input"
          />
        </label>
        <input
          type="number"
          min="0"
          placeholder="Quantity on hand"
          value={form.quantity}
          onChange={(e) => update("quantity", e.target.value)}
          className="text-input"
        />
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="Unit price ($)"
          value={form.unit_price}
          onChange={(e) => update("unit_price", e.target.value)}
          className="text-input"
        />
        <button type="submit" disabled={!canSubmit || loading}>
          {loading ? "Scanning…" : "Scan item"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result-card">
          <span className="grade-badge" style={{ backgroundColor: URGENCY_COLORS[result.urgency] }}>
            {URGENCY_LABELS[result.urgency] ?? result.urgency}
          </span>
          <p className="route">
            {result.days_left >= 0 ? `${result.days_left} day(s) left` : "Already expired"} — route:{" "}
            {result.route}
          </p>
          {result.suggested_markdown_pct > 0 && (
            <p className="score">Suggested markdown: {result.suggested_markdown_pct}%</p>
          )}
        </div>
      )}
    </section>
  );
}

function SecondServeReport({ refreshKey }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/secondserve/report`)
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        return res.json();
      })
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [refreshKey]);

  return (
    <section className="panel">
      <h2>Inventory report</h2>
      {error && <p className="error">Couldn't load report: {error}</p>}
      {!report && !error && <p>Loading…</p>}
      {report && (
        <>
          <p className="big-stat">${report.estimated_value_at_risk} at risk</p>
          <ul className="breakdown">
            <li>Expired: {report.counts_by_urgency.expired}</li>
            <li>Urgent (rescue): {report.counts_by_urgency.urgent}</li>
            <li>Near expiry (markdown): {report.counts_by_urgency.near_expiry}</li>
            <li>Watch: {report.counts_by_urgency.watch}</li>
            <li>OK: {report.counts_by_urgency.ok}</li>
          </ul>

          {report.items.length > 0 && (
            <table className="report-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Qty</th>
                  <th>Days left</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {report.items.map((item, i) => (
                  <tr
                    key={i}
                    className={["urgent", "expired"].includes(item.urgency) ? "flagged-row" : ""}
                  >
                    <td>{item.name}</td>
                    <td>{item.quantity}</td>
                    <td>{item.days_left}</td>
                    <td>{URGENCY_LABELS[item.urgency] ?? item.urgency}</td>
                    <td>
                      {item.route === "rescue"
                        ? "Rescue → KiwiHarvest"
                        : item.route === "markdown"
                        ? `Markdown -${item.suggested_markdown_pct}%`
                        : item.route === "monitor"
                        ? "Monitor"
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}

export default function SecondServe() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div>
      <p className="module-note">
        Mocked module: rule-based on expiry date, no photo or trained model
        needed — this is close to how a production version would work too.
        ≤1 day left → rescue via KiwiHarvest. 2-3 days → markdown suggestion.
        4-7 days → watch list.
      </p>
      <ScanForm onScanned={() => setRefreshKey((k) => k + 1)} />
      <SecondServeReport refreshKey={refreshKey} />
    </div>
  );
}
