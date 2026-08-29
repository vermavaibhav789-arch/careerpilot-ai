from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.db import get_db
from app.models.db_models import User
from app.models.schemas import AnalyzeResponse
from app.plans import enforce_quota, increment_usage
from app.services import analysis_store, document_parser, llm_client

router = APIRouter(prefix="/api", tags=["analyze"])
settings = get_settings()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    resume: UploadFile,
    job_description: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a resume file + paste a job description. Returns a match score,
    missing skills, strong areas, recommended changes, a structured
    breakdown of the job description itself, and a session_id to use for
    follow-up chat and interview requests. The session is saved to this
    account and will still be there next time you log in.
    """
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is empty.")

    enforce_quota(current_user, "analyses_used", "max_analyses")

    content = await resume.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Resume file is too large (max {settings.max_upload_size_mb}MB).",
        )

    resume_text = document_parser.extract_text(resume.filename, content)
    analysis = llm_client.analyze_match(resume_text, job_description)
    job_intelligence = llm_client.extract_job_intelligence(job_description)

    session_id = analysis_store.create_session(
        db,
        user_id=current_user.id,
        resume_text=resume_text,
        jd_text=job_description,
        analysis=analysis,
        job_intelligence=job_intelligence,
    )
    increment_usage(db, current_user, "analyses_used")

    return AnalyzeResponse(
        session_id=session_id, analysis=analysis, job_intelligence=job_intelligence
    )
