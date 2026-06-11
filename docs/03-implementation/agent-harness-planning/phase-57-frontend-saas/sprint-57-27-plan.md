---
sprint: 57.27
phase: Phase 57+ Frontend SaaS 24/N (pending close)
title: AD-Mockup-Fidelity-Rebuild-Overview — 1-Page Strict Rebuild (Frontend-Led)
class: frontend-mockup-strict-rebuild 0.60 (4th application; baseline KEEP per 3-sprint window rule; rich-dashboard sub-classification DECISION sprint per next-phase-candidates #41)
duration_days: 4 (Day 0 setup + 三-prong + Prong 5 / Day 1 page-head + KPI row + Active Loops + HITL Queue / Day 2 Cost Burn + Providers + Incidents + Error Trend + Quick Actions / Day 3 i18n + integration + closeout)
related:
  - Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md (overview audit row)
  - Sprint 57.25 plan + retrospective (frontend-mockup-strict-rebuild 0.60 class 3rd app; ratio 0.88; rich-dashboard sub-class DEFER)
  - Sprint 57.24 v2 plan + retrospective (7 reusable primitives extracted — CardShell / PageHead / StatCard / Spark / AreaChart / BarTrack / BackendGapBanner)
  - Sprint 57.26 retrospective (foundation-token correction; html 13px baseline; AD #42 Day-0 Prong 4 visual-baseline coverage)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17)
  - reference/design-mockups/page-overview.jsx:74-379 (overview page mockup + CostBurnChart + ErrorTrendChart helpers)
  - .claude/rules/sprint-workflow.md §Scope-class multiplier matrix
  - .claude/rules/sprint-workflow.md §Step 2.5 (Day-0 verify; Prong 4 visual-baseline coverage per AD #42; Prong 5 audit cross-ref)
  - claudedocs/1-planning/next-phase-candidates.md #41 (rich-dashboard sub-class 4th-data-point decision)
  - 16-frontend-design.md §Overview / operator dashboard page
  - 17-cross-category-interfaces.md (no new contracts this sprint; frontend-only + fixture banners for backend-gap widgets)
---

# Sprint 57.27 — AD-Mockup-Fidelity-Rebuild-Overview

## Sprint Goal

Rebuild **`/overview`** to **1:1 mockup fidelity** per mockup `reference/design-mockups/page-overview.jsx:74-379`, migrating the page's 9 widget groups off its 728-line all-in-one inline implementation onto the 7 reusable presentation primitives extracted in Sprint 57.24 v2 (`<CardShell>` / `<PageHead>` / `<StatCard>` / `<Spark>` / `<AreaChart>` / `<BarTrack>` / `<BackendGapBanner>`) — **frontend-led**, real data preserved where it exists (`useActiveLoops`), backend gaps filled via fixture data + visible "backend wire pending" banners per AP-2 honesty.

**Two-line philosophy** (per Sprint 57.20 Option W carry-forward):

1. **Frontend leads** — `/overview` rebuilt 1:1 from mockup; 9 widget groups ship visually (page-head with in-page title + mono tenant/role/clock + Export + New Chat / 4-stat KPI row WITH sparklines / Active Loops card / HITL Queue card / Cost Burn chart / Providers card / Recent Incidents card / Error Trend chart / Quick Actions strip); migrates inline primitives to the 7 shared Sprint 57.24 v2 primitives; closes the 16-drift list (D1-D16) catalogued in Day-0 exploration.
2. **Backend follows** — Existing `useActiveLoops(10)` hook is the only real data source and is preserved; HITL Queue / Providers / Recent Incidents / Error Trend / Cost Burn / KPI sparklines all ship as fixture data (already inline fixtures today) + visible `<BackendGapBanner>` per AP-2 honesty; backend aggregation work folds into NEW AD-Overview-Backend-Extensions-Phase58 carryover.

## Background

### Why Sprint 57.27 (this sprint)

The user compared `/overview` against the mockup on 2026-05-21 (post-Sprint 57.26 foundation-token correction) and reported visible drift in font sizing, colour, and main-content layout. Day-0 exploration confirmed: `/overview` is NOT a blank page — it is a Sprint 57.19/57.20 "close port" (`frontend/src/pages/overview/OverviewPage.tsx`, 728 lines, all 9 widgets present) — but it carries **16 catalogued drifts (D1-D16)** and uses **inline primitives** instead of the shared Sprint 57.24 v2 primitive set. Sprint 57.26 corrected only the global foundation tokens (`html` font-size, shell layout, radius); per-route content fidelity (widget-level font classes, colours, layout, missing sparklines / axis labels) is the `frontend-mockup-strict-rebuild` epic's scope, and `/overview` is this sprint's user-directed target.

| Mockup widget group | Production state (Sprint 57.19/57.20 close port) | Drift refs | Severity |
|---------------------|--------------------------------------------------|-----------|----------|
| A. page-head (in-page title + sub + route-pill + mono tenant/role/clock + Export + New Chat) | Partial — subtitle + route-pill + buttons present; in-page title delegated to AppShellV2 topbar; mono tenant/role/clock missing | D1, D2 | STRUCTURAL |
| B. KPI row 4× Stat (Active Sessions / HITL Pending / Cost MTD / SLA p95) | Partial — 4 stats render; NO sparklines (inline Stat has no `spark` prop) | D3, D5 | functional/cosmetic |
| C. Active Loops card (5-col loopRow) | Present — real data via `useActiveLoops`; row content layout differs (session-id only vs agent+session+tenant+model) | D4 | structural |
| D. HITL Queue card (3 risk-tinted cards) | Present — fixture; critical-tint approximation | D13 | cosmetic |
| E. Cost Burn card + CostBurnChart SVG | Present — chart drops x-axis labels + budget-line text label | D16 | structural |
| F. Providers card (4-row trafficDot) | Present — fixture | (token) | cosmetic |
| G. Recent Incidents card (4-row) | Present — fixture; Badge pill vs 4px; RiskBadge tone map | D11, D12 | cosmetic |
| H. Error Trend card + ErrorTrendChart SVG | Present — chart drops x-axis labels | D16 | structural |
| I. Quick Actions strip (4 quickBtn) | Present | (token) | cosmetic |
| Token-level (radius literal vs token / card-title 14px vs 12.5px / stat padding / card-head padding / page-wrapper gap) | inline-primitive defaults | D6-D10, D14 | cosmetic |
| Inline primitives (`Card` / `Badge` / `RiskBadge` / `Stat` defined inline in OverviewPage.tsx:51-137) | should migrate to shared `components/ui` + `components/charts` (Sprint 57.24 v2) | — | AP-3 dedup |

**Σ bottom-up**: ~6-7 hr (mid ~6.5 hr) before calibration
**Calibrated commit**: ~6.5 hr × 0.60 ≈ ~3.9 hr (KEEP class baseline per 3-sprint window rule)

### Class baseline + rich-dashboard sub-classification DECISION (next-phase-candidates #41)

This sprint is the **4th application of `frontend-mockup-strict-rebuild` 0.60 class** and the **decision sprint** for the rich-dashboard sub-classification proposed Sprint 57.24 v2 retro Q4 and deferred Sprint 57.25:

| Sprint | Scope shape | actual/committed ratio |
|--------|-------------|----------------------:|
| 57.23 (1st app) | Auth flow — 7 small routes | 0.59 (below band) |
| 57.24 v2 (2nd app) | 1 rich dashboard — cost-dashboard | 1.19 (top of band) |
| 57.25 (3rd app) | 1 rich dashboard — sla-dashboard | 0.88 (in band, lower edge) |
| 57.27 (this; 4th app) | 1 rich dashboard — overview (9 widgets) | **TBD** |

Per next-phase-candidates #41 resolution path: rich-dashboard 2-data-point mean (57.24 v2 + 57.25) = 1.04 sits in-band middle → sub-class hypothesis NOT confirmed. Day 3 retrospective Q4 records the 57.27 ratio as the 4th data point:
- If 57.27 ratio **in band [0.85, 1.20]** → 3-of-3 rich in band → **DROP** sub-class proposal entirely; KEEP 0.60 baseline
- If 57.27 ratio **> 1.20** → 2-of-3 rich above band → reconsider rich sub-class higher (~0.70-0.75)
- If 57.27 ratio **< 0.85** → drop rich-dashboard pattern entirely; KEEP 0.60 baseline accepts auth-flow + rich mixed

Class baseline **KEEP 0.60** this sprint per `When to adjust` 3-sprint window rule regardless of the reading.

### What is preserved (NOT rewritten)

| Layer | Specific | Reuse mechanism |
|-------|----------|-----------------|
| Page wrapper | `frontend/src/pages/overview/index.tsx` re-export | Unchanged |
| Auth gate | `RequireAuth` + AppShellV2 wrap + route `/overview` | Unchanged |
| Data fetching | `useActiveLoops(10)` (`@/features/loops/hooks/useActiveLoops`) | Unchanged; only real data source; loading/error/empty states preserved |
| Sprint 57.24 v2 primitives | `components/ui/{CardShell, PageHead, BackendGapBanner}` + `components/charts/{Spark, StatCard, AreaChart, BarTrack}` | Imported and reused; no API changes (Day 0 Prong 1+2 verify each API can serve overview) |
| i18n infra | `react-i18next` + `useTranslation("common")` | Unchanged; +N keys added |
| Vitest baseline | 430/430 (Sprint 57.26 close) | Adapt existing OverviewPage spec; add NEW specs for extracted widget components |

### What gets rewritten (this sprint scope)

| Layer | File | Approach |
|-------|------|----------|
| OverviewPage | `frontend/src/pages/overview/OverviewPage.tsx` | REWRITE in-place: 728-line all-in-one → ~150-line assembly importing 9 widget components + shared primitives; mockup `page-overview.jsx:74-266` 1:1 |
| ActiveLoopsCard | `frontend/src/features/overview/components/ActiveLoopsCard.tsx` (NEW; extracted) | 5-col loopRow per mockup `page-overview.jsx:99-141`; D4 content layout fix (agent+session+tenant+model); preserves `useActiveLoops` + loading/error/empty states |
| HITLQueueCard | `frontend/src/features/overview/components/HITLQueueCard.tsx` (NEW; extracted) | 3 risk-tinted cards per mockup `:143-167`; fixture + `<BackendGapBanner>` |
| CostBurnChart | `frontend/src/features/overview/components/CostBurnChart.tsx` (NEW; extracted) | SVG cumulative burn line + gradient + budget diagonal + gridlines + D16 x-axis labels + budget-line label per mockup `:273-329` |
| ProvidersCard | `frontend/src/features/overview/components/ProvidersCard.tsx` (NEW; extracted) | 4-row trafficDot per mockup `:180-199`; fixture + `<BackendGapBanner>` |
| IncidentsCard | `frontend/src/features/overview/components/IncidentsCard.tsx` (NEW; extracted) | 4-row per mockup `:204-225`; fixture + `<BackendGapBanner>`; D11 badge 4px + D12 RiskBadge tone fix |
| ErrorTrendChart | `frontend/src/features/overview/components/ErrorTrendChart.tsx` (NEW; extracted) | 24-bar histogram + D16 x-axis labels per mockup `:331-379` |
| QuickActionsStrip | `frontend/src/features/overview/components/QuickActionsStrip.tsx` (NEW; extracted) | 4 quickBtn per mockup `:236-266` |
| Fixtures | `frontend/src/features/overview/__fixtures__/{hitlQueue, providers, incidents, errorTrend, costBurn, kpiSparklines}.ts` | NEW; lift current inline OverviewPage consts to fixture files; add KPI sparkline arrays |
| i18n | `frontend/src/i18n/locales/{en,zh-TW}/common.json` | +N keys (overview.* page-head / KPI labels / banner reasons / quick-action labels) — Day 0 三-prong counts existing overview keys to compute N |
| Vitest specs | existing OverviewPage spec (adapt) + 7 NEW per-component specs | ~14-18 NEW cases + adapt |

### V2 紀律對齐 (per Sprint 57.25 pattern)

- **約束 1 單一範疇歸屬**: pure frontend sprint; all changes in `frontend/src/pages/overview/` + `frontend/src/features/overview/` + i18n
- **約束 2 主流量驗證**: `/overview` is the operator dashboard landing route; Playwright MCP pair-verify (mockup 8080 + production 3007 at 1440×900) attempted Day 1 + Day 2 + Day 3; Day-0 dev-login flow already verified working this session (`/auth/dev` → Continue as jamie@acme.com)
- **約束 3 LLM Provider Neutrality**: 0 SDK import preserved (frontend-only sprint)
- **約束 4 Anti-Pattern checklist**:
  - **AP-2 (no Potemkin)**: HITL Queue / Providers / Recent Incidents / Error Trend / Cost Burn / KPI sparklines all ship fixture data — each fixture-backed widget carries a visible `<BackendGapBanner>` declaring AD-Overview-Backend-Extensions-Phase58 carryover (expected ~4-5 banners; Active Loops is the one real-data widget, no banner)
  - **AP-3 (cross-directory scattering)**: this sprint REVERSES an AP-3 violation — inline `Card`/`Badge`/`Stat`/`RiskBadge` in OverviewPage.tsx migrate to the shared `components/ui` + `components/charts` set; widget components land in `features/overview/components/` (feature-scope)
  - **AP-4 (rename-only refactor)**: every extracted component delivers visible mockup-fidelity gain (D1-D16 closures); not a rename
  - AP-11 (version suffix): no `_v2` suffixes; OverviewPage.tsx rewritten in place
- **約束 5 測試優先**: Vitest 430 baseline preserved; NEW specs ~14-18 cases; Playwright e2e for `/overview` — Day 3 decision whether to add bootstrap e2e or defer; a11y-scan baseline preserved; visual-regression baseline for `/overview` regenerated via workflow_dispatch per AD #42 (Sprint 57.26 lesson — visual baselines MUST regen for any page-visual change)

## User Stories

### Group A — Day 0 setup + 三-prong + Prong 5 (PRE-WORK)

**US-A1**: As a Sprint 57.27 owner, I want plan + checklist landed + feature branch created from main `fb27df73` + Day 0 三-prong (Prong 1 path verify on 7 shared primitives + OverviewPage.tsx + Prong 2 content verify on shared-primitive APIs vs overview needs + `useActiveLoops` response shape + Prong 4 test selector verify on existing OverviewPage spec + visual-regression.spec.ts overview snapshot) + Prong 5 audit cross-ref (Sprint 57.22 AUDIT-REPORT overview row) + DRIFT-REPORT skeleton with the 16-drift list (D1-D16) + AD-Overview-Backend-Extensions-Phase58 carryover added to next-phase-candidates.md so that Day 1+ has a verified baseline and the 4th-app rich-dashboard sub-class decision data point is locked in.

### Group B — page-head + KPI row + Active Loops + HITL Queue (Day 1)

**US-B1**: As an operator viewing `/overview`, I want the page-head rendering in-page title + subtitle + `/overview` route-pill + mono `{tenant} · {role} · {clock}` line + page-actions (Export outline + New Chat primary) per mockup `page-overview.jsx:74-87`, and the 4-stat KPI row rendering `<StatCard>` for Active Sessions / HITL Pending / Cost MTD (WITH sparkline) / SLA p95 (WITH sparkline) per mockup `:90-95` — so that page identity + at-a-glance KPIs match mockup at 1440×900. Closes D1 (in-page title), D2 (mono meta line), D3 + D5 (sparklines). Decision: in-page title vs AppShellV2 topbar title — mockup renders it in-page; resolve Day 1 (likely render in-page + suppress topbar duplicate).

**US-B2**: As an operator, I want `<ActiveLoopsCard>` (real data via `useActiveLoops(10)`; preserves loading/error/empty states) rendering 5-col loopRow with agent name + session + tenant + model per mockup `:99-141` (closes D4), and `<HITLQueueCard>` rendering 3 risk-tinted cards per mockup `:143-167` with fixture data + `<BackendGapBanner>` — so that the left/right column pair below the KPI row matches mockup `grid2 1.4fr 1fr`.

### Group C — Cost Burn + Providers + Incidents + Error Trend + Quick Actions (Day 2)

**US-C1**: As an operator, I want `<CostBurnChart>` (SVG cumulative 30-day burn line + gradient area + budget diagonal + gridlines + x-axis labels `day 1 / today / day 30` + budget-line text label per mockup `:273-329`, closes D16) and `<ErrorTrendChart>` (24-bar histogram with tone-by-value + x-axis labels `-24h / -12h / now` per mockup `:331-379`, closes D16) — so that both inline SVG charts render axis labels matching mockup.

**US-C2**: As an operator, I want `<ProvidersCard>` (4-row trafficDot green/amber/red glow + mono name + p95 + calls per mockup `:180-199`) and `<IncidentsCard>` (4-row RiskBadge + mono id + title + status Badge + since per mockup `:204-225`, closes D11 badge 4px-radius + D12 RiskBadge `risk-*` tone map) — both fixture + `<BackendGapBanner>` — so that the two right/left fixture cards match mockup.

**US-C3**: As an operator, I want `<QuickActionsStrip>` rendering 4 quickBtn (New Chat / Review governance / Tenants / Verification; each icon + label + sub) per mockup `:236-266` as a full-width row — so that the dashboard footer strip matches mockup.

### Group D — i18n + integration + Vitest + Playwright + closeout (Day 3)

**US-D1**: As a multilingual operator, I want `frontend/src/i18n/locales/{en,zh-TW}/common.json` extended with the NEW keys (overview page-head copy + mono meta + KPI labels + 4-5 BackendGapBanner reasons + quick-action labels/subs + chart axis labels) so that all rebuilt widgets render in both EN and zh-TW. (Day 0 三-prong counts pre-existing `overview.*` keys; US-D1 adds only the delta.)

**US-D2**: As a routing maintainer, I want `OverviewPage.tsx` rewritten as a ~150-line assembly importing the 7 extracted widget components + shared primitives in mockup-faithful grid layout (`kpiRow` 4×1fr / `grid2` 1.4fr 1fr / `grid2eq` 1fr 1fr × 2 / quick strip), with token-level drifts D6-D10 + D14 closed (radius token, card-title 12.5px, stat padding, card-head padding, page-wrapper gap) using Sprint 57.18 wired tokens + STYLE.md §3 arbitrary-value escape hatches where Tailwind utility doesn't map — so that the page assembles cleanly and the inline-primitive AP-3 violation is fully reversed.

**US-D3**: As a Sprint 57.27 owner, I want Vitest 430 baseline grown to 430+N (N≥14 covering ActiveLoopsCard / HITLQueueCard / CostBurnChart / ProvidersCard / IncidentsCard / ErrorTrendChart / QuickActionsStrip + OverviewPage integration) without regression + Playwright MCP pair-verify (mockup 8080 + production 3007 at 1440×900) + visual-regression baseline regenerated via workflow_dispatch + cherry-pick (per AD #42 — overview snapshot will move) + commits + retrospective.md Q1-Q7 with calibration ratio analysis + rich-dashboard sub-class DECISION (4th data point) + memory snapshot `memory/project_phase57_27_overview_rebuild.md` + MEMORY.md +1 line + `.claude/rules/sprint-workflow.md` calibration matrix +1 row (4th app) + CLAUDE.md Current Sprint row + Last Updated footer + DRIFT-REPORT verdict = PARITY so that Sprint 57.27 = COMPLETE.

## Technical Specifications

### OverviewPage.tsx rewrite — 9-widget-group assembly

```tsx
// AFTER (mockup-direct port; ~150 lines; imports 7 extracted widgets + shared primitives)
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { PageHead } from "../../components/ui/PageHead";
import { CardShell } from "../../components/ui/CardShell";
import { StatCard } from "../../components/charts/StatCard";
import { Spark } from "../../components/charts/Spark";
import { ActiveLoopsCard } from "../../features/overview/components/ActiveLoopsCard";
import { HITLQueueCard } from "../../features/overview/components/HITLQueueCard";
import { CostBurnChart } from "../../features/overview/components/CostBurnChart";
import { ProvidersCard } from "../../features/overview/components/ProvidersCard";
import { IncidentsCard } from "../../features/overview/components/IncidentsCard";
import { ErrorTrendChart } from "../../features/overview/components/ErrorTrendChart";
import { QuickActionsStrip } from "../../features/overview/components/QuickActionsStrip";
import { kpiSparkCost, kpiSparkSla } from "../../features/overview/__fixtures__/kpiSparklines";

// Layout: PageHead → kpiRow grid-cols-4 → grid2 (ActiveLoops 1.4fr | HITLQueue 1fr)
//         → grid2eq (CostBurn | Providers) → grid2eq (Incidents | ErrorTrend)
//         → QuickActionsStrip full-width
```

Page-wrapper: `p-[18px]` + per-row `mb-[14px]` (mockup uses marginBottom not gap — D14; match mockup exactly). KPI row `grid grid-cols-4 gap-[12px]`. `grid2` = `grid grid-cols-[1.4fr_1fr] gap-[14px]`. `grid2eq` = `grid grid-cols-2 gap-[14px]`.

### Shared-primitive reuse + Day-0 API verify (Prong 2)

| Primitive | Path | Overview usage | Day-0 verify |
|-----------|------|----------------|--------------|
| `<PageHead>` | `components/ui/PageHead.tsx` | page-head title + subtitle + routePath pill + actions slot; **mono tenant/role/clock** = NEW need — verify PageHead has a meta slot or extend | Prong 2: read PageHead props |
| `<CardShell>` | `components/ui/CardShell.tsx` | all card wrappers (ActiveLoops / HITL / CostBurn / Providers / Incidents / ErrorTrend) | Prong 2: verify `flush`/`dense` body variants |
| `<StatCard>` | `components/charts/StatCard.tsx` | KPI row 4 stats; **spark prop** required for Cost MTD + SLA p95 | Prong 2: confirm `spark` prop exists (Sprint 57.25 used it) |
| `<Spark>` | `components/charts/Spark.tsx` | KPI sparklines (2) | Prong 1 path verify |
| `<AreaChart>` | `components/charts/AreaChart.tsx` | candidate for CostBurnChart — verify if area-fill API fits cumulative-burn shape, else keep CostBurnChart bespoke SVG | Prong 2: API shape |
| `<BarTrack>` | `components/charts/BarTrack.tsx` | NOT expected this sprint (overview has no bar-track widget) — confirm | — |
| `<BackendGapBanner>` | `components/ui/BackendGapBanner.tsx` | 4-5 instances (HITL / Providers / Incidents / ErrorTrend / CostBurn) | Prong 1 path verify |

**Open decision (Day 1)**: if `<PageHead>` has no mono-meta slot, either (a) extend PageHead with an optional `meta` prop (touches a shared primitive — needs care) or (b) render the mono line as a sibling below PageHead. Prefer (b) feature-scoped unless 2nd consumer is known (Karpathy §2).

**Open decision (Day 2)**: `<CostBurnChart>` — mockup `:273-329` is a bespoke cumulative-line + budget-diagonal SVG. `<AreaChart>` may not express the budget diagonal. Default: keep `CostBurnChart` as a feature-scoped bespoke SVG component (mockup-direct port), do NOT force-fit `<AreaChart>`. Confirm Day 0 Prong 2.

### Drift closure map (D1-D16 → User Story)

| Drift | Fix | Closed by |
|-------|-----|-----------|
| D1 in-page title missing | render title in PageHead in-page; suppress AppShellV2 topbar duplicate | US-B1 |
| D2 mono tenant/role/clock missing | add mono meta line | US-B1 |
| D3 + D5 KPI sparklines missing | use shared `<StatCard spark>` + `<Spark>` | US-B1 |
| D4 Active Loops row content | 5-col loopRow agent+session+tenant+model | US-B2 |
| D6 card radius literal vs token | use `--radius` token (8px post-57.26) | US-D2 |
| D7 card-head padding | match mockup `11px 14px` | US-D2 |
| D8 card-title 14px → 12.5px | CardShell title class | US-D2 |
| D9 stat padding asymmetric | StatCard `14px 16px` | US-D2 |
| D10 stat delta glyph → SVG icon | StatCard arrow icon | US-B1 |
| D11 badge pill → 4px radius | shared Badge default | US-C2 |
| D12 RiskBadge tone map | `risk-*` token colours | US-C2 |
| D13 HITL critical tint | match mockup `oklch(.../0.08)` | US-B2 |
| D14 page-wrapper gap → mb | per-row `mb-[14px]` | US-D2 |
| D16 chart x-axis labels missing | CostBurnChart + ErrorTrendChart axis labels | US-C1 |
| D15 maxTurns hardcoded 50 | OUT OF SCOPE — backend gap; folds to AD-Overview-Backend-Extensions-Phase58 | carryover |

## File Change List

### NEW files (~14)

1. `frontend/src/features/overview/components/ActiveLoopsCard.tsx` (~90 lines)
2. `frontend/src/features/overview/components/HITLQueueCard.tsx` (~70 lines)
3. `frontend/src/features/overview/components/CostBurnChart.tsx` (~95 lines)
4. `frontend/src/features/overview/components/ProvidersCard.tsx` (~60 lines)
5. `frontend/src/features/overview/components/IncidentsCard.tsx` (~70 lines)
6. `frontend/src/features/overview/components/ErrorTrendChart.tsx` (~75 lines)
7. `frontend/src/features/overview/components/QuickActionsStrip.tsx` (~55 lines)
8. `frontend/src/features/overview/__fixtures__/hitlQueue.ts`
9. `frontend/src/features/overview/__fixtures__/providers.ts`
10. `frontend/src/features/overview/__fixtures__/incidents.ts`
11. `frontend/src/features/overview/__fixtures__/errorTrend.ts`
12. `frontend/src/features/overview/__fixtures__/costBurn.ts`
13. `frontend/src/features/overview/__fixtures__/kpiSparklines.ts` (2 spark arrays: cost / sla)
14. (DRIFT-REPORT) `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-27/artifacts/overview-rebuild/DRIFT-REPORT.md`

### NEW spec files (7)

1. `frontend/tests/unit/overview/ActiveLoopsCard.test.tsx` (~4 cases: loading / error / empty / happy 5-col row)
2. `frontend/tests/unit/overview/HITLQueueCard.test.tsx` (~3 cases: 3 cards / critical tint / BackendGapBanner)
3. `frontend/tests/unit/overview/CostBurnChart.test.tsx` (~3 cases: svg path / axis labels / budget line)
4. `frontend/tests/unit/overview/ProvidersCard.test.tsx` (~2 cases: 4 rows / trafficDot tone)
5. `frontend/tests/unit/overview/IncidentsCard.test.tsx` (~3 cases: 4 rows / RiskBadge tone / Badge 4px)
6. `frontend/tests/unit/overview/ErrorTrendChart.test.tsx` (~2 cases: 24 bars / axis labels)
7. `frontend/tests/unit/overview/QuickActionsStrip.test.tsx` (~2 cases: 4 buttons / navigate on click)

### REWRITTEN files (1)

1. `frontend/src/pages/overview/OverviewPage.tsx` — 728-line all-in-one → ~150-line assembly

### MODIFIED files (3)

1. `frontend/src/i18n/locales/en/common.json` — +N keys (Day 0 三-prong counts existing `overview.*` keys to compute N delta)
2. `frontend/src/i18n/locales/zh-TW/common.json` — +N keys (mirror parity)
3. existing OverviewPage Vitest spec — adapt selectors for extracted-component layout

### DELETED files (0)

None — OverviewPage.tsx rewritten in place; inline primitives are deleted as code within the rewrite, not as files (they were never separate files). No orphan file delete this sprint.

### PRESERVED (not touched)

- `frontend/src/pages/overview/index.tsx` — re-export
- `frontend/src/features/loops/hooks/useActiveLoops.ts` — real data hook
- Sprint 57.24 v2 primitives (`components/ui/{CardShell,PageHead,BackendGapBanner}` + `components/charts/{Spark,StatCard,AreaChart,BarTrack}`) — reused; extended ONLY if Day-0 Prong 2 proves a gap (PageHead meta slot — decision US-B1)
- `backend/**` — 0 backend changes

## Acceptance Criteria

1. ✅ `/overview` renders all 9 mockup widget groups at 1440×900 per mockup `page-overview.jsx:74-266` 1:1
2. ✅ All 16 catalogued drifts D1-D14 + D16 closed (D15 maxTurns out-of-scope → carryover); DRIFT-REPORT documents each
3. ✅ Inline `Card`/`Badge`/`Stat`/`RiskBadge` migrated to shared `components/ui` + `components/charts` primitives (AP-3 violation reversed); 0 inline primitive definitions remain in OverviewPage.tsx
4. ✅ Real data preserved: `useActiveLoops(10)` feeds ActiveLoopsCard with loading/error/empty states intact
5. ✅ Fixture-backed widgets (HITL Queue / Providers / Incidents / Error Trend / Cost Burn) each ship a visible `<BackendGapBanner>` declaring AD-Overview-Backend-Extensions-Phase58 carryover (~4-5 banners)
6. ✅ KPI row 4 stats render WITH sparklines for Cost MTD + SLA p95 (D3 closed)
7. ✅ Vitest 430+N where N≥14 NEW cases; baseline preserved; existing OverviewPage spec adapted
8. ✅ Bundle KB delta ≤ +15 KB (shared primitives already shipped Sprint 57.24 v2; only NEW feature-scoped widgets + fixtures + i18n)
9. ✅ i18n EN + zh-TW parity for NEW keys; no missing-translation warnings on `npm run build`
10. ✅ Playwright MCP pair-verify (mockup 8080 + production 3007 at 1440×900); DRIFT-REPORT verdict = PARITY
11. ✅ visual-regression baseline for `/overview` regenerated via workflow_dispatch + cherry-pick (per AD #42 — page-visual change moves the snapshot; do NOT let CI surprise on it)
12. ✅ Commits + retrospective Q1-Q7 + calibration ratio (4th app data point) + rich-dashboard sub-class DECISION + memory snapshot + MEMORY.md +1 + sprint-workflow.md calibration matrix +1 row + CLAUDE.md minimal touch + PR landed

## Deliverables

- [ ] Plan + checklist drafted (this sprint Day 0)
- [ ] DRIFT-REPORT skeleton at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-27/artifacts/overview-rebuild/DRIFT-REPORT.md` with D1-D16 list
- [ ] AD-Overview-Backend-Extensions-Phase58 carryover added to `next-phase-candidates.md` (Day 3 closeout)
- [ ] 7 NEW feature-scoped widget components
- [ ] 6 NEW fixtures (hitlQueue / providers / incidents / errorTrend / costBurn / kpiSparklines)
- [ ] OverviewPage rewritten ~150-line assembly; mockup parity at 1440×900
- [ ] Inline primitives migrated to shared Sprint 57.24 v2 set (AP-3 reversal)
- [ ] Vitest ≥430+14 passing; existing OverviewPage spec adapted
- [ ] i18n EN + zh-TW NEW keys
- [ ] Playwright MCP pair-verify; code-level audit fallback if MCP blocked
- [ ] visual-regression baseline regenerated for `/overview`
- [ ] Retrospective Q1-Q7 + calibration ratio (4th app) + rich-dashboard sub-class DECISION + memory snapshot + MEMORY.md +1 + sprint-workflow calibration matrix +1 row + CLAUDE.md minimal touch + next-phase-candidates.md update
- [ ] PR opened + CI green + merge + post-merge cleanup

## Dependencies & Risks

### Dependencies

- Sprint 57.24 v2 7 primitives stable + present (Day 0 Prong 1 verify)
- `useActiveLoops` hook stable (Sprint 57.12 baseline; no expected drift)
- Sprint 57.18 wired tokens (oklch indigo + warning + success + risk tones) present
- Sprint 57.26 foundation tokens (html 13px / radius 8px / shell layout) merged to main `fb27df73`
- Sprint 57.23/57.24/57.25 visual-baseline workflow_dispatch + cherry-pick pattern (now also Sprint 57.26 evidence — AD #42)

### Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R1** | `<PageHead>` lacks a mono-meta slot → either extend a shared primitive (cross-consumer risk) or render sibling | MEDIUM | Day 0 Prong 2 reads PageHead API; default to feature-scoped sibling line (Karpathy §2 — don't extend shared primitive for 1 consumer) |
| **R2** | `<StatCard spark>` API mismatch with overview KPI needs | LOW | Sprint 57.25 already used `StatCard spark`; Day 0 Prong 2 confirms; if mismatch, fixture shape adapts to API not vice versa |
| **R3** | `<AreaChart>` cannot express CostBurnChart budget-diagonal → bespoke SVG needed | MEDIUM | Default decision: keep CostBurnChart bespoke feature-scoped SVG (mockup-direct port); do NOT force-fit AreaChart; ~95 lines budgeted |
| **R4** | 728-line OverviewPage rewrite scope underestimated (9 widgets) | MEDIUM | Widget extraction is mechanical (inline → file); 7 components × ~70 lines avg; Day 1 + Day 2 split 4+5 widgets; incremental commits per Day |
| **R5** | visual-regression `/overview` baseline | RESOLVED (Day 0) | Day 0 三-prong D-PRE-2: `/overview` is NOT in `visual-regression.spec.ts` (6-route list = app-shell / auth-login / cost-dashboard / governance / verification-recent / admin-tenants) → rebuild will NOT trigger a Sprint-57.26-style CI failure; risk removed. US-D3 MAY optionally add `/overview` to the spec for coverage (decision Day 3). |
| **R6** | Playwright MCP blocker (Sprint 57.22-57.25 history) | LOW | This session already drove Playwright MCP successfully (dev-login + screenshots + evaluate at 1440×900); MCP working; if it regresses → code-level audit fallback |
| **R7** | in-page title vs AppShellV2 topbar title duplication | LOW | US-B1 Day 1 decision: render in-page per mockup `page-overview.jsx:76` (`.page-title` confirmed present — D-PRE-8) + suppress/blank the topbar title for `/overview`; do NOT follow AUDIT-REPORT Unit 7's erroneous "Remove h1" action (D-PRE-8) |
| **R8** | 57.27 ratio outlier vs rich-dashboard sub-class decision | LOW | 4th data point feeds Day 3 retro Q4; decision rule pre-stated (next-phase-candidates #41); KEEP 0.60 baseline regardless this sprint |
| **R9** | D8 card-title fix (`text-sm` 14px → mockup 12.5px) lives in the shared `CardShell` primitive — touching it affects `/cost-dashboard` (57.24) + `/sla-dashboard` (57.25) | MEDIUM | Day 0 三-prong D-PRE-5. Day 1 decision: (a) change shared `CardShell` (corrects all 3 dashboards toward mockup; cheap Day 2/3 re-verify via Vitest + Playwright) or (b) leave `CardShell` + log a shared-primitive token-audit carryover. Default lean (a) — it is a correction, not a regression |
| **R10** | `Loop` type has no `agent_name` / `model` (backend Session ORM gap) — D4 loop-row content cannot fully close | LOW | Day 0 三-prong D-PRE-6. ActiveLoopsCard renders the mockup 5-col layout; `agent_name` / `model` are placeholder strings per the existing `features/loops/types.ts` mandate; folds to existing `AD-Loop-Session-Enrich-Phase58`. D4 reclassified = "layout closed; agent/model placeholder pending Phase 58" |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Risk Class A** (paths-filter vs `required_status_checks`): N/A — no `.github/workflows/` changes
- **Risk Class B** (cross-platform mypy unused-ignore): N/A — frontend-only
- **Risk Class C** (module-level singleton across test event loops): N/A — frontend Vitest

## Workload

| Group | Bottom-up est | Class haircut 0.60 | Day allocation |
|-------|---------------|--------------------|----------------|
| Group A (Day 0 setup + 三-prong + Prong 5) | ~0.6 hr | ~0.4 hr | Day 0 |
| Group B (page-head + KPI + Active Loops + HITL Queue) | ~2.5 hr | ~1.5 hr | Day 1 |
| Group C (Cost Burn + Providers + Incidents + Error Trend + Quick Actions) | ~2.7 hr | ~1.6 hr | Day 2 |
| Group D (i18n + integration + Vitest + closeout) | ~0.7 hr | ~0.4 hr | Day 3 |
| **Σ Bottom-up** | **~6.5 hr** | **~3.9 hr** | **4 working days (Day 0-3)** |

**Bottom-up est ~6.5 hr → calibrated commit ~3.9 hr (multiplier 0.60)**

Day 3 retrospective Q2: verify actual / committed ratio; expected range [0.85, 1.20]. 4th-app data point for the rich-dashboard sub-classification DECISION:
- 57.24 v2 = 1.19 / 57.25 = 0.88 → rich-dashboard 2-pt mean 1.04 (in-band middle)
- 57.27 ratio in band → DROP sub-class proposal; > 1.20 → reconsider rich ~0.70-0.75; < 0.85 → drop rich pattern entirely
- KEEP 0.60 baseline this sprint regardless

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + Prong 5 + DRIFT-REPORT skeleton

- [ ] Plan + checklist drafted (mirror Sprint 57.25 structure)
- [ ] Branch creation from main `fb27df73` (already created: `feature/sprint-57-27-overview-rebuild`)
- [ ] Day 0 三-prong: Prong 1 path verify (7 shared primitives + OverviewPage.tsx + features/overview/ dir) + Prong 2 content verify (PageHead/StatCard/CardShell/AreaChart APIs vs overview needs + useActiveLoops response shape) + Prong 4 test selector verify (existing OverviewPage spec + visual-regression.spec.ts overview snapshot)
- [ ] Day 0 Prong 5 audit cross-ref: grep Sprint 57.22 AUDIT-REPORT for overview row
- [ ] DRIFT-REPORT skeleton with D1-D16 list
- [ ] D-PRE findings catalogued in progress.md Day 0
- [ ] Fold Sprint 57.26 checklist §3.4 [x] marks (per user decision 2026-05-21) into Day 0 first commit

### Day 1 — Group B (page-head + KPI + Active Loops + HITL Queue)

- [ ] US-B1 page-head (in-page title + mono meta + Export + New Chat) + KPI row 4-stat WITH sparklines
- [ ] US-B2 ActiveLoopsCard (real data; D4 row content) + HITLQueueCard (fixture + banner)
- [ ] Vitest specs for ActiveLoopsCard (~4) + HITLQueueCard (~3)
- [ ] Playwright MCP pair-verify Day 1 widgets

### Day 2 — Group C (Cost Burn + Providers + Incidents + Error Trend + Quick Actions)

- [ ] US-C1 CostBurnChart + ErrorTrendChart (D16 axis labels)
- [ ] US-C2 ProvidersCard + IncidentsCard (D11 + D12)
- [ ] US-C3 QuickActionsStrip
- [ ] Vitest specs for 5 components (~12 cases)
- [ ] Playwright MCP pair-verify Day 2 widgets

### Day 3 — Group D + closeout

- [ ] US-D1 i18n EN + zh-TW NEW keys
- [ ] US-D2 OverviewPage final assembly + token drifts D6-D10/D14 + existing spec adapt
- [ ] US-D3 Vitest 430+14 passing
- [ ] Playwright MCP pair-verify full page (mockup 8080 + production 3007 at 1440×900)
- [ ] visual-regression baseline regenerate for `/overview` (workflow_dispatch + cherry-pick per AD #42)
- [ ] DRIFT-REPORT verdict = PARITY
- [ ] Retrospective.md Q1-Q7 + Q2 calibration ratio + Q4 rich-dashboard sub-class DECISION (4th data point)
- [ ] Memory snapshot `memory/project_phase57_27_overview_rebuild.md` + MEMORY.md +1 quality pointer
- [ ] `.claude/rules/sprint-workflow.md` calibration matrix +1 row (4th app) + MHist
- [ ] `next-phase-candidates.md` update (add AD-Overview-Backend-Extensions-Phase58 + resolve #41 sub-class decision)
- [ ] CLAUDE.md Current Sprint row + Last Updated footer (minimal touch per REFACTOR-001 §Sprint Closeout)
- [ ] PR open + CI green + merge + post-merge cleanup

---

**Plan drafted**: 2026-05-21 Day 0
**Sprint duration target**: 4 working days from Day 0 plan/checklist commit to PR merged
**Class**: `frontend-mockup-strict-rebuild` 0.60 (4th application; baseline KEEP per 3-sprint window rule; rich-dashboard sub-class DECISION sprint)
