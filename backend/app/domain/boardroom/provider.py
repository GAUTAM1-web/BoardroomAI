from __future__ import annotations

from typing import Protocol

from app.domain.boardroom.models import (
    BoardVote,
    ExecutiveOpinion,
    ExecutiveProfile,
    StartupBrief,
    StrategicAssessment,
)


class ExecutiveIntelligenceProvider(Protocol):
    def propose_strategy(
        self,
        brief: StartupBrief,
        assessment: StrategicAssessment,
        ceo: ExecutiveProfile,
    ) -> ExecutiveOpinion:
        """Create the opening CEO strategy."""

    def critique_strategy(
        self,
        brief: StartupBrief,
        assessment: StrategicAssessment,
        profile: ExecutiveProfile,
        opening_thesis: ExecutiveOpinion,
    ) -> ExecutiveOpinion:
        """Return an executive's independent critique."""

    def revise_strategy(
        self,
        brief: StartupBrief,
        assessment: StrategicAssessment,
        critiques: tuple[ExecutiveOpinion, ...],
    ) -> ExecutiveOpinion:
        """Synthesize dissent into a revised strategic plan."""

    def vote(
        self,
        profile: ExecutiveProfile,
        opinion: ExecutiveOpinion,
        assessment: StrategicAssessment,
        mitigation_strength: float,
    ) -> BoardVote:
        """Cast a final board vote."""
