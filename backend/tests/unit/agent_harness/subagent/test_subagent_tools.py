"""
File: backend/tests/unit/agent_harness/subagent/test_subagent_tools.py
Purpose: Unit tests for make_task_spawn_tool + make_handoff_tool factories (US-5).
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-5

Created: 2026-05-04 (Sprint 54.2)
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    StopReason,
    TokenUsage,
    ToolSpec,
)
from agent_harness.subagent import (
    DefaultSubagentDispatcher,
    make_handoff_tool,
    make_task_spawn_tool,
)

from ._child_loop_helpers import make_child_loop_factory


def _mock_response(text: str) -> ChatResponse:
    return ChatResponse(
        model="mock-gpt",
        content=text,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


# === make_task_spawn_tool ====================================================


@pytest.mark.asyncio
async def test_task_spawn_tool_returns_toolspec_and_handler() -> None:
    """Factory returns ToolSpec with task+mode schema and a callable handler."""
    chat = MockChatClient(responses=[_mock_response("ok")])
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)
    tool_spec, handler = make_task_spawn_tool(dispatcher=dispatcher, parent_session_id=uuid4())
    assert isinstance(tool_spec, ToolSpec)
    assert tool_spec.name == "task_spawn"
    assert "task" in tool_spec.input_schema["properties"]
    assert "mode" in tool_spec.input_schema["properties"]
    assert tool_spec.input_schema["properties"]["mode"]["enum"] == ["fork", "teammate"]
    assert tool_spec.input_schema["required"] == ["task"]
    assert callable(handler)


@pytest.mark.asyncio
async def test_task_spawn_handler_fork_returns_summary() -> None:
    """Handler with mode='fork' invokes dispatcher.spawn(FORK) and returns summary."""
    chat = MockChatClient(responses=[_mock_response("Fork result text")])
    dispatcher = DefaultSubagentDispatcher(
        chat_client=chat, child_loop_factory=make_child_loop_factory(chat)
    )
    _, handler = make_task_spawn_tool(dispatcher=dispatcher, parent_session_id=uuid4())
    result = await handler({"task": "find facts", "mode": "fork"})
    assert result["success"] is True
    assert "Fork result text" in result["summary"]
    assert "subagent_id" in result


@pytest.mark.asyncio
async def test_task_spawn_handler_missing_task_returns_error() -> None:
    """Handler with empty task → success=False; no LLM call."""
    chat = MockChatClient(responses=[_mock_response("never called")])
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)
    _, handler = make_task_spawn_tool(dispatcher=dispatcher, parent_session_id=uuid4())
    result = await handler({"task": ""})
    assert result["success"] is False
    assert result["error"] == "missing_task"
    assert chat.chat_call_count == 0


@pytest.mark.asyncio
async def test_task_spawn_handler_unknown_mode_rejected() -> None:
    """Handler with mode='handoff' (not in fork/teammate) → success=False."""
    chat = MockChatClient(responses=[_mock_response("never called")])
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)
    _, handler = make_task_spawn_tool(dispatcher=dispatcher, parent_session_id=uuid4())
    result = await handler({"task": "x", "mode": "handoff"})
    assert result["success"] is False
    assert "fork/teammate only" in result["error"] or "unknown_mode" in result["error"]


# === make_handoff_tool =======================================================


@pytest.mark.asyncio
async def test_handoff_tool_returns_toolspec_and_handler() -> None:
    """Factory returns ToolSpec with target_agent+context schema and handler."""
    chat = MockChatClient()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)
    tool_spec, handler = make_handoff_tool(dispatcher=dispatcher)
    assert isinstance(tool_spec, ToolSpec)
    assert tool_spec.name == "handoff"
    assert "target_agent" in tool_spec.input_schema["properties"]
    assert "context" in tool_spec.input_schema["properties"]
    assert tool_spec.input_schema["required"] == ["target_agent"]
    assert callable(handler)


@pytest.mark.asyncio
async def test_handoff_tool_handler_returns_new_session_id() -> None:
    """Handler invokes dispatcher.handoff() → returns handoff_initiated=True + UUID."""
    chat = MockChatClient()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)
    _, handler = make_handoff_tool(dispatcher=dispatcher)
    result = await handler({"target_agent": "expert", "context": {"k": "v"}})
    assert result["handoff_initiated"] is True
    assert result["target_agent"] == "expert"
    # Validate new_session_id parses as UUID
    UUID(result["new_session_id"])


@pytest.mark.asyncio
async def test_handoff_tool_handler_missing_target_returns_error() -> None:
    """Handler without target_agent → handoff_initiated=False."""
    chat = MockChatClient()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)
    _, handler = make_handoff_tool(dispatcher=dispatcher)
    result = await handler({"context": {}})
    assert result["handoff_initiated"] is False
    assert result["error"] == "missing_target_agent"
