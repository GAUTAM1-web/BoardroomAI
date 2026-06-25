from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.boardroom.models import ExecutiveOpinion, MeetingTurn


@dataclass
class ExecutiveMemory:
    """Meeting-scoped memory that every executive can consult during discussion."""

    turns: list[MeetingTurn] = field(default_factory=list)
    concerns_by_role: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def remember(self, turn: MeetingTurn) -> None:
        self.turns.append(turn)
        self.concerns_by_role[turn.speaker_role] = turn.concerns

    def references_for(self, role: str) -> tuple[str, ...]:
        if not self.turns:
            return ()
        latest = self.turns[-1]
        references = [latest.speaker_role]
        cfo_turn = self._latest_by_role("CFO")
        cto_turn = self._latest_by_role("CTO")
        investor_turn = self._latest_by_role("Investor")

        if role != "CFO" and cfo_turn is not None and cfo_turn.speaker_role not in references:
            references.append("CFO")
        if role != "CTO" and cto_turn is not None and cto_turn.speaker_role not in references:
            references.append("CTO")
        if (
            role not in {"Investor", "VC Partner"}
            and investor_turn is not None
            and investor_turn.speaker_role not in references
        ):
            references.append("Investor")
        return tuple(references[:3])

    def contextualize(self, opinion: ExecutiveOpinion) -> ExecutiveOpinion:
        references = self.references_for(opinion.role)
        if not references:
            return opinion

        prefix = self._prefix(opinion.role, references)
        return ExecutiveOpinion(
            role=opinion.role,
            stance=opinion.stance,
            confidence=opinion.confidence,
            message=f"{prefix} {opinion.message}",
            concerns=opinion.concerns,
            recommendations=opinion.recommendations,
        )

    def reasoning_for(self, opinion: ExecutiveOpinion) -> tuple[str, ...]:
        references = self.references_for(opinion.role)
        reasoning = [
            f"{opinion.role} evaluates the founder brief through its role-specific charter.",
            f"Current stance is '{opinion.stance}' with confidence {round(opinion.confidence, 3)}.",
        ]
        if references:
            reasoning.append(f"References prior arguments from {', '.join(references)}.")
        if opinion.concerns:
            reasoning.append(f"Primary concern: {opinion.concerns[0]}.")
        return tuple(reasoning)

    def _latest_by_role(self, role: str) -> MeetingTurn | None:
        for turn in reversed(self.turns):
            if turn.speaker_role == role:
                return turn
        return None

    def _prefix(self, role: str, references: tuple[str, ...]) -> str:
        first = references[0]
        if role == "CFO" and first == "CTO":
            return (
                "I disagree with the CTO on sequencing because the runway risk is more immediate."
            )
        if role == "CTO" and first == "CEO":
            return "After hearing the CEO, I agree with the direction but need tighter proof."
        if role == "Investor":
            return f"The {first} raised an important concern, and I am weighing it against scale."
        if role == "Legal Advisor":
            return f"After hearing {first}, I need to check the compliance implications."
        if role == "AI Ethics Advisor":
            return f"Building on {first}'s point, trust and governance need to be explicit."
        return f"After hearing {first}, I am updating my view."
