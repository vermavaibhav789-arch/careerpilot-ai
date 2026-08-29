from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import CareerDNA, User
from app.models.schemas import (
    CareerMapRequest,
    CareerMapResponse,
    CareerSimulationRequest,
    CareerSimulationResponse,
    SalaryIntelligenceRequest,
    SalaryIntelligenceResponse,
)
from app.plans import require_feature
from app.services import analysis_store, llm_client

router = APIRouter(prefix="/api/career", tags=["career-intelligence"])


@router.post("/salary", response_model=SalaryIntelligenceResponse)
def salary_intelligence(
    req: SalaryIntelligenceRequest, current_user: User = Depends(get_current_user)
):
    """Real, web-search-grounded salary data for a role/location - not an LLM guess from training data."""
    require_feature(current_user, "career_intelligence")

    report = llm_client.get_salary_intelligence(req.role, req.location)
    return SalaryIntelligenceResponse(report=report)


@router.post("/map", response_model=CareerMapResponse)
def career_map(
    req: CareerMapRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A web-search-grounded path from the candidate's current background toward a target role."""
    require_feature(current_user, "career_intelligence")

    record = analysis_store.get_session(db, req.session_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found. Run /api/analyze first.")

    analysis = analysis_store.get_match_analysis(record)
    current_context = f"Strong areas: {', '.join(analysis.strong_areas)}. Currently exploring roles like the one in this session's job description."

    report = llm_client.get_career_map(record.resume_text, current_context, req.target_role)
    return CareerMapResponse(report=report)


@router.post("/simulate", response_model=CareerSimulationResponse)
def simulate_scenario(
    req: CareerSimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    "What if I..." scenario analysis - career change, relocation, learning
    a skill, accepting a job. Web-search-grounded, and explicitly framed
    as an informed estimate rather than a guarantee, since this is
    inherently speculative in a way salary/career-map lookups aren't.
    """
    require_feature(current_user, "career_intelligence")

    dna = db.query(CareerDNA).filter(CareerDNA.user_id == current_user.id).first()
    dna_context = ""
    if dna and (dna.skills or dna.target_roles):
        dna_context = (
            f"Current skills: {', '.join(dna.skills) or 'none recorded'}. "
            f"Target roles: {', '.join(dna.target_roles) or 'none recorded'}."
        )

    resume_text = None
    if req.session_id:
        record = analysis_store.get_session(db, req.session_id, current_user.id)
        if record is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        resume_text = record.resume_text

    report = llm_client.simulate_career_scenario(req.scenario, dna_context, resume_text)
    return CareerSimulationResponse(report=report)
