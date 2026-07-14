from __future__ import annotations

from app.domain.boardroom.assessment import clamp
from app.domain.boardroom.models import BoardVote, MeetingTurn, StartupBrief, StrategicAssessment
from app.domain.boardroom.roles import EXECUTIVE_PROFILES


def build_evidence_packet(
    brief: StartupBrief,
    assessment: StrategicAssessment,
) -> dict[str, object]:
    competitor_count = len([competitor for competitor in brief.competitors if competitor.strip()])
    quality_score = clamp(
        0.34
        + min(competitor_count, 5) * 0.045
        + (0.08 if brief.budget > 0 else 0)
        + (0.08 if brief.timeline_months > 0 else 0)
        + (0.08 if len(brief.target_audience.strip()) >= 18 else 0)
        - assessment.overall_risk * 0.08,
        0.18,
        0.82,
    )
    return {
        "quality_score": round(quality_score * 100),
        "quality_label": _quality_label(quality_score),
        "facts": [
            {"claim": f"Startup idea: {brief.startup_idea}", "source": "founder brief"},
            {"claim": f"Industry: {brief.industry}", "source": "founder brief"},
            {"claim": f"Country: {brief.country}", "source": "founder brief"},
            {"claim": f"Budget: {brief.budget:,.0f}", "source": "founder brief"},
            {"claim": f"Timeline: {brief.timeline_months} months", "source": "founder brief"},
            {
                "claim": f"Target audience: {brief.target_audience}",
                "source": "founder brief",
            },
            {
                "claim": (
                    f"Known competitors: {', '.join(brief.competitors)}"
                    if brief.competitors
                    else "Known competitors were not supplied."
                ),
                "source": "founder brief",
            },
        ],
        "assumptions": _assumptions(brief, assessment),
        "missing_information": _missing_information(brief, assessment),
        "risk_signals": [
            {
                "risk": risk.replace("_", " "),
                "score": round(score * 100),
                "quality": "modeled from brief, not externally verified",
            }
            for risk, score in assessment.primary_risks
        ],
        "responsible_ai_note": (
            "BoardroomAI did not fabricate suppliers, businesses, market sources, "
            "or live evidence. "
            "This meeting uses founder-provided facts plus deterministic risk heuristics."
        ),
    }


def build_strategic_options(
    brief: StartupBrief,
    assessment: StrategicAssessment,
) -> list[dict[str, object]]:
    quality = build_evidence_packet(brief, assessment)["quality_score"]
    options = [
        {
            "option_id": "A",
            "name": "Constrained MVP",
            "description": (
                "Build one trusted workflow for the narrowest high-urgency segment, then expand "
                "only after paid usage evidence."
            ),
            "cost": round(brief.budget * 0.62),
            "time": f"{max(1, min(brief.timeline_months, 4))} months",
            "risk": round(
                (
                    assessment.risk_scores["technology_feasibility"]
                    + assessment.risk_scores["timeline_pressure"]
                )
                / 2
                * 100
            ),
            "confidence": round(clamp(0.78 - assessment.overall_risk * 0.18) * 100),
            "evidence": quality,
            "trade_offs": [
                "Fastest path to product evidence",
                "Requires strict scope discipline",
                "May under-serve broader platform ambition at first",
            ],
        },
        {
            "option_id": "B",
            "name": "Concierge Pilot",
            "description": (
                "Sell a high-touch pilot before full automation, using manual work to discover "
                "true buyer urgency and willingness to pay."
            ),
            "cost": round(brief.budget * 0.42),
            "time": "30-60 days",
            "risk": round(
                (
                    assessment.risk_scores["go_to_market_uncertainty"]
                    + assessment.risk_scores["capital_pressure"]
                )
                / 2
                * 100
            ),
            "confidence": round(clamp(0.74 - assessment.overall_risk * 0.08) * 100),
            "evidence": min(100, int(quality) + 8),
            "trade_offs": [
                "Best learning speed",
                "Lower engineering waste",
                "Less scalable until repeatable workflow data is proven",
            ],
        },
        {
            "option_id": "C",
            "name": "Evidence Pause",
            "description": (
                "Defer build spend until customer, compliance, pricing, and distribution evidence "
                "crosses the board's minimum threshold."
            ),
            "cost": round(brief.budget * 0.18),
            "time": "2-4 weeks",
            "risk": round(max(assessment.risk_scores.values()) * 100),
            "confidence": round(clamp(0.58 + assessment.overall_risk * 0.22) * 100),
            "evidence": min(100, int(quality) + 15),
            "trade_offs": [
                "Protects runway",
                "Improves evidence quality",
                "Delays market learning from a live product",
            ],
        },
    ]

    ranked = sorted(options, key=_option_score, reverse=True)
    for rank, option in enumerate(ranked, start=1):
        option["rank"] = rank
    return ranked


def build_decision_matrix(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    decision: str,
) -> dict[str, object]:
    options = build_strategic_options(brief, assessment)
    recommended = _recommended_option(options, decision)
    return {
        "recommended_option": recommended["option_id"],
        "recommendation": recommended["name"],
        "rows": [
            {
                "option": option["option_id"],
                "name": option["name"],
                "pros": _option_pros(option),
                "cons": _option_cons(option),
                "risks": _option_risks(option, assessment),
                "evidence": f"{option['evidence']}/100 evidence quality",
                "confidence": f"{option['confidence']}/100",
                "unknowns": _missing_information(brief, assessment)[:3],
                "recommended_next_action": _next_action(option),
            }
            for option in options
        ],
    }


def build_confidence_timeline(turns: tuple[MeetingTurn, ...]) -> list[dict[str, object]]:
    return [
        {
            "time": _clock(index),
            "role": turn.speaker_role,
            "confidence": round(turn.confidence * 100),
            "reason": _turn_reason(turn),
        }
        for index, turn in enumerate(turns)
    ]


def build_vote_timeline(votes: tuple[BoardVote, ...]) -> list[dict[str, object]]:
    return [
        {
            "time": _clock(index + 1),
            "role": vote.role,
            "vote": vote.vote,
            "confidence": round(vote.confidence * 100),
            "why": vote.rationale,
        }
        for index, vote in enumerate(votes)
    ]


def build_reasoning_flow(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    turns: tuple[MeetingTurn, ...],
    decision: str,
) -> dict[str, object]:
    return {
        "flow": [
            "Gather founder-provided evidence and score evidence quality.",
            "Identify assumptions and missing information before debate.",
            "Invite relevant executives for the selected meeting mode.",
            "CEO frames the strategic thesis.",
            "Risk Officer challenges the thesis as devil's advocate.",
            "Functional executives debate their role-specific risks.",
            "CEO revises the plan using dissent and missing-evidence gates.",
            "Executives cast final votes and update confidence.",
            "Board produces a decision brief and replay timeline.",
        ],
        "dominant_risks": [
            {"risk": risk.replace("_", " "), "score": round(score * 100)}
            for risk, score in assessment.primary_risks
        ],
        "non_repetition_guard": [
            f"{turn.speaker_role} referenced {', '.join(turn.memory_references)}"
            for turn in turns
            if turn.memory_references
        ][:8],
        "decision": decision,
        "mode": brief.normalized_meeting_mode,
    }


def build_meeting_replay(
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
) -> list[dict[str, object]]:
    replay = []
    for index, turn in enumerate(turns):
        replay.append(
            {
                "time": _clock(index),
                "event": _event_label(turn.turn_type),
                "role": turn.speaker_role,
                "what_happened": turn.message,
                "why_it_changed": (
                    turn.reasoning[-1]
                    if turn.reasoning
                    else turn.concerns[0]
                    if turn.concerns
                    else "Initial board position."
                ),
                "confidence": round(turn.confidence * 100),
            }
        )

    start = len(replay)
    for index, vote in enumerate(votes, start=start):
        replay.append(
            {
                "time": _clock(index),
                "event": "Final vote",
                "role": vote.role,
                "what_happened": vote.vote,
                "why_it_changed": vote.rationale,
                "confidence": round(vote.confidence * 100),
            }
        )
    return replay


def build_executive_scorecard(
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
) -> list[dict[str, object]]:
    profiles = {profile.role: profile for profile in EXECUTIVE_PROFILES}
    turns_by_role = {turn.speaker_role: turn for turn in turns}
    return [
        {
            "role": vote.role,
            "reasoning_style": profiles.get(vote.role).reasoning_style
            if profiles.get(vote.role)
            else "role-specific reasoning",
            "prediction": _prediction_for_vote(vote),
            "confidence": round(vote.confidence * 100),
            "confidence_accuracy": "pending actual outcome tracking",
            "evidence_quality": _role_evidence_quality(turns_by_role.get(vote.role)),
            "vote_change": "tracked in live vote timeline when preliminary and final votes differ",
        }
        for vote in votes
    ]


def build_final_decision_brief(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    votes: tuple[BoardVote, ...],
    decision: str,
    aggregate_confidence: float,
    top_recommendations: list[str],
) -> dict[str, object]:
    evidence = build_evidence_packet(brief, assessment)
    return {
        "recommendation": decision.replace("_", " "),
        "recommended_option": _recommended_option(
            build_strategic_options(brief, assessment),
            decision,
        )["name"],
        "evidence": {
            "quality_score": evidence["quality_score"],
            "strongest_facts": evidence["facts"][:4],
            "missing_information": evidence["missing_information"][:4],
        },
        "confidence": {
            "aggregate": round(aggregate_confidence * 100),
            "range": _confidence_range(votes),
        },
        "risks": [
            {"risk": risk.replace("_", " "), "score": round(score * 100)}
            for risk, score in assessment.primary_risks
        ],
        "immediate_actions": top_recommendations[:4],
        "30_day_actions": [
            "Interview buyers and rank segments by urgency, budget, and access.",
            "Validate pricing with paid pilots, letters of intent, or signed design partners.",
            "Document compliance, security, data, and human-review requirements.",
        ],
        "90_day_actions": [
            "Ship the constrained pilot only if evidence gates are met.",
            "Review confidence accuracy against real customer outcomes.",
            "Re-run the board with measured activation, retention, CAC, and risk data.",
        ],
    }


def build_visual_reasoning_heatmap(assessment: StrategicAssessment) -> list[dict[str, object]]:
    return [
        {
            "risk": risk.replace("_", " "),
            "score": round(score * 100),
            "heat": "high" if score >= 0.72 else "medium" if score >= 0.52 else "low",
        }
        for risk, score in sorted(
            assessment.risk_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]


def _assumptions(brief: StartupBrief, assessment: StrategicAssessment) -> list[str]:
    assumptions = [
        f"{brief.target_audience} has urgent budget ownership for this problem.",
        "The team can access enough customer evidence before heavy build spend.",
        "The first product can be narrowed without losing strategic upside.",
    ]
    if assessment.risk_scores["regulatory_exposure"] >= 0.6:
        assumptions.append("Compliance requirements can be handled before production launch.")
    if assessment.risk_scores["technology_feasibility"] >= 0.55:
        assumptions.append("Technical feasibility can be proven with a small architecture spike.")
    return assumptions


def _missing_information(brief: StartupBrief, assessment: StrategicAssessment) -> list[str]:
    missing = [
        "Verified buyer interviews or recorded customer discovery notes.",
        "Signed pilots, letters of intent, or willingness-to-pay evidence.",
        "Customer acquisition cost assumptions by channel.",
        "Retention or repeat-use signal from a realistic workflow.",
    ]
    if not brief.competitors:
        missing.append("Named competitor or substitute analysis.")
    if assessment.risk_scores["regulatory_exposure"] >= 0.6:
        missing.append("Compliance review by jurisdiction and data category.")
    if assessment.risk_scores["data_ethics"] >= 0.6:
        missing.append("AI governance, human review, consent, and appeal policy.")
    return missing


def _quality_label(score: float) -> str:
    if score >= 0.72:
        return "strong founder evidence, still externally unverified"
    if score >= 0.52:
        return "moderate founder evidence"
    return "thin evidence; board should de-risk before scaling"


def _option_score(option: dict[str, object]) -> float:
    return (
        float(option["confidence"]) * 0.42
        + float(option["evidence"]) * 0.28
        - float(option["risk"]) * 0.2
        - min(float(option["cost"]) / 10_000, 20) * 0.1
    )


def _recommended_option(options: list[dict[str, object]], decision: str) -> dict[str, object]:
    if decision == "defer_pending_de_risking":
        return next(option for option in options if option["option_id"] == "C")
    return options[0]


def _option_pros(option: dict[str, object]) -> list[str]:
    if option["option_id"] == "A":
        return ["Creates product evidence", "Keeps strategic upside", "Clarifies technical scope"]
    if option["option_id"] == "B":
        return [
            "Fastest customer learning",
            "Protects engineering budget",
            "Tests willingness to pay",
        ]
    return ["Protects runway", "Improves evidence quality", "Reduces avoidable execution risk"]


def _option_cons(option: dict[str, object]) -> list[str]:
    if option["option_id"] == "A":
        return [
            "Can still overbuild",
            "Needs strict prioritization",
            "Requires strong pilot access",
        ]
    if option["option_id"] == "B":
        return [
            "Manual work may not scale",
            "Can delay product polish",
            "Needs honest learning discipline",
        ]
    return ["Delays launch", "May lose momentum", "Can become analysis paralysis"]


def _option_risks(
    option: dict[str, object],
    assessment: StrategicAssessment,
) -> list[str]:
    dominant = [risk.replace("_", " ") for risk, _score in assessment.primary_risks[:2]]
    return [f"{risk} remains unresolved" for risk in dominant] + [
        f"Option {option['option_id']} risk score: {option['risk']}/100"
    ]


def _next_action(option: dict[str, object]) -> str:
    if option["option_id"] == "A":
        return "Define the one workflow, one persona, one metric, and one pilot cohort."
    if option["option_id"] == "B":
        return "Sell three concierge pilots before full automation."
    return "Run a two-week evidence sprint before committing build spend."


def _clock(index: int) -> str:
    seconds = index * 75
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _turn_reason(turn: MeetingTurn) -> str:
    if turn.reasoning:
        return turn.reasoning[0]
    if turn.concerns:
        return turn.concerns[0]
    return turn.stance


def _event_label(turn_type: str) -> str:
    labels = {
        "proposal": "Meeting starts",
        "assumption_challenge": "Risk Officer challenges assumptions",
        "critique": "Executive challenge",
        "revision": "CEO revises recommendation",
    }
    return labels.get(turn_type, turn_type.replace("_", " ").title())


def _prediction_for_vote(vote: BoardVote) -> str:
    if vote.vote == "approve":
        return "Plan can proceed if execution stays inside evidence gates."
    if vote.vote == "approve_with_conditions":
        return "Plan is viable only if stated board conditions are met."
    return "Plan should pause until missing evidence is resolved."


def _role_evidence_quality(turn: MeetingTurn | None) -> str:
    if turn is None:
        return "final vote only"
    if turn.concerns and turn.recommendations:
        return "explicit concern plus evidence-producing recommendation"
    if turn.concerns:
        return "concern identified, recommendation incomplete"
    return "limited role-specific evidence"


def _confidence_range(votes: tuple[BoardVote, ...]) -> str:
    if not votes:
        return "0-0"
    values = [round(vote.confidence * 100) for vote in votes]
    return f"{min(values)}-{max(values)}"
