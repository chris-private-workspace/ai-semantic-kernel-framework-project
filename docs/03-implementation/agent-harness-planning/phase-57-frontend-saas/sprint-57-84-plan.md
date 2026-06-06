# Sprint 57.84 Plan — C-15 billing leg: transactional billing Outbox (durable cost events + idempotent drain) (closes C-15 billing-write-atomicity / AD-Cost-Ledger-Outbox-Atomicity)

**Branch**: `feature/sprint-57-84-billing-outbox` (from `main` `179b4416`)
**Closes**: the **billing-write-atomicity leg of C-15** (the lone in-repo, billing-key-chain ② leg). IaC / DR / Analytics sub-items are external-blocked → deferred to `next-phase-candidates.md` (user decision 2026-06-05). This sprint ships the transactional Outbox backbone: cost events become durable atomically with the chat request, and an idempotent background drain materializes `cost_ledger` (Stripe consumer is future-leg).

---

## 0. Background

C-11 (57.79) fixed pricing-key + token-param billing **correctness**; B-7 (57.81) wired ErrorBudget Redis; B-8 (57.82-57.83) wired verification judge cost → ledger + flipped verification default. Those closed the "what we charge" correctness. C-15's billing leg closes the remaining **"do we reliably record the charge at all"** gap.

**The problem (Day-0 grep + code read, main `179b4416`)**:
- The chat flow is **purely in-memory** (`artifact.messages`); the only DB writes during a request are observer-driven: `sessions` (SAVEPOINT, `router.py:259`), `cost_ledger` (`router.py:445-485`), `audit_log` (SAVEPOINT, `router.py:504`), `tool_calls` (SAVEPOINT, `router.py:615`).
- `get_db_session` (`infrastructure/db/session.py:51-57`) **auto-commits after the SSE generator finishes**. The cost write is `db.add(...)` + `await db.flush()` (`cost_ledger.py:186-188`) inside that generator.
- The cost write sits in a **bare `try/except` that swallows the exception** (`router.py:453-458`, `:480-485`, `:597-600`). A flush failure (constraint, pool flake, poisoned session) is logged and dropped → the session/audit rows still attempt commit → **漏扣 (missing-charge)**: real-LLM (live since 57.79) revenue silently lost. There is **no idempotency key** on `cost_ledger` (recon: `models/cost_ledger.py` has zero unique/dedup constraint) → a future retry/replay path would **雙扣 (double-charge)**.
- **No live double-charge bug exists today** (Day-0 code recon: loop / `_verification` / tool sub_types are distinct, quota and ledger are independent layers). The present risk is **漏扣**; **雙扣** is a prevention concern for the future Stripe/retry path.

**The fix (Outbox pattern, user chose full Outbox over the lightweight option, 2026-06-05)**:
- Emit a **billing event row into a NEW `billing_outbox` table in the same request transaction** (atomic with session/audit — guaranteed to commit together; replaces the best-effort swallow).
- A **background poller drains pending outbox rows idempotently**, materializing `cost_ledger` (and, future-leg, Stripe), with a stable idempotency key so retries/replays never double-charge.

### Day-0 ground-truth (parent grep + code read, main `179b4416`)
- **Existing `outbox` design is NOT billing-shaped** (`09-db-schema-design.md:1045-1073`): `destination` ∈ {teams,email,webhook}, `source_type` ∈ {approval_request,alert} — a NOTIFICATION outbox. **No migration exists for it** (recon `grep outbox models/+migrations/` → 0). → build a dedicated `billing_outbox` (single-responsibility; do NOT cram billing into the notification schema). **Drift D1.**
- **Migration head = `0024_memory_ops`** (recon) → next = `0025`. Exact `down_revision` confirmed Day-1 by reading `0024` header.
- **No production background-task runtime**: `runtime/workers/{agent_loop_worker,queue_backend}.py` are `[STUB]` (Phase 53.1 Temporal, not wired); `MockQueueBackend` only. → the outbox poller is NEW, following the `api/main.py:_lifespan` `_wire_*` hook pattern (`_wire_rate_limit_counter` / `_wire_error_budget` precedent, 57.81). **Drift D2.**
- **No existing idempotency key** anywhere on `cost_ledger`; no `SELECT … FOR UPDATE SKIP LOCKED` idiom in repo → both NEW. Idempotency lives on `billing_outbox` (unique natural key) + an idempotent drain (claim → materialize → mark done in one txn).
- **RLS wrinkle**: per-request RLS sets `app.tenant_id` via middleware (`SET LOCAL`). The poller runs OUTSIDE a request (no tenant JWT) but must read pending rows **across all tenants**, then write `cost_ledger` **per-tenant-scoped**. Resolution (Day-3 design, confirmed against `0009_rls_policies`): a system-context escape clause on the `billing_outbox` policy for the claim read + `SET LOCAL app.tenant_id = <row.tenant_id>` before each row's `cost_ledger` materialize. **Drift D3 / Risk #3.**
- Leg-1 (57.82) judge→ledger wiring + C-11 (57.79) pricing are unchanged: the poller calls the **existing** `CostLedgerService.record_llm_call(...)` (pricing logic stays single-source); the outbox payload just carries that call's neutral args (provider/model/tokens/sub_type_suffix/session_id).

---

## 1. Sprint Goal

Make chat billing **durable + idempotent** by introducing a transactional `billing_outbox`: the chat request enqueues cost events atomically with its own DB transaction, and a new idempotent background poller drains them into `cost_ledger` — eliminating the swallowed-exception 漏扣 vector and preventing future 雙扣 — while keeping pricing/quota single-source and not regressing live real-LLM billing (shadow cut-line: direct write stays until the worker is proven, then flip to enqueue-only).

## 2. User Stories

- **US-1**: As finance, I want every chargeable LLM/tool call recorded as a durable `billing_outbox` event committed atomically with the chat request, so a ledger-write flake can no longer silently drop a charge (漏扣). (table + atomic enqueue)
- **US-2**: As finance, I want a stable idempotency key per billing event so a retry/replay/redelivery never charges twice (雙扣). (idempotency)
- **US-3**: As an operator, I want a background poller that drains pending outbox rows into `cost_ledger` idempotently with bounded retry/backoff, so transient DB/pricing failures self-heal instead of losing revenue. (drain worker)
- **US-4**: As a security owner, I want the poller to honour multi-tenant isolation (per-tenant `cost_ledger` writes; no cross-tenant leak), so the outbox does not become an isolation hole. (RLS-correct worker)
- **US-5**: As a maintainer, I want the chat router to enqueue instead of best-effort direct-write (with a safe shadow cut-line), plus unit/integration tests pinning atomicity + idempotency + isolation + drain, so the contract is verifiable and the live path doesn't regress. (router flip + tests)

## 3. Technical Specifications

### 3.0 Architecture

Transactional Outbox, single new domain in `platform_layer/billing/`. Producer side: the chat router observer enqueues a `BillingOutboxEvent` row using the **request's** `AsyncSession` (same `begin()` scope as session/audit → atomic commit). Consumer side: a NEW lifespan-managed async poller claims `pending`/retry-due rows (`FOR UPDATE SKIP LOCKED`), materializes `cost_ledger` via the **existing** `CostLedgerService.record_llm_call` (pricing single-source), marks `done`, all in one txn per claim batch; failures bump `retry_count` + `next_retry_at` (exponential backoff) and record `last_error`. LLM neutrality unaffected (payload carries neutral args; no SDK import). Multi-tenant: outbox table is `tenant_id`-scoped + RLS; the poller uses a system-context read for the claim and sets per-row tenant context for the `cost_ledger` write.

**Shadow cut-line (live-path safety)**: through Day 2 the router enqueues **in addition to** the existing direct `cost_ledger` write (dual-write shadow → billing never regresses even if the poller isn't running). Day 3 flips the router to **enqueue-only** once the poller drains correctly; the direct-write code is removed (no `_v2`/dead-code per AP-11).

### 3.1 `billing_outbox` table + migration `0025` (US-1/US-2) — NEW

- NEW `infrastructure/db/migrations/versions/0025_billing_outbox.py` (`down_revision` = `0024_memory_ops` revision id, confirmed Day-1).
- Columns: `id UUID PK`, `tenant_id UUID NOT NULL`, `event_type VARCHAR(32)` (`llm_call`/`tool_call`), `payload JSONB NOT NULL` (neutral `record_llm_call`/`record_tool_call` args: provider/model/input_tokens/output_tokens/cached_input_tokens/sub_type_suffix/tool_name/session_id), `idempotency_key VARCHAR(256) NOT NULL`, `status VARCHAR(16) NOT NULL DEFAULT 'pending'` (pending/processing/done/failed), `retry_count INT NOT NULL DEFAULT 0`, `next_retry_at TIMESTAMPTZ`, `last_error TEXT`, `session_id UUID`, `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `processed_at TIMESTAMPTZ`.
- Constraints/indexes: `UNIQUE (tenant_id, idempotency_key)` (idempotency — US-2); `idx_billing_outbox_due` on `(next_retry_at)` `WHERE status IN ('pending','failed')`; `idx_billing_outbox_tenant` on `(tenant_id)`; `CHECK` on status/event_type enums.
- **RLS** (multi-tenant 鐵律): `ENABLE ROW LEVEL SECURITY` + `tenant_isolation_billing_outbox` policy mirroring `0009_rls_policies` style, **plus** a system-context escape clause for the poller claim (Day-3, confirmed against `0009`). `run_all.py` `check_rls_policies` must stay green.
- ORM model `infrastructure/db/models/billing_outbox.py` (TenantScopedMixin) + register in `models/__init__.py` (after `cost_ledger` import) so Alembic/`check_rls_policies` see it.

### 3.2 `BillingOutboxService` enqueue (US-1/US-2) — `platform_layer/billing/billing_outbox.py` NEW

- `async def enqueue(self, db, *, tenant_id, event_type, payload, idempotency_key, session_id) -> None`: `db.add(BillingOutboxEvent(...))` + `flush()` using the **passed-in request session** (caller's txn). On `UNIQUE(tenant_id, idempotency_key)` conflict → swallow as no-op (idempotent enqueue; a redelivered event is not re-queued).
- Idempotency key builder: stable per logical event, e.g. `f"{session_id}:{event_type}:{sub_type_suffix or 'loop'}"` for LLM (loop vs `_verification` distinct), `f"{session_id}:tool:{tool_name}:{seq}"` for tools (seq from a per-request monotonic counter so repeated same-tool calls in one loop are distinct but replays are stable). Decide final shape Day-2 against the real router event stream.
- Module-level singleton + `set_/get_/maybe_get_billing_outbox` accessors mirroring `cost_ledger.py:272-295` (testability + reset hook per testing.md §Module-level Singleton Reset).

### 3.3 `BillingOutboxDrainer` idempotent drain (US-3/US-4) — same module

- `async def drain_once(self, system_db_factory) -> DrainStats`: claim a batch of due rows (`status='pending' OR (status='failed' AND next_retry_at<=now)`) via `FOR UPDATE SKIP LOCKED LIMIT N`; per row: `SET LOCAL app.tenant_id = row.tenant_id` → call existing `CostLedgerService.record_llm_call/record_tool_call` from `payload` → mark `status='done', processed_at=now`; on exception bump `retry_count`, set `next_retry_at = now + backoff(retry_count)`, `status='failed'`, `last_error`; after `MAX_RETRY` leave `failed` (dead-letter, surfaced by metric/log — NOT silently dropped). Idempotency: claim+materialize+mark in one txn so a crash mid-row re-claims it; the `done` flag + `cost_ledger` write are committed together (no double-charge on re-claim).

### 3.4 Lifespan poller wiring (US-3) — `api/main.py`

- NEW `_wire_billing_outbox_drainer()` in `_lifespan` (mirror `_wire_error_budget` 57.81): construct `BillingOutboxDrainer` + start an `asyncio.create_task` polling loop (`while not stop: await drain_once(); await asyncio.sleep(BILLING_OUTBOX_POLL_INTERVAL_S)`), store the task + a stop event on app state; cancel + await on shutdown. Fail-open: a poller crash logs + restarts the loop (never crashes app). Env: `BILLING_OUTBOX_POLL_INTERVAL_S` (default 5), `BILLING_OUTBOX_BATCH` (default 50), `BILLING_OUTBOX_MAX_RETRY` (default 8). A test/CI flag `BILLING_OUTBOX_DRAINER_ENABLED` (default true; conftest sets false) keeps the background task out of unit-test event loops (audit-observer precedent `router.py:498`).

### 3.5 Router flip (US-5) — `api/v1/chat/router.py`

- Day-2 (shadow): after each existing `cost_ledger.record_*` call, ALSO `billing_outbox.enqueue(...)` with the same args + idempotency key (dual-write; billing never regresses).
- Day-3 (flip): remove the direct `cost_ledger.record_*` calls from the 3 sites (loop / `_verification` / tool); the observer now ONLY enqueues; the poller materializes. Keep the best-effort isolation (enqueue failure must not break SSE — but now enqueue is in the guaranteed request txn, so a failure rolls the whole request back, which is the correct atomic behaviour — decide swallow-vs-propagate Day-3 with a test).

### 3.6 Tests (US-5) + 17.md

- Unit: `test_billing_outbox_service.py` — enqueue adds row; duplicate idempotency_key is no-op; drain_once materializes cost_ledger from payload; drain idempotent (run twice → one cost row); retry/backoff on materialize failure; dead-letter after MAX_RETRY.
- Integration: `test_chat_billing_outbox.py` — chat request enqueues outbox rows atomically (commit) ; drain produces the same cost_ledger rows the old direct path produced (parity); multi-tenant: tenant A's poller-materialized cost rows are tenant-A scoped, no tenant-B leak (Risk Class C singleton reset fixture).
- 17.md `17-cross-category-interfaces.md`: register the BillingOutbox enqueue/drain contract under the billing/governance cross-cutting section (single-source).

### 3.7 Lint / validation

`black + isort + flake8 + mypy src/` 0 + `run_all.py` 10/10 (esp. `check_rls_policies` for the new table + `check_llm_sdk_leak`). Full format chain pre-commit.

## 4. File Change List

**Code — NEW (4)**:
1. `backend/src/infrastructure/db/models/billing_outbox.py` — BillingOutboxEvent ORM (TenantScopedMixin)
2. `backend/src/infrastructure/db/migrations/versions/0025_billing_outbox.py` — table + indexes + RLS policy
3. `backend/src/platform_layer/billing/billing_outbox.py` — BillingOutboxService (enqueue) + BillingOutboxDrainer (drain) + singleton accessors
4. (poller wiring lives in `api/main.py` — edit, not new)

**Code — EDIT (3)**:
5. `backend/src/infrastructure/db/models/__init__.py` — register BillingOutboxEvent
6. `backend/src/api/main.py` — `_wire_billing_outbox_drainer()` lifespan hook + shutdown cancel
7. `backend/src/api/v1/chat/router.py` — Day-2 shadow enqueue → Day-3 flip to enqueue-only

**Config (1)**:
8. `backend/src/core/config/__init__.py` — `billing_outbox_poll_interval_s` / `_batch` / `_max_retry` / `_drainer_enabled` settings

**Tests (2 NEW)**:
9. `backend/tests/unit/platform_layer/billing/test_billing_outbox_service.py`
10. `backend/tests/integration/billing/test_chat_billing_outbox.py` (+ conftest singleton reset)

**Docs (2)**:
11. `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — BillingOutbox contract
12. `claudedocs/4-changes/feature-changes/CHANGE-051-billing-outbox.md`

## 5. Acceptance Criteria

1. `billing_outbox` table exists (migration `0025` applies on the `0024` head), `tenant_id` + RLS policy present, `UNIQUE(tenant_id, idempotency_key)` enforced; `check_rls_policies` green.
2. Chat request enqueues a durable outbox row per chargeable event atomically with its own transaction (integration test proves: request commit ⟺ outbox row present; no best-effort swallow on the producer side post-flip).
3. The drainer materializes the SAME `cost_ledger` rows the old direct path produced (parity test), idempotently (run drain twice → exactly one cost row per event), with retry/backoff + dead-letter after MAX_RETRY.
4. Multi-tenant isolation holds: poller-materialized `cost_ledger` rows are scoped to the originating tenant; no cross-tenant leak (isolation test).
5. Router flipped to enqueue-only (direct `cost_ledger.record_*` removed from the 3 sites; no dead code/`_v2`); live real-LLM chat still bills (verified — see §8 Risk #1 measurement).
6. `mypy src/` 0; full pytest green; `run_all.py` 10/10 (`check_llm_sdk_leak` + `check_rls_policies`).

## 6. Deliverables

- [ ] US-1: `billing_outbox` table + migration `0025` + RLS + ORM + register
- [ ] US-2: idempotency key (UNIQUE + builder) + idempotent enqueue
- [ ] US-3: `BillingOutboxDrainer` drain_once + lifespan poller + retry/backoff/dead-letter
- [ ] US-4: multi-tenant-correct drain (system claim + per-row tenant context)
- [ ] US-5: router shadow → flip; unit + integration tests (atomicity/idempotency/parity/isolation)
- [ ] Closeout: CHANGE-051 + 17.md + progress + retrospective + checklist + MEMORY + CLAUDE lean + next-phase-candidates (defer IaC/DR/Analytics)

## 7. Workload Calibration

- **Agent-delegated: no** (parent-direct — atomicity boundary, RLS-correct worker, and the live-billing-path flip are judgment-sensitive; consistent with billing sprints 57.79-57.83 all parent-direct). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~10.5 hr (schema+migration+RLS ~1.5 / ORM+register ~0.5 / service enqueue+drain+idempotency ~2.5 / router shadow+flip ~1.5 / poller+lifespan+shutdown+system-tenant ~2 / tests ~2.5) → class-calibrated commit ~8.4 hr (`medium-backend` 0.80).
- **Size caveat (honest)**: this is ≈2× a normal sprint and touches a real-LLM-live billing path. The Day structure carries the safety: **Day-2-end is a safe cut-line** (shadow dual-write — billing works via either path). If the Day-3 live-path flip + RLS-worker proves riskier than estimated, ship Day-1-2 (durable enqueue + shadow + drainer) and **carryover the enqueue-only flip** (the AD splits cleanly; not a failure). Noted in §8 Risk #2.

## 8. Dependencies & Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Flipping the live real-LLM billing path (enqueue-only) could silently regress billing | Shadow dual-write through Day 2 (billing never regresses); Day-3 flip gated on a drain-parity integration test; a real-Azure smoke (1-2 chats, mode=real_llm) confirms a `cost_ledger` row still appears via the drained path before closeout (57.79/57.80 local-backend pattern; user-authorized). Env rollback: re-enable direct write is a 1-commit revert. |
| 2 | Full Outbox is large (~8.4 hr) for one sprint | Day-2-end cut-line (shadow) = safe partial ship; enqueue-only flip can carryover as `AD-Billing-Outbox-Flip` if Day-3 over-runs. Not a failure — durable enqueue + drainer alone close the 漏扣 vector. |
| 3 | RLS: poller reads cross-tenant but must write per-tenant `cost_ledger` (Drift D3) | Day-3: read `0009_rls_policies` first; add a system-context escape clause to the `billing_outbox` policy for the claim read + `SET LOCAL app.tenant_id = row.tenant_id` per row before the `cost_ledger` materialize. Isolation test (US-4) is the gate. `check_rls_policies` must stay green. |
| 4 | Background `asyncio` task in lifespan leaking into unit-test event loops (Risk Class C/E) | `BILLING_OUTBOX_DRAINER_ENABLED` flag (conftest sets false; audit-observer precedent `router.py:498`); singleton reset autouse fixture; clean backend restart for the real-Azure smoke (Risk Class E — stale `--reload` masks lifespan wiring, 57.81/57.79 lesson). |
| 5 | Idempotency key collision or over-uniqueness (replays vs distinct same-tool calls in one loop) | Key builder decided Day-2 against the real router event stream; tool calls use a per-request monotonic seq; unit test covers duplicate-key no-op + distinct-event separation. |
| 6 | Drift D1: 09.md `outbox` is notification-shaped, not billing | Deliberately build dedicated `billing_outbox` (single-responsibility); do NOT reuse/extend the unbuilt notification design; documented in §0 + 17.md. |
| 7 | LLM neutrality | Payload carries neutral `record_llm_call` args; drainer calls existing `CostLedgerService` (pricing single-source); no SDK import. `check_llm_sdk_leak` green. |

## 9. Out of Scope (this sprint; carryover → next-phase-candidates.md)

- **C-15 IaC deploy pipeline** — external-blocked (Azure provision + GitHub Secrets). Deferred.
- **C-15 DR automation / multi-region / WAL** — external-blocked (Azure infra decisions). Deferred.
- **C-15 Analytics / data warehouse / CDC / dbt** — fully external infra. Deferred.
- **Stripe (external billing) consumer** — the outbox backbone is built for it, but this sprint's drainer materializes `cost_ledger` only; the Stripe drain target is a future worker-only change (the whole point of the outbox decoupling).
- **Notification outbox** (the 09.md teams/email/webhook design) — separate concern, not built here.
- **Per-verifier cost attribution / multi-judge registry** — B-8 carryovers, unrelated.
