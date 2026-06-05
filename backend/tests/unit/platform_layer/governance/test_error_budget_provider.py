"""
File: tests/unit/platform_layer/governance/test_error_budget_provider.py
Purpose: Cover the BudgetStore singleton provider + the chat factory wiring (B-7).
Category: Tests / platform_layer governance + Cat 8 wiring
Scope: Sprint 57.81

Description:
    B-7 wires the already-built RedisBudgetStore so the per-tenant error budget
    accumulates across requests (and instances) instead of resetting per request.
    These tests cover the singleton accessors + the key correctness claim: two
    successive make_chat_error_deps() calls (= two requests) over a wired shared
    store accumulate, whereas the unwired path falls back to InMemoryBudgetStore.

Created: 2026-06-05 (Sprint 57.81)
Modified: 2026-06-05
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fakeredis.aioredis import FakeRedis

from agent_harness.error_handling import (
    ErrorClass,
    InMemoryBudgetStore,
    RedisBudgetStore,
    TenantErrorBudget,
)
from api.v1.chat._category_factories import make_chat_error_deps
from platform_layer.governance.error_budget_provider import (
    get_budget_store,
    maybe_get_budget_store,
    reset_budget_store,
    set_budget_store,
)


@pytest.fixture(autouse=True)
def _reset_singleton() -> object:
    """Module-level singleton isolation (testing.md §Module-level Singleton Reset)."""
    reset_budget_store()
    yield
    reset_budget_store()


# ---------------------------------------------------------------------------
# Singleton accessors
# ---------------------------------------------------------------------------


def test_maybe_get_returns_none_when_unset() -> None:
    assert maybe_get_budget_store() is None


def test_set_then_maybe_get_returns_it() -> None:
    store = InMemoryBudgetStore()
    set_budget_store(store)
    assert maybe_get_budget_store() is store


def test_get_strict_raises_when_unset() -> None:
    with pytest.raises(RuntimeError):
        get_budget_store()


def test_reset_clears() -> None:
    set_budget_store(InMemoryBudgetStore())
    reset_budget_store()
    assert maybe_get_budget_store() is None


# ---------------------------------------------------------------------------
# Chat factory wiring — the B-7 correctness claim
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wired_store_accumulates_across_factory_calls() -> None:
    """Two make_chat_error_deps() calls (= two requests) over ONE wired shared
    store accumulate the per-tenant counter — the per-request reset is fixed."""
    store = RedisBudgetStore(FakeRedis(decode_responses=False))
    set_budget_store(store)
    tid = uuid4()

    # Request 1: fresh TenantErrorBudget wrapper over the shared store.
    _, _, _, budget1, _ = make_chat_error_deps()
    await budget1.record(tid, ErrorClass.TRANSIENT)

    # Request 2: a DIFFERENT wrapper (per-request rebuild) over the SAME store.
    _, _, _, budget2, _ = make_chat_error_deps()
    await budget2.record(tid, ErrorClass.TRANSIENT)

    day_count = await store.get(TenantErrorBudget._day_key(tid))
    assert day_count == 2, "per-request wrappers must share the wired store and accumulate"


@pytest.mark.asyncio
async def test_factory_uses_wired_store_instance() -> None:
    """make_chat_error_deps binds the wired store (not a fresh InMemory)."""
    store = RedisBudgetStore(FakeRedis(decode_responses=False))
    set_budget_store(store)

    _, _, _, budget, _ = make_chat_error_deps()
    assert budget._store is store


def test_factory_falls_back_to_inmemory_when_unwired() -> None:
    """No wired store → TenantErrorBudget backed by InMemoryBudgetStore (no crash)."""
    _, _, _, budget, _ = make_chat_error_deps()
    assert isinstance(budget._store, InMemoryBudgetStore)
