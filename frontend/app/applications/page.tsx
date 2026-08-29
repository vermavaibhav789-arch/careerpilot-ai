"use client";

import { useEffect, useState } from "react";
import {
  createApplication,
  deleteApplication,
  listApplications,
  updateApplication,
} from "@/lib/api";
import type { ApplicationStatus, JobApplication } from "@/lib/types";
import RequireAuth from "@/components/RequireAuth";

const STATUSES: ApplicationStatus[] = [
  "saved",
  "applied",
  "oa",
  "interview",
  "final_round",
  "offer",
  "rejected",
];

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  saved: "Saved",
  applied: "Applied",
  oa: "OA",
  interview: "Interview",
  final_round: "Final round",
  offer: "Offer",
  rejected: "Rejected",
};

function ApplicationsContent() {
  const [applications, setApplications] = useState<JobApplication[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsUpgrade, setNeedsUpgrade] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [view, setView] = useState<"list" | "kanban">("list");

  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [interviewDate, setInterviewDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function load() {
    listApplications()
      .then(setApplications)
      .catch((err) => {
        const message = err instanceof Error ? err.message : "Couldn't load applications.";
        if (message.includes("Pro")) {
          setNeedsUpgrade(true);
        } else {
          setError(message);
        }
      });
  }

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!company.trim() || !role.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createApplication({
        company: company.trim(),
        role: role.trim(),
        job_url: jobUrl.trim(),
        interview_date: interviewDate || null,
      });
      setCompany("");
      setRole("");
      setJobUrl("");
      setInterviewDate("");
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't add application.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStatusChange(id: string, status: ApplicationStatus) {
    try {
      await updateApplication(id, { status });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't update status.");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteApplication(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't delete.");
    }
  }

  if (needsUpgrade) {
    return (
      <main className="page">
        <div className="intro">
          <h1>Application tracker</h1>
        </div>
        <div className="empty-state">
          <p style={{ marginBottom: 16 }}>
            Career tracking is part of the Pro plan.
          </p>
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
        <h1>Application tracker</h1>
        <p>Keep track of where you've applied and how it's going.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        {!showForm ? (
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            + Add application
          </button>
        ) : (
          <span />
        )}
        <div className="mode-picker" style={{ marginBottom: 0 }}>
          <button
            type="button"
            className={`mode-option ${view === "list" ? "active" : ""}`}
            onClick={() => setView("list")}
          >
            List
          </button>
          <button
            type="button"
            className={`mode-option ${view === "kanban" ? "active" : ""}`}
            onClick={() => setView("kanban")}
          >
            Kanban
          </button>
        </div>
      </div>

      {showForm && (
        <form className="panel" onSubmit={handleCreate} style={{ marginBottom: 20 }}>
          <div className="field">
            <label htmlFor="company">Company</label>
            <input id="company" type="text" value={company} onChange={(e) => setCompany(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="role">Role</label>
            <input id="role" type="text" value={role} onChange={(e) => setRole(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="job_url">Job URL (optional)</label>
            <input id="job_url" type="text" value={jobUrl} onChange={(e) => setJobUrl(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="interview_date">Interview date (optional)</label>
            <input
              id="interview_date"
              type="datetime-local"
              value={interviewDate}
              onChange={(e) => setInterviewDate(e.target.value)}
            />
          </div>
          <div className="actions-row">
            <button type="button" className="btn" onClick={() => setShowForm(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Adding…" : "Add →"}
            </button>
          </div>
        </form>
      )}

      {applications === null && <p className="loading-text">Loading…</p>}

      {applications && applications.length === 0 && (
        <div className="empty-state">No applications tracked yet.</div>
      )}

      {applications && applications.length > 0 && view === "list" && (
        <div className="applications-list">
          {applications.map((app) => (
            <div className="application-row" key={app.id}>
              <div className="application-main">
                <p className="application-company">{app.company}</p>
                <p className="application-role">{app.role}</p>
                {app.interview_date && (
                  <p className="application-link" style={{ color: "var(--accent-warn)" }}>
                    Interview: {new Date(app.interview_date).toLocaleString()}
                  </p>
                )}
                {app.job_url && (
                  <a href={app.job_url} target="_blank" rel="noreferrer" className="application-link">
                    View posting ↗
                  </a>
                )}
              </div>
              <select
                className={`status-select status-${app.status}`}
                value={app.status}
                onChange={(e) => handleStatusChange(app.id, e.target.value as ApplicationStatus)}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {STATUS_LABELS[s]}
                  </option>
                ))}
              </select>
              <button className="btn btn-small" onClick={() => handleDelete(app.id)}>
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      {applications && applications.length > 0 && view === "kanban" && (
        <div className="kanban-board">
          {STATUSES.map((status) => {
            const apps = applications.filter((a) => a.status === status);
            return (
              <div className="kanban-column" key={status}>
                <p className={`kanban-column-header status-${status}`}>
                  {STATUS_LABELS[status]} · {apps.length}
                </p>
                {apps.map((app) => (
                  <div className="kanban-card" key={app.id}>
                    <p className="application-company">{app.company}</p>
                    <p className="application-role">{app.role}</p>
                    {app.interview_date && (
                      <p className="application-link" style={{ color: "var(--accent-warn)" }}>
                        {new Date(app.interview_date).toLocaleDateString()}
                      </p>
                    )}
                    <div className="kanban-card-actions">
                      <select
                        className="status-select"
                        value={app.status}
                        onChange={(e) => handleStatusChange(app.id, e.target.value as ApplicationStatus)}
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {STATUS_LABELS[s]}
                          </option>
                        ))}
                      </select>
                      <button className="btn btn-small" onClick={() => handleDelete(app.id)}>
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}

export default function ApplicationsPage() {
  return (
    <RequireAuth>
      <ApplicationsContent />
    </RequireAuth>
  );
}
