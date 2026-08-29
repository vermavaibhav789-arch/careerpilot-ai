"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDashboard } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import RequireAuth from "@/components/RequireAuth";
import ScoreGauge from "@/components/ScoreGauge";

const STATUS_LABELS: Record<string, string> = {
  saved: "Saved",
  applied: "Applied",
  oa: "OA",
  interview: "Interview",
  final_round: "Final round",
  offer: "Offer",
  rejected: "Rejected",
};

function DashboardContent() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load dashboard."));
  }, []);

  return (
    <main className="page">
      <div className="intro">
        <h1>Dashboard</h1>
        <p>Everything you've done across every session, in one place.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!data && !error && <p className="loading-text">Loading…</p>}

      {data && data.total_analyses === 0 && (
        <div className="empty-state">
          <p style={{ marginBottom: 16 }}>No analyses yet.</p>
          <Link href="/" className="btn btn-primary">
            Run your first analysis →
          </Link>
        </div>
      )}

      {data && data.total_analyses > 0 && (
        <>
          <div className="grid-two">
            <div className="panel">
              <p className="panel-label">Resume matching</p>
              {data.average_match_score !== null && (
                <ScoreGauge label="Average match score" value={Math.round(data.average_match_score)} max={100} />
              )}
              <p className="feedback-text" style={{ marginTop: 14 }}>
                {data.total_analyses} analysis{data.total_analyses === 1 ? "" : "es"} run so far.
              </p>
            </div>

            <div className="panel">
              <p className="panel-label">Interview practice</p>
              {data.average_interview_score !== null ? (
                <ScoreGauge
                  label="Average interview score"
                  value={Math.round(data.average_interview_score)}
                  max={100}
                />
              ) : (
                <div className="empty-state">No questions answered yet.</div>
              )}
              <p className="feedback-text" style={{ marginTop: 14 }}>
                {data.total_interview_questions_answered} question
                {data.total_interview_questions_answered === 1 ? "" : "s"} answered.
              </p>
            </div>
          </div>

          {Object.keys(data.applications_by_status).length > 0 && (
            <div className="panel">
              <p className="panel-label">Application funnel</p>
              <div className="usage-row" style={{ flexWrap: "wrap", gap: 16, borderTop: "none" }}>
                {Object.entries(data.applications_by_status).map(([status, count]) => (
                  <div key={status} className={`tag status-${status}`} style={{ padding: "8px 14px" }}>
                    {STATUS_LABELS[status] ?? status}: {count}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="panel">
            <p className="panel-label">Recent sessions</p>
            <div className="applications-list">
              {data.recent_sessions.map((s) => (
                <div className="application-row" key={s.session_id}>
                  <div className="application-main">
                    <p className="application-role">{s.jd_preview}</p>
                    <p className="application-link" style={{ color: "var(--text-dim)" }}>
                      {new Date(s.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <ScoreGauge label="Match" value={s.match_score} max={100} size="small" />
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </main>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}
