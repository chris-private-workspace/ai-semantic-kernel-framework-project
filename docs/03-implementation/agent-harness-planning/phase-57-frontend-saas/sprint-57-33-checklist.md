# Sprint 57.33 — Checklist

**Plan**: [`sprint-57-33-plan.md`](./sprint-57-33-plan.md)
**Sprint Goal**: Page-bug-fix sweep on `/subagents`, `/memory`, `/verification` — defensive `?? []` guard on `query.data.items.length` (and one `entries.length`). 5 files / 10 sites / 3-5 new Vitest specs. NEW class `frontend-page-bug-fix` 0.45 (1st application).

---

## Day 0 — Plan + Checklist + 三-prong + Before-baseline

### 0.1 Plan + Checklist drafted

- [x] **`sprint-57-33-plan.md` exists** — mirrors Sprint 57.32 format (11 ## sections + sub-sections)
  - DoD: file at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-33-plan.md`
- [x] **`sprint-57-33-checklist.md` exists** — this file
  - DoD: 5 Day groups, `- [ ]` boxes, DoD + Verify command per item

### 0.2 三-prong verify (plan-vs-repo)

- [x] **Prong 1 — path verify** — all 5 modified-file paths confirmed via Glob/PowerShell
- [x] **Prong 2 — content verify** — 10 offending sites confirmed via Grep `\.length`; byte-for-byte match with plan §Offending sites table; 0 drift
- [x] **Prong 3 — schema verify** — N/A (frontend-only crash fix; no DB schema touched)
- [x] **Drift findings catalog** — 0 drifts logged in progress.md Day 0 entry

### 0.3 Before-baseline 22-route sweep

- [x] **Run `route-sweep.mjs before`** — `claudedocs/4-changes/sprint-57-33-page-bug-fix/screenshots/before/` 22 PNGs captured
- [x] **Manual confirmation** — `/subagents` screenshot sampled; error boundary text "Cannot read properties of undefined (reading 'length')" matches AD baseline exactly

### 0.4 Day 0 commit

- [ ] **Commit Day 0 artifacts** — plan + checklist + progress.md (Day 0 entry) + before-baseline screenshots
  - Commit message: `docs(sprint-57-33): Day 0 — plan + checklist + 三-prong (10 sites confirmed) + before-baseline 22-route sweep`

---

## Day 1 — `/subagents` crash fix (Group B)

### 1.1 US-B1 — SubagentsPage defensive guard

- [x] **Edit `pages/subagents/SubagentsPage.tsx:262`** — `data?.items.length ?? 0` → `data?.items?.length ?? 0`
- [x] **Grep `items\.(map|filter|forEach)` in SubagentsPage** — 0 downstream sites (only L262 references `items` in the page; L17 is in comment, L274 is `SUBAGENT_LIST.length` static fixture)

### 1.2 US-B2 — Vitest defensive spec

- [x] **Add missing-items defensive spec** — `tests/unit/pages/subagents/SubagentsPage.test.tsx` — 1 case (`items` field omitted in mocked response). Page renders without throw + KPI cards render + carryover banner emerges on query resolve.

### 1.3 Day 1 5-gate quick-check

- [x] **Vitest pass** on Day 1 edit — 8/8 (7 baseline + 1 NEW defensive)
- [ ] **Commit Day 1** — `fix(frontend, sprint-57-33): /subagents crash fix — defensive ?. on items.length (US-B1+B2)`

---

## Day 2 — `/memory` crash fix (Group C)

### 2.1 US-C1 — MemoryRecentList defensive guard

- [ ] **Edit `features/memory/components/MemoryRecentList.tsx`** — 3 sites L120/126/171
  - L120: `query.data.items.length === 0` → `(query.data.items ?? []).length === 0`
  - L126: `query.data.items.length > 0` → `(query.data.items ?? []).length > 0`
  - L171: `offset + query.data.items.length` → `offset + (query.data.items ?? []).length`
  - DoD: all 3 sites guarded; consider top-of-`isSuccess`-branch `const items = query.data.items ?? []` refactor if cleaner (Idiom A from plan)

### 2.2 US-C2 — MemoryByScopeBrowser defensive guard

- [ ] **Edit `features/memory/components/MemoryByScopeBrowser.tsx`** — 2 sites L166/172
  - L166: `query.data.items.length === 0` → `(query.data.items ?? []).length === 0`
  - L172: `query.data.items.length > 0` → `(query.data.items ?? []).length > 0`
  - DoD: both sites guarded

### 2.3 US-C3 — Vitest defensive specs

- [ ] **Add defensive specs** to existing test files (or create co-located spec)
  - 1-2 specs: 1 covers MemoryRecentList empty-items; 1 covers MemoryByScopeBrowser empty-items
  - DoD: each asserts render without crash
  - Verify: `cd frontend; npm run test -- --run memory`

### 2.4 Day 2 5-gate quick-check + commit

- [ ] **tsc + ESLint + Vitest pass**
- [ ] **Commit Day 2** — `fix(frontend, sprint-57-33): /memory crash fix — defensive ?? [] on items.length (US-C1+C2+C3)`

---

## Day 3 — `/verification` crash fix (Group D)

### 3.1 US-D1 — VerificationList defensive guard

- [ ] **Edit `features/verification/components/VerificationList.tsx`** — 3 sites L186/200/257
  - L186: `query.data.items.length === 0` → `(query.data.items ?? []).length === 0`
  - L200: `query.data.items.length > 0` → `(query.data.items ?? []).length > 0`
  - L257: `offset + query.data.items.length` → `offset + (query.data.items ?? []).length`

### 3.2 US-D2 — CorrectionTraceView defensive guard

- [ ] **Edit `features/verification/components/CorrectionTraceView.tsx`** — 1 site L104
  - L104: `query.data.entries.length` → `(query.data.entries ?? []).length`

### 3.3 US-D3 — Vitest defensive specs

- [ ] **Add defensive specs** for VerificationList + CorrectionTraceView empty-state shapes
  - 1-2 new specs
  - Verify: `cd frontend; npm run test -- --run verification`

### 3.4 Day 3 5-gate quick-check + commit

- [ ] **tsc + ESLint + Vitest pass**
- [ ] **Commit Day 3** — `fix(frontend, sprint-57-33): /verification crash fix — defensive ?? [] on items/entries.length (US-D1+D2+D3)`

---

## Day 4 — Regression sweep + closeout (Group E)

### 4.1 US-E1 — 22-route sweep after

- [ ] **Run `route-sweep.mjs after`** — OUT_DIR = `frontend/screenshots/sprint-57-33-page-bug-fix/after/`
  - DoD: 22 PNGs captured
  - Verify: `cd frontend; node scripts/route-sweep.mjs after`
- [ ] **Sweep delta analysis** — confirm 3 ⚪ → ✅ PARITY; no other route regresses
  - DoD: REPOINT-REPORT.md documents delta with concrete per-route status table

### 4.2 US-E2 — Manual smoke navigation

- [ ] **Navigate `/subagents`** — empty-state or list renders; no error boundary
- [ ] **Navigate `/memory`** (both Recent + By Scope tabs) — same
- [ ] **Navigate `/verification`** — same
- [ ] Capture 3 verification screenshots (added to `frontend/screenshots/sprint-57-33-page-bug-fix/manual/`)

### 4.3 US-E3 — Final 5-gate verification

- [ ] **tsc** (via `npm run build`)
- [ ] **ESLint** (`npm run lint`)
- [ ] **Vitest** — count = 452 baseline + 3-5 new specs (final ~455-457)
- [ ] **Vite build** — success
- [ ] **check:mockup-fidelity** — diff empty + grep clean (CSS untouched)

### 4.4 US-E4 — Docs sync

- [ ] **REPOINT-REPORT.md** — `claudedocs/4-changes/sprint-57-33-page-bug-fix/REPOINT-REPORT.md` documenting:
  - 3 ⚪ → ✅ flip
  - 10 sites fixed across 5 files
  - 3-5 new Vitest defensive specs
  - 22-route sweep delta
- [ ] **progress.md Day 0-4** — daily entries with `Task X.Y — actual Z min (est ~W min, delta ±N%)` format
- [ ] **retrospective.md Q1-Q7** — Q2 calibration (`actual/committed` + `actual/bottom-up` + class evaluation per `When to adjust`)
- [ ] **`sprint-workflow.md §Scope-class multiplier matrix`** — add NEW `frontend-page-bug-fix` 0.45 row (1st application) + MHist entry
- [ ] **memory subfile** — `memory/project_phase57_33_page_bug_fix_sweep.md` with sprint summary
- [ ] **`MEMORY.md` pointer** — ~250-300 char quality pointer (topic + keywords + subfile link)
- [ ] **`CLAUDE.md` Current Sprint row + footer** — minimal touch (1-2 lines)
- [ ] **`next-phase-candidates.md`** — close AD-Overview-PreExisting-Route-Crashes (RESOLVED) + Sprint 57.33 Carryover section

### 4.5 US-E5 — Commit + PR + merge

- [ ] **Day 4 commit** on `feature/sprint-57-33-page-bug-fix-sweep`
  - Commit message: `chore(sprint-57-33): Day 4 closeout — REPOINT-REPORT + retro + memory + docs sync`
- [ ] **PR open** — `gh pr create` with body listing Sprint Goal + 3-route fix narrative + 5 gates green + 22-route sweep delta + class 1st-data-point note
- [ ] **CI green → squash-merge** — expect cleaner than 57.31/57.32 (no CSS change, no visual regression baseline regen needed)

### 4.6 Sprint closeout self-check

- [ ] Sacred Rule check — 0 unchecked items deleted
- [ ] Acceptance Criteria — all 5 pass (3 routes render + 22-route sweep flip + 5 gates + Vitest count maintained + docs synced)
- [ ] Working tree clean post-merge — on main
- [ ] Branch deleted — `feature/sprint-57-33-page-bug-fix-sweep` deleted local + remote
