from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import JobApplication, User
from app.models.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    MessageResponse,
)
from app.plans import require_feature

router = APIRouter(prefix="/api/applications", tags=["applications"])


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {value!r}")


def _to_response(app: JobApplication) -> ApplicationResponse:
    return ApplicationResponse(
        id=app.id,
        company=app.company,
        role=app.role,
        job_url=app.job_url,
        status=app.status,
        notes=app.notes,
        session_id=app.session_id,
        interview_date=app.interview_date.isoformat() if app.interview_date else None,
        created_at=app.created_at.isoformat(),
        updated_at=app.updated_at.isoformat(),
    )


@router.post("", response_model=ApplicationResponse)
def create_application(
    req: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "application_tracker")

    app = JobApplication(
        user_id=current_user.id,
        company=req.company,
        role=req.role,
        job_url=req.job_url,
        status=req.status,
        notes=req.notes,
        session_id=req.session_id,
        interview_date=_parse_date(req.interview_date),
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _to_response(app)


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    require_feature(current_user, "application_tracker")

    apps = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == current_user.id)
        .order_by(JobApplication.updated_at.desc())
        .all()
    )
    return [_to_response(a) for a in apps]


def _get_owned(application_id: str, current_user: User, db: Session) -> JobApplication:
    app = (
        db.query(JobApplication)
        .filter(JobApplication.id == application_id, JobApplication.user_id == current_user.id)
        .first()
    )
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return app


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: str,
    req: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "application_tracker")
    app = _get_owned(application_id, current_user, db)

    updates = req.model_dump(exclude_unset=True)
    if "interview_date" in updates:
        updates["interview_date"] = _parse_date(updates["interview_date"])
    for field, value in updates.items():
        setattr(app, field, value)

    db.add(app)
    db.commit()
    db.refresh(app)
    return _to_response(app)


@router.delete("/{application_id}", response_model=MessageResponse)
def delete_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "application_tracker")
    app = _get_owned(application_id, current_user, db)

    db.delete(app)
    db.commit()
    return MessageResponse(message="Deleted.")
