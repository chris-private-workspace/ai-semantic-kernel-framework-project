# Sprint 57.34 — AD-Orchestrator-Verbatim-Repoint

**File**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-34-plan.md`
**Purpose**: Plan for Sprint 57.34 — **5th Phase-2 per-page verbatim-CSS re-point** (`/orchestrator`), 1st **non-rich-dashboard** shape in the epic; **2nd validation data point** for `frontend-verbatim-css-repoint` 0.50 lifted baseline (`AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`, Sprint 57.31 NEW).
**Category**: Sprint planning / Phase 57+ Frontend SaaS — Phase-2 per-page re-point epic
**Scope**: Phase 57+ Frontend SaaS — Phase-2 per-page re-point epic, 5th application; 1st non-rich-dashboard shape
**Created**: 2026-05-24
**Last Modified**: 2026-05-24
**Status**: Draft → awaiting user approval

> **Modification History**
> - 2026-05-24: Initial draft (Sprint 57.34 Day 0) — /orchestrator Phase-2 verbatim re-point; 5th epic app + 1st non-rich-dashboard shape (config/tabbed-forms) — provides 2nd validation data point for baseline-lift AD per Sprint 57.32 Day 4 §Matrix next-data-point note

---

## Sprint Goal

Land the **5th Phase-2 per-page verbatim-CSS re-point** on `/orchestrator` — a config/admin page with 6 tabbed sub-views (Config / System Prompt / Tools / Subagents / Budgets / Policies). This is the **1st non-rich-dashboard shape** in the Phase-2 epic (prior 4 apps were rich operator dashboards: `/overview` + `/chat-v2` + `/cost-dashboard` + `/sla-dashboard`). It therefore provides the **2nd validation data point** for `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (Sprint 57.31 NEW; 1st validation = Sprint 57.32 `/sla-dashboard` rich-dashboard shape).

`/orchestrator` is currently a Sprint 57.19 vintage page using **Tailwind class translation** of mockup styles + **local Badge/Card/Stat/RiskBadge primitives** + **shadcn Tabs**. Re-point = swap local primitives → mockup-ui imports + replace Tailwind translations of `.page-head` `.page-sub` `.route-pill` `.grid-stats` `.grid-main` `.row` `.col` `.input` `.select` with verbatim mockup CSS class consumption.

---

## Background

### Why Sprint 57.34 (this sprint)

Sprint 57.33 closed the page-bug-fix sweep (3 ⚪ crash routes flipped to ✅) and unblocked Phase-2 re-point candidacy for `/subagents`, `/memory`, `/verification`. The natural Phase-2 epic continues with the next un-re-pointed `🟡` route. Per Sprint 57.32 Day 4 §Matrix next-data-point note explicitly:

> "Next data point Sprint 57.33 likely /admin-tenants (NEW admin shape — tests whether below-band pattern is rich-dashboard-shape-specific or class-wide) OR /orchestrator (debug UI; different production-only widget density)."

Sprint 57.33 took a different path (crash-fix sweep). Sprint 57.34 picks `/orchestrator` because:

1. **1st non-rich-dashboard shape** — first concrete test of the bimodal hypothesis (resurrected as shape-driven variance). Prior 4 rich-dashboard apps showed ratios: 57.29≈1.0 / 57.30≈0.40 / 57.31≈0.35 / 57.32~0.40-0.55 (3-pt mean ≈0.40 below band excluding 57.29 anchor). If `/orchestrator` (config/tabbed-forms shape) lands in [0.85, 1.20] band, then prior below-band ratios were rich-dashboard-shape-specific. If `/orchestrator` also lands below band, then variance is class-wide and the 0.50 → 0.40 lift proposal becomes stronger.

2. **2nd validation data point for baseline-lift AD** — fulfills `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` 2-3 sprint validation window per `When to adjust` 3-sprint window rule.

3. **Existing visible drift** — Sprint 57.19 vintage code uses local Tailwind-translated primitives + shadcn Tabs. Mockup verbatim re-point cleans up the most-degraded production page in the OPERATIONS sub-section.

4. **No backend pairing required** — `/orchestrator` is fixture-driven per `AD-Orchestrator-Backend-Wire` Phase 58+ defer. Re-point is pure frontend.

### Mockup source mapping (Day 0 Prong 2 confirmed)

`reference/design-mockups/page-agents.jsx:1-340`:

| Mockup line range | Mockup component | Production location | Re-point work |
|-------------------|------------------|---------------------|--------------|
| L8-63 | `Orchestrator` main (page-head + grid-stats + Tabs) | OrchestratorPage.tsx top-level (Sprint 57.19 inline) | Re-point page-head + Stat row + Tabs invocation; swap local Badge → mockup-ui |
| L65-114 | `OrchestratorConfig` (Field-driven Core settings + Loop policy Card) | OrchestratorPage.tsx Config tab block | Re-point Card + Field wrappers + `.col` + `.row` |
| L116-173 | `OrchestratorPrompt` (textarea + token estimate row) | OrchestratorPage.tsx Prompt tab block | Re-point Card + `.col` + `.textarea` / `.kbar` |
| L175-205 | `OrchestratorTools` (18 tools chip grid) | OrchestratorPage.tsx Tools tab block | Re-point `.chip` chip layout + Badge tones per Tool kind |
| L207-237 | `OrchestratorSubagents` (6 subagents list) | OrchestratorPage.tsx Subagents tab block | Re-point row layout + Badge tone per mode |
| L239-272 | `OrchestratorBudgets` (numeric Field + cost summary Card) | OrchestratorPage.tsx Budgets tab block | Re-point Field + `.row` + Card |
| L274-(end) | `OrchestratorPolicies` (4 Switch toggles + HITL config) | OrchestratorPage.tsx Policies tab block | Re-point Switch + Field + Card |

### Scope boundaries

**IN scope**:
- `/orchestrator` 1 production file (`OrchestratorPage.tsx`) verbatim re-point — all 7 sub-component inline blocks (1 main + 6 tab content) re-pointed.
- Add `Tabs` + `Field` + `Switch` to `mockup-ui.tsx` (assuming they aren't already; promotes for future admin pages reuse). Inline keep as page-local fallback if scope-creeping mockup-ui too much.
- Drop local Badge / Card / Stat / RiskBadge / TONE_CLASS map — import from mockup-ui.
- Drop shadcn `Tabs` import — use mockup-ui Tabs (or page-local if not yet in mockup-ui).
- 22-route regression sweep before/after + `/orchestrator` fidelity verify.

**OUT of scope**:
- The 12 remaining 🟡 AppShellV2 routes (loop-debug / memory / state-inspector / governance / admin-tenants / tenant-settings / compaction / + the 3 newly-unblocked `/subagents`, `/verification` for Phase-2 candidacy, `/memory` STRUCTURAL Phase 58+).
- `AD-Orchestrator-Backend-Wire` Phase 58+ wiring (still fixture).
- Refactor of `frontend/src/components/ui/tabs.tsx` shadcn primitive (used elsewhere; out of this PR's scope unless mockup-ui Tabs supersedes it).

### Class baseline — `frontend-verbatim-css-repoint` 0.50 (5th application; **2nd validation** of lifted baseline)

HYBRID weighted blend for Sprint 57.34:

| Component | Class | Multiplier | Weight |
|-----------|-------|------------|--------|
| Day-0 三-prong + before-baseline | `audit-cycle` | 0.85 | ~10% |
| Page-head + grid-stats + Tabs structure (Day 1) | `frontend-verbatim-css-repoint` | 0.50 | ~15% |
| 6 tab content re-point (Day 2-3) | `frontend-verbatim-css-repoint` | 0.50 | ~50% |
| mockup-ui primitive promotions (Tabs / Field / Switch, if applicable) | `medium-frontend` | 0.65 | ~10% |
| 22-route sweep + fidelity verify | `frontend-verbatim-css-repoint` | 0.50 | ~5% |
| Closeout + retro + docs | `closeout` | 0.80 | ~10% |
| **HYBRID blended baseline** | | **≈ 0.55** | |

Bottom-up estimate:
- Day 0: ~1.5 hr
- Day 1 (main + stats + Tabs): ~1.5 hr
- Day 2 (Config + Prompt tabs): ~1.5 hr
- Day 3 (Tools + Subagents + Budgets + Policies tabs): ~2 hr
- Day 4 (sweep + closeout): ~1 hr
- **Total: ~7.5 hr**

Calibrated commit: ~3.75 hr (multiplier 0.50 anchored to class baseline; HYBRID ≈ 0.55 if weighted exactly).

Per `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` 2nd validation evaluation criteria:
- If ratio ≈ 0.85-1.20 (in band) → 0.50 lift CONFIRMED for non-rich-dashboard shape; bimodal hypothesis **resurrected as shape-driven** likely (prior 3-pt rich-dashboard mean ≈0.40 below band; non-rich ≈ in band). Propose split: `-rich-dashboard` 0.40 vs `-config-form` 0.50.
- If ratio ≈ 0.40-0.55 (lower band edge / below) → 0.50 still too generous regardless of shape; **class-wide variance** confirmed → propose 0.50 → 0.40 lift in Sprint 57.35 retro.
- If ratio ≈ 0.60-0.85 (lower-band) → in-band lower edge; ambiguous; KEEP 0.50 + accumulate 3rd-validation data point next sprint.
- If ratio > 1.20 → over-corrected; revert toward 0.55-0.60.

### What is preserved (NOT changed)

- All component logic / state / TanStack hooks (page is fixture-driven; no hooks currently).
- All `data-testid` attributes (component scaffold tests use them).
- `frontend/src/components/ui/tabs.tsx` shadcn primitive — kept; only orchestrator stops importing it (if mockup-ui Tabs supersedes).
- `routes.config.ts` orchestrator entry.
- All other Phase-1 / Phase-2 / Sprint 57.28 verbatim-CSS foundation work.
- `styles-mockup.css` (verbatim copy; foundation not touched).

### What gets changed (this sprint scope)

**Day 1 — Main + Stats + Tabs** (1 file edit, possibly +1 mockup-ui addition):
- `OrchestratorPage.tsx` — drop local Badge / RISK_TONE / TONE_CLASS map (~30 lines); import mockup-ui Badge / RiskBadge.
- Re-point page-head + grid-stats verbatim per `page-agents.jsx:11-41`.
- Re-point Tabs invocation — either use mockup-ui Tabs (if promoted) or keep shadcn Tabs with mockup-aligned `.tabs` CSS class wrapper.
- (Optionally) `mockup-ui.tsx` — add `Tabs` primitive matching mockup signature.

**Day 2 — Config + Prompt tabs** (1 file edit, possibly +Field / Switch mockup-ui additions):
- `OrchestratorConfig` block — Card + `.col` + Field-driven form (Display name + Primary model + Max turns + Token budget + Worktree disabled).
- `OrchestratorPrompt` block — Card + textarea + token-estimate `.kbar` row.
- (Optionally) `mockup-ui.tsx` — add `Field` primitive (label + help text wrapper).

**Day 3 — Tools + Subagents + Budgets + Policies tabs** (1 file edit):
- `OrchestratorTools` block — `.chip` chip grid for 18 tools + per-Tool Badge tones.
- `OrchestratorSubagents` block — 6 subagents row layout + Badge tone per mode.
- `OrchestratorBudgets` block — numeric Field + cost summary Card.
- `OrchestratorPolicies` block — Switch toggles + Field-driven HITL config.
- (Optionally) `mockup-ui.tsx` — add `Switch` primitive.

**Day 4 — Regression sweep + fidelity verify + closeout**.

---

## User Stories

### Group A — Day 0 plan + 三-prong + before-baseline (PRE-WORK)

- **US-A1** (Plan + Checklist): As the AI, I draft Sprint 57.34 plan + checklist mirroring Sprint 57.32 format before any code runs. Acceptance: this file + `sprint-57-34-checklist.md` exist with full content.
- **US-A2** (Day-0 三-prong): As the AI, I run path-verify + content-verify on plan-time assertions; key Prong-2 grep checks: confirm `OrchestratorPage.tsx` is 598 lines + Sprint 57.19 vintage; verify mockup `page-agents.jsx:1-340` `Orchestrator` + 6 sub-components present + line ranges match; confirm mockup-ui `Tabs`/`Field`/`Switch` absence (Prong 1) and decide promote-vs-page-local; verify `.row` `.col` `.chip` `.input` `.select` `.textarea` CSS classes presence in `styles-mockup.css` (Prong 2).
- **US-A3** (Before-baseline screenshots): Playwright capture 22 AppShellV2 routes via `route-sweep.mjs before` (OUT_DIR re-point to sprint-57-34-* dir) + `/orchestrator` per-tab states if feasible (Config / Prompt / Tools / Subagents / Budgets / Policies) before any code change.

### Group B — Main page-head + grid-stats + Tabs (Day 1)

- **US-B1** (page-head re-point): As an operator opening `/orchestrator`, the page-head matches mockup `page-agents.jsx:11-34` byte-for-byte (brand-mark + title "orchestrator-main" + version Badge + live Badge + page-sub + route-pill + 3 action Buttons). Acceptance: visual diff vs mockup ≤ 1 px; `data-testid="orchestrator-page-head"` preserved.
- **US-B2** (grid-stats 4-stat row): `.grid-stats` 4-stat row matches mockup L36-41 (Sessions / Avg loop turns / Subagent spawns / p95 session). Acceptance: 4 `Stat` cells render via mockup-ui Stat; layout matches mockup grid.
- **US-B3** (Tabs structure): 6-tab Tabs bar matches mockup L43-53 (Config / Prompt / Tools+18 / Subagents+6 / Budgets / Policies). Acceptance: Tabs use mockup-aligned class (`.tabs`); `count` badge displays for Tools (18) + Subagents (6); active tab state preserved (existing `useState`).

### Group C — Config + Prompt tabs (Day 2)

- **US-C1** (OrchestratorConfig re-point): Config tab matches mockup L65-114 — Core settings Card + Loop policy Card with Field-driven form (Display name input + Primary model select + Max turns Field + Token budget Field + Worktree disabled note). Acceptance: visual diff vs mockup ≤ 2 px; all 6 Field labels + help text verbatim from mockup.
- **US-C2** (OrchestratorPrompt re-point): Prompt tab matches mockup L116-173 — System prompt Card + textarea (5-row default) + token estimate `.kbar` row with 3 Badges (tokens count / cost estimate / version). Acceptance: textarea uses `.textarea` CSS class; `.kbar` row matches mockup.

### Group D — Tools + Subagents + Budgets + Policies tabs (Day 3)

- **US-D1** (OrchestratorTools re-point): Tools tab matches mockup L175-205 — 18-tool chip grid with per-Tool Badge tone (`tool`/`memory`/`thinking`/etc.) + Add-Tool Button. Acceptance: visual diff ≤ 2 px; 18 chips render; tone Badge mapping matches mockup conditional.
- **US-D2** (OrchestratorSubagents re-point): Subagents tab matches mockup L207-237 — 6 subagents row layout with mode Badge (`fork`/`as_tool`/`teammate`/`handoff`). Acceptance: visual diff ≤ 2 px; mode dispatch matches.
- **US-D3** (OrchestratorBudgets re-point): Budgets tab matches mockup L239-272 — numeric Field (Max turns / Max tokens / Per-turn ms cap) + cost summary Card. Acceptance: visual diff ≤ 2 px.
- **US-D4** (OrchestratorPolicies re-point): Policies tab matches mockup L274-(end) — 4+ Switch toggles + HITL config Card. Acceptance: visual diff ≤ 2 px; Switch state preserved via local component state.

### Group E — Regression sweep + fidelity verify + closeout (Day 4)

- **US-E1** (22-route sweep after): Run `route-sweep.mjs after`; confirm `/orchestrator` flips to ✅ PARITY; no other route regresses (esp. 3 routes unblocked by Sprint 57.33). Document delta in REPOINT-REPORT.md.
- **US-E2** (Per-tab sample): Click through 6 tabs; sample 3 screenshots from `after/` (Config + Tools + Policies recommended for shape variety).
- **US-E3** (5-gate verification): tsc + ESLint + Vitest + Vite build + check:mockup-fidelity all green. Vitest count = 456 baseline (no new specs unless any Vitest tests are added).
- **US-E4** (Closeout): Update progress.md Days 1-4 + retrospective.md Q1-Q7 + sprint-workflow.md §Matrix (`frontend-verbatim-css-repoint` 5th data point + class evaluation per `When to adjust`) + memory subfile + next-phase-candidates.md (close baseline-lift AD if 2nd-validation conclusive + add Sprint 57.34 Carryover).
- **US-E5** (Commit + PR + merge): Open PR; CI green; squash-merge.

---

## Technical Specifications

### Verbatim re-point method (unchanged from Sprint 57.29-32)

Per `docs/rules-on-demand/frontend-mockup-fidelity.md`:
1. Read mockup source `page-agents.jsx` for the relevant range.
2. Translate **logic** (React state / hooks / event handlers) but **copy CSS class names byte-for-byte** from mockup.
3. Use `(query.data.X ?? [])` defensive pattern from Sprint 57.33 if any TanStack data appears (orchestrator is fixture so likely N/A).
4. Hybrid Tailwind+inline color bridge pattern (Sprint 57.31 precedent) — preserve Vitest contract `text-warning`/`text-danger` Tailwind classes alongside inline `style={{ color: var(--*) }}` where mockup uses inline style.

### mockup-ui primitive promotion decisions

| Primitive | Current location | Decision |
|-----------|------------------|----------|
| Tabs | shadcn `@/components/ui/tabs` | **Promote** to mockup-ui — admin pages (governance / tenant-settings) will need it too; mockup uses `<Tabs value items onChange />` signature distinct from shadcn |
| Field | None (Sprint 57.19 inline) | **Promote** to mockup-ui — config-pattern wrapper; reused across all admin/config pages |
| Switch | None (Sprint 57.19 inline) | **Promote** to mockup-ui — form toggle element; same reuse trajectory |
| Badge / Card / Stat / RiskBadge | mockup-ui (existing) | **Import** — drop local duplicates |

Scope guard: if any of Tabs/Field/Switch promotion exceeds ~30 lines added to mockup-ui, defer to page-local + log AD for future promotion sprint.

### Class baseline 5th-data-point evaluation criteria (2nd validation of 0.50 lift)

Per `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (Sprint 57.31 NEW; 1st validation = Sprint 57.32 ratio ~0.40-0.55 lower band edge KEEP 0.50):

| Sprint 57.34 ratio range | Interpretation | Action |
|--------------------------|----------------|--------|
| ≈ 0.85-1.20 (in band) | 0.50 lift CONFIRMED for non-rich-dashboard shape; bimodal hypothesis resurrected as shape-driven | Propose split `-rich-dashboard` (0.40) vs `-config-form` (0.50) in Sprint 57.35 retro |
| ≈ 0.40-0.55 (lower band edge / below) | Class-wide variance regardless of shape | Propose 0.50 → 0.40 lift in Sprint 57.35 retro (consistent with Sprint 57.30+57.31+57.32 3-pt mean ≈0.40 trend) |
| ≈ 0.60-0.85 (lower-band) | Ambiguous | KEEP 0.50 + accumulate 3rd-validation data point next sprint |
| > 1.20 | Over-corrected | Revert toward 0.55-0.60 |

---

## File Change List

### NEW files (0)

### MODIFIED files (~2-3)

| # | Path | Change |
|---|------|--------|
| 1 | `frontend/src/pages/orchestrator/OrchestratorPage.tsx` | Full re-point: drop local primitives (~50 lines) + replace Tailwind translations with mockup CSS classes + import mockup-ui Badge/Card/Stat/RiskBadge (+ Tabs/Field/Switch); +MHist |
| 2 | `frontend/src/components/mockup-ui.tsx` | Add `Tabs` + `Field` + `Switch` primitives (~50-100 lines combined; scope guard ≤ ~30 lines each); +MHist |
| 3 | `frontend/scripts/route-sweep.mjs` | OUT_DIR re-point to sprint-57-34-orchestrator-repoint; +MHist |

### DELETED files (0)

### PRESERVED (not touched)

- `frontend/src/components/ui/tabs.tsx` (shadcn primitive — still used by other pages; this sprint only stops orchestrator from importing it)
- All other production pages + features.
- `styles-mockup.css` (verbatim foundation; sprint 57.28 protocol).
- Backend, schema, all other layers.

---

## Acceptance Criteria

1. **`/orchestrator` page renders all 6 tabs without regression** — Config / Prompt / Tools / Subagents / Budgets / Policies each show correct content; tab switching works.
2. **Mockup-fidelity visual parity ≤ 2 px on representative elements** — page-head + grid-stats + Tabs + per-tab Card layouts.
3. **22-route sweep `after` baseline shows `/orchestrator` ✅ PARITY**, 0 new regressions on other 21 routes.
4. **5 gates green** — tsc + ESLint + Vitest + Vite build + check:mockup-fidelity.
5. **Vitest count maintains** — 456 baseline preserved (no new specs required unless Vitest assertion contracts change).
6. **Docs synced** — REPOINT-REPORT.md (route status delta) + retrospective.md (Q1-Q7) + sprint-workflow.md §Matrix `frontend-verbatim-css-repoint` 5th data point + 2nd-validation class evaluation + memory subfile + MEMORY.md pointer + CLAUDE.md Current Sprint row + footer + next-phase-candidates.md (Sprint 57.34 Carryover; baseline-lift AD update).

---

## Deliverables

- [ ] Day 0: this plan + checklist + 三-prong findings + before-baseline 22-route screenshots
- [ ] Day 1: page-head + grid-stats + Tabs re-point commit
- [ ] Day 2: Config + Prompt tabs commit
- [ ] Day 3: Tools + Subagents + Budgets + Policies tabs commit
- [ ] Day 4: 22-route sweep after + REPOINT-REPORT + retro + docs sync + PR + CI green + merge

---

## Dependencies & Risks

### Dependencies

- Sprint 57.28 verbatim-CSS foundation in place (unchanged).
- `frontend/scripts/route-sweep.mjs` operational (5 consecutive sprints validated).
- mockup-ui.tsx primitive library (extended this sprint with Tabs/Field/Switch).

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tabs primitive promotion exceeds ~30 lines / introduces shadcn-bridge complexity | Medium | Medium — scope creep | Scope guard: defer to page-local + log AD for future promotion sprint |
| 6 tab content re-points uncover mockup-ui primitive gaps (e.g. Chip / Slider) | Medium | Low — re-use existing or add page-local; gap deferral to future sprint | Day 0 Prong 2 widen grep beyond tabs structure to per-tab content primitives |
| Sprint 57.19 page has TypeScript type assertions on local primitive props that fail when swapping to mockup-ui (different Tone type signature) | Medium | Low — tsc catches; fix at swap time | Allocate ~15-20 min budget for Type fix on Day 1 |
| Hybrid Tailwind+inline color bridge pattern (Sprint 57.31 precedent) might be needed for tone-coded elements (RiskBadge / pass/fail dots) | Low | Low — pattern known | Apply preemptively per Sprint 57.32 lesson |
| `/orchestrator` Vitest spec contract may assert local-Badge JSX shape | Low | Low — Vitest catches; fix during Day 1 | Run targeted `npm run test -- --run orchestrator` after Day 1 |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Class A (paths-filter)**: this PR touches only `frontend/src/**`, no `.github/workflows/**` — backend-ci paths-filter skip; visual-regression baseline workflow should not need regen (no styles-mockup.css change).
- **Class C (singleton across test event loops)**: N/A (frontend Vitest only).

---

## Workload

Bottom-up est ~7.5 hr → calibrated commit ~3.75 hr (multiplier 0.50; class baseline 5th application; 2nd validation of lifted baseline).

Hour distribution:

| Day | Bottom-up | Calibrated | Tasks |
|-----|-----------|------------|-------|
| Day 0 | 1.5 hr | 0.7 hr | Plan + Checklist + 三-prong + before-baseline 22-route sweep |
| Day 1 | 1.5 hr | 0.75 hr | US-B1+B2+B3 — main page-head + grid-stats + Tabs structure |
| Day 2 | 1.5 hr | 0.75 hr | US-C1+C2 — Config + Prompt tabs |
| Day 3 | 2 hr | 1.0 hr | US-D1+D2+D3+D4 — Tools + Subagents + Budgets + Policies tabs |
| Day 4 | 1 hr | 0.5 hr | US-E1-E5 — 22-route sweep after + REPOINT-REPORT + retro + docs + PR/merge |
| **Total** | **~7.5 hr** | **~3.75 hr** | |

---

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + before-baseline

1. Write plan (this file) + checklist
2. 三-prong:
   - **Prong 1** path-verify: confirm `OrchestratorPage.tsx` exists + `page-agents.jsx` mockup exists + mockup-ui.tsx exists
   - **Prong 2** content-verify: re-grep mockup `Orchestrator` + 6 sub-components line ranges; confirm mockup-ui current exports (`Tabs`/`Field`/`Switch` absent); confirm `.row`/`.col`/`.chip` CSS classes in styles-mockup.css
   - **Prong 3** schema-verify: N/A (frontend-only)
3. Catalog drift findings in progress.md Day 0 entry
4. Run `route-sweep.mjs before` (OUT_DIR = sprint-57-34-orchestrator-repoint); confirm `/orchestrator` baseline status

### Day 1 — Main + Stats + Tabs

1. Decide Tabs promote-vs-keep
2. Edit `mockup-ui.tsx` add Tabs (if promote)
3. Edit `OrchestratorPage.tsx` — drop local Badge / TONE_CLASS / RiskBadge / RISK_TONE; import mockup-ui equivalents
4. Re-point page-head + grid-stats verbatim
5. Re-point Tabs invocation
6. Verify tsc + ESLint + Vitest targeted pass
7. Commit: `feat(frontend, sprint-57-34): /orchestrator main + grid-stats + Tabs verbatim re-point (US-B1+B2+B3)`

### Day 2 — Config + Prompt tabs

1. Decide Field promote-vs-keep
2. Edit mockup-ui.tsx add Field (if promote)
3. Re-point OrchestratorConfig + OrchestratorPrompt tab blocks
4. tsc + ESLint pass
5. Commit: `feat(frontend, sprint-57-34): /orchestrator Config + Prompt tabs verbatim re-point (US-C1+C2)`

### Day 3 — Tools + Subagents + Budgets + Policies

1. Decide Switch promote-vs-keep
2. Edit mockup-ui.tsx add Switch (if promote)
3. Re-point 4 remaining tab blocks
4. Full Vitest run (verify 456 baseline maintained)
5. Commit: `feat(frontend, sprint-57-34): /orchestrator Tools + Subagents + Budgets + Policies tabs verbatim re-point (US-D1+D2+D3+D4)`

### Day 4 — Sweep + closeout

1. Run `route-sweep.mjs after`; sample `/orchestrator` PARITY confirmation + verify other 21 routes unchanged
2. Write REPOINT-REPORT.md (delta narrative)
3. Run 5 gates final
4. Update retrospective.md Q1-Q7 (esp. Q2 calibration with 5th-data-point + 2nd-validation evaluation)
5. Update sprint-workflow.md §Scope-class multiplier matrix — `frontend-verbatim-css-repoint` 5th data point added + MHist
6. Update memory subfile + MEMORY.md pointer + CLAUDE.md Current Sprint + next-phase-candidates.md (Sprint 57.34 Carryover; baseline-lift AD update)
7. Commit: `chore(sprint-57-34): Day 4 closeout — REPOINT-REPORT + retro + memory + docs sync`
8. Push branch + open PR + wait CI green + squash-merge

---

## Related

- Sprint 57.29-32 4 prior Phase-2 re-point retrospectives — rich-dashboard ratios 1.0 / 0.40 / 0.35 / 0.40-0.55
- Sprint 57.32 Day 4 §Matrix next-data-point note (recommends /orchestrator or /admin-tenants for non-rich-dashboard shape)
- Sprint 57.31 baseline-lift `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (Sprint 57.34 = 2nd validation data point)
- Sprint 57.19 (`/orchestrator` initial port — Sprint 57.19 vintage code; predates verbatim-CSS protocol)
- `claudedocs/1-planning/next-phase-candidates.md` Phase-2 backlog
- `docs/rules-on-demand/frontend-mockup-fidelity.md` (verbatim-CSS method; unchanged)
- `reference/design-mockups/page-agents.jsx:1-340` (canonical mockup source)
- `frontend/src/components/mockup-ui.tsx` (primitive library; extended this sprint)
