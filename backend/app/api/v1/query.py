"""
Query API endpoints for RAG queries
"""
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import ValidationError

from app.agents.orchestrator import process_query
from app.agents.streaming import stream_query_events
from app.core.cache import Cache, get_cache, is_cacheable, query_cache_key
from app.core.config import settings
from app.core.rate_limit import WINDOW_SECONDS, enforce_rate_limit, get_rate_limiter
from app.core.security import ANONYMOUS, decode_access_token, require_scope
from app.models.query import QueryRequest, QueryResponse

router = APIRouter()

QUERY_SCOPE = "query:read"


@router.post(
    "",
    response_model=QueryResponse,
    dependencies=[Depends(require_scope(QUERY_SCOPE)), Depends(enforce_rate_limit)]
)
async def query_documents(request: QueryRequest, cache: Cache = Depends(get_cache)):
    """
    Process a RAG query through the complete workflow

    Args:
        request: Query request with query text and optional parameters
        cache: Response cache (injected)

    Returns:
        Query response with answer, sources, and metadata
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        logger.info(f"Processing query: {request.query[:100]}...")

        cache_key = query_cache_key(request.query, request.n_results, request.filters)
        if settings.QUERY_CACHE_TTL_SECONDS > 0:
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.info("Query cache hit")
                response = QueryResponse.model_validate_json(cached)
                response.metadata = {**(response.metadata or {}), "cache": "hit"}
                return response

        # Process query through RAG workflow
        result = await process_query(
            query=request.query,
            n_results=request.n_results,
            filters=request.filters
        )

        response = QueryResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            retrieved_chunks=result.get("retrieved_chunks", []),
            metadata=result.get("metadata", {})
        )

        if settings.QUERY_CACHE_TTL_SECONDS > 0 and is_cacheable(result):
            await cache.set(cache_key, response.model_dump_json(), settings.QUERY_CACHE_TTL_SECONDS)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def format_sse(event: str, data: dict) -> str:
    """Format one Server-Sent Events message"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def sse_stream(request: QueryRequest) -> AsyncIterator[str]:
    async for event, data in stream_query_events(request.query, request.filters):
        yield format_sse(event, data)


@router.post(
    "/stream",
    dependencies=[Depends(require_scope(QUERY_SCOPE)), Depends(enforce_rate_limit)]
)
async def stream_query(request: QueryRequest):
    """
    Stream an answer as Server-Sent Events

    Events: "metadata" (intent, sources), "token" (answer text), then "done" or "error".
    Try it with: curl -N -X POST localhost:8000/api/v1/query/stream \\
        -H 'Content-Type: application/json' -d '{"query": "..."}'
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    return StreamingResponse(
        sse_stream(request),
        media_type="text/event-stream",
        # Stop proxies (nginx, API gateways) from buffering the stream
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.websocket("/ws")
async def query_websocket(websocket: WebSocket):
    """
    Answer queries over a WebSocket, streaming the same events as /stream

    Client sends {"query": "..."}; server replies {"event": "...", ...data} per event.
    One connection can carry many queries. Auth is checked once, at connect.
    """
    principal = ANONYMOUS
    if settings.AUTH_ENABLED:
        authorization = websocket.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing bearer token")
            return
        try:
            principal = decode_access_token(authorization[7:])
        except HTTPException as e:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
            return
        if QUERY_SCOPE not in principal.scopes:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=f"Missing scope: {QUERY_SCOPE}")
            return

    await websocket.accept()
    limiter = get_rate_limiter()
    client_host = websocket.client.host if websocket.client else "unknown"
    caller = f"sub:{principal.subject}" if principal.authenticated else f"ip:{client_host}"

    try:
        while True:
            try:
                request = QueryRequest.model_validate(await websocket.receive_json())
            except (ValidationError, ValueError):
                request = None
            if request is None or not request.query.strip():
                await websocket.send_json({"event": "error", "message": "Expected {\"query\": \"...\"}"})
                continue

            if settings.RATE_LIMIT_PER_MINUTE > 0:
                result = await limiter.hit(caller, settings.RATE_LIMIT_PER_MINUTE, WINDOW_SECONDS)
                if not result.allowed:
                    await websocket.send_json({
                        "event": "error",
                        "message": "Rate limit exceeded",
                        "retry_after": result.reset_after
                    })
                    continue

            async for event, data in stream_query_events(request.query, request.filters):
                await websocket.send_json({"event": event, **data})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
