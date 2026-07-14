from __future__ import annotations

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_log_middleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    logger = structlog.get_logger("boardroom.startup")
    app = FastAPI(
        title="Boardroom AI API",
        version="1.0.0-rc.1",
        description="Executive board orchestration API for founders.",
    )
    app.middleware("http")(request_log_middleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.app_env}

    app.include_router(api_router)
    logger.info(
        "app_configured",
        environment=settings.app_env,
        ai_provider=settings.ai_provider,
        business_data_mode=settings.business_data_mode,
        maps_provider=settings.maps_provider,
    )
    return app


app = create_app()
