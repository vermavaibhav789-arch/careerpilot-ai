from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import CareerDNA, User
from app.models.schemas import (
    CareerDNAResponse,
    CareerDNAUpdate,
    CareerTwinResponse,
    SyncCareerDNARequest,
)
from app.services import analysis_store, llm_client

router = APIRouter(prefix="/api/career-dna", tags=["career-dna"])


def _get_or_create(db: Session, user_id: str) -> CareerDNA:
    dna = db.query(CareerDNA).filter(CareerDNA.user_id == user_id).first()
    if dna is None:
        dna = CareerDNA(user_id=user_id)
        db.add(dna)
        db.commit()
        db.refresh(dna)
    return dna


def _to_response(dna: CareerDNA) -> CareerDNAResponse:
    return CareerDNAResponse(
        skills=dna.skills or [],
        achievements=dna.achievements or [],
        certifications=dna.certifications or [],
        target_roles=dna.target_roles or [],
        target_industries=dna.target_industries or [],
        experience_summary=dna.experience_summary,
        salary_expectation=dna.salary_expectation,
        location_preference=dna.location_preference,
        work_mode_preference=dna.work_mode_preference,
        career_goals=dna.career_goals,
        updated_at=dna.updated_at.isoformat(),
    )


def _merge_dedupe(existing: list[str], new: list[str]) -> list[str]:
    """Union of two lists, deduped case-insensitively, preserving first-seen order and original casing."""
    seen: dict[str, str] = {item.lower(): item for item in existing}
    for item in new:
        if item.lower() not in seen:
            seen[item.lower()] = item
    return list(seen.values())


@router.get("", response_model=CareerDNAResponse)
def get_career_dna(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Your persistent professional profile - available on every plan, since
    it's your own identity data, not a premium AI feature. Auto-created
    empty on first access.
    """
    dna = _get_or_create(db, current_user.id)
    return _to_response(dna)


@router.patch("", response_model=CareerDNAResponse)
def update_career_dna(
    req: CareerDNAUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dna = _get_or_create(db, current_user.id)

    updates = req.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(dna, field, value)

    db.add(dna)
    db.commit()
    db.refresh(dna)
    return _to_response(dna)


@router.post("/sync-from-session", response_model=CareerDNAResponse)
def sync_from_session(
    req: SyncCareerDNARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pull structured skills/achievements/certifications out of a resume
    you've already analyzed and merge them into your persistent profile -
    additive, deduped, never overwrites what's already there.
    """
    record = analysis_store.get_session(db, req.session_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    extraction = llm_client.extract_career_dna(record.resume_text)
    dna = _get_or_create(db, current_user.id)

    dna.skills = _merge_dedupe(dna.skills or [], extraction.skills)
    dna.achievements = _merge_dedupe(dna.achievements or [], extraction.achievements)
    dna.certifications = _merge_dedupe(dna.certifications or [], extraction.certifications)

    db.add(dna)
    db.commit()
    db.refresh(dna)
    return _to_response(dna)


@router.get("/twin", response_model=CareerTwinResponse)
def career_twin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    A computed snapshot combining Career DNA with your most recent
    analysis - "where you stand now vs. where you're aiming," built
    entirely from data that already exists elsewhere. Not a continuously
    running simulation; a fresh computation each time you ask.
    """
    dna = _get_or_create(db, current_user.id)

    from app.models.db_models import AnalysisSession  # local import to avoid a circular import at module load

    latest = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.user_id == current_user.id)
        .order_by(AnalysisSession.created_at.desc())
        .first()
    )

    skill_gaps: list[str] = []
    overall_readiness: int | None = None
    if latest is not None:
        skill_gaps = latest.analysis.get("missing_skills", []) if latest.analysis else []
        readiness_data = analysis_store.compute_readiness(latest)
        overall_readiness = readiness_data["overall"]

    if not dna.target_roles:
        verdict = "Add target roles to your Career DNA to get a real current-vs-target picture."
    elif not skill_gaps:
        verdict = "Run an analysis against a job description to see concrete skill gaps toward your target."
    else:
        verdict = f"Closing {len(skill_gaps)} skill gap(s) is the fastest path toward {dna.target_roles[0]}."

    return CareerTwinResponse(
        current_skills=dna.skills or [],
        target_roles=dna.target_roles or [],
        skill_gaps=skill_gaps,
        overall_readiness=overall_readiness,
        verdict=verdict,
    )
