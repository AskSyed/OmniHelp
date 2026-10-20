"""
Streaming query pipeline - yields answer tokens as the LLM produces them

Transport-agnostic: yields (event, data) pairs that the SSE and WebSocket endpoints format
for their own protocol. Runs the same classify -> retrieve/SQL steps as the LangGraph
workflow, then streams generation directly. The refinement step is skipped, because a
second LLM pass over the full answer cannot start until generation has finished.
"""
import asyncio
from typing import Any, AsyncIterator, Dict, Optional, Tuple

from langchain_openai import ChatOpenAI
from loguru import logger

from app.agents.generation_agent import NO_CONTEXT_ANSWER, build_generation_prompt
from app.agents.orchestrator import build_initial_state, route_query
from app.agents.query_agent import classify_query
from app.agents.retrieval_agent import retrieve_context
from app.agents.sql_agent import execute_sql_query
from app.core.config import settings
from app.core.observability import tracer

StreamEvent = Tuple[str, Dict[str, Any]]


def create_streaming_llm() -> ChatOpenAI:
    """Build the chat model used for streamed generation"""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        openai_api_key=settings.OPENAI_API_KEY,
        streaming=True,
    )


async def stream_query_events(
    query: str,
    filters: Optional[Dict[str, Any]] = None
) -> AsyncIterator[StreamEvent]:
    """
    Run a query and yield events: one "metadata", many "token", then "done" or "error"

    Args:
        query: User query string
        filters: Optional metadata filters
    """
    state = build_initial_state(query, filters)

    with tracer.start_as_current_span("rag.stream") as span:
        try:
            # classify_query and retrieve_context are blocking (sync LLM/HTTP calls):
            # run them in a worker thread so they don't stall the event loop
            state = await asyncio.to_thread(classify_query, state)
            if route_query(state) == "execute_sql":
                state = await execute_sql_query(state)
            else:
                state = await asyncio.to_thread(retrieve_context, state)
            span.set_attribute("rag.intent", state["intent"])

            if state.get("error"):
                logger.error(f"Context step failed: {state['error']}")
                yield "error", {"message": "Could not retrieve context for this query"}
                return

            yield "metadata", {"intent": state["intent"], "sources": state.get("sources", [])}

            context = state.get("context", "")
            if not context:
                yield "token", {"text": NO_CONTEXT_ANSWER}
                yield "done", {}
                return

            token_count = 0
            async for chunk in create_streaming_llm().astream(build_generation_prompt(query, context)):
                if chunk.content:
                    token_count += 1
                    yield "token", {"text": chunk.content}

            span.set_attribute("rag.stream_chunks", token_count)
            yield "done", {}

        except Exception as e:
            logger.exception(f"Streaming query failed: {e}")
            yield "error", {"message": "An error occurred while generating the answer"}
