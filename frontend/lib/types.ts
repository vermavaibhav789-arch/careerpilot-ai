export interface MatchAnalysis {
  match_score: number;
  missing_skills: string[];
  strong_areas: string[];
  recommended_changes: string[];
  summary: string;
}

export interface JobIntelligence {
  required_skills: string[];
  preferred_skills: string[];
  experience_level: string;
  work_mode: string;
  location: string;
  hidden_signals: string[];
}

export interface AnalyzeResponse {
  session_id: string;
  analysis: MatchAnalysis;
  job_intelligence: JobIntelligence;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface InterviewQuestion {
  id: string;
  skill_area: string;
  question: string;
  difficulty: "junior" | "mid" | "senior";
  based_on: string;
}

export interface BulletRewrite {
  original: string;
  improved: string;
  note: string;
}

export interface ResumeOptimization {
  improved_summary: string;
  bullet_rewrites: BulletRewrite[];
  missing_keywords: string[];
  skills_section_suggestions: string[];
}

export type CoverLetterTone =
  | "professional"
  | "concise"
  | "startup"
  | "corporate"
  | "technical"
  | "enthusiastic";

export interface ATSCheckItem {
  check: string;
  status: "pass" | "warning" | "fail";
  note: string;
}

export interface ATSChecklist {
  items: ATSCheckItem[];
  overall_note: string;
}

export type InterviewMode = "technical" | "behavioral" | "hr" | "job_specific";

export type SectionType =
  | "headline"
  | "summary"
  | "objective"
  | "skills_list"
  | "bullet"
  | "work_experience_description"
  | "star_story";

export type DocumentType =
  | "resignation_letter"
  | "professional_bio"
  | "thank_you_email"
  | "follow_up_email"
  | "networking_email"
  | "salary_negotiation_email"
  | "offer_acceptance_email"
  | "offer_decline_email";

export interface CareerDNA {
  skills: string[];
  achievements: string[];
  certifications: string[];
  target_roles: string[];
  target_industries: string[];
  experience_summary: string;
  salary_expectation: string;
  location_preference: string;
  work_mode_preference: string;
  career_goals: string;
  updated_at: string;
}

export interface CareerTwin {
  current_skills: string[];
  target_roles: string[];
  skill_gaps: string[];
  overall_readiness: number | null;
  verdict: string;
}

export interface TruthGuardFinding {
  claim: string;
  supported: boolean;
  concern: string;
}

export interface TruthGuardReport {
  passed: boolean;
  findings: TruthGuardFinding[];
}

export interface ReadinessScore {
  overall: number;
  resume_match: number;
  interview_readiness: number | null;
  questions_answered: number;
  recommendation: "apply" | "improve" | "skip";
  verdict: string;
}

export interface WeaknessAnalysis {
  strengths_shown: string[];
  biggest_weaknesses: string[];
  recommended_learning: string[];
}

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "oa"
  | "interview"
  | "final_round"
  | "offer"
  | "rejected";

export interface JobApplication {
  id: string;
  company: string;
  role: string;
  job_url: string;
  status: ApplicationStatus;
  notes: string;
  session_id: string | null;
  interview_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlanLimits {
  max_analyses: number | null;
  max_interview_questions: number | null;
  max_voice_actions: number | null;
  resume_optimizer: boolean;
  cover_letter: boolean;
  ats_check: boolean;
  readiness_score: boolean;
  weakness_report: boolean;
  application_tracker: boolean;
  resume_library: boolean;
}

export interface Usage {
  plan: string;
  limits: PlanLimits;
  analyses_used: number;
  interview_questions_used: number;
  voice_actions_used: number;
}

export interface ResumeVersion {
  id: string;
  label: string;
  resume_text: string;
  original_filename: string;
  created_at: string;
  is_public?: boolean;
  public_slug?: string | null;
}

export interface ShareResumeResult {
  is_public: boolean;
  public_slug: string | null;
  public_url: string | null;
}

export interface PublicResume {
  label: string;
  resume_text: string;
}

export interface RecentSession {
  session_id: string;
  jd_preview: string;
  match_score: number;
  created_at: string;
}

export interface Dashboard {
  total_analyses: number;
  average_match_score: number | null;
  total_interview_questions_answered: number;
  average_interview_score: number | null;
  applications_by_status: Record<string, number>;
  recent_sessions: RecentSession[];
}

export interface EvaluateAnswerResult {
  evaluation: AnswerEvaluation;
  followup: InterviewQuestion | null;
}

export interface AnswerEvaluation {
  technical_accuracy: number;
  completeness: number;
  communication: number;
  missing_concepts: string[];
  suggested_answer: string;
  overall_feedback: string;
}
