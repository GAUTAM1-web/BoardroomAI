from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.domain.boardroom.orchestrator import BoardMeetingOrchestrator
from app.domain.boardroom.roles import EXECUTIVE_PROFILES
from app.domain.boardroom.streaming import LiveBoardMeetingOrchestrator
from app.infrastructure.ai.local_provider import LocalExecutiveIntelligenceProvider
from app.infrastructure.database.repositories import PostgresMeetingRepository
from app.infrastructure.database.session import AsyncSessionLocal
from app.schemas.boardroom import (
    BoardMeetingResponse,
    ExecutiveCatalogResponse,
    ExecutiveProfileResponse,
    StartupBriefRequest,
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
    orchestrator = BoardMeetingOrchestrator(provider=LocalExecutiveIntelligenceProvider())
    result = orchestrator.run(payload.to_domain())
    return BoardMeetingResponse.model_validate(result.to_dict())


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
            async for event in orchestrator.stream(payload.to_domain(), recorder=repository):
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
