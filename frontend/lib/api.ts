import type {
  AnalyzeResponse,
  ApplicationStatus,
  ATSChecklist,
  CareerDNA,
  CareerTwin,
  CoverLetterTone,
  Dashboard,
  DocumentType,
  EvaluateAnswerResult,
  InterviewMode,
  InterviewQuestion,
  JobApplication,
  PublicResume,
  ReadinessScore,
  ResumeOptimization,
  ResumeVersion,
  SectionType,
  ShareResumeResult,
  TruthGuardReport,
  Usage,
  WeaknessAnalysis,
} from "./types";
import { authHeaders, clearToken, setToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    if (res.status === 401) {
      // Token is missing/expired/invalid - clear it so the app's auth
      // check redirects to login on the next render instead of retrying
      // with a dead token forever.
      clearToken();
    }
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(detail);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function register(
  email: string,
  password: string
): Promise<{ email: string }> {
  const res = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await handleResponse<{ access_token: string; email: string }>(res);
  setToken(data.access_token);
  return { email: data.email };
}

export async function login(
  email: string,
  password: string
): Promise<{ email: string }> {
  // The backend's login endpoint uses OAuth2PasswordRequestForm (so the
  // FastAPI /docs page gets a working "Authorize" button), which expects
  // form-encoded fields named username/password, not JSON.
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  const data = await handleResponse<{ access_token: string; email: string }>(res);
  setToken(data.access_token);
  return { email: data.email };
}

export async function getMe(): Promise<{ id: string; email: string }> {
  const res = await fetch(`${API_URL}/api/auth/me`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<{ id: string; email: string }>(res);
}

// ---------------------------------------------------------------------------
// Resume / JD analysis
// ---------------------------------------------------------------------------

export async function analyzeResume(
  resumeFile: File,
  jobDescription: string
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("resume", resumeFile);
  formData.append("job_description", jobDescription);

  const res = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: formData,
  });
  return handleResponse<AnalyzeResponse>(res);
}

export async function sendChatMessage(
  sessionId: string,
  message: string
): Promise<{ answer: string }> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  return handleResponse<{ answer: string }>(res);
}

// ---------------------------------------------------------------------------
// Interview
// ---------------------------------------------------------------------------

export async function generateInterviewQuestions(
  sessionId: string,
  numQuestions = 5,
  mode: InterviewMode = "job_specific"
): Promise<{ questions: InterviewQuestion[] }> {
  const res = await fetch(`${API_URL}/api/interview/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, num_questions: numQuestions, mode }),
  });
  return handleResponse<{ questions: InterviewQuestion[] }>(res);
}

export async function getWeaknessReport(sessionId: string): Promise<{ analysis: WeaknessAnalysis }> {
  const res = await fetch(`${API_URL}/api/interview/${sessionId}/weakness-report`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<{ analysis: WeaknessAnalysis }>(res);
}

// ---------------------------------------------------------------------------
// Resume features
// ---------------------------------------------------------------------------

export async function optimizeResume(
  sessionId: string
): Promise<{ optimization: ResumeOptimization }> {
  const res = await fetch(`${API_URL}/api/resume/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return handleResponse<{ optimization: ResumeOptimization }>(res);
}

export async function generateCoverLetter(
  sessionId: string,
  tone: CoverLetterTone
): Promise<{ cover_letter: string }> {
  const res = await fetch(`${API_URL}/api/resume/cover-letter`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, tone }),
  });
  return handleResponse<{ cover_letter: string }>(res);
}

export async function checkATS(sessionId: string): Promise<{ checklist: ATSChecklist }> {
  const res = await fetch(`${API_URL}/api/resume/ats-check`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return handleResponse<{ checklist: ATSChecklist }>(res);
}

export async function getReadiness(sessionId: string): Promise<ReadinessScore> {
  const res = await fetch(`${API_URL}/api/resume/${sessionId}/readiness`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<ReadinessScore>(res);
}

// ---------------------------------------------------------------------------
// Password reset / email verification
// ---------------------------------------------------------------------------

export async function forgotPassword(email: string): Promise<{ message: string }> {
  const res = await fetch(`${API_URL}/api/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return handleResponse<{ message: string }>(res);
}

export async function resetPassword(
  token: string,
  newPassword: string
): Promise<{ message: string }> {
  const res = await fetch(`${API_URL}/api/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  return handleResponse<{ message: string }>(res);
}

export async function verifyEmail(token: string): Promise<{ message: string }> {
  const res = await fetch(
    `${API_URL}/api/auth/verify-email?${new URLSearchParams({ token }).toString()}`
  );
  return handleResponse<{ message: string }>(res);
}

export async function resendVerification(): Promise<{ message: string }> {
  const res = await fetch(`${API_URL}/api/auth/resend-verification`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  return handleResponse<{ message: string }>(res);
}

export async function logoutEverywhere(): Promise<{ message: string }> {
  const res = await fetch(`${API_URL}/api/auth/logout-everywhere`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  return handleResponse<{ message: string }>(res);
}

// ---------------------------------------------------------------------------
// Application tracker
// ---------------------------------------------------------------------------

export async function listApplications(): Promise<JobApplication[]> {
  const res = await fetch(`${API_URL}/api/applications`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<JobApplication[]>(res);
}

export async function createApplication(data: {
  company: string;
  role: string;
  job_url?: string;
  status?: ApplicationStatus;
  notes?: string;
  session_id?: string | null;
  interview_date?: string | null;
}): Promise<JobApplication> {
  const res = await fetch(`${API_URL}/api/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  });
  return handleResponse<JobApplication>(res);
}

export async function updateApplication(
  id: string,
  data: Partial<{
    company: string;
    role: string;
    job_url: string;
    status: ApplicationStatus;
    notes: string;
    interview_date: string | null;
  }>
): Promise<JobApplication> {
  const res = await fetch(`${API_URL}/api/applications/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  });
  return handleResponse<JobApplication>(res);
}

export async function deleteApplication(id: string): Promise<{ message: string }> {
  const res = await fetch(`${API_URL}/api/applications/${id}`, {
    method: "DELETE",
    headers: { ...authHeaders() },
  });
  return handleResponse<{ message: string }>(res);
}

// ---------------------------------------------------------------------------
// Account / plan
// ---------------------------------------------------------------------------

export async function getUsage(): Promise<Usage> {
  const res = await fetch(`${API_URL}/api/account/usage`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<Usage>(res);
}

export async function upgradeToPro(): Promise<Usage> {
  const res = await fetch(`${API_URL}/api/account/upgrade`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  return handleResponse<Usage>(res);
}

export async function downgradeToFree(): Promise<Usage> {
  const res = await fetch(`${API_URL}/api/account/downgrade`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  return handleResponse<Usage>(res);
}

// ---------------------------------------------------------------------------
// Resume library
// ---------------------------------------------------------------------------

export async function saveResumeFromSession(
  sessionId: string,
  label: string
): Promise<ResumeVersion> {
  const res = await fetch(`${API_URL}/api/resumes/from-session`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, label }),
  });
  return handleResponse<ResumeVersion>(res);
}

export async function listResumes(): Promise<ResumeVersion[]> {
  const res = await fetch(`${API_URL}/api/resumes`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<ResumeVersion[]>(res);
}

export async function deleteResume(id: string): Promise<{ message: string }> {
  const res = await fetch(`${API_URL}/api/resumes/${id}`, {
    method: "DELETE",
    headers: { ...authHeaders() },
  });
  return handleResponse<{ message: string }>(res);
}

export async function analyzeFromLibrary(
  resumeId: string,
  jobDescription: string
): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_URL}/api/resumes/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ resume_id: resumeId, job_description: jobDescription }),
  });
  return handleResponse<AnalyzeResponse>(res);
}

export async function shareResume(id: string): Promise<ShareResumeResult> {
  const res = await fetch(`${API_URL}/api/resumes/${id}/share`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  return handleResponse<ShareResumeResult>(res);
}

export async function unshareResume(id: string): Promise<ShareResumeResult> {
  const res = await fetch(`${API_URL}/api/resumes/${id}/unshare`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  return handleResponse<ShareResumeResult>(res);
}

// No auth - this fetches a resume via its public slug, callable from a
// logged-out page. Not exported from the authenticated api.ts pattern
// since it deliberately never attaches an auth header.
export async function getPublicResume(slug: string): Promise<PublicResume> {
  const res = await fetch(`${API_URL}/api/resumes/public/${slug}`);
  return handleResponse<PublicResume>(res);
}

// ---------------------------------------------------------------------------
// Career intelligence (web-search-grounded)
// ---------------------------------------------------------------------------

export async function getSalaryIntelligence(
  role: string,
  location: string
): Promise<{ report: string }> {
  const res = await fetch(`${API_URL}/api/career/salary`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ role, location }),
  });
  return handleResponse<{ report: string }>(res);
}

export async function getCareerMap(
  sessionId: string,
  targetRole: string
): Promise<{ report: string }> {
  const res = await fetch(`${API_URL}/api/career/map`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, target_role: targetRole }),
  });
  return handleResponse<{ report: string }>(res);
}

export async function simulateCareerScenario(
  scenario: string,
  sessionId?: string
): Promise<{ report: string }> {
  const res = await fetch(`${API_URL}/api/career/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ scenario, session_id: sessionId ?? null }),
  });
  return handleResponse<{ report: string }>(res);
}

// ---------------------------------------------------------------------------
// Career DNA
// ---------------------------------------------------------------------------

export async function getCareerDNA(): Promise<CareerDNA> {
  const res = await fetch(`${API_URL}/api/career-dna`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<CareerDNA>(res);
}

export async function updateCareerDNA(data: Partial<CareerDNA>): Promise<CareerDNA> {
  const res = await fetch(`${API_URL}/api/career-dna`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  });
  return handleResponse<CareerDNA>(res);
}

export async function syncCareerDNAFromSession(sessionId: string): Promise<CareerDNA> {
  const res = await fetch(`${API_URL}/api/career-dna/sync-from-session`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return handleResponse<CareerDNA>(res);
}

export async function getCareerTwin(): Promise<CareerTwin> {
  const res = await fetch(`${API_URL}/api/career-dna/twin`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<CareerTwin>(res);
}

// ---------------------------------------------------------------------------
// Truth Guard
// ---------------------------------------------------------------------------

export async function verifyContent(
  sessionId: string,
  generatedText: string
): Promise<{ report: TruthGuardReport }> {
  const res = await fetch(`${API_URL}/api/resume/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, generated_text: generatedText }),
  });
  return handleResponse<{ report: TruthGuardReport }>(res);
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export async function getDashboard(): Promise<Dashboard> {
  const res = await fetch(`${API_URL}/api/dashboard`, {
    headers: { ...authHeaders() },
  });
  return handleResponse<Dashboard>(res);
}

// ---------------------------------------------------------------------------
// Content generators
// ---------------------------------------------------------------------------

export async function generateSection(
  sessionId: string,
  sectionType: SectionType,
  context: string
): Promise<{ generated_text: string }> {
  const res = await fetch(`${API_URL}/api/generate/section`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, section_type: sectionType, context }),
  });
  return handleResponse<{ generated_text: string }>(res);
}

export async function generateDocument(
  documentType: DocumentType,
  context: string,
  sessionId?: string
): Promise<{ generated_text: string }> {
  const res = await fetch(`${API_URL}/api/generate/document`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ document_type: documentType, context, session_id: sessionId ?? null }),
  });
  return handleResponse<{ generated_text: string }>(res);
}

export async function fetchQuestionAudio(
  sessionId: string,
  questionId: string
): Promise<string> {
  // Media elements (<audio src=...>) can't attach custom headers, so this
  // fetches the audio as a blob (with the auth header) and hands back an
  // object URL instead of a plain endpoint URL.
  const params = new URLSearchParams({ session_id: sessionId });
  const res = await fetch(
    `${API_URL}/api/interview/questions/${questionId}/audio?${params.toString()}`,
    { headers: { ...authHeaders() } }
  );
  if (!res.ok) {
    throw new Error(`Couldn't load question audio (${res.status})`);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function transcribeAudio(
  audioBlob: Blob,
  filename = "answer.webm"
): Promise<{ transcript: string }> {
  const formData = new FormData();
  formData.append("audio", audioBlob, filename);

  const res = await fetch(`${API_URL}/api/interview/transcribe`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: formData,
  });
  return handleResponse<{ transcript: string }>(res);
}

export async function evaluateAnswer(
  sessionId: string,
  questionId: string,
  candidateAnswer: string
): Promise<EvaluateAnswerResult> {
  const res = await fetch(`${API_URL}/api/interview/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      candidate_answer: candidateAnswer,
    }),
  });
  return handleResponse<EvaluateAnswerResult>(res);
}
