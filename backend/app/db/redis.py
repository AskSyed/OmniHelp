"""
Shared async Redis client
"""
from typing import Optional
import redis.asyncio as redis
from loguru import logger
from app.core.config import settings


_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get the Redis client, or None when REDIS_URL is not configured"""
    global _client
    if _client is None and settings.REDIS_URL:
        # Short timeouts: a slow cache is worse than no cache
        _client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        logger.info("Redis client initialized")
    return _client


async def close_redis():
    """Close the Redis connection pool"""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
