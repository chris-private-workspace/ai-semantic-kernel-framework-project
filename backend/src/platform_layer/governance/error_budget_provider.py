"""
File: backend/src/platform_layer/governance/error_budget_provider.py
Purpose: Process-wide BudgetStore singleton accessors for the Cat 8 error budget.
Category: platform_layer / governance (wiring for 範疇 8 Error Handling)
Scope: Sprint 57.81 (B-7)

Description:
    Holds the process-global BudgetStore that backs the per-tenant error budget
    (Cat 8 TenantErrorBudget). api/main.py wires a Redis-backed store here at
    startup (fail-open); the chat factory (make_chat_error_deps) looks it up via
    maybe_get_budget_store() and falls back to an InMemoryBudgetStore when unset.

    Why here (platform_layer/governance), not agent_harness?
      - agent_harness stays DI-pure (no process-global mutable state). The Cat 8
        BudgetStore Protocol + both impls (InMemory / Redis) live in
        agent_harness.error_handling; this module only owns the wiring singleton,
        mirroring the 3 existing wiring singletons (rate_limit_counter / pricing /
        quota — all in platform_layer). Error budget is a platform-protection
        policy ("protect platform during incident" — budget.py docstring) → governance.

    Accessors mirror platform_layer/tenant/rate_limit_counter.py (get / maybe_get /
    set / reset). The BudgetStore type is imported under TYPE_CHECKING only — the
    Protocol is structural, so the holder needs no runtime agent_harness import.

Key Components:
    - get_budget_store(): strict accessor (raises if unset)
    - maybe_get_budget_store(): lenient accessor (None if unset — fail-open callers)
    - set_budget_store(): install at startup / test fixture
    - reset_budget_store(): test isolation hook

Owner: 01-eleven-categories-spec.md §Cat 8 + .claude/rules/multi-tenant-data.md
Created: 2026-06-05 (Sprint 57.81)
Last Modified: 2026-06-05

Modification History (newest-first):
    - 2026-06-05: Initial creation (Sprint 57.81) — B-7 wire RedisBudgetStore

Related:
    - agent_harness/error_handling/budget.py (BudgetStore Protocol + TenantErrorBudget)
    - agent_harness/error_handling/_redis_store.py (RedisBudgetStore)
    - api/main.py (_wire_error_budget) / api/v1/chat/_category_factories.py (consumer)
    - platform_layer/tenant/rate_limit_counter.py (singleton accessor pattern mirrored)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_harness.error_handling import BudgetStore


# === Singleton accessors (mirror rate_limit_counter.py get/set/reset/maybe_get) ===
_budget_store: BudgetStore | None = None


def get_budget_store() -> BudgetStore:
    """Strict accessor — raises if uninitialised."""
    if _budget_store is None:
        raise RuntimeError(
            "BudgetStore not initialised; call set_budget_store() at app startup "
            "or in a test fixture"
        )
    return _budget_store


def maybe_get_budget_store() -> BudgetStore | None:
    """Lenient accessor — returns None if uninitialised (fail-open callers).

    make_chat_error_deps uses this so dev / test runs without Redis (or before
    startup wiring) fall back to an InMemoryBudgetStore instead of failing.
    """
    return _budget_store


def set_budget_store(store: BudgetStore | None) -> None:
    """Install the singleton (app startup or test fixture)."""
    global _budget_store
    _budget_store = store


def reset_budget_store() -> None:
    """Test isolation hook (per testing.md section Module-level Singleton Reset Pattern)."""
    global _budget_store
    _budget_store = None
