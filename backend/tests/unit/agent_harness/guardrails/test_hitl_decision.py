"""
File: backend/tests/unit/agent_harness/guardrails/test_hitl_decision.py
Purpose: Unit tests for the HITL risk-threshold decision (Sprint 57.122 — the
    load-bearing read-side: RISK_ORDER / risk_ge / risk_le / resolve_tool_risk /
    decide_tool_hitl). Pure functions; table-driven across risk x policy x flag.
Category: Tests / 範疇 9 (HITL centralization)
Scope: Phase 57 / Sprint 57.122

Created: 2026-06-15 (Sprint 57.122 — AD-HITL-Policy-ReadSide-Potemkin-Phase58)

Modification History (newest-first):
    - 2026-06-15: Initial creation (Sprint 57.122 Day 1 — US-1/US-4)
"""

from __future__ import annotations

from uuid import UUID

import pytest

from agent_harness._contracts.hitl import (
    RISK_ORDER,
    HITLPolicy,
    RiskLevel,
    decide_tool_hitl,
    resolve_tool_risk,
    risk_ge,
    risk_le,
)

TENANT = UUID("11111111-1111-1111-1111-111111111111")

# Policy fixtures spanning the decision space.
DEFAULT = HITLPolicy(tenant_id=TENANT)  # auto=LOW, require=MEDIUM
PERMISSIVE = HITLPolicy(
    tenant_id=TENANT,
    auto_approve_max_risk=RiskLevel.HIGH,
    require_approval_min_risk=RiskLevel.CRITICAL,
)
STRICT = HITLPolicy(  # approve everything (require_min=LOW)
    tenant_id=TENANT,
    auto_approve_max_risk=RiskLevel.LOW,
    require_approval_min_risk=RiskLevel.LOW,
)
WIDE = HITLPolicy(  # big gray band MEDIUM/HIGH → per-rule bool decides
    tenant_id=TENANT,
    auto_approve_max_risk=RiskLevel.LOW,
    require_approval_min_risk=RiskLevel.CRITICAL,
)
OVERLAP = HITLPolicy(  # misconfigured: auto >= require → escalate-first must win
    tenant_id=TENANT,
    auto_approve_max_risk=RiskLevel.HIGH,
    require_approval_min_risk=RiskLevel.MEDIUM,
)


# --------------------------------------------------------------------------- #
# RISK_ORDER + comparison helpers                                             #
# --------------------------------------------------------------------------- #


def test_risk_order_is_total_and_strictly_increasing() -> None:
    assert RISK_ORDER == {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    # every level has a distinct rank
    assert len(set(RISK_ORDER.values())) == 4


@pytest.mark.parametrize(
    "a,b,ge,le",
    [
        (RiskLevel.LOW, RiskLevel.LOW, True, True),
        (RiskLevel.MEDIUM, RiskLevel.LOW, True, False),
        (RiskLevel.LOW, RiskLevel.MEDIUM, False, True),
        (RiskLevel.CRITICAL, RiskLevel.LOW, True, False),
        (RiskLevel.HIGH, RiskLevel.HIGH, True, True),
    ],
)
def test_risk_comparison_helpers(a: RiskLevel, b: RiskLevel, ge: bool, le: bool) -> None:
    assert risk_ge(a, b) is ge
    assert risk_le(a, b) is le


# --------------------------------------------------------------------------- #
# resolve_tool_risk                                                           #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "spec_risk,flagged,expected",
    [
        (RiskLevel.HIGH, False, RiskLevel.HIGH),  # spec authoritative, unflagged
        (RiskLevel.LOW, False, RiskLevel.LOW),  # unflagged benign
        (RiskLevel.LOW, True, RiskLevel.MEDIUM),  # flagged floor: LOW → MEDIUM
        (RiskLevel.MEDIUM, True, RiskLevel.MEDIUM),  # flagged, already at floor
        (RiskLevel.HIGH, True, RiskLevel.HIGH),  # flagged, spec above floor wins
        (None, True, RiskLevel.MEDIUM),  # flagged + unknown → MEDIUM
        (None, False, RiskLevel.LOW),  # unflagged + unknown → LOW
    ],
)
def test_resolve_tool_risk(spec_risk: RiskLevel | None, flagged: bool, expected: RiskLevel) -> None:
    assert resolve_tool_risk(spec_risk, rule_requires_approval=flagged) is expected


# --------------------------------------------------------------------------- #
# decide_tool_hitl — the two-threshold semantics                              #
# --------------------------------------------------------------------------- #

# (policy, risk, flagged, expected_escalate)
_DECIDE_CASES = [
    # DEFAULT (auto=LOW, require=MEDIUM)
    (DEFAULT, RiskLevel.LOW, False, False),
    (DEFAULT, RiskLevel.LOW, True, False),  # auto-approve overrides the flag (load-bearing)
    (DEFAULT, RiskLevel.MEDIUM, False, True),
    (DEFAULT, RiskLevel.MEDIUM, True, True),
    (DEFAULT, RiskLevel.HIGH, False, True),
    (DEFAULT, RiskLevel.CRITICAL, False, True),
    # PERMISSIVE (auto=HIGH, require=CRITICAL) — tenant trusts up to HIGH
    (PERMISSIVE, RiskLevel.LOW, False, False),
    (PERMISSIVE, RiskLevel.MEDIUM, True, False),  # flagged MEDIUM auto-approved
    (PERMISSIVE, RiskLevel.HIGH, True, False),  # flagged HIGH auto-approved
    (PERMISSIVE, RiskLevel.CRITICAL, False, True),
    # STRICT (require=LOW) — escalate everything
    (STRICT, RiskLevel.LOW, False, True),
    (STRICT, RiskLevel.MEDIUM, False, True),
    (STRICT, RiskLevel.CRITICAL, False, True),
    # WIDE (auto=LOW, require=CRITICAL) — gray band MEDIUM/HIGH → per-rule bool
    (WIDE, RiskLevel.LOW, False, False),
    (WIDE, RiskLevel.MEDIUM, False, False),  # gray + unflagged → pass
    (WIDE, RiskLevel.MEDIUM, True, True),  # gray + flagged → escalate
    (WIDE, RiskLevel.HIGH, False, False),
    (WIDE, RiskLevel.HIGH, True, True),
    (WIDE, RiskLevel.CRITICAL, False, True),
    # OVERLAP (auto=HIGH, require=MEDIUM, misconfigured) — escalate-first wins (safe)
    (OVERLAP, RiskLevel.LOW, False, False),
    (OVERLAP, RiskLevel.MEDIUM, False, True),  # escalate despite auto=HIGH
    (OVERLAP, RiskLevel.HIGH, False, True),
]


@pytest.mark.parametrize("policy,risk,flagged,expected", _DECIDE_CASES)
def test_decide_tool_hitl(
    policy: HITLPolicy, risk: RiskLevel, flagged: bool, expected: bool
) -> None:
    assert decide_tool_hitl(risk, policy, rule_requires_approval=flagged) is expected


@pytest.mark.parametrize("spec_risk", [None, RiskLevel.LOW])
def test_flagged_tool_still_escalates_under_default_policy(
    spec_risk: RiskLevel | None,
) -> None:
    """Backward-compat guard (no silent relaxation): a capability-matrix-flagged
    tool whose ToolSpec.risk_level is the LOW default (or unknown) — the only
    pre-57.122 escalation trigger — STILL escalates under the DEFAULT policy,
    because the flag floors the effective risk to MEDIUM and DEFAULT
    require_approval_min_risk=MEDIUM. Wiring the policy in only ADDS the per-tenant
    threshold behavior; it never relaxes existing approvals for default-policy
    tenants."""
    risk = resolve_tool_risk(spec_risk, rule_requires_approval=True)
    assert risk is RiskLevel.MEDIUM
    assert decide_tool_hitl(risk, DEFAULT, rule_requires_approval=True) is True


def test_permissive_tenant_can_auto_approve_a_flagged_tool() -> None:
    """Load-bearing proof: a permissive tenant (auto_approve_max_risk=HIGH) DOES
    auto-approve the same flagged LOW-spec tool that escalates by default — the
    threshold is now consulted at runtime."""
    risk = resolve_tool_risk(RiskLevel.LOW, rule_requires_approval=True)  # MEDIUM floor
    assert decide_tool_hitl(risk, PERMISSIVE, rule_requires_approval=True) is False
