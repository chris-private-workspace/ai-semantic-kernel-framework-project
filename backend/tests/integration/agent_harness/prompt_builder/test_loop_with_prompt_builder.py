"""Loop + PromptBuilder integration. Sprint 52.2 Day 3.8.

Verifies the full Cat 1 -> Cat 5 -> Adapter chain:
  - AgentLoopImpl injected with DefaultPromptBuilder
  - Per-turn build() emits PromptBuilt event with full payload
  - artifact.cache_breakpoints flows to MockChatClient.last_call_cache_breakpoints
  - Multi-turn dialog: memory_layers_used grows as session memory expands

Stays SDK-free (MockChatClient + InMemoryStore + InMemoryCacheManager +
TiktokenCounter). No anthropic / openai imports.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    MemoryAccessed,
    MemoryHint,
    PromptBuilt,
    StopReason,
    TokenUsage,
    ToolCall,
    ToolResult,
    TraceContext,
)
from agent_harness._contracts.tools import ToolSpec
from agent_harness.context_mgmt.cache_manager import InMemoryCacheManager
from agent_harness.context_mgmt.token_counter.tiktoken_counter import (
    TiktokenCounter,
)
from agent_harness.memory.retrieval import MemoryRetrieval
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.prompt_builder.builder import DefaultPromptBuilder
from agent_harness.tools._abc import ExecutionContext, ToolExecutor, ToolRegistry


class _StubRegistry(ToolRegistry):
    """Minimal ToolRegistry stub for integration tests."""

    def register(self, spec: ToolSpec) -> None:
        return None

    def get(self, name: str) -> ToolSpec | None:
        return None

    def list(self) -> list[ToolSpec]:
        return []

    def by_tag(self, tag: str) -> list[ToolSpec]:
        return []


class _NoopExecutor(ToolExecutor):
    """Minimal ToolExecutor stub; not exercised in single-turn tests."""

    async def execute(
        self,
        call: ToolCall,
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> ToolResult:
        return ToolResult(
            tool_call_id=call.id,
            tool_name=call.name,
            success=True,
            content="noop",
        )

    async def execute_batch(
        self,
        calls: list[ToolCall],
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> list[ToolResult]:
        return [await self.execute(c, trace_context=trace_context, context=context) for c in calls]


def _final_response(text: str = "done") -> ChatResponse:
    return ChatResponse(
        model="mock",
        content=text,
        stop_reason=StopReason.END_TURN,
        tool_calls=None,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


def _make_builder(retrieval: MemoryRetrieval) -> DefaultPromptBuilder:
    return DefaultPromptBuilder(
        memory_retrieval=retrieval,
        cache_manager=InMemoryCacheManager(),
        token_counter=TiktokenCounter(model="gpt-4o"),
    )


@pytest.mark.asyncio
async def test_loop_emits_prompt_built_event_with_full_payload() -> None:
    """Loop with prompt_builder injected emits PromptBuilt with full schema."""
    chat_client = MockChatClient(responses=[_final_response()])

    retrieval = MemoryRetrieval(layers={})
    retrieval.search = AsyncMock(return_value=[])  # type: ignore[method-assign]

    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=_NoopExecutor(),
        tool_registry=_StubRegistry(),
        prompt_builder=_make_builder(retrieval),
    )

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hello")]
    prompt_built = [ev for ev in events if isinstance(ev, PromptBuilt)]

    assert len(prompt_built) == 1
    pb = prompt_built[0]
    assert pb.messages_count >= 1
    assert pb.estimated_input_tokens >= 0
    assert pb.cache_breakpoints_count >= 0
    assert pb.position_strategy_used == "LostInMiddleStrategy"
    assert pb.duration_ms >= 0.0


@pytest.mark.asyncio
async def test_artifact_cache_breakpoints_flow_to_chat_client() -> None:
    """artifact.cache_breakpoints from build() reach MockChatClient.chat()."""
    chat_client = MockChatClient(responses=[_final_response()])

    retrieval = MemoryRetrieval(layers={})
    retrieval.search = AsyncMock(return_value=[])  # type: ignore[method-assign]

    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=_NoopExecutor(),
        tool_registry=_StubRegistry(),
        prompt_builder=_make_builder(retrieval),
    )

    _ = [ev async for ev in loop.run(session_id=uuid4(), user_input="hello")]

    # Default CachePolicy emits up to 3 breakpoints (system / tools / memory).
    # Minimal session has at least the system section -> >=1 breakpoint.
    assert chat_client.last_call_cache_breakpoints is not None
    assert len(chat_client.last_call_cache_breakpoints) >= 1


@pytest.mark.asyncio
async def test_memory_layers_grow_across_sessions() -> None:
    """Across 2 sequential session runs, memory_layers_used reflects state.

    Run 1: empty memory → memory_layers_used == ()
    Run 2: user + session memory present → contains "user" and "session"

    This simulates the natural progression where memory accumulates between
    sessions; PromptBuilder picks up whatever MemoryRetrieval returns.
    """
    call_count = {"n": 0}

    async def variable_search(*args: object, **kwargs: object) -> list[MemoryHint]:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return []
        return [
            MemoryHint(
                hint_id=uuid4(),
                layer="user",
                time_scale="long_term",
                summary="user-fact",
                confidence=0.9,
                relevance_score=0.8,
                full_content_pointer="db://user/1",
                timestamp=datetime.now(timezone.utc),
            ),
            MemoryHint(
                hint_id=uuid4(),
                layer="session",
                time_scale="short_term",
                summary="session-fact",
                confidence=0.85,
                relevance_score=0.75,
                full_content_pointer="db://session/1",
                timestamp=datetime.now(timezone.utc),
            ),
        ]

    retrieval = MemoryRetrieval(layers={})
    retrieval.search = variable_search  # type: ignore[method-assign]
    builder = _make_builder(retrieval)

    def _make_loop() -> AgentLoopImpl:
        chat_client = MockChatClient(responses=[_final_response()])
        return AgentLoopImpl(
            chat_client=chat_client,
            output_parser=OutputParserImpl(),
            tool_executor=_NoopExecutor(),
            tool_registry=_StubRegistry(),
            prompt_builder=builder,
        )

    # Run 1: empty memory.
    loop1 = _make_loop()
    events1 = [ev async for ev in loop1.run(session_id=uuid4(), user_input="run1")]
    pb1 = cast(list[PromptBuilt], [ev for ev in events1 if isinstance(ev, PromptBuilt)])
    assert len(pb1) == 1
    assert pb1[0].memory_layers_used == ()

    # Run 2: memory populated.
    loop2 = _make_loop()
    events2 = [ev async for ev in loop2.run(session_id=uuid4(), user_input="run2")]
    pb2 = cast(list[PromptBuilt], [ev for ev in events2 if isinstance(ev, PromptBuilt)])
    assert len(pb2) == 1
    assert set(pb2[0].memory_layers_used) >= {"user", "session"}


# ===========================================================================
# Sprint 57.75 (A-5c Memory tab): MemoryAccessed SSE LoopEvent emit.
# The loop emits one MemoryAccessed per retrieved hint after build() — feeding
# the chat-v2 Inspector Memory tab. On the no-prompt-builder path (echo_demo)
# nothing is emitted → the Memory tab stays honestly empty (D-DAY0-5).
# ===========================================================================


@pytest.mark.asyncio
async def test_loop_emits_memory_accessed_per_hint() -> None:
    """real_llm-style path (prompt_builder injected) with 2 retrieved hints emits
    2 MemoryAccessed events carrying scope / time_scale / key / summary."""

    async def two_hits(*args: object, **kwargs: object) -> list[MemoryHint]:
        return [
            MemoryHint(
                hint_id=uuid4(),
                layer="user",
                time_scale="long_term",
                summary="user prefers concise answers",
                confidence=0.9,
                relevance_score=0.8,
                full_content_pointer="db://user/42",
                timestamp=datetime.now(timezone.utc),
            ),
            MemoryHint(
                hint_id=uuid4(),
                layer="session",
                time_scale="short_term",
                summary="earlier asked about pricing",
                confidence=0.85,
                relevance_score=0.75,
                full_content_pointer="db://session/7",
                timestamp=datetime.now(timezone.utc),
            ),
        ]

    retrieval = MemoryRetrieval(layers={})
    retrieval.search = two_hits  # type: ignore[method-assign]
    loop = AgentLoopImpl(
        chat_client=MockChatClient(responses=[_final_response()]),
        output_parser=OutputParserImpl(),
        tool_executor=_NoopExecutor(),
        tool_registry=_StubRegistry(),
        prompt_builder=_make_builder(retrieval),
    )

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hi")]
    mem = [ev for ev in events if isinstance(ev, MemoryAccessed)]

    assert len(mem) == 2
    assert all(ev.operation == "read" for ev in mem)
    by_scope = {ev.layer: ev for ev in mem}
    assert set(by_scope) == {"user", "session"}
    assert by_scope["user"].time_scale == "long_term"
    assert by_scope["user"].key == "db://user/42"
    assert by_scope["user"].summary == "user prefers concise answers"
    assert by_scope["session"].time_scale == "short_term"


@pytest.mark.asyncio
async def test_loop_without_prompt_builder_emits_no_memory_accessed() -> None:
    """echo_demo-style path (no prompt_builder) emits zero MemoryAccessed events
    → the Memory tab shows an honest empty state, not a fabricated row."""
    loop = AgentLoopImpl(
        chat_client=MockChatClient(responses=[_final_response()]),
        output_parser=OutputParserImpl(),
        tool_executor=_NoopExecutor(),
        tool_registry=_StubRegistry(),
        # NO prompt_builder → memory injection branch never runs.
    )

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hi")]
    assert not [ev for ev in events if isinstance(ev, MemoryAccessed)]


# ===========================================================================
# Sprint 57.80 (AD-Chat-RealLLM-Orphan-Tool-Message): a 2-turn tool-calling
# script through loop + DefaultPromptBuilder must assemble a valid sequence —
# every role='tool' message immediately after its owning assistant(tool_calls).
# This exercises the FULL Cat1→Cat5 chain on a tool turn (the case that 400s on
# real Azure before the builder's tool-adjacency invariant). AP-10 closure: the
# MockChatClient does NOT validate adjacency, so the assertion is structural —
# on chat_client.last_request.messages (the turn-2 assembly), not the mock.
# ===========================================================================


def _tool_call_response(call_id: str = "c1") -> ChatResponse:
    return ChatResponse(
        model="mock",
        content="",
        stop_reason=StopReason.TOOL_USE,
        tool_calls=[ToolCall(id=call_id, name="echo_tool", arguments={"text": "hi"})],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


@pytest.mark.asyncio
async def test_loop_builder_tool_turn_keeps_tool_after_assistant() -> None:
    """real_llm-style path (prompt_builder injected) with a tool turn: the turn-2
    assembly sent to chat() has the tool message directly after its assistant —
    the orphan-tool 400 regression guard (fails on the pre-57.80 builder)."""
    chat_client = MockChatClient(responses=[_tool_call_response("c1"), _final_response()])

    retrieval = MemoryRetrieval(layers={})
    retrieval.search = AsyncMock(return_value=[])  # type: ignore[method-assign]

    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=_NoopExecutor(),
        tool_registry=_StubRegistry(),
        prompt_builder=_make_builder(retrieval),
    )

    _ = [ev async for ev in loop.run(session_id=uuid4(), user_input="echo hi")]

    # last_request = the final (turn-2) chat() call — the previously-400'ing assembly.
    sent = chat_client.last_request
    assert sent is not None
    messages = sent.messages
    a_idx = next(i for i, m in enumerate(messages) if m.role == "assistant" and m.tool_calls)
    t_idx = next(i for i, m in enumerate(messages) if m.role == "tool" and m.tool_call_id == "c1")
    assert t_idx == a_idx + 1, (
        "tool must immediately follow its assistant(tool_calls) in the assembled "
        f"request; got assistant@{a_idx}, tool@{t_idx} in {[m.role for m in messages]}"
    )
