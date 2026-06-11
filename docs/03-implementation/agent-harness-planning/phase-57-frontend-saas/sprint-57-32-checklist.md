# Sprint 57.32 — Checklist

> Plan: [`sprint-57-32-plan.md`](./sprint-57-32-plan.md)
>
> AD-Sla-Dashboard-Verbatim-Repoint — 4th Phase-2 per-page verbatim-CSS re-point + 1st validation of lifted 0.50 baseline.
>
> Day 0-4; mirror 57.31 day structure (smaller scope; clean mockup mapping = 0 production-only widgets).

---

## Day 0 — Plan + Checklist + 三-prong + before-baseline

### 0.1 Plan + Checklist drafted

- [x] **Plan file** `sprint-57-32-plan.md` exists with 10 sections
- [x] **Checklist file** (this file) drafted mirroring Sprint 57.31 format

### 0.2 Day-0 三-prong verify

- [x] **Prong 1 — Path verify** — Glob batched: 7 production paths all present (1 page + 6 components); 3 NEW paths correctly absent. 0 path drift.
- [x] **Prong 2 — Content verify** — 4 findings catalogued in progress.md (D1 mockup SlaPage L32-198 + D2 R1-mitigated `.btn-group`/`.kbar` both present in styles-mockup.css L461/L1115 + D3 R3-mitigated LatencyChart SVG body aligned with mockup canonical + D4 7 component files structurally intact); all 🟢 GREEN
- [x] **Prong 3 — Schema verify**: N/A (frontend-only)
- [x] **Prong 4 — Visual baseline scope** — only `/sla-dashboard` baseline likely needs regen Day 4; same AD-CI-7 ff-merge workaround as 57.31

### 0.3 Before-baseline screenshot capture

- [x] **22 AppShellV2 + AuthShell + Home route screenshots** via `route-sweep.mjs before` mode — 22/22 ✓ captured to `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-32/artifacts/sla-dashboard-repoint/screenshots/before/`; route-sweep.mjs OUT_DIR re-pointed + MHist entry added
- [x] **sla-dashboard extras** — **skipped**: regular sweep capture suffices (no additional stateful UI requiring separate snapshots like cost-dashboard MonthPicker / table anomaly)
- [x] **Day 0 commit** — `acab0292` on `feature/sprint-57-32-sla-dashboard-repoint` (includes 57.31 checklist closeout cosmetic catchup as housekeeping)

---

## Day 1 — Group B (page-head + TimeRangeTabs + KPI row)

### 1.1 US-B1 — page-head + TimeRangeTabs verbatim re-point — ✅ done

- [x] **Read mockup** `page-admin.jsx:34-52` (page-head + .btn-group time-range tabs)
- [x] **Re-point** `pages/sla-dashboard/index.tsx` — dropped `pageTitle="SLA Dashboard"` prop; page-head now lives verbatim inside SLAOverview
- [x] **Re-point** `TimeRangeTabs.tsx` — translated Tailwind container + per-button classes → mockup `.btn-group` + mockup-ui `Button` (variant ghost/outline; size sm); role="tablist" + aria-selected + data-testid preserved
- [x] **Header MHist** updated (1-line per Sprint 55.3 char budget)
- [x] **Verify**: Playwright shot `day1-sla-dashboard-fold.png` shows new page-head matches mockup L34-52 (PARITY visual)

### 1.2 US-B2 — SLAOverview grid-stats verbatim — ✅ done

- [x] **Read mockup** `page-admin.jsx:54-59` (4-stat grid-stats KPI row)
- [x] **Re-point** `SLAOverview.tsx` — added `layoutStyles` const (mirror Sprint 57.31 pattern: page / gridStats / gridMainRow1 / gridMainRow2 / monthPickerRow / monthPickerNote / noTenant); swapped imports `PageHead`/`StatCard`/`CardShell` → `Card`/`Stat`/`Spark`/`Badge`/`Button` from mockup-ui; replaced wrapper components with inline `.page-head` + `style={layoutStyles.gridStats}` + `style={layoutStyles.gridMainRow1/Row2}` + `.kbar` legend Badges
- [x] **Header MHist** updated
- [x] **Verify**: Playwright shot `day1-sla-dashboard-fold.png` confirms above-the-fold parity (page-head + KPI row + LatencyChart + SLOStatus)

### 1.3 Day 1 mini-verify — ✅ done

- [x] All Day 1 files lint-clean (ESLint exit 0)
- [x] tsc strict — 0 new errors (TS6310 carryover pre-existing only)
- [x] Vitest re-run — 452/452 baseline maintained; sla-dashboard subset 30/30 pass
- [x] Day 1 commit — `51fa3852` on `feature/sprint-57-32-sla-dashboard-repoint`

---

## Day 2 — Group C (Latency + SLO row) — ✅ done

### 2.1 US-C1 — LatencyChart Card wrapper + .kbar verbatim — ✅ done

- [x] **Read mockup** `page-admin.jsx:62-70` (Card wrapper + .kbar legend) — Card wrapper + .kbar legend ALREADY done Day 1 inside SLAOverview composition (Sprint 57.25 placed them in parent, not in LatencyChart.tsx itself). Day 2 work scoped to SVG body only.
- [x] **Re-point** `LatencyChart.tsx`
  - Sub: svg root `className="w-full" height={HEIGHT}` → `className="chart" style={{ height: HEIGHT }}` (mockup .chart class styles.css:1077 provides width 100% + height 180px default; inline style override matches mockup escape-hatch page-admin.jsx:174)
  - Sub: `<g>` for grid lines: explicit `stroke="var(--border)" strokeWidth={1} opacity={0.4}` → `className="grid"` (styles-mockup.css:1078 .chart .grid line provides stroke + strokeWidth via CSS); dropped opacity={0.4} drift (not in mockup)
  - Sub: `<g>` for axis text: explicit `fill="var(--fg-muted)" fontSize={9} fontFamily="ui-monospace"` → `className="axis"` (styles-mockup.css:1079 .chart .axis text provides fill var(--fg-subtle) + font-size 10px + font-family var(--font-mono))
  - Sub: 3-series paths preserved verbatim (stroke colors + widths + p99 opacity 0.9; data-testid + aria-label preserved)
  - Sub: Added file-level eslint-disable no-restricted-syntax verbatim escape-hatch comment
- [x] **Header MHist** updated

### 2.2 US-C2 — SLOStatusCard 5-row .bar-track verbatim — ✅ done

- [x] **Read mockup** `page-admin.jsx:72-98` (5-row SLO budget gauge)
- [x] **Re-point** `SLOStatusCard.tsx`
  - Sub: `<CardShell>` → mockup-ui `<Card>`
  - Sub: dropped imports `BarTrack from "components/charts"` + `CardShell from "components/ui/CardShell"` + `cn from "lib/utils"` → added `Card from "components/mockup-ui"`
  - Sub: outer Tailwind `flex flex-col gap-3` → mockup `.col` + inline style={{ gap: 12 }}
  - Sub: per-row header Tailwind `mb-1 flex items-center justify-between` → mockup `.spread` + inline style={{ marginBottom: 4 }}
  - Sub: inner left span Tailwind `inline-flex items-center gap-1.5 text-[12.5px]` → mockup `.row` + inline style={{ gap: 6, fontSize: 12.5 }}
  - Sub: color dot Tailwind `h-1.5 w-1.5 rounded-full bg-success/danger` → inline style={{ width: 6, height: 6, borderRadius: "50%", background: ok ? "var(--success)" : "var(--danger)" }}
  - Sub: current value — **Hybrid Tailwind+inline color bridge** (per Sprint 57.31 TenantTopTable precedent for Vitest contract continuity): `text-fg-muted`/`text-danger` Tailwind classes preserved alongside inline style color verbatim; mockup `.mono .tnum` added; size set via inline style={{ fontSize: 11.5 }}
  - Sub: inner separator Tailwind `text-fg-subtle` → mockup `.subtle`
  - Sub: `<BarTrack pct={s.used} tone={...}>` → verbatim `<div className="bar-track"><span style={{ width: Math.min(100, s.used) + "%", background: ok ? "var(--success)" : "var(--danger)" }} /></div>`
  - Sub: budget-used row Tailwind `mt-1 font-mono text-[10px] text-fg-subtle` → mockup `.subtle .mono` + inline style={{ fontSize: 10, marginTop: 3 }}
  - Sub: Added file-level eslint-disable no-restricted-syntax verbatim escape-hatch comment
- [x] **Header MHist** updated

### 2.3 Day 2 mini-verify — ✅ done

- [x] All Day 2 files lint-clean (ESLint exit 0)
- [x] tsc strict — 0 new errors
- [x] Vitest after Hybrid bridge fix — 452/452 baseline maintained; sla-dashboard subset 30/30 (2 spec drift caught + adapted via Hybrid Tailwind+inline color bridge per Sprint 57.31 TenantTopTable precedent)
- [x] Playwright shot `day2-sla-dashboard-full.png` confirms PARITY: LatencyChart 3-series SVG (p50 primary / p95 info / p99 warning) + SLOStatusCard 5-row budget gauge with proper ok/danger color coding (4 ok green + 1 failing Cost/run danger red)
- [x] Day 2 commit — `ffbf724b` on `feature/sprint-57-32-sla-dashboard-repoint`

---

## Day 3 — Group D (Top slow + Error rate + Vitest) — ✅ done

### 3.1 US-D1 — TopSlowOpsTable verbatim — ✅ done

- [x] **Read mockup** `page-admin.jsx:104-129` (.table 6-op)
- [x] **Re-point** `TopSlowOpsTable.tsx`
  - Sub: `<CardShell>` → mockup-ui `<Card title=... subtitle=... bodyClass="flush">`
  - Sub: table `className="w-full border-collapse text-left text-[12px]"` → `className="table"` (styles-mockup.css cascade supplies layout)
  - Sub: thead/th translations dropped (mockup has no className on tr/th; styles cascade from .table); textAlign right inline-style added to numeric col headers
  - Sub: Kind cell shadcn-style Badge (KIND_TONE_CLASS map with `bg-tool/15 text-tool` etc.) → mockup-ui `<Badge tone={KIND_TONE_MAP[row.kind]}>` with kind-to-tone dispatch (tool/primary/thinking/success/memory)
  - Sub: Operation td `px-4 py-2 font-mono text-[11.5px]` → `.mono` + inline `style={{ fontSize: 11.5 }}`
  - Sub: p50/p95 td `px-4 py-2 text-right font-mono tabular-nums` → `.mono .tnum` + inline `style={{ textAlign: "right" }}`
  - Sub: p99 td — **Hybrid Tailwind+inline color bridge** (preserve `text-warning`/`text-fg-muted` Tailwind alongside inline style color verbatim per Sprint 57.32 Day 2 SLOStatusCard precedent); `.mono .tnum` added
  - Sub: Calls td `px-4 py-2 text-right font-mono tabular-nums text-fg-subtle` → `.mono .tnum .subtle` + inline `style={{ textAlign: "right" }}`
  - Sub: Dropped imports: CardShell + cn util + KIND_TONE_CLASS shadcn map. Added Badge + Card from mockup-ui.
  - Sub: BackendGapBanner preserved per AP-2 honesty
  - Sub: Added file-level eslint-disable no-restricted-syntax verbatim escape-hatch comment
- [x] **Header MHist** updated

### 3.2 US-D2 — ErrorRateByServiceCard verbatim — ✅ done

- [x] **Read mockup** `page-admin.jsx:131-152` (6-row .bar-track)
- [x] **Re-point** `ErrorRateByServiceCard.tsx`
  - Sub: `<CardShell>` → mockup-ui `<Card>`
  - Sub: outer `flex flex-col gap-2.5` → `.col` + inline `style={{ gap: 10 }}` (mockup gap 10 not 2.5×4=10 coincidence; verbatim literal)
  - Sub: per-row header `mb-1 flex items-center justify-between` → `.spread` + inline `style={{ marginBottom: 3 }}` (mockup uses 3, not 1)
  - Sub: service name `font-mono text-[11.5px]` → `.mono` + inline `style={{ fontSize: 11.5 }}`
  - Sub: rate % — **Hybrid Tailwind+inline color bridge** (preserve `text-warning`/`text-fg-muted` Tailwind alongside inline style color verbatim); `.mono .tnum` added; inline style for fontSize 11 + color
  - Sub: `<BarTrack pct={...} tone={...}>` → verbatim `<div className="bar-track"><span style={{ width: Math.min(100, rate × 50) + "%", background: warn ? "var(--warning)" : "var(--success)" }} /></div>`
  - Sub: Dropped imports: BarTrack + CardShell + cn util. Added Card from mockup-ui.
  - Sub: BackendGapBanner preserved per AP-2 honesty
  - Sub: Added file-level eslint-disable no-restricted-syntax verbatim escape-hatch comment
- [x] **Header MHist** updated

### 3.3 US-D3 — Vitest comprehensive — ✅ done

- [x] Full Vitest suite — **452/452 baseline maintained** (no spec drift this time; Hybrid bridge applied preemptively for `text-warning`/`text-fg-muted` class assertions)
- [x] sla-dashboard subset 30/30 pass

### 3.4 Day 3 mini-verify — ✅ done

- [x] All Day 3 files lint-clean (ESLint exit 0)
- [x] tsc strict — 0 new errors (TS6310 carryover pre-existing only)
- [x] Playwright shot `day3-sla-dashboard-full.png` confirms PARITY (Top slow ops table 6 rows with Badge tone-per-kind + p99 color-coded; Error rate by service 6 rows with .bar-track scaled by rate × 50)
- [x] Day 3 commit — `3787d91f` on `feature/sprint-57-32-sla-dashboard-repoint`

---

## Day 4 — Group E (regression sweep + fidelity + closeout)

### 4.1 US-E1 — 22-route regression sweep — ✅ done

- [x] **after-sweep** via `route-sweep.mjs after` — 22/22 PNG captured
- [x] **Sweep triage** — 17 🟢 PARITY shell + 1 🟢 PARITY target + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails (cleanest yet)
- [x] **REPOINT-REPORT.md** written

### 4.2 US-E2 — /sla-dashboard fidelity verify — ✅ done

- [x] **Step 1** styles-mockup.css ↔ reference/design-mockups/styles.css diff → **empty** (foundation byte-identical contract honored)
- [x] **Step 2** mockup vs prod assessed via REPOINT-REPORT element-by-element table (12+ representative elements)
- [x] **Step 3** representative mockup elements catalogued in REPOINT-REPORT.md (.page-head + .grid-stats KPI + LatencyChart .chart/.grid/.axis + SLOStatusCard 5-row .bar-track + TopSlowOpsTable .table + ErrorRateByServiceCard .bar-track + 3 BackendGapBanner AP-2 honesty)
- [x] **Step 4** drift verdict logged: **🟢 PARITY**

### 4.3 US-E3 — Full gates — ✅ done

- [x] tsc strict — 0 new errors (TS6310 carryover pre-existing only)
- [x] ESLint exit 0
- [x] Vitest 94 files / 452/452 baseline maintained; sla-dashboard subset 30/30
- [x] Vite build successful (3.21s)
- [x] check:mockup-fidelity 25/25 baseline maintained; foundation diff guard PASSED
- [x] Bundle size delta: 0 (no orphan cleanup; no new modules)

### 4.4 US-E4 — Closeout

- [x] **retrospective.md** Q1-Q7 written (Q7 N/A SKIP per Sprint 57.29-57.31 precedent; Q4 has baseline-lift 1st-data-point evaluation + RESOLUTION action)
- [x] **Memory snapshot** `memory/project_phase57_32_sla_dashboard_repoint.md` NEW
- [x] **MEMORY.md** pointer entry added (~300 char quality pointer)
- [x] **CLAUDE.md** Current Sprint row + footer updated (minimal touch)
- [x] **`sprint-workflow.md §Scope-class multiplier matrix`** updated — `frontend-verbatim-css-repoint` row now 4 data points + baseline-lift 1st-data-point validation result + MHist entry
- [x] **`next-phase-candidates.md`** updated — Sprint 57.32 Carryover section added; baseline-lift AD updated with 1st validation status
- [x] **Day 4 commit** — `0d8eabd1` on `feature/sprint-57-32-sla-dashboard-repoint`
- [x] **PR open** — PR #166 https://github.com/laitim2001/ai-semantic-kernel-framework-project/pull/166
- [x] **CI green → squash-merge** — **All 7 checks PASS on 1st run** (Backend E2E / Frontend E2E chromium headless / Lighthouse informational / 2× Lint+Type+Build / 2× Lint+Type+Test with PG16 / v2-lints); no baseline regen needed (cleaner than Sprint 57.31); squash-merged as `eed0c70c` to main; feature branch deleted via `--delete-branch`

### 4.5 Sprint closeout self-check

- [x] Sacred Rule check — 0 unchecked items deleted
- [x] Acceptance Criteria — all 5 pass (PARITY + 0 catastrophic/structural + 5 gates green + baseline-lift 1st validation logged + docs synced)
- [x] Working tree clean post-merge — on main; only untracked older-sprint debug PNGs
- [x] Branch deleted — `feature/sprint-57-32-sla-dashboard-repoint` deleted local + remote
