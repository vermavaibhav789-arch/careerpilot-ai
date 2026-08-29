"use client";

import { useEffect, useState } from "react";
import { getCareerMap, getSalaryIntelligence, simulateCareerScenario } from "@/lib/api";
import RequireAuth from "@/components/RequireAuth";

function SalaryTab() {
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("Remote");
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!role.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { report } = await getSalaryIntelligence(role.trim(), location.trim() || "Remote");
      setReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't fetch salary data (this is a Pro feature).");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <form onSubmit={run}>
        <div className="field">
          <label htmlFor="role">Role</label>
          <input id="role" type="text" value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. AI Engineer" required />
        </div>
        <div className="field">
          <label htmlFor="location">Location</label>
          <input id="location" type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Bangalore, Remote, New York" />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Searching…" : "Get real salary data →"}
        </button>
      </form>

      {report && (
        <div className="cover-letter-box" style={{ marginTop: 18, whiteSpace: "pre-wrap" }}>
          {report}
        </div>
      )}
    </div>
  );
}

function CareerMapTab() {
  const [sessionId, setSessionId] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setSessionId(localStorage.getItem("careerpilot_session_id") || "");
    }
  }, []);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!targetRole.trim() || !sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const { report } = await getCareerMap(sessionId, targetRole.trim());
      setReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't generate a career map.");
    } finally {
      setLoading(false);
    }
  }

  if (!sessionId) {
    return (
      <div className="empty-state">
        Run an analysis on the <a href="/" style={{ color: "var(--accent-warn)" }}>Analyze page</a> first,
        so the career map has a resume to work from.
      </div>
    );
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <form onSubmit={run}>
        <div className="field">
          <label htmlFor="target">Target role</label>
          <input
            id="target"
            type="text"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="e.g. Staff AI Engineer"
            required
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Mapping…" : "Map my path →"}
        </button>
      </form>

      {report && (
        <div className="cover-letter-box" style={{ marginTop: 18, whiteSpace: "pre-wrap" }}>
          {report}
        </div>
      )}
    </div>
  );
}

function SimulatorTab() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenario, setScenario] = useState("");
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setSessionId(localStorage.getItem("careerpilot_session_id"));
    }
  }, []);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!scenario.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { report } = await simulateCareerScenario(scenario.trim(), sessionId || undefined);
      setReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't run that simulation (this is a Pro feature).");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <p style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 14 }}>
        Ask a "what if" — a career change, relocation, learning a new skill,
        or accepting a job. Grounded in real web search and your Career DNA
        if you've set one up. This is an informed estimate, not a guarantee.
      </p>
      <form onSubmit={run}>
        <div className="field">
          <label htmlFor="scenario">Scenario</label>
          <textarea
            id="scenario"
            rows={3}
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            placeholder="e.g. What if I switch from backend engineering to ML engineering?"
            required
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Simulating…" : "Run simulation →"}
        </button>
      </form>

      {report && (
        <div className="cover-letter-box" style={{ marginTop: 18, whiteSpace: "pre-wrap" }}>
          {report}
        </div>
      )}
    </div>
  );
}

function CareerIntelligenceContent() {
  const [tab, setTab] = useState<"salary" | "map" | "simulate">("salary");

  return (
    <main className="page">
      <div className="intro">
        <h1>Career intelligence</h1>
        <p>
          Grounded in real web search, not a guess from training data — the
          model looks up current numbers before answering.
        </p>
      </div>

      <div className="panel">
        <div className="tool-tabs">
          <button className={`tool-tab ${tab === "salary" ? "active" : ""}`} onClick={() => setTab("salary")}>
            Salary intelligence
          </button>
          <button className={`tool-tab ${tab === "map" ? "active" : ""}`} onClick={() => setTab("map")}>
            Career map
          </button>
          <button className={`tool-tab ${tab === "simulate" ? "active" : ""}`} onClick={() => setTab("simulate")}>
            Simulator
          </button>
        </div>
        {tab === "salary" && <SalaryTab />}
        {tab === "map" && <CareerMapTab />}
        {tab === "simulate" && <SimulatorTab />}
      </div>
    </main>
  );
}

export default function CareerIntelligencePage() {
  return (
    <RequireAuth>
      <CareerIntelligenceContent />
    </RequireAuth>
  );
}
