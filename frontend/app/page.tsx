"use client";

import { useState } from "react";
import { analyzeResume, saveResumeFromSession } from "@/lib/api";
import type { JobIntelligence, MatchAnalysis } from "@/lib/types";
import UploadForm from "@/components/UploadForm";
import MatchResults from "@/components/MatchResults";
import JobIntelligencePanel from "@/components/JobIntelligencePanel";
import ChatPanel from "@/components/ChatPanel";
import ResumeToolsPanel from "@/components/ResumeToolsPanel";
import ReadinessPanel from "@/components/ReadinessPanel";
import RequireAuth from "@/components/RequireAuth";

function SaveToLibrary({ sessionId }: { sessionId: string }) {
  const [label, setLabel] = useState("");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!label.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await saveResumeFromSession(sessionId, label.trim());
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't save (this is a Pro feature).");
    } finally {
      setSaving(false);
    }
  }

  if (saved) {
    return (
      <p className="feedback-text">
        Saved to your <a href="/resumes" style={{ color: "var(--accent-warn)" }}>resume library</a>.
      </p>
    );
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Name this resume version…"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
        <button className="btn" onClick={handleSave} disabled={saving || !label.trim()}>
          {saving ? "Saving…" : "Save to library"}
        </button>
      </div>
    </div>
  );
}

function AnalyzePageContent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<MatchAnalysis | null>(null);
  const [jobIntelligence, setJobIntelligence] = useState<JobIntelligence | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  async function handleSubmit(resume: File, jobDescription: string) {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeResume(resume, jobDescription);
      setAnalysis(result.analysis);
      setJobIntelligence(result.job_intelligence);
      setSessionId(result.session_id);
      if (typeof window !== "undefined") {
        localStorage.setItem("careerpilot_session_id", result.session_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div className="intro">
        <h1>Resume ↔ job description match</h1>
        <p>
          Upload your resume and paste a job description. CareerPilot scores
          your fit, flags gaps, and tells you exactly what to change —
          grounded in what's actually on the page, not generic advice.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-two">
        <div className="panel">
          <p className="panel-label">Input</p>
          <UploadForm onSubmit={handleSubmit} loading={loading} />
        </div>

        <div className="panel">
          <p className="panel-label">Readout</p>
          {analysis ? (
            <MatchResults analysis={analysis} />
          ) : (
            <div className="empty-state">
              {loading
                ? "Reading your resume against the job description…"
                : "Run an analysis to see your match score."}
            </div>
          )}
        </div>
      </div>

      {jobIntelligence && (
        <div className="panel">
          <p className="panel-label">About this job</p>
          <JobIntelligencePanel intel={jobIntelligence} />
        </div>
      )}

      {sessionId && analysis && (
        <div className="panel">
          <p className="panel-label">Readiness</p>
          <ReadinessPanel sessionId={sessionId} />
        </div>
      )}

      {sessionId && analysis && (
        <div className="panel">
          <p className="panel-label">Save this resume</p>
          <SaveToLibrary sessionId={sessionId} />
        </div>
      )}

      {sessionId && analysis && (
        <div className="panel">
          <p className="panel-label">Resume tools</p>
          <ResumeToolsPanel sessionId={sessionId} />
        </div>
      )}

      {sessionId && analysis && (
        <div className="panel">
          <ChatPanel sessionId={sessionId} />
        </div>
      )}
    </main>
  );
}

export default function AnalyzePage() {
  return (
    <RequireAuth>
      <AnalyzePageContent />
    </RequireAuth>
  );
}
