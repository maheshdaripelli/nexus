from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILES = (str(BACKEND_DIR / ".env"), str(BACKEND_DIR.parent / ".env.local"))


def _asyncpg_database_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"postgres", "postgresql"}:
        return value

    query = []
    for key, query_value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "channel_binding":
            continue
        if key == "sslmode":
            key = "ssl"
        query.append((key, query_value))

    return urlunsplit(
        parsed._replace(
            scheme="postgresql+asyncpg",
            query=urlencode(query),
        )
    )


class Settings(BaseSettings):
    APP_NAME: str = "Nexus API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/nexus"
    )
    DATABASE_URL_UNPOOLED: str | None = None

    JWT_SECRET_KEY: str = "development-only-change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("DATABASE_URL", "DATABASE_URL_UNPOOLED", mode="before")
    @classmethod
    def normalize_postgres_urls(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _asyncpg_database_url(value)

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()