import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
    openrouter_reasoning: bool = os.getenv("OPENROUTER_REASONING", "true").lower() == "true"
    openrouter_site_url: str = os.getenv("OPENROUTER_SITE_URL", "")
    openrouter_app_name: str = os.getenv("OPENROUTER_APP_NAME", "Personal AI Telegram Assistant")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./assistant.db")
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    default_timezone: str = os.getenv("DEFAULT_TIMEZONE", "UTC")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8000/oauth/google/callback",
    )
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")

    @property
    def allowed_user_ids(self) -> frozenset[int]:
        values = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "")
        return frozenset(int(value.strip()) for value in values.split(",") if value.strip())

    def validate_bot_runtime(self) -> None:
        if not self.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
        if not self.allowed_user_ids:
            raise RuntimeError("ALLOWED_TELEGRAM_USER_IDS must contain at least one user ID")


settings = Settings()
