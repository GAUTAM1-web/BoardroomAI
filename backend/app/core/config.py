from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+asyncpg://boardroom:boardroom_dev_password@localhost:5432/boardroom_ai",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    ai_provider: str = Field(default="local", alias="AI_PROVIDER")
    business_data_mode: str = Field(default="demo", alias="BUSINESS_DATA_MODE")
    maps_provider: str = Field(default="none", alias="MAPS_PROVIDER")
    places_provider: str = Field(default="osm_nominatim", alias="PLACES_PROVIDER")
    weather_provider: str = Field(default="open_meteo", alias="WEATHER_PROVIDER")
    news_provider: str = Field(default="gdelt_doc", alias="NEWS_PROVIDER")
    currency_provider: str = Field(default="frankfurter", alias="CURRENCY_PROVIDER")
    government_data_provider: str = Field(default="world_bank", alias="GOVERNMENT_DATA_PROVIDER")
    demographics_provider: str = Field(default="world_bank", alias="DEMOGRAPHICS_PROVIDER")
    maps_api_key: str = Field(default="", alias="MAPS_API_KEY")
    places_api_key: str = Field(default="", alias="PLACES_API_KEY")
    gdelt_api_key: str = Field(default="", alias="GDELT_API_KEY")
    live_data_cache_ttl_seconds: int = Field(default=900, alias="LIVE_DATA_CACHE_TTL_SECONDS")
    live_data_timeout_seconds: float = Field(default=2.5, alias="LIVE_DATA_TIMEOUT_SECONDS")
    currency_base: str = Field(default="USD", alias="CURRENCY_BASE")
    currency_quotes: str = Field(default="EUR,GBP,INR", alias="CURRENCY_QUOTES")
    provider_user_agent: str = Field(
        default="BoardroomAI/1.0 (local development; contact=admin@boardroom.local)",
        alias="PROVIDER_USER_AGENT",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env"),
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
