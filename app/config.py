from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Neon/libpq query params that asyncpg does not accept
_ASYNCPG_DROP_QUERY_KEYS = frozenset({"channel_binding", "options"})


def _strip_driver(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    for driver in ("postgresql+asyncpg://", "postgresql+psycopg://"):
        if url.startswith(driver):
            return "postgresql://" + url.removeprefix(driver)
    return url


def normalize_async_database_url(url: str) -> str:
    """Accept Neon-style postgresql:// URLs and normalize for asyncpg."""
    base = _strip_driver(url)
    parsed = urlparse(base)
    query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key in _ASYNCPG_DROP_QUERY_KEYS:
            continue
        if key == "sslmode" and value in ("require", "verify-full", "prefer"):
            query.append(("ssl", "require"))
            continue
        query.append((key, value))
    rebuilt = urlunparse(parsed._replace(query=urlencode(query)))
    return "postgresql+asyncpg://" + rebuilt.removeprefix("postgresql://")


def alembic_database_url(raw_url: str) -> str:
    """Sync URL for Alembic (psycopg3), compatible with Neon."""
    base = _strip_driver(raw_url)
    parsed = urlparse(base)
    query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "ssl":
            query.append(("sslmode", "require" if value in ("require", "true", "1") else value))
            continue
        query.append((key, value))
    rebuilt = urlunparse(parsed._replace(query=urlencode(query)))
    return "postgresql+psycopg://" + rebuilt.removeprefix("postgresql://")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/disaster_db"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        if isinstance(v, str):
            return normalize_async_database_url(v)
        return v

    groq_api_key: str = ""
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    cache_ttl_seconds: int = 300
    nominatim_user_agent: str = "disaster-platform/1.0"
    use_mock_geocoding: bool = False
    use_mock_llm: bool = False


settings = Settings()
