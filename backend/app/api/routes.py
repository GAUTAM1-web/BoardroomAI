from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Literal, TypeVar
from uuid import UUID

import httpx
import redis.asyncio as redis
import structlog
from asyncpg import PostgresError
from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.cache import SharedCache, session_cache_key
from app.core.config import get_settings
from app.core.deployment import environment_diagnostics, is_production, redacted_provider_posture
from app.core.jobs import JobQueue
from app.core.monitoring import monitoring_snapshot
from app.core.plugins import plugin_manifest
from app.core.recovery import integrity_check, recovery_plan
from app.core.scheduler import ScheduleStore
from app.domain.auth import auth_capabilities, create_session_payload, sign_session, verify_session
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
from app.domain.enterprise.saas_intelligence import (
    build_intelligence_suggestions,
    build_workflow_catalog,
)
from app.domain.enterprise.security import has_permission, normalize_enterprise_role
from app.infrastructure.ai.local_provider import LocalExecutiveIntelligenceProvider
from app.infrastructure.database.repositories import PostgresMeetingRepository
from app.infrastructure.database.session import AsyncSessionLocal
from app.schemas.auth import (
    AuthConfigResponse,
    AuthLogoutResponse,
    AuthSessionRequest,
    AuthSessionResponse,
    AuthStatusResponse,
)
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
    AssistantAnswerResponse,
    AssistantQuestionRequest,
    CollaboratorJoinRequest,
    CommentCreateRequest,
    CommentResolveRequest,
    CommentsResponse,
    DocumentImportRequest,
    DocumentImportResponse,
    EnterpriseAnalyticsResponse,
    EnterpriseCollectionResponse,
    EnterpriseDashboardResponse,
    EnterpriseIntelligenceResponse,
    OrganizationCreateRequest,
    OrganizationListResponse,
    OrganizationResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from app.schemas.operations import (
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    ScheduleCreateRequest,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleToggleRequest,
)

router = APIRouter(prefix="/api/v1", tags=["boardroom"])
v2_router = APIRouter(prefix="/api/v2", tags=["boardroom-v2"])
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


def _provider_health_rows(snapshot: dict[str, object]) -> list[dict[str, object]]:
    providers = snapshot.get("providers", {})
    if isinstance(providers, dict):
        rows = []
        for name, data in providers.items():
            if isinstance(data, dict):
                rows.append({"name": str(name), **data})
            else:
                rows.append({"name": str(name), "status": str(data)})
        return rows
    if isinstance(providers, list):
        return [item for item in providers if isinstance(item, dict)]
    return []


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


@router.get("/auth/config", response_model=AuthConfigResponse)
async def auth_config() -> AuthConfigResponse:
    return AuthConfigResponse.model_validate(auth_capabilities(get_settings()))


@router.get("/auth/session", response_model=AuthStatusResponse)
async def current_auth_session(request: Request) -> AuthStatusResponse:
    settings = get_settings()
    payload = verify_session(
        _session_token_from_request(request, settings.session_cookie_name),
        settings,
    )
    if payload is not None and settings.distributed_sessions_enabled:
        await _shared_cache(request).set_json(
            session_cache_key(str(payload.get("session_id"))),
            payload,
            ttl_seconds=settings.session_ttl_seconds,
        )
    return AuthStatusResponse.model_validate(
        {
            "authenticated": payload is not None,
            "session": payload,
            "capabilities": auth_capabilities(settings),
        }
    )


@router.post("/auth/session", response_model=AuthSessionResponse)
async def create_auth_session(
    payload: AuthSessionRequest,
    request: Request,
    response: Response,
) -> AuthSessionResponse:
    settings = get_settings()
    _ensure_auth_mode_enabled(payload, settings)
    session_payload = create_session_payload(
        mode=payload.mode,
        email=payload.email.strip().lower() if payload.email else None,
        settings=settings,
    )
    token = sign_session(session_payload, settings)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=max(300, settings.session_ttl_seconds),
        httponly=True,
        secure=is_production(settings),
        samesite="lax",
    )
    if settings.distributed_sessions_enabled:
        await _shared_cache(request).set_json(
            session_cache_key(str(session_payload["session_id"])),
            session_payload,
            ttl_seconds=settings.session_ttl_seconds,
        )
    return AuthSessionResponse.model_validate(session_payload)


@router.post("/auth/logout", response_model=AuthLogoutResponse)
async def logout_auth_session(request: Request, response: Response) -> AuthLogoutResponse:
    settings = get_settings()
    payload = verify_session(
        _session_token_from_request(request, settings.session_cookie_name),
        settings,
    )
    if payload is not None:
        await _shared_cache(request).delete(session_cache_key(str(payload.get("session_id"))))
    response.delete_cookie(settings.session_cookie_name)
    return AuthLogoutResponse()


@router.get("/diagnostics/environment")
async def diagnostics_environment() -> dict[str, object]:
    return environment_diagnostics(get_settings())


@router.get("/diagnostics/providers")
async def diagnostics_providers() -> dict[str, object]:
    settings = get_settings()
    return {
        "providers": provider_status(settings),
        "secrets": redacted_provider_posture(settings),
    }


@router.get("/diagnostics/dependencies")
async def diagnostics_dependencies() -> dict[str, object]:
    return await _dependency_diagnostics()


@router.get("/diagnostics")
async def diagnostics() -> dict[str, object]:
    settings = get_settings()
    dependencies = await _dependency_diagnostics()
    return {
        "environment": environment_diagnostics(settings),
        "dependencies": dependencies,
        "providers": provider_status(settings),
    }


@router.get("/versions")
async def api_versions() -> dict[str, object]:
    return {
        "current": "v1",
        "supported": ["v1", "v2-preview"],
        "deprecated": [],
        "notes": "v1 remains stable. v2 is a compatibility preview for future API expansion.",
    }


@router.get("/operations/cache/health")
async def operations_cache_health(
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    return await _shared_cache(request).health()


@router.get("/operations/jobs", response_model=JobListResponse)
async def operations_jobs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> JobListResponse:
    require_enterprise_permission(role, "workspace:admin")
    queue = _job_queue(request)
    return JobListResponse.model_validate(
        {"jobs": await queue.list(limit), "stats": await queue.stats()}
    )


@router.post("/operations/jobs", response_model=JobResponse)
async def create_operations_job(
    payload: JobCreateRequest,
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> JobResponse:
    normalized_role = require_enterprise_permission(role, "workspace:admin")
    job = await _job_queue(request).enqueue(
        payload.job_type,
        payload.payload,
        actor=normalized_role,
        organization_id=payload.organization_id,
    )
    return JobResponse.model_validate({"job": job})


@router.get("/operations/jobs/{job_id}", response_model=JobResponse)
async def operations_job_detail(
    job_id: str,
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> JobResponse:
    require_enterprise_permission(role, "workspace:admin")
    job = await _job_queue(request).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate({"job": job})


@router.post("/operations/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_operations_job(
    job_id: str,
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> JobResponse:
    require_enterprise_permission(role, "workspace:admin")
    job = await _job_queue(request).cancel(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate({"job": job})


@router.post("/operations/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_operations_job(
    job_id: str,
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> JobResponse:
    require_enterprise_permission(role, "workspace:admin")
    job = await _job_queue(request).retry(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate({"job": job})


@router.get("/operations/schedules", response_model=ScheduleListResponse)
async def operations_schedules(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> ScheduleListResponse:
    require_enterprise_permission(role, "workspace:admin")
    schedules = await _schedule_store(request).list(limit=limit)
    return ScheduleListResponse.model_validate({"schedules": schedules})


@router.post("/operations/schedules", response_model=ScheduleResponse)
async def create_operations_schedule(
    payload: ScheduleCreateRequest,
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> ScheduleResponse:
    normalized_role = require_enterprise_permission(role, "workspace:admin")
    try:
        schedule = await _schedule_store(request).create(
            payload.name,
            payload.cron,
            payload.job_type,
            payload.payload,
            actor=normalized_role,
            organization_id=payload.organization_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ScheduleResponse.model_validate({"schedule": schedule})


@router.patch("/operations/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_operations_schedule(
    schedule_id: str,
    payload: ScheduleToggleRequest,
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> ScheduleResponse:
    require_enterprise_permission(role, "workspace:admin")
    schedule = await _schedule_store(request).set_enabled(schedule_id, payload.enabled)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse.model_validate({"schedule": schedule})


@router.post("/operations/schedules/run-due")
async def enqueue_due_schedules(
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    jobs = await _schedule_store(request).enqueue_due()
    return {"jobs": jobs, "count": len(jobs)}


@router.get("/operations/monitoring")
async def operations_monitoring(
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    settings = get_settings()
    dependencies = await _dependency_diagnostics()
    providers = provider_status(settings)
    return monitoring_snapshot(
        dependencies=dependencies,
        providers=providers,
        jobs=await _job_queue(request).stats(),
        cache=await _shared_cache(request).health(),
        active_users=await _active_user_count(),
    )


@router.get("/operations/recovery/plan")
async def operations_recovery_plan(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    return recovery_plan(get_settings())


@router.get("/operations/integrity")
async def operations_integrity(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    return integrity_check(get_settings(), await _dependency_diagnostics())


@router.get("/operations/plugins")
async def operations_plugins(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    return plugin_manifest()


@router.get("/operations/benchmarks")
async def operations_benchmarks(
    request: Request,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    return {
        "benchmark_type": "live_runtime_snapshot",
        "monitoring": await operations_monitoring(request, role),
        "documented_results": "/docs/RELEASE_RC6.md",
    }


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


@router.get("/enterprise/intelligence-suite", response_model=EnterpriseIntelligenceResponse)
async def enterprise_intelligence_suite(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> EnterpriseIntelligenceResponse:
    require_enterprise_permission(role, "meetings:view")

    async def operation(repository: PostgresMeetingRepository) -> dict[str, object]:
        memory = await repository.executive_memory(limit=50)
        graph = await repository.knowledge_graph(limit=80)
        analytics = await repository.advanced_enterprise_analytics()
        collaboration = await repository.collaboration_presence(limit=12)
        observability = await repository.observability_snapshot()
        provider_snapshot = provider_status(get_settings())
        observability["provider_health"] = _provider_health_rows(provider_snapshot)
        observability["provider_cache"] = provider_snapshot.get("cache")
        return {
            "memory": memory,
            "knowledge_graph": graph,
            "analytics": analytics,
            "assistant_suggestions": build_intelligence_suggestions(
                memory,
                analytics,
                observability,
            ),
            "collaboration": collaboration,
            "observability": observability,
            "workflows": build_workflow_catalog(),
        }

    return EnterpriseIntelligenceResponse.model_validate(await with_repository(operation))


@router.get("/enterprise/executive-memory")
async def enterprise_executive_memory(
    executive_role: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "meetings:view")
    return await with_repository(
        lambda repository: repository.executive_memory(role=executive_role, limit=limit)
    )


@router.get("/enterprise/knowledge-graph")
async def enterprise_knowledge_graph(
    limit: int = Query(default=100, ge=10, le=200),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "meetings:view")
    return await with_repository(lambda repository: repository.knowledge_graph(limit=limit))


@router.get("/enterprise/advanced-analytics")
async def enterprise_advanced_analytics(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "meetings:view")
    return await with_repository(lambda repository: repository.advanced_enterprise_analytics())


@router.post("/enterprise/assistant", response_model=AssistantAnswerResponse)
async def enterprise_assistant(
    payload: AssistantQuestionRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> AssistantAnswerResponse:
    require_enterprise_permission(role, "meetings:view")
    answer = await with_repository(lambda repository: repository.assistant_answer(payload.question))
    return AssistantAnswerResponse.model_validate({"answer": answer})


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


@router.get("/search/global")
async def global_enterprise_search(
    q: str = Query(min_length=1, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "meetings:view")
    return await with_repository(
        lambda repository: repository.global_enterprise_search(q, limit=limit)
    )


@router.post("/documents/import", response_model=DocumentImportResponse)
async def import_enterprise_document(
    payload: DocumentImportRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> DocumentImportResponse:
    require_enterprise_permission(role, "reports:comment")
    try:
        document = await with_repository(
            lambda repository: repository.import_document(payload.model_dump(mode="json"))
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if document is None:
        raise HTTPException(status_code=404, detail="Linked meeting or analysis was not found.")
    return DocumentImportResponse.model_validate({"document": document})


@router.get("/collaboration/presence")
async def collaboration_presence(
    limit: int = Query(default=30, ge=1, le=100),
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "meetings:view")
    return await with_repository(lambda repository: repository.collaboration_presence(limit=limit))


@router.post("/workflows/run", response_model=WorkflowRunResponse)
async def run_enterprise_workflow(
    payload: WorkflowRunRequest,
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> WorkflowRunResponse:
    require_enterprise_permission(role, "tasks:manage")
    workflow = await with_repository(
        lambda repository: repository.run_workflow(payload.model_dump(mode="json"))
    )
    if workflow is None:
        raise HTTPException(status_code=404, detail="Linked meeting or analysis was not found.")
    return WorkflowRunResponse.model_validate({"workflow": workflow})


@router.get("/observability")
async def enterprise_observability(
    role: str | None = Header(default="Administrator", alias="X-Boardroom-Role"),
) -> dict[str, object]:
    require_enterprise_permission(role, "workspace:admin")
    snapshot = await with_repository(lambda repository: repository.observability_snapshot())
    provider_snapshot = provider_status(get_settings())
    snapshot["provider_health"] = _provider_health_rows(provider_snapshot)
    snapshot["provider_cache"] = provider_snapshot.get("cache")
    snapshot["provider_modes"] = provider_snapshot.get("modes", [])
    return snapshot


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


def _ensure_auth_mode_enabled(payload: AuthSessionRequest, settings: object) -> None:
    if payload.mode == "email":
        if not getattr(settings, "auth_email_enabled", True):
            raise HTTPException(status_code=403, detail="Email login is disabled.")
        if not payload.email or "@" not in payload.email:
            raise HTTPException(status_code=422, detail="A valid email address is required.")
    if payload.mode == "demo" and not getattr(settings, "auth_demo_enabled", True):
        raise HTTPException(status_code=403, detail="Demo account login is disabled.")
    if payload.mode == "guest" and not getattr(settings, "auth_guest_enabled", True):
        raise HTTPException(status_code=403, detail="Guest mode is disabled.")


def _session_token_from_request(request: Request, cookie_name: str) -> str | None:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return request.cookies.get(cookie_name)


def _shared_cache(request: Request) -> SharedCache:
    cache = getattr(request.app.state, "shared_cache", None)
    return cache if isinstance(cache, SharedCache) else SharedCache(get_settings())


def _job_queue(request: Request) -> JobQueue:
    queue = getattr(request.app.state, "job_queue", None)
    return queue if isinstance(queue, JobQueue) else JobQueue(get_settings())


def _schedule_store(request: Request) -> ScheduleStore:
    store = getattr(request.app.state, "schedule_store", None)
    if isinstance(store, ScheduleStore):
        return store
    return ScheduleStore(_job_queue(request))


async def _active_user_count() -> int:
    try:
        dashboard_payload = await with_repository(
            lambda repository: repository.enterprise_dashboard()
        )
    except HTTPException:
        return 0
    users = dashboard_payload.get("users", [])
    return len(users) if isinstance(users, list) else 0


async def _dependency_diagnostics() -> dict[str, object]:
    settings = get_settings()
    checks = [
        await _database_check(),
        await _redis_check(settings.redis_url),
        await _qdrant_check(settings.qdrant_url),
    ]
    status = "ok" if all(item["status"] == "ok" for item in checks) else "degraded"
    return {"status": status, "checks": checks}


async def _database_check() -> dict[str, object]:
    try:
        async with AsyncSessionLocal() as session:
            await asyncio.wait_for(session.execute(text("select 1")), timeout=3)
        return {"name": "postgres", "status": "ok"}
    except Exception as exc:
        logger.warning("diagnostic_database_failed", error_type=type(exc).__name__)
        return {"name": "postgres", "status": "degraded", "error": type(exc).__name__}


async def _redis_check(redis_url: str) -> dict[str, object]:
    if not redis_url:
        return {"name": "redis", "status": "missing"}
    client = redis.from_url(redis_url)
    try:
        await asyncio.wait_for(client.ping(), timeout=2)
        return {"name": "redis", "status": "ok"}
    except Exception as exc:
        logger.warning("diagnostic_redis_failed", error_type=type(exc).__name__)
        return {"name": "redis", "status": "degraded", "error": type(exc).__name__}
    finally:
        await client.aclose()


async def _qdrant_check(qdrant_url: str) -> dict[str, object]:
    if not qdrant_url:
        return {"name": "qdrant", "status": "missing"}
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{qdrant_url.rstrip('/')}/readyz")
        return {
            "name": "qdrant",
            "status": "ok" if response.status_code < 500 else "degraded",
            "status_code": response.status_code,
        }
    except Exception as exc:
        logger.warning("diagnostic_qdrant_failed", error_type=type(exc).__name__)
        return {"name": "qdrant", "status": "degraded", "error": type(exc).__name__}


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


@v2_router.get("/status")
async def v2_status() -> dict[str, object]:
    return {
        "status": "preview",
        "current_stable_version": "v1",
        "supported_versions": ["v1", "v2-preview"],
        "backward_compatibility": "v1 endpoints remain unchanged",
        "deprecation": {"v1": None},
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
