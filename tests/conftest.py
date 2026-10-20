"""
Shared fixtures for API tests that must not call OpenAI, Redis or the MCP server
"""
import pytest
from fastapi.testclient import TestClient

from app.core.cache import InMemoryCache, get_cache
from app.core.rate_limit import InMemoryRateLimiter, get_rate_limiter
from app.main import app


@pytest.fixture
def client():
    """Test client with an isolated cache and rate limiter"""
    cache = InMemoryCache()
    app.dependency_overrides[get_cache] = lambda: cache
    limiter = InMemoryRateLimiter()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def workflow_calls(monkeypatch):
    """Replace the RAG workflow with a fake; returns the list of queries it received"""
    calls = []

    async def fake_process_query(query, n_results=5, filters=None):
        calls.append(query)
        intent = "order_management" if "order" in query.lower() else "document_search"
        return {
            "answer": f"Answer to: {query}",
            "sources": ["handbook.pdf"],
            "retrieved_chunks": [],
            "metadata": {"intent": intent},
        }

    monkeypatch.setattr("app.api.v1.query.process_query", fake_process_query)
    return calls
