# Sprint 57.60 — Retrospective

**Sprint**: 57.60 — RateLimits MetaData Cleanup (close `AD-RateLimits-MetaData-Cleanup-Phase58`)
**Closed**: 2026-05-29
**Class**: `medium-backend` 0.80 / agent-delegated yes (single agent `rl-metadata-cleanup`, 26th consecutive code-implementer) / agent-factor `mechanical-pattern-reuse-heavy` 0.30
**Commits**: Day 0 `621afe72` · Day 1 `416c9f84` · Day 2 (closeout) pending

---

## Q1 — What went well

- **Day 0 三-Prong caught a plan gap (D-DAY0-G drift)**: plan §4.4 named only 2 test-conversion files; the Prong 2 grep `meta_data.*rate_limits backend/tests/` surfaced a 3rd (`test_admin_tenant_rate_limits.py`, 57.48-era — asserts GET honours meta_data + PUT writes it). Caught at Day 0, folded into plan §5 + §8 R2, converted cleanly on Day 1 — no silent test break.
- **D-DAY0-E CRITICAL safety invariant confirmed GREEN before any code**: read `0019.upgrade()` and verified the data-migration `SELECT ... WHERE "metadata" ? 'rate_limits'` is unconditional (no flag-gate / no skip except unparseable items that have no enforceable representation anyway). This proved the fallback removal loses no enforceable config — the single most important precondition, verified at Day 0 not discovered mid-Day-1.
- **Surgical removal, 0 regressions**: 5 transitional sites removed + orphan cleanup (bindings/imports/`db.refresh`/`db.flush`) by a single agent in ~15 min wall-clock; pytest 1840 → 1848 (+8), mypy `src/` 0/317, 9/9 V2 lints, black/isort/flake8 clean.
- **Physical-column discipline carried forward correctly**: `0020` raw SQL uses the physical `"metadata"` column (not ORM attr `meta_data`) — the exact `AD-Day0-Prong3-Physical-Column-Read` lesson from 57.59 D-DAY1-1, applied pre-emptively at plan-time (§4.3) and codified Day 2.
- **Live DB round-trip** (`0019→0020→0019→0020`) verified the cleanup + reverse-populate downgrade both work under the real psycopg/Alembic + asyncpg drivers.

## Q2 — What didn't go well

- **Plan §4.4 under-enumerated test targets** (2 of 3 files). The Prong 2 grep caught it, but the plan-time list was a subset of reality — a recurring pattern (plan names files from memory; grep finds the rest). Mitigated by the mandatory Prong 2 test-seed grep, but worth internalising: **never trust the plan's test-file list; always grep the removed field across `tests/`.**
- **`::jsonb` cast / asyncpg named-param collision** was an unforced surprise the agent had to debug mid-Day-1 (the `:items::jsonb` form parsed `::jsonb` as a named param under asyncpg). Not anticipated in the plan. Resolved with `CAST(:items AS jsonb)` (equivalent SQL, parses under both drivers) — now documented in the migration + below (Q3).

## Q3 — What we learned (generalizable)

1. **asyncpg named-param × `::type` cast collision** → in raw SQL run through the async test path, prefer `CAST(x AS type)` over the `x::type` shorthand when the statement also carries `:named` params. The `::` is ambiguous with asyncpg's param syntax. Reusable for any future raw-SQL migration with named binds.
2. **Removal-sprint Prong 2 rule**: when removing a stored field / fallback, grep the field name across the WHOLE `tests/` tree for seed-and-assert sites — the plan's enumerated test list is always a subset. (D-DAY0-G evidence: plan named 2, reality had 3 + 1 NEW assertion need.)
3. **`mechanical-pattern-reuse-heavy` 0.30 fits removal-shape work** (see Q4) — but with wide shape-variance vs the migration-wave shape that first generated the sub-class.

## Q4 — Calibration

**Bottom-up ~7.25 hr → class-calibrated ~5.6 hr (`medium-backend` 0.80) → agent-adjusted ~1.7 hr (`agent_factor` 0.30 `mechanical-pattern-reuse-heavy`).**

Actual ≈ **1.85 hr** (Day 0 plan+checklist+三-Prong 14 checks+drift catalog+branch+commit ~45 min + Day 1 agent wall-clock ~15 min + parent supervisory/validation/review ~15 min + Day 2 closeout ~30 min).

- **ratio actual/agent-adjusted ≈ 1.85 / 1.7 ≈ 1.09 ✅ IN BAND [0.85, 1.20]** (top-middle)
- ratio actual/class-committed ≈ 1.85 / 5.6 ≈ **0.33** (BELOW band — confound: agent speedup; resolved at the agent_factor sub-class layer per discipline → **KEEP `medium-backend` 0.80**)
- ratio actual/bottom-up ≈ 1.85 / 7.25 ≈ 0.26 (bottom-up ~3.9× generous — consistent with mechanical agent work)

**`medium-backend` 0.80 — 11th data point**: actual/class-committed ~0.33; last-3 (57.56≈0.66 + 57.57≈0.72 + 57.60≈0.33) — 1/3 < 0.7 lower-trigger NOT met; confound resolved at sub-class layer → **KEEP 0.80** per `When to adjust` 3-sprint window rule.

**`mechanical-pattern-reuse-heavy` 0.30 — 1st DELIBERATE FORWARD application** (Sprint 57.49 was the retroactive origin at ratio 0.21): ratio actual/agent-adjusted ≈ **1.09 IN BAND** → **KEEP 0.30**, single forward-data-point caution. Shape-variance note: 57.49 (frontend 5-tab+1-drawer migration wave, ~24 mechanical repetitions, ratio 0.21 → wanted ~0.20) vs 57.60 (backend 5-site removal + 1 migration + test conversions, fewer repetitions + more design, ratio 1.09 → 0.30 fits). The sub-class spans a wide shape range; the forward application landing IN band is the cleanest signal so far that 0.30 is well-calibrated for moderate-repetition mechanical work. If a future high-repetition (≥ 20×) agent sprint at 0.30 lands < 0.7 again, consider a tier refinement (`-high-repetition` ~0.20 vs `-moderate` 0.30) — defer until 2+ such data points.

**Counterfactual check**: had this been classified `mechanical-greenfield-port-style` 0.45 → agent-adjusted 2.52 hr → ratio 1.85/2.52 ≈ 0.73 (just below band lower edge). So `mechanical-pattern-reuse-heavy` 0.30 was the better fit (R7 risk resolved favourably).

## Q5 — Next steps (rolling — carryover candidates only, no specific future-sprint tasks)

- `AD-RateLimits-SyntaxValidation-Phase58` — now easier post-split (config table has typed `quota`/`window_type` columns); PUT-time validation; ~2-3 hr
- `AD-RateLimits-Alerting-Phase58` — SSE 80% threshold; pairs with usage table; ~3-4 hr (SSE infra ~80% from prior sprints)
- `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.61` — DEFERS (57.60 was single-domain, not multi-track bundle); 1st validation of tightened-0.45 awaits next genuine `mixed-multidomain-bundle` sprint
- `AD-AgentPrompt-CrossPlatform-Mypy-Warning` (57.59 lesson) — agent prompts touching Redis/asyncpg should flag Risk Class B + suggest dual-ignore (this sprint did NOT edit Redis/asyncpg stubs, so it didn't recur — but the candidate stands)
- **NEW `AD-Mypy-WholeDir-Conftest-Collision`** — pre-existing (since 57.53): `mypy --strict .` (whole-dir) duplicate-conftest collection error (two `tests/integration/{api,agent_harness}/conftest.py` lack `__init__.py`). NOT a CI concern (CI runs `mypy src/`). Phase 58+: add `__init__.py` to the 2 conftest dirs OR pin the mypy invocation scope.
- `AD-Day0-Prong3-Physical-Column-Read` + `AD-Day0-Prong2-Nested-Shape-Read` — **CODIFIED this sprint Day 2** (both hit 2 data points: 57.58/57.59 + 57.59/57.60); folded into `sprint-workflow.md §Step 2.5` Drift Class tables.

## Q6 — Phase 58.x RateLimits arc completeness (sprint-specific topic)

The RateLimits subsystem now has a **single source of truth** (`rate_limit_configs`) with **0 transitional fallback branches**. The Phase 58.x RateLimits arc is config-complete across 3 sprints:

- **57.58** RuntimeEnforcement — middleware + Cat 2 tool gate + Redis sliding-window counter + Live usage Card (config still in `meta_data` JSONB)
- **57.59** Potemkin Migration — two-table split (`rate_limit_configs` config + activated dormant `rate_limits` usage table; AP-4 closed); meta_data retained as transitional fallback
- **57.60** MetaData Cleanup (this) — removed the transitional fallback + dual-write + stripped the stored JSONB; config single-source achieved

Remaining RateLimits deeper extensions (SyntaxValidation / Alerting) are feature additions, not architectural debt — the storage layer is clean.

## Q7 — Design Note Extract (spike sprint only) — **N/A SKIP**

Sprint 57.60 is a refactor/cleanup sprint (transitional-code removal + data migration), NOT a spike into a new domain. No design note required (consistent with the feature/refactor-ship precedent — 9th consecutive Q7 N/A SKIP across the RateLimits + Tenant-settings ship sprints).
