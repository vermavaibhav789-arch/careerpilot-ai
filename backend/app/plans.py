"""
Plan definitions and enforcement.

No payment processing here - see routers/account.py for the upgrade
endpoint, which just flips a user's plan directly since there's no
Stripe/Razorpay integration yet. This module is the single source of truth
for what each plan unlocks, so the pricing page (frontend) and the actual
enforcement (backend) can't drift apart.

Usage limits are lifetime counters, not monthly - simpler to reason about
and test than a rolling/calendar reset window. Swapping to a monthly reset
later just means adding a `period_start` column and comparing against it
before checking the counter; the enforcement functions below wouldn't
change shape.

Voice usage is tracked as a count of voice actions (a transcription call or
a question-audio call), not literal seconds - measuring true audio duration
would need decoding the file (e.g. via pydub/ffmpeg), which is more
complexity than this stage of the product needs. Counting actions is an
honest, simple proxy: worth knowing about if you extend this.
"""

from typing import TypedDict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.db_models import User


class PlanLimits(TypedDict):
    max_analyses: int | None  # None = unlimited
    max_interview_questions: int | None
    max_voice_actions: int | None
    resume_optimizer: bool
    cover_letter: bool
    ats_check: bool
    readiness_score: bool
    weakness_report: bool
    application_tracker: bool
    resume_library: bool
    career_intelligence: bool


PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": {
        "max_analyses": 3,
        "max_interview_questions": 15,
        "max_voice_actions": 10,
        "resume_optimizer": False,
        "cover_letter": True,
        "ats_check": True,
        "readiness_score": True,
        "weakness_report": False,
        "application_tracker": False,
        "resume_library": False,
        "career_intelligence": False,
    },
    "pro": {
        "max_analyses": None,
        "max_interview_questions": None,
        "max_voice_actions": None,
        "resume_optimizer": True,
        "cover_letter": True,
        "ats_check": True,
        "readiness_score": True,
        "weakness_report": True,
        "application_tracker": True,
        "resume_library": True,
        "career_intelligence": True,
    },
}


def get_limits(user: User) -> PlanLimits:
    return PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])


def require_feature(user: User, feature: str) -> None:
    """Raise 402 if this plan doesn't include a boolean feature (e.g. 'resume_optimizer')."""
    if not get_limits(user)[feature]:  # type: ignore[literal-required]
        raise HTTPException(
            status_code=402,
            detail="This feature is part of the Pro plan. Upgrade to unlock it.",
        )


def increment_usage(db: Session, user: User, used_field: str, amount: int = 1) -> None:
    """Unconditionally increment a usage counter and commit. Call this AFTER the action succeeds."""
    setattr(user, used_field, getattr(user, used_field) + amount)
    db.add(user)
    db.commit()


def enforce_quota(user: User, used_field: str, limit_key: str, amount: int = 1) -> None:
    """Raise 402 if using `amount` more would exceed this plan's limit - a pure check, no mutation."""
    limit = get_limits(user)[limit_key]  # type: ignore[literal-required]
    current = getattr(user, used_field)

    if limit is not None and current + amount > limit:
        raise HTTPException(
            status_code=402,
            detail=(
                f"You've used {current}/{limit} on the free plan for this. "
                "Upgrade to Pro for more."
            ),
        )
