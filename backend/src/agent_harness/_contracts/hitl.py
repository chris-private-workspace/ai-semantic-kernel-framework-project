"""
File: backend/src/agent_harness/_contracts/hitl.py
Purpose: Single-source HITL types (ApprovalRequest / ApprovalDecision / HITLPolicy).
Category: cross-category single-source contracts (per 17.md §1)
Scope: Phase 49 / Sprint 49.1

Description:
    HITL (Human-in-the-Loop) was previously scattered across categories
    2 / 7 / 8 / 9 in V1. V2 centralizes via §HITL Centralization (per
    17.md §5). All categories use these contract types; only HITLManager
    (in agent_harness/hitl/) implements behavior.

Owner: 01-eleven-categories-spec.md §HITL 中央化
Single-source: 17.md §1.1, §5

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-06-15

Modification History:
    - 2026-06-15: Sprint 57.122 — add RISK_ORDER + decide_tool_hitl + resolve_tool_risk
    - 2026-04-29: Initial creation (Sprint 49.1)

Related:
    - 01-eleven-categories-spec.md §HITL 中央化
    - 17-cross-category-interfaces.md §5 (HITL centralization)
    - 14-security-deep-dive.md (compliance requirements)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class RiskLevel(Enum):
    """Risk levels driving HITL routing thresholds."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionType(Enum):
    """Reviewer decisions."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"  # bumped to higher reviewer tier


@dataclass(frozen=True)
class ApprovalRequest:
    """Submitted by category 2 (tools) or category 9 (guardrails)."""

    request_id: UUID
    tenant_id: UUID
    session_id: UUID
    requester: str  # e.g. "tools" / "guardrails"
    risk_level: RiskLevel
    payload: dict[str, Any]
    sla_deadline: datetime
    context_snapshot: dict[str, Any]  # for human reviewer's UI


@dataclass(frozen=True)
class ApprovalDecision:
    """Reviewer's decision; merged back into LoopState by Reducer."""

    request_id: UUID
    decision: DecisionType
    reviewer: str
    decided_at: datetime
    reason: str | None = None


@dataclass(frozen=True)
class HITLPolicy:
    """Per-tenant policy: which risk levels require approval, who reviews."""

    tenant_id: UUID
    auto_approve_max_risk: RiskLevel = RiskLevel.LOW
    require_approval_min_risk: RiskLevel = RiskLevel.MEDIUM
    reviewer_groups_by_risk: dict[RiskLevel, list[str]] = field(default_factory=dict)
    sla_seconds_by_risk: dict[RiskLevel, int] = field(default_factory=dict)


# === Sprint 57.122: HITL risk-threshold decision (load-bearing read-side) ===
# Why: the per-tenant HITLPolicy thresholds (auto_approve_max_risk /
# require_approval_min_risk) shipped write-side (DB store + admin GET/PUT) but were
# never consumed at tool execution — the loop hardcoded `if requires_approval:
# ESCALATE` + a flat RiskLevel.HIGH (AD-HITL-Policy-ReadSide-Potemkin-Phase58).
# These PURE, DB-free functions make the thresholds load-bearing: the loop resolves
# a tool call's risk (from ToolSpec.risk_level) + the tenant policy, then decides
# escalate vs auto-approve. Kept in the contract layer so they are testable +
# provider-neutral + importable by both the loop and tests.
# Semantics (design note 35; user decision 2026-06-15 — "both thresholds
# load-bearing" + "risk from ToolSpec.risk_level"): escalate-first ordering so a
# misconfigured overlapping policy errs to ESCALATE (the safe side).
# Related: 35-hitl-risk-threshold-semantics.md / orchestrator_loop/loop.py _cat9_tool_check

RISK_ORDER: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def risk_ge(a: RiskLevel, b: RiskLevel) -> bool:
    """True if risk ``a`` is at least as severe as ``b``.

    ``RiskLevel`` is a plain ``str`` Enum (not orderable) — always compare via
    ``RISK_ORDER``, never the members directly.
    """
    return RISK_ORDER[a] >= RISK_ORDER[b]


def risk_le(a: RiskLevel, b: RiskLevel) -> bool:
    """True if risk ``a`` is no more severe than ``b`` (see ``risk_ge``)."""
    return RISK_ORDER[a] <= RISK_ORDER[b]


def resolve_tool_risk(
    spec_risk: RiskLevel | None,
    *,
    rule_requires_approval: bool,
) -> RiskLevel:
    """Resolve the effective risk level of a tool call (Sprint 57.122).

    The tool's intrinsic ``ToolSpec.risk_level`` is the base (LOW when the spec is
    missing — tool not in the registry).

    The per-rule capability-matrix ``requires_approval=True`` flag is treated as a
    risk **floor of MEDIUM**: a flagged tool's effective risk is ``max(base,
    MEDIUM)``. This preserves backward compatibility — under the DEFAULT policy
    (``require_approval_min_risk=MEDIUM``) a flagged tool still escalates, so wiring
    the policy in never SILENTLY relaxes an approval the admin already required
    (most ``ToolSpec.risk_level`` default to LOW). A permissive tenant
    (``auto_approve_max_risk >= MEDIUM``) can still auto-approve it — that's the
    load-bearing part. (design note 35; user motivation 2026-06-15 = 企業安全剛需,
    i.e. tighter enforcement, not a relaxation.)
    """
    base = spec_risk if spec_risk is not None else RiskLevel.LOW
    if rule_requires_approval and RISK_ORDER[base] < RISK_ORDER[RiskLevel.MEDIUM]:
        return RiskLevel.MEDIUM
    return base


def decide_tool_hitl(
    risk: RiskLevel,
    policy: HITLPolicy,
    *,
    rule_requires_approval: bool,
) -> bool:
    """Decide whether a tool call needs human approval (HITL ESCALATE).

    Returns ``True`` → ESCALATE (require approval); ``False`` → auto-approve (run
    the tool).

    Two-threshold semantics (design note 35; both thresholds load-bearing — user
    decision 2026-06-15). Precedence is escalate-first so a misconfigured
    overlapping policy (``auto_approve_max_risk >= require_approval_min_risk``)
    errs to ESCALATE (the safe side):

        1. risk >= require_approval_min_risk          → ESCALATE
        2. risk <= auto_approve_max_risk              → auto-approve
           (the tenant trusts this risk band — even a per-rule-flagged tool)
        3. gray band (auto_max < risk < require_min)  → the per-rule
           ``rule_requires_approval`` bool decides (the platform baseline tiebreaker)
    """
    if risk_ge(risk, policy.require_approval_min_risk):
        return True
    if risk_le(risk, policy.auto_approve_max_risk):
        return False
    return rule_requires_approval
