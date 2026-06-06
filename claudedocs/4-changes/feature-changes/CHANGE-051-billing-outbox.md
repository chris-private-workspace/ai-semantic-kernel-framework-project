# CHANGE-051: Transactional billing Outbox (durable cost events + idempotent drain)

**Date**: 2026-06-05
**Sprint**: 57.84
**Scope**: platform_layer.billing + api/v1/chat + infrastructure/db (C-15 billing-write-atomicity leg)

## Problem
Chat billing was best-effort: the chat observer wrote `cost_ledger` directly inside a bare `try/except` that swallowed failures (`router.py`). A ledger-write flake therefore silently dropped a charge (**漏扣**) while the rest of the request committed — real money on the now-live real-LLM path. There was also no idempotency key on `cost_ledger`, so any future retry/replay path would **雙扣** (double-charge). (No live double-charge bug existed; the present risk was 漏扣 + future-retry prevention.) This is the lone in-repo, billing-key-chain ② leg of C-15; the IaC / DR / Analytics sub-items are external-blocked and deferred.

## Root Cause
The cost write was not transactionally coupled to the request and was isolated as best-effort (so a failure couldn't break the SSE stream). That isolation is exactly what made a failed write a silent revenue loss.

## Solution
Transactional Outbox pattern (user chose full Outbox over the lightweight option):
- **NEW `billing_outbox` table** (migration `0025`, `TenantScopedMixin`): `event_type` / `payload` (JSONB, neutral `record_*` args) / `idempotency_key` / `status` / `retry_count` / `next_retry_at` / `last_error` / `session_id`. `UNIQUE(tenant_id, idempotency_key)` + status/event_type CHECK + due/tenant indexes + RLS (two-policy + a system-sentinel USING escape so the cross-tenant drainer can claim). Dedicated table — NOT the unbuilt notification `outbox` design in 09.md (different shape).
- **`BillingOutboxService.enqueue`** (`platform_layer/billing/billing_outbox.py`): `pg_insert(...).on_conflict_do_nothing()` in the **request** transaction → the cost event commits atomically with session/audit (no swallow → no 漏扣); a redelivered event is a no-op (idempotent enqueue).
- **`BillingOutboxDrainer.drain_once`**: per-row independent txn — claim one due row (`FOR UPDATE SKIP LOCKED` under the system sentinel) → `set_config('app.tenant_id', row.tenant_id)` → materialize via the EXISTING `CostLedgerService.record_*` (pricing single-source, C-11 unchanged) → mark `done` in the same commit (**exactly-once** → no 雙扣). On failure: rollback (no cost written) → fresh txn records retry/backoff/`last_error`; dead-letter (next_retry_at=NULL) after MAX_RETRY.
- **Lifespan poller** (`api/main.py`): env-gated (`BILLING_OUTBOX_DRAINER_ENABLED`), fail-open, clean shutdown cancel.
- **Router flip** (`api/v1/chat/router.py`): the 3 cost-write observers (loop / `_verification` / tool) now `billing_outbox.enqueue(...)`; removed the per-request `CostLedgerService` + `pricing_loader` dep (drainer prices). Logged best-effort kept (SSE safety); atomicity comes from the shared request txn.

PR: pending (branch `feature/sprint-57-84-billing-outbox`).

## Verification
- Unit (`test_billing_outbox_service.py`): enqueue + idempotent no-op + pure helpers (6).
- Integration (`test_billing_outbox_drain.py`, real Postgres + NullPool engine): drain → cost_ledger **parity**, idempotent-twice (exactly-once), reschedule+backoff, dead-letter, **2-tenant isolation** (5).
- Updated flipped-contract callers: `test_chat_cost_ledger.py` + `test_phase56_3_e2e.py` (chat → outbox enqueue; SLA/quota unchanged).
- Gates: `mypy src/` 0/335 · `run_all.py` 10/10 (`check_rls_policies` + `check_llm_sdk_leak`) · full pytest **2161 passed**.
- real-Azure smoke: see retrospective (chat → enqueue → drain → cost_ledger on real Azure).

## Impact
Backend-only (+ migration `0025`). Behavioral change to a real-LLM-live billing path: chat now enqueues durable billing events; a background poller materializes `cost_ledger`. Env rollback: re-enabling the direct write is a 1-commit revert; the drainer can be disabled via `BILLING_OUTBOX_DRAINER_ENABLED=false`. LLM neutrality preserved (neutral payload; drainer uses existing CostLedgerService). Stripe (external billing) consumer is a future worker-only change — the backbone is now in place.

## Regression caught + fixed (in-sprint, pre-merge)
`_wire_billing_outbox()` leaked the module singleton (lifespan sets it; shutdown doesn't unset) → `test_main_lifespan` leaked it → a downstream chat-path test enqueued on the global engine without dispose → an innocent later `db_session` test hit `Event loop is closed`. Fixed with an autouse `_reset_billing_outbox_singleton` conftest fixture (Risk Class C / testing.md §Module-level Singleton Reset) + a dedicated NullPool engine for the drain test. Verified pre-sprint main was clean (2150 passed) → introduced + fixed within the sprint.
