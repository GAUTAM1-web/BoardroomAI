from __future__ import annotations

import logging
import sys
import time
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response

from app.core.config import Settings
from app.core.monitoring import mark_request_started, record_request, record_request_exception


def configure_logging(settings: Settings) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


async def request_log_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    logger = structlog.get_logger("boardroom.request")
    started = time.perf_counter()
    mark_request_started()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        record_request_exception(duration_ms)
        logger.exception(
            "request_failed",
            method=request.method,
            path=request.url.path,
            action=f"{request.method} {request.url.path}",
            outcome="failure",
            actor=request.headers.get("X-Boardroom-Role", "anonymous"),
            ip=request.client.host if request.client else None,
            organization=request.headers.get("X-Boardroom-Organization", "default"),
            duration_ms=duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    record_request(response.status_code, duration_ms)
    outcome = "success" if response.status_code < 400 else "failure"
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        action=f"{request.method} {request.url.path}",
        outcome=outcome,
        actor=request.headers.get("X-Boardroom-Role", "anonymous"),
        ip=request.client.host if request.client else None,
        organization=request.headers.get("X-Boardroom-Organization", "default"),
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response
