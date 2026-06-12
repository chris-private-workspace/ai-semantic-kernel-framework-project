"""
File: backend/tests/unit/agent_harness/subagent/test_subagent_tools.py
Purpose: Unit tests for make_task_spawn_tool + make_handoff_spec factories (US-5).
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-5 → handoff block converted Sprint 57.107 (B3 spec-only)

Created: 2026-05-04 (Sprint 54.2)
Modified: 2026-06-12 (Sprint 57.107 — make_handoff_tool → make_handoff_spec)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    StopReason,
    SubagentBudget,
    TokenUsage,
    ToolSpec,
)
from agent_harness._contracts.errors import SubagentFailureEscalation
from agent_harness.subagent import (
    DefaultSubagentDispatcher,
    make_handoff_spec,
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


# === failure policies (Sprint 57.110 B4) =====================================


def test_failure_policy_rides_budget() -> None:
    """SubagentBudget defaults to fail_soft (today byte-identical) + carries overrides."""
    assert SubagentBudget().failure_policy == "fail_soft"
    assert SubagentBudget(failure_policy="fail_partial").failure_policy == "fail_partial"


def _failing_child_dispatcher() -> DefaultSubagentDispatcher:
    """A dispatcher whose FORK child produces no final answer → empty_response failure."""
    chat = MockChatClient(
        responses=[ChatResponse(model="mock-gpt", content="", stop_reason=StopReason.END_TURN)]
    )
    return DefaultSubagentDispatcher(
        chat_client=chat, child_loop_factory=make_child_loop_factory(chat)
    )


@pytest.mark.asyncio
async def test_task_spawn_fail_fast_raises_on_child_failure() -> None:
    """fail_fast + a failed child → SubagentFailureEscalation (FATAL — run ends, no re-spawn)."""
    _, handler = make_task_spawn_tool(
        dispatcher=_failing_child_dispatcher(),
        parent_session_id=uuid4(),
        failure_policy="fail_fast",
    )
    with pytest.raises(SubagentFailureEscalation) as excinfo:
        await handler({"task": "doomed work"})
    assert excinfo.value.child_error == "empty_response"


@pytest.mark.asyncio
async def test_task_spawn_fail_soft_default_returns_error_result() -> None:
    """The default (fail_soft) keeps today's behavior: error result, parent LLM continues."""
    _, handler = make_task_spawn_tool(
        dispatcher=_failing_child_dispatcher(), parent_session_id=uuid4()
    )
    result = await handler({"task": "doomed work"})
    assert result["success"] is False
    assert result["error"] == "empty_response"


@pytest.mark.asyncio
async def test_task_spawn_fail_fast_success_does_not_raise() -> None:
    """fail_fast only escalates FAILURES — a successful child returns normally."""
    chat = MockChatClient(responses=[_mock_response("fine work")])
    dispatcher = DefaultSubagentDispatcher(
        chat_client=chat, child_loop_factory=make_child_loop_factory(chat)
    )
    _, handler = make_task_spawn_tool(
        dispatcher=dispatcher, parent_session_id=uuid4(), failure_policy="fail_fast"
    )
    result = await handler({"task": "good work"})
    assert result["success"] is True
    assert "fine work" in result["summary"]


# === make_handoff_spec (Sprint 57.107 — converted from make_handoff_tool) ====


def test_handoff_spec_returns_toolspec_and_handler() -> None:
    """Factory returns the spec-only ToolSpec with target_agent+reason schema."""
    tool_spec, handler = make_handoff_spec(suggested_targets=["researcher"])
    assert isinstance(tool_spec, ToolSpec)
    assert tool_spec.name == "handoff"
    assert "target_agent" in tool_spec.input_schema["properties"]
    assert "reason" in tool_spec.input_schema["properties"]
    assert tool_spec.input_schema["required"] == ["target_agent"]
    assert callable(handler)


@pytest.mark.asyncio
async def test_handoff_spec_handler_is_defensive_raise() -> None:
    """The handler never runs (loop-intercepted); invoking it raises loudly."""
    _, handler = make_handoff_spec(suggested_targets=["expert"])
    with pytest.raises(RuntimeError, match="loop-intercepted"):
        await handler({"target_agent": "expert"})


def test_handoff_spec_description_suggests_targets() -> None:
    """Suggested targets surface in the description (boot-time check is authoritative)."""
    tool_spec, _ = make_handoff_spec(suggested_targets=["reviewer", "planner"])
    assert "reviewer" in tool_spec.description
    assert "planner" in tool_spec.description


# === handoff registration gating (Sprint 57.107 B3) ==========================


def test_make_default_executor_registers_handoff_when_targets_given() -> None:
    """handoff_targets=[...] → the spec-only handoff tool is in the registry."""
    from business_domain._register_all import make_default_executor

    registry, _ = make_default_executor(mode="mock", handoff_targets=["researcher", "planner"])
    spec = registry.get("handoff")
    assert spec is not None
    assert "researcher" in spec.description


def test_make_default_executor_omits_handoff_by_default() -> None:
    """handoff_targets=None (echo / child / teammate executors) → tool absent."""
    from business_domain._register_all import make_default_executor

    registry, _ = make_default_executor(mode="mock")
    assert registry.get("handoff") is None
