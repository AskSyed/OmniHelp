"""
Tests for the SSE and WebSocket streaming endpoints
"""
import json
from types import SimpleNamespace

import pytest

from app.core.config import settings


class FakeStreamingLLM:
    async def astream(self, prompt):
        for text in ["Annual ", "leave ", "is 25 days."]:
            yield SimpleNamespace(content=text)


@pytest.fixture
def fake_pipeline(monkeypatch):
    def classify(state):
        state["intent"] = "document_search"
        return state

    def retrieve(state):
        state["context"] = "Employees get 25 days of annual leave."
        state["sources"] = ["handbook.pdf"]
        return state

    monkeypatch.setattr("app.agents.streaming.classify_query", classify)
    monkeypatch.setattr("app.agents.streaming.retrieve_context", retrieve)
    monkeypatch.setattr("app.agents.streaming.create_streaming_llm", FakeStreamingLLM)


def parse_sse(body: str) -> list:
    events = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((fields["event"], json.loads(fields["data"])))
    return events


def test_sse_streams_metadata_tokens_then_done(client, fake_pipeline):
    response = client.post("/api/v1/query/stream", json={"query": "How much leave do I get?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    assert events[0] == ("metadata", {"intent": "document_search", "sources": ["handbook.pdf"]})
    assert "".join(data["text"] for name, data in events if name == "token") == "Annual leave is 25 days."
    assert events[-1] == ("done", {})


def test_sse_reports_context_failure_as_error_event(client, fake_pipeline, monkeypatch):
    def failing_retrieve(state):
        state["error"] = "chroma unavailable"
        return state

    monkeypatch.setattr("app.agents.streaming.retrieve_context", failing_retrieve)
    events = parse_sse(client.post("/api/v1/query/stream", json={"query": "q"}).text)
    assert [name for name, _ in events] == ["error"]
    assert "chroma" not in events[0][1]["message"]  # internals are not leaked to the client


def test_websocket_streams_multiple_queries_on_one_connection(client, fake_pipeline):
    with client.websocket_connect("/api/v1/query/ws") as ws:
        for _ in range(2):
            ws.send_json({"query": "How much leave do I get?"})
            events = []
            while not events or events[-1]["event"] not in ("done", "error"):
                events.append(ws.receive_json())
            assert events[0]["event"] == "metadata"
            assert events[-1]["event"] == "done"


def test_websocket_rejects_missing_token_when_auth_enabled(client, fake_pipeline, monkeypatch):
    from pydantic import SecretStr
    from starlette.websockets import WebSocketDisconnect

    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "JWT_SECRET", SecretStr("test-secret"))
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/v1/query/ws") as ws:
            ws.receive_json()
    assert exc.value.code == 1008
