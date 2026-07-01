from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from app.domain.boardroom.assessment import assess_brief, clamp
from app.domain.boardroom.memory import ExecutiveMemory
from app.domain.boardroom.models import (
    BoardMeetingResult,
    BoardReport,
    BoardVote,
    ExecutiveOpinion,
    ExecutiveProfile,
    MeetingTurn,
    StartupBrief,
    StrategicAssessment,
)
from app.domain.boardroom.provider import ExecutiveIntelligenceProvider
from app.domain.boardroom.report import build_report
from app.domain.boardroom.roles import EXECUTIVE_PROFILES

REPORT_SECTION_TITLES = {
    "executive_summary": "Executive Summary",
    "startup_overview": "Startup Overview",
    "executive_opinions": "Executive Opinions",
    "business_plan": "Business Plan",
    "market_analysis": "Market Analysis",
    "competitor_analysis": "Competitor Analysis",
    "swot": "SWOT",
    "business_model_canvas": "Business Model Canvas",
    "customer_personas": "Customer Personas",
    "technology_architecture": "Technology Architecture",
    "database_design": "Database Design",
    "financial_forecast": "Financial Forecast",
    "hiring_plan": "Hiring Plan",
    "marketing_strategy": "Marketing Strategy",
    "investment_readiness": "Investment Readiness",
    "risk_assessment": "Risk Assessment",
    "financial_analysis": "Financial Analysis",
    "risk_matrix": "Risk Matrix",
    "action_plan": "Action Plan",
    "vc_readiness_score": "VC Readiness Score",
    "pitch_deck_summary": "Pitch Deck Summary",
    "ninety_day_roadmap": "90-Day Roadmap",
    "board_vote": "Board Vote",
    "confidence_scores": "Confidence Scores",
}


STATUS_BY_ROLE = {
    "CEO": "CEO is thinking...",
    "CTO": "CTO is researching...",
    "CFO": "CFO is calculating...",
    "Investor": "Investor is reviewing...",
    "Legal Advisor": "Lawyer is checking regulations...",
    "VC Partner": "VC Partner is testing fundability...",
    "Market Research Analyst": "Market Research Analyst is sizing demand...",
    "Competitive Intelligence Analyst": "Competitive Intelligence Analyst is mapping rivals...",
    "Cybersecurity Expert": "Cybersecurity Expert is threat modeling...",
    "Economist": "Economist is modeling market conditions...",
    "Growth Strategist": "Growth Strategist is designing experiments...",
    "AI Ethics Advisor": "AI Ethics Advisor is checking governance...",
}


@dataclass(frozen=True)
class BoardroomStreamEvent:
    meeting_id: UUID
    sequence: int
    event_type: str
    payload: dict[str, Any]
    role: str | None = None
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "meeting_id": str(self.meeting_id),
            "sequence": self.sequence,
            "event_type": self.event_type,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }


class BoardMeetingRecorder(Protocol):
    async def start_meeting(
        self,
        meeting_id: UUID,
        brief: StartupBrief,
        assessment: StrategicAssessment,
    ) -> None:
        """Persist the meeting shell before stream events begin."""

    async def record_event(self, event: BoardroomStreamEvent) -> None:
        """Persist the raw stream event."""

    async def record_turn(self, meeting_id: UUID, turn: MeetingTurn) -> None:
        """Persist a normalized timeline turn."""

    async def record_confidence(
        self,
        meeting_id: UUID,
        role: str,
        sequence: int,
        confidence: float,
        previous_confidence: float | None,
        reason: str,
    ) -> None:
        """Persist confidence history."""

    async def record_vote_event(
        self,
        meeting_id: UUID,
        vote: BoardVote,
        sequence: int,
        previous_vote: str | None,
        changed: bool,
    ) -> None:
        """Persist provisional and changed votes."""

    async def persist_report(self, meeting_id: UUID, report: BoardReport) -> None:
        """Persist final report and sections."""

    async def complete_meeting(
        self,
        meeting_id: UUID,
        consensus_reached: bool,
        aggregate_confidence: float,
        decision: str,
        final_votes: tuple[BoardVote, ...],
    ) -> None:
        """Persist the final decision and final vote snapshot."""


class NoopMeetingRecorder:
    async def start_meeting(
        self,
        meeting_id: UUID,
        brief: StartupBrief,
        assessment: StrategicAssessment,
    ) -> None:
        return None

    async def record_event(self, event: BoardroomStreamEvent) -> None:
        return None

    async def record_turn(self, meeting_id: UUID, turn: MeetingTurn) -> None:
        return None

    async def record_confidence(
        self,
        meeting_id: UUID,
        role: str,
        sequence: int,
        confidence: float,
        previous_confidence: float | None,
        reason: str,
    ) -> None:
        return None

    async def record_vote_event(
        self,
        meeting_id: UUID,
        vote: BoardVote,
        sequence: int,
        previous_vote: str | None,
        changed: bool,
    ) -> None:
        return None

    async def persist_report(self, meeting_id: UUID, report: BoardReport) -> None:
        return None

    async def complete_meeting(
        self,
        meeting_id: UUID,
        consensus_reached: bool,
        aggregate_confidence: float,
        decision: str,
        final_votes: tuple[BoardVote, ...],
    ) -> None:
        return None


class LiveBoardMeetingOrchestrator:
    def __init__(
        self,
        provider: ExecutiveIntelligenceProvider,
        delay_seconds: float = 0.15,
    ) -> None:
        self.provider = provider
        self.delay_seconds = delay_seconds

    async def stream(
        self,
        brief: StartupBrief,
        recorder: BoardMeetingRecorder | None = None,
        meeting_id: UUID | None = None,
    ) -> AsyncIterator[BoardroomStreamEvent]:
        active_recorder = recorder or NoopMeetingRecorder()
        active_meeting_id = meeting_id or uuid4()
        assessment = assess_brief(brief)
        sequence = 0
        memory = ExecutiveMemory()
        opinions: list[ExecutiveOpinion] = []
        turns: list[MeetingTurn] = []
        confidence_by_role: dict[str, float] = {}
        preliminary_votes: dict[str, BoardVote] = {}

        await active_recorder.start_meeting(active_meeting_id, brief, assessment)

        sequence += 1
        yield await self._emit(
            recorder=active_recorder,
            event=BoardroomStreamEvent(
                meeting_id=active_meeting_id,
                sequence=sequence,
                event_type="meeting_started",
                payload={
                    "assessment": {
                        "overall_risk": round(assessment.overall_risk, 3),
                        "risk_scores": {
                            key: round(value, 3) for key, value in assessment.risk_scores.items()
                        },
                        "signals": assessment.signals,
                    },
                    "executives": [profile.role for profile in EXECUTIVE_PROFILES],
                },
            ),
        )

        opening: ExecutiveOpinion | None = None
        for index, profile in enumerate(EXECUTIVE_PROFILES):
            await self._sleep()
            sequence += 1
            yield await self._emit(
                recorder=active_recorder,
                event=BoardroomStreamEvent(
                    meeting_id=active_meeting_id,
                    sequence=sequence,
                    event_type="executive_status",
                    role=profile.role,
                    payload={
                        "role": profile.role,
                        "status": "thinking",
                        "label": STATUS_BY_ROLE.get(profile.role, f"{profile.role} is thinking..."),
                    },
                ),
            )

            initial_confidence = self._initial_confidence(profile, assessment)
            confidence_by_role[profile.role] = initial_confidence
            sequence += 1
            yield await self._confidence_event(
                recorder=active_recorder,
                meeting_id=active_meeting_id,
                sequence=sequence,
                role=profile.role,
                confidence=initial_confidence,
                previous_confidence=None,
                reason=self._initial_confidence_reason(profile, assessment),
            )

            if index == 0:
                opinion = self.provider.propose_strategy(brief, assessment, profile)
                opening = opinion
                round_number = 1
                turn_type = "proposal"
            else:
                if opening is None:
                    raise RuntimeError("CEO opening thesis must exist before critiques")
                opinion = self.provider.critique_strategy(brief, assessment, profile, opening)
                opinion = memory.contextualize(opinion)
                round_number = 2
                turn_type = "critique"

            opinions.append(opinion)
            previous_confidence = confidence_by_role[profile.role]
            confidence_by_role[profile.role] = opinion.confidence
            sequence += 1
            yield await self._confidence_event(
                recorder=active_recorder,
                meeting_id=active_meeting_id,
                sequence=sequence,
                role=profile.role,
                confidence=opinion.confidence,
                previous_confidence=previous_confidence,
                reason=self._confidence_shift_reason(profile, opinion, previous_confidence, memory),
            )

            turn = MeetingTurn(
                sequence=sequence + 1,
                round_number=round_number,
                speaker_role=opinion.role,
                turn_type=turn_type,
                topic=self._topic_for(profile, assessment),
                stance=opinion.stance,
                confidence=opinion.confidence,
                message=opinion.message,
                concerns=opinion.concerns,
                recommendations=opinion.recommendations,
                reasoning=memory.reasoning_for(opinion),
                memory_references=memory.references_for(opinion.role),
                occurred_at=datetime.now(UTC).isoformat(),
            )
            memory.remember(turn)
            turns.append(turn)
            sequence += 1
            yield await self._timeline_event(active_recorder, active_meeting_id, sequence, turn)

            preliminary_vote = self._preliminary_vote(profile, opinion, assessment)
            preliminary_votes[profile.role] = preliminary_vote
            sequence += 1
            yield await self._vote_event(
                recorder=active_recorder,
                meeting_id=active_meeting_id,
                sequence=sequence,
                vote=preliminary_vote,
                previous_vote=None,
                changed=False,
                event_type="vote_cast",
            )

        critiques = tuple(opinion for opinion in opinions if opinion.role != "CEO")
        revision = self.provider.revise_strategy(brief, assessment, critiques)
        revision = memory.contextualize(revision)
        sequence += 1
        revision_turn = MeetingTurn(
            sequence=sequence,
            round_number=3,
            speaker_role=revision.role,
            turn_type="revision",
            topic="Consensus revision",
            stance=revision.stance,
            confidence=revision.confidence,
            message=revision.message,
            concerns=revision.concerns,
            recommendations=revision.recommendations,
            reasoning=memory.reasoning_for(revision),
            memory_references=memory.references_for(revision.role),
            occurred_at=datetime.now(UTC).isoformat(),
        )
        memory.remember(revision_turn)
        turns.append(revision_turn)
        yield await self._timeline_event(
            active_recorder,
            active_meeting_id,
            sequence,
            revision_turn,
        )

        mitigation_strength = self._mitigation_strength(revision, critiques)
        final_votes: list[BoardVote] = []
        for profile in EXECUTIVE_PROFILES:
            base_opinion = self._opinion_for(profile.role, tuple(opinions))
            final_vote = self.provider.vote(profile, base_opinion, assessment, mitigation_strength)
            final_votes.append(final_vote)
            previous_vote = preliminary_votes[profile.role].vote
            changed = previous_vote != final_vote.vote
            sequence += 1
            yield await self._vote_event(
                recorder=active_recorder,
                meeting_id=active_meeting_id,
                sequence=sequence,
                vote=final_vote,
                previous_vote=previous_vote,
                changed=changed,
                event_type="vote_changed" if changed else "vote_confirmed",
            )
            sequence += 1
            yield await self._confidence_event(
                recorder=active_recorder,
                meeting_id=active_meeting_id,
                sequence=sequence,
                role=profile.role,
                confidence=final_vote.confidence,
                previous_confidence=confidence_by_role[profile.role],
                reason=(
                    "Confidence updated after the CEO revision addressed board conditions."
                    if changed
                    else (
                        "Confidence held steady because the final plan matched "
                        "the role's conditions."
                    )
                ),
            )

        votes = tuple(final_votes)
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
        await active_recorder.persist_report(active_meeting_id, report)

        for section_key, content in report.sections.items():
            await self._sleep()
            sequence += 1
            yield await self._emit(
                recorder=active_recorder,
                event=BoardroomStreamEvent(
                    meeting_id=active_meeting_id,
                    sequence=sequence,
                    event_type="report_section",
                    payload={
                        "section_key": section_key,
                        "section_title": REPORT_SECTION_TITLES.get(section_key, section_key),
                        "content": content,
                    },
                ),
            )

        await active_recorder.complete_meeting(
            active_meeting_id,
            consensus_reached,
            aggregate_confidence,
            decision,
            votes,
        )
        result = BoardMeetingResult(
            meeting_id=active_meeting_id,
            consensus_reached=consensus_reached,
            aggregate_confidence=aggregate_confidence,
            decision=decision,
            assessment=assessment,
            turns=tuple(turns),
            votes=votes,
            report=report,
        )

        sequence += 1
        yield await self._emit(
            recorder=active_recorder,
            event=BoardroomStreamEvent(
                meeting_id=active_meeting_id,
                sequence=sequence,
                event_type="consensus_reached",
                payload={
                    "consensus_reached": consensus_reached,
                    "decision": decision,
                    "aggregate_confidence": round(aggregate_confidence, 3),
                    "result": result.to_dict(),
                },
            ),
        )

    async def _sleep(self) -> None:
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

    async def _emit(
        self,
        recorder: BoardMeetingRecorder,
        event: BoardroomStreamEvent,
    ) -> BoardroomStreamEvent:
        await recorder.record_event(event)
        return event

    async def _timeline_event(
        self,
        recorder: BoardMeetingRecorder,
        meeting_id: UUID,
        sequence: int,
        turn: MeetingTurn,
    ) -> BoardroomStreamEvent:
        await recorder.record_turn(meeting_id, turn)
        return await self._emit(
            recorder=recorder,
            event=BoardroomStreamEvent(
                meeting_id=meeting_id,
                sequence=sequence,
                event_type="timeline_statement",
                role=turn.speaker_role,
                payload=turn.to_dict(),
            ),
        )

    async def _confidence_event(
        self,
        recorder: BoardMeetingRecorder,
        meeting_id: UUID,
        sequence: int,
        role: str,
        confidence: float,
        previous_confidence: float | None,
        reason: str,
    ) -> BoardroomStreamEvent:
        await recorder.record_confidence(
            meeting_id,
            role,
            sequence,
            confidence,
            previous_confidence,
            reason,
        )
        delta = None if previous_confidence is None else confidence - previous_confidence
        return await self._emit(
            recorder=recorder,
            event=BoardroomStreamEvent(
                meeting_id=meeting_id,
                sequence=sequence,
                event_type="confidence_changed",
                role=role,
                payload={
                    "role": role,
                    "confidence": round(confidence, 3),
                    "previous_confidence": (
                        None if previous_confidence is None else round(previous_confidence, 3)
                    ),
                    "delta": None if delta is None else round(delta, 3),
                    "reason": reason,
                },
            ),
        )

    async def _vote_event(
        self,
        recorder: BoardMeetingRecorder,
        meeting_id: UUID,
        sequence: int,
        vote: BoardVote,
        previous_vote: str | None,
        changed: bool,
        event_type: str,
    ) -> BoardroomStreamEvent:
        await recorder.record_vote_event(meeting_id, vote, sequence, previous_vote, changed)
        return await self._emit(
            recorder=recorder,
            event=BoardroomStreamEvent(
                meeting_id=meeting_id,
                sequence=sequence,
                event_type=event_type,
                role=vote.role,
                payload={
                    **vote.to_dict(),
                    "previous_vote": previous_vote,
                    "changed": changed,
                },
            ),
        )

    def _initial_confidence(
        self,
        profile: ExecutiveProfile,
        assessment: StrategicAssessment,
    ) -> float:
        focused_risk = max(
            (assessment.risk_scores[risk] for risk in profile.risk_focus),
            default=assessment.overall_risk,
        )
        return clamp(0.72 - focused_risk * 0.18 + profile.optimism_bias, 0.38, 0.86)

    def _initial_confidence_reason(
        self,
        profile: ExecutiveProfile,
        assessment: StrategicAssessment,
    ) -> str:
        highest = max(profile.risk_focus, key=lambda risk: assessment.risk_scores[risk])
        return (
            f"Initial confidence reflects {highest.replace('_', ' ')} risk in this role's charter."
        )

    def _confidence_shift_reason(
        self,
        profile: ExecutiveProfile,
        opinion: ExecutiveOpinion,
        previous_confidence: float,
        memory: ExecutiveMemory,
    ) -> str:
        direction = "increased" if opinion.confidence >= previous_confidence else "decreased"
        references = memory.references_for(profile.role)
        if references:
            return (
                f"Confidence {direction} after considering {', '.join(references)} "
                f"and the role's concern: {opinion.concerns[0]}."
            )
        return f"Confidence {direction} after the opening strategic assessment."

    def _topic_for(
        self,
        profile: ExecutiveProfile,
        assessment: StrategicAssessment,
    ) -> str:
        highest = max(profile.risk_focus, key=lambda risk: assessment.risk_scores[risk])
        return highest.replace("_", " ").title()

    def _preliminary_vote(
        self,
        profile: ExecutiveProfile,
        opinion: ExecutiveOpinion,
        assessment: StrategicAssessment,
    ) -> BoardVote:
        focused_risk = max(
            (assessment.risk_scores[risk] for risk in profile.risk_focus),
            default=assessment.overall_risk,
        )
        if opinion.confidence < 0.5:
            vote = "abstain"
            rationale = f"{profile.role} abstains until the board hears more evidence."
        elif focused_risk >= profile.veto_threshold:
            vote = "reject"
            rationale = f"{profile.role} rejects the initial plan until its risk is reduced."
        elif focused_risk >= profile.veto_threshold - 0.16:
            vote = "approve_with_conditions"
            rationale = f"{profile.role} needs strict conditions before approval."
        else:
            vote = "approve"
            rationale = f"{profile.role} provisionally approves the direction."
        return BoardVote(
            role=profile.role,
            vote=vote,
            confidence=opinion.confidence,
            rationale=rationale,
        )

    def _opinion_for(
        self,
        role: str,
        opinions: tuple[ExecutiveOpinion, ...],
    ) -> ExecutiveOpinion:
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
