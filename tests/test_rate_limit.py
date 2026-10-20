"""
Tests for rate limiting
"""
import fakeredis
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.config import settings
from app.core.rate_limit import InMemoryRateLimiter, RedisRateLimiter


def test_requests_over_limit_get_429(client, workflow_calls, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 2)

    first = client.post("/api/v1/query", json={"query": "one"})
    second = client.post("/api/v1/query", json={"query": "two"})
    third = client.post("/api/v1/query", json={"query": "three"})

    assert [first.status_code, second.status_code, third.status_code] == [200, 200, 429]
    assert first.headers["x-ratelimit-remaining"] == "1"
    assert int(third.headers["retry-after"]) > 0
    assert workflow_calls == ["one", "two"]  # the rejected request never reached the LLM


def test_zero_disables_rate_limiting(client, workflow_calls, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 0)
    statuses = {client.post("/api/v1/query", json={"query": f"q{i}"}).status_code for i in range(5)}
    assert statuses == {200}


@pytest.mark.asyncio
async def test_in_memory_limiter_counts_callers_separately():
    limiter = InMemoryRateLimiter()
    assert (await limiter.hit("alice", 1, 60)).allowed
    assert not (await limiter.hit("alice", 1, 60)).allowed
    assert (await limiter.hit("bob", 1, 60)).allowed


@pytest.mark.asyncio
async def test_redis_limit_is_shared_across_replicas():
    server = fakeredis.FakeServer()
    replica_a = RedisRateLimiter(fakeredis.FakeAsyncRedis(server=server, decode_responses=True))
    replica_b = RedisRateLimiter(fakeredis.FakeAsyncRedis(server=server, decode_responses=True))

    results = [
        await replica_a.hit("alice", 3, 60),
        await replica_b.hit("alice", 3, 60),
        await replica_a.hit("alice", 3, 60),
        await replica_b.hit("alice", 3, 60),
    ]

    assert [r.allowed for r in results] == [True, True, True, False]


@pytest.mark.asyncio
async def test_redis_limiter_sets_expiry():
    client = fakeredis.FakeAsyncRedis(decode_responses=True)
    await RedisRateLimiter(client).hit("alice", 3, 60)
    [key] = await client.keys("omnihelp:ratelimit:*")
    assert 0 < await client.ttl(key) <= 60


@pytest.mark.asyncio
async def test_redis_outage_fails_open():
    class DownRedis:
        def pipeline(self, transaction=True):
            raise RedisConnectionError("connection refused")

    result = await RedisRateLimiter(DownRedis()).hit("alice", 3, 60)
    assert result.allowed
