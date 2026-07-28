from __future__ import annotations

ENTERPRISE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "meetings:create",
        "meetings:view",
        "meetings:edit",
        "reports:comment",
        "reports:export",
        "approvals:approve",
        "tasks:manage",
        "workspace:admin",
    },
    "founder": {
        "meetings:create",
        "meetings:view",
        "meetings:edit",
        "reports:comment",
        "reports:export",
        "approvals:approve",
        "tasks:manage",
        "workspace:admin",
    },
    "ceo": {
        "meetings:create",
        "meetings:view",
        "meetings:edit",
        "reports:comment",
        "reports:export",
        "approvals:approve",
        "tasks:manage",
        "workspace:admin",
    },
    "administrator": {
        "meetings:create",
        "meetings:view",
        "meetings:edit",
        "reports:comment",
        "reports:export",
        "approvals:approve",
        "tasks:manage",
        "workspace:admin",
    },
    "manager": {
        "meetings:create",
        "meetings:view",
        "meetings:edit",
        "reports:comment",
        "reports:export",
        "approvals:approve",
        "tasks:manage",
    },
    "executive": {
        "meetings:create",
        "meetings:view",
        "meetings:edit",
        "reports:comment",
        "reports:export",
        "approvals:approve",
        "tasks:manage",
    },
    "analyst": {
        "meetings:create",
        "meetings:view",
        "reports:comment",
        "tasks:manage",
    },
    "viewer": {
        "meetings:view",
    },
    "guest": {
        "meetings:view",
    },
}


def normalize_enterprise_role(role: str | None) -> str:
    normalized = (role or "administrator").strip().lower().replace(" ", "_")
    if normalized == "admin":
        return "administrator"
    if normalized in {"workspace_owner", "org_owner"}:
        return "owner"
    return normalized if normalized in ENTERPRISE_PERMISSIONS else "viewer"


def has_permission(role: str | None, permission: str) -> bool:
    normalized = normalize_enterprise_role(role)
    permissions = ENTERPRISE_PERMISSIONS.get(normalized, set())
    return permission in permissions
