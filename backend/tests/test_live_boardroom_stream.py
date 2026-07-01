from __future__ import annotations

from typing import Any, cast

import pytest

from app.domain.boardroom.models import StartupBrief
from app.domain.boardroom.streaming import (
    REPORT_SECTION_TITLES,
    LiveBoardMeetingOrchestrator,
    NoopMeetingRecorder,
)
from app.infrastructure.ai.local_provider import LocalExecutiveIntelligenceProvider

pytestmark = pytest.mark.asyncio


def _brief() -> StartupBrief:
    return StartupBrief(
        startup_idea="AI operating system that helps independent clinics manage cash flow",
        industry="healthcare fintech",
        country="United States",
        budget=150_000,
        timeline_months=6,
        competitors=("QuickBooks", "Brex", "Ramp"),
        target_audience="clinic owners with 5-50 employees",
        funding_stage="pre-seed",
        business_model="B2B SaaS",
    )


async def _collect_events() -> list[dict[str, Any]]:
    orchestrator = LiveBoardMeetingOrchestrator(
        LocalExecutiveIntelligenceProvider(),
        delay_seconds=0,
    )
    events = []
    async for event in orchestrator.stream(_brief(), recorder=NoopMeetingRecorder()):
        events.append(event.to_dict())
    return events


async def test_live_stream_emits_realtime_board_events() -> None:
    events = await _collect_events()
    event_types = [str(event["event_type"]) for event in events]

    assert event_types[0] == "meeting_started"
    assert "executive_status" in event_types
    assert "timeline_statement" in event_types
    assert "confidence_changed" in event_types
    assert "vote_cast" in event_types
    assert "report_section" in event_types
    assert event_types[-1] == "consensus_reached"


async def test_live_stream_contains_memory_and_vote_changes() -> None:
    events = await _collect_events()
    timeline_events = [event for event in events if event["event_type"] == "timeline_statement"]
    vote_change_events = [event for event in events if event["event_type"] == "vote_changed"]

    assert any(
        cast(dict[str, Any], event["payload"])["memory_references"]
        for event in timeline_events
        if cast(dict[str, Any], event["payload"])["speaker_role"] != "CEO"
    )
    assert any(
        "After hearing" in str(event["payload"]["message"])
        or "I disagree" in str(event["payload"]["message"])
        for event in timeline_events
    )
    assert vote_change_events


async def test_live_stream_generates_streamed_report_sections() -> None:
    events = await _collect_events()
    section_events = [event for event in events if event["event_type"] == "report_section"]
    final_event = events[-1]
    first_section = cast(dict[str, Any], section_events[0]["payload"])
    final_payload = cast(dict[str, Any], final_event["payload"])
    final_result = cast(dict[str, Any], final_payload["result"])

    assert len(section_events) == len(REPORT_SECTION_TITLES)
    assert first_section["section_key"] == "executive_summary"
    assert final_result["consensus_reached"] is True
