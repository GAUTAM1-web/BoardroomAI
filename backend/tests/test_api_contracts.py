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
