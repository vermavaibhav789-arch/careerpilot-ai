"use client";

import type { MatchAnalysis } from "@/lib/types";
import ScoreGauge from "./ScoreGauge";

export default function MatchResults({ analysis }: { analysis: MatchAnalysis }) {
  return (
    <div>
      <ScoreGauge label="Match score" value={analysis.match_score} max={100} />

      <p className="summary-text" style={{ marginTop: 20 }}>
        {analysis.summary}
      </p>

      <div className="two-col-tags">
        <div>
          <h4>Strong areas</h4>
          <div className="tag-row">
            {analysis.strong_areas.map((s) => (
              <span className="tag tag-good" key={s}>
                ✓ {s}
              </span>
            ))}
          </div>
        </div>
        <div>
          <h4>Missing skills</h4>
          <div className="tag-row">
            {analysis.missing_skills.map((s) => (
              <span className="tag tag-bad" key={s}>
                {s}
              </span>
            ))}
          </div>
        </div>
      </div>

      <h4
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--text-dim)",
          margin: "0 0 4px",
          fontWeight: 500,
        }}
      >
        Recommended changes
      </h4>
      <ul className="change-list">
        {analysis.recommended_changes.map((c) => (
          <li key={c}>{c}</li>
        ))}
      </ul>
    </div>
  );
}
