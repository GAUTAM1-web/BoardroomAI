from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.boardroom.models import (
    BoardReport,
    BoardVote,
    MeetingTurn,
    StartupBrief,
    StrategicAssessment,
)
from app.domain.boardroom.roles import EXECUTIVE_PROFILES
from app.domain.boardroom.streaming import BoardroomStreamEvent
from app.infrastructure.database.models import (
    BoardMeetingRecord,
    BoardVoteRecord,
    ConfidenceEventRecord,
    ExecutiveAgentRecord,
    FinalReportRecord,
    MeetingEventRecord,
    MeetingTurnRecord,
    ReportSectionRecord,
    StartupBriefRecord,
    VoteEventRecord,
)


class PostgresMeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start_meeting(
        self,
        meeting_id: UUID,
        brief: StartupBrief,
        assessment: StrategicAssessment,
    ) -> None:
        startup_brief = StartupBriefRecord(
            id=uuid4(),
            startup_idea=brief.startup_idea,
            industry=brief.industry,
            country=brief.country,
            budget=Decimal(str(brief.budget)),
            timeline_months=brief.timeline_months,
            competitors=list(brief.competitors),
            target_audience=brief.target_audience,
            funding_stage=brief.funding_stage,
            business_model=brief.business_model,
        )
        meeting = BoardMeetingRecord(
            id=meeting_id,
            startup_brief_id=startup_brief.id,
            status="streaming",
            consensus_reached=False,
            aggregate_confidence=Decimal("0"),
            decision="in_progress",
            current_phase="meeting_started",
            assessment={
                "overall_risk": round(assessment.overall_risk, 3),
                "risk_scores": {
                    key: round(value, 3) for key, value in assessment.risk_scores.items()
                },
                "signals": assessment.signals,
            },
        )
        self.session.add(startup_brief)
        self.session.add(meeting)
        for profile in EXECUTIVE_PROFILES:
            self.session.add(
                ExecutiveAgentRecord(
                    board_meeting_id=meeting_id,
                    role=profile.role,
                    charter=profile.charter,
                    personality=profile.personality,
                    goals=list(profile.goals),
                    risk_focus=list(profile.risk_focus),
                )
            )
        await self.session.commit()

    async def record_event(self, event: BoardroomStreamEvent) -> None:
        self.session.add(
            MeetingEventRecord(
                id=event.event_id,
                board_meeting_id=event.meeting_id,
                sequence=event.sequence,
                event_type=event.event_type,
                role=event.role,
                payload=event.payload,
                created_at=event.timestamp,
            )
        )
        await self._update_phase(event.meeting_id, event.event_type)
        await self.session.commit()

    async def record_turn(self, meeting_id: UUID, turn: MeetingTurn) -> None:
        self.session.add(
            MeetingTurnRecord(
                board_meeting_id=meeting_id,
                sequence=turn.sequence,
                round_number=turn.round_number,
                speaker_role=turn.speaker_role,
                turn_type=turn.turn_type,
                topic=turn.topic,
                stance=turn.stance,
                confidence=Decimal(str(round(turn.confidence, 4))),
                message=turn.message,
                concerns=list(turn.concerns),
                recommendations=list(turn.recommendations),
                reasoning=list(turn.reasoning),
                memory_references=list(turn.memory_references),
            )
        )
        await self.session.commit()

    async def record_confidence(
        self,
        meeting_id: UUID,
        role: str,
        sequence: int,
        confidence: float,
        previous_confidence: float | None,
        reason: str,
    ) -> None:
        delta = None if previous_confidence is None else confidence - previous_confidence
        self.session.add(
            ConfidenceEventRecord(
                board_meeting_id=meeting_id,
                sequence=sequence,
                role=role,
                confidence=Decimal(str(round(confidence, 4))),
                previous_confidence=(
                    None
                    if previous_confidence is None
                    else Decimal(str(round(previous_confidence, 4)))
                ),
                delta=None if delta is None else Decimal(str(round(delta, 4))),
                reason=reason,
            )
        )
        await self.session.commit()

    async def record_vote_event(
        self,
        meeting_id: UUID,
        vote: BoardVote,
        sequence: int,
        previous_vote: str | None,
        changed: bool,
    ) -> None:
        self.session.add(
            VoteEventRecord(
                board_meeting_id=meeting_id,
                sequence=sequence,
                role=vote.role,
                previous_vote=previous_vote,
                vote=vote.vote,
                changed=changed,
                confidence=Decimal(str(round(vote.confidence, 4))),
                rationale=vote.rationale,
            )
        )
        await self.session.commit()

    async def persist_report(self, meeting_id: UUID, report: BoardReport) -> None:
        existing_report = await self.session.scalar(
            select(FinalReportRecord).where(FinalReportRecord.board_meeting_id == meeting_id)
        )
        if existing_report is not None:
            return

        report_record = FinalReportRecord(
            board_meeting_id=meeting_id,
            title=report.title,
            decision=report.decision,
        )
        self.session.add(report_record)
        await self.session.flush()
        for position, (section_key, content) in enumerate(report.sections.items(), start=1):
            self.session.add(
                ReportSectionRecord(
                    final_report_id=report_record.id,
                    section_key=section_key,
                    section_title=section_key.replace("_", " ").title(),
                    content=content,
                    position=position,
                )
            )
        await self.session.commit()

    async def complete_meeting(
        self,
        meeting_id: UUID,
        consensus_reached: bool,
        aggregate_confidence: float,
        decision: str,
        final_votes: tuple[BoardVote, ...],
    ) -> None:
        meeting = await self.session.get(BoardMeetingRecord, meeting_id)
        if meeting is not None:
            meeting.status = "completed"
            meeting.consensus_reached = consensus_reached
            meeting.aggregate_confidence = Decimal(str(round(aggregate_confidence, 4)))
            meeting.decision = decision
            meeting.current_phase = "completed"
            meeting.completed_at = datetime.now(UTC)

        for vote in final_votes:
            self.session.add(
                BoardVoteRecord(
                    board_meeting_id=meeting_id,
                    role=vote.role,
                    vote=vote.vote,
                    confidence=Decimal(str(round(vote.confidence, 4))),
                    rationale=vote.rationale,
                )
            )
        await self.session.commit()

    async def _update_phase(self, meeting_id: UUID, event_type: str) -> None:
        meeting = await self.session.get(BoardMeetingRecord, meeting_id)
        if meeting is not None:
            meeting.current_phase = event_type
