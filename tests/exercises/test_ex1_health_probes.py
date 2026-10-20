"""
EXERCISE 1 - Liveness and readiness probes (about 15 min)

Today GET /health returns HTTP 200 even when it reports "unhealthy", so a load balancer or
Kubernetes would keep sending traffic to a broken pod.

Add to app/main.py:
- GET /health/live  -> 200 {"status": "alive"} whenever the process can serve requests.
                       Must NOT call ChromaDB or MCP (a slow dependency must not get the pod killed).
- GET /health/ready -> 200 when ChromaDB answers and (if MCP_SERVER_ENABLED) MCP is connected;
                       otherwise 503 with a body saying which check failed.

Run: cd backend && python -m pytest ../tests/exercises/test_ex1_health_probes.py -q
"""
import pytest
from fastapi.testclient import TestClient

import app.db.chroma as chroma
from app.core.config import settings
from app.main import app
from app.services.mcp_client_service import MCPClientService

client = TestClient(app)


class HealthyCollection:
    def count(self):
        return 3


class BrokenCollection:
    def count(self):
        raise RuntimeError("chroma is down")


@pytest.fixture
def mcp_disabled(monkeypatch):
    monkeypatch.setattr(settings, "MCP_SERVER_ENABLED", False)


def test_live_is_200_even_when_dependencies_are_down(monkeypatch):
    monkeypatch.setattr(chroma, "_collection", BrokenCollection())
    response = client.get("/health/live")
    assert response.status_code == 200


def test_ready_is_200_when_dependencies_are_up(monkeypatch, mcp_disabled):
    monkeypatch.setattr(chroma, "_collection", HealthyCollection())
    response = client.get("/health/ready")
    assert response.status_code == 200


def test_ready_is_503_when_chroma_is_down(monkeypatch, mcp_disabled):
    monkeypatch.setattr(chroma, "_collection", BrokenCollection())
    response = client.get("/health/ready")
    assert response.status_code == 503


def test_ready_is_503_when_mcp_is_disconnected(monkeypatch):
    async def disconnected(self):
        return False

    monkeypatch.setattr(settings, "MCP_SERVER_ENABLED", True)
    monkeypatch.setattr(chroma, "_collection", HealthyCollection())
    monkeypatch.setattr(MCPClientService, "check_connection", disconnected)
    response = client.get("/health/ready")
    assert response.status_code == 503
