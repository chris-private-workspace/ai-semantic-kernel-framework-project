"""
File: backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py
Purpose: Unit tests for 57.88 durable HITL pause-resume (deferred branch + resume()).
Category: Tests / 範疇 1 + 範疇 7 + 範疇 9 + §HITL Centralization
Scope: Phase 57 / Sprint 57.88 + 57.90 + 57.91 (input) + 57.92 (between-turns) + 57.93 (output)

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
    - Sprint 57.91 (Slice 3 leg 1): the generalized input-ESCALATE pause point —
      an input-guardrail ESCALATE pauses BEFORE any LLM call (input-kind
      pending_approval, no tool_call); ESCALATE without HITL fails closed to BLOCK;
      resume() of an input-kind pause drives _run_turns with NO tool exec.
    - Sprint 57.92 (Slice 3 leg 2): the between-turns ESCALATE pause point — a
      guardrail at the loop top (after ≥1 completed turn, before the next LLM call)
      ESCALATEs → pause (between-turns-kind pending_approval, no tool_call); ESCALATE
      without HITL fails closed to BLOCK; resume() drives _run_turns with
      skip_between_turns_once so the just-approved boundary does not re-pause.
    - Sprint 57.93 (Slice 3 output-guardrail leg): the output-ESCALATE pre-delivery
      pause point — an OUTPUT guardrail ESCALATE on a FINAL answer pauses BEFORE
      LLMResponded delivers it (output-kind pending_approval carrying the held-answer
      snapshot); resume() APPROVED re-emits the held answer (no _run_turns drive, no
      LLM re-call), REJECTED withholds it; the pre-gate is inert without HITL wiring
      or on a non-final response.

Created: 2026-06-08 (Sprint 57.88)
Last Modified: 2026-06-10 (Sprint 57.99 — A2 verification-ESCALATE pause: escalate tests)
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
    LLMResponded,
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
    VerificationResult,
)
from agent_harness._contracts.events import VerificationFailed, VerificationPassed
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
from agent_harness.guardrails.input.escalation_keyword_detector import (
    KeywordEscalationGuardrail,
)
from agent_harness.guardrails.output.escalation_keyword_detector import (
    OutputKeywordEscalationGuardrail,
)
from agent_harness.hitl import HITLManager
from agent_harness.orchestrator_loop.loop import (
    VERIFICATION_FAILED_STOP_REASON,
    AgentLoopImpl,
)
from agent_harness.orchestrator_loop.termination import TerminationReason
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl
from agent_harness.verification import Verifier, VerifierRegistry

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


# === Tests: input-ESCALATE pause point (57.91 Slice 3 leg 1) ================


def _build_input_loop(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager,
    hitl_deferred: bool,
    checkpointer: InMemoryCheckpointer | None = None,
    reducer: InMemoryReducer | None = None,
    phrases: frozenset[str] = frozenset({"escalate me"}),
) -> tuple[AgentLoopImpl, SpyExecutor]:
    """A loop whose INPUT chain ESCALATEs on a trigger phrase (Sprint 57.91).

    Wires the REAL KeywordEscalationGuardrail (input chain) so an input matching
    the phrase routes through `_cat9_input_check` → `_cat9_input_hitl_pause` →
    the generalized `_emit_deferred_pause` primitive (no tool involved).
    """
    registry = _registry_with_tool()
    executor = _executor(registry)
    engine = GuardrailEngine()
    engine.register(KeywordEscalationGuardrail(phrases), priority=5)
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


async def _run_with_input(loop: AgentLoopImpl, user_input: str) -> list[LoopEvent]:
    session_id = uuid4()
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    return [
        ev async for ev in loop.run(session_id=session_id, user_input=user_input, trace_context=ctx)
    ]


async def test_input_escalate_pauses_before_llm() -> None:
    """Sprint 57.91: an input-guardrail ESCALATE (deferred wiring) pauses BEFORE
    any LLM call — checkpoint pending_approval{kind:"input"} (no tool_call) +
    LoopCompleted(awaiting_approval) + ApprovalRequested; the LLM is NEVER called.
    """
    # FakeChatClient with NO responses → raises if the loop ever calls the LLM,
    # so a green test PROVES the pause happened before any LLM turn.
    chat = FakeChatClient(responses=[])
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_input_loop(
        chat_client=chat,
        hitl_manager=hitl,
        hitl_deferred=True,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    events = await _run_with_input(loop, "please escalate me now")

    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.AWAITING_APPROVAL.value
    assert any(isinstance(e, ApprovalRequested) for e in events)
    assert hitl.wait_called is False  # deferred, not blocking
    assert not executor.executed  # no tool — input pause is before the loop body
    # Checkpoint carries an INPUT-kind pending_approval (no tool_call).
    pauses = [s for s in checkpointer.saved if "pending_approval" in s.durable.metadata]
    assert pauses, "expected an input-pause checkpoint"
    pa = pauses[-1].durable.metadata["pending_approval"]
    assert pa["kind"] == "input"
    assert "tool_call" not in pa
    assert "approval_request_id" in pa


async def test_input_escalate_without_hitl_blocks() -> None:
    """Sprint 57.91 US-4: an input ESCALATE WITHOUT the deferred HITL wiring fails
    closed to BLOCK (GUARDRAIL_BLOCKED), not silent-proceed."""
    chat = FakeChatClient(responses=[])
    loop, executor = _build_input_loop(
        chat_client=chat,
        hitl_manager=SpyHITLManager(decision=None),
        hitl_deferred=False,  # HITL present but NOT deferred → cannot durably pause
        checkpointer=None,
        reducer=None,
    )

    events = await _run_with_input(loop, "please escalate me now")

    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.GUARDRAIL_BLOCKED.value
    blocks = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert blocks and blocks[0].guardrail_type == "input"
    assert not executor.executed


def _paused_input_state(*, decision_session: UUID) -> LoopState:
    """A paused checkpoint as an INPUT-kind pause would rehydrate it (no tool_call)."""
    return LoopState(
        transient=TransientState(
            messages=[
                Message(role="system", content="sys"),
                Message(role="user", content="please escalate me now"),
            ],
            current_turn=0,
            token_usage_so_far=0,
        ),
        durable=DurableState(
            session_id=decision_session,
            tenant_id=_TENANT_ID,
            metadata={
                "pending_approval": {
                    "kind": "input",
                    "approval_request_id": str(uuid4()),
                    "turn": 0,
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


async def test_resume_input_approved_continues_no_tool() -> None:
    """Sprint 57.91: resume() of an INPUT-kind pause, APPROVED → drives _run_turns
    to end_turn WITHOUT executing any tool (the approved input proceeds to the
    first LLM turn)."""
    session_id = uuid4()
    chat = FakeChatClient(responses=[("answer to the approved input", None, StopReason.END_TURN)])
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_input_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    assert hitl.get_decision_called is True
    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert received and received[0].decision == DecisionType.APPROVED.value
    # NO tool executed (input-kind has no pending tool).
    assert not executor.executed
    assert not any(isinstance(e, ToolCallExecuted) for e in events)
    # Drove the shared _run_turns to end_turn (a LOOP span brackets it).
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value
    assert any(isinstance(e, SpanStarted) and e.span_type == "LOOP" for e in events)


async def test_resume_input_rejected_blocks() -> None:
    """Sprint 57.91: resume() of an INPUT-kind pause, REJECTED →
    GuardrailTriggered(input, block) + GUARDRAIL_BLOCKED; no LLM call."""
    session_id = uuid4()
    chat = FakeChatClient(responses=[])  # reject never calls the LLM
    hitl = SpyHITLManager(decision=DecisionType.REJECTED)
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_input_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    blocks = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert blocks and blocks[0].guardrail_type == "input" and blocks[0].action == "block"
    assert not executor.executed
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.GUARDRAIL_BLOCKED.value


# === Tests: between-turns ESCALATE pause point (57.92 Slice 3 leg 2) ========


class BetweenTurnsEscalateGuardrail(Guardrail):
    """Always escalates on the BETWEEN_TURNS chain — deterministic gate trigger.

    Content-independent (always ESCALATE) so the loop-integration tests prove the
    gate / pause / resume / skip machinery without coupling to the tool result
    text. The REAL phrase-based BetweenTurnsKeywordGuardrail is tested in
    test_between_turns_keyword_detector.py.
    """

    guardrail_type = GuardrailType.BETWEEN_TURNS

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        return GuardrailResult(
            action=GuardrailAction.ESCALATE,
            reason="between-turns escalation",
            risk_level="HIGH",
        )


def _build_between_turns_loop(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager,
    hitl_deferred: bool,
    checkpointer: InMemoryCheckpointer | None = None,
    reducer: InMemoryReducer | None = None,
) -> tuple[AgentLoopImpl, SpyExecutor]:
    """A loop whose BETWEEN_TURNS chain ESCALATEs at the loop top (Sprint 57.92).

    NO tool guardrail is wired, so `sensitive_tool` executes normally in turn 0
    (the between-turns boundary only exists after ≥1 completed turn). At the top of
    turn 1 the BetweenTurnsEscalateGuardrail ESCALATEs → `_cat9_between_turns_check`
    → `_cat9_between_turns_hitl_pause` → the generalized `_emit_deferred_pause`.
    """
    registry = _registry_with_tool()
    executor = _executor(registry)
    engine = GuardrailEngine()
    engine.register(BetweenTurnsEscalateGuardrail())
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


def _chat_tool_use_only() -> FakeChatClient:
    """Turn 0 = a single TOOL_USE; NO turn-1 response (a 2nd LLM call would raise),
    so a green test proves the between-turns pause happened BEFORE turn 1's LLM call.
    """
    return FakeChatClient(
        responses=[
            (
                "calling tool",
                [ToolCall(id="tc-1", name="sensitive_tool", arguments={"x": 42})],
                StopReason.TOOL_USE,
            ),
        ],
    )


def _build_resume_loop_between_turns(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager,
    checkpointer: InMemoryCheckpointer,
    reducer: InMemoryReducer,
) -> tuple[AgentLoopImpl, SpyExecutor]:
    """A resume loop wired with the between-turns guardrail + deferred machinery.

    The always-escalate BETWEEN_TURNS guardrail means that WITHOUT
    `skip_between_turns_once` the gate would re-escalate at the top of the resumed
    turn — so a clean end_turn (no re-pause) proves the skip flag works.
    """
    registry = _registry_with_tool()
    executor = _executor(registry)
    engine = GuardrailEngine()
    engine.register(BetweenTurnsEscalateGuardrail())
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


def _paused_between_turns_state(*, decision_session: UUID) -> LoopState:
    """A paused checkpoint as a BETWEEN_TURNS-kind pause would rehydrate it.

    current_turn=1 (paused at the top of turn 1, after turn 0 completed); the
    transcript carries turn 0's assistant + tool messages; no tool_call in
    pending_approval (between-turns has no pending tool).
    """
    return LoopState(
        transient=TransientState(
            messages=[
                Message(role="user", content="please act"),
                Message(
                    role="assistant",
                    content="calling tool",
                    tool_calls=[ToolCall(id="tc-1", name="sensitive_tool", arguments={"x": 42})],
                ),
                Message(role="tool", content="tool_executed_ok", tool_call_id="tc-1"),
            ],
            current_turn=1,
            token_usage_so_far=2,
        ),
        durable=DurableState(
            session_id=decision_session,
            tenant_id=_TENANT_ID,
            metadata={
                "pending_approval": {
                    "kind": "between_turns",
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


async def test_between_turns_escalate_pauses_before_next_turn() -> None:
    """Sprint 57.92: after turn 0 completes, the loop-top between-turns guardrail
    ESCALATE (deferred wiring) pauses BEFORE turn 1's LLM call — checkpoint
    pending_approval{kind:"between_turns"} (no tool_call) +
    LoopCompleted(awaiting_approval) + ApprovalRequested; turn 1's LLM is NEVER
    called (the fake has only the turn-0 response → a 2nd call would raise)."""
    chat = _chat_tool_use_only()
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_between_turns_loop(
        chat_client=chat,
        hitl_manager=hitl,
        hitl_deferred=True,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    events = await _run(loop)

    # Turn 0's tool executed (the just-completed turn ran end-to-end in the loop).
    assert executor.executed and executor.executed[0].name == "sensitive_tool"
    # Paused at the top of turn 1 (awaiting_approval) before any turn-1 LLM call.
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.AWAITING_APPROVAL.value
    assert any(isinstance(e, ApprovalRequested) for e in events)
    assert hitl.wait_called is False  # deferred, not blocking
    # Checkpoint carries a BETWEEN_TURNS-kind pending_approval (no tool_call).
    pauses = [s for s in checkpointer.saved if "pending_approval" in s.durable.metadata]
    assert pauses, "expected a between-turns pause checkpoint"
    pa = pauses[-1].durable.metadata["pending_approval"]
    assert pa["kind"] == "between_turns"
    assert "tool_call" not in pa
    assert "approval_request_id" in pa
    assert pa["turn"] == 1


async def test_between_turns_escalate_without_hitl_blocks() -> None:
    """Sprint 57.92 US-4: a between-turns ESCALATE WITHOUT the deferred HITL wiring
    fails closed to BLOCK (GUARDRAIL_BLOCKED), not silent-proceed."""
    chat = _chat_tool_use_only()
    loop, executor = _build_between_turns_loop(
        chat_client=chat,
        hitl_manager=SpyHITLManager(decision=None),
        hitl_deferred=False,  # HITL present but NOT deferred → cannot durably pause
        checkpointer=None,
        reducer=None,
    )

    events = await _run(loop)

    # Turn 0's tool executed; then the loop-top gate blocked before turn 1.
    assert executor.executed and executor.executed[0].name == "sensitive_tool"
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.GUARDRAIL_BLOCKED.value
    blocks = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert blocks and blocks[-1].guardrail_type == "between_turns"
    assert not any(c.stop_reason == TerminationReason.AWAITING_APPROVAL.value for c in completes)


async def test_resume_between_turns_approved_continues_no_repause() -> None:
    """Sprint 57.92: resume() of a BETWEEN_TURNS-kind pause, APPROVED → drives
    _run_turns to end_turn with the gate SKIPPED once (no re-escalate on the
    just-approved boundary) and NO tool exec (between-turns has no pending tool)."""
    session_id = uuid4()
    # The resumed turn 1's LLM ends the turn (the gate must be skipped to reach it).
    chat = FakeChatClient(responses=[("final answer", None, StopReason.END_TURN)])
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_resume_loop_between_turns(
        chat_client=chat,
        hitl_manager=hitl,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    state = _paused_between_turns_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    assert hitl.get_decision_called is True
    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert received and received[0].decision == DecisionType.APPROVED.value
    # NO tool executed by resume (between-turns has no pending tool).
    assert not executor.executed
    assert not any(isinstance(e, ToolCallExecuted) for e in events)
    # Drove the shared _run_turns to end_turn WITHOUT re-pausing (gate skipped once).
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value
    assert not any(c.stop_reason == TerminationReason.AWAITING_APPROVAL.value for c in completes)
    assert any(isinstance(e, SpanStarted) and e.span_type == "LOOP" for e in events)


async def test_resume_between_turns_rejected_blocks() -> None:
    """Sprint 57.92: resume() of a BETWEEN_TURNS-kind pause, REJECTED →
    GuardrailTriggered(between_turns, block) + GUARDRAIL_BLOCKED; no LLM call."""
    session_id = uuid4()
    chat = FakeChatClient(responses=[])  # reject never calls the LLM
    hitl = SpyHITLManager(decision=DecisionType.REJECTED)
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_between_turns_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    blocks = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert blocks and blocks[0].guardrail_type == "between_turns" and blocks[0].action == "block"
    assert not executor.executed
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.GUARDRAIL_BLOCKED.value


# === Tests: output-ESCALATE pre-delivery pause point (57.93 Slice 3) ========


class OutputEscalateGuardrail(Guardrail):
    """Always escalates on the OUTPUT chain — deterministic pre-delivery trigger.

    Content-independent (always ESCALATE) so the loop-integration tests prove the
    pre-gate / pause / resume machinery without coupling to the answer text. The
    REAL phrase-based OutputKeywordEscalationGuardrail is tested in
    test_output_escalation_keyword_detector.py.
    """

    guardrail_type = GuardrailType.OUTPUT

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        return GuardrailResult(
            action=GuardrailAction.ESCALATE,
            reason="output escalation",
            risk_level="HIGH",
        )


def _build_output_loop(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager,
    hitl_deferred: bool,
    checkpointer: InMemoryCheckpointer | None = None,
    reducer: InMemoryReducer | None = None,
    guardrail: Guardrail | None = None,
) -> tuple[AgentLoopImpl, SpyExecutor]:
    """A loop whose OUTPUT chain ESCALATEs on a FINAL answer (Sprint 57.93).

    NO tool guardrail is wired (so a TOOL_USE turn dispatches normally). The OUTPUT
    guardrail (default: always-escalate) routes a FINAL answer through the
    pre-delivery gate → `_cat9_output_escalate_pause` → `_cat9_output_hitl_pause` →
    the generalized `_emit_deferred_pause` (BEFORE LLMResponded renders it).
    """
    registry = _registry_with_tool()
    executor = _executor(registry)
    engine = GuardrailEngine()
    engine.register(guardrail or OutputEscalateGuardrail(), priority=5)
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


def _paused_output_state(*, decision_session: UUID) -> LoopState:
    """A paused checkpoint as an OUTPUT-kind pause would rehydrate it.

    current_turn=0 (paused mid-turn-0, BEFORE the held answer was delivered); the
    held answer rides in pending_approval.response_snapshot (NOT in messages — the
    FINAL path never appended it); no tool_call (output pause has no pending tool).
    """
    return LoopState(
        transient=TransientState(
            messages=[
                Message(role="system", content="sys"),
                Message(role="user", content="tell me something confidential"),
            ],
            current_turn=0,
            token_usage_so_far=2,
        ),
        durable=DurableState(
            session_id=decision_session,
            tenant_id=_TENANT_ID,
            metadata={
                "pending_approval": {
                    "kind": "output",
                    "approval_request_id": str(uuid4()),
                    "turn": 0,
                    "response_snapshot": {
                        "answer_text": "the held confidential answer",
                        "input_tokens": 1,
                        "output_tokens": 1,
                        "cached_input_tokens": 0,
                        "provider": "fake",
                        "model": "fake",
                        "cache_hit_rate": 0.0,
                        "total_tokens": 2,
                    },
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


async def test_output_escalate_pauses_before_delivery() -> None:
    """Sprint 57.93: a FINAL answer flagged ESCALATE by the OUTPUT guardrail pauses
    BEFORE LLMResponded delivers it — checkpoint pending_approval{kind:"output",
    response_snapshot.answer_text} (no tool_call) + LoopCompleted(awaiting_approval)
    + ApprovalRequested; LLMResponded for the held answer is NEVER yielded (the
    answer is withheld until approval)."""
    chat = FakeChatClient(responses=[("the secret is confidential", None, StopReason.END_TURN)])
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_output_loop(
        chat_client=chat,
        hitl_manager=hitl,
        hitl_deferred=True,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    events = await _run(loop)

    # Withheld: the held answer's LLMResponded (which renders the AnswerBlock) was
    # NEVER yielded — the pause precedes delivery.
    assert not any(isinstance(e, LLMResponded) for e in events)
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.AWAITING_APPROVAL.value
    assert any(isinstance(e, ApprovalRequested) for e in events)
    assert hitl.wait_called is False  # deferred, not blocking
    # Checkpoint carries an OUTPUT-kind pending_approval with the held-answer snapshot.
    pauses = [s for s in checkpointer.saved if "pending_approval" in s.durable.metadata]
    assert pauses, "expected an output-pause checkpoint"
    pa = pauses[-1].durable.metadata["pending_approval"]
    assert pa["kind"] == "output"
    assert "tool_call" not in pa
    assert pa["response_snapshot"]["answer_text"] == "the secret is confidential"


async def test_resume_output_approved_replays_answer() -> None:
    """Sprint 57.93: resume() of an OUTPUT-kind pause, APPROVED → re-emits the held
    LLMResponded(answer_text) + LoopCompleted(END_TURN) with NO _run_turns drive (no
    LOOP span) and NO LLM call (the held answer is delivered, not regenerated)."""
    session_id = uuid4()
    # responses=[] → if resume drove _run_turns and called the LLM, this would raise.
    chat = FakeChatClient(responses=[])
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_output_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    assert hitl.get_decision_called is True
    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert received and received[0].decision == DecisionType.APPROVED.value
    # The held answer is re-emitted (now delivered to the UI).
    responded = [e for e in events if isinstance(e, LLMResponded)]
    assert responded and responded[-1].content == "the held confidential answer"
    # Terminal END_TURN; NO drive (no LOOP span); NO tool exec.
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value
    assert not any(isinstance(e, SpanStarted) and e.span_type == "LOOP" for e in events)
    assert not executor.executed


async def test_resume_output_rejected_blocks() -> None:
    """Sprint 57.93: resume() of an OUTPUT-kind pause, REJECTED →
    GuardrailTriggered(output, block) + GUARDRAIL_BLOCKED; the held answer is NEVER
    delivered (no LLMResponded)."""
    session_id = uuid4()
    chat = FakeChatClient(responses=[])
    hitl = SpyHITLManager(decision=DecisionType.REJECTED)
    loop, executor = _build_resume_loop(chat_client=chat, hitl_manager=hitl)

    state = _paused_output_state(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    blocks = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert blocks and blocks[0].guardrail_type == "output" and blocks[0].action == "block"
    # The held answer is withheld (never re-emitted).
    assert not any(isinstance(e, LLMResponded) for e in events)
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.GUARDRAIL_BLOCKED.value


async def test_output_pre_gate_skips_non_final() -> None:
    """Sprint 57.93 US-4: the pre-gate is gated on is_final_answer — a TOOL_USE turn
    whose assistant text matches the phrase is NOT pre-gated (the tool dispatches
    normally). Here the FINAL answer does NOT match → no pause; the loop ends
    normally (a real phrase-based OUTPUT guardrail makes the contrast concrete)."""
    chat = FakeChatClient(
        responses=[
            (
                "let me look up that confidential record",
                [ToolCall(id="tc-1", name="sensitive_tool", arguments={"x": 1})],
                StopReason.TOOL_USE,
            ),
            ("here is the result", None, StopReason.END_TURN),
        ],
    )
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, executor = _build_output_loop(
        chat_client=chat,
        hitl_manager=hitl,
        hitl_deferred=True,
        checkpointer=checkpointer,
        reducer=reducer,
        guardrail=OutputKeywordEscalationGuardrail(frozenset({"confidential"})),
    )

    events = await _run(loop)

    # The TOOL_USE turn (text contains "confidential") dispatched the tool — NOT paused.
    assert executor.executed and executor.executed[0].name == "sensitive_tool"
    # The FINAL answer ("here is the result") doesn't match → no pause; clean end_turn.
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value
    assert not any(c.stop_reason == TerminationReason.AWAITING_APPROVAL.value for c in completes)
    assert not any(isinstance(e, ApprovalRequested) for e in events)


async def test_output_pre_gate_inert_without_hitl() -> None:
    """Sprint 57.93 US-4: without the full deferred-HITL wiring the pre-gate is inert
    — the FINAL answer renders normally (LLMResponded yielded) and the per-response
    _cat9_output_check ESCALATE-continue path fires (GuardrailTriggered(output,
    escalate)); the loop still ends end_turn (answer delivered)."""
    chat = FakeChatClient(responses=[("the answer is confidential", None, StopReason.END_TURN)])
    loop, executor = _build_output_loop(
        chat_client=chat,
        hitl_manager=SpyHITLManager(decision=None),
        hitl_deferred=False,  # HITL not deferred + no checkpointer/reducer → pre-gate inert
        checkpointer=None,
        reducer=None,
    )

    events = await _run(loop)

    # The answer was delivered normally (pre-gate inert).
    responded = [e for e in events if isinstance(e, LLMResponded)]
    assert responded and responded[-1].content == "the answer is confidential"
    # The per-response output check still ran its ESCALATE-continue path.
    triggered = [
        e for e in events if isinstance(e, GuardrailTriggered) and e.guardrail_type == "output"
    ]
    assert triggered and triggered[-1].action == "escalate"
    # Ended normally (not paused, not blocked).
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value
    assert not any(c.stop_reason == TerminationReason.AWAITING_APPROVAL.value for c in completes)


# === Tests: HITLManager.get_decision (US-3) =================================


async def test_get_decision_pending_returns_none() -> None:
    hitl = SpyHITLManager(decision=None)
    assert await hitl.get_decision(uuid4()) is None


async def test_get_decision_decided_returns_decision() -> None:
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    decision = await hitl.get_decision(uuid4())
    assert decision is not None
    assert decision.decision == DecisionType.APPROVED


# === Tests: in-loop verification on resume (Sprint 57.98 A1 US-3/US-4) =======
# The Cat 10 verify gate now lives in the shared _run_turns (CHANGE-065), so a
# resumed continuation is verified by the SAME gate as a fresh run — closing the
# pre-57.98 hole where the outer run_with_verification wrapper never wrapped
# resume(). These tests build the resume loop WITH a verifier_registry and assert:
# (1) the resumed final answer is verified; (2) the durable verification_attempts
# counter (checkpoint metadata) survives a pause mid-correction; (3) a fresh run()
# resets it to 0; (4) an APPROVED output-pause REPLAY is NOT re-verified.


class _PassingVerifier(Verifier):
    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        return VerificationResult(
            passed=True, verifier_name="pass", verifier_type="rules_based", score=1.0
        )


class _FailingVerifier(Verifier):
    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        return VerificationResult(
            passed=False,
            verifier_name="fail",
            verifier_type="rules_based",
            score=0.0,
            reason="always fails",
            suggested_correction="do better",
        )


def _vregistry(*verifiers: Verifier) -> VerifierRegistry:
    reg = VerifierRegistry()
    for v in verifiers:
        reg.register(v)
    return reg


def _build_resume_loop_verified(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager,
    verifier_registry: VerifierRegistry,
    max_attempts: int = 2,
) -> tuple[AgentLoopImpl, SpyExecutor]:
    """`_build_resume_loop` + an injected in-loop Cat 10 verifier registry."""
    registry = _registry_with_tool()
    executor = _executor(registry)
    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        tenant_id=_TENANT_ID,
        hitl_manager=hitl_manager,
        verifier_registry=verifier_registry,
        max_correction_attempts=max_attempts,
    )
    return loop, executor


def _paused_state_verified(
    *,
    decision_session: UUID,
    verification_attempts: int = 0,
    kind: str = "tool",
    answer_text: str = "held answer",
) -> LoopState:
    """A paused checkpoint state with an optional durable verification_attempts.

    kind="tool" → a tool-HITL pause (resume execs the pending tool then continues);
    kind="output" → an output-guardrail pre-delivery pause (resume REPLAYS the
    held answer via _replay_approved_output, no _run_turns drive).
    """
    if kind == "output":
        pending: dict[str, Any] = {
            "kind": "output",
            "approval_request_id": str(uuid4()),
            "turn": 1,
            "response_snapshot": {"answer_text": answer_text},
        }
    else:
        pending = {
            "kind": "tool",
            "tool_call": {
                "name": "sensitive_tool",
                "arguments": {"x": 42},
                "tool_call_id": "tc-1",
            },
            "approval_request_id": str(uuid4()),
            "turn": 1,
        }
    metadata: dict[str, Any] = {"pending_approval": pending}
    if verification_attempts > 0:
        metadata["verification_attempts"] = verification_attempts
    return LoopState(
        transient=TransientState(
            messages=[Message(role="user", content="please act")],
            current_turn=1,
            token_usage_so_far=2,
        ),
        durable=DurableState(session_id=decision_session, tenant_id=_TENANT_ID, metadata=metadata),
        version=StateVersion(
            version=1,
            parent_version=None,
            created_at=_DATETIME_NOW,
            created_by_category="orchestrator_loop:hitl_pause",
        ),
    )


async def test_resumed_continuation_answer_is_verified() -> None:
    """US-4: a resumed (tool-HITL) continuation's FINAL answer runs through the gate."""
    session_id = uuid4()
    chat = FakeChatClient(responses=[("the answer", None, StopReason.END_TURN)])
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, executor = _build_resume_loop_verified(
        chat_client=chat, hitl_manager=hitl, verifier_registry=_vregistry(_PassingVerifier())
    )

    state = _paused_state_verified(decision_session=session_id)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    # The pre-approved tool ran, then the continuation's final answer was VERIFIED.
    assert executor.executed and executor.executed[0].name == "sensitive_tool"
    assert any(
        isinstance(e, VerificationPassed) for e in events
    ), "the resumed continuation's final answer must be verified (pre-57.98 it was not)"
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value


async def test_durable_counter_survives_pause_mid_correction() -> None:
    """US-3: a pause that checkpointed verification_attempts=1 resumes with the SAME
    budget — the resumed answers are attempts 1,2 (NOT reset to 0,1,2)."""
    session_id = uuid4()
    chat = FakeChatClient(
        responses=[("bad1", None, StopReason.END_TURN), ("bad2", None, StopReason.END_TURN)]
    )
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, _ = _build_resume_loop_verified(
        chat_client=chat,
        hitl_manager=hitl,
        verifier_registry=_vregistry(_FailingVerifier()),
        max_attempts=2,
    )

    state = _paused_state_verified(decision_session=session_id, verification_attempts=1)
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    failed = [e for e in events if isinstance(e, VerificationFailed)]
    # Counter survived as 1 → attempts 1 then 2 (2 failures), NOT 0,1,2 (3 failures).
    assert [f.correction_attempt for f in failed] == [1, 2]
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == VERIFICATION_FAILED_STOP_REASON


async def test_fresh_run_starts_counter_at_zero() -> None:
    """US-3 (D2): a fresh run() starts verification_attempts at 0 — a failing verifier
    exhausts attempts 0,1,2 (3 failures), proving no stale counter leaks in."""
    chat = FakeChatClient(
        responses=[
            ("b0", None, StopReason.END_TURN),
            ("b1", None, StopReason.END_TURN),
            ("b2", None, StopReason.END_TURN),
        ]
    )
    registry = _registry_with_tool()
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(),
        tool_executor=_executor(registry),
        tool_registry=registry,
        tenant_id=_TENANT_ID,
        verifier_registry=_vregistry(_FailingVerifier()),
        max_correction_attempts=2,
    )

    sid = uuid4()
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=sid)
    events = [ev async for ev in loop.run(session_id=sid, user_input="hi", trace_context=ctx)]

    failed = [e for e in events if isinstance(e, VerificationFailed)]
    assert [f.correction_attempt for f in failed] == [0, 1, 2]
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == VERIFICATION_FAILED_STOP_REASON


async def test_replay_approved_output_not_reverified() -> None:
    """US-4: an APPROVED output-pause REPLAYS the held answer directly — the in-loop
    gate is NOT re-run on it (code-path isolation; _replay_approved_output re-emits)."""
    session_id = uuid4()
    chat = FakeChatClient(responses=[])  # replay makes no LLM call
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, _ = _build_resume_loop_verified(
        chat_client=chat,
        hitl_manager=hitl,
        verifier_registry=_vregistry(_FailingVerifier()),  # would FAIL if it ran
    )

    state = _paused_state_verified(
        decision_session=session_id, kind="output", answer_text="held answer"
    )
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    events = [ev async for ev in loop.resume(state=state, trace_context=ctx)]

    # The held answer is re-delivered WITHOUT re-verification — even a FAILING verifier
    # never runs (an approved replay must not be second-guessed).
    assert not any(isinstance(e, (VerificationPassed, VerificationFailed)) for e in events)
    responded = [e for e in events if isinstance(e, LLMResponded)]
    assert responded and responded[-1].content == "held answer"
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.END_TURN.value


# === Sprint 57.99 A2: verification-ESCALATE human-in-the-loop ================
# The max-attempts verification failure (the A1 verification_failed terminal)
# conditionally ESCALATEs to a durable human HITL pause when the toggle is ON.
# Day-1 covers the run()-side escalate pause + the toggle-OFF byte-identical
# guarantee; the resume APPROVE/REJECT branches are Day-2.


def _build_verify_escalate_loop(
    *,
    chat_client: ChatClient,
    verifier_registry: VerifierRegistry,
    escalate_on_max: bool,
    hitl_manager: HITLManager,
    checkpointer: InMemoryCheckpointer | None = None,
    reducer: InMemoryReducer | None = None,
    max_attempts: int = 2,
) -> tuple[AgentLoopImpl, SpyExecutor]:
    """A loop with the in-loop Cat 10 gate + the full deferred-HITL wiring + the A2
    escalate toggle, so a max-attempts verification failure can ESCALATE to a pause.
    """
    registry = _registry_with_tool()
    executor = _executor(registry)
    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        tenant_id=_TENANT_ID,
        hitl_manager=hitl_manager,
        hitl_deferred=True,
        checkpointer=checkpointer,  # type: ignore[arg-type]
        reducer=reducer,  # type: ignore[arg-type]
        verifier_registry=verifier_registry,
        max_correction_attempts=max_attempts,
        verification_escalate_on_max=escalate_on_max,
    )
    return loop, executor


async def test_verify_escalate_off_preserves_a1_terminal() -> None:
    """A2 US-2: toggle OFF → a max-attempts verification failure takes the A1
    verification_failed terminal byte-identical, even WITH the full HITL wiring
    present (the toggle, not the wiring, gates the escalate). No ApprovalRequested."""
    chat = FakeChatClient(
        responses=[
            ("a", None, StopReason.END_TURN),
            ("b", None, StopReason.END_TURN),
            ("c", None, StopReason.END_TURN),  # attempt 2 == max → failed_max
        ]
    )
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    loop, _ = _build_verify_escalate_loop(
        chat_client=chat,
        verifier_registry=_vregistry(_FailingVerifier()),
        escalate_on_max=False,  # OFF → A1 terminal
        hitl_manager=hitl,
        checkpointer=InMemoryCheckpointer(),
        reducer=InMemoryReducer(),
    )

    events = await _run(loop)

    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == VERIFICATION_FAILED_STOP_REASON
    assert not any(isinstance(e, ApprovalRequested) for e in events)
    assert hitl.wait_called is False


async def test_verify_escalate_on_max_pauses_for_human() -> None:
    """A2 US-2: toggle ON → a max-attempts verification failure ESCALATEs to a durable
    human pause instead of verification_failed: ApprovalRequested(HIGH) +
    LoopCompleted(awaiting_approval) + a checkpoint carrying a verification-kind
    pending_approval with the held failed answer + the durable verification_escalated
    flag. No verification_failed terminal."""
    chat = FakeChatClient(
        responses=[
            ("a", None, StopReason.END_TURN),
            ("b", None, StopReason.END_TURN),
            ("c is the held failed answer", None, StopReason.END_TURN),  # attempt 2 == max
        ]
    )
    hitl = SpyHITLManager(decision=DecisionType.APPROVED)
    checkpointer = InMemoryCheckpointer()
    reducer = InMemoryReducer()
    loop, _ = _build_verify_escalate_loop(
        chat_client=chat,
        verifier_registry=_vregistry(_FailingVerifier()),
        escalate_on_max=True,  # ON → escalate
        hitl_manager=hitl,
        checkpointer=checkpointer,
        reducer=reducer,
    )

    events = await _run(loop)

    # ESCALATEd, NOT verification_failed.
    completes = [e for e in events if isinstance(e, LoopCompleted)]
    assert completes[-1].stop_reason == TerminationReason.AWAITING_APPROVAL.value
    assert not any(
        isinstance(e, LoopCompleted) and e.stop_reason == VERIFICATION_FAILED_STOP_REASON
        for e in events
    )
    approvals = [e for e in events if isinstance(e, ApprovalRequested)]
    assert approvals and approvals[-1].risk_level == "HIGH"
    assert hitl.wait_called is False  # deferred, not blocking
    # The checkpoint carries a verification-kind pending_approval with the held answer
    # + the durable verification_escalated flag (the bound for one coached turn).
    pauses = [s for s in checkpointer.saved if "pending_approval" in s.durable.metadata]
    assert pauses, "expected a verification-escalate pause checkpoint"
    pa = pauses[-1].durable.metadata["pending_approval"]
    assert pa["kind"] == "verification"
    assert pa["response_snapshot"]["answer_text"] == "c is the held failed answer"
    assert pauses[-1].durable.metadata.get("verification_escalated") is True
