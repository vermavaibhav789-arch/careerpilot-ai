"""
Speech-to-text for audio interview answers.

Claude's API is text-and-vision only — it has no audio input modality, so
transcription has to be a separate call before the text hits the normal
Claude-based evaluation pipeline. This uses OpenAI's transcription endpoint
(gpt-4o-mini-transcribe by default), which is a common, well-documented
choice for this specific job regardless of which provider does the
reasoning — mixing providers for different capabilities (Claude for
reasoning, Voyage for embeddings, OpenAI for transcription) is normal in
production RAG/AI stacks, not a compromise.
"""

from fastapi import HTTPException
from openai import OpenAI

from app.config import get_settings

settings = get_settings()
_client = OpenAI(api_key=settings.openai_api_key)

# Keep this in sync with the accept attribute on the frontend recorder and
# with what OpenAI's endpoint actually supports.
_ALLOWED_CONTENT_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
}


def transcribe(filename: str, content: bytes, content_type: str | None) -> str:
    if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type '{content_type}'.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    try:
        transcription = _client.audio.transcriptions.create(
            model=settings.stt_model,
            file=(filename, content, content_type or "audio/webm"),
        )
    except Exception as exc:  # noqa: BLE001 - surface as a clean 502 to the client
        raise HTTPException(
            status_code=502, detail=f"Transcription failed: {exc}"
        ) from exc

    text = transcription.text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Couldn't hear anything in that recording — try again.",
        )
    return text
