# Sprint 57.81 Retrospective — B-7 ErrorBudget Redis wiring

**Sprint**: 57.81
**Closed**: 2026-06-05
**Branch**: `feature/sprint-57-81-errorbudget-redis`
**Closes**: B-7 / `AD-ErrorBudget-Redis-Wiring`

---

## Q1. Goal achieved?

✅ Yes. The already-built `RedisBudgetStore` is now wired so the per-tenant error budget accumulates across requests (and instances):
- NEW `platform_layer/governance/error_budget_provider.py` singleton + `_wire_error_budget()` startup wiring (fail-open) + `RedisBudgetStore` export + chat factory swap (`maybe_get_budget_store() or InMemoryBudgetStore()`).
- Fixes BOTH the per-request reset (shared store) AND cross-instance correctness; AP-2 side-track repaid.
- Verified: fakeredis accumulation test (2 factory calls → count=2) + startup-log `error budget store wired`.
- Gates: mypy src/ 0 (332) / pytest 2137 (+7) / run_all 10/10.

## Q2. Estimate accuracy

- Plan: bottom-up ~4.3 hr → class-calibrated commit ~3.4 hr (`medium-backend` 0.80, `agent_factor` 1.0 parent-direct).
- Actual: ~3 hr. The wiring itself was small/fast (~1 hr: provider + wire fn + export + factory swap). Tests ~1 hr. Day-0 re-verify of the 18-sprint-old analysis doc + startup-log + closeout ~1 hr.
- Ratio ~0.88. `medium-backend` 0.80 held for a parent-direct wiring sprint. **NOT agent-delegated** → the 16-consecutive-agent-delegated wall-clock caveat does not apply.

## Q3. What went well

- **Day-0 re-verify caught a real drift**: the analysis doc assumed `RedisBudgetStore` was usable directly; the grep found it was **not exported** from `error_handling/__init__.py` (D1) → plan added the export. The doc's own §5 lesson ("18-sprint-old line numbers; grep-confirm, don't single-shot") paid off — all 7 D-DAY0 facts re-confirmed at new line numbers.
- **Live-consumer check beyond the doc**: verified `loop.py:320-322` actually calls `error_budget.record()` (the analysis doc said "loop.py not line-verified"). Confirmed the wiring connects to a real consumer (not a Potemkin), so the store swap changes real runtime behaviour.
- **Right verification tool for the gap**: the budget only increments on tool ERRORS, so a real-Azure happy-path chat would prove nothing. The fakeredis accumulation test (two factory calls → count=2) is the deterministic proof that the per-request reset is fixed; the startup-log check confirms the wiring fires. Chose this over a 57.79/57.80-style real-Azure leg — and documented why so it doesn't read as a coverage gap.
- **Scope discipline**: kept it Tier 1 wiring — did NOT copy the rate-limit counter's DB `session_factory` / RLS `app.tenant_id` (RedisBudgetStore is pure Redis; budget tenant isolation is already in the key), and did NOT pull in `error_budgets.yaml` per-tenant overrides.
- **Applied the 57.80 lesson**: ran the FULL format chain (black/isort/flake8 + mypy + pytest) before commit, not just mypy/pytest — no CI black surprise this time.

## Q4. Lessons

- **A stale analysis doc is a starting point, not ground truth**: an 18-sprint-old doc had drifted (RedisBudgetStore export gap) + omitted the live-consumer check. Re-running Prong 1 + 2 against current main is mandatory; the doc accelerates Day-0 but does not replace it.
- **Match the verification to where the code path actually runs**: error-only counters can't be exercised by a happy-path real-LLM call. Picking the deterministic fakeredis accumulation test (the real correctness claim) over an expensive-but-uninformative real-Azure run was the right call.

## Q5. Improvements next sprint

- When wiring an already-built component, add a one-line Day-0 check that the component is actually EXPORTED on the public path the wiring will import from — the export gap (D1) was a 30-second find that would have been a Day-1 import error otherwise.

## Q6. Carryover

- None blocking — B-7 closed.
- **error_budgets.yaml per-tenant overrides** — the `budget.py` docstring mentions YAML-tunable caps; the factory uses defaults (1000/day, 20000/month). Loading per-tenant overrides is a separate feature, not wiring. Carryover.
- **B-8 Verification default-enable** / **C-15 DevOps/data-platform billing** — the bundle's other legs; separate sprints.
- **Real-LLM budget-enforcement e2e** (provoke real tool errors to trip the budget on real Azure) — deferred; fakeredis accumulation is the proof here.

## Q7. Risks

- Low. Backend-only wiring, fail-open (Redis down → InMemory fallback → never blocks startup), no schema / migration / loop.py / budget.py / store-logic change. The new `platform_layer/governance → agent_harness` import is TYPE_CHECKING-only + an established allowed direction (check_cross_category_import green). The correctness claim is unit-proven (accumulation); the startup-log confirms the wiring fires. Pure Redis (no DB write-through) so no RLS / tenant-context risk.

---

## Design Note Extract

NO — wiring of an existing Cat 8 component (RedisBudgetStore, Sprint 53.2); no new contract / no 17.md change / no new domain.
