"use client";

import { useEffect, useState } from "react";
import { getWeaknessReport } from "@/lib/api";
import type { WeaknessAnalysis } from "@/lib/types";

export default function WeaknessReport({ sessionId }: { sessionId: string }) {
  const [analysis, setAnalysis] = useState<WeaknessAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWeaknessReport(sessionId)
      .then((r) => setAnalysis(r.analysis))
      .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load report."))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <p className="loading-text">Summarizing your round…</p>;
  if (error) return <div className="error-banner">{error}</div>;
  if (!analysis) return null;

  return (
    <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--border)", textAlign: "left" }}>
      <p className="panel-label">Round summary</p>

      {analysis.strengths_shown.length > 0 && (
        <>
          <h4 className="tool-section-title">What came through well</h4>
          <ul className="change-list">
            {analysis.strengths_shown.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </>
      )}

      <h4 className="tool-section-title">Biggest gaps</h4>
      <ul className="change-list">
        {analysis.biggest_weaknesses.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>

      <h4 className="tool-section-title">Worth studying next</h4>
      <ul className="change-list">
        {analysis.recommended_learning.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>
    </div>
  );
}
