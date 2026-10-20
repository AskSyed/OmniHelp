"""
Query response cache: Redis when configured, in-process otherwise

Cache-aside: the endpoint checks the cache, calls the workflow on a miss, then stores the
result. Cache failures are logged and treated as misses so Redis can never take the API down.
"""
import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Protocol

from loguru import logger
from redis.exceptions import RedisError

from app.core.config import settings
from app.db.redis import get_redis

# Bump when prompts or the response shape change, so stale answers are never served
CACHE_VERSION = "v1"


class Cache(Protocol):
    """Minimal async key/value cache interface"""

    async def get(self, key: str) -> Optional[str]: ...

    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...


class InMemoryCache:
    """Per-process LRU cache with TTL. Replicas do not share it."""

    def __init__(self, max_items: int = 1024):
        self._items: "OrderedDict[str, tuple[float, str]]" = OrderedDict()
        self._max_items = max_items

    async def get(self, key: str) -> Optional[str]:
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time.monotonic():
            del self._items[key]
            return None
        self._items.move_to_end(key)
        return value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._items[key] = (time.monotonic() + ttl_seconds, value)
        self._items.move_to_end(key)
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)


class RedisCache:
    """Cache shared by every replica"""

    def __init__(self, client):
        self._client = client

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self._client.get(key)
        except RedisError as e:
            logger.warning(f"Cache read failed, treating as miss: {e}")
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            await self._client.set(key, value, ex=ttl_seconds)
        except RedisError as e:
            logger.warning(f"Cache write failed, skipping: {e}")


_local_cache = InMemoryCache()


def get_cache() -> Cache:
    """FastAPI dependency: the configured cache backend"""
    client = get_redis()
    return RedisCache(client) if client is not None else _local_cache


def query_cache_key(query: str, n_results: int, filters: Optional[Dict[str, Any]]) -> str:
    """
    Build a cache key for a query

    Normalizes case and whitespace so trivial variations share an entry. The corpus is
    shared by all users today; once documents have per-user permissions, the caller's
    entitlements must become part of the key.
    """
    payload = json.dumps(
        {
            "query": " ".join(query.lower().split()),
            "n_results": n_results,
            "filters": filters or {},
            "model": settings.OPENAI_MODEL,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"omnihelp:query:{CACHE_VERSION}:{digest}"


def is_cacheable(result: Dict[str, Any]) -> bool:
    """Only cache successful answers built from documents, never live order data"""
    metadata = result.get("metadata") or {}
    return (
        bool(result.get("answer"))
        and not metadata.get("error")
        and metadata.get("intent") != "order_management"
    )
