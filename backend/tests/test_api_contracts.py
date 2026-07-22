from __future__ import annotations

from app.main import create_app


def test_dashboard_and_history_routes_are_registered_for_get() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert "get" in paths["/api/v1/dashboard"]
    assert "get" in paths["/api/v1/board-meetings"]
    assert "post" in paths["/api/v1/board-meetings"]


def test_history_workflow_routes_match_frontend_methods() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert "get" in paths["/api/v1/board-meetings/{meeting_id}"]
    assert "patch" in paths["/api/v1/board-meetings/{meeting_id}/favorite"]
    assert "delete" in paths["/api/v1/board-meetings/{meeting_id}"]
    assert "get" in paths["/api/v1/search"]
    assert "get" in paths["/api/v1/reports/{meeting_id}/export"]


def test_business_intelligence_routes_are_registered() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert "get" in paths["/api/v1/business-data/providers"]
    assert "post" in paths["/api/v1/business-data/providers/retry"]
    assert "post" in paths["/api/v1/business-analyses"]
    assert "get" in paths["/api/v1/business-analyses"]
    assert "get" in paths["/api/v1/business-analyses/{analysis_id}"]
    assert "get" in paths["/api/v1/business-analyses/{analysis_id}/export"]
    assert "post" in paths["/api/v1/business-analyses/{analysis_id}/performance-entries"]
    assert "post" in paths["/api/v1/business-analyses/{analysis_id}/board-review"]


def test_enterprise_collaboration_routes_are_registered() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert "get" in paths["/api/v1/organizations"]
    assert "post" in paths["/api/v1/organizations"]
    assert "get" in paths["/api/v1/enterprise/dashboard"]
    assert "get" in paths["/api/v1/enterprise/analytics"]
    assert "get" in paths["/api/v1/enterprise/admin"]
    assert "get" in paths["/api/v1/enterprise/audit"]
    assert "get" in paths["/api/v1/report-templates"]
    assert "get" in paths["/api/v1/knowledge/search"]
    assert "get" in paths["/api/v1/tasks"]
    assert "post" in paths["/api/v1/tasks"]
    assert "patch" in paths["/api/v1/tasks/{task_id}"]
    assert "get" in paths["/api/v1/calendar"]
    assert "get" in paths["/api/v1/notifications"]
    assert "post" in paths["/api/v1/board-meetings/{meeting_id}/collaborators"]
    assert "post" in paths["/api/v1/board-meetings/{meeting_id}/approvals"]
    assert "post" in paths["/api/v1/business-analyses/{analysis_id}/approvals"]
    assert "get" in paths["/api/v1/reports/{meeting_id}/comments"]
    assert "post" in paths["/api/v1/reports/{meeting_id}/comments"]
    assert "patch" in paths["/api/v1/reports/{meeting_id}/comments/{comment_id}"]
    assert "post" in paths["/api/v1/approvals/{workflow_id}/steps/{step_id}/decision"]
