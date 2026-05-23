# Sprint 57.33 — AD-Page-Bug-Fix-Sweep

**File**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-33-plan.md`
**Purpose**: Plan for Sprint 57.33 — fix the pre-existing `Cannot read properties of undefined (reading 'length')` error boundary on three `/subagents`, `/memory`, `/verification` routes flagged by Sprint 57.29/30 Day-0 baseline (AD-Overview-PreExisting-Route-Crashes). NEW class `frontend-page-bug-fix` baseline 0.45 (1st application).
**Category**: Sprint planning / Phase 57+ Frontend SaaS — bug-fix sweep
**Scope**: Phase 57+ Frontend SaaS — frontend page bug fix (not a Phase-2 re-point)
**Created**: 2026-05-24
**Last Modified**: 2026-05-24
**Status**: Draft → awaiting user approval

> **Modification History**
> - 2026-05-24: Initial draft (Sprint 57.33 Day 0) — page-bug-fix sweep on 3 ⚪ pre-existing crash routes per Sprint 57.30 carryover + Sprint 57.32 retro candidates list

---

## Sprint Goal

Land a **page-bug-fix sweep** on the three routes that have been flagged as 3 ⚪ pre-existing crashes in Sprint 57.29 + 57.30 22-route Day-0 baselines (and confirmed unchanged in Sprint 57.31 + 57.32 sweeps): `/subagents`, `/memory`, `/verification`. All three render an error boundary (`Cannot read properties of undefined (reading 'length')`) on first navigation because frontend components access `query.data.items.length` (or `entries.length`) on a TanStack Query payload whose `items`/`entries` field is `undefined` when the backend returns `{total: 0}` without the array field. Fix is a uniform defensive `?? []` guard across ~10 sites in 5 component files. This **unlocks future Phase-2 verbatim re-point** on these 3 routes (currently locked out — Sprint 57.22 audit flagged `/memory` for STRUCTURAL rebuild Phase 58+; the other two are crash-fix-then-re-point candidates).

**NEW class `frontend-page-bug-fix` 0.45 baseline (1st application)** — single-domain mechanical defensive-guard fixes; HYBRID blend resolves to ~0.50 mid-band. This sprint is the first data point for the class.

---

## Background

### Why Sprint 57.33 (this sprint)

Sprint 57.29 (`/overview` Phase-2 re-point) Day-0 baseline captured 3 ⚪ routes rendering an error boundary in the 22-route sweep:

```
⚪ /subagents — Cannot read properties of undefined (reading 'length')
⚪ /memory — Cannot read properties of undefined (reading 'length')
⚪ /verification — Cannot read properties of undefined (reading 'length')
```

Sprint 57.30 + 57.31 + 57.32 all re-confirmed the 3 ⚪ as **pre-existing, NOT regression** (sweep `after` matched sweep `before` on every sprint). The carryover `AD-Overview-PreExisting-Route-Crashes` was logged in `next-phase-candidates.md` as a "Separate FIX sprint candidate (Sprint 57.31+ `frontend-page-bug-fix` class at ~0.45 mid-band)".

Sprint 57.33 cashes that AD. Reasons to pick it now:

1. **Unblocks future Phase-2 re-point** — these 3 routes cannot be Phase-2 re-pointed (per the verbatim-css-repoint epic) while they crash, because the route-sweep can't take a meaningful `after` screenshot of a route stuck on an error boundary. Fixing the crash is prerequisite for any future visual re-point.

2. **User-visible quality issue** — operator clicks `/subagents` from sidebar → red error screen. This is the most visible UX defect on the platform right now.

3. **Trivial scope** — Day-0 quick grep already pinpointed 10 offending sites across 5 files, all of the same shape (`query.data.items.length` where `items` may be undefined). The fix is a uniform `?? []` guard — no design decisions, no backend changes, no migrations.

4. **NEW calibration class baseline** — `frontend-page-bug-fix` 0.45 was proposed in `next-phase-candidates.md` but never applied. This sprint provides the 1st validation data point.

### Crash root cause (Day 0 Prong 2 pre-investigation complete)

Each crash site follows the same shape: a TanStack Query component renders the response payload's array length **gated by `query.isSuccess`** (which guarantees `query.data` exists), but **NOT gated on the array field itself**:

```tsx
{query.isSuccess && query.data.items.length === 0 && (...)}
{query.isSuccess && query.data.items.length > 0 && (...)}
```

When the backend returns `{total: 0, items: undefined}` (or omits `items` entirely — e.g. legacy seed data, empty-state responses, Phase 58+ stub responses), `query.data.items` is `undefined` and `.length` crashes the component tree, bubbling up to the AppShellV2 error boundary.

The bug exists **regardless of whether the backend actually returns undefined** — the page is brittle to any payload shape variation. The fix makes the page defensive.

### Offending sites (Day 0 Prong 2 pre-investigation results)

| # | Route | File | Line | Offending expression |
|---|-------|------|------|---------------------|
| 1 | `/subagents` | `pages/subagents/SubagentsPage.tsx` | 262 | `data?.items.length ?? 0` (the `?.` chains data but not items; if `data` is defined but `items` undefined, crash) |
| 2 | `/memory` | `features/memory/components/MemoryRecentList.tsx` | 120 | `query.data.items.length === 0` |
| 3 | `/memory` | `features/memory/components/MemoryRecentList.tsx` | 126 | `query.data.items.length > 0` |
| 4 | `/memory` | `features/memory/components/MemoryRecentList.tsx` | 171 | `offset + query.data.items.length` |
| 5 | `/memory` | `features/memory/components/MemoryByScopeBrowser.tsx` | 166 | `query.data.items.length === 0` |
| 6 | `/memory` | `features/memory/components/MemoryByScopeBrowser.tsx` | 172 | `query.data.items.length > 0` |
| 7 | `/verification` | `features/verification/components/VerificationList.tsx` | 186 | `query.data.items.length === 0` |
| 8 | `/verification` | `features/verification/components/VerificationList.tsx` | 200 | `query.data.items.length > 0` |
| 9 | `/verification` | `features/verification/components/VerificationList.tsx` | 257 | `offset + query.data.items.length` |
| 10 | `/verification` | `features/verification/components/CorrectionTraceView.tsx` | 104 | `query.data.entries.length` |

**10 sites / 5 files / 3 routes** — all the same defensive-guard shape.

### Universal fix pattern

```tsx
// BEFORE — brittle
{query.isSuccess && query.data.items.length === 0 && (...)}

// AFTER — defensive
{query.isSuccess && (query.data.items ?? []).length === 0 && (...)}
```

For the offset-based render expression (`offset + query.data.items.length`):

```tsx
// AFTER — defensive
{offset + (query.data.items ?? []).length}
```

For the SubagentsPage:262 chain:

```tsx
// AFTER — defensive
const realItemsCount = data?.items?.length ?? 0;  // add ?. on items
```

Aligned with existing Vitest specs (no API surface change, no prop change, no test rewrites needed).

### Scope boundaries

**IN scope**:
- 5 component files × 10 offending `.length` sites — uniform `?? []` (or `?.`) defensive guard.
- 1 Vitest regression test per route confirming the empty-`items` payload no longer crashes (3 new specs in existing test files; Karpathy §2 inline near the component being tested).
- 22-route sweep before/after to confirm: (a) the 3 ⚪ routes flip to ✅ PARITY in the `after` baseline, (b) no other route regresses.

**OUT of scope**:
- Phase 58+ STRUCTURAL rebuild of `/memory` (per Sprint 57.22 audit Unit 10 — full 5-scope × 3-time-scale matrix + scrubber + memory-ops timeline; **defer to Phase 58+** dedicated sprint per Sprint 57.24 Q2 decision).
- Phase-2 verbatim CSS re-point of these 3 routes (separate `frontend-verbatim-css-repoint` sprint candidates, post-this-fix).
- Backend payload shape contract — the backend MAY legitimately return `{total: 0}` without `items`; frontend must tolerate that. We do NOT change the backend.
- Any other route's `.length` audit (e.g. /loop-debug, /state-inspector) — out of scope unless 22-route sweep `after` flags a new regression caused by this fix.

### Class baseline — `frontend-page-bug-fix` 0.45 (1st application)

NEW class per `next-phase-candidates.md` AD-Overview-PreExisting-Route-Crashes recommendation. HYBRID weighted blend for Sprint 57.33:

| Component | Class | Multiplier | Weight |
|-----------|-------|------------|--------|
| Day-0 三-prong + before-baseline | `audit-cycle` | 0.85 | ~15% |
| 10 mechanical defensive-guard fixes (5 files × ~2 sites each) | `frontend-refactor-mechanical` | 0.45 | ~50% |
| 3 new Vitest defensive specs (1 per route) | `medium-frontend` | 0.65 | ~20% |
| 22-route sweep after + REPOINT-REPORT + Vitest expand | `frontend-verbatim-css-repoint` | 0.50 | ~10% |
| Closeout + retro + docs | `closeout` | 0.80 | ~5% |
| **HYBRID blended baseline** | | **≈ 0.52** | |

Per `next-phase-candidates.md` proposal, anchor at **0.45 mid-band** (rounded slightly below HYBRID since this is a NEW class and the conservative anchor matches the mechanical-refactor majority weight). Per `When to adjust` 3-sprint window rule, KEEP 0.45 this sprint; evaluate at Day 4.

Bottom-up estimate: 5 hr (Day 0 ~1.5 hr + Day 1 ~0.5 hr + Day 2 ~1 hr + Day 3 ~1 hr + Day 4 ~1 hr).
Calibrated commit: ~2.25 hr (0.45 multiplier).

### What is preserved (NOT changed)

- All TanStack hook signatures, all prop types, all backend service modules.
- All `data-testid` attributes.
- All component-logic layer (event handlers, derived state, conditional render logic).
- All Sprint 57.x existing Vitest specs (no rewrites; only 3 new specs added).
- `routes.config.ts` entries for /subagents, /memory, /verification.
- `styles-mockup.css` (no CSS file touched — pure JSX defensive-guard fix).
- All prior Phase-1 / Phase-2 fidelity work on routes not in this scope.

### What gets changed (this sprint scope)

**Day 1 — `/subagents` fix** (1 file):
- `pages/subagents/SubagentsPage.tsx:262` — `data?.items.length ?? 0` → `data?.items?.length ?? 0`.
- Add 1 Vitest spec confirming empty-items payload renders without crash.

**Day 2 — `/memory` fix** (2 files):
- `features/memory/components/MemoryRecentList.tsx:120,126,171` — `query.data.items.length` → `(query.data.items ?? []).length`.
- `features/memory/components/MemoryByScopeBrowser.tsx:166,172` — same pattern.
- Add 1 Vitest spec.

**Day 3 — `/verification` fix** (2 files):
- `features/verification/components/VerificationList.tsx:186,200,257` — same pattern.
- `features/verification/components/CorrectionTraceView.tsx:104` — `query.data.entries.length` → `(query.data.entries ?? []).length`.
- Add 1 Vitest spec.

**Day 4 — Regression sweep + fidelity verify + closeout**.

---

## User Stories

### Group A — Day 0 plan + 三-prong + before-baseline (PRE-WORK)

- **US-A1** (Plan + Checklist): As the AI, I draft Sprint 57.33 plan + checklist mirroring Sprint 57.32 format before any code runs. Acceptance: this file + `sprint-57-33-checklist.md` exist with full content.
- **US-A2** (Day-0 三-prong): As the AI, I run path-verify + content-verify on the 10 offending sites listed in §Offending sites; verify each line + expression still matches the live file before fix; verify no schema involvement (Prong 3 N/A — frontend only); catalog any drift in progress.md Day 0 entry.
- **US-A3** (Before-baseline screenshots): Playwright capture 22 AppShellV2 routes via `route-sweep.mjs before` (OUT_DIR re-point to sprint-57-33-* dir) before any code change. Confirm the 3 ⚪ routes still crash as documented.

### Group B — /subagents crash fix (Day 1)

- **US-B1** (SubagentsPage defensive guard): As an operator clicking `/subagents` from the sidebar, I expect the page to render the empty-state or list, not crash with "Cannot read properties of undefined (reading 'length')". Acceptance: `SubagentsPage.tsx:262` adds `?.` on `items` (`data?.items?.length ?? 0`); page renders without error boundary; existing Vitest specs all pass.
- **US-B2** (Vitest defensive spec): As the maintainer, I add 1 spec ensuring the page tolerates `{data: undefined, isLoading: true}` AND `{data: {}, isSuccess: true}` AND `{data: {items: undefined, total: 0}, isSuccess: true}` shapes without crash. Acceptance: 3-case spec added to `tests/unit/pages/subagents/SubagentsPage.test.tsx` (or co-located test file as exists); all pass.

### Group C — /memory crash fix (Day 2)

- **US-C1** (MemoryRecentList defensive guard): As an operator clicking `/memory` then "Recent" tab, I expect to see the list / empty-state, not crash. Acceptance: `MemoryRecentList.tsx:120,126,171` use `(query.data.items ?? []).length` everywhere; existing Vitest specs all pass.
- **US-C2** (MemoryByScopeBrowser defensive guard): As an operator clicking the "By Scope" tab, same expectation. Acceptance: `MemoryByScopeBrowser.tsx:166,172` use `(query.data.items ?? []).length`; existing specs all pass.
- **US-C3** (Vitest defensive spec): Add 1 spec for each component (`MemoryRecentList.test.tsx` + `MemoryByScopeBrowser.test.tsx` if exist) confirming empty-items payload renders without crash. Acceptance: 2 new specs (or 1 spec if combined); all pass.

### Group D — /verification crash fix (Day 3)

- **US-D1** (VerificationList defensive guard): As an operator clicking `/verification`, same expectation. Acceptance: `VerificationList.tsx:186,200,257` use `(query.data.items ?? []).length`; existing specs all pass.
- **US-D2** (CorrectionTraceView defensive guard): As an operator opening a verification trace, same expectation. Acceptance: `CorrectionTraceView.tsx:104` uses `(query.data.entries ?? []).length`; existing specs all pass.
- **US-D3** (Vitest defensive spec): Add 1 spec confirming empty-items / empty-entries payload renders without crash. Acceptance: 1-2 new specs (per existing test file structure); all pass.

### Group E — Regression sweep + fidelity verify + closeout (Day 4)

- **US-E1** (22-route sweep after): Run `route-sweep.mjs after`; confirm: 3 ⚪ routes flip to ✅ PARITY; no other route regresses. Document delta in REPOINT-REPORT.md (3 routes 改 status, 0 new regressions).
- **US-E2** (Manual smoke navigation): Open `/subagents`, `/memory`, `/verification` in dev server; confirm each renders an empty-state or list, no error boundary. Take 3 verification screenshots.
- **US-E3** (5-gate verification): tsc + ESLint + Vitest + Vite build + check:mockup-fidelity all green. Vitest count = 452 baseline + ~3-5 new specs.
- **US-E4** (Closeout): Update progress.md Days 1-4 + retrospective.md Q1-Q7 + sprint-workflow.md §Matrix new row + memory subfile + next-phase-candidates.md (close AD-Overview-PreExisting-Route-Crashes; open new ADs if any).
- **US-E5** (Commit + PR + merge): Open PR; CI green; squash-merge.

---

## Technical Specifications

### Defensive-guard idiom

Two equivalent idioms are acceptable:

```tsx
// Idiom A — array fallback (preferred for empty-check + render-mapping uniformity)
const items = query.data.items ?? [];
{items.length === 0 && (...)}
{items.length > 0 && items.map(...)}
{offset + items.length} of {query.data.total}

// Idiom B — inline optional chain (preferred for single-use lookups)
{query.data.items?.length ?? 0}
```

Per existing Sprint 57.x conventions, use **Idiom A** (locally bind to `const items = ...` at top of `isSuccess` branch) wherever the component references the array more than once. Use Idiom B for single-reference sites (e.g. `SubagentsPage.tsx:262` where only `.length` is needed).

### NO API surface change

This sprint does NOT change:
- TanStack `useQuery` hook signatures.
- Backend service module signatures or `axios` calls.
- DTO type definitions in `frontend/src/features/{memory,verification,subagents}/types.ts`.
- Any data flow / state lifting / event handler.

Only `.length` reads are guarded. If the type definition currently asserts `items: Memory[]` (non-optional), it accurately describes the **happy path** but the runtime payload can omit it. We do NOT relax the type to `items?: Memory[]` because that would cascade to many false-positive `.map` guards. Defensive-guard is the minimal surgical change.

### 22-route sweep delta expectations

After the fix:
- 3 ⚪ routes (`/subagents`, `/memory`, `/verification`) flip from ⚪ ERROR-BOUNDARY to ✅ PARITY (empty-state render or actual list).
- The other 19 routes maintain their prior baseline status (17 ✅ PARITY shell + 1 ✅ PARITY `/sla-dashboard` target + 1 ✅ PROP stub from Sprint 57.32 sweep).
- Total `after` baseline: **20 ✅ + 0 ⚪ + 2 N/A** (the 2 remaining N/A are the routes that didn't run last sprint either — confirm in Day 0 sweep).

---

## File Change List

### NEW files (0)

This sprint creates no new production files. Adds 3-5 new Vitest specs (in existing test files where possible).

### MODIFIED files (~5-6)

| # | Path | Change |
|---|------|--------|
| 1 | `frontend/src/pages/subagents/SubagentsPage.tsx` | `data?.items.length ?? 0` → `data?.items?.length ?? 0` (L262); +MHist |
| 2 | `frontend/src/features/memory/components/MemoryRecentList.tsx` | `query.data.items.length` × 3 sites → `(items ?? []).length`; +MHist |
| 3 | `frontend/src/features/memory/components/MemoryByScopeBrowser.tsx` | `query.data.items.length` × 2 → `(items ?? []).length`; +MHist |
| 4 | `frontend/src/features/verification/components/VerificationList.tsx` | `query.data.items.length` × 3 → `(items ?? []).length`; +MHist |
| 5 | `frontend/src/features/verification/components/CorrectionTraceView.tsx` | `query.data.entries.length` → `(entries ?? []).length`; +MHist |
| 6 | Vitest spec files (existing) | +3-5 defensive specs per US-B2/C3/D3 |

### DELETED files (0)

### PRESERVED (not touched)

- `styles-mockup.css` (no CSS change)
- All component-logic / TanStack hooks / service modules / type definitions
- All other route pages and feature components

---

## Acceptance Criteria

1. **All 3 routes render without error boundary** — manual navigation to `/subagents`, `/memory`, `/verification` shows empty-state or populated list (no red error screen).
2. **22-route sweep `after` baseline shows 3 ⚪ → ✅ flip**, 0 new regressions on other 19 routes.
3. **5 gates green** — tsc + ESLint + Vitest + Vite build + check:mockup-fidelity.
4. **Vitest count maintains** — 452 baseline preserved + 3-5 new defensive specs (final ~455-457).
5. **Docs synced** — REPOINT-REPORT.md (route status delta) + retrospective.md (Q1-Q7) + sprint-workflow.md §Matrix NEW class row + memory subfile + MEMORY.md pointer + CLAUDE.md Current Sprint row + footer + next-phase-candidates.md (close AD-Overview-PreExisting-Route-Crashes; document `frontend-page-bug-fix` 0.45 1st data point).

---

## Deliverables

- [ ] Day 0: this plan + checklist + 三-prong findings + before-baseline 22-route screenshots
- [ ] Day 1: `/subagents` crash fix commit + Vitest spec
- [ ] Day 2: `/memory` crash fix commit + Vitest spec
- [ ] Day 3: `/verification` crash fix commit + Vitest specs
- [ ] Day 4: 22-route sweep after + REPOINT-REPORT + retro + docs sync + PR + CI green + merge

---

## Dependencies & Risks

### Dependencies

- Sprint 57.28 verbatim-CSS foundation in place (unchanged by this sprint).
- `frontend/scripts/route-sweep.mjs` operational (validated by Sprint 57.29-57.32 4 consecutive runs).
- Backend `/api/v1/{memory,verification,subagents}` reachable (read-only — this sprint doesn't depend on backend correctness, only on the page surviving any payload shape).

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Existing Vitest specs implicitly assume `query.data.items` is defined (e.g. test fixtures spread `{items: [...]}` always) | Low | Low — new defensive specs explicitly cover empty-items case; old specs unaffected | Run full Vitest suite after each Day's edit; if old spec fails, treat as drift and add an explicit guard test |
| Some pages might reference `.length` via destructure pattern (`const {items, total} = query.data; items.length`) not caught by my line-by-line grep | Low | Medium — would leave a crash site unfixed | Day 0 Prong 2 grep widens to `\.length` + destructured `items\.length` patterns; Day 4 manual smoke catches any miss |
| Sprint 57.22 audit flagged `/memory` for Phase 58+ STRUCTURAL rebuild — fixing the crash doesn't address structural drift | High | None (in scope) | Crash-fix is explicitly scoped; STRUCTURAL rebuild stays Phase 58+ AD-Memory-Structural-Rebuild-Phase58 unchanged |
| `data?.items?.length ?? 0` chain in SubagentsPage might still leave a downstream `.map` or `.filter` referencing undefined items | Low | Low — defensive `?? []` everywhere it's referenced, not just `.length` | Day 1 grep for `items.map` / `items.filter` in SubagentsPage; if any, also guard them |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Class A (paths-filter)**: this PR touches only `frontend/src/**` and `frontend/tests/**`, no `.github/workflows/**` — backend-ci will paths-filter skip, but visual-regression baseline workflow should not need regen since this is a non-CSS change. If branch protection blocks merge due to skipped required checks, apply the same `.github/workflows/backend-ci.yml` header touch workaround as Sprint 57.31.
- **Class C (singleton across test event loops)**: not applicable (frontend Vitest, no backend test event-loop concern).

---

## Workload

Bottom-up est ~5 hr → calibrated commit ~2.25 hr (multiplier 0.45; NEW class 1st application).

Hour distribution:

| Day | Bottom-up | Calibrated | Tasks |
|-----|-----------|------------|-------|
| Day 0 | 1.5 hr | 0.7 hr | Plan + Checklist + 三-prong + before-baseline 22-route sweep |
| Day 1 | 0.5 hr | 0.2 hr | US-B1 + US-B2 — `/subagents` 1-line fix + 1 Vitest spec |
| Day 2 | 1 hr | 0.5 hr | US-C1/C2/C3 — `/memory` 5 sites + 1-2 Vitest specs |
| Day 3 | 1 hr | 0.5 hr | US-D1/D2/D3 — `/verification` 4 sites + 1-2 Vitest specs |
| Day 4 | 1 hr | 0.4 hr | US-E1-E5 — 22-route sweep after + REPOINT-REPORT + retro + docs + PR/merge |
| **Total** | **~5 hr** | **~2.3 hr** | |

---

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + before-baseline

1. Write plan (this file) + checklist
2. 三-prong:
   - **Prong 1** path-verify: confirm 5 modified-file paths exist
   - **Prong 2** content-verify: re-grep `\.length` in 5 files; confirm 10 offending sites match plan
   - **Prong 3** schema-verify: N/A (no DB schema)
3. Catalog drift findings in progress.md Day 0 entry (expected 0 or near-0 — code-pattern grep was just run)
4. Run `route-sweep.mjs before` (OUT_DIR = `frontend/screenshots/sprint-57-33-*/before/`); confirm 3 ⚪ routes still crash as documented

### Day 1 — `/subagents`

1. Edit `SubagentsPage.tsx:262` — `data?.items.length ?? 0` → `data?.items?.length ?? 0`
2. Add Vitest spec for empty-items + missing-items + loading shapes
3. Commit: `fix(frontend, sprint-57-33): /subagents crash fix — defensive ?. on items.length (US-B1+B2)`

### Day 2 — `/memory`

1. Edit `MemoryRecentList.tsx:120,126,171` + `MemoryByScopeBrowser.tsx:166,172` — uniform `(items ?? []).length`
2. Add Vitest defensive specs (1-2 specs across 2 files)
3. Commit: `fix(frontend, sprint-57-33): /memory crash fix — defensive ?? [] on items.length (US-C1+C2+C3)`

### Day 3 — `/verification`

1. Edit `VerificationList.tsx:186,200,257` + `CorrectionTraceView.tsx:104` — uniform defensive guard
2. Add Vitest defensive specs (1-2 specs)
3. Commit: `fix(frontend, sprint-57-33): /verification crash fix — defensive ?? [] on items/entries.length (US-D1+D2+D3)`

### Day 4 — Sweep + closeout

1. Run `route-sweep.mjs after`; capture 3 ⚪ → ✅ flip
2. Write REPOINT-REPORT.md (delta narrative)
3. Run 5 gates: tsc + ESLint + Vitest + Vite build + check:mockup-fidelity
4. Manual smoke 3 routes
5. Update retrospective.md Q1-Q7 (esp. Q2 calibration with `actual/committed` + `actual/bottom-up`)
6. Update sprint-workflow.md §Scope-class multiplier matrix — add NEW `frontend-page-bug-fix` 0.45 row + MHist entry
7. Update memory subfile + MEMORY.md pointer + CLAUDE.md Current Sprint + next-phase-candidates.md (close AD-Overview-PreExisting-Route-Crashes)
8. Commit: `chore(sprint-57-33): Day 4 closeout — REPOINT-REPORT + retro + memory + docs sync`
9. Push branch + open PR + wait CI green + squash-merge

---

## Related

- `claudedocs/1-planning/next-phase-candidates.md` — AD-Overview-PreExisting-Route-Crashes (this sprint closes it)
- Sprint 57.29 / 57.30 / 57.31 / 57.32 retrospectives — 22-route sweep `before` evidence consistently flagging the 3 ⚪
- `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix — NEW `frontend-page-bug-fix` 0.45 row added Day 4
- `docs/rules-on-demand/frontend-mockup-fidelity.md` — unchanged (no CSS file touched, foundation untouched)
- Sprint 57.22 audit Unit 10 — `/memory` STRUCTURAL rebuild Phase 58+ scope (NOT in this sprint; only crash-fix here)
