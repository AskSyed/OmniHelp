"""
EXERCISE 2 - Stop blocking the event loop (about 10 min)

determine_mcp_tool() in app/agents/sql_agent.py is `async def` but calls the synchronous
llm.invoke(). While the LLM is thinking (often 1-3 s), the whole event loop is frozen: no
other request on this worker makes progress, including health checks.

Fix it so the test below passes. There are two reasonable fixes; be ready to explain
which you chose and why.

Run: cd backend && python -m pytest ../tests/exercises/test_ex2_event_loop.py -q
"""
import asyncio
import time
from types import SimpleNamespace

import pytest

from app.agents.sql_agent import determine_mcp_tool

LLM_REPLY = '{"tool": "get_order_status", "arguments": {"order_id": 1}}'


class SlowLLM:
    """Takes 300 ms to answer, like a real model call"""

    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt):
        time.sleep(0.3)
        return SimpleNamespace(content=LLM_REPLY)

    async def ainvoke(self, prompt):
        await asyncio.sleep(0.3)
        return SimpleNamespace(content=LLM_REPLY)


@pytest.mark.asyncio
async def test_other_tasks_keep_running_while_llm_is_called(monkeypatch):
    monkeypatch.setattr("app.agents.sql_agent.ChatOpenAI", SlowLLM)
    ticks = 0

    async def heartbeat():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.01)
            ticks += 1

    heartbeat_task = asyncio.create_task(heartbeat())
    tool, args = await determine_mcp_tool("What is the status of order 1?")
    heartbeat_task.cancel()

    assert (tool, args) == ("get_order_status", {"order_id": 1})
    # ~30 ticks expected if the loop stays free; 0-1 if it was blocked
    assert ticks >= 10, f"event loop was blocked: only {ticks} heartbeat ticks in 300 ms"
