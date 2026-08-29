from typing import Literal

from pydantic import BaseModel, EmailStr, Field

InterviewMode = Literal["technical", "behavioral", "hr", "job_specific"]

# ---------------------------------------------------------------------------
# Resume / JD matching
# ---------------------------------------------------------------------------


class MatchAnalysis(BaseModel):
    """
    Structured result of comparing a resume against a job description.
    This exact shape is what we ask Claude to return via structured outputs,
    so the API never has to guess-parse free text.
    """

    match_score: int = Field(..., ge=0, le=100, description="Overall fit, 0-100")
    missing_skills: list[str] = Field(
        ..., description="Skills the JD wants that the resume doesn't evidence"
    )
    strong_areas: list[str] = Field(
        ..., description="Skills/experience the resume clearly demonstrates that the JD wants"
    )
    recommended_changes: list[str] = Field(
        ..., description="Concrete, actionable edits to improve the resume for this JD"
    )
    summary: str = Field(..., description="2-3 sentence plain-language verdict")


class JobIntelligence(BaseModel):
    """
    Structured breakdown of the job description itself, independent of any
    specific resume — what it actually requires versus prefers, expectations
    it sets, and what it emphasizes beyond its literal skill list.
    """

    required_skills: list[str] = Field(..., description="Skills the JD explicitly requires")
    preferred_skills: list[str] = Field(
        ..., description="Skills listed as nice-to-have / preferred, not required"
    )
    experience_level: str = Field(
        ..., description="e.g. '2+ years', 'Entry level', or 'Not specified'"
    )
    work_mode: str = Field(..., description="e.g. 'Remote', 'Hybrid', 'Onsite', or 'Not specified'")
    location: str = Field(..., description="e.g. 'Bangalore, India', or 'Not specified'")
    hidden_signals: list[str] = Field(
        ...,
        description=(
            "What the JD emphasizes beyond its literal skill list - e.g. heavy "
            "focus on production deployment even though a cloud platform is "
            "only listed as 'preferred'. Empty list if nothing notable."
        ),
    )


class AnalyzeResponse(BaseModel):
    session_id: str
    analysis: MatchAnalysis
    job_intelligence: JobIntelligence


# ---------------------------------------------------------------------------
# Chat ("why am I not a good match?")
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str


# ---------------------------------------------------------------------------
# Interview questions
# ---------------------------------------------------------------------------


class InterviewQuestion(BaseModel):
    id: str
    skill_area: str = Field(..., description="e.g. 'RAG', 'FastAPI', 'System design'")
    question: str
    difficulty: Literal["junior", "mid", "senior"]
    based_on: str = Field(
        ..., description="Which resume/JD detail this question was grounded in"
    )


class InterviewQuestionSet(BaseModel):
    questions: list[InterviewQuestion]


class GenerateQuestionsRequest(BaseModel):
    session_id: str
    num_questions: int = Field(default=5, ge=1, le=10)
    mode: InterviewMode = "job_specific"


class GenerateQuestionsResponse(BaseModel):
    questions: list[InterviewQuestion]


# ---------------------------------------------------------------------------
# Interview answer evaluation
# ---------------------------------------------------------------------------


class AnswerEvaluation(BaseModel):
    technical_accuracy: int = Field(..., ge=0, le=10)
    completeness: int = Field(..., ge=0, le=10)
    communication: int = Field(..., ge=0, le=10)
    missing_concepts: list[str]
    suggested_answer: str
    overall_feedback: str


class EvaluateAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    candidate_answer: str


class EvaluateAnswerResponse(BaseModel):
    evaluation: AnswerEvaluation
    followup: InterviewQuestion | None = None


class FollowUpDecision(BaseModel):
    """
    Internal LLM output for deciding whether a real interviewer would probe
    deeper on this answer. Always returns a string (empty if unused) rather
    than an Optional field, since that's more reliable with structured
    outputs than a nullable field.
    """

    needs_followup: bool
    followup_question: str = ""


# ---------------------------------------------------------------------------
# Audio interview answers
# ---------------------------------------------------------------------------


class TranscribeResponse(BaseModel):
    transcript: str


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="At least 8 characters")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str


class UserResponse(BaseModel):
    id: str
    email: str


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# ---------------------------------------------------------------------------
# Job application tracker
# ---------------------------------------------------------------------------

ApplicationStatus = Literal[
    "saved", "applied", "oa", "interview", "final_round", "offer", "rejected"
]


class ApplicationCreate(BaseModel):
    company: str
    role: str
    job_url: str = ""
    status: ApplicationStatus = "saved"
    notes: str = ""
    session_id: str | None = None
    interview_date: str | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = None
    role: str | None = None
    job_url: str | None = None
    status: ApplicationStatus | None = None
    notes: str | None = None
    interview_date: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    company: str
    role: str
    job_url: str
    status: ApplicationStatus
    notes: str
    session_id: str | None
    interview_date: str | None
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Plans / usage (no payment processing - see app/plans.py)
# ---------------------------------------------------------------------------


class PlanLimitsResponse(BaseModel):
    max_analyses: int | None
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


class UsageResponse(BaseModel):
    plan: str
    limits: PlanLimitsResponse
    analyses_used: int
    interview_questions_used: int
    voice_actions_used: int


# ---------------------------------------------------------------------------
# Resume library
# ---------------------------------------------------------------------------


class SaveResumeToLibraryRequest(BaseModel):
    session_id: str
    label: str


class ResumeVersionResponse(BaseModel):
    id: str
    label: str
    resume_text: str
    original_filename: str
    created_at: str


class AnalyzeFromLibraryRequest(BaseModel):
    resume_id: str
    job_description: str


class ShareResumeResponse(BaseModel):
    is_public: bool
    public_slug: str | None
    public_url: str | None


class PublicResumeResponse(BaseModel):
    label: str
    resume_text: str


# ---------------------------------------------------------------------------
# Career intelligence (web-search-grounded, not LLM guesses)
# ---------------------------------------------------------------------------


class SalaryIntelligenceRequest(BaseModel):
    role: str
    location: str = "Remote"


class SalaryIntelligenceResponse(BaseModel):
    report: str


class CareerMapRequest(BaseModel):
    session_id: str
    target_role: str


class CareerMapResponse(BaseModel):
    report: str


class CareerSimulationRequest(BaseModel):
    session_id: str | None = Field(
        default=None, description="Optional - grounds the simulation in a specific resume if provided"
    )
    scenario: str = Field(
        ..., description="e.g. 'What if I switch to AI engineering?' or 'What if I relocate to Berlin?'"
    )


class CareerSimulationResponse(BaseModel):
    report: str


# ---------------------------------------------------------------------------
# Career DNA - persistent professional profile
# ---------------------------------------------------------------------------


class CareerDNAResponse(BaseModel):
    skills: list[str]
    achievements: list[str]
    certifications: list[str]
    target_roles: list[str]
    target_industries: list[str]
    experience_summary: str
    salary_expectation: str
    location_preference: str
    work_mode_preference: str
    career_goals: str
    updated_at: str


class CareerDNAUpdate(BaseModel):
    skills: list[str] | None = None
    achievements: list[str] | None = None
    certifications: list[str] | None = None
    target_roles: list[str] | None = None
    target_industries: list[str] | None = None
    experience_summary: str | None = None
    salary_expectation: str | None = None
    location_preference: str | None = None
    work_mode_preference: str | None = None
    career_goals: str | None = None


class SyncCareerDNARequest(BaseModel):
    session_id: str


class CareerDNAExtraction(BaseModel):
    """Internal LLM output for pulling structured facts out of a resume to merge into Career DNA."""

    skills: list[str]
    achievements: list[str]
    certifications: list[str]


class CareerTwinResponse(BaseModel):
    current_skills: list[str]
    target_roles: list[str]
    skill_gaps: list[str]
    overall_readiness: int | None
    verdict: str


# ---------------------------------------------------------------------------
# Truth Guard - independent verification of generated content
# ---------------------------------------------------------------------------


class TruthGuardFinding(BaseModel):
    claim: str = Field(..., description="The specific factual claim being checked")
    supported: bool
    concern: str = Field(default="", description="Explanation if unsupported, empty string if supported")


class TruthGuardReport(BaseModel):
    passed: bool = Field(..., description="True only if every claim found is supported by the source resume")
    findings: list[TruthGuardFinding]


class VerifyContentRequest(BaseModel):
    session_id: str
    generated_text: str = Field(..., description="The AI-generated text to independently fact-check")


class VerifyContentResponse(BaseModel):
    report: TruthGuardReport


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class RecentSession(BaseModel):
    session_id: str
    jd_preview: str
    match_score: int
    created_at: str


class DashboardResponse(BaseModel):
    total_analyses: int
    average_match_score: float | None
    total_interview_questions_answered: int
    average_interview_score: float | None
    applications_by_status: dict[str, int]
    recent_sessions: list[RecentSession]


# ---------------------------------------------------------------------------
# Resume section generator (headline, summary, bullets, STAR stories, etc.)
# ---------------------------------------------------------------------------

SectionType = Literal[
    "headline",
    "summary",
    "objective",
    "skills_list",
    "bullet",
    "work_experience_description",
    "star_story",
]


class GenerateSectionRequest(BaseModel):
    session_id: str
    section_type: SectionType
    context: str = Field(
        default="",
        description="Freeform input, e.g. raw accomplishment details for a bullet or STAR story. Can be blank for headline/summary/skills_list, which draw from the resume+JD alone.",
    )


class GenerateSectionResponse(BaseModel):
    generated_text: str


# ---------------------------------------------------------------------------
# Other career documents (resignation letter, professional bio, emails)
# ---------------------------------------------------------------------------

DocumentType = Literal[
    "resignation_letter",
    "professional_bio",
    "thank_you_email",
    "follow_up_email",
    "networking_email",
    "salary_negotiation_email",
    "offer_acceptance_email",
    "offer_decline_email",
]


class GenerateDocumentRequest(BaseModel):
    session_id: str | None = Field(
        default=None,
        description="Optional - only needed for documents that should be grounded in a specific resume/JD (e.g. follow_up_email). Resignation letters etc. work from context alone.",
    )
    document_type: DocumentType
    context: str = Field(
        ..., description="Specifics for this document - company name, last day, reason for follow-up, etc."
    )


class GenerateDocumentResponse(BaseModel):
    generated_text: str


# ---------------------------------------------------------------------------
# Resume optimizer
# ---------------------------------------------------------------------------


class BulletRewrite(BaseModel):
    original: str = Field(..., description="The candidate's actual original bullet")
    improved: str = Field(
        ...,
        description=(
            "Rewritten version - stronger structure/wording/quantification. "
            "Must not add any accomplishment, metric, or tool not implied by "
            "the original. If a genuine improvement would require information "
            "the candidate didn't provide, say so in the note instead of inventing it."
        ),
    )
    note: str = Field(..., description="Why this is better, or what info would strengthen it further")


class ResumeOptimization(BaseModel):
    improved_summary: str = Field(
        ..., description="A stronger professional summary, built only from what the resume states"
    )
    bullet_rewrites: list[BulletRewrite]
    missing_keywords: list[str] = Field(
        ..., description="JD terms/skills not present in the resume, worth adding if genuinely true"
    )
    skills_section_suggestions: list[str] = Field(
        ..., description="Specific skills to add to a skills section, IF the candidate actually has them per the resume"
    )


class OptimizeResumeRequest(BaseModel):
    session_id: str


class OptimizeResumeResponse(BaseModel):
    optimization: ResumeOptimization


# ---------------------------------------------------------------------------
# Cover letter generator
# ---------------------------------------------------------------------------

CoverLetterTone = Literal["professional", "concise", "startup", "corporate", "technical", "enthusiastic"]


class CoverLetterRequest(BaseModel):
    session_id: str
    tone: CoverLetterTone = "professional"


class CoverLetterResponse(BaseModel):
    cover_letter: str


# ---------------------------------------------------------------------------
# ATS compatibility checklist (heuristic, honestly labeled - not a fake score)
# ---------------------------------------------------------------------------


class ATSCheckItem(BaseModel):
    check: str = Field(..., description="What was checked, e.g. 'Standard section headers'")
    status: Literal["pass", "warning", "fail"]
    note: str = Field(..., description="Specific, concrete explanation - not generic advice")


class ATSChecklist(BaseModel):
    items: list[ATSCheckItem]
    overall_note: str = Field(
        ...,
        description=(
            "Honest framing - e.g. that ATS behavior varies by vendor and this "
            "is a heuristic check against common, well-documented parsing pitfalls, "
            "not a guaranteed score from any specific ATS."
        ),
    )


class ATSCheckRequest(BaseModel):
    session_id: str


class ATSCheckResponse(BaseModel):
    checklist: ATSChecklist


# ---------------------------------------------------------------------------
# Interview modes
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Readiness score - computed from existing data, no extra LLM call needed
# ---------------------------------------------------------------------------


class ReadinessScore(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    resume_match: int = Field(..., ge=0, le=100, description="Same as the match analysis score")
    interview_readiness: int | None = Field(
        None, ge=0, le=100, description="Average interview performance so far, null if no questions answered yet"
    )
    questions_answered: int
    recommendation: Literal["apply", "improve", "skip"]
    verdict: str


# ---------------------------------------------------------------------------
# Weakness analysis + learning recommendations
# ---------------------------------------------------------------------------


class WeaknessAnalysis(BaseModel):
    strengths_shown: list[str] = Field(..., description="What came through well across the answered questions")
    biggest_weaknesses: list[str] = Field(..., description="Specific recurring gaps, not vague categories")
    recommended_learning: list[str] = Field(
        ..., description="Specific, actionable topics/resources worth studying - not 'practice more'"
    )


class WeaknessReportResponse(BaseModel):
    analysis: WeaknessAnalysis
