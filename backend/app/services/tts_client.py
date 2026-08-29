"""
Text-to-speech for reading interview questions aloud.

Same reasoning as stt_client.py in reverse: Claude generates the question
text, but has no audio output modality, so turning it into speech is a
separate call to OpenAI's speech endpoint.
"""

from fastapi import HTTPException
from openai import OpenAI

from app.config import get_settings

settings = get_settings()
_client = OpenAI(api_key=settings.openai_api_key)


def synthesize(text: str) -> bytes:
    if not text.strip():
        raise HTTPException(status_code=400, detail="Nothing to synthesize.")

    try:
        response = _client.audio.speech.create(
            model=settings.tts_model,
            voice=settings.tts_voice,
            input=text,
            response_format="mp3",
        )
    except Exception as exc:  # noqa: BLE001 - surface as a clean 502 to the client
        raise HTTPException(
            status_code=502, detail=f"Speech synthesis failed: {exc}"
        ) from exc

    return response.read()
