"""
Replaces the old in-memory session_store.py with real, per-user persistent
storage. Same responsibilities (hold resume/JD text, match analysis, chat
history, generated interview questions) but backed by the AnalysisSession
table instead of a dict that forgot everything on restart.

Every read here is scoped by user_id - get_session returns None if the
session exists but belongs to someone else, which routers treat as a plain
404. That's deliberate: a 403 would confirm the session_id exists at all,
leaking information to someone probing IDs that aren't theirs.
"""

from sqlalchemy.orm import Session

from app.models.db_models import AnalysisSession
from app.models.schemas import InterviewQuestion, JobIntelligence, MatchAnalysis


def create_session(
    db: Session,
    user_id: str,
    resume_text: str,
    jd_text: str,
    analysis: MatchAnalysis,
    job_intelligence: JobIntelligence,
) -> str:
    record = AnalysisSession(
        user_id=user_id,
        resume_text=resume_text,
        jd_text=jd_text,
        analysis=analysis.model_dump(),
        job_intelligence=job_intelligence.model_dump(),
        chat_history=[],
        questions={},
        followup_of={},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.id


def get_session(db: Session, session_id: str, user_id: str) -> AnalysisSession | None:
    return (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == user_id)
        .first()
    )


def get_match_analysis(record: AnalysisSession) -> MatchAnalysis:
    return MatchAnalysis(**record.analysis)


def append_chat(db: Session, record: AnalysisSession, role: str, content: str) -> None:
    history = list(record.chat_history or [])
    history.append({"role": role, "content": content})
    record.chat_history = history  # reassign (not mutate) so SQLAlchemy detects the change
    db.add(record)
    db.commit()


def store_questions(db: Session, record: AnalysisSession, questions: list[InterviewQuestion]) -> None:
    q_map = dict(record.questions or {})
    for q in questions:
        q_map[q.id] = q.model_dump()
    record.questions = q_map
    db.add(record)
    db.commit()


def get_question(record: AnalysisSession, question_id: str) -> InterviewQuestion | None:
    data = (record.questions or {}).get(question_id)
    return InterviewQuestion(**data) if data else None


def store_followup(
    db: Session, record: AnalysisSession, followup: InterviewQuestion, parent_question_id: str
) -> None:
    q_map = dict(record.questions or {})
    q_map[followup.id] = followup.model_dump()
    record.questions = q_map

    f_map = dict(record.followup_of or {})
    f_map[followup.id] = parent_question_id
    record.followup_of = f_map

    db.add(record)
    db.commit()


def is_followup(record: AnalysisSession, question_id: str) -> bool:
    return question_id in (record.followup_of or {})


def store_evaluation(
    db: Session,
    record: AnalysisSession,
    question: InterviewQuestion,
    evaluation,  # AnswerEvaluation - avoiding the import here to dodge a circular import
) -> None:
    evals = list(record.evaluations or [])
    evals.append(
        {
            "question_id": question.id,
            "skill_area": question.skill_area,
            "question": question.question,
            "technical_accuracy": evaluation.technical_accuracy,
            "completeness": evaluation.completeness,
            "communication": evaluation.communication,
            "missing_concepts": evaluation.missing_concepts,
        }
    )
    record.evaluations = evals
    db.add(record)
    db.commit()


def compute_readiness(record: AnalysisSession) -> dict:
    """
    Computed entirely from data already on hand - no extra LLM call needed,
    and no fabricated sub-scores that don't correspond to a real signal
    (see the ATS checklist for the same principle applied elsewhere).
    """
    analysis = get_match_analysis(record)
    evals = record.evaluations or []

    interview_readiness = None
    if evals:
        total = sum(e["technical_accuracy"] + e["completeness"] + e["communication"] for e in evals)
        interview_readiness = round((total / (len(evals) * 30)) * 100)

    if interview_readiness is None:
        overall = analysis.match_score
        verdict = (
            f"Your resume match is {analysis.match_score}/100. Practice a few "
            "interview questions to get a fuller readiness picture."
        )
    else:
        overall = round((analysis.match_score + interview_readiness) / 2)
        if overall >= 80:
            verdict = "Strong on both fronts - you're in good shape to apply and interview."
        elif overall >= 60:
            verdict = "Solid foundation. Sharpening your interview answers would move the needle most."
        else:
            verdict = "Worth closing some resume/skill gaps before applying, and getting more practice reps in."

    # A simple, deterministic classification from the same numbers above -
    # no extra LLM call, same principle as the rest of this function.
    if overall >= 75:
        recommendation = "apply"
    elif overall >= 45:
        recommendation = "improve"
    else:
        recommendation = "skip"

    return {
        "overall": overall,
        "resume_match": analysis.match_score,
        "interview_readiness": interview_readiness,
        "questions_answered": len(evals),
        "recommendation": recommendation,
        "verdict": verdict,
    }
