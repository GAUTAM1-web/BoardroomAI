from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AuthConfigResponse(BaseModel):
    email_login: bool
    demo_account: bool
    guest_mode: bool
    session_persistence: bool
    oauth_ready: list[dict[str, Any]]


class AuthSessionRequest(BaseModel):
    mode: Literal["email", "demo", "guest"]
    email: str | None = Field(default=None, max_length=240)


class AuthUserResponse(BaseModel):
    email: str
    display_name: str
    role: str
    organization: str


class AuthSessionResponse(BaseModel):
    authenticated: bool = True
    session_id: str
    mode: str
    user: AuthUserResponse
    issued_at: str
    expires_at: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    session: AuthSessionResponse | None = None
    capabilities: dict[str, Any] = Field(default_factory=dict)


class AuthLogoutResponse(BaseModel):
    ok: bool = True
