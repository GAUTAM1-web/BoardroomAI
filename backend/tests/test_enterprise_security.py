from __future__ import annotations

from app.domain.enterprise.security import has_permission, normalize_enterprise_role


def test_enterprise_roles_are_normalized() -> None:
    assert normalize_enterprise_role("Admin") == "administrator"
    assert normalize_enterprise_role("CEO") == "ceo"
    assert normalize_enterprise_role("Unknown") == "viewer"


def test_enterprise_permissions_are_role_scoped() -> None:
    assert has_permission("Administrator", "workspace:admin")
    assert has_permission("Manager", "approvals:approve")
    assert has_permission("Analyst", "reports:comment")
    assert not has_permission("Viewer", "tasks:manage")
    assert not has_permission("Viewer", "reports:export")
