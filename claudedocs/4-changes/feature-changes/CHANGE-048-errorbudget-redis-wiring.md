# CHANGE-048: B-7 ErrorBudget Redis wiring

**Date**: 2026-06-05
**Sprint**: 57.81
**Scope**: 範疇 8 (Error Handling) wiring — `platform_layer/governance` provider + `api/main.py` startup + chat factory (backend-only)
**Closes**: B-7 (ErrorBudget cross-instance + per-request correctness) / `AD-ErrorBudget-Redis-Wiring`

## Problem
The per-tenant error budget (Cat 8 `TenantErrorBudget`) was backed by a fresh `InMemoryBudgetStore()` constructed **per request** inside `make_chat_error_deps()` (`_category_factories.py`). So the counters reset on every request — the error budget was effectively non-functional even on a single instance — and were never shared across instances. `RedisBudgetStore` had been fully implemented + fakeredis-tested since Sprint 53.2 but was **never wired** (AP-2 side-track code). This became live-relevant after Sprint 57.79/57.80 made the real_llm chat path actually run end-to-end.

## Root Cause
Wiring gap, not missing logic. `make_chat_error_deps()` hardcoded `TenantErrorBudget(InMemoryBudgetStore())`; nothing constructed a shared store. The `TenantErrorBudget` wrapper is stateless (all counter state lives in the `BudgetStore`, keyed `error_budget:{tenant_id}:day|month:...`), so a per-request wrapper over a SHARED store accumulates correctly — the fix is purely to provide that shared store.

## Solution
Backend wiring (Tier 1), mirroring the existing `_wire_rate_limit_counter` / `_wire_pricing_loader` patterns; agent_harness stays DI-pure:
1. NEW `platform_layer/governance/error_budget_provider.py` — process-global `BudgetStore` singleton accessors (`get_` / `maybe_get_` / `set_` / `reset_budget_store`), mirroring `rate_limit_counter.py`. `BudgetStore` typed via TYPE_CHECKING (structural Protocol → no runtime coupling).
2. `agent_harness/error_handling/__init__.py` — export `RedisBudgetStore` (was private) so the public package path is importable; redis import stays TYPE_CHECKING-lazy.
3. `api/main.py` — NEW `_wire_error_budget()` (fail-open): `Redis.from_url(settings.redis_url)` → `set_budget_store(RedisBudgetStore(client))`; called in `_lifespan` after the rate-limit + pricing wiring. Pure Redis — no DB `session_factory` / RLS (budget tenant isolation is already in the key; deliberately NOT copying the rate-limit counter's DB write-through).
4. `api/v1/chat/_category_factories.py` — `TenantErrorBudget(maybe_get_budget_store() or InMemoryBudgetStore())` + deferred-comment updated (AP-2 repaid). Fixes BOTH the per-request reset (shared store) AND cross-instance correctness.

No change to `loop.py` / `budget.py` / `RedisBudgetStore` / schema / frontend.

## Verification
- Unit/integration (`tests/unit/platform_layer/governance/test_error_budget_provider.py`, 7 tests): provider accessors; **accumulation** — two `make_chat_error_deps()` calls (= two requests) over a wired `RedisBudgetStore(FakeRedis())` + a `record()` each → `store.get(_day_key) == 2` (per-request reset fixed; InMemory baseline would not accumulate); `budget._store is store` (binds wired store); InMemory fallback when unwired.
- Startup-log (local backend, no Azure): `api.main: error budget store wired` confirmed alongside the rate-limit + pricing wiring (Risk Class E — wiring fires at startup, no fail-open warning). No real-Azure leg — the budget only increments on tool ERRORS (hard/expensive to provoke on a real happy-path chat); the fakeredis accumulation test is the deterministic proof.
- Gates: `mypy src/` 0 (332) + `pytest` 2137 passed / 4 skipped (+7) + `python scripts/lint/run_all.py` 10/10 (check_cross_category_import + check_llm_sdk_leak green; check_rls_policies unchanged — no schema).

## Impact
Backend-only (Cat 8 wiring). When Redis is available the per-tenant error budget now accumulates across requests + instances; when Redis is down the factory falls back to InMemory (fail-open, never blocks startup). No behaviour change for echo_demo / non-error paths.
