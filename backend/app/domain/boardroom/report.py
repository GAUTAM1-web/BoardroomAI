from __future__ import annotations

from app.domain.boardroom.models import (
    BoardReport,
    BoardVote,
    MeetingTurn,
    StartupBrief,
    StrategicAssessment,
)


def build_report(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
    decision: str,
    aggregate_confidence: float,
) -> BoardReport:
    primary_risks = [risk for risk, _score in assessment.primary_risks]
    approved = [vote for vote in votes if vote.vote == "approve"]
    conditional = [vote for vote in votes if vote.vote == "approve_with_conditions"]
    rejected = [vote for vote in votes if vote.vote == "reject"]
    top_recommendations = _top_recommendations(turns)

    sections = {
        "executive_summary": {
            "thesis": (
                f"Boardroom AI recommends {decision.replace('_', ' ')} for '{brief.startup_idea}' "
                f"as a focused {brief.business_model} opportunity in {brief.industry}."
            ),
            "board_position": (
                f"{len(approved)} executives approve, {len(conditional)} approve with conditions, "
                f"and {len(rejected)} reject until de-risked."
            ),
            "highest_priority": top_recommendations[:3],
        },
        "business_plan": {
            "beachhead": brief.target_audience,
            "offer": f"A focused first product for {brief.target_audience}.",
            "operating_model": [
                "Validate the painful workflow before broad platform expansion.",
                "Use expert-led onboarding to convert early customers into case studies.",
                "Tie roadmap expansion to measured retention and willingness to pay.",
            ],
        },
        "market_analysis": {
            "industry": brief.industry,
            "country": brief.country,
            "demand_view": assessment.signals["competition_signal"],
            "market_risks": [
                risk
                for risk in primary_risks
                if risk in {"market_complexity", "go_to_market_uncertainty", "competitive_pressure"}
            ],
        },
        "competitor_analysis": {
            "competitors": list(brief.competitors),
            "positioning_wedge": (
                "Win through narrower workflow depth, faster time-to-value, "
                "and founder-grade trust."
            ),
            "defensibility": [
                "Proprietary customer workflow data",
                "High-touch onboarding insights",
                "Compliance and trust controls embedded in the product",
            ],
        },
        "swot": {
            "strengths": [
                "Clear founder problem framing",
                "Board-reviewed operating constraints",
                "Premium product direction with explicit trust requirements",
            ],
            "weaknesses": [
                "Early market evidence is still incomplete",
                "Budget and timeline require strict scope control",
            ],
            "opportunities": [
                "Turn early users into reference customers",
                "Own a narrow category before expanding horizontally",
            ],
            "threats": [
                "Well-funded competitors can copy broad messaging",
                "Regulatory or security failures can erase trust quickly",
            ],
        },
        "business_model_canvas": {
            "customer_segments": [brief.target_audience],
            "value_propositions": ["Faster strategic execution with less founder guesswork"],
            "channels": ["Founder-led sales", "Expert communities", "Partner introductions"],
            "customer_relationships": ["High-touch onboarding", "Board-style quarterly reviews"],
            "revenue_streams": [brief.business_model],
            "key_resources": ["Product engineering", "Domain expertise", "Strategic data model"],
            "key_activities": ["Discovery", "MVP delivery", "Customer success", "Risk governance"],
            "key_partners": [
                "Legal/compliance advisors",
                "Cloud infrastructure",
                "Research data sources",
            ],
            "cost_structure": [
                "Engineering",
                "Customer discovery",
                "Security and compliance",
                "Cloud services",
            ],
        },
        "customer_personas": [
            {
                "name": "Focused Founder",
                "need": "Needs fast validation and a coherent operating plan.",
                "buying_trigger": "Investor deadline, product pivot, or uncertain strategy.",
            },
            {
                "name": "Operator Buyer",
                "need": "Needs decisions converted into execution and accountability.",
                "buying_trigger": "Manual planning is slowing growth.",
            },
        ],
        "technology_architecture": {
            "frontend": (
                "Next.js, React, TypeScript, Tailwind CSS, shadcn-style primitives, Framer Motion"
            ),
            "backend": (
                "FastAPI, clean domain services, provider adapters, "
                "WebSocket-ready event boundaries"
            ),
            "ai": (
                "Provider abstraction over local deterministic intelligence, OpenAI, "
                "Claude, Gemini, and Ollama"
            ),
            "data": "PostgreSQL system of record, Redis event/cache layer, Qdrant strategic memory",
        },
        "database_design": {
            "primary_database": "PostgreSQL",
            "core_tables": [
                "startup_briefs",
                "board_meetings",
                "executive_agents",
                "meeting_turns",
                "board_votes",
                "final_reports",
                "report_sections",
            ],
        },
        "financial_forecast": {
            "budget": brief.budget,
            "runway_signal": assessment.signals["budget_signal"],
            "first_90_day_allocation": {
                "product_and_engineering": 0.45,
                "customer_discovery_and_sales": 0.25,
                "security_legal_compliance": 0.15,
                "operations_and_contingency": 0.15,
            },
        },
        "hiring_plan": [
            "Founding full-stack/product engineer",
            "Fractional design partner",
            "Fractional compliance or legal advisor",
            "Founder-led sales support after first customer signal",
        ],
        "marketing_strategy": {
            "positioning": (
                "A board-level operating system for founders making consequential "
                "startup decisions."
            ),
            "channels": [
                "Founder communities",
                "Investor newsletters",
                "LinkedIn thought leadership",
                "Partner webinars",
            ],
            "proof_assets": [
                "Before/after board reports",
                "90-day execution case studies",
                "Investor-readiness scorecards",
            ],
        },
        "investment_readiness": {
            "stage": brief.funding_stage,
            "readiness": "conditional" if decision != "approve" else "strong for current stage",
            "must_prove": [
                "Urgent buyer problem",
                "Repeatable acquisition wedge",
                "Evidence of retention or repeated usage",
                "Credible path to defensibility",
            ],
        },
        "risk_assessment": {
            "overall_risk": round(assessment.overall_risk, 3),
            "primary_risks": primary_risks,
            "mitigations": top_recommendations[:6],
        },
        "pitch_deck_summary": {
            "slides": [
                "Problem",
                "Customer",
                "Insight",
                "Solution",
                "Market",
                "Business model",
                "Competition",
                "Go-to-market",
                "Traction plan",
                "Team and ask",
            ]
        },
        "ninety_day_roadmap": [
            {"days": "1-30", "focus": "Customer discovery, workflow mapping, architecture spike"},
            {"days": "31-60", "focus": "Pilot MVP, compliance checklist, activation measurement"},
            {"days": "61-90", "focus": "Paid pilot conversion, case study, investor evidence pack"},
        ],
        "board_vote": {
            "decision": decision,
            "votes": [vote.to_dict() for vote in votes],
        },
        "confidence_scores": {
            "aggregate": round(aggregate_confidence, 3),
            "by_role": {vote.role: round(vote.confidence, 3) for vote in votes},
        },
    }

    return BoardReport(
        title=f"Board Report: {brief.startup_idea}",
        decision=decision,
        sections=sections,
    )


def _top_recommendations(turns: tuple[MeetingTurn, ...]) -> list[str]:
    seen: set[str] = set()
    recommendations: list[str] = []
    for turn in turns:
        for recommendation in turn.recommendations:
            if recommendation not in seen:
                recommendations.append(recommendation)
                seen.add(recommendation)
    return recommendations
