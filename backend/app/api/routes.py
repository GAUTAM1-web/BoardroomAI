from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Literal, TypeVar
from uuid import UUID

import structlog
from asyncpg import PostgresError
from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.domain.boardroom.export import report_to_markdown, report_to_pdf
from app.domain.boardroom.ideas import generate_startup_ideas
from app.domain.boardroom.orchestrator import BoardMeetingOrchestrator
from app.domain.boardroom.roles import EXECUTIVE_PROFILES
from app.domain.boardroom.streaming import LiveBoardMeetingOrchestrator
from app.domain.business_intelligence.service import (
    build_board_review,
    build_business_analysis,
    clear_live_data_cache,
    provider_status,
)
from app.domain.enterprise.security import has_permission, normalize_enterprise_role
from app.infrastructure.ai.local_provider import LocalExecutiveIntelligenceProvider
from app.infrastructure.database.repositories import PostgresMeetingRepository
from app.infrastructure.database.session import AsyncSessionLocal
from app.schemas.boardroom import (
    BoardMeetingDetailResponse,
    BoardMeetingResponse,
    DashboardResponse,
    ExecutiveCatalogResponse,
    ExecutiveProfileResponse,
    FavoriteMeetingRequest,
    FavoriteMeetingResponse,
    GlobalSearchResponse,
    MeetingHistoryResponse,
    StartupBriefRequest,
    StartupIdeaGenerationRequest,
    StartupIdeasResponse,
)
from app.schemas.business import (
    BusinessAnalysisListResponse,
    BusinessAnalysisRequest,
    BusinessAnalysisResponse,
    BusinessBoardReviewResponse,
    BusinessPerformanceEntryRequest,
    BusinessPerformanceEntryResponse,
    BusinessProviderStatusResponse,
)
from app.schemas.enterprise import (
    AdminPanelResponse,
    ApprovalCreateRequest,
    ApprovalDecisionRequest,
    ApprovalResponse,
    CollaboratorJoinRequest,
    CommentCreateRequest,
    CommentResolveRequest,
    CommentsResponse,
    EnterpriseAnalyticsResponse,
    EnterpriseCollectionResponse,
    EnterpriseDashboardResponse,
    OrganizationCreateRequest,
    OrganizationListResponse,
    OrganizationResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/api/v1", tags=["boardroom"])
T = TypeVar("T")
logger = structlog.get_logger("boardroom.api")


async def with_repository(operation: Callable[[PostgresMeetingRepository], Awaitable[T]]) -> T:
    try:
        async with AsyncSessionLocal() as session:
            return await operation(PostgresMeetingRepository(session))
    except (PostgresError, SQLAlchemyError) as exc:
        logger.warning("repository_unavailable", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail=(
                "Database unavailable or schema is not migrated. "
                "Check DATABASE_URL and run Alembic migrations."
            ),
        ) from exc


def require_enterprise_permission(role: str | None, permission: str) -> str:
    if not has_permission(role, permission):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role or 'Administrator'}' cannot perform '{permission}'.",
        )
    return normalize_enterprise_role(role)


@router.get("/executives", response_model=ExecutiveCatalogResponse)
async def list_executives() -> ExecutiveCatalogResponse:
    return ExecutiveCatalogResponse(
        executives=[
            ExecutiveProfileResponse(
                role=profile.role,
                charter=profile.charter,
                personality=profile.personality,
                goals=list(profile.goals),
                risk_focus=list(profile.risk_focus),
            )
            for profile in EXECUTIVE_PROFILES
        ]
    )


@router.post("/board-meetings", response_model=BoardMeetingResponse)
async def create_board_meeting(
    payload: StartupBriefRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> BoardMeetingResponse:
    require_enterprise_permission(role, "meetings:create")
    brief = payload.to_domain()
    orchestrator = BoardMeetingOrchestrator(provider=LocalExecutiveIntelligenceProvider())
    result = orchestrator.run(brief)
    await with_repository(lambda repository: repository.persist_completed_result(brief, result))
    return BoardMeetingResponse.model_validate(result.to_dict())


@router.post("/startup-ideas/generate", response_model=StartupIdeasResponse)
async def generate_ideas(payload: StartupIdeaGenerationRequest) -> StartupIdeasResponse:
    ideas = generate_startup_ideas(payload.to_domain())
    return StartupIdeasResponse.model_validate({"ideas": [idea.to_dict() for idea in ideas]})


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard() -> DashboardResponse:
    return DashboardResponse.model_validate(
        await with_repository(lambda repository: repository.dashboard_snapshot())
    )


@router.get("/organizations", response_model=OrganizationListResponse)
async def list_organizations(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> OrganizationListResponse:
    require_enterprise_permission(role, "meetings:view")
    organizations = await with_repository(lambda repository: repository.list_organizations())
    return OrganizationListResponse.model_validate({"organizations": organizations})


@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    payload: OrganizationCreateRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> OrganizationResponse:
    require_enterprise_permission(role, "workspace:admin")
    organization = await with_repository(
        lambda repository: repository.create_organization(payload.model_dump(mode="json"))
    )
    return OrganizationResponse.model_validate({"organization": organization})


@router.get("/enterprise/dashboard", response_model=EnterpriseDashboardResponse)
async def enterprise_dashboard(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseDashboardResponse:
    require_enterprise_permission(role, "meetings:view")
    return EnterpriseDashboardResponse.model_validate(
        await with_repository(lambda repository: repository.enterprise_dashboard())
    )


@router.get("/enterprise/analytics", response_model=EnterpriseAnalyticsResponse)
async def enterprise_analytics(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseAnalyticsResponse:
    require_enterprise_permission(role, "meetings:view")
    return EnterpriseAnalyticsResponse.model_validate(
        await with_repository(lambda repository: repository.enterprise_analytics())
    )


@router.get("/enterprise/admin", response_model=AdminPanelResponse)
async def enterprise_admin_panel(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> AdminPanelResponse:
    require_enterprise_permission(role, "workspace:admin")
    panel = await with_repository(lambda repository: repository.admin_panel())
    panel["providers"] = provider_status(get_settings())
    return AdminPanelResponse.model_validate(panel)


@router.get("/enterprise/audit", response_model=EnterpriseCollectionResponse)
async def enterprise_audit_log(
    limit: int = Query(default=30, ge=1, le=100),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseCollectionResponse:
    require_enterprise_permission(role, "workspace:admin")
    items = await with_repository(lambda repository: repository.audit_log(limit=limit))
    return EnterpriseCollectionResponse.model_validate({"items": items})


@router.get("/report-templates", response_model=EnterpriseCollectionResponse)
async def report_templates(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseCollectionResponse:
    require_enterprise_permission(role, "meetings:view")
    items = await with_repository(lambda repository: repository.list_report_templates())
    return EnterpriseCollectionResponse.model_validate({"items": items})


@router.get("/knowledge/search", response_model=EnterpriseCollectionResponse)
async def knowledge_search(
    q: str = Query(min_length=1, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseCollectionResponse:
    require_enterprise_permission(role, "meetings:view")
    items = await with_repository(lambda repository: repository.search_knowledge(q, limit=limit))
    return EnterpriseCollectionResponse.model_validate({"items": items})


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=30, ge=1, le=100),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> TaskListResponse:
    require_enterprise_permission(role, "meetings:view")
    tasks = await with_repository(lambda repository: repository.list_tasks(status, limit=limit))
    return TaskListResponse.model_validate({"tasks": tasks})


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    payload: TaskCreateRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> TaskResponse:
    require_enterprise_permission(role, "tasks:manage")
    task = await with_repository(
        lambda repository: repository.create_task(payload.model_dump(mode="json"))
    )
    return TaskResponse.model_validate({"task": task})


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> TaskResponse:
    require_enterprise_permission(role, "tasks:manage")
    task = await with_repository(
        lambda repository: repository.update_task(
            task_id,
            payload.model_dump(mode="json", exclude_unset=True),
        )
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate({"task": task})


@router.get("/calendar", response_model=EnterpriseCollectionResponse)
async def calendar_events(
    limit: int = Query(default=30, ge=1, le=100),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseCollectionResponse:
    require_enterprise_permission(role, "meetings:view")
    items = await with_repository(lambda repository: repository.list_calendar_events(limit=limit))
    return EnterpriseCollectionResponse.model_validate({"items": items})


@router.get("/notifications", response_model=EnterpriseCollectionResponse)
async def notifications(
    limit: int = Query(default=30, ge=1, le=100),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseCollectionResponse:
    require_enterprise_permission(role, "meetings:view")
    items = await with_repository(lambda repository: repository.list_notifications(limit=limit))
    return EnterpriseCollectionResponse.model_validate({"items": items})


@router.get("/board-meetings", response_model=MeetingHistoryResponse)
async def list_board_meetings(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=30, ge=1, le=100),
    favorite_only: bool = Query(default=False),
) -> MeetingHistoryResponse:
    meetings = await with_repository(
        lambda repository: repository.list_meetings(q, limit=limit, favorite_only=favorite_only)
    )
    return MeetingHistoryResponse.model_validate({"meetings": meetings})


@router.get("/board-meetings/{meeting_id}", response_model=BoardMeetingDetailResponse)
async def get_board_meeting(meeting_id: UUID) -> BoardMeetingDetailResponse:
    meeting = await with_repository(lambda repository: repository.get_meeting_detail(meeting_id))
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return BoardMeetingDetailResponse.model_validate(meeting)


@router.post(
    "/board-meetings/{meeting_id}/collaborators",
    response_model=EnterpriseCollectionResponse,
)
async def join_board_meeting(
    meeting_id: UUID,
    payload: CollaboratorJoinRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseCollectionResponse:
    require_enterprise_permission(role, "meetings:view")
    collaborator = await with_repository(
        lambda repository: repository.join_meeting(meeting_id, payload.model_dump(mode="json"))
    )
    if collaborator is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return EnterpriseCollectionResponse.model_validate({"items": [collaborator]})


@router.post("/board-meetings/{meeting_id}/approvals", response_model=ApprovalResponse)
async def create_meeting_approval(
    meeting_id: UUID,
    payload: ApprovalCreateRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> ApprovalResponse:
    require_enterprise_permission(role, "approvals:approve")
    approval = await with_repository(
        lambda repository: repository.create_approval_workflow(
            meeting_id,
            payload.model_dump(mode="json"),
        )
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return ApprovalResponse.model_validate({"approval": approval})


@router.patch("/board-meetings/{meeting_id}/favorite", response_model=FavoriteMeetingResponse)
async def favorite_board_meeting(
    meeting_id: UUID,
    payload: FavoriteMeetingRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> FavoriteMeetingResponse:
    require_enterprise_permission(role, "meetings:edit")
    favorite = await with_repository(
        lambda repository: repository.set_favorite(meeting_id, payload.is_favorite)
    )
    if favorite is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return FavoriteMeetingResponse.model_validate(favorite)


@router.delete("/board-meetings/{meeting_id}", status_code=204)
async def delete_board_meeting(
    meeting_id: UUID,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> Response:
    require_enterprise_permission(role, "meetings:edit")
    deleted = await with_repository(lambda repository: repository.delete_meeting(meeting_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return Response(status_code=204)


@router.get("/search", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=10, ge=1, le=30),
) -> GlobalSearchResponse:
    return GlobalSearchResponse.model_validate(
        await with_repository(lambda repository: repository.global_search(q, limit=limit))
    )


@router.get("/business-data/providers", response_model=BusinessProviderStatusResponse)
async def business_provider_status() -> BusinessProviderStatusResponse:
    return BusinessProviderStatusResponse.model_validate(provider_status(get_settings()))


@router.post("/business-data/providers/retry", response_model=BusinessProviderStatusResponse)
async def retry_business_providers() -> BusinessProviderStatusResponse:
    clear_live_data_cache()
    return BusinessProviderStatusResponse.model_validate(provider_status(get_settings()))


@router.post("/business-analyses", response_model=BusinessAnalysisResponse)
async def create_business_analysis(
    payload: BusinessAnalysisRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> BusinessAnalysisResponse:
    require_enterprise_permission(role, "meetings:create")
    result = build_business_analysis(payload, settings=get_settings())
    await with_repository(
        lambda repository: repository.persist_business_analysis(
            payload.model_dump(mode="json"),
            result,
        )
    )
    return BusinessAnalysisResponse.model_validate(result)


@router.get("/business-analyses", response_model=BusinessAnalysisListResponse)
async def list_business_analyses(
    limit: int = Query(default=30, ge=1, le=100),
) -> BusinessAnalysisListResponse:
    analyses = await with_repository(lambda repository: repository.list_business_analyses(limit))
    return BusinessAnalysisListResponse.model_validate({"analyses": analyses})


@router.get("/business-analyses/{analysis_id}", response_model=BusinessAnalysisResponse)
async def get_business_analysis(analysis_id: UUID) -> BusinessAnalysisResponse:
    analysis = await with_repository(
        lambda repository: repository.get_business_analysis(analysis_id)
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Business analysis not found")
    return BusinessAnalysisResponse.model_validate(analysis)


@router.get("/business-analyses/{analysis_id}/export")
async def export_business_analysis(
    analysis_id: UUID,
    format: Literal["json", "markdown", "pdf"] = Query(default="pdf"),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> Response:
    require_enterprise_permission(role, "reports:export")
    analysis = await with_repository(
        lambda repository: repository.get_business_analysis(analysis_id)
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Business analysis not found")

    filename_base = f"business-decision-brief-{analysis_id}"
    if format == "json":
        return JSONResponse(
            content=analysis,
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.json"'},
        )

    export_payload = _business_export_payload(analysis)
    if format == "markdown":
        return PlainTextResponse(
            report_to_markdown(export_payload),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.md"'},
        )
    return Response(
        content=report_to_pdf(export_payload),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
    )


@router.post(
    "/business-analyses/{analysis_id}/performance-entries",
    response_model=BusinessPerformanceEntryResponse,
)
async def record_business_performance_entry(
    analysis_id: UUID,
    payload: BusinessPerformanceEntryRequest,
) -> BusinessPerformanceEntryResponse:
    entry = await with_repository(
        lambda repository: repository.record_business_performance_entry(
            analysis_id,
            payload.model_dump(mode="json"),
        )
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Business analysis not found")
    return BusinessPerformanceEntryResponse.model_validate(entry)


@router.post(
    "/business-analyses/{analysis_id}/board-review",
    response_model=BusinessBoardReviewResponse,
)
async def create_business_board_review(analysis_id: UUID) -> BusinessBoardReviewResponse:
    analysis = await with_repository(
        lambda repository: repository.get_business_analysis(analysis_id)
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Business analysis not found")
    performance_entries = await with_repository(
        lambda repository: repository.list_business_performance_entries(analysis_id)
    )
    if performance_entries is None:
        raise HTTPException(status_code=404, detail="Business analysis not found")
    entries = [
        BusinessPerformanceEntryRequest.model_validate(entry) for entry in performance_entries
    ]
    return BusinessBoardReviewResponse.model_validate(build_board_review(analysis, entries))


@router.post("/business-analyses/{analysis_id}/approvals", response_model=ApprovalResponse)
async def create_business_analysis_approval(
    analysis_id: UUID,
    payload: ApprovalCreateRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> ApprovalResponse:
    require_enterprise_permission(role, "approvals:approve")
    approval_payload = payload.model_dump(mode="json")
    approval_payload["business_analysis_id"] = str(analysis_id)
    approval = await with_repository(
        lambda repository: repository.create_approval_workflow(None, approval_payload)
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Business analysis not found")
    return ApprovalResponse.model_validate({"approval": approval})


@router.get("/reports/{meeting_id}/comments", response_model=CommentsResponse)
async def report_comments(
    meeting_id: UUID,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> CommentsResponse:
    require_enterprise_permission(role, "meetings:view")
    comments = await with_repository(
        lambda repository: repository.list_report_comments(meeting_id)
    )
    if comments is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return CommentsResponse.model_validate({"comments": comments})


@router.post("/reports/{meeting_id}/comments", response_model=CommentsResponse)
async def create_report_comment(
    meeting_id: UUID,
    payload: CommentCreateRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> CommentsResponse:
    require_enterprise_permission(role, "reports:comment")
    comment = await with_repository(
        lambda repository: repository.create_report_comment(
            meeting_id,
            payload.model_dump(mode="json"),
        )
    )
    if comment is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return CommentsResponse.model_validate({"comments": [comment]})


@router.patch("/reports/{meeting_id}/comments/{comment_id}", response_model=CommentsResponse)
async def resolve_report_comment(
    meeting_id: UUID,
    comment_id: UUID,
    payload: CommentResolveRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> CommentsResponse:
    require_enterprise_permission(role, "reports:comment")
    comment = await with_repository(
        lambda repository: repository.resolve_report_comment(
            meeting_id,
            comment_id,
            payload.status,
        )
    )
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return CommentsResponse.model_validate({"comments": [comment]})


@router.post("/approvals/{workflow_id}/steps/{step_id}/decision", response_model=ApprovalResponse)
async def decide_approval_step(
    workflow_id: UUID,
    step_id: UUID,
    payload: ApprovalDecisionRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> ApprovalResponse:
    require_enterprise_permission(role, "approvals:approve")
    approval = await with_repository(
        lambda repository: repository.decide_approval_step(
            workflow_id,
            step_id,
            payload.model_dump(mode="json"),
        )
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval step not found")
    return ApprovalResponse.model_validate({"approval": approval})


@router.get("/reports/{meeting_id}/export")
async def export_report(
    meeting_id: UUID,
    format: Literal["json", "markdown", "pdf"] = Query(default="pdf"),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> Response:
    require_enterprise_permission(role, "reports:export")
    meeting = await with_repository(lambda repository: repository.get_meeting_detail(meeting_id))
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    filename_base = f"boardroom-report-{meeting_id}"
    if format == "json":
        return JSONResponse(
            content=meeting,
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.json"'},
        )
    if format == "markdown":
        return PlainTextResponse(
            report_to_markdown(meeting),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.md"'},
        )
    return Response(
        content=report_to_pdf(meeting),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
    )


def _business_export_payload(analysis: dict[str, object]) -> dict[str, object]:
    report = analysis["report"]
    intake = analysis["intake"]
    score = analysis["opportunity_score"]
    return {
        "meeting_id": analysis["analysis_id"],
        "aggregate_confidence": float(score["score"]) / 100,
        "report": report,
        "startup_brief": {
            "startup_idea": intake["business_idea"],
            "industry": intake["business_category"],
            "country": (
                analysis.get("board_brief", {}).get("country")
                if isinstance(analysis.get("board_brief"), dict)
                else "Unknown"
            ),
        },
    }


@router.websocket("/board-meetings/live")
async def stream_board_meeting(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        raw_payload = await websocket.receive_json()
        payload = StartupBriefRequest.model_validate(raw_payload)

    except ValidationError as exc:
        await websocket.send_json(
            {
                "event_type": "error",
                "payload": {
                    "message": "Invalid founder brief.",
                    "details": exc.errors(),
                },
            }
        )
        await websocket.close(code=1003)
        return

    except WebSocketDisconnect:
        return

    orchestrator = LiveBoardMeetingOrchestrator(
        provider=LocalExecutiveIntelligenceProvider(),
        delay_seconds=0.25,
    )

    try:
        async with AsyncSessionLocal() as session:
            repository = PostgresMeetingRepository(session)

            async for event in orchestrator.stream(
                payload.to_domain(),
                recorder=repository,
            ):
                await websocket.send_json(event.to_dict())

    except WebSocketDisconnect:
        return

    except Exception as exc:
        logger.exception("live_boardroom_failed", error_type=type(exc).__name__)
        await websocket.send_json(
            {
                "event_type": "error",
                "payload": {
                    "message": "Live board meeting failed.",
                    "details": "See server logs for the failure reference.",
                },
            }
        )
        await websocket.close(code=1011)
