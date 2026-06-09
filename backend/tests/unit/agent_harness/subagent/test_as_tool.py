"""
File: backend/tests/unit/agent_harness/subagent/test_as_tool.py
Purpose: Unit tests for AsToolWrapper (wraps AgentSpec to ToolSpec + handler).
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-2

Created: 2026-05-04 (Sprint 54.2)
"""

from __future__ import annotations

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    AgentSpec,
    ChatResponse,
    StopReason,
    TokenUsage,
    ToolSpec,
)
from agent_harness.subagent import (
    AsToolWrapper,
    DefaultSubagentDispatcher,
    ForkExecutor,
)

from ._child_loop_helpers import make_child_loop_factory


def _mock_response(text: str) -> ChatResponse:
    return ChatResponse(
        model="mock-gpt",
        content=text,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


def test_as_tool_returns_toolspec_with_correct_schema() -> None:
    """wrap(spec) → ToolSpec with name=agent_<role> and 'task' string property."""
    chat = MockChatClient(responses=[_mock_response("ok")])
    wrapper = AsToolWrapper(
        fork_executor=ForkExecutor(child_loop_factory=make_child_loop_factory(chat))
    )
    spec = AgentSpec(role="researcher", prompt="You investigate facts.")
    tool_spec, handler = wrapper.wrap(spec)

    assert isinstance(tool_spec, ToolSpec)
    assert tool_spec.name == "agent_researcher"
    assert "researcher" in tool_spec.description
    # JSON Schema check
    assert tool_spec.input_schema["type"] == "object"
    assert "task" in tool_spec.input_schema["properties"]
    assert tool_spec.input_schema["properties"]["task"]["type"] == "string"
    assert tool_spec.input_schema["required"] == ["task"]
    # Handler is callable; smoke test only here (round-trip in next test)
    assert callable(handler)


@pytest.mark.asyncio
async def test_as_tool_handler_calls_fork_executor_returns_summary_dict() -> None:
    """Handler({"task": "..."}) → executes ForkExecutor → returns dict with success + summary."""
    chat = MockChatClient(responses=[_mock_response("Researcher found 3 facts.")])
    wrapper = AsToolWrapper(
        fork_executor=ForkExecutor(child_loop_factory=make_child_loop_factory(chat))
    )
    spec = AgentSpec(role="researcher", prompt="You investigate facts.")
    _, handler = wrapper.wrap(spec)

    result = await handler({"task": "Find X"})
    assert result["success"] is True
    assert "Researcher found 3 facts." in result["summary"]
    assert result["error"] is None
    assert "subagent_id" in result
    assert result["tokens_used"] == 15


@pytest.mark.asyncio
async def test_as_tool_handler_missing_task_returns_error() -> None:
    """Handler without 'task' arg → success=False, error='missing_task' (no LLM call)."""
    chat = MockChatClient(responses=[_mock_response("should not be called")])
    wrapper = AsToolWrapper(
        fork_executor=ForkExecutor(child_loop_factory=make_child_loop_factory(chat))
    )
    spec = AgentSpec(role="writer")
    _, handler = wrapper.wrap(spec)

    result = await handler({})  # No "task" key
    assert result["success"] is False
    assert result["error"] == "missing_task"
    assert chat.chat_call_count == 0  # ForkExecutor NOT called


def test_dispatcher_as_tool_factory_returns_pair() -> None:
    """dispatcher.as_tool_factory(spec) returns (ToolSpec, handler) tuple."""
    chat = MockChatClient(responses=[_mock_response("ok")])
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)
    spec = AgentSpec(role="critic")
    tool_spec, handler = dispatcher.as_tool_factory(spec)
    assert isinstance(tool_spec, ToolSpec)
    assert tool_spec.name == "agent_critic"
    assert callable(handler)
