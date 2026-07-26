from __future__ import annotations

import time

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.deployment import detect_deployment_target, effective_cors_origins
from app.core.logging import configure_logging, request_log_middleware

_RATE_LIMIT_BUCKETS: dict[str, tuple[int, int]] = {}


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
        allow_origins=effective_cors_origins(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        if _rate_limited(request, settings.rate_limit_per_minute):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please retry shortly."},
            )
        response = await call_next(request)
        if settings.security_headers_enabled:
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
            response.headers.setdefault(
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=(self)",
            )
        return response

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.app_env}

    @app.get("/health/live", tags=["system"])
    async def health_live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["system"])
    async def health_ready() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.app_env,
            "deployment_target": detect_deployment_target(settings),
        }

    app.include_router(api_router)
    logger.info(
        "app_configured",
        environment=settings.app_env,
        ai_provider=settings.ai_provider,
        business_data_mode=settings.business_data_mode,
        maps_provider=settings.maps_provider,
        deployment_target=detect_deployment_target(settings),
    )
    return app


app = create_app()


def _rate_limited(request: Request, limit_per_minute: int) -> bool:
    if limit_per_minute <= 0 or request.url.path.startswith("/health"):
        return False
    now_minute = int(time.time() // 60)
    key = f"{request.client.host if request.client else 'unknown'}:{now_minute}"
    _, count = _RATE_LIMIT_BUCKETS.get(key, (now_minute, 0))
    _RATE_LIMIT_BUCKETS[key] = (now_minute, count + 1)
    if len(_RATE_LIMIT_BUCKETS) > 2048:
        stale = [item for item, (minute, _) in _RATE_LIMIT_BUCKETS.items() if minute < now_minute]
        for item in stale[:512]:
            _RATE_LIMIT_BUCKETS.pop(item, None)
    return count + 1 > limit_per_minute
