"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import InterviewSession from "@/components/InterviewSession";
import RequireAuth from "@/components/RequireAuth";

function InterviewPageContent() {
  const [sessionId, setSessionId] = useState<string | null | undefined>(undefined);

  useEffect(() => {
    setSessionId(localStorage.getItem("careerpilot_session_id"));
  }, []);

  return (
    <main className="page">
      <div className="intro">
        <h1>Interview practice</h1>
        <p>
          Questions are generated from your resume and the job description,
          grounded by a retrieval-augmented knowledge base of skill-specific
          interview questions. Answers are scored on technical accuracy,
          completeness, and communication.
        </p>
      </div>

      <div className="panel">
        {sessionId === undefined && <p className="loading-text">Loading…</p>}

        {sessionId === null && (
          <div className="empty-state">
            <p>
              No active session yet. Run an analysis first so questions can
              be grounded in your actual resume and job description.
            </p>
            <Link href="/" className="btn btn-primary" style={{ display: "inline-block", marginTop: 16 }}>
              Go to Analyze →
            </Link>
          </div>
        )}

        {sessionId && <InterviewSession sessionId={sessionId} />}
      </div>
    </main>
  );
}

export default function InterviewPage() {
  return (
    <RequireAuth>
      <InterviewPageContent />
    </RequireAuth>
  );
}
