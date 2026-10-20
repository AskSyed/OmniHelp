"""
OpenTelemetry tracing setup and per-request context middleware
"""
import time
import uuid
from typing import Optional

from loguru import logger
from opentelemetry import propagate, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

from app.core.config import settings

tracer = trace.get_tracer("omnihelp")


def setup_tracing() -> TracerProvider:
    """
    Install the global tracer provider

    Exports over OTLP/HTTP when OTEL_EXPORTER_OTLP_ENDPOINT is set (an OpenTelemetry
    Collector, which can forward to Splunk, Dynatrace or Jaeger), else to the console if
    OTEL_CONSOLE_EXPORT is on. With neither, spans are created but not exported.
    """
    provider = TracerProvider(resource=Resource.create({"service.name": settings.OTEL_SERVICE_NAME}))

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/") + "/v1/traces"
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        logger.info(f"Exporting traces to {endpoint}")
    elif settings.OTEL_CONSOLE_EXPORT:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("Exporting traces to console")

    trace.set_tracer_provider(provider)
    return provider


class RequestContextMiddleware:
    """
    Pure ASGI middleware that, for every HTTP request:
    - continues the caller's trace (W3C traceparent header) or starts a new one
    - records a SERVER span named after the route template, not the raw path
    - tags every log line with request_id and trace_id
    - echoes X-Request-ID and X-Trace-ID response headers

    Pure ASGI rather than BaseHTTPMiddleware so streaming responses pass straight through
    and the span covers the whole stream.
    """

    def __init__(self, app, tracer_provider: Optional[TracerProvider] = None):
        self.app = app
        self.tracer = tracer_provider.get_tracer("omnihelp") if tracer_provider else tracer

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope["headers"]}
        request_id = headers.get("x-request-id") or uuid.uuid4().hex
        method = scope["method"]
        parent_context = propagate.extract(headers)

        with self.tracer.start_as_current_span(
            f"{method} {scope['path']}", context=parent_context, kind=SpanKind.SERVER
        ) as span:
            span_context = span.get_span_context()
            trace_id = format(span_context.trace_id, "032x") if span_context.is_valid else "-"
            span.set_attribute("http.request.method", method)
            span.set_attribute("url.path", scope["path"])
            span.set_attribute("omnihelp.request_id", request_id)
            started = time.perf_counter()
            status_code = 500

            async def send_with_context(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    message["headers"] = [
                        *message.get("headers", []),
                        (b"x-request-id", request_id.encode()),
                        (b"x-trace-id", trace_id.encode()),
                    ]
                await send(message)

            with logger.contextualize(request_id=request_id, trace_id=trace_id):
                try:
                    await self.app(scope, receive, send_with_context)
                finally:
                    route = scope.get("route")
                    if route is not None:
                        span.update_name(f"{method} {route.path}")
                        span.set_attribute("http.route", route.path)
                    span.set_attribute("http.response.status_code", status_code)
                    if status_code >= 500:
                        span.set_status(Status(StatusCode.ERROR))
                    elapsed_ms = (time.perf_counter() - started) * 1000
                    logger.info(f"{method} {scope['path']} -> {status_code} in {elapsed_ms:.1f}ms")
