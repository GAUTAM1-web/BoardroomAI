from __future__ import annotations

import time
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.api.routes import v2_router
from app.core.cache import SharedCache
from app.core.config import get_settings
from app.core.deployment import (
    detect_deployment_target,
    effective_cors_origins,
    environment_diagnostics,
    is_production,
)
from app.core.jobs import JobQueue
from app.core.logging import configure_logging, request_log_middleware
from app.core.scheduler import ScheduleStore
from app.infrastructure.database.session import engine

_RATE_LIMIT_BUCKETS: dict[str, tuple[int, int]] = {}


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    logger = structlog.get_logger("boardroom.startup")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.shared_cache = SharedCache(settings)
        app.state.job_queue = JobQueue(settings)
        app.state.schedule_store = ScheduleStore(app.state.job_queue)
        app.state.startup_checks = {
            "environment": environment_diagnostics(settings),
            "cache": await app.state.shared_cache.health(),
            "jobs": await app.state.job_queue.health(),
        }
        logger.info(
            "startup_checks_completed",
            environment=app.state.startup_checks["environment"]["status"],
            cache=app.state.startup_checks["cache"]["status"],
            jobs=app.state.startup_checks["jobs"]["status"],
        )
        yield
        await app.state.shared_cache.close()
        await app.state.job_queue.close()
        await engine.dispose()

    app = FastAPI(
        title="Boardroom AI API",
        version="1.0.0-rc.1",
        description="Executive board orchestration API for founders.",
        lifespan=lifespan,
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
        if _csrf_blocked(request, settings):
            return JSONResponse(status_code=403, content={"detail": "CSRF check failed."})
        response = await call_next(request)
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response.headers.setdefault("X-Request-ID", request_id)
        response.headers.setdefault("X-Boardroom-API-Version", "v1")
        response.headers.setdefault("X-Boardroom-Supported-Versions", "v1, v2-preview")
        if settings.security_headers_enabled:
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
            response.headers.setdefault("Content-Security-Policy", settings.content_security_policy)
            response.headers.setdefault(
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=(self)",
            )
            if is_production(settings):
                response.headers.setdefault(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains",
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
            "api_versions": "v1,v2-preview",
        }

    app.include_router(api_router)
    app.include_router(v2_router)
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


def _csrf_blocked(request: Request, settings: object) -> bool:
    if not getattr(settings, "csrf_protection_enabled", False):
        return False
    if request.method.upper() in {"GET", "HEAD", "OPTIONS"}:
        return False
    cookie_name = getattr(settings, "session_cookie_name", "boardroom_session")
    if cookie_name not in request.cookies:
        return False
    origin = request.headers.get("origin") or request.headers.get("referer", "")
    if not origin:
        return True
    allowed = effective_cors_origins(settings)
    return not any(origin.rstrip("/").startswith(value.rstrip("/")) for value in allowed)
