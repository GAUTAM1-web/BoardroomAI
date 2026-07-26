from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

from app.core.config import Settings
from app.core.deployment import environment_diagnostics, normalize_url, redacted_provider_posture
from app.domain.auth import auth_capabilities, create_session_payload, sign_session, verify_session


def test_auth_session_signing_round_trips_without_exposing_secret() -> None:
    settings = cast(
        Settings,
        SimpleNamespace(session_secret="unit-test-secret", session_ttl_seconds=3600),
    )
    payload = create_session_payload(mode="demo", email=None, settings=settings)

    token = sign_session(payload, settings)
    verified = verify_session(token, settings)

    assert verified is not None
    assert verified["mode"] == "demo"
    assert verified["user"]["role"] == "Administrator"
    assert "unit-test-secret" not in token


def test_auth_session_rejects_tampered_and_expired_tokens() -> None:
    settings = cast(
        Settings,
        SimpleNamespace(session_secret="unit-test-secret", session_ttl_seconds=3600),
    )
    payload = {
        "session_id": "expired",
        "mode": "guest",
        "user": {
            "email": "guest@boardroom.local",
            "display_name": "Guest Reviewer",
            "role": "Viewer",
            "organization": "Default Organization",
        },
        "issued_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        "expires_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
    }

    assert verify_session(sign_session(payload, settings), settings) is None
    assert verify_session(f"{sign_session(payload, settings)}tampered", settings) is None


def test_auth_capabilities_are_config_driven() -> None:
    settings = cast(
        Settings,
        SimpleNamespace(
            auth_email_enabled=False,
            auth_demo_enabled=True,
            auth_guest_enabled=False,
            oauth_google_enabled=True,
            google_client_id="client-id",
        ),
    )

    capabilities = auth_capabilities(settings)

    assert capabilities["email_login"] is False
    assert capabilities["demo_account"] is True
    assert capabilities["guest_mode"] is False
    assert capabilities["oauth_ready"] == [{"provider": "google", "enabled": True}]


def test_environment_diagnostics_report_readiness_without_secret_values() -> None:
    settings = cast(
        Settings,
        SimpleNamespace(
            app_env="production",
            deployment_target="auto",
            cors_origins=[],
            database_url="postgresql+asyncpg://user:password@db/boardroom",
            redis_url="redis://redis:6379/0",
            qdrant_url="https://qdrant.example.com",
            public_api_url="https://api.example.com/",
            public_frontend_url="https://app.example.com/",
            frontend_base_url="",
            session_secret="super-secret-session-value-32-plus",
            ai_provider="local",
            openai_api_key="sk-hidden",
            anthropic_api_key="",
            gemini_api_key="",
        ),
    )

    diagnostics = environment_diagnostics(settings)
    serialized = str(diagnostics)

    assert diagnostics["status"] == "ready"
    assert diagnostics["public_urls"] == {
        "frontend": "https://app.example.com",
        "api": "https://api.example.com",
    }
    assert "super-secret-session-value-32-plus" not in serialized
    assert "sk-hidden" not in serialized


def test_provider_posture_is_boolean_and_urls_are_normalized() -> None:
    settings = cast(
        Settings,
        SimpleNamespace(
            ai_provider="openai",
            openai_api_key="sk-hidden",
            anthropic_api_key="anthropic-hidden",
            gemini_api_key="",
            maps_api_key="",
            maps_provider="none",
            places_api_key="places-hidden",
            places_provider="custom",
            gdelt_api_key="",
            news_provider="gdelt_doc",
            oauth_google_enabled=False,
            google_client_id="",
        ),
    )

    posture = redacted_provider_posture(settings)

    assert posture["openai"] is True
    assert posture["anthropic"] is True
    assert posture["gemini"] is False
    assert posture["maps"] is False
    assert posture["places"] is True
    assert normalize_url("app.example.com/") == "https://app.example.com"
