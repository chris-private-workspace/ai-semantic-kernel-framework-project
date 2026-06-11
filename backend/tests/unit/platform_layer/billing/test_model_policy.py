"""
File: backend/tests/unit/platform_layer/billing/test_model_policy.py
Purpose: Unit tests for resolve_tenant_model_policy + the TTL cache (Sprint 57.104 C1).
Category: Tests / platform_layer / billing
Scope: Phase 57 / Sprint 57.104 (C1)

Created: 2026-06-11
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from adapters._base.model_policy import ModelPolicy
from platform_layer.billing import model_policy as mp

# NOTE: no module-level pytest.mark.asyncio — asyncio mode=AUTO auto-runs the async
# tests, and a module mark would spuriously tag the sync _ModelPolicyCache tests.


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
    mp.reset_model_policy_cache()


# === _ModelPolicyCache TTL (injected clock) ====================================


def test_cache_hit_within_ttl() -> None:
    clock = {"t": 0.0}
    cache = mp._ModelPolicyCache(ttl_s=60.0, clock=lambda: clock["t"])
    tid = uuid4()
    policy = ModelPolicy(action_deployment="d")
    cache.put(tid, policy)
    clock["t"] = 59.0
    assert cache.get(tid) is policy


def test_cache_miss_after_ttl() -> None:
    clock = {"t": 0.0}
    cache = mp._ModelPolicyCache(ttl_s=60.0, clock=lambda: clock["t"])
    tid = uuid4()
    cache.put(tid, ModelPolicy(action_deployment="d"))
    clock["t"] = 61.0
    assert cache.get(tid) is None


def test_cache_invalidate_drops_entry() -> None:
    cache = mp._ModelPolicyCache(ttl_s=60.0, clock=lambda: 0.0)
    tid = uuid4()
    cache.put(tid, ModelPolicy(action_deployment="d"))
    cache.invalidate(tid)
    assert cache.get(tid) is None


# === resolve_tenant_model_policy ===============================================


async def test_resolve_none_db_returns_empty() -> None:
    policy = await mp.resolve_tenant_model_policy(None, uuid4())
    assert policy.is_empty()


async def test_resolve_none_tenant_id_returns_empty() -> None:
    policy = await mp.resolve_tenant_model_policy(_FakeSession(), None)
    assert policy.is_empty()


async def test_resolve_absent_tenant_returns_empty() -> None:
    session = _FakeSession(tenant=None)
    policy = await mp.resolve_tenant_model_policy(session, uuid4())
    assert policy.is_empty()


async def test_resolve_parses_stored_policy() -> None:
    tenant = _FakeTenant({"model_policy": {"action_deployment": "act", "cheap_model": "chp"}})
    session = _FakeSession(tenant=tenant)
    policy = await mp.resolve_tenant_model_policy(session, uuid4())
    assert policy.action_deployment == "act"
    assert policy.cheap_model == "chp"
    assert policy.action_model is None


async def test_resolve_ignores_non_dict_model_policy() -> None:
    tenant = _FakeTenant({"model_policy": "not-a-dict"})
    session = _FakeSession(tenant=tenant)
    policy = await mp.resolve_tenant_model_policy(session, uuid4())
    assert policy.is_empty()


async def test_resolve_caches_second_call_no_db() -> None:
    tenant = _FakeTenant({"model_policy": {"action_deployment": "act"}})
    session = _FakeSession(tenant=tenant)
    tid = uuid4()
    first = await mp.resolve_tenant_model_policy(session, tid)
    second = await mp.resolve_tenant_model_policy(session, tid)
    assert first.action_deployment == "act"
    assert second.action_deployment == "act"
    assert session.execute_calls == 1  # 2nd call served from cache


async def test_resolve_invalidate_forces_reread() -> None:
    tenant = _FakeTenant({"model_policy": {"action_deployment": "act"}})
    session = _FakeSession(tenant=tenant)
    tid = uuid4()
    await mp.resolve_tenant_model_policy(session, tid)
    mp.invalidate_tenant_model_policy(tid)
    await mp.resolve_tenant_model_policy(session, tid)
    assert session.execute_calls == 2  # re-read after invalidate


async def test_resolve_fail_open_on_db_error() -> None:
    session = _FakeSession(raise_exc=True)
    policy = await mp.resolve_tenant_model_policy(session, uuid4())
    assert policy.is_empty()
