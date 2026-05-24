# Sprint 57.38 — Checklist

[Plan](sprint-57-38-plan.md)

**3-domain batched** (mirror 57.37 5-phase Day-numbering): Day 0 / Day 1 / Day 2 / Day 2.5 / Day 3

---

## Day 0 — Plan + Checklist + 三-prong (Domain B) + Domain C audit prep + before baseline

### 0.1 Plan + Checklist drafted (Sprint 57.37 template mirror)
- [x] **Read Sprint 57.37 plan + checklist § structure outline** (per sprint-workflow §Step 1 format-consistency rule)
- [x] **Draft `sprint-57-38-plan.md`** mirroring 57.37 §0-9 (10 sections) with 3-domain scope
- [x] **Draft `sprint-57-38-checklist.md`** mirroring 57.37 Day 0/1/2/3/3.5/4 → adapted to Day 0/1/2/2.5/3 (one less code day since Domain B = single page re-point smaller than 57.37 Domain A multi-day rebuild)

### 0.2 Step 2.5 Prong 1 — Path verify (Domain B + Domain C scope) ✅ COMPLETED with 5 drift findings
- [x] **Domain B `/subagents` production source path verify** — D1: real file is `SubagentsPage.tsx` (402 lines), NOT `SubagentRegistryView.tsx`; D2: no `components/__tests__/` dir exists
- [x] **Domain B mockup source path verify** — D4: actual mockup source is `page-agents.jsx:300+ SubagentsRegistry + SubagentDetail`, NOT `page-platform.jsx SubagentsPage`
- [ ] **Domain C fullbleed candidate enumeration prep**
  - `grep -l "AppShellV2" frontend/src/pages/**/index.tsx` → list ALL page mounts
  - `grep -L "fullBleed" $(grep -l "AppShellV2" frontend/src/pages/**/index.tsx)` → list pages NOT yet using fullBleed
  - `grep -n "loop-canvas\|chat-shell\|state-shell" reference/design-mockups/*.jsx` → enumerate mockup fullbleed-class layout usage
  - `grep -B2 "height: 100%" reference/design-mockups/styles.css | grep "{$"` → find layout-class selectors with full-viewport height
  - DoD: enumerated candidate list saved as Day 0 progress.md table

### 0.3 Step 2.5 Prong 2 — Content verify ✅ COMPLETED with 1 additional drift finding
- [x] **Sprint 57.33 defensive guards preserved as expected** — D3: actual pattern is `?.` optional chain on `items.length`, NOT `?? []`
- [x] **mockup SubagentsRegistry block actual content readable** — read `page-agents.jsx:300-360` confirmed 4-mode KPI grid + 2-col `1.4fr 1fr` + mockup `.table` + inner Tabs (spec/budget/tools/stats) + oklch row highlight
- [x] **AppShellV2 fullBleed prop signature confirmed (FIX-010 baseline preserved)** — 4 sites at lines 39 (MHist) + 75 (prop def) + 86 (default) + 121 (className branch)
- [x] **D5 (production form factor)**: SubagentsPage.tsx 402 lines Tailwind-utility-heavy → re-classified as `-with-extras` per progress.md drift catalogue
- [ ] **next-phase-candidates.md 3 carryover ADs all OPEN** — confirm before Day 3 close action

### 0.4 Step 2.5 Prong 3 — Schema verify
- [ ] **N/A — no DB schema / migration / ORM changes in Sprint 57.38** (Cat 3 audit unchanged from 57.37; all 3 domains are frontend-only or meta)

### 0.5 Catalog drift findings in progress.md
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-38/progress.md`**
  - Day 0 entry with "Drift findings" header
  - Format: `D{N}` ID + Finding + Implication; cross-ref plan §Risks if scope-shift
  - Decide go/no-go: ≤20% shift → continue; 20-50% → revise plan §Acceptance + §Workload; >50% → abort & redraft
  - DoD: progress.md exists with Day 0 entry

### 0.6 Capture before baseline (route-sweep)
- [ ] **Re-point `frontend/scripts/route-sweep.mjs` OUT_DIR** to `sprint-57-38-class-split-subagents-fullbleed-audit` (1-line edit + MHist entry; mirror Sprint 57.37 D-DAY0-3 pattern)
- [ ] **Start dev server** `npm run dev` (port 3007) in background
- [ ] **Run sweep before**: `node frontend/scripts/route-sweep.mjs before` → 22 PNGs in `claudedocs/4-changes/sprint-57-38-.../screenshots/before/`
- [ ] **Verify**: 22 files in before/ + no failed routes

### 0.7 Pre-Day-1 baseline checks
- [ ] **Vitest baseline confirm 464/464** (`cd frontend && npm test -- --reporter=dot`)
- [ ] **mockup-fidelity guard exit 0** (`node frontend/scripts/check-mockup-fidelity.mjs`)
- [ ] **TypeScript compile baseline** — `npm run typecheck` (skip if pre-existing tsconfig TS6310 same as FIX-010 hotfix)
- [ ] **Lint baseline** — `npm run lint` (clean except 3 pre-existing jsx-ast-utils warnings)

---

## Day 1 — Domain B `/subagents` verbatim CSS re-point (agent-delegated)

### 1.1 Agent delegation prep (Day 0 D1/D3/D4 amend)
- [ ] **Read `SubagentsPage.tsx` (402 lines) fully + mockup `page-agents.jsx:300-450` `SubagentsRegistry` + `SubagentDetail` block** (gather context for code-implementer agent prompt)
- [ ] **Prepare agent task brief**: scope = verbatim CSS swap on single 402-line `SubagentsPage.tsx`; preserve `?.length` defensive guard (D3 amend); mirror Sprint 57.34 `/orchestrator` precedent (config/tabbed-forms shape similar to inner Tabs in this page); use mockup verbatim inline-style literals per `AD-Inline-Style-Rule-vs-Verbatim-Method`; DO NOT touch backend wiring (`useSubagents` hook unchanged)

### 1.2 Domain B production code edit (agent-delegated)
- [ ] **Delegate to `code-implementer` agent**:
  - Input: `SubagentsPage.tsx` + `page-agents.jsx:300-450` mockup + Sprint 57.34 `OrchestratorPage` precedent file as reference
  - Output: verbatim CSS swap commit on `SubagentsPage.tsx` single-file
  - DoD: TS 0 errors / lint clean / Vitest still passes (no specs to adapt — D2 surprise pre-satisfied)
- [ ] **Mark 5th consecutive code-implementer delegation** in progress.md Day 1 entry

### 1.3 Vitest spec adapt (decide at agent finish)
- [ ] **Run Vitest** — `npm test -- --reporter=dot`
- [ ] **If all 464 pass** → D-DAY1-1 positive surprise (Sprint 57.37 D-DAY3-1 convention candidate validated — text/role/data-testid selectors are class-swap-resilient)
- [ ] **If any fail** → adapt spec (prefer adding text/role assertions over class-name assertions where possible)
- [ ] DoD: Vitest ≥464/464

### 1.4 Day 1 drift catalog + commit
- [ ] **progress.md Day 1 entry** — actual hr vs ~1.8 est; drift findings if any (D-DAY1-X format)
- [ ] **Commit**: `feat(frontend, sprint-57-38): Domain B /subagents verbatim CSS re-point`

---

## Day 2 — Domain C fullbleed audit + any 1-line fixes + Domain B spec finalize

### 2.1 Domain C audit finalize
- [ ] **Cross-ref Day 0 Prong 1 candidate list**: for each production page mount, examine corresponding mockup page block outer wrapper class
- [ ] **Per-page verdict**: `fullBleed Y/N` + matching mockup class (if Y) + production current state (`fullBleed`-present / -missing)
- [ ] **Build verdict table** in retrospective.md §Domain C draft
- [ ] DoD: enumerated list with verdict per candidate

### 2.2 Any 1-line fullbleed fixes (per audit verdict)
- [ ] **For each found prop-drop** (cap at 3 in-sprint per §Risks):
  - 1-line edit `<AppShellV2 ... fullBleed>` + MHist entry (mirror FIX-010 commit-line shape)
  - Create `FIX-011-XXX.md` change record per fix (per CLAUDE.md §Change Record Conventions)
  - Run Vitest spec for affected page (if any)
- [ ] **If > 3 sites found** → hard cap; log others as carryover AD `AD-FullBleed-Pages-Audit-Round-2`
- [ ] DoD: each fixed site has FIX-011/012/013-XXX record + MHist entry committed

### 2.3 Vitest spec stability check
- [ ] **Run Vitest** — must remain ≥464/464 after Day 2 edits
- [ ] **Run mockup-fidelity guard** — `node frontend/scripts/check-mockup-fidelity.mjs` exit 0; `HEX_OKLCH_BASELINE` bump within +0-3 envelope if any

### 2.4 Day 2 drift catalog + commit
- [ ] **progress.md Day 2 entry**
- [ ] **Commit**: `feat(frontend, sprint-57-38): Domain C fullbleed audit + fixes (FIX-011..)`

---

## Day 2.5 — Capture after baseline + 22-route sweep diff review + fidelity verdict

### 2.5.1 Capture after baseline (route-sweep)
- [ ] **Run sweep after**: `node frontend/scripts/route-sweep.mjs after` → 22 PNGs in `screenshots/after/`
- [ ] **Verify**: 22 files in after/ + 0 failed routes

### 2.5.2 Before/after diff review
- [ ] **Compare each route**: before/X.png vs after/X.png
- [ ] **Classify**: IDENTICAL (byte-equal) / CHANGED (visual diff) / FAIL (any route crashed)
- [ ] **Expected CHANGED set**: `/subagents` (Domain B intentional) + N fullbleed-fixed routes (Domain C intentional) + `app-shell.png` if `/loop-debug`/fullBleed routes appear in baseline scope
- [ ] **0 UNINTENDED regressions**: any CHANGED outside expected set = drift to investigate before close

### 2.5.3 Fidelity verdict (Domain B)
- [ ] **`/subagents` verdict**: PARITY / NEAR-PARITY / MINOR-DRIFT / MAJOR-DRIFT
- [ ] DoD: verdict recorded in retrospective.md §Domain B

### 2.5.4 Day 2.5 drift + commit
- [ ] **progress.md Day 2.5 entry** — sweep summary IDENTICAL count / CHANGED count
- [ ] **Commit**: `chore(sprint-57-38): Day 2.5 22-route sweep + fidelity verdicts`

---

## Day 3 — Closeout (retro + 3-class matrix + memory + push + PR)

### 3.1 Retrospective
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-38/retrospective.md`** with Q1-Q7 sections
- [ ] **Q2 Domain A decision rationale** — formal Option 1 vs Option 2 narrative; matrix-update edit excerpt; rationale links to 57.34/57.35/57.36/57.37B data points
- [ ] **Q2 calibration ratios per domain** — `actual_total_hr / committed_total_hr` for each of A/B/C; HYBRID blended ratio; verdict vs ~0.62 expected
- [ ] **Q5 carryover candidates** — close 3 ADs + log any new (e.g., `AD-FullBleed-Pages-Audit-Round-2` if cap hit)

### 3.2 Calibration matrix update (3 domains, sprint-workflow.md §Scope-class multiplier matrix) (Day 0 D5 amend)
- [ ] **Domain A decision applied**:
  - If Option 1 → lift `frontend-verbatim-css-repoint` single row 0.50 → 0.60
  - If Option 2 → split into 2 rows `-simple` (0.50) + `-with-extras` (0.65)
- [ ] **Domain B 5th application `-with-extras` data point** (Day 0 D5 reclass; was originally `-simple` 1st app) — add to `-with-extras` row; this is **first non-AP-2/dual-mount extras shape** (KPI grid + 2-col + Tabs + oklch literals) — record this distinct sub-shape note
- [ ] **Domain C `sprint-meta + micro-fix` class** — log as new row OR fold into existing `sprint-meta` if exists; 1-data-point baseline opens
- [ ] **CLOSE 3 carryover ADs**: `class-split-proposal` / `multi-dimensional-variance-watch` / `baseline-lift`

### 3.3 Memory subfile + MEMORY.md pointer
- [ ] **Create `memory/project_phase57_38_class_split_subagents_fullbleed_audit.md`** with sprint detail
- [ ] **Add MEMORY.md entry** — quality pointer (~250-300 char with topic + keywords + subfile link per §Sprint Closeout Update Policy)
- [ ] DoD: index entry rendered

### 3.4 next-phase-candidates.md
- [ ] **Add Sprint 57.38 carryover section** at top
- [ ] **CLOSE 3 ADs** with closure rationale + Sprint 57.38 link
- [ ] **Add any new carryover** (e.g., Round-2 audit if cap hit; new sub-class baseline watch ADs if Domain B ratio outside band)

### 3.5 CLAUDE.md minimal touch (per §Sprint Closeout Update Policy)
- [ ] **Update `Current Sprint` row** with 57.39 + branch placeholder
- [ ] **Update `Last Updated` footer** — 1-line: `**Last Updated**: 2026-05-24 (Sprint 57.38 — 3-domain batched: class-split decision + /subagents re-point + fullBleed audit); see memory/ for sprint history`
- [ ] **NO retro detail packed into table cells** (per REFACTOR-001 lesson)

### 3.6 Commit closeout + push + PR
- [ ] **Final commit**: `chore(sprint-57-38): closeout — retro + 3-class matrix + memory + CLAUDE.md`
- [ ] **Push**: `git push -u origin feature/sprint-57-38-class-split-subagents-fullbleed-audit`
- [ ] **Open PR**: `gh pr create --base main --title "feat(frontend, sprint-57-38): 3-domain batched..."` with full body (mirror 57.37 PR template)
- [ ] **Wait for CI green** → squash-merge ready → user confirmation before merge

---

## Sprint 57.38 Closeout Self-Check (per `.claude/rules/sprint-workflow.md` §Sprint Closeout)

- [ ] **CLAUDE.md changes**: Only Current Sprint row + Last Updated footer (no per-sprint history table additions)?
- [ ] **MEMORY.md new entry**: ~250-300 char quality pointer (topic + keywords + subfile link)?
- [ ] **Sprint detail preserved**: memory subfile + retrospective.md with full content?
- [ ] **Carryover / open items**: documented in `next-phase-candidates.md` (NOT in CLAUDE.md / MEMORY.md prose)?
- [ ] **Calibration ratios**: tracked in `sprint-workflow.md §Scope-class multiplier matrix` (3 domains)?
- [ ] **D-DAY1-1 surprise note**: if Vitest spec needed NO update → record as Sprint 57.37 D-DAY3-1 convention candidate validation
