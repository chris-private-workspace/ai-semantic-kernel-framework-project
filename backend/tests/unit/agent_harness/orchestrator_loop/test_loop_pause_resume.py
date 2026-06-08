"""
File: backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py
Purpose: Unit tests for 57.88 durable HITL pause-resume (deferred branch + resume()).
Category: Tests / 範疇 1 + 範疇 7 + §HITL Centralization
Scope: Phase 57 / Sprint 57.88 (US-1 / US-3) + Sprint 57.90 Slice 2 (multi-pause)

Description:
    Validates the Stage-1 backend core of the durable HITL pause-resume spike:
    - deferred ESCALATE branch: hitl_deferred=True + ESCALATE → checkpoint saved
      (with pending_approval payload) + LoopCompleted(awaiting_approval) +
      wait_for_decision NOT called + the pending tool NOT executed.
    - blocking-branch regression: hitl_deferred=False keeps 53.5 behavior
      (wait_for_decision called; APPROVED → tool executes).
    - HITLManager.get_decision: pending → None; decided → ApprovalDecision.
    - resume(): APPROVED → pending tool executes + loop continues to end_turn;
      REJECTED → GuardrailTriggered(block), tool NOT executed.
    - Sprint 57.90 Slice 2: resume() now drives the shared `_run_turns` (it emits
      a LOOP span) and a 2nd approval-required tool in the resumed continuation
      pauses AGAIN (multi-pause-per-run) — impossible with the old reduced copy.

Created: 2026-06-08 (Sprint 57.88)
Last Modified: 2026-06-08 (Sprint 57.90 Slice 2 — multi-pause test + LOOP-span assertion)
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Literal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StopReason, StreamEvent
from agent_harness._contracts import (
    ApprovalReceived,
    ApprovalRequested,
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    DurableState,
    ExecutionContext,
    GuardrailTriggered,
    LoopCompleted,
    LoopEvent,
    LoopState,
    Message,
    SpanStarted,
    StateVersion,
    TokenUsage,
    ToolCall,
    ToolCallExecuted,
    ToolSpec,
    TraceContext,
    TransientState,
)
from agent_harness._contracts.hitl import (
    ApprovalDecision,
    ApprovalRequest,
    DecisionType,
    HITLPolicy,
)
from agent_harness.guardrails._abc import (
    Guardrail,
    GuardrailAction,
    GuardrailResult,
    GuardrailType,
)
from agent_harness.guardrails.engine import GuardrailEngine
from agent_harness.hitl import HITLManager
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from agent_harness.orchestrator_loop.termination import TerminationReason
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl

pytestmark = pytest.mark.asyncio

_TENANT_ID = UUID("00000000-0000-0000-0000-000000000099")
_DATETIME_NOW = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)


# === Fakes ==================================================================


class FakeChatClient(ChatClient):
    """Returns canned (text, tool_calls?, stop_reason) tuples per chat() call."""

    def __init__(
        self,
        responses: list[tuple[str, list[ToolCall] | None, StopReason]],
    ) -> None:
        self._responses = responses
        self._idx = 0

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        if self._idx >= len(self._responses):
            raise RuntimeError("Loop ran more turns than fake responses")
        text, tool_calls, stop = self._responses[self._idx]
        self._idx += 1
        return ChatResponse(
            model="fake",
            content=text,
            tool_calls=tool_calls,
            stop_reason=stop,
            usage=TokenUsage(prompt_tokens=1, completion_tokens=1),
        )

    def stream(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        return self._dummy()

    async def _dummy(self) -> AsyncIterator[StreamEvent]:
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
            model_name="fake",
            model_family="fake",
            provider="fake",
            context_window=8192,
            max_output_tokens=4096,
        )


class EscalateGuardrail(Guardrail):
    """Always escalates — deterministically triggers the ESCALATE branch."""

    guardrail_type = GuardrailType.TOOL

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        return GuardrailResult(
            action=GuardrailAction.ESCALATE,
            reason="policy escalation",
            risk_level="HIGH",
        )


class SpyHITLManager(HITLManager):
    """Records calls; wait_for_decision flagged so we can assert it's NOT used
    in deferred mode. get_decision returns a configurable canned decision.
    """

    def __init__(self, *, decision: DecisionType | None = None) -> None:
        self._decision = decision
        self.requests: list[ApprovalRequest] = []
        self.wait_called = False
        self.get_decision_called = False

    async def request_approval(
        self,
        req: ApprovalRequest,
        *,
        trace_context: TraceContext | None = None,
    ) -> UUID:
        self.requests.append(req)
        return req.request_id

    async def get_pending(
        self,
        tenant_id: UUID,
        *,
        trace_context: TraceContext | None = None,
    ) -> list[ApprovalRequest]:
        return list(self.requests)

    async def decide(
        self,
        *,
        request_id: UUID,
        decision: ApprovalDecision,
        trace_context: TraceContext | None = None,
    ) -> None:
        self._decision = decision.decision

    async def wait_for_decision(
        self,
        request_id: UUID,
        *,
        timeout_s: int,
        trace_context: TraceContext | None = None,
    ) -> ApprovalDecision:
        self.wait_called = True
        assert self._decision is not None
        return ApprovalDecision(
            request_id=request_id,
            decision=self._decision,
            reviewer="reviewer@test",
            decided_at=_DATETIME_NOW,
            reason="canned",
        )

    async def get_decision(
        self,
        request_id: UUID,
        *,
        trace_context: TraceContext | None = None,
    ) -> ApprovalDecision | None:
        self.get_decision_called = True
        if self._decision is None:
            return None
        return ApprovalDecision(
            request_id=request_id,
            decision=self._decision,
            reviewer="reviewer@test",
            decided_at=_DATETIME_NOW,
            reason="canned",
        )

    async def get_policy(
        self,
        tenant_id: UUID,
        *,
        trace_context: TraceContext | None = None,
    ) -> HITLPolicy:
        return HITLPolicy(tenant_id=tenant_id)


class InMemoryReducer:
    """Minimal Reducer fake — bumps the version, ignores the update body."""

    async def merge(
        self,
        state: LoopState,
        update: dict[str, Any],
        *,
        source_category: str,
        trace_context: TraceContext | None = None,
    ) -> LoopState:
        return state


class InMemoryCheckpointer:
    """Minimal Checkpointer fake — keeps the last saved state in memory.

    Round-trips DurableState.metadata exactly like the production DBCheckpointer
    (the JSONB serializer persists metadata) so pending_approval survives.
    """

    def __init__(self) -> None:
        self.saved: list[LoopState] = []
        self._version = 0

    async def save(
        self,
        state: LoopState,
        *,
        trace_context: TraceContext | None = None,
    ) -> StateVersion:
        self._version += 1
        self.saved.append(state)
        return StateVersion(
            version=self._version,
            parent_version=self._version - 1 if self._version > 1 else None,
            created_at=_DATETIME_NOW,
            created_by_category=state.version.created_by_category,
        )

    async def load(
        self,
        *,
        version: int,
        trace_context: TraceContext | None = None,
    ) -> LoopState:
        return self.saved[version - 1]

    async def time_travel(
        self,
        *,
        target_version: int,
        trace_context: TraceContext | None = None,
    ) -> LoopState:
        return self.saved[target_version - 1]


# === Builders ===============================================================


def _registry_with_tool() -> ToolRegistryImpl:
    registry = ToolRegistryImpl()
    registry.register(
        ToolSpec(
            name="sensitive_tool",
            description="tool requiring approval",
            input_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
        )
    )
    return registry


class SpyExecutor(ToolExecutorImpl):
    """ToolExecutorImpl that records every executed call for assertions."""

    def __init__(self, registry: ToolRegistryImpl) -> None:
        async def _ok(call: ToolCall, context: ExecutionContext) -> Any:
            return "tool_executed_ok"

        super().__init__(registry=registry, handlers={"sensitive_tool": _ok})
        self.executed: list[ToolCall] = []

    async def execute(
        self,
        call: ToolCall,
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> Any:
        self.executed.append(call)
        return await super().execute(call, trace_context=trace_context, context=context)


def _executor(registry: ToolRegistryImpl) -> SpyExecutor:
    return SpyExecutor(registry)


def _build_loop(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager,
    hitl_deferred: bool,
    checkpointer: InMemoryCheckpointer | None = None,
    reducer: InMemoryReducer | None = None,
) -> tuple[AgentLoopImpl, SpyExecutor]:
    registry = _registry_with_tool()
    executor = _executor(registry)
    engine = GuardrailEngine()
    engine.register(EscalateGuardrail(), priority=10)
    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        guardrail_engine=engine,
        tenant_id=_TENANT_ID,
        hitl_manager=hitl_manager,
        hitl_deferred=hitl_deferred,
        checkpointer=checkpointer,  # type: ignore[arg-type]
        reducer=reducer,  # type: ignore[arg-type]
    )
    return loop, executor


def _chat_one_tool_call() -> FakeChatClient:
    return FakeChatClient(
        responses=[
            (
                "calling tool",
                [ToolCall(id="tc-1", name="sensitive_tool", arguments={"x": 42})],
                StopReason.TOOL_USE,
            ),
            ("done", None, StopReason.END_TURN),
        ],
    )


async def _run(loop: AgentLoopImpl) -> list[LoopEvent]:
    session_id = uuid4()
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    return [ev async for ev in loop.run(session_id=session_id, user_input="hi", trace_context=ctx)]


# === Tests: deferred branch (US-1) ==========================================


async def test_deferred_escalate_pauses_with_awaiting_approval() -> None:
    """hitl_deferred=True + ESCALATE → checkpoint saved + awaiting_approval +
    wait_for_decision NOT called + pending tool NOT executed."""
    chat = _chat_one_tool_call()
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_loop(
        chat_client=chat,
        hitl_manager=hitl,
        hitl_deferred=True,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    events = await _run(loop)

    # Terminal event is awaiting_approval.
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes, "expected a LoopCompleted"
    assert completes[-1].stop_reason == TerminationReason.AWAITING_APPROVAL.value

    # ApprovalRequested emitted.
    assert any(isinstance(e, ApprovalRequested) for e in events)

    # wait_for_decision NOT called (the whole point of deferred mode).
    assert hitl.wait_called is False

    # The pending tool was NOT executed (paused before exec).
    assert executor is not None
    # A checkpoint with pending_approval was persisted.
    pauses = [s for s in checkpointer.saved if "pending_approval" in s.durable.metadata]
    assert pauses, "expected a checkpoint carrying pending_approval"
    pa = pauses[-1].durable.metadata["pending_approval"]
    assert pa["tool_call"]["name"] == "sensitive_tool"
    assert pa["tool_call"]["arguments"] == {"x": 42}
    assert pa["tool_call"]["tool_call_id"] == "tc-1"
    assert "approval_request_id" in pa
    assert "turn" in pa


async def test_deferred_without_checkpointer_falls_back_to_blocking() -> None:
    """deferred=True but no checkpointer → cannot persist → blocking path used."""
    chat = _chat_one_tool_call()
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, _ = _build_loop(
        chat_client=chat,
        hitl_manager=hitl,
        hitl_deferred=True,
        checkpointer=None,
        reducer=None,
    )

    events = await _run(loop)

    # Fell back to blocking: wait_for_decision was called; no awaiting_approval.
    assert hitl.wait_called is True
    assert not any(
        isinstance(e, LoopCompleted) and e.stop_reason == TerminationReason.AWAITING_APPROVAL.value
        for e in events
    )


# === Tests: blocking-branch regression (US-1) ===============================


async def test_blocking_branch_unchanged_when_not_deferred() -> None:
    """hitl_deferred=False (default) → 53.5 blocking behavior preserved:
    wait_for_decision called; APPROVED → tool executes; ends end_turn."""
    chat = _chat_one_tool_call()
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_loop(
        chat_client=chat,
        hitl_manager=hitl,
        hitl_deferred=False,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    events = await _run(loop)

    assert hitl.wait_called is True
    assert executor.executed, "approved tool should have executed"
    assert executor.executed[0].name == "sensitive_tool"
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value
    # No awaiting_approval anywhere.
    assert not any(e.stop_reason == TerminationReason.AWAITING_APPROVAL.value for e in completes)


# === Tests: resume() (US-3) =================================================


def _paused_state(*, decision_session: UUID) -> LoopState:
    """Build a LoopState as a paused checkpoint would rehydrate it."""
    return LoopState(
        transient=TransientState(
            messages=[
                Message(role="user", content="please act"),
                Message(
                    role="assistant",
                    content="calling tool",
                    tool_calls=[ToolCall(id="tc-1", name="sensitive_tool", arguments={"x": 42})],
                ),
            ],
            current_turn=1,
            token_usage_so_far=2,
        ),
        durable=DurableState(
            session_id=decision_session,
            tenant_id=_TENANT_ID,
            metadata={
                "pending_approval": {
                    "tool_call": {
                        "name": "sensitive_tool",
                        "arguments": {"x": 42},
                        "tool_call_id": "tc-1",
                    },
                    "approval_request_id": str(uuid4()),
                    "turn": 1,
                }
            },
        ),
        version=StateVersion(
            version=1,
            parent_version=None,
            created_at=_DATETIME_NOW,
            created_by_category="orchestrator_loop:hitl_pause",
        ),
    )


def _build_resume_loop(
    *, chat_client: ChatClient, hitl_manager: HITLManager
) -> tuple[AgentLoopImpl, SpyExecutor]:
    registry = _registry_with_tool()
    executor = _executor(registry)
    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        tenant_id=_TENANT_ID,
        hitl_manager=hitl_manager,
    )
    return loop, executor


async def test_resume_approved_executes_tool_and_continues() -> None:
    """resume() APPROVED → pending tool executes → loop continues to end_turn."""
    session_id = uuid4()
    # After the resumed tool result is appended, the LLM ends the turn.
    chat = FakeChatClient(responses=[("final answer", None, StopReason.END_TURN)])
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    assert hitl.get_decision_called is True
    # ApprovalReceived(APPROVED) emitted.
    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert received and received[0].decision == DecisionType.APPROVED.value
    # Pending tool executed.
    assert executor.executed and executor.executed[0].name == "sensitive_tool"
    # Tool execution event present.
    assert any(isinstance(e, ToolCallExecuted) for e in events)
    # Continued to end_turn.
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value
    # Sprint 57.90 Slice 2: the continuation runs through the shared _run_turns,
    # so a LOOP span brackets it (the deleted _resume_continuation emitted none).
    assert any(
        isinstance(e, SpanStarted) and e.span_type == "LOOP" for e in events
    ), "resume() should drive _run_turns inside a LOOP span"


async def test_resume_rejected_blocks_tool() -> None:
    """resume() REJECTED → GuardrailTriggered(block) → tool NOT executed."""
    session_id = uuid4()
    # No chat responses needed; reject path never calls the LLM.
    chat = FakeChatClient(responses=[])
    hitl = SpyHITLManager(decision=DecisionType.REJECTED)
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    # GuardrailTriggered(block) emitted.
    blocks = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert blocks and blocks[0].action == "block"
    # Tool NOT executed.
    assert not executor.executed
    # Terminated guardrail_blocked.
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.GUARDRAIL_BLOCKED.value


async def test_resume_undecided_terminates_error() -> None:
    """resume() when decision still pending (get_decision → None) → ERROR."""
    session_id = uuid4()
    chat = FakeChatClient(responses=[])
    hitl = SpyHITLManager(decision=None)  # undecided
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.ERROR.value
    assert not executor.executed


# === Tests: multi-pause-per-run (57.90 Slice 2) =============================


def _build_resume_loop_multipause(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager,
    checkpointer: InMemoryCheckpointer,
    reducer: InMemoryReducer,
) -> tuple[AgentLoopImpl, SpyExecutor]:
    """A resume loop wired for the deferred-pause machinery (Sprint 57.90).

    Unlike `_build_resume_loop`, this wires the ESCALATE guardrail + hitl_deferred
    + checkpointer/reducer so a 2nd approval-required tool requested DURING the
    resumed continuation re-enters `_cat9_hitl_branch`'s deferred branch and pauses
    again — the multi-pause-per-run behavior that only exists because resume() now
    drives the shared `_run_turns` (the deleted `_resume_continuation` reduced copy
    had no Cat 9 per-tool path, so it executed the 2nd tool silently).
    """
    registry = _registry_with_tool()
    executor = _executor(registry)
    engine = GuardrailEngine()
    engine.register(EscalateGuardrail(), priority=10)
    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        guardrail_engine=engine,
        tenant_id=_TENANT_ID,
        hitl_manager=hitl_manager,
        hitl_deferred=True,
        checkpointer=checkpointer,  # type: ignore[arg-type]
        reducer=reducer,  # type: ignore[arg-type]
    )
    return loop, executor


async def test_resume_continuation_can_pause_again() -> None:
    """Sprint 57.90 Slice 2 (multi-pause-per-run): after resume() executes the 1st
    pre-approved pending tool, the resumed continuation requests a 2nd
    approval-required tool → it ESCALATEs → the loop pauses AGAIN (a NEW
    pending_approval checkpoint + LoopCompleted(awaiting_approval)) instead of
    silently executing it (the one-approval-per-run limitation of the deleted
    `_resume_continuation`). Only possible because resume() drives the shared
    `_run_turns` which carries the Cat 9 deferred branch.
    """
    session_id = uuid4()
    # The resumed continuation's first LLM turn requests a 2nd approval tool.
    chat = FakeChatClient(
        responses=[
            (
                "calling tool again",
                [ToolCall(id="tc-2", name="sensitive_tool", arguments={"x": 7})],
                StopReason.TOOL_USE,
            ),
        ],
    )
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)  # the 1st pending is approved
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_resume_loop_multipause(
        chat_client=chat,
        hitl_manager=hitl,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    state = _paused_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    # The 1st pending tool (tc-1) executed once (pre-approved, outside _run_turns).
    assert executor.executed and executor.executed[0].id == "tc-1"
    # The 2nd tool (tc-2) was NOT executed — it paused before exec.
    assert all(c.id != "tc-2" for c in executor.executed)
    # The resumed continuation paused AGAIN (multi-pause).
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.AWAITING_APPROVAL.value
    # A NEW checkpoint carrying the 2nd tool's pending_approval was persisted.
    pauses = [s for s in checkpointer.saved if "pending_approval" in s.durable.metadata]
    assert pauses, "expected a 2nd pause checkpoint"
    assert pauses[-1].durable.metadata["pending_approval"]["tool_call"]["tool_call_id"] == "tc-2"
    # The 2nd pause re-requested approval (deferred) for the new tool.
    assert any(isinstance(e, ApprovalRequested) for e in events)


# === Tests: HITLManager.get_decision (US-3) =================================


async def test_get_decision_pending_returns_none() -> None:
    hitl = SpyHITLManager(decision=None)
    assert await hitl.get_decision(uuid4()) is None


async def test_get_decision_decided_returns_decision() -> None:
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    decision = await hitl.get_decision(uuid4())
    assert decision is not None
    assert decision.decision == DecisionType.APPROVED
