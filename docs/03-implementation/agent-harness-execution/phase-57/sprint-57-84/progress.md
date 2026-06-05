# Sprint 57.84 Progress — C-15 billing leg: transactional billing Outbox

**Branch**: `feature/sprint-57-84-billing-outbox` (from `main` `179b4416`)
**Closes**: C-15 **billing-write-atomicity leg** (durable cost events + idempotent drain). IaC/DR/Analytics deferred (external-blocked).

---

## Day 0 — 2026-06-05 — Plan-vs-Repo Verify + Branch + Decisions

### Accomplishments
- A/B/C area sweep → user picked **C-15**; two parallel read-only Explore recons (planning-doc scope + cost_ledger code map) defined the real shape.
- AskUserQuestion ×1 (2 questions): scope = **billing-write-atomicity leg only** (IaC/DR/Analytics external-blocked → deferred); depth = **full Outbox pattern**.
- Day-0 三-prong verify (Prong 1 path + Prong 2 content + Prong 3 schema — schema in scope) + 3 drift findings.
- Plan + checklist drafted (mirror 57.83 9-section / Day 0-4); branch created.

### Day-0 verify (Prong 1 + 2 + 3)
- **Prong 1 (path)** ✅ — `router.py` cost observer, `cost_ledger.py` service+accessors, `session.py:41-57` get_db_session auto-commit, `models/cost_ledger.py` + `models/__init__.py`, `api/main.py` `_lifespan`+`_wire_*`, `runtime/workers/*` stubs, migration head `0024_memory_ops`.
- **Prong 2 (content)** ✅:
  - Chat flow PURELY in-memory (`artifact.messages`); only DB writes = observer `sessions`/`cost_ledger`/`audit_log`/`tool_calls`. `get_db_session` auto-commits AFTER the SSE generator (`session.py:51-57`).
  - Cost write = `db.add`+`flush()` in a **bare try/except that swallows** (`router.py:453-458/:480-485/:597-600`) → **漏扣 vector**. NO idempotency key on cost_ledger.
  - **No live 雙扣 bug** (loop / `_verification` / tool sub_types distinct; quota & ledger independent layers). Present risk is 漏扣; 雙扣 is future-retry prevention.
  - No production worker runtime (`runtime/workers` `[STUB]` Phase 53.1; MockQueueBackend only); no `SKIP LOCKED` idiom; poller must follow `_wire_*` lifespan pattern (57.81 `_wire_error_budget` precedent).
- **Prong 3 (schema)** ✅:
  - 09.md `outbox` (`:1045-1073`) is NOTIFICATION-shaped (`destination` teams/email/webhook; `source_type` approval_request/alert) — **NOT billing**; no migration exists → dedicated `billing_outbox`.
  - Migration head `0024_memory_ops` → next `0025` (exact `down_revision` read Day-1).
  - `cost_ledger` ORM has NO unique/dedup key (recon); new model registers in `models/__init__.py`.

### Drift findings
- **D1** — 09.md `outbox` is notification-shaped, not billing. Implication: build dedicated `billing_outbox` table (single-responsibility); do NOT reuse/extend the unbuilt notification design. (plan §0 + §8 Risk #6)
- **D2** — no production background-task runtime (`runtime/workers` stubs). Implication: outbox poller is NEW, following the `api/main.py:_lifespan` `_wire_*` hook pattern (57.81). (plan §3.4)
- **D3** — RLS: the poller runs outside a request (no tenant JWT) but reads pending rows cross-tenant while writing `cost_ledger` per-tenant. Implication: system-context escape clause on the `billing_outbox` policy for the claim read + `SET LOCAL app.tenant_id = row.tenant_id` per row before the materialize. Resolved Day-3 against `0009_rls_policies`. (plan §8 Risk #3)

### Decisions locked (AskUserQuestion 2026-06-05)
- **Scope** = billing-write-atomicity leg ONLY. C-15 IaC / DR / multi-region / Analytics are external-blocked (Azure provision + Secrets + infra decisions + new external infra) → deferred to `next-phase-candidates.md`.
- **Depth** = **full Outbox pattern** (table + migration + idempotent worker + publisher) — user chose this over the lightweight transactional-coupling option, motivated by future external (Stripe) billing-consumer decoupling.
- **parent-direct** (NOT agent-delegated) — atomicity boundary, RLS-correct worker, and the live-billing-path flip are judgment-sensitive (consistent with billing sprints 57.79-57.83).
- **Shadow cut-line**: Day-2-end dual-write (billing never regresses) is a safe partial-ship point; Day-3 enqueue-only flip can carryover if it over-runs.

### Blockers / dependencies
- **Day 4 real-Azure smoke** (user-authorized, bounded 1-2 chats) — confirm a `cost_ledger` row still appears via the DRAINED path post-flip. Clean backend restart (Risk Class E).

### Remaining for Day 1+
- Day 1: `billing_outbox` ORM + register + migration `0025` (+ RLS).
- Day 2: `BillingOutboxService.enqueue` + `BillingOutboxDrainer.drain_once` + router shadow dual-write + unit tests. **(Day-2-end cut-line)**
- Day 3: lifespan poller wiring + RLS-correct cross-tenant drain + router flip to enqueue-only.
- Day 4: integration/isolation tests + real-Azure smoke + closeout.

### Notes
- Bottom-up est ~10.5 hr → calibrated ~8.4 hr (`medium-backend` 0.80, parent-direct, `agent_factor` 1.0). Large sprint (≈2× normal); Day structure carries the safety via the Day-2-end shadow cut-line.
- LLM neutrality preserved: outbox payload carries neutral `record_llm_call` args; drainer calls the EXISTING `CostLedgerService` (pricing single-source, C-11/57.79 unchanged).

---

## Day 1 — 2026-06-05 — Schema: billing_outbox table + migration + ORM (US-1/US-2)

### Accomplishments
- **NEW `infrastructure/db/models/billing_outbox.py`** — `BillingOutboxEvent` (TenantScopedMixin): BigInteger PK (ordered drain), event_type/payload(JSONB `dict[str, object]`)/idempotency_key/status/retry_count/next_retry_at/last_error/session_id/created_at/processed_at; `UNIQUE(tenant_id, idempotency_key)` (idempotency) + status/event_type CHECK + `idx_billing_outbox_due` (partial WHERE status IN pending/failed) + `idx_billing_outbox_tenant`. Enums `OutboxStatus`/`OutboxEventType`.
- **Registered** in `models/__init__.py` (import + `__all__`).
- **NEW migration `0025_billing_outbox.py`** (down_revision `0024_memory_ops`) — table + 2 indexes + ENABLE+FORCE RLS + two policies mirroring 0024, **plus the drainer system-context escape** in the USING clause (all-zeros sentinel → cross-tenant visibility for the poller claim).

### Key decision — D3 (RLS cross-tenant drain) resolved at Day-1, not Day-3
- Read `scripts/lint/check_rls_policies.py`: the lint only requires `ENABLE ROW LEVEL SECURITY` + a `CREATE POLICY ... ON <table>` (regex), it does **NOT** constrain the USING expression. → I can write the full poller-escape RLS in the Day-1 migration without a second migration on Day-3. The escape: `tenant_id = current_setting('app.tenant_id', true)::uuid OR current_setting(...) = '00000000-...-0'::uuid`. A real request never runs under the all-zeros sentinel (missing JWT → 401), so per-request isolation is unaffected; the isolation test (US-4, Day-4) is the gate.

### Verification
- Migration applied **both directions** on Docker DB (ipa_v2, head was `0024_memory_ops`): upgrade → downgrade -1 (drops cleanly) → re-upgrade; `alembic current` = `0025_billing_outbox (head)`.
- `run_all.py` **10/10 green** (`check_rls_policies` recognizes `billing_outbox`; `check_llm_sdk_leak` green — no SDK import).
- `mypy src/` **0 issues / 334 files** (+2 vs 332: new model); black/isort applied; flake8 0.

### Remaining for Day 2+
- Day 2: `BillingOutboxService.enqueue` (idempotent) + `BillingOutboxDrainer.drain_once` (claim/materialize/mark idempotent) + idempotency-key builder + router **shadow dual-write** + unit tests. **Day-2-end = safe cut-line.**
- Day 3: lifespan poller wiring + per-row tenant-context drain + router flip to enqueue-only.
- Day 4: integration/isolation tests + real-Azure smoke + closeout.

### Notes
- Day-1 was lighter than the ~1.5+0.5 hr bottom-up (schema + model + migration ≈ 1 hr) — the lint-leniency discovery folded the D3 RLS design into Day-1 cleanly.
