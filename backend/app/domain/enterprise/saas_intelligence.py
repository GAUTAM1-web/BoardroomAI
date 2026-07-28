from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_assistant_answer(
    question: str,
    search_results: dict[str, Any],
    memory: dict[str, Any],
    analytics: dict[str, Any],
) -> dict[str, Any]:
    normalized = question.strip()
    sources = _search_sources(search_results)
    source_count = sum(len(items) for items in search_results.get("collections", {}).values())
    answer = _answer_text(normalized, search_results, memory, analytics, source_count)
    return {
        "question": normalized,
        "answer": answer,
        "source_count": source_count,
        "sources": sources[:12],
        "recommended_actions": _recommended_actions(normalized, search_results, memory),
        "limitations": [
            "The assistant uses stored BoardroomAI records and configured provider outputs.",
            "Unavailable live provider evidence is reported separately and is not fabricated.",
        ],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def build_intelligence_suggestions(
    memory: dict[str, Any],
    analytics: dict[str, Any],
    observability: dict[str, Any],
) -> list[dict[str, Any]]:
    suggestions = []
    pending_tasks = int(analytics.get("department_scorecards", {}).get("open_tasks", 0))
    if pending_tasks:
        suggestions.append(
            {
                "title": "Clear open enterprise tasks",
                "reason": f"{pending_tasks} open task records are still active.",
                "action": "Review ownership and due dates before the next board review.",
                "priority": "medium",
            }
        )

    rejected = int(memory.get("decision_history", {}).get("rejected_or_deferred", 0))
    if rejected:
        suggestions.append(
            {
                "title": "Review rejected and deferred decisions",
                "reason": f"{rejected} decisions need archived rationale or outcome follow-up.",
                "action": "Search rejected recommendations and convert learnings into templates.",
                "priority": "medium",
            }
        )

    unhealthy = [
        provider
        for provider in observability.get("provider_health", [])
        if provider.get("status") not in {"configured", "available", "demo", "not_required"}
    ]
    if unhealthy:
        suggestions.append(
            {
                "title": "Check provider configuration",
                "reason": f"{len(unhealthy)} provider checks require attention.",
                "action": "Open provider health and retry after credentials or network are fixed.",
                "priority": "high",
            }
        )

    if not suggestions:
        suggestions.append(
            {
                "title": "Run a fresh board review",
                "reason": "No urgent governance blockers were detected in stored records.",
                "action": "Pick a recent recommendation and capture outcome evidence.",
                "priority": "low",
            }
        )
    return suggestions


def build_workflow_catalog() -> dict[str, Any]:
    return {
        "available_triggers": ["meeting.completed", "business_analysis.created", "manual"],
        "available_actions": [
            "generate_report",
            "assign_tasks",
            "notify_executives",
            "export_pdf",
            "archive_decision",
            "update_dashboard",
        ],
        "email_ready": True,
        "desktop_ready": True,
    }


def _answer_text(
    question: str,
    search_results: dict[str, Any],
    memory: dict[str, Any],
    analytics: dict[str, Any],
    source_count: int,
) -> str:
    if source_count:
        top_titles = [
            str(source.get("title"))
            for source in _search_sources(search_results)
            if source.get("title")
        ][:3]
        joined = ", ".join(top_titles)
        return (
            f"I found {source_count} stored records related to '{question}'. "
            f"The strongest matches are {joined}. Use these as evidence references before "
            "approving, rejecting, or assigning follow-up work."
        )

    decisions = memory.get("decision_history", {})
    meeting_total = int(analytics.get("meeting_effectiveness", {}).get("total_meetings", 0))
    return (
        f"I did not find a direct stored match for '{question}'. The workspace currently has "
        f"{meeting_total} meeting records and "
        f"{decisions.get('approved_or_conditionally_approved', 0)} approved or conditionally "
        "approved decisions. Add a document, meeting, or business analysis to ground the "
        "next answer."
    )


def _recommended_actions(
    question: str,
    search_results: dict[str, Any],
    memory: dict[str, Any],
) -> list[str]:
    actions = []
    normalized = question.lower()
    if "reject" in normalized:
        actions.append("Open the rejected decision records and confirm that rationale is archived.")
    if "risk" in normalized:
        actions.append("Review risk trends and create a mitigation owner for unresolved issues.")
    if search_results.get("collections", {}).get("tasks"):
        actions.append("Update task owners and deadlines for matching recommendations.")
    if memory.get("executive_memory"):
        actions.append("Compare executive confidence movement before sign-off.")
    return actions or [
        "Run global search again with a narrower industry, city, executive, or decision term."
    ]


def _search_sources(search_results: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for collection, items in search_results.get("collections", {}).items():
        for item in items:
            if not isinstance(item, dict):
                continue
            sources.append(
                {
                    "collection": collection,
                    "id": item.get("id")
                    or item.get("meeting_id")
                    or item.get("analysis_id")
                    or item.get("report_id"),
                    "title": item.get("title")
                    or item.get("startup_idea")
                    or item.get("business_idea")
                    or item.get("role"),
                }
            )
    return sources
