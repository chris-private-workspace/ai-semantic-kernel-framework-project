# Sprint 57.36 — Checklist

**Plan**: [`sprint-57-36-plan.md`](./sprint-57-36-plan.md)
**Theme**: AD-Loop-Debug-Verbatim-Repoint (7th Phase-2 per-page; 3rd shape-validation data point)
**Class**: `frontend-verbatim-css-repoint` 0.50 (HYBRID ≈ 0.55)

---

## Day 0 — Plan + Checklist + 三-prong + before baseline

### 0.1 Plan + Checklist drafted (Sprint 57.35 template mirror)
- [x] `sprint-57-36-plan.md` written matching 57.35 9-section structure
- [x] `sprint-57-36-checklist.md` written matching 57.35 Day 0-4 structure
- [x] Plan §Workload Bottom-up est ~4.75 hr → calibrated ~2.4 hr (multiplier 0.50)
- [x] Mockup mapping table §1.2 with mockup file:line + production target + disposition

### 0.2 Step 2.5 Prong 1 — Path verify
- [ ] **Glob mockup `page-governance.jsx`** confirms L33-263 LoopDebug + LoopDebugHeader + EventRow + LoopInspector exist
  - DoD: `reference/design-mockups/page-governance.jsx` 1 file, ≥ 263 lines
  - Verify: `wc -l reference/design-mockups/page-governance.jsx`
- [ ] **Glob production `LoopVisualizer.tsx`** confirms single-file scope
  - DoD: `frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx` 1 file, 209 lines
  - Verify: `wc -l frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx`
- [ ] **Grep `styles-mockup.css`** for `.loop-canvas` / `.loop-track` / `.loop-turn` / `.loop-turn-head` / `.loop-turn-body` / `.event-row` / `.ev-dot` / `.ev-type` / `.ev-detail` / `.ev-timing` / `.turn-no` / `.loop-inspector` class definitions
  - DoD: all 12 classes have `.class { ... }` CSS rule in `frontend/src/styles-mockup.css`
  - Catch R-2: any class missing → escalate before Day 1
- [ ] **Glob `BackendGapBanner` component** confirms availability + recent caller
  - DoD: component exists in `frontend/src/components/` or `frontend/src/features/_primitives/`
  - Verify: `grep -rn "BackendGapBanner" frontend/src/features/cost-dashboard/ frontend/src/features/sla-dashboard/ frontend/src/features/overview/`

### 0.3 Step 2.5 Prong 2 — Content verify
- [ ] **Grep `useChatStore` rawEvents subscription pattern** in LoopVisualizer.tsx
  - DoD: confirm `useChatStore((s) => s.rawEvents)` or equivalent selector pattern; catch any drift from Sprint 57.30 chat_v2 store API
  - Verify: `grep -n "useChatStore\|rawEvents" frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx`
- [ ] **Grep dual-mount mode prop usage** confirms inline + standalone both consumed
  - DoD: confirm both `<LoopVisualizer mode="inline" />` (chat-v2) + `<LoopVisualizer mode="standalone" />` (loop-debug page) call sites
  - Verify: `grep -rn "LoopVisualizer" frontend/src/`
- [ ] **Grep BackendGapBanner current API shape** vs Sprint 57.27 usage
  - DoD: confirm prop names (title / body / href / variant) match Sprint 57.27+ pattern; catch any breaking API drift
  - Verify: read 1-3 lines around BackendGapBanner call in `/overview` rebuild
- [ ] **Grep LoopVisualizer spec file** for class-name-based selectors
  - DoD: confirm any `LoopVisualizer.test.tsx` or related spec selector patterns (`getByRole` / `getByText` / `getByTestId` / `querySelector('.X')`)
  - Verify: `find frontend/src -name "LoopVisualizer*.test.tsx" -o -name "*loop*.test.tsx"`
- [ ] **Grep mockup-fidelity HEX_OKLCH_BASELINE** confirms current value (41 per Sprint 57.35)
  - DoD: `frontend/scripts/check-mockup-fidelity.mjs` has `HEX_OKLCH_BASELINE = 41`
  - Verify: `grep -n "HEX_OKLCH_BASELINE" frontend/scripts/check-mockup-fidelity.mjs`

### 0.4 Step 2.5 Prong 3 — Schema verify
- [x] **N/A** — sprint touches no DB schema / Alembic / ORM models (frontend-only)

### 0.5 Catalog drift findings in progress.md
- [ ] Each Day 0 Prong 1+2 finding gets D-DAY0-N ID + Finding + Implication entry
- [ ] If any finding shifts scope >20% → revise plan §Acceptance Criteria + §Workload + re-confirm with user
- [ ] If any finding shifts scope ≤20% → continue Day 1 with risk noted in §Risks

### 0.6 Capture before baseline (route-sweep)
- [ ] **Re-point `route-sweep.mjs` OUT_DIR** to `sprint-57-36-loop-debug-repoint`
  - DoD: edit `OUT_DIR` const path + add Modification History 1-line entry
  - Verify: `grep -n "sprint-57-36" frontend/scripts/route-sweep.mjs`
- [ ] **Run `node scripts/route-sweep.mjs before`** from `frontend/`
  - DoD: 22 PNG files in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-36/artifacts/loop-debug-repoint/screenshots/before/`
  - Verify: `ls docs/03-implementation/agent-harness-execution/phase-57/sprint-57-36/artifacts/loop-debug-repoint/screenshots/before/ | wc -l` → 22
- [ ] **Manual review of before screenshots** confirms 0 broken routes (≤1 expected pre-existing fails)
  - DoD: `/loop-debug` + `/chat-v2` both render without 404 / 500 / blank screen

### 0.7 Pre-Day-1 baseline checks
- [ ] **Vitest baseline confirmed**: `npm run test` (frontend) → 456/456 passing
  - DoD: confirms R-4 catch — no pre-existing spec breakage before our edits
- [ ] **Mockup-fidelity baseline**: `npm run check:mockup-fidelity` exit 0
  - DoD: confirms `styles-mockup.css` byte-identical + grep guard passes at 41

---

## Day 1 — LoopVisualizer.tsx verbatim port (agent-delegated)

### 1.1 Agent delegation prep
- [ ] **Compose agent task brief** for code-implementer agent
  - DoD: task brief includes plan §3.1-3.5 spec + mockup file:line references + dual-mount preservation rule + Vitest spec update directive
- [ ] **Spawn code-implementer agent** for Day 1 verbatim port
  - DoD: agent receives full context; commits Day 1 progress message

### 1.2 Standalone mode JSX wrapper migration
- [ ] **Wrap standalone mode body in `.loop-canvas` 2-col** per mockup L56
  - DoD: `<div className="loop-canvas"><div className="loop-track">...</div><aside className="loop-inspector">...</aside></div>`
- [ ] **Add placeholder `.loop-inspector` content** for layout completeness
  - DoD: minimal "Inspector pane deferred — see banner above" or mockup-faithful empty state per plan §3.5

### 1.3 Per-turn block class migration
- [ ] **Each turn bucket uses `.loop-turn` + `data-status` attr** per mockup L76
  - DoD: `<div className="loop-turn" data-status={status}>`
- [ ] **Turn header uses `.loop-turn-head`** with `.turn-no` number badge
  - DoD: `<div className="loop-turn-head"><span className="turn-no">turn {n}</span>...</div>`
- [ ] **Turn body uses `.loop-turn-body`** wrapping event list
  - DoD: `<div className="loop-turn-body">{events.map(...)}</div>`

### 1.4 Per-event row class migration + tone mapping
- [ ] **Each event row uses `.event-row` + `.ev-dot` + `.ev-type` + `.ev-detail` + `.ev-timing`** per mockup L193-209
  - DoD: 5 sub-elements present with class names
- [ ] **Tone map adopts mockup L189-191** (`fg → --fg-muted` / `primary → --primary` / `thinking → --thinking` / `tool → --tool` / `memory → --memory` / `success → --success` / `warning → --warning`)
  - DoD: tone → `var(--X)` mapping mirrors mockup verbatim; no hardcoded hex/oklch
- [ ] **Per-event timing renders as `+{N}ms`** per mockup L209
  - DoD: `.ev-timing` shows offset from session start (or per-turn relative — agent picks per existing prod data shape)

### 1.5 Inline mode (chat-v2 cascade) preservation
- [ ] **Inline mode branches WITHOUT `.loop-canvas`** wrapper
  - DoD: `if (mode === "inline") return <div className="loop-track" data-mode="inline">...</div>;`
- [ ] **Inline mode reuses `.loop-turn` + `.event-row`** for visual consistency
  - DoD: same primitive classes; compact layout (no inspector aside)

### 1.6 Day 1 drift catalog + commit
- [ ] **Catalog D-DAY1-N drift findings** in progress.md
- [ ] **Day 1 commit**: `feat(frontend, sprint-57-36): Day 1 — LoopVisualizer verbatim port (mockup classes + dual-mount preserved)`

---

## Day 2 — AP-2 BackendGapBanner + Vitest spec

### 2.1 BackendGapBanner integration in standalone mode
- [ ] **Render BackendGapBanner above `.loop-canvas` in standalone mode only**
  - DoD: copy per plan §3.3; absent in inline mode
- [ ] **Verify banner visible in /loop-debug route render**
  - DoD: manual browser check at `localhost:3007/loop-debug`

### 2.2 Vitest spec updates (preserve behavioral intent)
- [ ] **Update any class-name-based selectors** to mockup classes
  - DoD: `getByText` / `getByRole` / `data-testid` preferred; `querySelector('.X')` updated to mockup class
- [ ] **Add AP-2 banner presence spec** (if not duplicating existing AP-2 banner pattern)
  - DoD: spec verifies standalone renders banner; inline does not
- [ ] **Run `npm run test`** → exit 0, count ≥ 456
  - DoD: baseline preserved or +N for new banner spec

### 2.3 check-mockup-fidelity guard re-evaluate
- [ ] **Run `npm run check:mockup-fidelity`** post-Day-2-edit
  - DoD: exit 0
  - If new `oklch(from var(--X) l c h / X)` token-vocab patterns added → bump `HEX_OKLCH_BASELINE` with 1-line `// Sprint 57.36 ...` Modification History rationale
  - If production LoopVisualizer's prior hardcoded hex/oklch literals are removed by re-point → lower `HEX_OKLCH_BASELINE` with rationale
- [ ] **Update HEX_OKLCH_BASELINE** per actual offender count delta

### 2.4 Day 2 drift catalog + commit
- [ ] **Catalog D-DAY2-N drift findings** in progress.md
- [ ] **Day 2 commit**: `feat(frontend, sprint-57-36): Day 2 — AP-2 BackendGapBanner + Vitest spec preservation`

---

## Day 3 — 22-route sweep + drift handle + fidelity verify

### 3.1 Capture after baseline (route-sweep)
- [ ] **Run `node scripts/route-sweep.mjs after`** from `frontend/`
  - DoD: 22 PNG files in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-36/artifacts/loop-debug-repoint/screenshots/after/`
  - Verify: `ls docs/03-implementation/agent-harness-execution/phase-57/sprint-57-36/artifacts/loop-debug-repoint/screenshots/after/ | wc -l` → 22

### 3.2 Before/after diff review
- [ ] **`/loop-debug` route**: structural / visual delta as expected (verbatim re-point + AP-2 banner)
  - DoD: matches mockup `LoopDebug` shape (turn buckets + event rows + banner above + empty inspector aside)
- [ ] **`/chat-v2` route**: inline LoopVisualizer mount NOT regressed (Sprint 57.30 ship preserved)
  - DoD: visual delta ≤ ε; if any change → must be mockup-faithful improvement
- [ ] **Other 20 routes**: 0 regression
  - DoD: cosmetic ≤ 0; structural = 0; catastrophic = 0

### 3.3 Fidelity verdict
- [ ] **Per-mockup visual diff**: `/loop-debug` vs `reference/design-mockups/index.html` LoopDebug section
  - DoD: PARITY verdict if turn shapes + event rows + tone colors + AP-2 banner all align with mockup verbatim
  - PROP / DRIFT verdict if delta found; catalog in DRIFT-REPORT.md
- [ ] **DRIFT-REPORT.md authored** if any drift found
  - DoD: per-unit severity + classification + rebuild estimate per Sprint 57.22 audit-report template

### 3.4 Day 3 drift catalog + commit
- [ ] **Catalog D-DAY3-N drift findings** in progress.md
- [ ] **Day 3 commit**: `feat(frontend, sprint-57-36): Day 3 — 22-route sweep + fidelity verdict`

---

## Day 4 — Closeout (retro + memory + push + PR)

### 4.1 Retrospective
- [ ] **Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-36/retrospective.md`** per Sprint 57.35 Q1-Q7 template
  - DoD: Q1 went-well / Q2 calibration (with actual hr + ratio) / Q3 didn't-go-as-planned / Q4 differently-next-time / Q5 next-pickup-candidates / Q6 carryover / Q7 N/A (not spike)

### 4.2 Calibration matrix update
- [ ] **Update `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix** `frontend-verbatim-css-repoint` row
  - DoD: 7th data point appended with ratio + shape-vs-scale interpretation per plan §1.5 evaluation criteria
- [ ] **Update / close ADs**:
  - `AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch` (Sprint 57.34 NEW; Sprint 57.35 weakened): if Sprint 57.36 in band → CLOSE (REJECTED bimodal hypothesis)
  - `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` (Sprint 57.35 NEW): promote based on Sprint 57.36 evidence

### 4.3 Memory subfile + MEMORY.md pointer
- [ ] **Write `memory/project_phase57_36_loop_debug_repoint.md`** per REFACTOR-001 single-source policy
  - DoD: full retro highlights + calibration ratio + carryover ADs + file change list + keywords
- [ ] **Update `memory/MEMORY.md`** with 1-line quality pointer (≤300 char)
  - DoD: subfile link + 1-sentence topic + keywords for future retrieval

### 4.4 next-phase-candidates.md
- [ ] **Update `claudedocs/1-planning/next-phase-candidates.md`** Sprint 57.36 Carryover section
  - DoD: any NEW ADs added; resolved ADs marked closed

### 4.5 CLAUDE.md minimal touch
- [ ] **Update `Current Sprint` row** (next sprint id placeholder if not pre-written; or current sprint closed marker)
- [ ] **Update `Last Updated` footer** 1-line per REFACTOR-001 policy
- [ ] **NO new Latest Sprint / Prev Sprint table rows** — single-source preserved elsewhere

### 4.6 Commit closeout + push + PR
- [ ] **Closeout commit**: `chore(sprint-57-36): closeout — retro + memory + calibration matrix + next-phase-candidates`
- [ ] **Push branch + open PR** against main
  - Title: `feat(frontend, sprint-57-36): /loop-debug Phase-2 Verbatim-CSS Re-Point (7th app) — 3rd shape-validation data point`
  - Body: Sprint goal + 22-route sweep verdict + calibration ratio + AP-2 banner rationale + Day 1-3 commits referenced
- [ ] **Monitor CI green** (frontend-ci + V2 Lint + mockup-fidelity guard)
  - If paths-filter triggers backend-ci skip → workaround per `.claude/rules/sprint-workflow.md` §Risk Class A
- [ ] **Squash-merge to main** once CI green + user approval

---

## Sprint 57.36 Closeout Self-Check (per `.claude/rules/sprint-workflow.md` §Sprint Closeout)

- [ ] CLAUDE.md changes only navigator / principle / rule level? (NO sprint history additions)
- [ ] MEMORY.md new entry ~250-300 char quality pointer? (NOT packed retro summary)
- [ ] Sprint detail preserved in memory subfile + retrospective.md? (single-source)
- [ ] Carryover / open items in `next-phase-candidates.md`? (NOT in CLAUDE.md table cell)
- [ ] Calibration ratio tracked in `sprint-workflow.md` matrix? (NOT in CLAUDE.md / MEMORY.md prose)

---

**End of checklist**
