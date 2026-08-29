from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central app config. Values are read from environment variables / a .env
    file in the backend/ directory. See .env.example for what's required.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    # Model used for extraction, question generation, and evaluation.
    # claude-sonnet-5 is a good default balance of quality and cost for this
    # kind of structured-reasoning task. Swap to claude-haiku-4-5-20251001
    # for a cheaper/faster option once you've validated prompts.
    anthropic_model: str = "claude-sonnet-5"

    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "interview_bank"

    # Voyage AI is Anthropic's recommended embeddings partner (Anthropic
    # doesn't serve its own embedding model). Free tier is plenty for this
    # project. Get a key at https://www.voyageai.com
    voyage_api_key: str = ""
    voyage_model: str = "voyage-3.5"

    # Speech-to-text for audio interview answers. Claude's API doesn't accept
    # audio input directly, so transcription is a separate call to OpenAI's
    # transcription endpoint before the transcript goes through the normal
    # text evaluation pipeline. gpt-4o-mini-transcribe is the cheap/fast
    # option; swap to gpt-4o-transcribe for higher accuracy.
    openai_api_key: str = ""
    stt_model: str = "gpt-4o-mini-transcribe"

    # Text-to-speech for reading interview questions aloud. Same reasoning
    # as STT above - no Claude audio output, so this is a second OpenAI call.
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "alloy"

    # Database - SQLite by default (zero setup, one file). Swap to Postgres
    # in production by changing this to a postgresql:// URL; SQLAlchemy and
    # the JSON columns used in db_models.py work the same either way.
    database_url: str = "sqlite:///./careerpilot.db"

    # JWT auth. Generate a real secret for anything beyond local dev:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    jwt_secret: str = "dev-only-secret-change-this-before-deploying-anywhere"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # Used to build links inside verification/reset emails
    frontend_url: str = "http://localhost:3000"

    # Email (verification + password reset). If smtp_username is left blank,
    # emails are printed to the backend console instead of sent - the whole
    # flow works end to end in this "dev mode" with zero setup, and you can
    # switch to real delivery just by filling these in. Gmail needs an App
    # Password here, NOT your normal account password - generate one at
    # https://myaccount.google.com/apppasswords (requires 2-Step Verification
    # to be turned on first).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]

    max_upload_size_mb: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
