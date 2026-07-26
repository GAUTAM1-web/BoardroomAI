from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

from app.core.config import Settings

AuthMode = Literal["email", "demo", "guest"]


def create_session_payload(
    *,
    mode: AuthMode,
    email: str | None,
    settings: Settings,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    role = "Administrator" if mode == "demo" else "Viewer" if mode == "guest" else "Analyst"
    display_name = (
        "Demo Executive"
        if mode == "demo"
        else "Guest Reviewer"
        if mode == "guest"
        else (email or "Workspace User").split("@")[0].replace(".", " ").title()
    )
    user_email = email or ("demo@boardroom.local" if mode == "demo" else "guest@boardroom.local")
    return {
        "session_id": str(uuid4()),
        "mode": mode,
        "user": {
            "email": user_email,
            "display_name": display_name,
            "role": role,
            "organization": "Default Organization",
        },
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=_ttl(settings))).isoformat(),
    }


def sign_session(payload: dict[str, Any], settings: Settings) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(_secret(settings), body.encode("utf-8"), hashlib.sha256).digest()
    return f"{body}.{_b64(signature)}"


def verify_session(token: str | None, settings: Settings) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    body, signature = token.split(".", 1)
    expected = _b64(hmac.new(_secret(settings), body.encode("utf-8"), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_unb64(body).decode("utf-8"))
        expires_at = datetime.fromisoformat(str(payload["expires_at"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if expires_at <= datetime.now(UTC):
        return None
    return payload if isinstance(payload, dict) else None


def auth_capabilities(settings: Settings) -> dict[str, Any]:
    return {
        "email_login": settings.auth_email_enabled,
        "demo_account": settings.auth_demo_enabled,
        "guest_mode": settings.auth_guest_enabled,
        "session_persistence": True,
        "oauth_ready": [
            {
                "provider": "google",
                "enabled": settings.oauth_google_enabled and bool(settings.google_client_id),
            }
        ],
    }


def _ttl(settings: Settings) -> int:
    return max(300, int(settings.session_ttl_seconds or 604800))


def _secret(settings: Settings) -> bytes:
    value = settings.session_secret or "boardroom-development-session-secret"
    return value.encode("utf-8")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
