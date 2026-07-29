from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import redis.asyncio as redis

from app.core.config import Settings, get_settings

_MEMORY_CACHE: dict[str, tuple[datetime, object]] = {}


class SharedCache:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: redis.Redis | None = None

    async def get_json(self, key: str) -> object | None:
        memory_value = _memory_get(key)
        if memory_value is not None:
            return memory_value
        client = self._redis_client()
        if client is None:
            return None
        try:
            raw_value = await client.get(_cache_key(key))
        except Exception:
            return None
        if raw_value is None:
            return None
        try:
            return json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            return None

    async def set_json(self, key: str, value: object, ttl_seconds: int | None = None) -> None:
        ttl = max(1, int(ttl_seconds or self.settings.shared_cache_ttl_seconds))
        _memory_set(key, value, ttl)
        client = self._redis_client()
        if client is None:
            return
        try:
            await client.set(_cache_key(key), json.dumps(value, default=str), ex=ttl)
        except Exception:
            return

    async def delete(self, key: str) -> None:
        _MEMORY_CACHE.pop(key, None)
        client = self._redis_client()
        if client is None:
            return
        try:
            await client.delete(_cache_key(key))
        except Exception:
            return

    async def health(self) -> dict[str, object]:
        client = self._redis_client()
        if client is None:
            return {"backend": "memory", "status": "ok", "keys": len(_MEMORY_CACHE)}
        try:
            await client.ping()
            return {"backend": "redis", "status": "ok", "memory_keys": len(_MEMORY_CACHE)}
        except Exception as exc:
            return {
                "backend": "memory",
                "status": "degraded",
                "error": type(exc).__name__,
                "keys": len(_MEMORY_CACHE),
            }

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _redis_client(self) -> redis.Redis | None:
        if self.settings.job_queue_backend.strip().lower() == "memory":
            return None
        if not self.settings.redis_url:
            return None
        if self._client is None:
            self._client = redis.from_url(self.settings.redis_url, decode_responses=True)
        return self._client


def session_cache_key(session_id: str) -> str:
    return f"session:{session_id}"


def _cache_key(key: str) -> str:
    return f"boardroomai:cache:{key}"


def _memory_get(key: str) -> object | None:
    item = _MEMORY_CACHE.get(key)
    if item is None:
        return None
    expires_at, value = item
    if expires_at <= datetime.now(UTC):
        _MEMORY_CACHE.pop(key, None)
        return None
    return value


def _memory_set(key: str, value: object, ttl_seconds: int) -> None:
    _MEMORY_CACHE[key] = (datetime.now(UTC) + timedelta(seconds=ttl_seconds), value)
    if len(_MEMORY_CACHE) > 4096:
        _purge_memory_cache()


def _purge_memory_cache() -> None:
    now = datetime.now(UTC)
    stale = [key for key, (expires_at, _value) in _MEMORY_CACHE.items() if expires_at <= now]
    for key in stale[:1024]:
        _MEMORY_CACHE.pop(key, None)
