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
    opinion_sections = _executive_opinions(turns, votes)
    vc_scores = _vc_scores(assessment, aggregate_confidence, decision)
    market = _market_analysis(brief, assessment)
    financial = _financial_analysis(brief, assessment)

    sections = {
        "executive_summary": {
            "thesis": (
                f"Boardroom AI recommends {decision.replace('_', ' ')} for '{brief.startup_idea}' "
                f"as a focused {brief.business_model} opportunity in {brief.industry}."
            ),
            "startup_overview": _startup_overview(brief, decision, aggregate_confidence),
            "board_position": (
                f"{len(approved)} executives approve, {len(conditional)} approve with conditions, "
                f"and {len(rejected)} reject until de-risked."
            ),
            "highest_priority": top_recommendations[:3],
            "vc_readiness_snapshot": vc_scores,
        },
        "startup_overview": _startup_overview(brief, decision, aggregate_confidence),
        "executive_opinions": opinion_sections,
        "business_plan": {
            "beachhead": brief.target_audience,
            "offer": f"A focused first product for {brief.target_audience}.",
            "problem": _problem_statement(brief),
            "solution": _solution_statement(brief),
            "operating_model": [
                "Validate the painful workflow before broad platform expansion.",
                "Use expert-led onboarding to convert early customers into case studies.",
                "Tie roadmap expansion to measured retention and willingness to pay.",
            ],
            "success_metrics": [
                "Activation rate above 55 percent in the first pilot cohort.",
                "At least 3 paid pilots or letters of intent within 90 days.",
                "Clear retention signal from weekly repeated workflow usage.",
            ],
        },
        "market_analysis": market,
        "competitor_analysis": _competitor_analysis(brief),
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
                "Create proprietary workflow benchmarks from early deployments",
            ],
            "threats": [
                "Well-funded competitors can copy broad messaging",
                "Regulatory or security failures can erase trust quickly",
                "Buyer urgency may be lower than founder intuition suggests",
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
            "security_controls": [
                "Audit every board event",
                "Separate provider adapters from persisted meeting state",
                "Treat report exports as generated artifacts from immutable meeting data",
            ],
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
        "financial_forecast": financial,
        "financial_analysis": financial,
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
        "risk_matrix": _risk_matrix(assessment),
        "action_plan": {
            "immediate_actions": top_recommendations[:4],
            "30_day_plan": [
                "Complete buyer discovery and rank segments by pain, urgency, and budget.",
                "Define legal, security, and data-handling requirements before pilot onboarding.",
                "Instrument activation, retention, and willingness-to-pay signals.",
            ],
            "90_day_plan": [
                "Ship a constrained pilot MVP to the highest-urgency segment.",
                "Convert discovery evidence into a board-ready investor data room.",
                "Run two acquisition channels with measured conversion economics.",
            ],
            "one_year_plan": [
                "Expand only from proven workflow depth into adjacent workflows.",
                "Build partner distribution around the initial wedge.",
                "Formalize governance, support, and customer success playbooks.",
            ],
        },
        "vc_readiness_score": vc_scores,
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


def _startup_overview(
    brief: StartupBrief,
    decision: str,
    aggregate_confidence: float,
) -> dict[str, object]:
    return {
        "startup": brief.startup_idea,
        "problem": _problem_statement(brief),
        "solution": _solution_statement(brief),
        "target_market": brief.target_audience,
        "revenue_model": brief.business_model,
        "business_model": brief.business_model,
        "funding_stage": brief.funding_stage,
        "board_decision": decision,
        "confidence": round(aggregate_confidence, 3),
    }


def _market_analysis(
    brief: StartupBrief,
    assessment: StrategicAssessment,
) -> dict[str, object]:
    tam = max(1.2, 2.8 + len(brief.industry) * 0.18)
    sam = tam * 0.22
    som = sam * 0.08
    return {
        "industry": brief.industry,
        "country": brief.country,
        "tam": f"${tam:.1f}B estimated total addressable market",
        "sam": f"${sam:.1f}B serviceable available market",
        "som": f"${som:.1f}B realistic early serviceable obtainable market",
        "market_growth": "Moderate-to-high if the wedge proves recurring budget ownership.",
        "industry_trends": [
            "AI-enabled workflow compression",
            "Buyer demand for measurable ROI before platform expansion",
            "Trust, compliance, and data governance moving earlier in sales cycles",
        ],
        "demand_view": assessment.signals["competition_signal"],
        "market_risks": [
            risk
            for risk in assessment.risk_scores
            if risk in {"market_complexity", "go_to_market_uncertainty", "competitive_pressure"}
        ],
    }


def _competitor_analysis(brief: StartupBrief) -> dict[str, object]:
    return {
        "major_competitors": list(brief.competitors),
        "advantages": [
            "Narrower workflow depth",
            "Faster time-to-value for the beachhead segment",
            "Board-reviewed operating and risk gates",
        ],
        "disadvantages": [
            "Lower brand awareness than incumbents",
            "Limited early distribution",
            "Unproven retention until pilot usage is measured",
        ],
        "market_positioning": (
            "Position as the specialist operating layer for a painful workflow rather than "
            "a broad horizontal platform."
        ),
        "competitive_moat": [
            "Proprietary customer workflow data",
            "High-touch onboarding insights",
            "Compliance and trust controls embedded in the product",
        ],
    }


def _financial_analysis(
    brief: StartupBrief,
    assessment: StrategicAssessment,
) -> dict[str, object]:
    monthly_burn = max(12_000, brief.budget / max(brief.timeline_months, 1))
    first_year_arr = brief.budget * (1.7 if "b2b" in brief.business_model.lower() else 1.15)
    return {
        "budget": brief.budget,
        "revenue_projection": {
            "first_year_arr": round(first_year_arr, 2),
            "base_case_customers": 12,
            "expansion_case_customers": 28,
        },
        "burn_rate": round(monthly_burn, 2),
        "funding_requirement": round(max(brief.budget * 1.4, monthly_burn * 12), 2),
        "scaling_cost": round(brief.budget * 2.2, 2),
        "profitability": "Possible after repeatable acquisition and onboarding costs are proven.",
        "runway_signal": assessment.signals["budget_signal"],
        "first_90_day_allocation": {
            "product_and_engineering": 0.45,
            "customer_discovery_and_sales": 0.25,
            "security_legal_compliance": 0.15,
            "operations_and_contingency": 0.15,
        },
    }


def _risk_matrix(assessment: StrategicAssessment) -> dict[str, object]:
    mapping = {
        "technical": "technology_feasibility",
        "legal": "regulatory_exposure",
        "financial": "capital_pressure",
        "operational": "operational_complexity",
        "security": "data_ethics",
        "hiring": "timeline_pressure",
        "compliance": "regulatory_exposure",
        "market": "market_complexity",
    }
    matrix = {}
    for label, risk_key in mapping.items():
        score = assessment.risk_scores[risk_key]
        matrix[label] = {
            "score": round(score, 3),
            "severity": _severity(score),
            "mitigation": _mitigation_for(risk_key),
        }
    return matrix


def _executive_opinions(
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
) -> list[dict[str, object]]:
    turns_by_role: dict[str, MeetingTurn] = {}
    for turn in turns:
        turns_by_role[turn.speaker_role] = turn
    opinions = []
    for vote in votes:
        turn = turns_by_role.get(vote.role)
        opinions.append(
            {
                "role": vote.role,
                "opinion": turn.message if turn else vote.rationale,
                "vote": vote.vote,
                "confidence": round(vote.confidence, 3),
                "concerns": list(turn.concerns) if turn else [],
                "recommendations": list(turn.recommendations) if turn else [vote.rationale],
            }
        )
    return opinions


def _vc_scores(
    assessment: StrategicAssessment,
    aggregate_confidence: float,
    decision: str,
) -> dict[str, int]:
    innovation = _score_from_risk(assessment.risk_scores["technology_feasibility"], invert=True)
    execution = _score_from_risk(
        (assessment.risk_scores["timeline_pressure"] + assessment.risk_scores["capital_pressure"])
        / 2,
        invert=True,
    )
    market = _score_from_risk(assessment.risk_scores["market_complexity"], invert=True)
    scalability = _score_from_risk(assessment.risk_scores["operational_complexity"], invert=True)
    competition = _score_from_risk(assessment.risk_scores["competitive_pressure"], invert=True)
    risk = _score_from_risk(assessment.overall_risk, invert=True)
    investment_readiness = round(aggregate_confidence * 100)
    if decision == "defer_pending_de_risking":
        investment_readiness = min(investment_readiness, 62)
    overall = round(
        (
            innovation
            + execution
            + market
            + scalability
            + competition
            + risk
            + investment_readiness
        )
        / 7
    )
    return {
        "innovation": innovation,
        "execution": execution,
        "market": market,
        "scalability": scalability,
        "competition": competition,
        "risk": risk,
        "investment_readiness": investment_readiness,
        "overall_vc_score": overall,
    }


def _score_from_risk(value: float, invert: bool) -> int:
    score = (1 - value) * 100 if invert else value * 100
    return max(1, min(99, round(score)))


def _problem_statement(brief: StartupBrief) -> str:
    return (
        f"{brief.target_audience} in {brief.country} need a more reliable way to handle "
        f"the workflow implied by {brief.startup_idea}."
    )


def _solution_statement(brief: StartupBrief) -> str:
    return (
        f"Build a focused {brief.business_model} product that solves one urgent workflow in "
        f"{brief.industry}, proves willingness to pay, and expands only after retention is clear."
    )


def _severity(score: float) -> str:
    if score >= 0.74:
        return "high"
    if score >= 0.52:
        return "medium"
    return "low"


def _mitigation_for(risk_key: str) -> str:
    mitigations = {
        "technology_feasibility": (
            "Run an architecture spike and de-scope non-essential automation."
        ),
        "regulatory_exposure": "Define compliance requirements before production customer data.",
        "capital_pressure": "Reserve contingency and gate spend behind buyer evidence.",
        "operational_complexity": "Document onboarding, support, and escalation workflows early.",
        "data_ethics": "Publish consent, explainability, retention, and human-review controls.",
        "timeline_pressure": "Split the roadmap into discovery, pilot, and evidence gates.",
        "market_complexity": "Interview buyers and rank segments by urgency and budget.",
    }
    return mitigations[risk_key]


def _top_recommendations(turns: tuple[MeetingTurn, ...]) -> list[str]:
    seen: set[str] = set()
    recommendations: list[str] = []
    for turn in turns:
        for recommendation in turn.recommendations:
            if recommendation not in seen:
                recommendations.append(recommendation)
                seen.add(recommendation)
    return recommendations
