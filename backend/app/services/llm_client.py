"""
Thin wrapper around the Anthropic Claude API.

Uses Claude's native structured outputs (client.messages.parse with a
Pydantic model as output_format) so every extraction/generation/evaluation
call returns validated, typed data instead of hand-parsed JSON strings.
Docs: https://docs.claude.com/en/docs/build-with-claude/structured-outputs
"""

from anthropic import Anthropic

from app.config import get_settings
from app.models.schemas import (
    AnswerEvaluation,
    ATSChecklist,
    CareerDNAExtraction,
    DocumentType,
    FollowUpDecision,
    InterviewMode,
    InterviewQuestionSet,
    JobIntelligence,
    MatchAnalysis,
    ResumeOptimization,
    SectionType,
    TruthGuardReport,
    WeaknessAnalysis,
)

settings = get_settings()
_client = Anthropic(api_key=settings.anthropic_api_key)


def _text_from_response(response) -> str:
    """
    Concatenate every text block in a non-structured Messages response.
    Matters for web-search-enabled calls specifically: Claude's answer can
    be split across multiple text blocks interleaved with search/tool_use
    blocks, so returning only the first one (as a naive implementation
    would) can silently truncate the response. For plain single-block
    responses this behaves identically to returning that one block.
    """
    return "".join(block.text for block in response.content if block.type == "text")


# ---------------------------------------------------------------------------
# 1. Resume <-> JD matching
# ---------------------------------------------------------------------------


def analyze_match(resume_text: str, jd_text: str) -> MatchAnalysis:
    prompt = f"""You are a technical recruiter and career coach reviewing a
candidate for a specific role. Compare the resume against the job
description and produce an honest, specific assessment.

Rules:
- match_score reflects genuine fit for THIS job, not general resume quality.
- missing_skills: only skills/experience the JD asks for that the resume
  does not evidence. Be specific (e.g. "RAG pipeline experience", not "AI").
- strong_areas: skills/experience the resume demonstrates that this JD wants.
- recommended_changes: concrete, actionable edits — things the candidate
  could actually rewrite on their resume, not generic advice.

<job_description>
{jd_text}
</job_description>

<resume>
{resume_text}
</resume>"""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
        output_format=MatchAnalysis,
    )
    return response.parsed_output


def extract_job_intelligence(jd_text: str) -> JobIntelligence:
    """
    Analyze the job description on its own terms, independent of any
    specific resume — what's actually required vs. preferred, what
    expectations it sets, and what it emphasizes beyond the literal skill
    list. This is what lets the product reason about the job itself, not
    just do keyword matching against a resume.
    """
    prompt = f"""Analyze this job description on its own. Extract what it
actually requires versus what's merely preferred — don't inflate preferred
skills into requirements. If experience level, work mode, or location
aren't stated, say "Not specified" rather than guessing.

For hidden_signals: look for skills or topics the JD returns to repeatedly,
emphasizes in the responsibilities section, or lists early/prominently even
if formally categorized as "preferred" or "nice to have" — these often
reveal what the team actually cares about most day-to-day. Give 0-3 signals,
each one specific sentence. Leave the list empty if nothing stands out.

<job_description>
{jd_text}
</job_description>"""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
        output_format=JobIntelligence,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 2. Conversational Q&A over resume + JD + match analysis
# ---------------------------------------------------------------------------


def answer_question(
    resume_text: str,
    jd_text: str,
    analysis: MatchAnalysis,
    conversation_history: list[dict],
    question: str,
) -> str:
    system = f"""You are CareerPilot, an AI career coach. Answer the
candidate's questions about their fit for this specific job using ONLY the
resume, job description, and match analysis below. Be direct and specific —
reference actual lines from the resume/JD rather than speaking generically.
Keep answers focused, a few sentences to a short paragraph unless asked for
more detail.

<job_description>
{jd_text}
</job_description>

<resume>
{resume_text}
</resume>

<match_analysis>
match_score: {analysis.match_score}
missing_skills: {", ".join(analysis.missing_skills)}
strong_areas: {", ".join(analysis.strong_areas)}
recommended_changes: {", ".join(analysis.recommended_changes)}
</match_analysis>"""

    messages = conversation_history + [{"role": "user", "content": question}]

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1000,
        system=system,
        messages=messages,
    )
    return _text_from_response(response)


# ---------------------------------------------------------------------------
# 3. Interview question generation (RAG-grounded)
# ---------------------------------------------------------------------------


def generate_interview_questions(
    resume_text: str,
    jd_text: str,
    missing_skills: list[str],
    strong_areas: list[str],
    retrieved_reference_questions: list[dict],
    num_questions: int,
    mode: InterviewMode = "job_specific",
) -> InterviewQuestionSet:
    reference_block = "\n\n".join(
        f"- Skill: {r['skill']}\n  Sample question: {r['question']}\n  Key concepts to probe: {r['key_concepts']}"
        for r in retrieved_reference_questions
    )

    mode_instructions = {
        "technical": (
            "Focus entirely on technical depth — architecture decisions, "
            "tradeoffs, debugging, and how they'd approach real technical "
            "problems in the skill areas below. No behavioral/HR questions."
        ),
        "behavioral": (
            "Ask behavioral questions in the style of 'Tell me about a time "
            "when...', 'Why should we hire you?', 'Describe a difficult "
            "project you worked on.' Ground each in something plausible from "
            "their actual resume (a project, a role, a transition) rather "
            "than a generic prompt. No technical/coding questions."
        ),
        "hr": (
            "Ask practical HR-round questions: salary expectations, notice "
            "period, willingness to relocate/work mode, career goals, why "
            "they're looking to move roles. Keep these realistic and "
            "grounded in what this specific JD's work mode/location implies."
        ),
        "job_specific": (
            "Prioritize: (1) areas where the resume claims experience the JD "
            "cares about, to test real depth, and (2) gaps between the "
            "resume and JD requirements, to see if they can reason about it "
            "even without hands-on experience."
        ),
    }[mode]

    prompt = f"""Generate {num_questions} interview questions for this
candidate, tailored to THEIR resume and THIS job description.

Interview mode: {mode}
{mode_instructions}

Ground each question in something specific — mention a project, skill, or
requirement it's testing. Vary difficulty across junior/mid/senior. Use the
reference questions below (from a curated interview question bank) as
inspiration for what a strong question looks like — do not copy them
verbatim, adapt them to this specific candidate. The reference bank is
technical-only, so for behavioral/hr modes use it only for general
inspiration on rigor, not topic.

<job_description>
{jd_text}
</job_description>

<resume>
{resume_text}
</resume>

<missing_skills>{", ".join(missing_skills)}</missing_skills>
<strong_areas>{", ".join(strong_areas)}</strong_areas>

<reference_questions_from_knowledge_base>
{reference_block}
</reference_questions_from_knowledge_base>

Generate exactly {num_questions} questions, each with a unique id like "q1", "q2", etc."""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        output_format=InterviewQuestionSet,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 4. Answer evaluation (RAG-grounded)
# ---------------------------------------------------------------------------


def evaluate_answer(
    question: str,
    skill_area: str,
    candidate_answer: str,
    retrieved_reference: dict | None,
) -> AnswerEvaluation:
    reference_block = (
        f"Reference ideal answer: {retrieved_reference['ideal_answer']}\n"
        f"Key concepts a strong answer should hit: {retrieved_reference['key_concepts']}"
        if retrieved_reference
        else "No reference material available — evaluate using general best practices."
    )

    prompt = f"""Evaluate this candidate's interview answer.

<question skill_area="{skill_area}">
{question}
</question>

<candidate_answer>
{candidate_answer}
</candidate_answer>

<grounding_context>
{reference_block}
</grounding_context>

Score technical_accuracy, completeness, and communication each from 0-10.
List specific missing_concepts (concrete terms/ideas, not vague notes).
Write a suggested_answer that shows what a strong answer looks like.
overall_feedback should be direct and actionable, 2-4 sentences."""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
        output_format=AnswerEvaluation,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 5. Adaptive follow-up questions
# ---------------------------------------------------------------------------


def generate_followup(
    question: str,
    skill_area: str,
    candidate_answer: str,
    evaluation: AnswerEvaluation,
    retrieved_reference: dict | None,
) -> FollowUpDecision:
    reference_block = (
        f"Key concepts a strong answer should hit: {retrieved_reference['key_concepts']}"
        if retrieved_reference
        else "No reference material available."
    )

    prompt = f"""You are conducting a live interview. Decide whether a real
interviewer would naturally follow up on this answer, the way a good
interviewer probes deeper rather than moving straight to the next topic.

Follow up ONLY if there's a specific, meaningful gap worth probing — e.g.
the candidate mentioned something interesting but didn't explain it, gave a
surface-level answer to a deeper topic, or skipped something important from
the reference concepts. Do NOT follow up just because the answer wasn't
perfect, and do NOT follow up on a strong, complete answer.

If you do follow up, ask ONE natural, conversational question that digs
into the SAME topic — not a new subject. Reference something specific the
candidate actually said.

<original_question skill_area="{skill_area}">
{question}
</original_question>

<candidate_answer>
{candidate_answer}
</candidate_answer>

<evaluation>
technical_accuracy: {evaluation.technical_accuracy}/10
completeness: {evaluation.completeness}/10
missing_concepts: {", ".join(evaluation.missing_concepts) or "none"}
</evaluation>

<reference>
{reference_block}
</reference>"""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
        output_format=FollowUpDecision,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 6. Resume optimizer
# ---------------------------------------------------------------------------


def optimize_resume(resume_text: str, jd_text: str) -> ResumeOptimization:
    prompt = f"""Rewrite parts of this resume to be stronger for this
specific job — but you must NEVER invent experience, tools, metrics, or
accomplishments that aren't stated or clearly implied in the original.

Rules, no exceptions:
- Rephrasing, restructuring, and quantifying vague claims INTO something
  concrete is allowed only if the underlying fact is already there (e.g.
  "led a small team" can become "led a 3-person team" only if the resume
  says 3 people somewhere; otherwise keep it qualitative).
- If a bullet is weak because it's missing information (impact, scale,
  outcome) that would need input from the candidate, say so directly in
  the note — e.g. "Add the team size and the specific outcome if you have
  them" — rather than fabricating plausible-sounding numbers.
- missing_keywords and skills_section_suggestions must only include things
  a careful read of the resume shows the candidate actually has evidence
  for — if you're suggesting something conditionally (e.g. "add RAG if
  you've built one"), put that framing in the text itself.

<job_description>
{jd_text}
</job_description>

<resume>
{resume_text}
</resume>

Pick the 3-6 bullets most worth rewriting (weakest phrasing relative to
this JD), not every bullet in the resume."""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
        output_format=ResumeOptimization,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 7. Cover letter generator
# ---------------------------------------------------------------------------


def generate_cover_letter(resume_text: str, jd_text: str, tone: str) -> str:
    tone_guidance = {
        "professional": "Polished and formal, standard business letter register.",
        "concise": "As short as possible while still specific - aim for under 150 words.",
        "startup": "Direct, energetic, a bit informal - like writing to a small team, not HR.",
        "corporate": "Formal and structured, appropriate for a large traditional company.",
        "technical": "Leads with concrete technical work and specifics, minimal soft-skill language.",
        "enthusiastic": "Genuine enthusiasm for this specific role/company, without generic flattery.",
    }.get(tone, "Polished and professional.")

    prompt = f"""Write a cover letter for this candidate applying to this
job. Tone: {tone}. {tone_guidance}

Ground it in specifics from BOTH documents — reference actual things from
the resume (real projects/skills) and actual things from the JD (real
requirements/team focus), not generic phrases like "I am a hard worker who
is passionate about technology." Do not invent experience the resume
doesn't support. No placeholder brackets like [Company Name] — if the
company name isn't in the JD, refer to "your team" or similar naturally.

<job_description>
{jd_text}
</job_description>

<resume>
{resume_text}
</resume>"""

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return _text_from_response(response)


# ---------------------------------------------------------------------------
# 8. ATS compatibility checklist (honest heuristic, not a fabricated score)
# ---------------------------------------------------------------------------


def check_ats_compatibility(resume_text: str) -> ATSChecklist:
    prompt = f"""Check this resume's TEXT CONTENT for well-documented ATS
(applicant tracking system) parsing pitfalls. You only have the extracted
text, not the visual layout, so infer likely formatting issues from the
text structure itself (e.g. garbled/run-together text often indicates a
multi-column layout or text-in-tables that don't extract cleanly).

Check specifically for:
1. Standard section headers present (Experience, Education, Skills, etc.)
   vs. creative/non-standard header names ATS software may not recognize
2. Signs of multi-column layout or tables (text appearing out of logical
   order, run-together phrases from side-by-side columns)
3. Contact info present and in a normal location (usually near the top)
4. Consistent, parseable date formats for experience entries
5. No obvious signs of text-in-images (unexpectedly short extracted text
   relative to what a resume should contain)
6. Job titles and company names clearly distinguishable from surrounding text

For each check, mark pass/warning/fail with a SPECIFIC note referencing
what you actually observed in this resume's text, not a generic comment.

<resume_extracted_text>
{resume_text}
</resume_extracted_text>

For overall_note: be explicit that ATS behavior varies by vendor (Workday,
Greenhouse, Taleo, iCIMS etc. all parse differently) and this is a
heuristic check against common pitfalls, not a guaranteed score from any
real ATS system."""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
        output_format=ATSChecklist,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 9. Weakness analysis + learning recommendations
# ---------------------------------------------------------------------------


def analyze_weaknesses(evaluated_qa: list[dict]) -> WeaknessAnalysis:
    qa_block = "\n\n".join(
        f"Q ({e['skill_area']}): {e['question']}\n"
        f"Scores - technical: {e['technical_accuracy']}/10, completeness: {e['completeness']}/10, "
        f"communication: {e['communication']}/10\n"
        f"Missing concepts: {', '.join(e['missing_concepts']) or 'none'}"
        for e in evaluated_qa
    )

    prompt = f"""Here are all the questions a candidate answered in a mock
interview round, with scores and identified gaps for each. Summarize the
pattern across ALL of them — not a recap of each individual question.

strengths_shown: what came through consistently well (skip if nothing clear)
biggest_weaknesses: specific recurring gaps (e.g. "doesn't discuss
evaluation/testing of ML systems", not vague labels like "needs
improvement"). 2-5 items, most important first.
recommended_learning: specific, actionable next steps tied directly to the
weaknesses above (e.g. "spend time on retrieval evaluation metrics like
precision@k and MRR" rather than "study RAG more"). 2-5 items.

<answered_questions>
{qa_block}
</answered_questions>"""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
        output_format=WeaknessAnalysis,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 10. Resume section generator (headline, summary, bullets, STAR stories...)
# ---------------------------------------------------------------------------

_NO_FABRICATION_RULE = """
Hard rule, no exceptions: never invent experience, employers, metrics, team
sizes, or outcomes that aren't stated or clearly implied by the resume or
the context provided below. If the strongest version of this would need a
number or detail the person hasn't given you, write it in a way that
doesn't require that detail, and add one line at the end starting with
"To strengthen this:" naming exactly what real detail would make it better.
"""

_SECTION_INSTRUCTIONS: dict[str, str] = {
    "headline": "Write ONE professional headline/title line (under 12 words) tailored to this job.",
    "summary": "Write a 2-4 sentence professional summary for the top of the resume, tailored to this job.",
    "objective": "Write a career objective statement (2-3 sentences) - more appropriate for a student/early-career resume than a summary.",
    "skills_list": "Produce a comma-separated list of skills to feature on the resume, prioritized for this job. Only include skills the resume actually evidences.",
    "bullet": "Turn the raw accomplishment in <context> into ONE polished, quantified-where-possible resume bullet.",
    "work_experience_description": "Turn <context> into a fuller paragraph-style description of a role (3-5 sentences) suitable for a resume or LinkedIn.",
    "star_story": "Turn <context> into a STAR-structured story (Situation, Task, Action, Result - label each part) for use in a behavioral interview answer.",
}


def generate_resume_section(
    resume_text: str, jd_text: str, section_type: SectionType, context: str
) -> str:
    instruction = _SECTION_INSTRUCTIONS[section_type]

    prompt = f"""{instruction}
{_NO_FABRICATION_RULE}

<job_description>
{jd_text}
</job_description>

<resume>
{resume_text}
</resume>

<context>
{context or "(none provided - draw only from the resume and job description above)"}
</context>"""

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return _text_from_response(response)


# ---------------------------------------------------------------------------
# 11. Other career documents (resignation letter, bio, follow-up email...)
# ---------------------------------------------------------------------------

_DOCUMENT_INSTRUCTIONS: dict[str, str] = {
    "resignation_letter": "Write a professional, brief resignation letter. Use placeholders like [Manager's name] and [Last day] only for details not given in <context>.",
    "professional_bio": "Write a third-person professional bio (100-150 words) suitable for a company website or speaker page.",
    "thank_you_email": "Write a short post-interview thank-you email, referencing something specific from the interview described in <context>.",
    "follow_up_email": "Write a brief, polite follow-up email checking on application status.",
    "networking_email": "Write a short, genuine networking outreach email - not generic flattery.",
    "salary_negotiation_email": "Write a professional email negotiating a job offer's salary, firm but collaborative in tone.",
    "offer_acceptance_email": "Write a warm, professional email formally accepting a job offer.",
    "offer_decline_email": "Write a brief, gracious email declining a job offer, leaving the door open for the future.",
}


def generate_career_document(
    document_type: DocumentType,
    context: str,
    resume_text: str | None,
    jd_text: str | None,
) -> str:
    instruction = _DOCUMENT_INSTRUCTIONS[document_type]

    grounding = ""
    if resume_text and jd_text:
        grounding = f"""
<job_description>
{jd_text}
</job_description>

<resume>
{resume_text}
</resume>
"""

    prompt = f"""{instruction}
{_NO_FABRICATION_RULE}
No placeholder brackets for anything actually provided in <context> below -
only use them for genuinely missing specifics (e.g. a manager's name).

<context>
{context}
</context>
{grounding}"""

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return _text_from_response(response)


# ---------------------------------------------------------------------------
# 12. Career intelligence - grounded in real web search, not an LLM guess
# ---------------------------------------------------------------------------
# Both of these enable Claude's server-side web search tool so the numbers
# come from actual current sources rather than the model's training data,
# which goes stale and was never reliable for compensation figures anyway.
# max_uses caps how many searches a single call can run, since each search
# has a real cost (~$0.01 at published API pricing) on top of token usage.

_WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 4}


def get_salary_intelligence(role: str, location: str) -> str:
    prompt = f"""Search for current, real salary data for this role and
location, then write a short salary intelligence report grounded in what
you actually find - do not estimate from memory alone.

Role: {role}
Location: {location}

Cover:
- A realistic base salary range, naming which source(s) it came from
- How experience level (junior/mid/senior) shifts that range
- Any notable remote-work or regional adjustment
- One sentence noting that actual offers vary by company/industry on top of this

Keep it to a few short paragraphs - a quick, honest briefing, not an
exhaustive report."""

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1200,
        tools=[_WEB_SEARCH_TOOL],
        messages=[{"role": "user", "content": prompt}],
    )
    return _text_from_response(response)


def get_career_map(resume_text: str, current_context: str, target_role: str) -> str:
    prompt = f"""Search for current, real information about the career path
toward this target role, then write a short career map grounded in what
you find - not a generic guess.

<target_role>
{target_role}
</target_role>

<candidate_background>
{current_context}
</candidate_background>

<resume>
{resume_text}
</resume>

Cover:
- Realistic intermediate role(s) between where this candidate is now and
  the target role, based on real hiring patterns for this path
- Skills the resume already shows vs. skills genuinely missing for the
  target role
- A realistic timeframe and any certifications/experience commonly
  expected along this path
- Cite what you found this on (site/source names)

A few short paragraphs - a career coach's honest briefing, not an
exhaustive report."""

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1500,
        tools=[_WEB_SEARCH_TOOL],
        messages=[{"role": "user", "content": prompt}],
    )
    return _text_from_response(response)


# ---------------------------------------------------------------------------
# 13. Career DNA extraction (structured facts pulled from a resume)
# ---------------------------------------------------------------------------


def extract_career_dna(resume_text: str) -> CareerDNAExtraction:
    prompt = f"""Extract structured facts from this resume for a persistent
career profile. Only include what the resume actually states - this
profile gets merged with data from other resumes/sessions over time, so
precision matters more than completeness here.

skills: concrete skills actually demonstrated (not aspirational)
achievements: specific accomplishments with real outcomes/metrics stated
certifications: actual named certifications/credentials mentioned

<resume>
{resume_text}
</resume>"""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        output_format=CareerDNAExtraction,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 14. Truth Guard - independent verification pass on generated content
# ---------------------------------------------------------------------------


def verify_against_source(generated_text: str, source_resume: str) -> TruthGuardReport:
    """
    A second, independent check on AI-generated content - not the same
    call that wrote it, and specifically instructed to be skeptical rather
    than to defend the text. This is defense-in-depth on top of the
    no-fabrication instructions already in the generation prompts
    themselves (resume optimizer, section generator, career documents) -
    catching cases where a single prompt-level instruction wasn't enough.
    """
    prompt = f"""You are an independent fact-checker reviewing someone
else's writing - you did NOT write the text below, and your job is to be
skeptical, not to defend it. Check whether EVERY factual claim (metric,
employer, job title, achievement, tool, scope, team size, outcome) in the
generated text is actually supported by the original resume. Flag
anything that looks invented, embellished, or more specific than what the
resume actually states - even if it sounds plausible or is the kind of
thing that's "probably true."

<original_resume>
{source_resume}
</original_resume>

<generated_text_to_check>
{generated_text}
</generated_text_to_check>

List each distinct factual claim you find and whether the resume supports
it. Set passed=true only if every single claim is genuinely supported."""

    response = _client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
        output_format=TruthGuardReport,
    )
    return response.parsed_output


# ---------------------------------------------------------------------------
# 15. Career Simulator - "what if I..." scenarios, grounded in web search
# ---------------------------------------------------------------------------


def simulate_career_scenario(
    scenario: str, career_dna_context: str, resume_text: str | None
) -> str:
    resume_block = f"\n<resume>\n{resume_text}\n</resume>\n" if resume_text else ""

    prompt = f"""Search for real, current information relevant to this
career scenario, then give an honest, grounded analysis - an informed
estimate clearly labeled as such, not a guaranteed prediction about this
specific person's outcome.

<scenario>
{scenario}
</scenario>

<candidate_context>
{career_dna_context or "No profile data available - answer from the scenario and general current market information."}
</candidate_context>
{resume_block}
Cover:
- A realistic time-to-transition estimate, if the scenario involves a change
- Expected salary impact, grounded in what you actually find, with sources
- Concrete skill requirements - what's needed vs. what this candidate already has
- Honest opportunity/risk analysis - real tradeoffs, not just upside
- One closing sentence making clear this is an informed estimate based on
  current market patterns, not a guarantee

A few short paragraphs - a career coach's honest take, not an exhaustive report."""

    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1500,
        tools=[_WEB_SEARCH_TOOL],
        messages=[{"role": "user", "content": prompt}],
    )
    return _text_from_response(response)
