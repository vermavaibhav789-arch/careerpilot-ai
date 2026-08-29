"use client";

import { useState } from "react";

interface UploadFormProps {
  onSubmit: (resume: File, jobDescription: string) => void;
  loading: boolean;
}

export default function UploadForm({ onSubmit, loading }: UploadFormProps) {
  const [resume, setResume] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");

  const canSubmit = resume !== null && jobDescription.trim().length > 0 && !loading;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (resume && jobDescription.trim()) {
      onSubmit(resume, jobDescription.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="resume-upload">Resume</label>
        <label className="file-drop" htmlFor="resume-upload">
          {resume ? (
            <>
              <strong>{resume.name}</strong> — click to change
            </>
          ) : (
            <>
              <strong>Choose a file</strong> — .pdf, .docx, or .txt
            </>
          )}
          <input
            id="resume-upload"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => setResume(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>

      <div className="field">
        <label htmlFor="jd-text">Job description</label>
        <textarea
          id="jd-text"
          rows={8}
          placeholder="Paste the full job description here…"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
        />
      </div>

      <button type="submit" className="btn btn-primary" disabled={!canSubmit}>
        {loading ? "Analyzing…" : "Run analysis →"}
      </button>
    </form>
  );
}
