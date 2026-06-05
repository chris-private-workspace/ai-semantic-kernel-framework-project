# Sprint 57.81 Plan — B-7 ErrorBudget Redis wiring (wire the already-built RedisBudgetStore) (closes AD-ErrorBudget-Redis-Wiring / B-7)

**Branch**: `feature/sprint-57-81-errorbudget-redis` (from `main` `18b6dd16`)
**Closes**: B-7 (ErrorBudget cross-instance + per-request correctness) — the billing/resilience bundle's budget half.
**Scope**: Backend wiring only (Cat 8 ErrorBudget store provider singleton + startup wire + chat factory swap). NOT a new store (RedisBudgetStore already built + tested, Sprint 53.2); NOT loop.py / budget.py logic; NOT error_budgets.yaml per-tenant overrides.

---

## 0. Background

B-7 is a wiring gap, not a missing feature: `RedisBudgetStore` was fully implemented + fakeredis-tested in Sprint 53.2 but never wired — the chat factory hardcodes `InMemoryBudgetStore()`. Two correctness problems result once real_llm runs (now LIVE after Sprint 57.79/57.80 real-Azure verification):
1. **Per-request reset** — `make_chat_error_deps()` runs inside `build_real_llm_handler` **per request**, so every request constructs a fresh `InMemoryBudgetStore()` → the counter never accumulates even on a single instance → the error budget is effectively non-functional.
2. **Cross-instance** — even with a persistent in-process store, horizontal scaling would split counts across instances.

Both are fixed by wiring the shared `RedisBudgetStore` once at startup (the `TenantErrorBudget` wrapper is stateless; all counter state lives in the store, keyed `error_budget:{tenant_id}:day|month:...`). This is AP-2 (Side-Track Code) debt repayment, mirroring the existing `_wire_rate_limit_counter` / `_wire_pricing_loader` startup wiring + their `set_/maybe_get_` singleton accessors.

### Day-0 ground-truth (parent grep + code read, main `18b6dd16`; the source analysis `cat8-errorbudget-redis-wiring-analysis-20260531.md` is 18 sprints old — all line numbers re-verified)
- **D-DAY0-1 (RedisBudgetStore exists, fully impl)**: `agent_harness/error_handling/_redis_store.py:35-61` — `RedisBudgetStore(client: Redis[bytes])` with MULTI/EXEC `increment` + `get`. **NOT exported** from `error_handling/__init__.py` (only `BudgetStore` / `InMemoryBudgetStore` / `TenantErrorBudget` are) → wiring must add the export.
- **D-DAY0-2 (state lives in the store)**: `budget.py:52-66` `BudgetStore` Protocol (async `increment(key, ttl)→int` + `get(key)→int`); `TenantErrorBudget` (`:108-165`) delegates all counting to the store (keys `error_budget:{tenant_id}:day:{date}` / `:month:{ym}`). ⇒ a per-request `TenantErrorBudget(shared_redis_store)` accumulates correctly — Tier 1 wiring fixes BOTH the per-request reset AND cross-instance.
- **D-DAY0-3 (wiring gap site)**: `api/v1/chat/_category_factories.py:236 make_chat_error_deps`; deferred comment `:248-252`; `error_budget = TenantErrorBudget(InMemoryBudgetStore())` `:257`; imports `InMemoryBudgetStore` / `TenantErrorBudget` `:60` / `:62`.
- **D-DAY0-4 (wiring templates)**: `api/main.py:86 _wire_rate_limit_counter` (fail-open) + `:122 _wire_pricing_loader` (fail-soft); both called in `_lifespan` (`:166` / `:167`). Singleton accessor pattern: `platform_layer/tenant/rate_limit_counter.py:526-558` (`get_` strict / `maybe_get_` lenient / `set_` install / `reset_` test-hook; "mirror quota.py").
- **D-DAY0-5 (live consumer — NOT Potemkin)**: `loop.py:218` ctor `error_budget: TenantErrorBudget | None`; `:269` stored; `:320-322` `_handle_tool_error` calls `await self._error_budget.record(self._tenant_id, cls)` on a (non-FATAL) tool error; `is_exceeded` is consumed by `DefaultErrorTerminator`. `tenant_id` is passed to `AgentLoopImpl` by `build_real_llm_handler`. ⇒ wiring connects to a real consumer; the store swap actually changes runtime behaviour.
- **D-DAY0-6 (singleton home — platform_layer convention)**: all 3 existing wiring singletons (`rate_limit_counter` / `pricing` / `quota`) live in `platform_layer`; agent_harness stays DI-pure (no process-global mutable). platform_layer→agent_harness import is allowed (10+ precedents incl. `governance/`). → new `platform_layer/governance/error_budget_provider.py` (error budget = platform-protection policy per `budget.py` docstring "protect platform during incident" → governance).
- **D-DAY0-7 (test fixture reuse)**: `tests/integration/agent_harness/error_handling/test_redis_budget_store.py` uses `fakeredis.aioredis.FakeRedis(decode_responses=False)` + `RedisBudgetStore(client=...)` (fakeredis>=2.20, Sprint 53.3). Reuse for the wiring + accumulation tests.

---

## 1. Sprint Goal

Wire the already-built `RedisBudgetStore` into the chat error-handling path so the per-tenant error budget accumulates across requests (and across instances) instead of resetting every request — via a `platform_layer` singleton provider + a startup `_wire_error_budget()` (fail-open, mirroring `_wire_rate_limit_counter`) + a one-line factory swap, with NO change to `loop.py` / `budget.py` / `RedisBudgetStore`.

---

## 2. User Stories

- **US-1** — 作為平台維護者，我希望 per-tenant error budget 在 real_llm 流量中跨請求累積（非每請求歸零），以便 budget 真正能保護平台（不再形同失效）。
- **US-2** — 作為 SRE，我希望 error budget 計數在水平擴展時跨實例共享（Redis），以便多實例部署下 budget enforcement 正確。
- **US-3** — 作為開發者，我希望 budget store 走 fail-open 的 startup wiring（Redis 不可用退回 InMemory，不擋 startup），以便 dev / test / Redis 故障時服務不中斷。
- **US-4** — 作為 QA，我希望 unit/integration 測試證明「wired 後工廠拿到 Redis store + 跨工廠呼叫累積 + Redis 缺席時退回 InMemory」，以便回歸保護。

---

## 3. Technical Specifications

### 3.0 Architecture
Pure wiring, Tier 1. agent_harness defines the `BudgetStore` Protocol + both impls (`InMemoryBudgetStore`, `RedisBudgetStore`) — unchanged. platform_layer gains a process-global provider (the wiring singleton, mirroring the 3 existing ones). api/main.py wires the Redis-backed store at startup (fail-open). The chat factory looks up the wired store, falling back to InMemory. No loop.py / budget.py / schema / migration change. LLM-neutral (no provider SDK; pure Redis).

### 3.1 Budget store provider singleton (US-2/US-3) — NEW `platform_layer/governance/error_budget_provider.py`
- Module-global `_budget_store: BudgetStore | None = None` + 4 accessors mirroring `rate_limit_counter.py:526-558`:
  - `get_budget_store() -> BudgetStore` (strict; raises if uninitialised — for any strict caller)
  - `maybe_get_budget_store() -> BudgetStore | None` (lenient; the factory uses this → falls back to InMemory)
  - `set_budget_store(store: BudgetStore | None) -> None` (install at startup / test fixture)
  - `reset_budget_store() -> None` (test isolation hook, per `testing.md` §Module-level Singleton Reset Pattern)
- `BudgetStore` type imported under `TYPE_CHECKING` (`from __future__ import annotations`) — the Protocol is structural, so no runtime agent_harness coupling needed for the holder.

### 3.2 Startup wiring (US-2/US-3) — `api/main.py`
- NEW `_wire_error_budget()` mirroring `_wire_rate_limit_counter` (`:86-119`): `Redis.from_url(settings.redis_url)` → `set_budget_store(RedisBudgetStore(client))`; whole body `except Exception` **fail-open** (Redis down → store stays None → factory falls back to InMemory → budget degrades to per-request, never blocks startup). `logger.info("api.main: error budget store wired")` on success.
- Call `_wire_error_budget()` in `_lifespan` after `_wire_rate_limit_counter()` / `_wire_pricing_loader()` (`:166-167`).
- **No `app.tenant_id` / RLS / DB session** — RedisBudgetStore is pure Redis (no DB write-through); do NOT copy the rate-limit counter's `session_factory` / `_set_tenant_context` (that would be over-engineering — budget tenant isolation is already in the key).

### 3.3 Export RedisBudgetStore (US-2) — `agent_harness/error_handling/__init__.py`
- Add `RedisBudgetStore` to the imports + `__all__` (currently only `BudgetStore` / `InMemoryBudgetStore` / `TenantErrorBudget` are exported) so `api/main.py` imports it via the public package path (`from agent_harness.error_handling import RedisBudgetStore`), consistent with how rate-limit wiring imports `RedisRateLimitCounter` from the public module.

### 3.4 Chat factory swap (US-1) — `api/v1/chat/_category_factories.py`
- `:257` `TenantErrorBudget(InMemoryBudgetStore())` → `TenantErrorBudget(maybe_get_budget_store() or InMemoryBudgetStore())` + import `maybe_get_budget_store` from `platform_layer.governance.error_budget_provider`.
- Update the deferred comment (`:248-252`) to state the store is now the wired shared store (Redis when available) with InMemory fallback — AP-2 debt repaid.

### 3.5 Tests (US-4) — NEW `test_error_budget_provider.py` + extend factory/wiring test
- NEW `tests/.../error_budget_provider` unit test (or co-located): `set_budget_store` → `maybe_get_budget_store` returns it; `reset_budget_store` clears; `get_budget_store` raises when unset.
- Accumulation test (the key correctness claim): with a wired `RedisBudgetStore(FakeRedis())`, call `make_chat_error_deps()` TWICE (simulating two requests), `record()` an error via each returned `TenantErrorBudget`, assert the second `is_exceeded`/`get` reflects the ACCUMULATED count (proves the per-request reset is fixed) — vs the InMemory baseline where two factory calls would NOT accumulate.
- Fallback test: with no wired store, `make_chat_error_deps()` returns a `TenantErrorBudget` backed by `InMemoryBudgetStore` (no crash; preserves dev/test behaviour).
- Reuse the `FakeRedis(decode_responses=False)` fixture pattern from `test_redis_budget_store.py`.

### 3.6 Startup-log integration check (US-3) — local, no Azure
- Start backend; confirm startup log `error budget store wired` (mirrors `pricing loader wired` / `rate-limit counter wired`). This proves the wiring fires at startup (Risk Class E style) WITHOUT a real LLM call. **No real-Azure run** — budget only increments on tool ERRORS (hard/expensive to provoke via real chat); the fakeredis accumulation test (§3.5) is the deterministic proof of the correctness claim. (Rationale recorded so a reviewer doesn't expect a 57.79/57.80-style real-LLM leg.)

### 3.7 Lint / validation
`mypy src/` + `pytest` (new + regression) + `python scripts/lint/run_all.py` (10/10 — no schema, no LLM-SDK leak; `check_cross_category_import` must stay green for the new platform_layer→agent_harness type-only import). NO frontend / migration / wire-schema / ORM change.

---

## 4. File Change List

**NEW (2)**
- `backend/src/platform_layer/governance/error_budget_provider.py` (singleton accessors)
- `backend/tests/unit/platform_layer/governance/test_error_budget_provider.py` (provider + accumulation + fallback tests) — final path confirmed Day 1 against existing test tree

**EDIT (3)**
- `backend/src/agent_harness/error_handling/__init__.py` (export `RedisBudgetStore`)
- `backend/src/api/main.py` (`_wire_error_budget()` + call in `_lifespan`)
- `backend/src/api/v1/chat/_category_factories.py` (`maybe_get_budget_store() or InMemoryBudgetStore()` + import + deferred-comment update)

**NO frontend / migration / wire-schema / ORM / loop.py / budget.py / RedisBudgetStore change.**

---

## 5. Acceptance Criteria

- `set_budget_store` / `maybe_get_budget_store` / `get_budget_store` / `reset_budget_store` behave as the rate-limit accessors do (install / lenient / strict-raise / clear) — unit-tested.
- `_wire_error_budget()` installs a `RedisBudgetStore` from `settings.redis_url` at startup and is fail-open (Redis down → store None → factory InMemory fallback; startup never blocked).
- `make_chat_error_deps()` returns a `TenantErrorBudget` backed by the wired store when present, InMemory otherwise; with a wired Redis store, two successive factory calls + records ACCUMULATE (per-request reset fixed) — integration-tested with fakeredis.
- Startup log `error budget store wired` confirmed on a local backend start.
- Gates: backend mypy 0 + pytest (new + regression) green + run_all 10/10. No frontend.

---

## 6. Deliverables

- [ ] `error_budget_provider.py` singleton accessors (mirror rate_limit_counter)
- [ ] `_wire_error_budget()` in main.py + call in `_lifespan` (fail-open)
- [ ] Export `RedisBudgetStore` from `error_handling/__init__.py`
- [ ] Factory swap `maybe_get_budget_store() or InMemoryBudgetStore()` + deferred-comment update (AP-2 repaid)
- [ ] Tests: provider accessors + fakeredis accumulation (per-request-reset fixed) + InMemory fallback
- [ ] Startup-log `error budget store wired` confirmed (local, no Azure) — evidence in progress.md
- [ ] All gates green; closeout (CHANGE-048 + progress + retro + MEMORY + CLAUDE lean; B-7 closed)

---

## 7. Workload Calibration

Scope class `medium-backend` (0.80 — small wiring + new provider module + tests + startup-log check; lighter than 57.79/57.80 but same class). **Agent-delegated: no** (parent-direct — small careful wiring + startup verification). `agent_factor` = 1.0 → 3-segment form.

Bottom-up est ~4.3 hr (provider ~0.5 + wire fn ~0.5 + factory+export ~0.5 + tests ~1.5 + startup verify ~0.3 + closeout ~1) → class-calibrated commit ~3.4 hr (mult 0.80).

---

## 8. Dependencies & Risks

- **Dependency**: `RedisBudgetStore` + fakeredis test infra (Sprint 53.2/53.3) live; `settings.redis_url` + `Redis.from_url` pattern proven by `_wire_rate_limit_counter`. No new infra.
- **Risk: stale analysis doc line numbers** — `cat8-errorbudget-redis-wiring-analysis-20260531.md` is 18 sprints old; ALL line numbers re-verified at Day 0 (D-DAY0-1..7) against `18b6dd16`. Per the doc's own §5 tool-reliability lesson, key routing was grep-confirmed (not single-shot).
- **Risk: cross-category import** — the new platform_layer provider type-hints `BudgetStore` (agent_harness Protocol). Mitigated: TYPE_CHECKING-only import + platform_layer→agent_harness is an established allowed direction (10+ precedents); `check_cross_category_import` must stay green (Day-1 gate).
- **Risk: budget only increments on errors** — the correctness claim (accumulation) cannot be cheaply shown via a real happy-path chat; proven instead by the deterministic fakeredis accumulation test + the startup-log wiring check. No real-Azure leg this sprint (unlike 57.79/57.80 where the bug was on the happy path). Documented in §3.6 so it is not read as a coverage gap.
- **Risk: don't over-wire** — RedisBudgetStore is pure Redis; do NOT copy the rate-limit counter's DB `session_factory` / RLS `app.tenant_id` (budget tenant isolation is already in the key; adding DB write-through would be scope creep / over-engineering per the analysis §6).

---

## 9. Out of Scope (this sprint; carryover)

- **error_budgets.yaml per-tenant overrides** — the `budget.py` docstring mentions YAML-tunable per-tenant caps; the factory uses the `TenantErrorBudget` defaults (1000/day, 20000/month). Loading per-tenant overrides is a separate feature, not wiring. Not this sprint.
- **B-8 Verification default-enable** / **C-15 DevOps/data-platform billing** — the bundle's other legs; separate sprints.
- **Real-LLM budget-enforcement e2e** (provoking real tool errors to trip the budget on real Azure) — deferred; the fakeredis accumulation test is the proof here.
- **GitHub Secrets + scheduled e2e gate** (`AD-CI-6`) — production-launch concern.
