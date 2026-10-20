"""
Fixed-window rate limiting per caller

Each caller gets RATE_LIMIT_PER_MINUTE requests per clock minute. The Redis backend makes
the limit global across replicas; the in-memory backend only limits a single process.
"""
import time
from dataclasses import dataclass
from typing import Dict, Protocol, Tuple

from fastapi import Depends, HTTPException, Request, Response, status
from loguru import logger
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.security import Principal, get_current_principal
from app.db.redis import get_redis

WINDOW_SECONDS = 60


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_after: int  # seconds until the window resets


class RateLimiter(Protocol):
    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult: ...


def _window(window_seconds: int) -> Tuple[int, int]:
    """Return (window number, seconds until it ends)"""
    now = int(time.time())
    return now // window_seconds, window_seconds - now % window_seconds


class InMemoryRateLimiter:
    """Per-process counters. Fine for one replica; N replicas allow N x the limit."""

    def __init__(self, max_keys: int = 10_000):
        self._counts: Dict[str, Tuple[int, int]] = {}  # key -> (window, count)
        self._max_keys = max_keys

    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        window, reset_after = _window(window_seconds)
        counted_window, count = self._counts.get(key, (window, 0))
        count = count + 1 if counted_window == window else 1
        self._counts[key] = (window, count)

        if len(self._counts) > self._max_keys:
            # Drop callers that have not been seen in the current window
            self._counts = {k: v for k, v in self._counts.items() if v[0] == window}

        return RateLimitResult(count <= limit, max(0, limit - count), reset_after)


class RedisRateLimiter:
    """Counters shared by every replica"""

    def __init__(self, client):
        self._client = client

    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        window, reset_after = _window(window_seconds)
        redis_key = f"omnihelp:ratelimit:{key}:{window}"
        try:
            # MULTI/EXEC so the counter and its expiry are set together
            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incr(redis_key)
                pipe.expire(redis_key, window_seconds)
                count, _ = await pipe.execute()
        except RedisError as e:
            # Fail open: an outage in the limiter should not become an outage of the API
            logger.warning(f"Rate limiter unavailable, allowing request: {e}")
            return RateLimitResult(True, limit, reset_after)

        return RateLimitResult(count <= limit, max(0, limit - count), reset_after)


_local_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> RateLimiter:
    """FastAPI dependency: the configured rate limiter backend"""
    client = get_redis()
    return RedisRateLimiter(client) if client is not None else _local_limiter


async def enforce_rate_limit(
    request: Request,
    response: Response,
    principal: Principal = Depends(get_current_principal),
    limiter: RateLimiter = Depends(get_rate_limiter),
):
    """
    FastAPI dependency: reject the request with 429 once the caller is over the limit

    Callers are identified by token subject, or by client IP when auth is off.
    """
    limit = settings.RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return

    if principal.authenticated:
        caller = f"sub:{principal.subject}"
    else:
        caller = f"ip:{request.client.host if request.client else 'unknown'}"

    result = await limiter.hit(caller, limit, WINDOW_SECONDS)

    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_after),
    }
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={**headers, "Retry-After": str(result.reset_after)},
        )
    response.headers.update(headers)
