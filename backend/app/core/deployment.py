from __future__ import annotations

import os
from typing import Any

from app.core.config import Settings

PLACEHOLDER_SESSION_SECRETS = {
    "development-session-secret-change-before-production",
    "replace-with-a-long-random-secret",
    "replace-with-at-least-32-random-characters",
}


def detect_deployment_target(settings: Settings) -> str:
    configured = settings.deployment_target.strip().lower()
    if configured and configured != "auto":
        return configured
    if os.getenv("VERCEL"):
        return "vercel"
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return "railway"
    if os.getenv("RENDER"):
        return "render"
    if os.getenv("FLY_APP_NAME"):
        return "fly.io"
    if os.getenv("K_SERVICE"):
        return "cloud-run"
    if os.getenv("DOCKER_CONTAINER") or os.path.exists("/.dockerenv"):
        return "docker"
    return "local"


def is_production(settings: Settings) -> bool:
    return settings.app_env.strip().lower() in {"production", "prod"}


def effective_cors_origins(settings: Settings) -> list[str]:
    origins = list(settings.cors_origins)
    for value in (
        settings.public_frontend_url,
        settings.frontend_base_url,
        os.getenv("VERCEL_PROJECT_PRODUCTION_URL", ""),
    ):
        normalized = normalize_url(value)
        if normalized and normalized not in origins:
            origins.append(normalized)
    return origins


def environment_diagnostics(settings: Settings) -> dict[str, Any]:
    target = detect_deployment_target(settings)
    production = is_production(settings)
    profile = configuration_profile(settings)
    checks = [
        _check("DATABASE_URL", bool(settings.database_url), required=True),
        _check("REDIS_URL", bool(settings.redis_url), required=production),
        _check("QDRANT_URL", bool(settings.qdrant_url), required=production),
        _check("PUBLIC_API_URL", bool(settings.public_api_url), required=production),
        _check("PUBLIC_FRONTEND_URL", bool(settings.public_frontend_url), required=production),
        _check("SESSION_SECRET", _session_secret_ready(settings), required=production),
        _provider_check("OPENAI_API_KEY", settings.ai_provider, "openai", settings.openai_api_key),
        _provider_check(
            "ANTHROPIC_API_KEY",
            settings.ai_provider,
            "anthropic",
            settings.anthropic_api_key,
        ),
        _provider_check("GEMINI_API_KEY", settings.ai_provider, "gemini", settings.gemini_api_key),
    ]
    required_failures = [item for item in checks if item["required"] and item["status"] != "ok"]
    return {
        "status": "ready" if not required_failures else "degraded",
        "environment": settings.app_env,
        "deployment_target": target,
        "production": production,
        "profile": profile,
        "public_urls": {
            "frontend": normalize_url(settings.public_frontend_url or settings.frontend_base_url),
            "api": normalize_url(settings.public_api_url),
        },
        "cors_origins": effective_cors_origins(settings),
        "checks": checks,
        "missing_required": [item["name"] for item in required_failures],
        "notes": [
            (
                "Diagnostics intentionally report presence and readiness only; secret values are "
                "never returned."
            ),
            (
                "Missing optional providers degrade live evidence but do not block demo or "
                "manual workflows."
            ),
        ],
    }


def configuration_profile(settings: Settings) -> dict[str, Any]:
    environment = settings.app_env.strip().lower() or "development"
    required_by_environment = {
        "development": ["DATABASE_URL"],
        "testing": ["DATABASE_URL"],
        "staging": [
            "DATABASE_URL",
            "REDIS_URL",
            "QDRANT_URL",
            "SESSION_SECRET",
            "PUBLIC_API_URL",
            "PUBLIC_FRONTEND_URL",
        ],
        "production": [
            "DATABASE_URL",
            "REDIS_URL",
            "QDRANT_URL",
            "SESSION_SECRET",
            "PUBLIC_API_URL",
            "PUBLIC_FRONTEND_URL",
        ],
    }
    required = required_by_environment.get(environment, required_by_environment["development"])
    return {
        "environment": environment,
        "required_variables": required,
        "distributed_sessions": getattr(settings, "distributed_sessions_enabled", True),
        "job_queue_backend": getattr(settings, "job_queue_backend", "redis"),
        "shared_cache_ttl_seconds": getattr(settings, "shared_cache_ttl_seconds", 300),
        "csrf_protection": getattr(settings, "csrf_protection_enabled", False),
        "security_headers": getattr(settings, "security_headers_enabled", True),
        "supports": ["development", "testing", "staging", "production"],
    }


def redacted_provider_posture(settings: Settings) -> dict[str, Any]:
    return {
        "ai_provider": settings.ai_provider,
        "openai": bool(settings.openai_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "gemini": bool(settings.gemini_api_key),
        "maps": bool(settings.maps_api_key) or settings.maps_provider != "none",
        "places": bool(settings.places_api_key) or settings.places_provider != "none",
        "news": bool(settings.gdelt_api_key) or settings.news_provider != "none",
        "google_oauth": settings.oauth_google_enabled and bool(settings.google_client_id),
    }


def normalize_url(value: str) -> str:
    trimmed = value.strip().rstrip("/")
    if not trimmed:
        return ""
    if trimmed.startswith(("http://", "https://")):
        return trimmed
    return f"https://{trimmed}"


def _session_secret_ready(settings: Settings) -> bool:
    value = settings.session_secret.strip()
    if not is_production(settings):
        return True
    if len(value) < 32:
        return False
    return value not in PLACEHOLDER_SESSION_SECRETS


def _check(name: str, ok: bool, required: bool) -> dict[str, Any]:
    return {
        "name": name,
        "status": "ok" if ok else "missing",
        "required": required,
    }


def _provider_check(
    name: str,
    configured_provider: str,
    expected_provider: str,
    key_value: str,
) -> dict[str, Any]:
    required = configured_provider.strip().lower() == expected_provider
    return _check(name, bool(key_value) or not required, required=required)
