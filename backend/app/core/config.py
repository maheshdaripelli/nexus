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
