from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.domain.boardroom.models import (
    BoardMeetingResult,
    BoardReport,
    BoardVote,
    MeetingTurn,
    StartupBrief,
    StrategicAssessment,
)
from app.domain.boardroom.roles import EXECUTIVE_PROFILES, select_executive_profiles
from app.domain.boardroom.streaming import REPORT_SECTION_TITLES, BoardroomStreamEvent
from app.domain.business_intelligence.service import build_business_analysis
from app.domain.enterprise.document_intelligence import analyze_document_import
from app.domain.enterprise.saas_intelligence import (
    build_assistant_answer,
    build_workflow_catalog,
)
from app.domain.enterprise.security import ENTERPRISE_PERMISSIONS
from app.infrastructure.database.models import (
    ApprovalStepRecord,
    ApprovalWorkflowRecord,
    AuditEventRecord,
    BoardMeetingRecord,
    BoardVoteRecord,
    BusinessAnalysisRecord,
    BusinessEvidenceRecord,
    BusinessPerformanceEntryRecord,
    BusinessValidationTaskRecord,
    CalendarEventRecord,
    ConfidenceEventRecord,
    EnterpriseDepartmentRecord,
    EnterpriseMembershipRecord,
    EnterpriseNotificationRecord,
    EnterpriseOrganizationRecord,
    EnterpriseTaskRecord,
    EnterpriseTeamRecord,
    EnterpriseUserRecord,
    ExecutiveAgentRecord,
    FinalReportRecord,
    KnowledgeItemRecord,
    MeetingCollaboratorRecord,
    MeetingEventRecord,
    MeetingTurnRecord,
    ReportCommentRecord,
    ReportSectionRecord,
    ReportTemplateRecord,
    SavedSupplierRecord,
    StartupBriefRecord,
    VoteEventRecord,
)
from app.schemas.business import BusinessAnalysisRequest

DEFAULT_ORGANIZATION_SLUG = "default"
DEFAULT_USER_EMAIL = "owner@boardroom.local"
PORTFOLIO_DEMO_STARTUP_IDEA = "Portfolio Demo: Neighborhood Health Ops Copilot"
PORTFOLIO_DEMO_BUSINESS_IDEA = "Portfolio Demo: High-street healthy quick-service restaurant"

DEFAULT_REPORT_TEMPLATES = (
    ("Restaurant", "restaurant"),
    ("Retail", "retail"),
    ("Manufacturing", "manufacturing"),
    ("Healthcare", "healthcare"),
    ("Technology", "technology"),
    ("Franchise", "franchise"),
    ("Export", "export"),
)


class PostgresMeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_default_workspace(self) -> dict[str, UUID]:
        organization = await self.session.scalar(
            select(EnterpriseOrganizationRecord).where(
                EnterpriseOrganizationRecord.slug == DEFAULT_ORGANIZATION_SLUG
            )
        )
        if organization is None:
            organization = EnterpriseOrganizationRecord(
                id=uuid4(),
                name="Default Organization",
                slug=DEFAULT_ORGANIZATION_SLUG,
                status="active",
                default_locale="en",
            )
            self.session.add(organization)
            await self.session.flush()

            departments: dict[str, EnterpriseDepartmentRecord] = {}
            for name in ("Marketing", "Finance", "HR", "Operations", "Product"):
                department = EnterpriseDepartmentRecord(
                    organization_id=organization.id,
                    name=name,
                )
                self.session.add(department)
                departments[name] = department
            await self.session.flush()

            for name, department_name in (
                ("Executive Team", "Operations"),
                ("Finance Review", "Finance"),
                ("Product Council", "Product"),
                ("Marketing Strategy", "Marketing"),
                ("People Operations", "HR"),
            ):
                self.session.add(
                    EnterpriseTeamRecord(
                        organization_id=organization.id,
                        department_id=departments[department_name].id,
                        name=name,
                    )
                )

        user = await self.session.scalar(
            select(EnterpriseUserRecord).where(EnterpriseUserRecord.email == DEFAULT_USER_EMAIL)
        )
        if user is None:
            user = EnterpriseUserRecord(
                id=uuid4(),
                display_name="Workspace Owner",
                email=DEFAULT_USER_EMAIL,
                locale="en",
                status="active",
            )
            self.session.add(user)
            await self.session.flush()

        membership = await self.session.scalar(
            select(EnterpriseMembershipRecord).where(
                EnterpriseMembershipRecord.organization_id == organization.id,
                EnterpriseMembershipRecord.user_id == user.id,
            )
        )
        if membership is None:
            self.session.add(
                EnterpriseMembershipRecord(
                    organization_id=organization.id,
                    user_id=user.id,
                    role="Administrator",
                    permissions=sorted(ENTERPRISE_PERMISSIONS["administrator"]),
                )
            )

        await self._ensure_default_templates(organization.id)
        await self._ensure_default_knowledge(organization.id)
        await self._ensure_default_calendar(organization.id)
        if get_settings().demo_content_enabled:
            await self._ensure_portfolio_demo_content(organization.id, user.id)
        await self.session.commit()
        return {"organization_id": organization.id, "user_id": user.id}

    async def start_meeting(
        self,
        meeting_id: UUID,
        brief: StartupBrief,
        assessment: StrategicAssessment,
    ) -> None:
        workspace = await self.ensure_default_workspace()
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
            meeting_mode=brief.normalized_meeting_mode,
        )
        meeting = BoardMeetingRecord(
            id=meeting_id,
            organization_id=workspace["organization_id"],
            created_by_user_id=workspace["user_id"],
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
        self._add_audit_event(
            workspace["organization_id"],
            workspace["user_id"],
            "board_meeting.started",
            "board_meeting",
            meeting_id,
            {"startup_idea": brief.startup_idea, "meeting_mode": brief.normalized_meeting_mode},
        )
        for profile in select_executive_profiles(brief):
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
        meeting = await self.session.get(BoardMeetingRecord, meeting_id)

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
        if meeting is not None and meeting.organization_id is not None:
            self.session.add(
                KnowledgeItemRecord(
                    organization_id=meeting.organization_id,
                    title=report.title,
                    item_type="report",
                    source_type="board_meeting",
                    source_id=meeting_id,
                    content=str(report.sections.get("executive_summary", {}))[:4000],
                    tags=["report", report.decision, "boardroom"],
                )
            )
            self._add_audit_event(
                meeting.organization_id,
                meeting.created_by_user_id,
                "report.generated",
                "board_meeting",
                meeting_id,
                {"title": report.title, "decision": report.decision},
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
            self._add_audit_event(
                meeting.organization_id,
                meeting.created_by_user_id,
                "board_meeting.completed",
                "board_meeting",
                meeting_id,
                {
                    "decision": decision,
                    "aggregate_confidence": round(aggregate_confidence, 4),
                },
            )
            if meeting.organization_id is not None:
                self.session.add(
                    EnterpriseNotificationRecord(
                        organization_id=meeting.organization_id,
                        user_id=meeting.created_by_user_id,
                        channel="in_app",
                        title="Board meeting completed",
                        body=f"Decision: {decision.replace('_', ' ')}",
                        status="unread",
                    )
                )

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

    async def persist_business_analysis(
        self,
        request_payload: dict[str, object],
        result: dict[str, object],
    ) -> None:
        workspace = await self.ensure_default_workspace()
        await self._add_business_analysis_records(
            workspace["organization_id"],
            workspace["user_id"],
            request_payload,
            result,
        )
        await self.session.commit()

    async def _add_business_analysis_records(
        self,
        organization_id: UUID,
        user_id: UUID,
        request_payload: dict[str, object],
        result: dict[str, object],
    ) -> UUID:
        analysis_id = UUID(str(result["analysis_id"]))
        intake = result["intake"]
        recommendation = result["recommendation"]
        opportunity_score = result["opportunity_score"]
        record = BusinessAnalysisRecord(
            id=analysis_id,
            organization_id=organization_id,
            created_by_user_id=user_id,
            workflow_type=str(intake["workflow_type"]),
            business_idea=str(intake["business_idea"]),
            business_category=str(intake["business_category"]),
            location_label=str(intake["location_label"]),
            budget=(Decimal(str(intake["budget"])) if intake.get("budget") is not None else None),
            data_mode=str(result["data_mode"]),
            provider_label=str(result["provider_label"]),
            recommendation_label=str(recommendation["label"]),
            opportunity_score=int(opportunity_score["score"]),
            evidence_confidence=str(result["evidence_confidence"]),
            request_payload=request_payload,
            result=result,
        )
        self.session.add(record)
        self._add_audit_event(
            organization_id,
            user_id,
            "business_analysis.created",
            "business_analysis",
            analysis_id,
            {"business_idea": str(intake["business_idea"]), "data_mode": str(result["data_mode"])},
        )

        for evidence in result.get("evidence", []):
            if not isinstance(evidence, dict):
                continue
            self.session.add(
                BusinessEvidenceRecord(
                    id=UUID(str(evidence["id"])),
                    analysis_id=analysis_id,
                    claim=str(evidence["claim"]),
                    source_name=str(evidence["source_name"]),
                    source_url=(
                        str(evidence["source_url"])
                        if evidence.get("source_url") is not None
                        else None
                    ),
                    source_type=str(evidence["source_type"]),
                    retrieval_time=_parse_datetime(str(evidence["retrieval_time"])),
                    location=evidence.get("location"),
                    value=evidence.get("value"),
                    confidence=str(evidence["confidence"]),
                    verification_status=str(evidence["verification_status"]),
                    freshness=str(evidence["freshness"]),
                    notes=str(evidence["notes"]) if evidence.get("notes") is not None else None,
                    tags=list(evidence.get("tags") or []),
                )
            )

        for supplier in result.get("suppliers", []):
            if not isinstance(supplier, dict):
                continue
            self.session.add(
                SavedSupplierRecord(
                    analysis_id=analysis_id,
                    name=str(supplier["name"]),
                    category=(
                        str(supplier["category"]) if supplier.get("category") is not None else None
                    ),
                    location_label=(
                        str(supplier["location"]) if supplier.get("location") is not None else None
                    ),
                    distance_km=(
                        Decimal(str(supplier["distance_km"]))
                        if supplier.get("distance_km") is not None
                        else None
                    ),
                    verification_status=str(supplier["verification_status"]),
                    contact_status=(
                        str(supplier["contact_status"])
                        if supplier.get("contact_status") is not None
                        else None
                    ),
                    is_preferred=bool(supplier.get("is_preferred", False)),
                    supplier_data=supplier,
                )
            )

        for task in result.get("validation_plan", []):
            if not isinstance(task, dict):
                continue
            self.session.add(
                BusinessValidationTaskRecord(
                    analysis_id=analysis_id,
                    task=str(task["task"]),
                    owner=str(task["owner"]) if task.get("owner") is not None else None,
                    due_date=str(task["due_date"]) if task.get("due_date") is not None else None,
                    cost=str(task["cost"]) if task.get("cost") is not None else None,
                    expected_evidence=(
                        str(task["expected_evidence"])
                        if task.get("expected_evidence") is not None
                        else None
                    ),
                    result=str(task["result"]) if task.get("result") is not None else None,
                    outcome=str(task["outcome"]) if task.get("outcome") is not None else None,
                    effect_on_confidence=(
                        str(task["effect_on_confidence"])
                        if task.get("effect_on_confidence") is not None
                        else None
                    ),
                    status="open",
                )
            )
        return analysis_id

    async def list_business_analyses(self, limit: int = 30) -> list[dict[str, object]]:
        stmt = (
            select(BusinessAnalysisRecord)
            .order_by(BusinessAnalysisRecord.created_at.desc())
            .limit(limit)
        )
        records = (await self.session.scalars(stmt)).all()
        return [self._business_analysis_summary(record) for record in records]

    async def get_business_analysis(self, analysis_id: UUID) -> dict[str, object] | None:
        record = await self.session.scalar(
            select(BusinessAnalysisRecord)
            .where(BusinessAnalysisRecord.id == analysis_id)
            .options(selectinload(BusinessAnalysisRecord.performance_entries))
        )
        if record is None:
            return None
        return {
            **record.result,
            "created_at": _iso(record.created_at),
            "performance_entries": [
                self._performance_entry_dict(entry)
                for entry in sorted(record.performance_entries, key=lambda item: item.created_at)
            ],
        }

    async def record_business_performance_entry(
        self,
        analysis_id: UUID,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        analysis = await self.session.get(BusinessAnalysisRecord, analysis_id)
        if analysis is None:
            return None
        entry = BusinessPerformanceEntryRecord(
            analysis_id=analysis_id,
            period_label=str(payload["period_label"]),
            revenue=(
                Decimal(str(payload["revenue"])) if payload.get("revenue") is not None else None
            ),
            expenses=(
                Decimal(str(payload["expenses"])) if payload.get("expenses") is not None else None
            ),
            customers=(int(payload["customers"]) if payload.get("customers") is not None else None),
            transactions=(
                int(payload["transactions"]) if payload.get("transactions") is not None else None
            ),
            performance_data=payload,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return self._performance_entry_dict(entry)

    async def list_business_performance_entries(
        self,
        analysis_id: UUID,
    ) -> list[dict[str, object]] | None:
        analysis = await self.session.get(BusinessAnalysisRecord, analysis_id)
        if analysis is None:
            return None
        records = (
            await self.session.scalars(
                select(BusinessPerformanceEntryRecord)
                .where(BusinessPerformanceEntryRecord.analysis_id == analysis_id)
                .order_by(BusinessPerformanceEntryRecord.created_at.asc())
            )
        ).all()
        return [self._performance_entry_dict(record) for record in records]

    async def list_organizations(self) -> list[dict[str, object]]:
        await self.ensure_default_workspace()
        records = (
            await self.session.scalars(
                select(EnterpriseOrganizationRecord).order_by(
                    EnterpriseOrganizationRecord.created_at.desc()
                )
            )
        ).all()
        return [await self._organization_dict(record) for record in records]

    async def create_organization(self, payload: dict[str, object]) -> dict[str, object]:
        await self.ensure_default_workspace()
        name = str(payload["name"]).strip()
        slug = await self._unique_organization_slug(str(payload.get("slug") or name))
        organization = EnterpriseOrganizationRecord(
            id=uuid4(),
            name=name,
            slug=slug,
            status="active",
            default_locale=str(payload.get("default_locale") or "en"),
        )
        self.session.add(organization)
        await self.session.flush()

        departments: dict[str, EnterpriseDepartmentRecord] = {}
        for department_name in ("Marketing", "Finance", "HR", "Operations", "Product"):
            department = EnterpriseDepartmentRecord(
                organization_id=organization.id,
                name=department_name,
            )
            self.session.add(department)
            departments[department_name] = department
        await self.session.flush()

        for team_name, department_name in (
            ("Executive Team", "Operations"),
            ("Finance Review", "Finance"),
            ("Product Council", "Product"),
            ("Marketing Strategy", "Marketing"),
            ("People Operations", "HR"),
        ):
            self.session.add(
                EnterpriseTeamRecord(
                    organization_id=organization.id,
                    department_id=departments[department_name].id,
                    name=team_name,
                )
            )

        await self._ensure_default_templates(organization.id)
        await self._ensure_default_knowledge(organization.id)
        await self._ensure_default_calendar(organization.id)
        self._add_audit_event(
            organization.id,
            None,
            "organization.created",
            "organization",
            organization.id,
            {"name": organization.name, "slug": organization.slug},
        )
        await self.session.commit()
        return await self._organization_dict(organization)

    async def enterprise_dashboard(self) -> dict[str, object]:
        organization, user = await self._default_workspace_records()
        analytics = await self.enterprise_analytics()
        departments = (
            await self.session.scalars(
                select(EnterpriseDepartmentRecord)
                .where(EnterpriseDepartmentRecord.organization_id == organization.id)
                .order_by(EnterpriseDepartmentRecord.name.asc())
            )
        ).all()
        teams = (
            await self.session.scalars(
                select(EnterpriseTeamRecord)
                .where(EnterpriseTeamRecord.organization_id == organization.id)
                .order_by(EnterpriseTeamRecord.name.asc())
            )
        ).all()
        users = await self._workspace_users(organization.id)
        pending_approvals = await self._approval_workflows(status="pending", limit=8)
        tasks = await self.list_tasks(status=None, limit=8)
        board_activity = await self.audit_log(limit=12)
        upcoming_reviews = await self.list_calendar_events(limit=8)
        return {
            "organization": await self._organization_dict(organization),
            "departments": [self._department_dict(record) for record in departments],
            "teams": [self._team_dict(record) for record in teams],
            "users": users,
            "recent_meetings": await self.list_meetings(limit=8),
            "pending_approvals": pending_approvals,
            "tasks": tasks,
            "board_activity": board_activity,
            "upcoming_reviews": upcoming_reviews,
            "analytics": analytics["analytics"],
            "executive_dashboard": analytics["executive_dashboard"],
            "current_user": self._user_dict(user),
        }

    async def enterprise_analytics(self) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        meeting_records = (
            await self.session.scalars(
                select(BoardMeetingRecord)
                .where(BoardMeetingRecord.organization_id == organization_id)
                .order_by(BoardMeetingRecord.created_at.desc())
                .limit(100)
            )
        ).all()
        if not meeting_records:
            meeting_records = (
                await self.session.scalars(
                    select(BoardMeetingRecord)
                    .order_by(BoardMeetingRecord.created_at.desc())
                    .limit(100)
                )
            ).all()

        completed = [record for record in meeting_records if record.status == "completed"]
        decision_counts: dict[str, int] = {}
        for record in completed:
            decision_counts[record.decision] = decision_counts.get(record.decision, 0) + 1
        approved = sum(
            count
            for decision, count in decision_counts.items()
            if decision in {"approve", "approve_with_conditions"}
        )

        approval_records = (
            await self.session.scalars(
                select(ApprovalWorkflowRecord)
                .where(ApprovalWorkflowRecord.organization_id == organization_id)
                .order_by(ApprovalWorkflowRecord.created_at.desc())
                .limit(100)
            )
        ).all()
        completed_approvals = [
            approval
            for approval in approval_records
            if approval.completed_at is not None and approval.created_at is not None
        ]
        approval_hours = [
            (approval.completed_at - approval.created_at).total_seconds() / 3600
            for approval in completed_approvals
        ]
        role_rows = (
            await self.session.execute(
                select(MeetingTurnRecord.speaker_role, func.count())
                .join(
                    BoardMeetingRecord,
                    MeetingTurnRecord.board_meeting_id == BoardMeetingRecord.id,
                )
                .where(BoardMeetingRecord.organization_id == organization_id)
                .group_by(MeetingTurnRecord.speaker_role)
                .order_by(func.count().desc())
                .limit(6)
            )
        ).all()
        evidence_rows = (
            await self.session.execute(
                select(BusinessAnalysisRecord.evidence_confidence, func.count())
                .where(BusinessAnalysisRecord.organization_id == organization_id)
                .group_by(BusinessAnalysisRecord.evidence_confidence)
            )
        ).all()
        evidence_quality = [
            {"confidence": confidence, "count": count} for confidence, count in evidence_rows
        ]
        trends = [
            {
                "meeting_id": str(record.id),
                "date": _iso(record.completed_at or record.created_at),
                "decision": record.decision,
                "confidence": float(record.aggregate_confidence),
                "risk": (record.assessment or {}).get("overall_risk"),
            }
            for record in completed[:12]
        ]
        analytics = {
            "meetings": {
                "total": len(meeting_records),
                "completed": len(completed),
                "active": len(
                    [record for record in meeting_records if record.status != "completed"]
                ),
            },
            "decisions": decision_counts,
            "approval_time_hours": (
                round(sum(approval_hours) / len(approval_hours), 2) if approval_hours else 0
            ),
            "most_active_executives": [
                {"role": role, "turns": count} for role, count in role_rows
            ],
            "success_rate": round(approved / len(completed), 3) if completed else 0.0,
            "evidence_quality": evidence_quality,
        }
        executive_dashboard = {
            "decision_quality_trends": trends,
            "confidence_trends": [
                {"date": item["date"], "confidence": item["confidence"]} for item in trends
            ],
            "risk_trends": [
                {"date": item["date"], "risk": item["risk"]}
                for item in trends
                if item["risk"] is not None
            ],
            "replay_frequency": await self._count(
                BoardMeetingRecord,
                BoardMeetingRecord.organization_id == organization_id,
                BoardMeetingRecord.is_favorite.is_(True),
            ),
            "recommendation_outcomes": decision_counts,
            "acceptance_rate": analytics["success_rate"],
        }
        return {"analytics": analytics, "executive_dashboard": executive_dashboard}

    async def executive_memory(
        self,
        role: str | None = None,
        limit: int = 50,
    ) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        stmt = (
            select(BoardMeetingRecord)
            .where(BoardMeetingRecord.organization_id == organization_id)
            .options(
                selectinload(BoardMeetingRecord.startup_brief),
                selectinload(BoardMeetingRecord.turns),
                selectinload(BoardMeetingRecord.votes),
                selectinload(BoardMeetingRecord.confidence_events),
            )
            .order_by(BoardMeetingRecord.created_at.desc())
            .limit(limit)
        )
        records = (await self.session.scalars(stmt)).unique().all()
        normalized_role = role.strip().lower() if role else None
        role_memory: dict[str, dict[str, object]] = {}
        role_meetings: dict[str, set[str]] = {}
        role_confidences: dict[str, list[float]] = {}
        recent_decisions = []
        confidence_history = []

        for record in records:
            meeting_key = str(record.id)
            assessment = record.assessment or {}
            recent_decisions.append(
                {
                    "meeting_id": meeting_key,
                    "startup_idea": record.startup_brief.startup_idea,
                    "decision": record.decision,
                    "confidence": float(record.aggregate_confidence),
                    "risk": assessment.get("overall_risk"),
                    "created_at": _iso(record.created_at),
                    "completed_at": _iso(record.completed_at),
                    "created_by_user_id": (
                        str(record.created_by_user_id) if record.created_by_user_id else None
                    ),
                }
            )
            confidence_history.append(
                {
                    "meeting_id": meeting_key,
                    "date": _iso(record.completed_at or record.created_at),
                    "confidence": float(record.aggregate_confidence),
                    "decision": record.decision,
                }
            )
            for vote in record.votes:
                if normalized_role and vote.role.lower() != normalized_role:
                    continue
                slot = _memory_slot(role_memory, vote.role)
                role_meetings.setdefault(vote.role, set()).add(meeting_key)
                role_confidences.setdefault(vote.role, []).append(float(vote.confidence))
                vote_counts = slot["vote_counts"]
                if isinstance(vote_counts, dict):
                    vote_counts[vote.vote] = int(vote_counts.get(vote.vote, 0)) + 1
                if vote.vote not in {"approve", "approve_with_conditions"}:
                    disagreements = slot["disagreements"]
                    if isinstance(disagreements, list):
                        disagreements.append(
                            {
                                "meeting_id": meeting_key,
                                "vote": vote.vote,
                                "rationale": vote.rationale,
                            }
                        )
            for turn in record.turns:
                if normalized_role and turn.speaker_role.lower() != normalized_role:
                    continue
                slot = _memory_slot(role_memory, turn.speaker_role)
                role_meetings.setdefault(turn.speaker_role, set()).add(meeting_key)
                recommendations = slot["recommendations"]
                if isinstance(recommendations, list):
                    recommendations.extend(
                        {
                            "meeting_id": meeting_key,
                            "recommendation": recommendation,
                            "confidence": float(turn.confidence),
                            "topic": turn.topic,
                        }
                        for recommendation in turn.recommendations[:4]
                    )
                references = slot["memory_references"]
                if isinstance(references, list):
                    references.extend(turn.memory_references or [])
                if turn.stance.lower() in {"cautious", "conditional", "disagree"}:
                    disagreements = slot["disagreements"]
                    if isinstance(disagreements, list):
                        disagreements.append(
                            {
                                "meeting_id": meeting_key,
                                "stance": turn.stance,
                                "message": turn.message[:360],
                            }
                        )

        executives = []
        for executive_role, slot in sorted(role_memory.items()):
            confidences = role_confidences.get(executive_role, [])
            slot["meetings_seen"] = len(role_meetings.get(executive_role, set()))
            slot["average_confidence"] = (
                round(sum(confidences) / len(confidences), 3) if confidences else 0.0
            )
            slot["recommendations"] = slot["recommendations"][:12]  # type: ignore[index]
            slot["disagreements"] = slot["disagreements"][:8]  # type: ignore[index]
            slot["memory_references"] = sorted(set(slot["memory_references"]))[:20]  # type: ignore[arg-type]
            executives.append(slot)

        approved = [
            item
            for item in recent_decisions
            if item["decision"] in {"approve", "approve_with_conditions"}
        ]
        rejected = [
            item
            for item in recent_decisions
            if str(item["decision"]).startswith(("reject", "defer"))
        ]
        return {
            "organization_id": str(organization_id),
            "role_filter": role,
            "executive_memory": executives,
            "decision_history": {
                "total": len(recent_decisions),
                "approved_or_conditionally_approved": len(approved),
                "rejected_or_deferred": len(rejected),
                "recent": recent_decisions[:20],
            },
            "confidence_history": confidence_history[:30],
            "generated_at": _iso(datetime.now(UTC)),
        }

    async def knowledge_graph(self, limit: int = 100) -> dict[str, object]:
        organization, _user = await self._default_workspace_records()
        nodes: dict[str, dict[str, object]] = {}
        edges: list[dict[str, object]] = []

        def add_node(node_id: str, node_type: str, label: str, **metadata: object) -> None:
            nodes.setdefault(
                node_id,
                {
                    "id": node_id,
                    "type": node_type,
                    "label": label,
                    "metadata": self._json_details(metadata),
                },
            )

        def add_edge(source: str, target: str, relationship: str) -> None:
            edges.append(
                {
                    "id": f"{source}:{relationship}:{target}",
                    "source": source,
                    "target": target,
                    "relationship": relationship,
                }
            )

        organization_node = f"organization:{organization.id}"
        add_node(organization_node, "organization", organization.name, slug=organization.slug)
        for user in await self._workspace_users(organization.id):
            node_id = f"user:{user['id']}"
            add_node(
                node_id,
                "user",
                str(user["display_name"]),
                role=user.get("role"),
                email=user.get("email"),
            )
            add_edge(organization_node, node_id, "has_member")

        meetings = (
            await self.session.scalars(
                select(BoardMeetingRecord)
                .where(BoardMeetingRecord.organization_id == organization.id)
                .options(
                    selectinload(BoardMeetingRecord.startup_brief),
                    selectinload(BoardMeetingRecord.votes),
                    selectinload(BoardMeetingRecord.reports),
                )
                .order_by(BoardMeetingRecord.created_at.desc())
                .limit(limit)
            )
        ).unique().all()
        for meeting in meetings:
            meeting_node = f"meeting:{meeting.id}"
            add_node(
                meeting_node,
                "board_meeting",
                meeting.startup_brief.startup_idea,
                decision=meeting.decision,
                confidence=float(meeting.aggregate_confidence),
            )
            add_edge(organization_node, meeting_node, "owns_decision")
            for vote in meeting.votes:
                role_node = f"executive:{vote.role}"
                add_node(role_node, "executive", vote.role, confidence=float(vote.confidence))
                add_edge(role_node, meeting_node, f"voted_{vote.vote}")
            for report in meeting.reports:
                report_node = f"report:{report.id}"
                add_node(report_node, "report", report.title, decision=report.decision)
                add_edge(meeting_node, report_node, "produced")
            risk_scores = (meeting.assessment or {}).get("risk_scores", {})
            if isinstance(risk_scores, dict):
                for risk_name, value in risk_scores.items():
                    risk_node = f"risk:{str(risk_name).lower()}"
                    add_node(risk_node, "risk", str(risk_name), score=value)
                    add_edge(meeting_node, risk_node, "contains_risk")

        analyses = (
            await self.session.scalars(
                select(BusinessAnalysisRecord)
                .where(BusinessAnalysisRecord.organization_id == organization.id)
                .options(
                    selectinload(BusinessAnalysisRecord.evidence_records),
                    selectinload(BusinessAnalysisRecord.saved_suppliers),
                )
                .order_by(BusinessAnalysisRecord.created_at.desc())
                .limit(limit)
            )
        ).unique().all()
        for analysis in analyses:
            analysis_node = f"analysis:{analysis.id}"
            add_node(
                analysis_node,
                "business_analysis",
                analysis.business_idea,
                category=analysis.business_category,
                recommendation=analysis.recommendation_label,
            )
            add_edge(organization_node, analysis_node, "owns_analysis")
            for evidence in analysis.evidence_records[:10]:
                evidence_node = f"evidence:{evidence.id}"
                add_node(
                    evidence_node,
                    "evidence",
                    evidence.claim[:120],
                    source_type=evidence.source_type,
                    confidence=evidence.confidence,
                )
                add_edge(analysis_node, evidence_node, "uses_evidence")
            for supplier in analysis.saved_suppliers[:10]:
                supplier_node = f"supplier:{supplier.id}"
                add_node(
                    supplier_node,
                    "supplier",
                    supplier.name,
                    category=supplier.category,
                    preferred=supplier.is_preferred,
                )
                add_edge(analysis_node, supplier_node, "shortlists_supplier")

        tasks = await self.list_tasks(limit=limit)
        for task in tasks:
            task_node = f"task:{task['id']}"
            add_node(task_node, "task", str(task["title"]), status=task.get("status"))
            add_edge(organization_node, task_node, "tracks_work")
            if task.get("board_meeting_id"):
                add_edge(f"meeting:{task['board_meeting_id']}", task_node, "has_task")
            if task.get("business_analysis_id"):
                add_edge(f"analysis:{task['business_analysis_id']}", task_node, "has_task")

        knowledge_records = (
            await self.session.scalars(
                select(KnowledgeItemRecord)
                .where(KnowledgeItemRecord.organization_id == organization.id)
                .order_by(KnowledgeItemRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        for item in knowledge_records:
            item_node = f"knowledge:{item.id}"
            add_node(item_node, "knowledge_item", item.title, tags=item.tags)
            add_edge(organization_node, item_node, "stores_knowledge")

        return {
            "organization_id": str(organization.id),
            "nodes": list(nodes.values()),
            "edges": edges[: limit * 4],
            "counts": {
                "nodes": len(nodes),
                "edges": min(len(edges), limit * 4),
                "meetings": len(meetings),
                "business_analyses": len(analyses),
                "knowledge_items": len(knowledge_records),
            },
            "generated_at": _iso(datetime.now(UTC)),
        }

    async def advanced_enterprise_analytics(self) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        base = await self.enterprise_analytics()
        meetings = (
            await self.session.scalars(
                select(BoardMeetingRecord)
                .where(BoardMeetingRecord.organization_id == organization_id)
                .options(
                    selectinload(BoardMeetingRecord.turns),
                    selectinload(BoardMeetingRecord.votes),
                    selectinload(BoardMeetingRecord.confidence_events),
                )
                .order_by(BoardMeetingRecord.created_at.desc())
                .limit(100)
            )
        ).unique().all()
        analyses = (
            await self.session.scalars(
                select(BusinessAnalysisRecord)
                .where(BusinessAnalysisRecord.organization_id == organization_id)
                .options(
                    selectinload(BusinessAnalysisRecord.performance_entries),
                    selectinload(BusinessAnalysisRecord.saved_suppliers),
                )
                .order_by(BusinessAnalysisRecord.created_at.desc())
                .limit(100)
            )
        ).unique().all()
        total_meetings = len(meetings)
        completed = [meeting for meeting in meetings if meeting.status == "completed"]
        turn_count = sum(len(meeting.turns) for meeting in meetings)
        confidence_values = [float(meeting.aggregate_confidence) for meeting in completed]

        role_scores: dict[str, list[float]] = {}
        role_votes: dict[str, dict[str, int]] = {}
        for meeting in meetings:
            for vote in meeting.votes:
                role_scores.setdefault(vote.role, []).append(float(vote.confidence))
                votes = role_votes.setdefault(vote.role, {})
                votes[vote.vote] = int(votes.get(vote.vote, 0)) + 1

        revenue_projection = []
        decision_accuracy = []
        supplier_rankings = []
        for analysis in analyses:
            result = analysis.result if isinstance(analysis.result, dict) else {}
            monthly = _dict_at(result, "daily_sales", "monthly_targets")
            target = _float_or_none(monthly.get("required_monthly_revenue"))
            latest_entry = (
                sorted(analysis.performance_entries, key=lambda item: item.created_at)[-1]
                if analysis.performance_entries
                else None
            )
            latest_revenue = (
                float(latest_entry.revenue)
                if latest_entry is not None and latest_entry.revenue is not None
                else None
            )
            variance = (
                round((latest_revenue - target) / target, 3)
                if latest_revenue is not None and target
                else None
            )
            revenue_projection.append(
                {
                    "analysis_id": str(analysis.id),
                    "business_idea": analysis.business_idea,
                    "target_monthly_revenue": target,
                    "latest_revenue": latest_revenue,
                    "variance_vs_target": variance,
                    "recommendation": analysis.recommendation_label,
                }
            )
            if latest_entry is not None:
                decision_accuracy.append(
                    {
                        "analysis_id": str(analysis.id),
                        "period_label": latest_entry.period_label,
                        "recommendation": analysis.recommendation_label,
                        "variance_vs_target": variance,
                    }
                )
            for supplier in analysis.saved_suppliers:
                supplier_rankings.append(
                    {
                        "supplier_id": str(supplier.id),
                        "analysis_id": str(analysis.id),
                        "name": supplier.name,
                        "category": supplier.category,
                        "distance_km": (
                            float(supplier.distance_km)
                            if supplier.distance_km is not None
                            else None
                        ),
                        "verification_status": supplier.verification_status,
                        "contact_status": supplier.contact_status,
                        "is_preferred": supplier.is_preferred,
                    }
                )

        task_rows = await self.list_tasks(limit=100)
        task_status_counts: dict[str, int] = {}
        for task in task_rows:
            status = str(task.get("status") or "open")
            task_status_counts[status] = task_status_counts.get(status, 0) + 1

        confidence_evolution = [
            {
                "meeting_id": str(meeting.id),
                "role": event.role,
                "confidence": float(event.confidence),
                "delta": float(event.delta) if event.delta is not None else None,
                "reason": event.reason,
                "created_at": _iso(event.created_at),
            }
            for meeting in meetings
            for event in sorted(meeting.confidence_events, key=lambda item: item.sequence)
        ][:50]
        risk_trends = [
            {
                "meeting_id": str(meeting.id),
                "decision": meeting.decision,
                "date": _iso(meeting.completed_at or meeting.created_at),
                "overall_risk": (meeting.assessment or {}).get("overall_risk"),
                "risk_scores": (meeting.assessment or {}).get("risk_scores", {}),
            }
            for meeting in completed[:30]
        ]
        opportunity_tracking = [
            {
                "analysis_id": str(analysis.id),
                "business_idea": analysis.business_idea,
                "category": analysis.business_category,
                "location": analysis.location_label,
                "score": analysis.opportunity_score,
                "recommendation": analysis.recommendation_label,
                "evidence_confidence": analysis.evidence_confidence,
                "created_at": _iso(analysis.created_at),
            }
            for analysis in analyses[:30]
        ]

        return {
            **base,
            "revenue_projection": revenue_projection[:30],
            "risk_trends": risk_trends,
            "meeting_effectiveness": {
                "total_meetings": total_meetings,
                "completed_meetings": len(completed),
                "completion_rate": round(len(completed) / total_meetings, 3)
                if total_meetings
                else 0.0,
                "consensus_rate": round(
                    sum(1 for meeting in completed if meeting.consensus_reached) / len(completed),
                    3,
                )
                if completed
                else 0.0,
                "average_confidence": round(sum(confidence_values) / len(confidence_values), 3)
                if confidence_values
                else 0.0,
                "average_turns_per_meeting": round(turn_count / total_meetings, 2)
                if total_meetings
                else 0.0,
            },
            "executive_performance": [
                {
                    "role": role,
                    "average_confidence": round(sum(values) / len(values), 3),
                    "votes": role_votes.get(role, {}),
                }
                for role, values in sorted(role_scores.items())
                if values
            ],
            "confidence_evolution": confidence_evolution,
            "opportunity_tracking": opportunity_tracking,
            "department_scorecards": {
                "open_tasks": task_status_counts.get("open", 0)
                + task_status_counts.get("in_progress", 0),
                "tasks_by_status": task_status_counts,
                "departments": [
                    self._department_dict(record)
                    for record in (
                        await self.session.scalars(
                            select(EnterpriseDepartmentRecord)
                            .where(EnterpriseDepartmentRecord.organization_id == organization_id)
                            .order_by(EnterpriseDepartmentRecord.name.asc())
                        )
                    ).all()
                ],
            },
            "decision_accuracy": decision_accuracy[:30],
            "supplier_rankings": sorted(
                supplier_rankings,
                key=lambda item: (
                    not bool(item["is_preferred"]),
                    item["distance_km"] is None,
                    item["distance_km"] or 999999,
                ),
            )[:30],
        }

    async def global_enterprise_search(
        self,
        query: str,
        limit: int = 20,
    ) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        base = await self.global_search(query, limit=limit)
        pattern = f"%{query.strip()}%"
        tasks = (
            await self.session.scalars(
                select(EnterpriseTaskRecord)
                .where(
                    EnterpriseTaskRecord.organization_id == organization_id,
                    or_(
                        EnterpriseTaskRecord.title.ilike(pattern),
                        EnterpriseTaskRecord.description.ilike(pattern),
                        EnterpriseTaskRecord.source.ilike(pattern),
                        EnterpriseTaskRecord.status.ilike(pattern),
                    ),
                )
                .order_by(EnterpriseTaskRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        analyses = (
            await self.session.scalars(
                select(BusinessAnalysisRecord)
                .where(
                    BusinessAnalysisRecord.organization_id == organization_id,
                    or_(
                        BusinessAnalysisRecord.business_idea.ilike(pattern),
                        BusinessAnalysisRecord.business_category.ilike(pattern),
                        BusinessAnalysisRecord.location_label.ilike(pattern),
                        BusinessAnalysisRecord.recommendation_label.ilike(pattern),
                        cast(BusinessAnalysisRecord.result, String).ilike(pattern),
                    ),
                )
                .order_by(BusinessAnalysisRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        evidence_rows = (
            await self.session.execute(
                select(BusinessEvidenceRecord, BusinessAnalysisRecord)
                .join(BusinessAnalysisRecord)
                .where(
                    BusinessAnalysisRecord.organization_id == organization_id,
                    or_(
                        BusinessEvidenceRecord.claim.ilike(pattern),
                        BusinessEvidenceRecord.source_name.ilike(pattern),
                        BusinessEvidenceRecord.source_type.ilike(pattern),
                        cast(BusinessEvidenceRecord.tags, String).ilike(pattern),
                    ),
                )
                .order_by(BusinessEvidenceRecord.retrieval_time.desc())
                .limit(limit)
            )
        ).all()
        supplier_rows = (
            await self.session.execute(
                select(SavedSupplierRecord, BusinessAnalysisRecord)
                .join(BusinessAnalysisRecord)
                .where(
                    BusinessAnalysisRecord.organization_id == organization_id,
                    or_(
                        SavedSupplierRecord.name.ilike(pattern),
                        SavedSupplierRecord.category.ilike(pattern),
                        SavedSupplierRecord.location_label.ilike(pattern),
                        SavedSupplierRecord.verification_status.ilike(pattern),
                        cast(SavedSupplierRecord.supplier_data, String).ilike(pattern),
                    ),
                )
                .order_by(SavedSupplierRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        user_rows = (
            await self.session.execute(
                select(EnterpriseUserRecord, EnterpriseMembershipRecord)
                .join(
                    EnterpriseMembershipRecord,
                    EnterpriseMembershipRecord.user_id == EnterpriseUserRecord.id,
                )
                .where(
                    EnterpriseMembershipRecord.organization_id == organization_id,
                    or_(
                        EnterpriseUserRecord.display_name.ilike(pattern),
                        EnterpriseUserRecord.email.ilike(pattern),
                        EnterpriseMembershipRecord.role.ilike(pattern),
                    ),
                )
                .order_by(EnterpriseUserRecord.display_name.asc())
                .limit(limit)
            )
        ).all()
        knowledge = await self.search_knowledge(query, limit=limit)
        collections = {
            "meetings": base["meetings"],
            "reports": base["reports"],
            "executives": base["executives"],
            "tasks": [await self._task_dict(task) for task in tasks],
            "business_analyses": [self._business_analysis_summary(record) for record in analyses],
            "evidence": [
                {
                    "id": str(evidence.id),
                    "analysis_id": str(analysis.id),
                    "claim": evidence.claim,
                    "source_name": evidence.source_name,
                    "source_type": evidence.source_type,
                    "confidence": evidence.confidence,
                    "tags": evidence.tags,
                    "created_at": _iso(evidence.retrieval_time),
                }
                for evidence, analysis in evidence_rows
            ],
            "suppliers": [
                {
                    "id": str(supplier.id),
                    "analysis_id": str(analysis.id),
                    "name": supplier.name,
                    "category": supplier.category,
                    "location_label": supplier.location_label,
                    "verification_status": supplier.verification_status,
                    "is_preferred": supplier.is_preferred,
                    "created_at": _iso(supplier.created_at),
                }
                for supplier, analysis in supplier_rows
            ],
            "knowledge": knowledge,
            "users": [
                {
                    **self._user_dict(user),
                    "role": membership.role,
                    "team_id": str(membership.team_id) if membership.team_id else None,
                }
                for user, membership in user_rows
            ],
        }
        flattened = [
            {"collection": collection, **item}
            for collection, items in collections.items()
            for item in items
            if isinstance(item, dict)
        ][: limit * 4]
        return {
            **base,
            "collections": collections,
            "items": flattened,
            "total": sum(len(items) for items in collections.values()),
        }

    async def assistant_answer(self, question: str) -> dict[str, object]:
        search_results = await self.global_enterprise_search(question, limit=8)
        memory = await self.executive_memory(limit=20)
        analytics = await self.advanced_enterprise_analytics()
        return build_assistant_answer(question, search_results, memory, analytics)

    async def observability_snapshot(self) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        audits = await self.audit_log(limit=30)
        errors = [
            audit
            for audit in audits
            if "error" in str(audit.get("action", "")).lower()
            or "failed" in str(audit.get("action", "")).lower()
        ]
        return {
            "database": {
                "organization_id": str(organization_id),
                "organizations": await self._count(EnterpriseOrganizationRecord),
                "users": await self._count(EnterpriseUserRecord),
                "meetings": await self._count(BoardMeetingRecord),
                "business_analyses": await self._count(BusinessAnalysisRecord),
                "knowledge_items": await self._count(KnowledgeItemRecord),
                "audit_events": await self._count(AuditEventRecord),
            },
            "recent_errors": errors[:10],
            "recent_audit_events": audits[:10],
            "security": {
                "role_checks": True,
                "audit_logging": True,
                "secure_exports": True,
                "secret_redaction": True,
            },
            "generated_at": _iso(datetime.now(UTC)),
        }

    async def collaboration_presence(self, limit: int = 30) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        collaborator_rows = (
            await self.session.execute(
                select(MeetingCollaboratorRecord, EnterpriseUserRecord, BoardMeetingRecord)
                .join(
                    EnterpriseUserRecord,
                    MeetingCollaboratorRecord.user_id == EnterpriseUserRecord.id,
                )
                .join(
                    BoardMeetingRecord,
                    MeetingCollaboratorRecord.board_meeting_id == BoardMeetingRecord.id,
                )
                .where(BoardMeetingRecord.organization_id == organization_id)
                .order_by(MeetingCollaboratorRecord.joined_at.desc())
                .limit(limit)
            )
        ).all()
        comments = (
            await self.session.scalars(
                select(ReportCommentRecord)
                .where(ReportCommentRecord.organization_id == organization_id)
                .order_by(ReportCommentRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        users = await self._workspace_users(organization_id)
        return {
            "active_users": users,
            "meeting_collaborators": [
                {
                    "meeting_id": str(meeting.id),
                    "collaborator": self._collaborator_dict(collaborator, user),
                    "decision": meeting.decision,
                }
                for collaborator, user, meeting in collaborator_rows
            ],
            "recent_comments": [await self._comment_dict(comment) for comment in comments],
            "notifications": await self.list_notifications(limit=limit),
            "generated_at": _iso(datetime.now(UTC)),
        }

    async def import_document(self, payload: dict[str, object]) -> dict[str, object] | None:
        organization, user = await self._default_workspace_records()
        meeting_id = _uuid_or_none(payload.get("meeting_id"))
        business_analysis_id = _uuid_or_none(payload.get("business_analysis_id"))
        meeting_exists = (
            await self.session.get(BoardMeetingRecord, meeting_id)
            if meeting_id is not None
            else None
        )
        if meeting_id is not None and meeting_exists is None:
            return None
        if (
            business_analysis_id is not None
            and await self.session.get(BusinessAnalysisRecord, business_analysis_id) is None
        ):
            return None
        document = analyze_document_import(payload)
        source_id = meeting_id or business_analysis_id
        knowledge = KnowledgeItemRecord(
            id=uuid4(),
            organization_id=organization.id,
            title=str(document["filename"]),
            item_type="document",
            source_type="document_import",
            source_id=source_id,
            content=str(document["extracted_text"] or document["summary"]),
            tags=list(document["tags"]),
        )
        self.session.add(knowledge)
        self._add_audit_event(
            organization.id,
            user.id,
            "document.imported",
            "document",
            knowledge.id,
            {
                "filename": document["filename"],
                "classification": document["classification"],
                "extraction_status": document["extraction_status"],
                "meeting_id": str(meeting_id) if meeting_id else None,
                "business_analysis_id": str(business_analysis_id)
                if business_analysis_id
                else None,
            },
        )
        await self.session.commit()
        document["knowledge_item_id"] = str(knowledge.id)
        return document

    async def run_workflow(self, payload: dict[str, object]) -> dict[str, object] | None:
        organization, user = await self._default_workspace_records()
        meeting_id = _uuid_or_none(payload.get("meeting_id"))
        business_analysis_id = _uuid_or_none(payload.get("business_analysis_id"))
        meeting = (
            await self.session.scalar(
                select(BoardMeetingRecord)
                .where(BoardMeetingRecord.id == meeting_id)
                .options(selectinload(BoardMeetingRecord.startup_brief))
            )
            if meeting_id
            else None
        )
        analysis = (
            await self.session.get(BusinessAnalysisRecord, business_analysis_id)
            if business_analysis_id
            else None
        )
        if meeting_id is not None and meeting is None:
            return None
        if business_analysis_id is not None and analysis is None:
            return None

        workflow_id = uuid4()
        actions = [str(action) for action in payload.get("actions") or []]
        executed: list[dict[str, object]] = []
        skipped: list[dict[str, object]] = []
        for action in actions:
            if action == "assign_tasks":
                task = EnterpriseTaskRecord(
                    organization_id=organization.id,
                    board_meeting_id=meeting_id,
                    business_analysis_id=business_analysis_id,
                    assignee_user_id=user.id,
                    title=_workflow_task_title(meeting, analysis),
                    description="Generated from enterprise workflow automation.",
                    source="workflow_automation",
                    status="open",
                    due_at=datetime.now(UTC) + timedelta(days=7),
                )
                self.session.add(task)
                executed.append({"action": action, "task_title": task.title})
            elif action == "notify_executives":
                self.session.add(
                    EnterpriseNotificationRecord(
                        organization_id=organization.id,
                        user_id=user.id,
                        channel="in_app",
                        title="Workflow automation completed",
                        body=f"{payload.get('trigger', 'manual')} workflow produced updates.",
                        status="unread",
                    )
                )
                executed.append({"action": action, "channel": "in_app"})
            elif action == "export_pdf":
                if meeting_id:
                    executed.append(
                        {
                            "action": action,
                            "url": f"/api/v1/reports/{meeting_id}/export?format=pdf",
                        }
                    )
                elif business_analysis_id:
                    executed.append(
                        {
                            "action": action,
                            "url": (
                                f"/api/v1/business-analyses/{business_analysis_id}"
                                "/export?format=pdf"
                            ),
                        }
                    )
                else:
                    skipped.append({"action": action, "reason": "No exportable entity supplied."})
            elif action == "archive_decision":
                archive = KnowledgeItemRecord(
                    organization_id=organization.id,
                    title=_workflow_archive_title(meeting, analysis),
                    item_type="decision_archive",
                    source_type="workflow_automation",
                    source_id=meeting_id or business_analysis_id,
                    content=_workflow_archive_content(meeting, analysis),
                    tags=["workflow", "decision_history"],
                )
                self.session.add(archive)
                executed.append({"action": action, "knowledge_title": archive.title})
            elif action in {"generate_report", "update_dashboard"}:
                executed.append({"action": action, "status": "available_from_existing_records"})
            else:
                skipped.append({"action": action, "reason": "Action is not registered."})

        self._add_audit_event(
            organization.id,
            user.id,
            "workflow.run",
            "workflow",
            workflow_id,
            {
                "trigger": payload.get("trigger"),
                "actions": actions,
                "executed": executed,
                "skipped": skipped,
            },
        )
        await self.session.commit()
        return {
            "id": str(workflow_id),
            "trigger": payload.get("trigger"),
            "meeting_id": str(meeting_id) if meeting_id else None,
            "business_analysis_id": str(business_analysis_id) if business_analysis_id else None,
            "executed": executed,
            "skipped": skipped,
            "catalog": build_workflow_catalog(),
            "created_at": _iso(datetime.now(UTC)),
        }

    async def admin_panel(self) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        organizations = await self.list_organizations()
        users = await self._workspace_users(organization_id)
        usage_statistics = {
            "organizations": len(organizations),
            "users": len(users),
            "meetings": await self._count(BoardMeetingRecord),
            "business_analyses": await self._count(BusinessAnalysisRecord),
            "tasks": await self._count(EnterpriseTaskRecord),
            "audit_events": await self._count(AuditEventRecord),
        }
        return {
            "users": users,
            "organizations": organizations,
            "api_keys": [
                {
                    "name": "Server managed provider keys",
                    "status": "configured_by_environment",
                    "secret": "redacted",
                }
            ],
            "providers": {},
            "feature_flags": {
                "enterprise_workspace": True,
                "collaboration": True,
                "email_notifications_ready": True,
                "localization_ready": True,
            },
            "diagnostics": {
                "default_workspace": str(organization_id),
                "desktop_compatibility": "preserved",
                "api_compatibility": "additive",
            },
            "usage_statistics": usage_statistics,
        }

    async def list_report_templates(self) -> list[dict[str, object]]:
        workspace = await self.ensure_default_workspace()
        records = (
            await self.session.scalars(
                select(ReportTemplateRecord)
                .where(
                    or_(
                        ReportTemplateRecord.organization_id == workspace["organization_id"],
                        ReportTemplateRecord.organization_id.is_(None),
                    )
                )
                .order_by(ReportTemplateRecord.category.asc())
            )
        ).all()
        return [self._report_template_dict(record) for record in records]

    async def search_knowledge(self, query: str, limit: int = 20) -> list[dict[str, object]]:
        workspace = await self.ensure_default_workspace()
        normalized = query.strip().lower()
        pattern = f"%{query.strip()}%"
        records = (
            await self.session.scalars(
                select(KnowledgeItemRecord)
                .where(
                    KnowledgeItemRecord.organization_id == workspace["organization_id"],
                    or_(
                        KnowledgeItemRecord.title.ilike(pattern),
                        KnowledgeItemRecord.content.ilike(pattern),
                        cast(KnowledgeItemRecord.tags, String).ilike(pattern),
                    ),
                )
                .order_by(KnowledgeItemRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        items = [self._knowledge_item_dict(record) for record in records]
        if "rejected" in normalized:
            rejected_meetings = (
                await self.session.scalars(
                    select(BoardMeetingRecord)
                    .where(BoardMeetingRecord.decision.ilike("%reject%"))
                    .order_by(BoardMeetingRecord.created_at.desc())
                    .limit(limit)
                )
            ).all()
            items.extend(
                {
                    "id": str(record.id),
                    "title": f"Rejected board recommendation: {record.decision}",
                    "item_type": "decision",
                    "source_type": "board_meeting",
                    "source_id": str(record.id),
                    "content": str(record.assessment or {}),
                    "tags": ["rejected", "decision"],
                    "created_at": _iso(record.created_at),
                }
                for record in rejected_meetings
            )

        budget_limit = self._extract_lakh_budget(normalized)
        if budget_limit is not None:
            analysis_stmt = (
                select(BusinessAnalysisRecord)
                .where(BusinessAnalysisRecord.budget <= budget_limit)
                .order_by(BusinessAnalysisRecord.created_at.desc())
                .limit(limit)
            )
            if "restaurant" in normalized:
                analysis_stmt = analysis_stmt.where(
                    or_(
                        BusinessAnalysisRecord.business_category.ilike("%restaurant%"),
                        BusinessAnalysisRecord.business_idea.ilike("%restaurant%"),
                    )
                )
            analyses = (await self.session.scalars(analysis_stmt)).all()
            items.extend(
                {
                    "id": str(record.id),
                    "title": record.business_idea,
                    "item_type": "business_analysis",
                    "source_type": "business_analysis",
                    "source_id": str(record.id),
                    "content": record.recommendation_label,
                    "tags": [record.business_category, "budget_filtered"],
                    "created_at": _iso(record.created_at),
                }
                for record in analyses
            )
        return items[:limit]

    async def audit_log(self, limit: int = 30) -> list[dict[str, object]]:
        workspace = await self.ensure_default_workspace()
        records = (
            await self.session.scalars(
                select(AuditEventRecord)
                .where(AuditEventRecord.organization_id == workspace["organization_id"])
                .order_by(AuditEventRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [self._audit_event_dict(record) for record in records]

    async def list_report_comments(self, meeting_id: UUID) -> list[dict[str, object]] | None:
        meeting = await self.session.get(BoardMeetingRecord, meeting_id)
        if meeting is None:
            return None
        records = (
            await self.session.scalars(
                select(ReportCommentRecord)
                .where(ReportCommentRecord.board_meeting_id == meeting_id)
                .order_by(ReportCommentRecord.created_at.asc())
            )
        ).all()
        return [await self._comment_dict(record) for record in records]

    async def create_report_comment(
        self,
        meeting_id: UUID,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        meeting = await self._meeting_with_workspace(meeting_id)
        if meeting is None:
            return None
        workspace = await self.ensure_default_workspace()
        author_id = meeting.created_by_user_id or workspace["user_id"]
        comment = ReportCommentRecord(
            id=uuid4(),
            organization_id=meeting.organization_id or workspace["organization_id"],
            board_meeting_id=meeting_id,
            parent_comment_id=(
                UUID(str(payload["parent_comment_id"]))
                if payload.get("parent_comment_id") is not None
                else None
            ),
            author_user_id=author_id,
            section_key=(
                str(payload["section_key"]) if payload.get("section_key") is not None else None
            ),
            body=str(payload["body"]),
            mentions=list(payload.get("mentions") or []),
            status="open",
        )
        self.session.add(comment)
        self._add_audit_event(
            comment.organization_id,
            author_id,
            "report.comment.created",
            "board_meeting",
            meeting_id,
            {"section_key": comment.section_key, "mentions": comment.mentions},
        )
        for mention in comment.mentions:
            mentioned_user = await self._ensure_user(str(mention), str(mention).split("@")[0])
            self.session.add(
                EnterpriseNotificationRecord(
                    organization_id=comment.organization_id,
                    user_id=mentioned_user.id,
                    channel="in_app",
                    title="You were mentioned in a report",
                    body=comment.body[:240],
                    status="unread",
                )
            )
        await self.session.commit()
        await self.session.refresh(comment)
        return await self._comment_dict(comment)

    async def resolve_report_comment(
        self,
        meeting_id: UUID,
        comment_id: UUID,
        status: str,
    ) -> dict[str, object] | None:
        comment = await self.session.get(ReportCommentRecord, comment_id)
        if comment is None or comment.board_meeting_id != meeting_id:
            return None
        workspace = await self.ensure_default_workspace()
        comment.status = status
        comment.resolved_at = datetime.now(UTC) if status == "resolved" else None
        self._add_audit_event(
            comment.organization_id,
            workspace["user_id"],
            "report.comment.updated",
            "comment",
            comment_id,
            {"status": status},
        )
        await self.session.commit()
        return await self._comment_dict(comment)

    async def join_meeting(
        self,
        meeting_id: UUID,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        meeting = await self._meeting_with_workspace(meeting_id)
        if meeting is None:
            return None
        user = await self._ensure_user(
            str(payload.get("user_email") or DEFAULT_USER_EMAIL),
            str(payload.get("display_name") or "Workspace Member"),
        )
        collaborator = await self.session.scalar(
            select(MeetingCollaboratorRecord).where(
                MeetingCollaboratorRecord.board_meeting_id == meeting_id,
                MeetingCollaboratorRecord.user_id == user.id,
            )
        )
        if collaborator is None:
            collaborator = MeetingCollaboratorRecord(
                id=uuid4(),
                board_meeting_id=meeting_id,
                user_id=user.id,
                role=str(payload.get("role") or "Manager"),
                status="joined",
            )
            self.session.add(collaborator)
        else:
            collaborator.role = str(payload.get("role") or collaborator.role)
            collaborator.status = "joined"
        self._add_audit_event(
            meeting.organization_id,
            user.id,
            "board_meeting.collaborator_joined",
            "board_meeting",
            meeting_id,
            {"role": collaborator.role},
        )
        await self.session.commit()
        return {
            "meeting_id": str(meeting_id),
            "collaborator": self._collaborator_dict(collaborator, user),
        }

    async def create_approval_workflow(
        self,
        meeting_id: UUID | None,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        workspace = await self.ensure_default_workspace()
        organization_id = workspace["organization_id"]
        if meeting_id is not None:
            meeting = await self._meeting_with_workspace(meeting_id)
            if meeting is None:
                return None
            organization_id = meeting.organization_id or organization_id
        business_analysis_id = (
            UUID(str(payload["business_analysis_id"]))
            if payload.get("business_analysis_id") is not None
            else None
        )
        if business_analysis_id is not None:
            analysis = await self.session.get(BusinessAnalysisRecord, business_analysis_id)
            if analysis is None:
                return None
            organization_id = analysis.organization_id or organization_id
        workflow = ApprovalWorkflowRecord(
            id=uuid4(),
            organization_id=organization_id,
            board_meeting_id=meeting_id,
            business_analysis_id=business_analysis_id,
            status="pending",
            requested_by_user_id=workspace["user_id"],
            reason=str(payload["reason"]) if payload.get("reason") is not None else None,
        )
        self.session.add(workflow)
        await self.session.flush()
        steps = list(payload.get("steps") or ["Manager", "CEO"])
        for position, role in enumerate(steps, start=1):
            self.session.add(
                ApprovalStepRecord(
                    id=uuid4(),
                    workflow_id=workflow.id,
                    role=str(role),
                    position=position,
                    status="pending",
                )
            )
        self._add_audit_event(
            organization_id,
            workspace["user_id"],
            "approval.workflow.created",
            "approval_workflow",
            workflow.id,
            {"steps": steps, "board_meeting_id": str(meeting_id) if meeting_id else None},
        )
        await self.session.commit()
        return await self._approval_dict(workflow.id)

    async def decide_approval_step(
        self,
        workflow_id: UUID,
        step_id: UUID,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        workspace = await self.ensure_default_workspace()
        workflow = await self.session.get(ApprovalWorkflowRecord, workflow_id)
        step = await self.session.get(ApprovalStepRecord, step_id)
        if workflow is None or step is None or step.workflow_id != workflow_id:
            return None
        step.status = str(payload["status"])
        step.reason = str(payload["reason"]) if payload.get("reason") is not None else None
        step.approver_user_id = workspace["user_id"]
        step.decided_at = datetime.now(UTC)
        steps = (
            await self.session.scalars(
                select(ApprovalStepRecord)
                .where(ApprovalStepRecord.workflow_id == workflow_id)
                .order_by(ApprovalStepRecord.position.asc())
            )
        ).all()
        if step.status == "rejected":
            workflow.status = "rejected"
            workflow.completed_at = datetime.now(UTC)
        elif all(item.status == "approved" for item in steps):
            workflow.status = "approved"
            workflow.completed_at = datetime.now(UTC)
        else:
            workflow.status = "pending"
        self.session.add(
            EnterpriseNotificationRecord(
                organization_id=workflow.organization_id,
                user_id=workflow.requested_by_user_id,
                channel="in_app",
                title="Approval workflow updated",
                body=f"{step.role} marked the step {step.status}.",
                status="unread",
            )
        )
        self._add_audit_event(
            workflow.organization_id,
            workspace["user_id"],
            f"approval.step.{step.status}",
            "approval_step",
            step_id,
            {"workflow_id": str(workflow_id), "reason": step.reason},
        )
        await self.session.commit()
        return await self._approval_dict(workflow_id)

    async def list_tasks(
        self,
        status: str | None = None,
        limit: int = 30,
    ) -> list[dict[str, object]]:
        workspace = await self.ensure_default_workspace()
        stmt = (
            select(EnterpriseTaskRecord)
            .where(EnterpriseTaskRecord.organization_id == workspace["organization_id"])
            .order_by(EnterpriseTaskRecord.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(EnterpriseTaskRecord.status == status)
        records = (await self.session.scalars(stmt)).all()
        return [await self._task_dict(record) for record in records]

    async def create_task(self, payload: dict[str, object]) -> dict[str, object]:
        workspace = await self.ensure_default_workspace()
        assignee_id: UUID | None = None
        if payload.get("assignee_email") is not None:
            assignee = await self._ensure_user(
                str(payload["assignee_email"]),
                str(payload["assignee_email"]).split("@")[0],
            )
            assignee_id = assignee.id
        due_at = (
            _parse_datetime(str(payload["due_at"])) if payload.get("due_at") is not None else None
        )
        task = EnterpriseTaskRecord(
            id=uuid4(),
            organization_id=workspace["organization_id"],
            board_meeting_id=(
                UUID(str(payload["board_meeting_id"]))
                if payload.get("board_meeting_id") is not None
                else None
            ),
            business_analysis_id=(
                UUID(str(payload["business_analysis_id"]))
                if payload.get("business_analysis_id") is not None
                else None
            ),
            assignee_user_id=assignee_id,
            title=str(payload["title"]),
            description=(
                str(payload["description"]) if payload.get("description") is not None else None
            ),
            source=str(payload.get("source") or "manual"),
            status="open",
            due_at=due_at,
        )
        self.session.add(task)
        if due_at is not None:
            self.session.add(
                CalendarEventRecord(
                    organization_id=workspace["organization_id"],
                    title=task.title,
                    event_type="task_deadline",
                    starts_at=due_at,
                    related_entity_type="task",
                    related_entity_id=task.id,
                )
            )
        self._add_audit_event(
            workspace["organization_id"],
            workspace["user_id"],
            "task.created",
            "task",
            task.id,
            {"title": task.title, "source": task.source},
        )
        await self.session.commit()
        return await self._task_dict(task)

    async def update_task(
        self,
        task_id: UUID,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        workspace = await self.ensure_default_workspace()
        task = await self.session.get(EnterpriseTaskRecord, task_id)
        if task is None:
            return None
        if payload.get("status") is not None:
            task.status = str(payload["status"])
        if payload.get("title") is not None:
            task.title = str(payload["title"])
        if payload.get("description") is not None:
            task.description = str(payload["description"])
        if payload.get("due_at") is not None:
            task.due_at = _parse_datetime(str(payload["due_at"]))
        self._add_audit_event(
            task.organization_id,
            workspace["user_id"],
            "task.updated",
            "task",
            task.id,
            {"status": task.status, "title": task.title},
        )
        await self.session.commit()
        return await self._task_dict(task)

    async def list_calendar_events(self, limit: int = 30) -> list[dict[str, object]]:
        workspace = await self.ensure_default_workspace()
        records = (
            await self.session.scalars(
                select(CalendarEventRecord)
                .where(CalendarEventRecord.organization_id == workspace["organization_id"])
                .order_by(CalendarEventRecord.starts_at.asc())
                .limit(limit)
            )
        ).all()
        return [self._calendar_event_dict(record) for record in records]

    async def list_notifications(self, limit: int = 30) -> list[dict[str, object]]:
        workspace = await self.ensure_default_workspace()
        records = (
            await self.session.scalars(
                select(EnterpriseNotificationRecord)
                .where(EnterpriseNotificationRecord.organization_id == workspace["organization_id"])
                .order_by(EnterpriseNotificationRecord.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [self._notification_dict(record) for record in records]

    async def _ensure_portfolio_demo_content(self, organization_id: UUID, user_id: UUID) -> None:
        await self._ensure_portfolio_demo_meeting(organization_id, user_id)
        await self._ensure_portfolio_demo_business_analysis(organization_id, user_id)

    async def _ensure_portfolio_demo_meeting(self, organization_id: UUID, user_id: UUID) -> None:
        existing = await self.session.scalar(
            select(BoardMeetingRecord)
            .join(BoardMeetingRecord.startup_brief)
            .where(
                BoardMeetingRecord.organization_id == organization_id,
                StartupBriefRecord.startup_idea == PORTFOLIO_DEMO_STARTUP_IDEA,
            )
        )
        if existing is not None:
            return

        now = datetime.now(UTC)
        meeting_id = uuid4()
        brief_id = uuid4()
        report_id = uuid4()
        self.session.add(
            StartupBriefRecord(
                id=brief_id,
                startup_idea=PORTFOLIO_DEMO_STARTUP_IDEA,
                industry="Healthcare operations AI",
                country="United States",
                budget=Decimal("180000.00"),
                timeline_months=6,
                competitors=["Abridge", "Nabla", "Notable"],
                target_audience="Independent clinics with five to fifty staff members",
                funding_stage="pre-seed",
                business_model="B2B SaaS",
                meeting_mode="investor_pitch",
                created_at=now - timedelta(days=5),
            )
        )
        self.session.add(
            BoardMeetingRecord(
                id=meeting_id,
                organization_id=organization_id,
                created_by_user_id=user_id,
                startup_brief_id=brief_id,
                status="completed",
                is_favorite=True,
                consensus_reached=True,
                aggregate_confidence=Decimal("0.8400"),
                decision="approve_with_conditions",
                current_phase="completed",
                assessment={
                    "overall_risk": 0.38,
                    "risk_scores": {
                        "market": 0.32,
                        "financial": 0.36,
                        "operational": 0.42,
                        "legal": 0.48,
                    },
                    "signals": {
                        "market": "Strong clinic pain, but workflow adoption must be proven.",
                        "legal": "HIPAA review and vendor BAAs are pre-launch blockers.",
                    },
                },
                created_at=now - timedelta(days=5),
                completed_at=now - timedelta(days=4, hours=20),
            )
        )
        for profile in EXECUTIVE_PROFILES[:6]:
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
        for sequence, role, stance, message in (
            (
                1,
                "CEO",
                "supportive",
                "The wedge is specific enough for a focused clinic operations pilot.",
            ),
            (
                2,
                "Risk Officer",
                "cautious",
                "Approval should depend on security review and signed pilot letters.",
            ),
            (
                3,
                "CFO",
                "conditional",
                "Budget is viable if the team keeps integration scope narrow.",
            ),
        ):
            self.session.add(
                MeetingTurnRecord(
                    board_meeting_id=meeting_id,
                    sequence=sequence,
                    round_number=1,
                    speaker_role=role,
                    turn_type="portfolio_demo",
                    topic="Demo decision review",
                    stance=stance,
                    confidence=Decimal("0.8200"),
                    message=message,
                    concerns=["Evidence must be validated with pilots"],
                    recommendations=["Secure two design partners", "Complete compliance review"],
                    reasoning=["Demo seed for recruiter walkthrough"],
                    memory_references=["portfolio-demo"],
                    created_at=now - timedelta(days=4, hours=23, minutes=60 - sequence),
                )
            )
        for role, vote, confidence, rationale in (
            (
                "CEO",
                "approve_with_conditions",
                Decimal("0.8700"),
                "Approve after pilot evidence and security checklist.",
            ),
            (
                "Risk Officer",
                "approve_with_conditions",
                Decimal("0.7600"),
                "Proceed only with explicit compliance gates.",
            ),
            (
                "CFO",
                "approve_with_conditions",
                Decimal("0.8400"),
                "Capital plan is controlled enough for a six-month validation cycle.",
            ),
        ):
            self.session.add(
                BoardVoteRecord(
                    board_meeting_id=meeting_id,
                    role=role,
                    vote=vote,
                    confidence=confidence,
                    rationale=rationale,
                )
            )
        self.session.add(
            FinalReportRecord(
                id=report_id,
                board_meeting_id=meeting_id,
                title="Board Report: Neighborhood Health Ops Copilot",
                decision="approve_with_conditions",
                created_at=now - timedelta(days=4, hours=20),
            )
        )
        for position, (section_key, section_title, content) in enumerate(
            (
                (
                    "executive_summary",
                    "Executive Summary",
                    {
                        "summary": "Approve a narrow clinic-ops pilot with compliance gates.",
                        "conditions": [
                            "Two signed pilot letters",
                            "HIPAA/security review",
                            "Integration scope capped at scheduling and documentation workflows",
                        ],
                    },
                ),
                (
                    "evidence_packet",
                    "Evidence Packet",
                    {
                        "live_evidence": 0,
                        "historical_evidence": 2,
                        "user_provided_information": 3,
                        "ai_inference": 4,
                    },
                ),
                (
                    "decision_history",
                    "Decision History",
                    {
                        "created_by": DEFAULT_USER_EMAIL,
                        "approved_by": "CEO",
                        "reason": "Portfolio demo seed for review workflows.",
                        "confidence": 0.84,
                    },
                ),
            ),
            start=1,
        ):
            self.session.add(
                ReportSectionRecord(
                    final_report_id=report_id,
                    section_key=section_key,
                    section_title=section_title,
                    content=content,
                    position=position,
                )
            )
        workflow_id = uuid4()
        self.session.add(
            ApprovalWorkflowRecord(
                id=workflow_id,
                organization_id=organization_id,
                board_meeting_id=meeting_id,
                status="pending",
                requested_by_user_id=user_id,
                reason="Demo manager and CEO sign-off path.",
                created_at=now - timedelta(days=3),
            )
        )
        for position, role in enumerate(("Manager", "CEO"), start=1):
            self.session.add(
                ApprovalStepRecord(
                    workflow_id=workflow_id,
                    role=role,
                    position=position,
                    status="pending",
                )
            )
        self.session.add(
            EnterpriseTaskRecord(
                organization_id=organization_id,
                board_meeting_id=meeting_id,
                assignee_user_id=user_id,
                title="Validate clinic pilot commitments",
                description="Confirm two design partners and document integration constraints.",
                source="portfolio_demo",
                status="open",
                due_at=now + timedelta(days=10),
            )
        )
        self.session.add(
            EnterpriseNotificationRecord(
                organization_id=organization_id,
                user_id=user_id,
                channel="in_app",
                title="Recruiter demo workspace is ready",
                body="A sample meeting, report, approval, task, and business analysis were seeded.",
                status="unread",
                created_at=now - timedelta(days=2),
            )
        )
        self._add_audit_event(
            organization_id,
            user_id,
            "portfolio_demo.seeded",
            "board_meeting",
            meeting_id,
            {"startup_idea": PORTFOLIO_DEMO_STARTUP_IDEA},
        )

    async def _ensure_portfolio_demo_business_analysis(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> None:
        existing = await self.session.scalar(
            select(BusinessAnalysisRecord).where(
                BusinessAnalysisRecord.organization_id == organization_id,
                BusinessAnalysisRecord.business_idea == PORTFOLIO_DEMO_BUSINESS_IDEA,
            )
        )
        if existing is not None:
            return

        request = BusinessAnalysisRequest.model_validate(
            {
                "workflow_type": "existing_idea",
                "business_idea": PORTFOLIO_DEMO_BUSINESS_IDEA,
                "business_category": "Restaurant",
                "location": {
                    "country": "India",
                    "city": "Bengaluru",
                    "locality": "Indiranagar",
                    "radius_km": 3,
                    "source": "manual",
                },
                "budget": 1800000,
                "priorities": [
                    "Full analysis",
                    "Supplier validation",
                    "Required daily sales",
                ],
                "data_mode": "demo",
                "shop_size_sqft": 850,
                "target_customers": "office workers, students, and evening delivery customers",
                "risk_tolerance": "medium",
                "timeline": "Open within four months",
                "manual_competitors": [
                    {
                        "name": "Indiranagar Bowl Co.",
                        "category": "healthy bowls",
                        "distance_km": 0.8,
                        "notes": "Observed lunch queues in demo scenario.",
                    }
                ],
                "manual_suppliers": [
                    {
                        "name": "Fresh Produce Aggregator",
                        "category": "vegetables and grains",
                        "distance_km": 7,
                        "product_categories": ["produce", "grains", "packaging"],
                        "delivery_available": True,
                        "contact_status": "shortlisted",
                    }
                ],
                "financial_assumptions": {
                    "expected_rent": 220000,
                    "security_deposit": 1320000,
                    "equipment_budget": 450000,
                    "opening_inventory_budget": 180000,
                    "marketing_budget": 120000,
                    "monthly_staff_cost": 240000,
                    "working_capital_months": 3,
                    "average_transaction_value": 260,
                    "gross_margin_percent": 58,
                    "working_days_per_month": 30,
                },
                "optional_inputs": {"portfolio_demo": True},
            }
        )
        result = build_business_analysis(request, settings=get_settings())
        analysis_id = await self._add_business_analysis_records(
            organization_id,
            user_id,
            request.model_dump(mode="json"),
            result,
        )
        self.session.add(
            EnterpriseTaskRecord(
                organization_id=organization_id,
                business_analysis_id=analysis_id,
                assignee_user_id=user_id,
                title="Visit shortlisted restaurant location",
                description="Check footfall, frontage, parking, and nearby competitors.",
                source="portfolio_demo",
                status="open",
                due_at=datetime.now(UTC) + timedelta(days=5),
            )
        )

    async def _ensure_default_templates(self, organization_id: UUID) -> None:
        existing = set(
            (
                await self.session.scalars(
                    select(ReportTemplateRecord.category).where(
                        ReportTemplateRecord.organization_id == organization_id
                    )
                )
            ).all()
        )
        default_sections = [
            "executive_summary",
            "market_assessment",
            "financial_review",
            "risk_register",
            "decision_history",
            "approval_plan",
        ]
        for name, category in DEFAULT_REPORT_TEMPLATES:
            if category in existing:
                continue
            self.session.add(
                ReportTemplateRecord(
                    organization_id=organization_id,
                    name=f"{name} Decision Report",
                    category=category,
                    locale="en",
                    sections=default_sections,
                )
            )

    async def _ensure_default_knowledge(self, organization_id: UUID) -> None:
        existing = await self.session.scalar(
            select(KnowledgeItemRecord).where(
                KnowledgeItemRecord.organization_id == organization_id,
                KnowledgeItemRecord.source_type == "seed",
            )
        )
        if existing is not None:
            return
        for title, content, tags in (
            (
                "Approval Playbook",
                "Analysts prepare evidence, managers approve readiness, and CEOs sign off.",
                ["approval", "governance", "workflow"],
            ),
            (
                "Evidence Quality Standard",
                (
                    "Recommendations should include source freshness, confidence, risk, "
                    "and next steps."
                ),
                ["evidence", "quality", "best_practice"],
            ),
            (
                "Board Review Cadence",
                "Review active decisions monthly and archive outcomes with confidence movement.",
                ["calendar", "review", "decision_history"],
            ),
        ):
            self.session.add(
                KnowledgeItemRecord(
                    organization_id=organization_id,
                    title=title,
                    item_type="best_practice",
                    source_type="seed",
                    content=content,
                    tags=tags,
                )
            )

    async def _ensure_default_calendar(self, organization_id: UUID) -> None:
        existing = await self.session.scalar(
            select(CalendarEventRecord).where(
                CalendarEventRecord.organization_id == organization_id,
                CalendarEventRecord.event_type == "board_review",
            )
        )
        if existing is not None:
            return
        starts_at = datetime.now(UTC) + timedelta(days=7)
        self.session.add(
            CalendarEventRecord(
                organization_id=organization_id,
                title="Monthly board review",
                event_type="board_review",
                starts_at=starts_at,
                ends_at=starts_at + timedelta(hours=1),
            )
        )

    async def _default_workspace_records(
        self,
    ) -> tuple[EnterpriseOrganizationRecord, EnterpriseUserRecord]:
        workspace = await self.ensure_default_workspace()
        organization = await self.session.get(
            EnterpriseOrganizationRecord,
            workspace["organization_id"],
        )
        user = await self.session.get(EnterpriseUserRecord, workspace["user_id"])
        if organization is None or user is None:
            raise RuntimeError("Default enterprise workspace could not be loaded.")
        return organization, user

    async def _meeting_with_workspace(self, meeting_id: UUID) -> BoardMeetingRecord | None:
        workspace = await self.ensure_default_workspace()
        meeting = await self.session.get(BoardMeetingRecord, meeting_id)
        if meeting is None:
            return None
        changed = False
        if meeting.organization_id is None:
            meeting.organization_id = workspace["organization_id"]
            changed = True
        if meeting.created_by_user_id is None:
            meeting.created_by_user_id = workspace["user_id"]
            changed = True
        if changed:
            self._add_audit_event(
                meeting.organization_id,
                meeting.created_by_user_id,
                "board_meeting.workspace_attached",
                "board_meeting",
                meeting.id,
                {},
            )
            await self.session.flush()
        return meeting

    async def _ensure_user(self, email: str, display_name: str) -> EnterpriseUserRecord:
        normalized_email = email.strip().lower()
        user = await self.session.scalar(
            select(EnterpriseUserRecord).where(EnterpriseUserRecord.email == normalized_email)
        )
        if user is not None:
            return user
        user = EnterpriseUserRecord(
            id=uuid4(),
            display_name=display_name.strip() or normalized_email,
            email=normalized_email,
            locale="en",
            status="active",
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def _workspace_users(self, organization_id: UUID) -> list[dict[str, object]]:
        rows = (
            await self.session.execute(
                select(EnterpriseUserRecord, EnterpriseMembershipRecord)
                .join(
                    EnterpriseMembershipRecord,
                    EnterpriseMembershipRecord.user_id == EnterpriseUserRecord.id,
                )
                .where(EnterpriseMembershipRecord.organization_id == organization_id)
                .order_by(EnterpriseUserRecord.display_name.asc())
            )
        ).all()
        return [
            {
                **self._user_dict(user),
                "role": membership.role,
                "permissions": membership.permissions,
                "team_id": str(membership.team_id) if membership.team_id else None,
            }
            for user, membership in rows
        ]

    async def _approval_workflows(
        self,
        status: str | None = None,
        limit: int = 30,
    ) -> list[dict[str, object]]:
        workspace = await self.ensure_default_workspace()
        stmt = (
            select(ApprovalWorkflowRecord)
            .where(ApprovalWorkflowRecord.organization_id == workspace["organization_id"])
            .order_by(ApprovalWorkflowRecord.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(ApprovalWorkflowRecord.status == status)
        workflows = (await self.session.scalars(stmt)).all()
        return [
            approval
            for approval in [await self._approval_dict(workflow.id) for workflow in workflows]
            if approval is not None
        ]

    async def _approval_dict(self, workflow_id: UUID) -> dict[str, object] | None:
        workflow = await self.session.get(ApprovalWorkflowRecord, workflow_id)
        if workflow is None:
            return None
        steps = (
            await self.session.scalars(
                select(ApprovalStepRecord)
                .where(ApprovalStepRecord.workflow_id == workflow_id)
                .order_by(ApprovalStepRecord.position.asc())
            )
        ).all()
        return {
            "id": str(workflow.id),
            "organization_id": str(workflow.organization_id),
            "board_meeting_id": (
                str(workflow.board_meeting_id) if workflow.board_meeting_id else None
            ),
            "business_analysis_id": (
                str(workflow.business_analysis_id) if workflow.business_analysis_id else None
            ),
            "status": workflow.status,
            "requested_by_user_id": str(workflow.requested_by_user_id),
            "reason": workflow.reason,
            "created_at": _iso(workflow.created_at),
            "completed_at": _iso(workflow.completed_at),
            "steps": [
                {
                    "id": str(step.id),
                    "role": step.role,
                    "position": step.position,
                    "status": step.status,
                    "approver_user_id": (
                        str(step.approver_user_id) if step.approver_user_id else None
                    ),
                    "reason": step.reason,
                    "decided_at": _iso(step.decided_at),
                }
                for step in steps
            ],
        }

    async def _organization_dict(
        self,
        record: EnterpriseOrganizationRecord,
    ) -> dict[str, object]:
        return {
            "id": str(record.id),
            "name": record.name,
            "slug": record.slug,
            "status": record.status,
            "default_locale": record.default_locale,
            "created_at": _iso(record.created_at),
            "departments_count": await self._count(
                EnterpriseDepartmentRecord,
                EnterpriseDepartmentRecord.organization_id == record.id,
            ),
            "teams_count": await self._count(
                EnterpriseTeamRecord,
                EnterpriseTeamRecord.organization_id == record.id,
            ),
            "users_count": await self._count(
                EnterpriseMembershipRecord,
                EnterpriseMembershipRecord.organization_id == record.id,
            ),
        }

    def _department_dict(self, record: EnterpriseDepartmentRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "name": record.name,
            "created_at": _iso(record.created_at),
        }

    def _team_dict(self, record: EnterpriseTeamRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "department_id": str(record.department_id) if record.department_id else None,
            "name": record.name,
            "created_at": _iso(record.created_at),
        }

    def _user_dict(self, record: EnterpriseUserRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "display_name": record.display_name,
            "email": record.email,
            "locale": record.locale,
            "status": record.status,
            "created_at": _iso(record.created_at),
        }

    async def _comment_dict(self, record: ReportCommentRecord) -> dict[str, object]:
        author = await self.session.get(EnterpriseUserRecord, record.author_user_id)
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "board_meeting_id": str(record.board_meeting_id),
            "parent_comment_id": (
                str(record.parent_comment_id) if record.parent_comment_id else None
            ),
            "author_user_id": str(record.author_user_id),
            "author": self._user_dict(author) if author is not None else None,
            "section_key": record.section_key,
            "body": record.body,
            "mentions": record.mentions,
            "status": record.status,
            "resolved_at": _iso(record.resolved_at),
            "created_at": _iso(record.created_at),
        }

    def _collaborator_dict(
        self,
        record: MeetingCollaboratorRecord,
        user: EnterpriseUserRecord,
    ) -> dict[str, object]:
        return {
            "id": str(record.id),
            "board_meeting_id": str(record.board_meeting_id),
            "user": self._user_dict(user),
            "role": record.role,
            "status": record.status,
            "joined_at": _iso(record.joined_at),
        }

    async def _task_dict(self, record: EnterpriseTaskRecord) -> dict[str, object]:
        assignee = (
            await self.session.get(EnterpriseUserRecord, record.assignee_user_id)
            if record.assignee_user_id is not None
            else None
        )
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "board_meeting_id": str(record.board_meeting_id) if record.board_meeting_id else None,
            "business_analysis_id": (
                str(record.business_analysis_id) if record.business_analysis_id else None
            ),
            "assignee": self._user_dict(assignee) if assignee is not None else None,
            "title": record.title,
            "description": record.description,
            "source": record.source,
            "status": record.status,
            "due_at": _iso(record.due_at),
            "created_at": _iso(record.created_at),
        }

    def _calendar_event_dict(self, record: CalendarEventRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "title": record.title,
            "event_type": record.event_type,
            "starts_at": _iso(record.starts_at),
            "ends_at": _iso(record.ends_at),
            "related_entity_type": record.related_entity_type,
            "related_entity_id": (
                str(record.related_entity_id) if record.related_entity_id else None
            ),
            "created_at": _iso(record.created_at),
        }

    def _notification_dict(self, record: EnterpriseNotificationRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "user_id": str(record.user_id) if record.user_id else None,
            "channel": record.channel,
            "title": record.title,
            "body": record.body,
            "status": record.status,
            "created_at": _iso(record.created_at),
        }

    def _knowledge_item_dict(self, record: KnowledgeItemRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "title": record.title,
            "item_type": record.item_type,
            "source_type": record.source_type,
            "source_id": str(record.source_id) if record.source_id else None,
            "content": record.content,
            "tags": record.tags,
            "created_at": _iso(record.created_at),
        }

    def _report_template_dict(self, record: ReportTemplateRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id) if record.organization_id else None,
            "name": record.name,
            "category": record.category,
            "locale": record.locale,
            "sections": record.sections,
            "created_at": _iso(record.created_at),
        }

    def _audit_event_dict(self, record: AuditEventRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "organization_id": str(record.organization_id) if record.organization_id else None,
            "actor_user_id": str(record.actor_user_id) if record.actor_user_id else None,
            "action": record.action,
            "entity_type": record.entity_type,
            "entity_id": str(record.entity_id) if record.entity_id else None,
            "details": record.details,
            "created_at": _iso(record.created_at),
        }

    async def _unique_organization_slug(self, value: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-") or "workspace"
        slug = base[:110]
        suffix = 2
        while await self.session.scalar(
            select(EnterpriseOrganizationRecord).where(
                EnterpriseOrganizationRecord.slug == slug
            )
        ):
            ending = f"-{suffix}"
            slug = f"{base[: 120 - len(ending)]}{ending}"
            suffix += 1
        return slug

    async def _count(self, model: object, *conditions: object) -> int:
        stmt = select(func.count()).select_from(model)
        for condition in conditions:
            stmt = stmt.where(condition)
        return int(await self.session.scalar(stmt) or 0)

    def _extract_lakh_budget(self, query: str) -> Decimal | None:
        match = re.search(r"(?:under|below|less than)\D*(\d+(?:\.\d+)?)\s*lakh", query)
        if match is None:
            return None
        return Decimal(str(float(match.group(1)) * 100000))

    def _add_audit_event(
        self,
        organization_id: UUID | None,
        actor_user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID | None,
        details: dict[str, object],
    ) -> None:
        self.session.add(
            AuditEventRecord(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=self._json_details(details),
            )
        )

    def _json_details(self, value: object) -> object:
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return _iso(value)
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {str(key): self._json_details(item) for key, item in value.items()}
        if isinstance(value, list | tuple | set):
            return [self._json_details(item) for item in value]
        return value

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
                    report.title if report else f"Board Report: {record.startup_brief.startup_idea}"
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
            "meeting_mode": record.meeting_mode,
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

    def _business_analysis_summary(self, record: BusinessAnalysisRecord) -> dict[str, object]:
        return {
            "analysis_id": str(record.id),
            "business_idea": record.business_idea,
            "business_category": record.business_category,
            "location_label": record.location_label,
            "recommendation_label": record.recommendation_label,
            "opportunity_score": record.opportunity_score,
            "evidence_confidence": record.evidence_confidence,
            "data_mode": record.data_mode,
            "created_at": _iso(record.created_at),
        }

    def _performance_entry_dict(
        self,
        record: BusinessPerformanceEntryRecord,
    ) -> dict[str, object]:
        return {
            **record.performance_data,
            "entry_id": str(record.id),
            "analysis_id": str(record.analysis_id),
            "period_label": record.period_label,
            "revenue": float(record.revenue) if record.revenue is not None else None,
            "expenses": float(record.expenses) if record.expenses is not None else None,
            "customers": record.customers,
            "transactions": record.transactions,
            "created_at": _iso(record.created_at),
        }


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)


def _memory_slot(
    slots: dict[str, dict[str, object]],
    role: str,
) -> dict[str, object]:
    return slots.setdefault(
        role,
        {
            "role": role,
            "meetings_seen": 0,
            "average_confidence": 0.0,
            "vote_counts": {},
            "recommendations": [],
            "disagreements": [],
            "memory_references": [],
        },
    )


def _dict_at(value: dict[str, object], *keys: str) -> dict[str, object]:
    current: object = value
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _uuid_or_none(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _workflow_task_title(
    meeting: BoardMeetingRecord | None,
    analysis: BusinessAnalysisRecord | None,
) -> str:
    if analysis is not None:
        return f"Validate recommendation: {analysis.business_idea}"[:220]
    if meeting is not None and meeting.startup_brief is not None:
        return f"Follow up board decision: {meeting.startup_brief.startup_idea}"[:220]
    return "Review enterprise workflow output"


def _workflow_archive_title(
    meeting: BoardMeetingRecord | None,
    analysis: BusinessAnalysisRecord | None,
) -> str:
    if analysis is not None:
        return f"Decision archive: {analysis.business_idea}"[:220]
    if meeting is not None and meeting.startup_brief is not None:
        return f"Decision archive: {meeting.startup_brief.startup_idea}"[:220]
    return "Decision archive"


def _workflow_archive_content(
    meeting: BoardMeetingRecord | None,
    analysis: BusinessAnalysisRecord | None,
) -> str:
    if analysis is not None:
        return (
            f"Business analysis {analysis.id} recorded recommendation "
            f"{analysis.recommendation_label} with opportunity score "
            f"{analysis.opportunity_score} and evidence confidence "
            f"{analysis.evidence_confidence}."
        )
    if meeting is not None:
        return (
            f"Board meeting {meeting.id} recorded decision {meeting.decision} "
            f"with aggregate confidence {float(meeting.aggregate_confidence):.3f}."
        )
    return "Workflow archived a decision event without a linked meeting or analysis."
