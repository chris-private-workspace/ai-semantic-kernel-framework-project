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

- [x] **Edit `features/memory/components/MemoryRecentList.tsx`** — 4 sites L120/126/141/171 (drift D1: plan listed 3 sites L120/126/171; Day 2 grep found additional `.map` site L141 — same crash pattern just on `.map` instead of `.length`; both fixed uniformly with `(query.data.items ?? [])`)

### 2.2 US-C2 — MemoryByScopeBrowser defensive guard

- [x] **Edit `features/memory/components/MemoryByScopeBrowser.tsx`** — 3 sites L166/172/174 (drift D2: plan listed 2 sites L166/172; Day 2 grep found additional `.map` site L174 — same pattern)

### 2.3 US-C3 — Vitest defensive specs

- [x] **Added 2 defensive specs** — `MemoryRecentList.test.tsx` (no-items shape → empty state renders) + `MemoryByScopeBrowser.test.tsx` (click layer-card-system + no-items payload → scope-empty renders); each asserts no throw

### 2.4 Day 2 5-gate quick-check + commit

- [x] **Vitest pass** — memory 30/30 (28 baseline + 2 NEW defensive)
- [ ] **Commit Day 2** — `fix(frontend, sprint-57-33): /memory crash fix — defensive ?? [] on items.length/map (US-C1+C2+C3)`

---

## Day 3 — `/verification` crash fix (Group D)

### 3.1 US-D1 — VerificationList defensive guard

- [x] **Edit `features/verification/components/VerificationList.tsx`** — 4 sites L186/200/215/257 (drift D3: plan listed 3 .length sites; Day 3 grep found additional `.map` at L215 — same pattern; replace_all of `query.data.items` → `(query.data.items ?? [])` covered all 4 in one edit)

### 3.2 US-D2 — CorrectionTraceView defensive guard

- [x] **Edit `features/verification/components/CorrectionTraceView.tsx`** — 2 sites L58/L104 (drift D4: plan listed 1 site L104; Day 3 found additional `_groupByTurn(query.data.entries)` call at L58 — `_groupByTurn` would crash inside `for…of` on undefined; both guarded with `?? []`)

### 3.3 US-D3 — Vitest defensive specs

- [x] **Added 1 defensive spec** to `VerificationList.test.tsx` (no-items shape → empty state renders + no throw). `CorrectionTraceView` defensive spec deliberately skipped — its crash path is indirect (via `_groupByTurn` for…of) and covered by manual smoke navigation in Day 4 (per plan US-D3 "1-2 new specs"; 1 chosen for scope discipline)

### 3.4 Day 3 5-gate quick-check + commit

- [x] **Vitest pass full suite** — **456/456** (452 baseline + 4 NEW defensive across subagents/memoryRecent/memoryByScope/verification)
- [ ] **Commit Day 3** — `fix(frontend, sprint-57-33): /verification crash fix — defensive ?? [] on items/entries.length (US-D1+D2+D3)`

---

## Day 4 — Regression sweep + closeout (Group E)

### 4.1 US-E1 — 22-route sweep after

- [x] **Run `route-sweep.mjs after`** — 22 PNGs captured to `claudedocs/4-changes/sprint-57-33-page-bug-fix/screenshots/after/`
- [x] **Sweep delta analysis** — 3 ⚪ → ✅ flip confirmed (subagents = full Registry; memory = empty state; verification = filter form + empty state); 0 regressions on 19 other routes; FIX-REPORT.md documents per-route delta

### 4.2 US-E2 — Manual smoke navigation

- [x] **Navigate `/subagents`** — empty-state or list renders; no error boundary
- [x] **Navigate `/memory`** (both Recent + By Scope tabs) — same
- [x] **Navigate `/verification`** — same
- [x] 3 verification screenshots captured via after-baseline sweep (sampling subagents.png / memory.png / verification.png from `screenshots/after/` in lieu of separate manual/ dir; functionally equivalent)

### 4.3 US-E3 — Final 5-gate verification

- [x] **tsc + Vite build** — `built in 3.16s` (subsumed in `npm run build`)
- [x] **ESLint** — exit 0
- [x] **Vitest** — **456/456** (452 baseline + 4 NEW defensive)
- [x] **check:mockup-fidelity** — diff empty + grep clean (baseline 25 hex/oklch unchanged)

### 4.4 US-E4 — Docs sync

- [x] **FIX-REPORT.md** — `claudedocs/4-changes/sprint-57-33-page-bug-fix/FIX-REPORT.md` (3 ⚪ → ✅ delta + 11 sites fixed across 5 files + 4 NEW Vitest specs + drift catalog D1-D4 + calibration; renamed from REPOINT-REPORT.md since this is a bug-fix not re-point sprint)
- [x] **progress.md Day 0-4** — daily entries with task-level estimate vs actual
- [x] **retrospective.md Q1-Q7** — Q2 calibration ratio 1.24 top edge of band + 1st-data-point KEEP 0.45
- [x] **`sprint-workflow.md §Matrix`** — NEW `frontend-page-bug-fix` 0.45 row added + MHist entry
- [x] **memory subfile** — `memory/project_phase57_33_page_bug_fix_sweep.md` written
- [x] **`MEMORY.md` pointer** — Sprint 57.33 entry added above Sprint 57.32 entry
- [x] **`CLAUDE.md` Current Sprint row + footer** — minimal touch (2 line edits)
- [x] **`next-phase-candidates.md`** — Sprint 57.33 Carryover section added + AD-Overview-PreExisting-Route-Crashes marked ✅ RESOLVED

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
