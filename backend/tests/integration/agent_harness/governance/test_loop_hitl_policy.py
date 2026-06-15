"""
File: backend/tests/integration/agent_harness/governance/test_loop_hitl_policy.py
Purpose: Integration tests for the HITL policy read-side load-bearing wiring
    (Sprint 57.122 — AD-HITL-Policy-ReadSide-Potemkin-Phase58). Drives the loop's
    Cat 9 tool gate (_cat9_tool_check) with a configurable guardrail verdict +
    ToolSpec.risk_level + per-tenant HITLPolicy and asserts the escalate-vs-auto-
    approve decision now follows the tenant's risk thresholds — the SAME tool +
    SAME risk routes differently under two tenants' policies (the load-bearing
    proof), and a high-risk UNFLAGGED tool now escalates under a strict policy.
Category: Tests / 範疇 9 (Guardrails / HITL) + 範疇 1 (loop integration)
Scope: Phase 57 / Sprint 57.122

Created: 2026-06-15 (Sprint 57.122 — US-4 integration + multi-tenant)

Modification History (newest-first):
    - 2026-06-15: Initial creation (Sprint 57.122 Day 2)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from adapters._base.chat_client import ChatClient
from agent_harness._contracts import (
    ApprovalRequested,
    LoopEvent,
    ToolCall,
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
from agent_harness.tools import ToolRegistryImpl

pytestmark = pytest.mark.asyncio

_TENANT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_TENANT_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_NOW = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)

# Policy fixtures.
DEFAULT_POLICY = HITLPolicy(tenant_id=_TENANT_A)  # auto=LOW, require=MEDIUM
PERMISSIVE_POLICY = HITLPolicy(  # tenant trusts up to HIGH
    tenant_id=_TENANT_B,
    auto_approve_max_risk=RiskLevel.HIGH,
    require_approval_min_risk=RiskLevel.CRITICAL,
)
STRICT_POLICY = HITLPolicy(  # require approval for everything
    tenant_id=_TENANT_A,
    auto_approve_max_risk=RiskLevel.LOW,
    require_approval_min_risk=RiskLevel.LOW,
)


# === Fakes ================================================================== #


class _Guardrail(Guardrail):
    """Returns a fixed action — PASS (unflagged) or ESCALATE (requires_approval)."""

    guardrail_type = GuardrailType.TOOL

    def __init__(self, action: GuardrailAction) -> None:
        self._action = action

    async def check(
        self, *, content: Any, trace_context: TraceContext | None = None
    ) -> GuardrailResult:
        if self._action == GuardrailAction.ESCALATE:
            return GuardrailResult(
                action=GuardrailAction.ESCALATE, reason="flagged", risk_level="MEDIUM"
            )
        return GuardrailResult(action=GuardrailAction.PASS)


class _PolicyHITL(HITLManager):
    """HITLManager returning a fixed policy; records get_policy + request_approval.

    Blocking mode auto-APPROVES (wait_for_decision) so _cat9_hitl_branch returns
    without a block — the test asserts on whether an ApprovalRequested was emitted.
    """

    def __init__(self, policy: HITLPolicy) -> None:
        self._policy = policy
        self.policy_calls = 0
        self.requests: list[ApprovalRequest] = []

    async def request_approval(
        self, req: ApprovalRequest, *, trace_context: TraceContext | None = None
    ) -> UUID:
        self.requests.append(req)
        return req.request_id

    async def get_pending(
        self, tenant_id: UUID, *, trace_context: TraceContext | None = None
    ) -> list[ApprovalRequest]:
        return list(self.requests)

    async def decide(
        self,
        *,
        request_id: UUID,
        decision: ApprovalDecision,
        trace_context: TraceContext | None = None,
    ) -> None:
        return None

    async def wait_for_decision(
        self,
        request_id: UUID,
        *,
        timeout_s: int,
        trace_context: TraceContext | None = None,
    ) -> ApprovalDecision:
        return ApprovalDecision(
            request_id=request_id,
            decision=DecisionType.APPROVED,
            reviewer="reviewer@test",
            decided_at=_NOW,
            reason="auto",
        )

    async def get_decision(
        self, request_id: UUID, *, trace_context: TraceContext | None = None
    ) -> ApprovalDecision | None:
        return None

    async def get_policy(
        self, tenant_id: UUID, *, trace_context: TraceContext | None = None
    ) -> HITLPolicy:
        self.policy_calls += 1
        return self._policy


def _registry(tool_risk: RiskLevel) -> ToolRegistryImpl:
    registry = ToolRegistryImpl()
    registry.register(
        ToolSpec(
            name="the_tool",
            description="a tool",
            input_schema={"type": "object", "properties": {}},
            risk_level=tool_risk,
        )
    )
    return registry


def _build(
    *, action: GuardrailAction, tool_risk: RiskLevel, hitl: _PolicyHITL, tenant_id: UUID
) -> AgentLoopImpl:
    engine = GuardrailEngine()
    engine.register(_Guardrail(action), priority=10)
    return AgentLoopImpl(
        chat_client=MagicMock(spec=ChatClient),  # never called by _cat9_tool_check
        output_parser=OutputParserImpl(),
        tool_executor=MagicMock(),
        tool_registry=_registry(tool_risk),
        guardrail_engine=engine,
        tenant_id=tenant_id,
        hitl_manager=hitl,
    )


async def _gate(loop: AgentLoopImpl, *, tenant_id: UUID) -> list[LoopEvent]:
    """Drive _cat9_tool_check for one tool call; collect the yielded events."""
    session_id = uuid4()
    ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    tc = ToolCall(id="tc-1", name="the_tool", arguments={})
    return [
        ev
        async for ev in loop._cat9_tool_check(
            tc=tc, ctx=ctx, turn_count=0, session_id=session_id, messages=[]
        )
    ]


def _escalated(events: list[LoopEvent]) -> bool:
    return any(isinstance(e, ApprovalRequested) for e in events)


# === Tests ================================================================== #


@pytest.mark.parametrize(
    "action,tool_risk,policy,tenant,expect_escalate",
    [
        # Flagged tool (ESCALATE), LOW spec → floored to MEDIUM:
        #   DEFAULT (require=MEDIUM) → escalate (backward-compatible)
        (GuardrailAction.ESCALATE, RiskLevel.LOW, DEFAULT_POLICY, _TENANT_A, True),
        #   PERMISSIVE (auto=HIGH) → auto-approve (THE load-bearing delta)
        (GuardrailAction.ESCALATE, RiskLevel.LOW, PERMISSIVE_POLICY, _TENANT_B, False),
        # Unflagged tool (PASS), HIGH spec:
        #   DEFAULT (require=MEDIUM) → NEW escalation trigger (high-risk unflagged)
        (GuardrailAction.PASS, RiskLevel.HIGH, DEFAULT_POLICY, _TENANT_A, True),
        #   PERMISSIVE (auto=HIGH) → auto-approve (HIGH <= auto)
        (GuardrailAction.PASS, RiskLevel.HIGH, PERMISSIVE_POLICY, _TENANT_B, False),
        # Unflagged LOW tool → never escalates under DEFAULT (benign baseline)
        (GuardrailAction.PASS, RiskLevel.LOW, DEFAULT_POLICY, _TENANT_A, False),
        # STRICT (require=LOW) → escalate even an unflagged LOW tool
        (GuardrailAction.PASS, RiskLevel.LOW, STRICT_POLICY, _TENANT_A, True),
    ],
)
async def test_tool_gate_follows_tenant_policy(
    action: GuardrailAction,
    tool_risk: RiskLevel,
    policy: HITLPolicy,
    tenant: UUID,
    expect_escalate: bool,
) -> None:
    hitl = _PolicyHITL(policy)
    loop = _build(action=action, tool_risk=tool_risk, hitl=hitl, tenant_id=tenant)
    events = await _gate(loop, tenant_id=tenant)

    assert _escalated(events) is expect_escalate
    # The policy was consulted at runtime (load-bearing read-side wiring).
    assert hitl.policy_calls >= 1
    if expect_escalate:
        assert hitl.requests, "an ApprovalRequest should have been submitted"
        # The ApprovalRequest carries the resolved risk (not the hardcoded HIGH).
        assert hitl.requests[-1].risk_level != RiskLevel.HIGH or tool_risk in (
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        )
    else:
        assert not hitl.requests, "no approval should be requested on auto-approve"


async def test_same_flagged_tool_routes_differently_per_tenant() -> None:
    """The load-bearing proof: the SAME flagged tool (same resolved MEDIUM risk)
    escalates for a default-policy tenant but auto-approves for a permissive one —
    the runtime now reads each tenant's HITLPolicy."""
    # Tenant A — default policy → escalate.
    hitl_a = _PolicyHITL(DEFAULT_POLICY)
    loop_a = _build(
        action=GuardrailAction.ESCALATE,
        tool_risk=RiskLevel.LOW,
        hitl=hitl_a,
        tenant_id=_TENANT_A,
    )
    events_a = await _gate(loop_a, tenant_id=_TENANT_A)

    # Tenant B — permissive policy (auto_approve_max_risk=HIGH) → auto-approve.
    hitl_b = _PolicyHITL(PERMISSIVE_POLICY)
    loop_b = _build(
        action=GuardrailAction.ESCALATE,
        tool_risk=RiskLevel.LOW,
        hitl=hitl_b,
        tenant_id=_TENANT_B,
    )
    events_b = await _gate(loop_b, tenant_id=_TENANT_B)

    assert _escalated(events_a) is True
    assert _escalated(events_b) is False
    assert hitl_a.requests and not hitl_b.requests


async def test_escalation_carries_resolved_risk_not_hardcoded_high() -> None:
    """A flagged MEDIUM-risk tool under a default policy escalates with the
    resolved MEDIUM risk on the ApprovalRequest — proving the hardcoded
    RiskLevel.HIGH was dropped (reviewer routing + SLA now use the real risk)."""
    hitl = _PolicyHITL(DEFAULT_POLICY)
    loop = _build(
        action=GuardrailAction.ESCALATE,
        tool_risk=RiskLevel.MEDIUM,
        hitl=hitl,
        tenant_id=_TENANT_A,
    )
    await _gate(loop, tenant_id=_TENANT_A)
    assert hitl.requests
    assert hitl.requests[-1].risk_level == RiskLevel.MEDIUM


async def test_policy_resolved_once_and_cached_across_tool_calls() -> None:
    """The per-tenant policy is resolved once per run + cached (no DB round-trip
    per tool call)."""
    hitl = _PolicyHITL(DEFAULT_POLICY)
    loop = _build(
        action=GuardrailAction.PASS,
        tool_risk=RiskLevel.LOW,
        hitl=hitl,
        tenant_id=_TENANT_A,
    )
    await _gate(loop, tenant_id=_TENANT_A)
    await _gate(loop, tenant_id=_TENANT_A)
    assert hitl.policy_calls == 1, "policy should be resolved once and cached"
