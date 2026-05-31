"""Application configuration via pydantic-settings.

All settings are populated from environment variables (with a `.env` file
fallback for local dev). Import the module-level `settings` singleton anywhere.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    app_name: str = "ConvIQ"
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # ---- Paths ----
    uploads_dir: Path = Path("/tmp/conviq/uploads")
    domains_dir: Path = PROJECT_ROOT / "domains"

    # ---- Database ----
    database_url: str = "postgresql+asyncpg://conviq:conviq@localhost:5432/conviq"

    # ---- Redis (Celery broker + pub/sub for SSE) ----
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ---- LLM (Gemini) ----
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"

    # ---- HuggingFace (pyannote license + model publishing) ----
    hf_token: str = ""
    hf_username: str = ""
    pyannote_model: str = "pyannote/speaker-diarization-3.1"

    # ---- Whisper ----
    whisper_model_size: str = "small"

    # ---- Custom dialogue-act model ----
    dialogue_act_model: str = "models/dialogue-act/distilbert-dailydialog-app-buckets"

    # ---- Embeddings (for pgvector + Chroma) ----
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ---- Upload limits ----
    max_upload_mb: int = 100
    allowed_audio_extensions: tuple[str, ...] = (
        "mp3",
        "m4a",
        "flac",
        "ogg",
        "aac",
    )


settings = Settings()
