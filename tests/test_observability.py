"""
Tests for tracing and request-context middleware
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind

from app.core.observability import RequestContextMiddleware

TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
PARENT_SPAN_ID = "b7ad6b7169203331"


def make_app():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    app = FastAPI()

    @app.get("/orders/{order_id}")
    async def get_order(order_id: int):
        return {"id": order_id}

    app.add_middleware(RequestContextMiddleware, tracer_provider=provider)
    return TestClient(app), exporter


def test_continues_incoming_trace_and_names_span_by_route():
    client, exporter = make_app()

    response = client.get(
        "/orders/42",
        headers={"traceparent": f"00-{TRACE_ID}-{PARENT_SPAN_ID}-01", "X-Request-ID": "req-123"},
    )

    assert response.headers["x-request-id"] == "req-123"
    assert response.headers["x-trace-id"] == TRACE_ID
    [span] = exporter.get_finished_spans()
    assert span.name == "GET /orders/{order_id}"  # route template, not /orders/42
    assert span.kind == SpanKind.SERVER
    assert format(span.parent.span_id, "016x") == PARENT_SPAN_ID
    assert span.attributes["http.response.status_code"] == 200


def test_generates_request_id_and_new_trace_when_absent():
    client, exporter = make_app()

    response = client.get("/orders/1")

    assert len(response.headers["x-request-id"]) == 32
    [span] = exporter.get_finished_spans()
    assert span.parent is None
    assert format(span.context.trace_id, "032x") == response.headers["x-trace-id"]
