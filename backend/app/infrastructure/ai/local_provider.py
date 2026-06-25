from __future__ import annotations

from app.domain.boardroom.assessment import clamp
from app.domain.boardroom.models import (
    BoardVote,
    ExecutiveOpinion,
    ExecutiveProfile,
    StartupBrief,
    StrategicAssessment,
)

RISK_LABELS = {
    "market_complexity": "market segmentation and buyer urgency are not yet sharp enough",
    "technology_feasibility": "the technical plan needs tighter architecture and delivery proof",
    "capital_pressure": "the budget creates runway pressure against the requested scope",
    "timeline_pressure": "the timeline is compressed for the amount of validation required",
    "regulatory_exposure": "compliance exposure must be designed into the operating model",
    "competitive_pressure": "the market contains enough competitors to require a clear wedge",
    "go_to_market_uncertainty": "the acquisition motion is still not precise enough",
    "operational_complexity": "delivery and support operations can become complex quickly",
    "data_ethics": "data governance, consent, and AI transparency need explicit controls",
}


class LocalExecutiveIntelligenceProvider:
    """Deterministic strategic reasoning provider used for local development and tests."""

    def propose_strategy(
        self,
        brief: StartupBrief,
        assessment: StrategicAssessment,
        ceo: ExecutiveProfile,
    ) -> ExecutiveOpinion:
        risk_names = [risk for risk, _score in assessment.primary_risks[:3]]
        concerns = tuple(RISK_LABELS[risk] for risk in risk_names)
        recommendations = (
            f"Start with a narrow beachhead inside {brief.target_audience}.",
            (
                "Define one painful workflow, one activation metric, and one revenue "
                "test before scaling."
            ),
            "Use board conditions as operating constraints for the first 90 days.",
        )
        confidence = clamp(0.82 - assessment.overall_risk * 0.18 + ceo.optimism_bias, 0.5, 0.94)
        stance = "support with conditions" if assessment.overall_risk >= 0.52 else "support"
        message = (
            f"The initial strategy is to validate '{brief.startup_idea}' as a focused "
            f"{brief.business_model} in {brief.industry}. The board should approve a constrained "
            "MVP only if the team narrows the wedge, instruments proof, and protects runway."
        )
        return ExecutiveOpinion(
            role=ceo.role,
            stance=stance,
            confidence=confidence,
            message=message,
            concerns=concerns,
            recommendations=recommendations,
        )

    def critique_strategy(
        self,
        brief: StartupBrief,
        assessment: StrategicAssessment,
        profile: ExecutiveProfile,
        opening_thesis: ExecutiveOpinion,
    ) -> ExecutiveOpinion:
        focused_risks = self._focused_risks(profile, assessment)
        strongest_risk = focused_risks[0][1] if focused_risks else assessment.overall_risk
        confidence = clamp(
            0.78 - assessment.overall_risk * 0.16 - strongest_risk * 0.08 + profile.optimism_bias,
            0.42,
            0.94,
        )

        if strongest_risk >= profile.veto_threshold:
            stance = "reject until de-risked"
        elif strongest_risk >= profile.veto_threshold - 0.12:
            stance = "support only with strict conditions"
        else:
            stance = "support with targeted revisions"

        concerns = tuple(RISK_LABELS[risk] for risk, _score in focused_risks[:3])
        recommendations = tuple(
            self._recommendation_for_risk(profile.role, risk, brief)
            for risk, _score in focused_risks[:3]
        )
        message = self._message_for_profile(profile, brief, stance, focused_risks, opening_thesis)

        return ExecutiveOpinion(
            role=profile.role,
            stance=stance,
            confidence=confidence,
            message=message,
            concerns=concerns,
            recommendations=recommendations,
        )

    def revise_strategy(
        self,
        brief: StartupBrief,
        assessment: StrategicAssessment,
        critiques: tuple[ExecutiveOpinion, ...],
    ) -> ExecutiveOpinion:
        repeated_concerns = self._top_repeated_concerns(critiques)
        recommendations = (
            "Reduce the MVP to one mission-critical workflow and one primary persona.",
            "Create a compliance and security checklist before onboarding real customer data.",
            (
                "Reserve budget for customer discovery, onboarding support, "
                "and measurement infrastructure."
            ),
            "Define kill criteria so the board can stop, pivot, or fundraise with evidence.",
        )
        confidence = clamp(0.84 - assessment.overall_risk * 0.12, 0.58, 0.92)
        message = (
            "The revised plan accepts the board's dissent: narrow the beachhead, prove willingness "
            "to pay, ship only the trusted workflow, and make compliance, security, "
            "and metrics part of the first release instead of later cleanup."
        )
        return ExecutiveOpinion(
            role="CEO",
            stance="revised conditional consensus",
            confidence=confidence,
            message=message,
            concerns=tuple(repeated_concerns),
            recommendations=recommendations,
        )

    def vote(
        self,
        profile: ExecutiveProfile,
        opinion: ExecutiveOpinion,
        assessment: StrategicAssessment,
        mitigation_strength: float,
    ) -> BoardVote:
        focused_risk = max(
            (assessment.risk_scores[risk] for risk in profile.risk_focus),
            default=assessment.overall_risk,
        )
        adjusted_risk = clamp(focused_risk - mitigation_strength)

        if adjusted_risk >= profile.veto_threshold:
            vote = "reject"
            rationale = (
                f"{profile.role} rejects the current plan because "
                f"{RISK_LABELS[self._highest_focus(profile, assessment)]}."
            )
        elif adjusted_risk >= profile.veto_threshold - 0.16:
            vote = "approve_with_conditions"
            rationale = (
                f"{profile.role} approves only if the company treats the board conditions as "
                "release gates."
            )
        else:
            vote = "approve"
            rationale = (
                f"{profile.role} approves the revised plan because the immediate scope is narrow "
                "enough to test without pretending the larger strategy is already solved."
            )

        confidence = clamp(opinion.confidence + mitigation_strength * 0.22, 0.45, 0.96)
        return BoardVote(role=profile.role, vote=vote, confidence=confidence, rationale=rationale)

    def _focused_risks(
        self, profile: ExecutiveProfile, assessment: StrategicAssessment
    ) -> list[tuple[str, float]]:
        return sorted(
            ((risk, assessment.risk_scores[risk]) for risk in profile.risk_focus),
            key=lambda item: item[1],
            reverse=True,
        )

    def _highest_focus(self, profile: ExecutiveProfile, assessment: StrategicAssessment) -> str:
        return self._focused_risks(profile, assessment)[0][0]

    def _message_for_profile(
        self,
        profile: ExecutiveProfile,
        brief: StartupBrief,
        stance: str,
        focused_risks: list[tuple[str, float]],
        opening_thesis: ExecutiveOpinion,
    ) -> str:
        strongest = focused_risks[0][0]
        goal = profile.goals[0]
        return (
            f"{profile.role} is {stance}. To {goal}, the plan for "
            f"'{brief.startup_idea}' must address "
            f"that {RISK_LABELS[strongest]}. The CEO thesis is directionally useful, but it needs "
            "measurable gates before the board should treat it as an operating plan."
        )

    def _recommendation_for_risk(self, role: str, risk: str, brief: StartupBrief) -> str:
        recommendations = {
            "market_complexity": (
                f"{role}: interview 15 buyers in {brief.target_audience} and segment by urgency."
            ),
            "technology_feasibility": (
                f"{role}: build a thin architecture spike before committing the full "
                "product roadmap."
            ),
            "capital_pressure": (
                f"{role}: cap the first release to a budgeted MVP and keep 25 percent "
                "runway unallocated."
            ),
            "timeline_pressure": (
                f"{role}: split delivery into discovery, prototype, pilot, and investor "
                "evidence gates."
            ),
            "regulatory_exposure": (
                f"{role}: define compliance requirements before processing production "
                "customer data."
            ),
            "competitive_pressure": (
                f"{role}: choose one competitor weakness and make it the wedge for positioning."
            ),
            "go_to_market_uncertainty": (
                f"{role}: run three channel tests with explicit acquisition cost and "
                "conversion targets."
            ),
            "operational_complexity": (
                f"{role}: document onboarding, support, and escalation flows before launch."
            ),
            "data_ethics": (
                f"{role}: publish consent, explainability, retention, and human review rules."
            ),
        }
        return recommendations[risk]

    def _top_repeated_concerns(self, critiques: tuple[ExecutiveOpinion, ...]) -> list[str]:
        counts: dict[str, int] = {}
        for critique in critiques:
            for concern in critique.concerns:
                counts[concern] = counts.get(concern, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        return [concern for concern, _count in ranked[:4]]
