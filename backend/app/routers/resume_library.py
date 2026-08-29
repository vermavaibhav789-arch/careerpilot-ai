import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.db import get_db
from app.models.db_models import ResumeVersion, User
from app.models.schemas import (
    AnalyzeFromLibraryRequest,
    AnalyzeResponse,
    MessageResponse,
    PublicResumeResponse,
    ResumeVersionResponse,
    SaveResumeToLibraryRequest,
    ShareResumeResponse,
)
from app.plans import enforce_quota, increment_usage, require_feature
from app.services import analysis_store, llm_client

router = APIRouter(prefix="/api/resumes", tags=["resume-library"])
settings = get_settings()


def _to_response(rv: ResumeVersion) -> ResumeVersionResponse:
    return ResumeVersionResponse(
        id=rv.id,
        label=rv.label,
        resume_text=rv.resume_text,
        original_filename=rv.original_filename,
        created_at=rv.created_at.isoformat(),
    )


@router.post("/from-session", response_model=ResumeVersionResponse)
def save_from_session(
    req: SaveResumeToLibraryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the resume text from an already-analyzed session as a reusable, named library entry."""
    require_feature(current_user, "resume_library")

    record = analysis_store.get_session(db, req.session_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    resume_version = ResumeVersion(
        user_id=current_user.id,
        label=req.label,
        resume_text=record.resume_text,
    )
    db.add(resume_version)
    db.commit()
    db.refresh(resume_version)
    return _to_response(resume_version)


@router.get("", response_model=list[ResumeVersionResponse])
def list_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature(current_user, "resume_library")

    versions = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.user_id == current_user.id)
        .order_by(ResumeVersion.created_at.desc())
        .all()
    )
    return [_to_response(v) for v in versions]


@router.delete("/{resume_id}", response_model=MessageResponse)
def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "resume_library")

    version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == resume_id, ResumeVersion.user_id == current_user.id)
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Resume not found.")

    db.delete(version)
    db.commit()
    return MessageResponse(message="Deleted.")


def _get_owned_resume(resume_id: str, current_user: User, db: Session) -> ResumeVersion:
    version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == resume_id, ResumeVersion.user_id == current_user.id)
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return version


@router.post("/{resume_id}/share", response_model=ShareResumeResponse)
def share_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Make this resume viewable via a public, unguessable link - opt-in, and
    only the resume text is exposed (no account info). Anyone with the
    link can view it, same as sharing a Google Doc link; there's no access
    list or expiry yet (see README).
    """
    require_feature(current_user, "resume_library")
    version = _get_owned_resume(resume_id, current_user, db)

    if not version.public_slug:
        version.public_slug = secrets.token_urlsafe(12)
    version.is_public = True
    db.add(version)
    db.commit()

    return ShareResumeResponse(
        is_public=True,
        public_slug=version.public_slug,
        public_url=f"{settings.frontend_url}/r/{version.public_slug}",
    )


@router.post("/{resume_id}/unshare", response_model=ShareResumeResponse)
def unshare_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "resume_library")
    version = _get_owned_resume(resume_id, current_user, db)

    version.is_public = False
    db.add(version)
    db.commit()

    return ShareResumeResponse(is_public=False, public_slug=None, public_url=None)


@router.get("/public/{slug}", response_model=PublicResumeResponse)
def get_public_resume(slug: str, db: Session = Depends(get_db)):
    """No auth - this is the whole point. Only returns data for resumes explicitly marked public."""
    version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.public_slug == slug, ResumeVersion.is_public.is_(True))
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="This resume isn't available.")

    return PublicResumeResponse(label=version.label, resume_text=version.resume_text)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_from_library(
    req: AnalyzeFromLibraryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a match analysis against a saved resume and a new job description -
    no file upload needed. Same quota and downstream session behavior as
    /api/analyze; this just skips document parsing since the text is
    already stored.
    """
    require_feature(current_user, "resume_library")

    version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == req.resume_id, ResumeVersion.user_id == current_user.id)
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if not req.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is empty.")

    enforce_quota(current_user, "analyses_used", "max_analyses")

    analysis = llm_client.analyze_match(version.resume_text, req.job_description)
    job_intelligence = llm_client.extract_job_intelligence(req.job_description)

    session_id = analysis_store.create_session(
        db,
        user_id=current_user.id,
        resume_text=version.resume_text,
        jd_text=req.job_description,
        analysis=analysis,
        job_intelligence=job_intelligence,
    )
    increment_usage(db, current_user, "analyses_used")

    return AnalyzeResponse(
        session_id=session_id, analysis=analysis, job_intelligence=job_intelligence
    )
