"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getPublicResume } from "@/lib/api";
import type { PublicResume } from "@/lib/types";

export default function PublicResumePage() {
  const params = useParams();
  const slug = typeof params.slug === "string" ? params.slug : "";

  const [resume, setResume] = useState<PublicResume | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    getPublicResume(slug)
      .then(setResume)
      .catch(() => setError("This resume isn't available. The link may be wrong or no longer shared."));
  }, [slug]);

  return (
    <main className="page">
      {error && <div className="error-banner">{error}</div>}
      {!resume && !error && <p className="loading-text">Loading…</p>}

      {resume && (
        <div className="panel">
          <p className="panel-label">{resume.label}</p>
          <pre className="public-resume-text">{resume.resume_text}</pre>
        </div>
      )}

      <p className="field-hint" style={{ marginTop: 20, textAlign: "center" }}>
        Shared via CareerPilot AI
      </p>
    </main>
  );
}
