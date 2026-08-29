from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import User
from app.models.schemas import PlanLimitsResponse, UsageResponse
from app.plans import get_limits

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/usage", response_model=UsageResponse)
def usage(current_user: User = Depends(get_current_user)):
    limits = get_limits(current_user)
    return UsageResponse(
        plan=current_user.plan,
        limits=PlanLimitsResponse(**limits),
        analyses_used=current_user.analyses_used,
        interview_questions_used=current_user.interview_questions_used,
        voice_actions_used=current_user.voice_actions_used,
    )


@router.post("/upgrade", response_model=UsageResponse)
def upgrade(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Sets the account to Pro directly - there's no payment processing wired
    up yet (see the README), so this is a placeholder for where a real
    checkout-completion webhook would call the same plan update. Wiring in
    Stripe/Razorpay later means adding that webhook handler in front of
    this same "set plan and commit" logic, not replacing it.
    """
    current_user.plan = "pro"
    db.add(current_user)
    db.commit()

    limits = get_limits(current_user)
    return UsageResponse(
        plan=current_user.plan,
        limits=PlanLimitsResponse(**limits),
        analyses_used=current_user.analyses_used,
        interview_questions_used=current_user.interview_questions_used,
        voice_actions_used=current_user.voice_actions_used,
    )


@router.post("/downgrade", response_model=UsageResponse)
def downgrade(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.plan = "free"
    db.add(current_user)
    db.commit()

    limits = get_limits(current_user)
    return UsageResponse(
        plan=current_user.plan,
        limits=PlanLimitsResponse(**limits),
        analyses_used=current_user.analyses_used,
        interview_questions_used=current_user.interview_questions_used,
        voice_actions_used=current_user.voice_actions_used,
    )
