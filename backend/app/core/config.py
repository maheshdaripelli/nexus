from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "Nexus API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    DATABASE_URL: str = (
        "postgresql+asyncpg://nexus_app:change-me@localhost:5432/nexus"
    )

    JWT_SECRET_KEY: str = "development-only-change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email provider: "smtp", "resend", or "brevo".
    EMAIL_PROVIDER: str = "smtp"
    EMAIL_FROM: str = "Nexus"

    # Gmail SMTP (use a Google App Password, never your normal account password).
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # Resend settings, used only when EMAIL_PROVIDER="resend".
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "Nexus <onboarding@resend.dev>"
    EMAIL_TEST_MODE: bool = False

    # Brevo transactional email API, used when EMAIL_PROVIDER="brevo".
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = ""
    BREVO_SENDER_NAME: str = "Nexus"

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
