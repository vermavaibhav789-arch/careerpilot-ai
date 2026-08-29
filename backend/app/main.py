from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.models import db_models  # noqa: F401 - import registers models with Base
from app.routers import (
    account,
    analyze,
    applications,
    auth,
    career,
    career_dna,
    chat,
    dashboard,
    generators,
    interview,
    resume,
    resume_library,
)

settings = get_settings()

# Creates tables that don't exist yet - safe to run every startup, never
# touches existing tables. For real schema changes later, use Alembic
# migrations instead of relying on this.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CareerPilot AI",
    description="AI-powered resume/JD matching and interview intelligence API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(interview.router)
app.include_router(resume.router)
app.include_router(resume_library.router)
app.include_router(applications.router)
app.include_router(account.router)
app.include_router(dashboard.router)
app.include_router(generators.router)
app.include_router(career.router)
app.include_router(career_dna.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
