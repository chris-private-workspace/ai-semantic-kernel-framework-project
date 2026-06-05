# Sprint 57.81 Progress — B-7 ErrorBudget Redis wiring

**Branch**: `feature/sprint-57-81-errorbudget-redis` (from `main` `18b6dd16`)
**Closes**: B-7 / `AD-ErrorBudget-Redis-Wiring`

---

## Day 0 — 2026-06-05 — Plan-vs-Repo Verify + Branch + Decisions

### Accomplishments
- User picked B-7 (ErrorBudget Redis) after merging Sprint 57.80 (#246).
- Read the source analysis `cat8-errorbudget-redis-wiring-analysis-20260531.md` (18 sprints old) + re-verified ALL its claims/line-numbers against current main `18b6dd16` (the doc's own §5 warns line numbers drift + tool-reliability).
- Plan + checklist drafted (mirror 57.80 9-section / Day 0-4 format).
- Branch created.

### Day-0 verify (Prong 1 path + Prong 2 content; Prong 3 N/A — no schema)
- **Prong 1 (path)** ✅ — `_redis_store.py`, `budget.py`, `error_handling/__init__.py`, `api/main.py`, `rate_limit_counter.py`, `_category_factories.py`, `loop.py`, `test_redis_budget_store.py`, `platform_layer/governance/` all confirmed.
- **Prong 2 (content)** ✅ — D-DAY0-1..7 (plan §0):
  - **D-DAY0-1**: `RedisBudgetStore` fully impl (`_redis_store.py:35-61`, MULTI/EXEC) but **NOT exported** from `error_handling/__init__.py` → wiring must add export.
  - **D-DAY0-2**: `TenantErrorBudget` delegates all state to the `BudgetStore` (keys carry tenant_id) → per-request `TenantErrorBudget(shared_redis)` accumulates → Tier 1 wiring fixes BOTH per-request reset AND cross-instance.
  - **D-DAY0-3**: gap site `_category_factories.py:236` / deferred comment :248-252 / `TenantErrorBudget(InMemoryBudgetStore())` :257.
  - **D-DAY0-4**: wire templates `main.py:86 _wire_rate_limit_counter` + `:122 _wire_pricing_loader` (lifespan :166-167); singleton accessor pattern `rate_limit_counter.py:526-558`.
  - **D-DAY0-5 (live consumer — NOT Potemkin)**: `loop.py:218/269/320-322` — `_handle_tool_error` calls `await self._error_budget.record(self._tenant_id, cls)`; tenant_id passed by real_llm handler. Store swap changes real runtime behaviour.
  - **D-DAY0-6**: singleton → `platform_layer/governance/` (3 existing wiring singletons all in platform_layer; agent_harness DI-pure; platform→agent_harness import allowed, 10+ precedents incl governance/).
  - **D-DAY0-7**: test fixture `FakeRedis(decode_responses=False)` + `RedisBudgetStore(client=)` reusable.
- **Prong 3 (schema)** N/A — RedisBudgetStore is pure Redis, no DB write-through.

### Drift findings
- **D1 (RedisBudgetStore not exported)**: `error_handling/__init__.py` exports only BudgetStore/InMemory/TenantErrorBudget → plan §3.3 adds the export (vs the analysis doc which assumed direct use). Minor additive.
- **D2 (no drift on core claims)**: all 3 pillars (RedisBudgetStore impl / gap site / wire template) re-confirmed at new line numbers; live-consumer claim (loop.py record()) added beyond the analysis doc.
- No scope shift (≤20%). GO for Day 1.

### Decisions locked
- Singleton in **`platform_layer/governance/error_budget_provider.py`** (NOT agent_harness — DI-purity + convention).
- **Fail-open** wire (mirror `_wire_rate_limit_counter`); **NO** DB session_factory / RLS / app.tenant_id (pure Redis — budget tenant isolation already in key; copying rate-limit DB write-through = over-engineering per analysis §6).
- **NO real-Azure leg** — budget increments on tool ERRORS only (hard/expensive to provoke on real happy-path chat); the fakeredis accumulation test is the deterministic proof + a startup-log check confirms wiring fires. (Unlike 57.79/57.80 where the bug was on the happy path.)
- **parent-direct** (NOT agent-delegated — small careful wiring + startup verify). agent_factor 1.0.

### Blockers / dependencies
- None. RedisBudgetStore + fakeredis infra (53.2/53.3) + `Redis.from_url`/`settings.redis_url` pattern all live.

### Remaining for Day 1+
- Day 1: provider singleton + export + `_wire_error_budget()` + factory swap.
- Day 2: provider/accumulation/fallback tests (fakeredis).
- Day 3: startup-log `error budget store wired` confirm (local, no Azure).
- Day 4: sweep + closeout.

### Notes
- Bottom-up est ~4.3 hr → calibrated ~3.4 hr (medium-backend 0.80, parent-direct).
