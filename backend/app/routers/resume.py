from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import User
from app.models.schemas import (
    ATSCheckRequest,
    ATSCheckResponse,
    CoverLetterRequest,
    CoverLetterResponse,
    OptimizeResumeRequest,
    OptimizeResumeResponse,
    ReadinessScore,
    VerifyContentRequest,
    VerifyContentResponse,
)
from app.plans import require_feature
from app.services import analysis_store, llm_client

router = APIRouter(prefix="/api/resume", tags=["resume"])


def _get_owned_session(session_id: str, current_user: User, db: Session):
    record = analysis_store.get_session(db, session_id, current_user.id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="Session not found. Run /api/analyze first."
        )
    return record


@router.post("/optimize", response_model=OptimizeResumeResponse)
async def optimize(
    req: OptimizeResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Concrete before/after bullet rewrites for this resume against this JD.
    Never invents experience - see the prompt in llm_client.optimize_resume
    for the exact guardrail.
    """
    record = _get_owned_session(req.session_id, current_user, db)
    require_feature(current_user, "resume_optimizer")
    optimization = llm_client.optimize_resume(record.resume_text, record.jd_text)
    return OptimizeResumeResponse(optimization=optimization)


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def cover_letter(
    req: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a cover letter grounded in the actual resume and JD, in the requested tone."""
    record = _get_owned_session(req.session_id, current_user, db)
    letter = llm_client.generate_cover_letter(record.resume_text, record.jd_text, req.tone)
    return CoverLetterResponse(cover_letter=letter)


@router.post("/ats-check", response_model=ATSCheckResponse)
async def ats_check(
    req: ATSCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Heuristic ATS-compatibility checklist against well-documented parsing
    pitfalls. Deliberately NOT a fabricated precision score - there's no
    single ATS, so no single true score exists. See ATSChecklist's docstring.
    """
    record = _get_owned_session(req.session_id, current_user, db)
    checklist = llm_client.check_ats_compatibility(record.resume_text)
    return ATSCheckResponse(checklist=checklist)


@router.get("/{session_id}/readiness", response_model=ReadinessScore)
async def readiness(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Aggregate readiness score from resume match + interview performance so
    far. Computed directly from stored data, no extra LLM call - see
    analysis_store.compute_readiness for why (no fabricated sub-scores).
    """
    record = _get_owned_session(session_id, current_user, db)
    data = analysis_store.compute_readiness(record)
    return ReadinessScore(**data)


@router.post("/verify", response_model=VerifyContentResponse)
async def verify_content(
    req: VerifyContentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Truth Guard: an independent second AI pass that checks any generated
    text (from the resume optimizer, a section generator, a cover letter -
    or anything you paste in) against your actual resume, flagging claims
    it can't verify. This is a separate call from whatever generated the
    text, specifically instructed to be skeptical - defense in depth on
    top of the no-fabrication instructions already baked into generation.
    Free on every plan: safety checks shouldn't be a paywall.
    """
    record = _get_owned_session(req.session_id, current_user, db)
    report = llm_client.verify_against_source(req.generated_text, record.resume_text)
    return VerifyContentResponse(report=report)
