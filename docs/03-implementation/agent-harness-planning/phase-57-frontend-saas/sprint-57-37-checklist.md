# Sprint 57.37 — Checklist

**Plan**: [`sprint-57-37-plan.md`](./sprint-57-37-plan.md)
**Theme**: AD-LoopDebug-Full-Rebuild-And-StateInspector-Repoint (2-domain batched)
**Class**: HYBRID — Domain A `frontend-mockup-strict-rebuild` 0.60 (5th app) + Domain B `frontend-verbatim-css-repoint` 0.50 (8th app); blended ≈ 0.58

---

## Day 0 — Plan + Checklist + 三-prong (2 domains) + before baseline

### 0.1 Plan + Checklist drafted (Sprint 57.36 template mirror)
- [x] `sprint-57-37-plan.md` written matching Sprint 57.36 9-section structure with 2-domain extensions
- [x] `sprint-57-37-checklist.md` written matching Sprint 57.36 Day 0-4 structure
- [x] Plan §Workload Bottom-up est ~9.5-10 hr → calibrated ~5.5 hr (HYBRID multiplier 0.58)
- [x] Mockup mapping tables §1.2 for BOTH domains with mockup file:line + production target + disposition

### 0.2 Step 2.5 Prong 1 — Path verify (BOTH domains; extended `src/**` AND `tests/**` per Sprint 57.36 D-DAY1-1 lesson)
- [ ] **Glob mockup `page-governance.jsx`** L33-263 + `page-platform.jsx` L21+ (StateInspector) confirmed exist
  - DoD: both mockup files exist; line ranges accessible
- [ ] **Glob production targets** confirm scope
  - DoD: `frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx` (209 lines) + `frontend/src/pages/state-inspector/StateInspectorPage.tsx` (366 lines) + `frontend/src/pages/state-inspector/index.tsx` (1-line export)
- [ ] **Glob `frontend/src/**` AND `frontend/tests/**`** for any LoopVisualizer / StateInspector test files (Sprint 57.36 D-DAY1-1 lesson)
  - DoD: confirm `frontend/tests/unit/orchestrator-loop/LoopVisualizer.test.tsx` exists (Sprint 57.36) + check StateInspector test file existence
- [ ] **Glob `frontend/src/features/orchestrator-loop/`** for existing `_fixtures/` or `_components/` directories
  - DoD: confirm none exist (will need to create) OR find existing structure to reuse
- [ ] **Grep `styles-mockup.css`** for ALL StateInspector-specific classes mockup uses
  - DoD: scan `page-platform.jsx:21+` for class names, then grep each in styles-mockup.css; confirm all classes are byte-identical copied; flag any missing (R-4 catch)

### 0.3 Step 2.5 Prong 2 — Content verify
- [ ] **Read `frontend/src/features/chat_v2/types.ts`** for `LoopEvent` discriminated union shape
  - DoD: confirm all event types we need for fixture exist; document semantic mapping mockup → production
- [ ] **Grep `useStateSnapshot` hook** in StateInspectorPage.tsx
  - DoD: confirm Sprint 57.19 US-B3 backend wiring location; ensure Domain B re-point preserves
- [ ] **Read `BackendGapBanner.tsx` API** confirm `{ reason: string }` (Sprint 57.36 D-DAY0-2)
  - DoD: API unchanged since 57.36
- [ ] **Grep existing `LoopVisualizer.tsx` Sprint 57.36 baseline** for current dual-mount + eventTone pattern
  - DoD: confirm what Domain A extends + what stays
- [ ] **Read `StateInspectorPage.tsx` L48-58 TONE_CLASS Record** to plan replacement
  - DoD: list all `bg-X/16 text-X` patterns → mockup token vars needed; preview HEX_OKLCH_BASELINE delta

### 0.4 Step 2.5 Prong 3 — Schema verify
- [x] **N/A** — frontend-only sprint; no DB schema / Alembic / ORM model changes

### 0.5 Catalog drift findings in progress.md
- [ ] Each Day 0 Prong 1+2 finding gets D-DAY0-N ID + Finding + Implication entry
- [ ] If any finding shifts scope >20% → revise plan §Acceptance Criteria + §Workload + re-confirm with user
- [ ] If any finding shifts scope ≤20% → continue Day 1 with risk noted in §Risks

### 0.6 Capture before baseline (route-sweep)
- [ ] **Re-point `route-sweep.mjs` OUT_DIR** to `sprint-57-37-loop-debug-state-inspector`
  - DoD: edit `OUT_DIR` const path + add Modification History 1-line entry
- [ ] **Run `node scripts/route-sweep.mjs before`** from `frontend/`
  - DoD: 22 PNG files in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-37/artifacts/loop-debug-state-inspector/screenshots/before/`
- [ ] **Manual review of before screenshots** confirms 0 broken routes
  - DoD: `/loop-debug` (empty-state baseline) + `/state-inspector` (Sprint 57.19 vintage baseline) + `/chat-v2` (inline LoopVisualizer mount baseline)

### 0.7 Pre-Day-1 baseline checks
- [ ] **Vitest baseline confirmed**: `npm run test -- --run` → 456/456 passing
- [ ] **Mockup-fidelity baseline**: `npm run check:mockup-fidelity` exit 0 (baseline = 41)

---

## Day 1 — Domain A: Fixture + Playback + Filter (agent-delegated)

### 1.1 Agent delegation prep
- [ ] **Compose agent task brief** for code-implementer agent (2-domain scope)
  - DoD: brief includes plan §3.1-3.6 spec + drift summary D-DAY0-N + corrected BackendGapBanner API + dual-mount preservation + Sprint 57.36 cascade-safety directive
- [ ] **Spawn code-implementer agent** for Day 1-3 batched implementation
  - DoD: agent receives full context; commits Day 1 progress message

### 1.2 Fixture file (NEW)
- [ ] **Create `frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts`**
  - DoD: 14-22 typed `LoopEvent` entries mapping mockup `LoopEvents` L5-31 semantically
  - File header per `.claude/rules/file-header-convention.md` Python pattern adapted for TS
  - Mockup → production type mapping table documented in file header `Description:`
- [ ] **Mockup-to-production mapping decisions**
  - DoD: mapping table in fixture file + comment explaining gaps (e.g. mockup `subagent.spawn` → no production equivalent → omit or map to closest)

### 1.3 Fixture loader in LoopVisualizer.tsx
- [ ] **Empty-state branch wires fixture** when `rawEvents.length === 0` AND `mode === "standalone"`
  - DoD: `events = rawEvents.length === 0 && mode === "standalone" ? DEMO_LOOP_EVENTS : rawEvents`
- [ ] **AP-2 banner shows "DEMO DATA" only when fixture is active**
  - DoD: conditional banner copy

### 1.4 Playback state machine
- [ ] **Add `cursor` / `playing` / `speed` state** per plan §3.2
  - DoD: useState hooks; useEffect interval at `1000/speed` ms; cleanup on unmount
- [ ] **Render playback strip** per mockup L154-184
  - DoD: Pause/Resume button + scrubber input range + speed pills 1×/4×/8×/16× with mockup classes (`.btn-group`, `.btn`, mockup styling)

### 1.5 Filter state
- [ ] **Add `filter` state** with 6 categories per plan §3.3
  - DoD: useState Record<FilterCategory, boolean>; `eventCategory()` helper function
- [ ] **Render filter pills** per mockup L132-150
  - DoD: 6 mockup `<button className="badge">` with opacity + click toggle

### 1.6 Day 1 drift catalog + commit
- [ ] **Catalog D-DAY1-N drift findings** in progress.md
- [ ] **Day 1 commit**: `feat(frontend, sprint-57-37): Day 1 — Domain A LoopVisualizer fixture + playback + filter`

---

## Day 2 — Domain A: Inspector + AP-2 + Vitest (agent-delegated)

### 2.1 LoopInspector right pane
- [ ] **Implement `<LoopInspector event={selected} allEvents={...} />`** per plan §3.4 + mockup L214-263
  - DoD: selected-event detail rendering (KvRow rows for ts / turn / audit_id / span_id / tenant / session_id / agent + HITL Policy section conditional + Raw payload JSON)
- [ ] **Selected event click handler** wires event row click → `setSelected(index)`
  - DoD: visual selection state on event row; inspector updates
- [ ] **Empty inspector placeholder** for no-event-selected state
  - DoD: friendly empty-state copy (NOT the "deferred Phase 58+" copy — that was Sprint 57.36 placeholder; replace)

### 2.2 AP-2 BackendGapBanner copy correction
- [ ] **Update banner reason** per plan §3.x + US-A5
  - DoD: "DEMO DATA — these events are fixture data from the mockup; live SSE events populate when chat-v2 session runs; per-event detail persistence + cross-session lookup require backend SSE event persistence (Phase 58+ per Sprint 57.12 AP-6)."
- [ ] **Banner conditional**: shows only when fixture active (rawEvents empty + standalone)
  - DoD: if real events present → no banner (operator has live data, no need for demo disclosure)

### 2.3 Vitest spec updates
- [ ] **Update existing `LoopVisualizer.test.tsx`** for new fixture behavior
  - DoD: tests for empty-rawEvents-standalone shows fixture; tests for rawEvents-present uses real events
- [ ] **Add specs for new widgets** (playback / filter / inspector) — KEEP MINIMAL (don't gold-plate)
  - DoD: 2-4 new specs verify state interactions; preserve baseline ≥ 456 + N
- [ ] **Run `npm run test`** → exit 0
  - DoD: baseline preserved or +N for new specs

### 2.4 Day 2 drift catalog + commit
- [ ] **Catalog D-DAY2-N drift findings** in progress.md
- [ ] **Day 2 commit**: `feat(frontend, sprint-57-37): Day 2 — Domain A LoopInspector + AP-2 banner correction + Vitest`

---

## Day 3 — Domain B: StateInspectorPage verbatim re-point (agent-delegated)

### 3.1 Read mockup `page-platform.jsx:21+` StateInspector
- [ ] **Read mockup StateInspector main section** (estimate L21 to L200+)
  - DoD: identify all classes used + structure (4 KPI cards / 320px-1fr grid / version chain left / current-state + diff right)
- [ ] **Confirm all classes in `styles-mockup.css`** (Day 0 Prong 1 should have caught any missing)
  - DoD: 0 missing classes; if any missing → block until Layer 2 verbatim copy updated

### 3.2 StateInspectorPage.tsx verbatim CSS swap
- [ ] **Drop `TONE_CLASS` Record** + replace with direct `style={{ background: 'var(--X)', color: 'var(--X)' }}` or `var(--X)` alpha-tint per Sprint 57.36 `eventTone()` precedent
  - DoD: 0 instances of `bg-X/16 text-X` Tailwind utility patterns
- [ ] **Replace Tailwind utility grid** with mockup verbatim grid pattern
  - DoD: `.version-grid` or inline grid template matching mockup L?
- [ ] **Replace shadcn token classes** (`bg-muted text-muted-foreground` etc.) with mockup tokens (`var(--bg-2)` / `var(--fg-muted)`)
- [ ] **Preserve `useStateSnapshot` hook + carryover banner** (US-B2)
  - DoD: Sprint 57.19 US-B3 behavior unchanged

### 3.3 Vitest spec updates (Domain B)
- [ ] **Update StateInspector spec if exists** for class selector changes
  - DoD: tests pass; baseline preserved
- [ ] **Run `npm run test`** → exit 0

### 3.4 check-mockup-fidelity guard re-evaluate
- [ ] **Run `npm run check:mockup-fidelity`** post-Domain-A+B edits
  - DoD: exit 0
  - If new `oklch(from var(--X) l c h / X)` patterns added by either domain → bump `HEX_OKLCH_BASELINE` with 1-line rationale
  - If Domain B verbatim drops hardcoded colors → potentially lower; net delta depends on Domain A additions

### 3.5 Day 3 drift catalog + commit
- [ ] **Catalog D-DAY3-N drift findings** in progress.md
- [ ] **Day 3 commit**: `feat(frontend, sprint-57-37): Day 3 — Domain B StateInspector verbatim CSS re-point`

---

## Day 3.5 — 22-route sweep + drift handle + 2-domain fidelity verify

### 3.5.1 Capture after baseline (route-sweep)
- [ ] **Run `node scripts/route-sweep.mjs after`** from `frontend/`
  - DoD: 22 PNG files in `screenshots/after/`

### 3.5.2 Before/after diff review
- [ ] **`/loop-debug` route**: major structural delta (fixture demo events visible; playback strip + filter pills + inspector pane all rendered)
  - DoD: matches mockup `LoopDebug` visually
- [ ] **`/state-inspector` route**: visual delta from verbatim class swap (subtle if mockup classes happen to produce similar visual to prior Tailwind utility)
  - DoD: matches mockup `StateInspector` visually
- [ ] **`/chat-v2` route**: inline LoopVisualizer mount NOT regressed (Sprint 57.30 + 57.36 ship preserved)
  - DoD: visual delta ≤ ε
- [ ] **Other 19 routes**: 0 regression
  - DoD: cosmetic ≤ 0; structural = 0

### 3.5.3 Fidelity verdict (both domains)
- [ ] **Per-mockup visual diff Domain A**: `/loop-debug` after vs `localhost:8080/#loop-debug` mockup
  - DoD: PARITY (or PROP with documented gaps)
- [ ] **Per-mockup visual diff Domain B**: `/state-inspector` after vs `localhost:8080/#state-inspector` mockup
  - DoD: PARITY (or PROP with documented gaps)

### 3.5.4 Day 3.5 drift + commit
- [ ] **Catalog D-DAY3.5-N drift findings**
- [ ] **Sweep commit**: included in Day 4 closeout commit OR separate per agent preference

---

## Day 4 — Closeout (retro + 2-class matrix + memory + push + PR)

### 4.1 Retrospective
- [ ] **Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-37/retrospective.md`** per Sprint 57.36 Q1-Q7 template
  - DoD: Q1 went-well / Q2 calibration (2 domain ratios computed separately) / Q3 didn't-go-as-planned / Q4 differently-next-time / Q5 next-pickup-candidates / Q6 carryover / Q7 N/A (not spike)
  - Must address BOTH calibration class data points + multi-dimensional-variance-watch AD evolution

### 4.2 Calibration matrix update (2 classes)
- [ ] **Update `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix** for BOTH classes:
  - `frontend-mockup-strict-rebuild` row: 5th data point (Domain A ratio)
  - `frontend-verbatim-css-repoint` row: 8th data point + 4th non-rich (Domain B ratio); explicitly note if Domain B in band → "simple" sub-class proposal strengthens
- [ ] **Update / close ADs**:
  - `AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch` (Sprint 57.36 NEW): evaluate Domain B 4th non-rich data point; if in band → propose Sprint 57.38 class split

### 4.3 Memory subfile + MEMORY.md pointer
- [ ] **Write `memory/project_phase57_37_loop_debug_fixture_state_inspector.md`** per REFACTOR-001 single-source policy
- [ ] **Update `memory/MEMORY.md`** with 1-line quality pointer

### 4.4 next-phase-candidates.md
- [ ] **Update `claudedocs/1-planning/next-phase-candidates.md`** Sprint 57.37 Carryover section
  - 2-domain bundle requires distinct entries OR single entry referencing both

### 4.5 CLAUDE.md minimal touch
- [ ] **Update `Current Sprint` row** + `Last Updated` footer per REFACTOR-001

### 4.6 Commit closeout + push + PR
- [ ] **Closeout commit**: `chore(sprint-57-37): closeout — retro + memory + 2-class calibration matrix`
- [ ] **Push branch + open PR** against main
  - Title: `feat(frontend, sprint-57-37): /loop-debug Full Rebuild (closes 57.36 mockup-fidelity gap) + /state-inspector Phase-2 Re-Point (8th app) — 2-domain batched`
- [ ] **Monitor CI green**
- [ ] **Squash-merge to main** once CI green + user approval

---

## Sprint 57.37 Closeout Self-Check (per `.claude/rules/sprint-workflow.md` §Sprint Closeout)

- [ ] CLAUDE.md changes only navigator / principle / rule level
- [ ] MEMORY.md new entry ~300-500 char quality pointer (2-domain may warrant slightly longer)
- [ ] Sprint detail preserved in memory subfile + retrospective.md
- [ ] Carryover / open items in `next-phase-candidates.md`
- [ ] 2 calibration ratios tracked in `sprint-workflow.md` matrix (one per class)

---

**End of checklist**
