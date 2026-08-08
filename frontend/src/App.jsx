import { useEffect, useState } from "react";
import ScrapSense from "./ScrapSense.jsx";
import SecondServe from "./SecondServe.jsx";
import { IconLeaf, IconPlate, IconClock, IconUpload, IconSparkles, IconRecycle } from "./icons.jsx";
import { StatCard, Spinner } from "./ui.jsx";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const GRADE_INFO = {
  A: { label: "Grade A", route: "Retail", color: "#1f8a4c" },
  B: { label: "Grade B", route: "Manual review (Grade B proxy)", color: "#d97706" },
  C: { label: "Grade C", route: "Rescue → KiwiHarvest", color: "#d0342c" },
};

function GradeBadge({ grade }) {
  const info = GRADE_INFO[grade] ?? { label: grade, route: "Unknown", color: "#555" };
  return (
    <span className="grade-badge" style={{ backgroundColor: info.color }}>
      <IconSparkles width={14} height={14} />
      {info.label}
    </span>
  );
}

function BatchOverlay({ previewUrl, batchResult }) {
  const { image_width, image_height, items } = batchResult;
  return (
    <div className="overlay-frame">
      <img src={previewUrl} alt="Graded produce" className="overlay-img" />
      <div className="overlay-boxes">
        {items.map((item, i) => {
          const info = GRADE_INFO[item.grade] ?? { color: "#555" };
          const left = (item.box.x / image_width) * 100;
          const top = (item.box.y / image_height) * 100;
          const w = (item.box.w / image_width) * 100;
          const h = (item.box.h / image_height) * 100;
          return (
            <div
              key={i}
              className="overlay-box"
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${w}%`,
                height: `${h}%`,
                borderColor: info.color,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

function UploadPanel({ onGraded }) {
  const [mode, setMode] = useState("single"); // "single" | "batch"
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [batchResult, setBatchResult] = useState(null);

  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setResult(null);
    setBatchResult(null);
    setError(null);
    setPreviewUrl(URL.createObjectURL(selected));
  }

  function handleModeChange(newMode) {
    setMode(newMode);
    setResult(null);
    setBatchResult(null);
    setError(null);
  }

  async function handleSubmit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const endpoint = mode === "batch" ? "/grade-batch" : "/grade";
      const res = await fetch(`${API_URL}${endpoint}`, { method: "POST", body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      if (mode === "batch") {
        setBatchResult(data);
      } else {
        setResult(data);
      }
      onGraded?.();
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
          <IconLeaf />
        </span>
        <h2>Grade a produce photo</h2>
      </div>

      <div className="mode-toggle">
        <button
          type="button"
          className={`mode-button ${mode === "single" ? "active" : ""}`}
          onClick={() => handleModeChange("single")}
        >
          Single fruit
        </button>
        <button
          type="button"
          className={`mode-button ${mode === "batch" ? "active" : ""}`}
          onClick={() => handleModeChange("batch")}
        >
          Bunch / crate
        </button>
      </div>
      {mode === "batch" && (
        <p className="hint-text">
          Works best on produce laid out in a single layer with some space between
          pieces (a tray, box, or table). Dense, overlapping piles will undercount.
        </p>
      )}

      <label className="file-drop">
        <IconUpload width={18} height={18} />
        {file ? file.name : "Choose a photo to grade"}
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFileChange} />
      </label>

      {previewUrl && !batchResult && (
        <img src={previewUrl} alt="Selected produce" className="preview" />
      )}
      {previewUrl && batchResult && <BatchOverlay previewUrl={previewUrl} batchResult={batchResult} />}

      <button onClick={handleSubmit} disabled={!file || loading}>
        {loading && <Spinner />}
        {loading ? "Grading…" : mode === "batch" ? "Grade this bunch" : "Grade this produce"}
      </button>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result-card">
          <GradeBadge grade={result.grade} />
          <p className="route">{GRADE_INFO[result.grade]?.route}</p>
          <p className="score">Confidence score: {result.score}</p>
        </div>
      )}

      {batchResult && (
        <div className="result-card">
          <p className="route">
            {batchResult.detection_mode === "single_fallback"
              ? "Only one fruit detected — graded as a single item."
              : `${batchResult.items.length} fruit${batchResult.items.length === 1 ? "" : "s"} detected`}
          </p>
          <div className="stat-grid" style={{ marginTop: "0.75rem" }}>
            <StatCard label="Grade A → retail" value={batchResult.counts_by_grade.A} accent="#1f8a4c" />
            <StatCard label="Grade B → review" value={batchResult.counts_by_grade.B} accent="#d97706" />
            <StatCard label="Grade C → rescue" value={batchResult.counts_by_grade.C} accent="#d0342c" />
          </div>
        </div>
      )}
    </section>
  );
}

function ImpactDashboard({ refreshKey }) {
  const [impact, setImpact] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/impact`)
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        return res.json();
      })
      .then(setImpact)
      .catch((err) => setError(err.message));
  }, [refreshKey]);

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-icon">
          <IconRecycle />
        </span>
        <h2>Impact dashboard</h2>
      </div>
      {error && <p className="error">Couldn't load impact stats: {error}</p>}
      {!impact && !error && <p className="empty-state">Loading…</p>}
      {impact && (
        <div className="stat-grid">
          <StatCard label="Items graded" value={impact.total_items_graded} accent="#1f8a4c" />
          <StatCard
            label="kg diverted from landfill"
            value={impact.estimated_kg_diverted_from_landfill}
            accent="#166a3a"
          />
          <StatCard label="Grade A → retail" value={impact.counts_by_grade.A} accent="#1f8a4c" />
          <StatCard label="Grade B → review" value={impact.counts_by_grade.B} accent="#d97706" />
          <StatCard label="Grade C → rescue" value={impact.counts_by_grade.C} accent="#d0342c" />
        </div>
      )}
    </section>
  );
}

const TABS = [
  { id: "secondcrop", label: "SecondCrop", icon: IconLeaf },
  { id: "scrapsense", label: "ScrapSense", icon: IconPlate },
  { id: "secondserve", label: "Second Serve", icon: IconClock },
];

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeTab, setActiveTab] = useState("secondcrop");

  return (
    <div className="app">
      <div className="hero">
        <div className="hero-inner">
          <span className="hero-badge">
            <IconSparkles width={14} height={14} />
            Aotearoa AI Hackathon
          </span>
          <h1>Kai Loop</h1>
          <p className="tagline">
            Catching food waste at every stage of the supply chain — before it becomes waste.
          </p>
        </div>
      </div>

      <div className="content">
        <nav className="tabs">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon width={16} height={16} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        <main>
          {activeTab === "secondcrop" && (
            <>
              <UploadPanel onGraded={() => setRefreshKey((k) => k + 1)} />
              <ImpactDashboard refreshKey={refreshKey} />
            </>
          )}
          {activeTab === "scrapsense" && <ScrapSense />}
          {activeTab === "secondserve" && <SecondServe />}
        </main>
      </div>
    </div>
  );
}
