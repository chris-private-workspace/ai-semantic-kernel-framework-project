"""
File: backend/tests/unit/platform_layer/governance/test_harness_policy.py
Purpose: Unit tests for HarnessPolicy + resolver + TTL cache (Sprint 57.106 C3).
Category: Tests / platform_layer / governance
Scope: Phase 57 / Sprint 57.106 (C3)

Created: 2026-06-12
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from platform_layer.governance import harness_policy as hp
from platform_layer.governance.harness_policy import HarnessPolicy

# NOTE: no module-level pytest.mark.asyncio — asyncio mode=AUTO auto-runs the async
# tests, and a module mark would spuriously tag the sync cache/value-object tests.


class _FakeResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


class _FakeSession:
    """Minimal AsyncSession stand-in: counts execute calls, returns a fixed row."""

    def __init__(self, tenant: Any = None, *, raise_exc: bool = False) -> None:
        self._tenant = tenant
        self._raise = raise_exc
        self.execute_calls = 0

    async def execute(self, _stmt: Any) -> _FakeResult:
        self.execute_calls += 1
        if self._raise:
            raise RuntimeError("db flake")
        return _FakeResult(self._tenant)


class _FakeTenant:
    def __init__(self, meta_data: dict[str, Any] | None) -> None:
        self.meta_data = meta_data


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    hp.reset_harness_policy_cache()


# === HarnessPolicy value object ================================================


def test_from_dict_none_is_empty() -> None:
    assert HarnessPolicy.from_dict(None).is_empty()
    assert HarnessPolicy.from_dict({}).is_empty()


def test_from_dict_parses_all_field_types() -> None:
    policy = HarnessPolicy.from_dict(
        {
            "escalate_input_phrases": ["wire transfer", "  "],
            "escalate_tools": ["mock_patrol_check_servers"],
            "verification_mode": " disabled ",
            "verification_judge_template": "safety_review",
            "verification_escalate_on_max": True,
            "risky_action_enabled": False,
            "risky_action_extra_patterns": ["DROP\\s+TABLE"],
        }
    )
    assert policy.escalate_input_phrases == ("wire transfer",)
    assert policy.escalate_tools == ("mock_patrol_check_servers",)
    assert policy.verification_mode == "disabled"
    assert policy.verification_judge_template == "safety_review"
    assert policy.verification_escalate_on_max is True
    assert policy.risky_action_enabled is False
    assert policy.risky_action_extra_patterns == ("DROP\\s+TABLE",)
    assert policy.escalate_output_phrases is None  # not set → default


def test_from_dict_explicit_empty_list_is_off_override() -> None:
    """[] = explicit off-override; distinct from None = not-set (use default)."""
    policy = HarnessPolicy.from_dict({"escalate_tools": []})
    assert policy.escalate_tools == ()
    assert policy.escalate_input_phrases is None
    assert not policy.is_empty()


def test_from_dict_wrong_types_treated_as_not_set() -> None:
    policy = HarnessPolicy.from_dict(
        {
            "escalate_tools": "not-a-list",
            "verification_mode": 42,
            "verification_escalate_on_max": "yes",
            "risky_action_extra_patterns": [1, 2],
        }
    )
    assert policy.is_empty()


def test_to_dict_round_trip_drops_none() -> None:
    policy = HarnessPolicy.from_dict({"escalate_tools": ["a"], "risky_action_enabled": True})
    raw = policy.to_dict()
    assert raw == {"escalate_tools": ["a"], "risky_action_enabled": True}
    assert HarnessPolicy.from_dict(raw) == policy


# === _HarnessPolicyCache TTL (injected clock) ===================================


def test_cache_hit_within_ttl() -> None:
    clock = {"t": 0.0}
    cache = hp._HarnessPolicyCache(ttl_s=60.0, clock=lambda: clock["t"])
    tid = uuid4()
    policy = HarnessPolicy(verification_mode="disabled")
    cache.put(tid, policy)
    clock["t"] = 59.0
    assert cache.get(tid) is policy


def test_cache_miss_after_ttl() -> None:
    clock = {"t": 0.0}
    cache = hp._HarnessPolicyCache(ttl_s=60.0, clock=lambda: clock["t"])
    tid = uuid4()
    cache.put(tid, HarnessPolicy(verification_mode="disabled"))
    clock["t"] = 61.0
    assert cache.get(tid) is None


def test_cache_invalidate_drops_entry() -> None:
    cache = hp._HarnessPolicyCache(ttl_s=60.0, clock=lambda: 0.0)
    tid = uuid4()
    cache.put(tid, HarnessPolicy(verification_mode="disabled"))
    cache.invalidate(tid)
    assert cache.get(tid) is None


# === resolve_tenant_harness_policy ==============================================


async def test_resolve_none_db_returns_empty() -> None:
    policy = await hp.resolve_tenant_harness_policy(None, uuid4())
    assert policy.is_empty()


async def test_resolve_none_tenant_id_returns_empty() -> None:
    policy = await hp.resolve_tenant_harness_policy(_FakeSession(), None)
    assert policy.is_empty()


async def test_resolve_absent_tenant_returns_empty() -> None:
    session = _FakeSession(tenant=None)
    policy = await hp.resolve_tenant_harness_policy(session, uuid4())
    assert policy.is_empty()


async def test_resolve_parses_stored_policy() -> None:
    tenant = _FakeTenant(
        {"harness_policy": {"escalate_tools": ["t1"], "verification_mode": "disabled"}}
    )
    session = _FakeSession(tenant=tenant)
    policy = await hp.resolve_tenant_harness_policy(session, uuid4())
    assert policy.escalate_tools == ("t1",)
    assert policy.verification_mode == "disabled"
    assert policy.escalate_input_phrases is None


async def test_resolve_ignores_non_dict_harness_policy() -> None:
    tenant = _FakeTenant({"harness_policy": "not-a-dict"})
    session = _FakeSession(tenant=tenant)
    policy = await hp.resolve_tenant_harness_policy(session, uuid4())
    assert policy.is_empty()


async def test_resolve_caches_second_call_no_db() -> None:
    tenant = _FakeTenant({"harness_policy": {"escalate_tools": ["t1"]}})
    session = _FakeSession(tenant=tenant)
    tid = uuid4()
    first = await hp.resolve_tenant_harness_policy(session, tid)
    second = await hp.resolve_tenant_harness_policy(session, tid)
    assert first.escalate_tools == ("t1",)
    assert second.escalate_tools == ("t1",)
    assert session.execute_calls == 1  # 2nd call served from cache


async def test_resolve_invalidate_forces_reread() -> None:
    tenant = _FakeTenant({"harness_policy": {"escalate_tools": ["t1"]}})
    session = _FakeSession(tenant=tenant)
    tid = uuid4()
    await hp.resolve_tenant_harness_policy(session, tid)
    hp.invalidate_tenant_harness_policy(tid)
    await hp.resolve_tenant_harness_policy(session, tid)
    assert session.execute_calls == 2  # re-read after invalidate


async def test_resolve_fail_open_on_db_error() -> None:
    session = _FakeSession(raise_exc=True)
    policy = await hp.resolve_tenant_harness_policy(session, uuid4())
    assert policy.is_empty()


# === handoff governance fields (Sprint 57.107 B3) ============================


def test_from_dict_handoff_fields_round_trip() -> None:
    """handoff_enabled + handoff_target_allowlist parse + survive to_dict."""
    policy = hp.HarnessPolicy.from_dict(
        {"handoff_enabled": False, "handoff_target_allowlist": ["planner", "reviewer"]}
    )
    assert policy.handoff_enabled is False
    assert policy.handoff_target_allowlist == ("planner", "reviewer")
    assert policy.to_dict() == {
        "handoff_enabled": False,
        "handoff_target_allowlist": ["planner", "reviewer"],
    }


def test_handoff_fields_tri_state_not_set() -> None:
    """Absent / wrong-typed handoff fields → None (system default: handoff ON)."""
    policy = hp.HarnessPolicy.from_dict({"handoff_enabled": "yes", "handoff_target_allowlist": "x"})
    assert policy.handoff_enabled is None
    assert policy.handoff_target_allowlist is None
    assert policy.is_empty()


def test_subagent_failure_policy_round_trip() -> None:
    """Sprint 57.110 (B4): subagent_failure_policy rides the _STR_FIELDS round-trip."""
    policy = hp.HarnessPolicy.from_dict({"subagent_failure_policy": "fail_fast"})
    assert policy.subagent_failure_policy == "fail_fast"
    assert not policy.is_empty()
    assert policy.to_dict() == {"subagent_failure_policy": "fail_fast"}


def test_subagent_failure_policy_tri_state_not_set() -> None:
    """Absent / wrong-typed → None (the fail_soft system default applies at wiring)."""
    assert hp.HarnessPolicy.from_dict({}).subagent_failure_policy is None
    policy = hp.HarnessPolicy.from_dict({"subagent_failure_policy": 7})
    assert policy.subagent_failure_policy is None
    assert policy.is_empty()
