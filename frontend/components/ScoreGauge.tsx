"use client";

interface ScoreGaugeProps {
  label: string;
  value: number;
  max: number;
  segments?: number;
  size?: "default" | "small";
}

function bandFor(ratio: number): "good" | "warn" | "bad" {
  if (ratio >= 0.7) return "good";
  if (ratio >= 0.4) return "warn";
  return "bad";
}

export default function ScoreGauge({
  label,
  value,
  max,
  segments = 20,
  size = "default",
}: ScoreGaugeProps) {
  const ratio = Math.max(0, Math.min(1, value / max));
  const band = bandFor(ratio);
  const filledCount = Math.round(ratio * segments);

  return (
    <div className="gauge-block">
      <div className="gauge-header">
        <span className="gauge-label">{label}</span>
        <span className={`gauge-value ${size === "small" ? "small" : ""} band-${band}`}>
          {value}
          <span style={{ color: "var(--text-dim)", fontWeight: 400 }}>/{max}</span>
        </span>
      </div>
      <div className={`gauge ${size === "small" ? "small" : ""}`}>
        {Array.from({ length: segments }).map((_, i) => (
          <div
            key={i}
            className={`gauge-tick ${i < filledCount ? `filled band-${band}` : ""}`}
          />
        ))}
      </div>
    </div>
  );
}
