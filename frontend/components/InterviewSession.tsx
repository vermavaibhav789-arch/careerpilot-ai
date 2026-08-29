"use client";

import { useState } from "react";
import { evaluateAnswer, generateInterviewQuestions } from "@/lib/api";
import type { AnswerEvaluation, InterviewMode, InterviewQuestion } from "@/lib/types";
import ScoreGauge from "./ScoreGauge";
import AudioRecorder from "./AudioRecorder";
import QuestionAudio from "./QuestionAudio";
import WeaknessReport from "./WeaknessReport";

type Status = "idle" | "loading-questions" | "ready" | "submitting" | "evaluated" | "complete";

const MODES: { value: InterviewMode; label: string }[] = [
  { value: "job_specific", label: "Job-specific" },
  { value: "technical", label: "Technical" },
  { value: "behavioral", label: "Behavioral" },
  { value: "hr", label: "HR round" },
];

export default function InterviewSession({ sessionId }: { sessionId: string }) {
  const [status, setStatus] = useState<Status>("idle");
  const [mode, setMode] = useState<InterviewMode>("job_specific");
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [index, setIndex] = useState(0);

  // The question currently being answered. Normally questions[index], but
  // temporarily swaps to a follow-up question when the interviewer probes
  // deeper on a weak answer.
  const [activeQuestion, setActiveQuestion] = useState<InterviewQuestion | null>(null);
  const [isFollowupActive, setIsFollowupActive] = useState(false);
  const [pendingFollowup, setPendingFollowup] = useState<InterviewQuestion | null>(null);

  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState<AnswerEvaluation | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function startInterview() {
    setStatus("loading-questions");
    setError(null);
    try {
      const { questions: qs } = await generateInterviewQuestions(sessionId, 5, mode);
      setQuestions(qs);
      setIndex(0);
      setActiveQuestion(qs[0] ?? null);
      setIsFollowupActive(false);
      setPendingFollowup(null);
      setAnswer("");
      setEvaluation(null);
      setStatus("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't generate questions.");
      setStatus("idle");
    }
  }

  async function submitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!activeQuestion || !answer.trim()) return;
    setStatus("submitting");
    setError(null);
    try {
      const result = await evaluateAnswer(sessionId, activeQuestion.id, answer.trim());
      setEvaluation(result.evaluation);
      setPendingFollowup(result.followup);
      setStatus("evaluated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't evaluate answer.");
      setStatus("ready");
    }
  }

  function answerFollowup() {
    if (!pendingFollowup) return;
    setActiveQuestion(pendingFollowup);
    setIsFollowupActive(true);
    setPendingFollowup(null);
    setAnswer("");
    setEvaluation(null);
    setStatus("ready");
  }

  function nextQuestion() {
    const nextIndex = index + 1;
    setIsFollowupActive(false);
    setPendingFollowup(null);
    if (nextIndex >= questions.length) {
      setStatus("complete");
      return;
    }
    setIndex(nextIndex);
    setActiveQuestion(questions[nextIndex]);
    setAnswer("");
    setEvaluation(null);
    setStatus("ready");
  }

  if (status === "idle") {
    return (
      <div className="empty-state">
        <p style={{ marginBottom: 16 }}>
          Generate interview questions grounded in your resume, this job
          description, and a curated bank of skill-specific interview
          questions retrieved via RAG. If an answer leaves something
          important unaddressed, CareerPilot will follow up on it — like a
          real interviewer would.
        </p>
        <div className="mode-picker">
          {MODES.map((m) => (
            <button
              key={m.value}
              type="button"
              className={`mode-option ${mode === m.value ? "active" : ""}`}
              onClick={() => setMode(m.value)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <button className="btn btn-primary" onClick={startInterview}>
          Start interview →
        </button>
      </div>
    );
  }

  if (status === "loading-questions") {
    return <p className="loading-text">Generating tailored questions…</p>;
  }

  if (status === "complete") {
    return (
      <div>
        <div className="empty-state">
          <p style={{ marginBottom: 16 }}>
            That's all {questions.length} questions. Nice work.
          </p>
          <button className="btn btn-primary" onClick={startInterview}>
            Start a new round →
          </button>
        </div>
        <WeaknessReport sessionId={sessionId} />
      </div>
    );
  }

  if (!activeQuestion) return null;

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}

      <div className="q-meta">
        <span className="q-index">
          Q {index + 1} / {questions.length}
          {isFollowupActive && " · follow-up"}
        </span>
        <span className="q-skill-tag">{activeQuestion.skill_area}</span>
        <span className="q-difficulty">{activeQuestion.difficulty}</span>
      </div>

      <p className="q-text">
        {isFollowupActive && "↳ "}
        {activeQuestion.question}
      </p>
      <QuestionAudio sessionId={sessionId} questionId={activeQuestion.id} />
      <p className="q-based-on">based on: {activeQuestion.based_on}</p>

      {status !== "evaluated" && (
        <form onSubmit={submitAnswer}>
          <AudioRecorder
            onTranscript={(text) => setAnswer(text)}
            disabled={status === "submitting"}
          />
          <div className="answer-divider">or type</div>
          <textarea
            className="answer-editor"
            placeholder="Type your answer, or record it above — either way you can edit before submitting…"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            disabled={status === "submitting"}
          />
          <div className="actions-row">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={status === "submitting" || !answer.trim()}
            >
              {status === "submitting" ? "Evaluating…" : "Submit answer →"}
            </button>
          </div>
        </form>
      )}

      {evaluation && (
        <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--border)" }}>
          <p className="panel-label" style={{ marginBottom: 16 }}>
            Evaluation
          </p>

          <div className="eval-dimensions">
            <ScoreGauge
              label="Technical accuracy"
              value={evaluation.technical_accuracy}
              max={10}
              size="small"
            />
            <ScoreGauge
              label="Completeness"
              value={evaluation.completeness}
              max={10}
              size="small"
            />
            <ScoreGauge
              label="Communication"
              value={evaluation.communication}
              max={10}
              size="small"
            />
          </div>

          {evaluation.missing_concepts.length > 0 && (
            <>
              <h4
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--text-dim)",
                  margin: "0 0 8px",
                  fontWeight: 500,
                }}
              >
                Missing concepts
              </h4>
              <div className="tag-row" style={{ marginBottom: 16 }}>
                {evaluation.missing_concepts.map((c) => (
                  <span className="tag tag-bad" key={c}>
                    {c}
                  </span>
                ))}
              </div>
            </>
          )}

          <p className="feedback-text">{evaluation.overall_feedback}</p>

          <div className="suggested-answer-box">
            <strong style={{ display: "block", marginBottom: 6, fontSize: 12 }}>
              Suggested answer
            </strong>
            {evaluation.suggested_answer}
          </div>

          {pendingFollowup ? (
            <div className="followup-prompt">
              <p className="followup-prompt-label">↳ CareerPilot wants to follow up</p>
              <p className="followup-prompt-text">{pendingFollowup.question}</p>
              <div className="actions-row">
                <button className="btn btn-primary" onClick={answerFollowup}>
                  Answer follow-up →
                </button>
              </div>
            </div>
          ) : (
            <div className="actions-row">
              <button className="btn btn-primary" onClick={nextQuestion}>
                Next question →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
