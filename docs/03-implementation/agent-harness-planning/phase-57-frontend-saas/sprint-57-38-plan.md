# Sprint 57.38 — AD-ClassSplit-Decision-And-Subagents-Repoint-And-FullBleed-Audit

**Phase**: 57 (Frontend SaaS)
**Sprint id**: 57.38
**Drafted**: 2026-05-24 (Day 0)
**Branch**: `feature/sprint-57-38-class-split-subagents-fullbleed-audit`
**Class**: 3-domain batched HYBRID — `frontend-verbatim-css-repoint -with-extras` (Domain B; ~~1st application of `-simple` baseline~~ **5th application of `-with-extras` per Day 0 D5 reclassification**) + sprint-meta (Domain A) + sprint-meta + micro-audit (Domain C)
**Mirror template**: Sprint 57.37 plan (2-domain batched precedent; § structure 0-9, 10 main sections)

**Day 0 amend note (2026-05-24)**: Plan §1.2 / §1.4 / §1.5 / §3.3 / §4 / §5 / §8 amended per progress.md Day 0 drift findings D1-D5 (user confirmed Option A 2026-05-24). Original draft assumed Domain B was a `-simple` 1-file ~3-hr CSS swap; Day 0 Prong 1+2 grep revealed production is a 402-line Tailwind-utility-heavy `SubagentsPage.tsx` mapping to mockup `page-agents.jsx:311+ SubagentsRegistry + SubagentDetail` (not `page-platform.jsx SubagentsPage`) with 4-mode KPI grid + 8-row table + 2-col grid `1.4fr 1fr` + inner Tabs + oklch-heavy inline literals. Re-classified to `-with-extras` 0.65 baseline. See progress.md Day 0 entry for full drift catalogue.

---

## 0. Sprint Goal

Three-domain batched sprint: (A) resolve the 3-consecutive-above-band lift trigger from Sprint 57.37 via formal class-split decision, (B) first application of the resulting split baseline on `/subagents` simple-shape Phase-2 re-point, and (C) FIX-010 follow-up micro-audit to confirm no other `fullBleed`-class pages are missing the prop.

### Domain A — `frontend-verbatim-css-repoint` Class-Split Decision (meta retro)

Resolve `AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal` (Sprint 57.37 NEW carryover) by choosing between:

- **Option 1 (baseline lift)**: 0.50 → 0.60 class-wide
- **Option 2 (recommended)**: class split into `-simple` (0.50: pure 1-file CSS swap, no extras; 57.34 baseline) vs `-with-extras` (0.65: + any of {AP-2 banner, dual-mount, playback/filter/inspector widgets, verbatim oklch-heavy port with HEX_OKLCH_BASELINE bumps, multi-file batched > 3 files}; 57.35/57.36/57.37B mean 1.48)

Update `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix accordingly. Close 3 carryover ADs (`class-split-proposal`, `multi-dimensional-variance-watch`, `baseline-lift`).

### Domain B — `/subagents` Phase-2 Verbatim CSS Re-Point (5th app of `-with-extras` baseline per Day 0 D5)

Per Sprint 57.33 (`AD-Page-Bug-Fix-Sweep`) unblock list (next-phase-candidates.md §Sprint 57.33), `/subagents` is now stable (crash bug fixed) and ready for Phase-2 re-point. Real production source: **`frontend/src/pages/subagents/SubagentsPage.tsx`** (single 402-line file; `frontend/src/pages/subagents/index.tsx` is a 1-line re-export wrapper). Currently uses Sprint 57.19 vintage Tailwind utility tokens (`rounded-[12px] border border-border bg-card text-card-foreground`, `text-muted-foreground`, `bg-muted/30`); swap to mockup verbatim CSS classes from **`reference/design-mockups/page-agents.jsx:300+ SubagentsRegistry + SubagentDetail`**. Production includes:

- 4-mode KPI grid (fork / as_tool / teammate / handoff) with mockup `.grid-3` + `.stat` + colored `borderLeft`
- 2-col grid `1.4fr 1fr` (list table + detail card)
- Mockup `.table` with 8-row registry fixture
- Inner Tabs (spec / budget / tools / stats) per detail panel
- Inline `oklch(from var(--primary) l c h / 0.10)` literals (selected row highlight)

**Empirically validate Domain A's chosen `-with-extras` 0.65 baseline as a 5th data point** (after 57.35/36/37B mean 1.48). This is the first `-with-extras` candidate **without** AP-2 BackendGapBanner / dual-mount — instead the extras come from KPI grid + 2-col layout + Tabs + 8-row table + oklch literals. Tests whether the `-with-extras` class covers this distinct shape.

### Domain C — `AD-FullBleed-Pages-Audit` (FIX-010 follow-up micro)

Grep `frontend/src/pages/**/index.tsx` for `<AppShellV2` mounts and cross-check against mockup full-viewport layout classes (`loop-canvas` / `chat-shell` / `state-shell` / similar — to be enumerated by Day 0 prong). Fix any missing `fullBleed` props in-sprint (1-line each). Tracked candidates (per FIX-010 record §Follow-up Audit Candidate): `/state-inspector`, `/orchestrator`, `/memory`.

---

## 1. Background

### 1.1 Why 3-domain batched

Sprint 57.37 demonstrated the 2-domain batched model works when domains share Day 0/3.5/4 overhead and only diverge at Day 1-3 (`56.36→57.37` continuity: 4.5 hr wall-clock for 2 domains). Sprint 57.38 batches 3 domains because **all three share the Day 0 setup + Day 2.5 sweep + Day 3 closeout cost** but Domain A is meta-only (no code days, just decision + matrix update lives in Day 0 + Day 3 closeout) and Domain C is micro-audit (1-2 hr Day 0 + Day 2 fixes). Effective shape ≈ 1.2-domain Day-1-2 ship cost.

Domain B is **first empirical test of the new split baseline** so it must run in the same sprint as Domain A — otherwise Domain A's matrix update lacks a co-validating data point.

### 1.2 Mockup source mapping (Day 0 Prong 2 to confirm)

#### Domain B (`/subagents`) — `reference/design-mockups/page-agents.jsx:300+ SubagentsRegistry + SubagentDetail` (Day 0 D4 amend)

- Block: `SubagentsRegistry` + `SubagentDetail` at `reference/design-mockups/page-agents.jsx:300-450` (confirmed by Day 0 Prong 1 grep)
- Production source: **`frontend/src/pages/subagents/SubagentsPage.tsx` single 402-line file** (Day 0 D1 amend; `index.tsx` is 1-line re-export wrapper; no `SubagentRegistryView.tsx`; no `frontend/src/features/subagents/components/` dir)
- Visual elements confirmed (mockup `page-agents.jsx:311-420`):
  1. `.page-head` + `.page-title` "Subagent Registry" + `.page-sub` route-pill + count
  2. `.page-actions` Sync from repo / New subagent buttons
  3. `.grid-3` 4-mode KPI strip with `borderLeft: 3px solid var(--thinking|tool|memory|info)` and `.stat-label` / `.stat-value` / `.subtle`
  4. 2-col grid `display: grid; grid-template-columns: 1.4fr 1fr; gap: 14px`
  5. Left card `Card title="Subagents"` with mockup `.table` 8-row registry fixture
  6. Right card `Card title=<selected role>` with inner Tabs (spec / budget / tools / stats)
  7. Selected row highlight via inline `oklch(from var(--primary) l c h / 0.10)`

#### Domain C (`fullBleed` audit) — `reference/design-mockups/page-*.jsx`

- Method: grep `reference/design-mockups/*.jsx` for full-viewport layout class names (`loop-canvas`, `chat-shell`, `state-shell`, etc.) AND grep `reference/design-mockups/styles.css` for `height: 100%` + `overflow: hidden` block selectors → enumerate fullbleed-class layout candidates; cross-reference production page wrappers.

### 1.3 Scope boundaries

**In scope**:
- Domain A: retro decision narrative + matrix update + 3 AD closures
- Domain B: `/subagents` verbatim CSS swap (production code) + spec adapt + 22-route sweep slot
- Domain C: enumerate fullbleed candidates + 1-line fix per missing prop + spec stability check

**Out of scope** (defer Phase 58+ per next-phase-candidates.md):
- `/memory` STRUCTURAL rebuild (~25-30 hr; needs backend pairing)
- `/tenant-settings` STRUCTURAL (Phase 58+)
- Backend API changes
- `AD-Tabs-Migration-To-MockupUi` (low priority; out-of-scope per 57.34 carryover)
- `AD-Visual-Regression-Shell-Spec-Hardening` (FIX-010 follow-up; deferred to dedicated test-hardening sprint)

### 1.4 Class baselines — HYBRID blend across 3 domains (Day 0 D5 amend)

| Domain | Class | Baseline | Weight (est) |
|--------|-------|----------|--------------|
| A — class-split decision | `sprint-meta` | 0.85 | ~20% |
| B — `/subagents` re-point | `frontend-verbatim-css-repoint -with-extras` (5th application; Day 0 D5 reclass) | 0.65 (assumed if Option 2 chosen; matches 57.35/36/37B 4-pt evidence mean 1.48) | ~65% |
| C — fullbleed audit | `sprint-meta + micro-fix` | 0.65 (audit-cycle + mechanical 1-line blend) | ~15% |

**HYBRID blended baseline**: 0.85×0.20 + 0.65×0.65 + 0.65×0.15 = **~0.69** (was 0.62 pre-amend)

### 1.5 3-domain calibration evaluation criteria

#### Domain A — `sprint-meta` (decision sprint; no commit code)
- Actual: ~1 hr decision narrative + matrix update + AD closure markdown edits
- Bottom-up: ~1.5 hr
- Expected ratio: `actual / committed ≈ 1.0` (meta work has low variance)

#### Domain B — `frontend-verbatim-css-repoint -with-extras` (5th application per Day 0 D5; validates 0.65 baseline against distinct shape — KPI grid + 2-col + Tabs + 8-row table + oklch literals; no AP-2 / dual-mount as in 57.35-37B)
- This sprint adds the **5th `-with-extras` data point** (extending 57.35/36/37B mean 1.48 evidence)
- Per `When to adjust` 3-sprint window rule: 4 existing data points + this 1 = 5; if ratio continues > 1.20 → propose further refinement (e.g., split `-with-extras` further into AP-2-bearing vs layout-rich sub-sub-classes)
- Sub-class evaluation criteria:
  - **PASS**: ratio actual/committed in [0.85, 1.20] band → 0.65 baseline validates against distinct extras shape (KPI grid + 2-col + Tabs + table is well-modeled by `-with-extras`)
  - **ABOVE band ≥ 5th consecutive**: log new AD `AD-Sprint-Plan-frontend-verbatim-css-repoint-with-extras-sub-classify`
  - **In band**: confirms `-with-extras` baseline is correctly tuned for this shape diversity

#### Domain C — `sprint-meta + micro-fix`
- Per-fullbleed-fix unit cost ~10-15 min (1-line prop + MHist + Vitest run if affected); audit method cost ~30-45 min (grep + cross-ref + verdict)
- Expected ratio: `actual / committed ≈ 0.8-1.1` (audit + mechanical fix blend stable)

---

## 2. User Stories

### Domain A — class-split decision

#### US-A1 — Choose split option (1 or 2) with explicit rationale
As the calibration discipline owner, I want a formal decision recorded in retrospective.md Q2 + the matrix updated, so that Sprint 57.39+ has unambiguous baseline guidance.

#### US-A2 — Close 3 carryover ADs
As the calibration history reader, I want `AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal` + `multi-dimensional-variance-watch` + `baseline-lift` all marked CLOSED in next-phase-candidates.md, so the open AD pool is accurate.

### Domain B — /subagents re-point

#### US-B1 — Verbatim mockup CSS classes adopted
As the operator, I want `/subagents` visual to match mockup `localhost:8080/#subagents` per the Sprint 57.33 unblock list, so the production page uses verbatim CSS classes instead of HSL-translated Tailwind.

#### US-B2 — Sprint 57.33 defensive-guard behavior preserved
As a current `/subagents` user, the crash-fix `(query.data.items ?? [])` defensive guards from Sprint 57.33 must NOT regress — production must continue to render empty state when API returns null/undefined.

### Domain C — fullbleed audit

#### US-C1 — Enumerate all fullbleed-class layout candidates
As the layout-class disciplinarian, I want a complete list of mockup full-viewport layout selectors (`loop-canvas` etc.) cross-referenced against `frontend/src/pages/**/index.tsx` mounts, so missing `fullBleed` props are visible.

#### US-C2 — Fix every found prop-drop in-sprint (or formally defer)
For each fullbleed-class page found missing the prop, apply 1-line fix OR formally log a deferral reason in retrospective.md.

### Cross-domain

#### US-D1 — Vitest baseline preserved (≥464/464)
After all sprint changes, Vitest must remain green at or above the 464 baseline (Sprint 57.37 close). Domain B may add 1-2 NEW defensive specs (parallel to Sprint 57.33 +4 specs pattern). Domain C may add 0-2 specs (per fix).

#### US-D2 — 22-route sweep clean
22-route Playwright sweep `before` vs `after`: 0 unintended regressions; only expected diffs (`/subagents` Domain B + any Domain C fixed routes).

---

## 3. Technical Specifications

### 3.1 Domain A: Decision matrix

| Criterion | Option 1 (lift 0.60 class-wide) | Option 2 (split -simple/with-extras) |
|-----------|----------------------------------|--------------------------------------|
| Simplicity | High (1 baseline) | Medium (2 baselines + decision rule per sprint) |
| In-band fit for 57.34 (1-file, no extras) | Over-corrects (0.60 baseline implies committed ~ bottom-up × 0.60; 57.34 actual/committed was 1.0 at 0.50) → expected new ratio ~0.83, lower-band edge | Stays at 0.50 → in-band middle |
| In-band fit for 57.35-37B (with extras) | Marginal (0.60 vs observed 1.33-1.7 → actual / new committed ~1.1-1.4, top-of-band-to-above) | 0.65 → expected ratio ~1.0 in-band middle |
| Future sprint classification cost | None | Per-sprint decision (rules table needed) |
| Empirical fit | Mismatch — simple-shape over-corrected, extras-shape still drift-prone | Match — each sub-class targets its own observed mean |

**Recommended: Option 2** — see retrospective.md §Q2 for full rationale; matrix updated in §3.1.

### 3.2 Domain A: Matrix update edit shape

Edit `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix row `frontend-verbatim-css-repoint`:

- Split into 2 rows (or keep single row with `Baseline` cell showing branching rule)
- `-simple` row: baseline 0.50; in-band evidence 57.34
- `-with-extras` row: baseline 0.65; in-band evidence 57.35-57.37B mean
- `When to adjust` clause stays applicable per sub-class

### 3.3 Domain B: `/subagents` CSS swap (Day 0 D1/D3/D4 amend)

Production file confirmed by Day 0 Prong 1:
- **`frontend/src/pages/subagents/SubagentsPage.tsx`** single 402-line file (inline primitives + `TONE_CLASS` lookup + `useSubagents` + `useTranslation`)

Swap pattern (mirrors Sprint 57.34 `/orchestrator` precedent):
- Tailwind utility classes → mockup verbatim CSS class names per §1.2 visual elements 1-7
- Inline `style={{ color: var(--xxx) }}` literals preserved verbatim from mockup (per `AD-Inline-Style-Rule-vs-Verbatim-Method`; file-level `eslint-disable no-restricted-syntax` with rationale comment expected)
- Preserve Sprint 57.33 defensive **`?.length` optional chain on items** (Day 0 D3 amend; original plan said `?? []` but real pattern is `?.`); Day 1 spec stability check: empty state still renders when items is null/undefined
- `HEX_OKLCH_BASELINE` envelope: +5-8 expected bump (oklch literals from selected row highlight + KPI mode-color borderLeft); current baseline 50 → target ≤58 after Domain B

### 3.4 Domain C: fullbleed audit method

1. Day 0 grep step:
   - `grep -n "height: 100%" reference/design-mockups/styles.css | grep -B1 "{"` — find layout-class selectors
   - `grep -l "className=\"loop-canvas\|chat-shell\|state-shell\|other-fullbleed-classes" reference/design-mockups/*.jsx` — find which mockup pages use them
   - `grep -rn "AppShellV2" frontend/src/pages/**/index.tsx` — enumerate production page wrappers (with/without `fullBleed`)
2. Cross-ref: for each production page mount, decide expected `fullBleed` value (Y/N) by examining the corresponding mockup page block's outer wrapper class
3. Per missing prop: 1-line edit (mirrors FIX-010 shape); MHist entry; record candidate in audit checklist row

---

## 4. File Change List

### Domain A (meta — no production code)
- `.claude/rules/sprint-workflow.md` — §Scope-class multiplier matrix `frontend-verbatim-css-repoint` row split (Option 2) or value lift (Option 1)
- `claudedocs/1-planning/next-phase-candidates.md` — close 3 ADs + add Sprint 57.38 carryover section
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-38/retrospective.md` — full Q1-Q7 retro + Q2 decision rationale

### Domain B (`/subagents` re-point) — Day 0 D1/D2 amend

- **`frontend/src/pages/subagents/SubagentsPage.tsx`** — single 402-line file; verbatim CSS swap (Tailwind utility → mockup verbatim per §3.3)
- ~~`frontend/src/pages/subagents/index.tsx`~~ — 1-line re-export wrapper; NOT touched
- ~~`frontend/src/features/subagents/components/SubagentRegistryView.tsx`~~ — does NOT exist (Day 0 D1)
- ~~`frontend/src/features/subagents/components/__tests__/*.test.tsx`~~ — does NOT exist (Day 0 D2); 0 specs to adapt
- **Optional NEW spec**: `frontend/src/pages/subagents/__tests__/SubagentsPage.test.tsx` (parallel to Sprint 57.33 +4 defensive specs pattern; verify empty state when items null/undefined; +1 spec budget if added)
- `frontend/scripts/check-mockup-fidelity.mjs` — `HEX_OKLCH_BASELINE` bump expected +5-8 (per §3.3); current 50 → target ≤58

### Domain C (fullbleed audit)
- `frontend/src/pages/<found>/index.tsx` — 1-line `fullBleed` prop per missing site (count TBD by Day 0 audit; expected 0-3 sites)
- `claudedocs/4-changes/bug-fixes/FIX-011-XXX.md` per fix site (if any)
- `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/<affected>.png` — visual baseline regen if needed (mirrors FIX-010 fix-cycle)

### Cross-domain
- `frontend/scripts/route-sweep.mjs` — re-point `OUT_DIR` to `sprint-57-38-class-split-subagents-fullbleed-audit`
- `memory/project_phase57_38_*.md` — sprint subfile (3-domain pointer)
- `memory/MEMORY.md` — quality pointer (~300 char)
- Sprint plan + checklist + progress.md + retrospective.md (this file + checklist + execution files)

---

## 5. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| AC1 | Domain A decision formally recorded with rationale | retrospective.md Q2 narrative + matrix edit diff visible |
| AC2 | 3 carryover ADs CLOSED in next-phase-candidates.md | grep `CLOSED.*class-split-proposal\|multi-dimensional-variance-watch\|baseline-lift` returns 3 |
| AC3 | `/subagents` visual matches mockup `localhost:8080/#subagents` | Day 2.5 fidelity verdict PARITY; route-sweep before/after diff localised to `/subagents` |
| AC4 | Sprint 57.33 defensive `?.length` optional chain preserved (Day 0 D3 amend; was `?? []` pre-amend) | grep `\?\.length\|items\?\.\|data\?\.` in `SubagentsPage.tsx` returns ≥1 site |
| AC5 | Domain C: fullbleed audit produces enumerated list + per-site verdict | retrospective.md §Domain C table |
| AC6 | Vitest ≥464/464 | `npm test -- --reporter=dot` last line |
| AC7 | 22-route sweep 0 unintended regressions | progress.md Day 2.5 entry: 22 routes verdict summary |
| AC8 | mockup-fidelity guard preserved | `node frontend/scripts/check-mockup-fidelity.mjs` exit 0 |
| AC9 | Plan-vs-repo Day 0 三-prong with ≥1 drift findings catalogued (if any) | progress.md Day 0 "Drift findings" header |

---

## 6. Deliverables

- [ ] Domain A: `class-split-proposal` decision (Option 1 or 2) recorded
- [ ] Domain A: `.claude/rules/sprint-workflow.md` matrix row edit committed
- [ ] Domain A: 3 carryover ADs closed in next-phase-candidates.md
- [ ] Domain B: `/subagents` verbatim CSS re-point shipped
- [ ] Domain B: Vitest spec adapted (or D-DAY3-1 surprise — no update needed)
- [ ] Domain C: fullbleed audit enumerated + verdict per candidate
- [ ] Domain C: any missing `fullBleed` props fixed in-sprint (or formal deferral)
- [ ] 22-route sweep before/after diff reviewed; verdict logged
- [ ] retrospective.md Q1-Q7 with calibration ratios computed (3 domains)
- [ ] Memory subfile + MEMORY.md pointer entry per Sprint Closeout Update Policy
- [ ] PR opened against main; CI green; squash-merge ready

---

## 7. Risks & Mitigations

| Risk | Class | Mitigation |
|------|-------|-----------|
| Domain B test class-name brittleness | Test maintenance | Per Sprint 57.37 D-DAY3-1 convention candidate: prefer text/role/data-testid (check Day 0 Prong 2 if existing spec uses them) |
| Domain B introduces visual-regression baseline drift on `app-shell.png` | Visual-regression baseline (Risk Class — recurring from FIX-010 fix-cycle) | Same AD-CI-7 manual PR fallback; baseline regen workflow_dispatch on feature branch |
| Domain C audit finds many missing props → in-sprint scope blowout | Audit scope creep | Hard cap: if > 3 sites found, fix top 3 in-sprint + log others as carryover; ratio re-eval per actual count |
| Domain B `/subagents` Sprint 57.33 defensive guards regress | Functional regression | Day 0 Prong 2 grep both `?? []` sites before edit; spec verifies empty state still renders |
| Day 0 Prong 1 mockup source line range search returns nothing | Plan-vs-repo drift (Sprint 53.7 D4-D12 class) | Drift catalogue + plan §1.2 amend in progress.md; scope confirm with user before Day 1 |
| `HEX_OKLCH_BASELINE` bump conflict if Domain B introduces token-relative oklch | Mockup-fidelity guard | Mirrors Sprint 57.29-37 precedent; expected +0-3 within 50 → 53 envelope |
| Risk Class A: paths-filter vs `required_status_checks` | CI infra (recurring per sprint-workflow §Common Risk Classes A) | Touch `.github/workflows/backend-ci.yml` header comment if backend-ci skips on PR |

---

## 8. Workload (Day 0 D5 amend)

**Bottom-up est** ~13 hr → **calibrated commit ~9 hr** (multiplier ~0.69 HYBRID blend per §1.4)

### Day-by-day allocation

| Day | Focus | Bottom-up | Calibrated |
|-----|-------|-----------|------------|
| Day 0 | Plan/checklist drafted (mirror 57.37) + 三-prong (5 drifts caught + amend) + before baseline | ~3 hr | ~2 hr |
| Day 1 | Domain B `/subagents` verbatim CSS re-point (agent-delegated; 5th consecutive code-implementer per Sprint 57.34-37 pattern). **402-line file with KPI grid + 2-col + Tabs + 8-row table + oklch literals** per D5 amend; bottom-up ~5-6 hr | ~5.5 hr | ~3.6 hr |
| Day 2 | Optional NEW SubagentsPage spec (+1 spec) + Domain C audit finalize + any 1-line fullbleed fixes (cap 3) | ~2 hr | ~1.4 hr |
| Day 2.5 | Capture after baseline + 22-route sweep diff review + fidelity verdict (Domain B + any Domain C fixed routes) | ~1.5 hr | ~1.0 hr |
| Day 3 (closeout) | Retro Q1-Q7 + Domain A decision finalised + 3-class calibration matrix update + memory subfile + push + PR | ~1.5 hr | ~1.0 hr |

---

## 9. Dependencies

- Sprint 57.37 merged main `16e755a6` (closed by PR #173) — calibration data points (8 total / 4 non-rich)
- FIX-010 merged main `50420a07` (closed by PR #175) — fullBleed prop precedent + AppShellV2 prop signature
- Sprint 57.33 merged main — `/subagents` crash-fix baseline (PRE-CONDITION for Domain B viability)
- next-phase-candidates.md authority for 3 carryover ADs being closed (currently OPEN status)
- mockup source: `reference/design-mockups/page-platform.jsx` (`SubagentsPage` block — Day 0 Prong 1)
- 4-layer mockup-fidelity protocol (Sprint 57.28 foundation) intact: `styles-mockup.css` byte-identical; tailwind bridge; theme toggle; CI guard

---

**Status**: drafted Day 0; ready for Day 0 三-prong execution (see checklist §0.2-0.5)

**Modification History**:
- 2026-05-24: Initial draft Day 0 (Sprint 57.38)
