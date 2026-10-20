"""
Tests for the query response cache
"""
import fakeredis
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.cache import InMemoryCache, RedisCache, is_cacheable, query_cache_key


def test_repeated_query_is_served_from_cache(client, workflow_calls):
    first = client.post("/api/v1/query", json={"query": "What is the leave policy?"})
    second = client.post("/api/v1/query", json={"query": "  what is the LEAVE policy? "})

    assert workflow_calls == ["What is the leave policy?"]
    assert second.json()["answer"] == first.json()["answer"]
    assert second.json()["metadata"]["cache"] == "hit"
    assert "cache" not in first.json()["metadata"]


def test_order_queries_are_never_cached(client, workflow_calls):
    client.post("/api/v1/query", json={"query": "Status of order 7?"})
    client.post("/api/v1/query", json={"query": "Status of order 7?"})
    assert len(workflow_calls) == 2


def test_cache_key_depends_on_parameters():
    base = query_cache_key("leave policy", 5, None)
    assert query_cache_key("Leave   POLICY", 5, {}) == base
    assert query_cache_key("leave policy", 3, None) != base
    assert query_cache_key("leave policy", 5, {"source": "hr.pdf"}) != base


def test_errors_are_not_cacheable():
    assert is_cacheable({"answer": "ok", "metadata": {"intent": "document_search"}})
    assert not is_cacheable({"answer": "sorry", "metadata": {"error": "timeout"}})
    assert not is_cacheable({"answer": "", "metadata": {}})


@pytest.mark.asyncio
async def test_in_memory_cache_expires_and_evicts():
    cache = InMemoryCache(max_items=2)
    await cache.set("expired", "x", ttl_seconds=-1)
    assert await cache.get("expired") is None

    await cache.set("a", "1", 60)
    await cache.set("b", "2", 60)
    await cache.get("a")  # a is now most recently used
    await cache.set("c", "3", 60)
    assert await cache.get("b") is None
    assert await cache.get("a") == "1"


@pytest.mark.asyncio
async def test_redis_cache_round_trip_with_ttl():
    client = fakeredis.FakeAsyncRedis(decode_responses=True)
    cache = RedisCache(client)
    await cache.set("k", "v", 30)
    assert await cache.get("k") == "v"
    assert 0 < await client.ttl("k") <= 30


@pytest.mark.asyncio
async def test_redis_outage_is_a_cache_miss():
    class DownRedis:
        async def get(self, key):
            raise RedisConnectionError("connection refused")

        async def set(self, key, value, ex=None):
            raise RedisConnectionError("connection refused")

    cache = RedisCache(DownRedis())
    await cache.set("k", "v", 30)
    assert await cache.get("k") is None
