from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import User
from app.models.schemas import (
    GenerateDocumentRequest,
    GenerateDocumentResponse,
    GenerateSectionRequest,
    GenerateSectionResponse,
)
from app.plans import require_feature
from app.services import analysis_store, llm_client

router = APIRouter(prefix="/api/generate", tags=["generators"])


@router.post("/section", response_model=GenerateSectionResponse)
def generate_section(
    req: GenerateSectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Standalone resume content generation - headline, summary, objective,
    skills list, a single bullet, a fuller role description, or a STAR
    story. Same no-fabrication rule as the resume optimizer; gated behind
    the same plan feature since it's the same category of tool.
    """
    require_feature(current_user, "resume_optimizer")

    record = analysis_store.get_session(db, req.session_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found. Run /api/analyze first.")

    text = llm_client.generate_resume_section(
        resume_text=record.resume_text,
        jd_text=record.jd_text,
        section_type=req.section_type,
        context=req.context,
    )
    return GenerateSectionResponse(generated_text=text)


@router.post("/document", response_model=GenerateDocumentResponse)
def generate_document(
    req: GenerateDocumentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Career documents beyond the cover letter - resignation letters,
    professional bios, and job-search emails (thank-you, follow-up,
    networking, negotiation, offer response). Free-tier, same as the
    cover letter generator: low-cost, high-conversion-value tools.
    session_id is optional - only documents that benefit from resume/JD
    context use it; a resignation letter doesn't need either.
    """
    require_feature(current_user, "cover_letter")

    resume_text = jd_text = None
    if req.session_id:
        record = analysis_store.get_session(db, req.session_id, current_user.id)
        if record is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        resume_text, jd_text = record.resume_text, record.jd_text

    text = llm_client.generate_career_document(
        document_type=req.document_type,
        context=req.context,
        resume_text=resume_text,
        jd_text=jd_text,
    )
    return GenerateDocumentResponse(generated_text=text)
