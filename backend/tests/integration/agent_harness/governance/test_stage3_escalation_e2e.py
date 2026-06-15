"""
File: backend/tests/integration/agent_harness/governance/test_stage3_escalation_e2e.py
Purpose: E2E tests for Cat 9 Stage 3 ESCALATE → AgentLoop → HITLManager wiring.
Category: Tests / Integration / Cat 9 + §HITL Centralization
Scope: Phase 53 / Sprint 53.5 US-3 (closes AD-Cat9-4)

Description:
    Verifies that when a ToolGuardrail escalates a tool call:
    - AgentLoop yields ApprovalRequested event
    - HITLManager.request_approval is called with correct payload
    - AgentLoop awaits wait_for_decision
    - On APPROVED → no GuardrailTriggered; tool executes normally
    - On REJECTED / ESCALATED → GuardrailTriggered(action=block) emitted; tool not executed
    - On TimeoutError from wait_for_decision → treated as REJECTED + audit
    - When hitl_manager is None (53.3 baseline) → ESCALATE is a soft block

Created: 2026-05-04 (Sprint 53.5 Day 2)

Modification History:
    - 2026-06-15: Sprint 57.122 — risk_level assertion HIGH→MEDIUM (policy-resolved risk)
    - 2026-05-04: Initial creation (Sprint 53.5 US-3 — closes AD-Cat9-4)
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    ExecutionContext,
    GuardrailTriggered,
    LoopCompleted,
    LoopEvent,
    Message,
    TokenUsage,
    ToolCall,
    ToolCallExecuted,
    ToolSpec,
    TraceContext,
)
from agent_harness._contracts.hitl import (
    ApprovalDecision,
    ApprovalRequest,
    DecisionType,
    HITLPolicy,
    RiskLevel,
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
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl

pytestmark = pytest.mark.asyncio


# === Fake ChatClient (mirrors test_loop_guardrails.py pattern) =============


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


# === Test fixtures ==========================================================


class EscalateGuardrail(Guardrail):
    """Always escalates. Used to deterministically trigger Stage 3."""

    guardrail_type = GuardrailType.TOOL

    def __init__(self, reason: str = "policy escalation") -> None:
        self._reason = reason

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        return GuardrailResult(
            action=GuardrailAction.ESCALATE,
            reason=self._reason,
            risk_level="HIGH",
        )


class FakeHITLManager(HITLManager):
    """Canned-decision HITLManager for e2e tests.

    Records every request_approval call so tests can assert payload shape.
    `decision_type` controls outcome; None → simulate TimeoutError.
    """

    def __init__(
        self,
        *,
        decision_type: DecisionType | None,
        timeout: bool = False,
    ) -> None:
        self._decision_type = decision_type
        self._timeout = timeout
        self.requests: list[ApprovalRequest] = []
        self.last_decision: ApprovalDecision | None = None

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
        self.last_decision = decision

    async def wait_for_decision(
        self,
        request_id: UUID,
        *,
        timeout_s: int,
        trace_context: TraceContext | None = None,
    ) -> ApprovalDecision:
        if self._timeout:
            raise TimeoutError(f"approval {request_id} not decided within {timeout_s}s")
        assert self._decision_type is not None
        return ApprovalDecision(
            request_id=request_id,
            decision=self._decision_type,
            reviewer="reviewer@test",
            decided_at=datetime.now(timezone.utc),
            reason=f"test {self._decision_type.value.lower()}",
        )

    async def get_decision(
        self,
        request_id: UUID,
        *,
        trace_context: TraceContext | None = None,
    ) -> ApprovalDecision | None:
        # Non-blocking: None when still pending (timeout sim), else canned.
        if self._timeout or self._decision_type is None:
            return None
        return ApprovalDecision(
            request_id=request_id,
            decision=self._decision_type,
            reviewer="reviewer@test",
            decided_at=datetime.now(timezone.utc),
            reason=f"test {self._decision_type.value.lower()}",
        )

    async def get_policy(
        self,
        tenant_id: UUID,
        *,
        trace_context: TraceContext | None = None,
    ) -> HITLPolicy:
        return HITLPolicy(tenant_id=tenant_id)


# === Loop builder ===========================================================


_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def _build_loop(
    *,
    chat_client: ChatClient,
    hitl_manager: HITLManager | None,
    hitl_timeout_s: int = 10,
) -> AgentLoopImpl:
    """Wire a loop with EscalateGuardrail + optional hitl_manager."""
    registry = ToolRegistryImpl()
    registry.register(
        ToolSpec(
            name="sensitive_tool",
            description="tool requiring approval",
            input_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
        )
    )

    async def _ok(call: ToolCall, context: ExecutionContext) -> Any:
        return "tool_executed_ok"

    executor = ToolExecutorImpl(registry=registry, handlers={"sensitive_tool": _ok})
    parser = OutputParserImpl()

    engine = GuardrailEngine()
    engine.register(EscalateGuardrail(), priority=10)

    return AgentLoopImpl(
        chat_client=chat_client,
        output_parser=parser,
        tool_executor=executor,
        tool_registry=registry,
        guardrail_engine=engine,
        tenant_id=_TENANT_ID,
        hitl_manager=hitl_manager,
        hitl_timeout_s=hitl_timeout_s,
    )


def _make_chat_with_one_tool_call(text: str = "calling tool") -> FakeChatClient:
    """Two-turn chat: turn 1 emits a tool_call, turn 2 ends naturally."""
    return FakeChatClient(
        responses=[
            (
                text,
                [ToolCall(id="tc-1", name="sensitive_tool", arguments={"x": 42})],
                StopReason.TOOL_USE,
            ),
            ("done", None, StopReason.END_TURN),
        ],
    )


async def _collect(loop: AgentLoopImpl, user_input: str) -> list[LoopEvent]:
    events: list[LoopEvent] = []
    session_id = uuid4()
    trace_ctx = TraceContext(tenant_id=_TENANT_ID, session_id=session_id)
    async for ev in loop.run(
        session_id=session_id,
        user_input=user_input,
        trace_context=trace_ctx,
    ):
        events.append(ev)
    return events


# === Tests ==================================================================


async def test_stage3_approved_tool_runs_normally() -> None:
    """ESCALATE → APPROVED → tool executes (no GuardrailTriggered emitted)."""
    chat = _make_chat_with_one_tool_call()
    hitl = FakeHITLManager(decision_type=DecisionType.APPROVED)
    loop = _build_loop(chat_client=chat, hitl_manager=hitl)

    events = await _collect(loop, user_input="please call sensitive tool")

    # Approval lifecycle events emitted.
    requested = [e for e in events if isinstance(e, ApprovalRequested)]
    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert len(requested) == 1, "expected one ApprovalRequested event"
    assert len(received) == 1, "expected one ApprovalReceived event"
    assert received[0].decision == "APPROVED"

    # No block event.
    blocks = [e for e in events if isinstance(e, GuardrailTriggered) and e.action == "block"]
    assert blocks == [], "APPROVED should not yield GuardrailTriggered(block)"

    # Tool actually executed.
    executed = [e for e in events if isinstance(e, ToolCallExecuted)]
    assert len(executed) == 1
    assert "tool_executed_ok" in (executed[0].result_content or "")

    # HITLManager received exactly one approval request with correct payload.
    assert len(hitl.requests) == 1
    req = hitl.requests[0]
    assert req.tenant_id == _TENANT_ID
    assert req.requester == "guardrails"
    # Sprint 57.122: the ApprovalRequest now carries the policy-resolved risk
    # (sensitive_tool's ToolSpec.risk_level defaults LOW + the requires_approval
    # MEDIUM-floor) instead of the pre-57.122 hardcoded RiskLevel.HIGH.
    assert req.risk_level == RiskLevel.MEDIUM
    assert req.payload["tool_name"] == "sensitive_tool"
    assert req.payload["tool_arguments"] == {"x": 42}


async def test_stage3_rejected_blocks_tool() -> None:
    """ESCALATE → REJECTED → GuardrailTriggered(block) + tool NOT executed."""
    chat = _make_chat_with_one_tool_call()
    hitl = FakeHITLManager(decision_type=DecisionType.REJECTED)
    loop = _build_loop(chat_client=chat, hitl_manager=hitl)

    events = await _collect(loop, user_input="please call sensitive tool")

    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert received[0].decision == "REJECTED"

    blocks = [e for e in events if isinstance(e, GuardrailTriggered) and e.action == "block"]
    assert len(blocks) == 1, "REJECTED must emit GuardrailTriggered(block)"
    assert "rejected" in blocks[0].reason.lower()

    # Tool still emits ToolCallExecuted (with error result content) per loop's
    # cat9_blocked path; verify the recorded result is NOT the success string.
    executed = [e for e in events if isinstance(e, ToolCallExecuted)]
    assert len(executed) == 1
    assert "tool_executed_ok" not in (executed[0].result_content or "")
    assert "blocked" in (executed[0].result_content or "").lower()


async def test_stage3_escalated_blocks_tool() -> None:
    """ESCALATED (bumped to higher tier reviewer who hasn't decided yet)
    is treated as not-approved → block."""
    chat = _make_chat_with_one_tool_call()
    hitl = FakeHITLManager(decision_type=DecisionType.ESCALATED)
    loop = _build_loop(chat_client=chat, hitl_manager=hitl)

    events = await _collect(loop, user_input="trigger escalation")

    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert received[0].decision == "ESCALATED"

    blocks = [e for e in events if isinstance(e, GuardrailTriggered) and e.action == "block"]
    assert len(blocks) == 1
    assert "escalated" in blocks[0].reason.lower()


async def test_stage3_timeout_blocks_tool() -> None:
    """wait_for_decision raises TimeoutError → treated as REJECTED."""
    chat = _make_chat_with_one_tool_call()
    hitl = FakeHITLManager(decision_type=None, timeout=True)
    loop = _build_loop(chat_client=chat, hitl_manager=hitl, hitl_timeout_s=1)

    events = await _collect(loop, user_input="wait for timeout")

    received = [e for e in events if isinstance(e, ApprovalReceived)]
    assert len(received) == 1
    assert received[0].decision == "REJECTED"

    blocks = [e for e in events if isinstance(e, GuardrailTriggered) and e.action == "block"]
    assert len(blocks) == 1
    assert "timeout" in blocks[0].reason.lower()


async def test_stage3_no_hitl_manager_falls_back_to_soft_block() -> None:
    """53.3 baseline preserved: hitl_manager=None → ESCALATE is soft-block."""
    chat = _make_chat_with_one_tool_call()
    loop = _build_loop(chat_client=chat, hitl_manager=None)

    events = await _collect(loop, user_input="without hitl wiring")

    # No HITL events should appear.
    assert not any(isinstance(e, ApprovalRequested) for e in events)
    assert not any(isinstance(e, ApprovalReceived) for e in events)

    # ESCALATE soft block via existing GuardrailTriggered(action="escalate") path.
    triggered = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert len(triggered) == 1
    assert triggered[0].action == "escalate"


async def test_stage3_request_payload_carries_session_and_trace() -> None:
    """ApprovalRequest must carry session_id and tenant_id for governance UI."""
    chat = _make_chat_with_one_tool_call()
    hitl = FakeHITLManager(decision_type=DecisionType.APPROVED)
    loop = _build_loop(chat_client=chat, hitl_manager=hitl)

    await _collect(loop, user_input="payload test")

    req = hitl.requests[0]
    assert req.tenant_id == _TENANT_ID
    assert isinstance(req.session_id, UUID)
    assert "tool_call_id" in req.context_snapshot
    assert req.context_snapshot["tool_call_id"] == "tc-1"
    assert req.payload["reason"]  # non-empty


async def test_stage3_loop_does_not_terminate_on_block() -> None:
    """Stage 3 block is a per-tool soft block; loop continues to next turn."""
    chat = _make_chat_with_one_tool_call()
    hitl = FakeHITLManager(decision_type=DecisionType.REJECTED)
    loop = _build_loop(chat_client=chat, hitl_manager=hitl)

    events = await _collect(loop, user_input="block but continue")

    # LoopCompleted should be END_TURN (turn 2's natural end), not GUARDRAIL_BLOCKED
    # — because Stage 3 ESCALATE → block is per-tool, not per-loop.
    completed = [e for e in events if isinstance(e, LoopCompleted)]
    assert len(completed) == 1
    assert completed[-1].stop_reason == "end_turn"
