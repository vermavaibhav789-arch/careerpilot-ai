"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeFromLibrary, deleteResume, listResumes, shareResume, unshareResume } from "@/lib/api";
import type { ResumeVersion } from "@/lib/types";
import RequireAuth from "@/components/RequireAuth";

function ResumeLibraryContent() {
  const router = useRouter();
  const [resumes, setResumes] = useState<ResumeVersion[] | null>(null);
  const [needsUpgrade, setNeedsUpgrade] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [shareUrls, setShareUrls] = useState<Record<string, string | null>>({});

  function load() {
    listResumes()
      .then(setResumes)
      .catch((err) => {
        const message = err instanceof Error ? err.message : "Couldn't load your resumes.";
        if (message.includes("Pro")) {
          setNeedsUpgrade(true);
        } else {
          setError(message);
        }
      });
  }

  useEffect(load, []);

  async function handleDelete(id: string) {
    try {
      await deleteResume(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't delete.");
    }
  }

  async function handleShareToggle(id: string, currentlyShared: boolean) {
    try {
      const result = currentlyShared ? await unshareResume(id) : await shareResume(id);
      setShareUrls((prev) => ({ ...prev, [id]: result.public_url }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't update sharing.");
    }
  }

  function copyLink(url: string) {
    navigator.clipboard.writeText(url);
  }

  async function handleAnalyze(e: React.FormEvent) {
    e.preventDefault();
    if (!analyzingId || !jobDescription.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await analyzeFromLibrary(analyzingId, jobDescription.trim());
      localStorage.setItem("careerpilot_session_id", result.session_id);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't analyze.");
      setSubmitting(false);
    }
  }

  if (needsUpgrade) {
    return (
      <main className="page">
        <div className="intro">
          <h1>Resume library</h1>
        </div>
        <div className="empty-state">
          <p style={{ marginBottom: 16 }}>The resume library is part of the Pro plan.</p>
          <a href="/pricing" className="btn btn-primary">
            See plans →
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="page">
      <div className="intro">
        <h1>Resume library</h1>
        <p>
          Save a resume once from any analysis, then reuse it against new job
          descriptions without re-uploading the file. Save a resume from the{" "}
          <a href="/" style={{ color: "var(--accent-warn)" }}>
            Analyze page
          </a>{" "}
          after running a match.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {resumes === null && <p className="loading-text">Loading…</p>}
      {resumes && resumes.length === 0 && <div className="empty-state">No saved resumes yet.</div>}

      {resumes && resumes.length > 0 && (
        <div className="applications-list">
          {resumes.map((r) => {
            const isShared = shareUrls[r.id] !== undefined ? !!shareUrls[r.id] : !!r.is_public;
            const url = shareUrls[r.id] !== undefined ? shareUrls[r.id] : null;
            return (
              <div key={r.id}>
                <div className="application-row">
                  <div className="application-main">
                    <p className="application-company">{r.label}</p>
                    <p className="application-role">
                      Saved {new Date(r.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    className="btn btn-small"
                    onClick={() => setAnalyzingId(analyzingId === r.id ? null : r.id)}
                  >
                    {analyzingId === r.id ? "Cancel" : "Analyze vs. new JD"}
                  </button>
                  <button className="btn btn-small" onClick={() => handleShareToggle(r.id, isShared)}>
                    {isShared ? "Unshare" : "Share"}
                  </button>
                  <button className="btn btn-small" onClick={() => handleDelete(r.id)}>
                    Delete
                  </button>
                </div>
                {isShared && url && (
                  <div className="share-row" style={{ marginLeft: 4, marginBottom: 8 }}>
                    <span className="share-url">{url}</span>
                    <button className="btn btn-small" onClick={() => copyLink(url)}>
                      Copy link
                    </button>
                  </div>
                )}
                {analyzingId === r.id && (
                  <form className="panel" onSubmit={handleAnalyze} style={{ marginTop: 8 }}>
                    <div className="field">
                      <label htmlFor="jd">Job description</label>
                      <textarea
                        id="jd"
                        rows={6}
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        placeholder="Paste the job description…"
                      />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                      {submitting ? "Analyzing…" : "Run analysis →"}
                    </button>
                  </form>
                )}
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}

export default function ResumeLibraryPage() {
  return (
    <RequireAuth>
      <ResumeLibraryContent />
    </RequireAuth>
  );
}
