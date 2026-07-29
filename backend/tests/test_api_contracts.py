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


def test_global_enterprise_saas_routes_are_registered() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert "get" in paths["/api/v1/enterprise/intelligence-suite"]
    assert "get" in paths["/api/v1/enterprise/executive-memory"]
    assert "get" in paths["/api/v1/enterprise/knowledge-graph"]
    assert "get" in paths["/api/v1/enterprise/advanced-analytics"]
    assert "post" in paths["/api/v1/enterprise/assistant"]
    assert "get" in paths["/api/v1/search/global"]
    assert "post" in paths["/api/v1/documents/import"]
    assert "get" in paths["/api/v1/collaboration/presence"]
    assert "post" in paths["/api/v1/workflows/run"]
    assert "get" in paths["/api/v1/observability"]


def test_production_readiness_routes_are_registered() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert "get" in paths["/health/live"]
    assert "get" in paths["/health/ready"]
    assert "get" in paths["/api/v1/auth/config"]
    assert "get" in paths["/api/v1/auth/session"]
    assert "post" in paths["/api/v1/auth/session"]
    assert "post" in paths["/api/v1/auth/logout"]
    assert "get" in paths["/api/v1/diagnostics"]
    assert "get" in paths["/api/v1/diagnostics/environment"]
    assert "get" in paths["/api/v1/diagnostics/providers"]
    assert "get" in paths["/api/v1/diagnostics/dependencies"]
    assert "get" in paths["/api/v1/versions"]
    assert "get" in paths["/api/v2/status"]


def test_operations_routes_are_registered() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert "get" in paths["/api/v1/operations/cache/health"]
    assert "get" in paths["/api/v1/operations/jobs"]
    assert "post" in paths["/api/v1/operations/jobs"]
    assert "get" in paths["/api/v1/operations/jobs/{job_id}"]
    assert "post" in paths["/api/v1/operations/jobs/{job_id}/cancel"]
    assert "post" in paths["/api/v1/operations/jobs/{job_id}/retry"]
    assert "get" in paths["/api/v1/operations/schedules"]
    assert "post" in paths["/api/v1/operations/schedules"]
    assert "patch" in paths["/api/v1/operations/schedules/{schedule_id}"]
    assert "post" in paths["/api/v1/operations/schedules/run-due"]
    assert "get" in paths["/api/v1/operations/monitoring"]
    assert "get" in paths["/api/v1/operations/recovery/plan"]
    assert "get" in paths["/api/v1/operations/integrity"]
    assert "get" in paths["/api/v1/operations/plugins"]
    assert "get" in paths["/api/v1/operations/benchmarks"]
