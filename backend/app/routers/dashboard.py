from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import AnalysisSession, JobApplication, User
from app.models.schemas import DashboardResponse, RecentSession

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Aggregate stats across every session this account has, computed
    directly from stored data - no extra LLM call, same principle as the
    readiness score. Available on both plans; the numbers themselves will
    just be smaller on Free given the usage limits.
    """
    sessions = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.user_id == current_user.id)
        .order_by(AnalysisSession.created_at.desc())
        .all()
    )

    match_scores = [s.analysis["match_score"] for s in sessions if s.analysis]
    average_match_score = round(sum(match_scores) / len(match_scores), 1) if match_scores else None

    all_evaluations = [e for s in sessions for e in (s.evaluations or [])]
    total_questions_answered = len(all_evaluations)
    if all_evaluations:
        total_points = sum(
            e["technical_accuracy"] + e["completeness"] + e["communication"] for e in all_evaluations
        )
        average_interview_score = round((total_points / (total_questions_answered * 30)) * 100, 1)
    else:
        average_interview_score = None

    applications = (
        db.query(JobApplication).filter(JobApplication.user_id == current_user.id).all()
    )
    applications_by_status: dict[str, int] = {}
    for app in applications:
        applications_by_status[app.status] = applications_by_status.get(app.status, 0) + 1

    recent_sessions = [
        RecentSession(
            session_id=s.id,
            jd_preview=(s.jd_text[:80] + "…") if len(s.jd_text) > 80 else s.jd_text,
            match_score=s.analysis["match_score"] if s.analysis else 0,
            created_at=s.created_at.isoformat(),
        )
        for s in sessions[:5]
    ]

    return DashboardResponse(
        total_analyses=len(sessions),
        average_match_score=average_match_score,
        total_interview_questions_answered=total_questions_answered,
        average_interview_score=average_interview_score,
        applications_by_status=applications_by_status,
        recent_sessions=recent_sessions,
    )
