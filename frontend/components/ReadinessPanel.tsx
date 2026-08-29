"use client";

import { useEffect, useState } from "react";
import { getReadiness } from "@/lib/api";
import type { ReadinessScore } from "@/lib/types";
import ScoreGauge from "./ScoreGauge";

export default function ReadinessPanel({
  sessionId,
  refreshKey,
}: {
  sessionId: string;
  refreshKey?: number;
}) {
  const [score, setScore] = useState<ReadinessScore | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getReadiness(sessionId)
      .then(setScore)
      .catch(() => setScore(null))
      .finally(() => setLoading(false));
    // refreshKey changes after each interview answer, so this re-fetches
    // and the readiness score updates as you practice.
  }, [sessionId, refreshKey]);

  if (loading) return <p className="loading-text">Loading readiness…</p>;
  if (!score) return null;

  const badgeClass =
    score.recommendation === "apply"
      ? "band-good"
      : score.recommendation === "improve"
        ? "band-warn"
        : "band-bad";
  const badgeLabel =
    score.recommendation === "apply"
      ? "Apply now"
      : score.recommendation === "improve"
        ? "Improve first"
        : "Consider other roles";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <ScoreGauge label="Overall readiness" value={score.overall} max={100} />
        <span className={`recommendation-badge ${badgeClass}`}>{badgeLabel}</span>
      </div>
      <div className="readiness-breakdown">
        <div>
          <span className="jd-expectation-label">Resume match</span>
          <span className="jd-expectation-value">{score.resume_match}/100</span>
        </div>
        <div>
          <span className="jd-expectation-label">Interview readiness</span>
          <span className="jd-expectation-value">
            {score.interview_readiness === null
              ? "Not practiced yet"
              : `${score.interview_readiness}/100 (${score.questions_answered} answered)`}
          </span>
        </div>
      </div>
      <p className="feedback-text" style={{ marginTop: 14 }}>{score.verdict}</p>
    </div>
  );
}
