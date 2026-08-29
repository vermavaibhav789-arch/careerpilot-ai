from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import User
from app.models.schemas import (
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    InterviewQuestion,
    TranscribeResponse,
    WeaknessReportResponse,
)
from app.plans import enforce_quota, increment_usage, require_feature
from app.services import analysis_store, interview_engine, llm_client, stt_client, tts_client

router = APIRouter(prefix="/api/interview", tags=["interview"])

MAX_AUDIO_MB = 15


@router.post("/questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    req: GenerateQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate interview questions grounded in this session's resume + JD."""
    record = analysis_store.get_session(db, req.session_id, current_user.id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="Session not found. Run /api/analyze first."
        )

    analysis = analysis_store.get_match_analysis(record)
    enforce_quota(current_user, "interview_questions_used", "max_interview_questions", req.num_questions)

    question_set = interview_engine.generate_questions(
        resume_text=record.resume_text,
        jd_text=record.jd_text,
        missing_skills=analysis.missing_skills,
        strong_areas=analysis.strong_areas,
        num_questions=req.num_questions,
        mode=req.mode,
    )

    analysis_store.store_questions(db, record, question_set.questions)
    increment_usage(db, current_user, "interview_questions_used", len(question_set.questions))

    return GenerateQuestionsResponse(questions=question_set.questions)


@router.post("/evaluate", response_model=EvaluateAnswerResponse)
async def evaluate_answer(
    req: EvaluateAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate a candidate's answer to a previously generated question.

    If this was a primary question (not itself a follow-up), also decides
    whether a real interviewer would probe deeper — if so, a follow-up
    question is generated, stored, and returned for the frontend to surface
    before moving on. Follow-ups are capped at one level: answering a
    follow-up never spawns another one.
    """
    record = analysis_store.get_session(db, req.session_id, current_user.id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="Session not found. Run /api/analyze first."
        )

    question = analysis_store.get_question(record, req.question_id)
    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Question not found. Generate questions via /api/interview/questions first.",
        )

    allow_followup = not analysis_store.is_followup(record, req.question_id)
    evaluation, followup_decision = interview_engine.evaluate(
        question, req.candidate_answer, allow_followup=allow_followup
    )
    analysis_store.store_evaluation(db, record, question, evaluation)

    followup_question = None
    if (
        followup_decision
        and followup_decision.needs_followup
        and followup_decision.followup_question.strip()
    ):
        followup_question = InterviewQuestion(
            id=f"{req.question_id}_followup",
            skill_area=question.skill_area,
            question=followup_decision.followup_question.strip(),
            difficulty=question.difficulty,
            based_on=f"Follow-up on your answer about {question.skill_area}",
        )
        analysis_store.store_followup(db, record, followup_question, req.question_id)

    return EvaluateAnswerResponse(evaluation=evaluation, followup=followup_question)


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Transcribe a recorded audio answer to text. Returns the transcript for
    the frontend to show (and let the candidate edit) before it's submitted
    to /api/interview/evaluate through the normal text path.
    """
    enforce_quota(current_user, "voice_actions_used", "max_voice_actions")

    content = await audio.read()
    if len(content) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"Audio file is too large (max {MAX_AUDIO_MB}MB)."
        )

    transcript = stt_client.transcribe(
        filename=audio.filename or "answer.webm",
        content=content,
        content_type=audio.content_type,
    )
    increment_usage(db, current_user, "voice_actions_used")
    return TranscribeResponse(transcript=transcript)


@router.get("/questions/{question_id}/audio")
async def question_audio(
    question_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Text-to-speech for a previously generated question, so it can be read
    aloud in the interview UI instead of only shown as text.
    """
    record = analysis_store.get_session(db, session_id, current_user.id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="Session not found. Run /api/analyze first."
        )

    question = analysis_store.get_question(record, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found.")

    enforce_quota(current_user, "voice_actions_used", "max_voice_actions")
    audio_bytes = tts_client.synthesize(question.question)
    increment_usage(db, current_user, "voice_actions_used")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.get("/{session_id}/weakness-report", response_model=WeaknessReportResponse)
async def weakness_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Summarize patterns across every question answered in this session so
    far - recurring strengths, recurring gaps, and specific study
    recommendations tied to those gaps. Needs at least one answered
    question to have anything to summarize.
    """
    record = analysis_store.get_session(db, session_id, current_user.id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="Session not found. Run /api/analyze first."
        )

    require_feature(current_user, "weakness_report")

    evaluations = record.evaluations or []
    if not evaluations:
        raise HTTPException(
            status_code=400,
            detail="No answered questions yet - answer at least one interview question first.",
        )

    analysis = llm_client.analyze_weaknesses(evaluations)
    return WeaknessReportResponse(analysis=analysis)
