import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const GENE_START = 43044292;
const GENE_END = 43170245;
const TRACK_WIDTH = 860;

const SIGNIFICANCE_COLORS = {
  pathogenic: "#dc2626",
  uncertain_significance: "#d97706",
  likely_benign: "#059669",
  benign: "#059669",
};

function VariantTrack({ variants }) {
  return (
    <svg viewBox="0 0 900 140" className="variant-track">
      <line x1="40" y1="90" x2={40 + TRACK_WIDTH} y2="90" stroke="#cbd5e1" strokeWidth="3" />
      <text x="40" y="115" className="track-label">chr17:{GENE_START.toLocaleString()}</text>
      <text x={40 + TRACK_WIDTH} y="115" textAnchor="end" className="track-label">
        {GENE_END.toLocaleString()}
      </text>

      {variants.map((v) => {
        const fraction = (v.position - GENE_START) / (GENE_END - GENE_START);
        const x = 40 + fraction * TRACK_WIDTH;
        const color = SIGNIFICANCE_COLORS[v.clinical_significance] || "#64748b";
        return (
          <g key={v.id}>
            <line x1={x} y1="90" x2={x} y2="55" stroke={color} strokeWidth="2" />
            <circle cx={x} cy="50" r="7" fill={color}>
              <title>
                chr17:{v.position} {v.ref}&gt;{v.alt} — {v.clinical_significance} ({v.consequence})
              </title>
            </circle>
          </g>
        );
      })}
    </svg>
  );
}

function App() {
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [variants, setVariants] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/runs`)
      .then((res) => res.json())
      .then((data) => setRuns(data));
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/stats`)
      .then((res) => res.json())
      .then((data) => setStats(data));
  }, []);

  function loadVariants(runId) {
    setSelectedRunId(runId);
    fetch(`${API_BASE}/runs/${runId}/variants`)
      .then((res) => res.json())
      .then((data) => setVariants(data));
  }

  return (
    <div className="dashboard">
      <header className="app-header">
        <h1>NGS Pipeline Dashboard</h1>
        <p className="subtitle">BRCA1 Cancer Variant Analysis</p>
      </header>

      {stats && (
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-value">{stats.total_runs}</div>
            <div className="stat-label">Pipeline Runs</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.total_variants}</div>
            <div className="stat-label">Variants Called</div>
          </div>
          <div className="stat-card stat-card-alert">
            <div className="stat-value">{stats.pathogenic_variants}</div>
            <div className="stat-label">Pathogenic Findings</div>
          </div>
        </div>
      )}

      <div className="card about-card">
        <h2>About this pipeline</h2>
        <p>
          An end-to-end cancer genomics pipeline: simulated NGS reads are aligned (BWA-MEM),
          variant-called (GATK HaplotypeCaller), and annotated against real ClinVar clinical
          significance data (Ensembl VEP) for the BRCA1 gene — a clinically significant
          breast/ovarian cancer gene. Every pipeline stage runs in Docker; results are stored
          in Postgres and served through a Flask API.
        </p>
        <div className="tech-badges">
          {["Python", "Flask", "PostgreSQL", "Docker", "React", "BWA", "GATK", "Ensembl VEP"].map(
            (tech) => (
              <span key={tech} className="tech-badge">{tech}</span>
            )
          )}
        </div>
      </div>

      <div className="card">
        <h2>Pipeline Runs</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Sample</th>
              <th>Status</th>
              <th>Started</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr
                key={run.id}
                className={selectedRunId === run.id ? "row-selected" : ""}
              >
                <td>{run.id}</td>
                <td>{run.sample_name}</td>
                <td>
                  <span className={`badge badge-status-${run.status}`}>
                    {run.status}
                  </span>
                </td>
                <td className="mono">{run.started_at}</td>
                <td>
                  <button className="btn" onClick={() => loadVariants(run.id)}>
                    View variants
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedRunId && (
        <div className="card">
          <h2>Variants — Run {selectedRunId}</h2>
          <VariantTrack variants={variants} />
          <table className="data-table">
            <thead>
              <tr>
                <th>Chrom</th>
                <th>Position</th>
                <th>Ref</th>
                <th>Alt</th>
                <th>Consequence</th>
                <th>Clinical Significance</th>
              </tr>
            </thead>
            <tbody>
              {variants.map((v) => (
                <tr key={v.id}>
                  <td className="mono">{v.chrom}</td>
                  <td className="mono">{v.position}</td>
                  <td className="mono">{v.ref}</td>
                  <td className="mono">{v.alt}</td>
                  <td>{v.consequence}</td>
                  <td>
                    <span className={`badge badge-sig-${v.clinical_significance}`}>
                      {v.clinical_significance}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;