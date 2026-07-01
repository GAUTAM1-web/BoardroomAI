from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError

from app.domain.boardroom.export import report_to_markdown, report_to_pdf
from app.domain.boardroom.ideas import generate_startup_ideas
from app.domain.boardroom.orchestrator import BoardMeetingOrchestrator
from app.domain.boardroom.roles import EXECUTIVE_PROFILES
from app.domain.boardroom.streaming import LiveBoardMeetingOrchestrator
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

router = APIRouter(prefix="/api/v1", tags=["boardroom"])


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
async def create_board_meeting(payload: StartupBriefRequest) -> BoardMeetingResponse:
    brief = payload.to_domain()
    orchestrator = BoardMeetingOrchestrator(provider=LocalExecutiveIntelligenceProvider())
    result = orchestrator.run(brief)
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        await repository.persist_completed_result(brief, result)
    return BoardMeetingResponse.model_validate(result.to_dict())


@router.post("/startup-ideas/generate", response_model=StartupIdeasResponse)
async def generate_ideas(payload: StartupIdeaGenerationRequest) -> StartupIdeasResponse:
    ideas = generate_startup_ideas(payload.to_domain())
    return StartupIdeasResponse.model_validate({"ideas": [idea.to_dict() for idea in ideas]})


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard() -> DashboardResponse:
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        return DashboardResponse.model_validate(await repository.dashboard_snapshot())


@router.get("/board-meetings", response_model=MeetingHistoryResponse)
async def list_board_meetings(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=30, ge=1, le=100),
    favorite_only: bool = Query(default=False),
) -> MeetingHistoryResponse:
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        meetings = await repository.list_meetings(q, limit=limit, favorite_only=favorite_only)
        return MeetingHistoryResponse.model_validate({"meetings": meetings})


@router.get("/board-meetings/{meeting_id}", response_model=BoardMeetingDetailResponse)
async def get_board_meeting(meeting_id: UUID) -> BoardMeetingDetailResponse:
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        meeting = await repository.get_meeting_detail(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return BoardMeetingDetailResponse.model_validate(meeting)


@router.patch("/board-meetings/{meeting_id}/favorite", response_model=FavoriteMeetingResponse)
async def favorite_board_meeting(
    meeting_id: UUID,
    payload: FavoriteMeetingRequest,
) -> FavoriteMeetingResponse:
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        favorite = await repository.set_favorite(meeting_id, payload.is_favorite)
        if favorite is None:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return FavoriteMeetingResponse.model_validate(favorite)


@router.delete("/board-meetings/{meeting_id}", status_code=204)
async def delete_board_meeting(meeting_id: UUID) -> Response:
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        deleted = await repository.delete_meeting(meeting_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Meeting not found")
    return Response(status_code=204)


@router.get("/search", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=10, ge=1, le=30),
) -> GlobalSearchResponse:
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        return GlobalSearchResponse.model_validate(await repository.global_search(q, limit=limit))


@router.get("/reports/{meeting_id}/export")
async def export_report(
    meeting_id: UUID,
    format: Literal["json", "markdown", "pdf"] = Query(default="pdf"),
) -> Response:
    async with AsyncSessionLocal() as session:
        repository = PostgresMeetingRepository(session)
        meeting = await repository.get_meeting_detail(meeting_id)
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
        await websocket.send_json(
            {
                "event_type": "error",
                "payload": {
                    "message": "Live board meeting failed.",
                    "details": str(exc),
                },
            }
        )
        await websocket.close(code=1011)
