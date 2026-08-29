"""
Interview engine: the RAG layer for question generation and answer
evaluation. Retrieves relevant entries from the vector store knowledge base
and passes them to the LLM as grounding context.
"""

from app.models.schemas import (
    AnswerEvaluation,
    FollowUpDecision,
    InterviewQuestion,
    InterviewQuestionSet,
)
from app.services import llm_client, vector_store


def generate_questions(
    resume_text: str,
    jd_text: str,
    missing_skills: list[str],
    strong_areas: list[str],
    num_questions: int,
    mode: str = "job_specific",
) -> InterviewQuestionSet:
    # The knowledge base is technical-only, so retrieval only helps for
    # technical/job_specific modes - behavioral/hr questions come from the
    # model's own judgment plus the mode instructions in the prompt.
    retrieved: list[dict] = []
    if mode in ("technical", "job_specific"):
        skills_to_probe = (missing_skills + strong_areas)[:6] or ["Python", "System design"]
        seen_questions = set()
        for skill in skills_to_probe:
            for match in vector_store.query(skill, n_results=1):
                if match["question"] and match["question"] not in seen_questions:
                    retrieved.append(match)
                    seen_questions.add(match["question"])

    return llm_client.generate_interview_questions(
        resume_text=resume_text,
        jd_text=jd_text,
        missing_skills=missing_skills,
        strong_areas=strong_areas,
        retrieved_reference_questions=retrieved,
        num_questions=num_questions,
        mode=mode,
    )


def evaluate(
    question: InterviewQuestion, candidate_answer: str, allow_followup: bool
) -> tuple[AnswerEvaluation, FollowUpDecision | None]:
    """
    Evaluate a candidate's answer and, only for primary questions (not
    follow-ups themselves — capped at one level deep so this can't spiral
    into an endless interrogation), decide whether a real interviewer would
    naturally probe deeper.
    """
    # Retrieve the closest reference answer for this specific question's
    # skill area to ground both the evaluation rubric and the follow-up.
    matches = vector_store.query(question.question, n_results=1)
    reference = matches[0] if matches else None

    evaluation = llm_client.evaluate_answer(
        question=question.question,
        skill_area=question.skill_area,
        candidate_answer=candidate_answer,
        retrieved_reference=reference,
    )

    followup_decision: FollowUpDecision | None = None
    if allow_followup:
        followup_decision = llm_client.generate_followup(
            question=question.question,
            skill_area=question.skill_area,
            candidate_answer=candidate_answer,
            evaluation=evaluation,
            retrieved_reference=reference,
        )

    return evaluation, followup_decision
