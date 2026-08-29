"use client";

import type { JobIntelligence } from "@/lib/types";

export default function JobIntelligencePanel({ intel }: { intel: JobIntelligence }) {
  return (
    <div>
      <div className="two-col-tags">
        <div>
          <h4>Required</h4>
          <div className="tag-row">
            {intel.required_skills.length === 0 && (
              <span style={{ color: "var(--text-dim)", fontSize: 13 }}>None specified</span>
            )}
            {intel.required_skills.map((s) => (
              <span className="tag" key={s}>
                {s}
              </span>
            ))}
          </div>
        </div>
        <div>
          <h4>Preferred</h4>
          <div className="tag-row">
            {intel.preferred_skills.length === 0 && (
              <span style={{ color: "var(--text-dim)", fontSize: 13 }}>None specified</span>
            )}
            {intel.preferred_skills.map((s) => (
              <span className="tag" key={s} style={{ opacity: 0.75 }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="jd-expectations">
        <div>
          <span className="jd-expectation-label">Experience</span>
          <span className="jd-expectation-value">{intel.experience_level}</span>
        </div>
        <div>
          <span className="jd-expectation-label">Work mode</span>
          <span className="jd-expectation-value">{intel.work_mode}</span>
        </div>
        <div>
          <span className="jd-expectation-label">Location</span>
          <span className="jd-expectation-value">{intel.location}</span>
        </div>
      </div>

      {intel.hidden_signals.length > 0 && (
        <>
          <h4
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--text-dim)",
              margin: "20px 0 10px",
              fontWeight: 500,
            }}
          >
            Reading between the lines
          </h4>
          {intel.hidden_signals.map((signal) => (
            <div className="suggested-answer-box" key={signal} style={{ marginTop: 0, marginBottom: 10 }}>
              {signal}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
