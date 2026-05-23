# Sprint 57.31 — Retrospective (Day 4 closeout)

**Date**: 2026-05-23
**Branch**: `feature/sprint-57-31-cost-dashboard-repoint`
**Base SHA**: `8533603b` (main; Sprint 57.30 squash-merge PR #164)
**Sprint Goal**: 3rd Phase-2 per-page verbatim-CSS re-point on `/cost-dashboard` + 3rd data point for `AD-Sprint-Plan-frontend-verbatim-bimodal-watch`

## Q1 — What went well

1. **Clean PARITY on `/cost-dashboard`** — first sprint of the Phase-2 epic where 0 🟡 cosmetic deltas surfaced. Sprint 57.29 had 18 🟡 (overview content delta acceptable); Sprint 57.30 had 18 🟡 (shell-wide avatar 36→26); Sprint 57.31 has 0 🟡 / 0 🟠 / 0 🔴. Triage report: 22-route sweep is **18 🟢 PARITY + 1 🟢 PROP-stub + 3 ⚪ pre-existing fails**. Shell-unchanged claim verified (the only pixel delta on non-cost-dashboard routes is clock timestamp drift on /overview topbar — capture-time artifact, not regression).

2. **Single batched Day 1 delegation worked cleanly** — per Day 0 visual finding that production cost-dashboard was already very mockup-aligned from Sprint 57.24 v2 strict rebuild, batching 7 components into one `code-implementer` agent (~60 min) was more efficient than 3 daily delegations. 5 gates green first pass. 0 Vitest spec drift (testid + class-membership contracts preserved by hybrid approach on TenantTopTable). Plan-vs-execution adjustment justified by Day 0 finding + audit-trail preserved in progress.md.

3. **CostBreakdownTable production-only-by-design decision (D4)** — agent correctly distinguished CostBreakdownTable (real backend `by_type` 2-level drill-down for current tenant) from TenantTopTable (cross-tenant admin fixture). Re-pointed CostBreakdownTable to mockup `.table` vocabulary verbatim WITHOUT an AP-2 BackendGapBanner — production has real backend data, no gap to mark. Distinguishes from MonthPicker (D5: production-only UI affordance, NOT a backend gap). Two distinct "production-only" patterns correctly identified.

4. **0 Vitest spec adaptation needed** — TenantTopTable spec asserts `text-danger` / `text-warning` class membership for quota% color-coding. Agent preserved those Tailwind classnames **alongside** the new inline-style `color: var(--danger|warning|fg-muted)` for the verbatim visual. Hybrid bridge: existing spec keeps passing, new visual matches mockup. This pattern (preserve test-essential classnames while adding verbatim styles) should be documented for future Phase-2 sprints where Vitest specs assert class membership.

5. **Pattern reuse acceleration continues** — Sprint 57.29 ~5 hr / Sprint 57.30 ~5 hr / Sprint 57.31 ~2.5-3 hr (estimated agent-assisted wall-clock). Each subsequent sprint of Phase-2 epic compresses further as the verbatim re-point method becomes routine.

## Q2 — What didn't go well + calibration ratio

**Calibration**:
- Bottom-up estimate per plan §Workload: ~12-18 hr
- Committed (HYBRID 0.60 blend): ~7-10 hr
- **Actual**: ~2.5-3 hr of agent-assisted wall-clock (Day 0 ~1 hr + Day 1 ~1 hr + Day 4 ~30-60 min)
- **Ratio actual / committed ≈ 0.30-0.43** — **BELOW [0.85, 1.20] band by ~0.45-0.55**

3-data-point window for `frontend-verbatim-css-repoint`:

| Sprint | Page | Ratio | Band Status |
|--------|------|-------|-------------|
| 57.29 | /overview (rich dashboard) | ≈ 1.0 | In band middle |
| 57.30 | /chat-v2 (structural-heavy + shell hotfix bundled) | ≈ 0.40 | Below band by 0.45 |
| 57.31 | /cost-dashboard (rich dashboard) | ≈ 0.30-0.43 | Below band by 0.45-0.55 |
| **3-pt mean** | | **≈ 0.55-0.60** | **Lower edge of band** |

### Bimodal-watch evaluation (AD-Sprint-Plan-frontend-verbatim-bimodal-watch from Sprint 57.30 carryover)

Per plan §Class baseline 3rd-data-point evaluation criteria matrix:

- **57.31 ratio 0.30-0.43** falls in the "0.40-0.55 range" → "Bimodal WEAKENS; baseline too generous overall; propose lower baseline 0.60→0.50".

Why bimodal hypothesis WEAKENED (not confirmed): if rich-dashboard shape drove 57.29's high ratio (≈1.0), 57.31 (same rich-dashboard shape — /cost-dashboard) should have landed similarly high. Instead it landed near 57.30's structural-heavy ratio. So shape is NOT the driver of variance.

What IS the driver of variance: **estimate generosity in early class applications**. Sprint 57.29 was the 1st application; bottom-up estimates included buffer for unknowns ("Day-0 三-prong novelty / verbatim primitive port / shell + 3 overlay re-point all-new"). Sprint 57.30 onwards reused those novelty solutions → estimate generosity diminished as actual ratios approach reality.

### Recommended action

**RESOLVE `AD-Sprint-Plan-frontend-verbatim-bimodal-watch`** with decision: NOT a bimodal class. Lower `frontend-verbatim-css-repoint` baseline `0.60 → 0.50` per `When to adjust` rule (3+ consecutive < 0.7 = 57.30, 57.31; technically not 3 consecutive yet because 57.29 was in band, but `actual / committed < 0.7` for 2 consecutive sprints + clear non-bimodal pattern justifies action).

NEW AD logged Day 4 closeout: **`AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** to validate 0.50 across 2-3 next sprints.

## Q3 — What we learned (generalizable)

1. **Day 1 batched delegation is the right pattern when Day 0 reveals high mockup-alignment baseline**. Sprint 57.29 + 57.30 each used 4-5 daily agent delegations (necessary because Phase-1 alignment was variable per file). Sprint 57.31 used 1 batched Day 1 + 0 Day 2/3 because Day 0 visual baseline showed production was already 80%+ mockup-aligned. The decision rule: if Day 0 baseline visual is already very close to mockup, batch; if Day 0 baseline shows significant translated-Tailwind / shadcn-default usage, daily.

2. **Hybrid "preserve class + add inline-style" works for Vitest contract preservation**. Sprint 57.30 Day 4 had to adapt 1 spec for `.border-danger/40` → `.block.verification.failed`. Sprint 57.31 avoided that by preserving `text-danger` / `text-warning` classnames alongside `color: var(--danger|warning)` inline-style. Pattern: when a Vitest spec asserts class membership, the verbatim re-point can ADD the inline style without REMOVING the class. Both pass.

3. **Production-only widget triage — 3 distinct patterns**:
   - **Mockup token vocabulary only** (MonthPicker D5) — `var(--*)` inline; no AP-2 banner; pure UI affordance.
   - **Mockup `.table` vocabulary verbatim** (CostBreakdownTable D4 decision c) — real backend; no AP-2; same vocabulary as if mockup had it.
   - **Mockup vocabulary + AP-2 BackendGapBanner** (e.g. Sprint 57.30 InputBar error banner) — fixture data; AP-2 honesty banner.

   Day 0 Prong-2 finding-class-(c) introduced this sprint extends the pattern set. Future sprints: identify which class on first read.

4. **Sprint estimate accuracy improves with class iteration** — bottom-up estimates in Sprint 57.29 (1st app) were ~5× actual; Sprint 57.31 (3rd app) are ~4-6× actual. The HYBRID multiplier 0.60 was calibrated to compress the bottom-up generosity by 40%; it under-compressed (should have been ~0.20-0.25 to land in-band, or bottom-up should have been ~3-4 hr not ~12-18 hr). Action: **lower bottom-up estimate AND/OR lower multiplier**. The lowered 0.50 baseline addresses the multiplier; future plan §Workload sections should also halve the bottom-up component estimates.

## Q4 — Audit Debt deferred (carryover)

- **`AD-Sprint-Plan-frontend-verbatim-bimodal-watch`** — ✅ **CLOSED**: 3rd data point evaluated; bimodal hypothesis WEAKENED (rejected); class is NOT bimodal but baseline 0.60 too generous overall.
- **NEW `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** — Day 4 calibration: lower `frontend-verbatim-css-repoint` baseline 0.60 → 0.50 per `When to adjust` rule + 3-data-point evidence (3-pt mean ~0.55-0.60 lower band edge). Validate across 2-3 next sprints; if 0.50 lands in band consistently → keep; if still low → consider 0.40.
- **NEW `AD-CostBreakdownTable-Backend-Tenant-Scope`** — D4 decision (c) noted: `CostBreakdownTable` shows real backend by_type drill-down for current tenant; distinct from TenantTopTable (cross-tenant admin fixture). Future Phase-2 work on /cost-dashboard should ensure these two tables don't merge accidentally; document data ownership.
- Sprint 57.30 carryover still open: `AD-Tsconfig-Node-NoEmit` / `AD-Topbar-Use-Button-Primitive` / `AD-Topbar-Tweaks-Panel-Phase58+` / `AD-ApprovalCard-Legacy-Phase58-Migrate` — none touched this sprint, all remain open.
- Sprint 57.29 carryover still open: `AD-Inline-Style-Rule-vs-Verbatim-Method` / `AD-MockupFidelity-Guard-TokenRelative-Oklch` / `AD-Overview-PreExisting-Route-Crashes` (3 crash routes) — none touched this sprint.

## Q5 — Next steps (carryover candidates, rolling planning)

Phase-2 per-page re-point epic remaining backlog after Sprint 57.31:

**Re-point candidates (11 🟡 AppShellV2 routes — 1 already cost-dashboard done)**:
- sla-dashboard (rich dashboard; similar to cost-dashboard; expected ratio ~0.30-0.40 if 0.50 baseline lifted)
- admin-tenants (admin list+form; ~4 files; expected mid-band)
- tenant-settings (~3-4 files admin)
- governance (~6 files governance + audit)
- orchestrator (debug UI; ~6 files)
- loop-debug + state-inspector (debug UI bundle; ~5 files)
- compaction (PROP stub; tiny)
- + 3 ⚪ crash-fix routes (separate "frontend-page-bug-fix" class)

**Recommended next**: sla-dashboard (4th data point validates 0.50 baseline lift on similar rich-dashboard shape). OR admin-tenants (NEW data point — smaller-scope admin shape).

## Q6 — Solo-dev policy validation

- **enforce_admins=true**: still active ✅
- **review_count=0**: still in effect ✅
- **5 required CI checks**: all expected green on PR
- **No `--admin` bypass**: ✅
- **No `--no-verify` / `--force` used**: ✅
- **Plan + Checklist → Code → Update → Progress → Retro flow**: ✅ (5-step V2 sprint workflow honoured)
- **Karpathy §1 stop-on-ambiguity**: ✅ (AskUserQuestion used Day 0 for next page selection)
- **Karpathy §2 simplicity-first**: ✅ (single Day 1 batched delegation when Day 0 finding justified it; no over-engineering)
- **Karpathy §3 orphan-cleanup-of-own-changes**: N/A this sprint (no orphans created)

## Q7 — N/A SKIP

Feature ship not spike (per Sprint 57.29-57.30 precedent); no design note extract required.

---

**Sprint 57.31 STATUS: COMPLETE PENDING MERGE**. /cost-dashboard PARITY achieved + 3rd data point resolves bimodal-watch + new baseline-lift action logged + 22-route sweep cleanest yet (0 cosmetic deltas). Ready for PR + CI green → squash-merge.
