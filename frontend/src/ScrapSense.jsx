import { useEffect, useState } from "react";
import { IconPlate, IconUpload, IconSparkles } from "./icons.jsx";
import { MiniBar, Spinner } from "./ui.jsx";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const LEVEL_LABELS = {
  clean_plate: "Clean plate",
  partial_leftover: "Partial leftover",
  high_leftover: "High leftover",
};

const LEVEL_COLORS = {
  clean_plate: "#1f8a4c",
  partial_leftover: "#d97706",
  high_leftover: "#d0342c",
};

function PlateUpload({ onLogged }) {
  const [dishId, setDishId] = useState("");
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setResult(null);
    setError(null);
    setPreviewUrl(URL.createObjectURL(selected));
  }

  async function handleSubmit() {
    if (!file || !dishId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("dish_id", dishId.trim());
      formData.append("file", file);
      const res = await fetch(`${API_URL}/scrapsense/log`, { method: "POST", body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
      onLogged?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-icon">
          <IconPlate />
        </span>
        <h2>Log a plate photo</h2>
      </div>

      <input
        type="text"
        placeholder="Dish name (e.g. lasagna)"
        value={dishId}
        onChange={(e) => setDishId(e.target.value)}
        className="text-input"
      />

      <label className="file-drop">
        <IconUpload width={18} height={18} />
        {file ? file.name : "Choose a plate photo"}
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFileChange} />
      </label>

      {previewUrl && <img src={previewUrl} alt="Plate" className="preview" />}

      <button onClick={handleSubmit} disabled={!file || !dishId.trim() || loading}>
        {loading && <Spinner />}
        {loading ? "Analyzing…" : "Log this plate"}
      </button>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result-card">
          <span className="grade-badge" style={{ backgroundColor: LEVEL_COLORS[result.waste_level] }}>
            <IconSparkles width={14} height={14} />
            {LEVEL_LABELS[result.waste_level] ?? result.waste_level}
          </span>
          <p className="score" style={{ marginTop: "0.6rem" }}>
            Waste ratio: {Math.round(result.waste_ratio * 100)}%
          </p>
        </div>
      )}
    </section>
  );
}

function ScrapSenseReport({ refreshKey }) {
  const [dishes, setDishes] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/scrapsense/report`)
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        return res.json();
      })
      .then((data) => setDishes(data.dishes))
      .catch((err) => setError(err.message));
  }, [refreshKey]);

  return (
    <section className="panel">
      <h2>Dish report</h2>
      {error && <p className="error">Couldn't load report: {error}</p>}
      {!dishes && !error && <p className="empty-state">Loading…</p>}
      {dishes && dishes.length === 0 && <p className="empty-state">No plates logged yet.</p>}
      {dishes && dishes.length > 0 && (
        <table className="report-table">
          <thead>
            <tr>
              <th>Dish</th>
              <th>Plates</th>
              <th>Avg waste</th>
              <th>Status</th>
              <th>Suggested cut</th>
            </tr>
          </thead>
          <tbody>
            {dishes.map((d) => (
              <tr key={d.dish_id} className={d.flagged_over_portioned ? "flagged-row" : ""}>
                <td>{d.dish_id}</td>
                <td>{d.plates_logged}</td>
                <td>
                  <MiniBar
                    pct={d.avg_waste_ratio * 100}
                    color={d.flagged_over_portioned ? "#d0342c" : "#1f8a4c"}
                  />{" "}
                  {Math.round(d.avg_waste_ratio * 100)}%
                </td>
                <td>
                  {d.flagged_over_portioned ? (
                    <span className="pill" style={{ background: "#fde8e6", color: "#d0342c" }}>
                      Over-portioned
                    </span>
                  ) : (
                    <span className="pill" style={{ background: "#e3f5e8", color: "#1f8a4c" }}>
                      OK
                    </span>
                  )}
                </td>
                <td>{d.flagged_over_portioned ? `-${d.suggested_portion_cut_pct}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default function ScrapSense() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div>
      <p className="module-note">
        <IconSparkles width={16} height={16} style={{ flexShrink: 0, marginTop: "0.1rem" }} />
        <span>
          Mocked module: a saturation-based heuristic estimates leftover food on
          each plate (no trained model yet). A dish is flagged once 3+ plates
          average 35%+ waste.
        </span>
      </p>
      <PlateUpload onLogged={() => setRefreshKey((k) => k + 1)} />
      <ScrapSenseReport refreshKey={refreshKey} />
    </div>
  );
}
