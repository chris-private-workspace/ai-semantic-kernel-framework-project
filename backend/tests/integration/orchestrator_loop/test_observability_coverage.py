"""
File: backend/tests/integration/orchestrator_loop/test_observability_coverage.py
Purpose: Verify Cat 12 instrumentation coverage on the 50.1 main loop.
Category: Integration tests / 範疇 12 (Observability)
Scope: Phase 50 / Sprint 50.1 (Day 4.2)

Description:
    .claude/rules/observability-instrumentation.md mandates 5 emit points;
    this test verifies the ones reachable in 50.1 scope (Loop turn / Tool
    execute / Output parser parse). LLM call (point 3) is wrapped by
    AzureOpenAIAdapter — out of 50.1 scope but verified at adapter contract
    test level (49.4). State checkpoint (point 5) lands Phase 53.1.

    Approach: inject a `RecordingTracer` (test-only Tracer ABC subclass
    that captures every start_span + record_metric call) into all three
    collaborators (Loop / Parser / Tool Executor) and the InMemoryToolExecutor's
    metric emit. Then run an echo flow and assert the captured records.

    Why NOT OpenTelemetry SDK in-memory exporter? OTel `set_tracer_provider`
    is global state that can't be cleanly reset between tests; using an ABC
    subclass keeps tests hermetic and exercises the same Tracer interface
    that production code uses.

Created: 2026-04-30 (Sprint 50.1 Day 4.2)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    MetricEvent,
    SpanCategory,
    StopReason,
    ToolCall,
    TraceContext,
)
from agent_harness.observability import MetricRegistry, Tracer
from agent_harness.orchestrator_loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl, make_echo_executor


class RecordingTracer(Tracer):
    """Test-only Tracer that captures every start_span + record_metric call."""

    def __init__(self) -> None:
        self.spans: list[dict[str, Any]] = []
        self.metrics: list[MetricEvent] = []

    @asynccontextmanager
    async def _span_cm(
        self,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None,
        attributes: dict[str, Any] | None,
    ) -> AsyncIterator[TraceContext]:
        ctx = trace_context or TraceContext.create_root()
        self.spans.append(
            {
                "name": name,
                "category": category.value,
                "attributes": dict(attributes or {}),
            }
        )
        yield ctx

    def start_span(
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        return self._span_cm(name, category, trace_context, attributes)

    def record_metric(self, event: MetricEvent) -> None:
        self.metrics.append(event)

    def get_current_context(self) -> TraceContext | None:
        return None


@pytest.mark.asyncio
async def test_e2e_emits_per_turn_loop_and_tool_spans() -> None:
    """Multi-turn echo flow yields agent_loop + tool.echo_tool + output_parser
    spans across all three collaborators."""
    rec = RecordingTracer()
    registry, _ = make_echo_executor()
    # Re-build executor with shared RecordingTracer (same registry).
    executor = ToolExecutorImpl(
        registry=registry,
        handlers={"echo_tool": _shared_echo_handler},
        tracer=rec,
        metric_registry=MetricRegistry(),
    )

    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="m",
                content="calling",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": "x"})],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(model="m", content="done", stop_reason=StopReason.END_TURN),
        ]
    )
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(tracer=rec),
        tool_executor=executor,
        tool_registry=registry,
        tracer=rec,
    )

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="echo x")]
    assert events  # non-empty

    # Span coverage: collect (name, category) tuples emitted.
    span_keys = [(s["name"], s["category"]) for s in rec.spans]

    # 1. Loop owns its run() span exactly once.
    assert ("agent_loop.run", "orchestrator_loop") in span_keys

    # 1b. Sprint 57.71 (A-4 Tier 1): the loop now opens its own per-turn span
    # tree — a TURN span + an LLM_CALL span per turn (both ORCHESTRATOR-category,
    # distinguished by name + attributes["span_type"]). 2 turns → 2 TURN +
    # 2 LLM_CALL spans.
    assert ("agent_loop.turn", "orchestrator_loop") in span_keys
    assert ("agent_loop.llm_call", "orchestrator_loop") in span_keys
    assert len([k for k in span_keys if k == ("agent_loop.turn", "orchestrator_loop")]) == 2
    assert len([k for k in span_keys if k == ("agent_loop.llm_call", "orchestrator_loop")]) == 2

    # 2. Tool spans (category="tools") now come from TWO owners (Sprint 57.71):
    #    - the executor's internal `tool.echo_tool` span (Cat 2; pre-existing)
    #    - the loop's own `agent_loop.tool.echo_tool` TOOL_EXEC span (Cat 1 wrap)
    # exactly 1 tool call here → 1 of each (2 total tools-category spans). The
    # loop is the trace-tree owner; the executor span stays NoOp on the real
    # chat path (here both share the RecordingTracer for coverage assertions).
    assert ("tool.echo_tool", "tools") in span_keys
    assert ("agent_loop.tool.echo_tool", "tools") in span_keys
    tool_spans = [k for k in span_keys if k[1] == "tools"]
    assert len(tool_spans) == 2

    # 3. Output parser span emitted per turn (2 turns → 2 parse spans).
    parser_spans = [k for k in span_keys if k[1] == "output_parser"]
    assert len(parser_spans) == 2
    assert parser_spans[0] == ("output_parser.parse", "output_parser")


async def _shared_echo_handler(call: ToolCall) -> str:
    return str(call.arguments.get("text", ""))


@pytest.mark.asyncio
async def test_e2e_emits_tool_execution_duration_metric() -> None:
    """InMemoryToolExecutor must emit `tool_execution_duration_seconds`
    histogram per successful tool call."""
    rec = RecordingTracer()
    registry, _ = make_echo_executor()
    executor = ToolExecutorImpl(
        registry=registry,
        handlers={"echo_tool": _shared_echo_handler},
        tracer=rec,
        metric_registry=MetricRegistry(),
    )

    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="m",
                content="x",
                tool_calls=[
                    ToolCall(id="c1", name="echo_tool", arguments={"text": "y"}),
                    ToolCall(id="c2", name="echo_tool", arguments={"text": "z"}),
                ],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(model="m", content="end", stop_reason=StopReason.END_TURN),
        ]
    )
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(tracer=rec),
        tool_executor=executor,
        tool_registry=registry,
        tracer=rec,
    )
    [ev async for ev in loop.run(session_id=uuid4(), user_input="multi")]

    # 2 tool calls → 2 metric events
    duration_metrics = [
        m for m in rec.metrics if m.metric_name == "tool_execution_duration_seconds"
    ]
    assert len(duration_metrics) == 2
    assert all(m.metric_type == "histogram" for m in duration_metrics)
    assert all(m.value >= 0.0 for m in duration_metrics)
    # Labels carry tool_name + status
    assert all(m.labels.get("tool_name") == "echo_tool" for m in duration_metrics)
    assert all(m.labels.get("status") == "success" for m in duration_metrics)


@pytest.mark.asyncio
async def test_tool_failure_emits_error_metric() -> None:
    """Tool handler exception → metric labelled status=error (still emitted)."""
    rec = RecordingTracer()

    async def crashing_handler(call: ToolCall) -> str:
        raise RuntimeError("oops")

    # Build a registry with a minimal `crash` spec so ToolExecutorImpl reaches
    # the handler instead of short-circuiting on unknown-tool lookup.
    from agent_harness._contracts import ToolAnnotations, ToolSpec  # noqa: PLC0415

    registry = ToolRegistryImpl()
    registry.register(
        ToolSpec(
            name="crash",
            description="test",
            input_schema={"type": "object", "properties": {}},
            annotations=ToolAnnotations(read_only=True),
        )
    )
    executor = ToolExecutorImpl(
        registry=registry,
        handlers={"crash": crashing_handler},
        tracer=rec,
        metric_registry=MetricRegistry(),
    )
    result = await executor.execute(ToolCall(id="c1", name="crash", arguments={}))
    assert result.success is False
    error_metrics = [
        m
        for m in rec.metrics
        if m.metric_name == "tool_execution_duration_seconds" and m.labels.get("status") == "error"
    ]
    assert len(error_metrics) == 1
