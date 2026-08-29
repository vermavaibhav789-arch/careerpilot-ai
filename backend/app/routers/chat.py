from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.db_models import User
from app.models.schemas import ChatRequest, ChatResponse
from app.services import analysis_store, llm_client

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask a follow-up question about the match, e.g. "Why am I not a good
    match for this job?". Uses the resume, JD, and match analysis from the
    session as context, plus prior turns in this session's conversation.
    """
    record = analysis_store.get_session(db, req.session_id, current_user.id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="Session not found. Run /api/analyze first."
        )

    analysis = analysis_store.get_match_analysis(record)
    answer = llm_client.answer_question(
        resume_text=record.resume_text,
        jd_text=record.jd_text,
        analysis=analysis,
        conversation_history=record.chat_history or [],
        question=req.message,
    )

    analysis_store.append_chat(db, record, "user", req.message)
    analysis_store.append_chat(db, record, "assistant", answer)

    return ChatResponse(answer=answer)
