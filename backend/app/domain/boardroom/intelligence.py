from __future__ import annotations

from app.domain.boardroom.assessment import clamp
from app.domain.boardroom.models import (
    BoardVote,
    ExecutiveProfile,
    MeetingTurn,
    StartupBrief,
    StrategicAssessment,
)
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


def build_internal_research(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    profiles: tuple[ExecutiveProfile, ...] = (),
    invited_executives: tuple[str, ...] = (),
) -> dict[str, object]:
    evidence = build_evidence_packet(brief, assessment)
    executive_roles = [profile.role for profile in profiles] or list(invited_executives)
    return {
        "purpose": "Silent pre-meeting research before any executive speaks.",
        "business_understanding": {
            "idea": brief.startup_idea,
            "industry": brief.industry,
            "customer": brief.target_audience,
            "model": brief.business_model,
            "country": brief.country,
        },
        "objectives": _objectives(brief),
        "constraints": _constraints(brief, assessment),
        "evidence": evidence["facts"],
        "assumptions": evidence["assumptions"],
        "unknowns": evidence["missing_information"],
        "contradictions": _contradictions(brief, assessment),
        "hypotheses": _hypotheses(brief, assessment),
        "invited_executives": executive_roles,
        "evidence_quality": {
            "score": evidence["quality_score"],
            "label": evidence["quality_label"],
        },
        "confidence": {
            "research_confidence": _score_to_confidence(int(evidence["quality_score"])),
            "reason": (
                "Confidence is limited to founder-provided facts and deterministic heuristics."
            ),
        },
        "source_discipline": (
            "No external sources were invented. Unverified market, supplier, customer, "
            "and competitor claims remain unknown until supplied or connected through live "
            "providers."
        ),
    }


def build_reasoning_pipeline(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
    decision: str,
) -> dict[str, object]:
    evidence = build_evidence_packet(brief, assessment)
    top_risk = assessment.primary_risks[0][0].replace("_", " ")
    return {
        "rule": "The board must not jump from brief to conclusion without staged reasoning.",
        "stages": [
            _stage(
                "Understand the business",
                _solution_statement(brief),
                evidence["quality_score"],
            ),
            _stage("Extract objectives", _objectives(brief), evidence["quality_score"]),
            _stage(
                "Identify constraints",
                _constraints(brief, assessment),
                evidence["quality_score"],
            ),
            _stage(
                "Identify missing information",
                evidence["missing_information"],
                int(evidence["quality_score"]) - 8,
            ),
            _stage("Build hypotheses", _hypotheses(brief, assessment), evidence["quality_score"]),
            _stage("Gather evidence", evidence["facts"], evidence["quality_score"]),
            _stage(
                "Evaluate evidence quality",
                evidence["quality_label"],
                evidence["quality_score"],
            ),
            _stage(
                "Generate multiple strategies",
                [option["name"] for option in build_strategic_options(brief, assessment)],
                evidence["quality_score"],
            ),
            _stage("Challenge every strategy", f"Highest challenge area: {top_risk}.", 62),
            _stage("Debate", [turn.stance for turn in turns if turn.turn_type != "proposal"], 66),
            _stage("Revise", _latest_revision(turns), 70),
            _stage("Vote", [vote.to_dict() for vote in votes], _average_vote_confidence(votes)),
            _stage(
                "Produce recommendation",
                decision.replace("_", " "),
                _average_vote_confidence(votes),
            ),
            _stage("Produce validation plan", _validation_steps(assessment), 68),
        ],
    }


def build_debate_tree(turns: tuple[MeetingTurn, ...]) -> dict[str, object]:
    nodes = []
    edges = []
    for index, turn in enumerate(turns):
        node_id = f"turn_{index + 1}"
        nodes.append(
            {
                "id": node_id,
                "minute": _clock(index),
                "role": turn.speaker_role,
                "type": turn.turn_type,
                "stance": turn.stance,
                "confidence": round(turn.confidence * 100),
                "claim": turn.message,
            }
        )
        if index > 0:
            edges.append(
                {
                    "from": f"turn_{index}",
                    "to": node_id,
                    "relationship": _edge_relationship(turn),
                    "effect": _edge_effect(turn),
                }
            )

    revision_id = next(
        (f"turn_{index + 1}" for index, turn in enumerate(turns) if turn.turn_type == "revision"),
        None,
    )
    if revision_id:
        for index, turn in enumerate(turns):
            if turn.turn_type in {"critique", "assumption_challenge"}:
                edges.append(
                    {
                        "from": f"turn_{index + 1}",
                        "to": revision_id,
                        "relationship": "forced_revision",
                        "effect": f"{turn.speaker_role} pressure changed the CEO plan.",
                    }
                )

    return {"nodes": nodes, "edges": edges}


def build_confidence_propagation(
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
) -> dict[str, object]:
    role_confidence = {vote.role: round(vote.confidence * 100) for vote in votes}
    influence_events = []
    for turn in turns:
        for reference in turn.memory_references:
            influence_events.append(
                {
                    "source": reference,
                    "target": turn.speaker_role,
                    "direction": "raises scrutiny",
                    "confidence_effect": _confidence_effect(turn),
                    "reason": _turn_reason(turn),
                }
            )

    present_roles = {turn.speaker_role for turn in turns} | {vote.role for vote in votes}
    influence_events.extend(_relationship_influences(present_roles))
    return {
        "final_confidence_by_role": role_confidence,
        "influence_events": influence_events,
        "interpretation": (
            "Confidence is not independent. Strong finance, risk, legal, or operations "
            "arguments can reduce enthusiasm even when the final vote remains supportive."
        ),
    }


def build_counterfactual_analysis(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    decision: str,
) -> list[dict[str, object]]:
    cases = [
        ("Budget need rises 20 percent", 0.06, "capital_pressure"),
        ("Sales or adoption lands 30 percent lower", 0.09, "go_to_market_uncertainty"),
        ("A strong competitor enters the beachhead", 0.08, "competitive_pressure"),
        ("Supplier, vendor, or platform dependency fails", 0.07, "operational_complexity"),
        ("Inflation or rates double the cost pressure", 0.07, "capital_pressure"),
    ]
    return [
        {
            "what_if": label,
            "affected_risk": risk.replace("_", " "),
            "new_risk_score": round(clamp(assessment.risk_scores[risk] + delta) * 100),
            "recommendation_shift": _counterfactual_shift(
                decision,
                clamp(assessment.overall_risk + delta),
            ),
            "board_response": _counterfactual_response(label, brief),
        }
        for label, delta, risk in cases
    ]


def build_scenario_simulator(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    decision: str,
) -> list[dict[str, object]]:
    scenarios = [
        ("Optimistic", -0.12, "Demand validates quickly and costs stay controlled."),
        ("Base", 0.0, "Founder evidence is accurate but still requires proof gates."),
        ("Conservative", 0.1, "Customer conversion and implementation both take longer."),
        ("Worst Case", 0.2, "Revenue is delayed, costs rise, and competitive pressure increases."),
        ("Black Swan", 0.32, "A regulatory, platform, supplier, or trust shock hits the plan."),
    ]
    return [
        {
            "scenario": name,
            "description": description,
            "risk": round(clamp(assessment.overall_risk + delta) * 100),
            "recommended_strategy": _strategy_for_scenario(name, decision),
            "confidence": round(clamp(0.76 - (assessment.overall_risk + delta) * 0.28) * 100),
            "decision": _scenario_decision(decision, clamp(assessment.overall_risk + delta)),
            "validation_focus": _scenario_validation_focus(name, brief),
        }
        for name, delta, description in scenarios
    ]


def build_cognitive_bias_detection(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    turns: tuple[MeetingTurn, ...],
    decision: str,
) -> list[dict[str, object]]:
    evidence_score = int(build_evidence_packet(brief, assessment)["quality_score"])
    detected = []
    if evidence_score < 58 and decision != "defer_pending_de_risking":
        detected.append(
            _bias(
                "confirmation bias",
                "The board may be treating founder-provided evidence as stronger than it is.",
                "Require buyer evidence before scaling spend.",
            )
        )
    if any(turn.speaker_role == "CEO" and turn.confidence > 0.72 for turn in turns):
        detected.append(
            _bias(
                "optimism bias",
                "The opening thesis is confident before external validation is available.",
                "Keep approval conditional on evidence gates.",
            )
        )
    if brief.budget >= 100_000 and assessment.risk_scores["capital_pressure"] >= 0.45:
        detected.append(
            _bias(
                "sunk-cost bias",
                "A large planned budget can make the team defend spend already imagined.",
                "Pre-commit to kill criteria before the money is spent.",
            )
        )
    if brief.competitors:
        detected.append(
            _bias(
                "anchoring",
                "Named competitors can anchor positioning around incumbents instead of customers.",
                "Validate the customer's switching trigger, not only competitor gaps.",
            )
        )
    if not detected:
        detected.append(
            _bias(
                "overconfidence",
                "No severe bias was detected, but early plans can still overstate certainty.",
                "Run the validation plan before treating the recommendation as proven.",
            )
        )
    return detected


def build_executive_challenge_questions(
    brief: StartupBrief,
    assessment: StrategicAssessment,
) -> list[dict[str, object]]:
    questions = [
        "What would make this business fail?",
        "What worries you most about this plan?",
        "Which assumption are you least confident about?",
        "What evidence would completely change your mind?",
    ]
    questions.extend(_risk_questions(assessment))
    return [
        {
            "question": question,
            "why_it_matters": _question_reason(question, brief),
        }
        for question in dict.fromkeys(questions)
    ]


def build_dynamic_expert_roster(
    invited_executives: tuple[str, ...],
) -> dict[str, object]:
    permanent_roles = {profile.role for profile in EXECUTIVE_PROFILES}
    dynamic_roles = [role for role in invited_executives if role not in permanent_roles]
    return {
        "permanent_board_members": [role for role in invited_executives if role in permanent_roles],
        "dynamic_specialists": dynamic_roles,
        "rationale": [
            f"{role} joined because the brief created a specialist risk surface."
            for role in dynamic_roles
        ]
        or ["No additional specialist was needed beyond the permanent board."],
    }


def build_boardroom_timeline(
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
) -> list[dict[str, object]]:
    return [
        {
            "minute": "00:00",
            "phase": "Evidence collection",
            "jump_key": "evidence_packet",
            "what_changed": (
                "Founder facts, assumptions, unknowns, and evidence quality were scored."
            ),
        },
        {
            "minute": "02:00",
            "phase": "Risk review",
            "jump_key": "risk_matrix",
            "what_changed": "Primary risk areas were converted into board constraints.",
        },
        {
            "minute": "04:00",
            "phase": "Executive debate",
            "jump_key": "debate_tree",
            "what_changed": _first_challenge(turns),
        },
        {
            "minute": "08:00",
            "phase": "Revision",
            "jump_key": "reasoning_pipeline",
            "what_changed": _latest_revision(turns),
        },
        {
            "minute": "12:00",
            "phase": "Voting",
            "jump_key": "vote_timeline",
            "what_changed": f"{len(votes)} executives cast final votes.",
        },
        {
            "minute": "15:00",
            "phase": "Final recommendation",
            "jump_key": "final_decision_brief",
            "what_changed": "The recommendation became conditional on validation evidence.",
        },
    ]


def build_decision_explainability(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    votes: tuple[BoardVote, ...],
    decision: str,
) -> dict[str, object]:
    evidence = build_evidence_packet(brief, assessment)
    return {
        "why": _decision_why(decision, votes),
        "evidence": evidence["facts"][:5],
        "confidence": {
            "vote_range": _confidence_range(votes),
            "evidence_quality": evidence["quality_score"],
        },
        "assumptions": evidence["assumptions"],
        "counterarguments": [
            vote.rationale for vote in votes if vote.vote in {"reject", "approve_with_conditions"}
        ][:5],
        "missing_evidence": evidence["missing_information"],
        "validation_steps": _validation_steps(assessment),
        "plain_english": (
            f"The board is not saying '{brief.startup_idea}' is proven. It is saying "
            "the next decision should be earned through evidence gates."
        ),
    }


def build_executive_performance_tracking(
    turns: tuple[MeetingTurn, ...],
    votes: tuple[BoardVote, ...],
) -> list[dict[str, object]]:
    turns_by_role = {turn.speaker_role: turn for turn in turns}
    return [
        {
            "role": vote.role,
            "prediction_accuracy": "pending recorded outcomes",
            "evidence_quality": _role_evidence_quality(turns_by_role.get(vote.role)),
            "vote_stability": _vote_stability(vote),
            "recommendation_quality": _recommendation_quality(turns_by_role.get(vote.role)),
            "learning_status": "will improve after outcome and performance entries are recorded",
        }
        for vote in votes
    ]


def build_ai_reflection(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    turns: tuple[MeetingTurn, ...],
) -> dict[str, object]:
    evidence = build_evidence_packet(brief, assessment)
    return {
        "where_evidence_was_weak": evidence["missing_information"][:5],
        "dominant_assumptions": evidence["assumptions"][:5],
        "what_should_be_investigated": _validation_steps(assessment),
        "could_another_board_disagree": (
            "Yes. A board with live market, customer, supplier, legal, or outcome data could "
            "change the risk weights and vote differently."
        ),
        "self_critique": [
            "The system used deterministic heuristics, not live external research.",
            "It emphasized risk gates over certainty because evidence is still incomplete.",
            (
                f"The debate included {len(turns)} turns, but actual outcome tracking is "
                "still pending."
            ),
        ],
    }


def build_decision_journal(
    brief: StartupBrief,
    assessment: StrategicAssessment,
    votes: tuple[BoardVote, ...],
    decision: str,
    aggregate_confidence: float,
) -> dict[str, object]:
    evidence = build_evidence_packet(brief, assessment)
    return {
        "meeting": {
            "startup": brief.startup_idea,
            "mode": brief.normalized_meeting_mode,
            "decision": decision,
            "aggregate_confidence": round(aggregate_confidence, 3),
        },
        "evidence": {
            "quality_score": evidence["quality_score"],
            "facts": evidence["facts"],
            "unknowns": evidence["missing_information"],
        },
        "votes": [vote.to_dict() for vote in votes],
        "outcome": "not recorded yet",
        "lessons_learned": [
            "Record actual customer, revenue, cost, and risk outcomes after validation.",
            "Compare future outcomes against today's assumptions before updating confidence.",
            "Do not overwrite this journal entry; append corrections and results later.",
        ],
    }


def build_validation_plan(assessment: StrategicAssessment) -> list[dict[str, object]]:
    return [
        {
            "step": step,
            "expected_evidence": _expected_evidence(step),
            "confidence_effect": "raises board confidence if passed; lowers it if failed",
        }
        for step in _validation_steps(assessment)
    ]


def _objectives(brief: StartupBrief) -> list[str]:
    return [
        f"Validate whether {brief.target_audience} has urgent demand.",
        f"Prove the {brief.business_model} model with real willingness-to-pay evidence.",
        "Preserve enough runway to pivot if the evidence weakens.",
        "Turn the first operating wedge into a repeatable learning system.",
    ]


def _constraints(brief: StartupBrief, assessment: StrategicAssessment) -> list[str]:
    constraints = [
        f"Budget ceiling: {brief.budget:,.0f}.",
        f"Timeline pressure: {brief.timeline_months} months.",
        f"Evidence quality is limited by founder-supplied inputs in {brief.country}.",
    ]
    for risk, score in assessment.primary_risks[:3]:
        constraints.append(f"{risk.replace('_', ' ')} risk is {round(score * 100)}/100.")
    return constraints


def _contradictions(brief: StartupBrief, assessment: StrategicAssessment) -> list[str]:
    contradictions = []
    if brief.timeline_months <= 4 and assessment.risk_scores["technology_feasibility"] >= 0.5:
        contradictions.append("The timeline is aggressive for the current technical uncertainty.")
    if brief.budget < 75_000 and assessment.risk_scores["capital_pressure"] >= 0.5:
        contradictions.append("The budget may not support the desired scope plus validation work.")
    if brief.competitors and assessment.risk_scores["competitive_pressure"] >= 0.5:
        contradictions.append(
            "Known competitors imply differentiation must be proven, not asserted."
        )
    if assessment.risk_scores["regulatory_exposure"] >= 0.55:
        contradictions.append(
            "The launch plan depends on compliance clarity that is not yet supplied."
        )
    return contradictions or [
        "No direct contradiction was detected, but evidence remains incomplete."
    ]


def _hypotheses(brief: StartupBrief, assessment: StrategicAssessment) -> list[str]:
    highest = assessment.primary_risks[0][0].replace("_", " ")
    return [
        f"If {brief.target_audience} confirms weekly pain, a narrow pilot can earn approval.",
        f"If {highest} remains unresolved, the board should defer or narrow scope.",
        "If paid pilots are unavailable, willingness to pay is weaker than the strategy assumes.",
        "If compliance or trust gates fail, launch should pause even if demand looks attractive.",
    ]


def _solution_statement(brief: StartupBrief) -> str:
    return (
        f"Build a focused {brief.business_model} product for {brief.target_audience} in "
        f"{brief.industry}, then expand only after evidence proves retention and payment."
    )


def _score_to_confidence(score: int) -> str:
    if score >= 72:
        return "moderate-high"
    if score >= 52:
        return "moderate"
    return "low"


def _stage(name: str, output: object, confidence: object) -> dict[str, object]:
    numeric_confidence = confidence if isinstance(confidence, int) else 65
    return {
        "stage": name,
        "status": "completed",
        "output": output,
        "confidence": max(1, min(99, numeric_confidence)),
    }


def _latest_revision(turns: tuple[MeetingTurn, ...]) -> str:
    for turn in reversed(turns):
        if turn.turn_type == "revision":
            return turn.message
    return "No formal revision was recorded."


def _average_vote_confidence(votes: tuple[BoardVote, ...]) -> int:
    if not votes:
        return 0
    return round(sum(vote.confidence for vote in votes) / len(votes) * 100)


def _validation_steps(assessment: StrategicAssessment) -> list[str]:
    steps = [
        "Interview buyers and capture verbatim pain, budget, and urgency evidence.",
        "Secure paid pilots, letters of intent, or deposits before scaling build spend.",
        "Instrument activation, retention, acquisition cost, and support load.",
    ]
    if assessment.risk_scores["technology_feasibility"] >= 0.5:
        steps.append("Run a technical feasibility spike with explicit pass/fail criteria.")
    if assessment.risk_scores["regulatory_exposure"] >= 0.5:
        steps.append("Complete a jurisdiction-specific compliance review before launch.")
    if assessment.risk_scores["data_ethics"] >= 0.5:
        steps.append("Define consent, human review, explainability, and escalation rules.")
    return steps


def _edge_relationship(turn: MeetingTurn) -> str:
    if turn.turn_type == "assumption_challenge":
        return "devils_advocate_challenge"
    if turn.turn_type == "critique":
        return "functional_disagreement"
    if turn.turn_type == "revision":
        return "position_changed"
    return "sequence"


def _edge_effect(turn: MeetingTurn) -> str:
    if turn.turn_type == "assumption_challenge":
        return "Weak assumptions were surfaced before the wider debate continued."
    if turn.turn_type == "critique":
        return f"{turn.speaker_role} added role-specific constraints."
    if turn.turn_type == "revision":
        return "The CEO incorporated dissent into the final operating recommendation."
    return "The meeting moved to the next reasoning step."


def _confidence_effect(turn: MeetingTurn) -> str:
    if turn.confidence >= 0.75:
        return "+3 to +6 points for aligned roles"
    if turn.confidence <= 0.52:
        return "-4 to -8 points because uncertainty increased"
    return "mixed influence; scrutiny increased but direction remained viable"


def _relationship_influences(present_roles: set[str]) -> list[dict[str, object]]:
    relationships = [
        (
            "CFO",
            "CEO",
            "trusted_financial_guardrail",
            "CEO confidence moves down when CFO flags runway pressure.",
        ),
        (
            "Risk Officer",
            "CMO",
            "productive_tension",
            "Risk challenges Marketing when demand evidence is mostly narrative.",
        ),
        (
            "Operations Advisor",
            "CFO",
            "execution_finance_alignment",
            "Operations supports Finance when scope creates support or staffing cost.",
        ),
        (
            "Legal Advisor",
            "CEO",
            "compliance_interrupt",
            "Legal interrupts strategy when compliance has not been converted into gates.",
        ),
    ]
    return [
        {
            "source": source,
            "target": target,
            "relationship": relation,
            "confidence_effect": effect,
        }
        for source, target, relation, effect in relationships
        if source in present_roles and target in present_roles
    ]


def _counterfactual_shift(decision: str, risk: float) -> str:
    if risk >= 0.7:
        return "shift to defer pending de-risking"
    if risk >= 0.56 and decision == "approve":
        return "shift to approve with conditions"
    if risk >= 0.56:
        return "tighten conditions and validation gates"
    return "recommendation likely holds"


def _counterfactual_response(label: str, brief: StartupBrief) -> str:
    if "Sales" in label:
        return f"Cut scope and prove one paid use case inside {brief.target_audience}."
    if "competitor" in label.lower():
        return "Move from broad positioning to a specific competitor weakness and proof asset."
    if "Supplier" in label:
        return "Add backup vendors, substitute inputs, and customer communication playbooks."
    return "Recalculate runway, delay nonessential spend, and rerun the board."


def _strategy_for_scenario(name: str, decision: str) -> str:
    if name == "Optimistic":
        return "Constrained MVP with faster pilot expansion."
    if name == "Base":
        return decision.replace("_", " ")
    if name == "Conservative":
        return "Concierge pilot with strict spend gates."
    if name == "Worst Case":
        return "Evidence pause until demand and cost assumptions recover."
    return "Crisis protocol: preserve cash, protect trust, and reassess viability."


def _scenario_decision(decision: str, risk: float) -> str:
    if risk >= 0.74:
        return "defer_pending_de_risking"
    if risk >= 0.56:
        return "approve_with_conditions"
    return decision


def _scenario_validation_focus(name: str, brief: StartupBrief) -> str:
    if name == "Optimistic":
        return "Avoid over-expansion; keep measuring retention and support load."
    if name == "Base":
        return f"Validate paid urgency from {brief.target_audience}."
    if name == "Conservative":
        return "Protect runway and require evidence before each spend gate."
    if name == "Worst Case":
        return "Test whether the business should pivot, pause, or exit."
    return "Define emergency triggers and a decision owner before the shock happens."


def _bias(name: str, signal: str, correction: str) -> dict[str, object]:
    return {
        "bias": name,
        "signal": signal,
        "polite_correction": correction,
    }


def _risk_questions(assessment: StrategicAssessment) -> list[str]:
    questions = []
    for risk, _score in assessment.primary_risks[:3]:
        questions.append(f"What evidence would reduce {risk.replace('_', ' ')} risk?")
    return questions


def _question_reason(question: str, brief: StartupBrief) -> str:
    if "fail" in question.lower():
        return "Failure-mode thinking prevents the board from approving a fragile plan."
    if "worries" in question.lower():
        return "The founder's fear often reveals the true unresolved constraint."
    if "least confident" in question.lower():
        return "Low-confidence assumptions should become validation tasks."
    if "change your mind" in question.lower():
        return "Decision reversibility improves when disconfirming evidence is named early."
    return f"It turns uncertainty about {brief.startup_idea} into an evidence request."


def _first_challenge(turns: tuple[MeetingTurn, ...]) -> str:
    for turn in turns:
        if turn.turn_type in {"assumption_challenge", "critique"}:
            return turn.message
    return "No challenge was recorded."


def _decision_why(decision: str, votes: tuple[BoardVote, ...]) -> str:
    supportive = sum(1 for vote in votes if vote.vote in {"approve", "approve_with_conditions"})
    rejected = sum(1 for vote in votes if vote.vote == "reject")
    return (
        f"The board reached {decision.replace('_', ' ')} because {supportive} executives "
        f"supported the plan and {rejected} rejected it after dissent and revision."
    )


def _vote_stability(vote: BoardVote) -> str:
    if vote.vote == "approve":
        return "stable support unless validation evidence weakens"
    if vote.vote == "approve_with_conditions":
        return "conditional and sensitive to evidence gates"
    return "unstable until missing evidence is resolved"


def _recommendation_quality(turn: MeetingTurn | None) -> str:
    if turn is None:
        return "pending role-specific recommendation tracking"
    if len(turn.recommendations) >= 3 and turn.concerns:
        return "strong: concern plus multiple validation recommendations"
    if turn.recommendations:
        return "moderate: recommendation present but evidence depth is limited"
    return "weak: no explicit recommendation captured"


def _expected_evidence(step: str) -> str:
    lowered = step.lower()
    if "buyer" in lowered:
        return "Interview notes, segment scores, objections, and willingness-to-pay signals."
    if "paid" in lowered or "letter" in lowered:
        return "Signed pilot, deposit, LOI, or clear rejection reason."
    if "activation" in lowered:
        return "Instrumented usage, retention, acquisition, and support metrics."
    if "technical" in lowered:
        return "Prototype result, failure log, architecture decision, and cost estimate."
    if "compliance" in lowered:
        return "Legal memo, checklist, control owner, and launch blocking issues."
    return "Documented pass/fail result and board confidence update."


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
