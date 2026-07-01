from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import String, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.boardroom.models import (
    BoardMeetingResult,
    BoardReport,
    BoardVote,
    MeetingTurn,
    StartupBrief,
    StrategicAssessment,
)
from app.domain.boardroom.roles import EXECUTIVE_PROFILES
from app.domain.boardroom.streaming import REPORT_SECTION_TITLES, BoardroomStreamEvent
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
                    section_title=REPORT_SECTION_TITLES.get(
                        section_key,
                        section_key.replace("_", " ").title(),
                    ),
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

    async def persist_completed_result(
        self,
        brief: StartupBrief,
        result: BoardMeetingResult,
    ) -> None:
        await self.start_meeting(result.meeting_id, brief, result.assessment)
        for turn in result.turns:
            await self.record_turn(result.meeting_id, turn)
        await self.persist_report(result.meeting_id, result.report)
        await self.complete_meeting(
            result.meeting_id,
            result.consensus_reached,
            result.aggregate_confidence,
            result.decision,
            result.votes,
        )

    async def list_meetings(
        self,
        query: str | None = None,
        limit: int = 30,
        favorite_only: bool = False,
    ) -> list[dict[str, object]]:
        stmt = (
            select(BoardMeetingRecord)
            .join(BoardMeetingRecord.startup_brief)
            .options(
                selectinload(BoardMeetingRecord.startup_brief),
                selectinload(BoardMeetingRecord.reports),
            )
            .order_by(BoardMeetingRecord.created_at.desc())
            .limit(limit)
        )
        if favorite_only:
            stmt = stmt.where(BoardMeetingRecord.is_favorite.is_(True))
        if query:
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    StartupBriefRecord.startup_idea.ilike(pattern),
                    StartupBriefRecord.industry.ilike(pattern),
                    StartupBriefRecord.country.ilike(pattern),
                    StartupBriefRecord.business_model.ilike(pattern),
                    StartupBriefRecord.funding_stage.ilike(pattern),
                    BoardMeetingRecord.decision.ilike(pattern),
                )
            )
        records = (await self.session.scalars(stmt)).unique().all()
        return [self._meeting_summary(record) for record in records]

    async def dashboard_snapshot(self) -> dict[str, object]:
        summaries = await self.list_meetings(limit=100)
        completed = [summary for summary in summaries if summary["status"] == "completed"]
        approved = [
            summary
            for summary in completed
            if str(summary["decision"]) in {"approve", "approve_with_conditions"}
        ]
        average_confidence = (
            sum(float(summary["aggregate_confidence"]) for summary in completed) / len(completed)
            if completed
            else 0.0
        )
        industry_counts: dict[str, int] = {}
        for summary in summaries:
            industry = str(summary["industry"])
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        top_industries = [
            {"industry": industry, "count": count}
            for industry, count in sorted(
                industry_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:6]
        ]
        reports = [summary for summary in summaries if summary.get("report_title")]
        return {
            "total_meetings": len(summaries),
            "reports_generated": len(reports),
            "approval_rate": round(len(approved) / len(completed), 3) if completed else 0.0,
            "average_confidence": round(average_confidence, 3),
            "top_industries": top_industries,
            "recent_meetings": summaries[:8],
            "recent_reports": reports[:8],
            "recent_board_decisions": completed[:8],
        }

    async def get_meeting_detail(self, meeting_id: UUID) -> dict[str, object] | None:
        stmt = (
            select(BoardMeetingRecord)
            .where(BoardMeetingRecord.id == meeting_id)
            .options(
                selectinload(BoardMeetingRecord.startup_brief),
                selectinload(BoardMeetingRecord.turns),
                selectinload(BoardMeetingRecord.votes),
                selectinload(BoardMeetingRecord.reports).selectinload(FinalReportRecord.sections),
            )
        )
        record = await self.session.scalar(stmt)
        if record is None:
            return None
        return self._meeting_detail(record)

    async def set_favorite(self, meeting_id: UUID, is_favorite: bool) -> dict[str, object] | None:
        record = await self.session.get(BoardMeetingRecord, meeting_id)
        if record is None:
            return None
        record.is_favorite = is_favorite
        await self.session.commit()
        return {"meeting_id": str(record.id), "is_favorite": record.is_favorite}

    async def delete_meeting(self, meeting_id: UUID) -> bool:
        record = await self.session.get(BoardMeetingRecord, meeting_id)
        if record is None:
            return False
        await self.session.delete(record)
        await self.session.commit()
        return True

    async def global_search(self, query: str, limit: int = 10) -> dict[str, object]:
        pattern = f"%{query.strip()}%"
        meetings = await self.list_meetings(query=query, limit=limit)
        report_stmt = (
            select(FinalReportRecord, ReportSectionRecord, BoardMeetingRecord, StartupBriefRecord)
            .join(FinalReportRecord.board_meeting)
            .join(BoardMeetingRecord.startup_brief)
            .join(FinalReportRecord.sections)
            .where(
                or_(
                    FinalReportRecord.title.ilike(pattern),
                    FinalReportRecord.decision.ilike(pattern),
                    ReportSectionRecord.section_key.ilike(pattern),
                    ReportSectionRecord.section_title.ilike(pattern),
                    cast(ReportSectionRecord.content, String).ilike(pattern),
                )
            )
            .order_by(FinalReportRecord.created_at.desc(), ReportSectionRecord.position.asc())
            .limit(limit)
        )
        rows = (await self.session.execute(report_stmt)).all()
        reports = [
            {
                "meeting_id": str(meeting.id),
                "report_id": str(report.id),
                "title": report.title,
                "section_key": section.section_key,
                "section_title": section.section_title,
                "startup_idea": brief.startup_idea,
                "decision": report.decision,
            }
            for report, section, meeting, brief in rows
        ]
        executives = [
            {
                "role": profile.role,
                "charter": profile.charter,
                "personality": profile.personality,
                "goals": list(profile.goals),
                "risk_focus": list(profile.risk_focus),
            }
            for profile in EXECUTIVE_PROFILES
            if query.lower() in profile.role.lower()
            or query.lower() in profile.charter.lower()
            or query.lower() in profile.personality.lower()
        ][:limit]
        return {"query": query, "meetings": meetings, "reports": reports, "executives": executives}

    async def _update_phase(self, meeting_id: UUID, event_type: str) -> None:
        meeting = await self.session.get(BoardMeetingRecord, meeting_id)
        if meeting is not None:
            meeting.current_phase = event_type

    def _meeting_summary(self, record: BoardMeetingRecord) -> dict[str, object]:
        latest_report = self._latest_report(record)
        return {
            "meeting_id": str(record.id),
            "startup_idea": record.startup_brief.startup_idea,
            "industry": record.startup_brief.industry,
            "country": record.startup_brief.country,
            "decision": record.decision,
            "status": record.status,
            "aggregate_confidence": float(record.aggregate_confidence),
            "consensus_reached": record.consensus_reached,
            "is_favorite": record.is_favorite,
            "created_at": _iso(record.created_at),
            "completed_at": _iso(record.completed_at),
            "report_title": latest_report.title if latest_report else None,
        }

    def _meeting_detail(self, record: BoardMeetingRecord) -> dict[str, object]:
        report = self._latest_report(record)
        sections = {}
        if report is not None:
            for section in sorted(report.sections, key=lambda item: item.position):
                sections[section.section_key] = section.content
        return {
            "meeting_id": str(record.id),
            "consensus_reached": record.consensus_reached,
            "aggregate_confidence": float(record.aggregate_confidence),
            "decision": record.decision,
            "assessment": record.assessment or {},
            "turns": [
                self._turn_dict(turn)
                for turn in sorted(
                    record.turns,
                    key=lambda item: item.sequence if item.sequence is not None else 10_000,
                )
            ],
            "votes": [self._vote_dict(vote) for vote in record.votes],
            "report": {
                "title": (
                    report.title
                    if report
                    else f"Board Report: {record.startup_brief.startup_idea}"
                ),
                "decision": report.decision if report else record.decision,
                "sections": sections,
            },
            "startup_brief": self._brief_dict(record.startup_brief),
            "status": record.status,
            "is_favorite": record.is_favorite,
            "created_at": _iso(record.created_at),
            "completed_at": _iso(record.completed_at),
        }

    def _latest_report(self, record: BoardMeetingRecord) -> FinalReportRecord | None:
        if not record.reports:
            return None
        return sorted(record.reports, key=lambda report: report.created_at, reverse=True)[0]

    def _brief_dict(self, record: StartupBriefRecord) -> dict[str, object]:
        return {
            "startup_idea": record.startup_idea,
            "industry": record.industry,
            "country": record.country,
            "budget": float(record.budget),
            "timeline_months": record.timeline_months,
            "competitors": record.competitors,
            "target_audience": record.target_audience,
            "funding_stage": record.funding_stage,
            "business_model": record.business_model,
        }

    def _turn_dict(self, record: MeetingTurnRecord) -> dict[str, object]:
        return {
            "sequence": record.sequence,
            "round_number": record.round_number,
            "speaker_role": record.speaker_role,
            "turn_type": record.turn_type,
            "topic": record.topic,
            "stance": record.stance,
            "confidence": float(record.confidence),
            "message": record.message,
            "concerns": record.concerns,
            "recommendations": record.recommendations,
            "reasoning": record.reasoning or [],
            "memory_references": record.memory_references or [],
            "occurred_at": _iso(record.created_at),
        }

    def _vote_dict(self, record: BoardVoteRecord) -> dict[str, object]:
        return {
            "role": record.role,
            "vote": record.vote,
            "confidence": float(record.confidence),
            "rationale": record.rationale,
        }


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
