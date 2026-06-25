from __future__ import annotations

from uuid import uuid4

from app.domain.boardroom.assessment import assess_brief
from app.domain.boardroom.models import (
    BoardMeetingResult,
    BoardVote,
    ExecutiveOpinion,
    MeetingTurn,
    StartupBrief,
)
from app.domain.boardroom.provider import ExecutiveIntelligenceProvider
from app.domain.boardroom.report import build_report
from app.domain.boardroom.roles import EXECUTIVE_PROFILES


class BoardMeetingOrchestrator:
    def __init__(self, provider: ExecutiveIntelligenceProvider) -> None:
        self.provider = provider

    def run(self, brief: StartupBrief) -> BoardMeetingResult:
        assessment = assess_brief(brief)
        ceo = EXECUTIVE_PROFILES[0]
        opening = self.provider.propose_strategy(brief, assessment, ceo)

        turns: list[MeetingTurn] = [
            self._turn(round_number=1, turn_type="proposal", opinion=opening)
        ]

        critiques = tuple(
            self.provider.critique_strategy(brief, assessment, profile, opening)
            for profile in EXECUTIVE_PROFILES[1:]
        )
        turns.extend(
            self._turn(round_number=2, turn_type="critique", opinion=critique)
            for critique in critiques
        )

        revision = self.provider.revise_strategy(brief, assessment, critiques)
        turns.append(self._turn(round_number=3, turn_type="revision", opinion=revision))

        mitigation_strength = self._mitigation_strength(revision, critiques)
        all_opinions = (opening, *critiques)
        votes = tuple(
            self.provider.vote(
                profile,
                self._opinion_for(profile.role, all_opinions),
                assessment,
                mitigation_strength,
            )
            for profile in EXECUTIVE_PROFILES
        )

        consensus_reached = self._is_consensus(votes)
        decision = self._decision(votes, consensus_reached)
        aggregate_confidence = sum(vote.confidence for vote in votes) / len(votes)

        report = build_report(
            brief=brief,
            assessment=assessment,
            turns=tuple(turns),
            votes=votes,
            decision=decision,
            aggregate_confidence=aggregate_confidence,
        )

        return BoardMeetingResult(
            meeting_id=uuid4(),
            consensus_reached=consensus_reached,
            aggregate_confidence=aggregate_confidence,
            decision=decision,
            assessment=assessment,
            turns=tuple(turns),
            votes=votes,
            report=report,
        )

    def _turn(self, round_number: int, turn_type: str, opinion: ExecutiveOpinion) -> MeetingTurn:
        return MeetingTurn(
            round_number=round_number,
            speaker_role=opinion.role,
            turn_type=turn_type,
            stance=opinion.stance,
            confidence=opinion.confidence,
            message=opinion.message,
            concerns=opinion.concerns,
            recommendations=opinion.recommendations,
        )

    def _opinion_for(self, role: str, opinions: tuple[ExecutiveOpinion, ...]) -> ExecutiveOpinion:
        for opinion in opinions:
            if opinion.role == role:
                return opinion
        return opinions[0]

    def _mitigation_strength(
        self,
        revision: ExecutiveOpinion,
        critiques: tuple[ExecutiveOpinion, ...],
    ) -> float:
        unique_conditions = {
            recommendation for critique in critiques for recommendation in critique.recommendations
        }
        condition_factor = min(len(unique_conditions), 12) * 0.012
        revision_factor = min(len(revision.recommendations), 5) * 0.028
        return min(0.24, condition_factor + revision_factor)

    def _is_consensus(self, votes: tuple[BoardVote, ...]) -> bool:
        supportive = sum(1 for vote in votes if vote.vote in {"approve", "approve_with_conditions"})
        rejections = sum(1 for vote in votes if vote.vote == "reject")
        return supportive / len(votes) >= 0.78 and rejections <= 2

    def _decision(self, votes: tuple[BoardVote, ...], consensus_reached: bool) -> str:
        if not consensus_reached:
            return "defer_pending_de_risking"
        conditional = sum(1 for vote in votes if vote.vote == "approve_with_conditions")
        if conditional >= 5:
            return "approve_with_conditions"
        return "approve"
