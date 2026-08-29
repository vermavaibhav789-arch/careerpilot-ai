"""
Database models.

AnalysisSession replaces the old in-memory session_store dict - same idea
(one record per resume+JD analysis, holding chat history and interview
questions) but now a real row scoped to a user_id, so it survives a
restart and can't be read by anyone else.

Nested data (chat history, generated questions, which questions are
follow-ups) is stored as JSON columns rather than fully normalized tables.
That's a deliberate simplification: it keeps the migration from the old
dict-based store small while still being genuinely persistent and
per-user. Worth revisiting with proper child tables if querying into that
nested data (e.g. "find all questions about RAG across all sessions")
becomes a real requirement.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # JWT revocation: bump this to instantly invalidate every token issued
    # before now (logout-everywhere, and automatically on password reset).
    token_version: Mapped[int] = mapped_column(Integer, default=0)

    # Plan + usage. No payment processing - "pro" is set directly by
    # /api/account/upgrade for now. See app/plans.py for what each plan unlocks.
    plan: Mapped[str] = mapped_column(String, default="free")
    analyses_used: Mapped[int] = mapped_column(Integer, default=0)
    interview_questions_used: Mapped[int] = mapped_column(Integer, default=0)
    voice_actions_used: Mapped[int] = mapped_column(Integer, default=0)

    # Email verification (soft - tracked, not currently required to use the
    # app; see README for how to hard-gate specific routes on this).
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str | None] = mapped_column(String, nullable=True)
    verification_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Password reset
    reset_token: Mapped[str | None] = mapped_column(String, nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sessions: Mapped[list["AnalysisSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    resume_versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    career_dna: Mapped["CareerDNA | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    resume_text: Mapped[str] = mapped_column(String, nullable=False)
    jd_text: Mapped[str] = mapped_column(String, nullable=False)

    analysis: Mapped[dict] = mapped_column(JSON, nullable=False)
    job_intelligence: Mapped[dict] = mapped_column(JSON, nullable=False)

    chat_history: Mapped[list] = mapped_column(JSON, default=list)
    questions: Mapped[dict] = mapped_column(JSON, default=dict)  # question_id -> InterviewQuestion dict
    followup_of: Mapped[dict] = mapped_column(JSON, default=dict)  # followup_id -> parent question_id
    evaluations: Mapped[list] = mapped_column(JSON, default=list)  # list of evaluation records, one per answered question

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="sessions")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    company: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    job_url: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="saved")
    notes: Mapped[str] = mapped_column(String, default="")
    interview_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Optional link back to the match analysis this application came from,
    # so "add to tracker" from the Analyze page can carry the JD/resume
    # context forward without duplicating it.
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("analysis_sessions.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="applications")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    label: Mapped[str] = mapped_column(String, nullable=False)
    resume_text: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, default="")

    # Public sharing - opt-in, unguessable slug rather than the sequential id
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    public_slug: Mapped[str | None] = mapped_column(String, unique=True, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="resume_versions")


class CareerDNA(Base):
    """
    A persistent professional profile, separate from any single resume/JD
    session - the "who you are professionally" data that should carry
    across every analysis, interview round, and document you generate,
    rather than living and dying with one upload.

    One row per user. Nested lists stored as JSON columns, same pragmatic
    pattern as AnalysisSession - fine for "load the whole profile," would
    need real child tables if you ever need to query into these lists
    directly (e.g. "everyone with skill X").
    """

    __tablename__ = "career_dna"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)

    skills: Mapped[list] = mapped_column(JSON, default=list)
    achievements: Mapped[list] = mapped_column(JSON, default=list)
    certifications: Mapped[list] = mapped_column(JSON, default=list)
    target_roles: Mapped[list] = mapped_column(JSON, default=list)
    target_industries: Mapped[list] = mapped_column(JSON, default=list)

    experience_summary: Mapped[str] = mapped_column(String, default="")
    salary_expectation: Mapped[str] = mapped_column(String, default="")
    location_preference: Mapped[str] = mapped_column(String, default="")
    work_mode_preference: Mapped[str] = mapped_column(String, default="")
    career_goals: Mapped[str] = mapped_column(String, default="")

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="career_dna")
