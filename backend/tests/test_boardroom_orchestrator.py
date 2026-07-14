from __future__ import annotations

from dataclasses import replace

from app.domain.boardroom.models import StartupBrief
from app.domain.boardroom.orchestrator import BoardMeetingOrchestrator
from app.domain.boardroom.roles import EXECUTIVE_PROFILES, select_executive_profiles
from app.infrastructure.ai.local_provider import LocalExecutiveIntelligenceProvider


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


def test_board_meeting_includes_every_executive_vote() -> None:
    orchestrator = BoardMeetingOrchestrator(LocalExecutiveIntelligenceProvider())

    result = orchestrator.run(_brief())

    assert len(result.votes) == len(EXECUTIVE_PROFILES)
    assert {vote.role for vote in result.votes} == {profile.role for profile in EXECUTIVE_PROFILES}
    assert all(0.0 < vote.confidence <= 1.0 for vote in result.votes)


def test_board_meeting_generates_required_report_sections() -> None:
    orchestrator = BoardMeetingOrchestrator(LocalExecutiveIntelligenceProvider())

    result = orchestrator.run(_brief())

    required_sections = {
        "executive_summary",
        "evidence_packet",
        "strategic_options",
        "decision_matrix",
        "startup_overview",
        "executive_opinions",
        "business_plan",
        "market_analysis",
        "competitor_analysis",
        "swot",
        "business_model_canvas",
        "customer_personas",
        "technology_architecture",
        "database_design",
        "financial_forecast",
        "hiring_plan",
        "marketing_strategy",
        "investment_readiness",
        "risk_assessment",
        "financial_analysis",
        "risk_matrix",
        "action_plan",
        "vc_readiness_score",
        "pitch_deck_summary",
        "ninety_day_roadmap",
        "board_vote",
        "confidence_scores",
        "confidence_timeline",
        "vote_timeline",
        "reasoning_flow",
        "meeting_replay",
        "executive_scorecard",
        "visual_reasoning_heatmap",
        "final_decision_brief",
    }

    assert required_sections.issubset(result.report.sections.keys())
    assert result.report.sections["confidence_scores"]["aggregate"] == round(
        result.aggregate_confidence, 3
    )


def test_board_meeting_contains_dissent_and_revision() -> None:
    orchestrator = BoardMeetingOrchestrator(LocalExecutiveIntelligenceProvider())

    result = orchestrator.run(_brief())

    assert any("conditions" in vote.vote for vote in result.votes)
    assert any(turn.turn_type == "revision" for turn in result.turns)
    assert any(turn.turn_type == "assumption_challenge" for turn in result.turns)
    assert any(turn.turn_type == "critique" for turn in result.turns)


def test_meeting_mode_selects_dynamic_board_with_risk_officer() -> None:
    orchestrator = BoardMeetingOrchestrator(LocalExecutiveIntelligenceProvider())
    brief = replace(_brief(), meeting_mode="quick_review")

    result = orchestrator.run(brief)
    selected_roles = {profile.role for profile in select_executive_profiles(brief)}

    assert len(result.votes) < len(EXECUTIVE_PROFILES)
    assert {vote.role for vote in result.votes} == selected_roles
    assert "Risk Officer" in selected_roles
    assert result.report.sections["executive_summary"]["meeting_mode"] == "quick_review"
