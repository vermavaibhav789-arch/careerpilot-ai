"use client";

import { useState } from "react";
import { checkATS, generateCoverLetter, generateDocument, generateSection, optimizeResume, verifyContent } from "@/lib/api";
import type { ATSChecklist, CoverLetterTone, DocumentType, ResumeOptimization, SectionType, TruthGuardReport } from "@/lib/types";

type Tab = "optimize" | "cover-letter" | "ats" | "sections" | "documents" | "truth-guard";

const TONES: CoverLetterTone[] = [
  "professional",
  "concise",
  "startup",
  "corporate",
  "technical",
  "enthusiastic",
];

const SECTION_TYPES: { value: SectionType; label: string; contextHint: string }[] = [
  { value: "headline", label: "Headline", contextHint: "" },
  { value: "summary", label: "Summary", contextHint: "" },
  { value: "objective", label: "Objective", contextHint: "" },
  { value: "skills_list", label: "Skills list", contextHint: "" },
  { value: "bullet", label: "Bullet point", contextHint: "e.g. 'led a team of 5, cut deploy time in half'" },
  { value: "work_experience_description", label: "Role description", contextHint: "e.g. 'backend engineer at a fintech startup for 2 years'" },
  { value: "star_story", label: "STAR story", contextHint: "e.g. 'a time a project was behind schedule and I...'" },
];

const DOCUMENT_TYPES: { value: DocumentType; label: string; needsSession: boolean }[] = [
  { value: "resignation_letter", label: "Resignation letter", needsSession: false },
  { value: "professional_bio", label: "Professional bio", needsSession: false },
  { value: "networking_email", label: "Networking email", needsSession: false },
  { value: "thank_you_email", label: "Interview thank-you", needsSession: true },
  { value: "follow_up_email", label: "Application follow-up", needsSession: true },
  { value: "salary_negotiation_email", label: "Salary negotiation", needsSession: true },
  { value: "offer_acceptance_email", label: "Offer acceptance", needsSession: true },
  { value: "offer_decline_email", label: "Offer decline", needsSession: true },
];

export default function ResumeToolsPanel({ sessionId }: { sessionId: string }) {
  const [tab, setTab] = useState<Tab>("optimize");

  return (
    <div>
      <div className="tool-tabs">
        <button className={`tool-tab ${tab === "optimize" ? "active" : ""}`} onClick={() => setTab("optimize")}>
          Optimize resume
        </button>
        <button className={`tool-tab ${tab === "sections" ? "active" : ""}`} onClick={() => setTab("sections")}>
          Write a section
        </button>
        <button className={`tool-tab ${tab === "cover-letter" ? "active" : ""}`} onClick={() => setTab("cover-letter")}>
          Cover letter
        </button>
        <button className={`tool-tab ${tab === "documents" ? "active" : ""}`} onClick={() => setTab("documents")}>
          Other documents
        </button>
        <button className={`tool-tab ${tab === "ats" ? "active" : ""}`} onClick={() => setTab("ats")}>
          ATS check
        </button>
        <button className={`tool-tab ${tab === "truth-guard" ? "active" : ""}`} onClick={() => setTab("truth-guard")}>
          Truth Guard
        </button>
      </div>

      {tab === "optimize" && <OptimizeTab sessionId={sessionId} />}
      {tab === "sections" && <SectionsTab sessionId={sessionId} />}
      {tab === "cover-letter" && <CoverLetterTab sessionId={sessionId} />}
      {tab === "documents" && <DocumentsTab sessionId={sessionId} />}
      {tab === "ats" && <ATSTab sessionId={sessionId} />}
      {tab === "truth-guard" && <TruthGuardTab sessionId={sessionId} />}
    </div>
  );
}

function OptimizeTab({ sessionId }: { sessionId: string }) {
  const [result, setResult] = useState<ResumeOptimization | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const { optimization } = await optimizeResume(sessionId);
      setResult(optimization);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't optimize resume.");
    } finally {
      setLoading(false);
    }
  }

  if (!result) {
    return (
      <div className="empty-state">
        {error && <div className="error-banner">{error}</div>}
        <p style={{ marginBottom: 16 }}>
          Get concrete before/after rewrites for your weakest bullets. This
          never invents experience — only rephrases, quantifies, or tells you
          exactly what information would make a bullet stronger.
        </p>
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? "Analyzing…" : "Optimize my resume →"}
        </button>
      </div>
    );
  }

  return (
    <div>
      <h4 className="tool-section-title">Improved summary</h4>
      <p className="suggested-answer-box">{result.improved_summary}</p>

      <h4 className="tool-section-title">Bullet rewrites</h4>
      {result.bullet_rewrites.map((b, i) => (
        <div className="bullet-rewrite" key={i}>
          <p className="bullet-original">{b.original}</p>
          <p className="bullet-improved">{b.improved}</p>
          <p className="bullet-note">{b.note}</p>
        </div>
      ))}

      {result.missing_keywords.length > 0 && (
        <>
          <h4 className="tool-section-title">Missing keywords</h4>
          <div className="tag-row" style={{ marginBottom: 16 }}>
            {result.missing_keywords.map((k) => (
              <span className="tag tag-bad" key={k}>
                {k}
              </span>
            ))}
          </div>
        </>
      )}

      {result.skills_section_suggestions.length > 0 && (
        <>
          <h4 className="tool-section-title">Add to your skills section</h4>
          <div className="tag-row">
            {result.skills_section_suggestions.map((s) => (
              <span className="tag" key={s}>
                {s}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function CoverLetterTab({ sessionId }: { sessionId: string }) {
  const [tone, setTone] = useState<CoverLetterTone>("professional");
  const [letter, setLetter] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const { cover_letter } = await generateCoverLetter(sessionId, tone);
      setLetter(cover_letter);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't generate cover letter.");
    } finally {
      setLoading(false);
    }
  }

  function copy() {
    if (!letter) return;
    navigator.clipboard.writeText(letter);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <div className="field">
        <label htmlFor="tone">Tone</label>
        <select
          id="tone"
          className="tone-select"
          value={tone}
          onChange={(e) => setTone(e.target.value as CoverLetterTone)}
        >
          {TONES.map((t) => (
            <option key={t} value={t}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </option>
          ))}
        </select>
      </div>
      <button className="btn btn-primary" onClick={run} disabled={loading}>
        {loading ? "Writing…" : letter ? "Regenerate →" : "Generate cover letter →"}
      </button>

      {letter && (
        <div style={{ marginTop: 18 }}>
          <div className="cover-letter-box">{letter}</div>
          <div className="actions-row">
            <button className="btn" onClick={copy}>
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ATSTab({ sessionId }: { sessionId: string }) {
  const [result, setResult] = useState<ATSChecklist | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const { checklist } = await checkATS(sessionId);
      setResult(checklist);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't run ATS check.");
    } finally {
      setLoading(false);
    }
  }

  if (!result) {
    return (
      <div className="empty-state">
        {error && <div className="error-banner">{error}</div>}
        <p style={{ marginBottom: 16 }}>
          A heuristic check against common, well-documented ATS parsing
          pitfalls — not a fabricated score. Real ATS software (Workday,
          Greenhouse, Taleo...) all parse differently, so treat this as
          "things worth fixing," not a guarantee.
        </p>
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? "Checking…" : "Run ATS check →"}
        </button>
      </div>
    );
  }

  return (
    <div>
      {result.items.map((item, i) => (
        <div className="ats-item" key={i}>
          <span className={`ats-status ats-${item.status}`}>
            {item.status === "pass" ? "✓" : item.status === "warning" ? "!" : "✕"}
          </span>
          <div>
            <p className="ats-check-name">{item.check}</p>
            <p className="ats-check-note">{item.note}</p>
          </div>
        </div>
      ))}
      <p className="field-hint" style={{ marginTop: 14 }}>{result.overall_note}</p>
    </div>
  );
}

function SectionsTab({ sessionId }: { sessionId: string }) {
  const [sectionType, setSectionType] = useState<SectionType>("headline");
  const [context, setContext] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = SECTION_TYPES.find((s) => s.value === sectionType)!;

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const { generated_text } = await generateSection(sessionId, sectionType, context);
      setResult(generated_text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't generate that (this is a Pro feature).");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <div className="field">
        <label htmlFor="section-type">What do you need?</label>
        <select
          id="section-type"
          className="tone-select"
          value={sectionType}
          onChange={(e) => setSectionType(e.target.value as SectionType)}
        >
          {SECTION_TYPES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="section-context">Details (optional for headline/summary/objective/skills)</label>
        <textarea
          id="section-context"
          rows={3}
          placeholder={selected.contextHint || "Any specifics to draw from…"}
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
      </div>
      <button className="btn btn-primary" onClick={run} disabled={loading}>
        {loading ? "Writing…" : "Generate →"}
      </button>

      {result && <div className="cover-letter-box" style={{ marginTop: 16 }}>{result}</div>}
    </div>
  );
}

function DocumentsTab({ sessionId }: { sessionId: string }) {
  const [documentType, setDocumentType] = useState<DocumentType>("resignation_letter");
  const [context, setContext] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const selected = DOCUMENT_TYPES.find((d) => d.value === documentType)!;

  async function run() {
    if (!context.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { generated_text } = await generateDocument(
        documentType,
        context.trim(),
        selected.needsSession ? sessionId : undefined
      );
      setResult(generated_text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't generate that.");
    } finally {
      setLoading(false);
    }
  }

  function copy() {
    if (!result) return;
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <div className="field">
        <label htmlFor="doc-type">Document</label>
        <select
          id="doc-type"
          className="tone-select"
          value={documentType}
          onChange={(e) => setDocumentType(e.target.value as DocumentType)}
        >
          {DOCUMENT_TYPES.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="doc-context">Specifics</label>
        <textarea
          id="doc-context"
          rows={3}
          placeholder="e.g. company name, last day, who to address it to, key details to include…"
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
      </div>
      <button className="btn btn-primary" onClick={run} disabled={loading || !context.trim()}>
        {loading ? "Writing…" : "Generate →"}
      </button>

      {result && (
        <div style={{ marginTop: 16 }}>
          <div className="cover-letter-box">{result}</div>
          <div className="actions-row">
            <button className="btn" onClick={copy}>
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function TruthGuardTab({ sessionId }: { sessionId: string }) {
  const [text, setText] = useState("");
  const [report, setReport] = useState<TruthGuardReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { report } = await verifyContent(sessionId, text.trim());
      setReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't verify.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <p style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 14 }}>
        Paste any AI-generated (or your own) resume text below. An independent
        pass checks every factual claim against your actual resume — not the
        same call that might have written it, and instructed to be skeptical.
      </p>
      <div className="field">
        <label htmlFor="verify-text">Text to check</label>
        <textarea
          id="verify-text"
          rows={5}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste a bullet, summary, or any generated text here…"
        />
      </div>
      <button className="btn btn-primary" onClick={run} disabled={loading || !text.trim()}>
        {loading ? "Checking…" : "Verify against my resume →"}
      </button>

      {report && (
        <div style={{ marginTop: 18 }}>
          <div className={`recommendation-badge ${report.passed ? "band-good" : "band-bad"}`} style={{ marginBottom: 14, display: "inline-block" }}>
            {report.passed ? "All claims supported" : "Unsupported claims found"}
          </div>
          {report.findings.map((f, i) => (
            <div className="ats-item" key={i}>
              <span className={`ats-status ${f.supported ? "ats-pass" : "ats-fail"}`}>
                {f.supported ? "✓" : "✕"}
              </span>
              <div>
                <p className="ats-check-name">{f.claim}</p>
                {!f.supported && <p className="ats-check-note">{f.concern}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
