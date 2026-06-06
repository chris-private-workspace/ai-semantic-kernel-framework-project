# Sprint 57.84 — Checklist (C-15 billing leg: transactional billing Outbox)

**Plan**: `sprint-57-84-plan.md`
**Branch**: `feature/sprint-57-84-billing-outbox` (from `main` `179b4416`)
**Closes**: C-15 **billing-write-atomicity leg** / `AD-Cost-Ledger-Outbox-Atomicity`. IaC/DR/Analytics deferred (external-blocked).

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (parent grep + code read, main `179b4416`)
- [x] **Prong 1 (path)** — confirm: `api/v1/chat/router.py` (cost-write observer), `platform_layer/billing/cost_ledger.py` (CostLedgerService + singleton accessors), `infrastructure/db/session.py` (get_db_session auto-commit), `infrastructure/db/models/cost_ledger.py` + `models/__init__.py`, `api/main.py` `_lifespan` + `_wire_*`, `runtime/workers/*` (stubs), migration head `0024_memory_ops`.
- [x] **Prong 2 (content)** — chat flow in-memory; cost write best-effort try/except + flush (漏扣 vector); no idempotency key on cost_ledger; no live double-charge (sub_types distinct); no production worker runtime (`[STUB]`); no `SKIP LOCKED` idiom; poller must follow `_wire_*` lifespan pattern.
- [x] **Prong 3 (schema)** — 09.md `outbox` is NOTIFICATION-shaped (teams/email/webhook), NOT billing → build dedicated `billing_outbox` (D1); migration head `0024` → next `0025` (exact down_revision read Day-1); cost_ledger has NO unique/dedup key; new model must register in `models/__init__.py`; RLS poller-cross-tenant wrinkle (D3).
- [x] **Drift findings** — D1 (notification outbox ≠ billing → dedicated table); D2 (no worker runtime → new lifespan poller); D3 (RLS: poller reads cross-tenant, writes per-tenant → system-context escape + per-row tenant SET).
- [x] **Design locked** (AskUserQuestion 2026-06-05): scope = billing-write-atomicity leg only (IaC/DR/Analytics deferred); depth = **full Outbox** (table + migration + idempotent worker + publisher). parent-direct.
- [x] **go/no-go** — GO; shadow cut-line at Day-2-end; flip can carryover if Day-3 over-runs.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-84-billing-outbox`
- [x] **Decisions locked**: dedicated `billing_outbox`; atomic enqueue in request txn; lifespan async poller (`SKIP LOCKED` + backoff + dead-letter); idempotency via `UNIQUE(tenant_id, idempotency_key)` + idempotent drain; shadow dual-write Day-2 → enqueue-only flip Day-3; drainer materializes `cost_ledger` (Stripe future-leg); parent-direct (`agent_factor` 1.0).
- [x] **Day-0 commit** plan + checklist + progress.md Day 0 (`ef8c1f3e`)

---

## Day 1 — Schema: `billing_outbox` table + migration + ORM (US-1/US-2)

### 1.1 ORM model
- [x] **NEW `infrastructure/db/models/billing_outbox.py`** — `BillingOutboxEvent` (TenantScopedMixin): id(BigInteger PK)/tenant_id/event_type/payload(JSONB)/idempotency_key/status/retry_count/next_retry_at/last_error/session_id/created_at/processed_at + UNIQUE + 2 CHECK + 2 Index
  - DoD: mypy clean ✅ (`dict[str, object]` for JSONB under strict); columns match plan §3.1
- [x] **Register** in `infrastructure/db/models/__init__.py` (after audit, before cost_ledger import) + `__all__`
  - DoD: `check_rls_policies` discovers `billing_outbox` (10/10 green) ✅

### 1.2 migration 0025
- [x] **Read `0024_memory_ops.py` header** → `revision="0024_memory_ops"` → `down_revision="0024_memory_ops"`
- [x] **NEW `migrations/versions/0025_billing_outbox.py`** — CREATE TABLE + `UNIQUE(tenant_id, idempotency_key)` + `idx_billing_outbox_due` (partial WHERE status IN pending/failed) + `idx_billing_outbox_tenant` + status/event_type CHECK + ENABLE+FORCE RLS + `tenant_isolation_billing_outbox` (USING + **system-sentinel escape** for drainer) + `tenant_insert_billing_outbox` (WITH CHECK) — mirror 0024 two-policy
  - DoD: applied **both directions** on Docker DB (upgrade → downgrade -1 → re-upgrade; head=`0025_billing_outbox`) ✅. Lint leniency confirmed (`check_rls_policies` only needs ENABLE+CREATE POLICY, not USING content) → full escape RLS in Day-1 (D3 resolved early)
- [x] **black + isort + flake8 + mypy src/** — clean (mypy 0/334; flake8 0; black/isort applied)

---

## Day 2 — Service: enqueue + drain + tests (US-1/US-2/US-3/US-4)

> **Day-序 resequence** (noted in progress.md, not a scope change): the router **shadow + flip** both move to Day 3 (shadow becomes the Day-3 intra-day safety step before the flip). Day 2 = pure new module + tests, ZERO risk to the existing cost-write path (nothing wired). The drainer is integration-tested NOW (before Day-3 wiring).

### 2.1 BillingOutboxService.enqueue
- [x] **NEW `platform_layer/billing/billing_outbox.py`** — `BillingOutboxService.enqueue(db, *, tenant_id, event_type, payload, idempotency_key, session_id)` using the passed-in request session; `pg_insert(...).on_conflict_do_nothing(constraint="uq_billing_outbox_idem")` (idempotent enqueue); singleton accessors (`set_/get_/maybe_get_billing_outbox`, reset hook)
  - DoD: enqueue adds row in caller's txn ✅; duplicate key no-op ✅ (unit tests)

### 2.2 BillingOutboxDrainer.drain_once
- [x] **`BillingOutboxDrainer.drain_once() -> DrainStats`** — per-row independent txn: claim ONE due row (`FOR UPDATE SKIP LOCKED LIMIT 1` under sentinel) → `set_config('app.tenant_id', row.tenant_id, true)` → existing `CostLedgerService.record_llm_call/record_tool_call` from payload → mark `done` (same commit = exactly-once); on materialize failure → rollback (clears poisoned session + releases lock) → fresh txn records retry/backoff/last_error; dead-letter (status=failed, next_retry_at=NULL) after MAX_RETRY
  - DoD: claim+materialize+mark atomic (no 雙扣) ✅; pricing single-source (existing CostLedgerService) ✅ (drain integration tests)

### 2.3 idempotency key builder
- [x] **Idempotency key builder** — `llm_idempotency_key(session_id, sub_type)` = `{sid}:llm:{sub_type or 'loop'}` (loop vs _verification distinct); `tool_idempotency_key(session_id, tool_name, seq)` = `{sid}:tool:{tool_name}:{seq}` (per-request monotonic seq)
  - DoD: loop≠verification, same-tool seq disambiguation (unit tests)
- [→] **`router.py` shadow** — MOVED to Day 3 (intra-day safety step before flip). Not deleted; see Day 3.

### 2.4 unit + integration tests + gate
- [x] **NEW `test_billing_outbox_service.py`** (unit, db_session) — enqueue adds pending row / dup key no-op + pure helpers (key builders / backoff exponential+capped / payload validators incl. error cases) — 6 tests
- [x] **NEW `test_billing_outbox_drain.py`** (integration, committed data + cleanup) — drain materializes cost_ledger PARITY / idempotent-twice (→ exactly-once) / reschedule+backoff / dead-letter after max_retry / **2-tenant scoping (US-4)** — 5 tests
- [x] **black + isort + flake8 + mypy src/** — clean (mypy 0/335; flake8 0); **pytest 11/11 green** (6 unit + 5 integration)
  - Fix during gate: `SET LOCAL app.tenant_id = :p` → `SELECT set_config('app.tenant_id', :p, true)` (asyncpg rejects bind params on SET utility; mirror `middleware/tenant_context.py`); `int ** int`→`Any` mypy → bit-shift `<<`; removed stray `tests/integration/billing/__init__.py` (basename `billing` package collided with unit test pkg)
- [x] **Cut-line checkpoint** — Day-2-end = safe (nothing wired; existing cost-write path untouched). Day-3 flip risk assessed: drainer proven by integration tests → safe to wire.

---

## Day 3 — Poller wiring + router flip + RLS-correct drain (US-3/US-4/US-5)

### 3.1 lifespan poller
- [x] **`api/main.py`** — `_wire_billing_outbox()` (enqueue singleton) + `_billing_outbox_poll_loop` (fail-open, stop-event-interruptible sleep) + `_start_billing_outbox_drainer(app)` (env `BILLING_OUTBOX_DRAINER_ENABLED` gate; pricing-loader dep; `asyncio.create_task`; task+stop on app.state) + lifespan startup calls + shutdown cancel (stop BEFORE OTel/engine teardown)
- [x] **`core/config/__init__.py`** — `billing_outbox_poll_interval_s` (5) / `_batch` (50) / `_max_retry` (8) settings + docstring (enabled flag = os.environ, not Settings, to dodge the lru_cache trap)

### 3.2 RLS-correct cross-tenant drain
- [x] **RLS escape** — resolved at **Day-1** (0025 migration already carries the system-sentinel escape in the `tenant_isolation_billing_outbox` USING clause; `check_rls_policies` lenient → no separate migration). Drainer `set_config('app.tenant_id', sentinel)` for the claim + per-row `set_config(..., row.tenant_id)` before the `cost_ledger` materialize.
  - DoD: `check_rls_policies` green ✅; **2-tenant isolation test** (drain test US-4) passes ✅

### 3.3 router flip to enqueue-only
- [x] **`router.py` flip** — removed direct `cost_ledger.record_*` from the 3 sites; observer now ONLY `billing_outbox.enqueue(...)`; removed `cost_ledger`/`PricingLoader`/`maybe_get_pricing_loader` imports + `pricing_loader` endpoint dep + per-request `CostLedgerService`; `_FALLBACK_PRICING_MODEL` retained (drainer prices); tool_seq counter; no dead code (AP-11). Swallow-vs-propagate: kept **logged best-effort** (SSE safety, consistent w/ sessions/audit observers); atomicity from the shared request txn (enqueue = single INSERT committing with session/audit).
- [x] **Updated existing callers of the flipped contract** — `test_chat_cost_ledger.py` (2 tests → assert outbox; quota test unchanged) + `test_phase56_3_e2e.py` (cost section → outbox; SLA + quota unchanged). Other `_stream_loop_events` callers don't pass `cost_ledger=` → unaffected.

### 3.4 Day-3 regression fix — test-isolation (Risk Class C)
- [x] **Root cause (bisected `unit/api`+incident, 2s repro)** — `_wire_billing_outbox()` in the lifespan sets the module singleton; shutdown doesn't unset it (correct for prod). `test_main_lifespan` (TestClient) leaks it → a downstream chat-path test consumes `maybe_get_billing_outbox()` → enqueues on the GLOBAL engine without dispose → a later `db_session` test (`incident/test_service`) hits `RuntimeError: Event loop is closed`. Verified pre-sprint main clean (2150) → I introduced it (not pre-existing).
- [x] **Fix** — autouse `_reset_billing_outbox_singleton` in `tests/conftest.py` (`set_billing_outbox(None)` around each test; testing.md §Module-level Singleton Reset) + drain test dedicated NullPool engine (isolates direct-session churn) + `SET LOCAL`→`set_config(...)` (Day-2).
  - DoD: full suite **2161 passed** (was 1 flaky fail); mypy 0/335; run_all 10/10

---

## Day 4 — Integration tests + real-Azure smoke + Closeout

### 4.1 integration + isolation
- [x] **Coverage achieved across existing files (no separate `test_chat_billing_outbox.py` — would duplicate)** — producer (chat → enqueue): `test_chat_cost_ledger.py` + `test_phase56_3_e2e.py` (Day 3); drainer parity + idempotent-twice + dead-letter + **2-tenant isolation (US-4)**: `test_billing_outbox_drain.py` (Day 2). The full chat→enqueue→drain→cost_ledger chain on real data = the real-Azure smoke below. A separate automated chain test would need the committed-data pattern (db_session rolls back) and mostly re-assert the drain test — skipped to avoid redundant infra.
- [x] **real-Azure smoke** ✅ (user-authorized; Risk Class E clean restart) — `real_llm` chat (session f5f60c3a, gpt-5.2) → 1 `llm_call` outbox row drained to `done` → 2 `cost_ledger` rows via the DRAINER (input qty=1997 + output qty=41, **unit_cost > 0** — C-11 normalize works through the drainer). Chain chat→enqueue→drain→cost_ledger verified live. Backend stopped + temps removed.

### 4.2 Full sweep
- [x] **Backend gates** — black/isort/flake8 0 + `mypy src/` 0/335 + `pytest` 2161 passed/4 skipped + `run_all.py` 10/10 (`check_rls_policies` + `check_llm_sdk_leak` + `check_event_schema_sync` green)
- [x] **No frontend** — backend + docs only
- [x] **Read all changed code** — final pass (router flip, drainer, migration, conftest fix)

### 4.3 Closeout docs
- [x] **CHANGE-051** in `claudedocs/4-changes/feature-changes/`
- [→] **17.md** — **N/A** (assessed): 17.md is the 11+1 cross-CATEGORY registry (ChatClient / LoopEvent / HITL / tool registry); platform_layer.billing is not registered there (sibling `cost_ledger` is absent too). BillingOutbox is documented in CHANGE-051 + module docstrings + the plan — forcing it into 17.md would violate that file's scope.
- [x] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7 (atomicity design + flip + real-Azure smoke)
- [x] **Checklist** all `[x]` (no flip carryover — flip shipped; smoke passed)
- [x] **Calibration** record (medium-backend 0.80; agent_factor 1.0 parent-direct; ratio ~1.1-1.2 — over-run entirely the Day-3 singleton-leak debug; large-sprint note in retro Q2)
- [x] **AD status**: C-15 billing-write-atomicity leg **CLOSED**; IaC/DR/Analytics deferred → next-phase-candidates.md (no flip carryover)
- [x] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [x] **Design note?** — **NO** (feature-continuation within the billing key-chain; new pattern but no new domain spike / no new cross-CATEGORY contract — lives in CHANGE-051 + module docstrings + plan; per §Step 5.5 spike-vs-continuation)

### 4.4 Ship
- [x] **Commit mapping** Day-0 `ef8c1f3e` / Day-1 schema `cd84b437` / Day-2 service+tests `fe4beeed` / Day-3 flip+poller+fix `51524a35` / Day-4 closeout (pending)
- [ ] **Push + PR** (user-gated — explicit authorization required)
