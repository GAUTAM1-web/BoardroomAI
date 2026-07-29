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
    deployment_target: str = Field(default="auto", alias="DEPLOYMENT_TARGET")
    public_frontend_url: str = Field(default="", alias="PUBLIC_FRONTEND_URL")
    public_api_url: str = Field(default="", alias="PUBLIC_API_URL")
    frontend_base_url: str = Field(default="", alias="FRONTEND_BASE_URL")
    database_url: str = Field(
        default="postgresql+asyncpg://boardroom:boardroom_dev_password@localhost:5432/boardroom_ai",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    ai_provider: str = Field(default="local", alias="AI_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    business_data_mode: str = Field(default="demo", alias="BUSINESS_DATA_MODE")
    maps_provider: str = Field(default="osm_nominatim", alias="MAPS_PROVIDER")
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
    session_secret: str = Field(default="", alias="SESSION_SECRET")
    session_cookie_name: str = Field(default="boardroom_session", alias="SESSION_COOKIE_NAME")
    session_ttl_seconds: int = Field(default=604800, alias="SESSION_TTL_SECONDS")
    auth_email_enabled: bool = Field(default=True, alias="AUTH_EMAIL_ENABLED")
    auth_demo_enabled: bool = Field(default=True, alias="AUTH_DEMO_ENABLED")
    auth_guest_enabled: bool = Field(default=True, alias="AUTH_GUEST_ENABLED")
    oauth_google_enabled: bool = Field(default=False, alias="OAUTH_GOOGLE_ENABLED")
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    demo_content_enabled: bool = Field(default=True, alias="DEMO_CONTENT_ENABLED")
    rate_limit_per_minute: int = Field(default=240, alias="RATE_LIMIT_PER_MINUTE")
    distributed_sessions_enabled: bool = Field(default=True, alias="DISTRIBUTED_SESSIONS_ENABLED")
    shared_cache_ttl_seconds: int = Field(default=300, alias="SHARED_CACHE_TTL_SECONDS")
    job_queue_backend: str = Field(default="redis", alias="JOB_QUEUE_BACKEND")
    job_default_timeout_seconds: int = Field(default=900, alias="JOB_DEFAULT_TIMEOUT_SECONDS")
    job_max_attempts: int = Field(default=3, alias="JOB_MAX_ATTEMPTS")
    csrf_protection_enabled: bool = Field(default=False, alias="CSRF_PROTECTION_ENABLED")
    security_headers_enabled: bool = Field(default=True, alias="SECURITY_HEADERS_ENABLED")
    content_security_policy: str = Field(
        default=(
            "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "connect-src 'self' http: https: ws: wss:"
        ),
        alias="CONTENT_SECURITY_POLICY",
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
