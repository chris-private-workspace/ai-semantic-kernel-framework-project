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

import asyncio
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ApprovalRequested,
    ChatResponse,
    GuardrailTriggered,
    LoopCompleted,
    StopReason,
    SubagentBudget,
    TokenUsage,
    ToolCall,
    ToolSpec,
)
from agent_harness.guardrails import build_default_guardrail_engine
from agent_harness.guardrails.input import KeywordEscalationGuardrail
from agent_harness.guardrails.tool.capability_matrix import CapabilityMatrix, PermissionRule
from agent_harness.guardrails.tool.tool_guardrail import ToolGuardrail
from agent_harness.subagent import DefaultSubagentDispatcher, ForkExecutor
from agent_harness.tools.executor import ToolExecutorImpl
from agent_harness.tools.registry import ToolRegistryImpl
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


# --- Sprint 57.110 (B4): child governance — Cat 9 engine in the child loop --------


def _escalating_engine(phrase: str):  # type: ignore[no-untyped-def]
    """A COMPOSED engine (defaults + an input-ESCALATE keyword) — the handler shape."""
    engine = build_default_guardrail_engine()
    engine.register(KeywordEscalationGuardrail(frozenset({phrase})), priority=5)
    return engine


@pytest.mark.asyncio
async def test_child_loop_factory_threads_guardrail_engine() -> None:
    """The ChildLoopFactory threads the composed engine into the child loop (B4 鐵律)."""
    chat = MockChatClient(responses=[_final("ok")])
    engine = build_default_guardrail_engine()
    factory = make_child_loop_factory(chat, guardrail_engine=engine)
    child = factory(SubagentBudget())
    assert child._guardrail_engine is engine  # noqa: SLF001 — identity, not a copy


@pytest.mark.asyncio
async def test_child_input_escalate_fail_closes_to_block() -> None:
    """Sprint 57.110 (B4): the child has NO HITL wiring — an input ESCALATE fail-closes
    to BLOCK before any child LLM call, and the result is truthfully labelled."""
    chat = MockChatClient(responses=[_final("never reached")])
    fork = ForkExecutor(
        child_loop_factory=make_child_loop_factory(
            chat, guardrail_engine=_escalating_engine("forbidden topic")
        )
    )
    result = await fork.execute(
        subagent_id=uuid4(),
        task="please research the forbidden topic in depth",
        budget=SubagentBudget(),
    )
    assert result.success is False
    assert result.error == "child_guardrail_blocked"


@pytest.mark.asyncio
async def test_child_escalate_emits_block_not_pause() -> None:
    """ESCALATE-in-child fail-closes: the GuardrailTriggered event keeps the truthful
    action ('escalate') while the RUN terminates guardrail_blocked, and NEVER an
    ApprovalRequested (no pause — loop.py's fail-closed invariant)."""
    chat = MockChatClient(responses=[_final("never reached")])
    factory = make_child_loop_factory(chat, guardrail_engine=_escalating_engine("forbidden topic"))
    child = factory(SubagentBudget())
    events = [
        ev
        async for ev in child.run(
            session_id=uuid4(), user_input="tell me about the forbidden topic"
        )
    ]
    assert not any(isinstance(ev, ApprovalRequested) for ev in events)
    triggered = [ev for ev in events if isinstance(ev, GuardrailTriggered)]
    assert triggered and triggered[0].guardrail_type == "input"
    assert triggered[0].action == "escalate"  # the event keeps the guardrail's truth
    completed = [ev for ev in events if isinstance(ev, LoopCompleted)]
    assert completed and completed[-1].stop_reason == "guardrail_blocked"  # the run blocks


@pytest.mark.asyncio
async def test_child_tool_escalate_blocks_tool_and_continues() -> None:
    """A tool requiring approval ESCALATEs in the child → soft-blocked (no HITL);
    the LLM sees an error ToolResult and the child still reaches its final answer."""
    registry, executor = make_default_executor()  # includes echo_tool
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="mock-gpt",
                content="",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": "ping"})],
                stop_reason=StopReason.TOOL_USE,
            ),
            _final("done without the tool"),
        ]
    )
    engine = build_default_guardrail_engine()
    engine.register(
        ToolGuardrail(
            CapabilityMatrix(
                capability_to_tools={},
                permission_rules={"echo_tool": PermissionRule(requires_approval=True)},
            )
        ),
        priority=10,
    )
    fork = ForkExecutor(
        child_loop_factory=make_child_loop_factory(
            chat, registry=registry, executor=executor, guardrail_engine=engine
        )
    )
    result = await fork.execute(subagent_id=uuid4(), task="echo ping", budget=SubagentBudget())
    assert result.success is True
    assert "done without the tool" in result.summary


# --- Sprint 57.110 (B4): fail_partial salvage --------------------------------


def _slow_tool_setup() -> tuple[MockChatClient, ToolRegistryImpl, ToolExecutorImpl]:
    """A child whose turn-1 emits partial content then blocks in a slow tool —
    the wait_for timeout cancels it with the partial answer already captured."""
    slow_spec = ToolSpec(
        name="slow_tool",
        description="sleeps past the budget",
        input_schema={"type": "object", "properties": {}},
    )

    async def slow_handler(call: ToolCall) -> str:
        await asyncio.sleep(10)
        return "never returns"

    registry = ToolRegistryImpl()
    registry.register(slow_spec)
    executor = ToolExecutorImpl(registry=registry, handlers={"slow_tool": slow_handler})
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="mock-gpt",
                content="partial finding so far",
                tool_calls=[ToolCall(id="s1", name="slow_tool", arguments={})],
                stop_reason=StopReason.TOOL_USE,
            )
        ]
    )
    return chat, registry, executor


@pytest.mark.asyncio
async def test_fail_partial_salvages_timed_out_child_output() -> None:
    """fail_partial: a timed-out child's partial work lands in summary (error kept)."""
    chat, registry, executor = _slow_tool_setup()
    fork = ForkExecutor(
        child_loop_factory=make_child_loop_factory(chat, registry=registry, executor=executor)
    )
    result = await fork.execute(
        subagent_id=uuid4(),
        task="long research",
        budget=SubagentBudget(max_duration_s=1, failure_policy="fail_partial"),
    )
    assert result.success is False
    assert result.error == "timeout: 1s"
    assert "partial finding so far" in result.summary  # salvaged, not discarded
    assert result.metadata["failure_policy"] == "fail_partial"


@pytest.mark.asyncio
async def test_fail_soft_timeout_keeps_empty_summary() -> None:
    """The default (fail_soft) keeps today's shape: timeout → empty summary."""
    chat, registry, executor = _slow_tool_setup()
    fork = ForkExecutor(
        child_loop_factory=make_child_loop_factory(chat, registry=registry, executor=executor)
    )
    result = await fork.execute(
        subagent_id=uuid4(),
        task="long research",
        budget=SubagentBudget(max_duration_s=1),
    )
    assert result.success is False
    assert result.error == "timeout: 1s"
    assert result.summary == ""
