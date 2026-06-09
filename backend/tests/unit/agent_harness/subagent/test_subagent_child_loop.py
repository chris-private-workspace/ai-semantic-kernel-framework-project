"""
File: backend/tests/unit/agent_harness/subagent/test_subagent_child_loop.py
Purpose: Sprint 57.94 — FORK runs a REAL child AgentLoop (multi-turn + tool, recursion-safe).
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 57.94

Description:
    Proves the 地基 A payoff: a FORK subagent is a real multi-turn TAO loop that can
    call tools (NOT a single-shot chat), built via the ChildLoopFactory; with a
    recursion-safe tool subset (no task_spawn / handoff), tenant threading, and its
    own Cat 12 LOOP span.

Created: 2026-06-09 (Sprint 57.94)
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
    ToolCall,
)
from agent_harness.subagent import DefaultSubagentDispatcher, ForkExecutor
from business_domain._register_all import make_default_executor

from ._child_loop_helpers import RecordingTracer, make_child_loop_factory


def _final(text: str, prompt: int = 50, completion: int = 30) -> ChatResponse:
    return ChatResponse(
        model="mock-gpt",
        content=text,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
        ),
    )


@pytest.mark.asyncio
async def test_fork_child_loop_runs_multi_turn_with_tool() -> None:
    """A 2-step script (tool_call → final answer) proves a REAL multi-turn loop.

    A single-shot chat would return turn-1's empty tool-call content → empty_response
    failure. Reaching turn-2's final answer REQUIRES turn-1's echo_tool to execute.
    """
    registry, executor = make_default_executor()  # includes echo_tool
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="mock-gpt",
                content="",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": "ping"})],
                stop_reason=StopReason.TOOL_USE,
            ),
            _final("done: ping"),
        ]
    )
    fork = ForkExecutor(
        child_loop_factory=make_child_loop_factory(chat, registry=registry, executor=executor)
    )
    result = await fork.execute(
        subagent_id=uuid4(),
        task="echo ping",
        budget=SubagentBudget(),
    )
    assert result.success is True
    assert "done: ping" in result.summary  # reached turn 2 → multi-turn + tool executed


@pytest.mark.asyncio
async def test_child_registry_excludes_spawn_tools() -> None:
    """Recursion guard: make_default_executor(subagent_dispatcher=None) omits task_spawn/handoff."""
    chat = MockChatClient()
    dispatcher = DefaultSubagentDispatcher(
        chat_client=chat, child_loop_factory=make_child_loop_factory(chat)
    )
    parent_registry, _ = make_default_executor(
        subagent_dispatcher=dispatcher, parent_session_id=uuid4()
    )
    child_registry, _ = make_default_executor(subagent_dispatcher=None)

    parent_names = {s.name for s in parent_registry.list()}
    child_names = {s.name for s in child_registry.list()}

    assert "task_spawn" in parent_names  # the parent CAN spawn
    assert "task_spawn" not in child_names  # the child CANNOT spawn (recursion bounded at 1)
    assert "agent_researcher" not in child_names  # the AS_TOOL wrapper is also excluded
    assert "echo_tool" in child_names  # but the child still carries real tools


@pytest.mark.asyncio
async def test_child_loop_factory_threads_tenant() -> None:
    """The ChildLoopFactory threads tenant_id into the child loop (enterprise isolation)."""
    chat = MockChatClient(responses=[_final("ok")])
    tenant = uuid4()
    factory = make_child_loop_factory(chat, tenant_id=tenant)
    child = factory(SubagentBudget())
    assert child._tenant_id == tenant  # noqa: SLF001 — assert the child runs under the tenant


@pytest.mark.asyncio
async def test_fork_child_loop_opens_loop_span() -> None:
    """The child loop opens its own Cat 12 LOOP span via the threaded tracer (US-4)."""
    chat = MockChatClient(responses=[_final("traced")])
    tracer = RecordingTracer()
    fork = ForkExecutor(child_loop_factory=make_child_loop_factory(chat, tracer=tracer))
    result = await fork.execute(
        subagent_id=uuid4(),
        task="trace me",
        budget=SubagentBudget(),
    )
    assert result.success is True
    assert "agent_loop.run" in tracer.span_names  # the child opened its own LOOP span
