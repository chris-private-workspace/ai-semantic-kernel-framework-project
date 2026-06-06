# Sprint 57.84 Retrospective — C-15 billing leg: transactional billing Outbox

**Sprint**: 57.84
**Closed**: 2026-06-06
**Branch**: `feature/sprint-57-84-billing-outbox`
**Closes**: C-15 **billing-write-atomicity leg** / `AD-Cost-Ledger-Outbox-Atomicity`. IaC / DR / Analytics sub-items external-blocked → deferred.

---

## Q1. Goal achieved?

✅ Yes. Chat billing is now durable + idempotent via a transactional `billing_outbox`:
- NEW `billing_outbox` table (migration `0025`, RLS + system-sentinel drainer escape) + `BillingOutboxService.enqueue` (atomic, ON CONFLICT idempotent) + `BillingOutboxDrainer.drain_once` (per-row txn, exactly-once materialize via existing CostLedgerService, retry/backoff/dead-letter) + lifespan poller.
- Router **flipped** from best-effort direct `cost_ledger` write → durable `billing_outbox.enqueue` (the 漏扣 vector is gone; the outbox idempotency key prevents future 雙扣).
- Gates: mypy 0/335 · run_all 10/10 · full pytest **2161 passed**. real-Azure smoke: see Q7.

## Q2. Estimate accuracy

- Plan: bottom-up ~10.5 hr → class-calibrated commit ~8.4 hr (`medium-backend` 0.80, `agent_factor` 1.0 parent-direct).
- Actual: ~9-10 hr. Day-0 + schema (Day 1) ~2 hr; service + drainer + tests (Day 2) ~3 hr; **router flip + poller + the regression hunt (Day 3) ~4-5 hr** (the singleton-leak pollution debugging was ~1.5-2 hr of that); closeout ~1 hr.
- Ratio actual/committed ~1.1-1.2 — band upper edge. **The over-run was entirely the Day-3 test-isolation regression** (a self-inflicted singleton leak whose failure surfaced on innocent tests, requiring bisection). Pure-code estimate held; the debugging tail did not. `medium-backend` 0.80 roughly held given the larger-than-usual scope. Clean parent-direct data point.

## Q3. What went well

- **Day-0 三-prong caught the real shape early**: the 09.md `outbox` being notification-shaped (D1) + no worker runtime (D2) + the RLS cross-tenant wrinkle (D3) were all surfaced before code. The lint-leniency discovery (check_rls_policies only needs ENABLE+CREATE POLICY, not the USING body) let me fold the D3 RLS escape into the Day-1 migration cleanly (no second migration).
- **Drainer correctness design held**: per-row independent txn (claim+materialize+mark-done atomic = exactly-once; rollback-then-record-failure avoids the poisoned-session trap of a single batch txn) was integration-proven against real Postgres BEFORE Day-3 wired it.
- **The pre-sprint-main baseline check was decisive**: running the full suite on `main` (2150 clean) proved I introduced the flakiness — that turned an "is this pre-existing?" rabbit hole into a definite "find my bug".
- **Bisection to a 2-second repro** (`unit/api` + incident) made the singleton-leak root cause tractable after the full-suite symptom looked like non-deterministic GC timing.

## Q4. Lessons

- **A new lifespan-wired module singleton needs a conftest reset fixture from the START.** `_wire_billing_outbox()` set the singleton; `test_main_lifespan` (TestClient) leaked it; a downstream chat-path test consumed it → enqueued on the global engine → an innocent later test hit "Event loop is closed". The pricing/rate-limit/error-budget singletons leak the same way but were benign (no consumer binds the global engine); billing_outbox's consumer does. **Action codified**: when adding a `set_*` singleton wired in the lifespan, add the autouse reset in the same sprint (Risk Class C / testing.md §Module-level Singleton Reset).
- **`-p no:unraisableexception` is the fast way to tell a GC-warning-elevated-to-failure from a real failure.** Here it stayed failing → real pollution, not a cosmetic GC warning. Saved chasing the wrong (asyncpg GC) theory.
- **asyncpg + SET utility statement rejects bind params** → use `SELECT set_config(name, value, is_local)` (the function form). Mirror `middleware/tenant_context.py`.
- **Direct `get_session_factory()` use in tests (outside the db_session fixture) needs a dedicated NullPool engine** to avoid pooled connections lingering across per-test event loops.

## Q5. Improvements next sprint

- For any sprint that wires a new singleton in `api/main.py:_lifespan`, add the conftest reset fixture as a Day-1 checklist item (not discovered as a Day-3 regression). Consider a lint/grep that flags a `set_*` singleton without a matching conftest reset.

## Q6. Carryover (→ next-phase-candidates.md)

- **C-15 IaC deploy pipeline** — external-blocked (Azure provision + GitHub Secrets). Deferred.
- **C-15 DR automation / multi-region / WAL** — external-blocked (Azure infra decisions). Deferred.
- **C-15 Analytics / data warehouse / CDC / dbt** — fully external infra. Deferred.
- **Stripe (external billing) consumer** — the outbox backbone is built for it; this sprint's drainer materializes `cost_ledger` only. Future worker-only change.
- **Enqueue-itself failure** — kept logged best-effort (SSE safety); a rare enqueue failure that doesn't poison the txn is swallowed (the major 漏扣 vector — heavy pricing+flush after session commit — is eliminated). Revisit if metrics show enqueue failures.
- (B-8 carryovers unrelated: per-verifier cost attribution, multi-judge registry.)

## Q7. Risks

- **Medium** (touched a real-LLM-live billing path). Mitigations: producer + drainer + 2-tenant isolation all tested; the flip is env-revertible (`BILLING_OUTBOX_DRAINER_ENABLED=false` + 1-commit revert of the direct write); not merged until gates green. **real-Azure smoke**: ✅ PASSED (user-authorized, gpt-5.2). A `real_llm` chat (session f5f60c3a) enqueued 1 `llm_call` outbox row → the background drainer marked it `done` (retry=0) and materialized 2 `cost_ledger` rows (`azure_openai_gpt-5.2-2025-12-11` input qty=1997 + output qty=41) with **unit_cost > 0** (C-11 date-suffix pricing normalize applied via the drainer's single-source CostLedgerService). VERDICT: outbox_all_done + 2 cost rows + nonzero cost — the chat→enqueue→drain→cost_ledger chain works end-to-end on the live path (clean backend restart per Risk Class E; backend stopped + temp scripts removed after). The full chain is also covered by the producer tests (chat→outbox) + drainer tests (outbox→cost_ledger parity + isolation).
- Residual: the in-sprint singleton-leak regression is fixed + verified (2161 passed); the conftest reset is autouse so it can't regress silently.

---

## Design Note Extract

NO — this is a feature-continuation sprint within the billing key-chain (extends the existing cost_ledger / pricing single-source with a durable-event backbone). New transactional-outbox pattern, but no new domain spike + no new cross-CATEGORY contract (17.md scope = 11+1 categories; billing is platform_layer, not registered there). The pattern + contract live in CHANGE-051 + the module docstrings + the plan.
