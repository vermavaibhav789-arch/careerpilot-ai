"use client";

import { useEffect, useState } from "react";
import { getCareerDNA, getCareerTwin, syncCareerDNAFromSession, updateCareerDNA } from "@/lib/api";
import type { CareerDNA, CareerTwin } from "@/lib/types";
import RequireAuth from "@/components/RequireAuth";
import ScoreGauge from "@/components/ScoreGauge";

function listToText(list: string[]): string {
  return list.join(", ");
}

function textToList(text: string): string[] {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function CareerDNAContent() {
  const [dna, setDna] = useState<CareerDNA | null>(null);
  const [twin, setTwin] = useState<CareerTwin | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Editable fields
  const [targetRoles, setTargetRoles] = useState("");
  const [targetIndustries, setTargetIndustries] = useState("");
  const [salaryExpectation, setSalaryExpectation] = useState("");
  const [locationPreference, setLocationPreference] = useState("");
  const [workModePreference, setWorkModePreference] = useState("");
  const [careerGoals, setCareerGoals] = useState("");

  function load() {
    getCareerDNA().then((d) => {
      setDna(d);
      setTargetRoles(listToText(d.target_roles));
      setTargetIndustries(listToText(d.target_industries));
      setSalaryExpectation(d.salary_expectation);
      setLocationPreference(d.location_preference);
      setWorkModePreference(d.work_mode_preference);
      setCareerGoals(d.career_goals);
    });
    getCareerTwin().then(setTwin).catch(() => {});
  }

  useEffect(() => {
    load();
    setSessionId(localStorage.getItem("careerpilot_session_id"));
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateCareerDNA({
        target_roles: textToList(targetRoles),
        target_industries: textToList(targetIndustries),
        salary_expectation: salaryExpectation,
        location_preference: locationPreference,
        work_mode_preference: workModePreference,
        career_goals: careerGoals,
      });
      setDna(updated);
      getCareerTwin().then(setTwin).catch(() => {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't save.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSync() {
    if (!sessionId) return;
    setSyncing(true);
    setError(null);
    try {
      const updated = await syncCareerDNAFromSession(sessionId);
      setDna(updated);
      getCareerTwin().then(setTwin).catch(() => {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't sync.");
    } finally {
      setSyncing(false);
    }
  }

  if (!dna) return <main className="page"><p className="loading-text">Loading…</p></main>;

  return (
    <main className="page">
      <div className="intro">
        <h1>Career DNA</h1>
        <p>
          Your persistent professional profile — carries across every
          resume and session, instead of starting over each time.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-two">
        <div className="panel">
          <p className="panel-label">Your profile</p>

          {sessionId && (
            <button className="btn" onClick={handleSync} disabled={syncing} style={{ marginBottom: 16 }}>
              {syncing ? "Syncing…" : "↻ Sync skills from latest analysis"}
            </button>
          )}

          {dna.skills.length > 0 && (
            <>
              <h4 className="tool-section-title">Skills</h4>
              <div className="tag-row" style={{ marginBottom: 14 }}>
                {dna.skills.map((s) => (
                  <span className="tag" key={s}>{s}</span>
                ))}
              </div>
            </>
          )}

          {dna.achievements.length > 0 && (
            <>
              <h4 className="tool-section-title">Achievements</h4>
              <ul className="change-list" style={{ marginBottom: 14 }}>
                {dna.achievements.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </>
          )}

          {dna.certifications.length > 0 && (
            <>
              <h4 className="tool-section-title">Certifications</h4>
              <div className="tag-row">
                {dna.certifications.map((c) => (
                  <span className="tag tag-good" key={c}>{c}</span>
                ))}
              </div>
            </>
          )}

          {dna.skills.length === 0 && dna.achievements.length === 0 && (
            <div className="empty-state">
              Nothing here yet — run an analysis, then sync it in.
            </div>
          )}
        </div>

        <div className="panel">
          <p className="panel-label">Preferences & goals</p>
          <form onSubmit={handleSave}>
            <div className="field">
              <label htmlFor="target-roles">Target roles (comma-separated)</label>
              <input id="target-roles" type="text" value={targetRoles} onChange={(e) => setTargetRoles(e.target.value)} placeholder="e.g. AI Engineer, ML Engineer" />
            </div>
            <div className="field">
              <label htmlFor="target-industries">Target industries</label>
              <input id="target-industries" type="text" value={targetIndustries} onChange={(e) => setTargetIndustries(e.target.value)} placeholder="e.g. Fintech, Healthcare" />
            </div>
            <div className="field">
              <label htmlFor="salary">Salary expectation</label>
              <input id="salary" type="text" value={salaryExpectation} onChange={(e) => setSalaryExpectation(e.target.value)} placeholder="e.g. 25-35 LPA" />
            </div>
            <div className="field">
              <label htmlFor="location">Location preference</label>
              <input id="location" type="text" value={locationPreference} onChange={(e) => setLocationPreference(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="work-mode">Work mode preference</label>
              <input id="work-mode" type="text" value={workModePreference} onChange={(e) => setWorkModePreference(e.target.value)} placeholder="e.g. Remote, Hybrid" />
            </div>
            <div className="field">
              <label htmlFor="goals">Career goals</label>
              <textarea id="goals" rows={3} value={careerGoals} onChange={(e) => setCareerGoals(e.target.value)} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save →"}
            </button>
          </form>
        </div>
      </div>

      {twin && (
        <div className="panel">
          <p className="panel-label">Career Twin — current vs. target</p>
          {twin.overall_readiness !== null && (
            <ScoreGauge label="Overall readiness toward target" value={twin.overall_readiness} max={100} />
          )}
          {twin.skill_gaps.length > 0 && (
            <>
              <h4 className="tool-section-title">Gaps toward your target role</h4>
              <div className="tag-row" style={{ marginBottom: 14 }}>
                {twin.skill_gaps.map((s) => (
                  <span className="tag tag-bad" key={s}>{s}</span>
                ))}
              </div>
            </>
          )}
          <p className="feedback-text">{twin.verdict}</p>
        </div>
      )}
    </main>
  );
}

export default function CareerDNAPage() {
  return (
    <RequireAuth>
      <CareerDNAContent />
    </RequireAuth>
  );
}
