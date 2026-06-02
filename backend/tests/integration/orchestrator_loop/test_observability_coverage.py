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
Last Modified: 2026-06-02

Modification History:
    - 2026-06-02: Sprint 57.71 — RecordingTracer captures parent linkage
        (span_id / parent_span_id) + ERROR status; add LOOP→TURN→operation
        tree-reconstruction / nesting / ERROR-status / edge-case tests (A-4 Tier 1)
    - 2026-04-30: Initial creation (Sprint 50.1 Day 4.2)
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
    TokenUsage,
    ToolCall,
    TraceContext,
)
from agent_harness.observability import MetricRegistry, NoOpTracer, Tracer
from agent_harness.orchestrator_loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl, make_echo_executor


class RecordingTracer(Tracer):
    """Test-only Tracer that captures every start_span + record_metric call.

    Sprint 57.71 (A-4 Tier 1): each recorded span now captures parent linkage
    so a parent→child trace tree can be reconstructed. Mirroring the production
    NoOpTracer/OTelTracer, ``_span_cm`` mints a real child ``TraceContext``
    (fresh ``span_id``, ``parent_span_id`` = the incoming ctx's ``span_id``) and
    yields it — so threading the yielded ctx into nested ``start_span`` calls
    builds the LOOP→TURN→operation hierarchy. The recorded ``attributes`` dict
    is stored BY REFERENCE (not copied) so post-response token writes the loop
    folds into the shared ``llm_attrs`` dict are observable after the run.

    ERROR status: like OTelTracer, the cm catches a propagating exception, flips
    the span's recorded ``status`` to ``"error"`` + stores the exception repr,
    then re-raises — letting a test assert ERROR status without an OTel SDK.
    """

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
        parent = trace_context or TraceContext.create_root()
        child = TraceContext(
            trace_id=parent.trace_id,
            span_id=uuid4().hex[:16],
            parent_span_id=parent.span_id,
            tenant_id=parent.tenant_id,
            user_id=parent.user_id,
            session_id=parent.session_id,
            baggage=dict(parent.baggage),
        )
        record: dict[str, Any] = {
            "name": name,
            "category": category.value,
            # BY REFERENCE so the loop's post-response token writes into the
            # shared llm_attrs dict are visible to the test after the run.
            "attributes": attributes if attributes is not None else {},
            "span_id": child.span_id,
            "parent_span_id": child.parent_span_id,
            "status": "ok",
            "exception": None,
        }
        self.spans.append(record)
        try:
            yield child
        except Exception as exc:  # noqa: BLE001 — mirror OTelTracer ERROR capture
            record["status"] = "error"
            record["exception"] = repr(exc)
            raise

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


def _children_of(spans: list[dict[str, Any]], parent_span_id: str | None) -> list[dict[str, Any]]:
    """Return spans whose parent_span_id == the given span_id (tree helper)."""
    return [s for s in spans if s["parent_span_id"] == parent_span_id]


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


# ===========================================================================
# Sprint 57.71 (A-4 Tier 1, Stage 2): reconstructable LOOP→TURN→operation tree
# ===========================================================================


class _RaisingChatClient(MockChatClient):
    """MockChatClient that raises a (non-Cancelled) exception on chat().

    Used to drive an exception THROUGH the loop's LLM_CALL span `async with`
    body so the RecordingTracer can capture ERROR span status — the production
    OTelTracer's record_exception + set_status(ERROR) path, exercised without
    an OTel SDK. (Tool-handler crashes don't work for this: ToolExecutorImpl
    catches them internally → ToolResult(success=False), so nothing propagates
    through the loop's TOOL_EXEC span.)
    """

    async def chat(
        self,
        request: Any,
        *,
        cache_breakpoints: Any = None,
        trace_context: Any = None,
    ) -> ChatResponse:
        raise RuntimeError("boom in chat")


def _build_loop(rec: Tracer, responses: list[ChatResponse]) -> AgentLoopImpl:
    """Echo-tool loop wired with the given tracer + canned chat responses."""
    registry, _ = make_echo_executor()
    executor = ToolExecutorImpl(
        registry=registry,
        handlers={"echo_tool": _shared_echo_handler},
        tracer=rec,
        metric_registry=MetricRegistry(),
    )
    chat = MockChatClient(responses=responses)
    return AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(tracer=rec),
        tool_executor=executor,
        tool_registry=registry,
        tracer=rec,
    )


@pytest.mark.asyncio
async def test_reconstructs_loop_turn_operation_tree_with_correct_nesting() -> None:
    """A 2-turn + 1-tool run must reconstruct LOOP→(2× TURN)→{LLM_CALL, TOOL_EXEC}
    with parent/child nesting correct: TURN's parent is LOOP; each LLM_CALL /
    TOOL_EXEC's parent is its OWN TURN, NOT the root LOOP (the D1 nesting fix)."""
    rec = RecordingTracer()
    loop = _build_loop(
        rec,
        responses=[
            ChatResponse(
                model="m",
                content="calling",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": "x"})],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(model="m", content="done", stop_reason=StopReason.END_TURN),
        ],
    )
    [ev async for ev in loop.run(session_id=uuid4(), user_input="echo x")]

    spans = rec.spans

    # --- Root LOOP span: exactly one, no parent among recorded spans. ---
    loop_spans = [s for s in spans if s["attributes"].get("span_type") == "LOOP"]
    assert len(loop_spans) == 1
    root = loop_spans[0]
    assert root["name"] == "agent_loop.run"
    recorded_ids = {s["span_id"] for s in spans}
    assert root["parent_span_id"] not in recorded_ids  # root's parent is the request ctx

    # --- TURN spans: 2, both children of the root LOOP span. ---
    turn_spans = [s for s in spans if s["attributes"].get("span_type") == "TURN"]
    assert len(turn_spans) == 2
    assert all(
        t["parent_span_id"] == root["span_id"] for t in turn_spans
    ), "every TURN must nest under LOOP (not be a flat sibling — the D1 bug)"
    # Turn numbers are 0 then 1 (per-turn attribute carried).
    assert sorted(t["attributes"]["turn"] for t in turn_spans) == [0, 1]
    turn_ids = {t["span_id"] for t in turn_spans}

    # --- LLM_CALL spans: 2, each a child of a TURN (never the root LOOP). ---
    llm_spans = [s for s in spans if s["attributes"].get("span_type") == "LLM_CALL"]
    assert len(llm_spans) == 2
    assert all(
        s["parent_span_id"] in turn_ids for s in llm_spans
    ), "LLM_CALL must nest under its TURN, not the root LOOP"
    assert all(s["parent_span_id"] != root["span_id"] for s in llm_spans)

    # --- TOOL_EXEC span: 1 (turn 0 only), child of turn 0's TURN span. ---
    tool_spans = [s for s in spans if s["attributes"].get("span_type") == "TOOL_EXEC"]
    assert len(tool_spans) == 1
    assert tool_spans[0]["name"] == "agent_loop.tool.echo_tool"
    assert tool_spans[0]["parent_span_id"] in turn_ids
    assert tool_spans[0]["parent_span_id"] != root["span_id"]

    # --- Tree helper round-trips: LOOP has exactly the 2 TURN children among
    #     the loop's own spans (LLM_CALL/TOOL_EXEC parent to TURN, not LOOP). ---
    loop_own_span_types = {"LOOP", "TURN", "LLM_CALL", "TOOL_EXEC", "PROMPT_BUILD", "COMPACTION"}
    loop_own = [s for s in spans if s["attributes"].get("span_type") in loop_own_span_types]
    loop_children = _children_of(loop_own, root["span_id"])
    assert {c["attributes"]["span_type"] for c in loop_children} == {"TURN"}
    assert len(loop_children) == 2
    # Each TURN's loop-own children are exactly {LLM_CALL} on the END_TURN turn
    # and {LLM_CALL, TOOL_EXEC} on the tool-use turn.
    child_type_sets = sorted(
        (
            tuple(
                sorted(c["attributes"]["span_type"] for c in _children_of(loop_own, t["span_id"]))
            )
            for t in turn_spans
        )
    )
    assert child_type_sets == [("LLM_CALL",), ("LLM_CALL", "TOOL_EXEC")]


@pytest.mark.asyncio
async def test_llm_call_span_carries_token_attrs_tool_span_carries_tool_attr() -> None:
    """LLM_CALL spans carry post-response TokenUsage (observed via the shared
    attrs dict, recorded by reference); TOOL_EXEC carries the tool name."""
    rec = RecordingTracer()
    loop = _build_loop(
        rec,
        responses=[
            ChatResponse(
                model="m",
                content="calling",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": "x"})],
                stop_reason=StopReason.TOOL_USE,
                usage=TokenUsage(
                    prompt_tokens=11,
                    completion_tokens=7,
                    cached_input_tokens=3,
                    total_tokens=18,
                ),
            ),
            ChatResponse(
                model="m",
                content="done",
                stop_reason=StopReason.END_TURN,
                usage=TokenUsage(prompt_tokens=5, completion_tokens=2, total_tokens=7),
            ),
        ],
    )
    [ev async for ev in loop.run(session_id=uuid4(), user_input="echo x")]

    llm_spans = [s for s in rec.spans if s["attributes"].get("span_type") == "LLM_CALL"]
    assert len(llm_spans) == 2
    # The recorded attributes dict is the same object the loop wrote tokens into
    # AFTER the response (by reference), so the post-response token attrs appear.
    first = llm_spans[0]["attributes"]
    # model attr comes from chat_client.model_info().model_name (MockChatClient
    # default "mock-model"), NOT the per-response ChatResponse.model field.
    assert first["model"] == "mock-model"
    assert first["prompt_tokens"] == 11
    assert first["completion_tokens"] == 7
    assert first["cached_input_tokens"] == 3
    assert first["total_tokens"] == 18

    tool_spans = [s for s in rec.spans if s["attributes"].get("span_type") == "TOOL_EXEC"]
    assert len(tool_spans) == 1
    assert tool_spans[0]["attributes"]["tool"] == "echo_tool"


@pytest.mark.asyncio
async def test_raised_exception_sets_error_span_status() -> None:
    """A chat() that raises propagates THROUGH the LLM_CALL span `async with`
    body → the RecordingTracer flips that span's status to ERROR (and the
    enclosing TURN + root LOOP spans too, as the exception unwinds)."""
    rec = RecordingTracer()
    registry, _ = make_echo_executor()
    executor = ToolExecutorImpl(
        registry=registry,
        handlers={"echo_tool": _shared_echo_handler},
        tracer=rec,
        metric_registry=MetricRegistry(),
    )
    loop = AgentLoopImpl(
        chat_client=_RaisingChatClient(),
        output_parser=OutputParserImpl(tracer=rec),
        tool_executor=executor,
        tool_registry=registry,
        tracer=rec,
    )

    with pytest.raises(RuntimeError, match="boom in chat"):
        [ev async for ev in loop.run(session_id=uuid4(), user_input="trigger")]

    # The LLM_CALL span must be recorded with ERROR status + exception repr.
    llm_spans = [s for s in rec.spans if s["attributes"].get("span_type") == "LLM_CALL"]
    assert len(llm_spans) == 1
    assert llm_spans[0]["status"] == "error"
    assert "boom in chat" in (llm_spans[0]["exception"] or "")

    # The exception unwinds through the enclosing TURN + root LOOP spans, so
    # those are ERROR too (the tracer catches on the way out of each).
    turn_spans = [s for s in rec.spans if s["attributes"].get("span_type") == "TURN"]
    assert turn_spans and all(t["status"] == "error" for t in turn_spans)
    loop_spans = [s for s in rec.spans if s["attributes"].get("span_type") == "LOOP"]
    assert loop_spans and loop_spans[0]["status"] == "error"


@pytest.mark.asyncio
async def test_zero_tool_turn_has_turn_and_llm_call_but_no_tool_exec() -> None:
    """A pure-LLM turn (END_TURN, no tool_calls) opens TURN + LLM_CALL but no
    TOOL_EXEC span."""
    rec = RecordingTracer()
    loop = _build_loop(
        rec,
        responses=[ChatResponse(model="m", content="hi", stop_reason=StopReason.END_TURN)],
    )
    [ev async for ev in loop.run(session_id=uuid4(), user_input="say hi")]

    span_types = [s["attributes"].get("span_type") for s in rec.spans]
    assert span_types.count("TURN") == 1
    assert span_types.count("LLM_CALL") == 1
    assert "TOOL_EXEC" not in span_types


@pytest.mark.asyncio
async def test_multi_tool_turn_has_sibling_tool_exec_spans_under_one_turn() -> None:
    """Two tool_calls in one turn → two sibling TOOL_EXEC spans under the SAME
    TURN span (parallel/multiple tools = siblings)."""
    rec = RecordingTracer()
    loop = _build_loop(
        rec,
        responses=[
            ChatResponse(
                model="m",
                content="multi",
                tool_calls=[
                    ToolCall(id="c1", name="echo_tool", arguments={"text": "a"}),
                    ToolCall(id="c2", name="echo_tool", arguments={"text": "b"}),
                ],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(model="m", content="end", stop_reason=StopReason.END_TURN),
        ],
    )
    [ev async for ev in loop.run(session_id=uuid4(), user_input="multi")]

    tool_spans = [s for s in rec.spans if s["attributes"].get("span_type") == "TOOL_EXEC"]
    assert len(tool_spans) == 2
    # Both siblings share one parent TURN span (the first / tool-use turn).
    parent_ids = {s["parent_span_id"] for s in tool_spans}
    assert len(parent_ids) == 1
    turn_ids = {s["span_id"] for s in rec.spans if s["attributes"].get("span_type") == "TURN"}
    assert parent_ids.issubset(turn_ids)


@pytest.mark.asyncio
async def test_noop_tracer_default_path_runs_without_spans() -> None:
    """The default (no tracer injected → NoOpTracer) path runs the loop with no
    errors. NoOpTracer records span names but does no I/O — the loop must behave
    identically (no exception, normal completion)."""
    registry, _ = make_echo_executor()
    executor = ToolExecutorImpl(
        registry=registry,
        handlers={"echo_tool": _shared_echo_handler},
        metric_registry=MetricRegistry(),
    )
    chat = MockChatClient(
        responses=[ChatResponse(model="m", content="ok", stop_reason=StopReason.END_TURN)]
    )
    # No `tracer=` kwarg → AgentLoopImpl falls back to NoOpTracer.
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
    )
    assert isinstance(loop._tracer, NoOpTracer)
    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hi")]
    assert events  # ran to completion, no exception
