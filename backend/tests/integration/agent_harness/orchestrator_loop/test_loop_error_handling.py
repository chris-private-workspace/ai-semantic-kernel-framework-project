"""
File: backend/tests/integration/agent_harness/orchestrator_loop/test_loop_error_handling.py
Purpose: Integration tests for AgentLoop Cat 8 chain wiring (Sprint 53.2 US-6).
Category: Tests / Integration / 範疇 1 + 範疇 8
Scope: Phase 53.2 / Sprint 53.2

Created: 2026-05-03 (Sprint 53.2 Day 4)
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Literal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StopReason, StreamEvent
from agent_harness._contracts import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    ExecutionContext,
    LoopCompleted,
    LoopEvent,
    LoopTerminated,
    Message,
    TokenUsage,
    ToolCall,
    ToolSpec,
    TraceContext,
)
from agent_harness.error_handling import (
    DefaultErrorPolicy,
    DefaultErrorTerminator,
    InMemoryBudgetStore,
    TenantErrorBudget,
    TerminationReason,
)
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl

# === Fakes =================================================================


class FakeChatClient(ChatClient):
    """Returns a canned tool_use response then end_turn."""

    def __init__(self, tool_name: str = "fake_tool") -> None:
        self._tool_name = tool_name
        self._call_count = 0

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self._call_count += 1
        if self._call_count == 1:
            return ChatResponse(
                model="fake-model",
                content="Calling tool",
                tool_calls=[ToolCall(id="call_1", name=self._tool_name, arguments={"x": 1})],
                stop_reason=StopReason.TOOL_USE,
                usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
            )
        return ChatResponse(
            model="fake-model",
            content="acknowledged the failure; stopping",
            tool_calls=None,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage(prompt_tokens=12, completion_tokens=4),
        )

    def stream(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        return self._dummy_stream()

    async def _dummy_stream(self) -> AsyncIterator[StreamEvent]:
        if False:
            yield  # type: ignore[unreachable]

    async def count_tokens(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> int:
        return 1

    def get_pricing(self) -> PricingInfo:
        return MagicMock(spec=PricingInfo)

    def supports_feature(
        self,
        feature: Literal[
            "thinking",
            "caching",
            "vision",
            "audio",
            "computer_use",
            "structured_output",
            "parallel_tool_calls",
        ],
    ) -> bool:
        return False

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            model_name="fake-model",
            model_family="fake",
            provider="fake-provider",
            context_window=8192,
            max_output_tokens=4096,
        )


class _RecordingFakeChatClient(FakeChatClient):
    """FakeChatClient that records the messages it receives each turn, so a test can
    assert what the LLM actually sees (Sprint 57.144 — the structured-reflection tool
    message)."""

    def __init__(self, tool_name: str = "fake_tool") -> None:
        super().__init__(tool_name)
        self.seen_messages: list[list[Message]] = []

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self.seen_messages.append(list(request.messages))
        return await super().chat(
            request, cache_breakpoints=cache_breakpoints, trace_context=trace_context
        )


def _make_failing_loop_components(
    exc_type: type[BaseException],
) -> tuple[ToolRegistryImpl, ToolExecutorImpl]:
    """Build a registry+executor where 'fake_tool' raises exc_type."""
    registry = ToolRegistryImpl()
    spec = ToolSpec(
        name="fake_tool",
        description="A tool that raises for Cat 8 testing.",
        input_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
    )
    registry.register(spec)

    async def _fail(call: ToolCall, context: ExecutionContext) -> Any:
        raise exc_type("simulated tool failure")

    executor = ToolExecutorImpl(registry=registry, handlers={"fake_tool": _fail})
    return registry, executor


class _RaisingExecutor(ToolExecutorImpl):
    """A ToolExecutor whose execute() ITSELF raises — the RARE loop.py:3068 path, distinct
    from a handler soft-failure caught inside ToolExecutorImpl.execute() (the dominant
    _build_failure path). Sprint 57.163 US-1: the real executor is designed to turn every
    failure into a ToolResult, so this near-dead branch cannot be reached via a real executor
    on the 主流量 — inject a raising executor to exercise the wiring (gate-only, NOT a
    drive-through: the branch is defensive full-coverage, near-unreachable in production)."""

    def __init__(self, registry: ToolRegistryImpl, exc: BaseException) -> None:
        super().__init__(registry=registry, handlers={})
        self._exc = exc

    async def execute(
        self,
        call: ToolCall,
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> Any:
        raise self._exc


def _make_raising_loop_components(
    exc: BaseException,
) -> tuple[ToolRegistryImpl, _RaisingExecutor]:
    """Build a registry + an executor whose execute() itself raises (rare path)."""
    registry = ToolRegistryImpl()
    registry.register(
        ToolSpec(
            name="fake_tool",
            description="A tool whose executor itself raises for rare-path testing.",
            input_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
        )
    )
    return registry, _RaisingExecutor(registry, exc)


# === fixtures ==============================================================


@pytest.fixture
def session_id():
    return uuid4()


@pytest.fixture
def trace_ctx():
    return TraceContext.create_root()


# === tests =================================================================


class TestLLMRecoverable:
    @pytest.mark.asyncio
    async def test_uncaught_tool_exception_becomes_llm_recoverable(
        self, session_id, trace_ctx
    ) -> None:
        registry, executor = _make_failing_loop_components(ConnectionError)
        loop = AgentLoopImpl(
            chat_client=FakeChatClient(),
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            error_policy=DefaultErrorPolicy(),
            # No terminator → never terminates
        )
        events: list[LoopEvent] = []
        async for ev in loop.run(
            session_id=session_id,
            user_input="please call fake_tool",
            trace_context=trace_ctx,
        ):
            events.append(ev)

        completes = [e for e in events if isinstance(e, LoopCompleted)]
        assert len(completes) == 1
        assert completes[0].stop_reason == "end_turn"
        assert not any(isinstance(e, LoopTerminated) for e in events)

    @pytest.mark.asyncio
    async def test_structured_reflection_reaches_llm_when_lever_on(
        self, session_id, trace_ctx, monkeypatch
    ) -> None:
        """Sprint 57.144 US-2 (research #7 Half B): with the lever ON, the LLM-visible
        tool message (content, NOT error) carries the typed diagnosis end-to-end through
        the loop. A ConnectionError → executor catches → FAILED_API reflection."""
        monkeypatch.setenv("CHAT_TOOL_ERROR_REFLECTION", "1")
        registry, executor = _make_failing_loop_components(ConnectionError)
        chat = _RecordingFakeChatClient()
        loop = AgentLoopImpl(
            chat_client=chat,
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            error_policy=DefaultErrorPolicy(),
        )
        async for _ in loop.run(
            session_id=session_id, user_input="call fake_tool", trace_context=trace_ctx
        ):
            pass
        tool_msgs = [m for msgs in chat.seen_messages for m in msgs if m.role == "tool"]
        assert tool_msgs, "expected a tool-role message fed back to the LLM"
        joined = " ".join(str(m.content) for m in tool_msgs)
        assert "tool execution failed (external/API error)" in joined

    @pytest.mark.asyncio
    async def test_no_reflection_in_llm_message_when_lever_off(
        self, session_id, trace_ctx, monkeypatch
    ) -> None:
        """Byte-identical default: lever OFF → the soft-failure tool message content is
        empty (pre-57.144 behavior), no taxonomy text leaks into the LLM context."""
        monkeypatch.delenv("CHAT_TOOL_ERROR_REFLECTION", raising=False)
        registry, executor = _make_failing_loop_components(ConnectionError)
        chat = _RecordingFakeChatClient()
        loop = AgentLoopImpl(
            chat_client=chat,
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            error_policy=DefaultErrorPolicy(),
        )
        async for _ in loop.run(
            session_id=session_id, user_input="call fake_tool", trace_context=trace_ctx
        ):
            pass
        tool_msgs = [m for msgs in chat.seen_messages for m in msgs if m.role == "tool"]
        joined = " ".join(str(m.content) for m in tool_msgs)
        assert "tool execution failed" not in joined  # content="" today


class TestFatalTermination:
    @pytest.mark.asyncio
    async def test_fatal_exception_terminates_loop(self, session_id, trace_ctx) -> None:
        class MyMysteryBug(Exception):
            pass

        registry, executor = _make_failing_loop_components(MyMysteryBug)
        loop = AgentLoopImpl(
            chat_client=FakeChatClient(),
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            tenant_id=uuid4(),
            error_policy=DefaultErrorPolicy(),
            error_terminator=DefaultErrorTerminator(),
        )
        events: list[LoopEvent] = []
        async for ev in loop.run(
            session_id=session_id,
            user_input="please call fake_tool",
            trace_context=trace_ctx,
        ):
            events.append(ev)

        terminated = [e for e in events if isinstance(e, LoopTerminated)]
        assert len(terminated) == 1
        assert terminated[0].reason == TerminationReason.FATAL_EXCEPTION.value


class TestBudgetTermination:
    @pytest.mark.asyncio
    async def test_budget_pre_exceeded_terminates_loop(self, session_id, trace_ctx) -> None:
        """Tenant pre-exceeded their daily error budget; the next tool failure
        is intercepted by ErrorTerminator BEFORE the loop continues."""
        store = InMemoryBudgetStore()
        budget = TenantErrorBudget(store, max_per_day=2, max_per_month=100)
        tenant = uuid4()
        # Pre-exceed budget out-of-band (simulates earlier requests this day)
        from agent_harness.error_handling import ErrorClass

        for _ in range(3):  # 3 > 2 → exceeded
            await budget.record(tenant, ErrorClass.TRANSIENT)

        registry, executor = _make_failing_loop_components(ConnectionError)
        loop = AgentLoopImpl(
            chat_client=FakeChatClient(),
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            tenant_id=tenant,
            error_policy=DefaultErrorPolicy(),
            error_budget=budget,
            error_terminator=DefaultErrorTerminator(error_budget=budget),
        )
        events: list[LoopEvent] = []
        async for ev in loop.run(
            session_id=session_id,
            user_input="please call fake_tool",
            trace_context=trace_ctx,
        ):
            events.append(ev)

        terminated = [e for e in events if isinstance(e, LoopTerminated)]
        assert len(terminated) == 1
        assert terminated[0].reason == TerminationReason.BUDGET_EXCEEDED.value


class TestOptOut:
    @pytest.mark.asyncio
    async def test_no_cat8_deps_propagates_failure_via_tool_result(
        self, session_id, trace_ctx
    ) -> None:
        """Without Cat 8 deps, ToolExecutorImpl already catches and returns
        ToolResult(success=False); loop continues to end_turn (53.1 baseline)."""
        registry, executor = _make_failing_loop_components(ConnectionError)
        loop = AgentLoopImpl(
            chat_client=FakeChatClient(),
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            # No error_policy → opt-out
        )
        events: list[LoopEvent] = []
        async for ev in loop.run(
            session_id=session_id,
            user_input="please call fake_tool",
            trace_context=trace_ctx,
        ):
            events.append(ev)

        # 53.1 baseline: ToolExecutor catches; soft-failure; loop ends normally
        completes = [e for e in events if isinstance(e, LoopCompleted)]
        assert len(completes) == 1
        assert not any(isinstance(e, LoopTerminated) for e in events)


class TestRarePathReflection:
    """Sprint 57.163 US-1: the RARE path where the executor ITSELF raises (loop.py:3068),
    NOT a handler soft-failure the executor catches (the dominant _build_failure path that
    Sprint 57.144's TestLLMRecoverable already covers). Gate-only: near-unreachable on the
    主流量 (the real executor turns every failure into a ToolResult) — these assert the
    wiring of the branch with both lever states, NOT usability."""

    @pytest.mark.asyncio
    async def test_rare_path_reflection_when_lever_on(
        self, session_id, trace_ctx, monkeypatch
    ) -> None:
        monkeypatch.setenv("CHAT_TOOL_ERROR_REFLECTION", "1")
        # error_policy not None → reaches :3068 (not the opt-out re-raise); no terminator +
        # no error_budget → never terminates → falls through to the reflection synthesis.
        registry, executor = _make_raising_loop_components(RuntimeError("boom"))
        chat = _RecordingFakeChatClient()
        loop = AgentLoopImpl(
            chat_client=chat,
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            error_policy=DefaultErrorPolicy(),
        )
        async for _ in loop.run(
            session_id=session_id, user_input="call fake_tool", trace_context=trace_ctx
        ):
            pass
        tool_msgs = [m for msgs in chat.seen_messages for m in msgs if m.role == "tool"]
        assert tool_msgs, "expected a tool-role message fed back to the LLM"
        joined = " ".join(str(m.content) for m in tool_msgs)
        # RuntimeError → classify_tool_error → INVOCATION taxonomy → typed diagnosis in content
        assert "tool invocation error" in joined
        assert "boom" in joined

    @pytest.mark.asyncio
    async def test_rare_path_baseline_when_lever_off(
        self, session_id, trace_ctx, monkeypatch
    ) -> None:
        monkeypatch.delenv("CHAT_TOOL_ERROR_REFLECTION", raising=False)
        registry, executor = _make_raising_loop_components(RuntimeError("boom"))
        chat = _RecordingFakeChatClient()
        loop = AgentLoopImpl(
            chat_client=chat,
            output_parser=OutputParserImpl(),
            tool_executor=executor,
            tool_registry=registry,
            error_policy=DefaultErrorPolicy(),
        )
        async for _ in loop.run(
            session_id=session_id, user_input="call fake_tool", trace_context=trace_ctx
        ):
            pass
        tool_msgs = [m for msgs in chat.seen_messages for m in msgs if m.role == "tool"]
        joined = " ".join(str(m.content) for m in tool_msgs)
        # lever OFF → the pre-57.144 rare-path baseline content (loop.py:3078), no taxonomy label
        assert "Please adjust your approach" in joined
        assert "tool invocation error" not in joined
