from __future__ import annotations

from app.domain.boardroom.export import report_to_markdown, report_to_pdf
from app.domain.boardroom.ideas import StartupIdeaRequest, generate_startup_ideas
from app.domain.boardroom.models import StartupBrief
from app.domain.boardroom.orchestrator import BoardMeetingOrchestrator
from app.infrastructure.ai.local_provider import LocalExecutiveIntelligenceProvider


def test_generator_parses_prompt_count_and_creates_meeting_briefs() -> None:
    ideas = generate_startup_ideas(
        StartupIdeaRequest(
            prompt="Generate 12 startup ideas for healthcare AI",
            country="United States",
        )
    )

    assert len(ideas) == 12
    assert all(idea.meeting_brief.startup_idea for idea in ideas)
    assert all(idea.success_probability > 0 for idea in ideas)


def test_report_exports_markdown_and_pdf_bytes() -> None:
    brief = StartupBrief(
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
    result = BoardMeetingOrchestrator(LocalExecutiveIntelligenceProvider()).run(brief)
    meeting = {
        **result.to_dict(),
        "startup_brief": {
            "startup_idea": brief.startup_idea,
            "industry": brief.industry,
            "country": brief.country,
            "budget": brief.budget,
            "timeline_months": brief.timeline_months,
            "competitors": list(brief.competitors),
            "target_audience": brief.target_audience,
            "funding_stage": brief.funding_stage,
            "business_model": brief.business_model,
        },
    }

    markdown = report_to_markdown(meeting)
    pdf = report_to_pdf(meeting)

    assert "VC Readiness Score" in markdown
    assert pdf.startswith(b"%PDF-1.4")
