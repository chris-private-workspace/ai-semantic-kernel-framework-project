# Sprint 57.31 — `/cost-dashboard` Verbatim-CSS Re-Point — REPOINT-REPORT

**Sprint**: 57.31 — AD-Cost-Dashboard-Verbatim-Repoint (3rd Phase-2 per-page re-point)
**Date**: 2026-05-23
**Branch**: `feature/sprint-57-31-cost-dashboard-repoint`
**Base SHA**: `8533603b` (main; Sprint 57.30 squash-merge — PR #164)
**Author**: AI (Sprint 57.31 Day 4 closeout)

---

## Summary

Sprint 57.31 lands the third Phase-2 per-page verbatim-CSS re-point on `/cost-dashboard`, continuing the epic after Sprint 57.29 (`/overview`) and Sprint 57.30 (`/chat-v2`). Day 1 batched delegation re-pointed 7 production files (1 page + 6 components) to consume mockup CSS classes directly (`.page-head` / `.grid-stats` / `.grid-main` / `.bar-track` / `.table` / `.spread` / `.col` / `.tnum` / `.thin-rule` / `.route-pill`) and mockup-ui primitives (`<Stat>` / `<Spark>` / `<AreaChart>` / `<Card>` / `<Badge>` / `<Icon>`) from the Sprint 57.29 verbatim foundation. Final Day-4 22-route regression sweep + `/cost-dashboard` fidelity verification confirms **PARITY** with mockup canonical `reference/design-mockups/page-admin.jsx:201-320` (the `CostPage` const).

The 22-route sweep shows **0 catastrophic / 0 structural / 0 cosmetic regressions on the 18 working AppShellV2 + Auth-shell routes** — all 18 are byte-identical or pixel-identical (timestamp-only delta on `/overview` from clock drift between captures). The 3 pre-existing crash routes (`/subagents` / `/memory` / `/verification`) show identical "Cannot read properties of undefined (reading 'length')" crash before == after, confirming the `AD-Overview-PreExisting-Route-Crashes` Sprint 57.29 carryover state — **NOT a Sprint 57.31 regression**. The 1 PROP stub route (`/compaction` via `prop-stub-compaction`) byte-identical. All 5 quality gates green (Vitest 452/452 / tsc strict / ESLint exit 0 / Vite build 3.15s / check:mockup-fidelity 25/25 HEX_OKLCH_BASELINE unchanged).

**Final verdict: 🟢 PARITY** on `/cost-dashboard` against mockup canonical CostPage; **🟢 PARITY** on all 18 working non-target routes; **⚪ Pre-existing fail unchanged** on 3 crash routes (out-of-scope).

---

## 22-Route Regression Sweep — Before vs After

Capture parameters: Playwright 1440×900 viewport, hermetic mocked backend per Sprint 57.14 CONVENTION §8, both captures from same dev server session (`route-sweep.mjs before` Day 0 / `route-sweep.mjs after` Day 4).

| # | Route | Before | After | Classification | Notes |
|---|-------|--------|-------|----------------|-------|
| 1 | `/` (home) | redirect → `/overview` | redirect → `/overview` | 🟢 PARITY | Shell + redirect chain unchanged |
| 2 | `/overview` | AppShellV2 + 5 widgets render | AppShellV2 + 5 widgets render | 🟢 PARITY | Pixel-identical except clock `19:06:45 → 19:22:49` topbar timestamp drift (capture-time only, not code change) |
| 3 | `/chat-v2` | 3-col chatv2 shell w/ Inspector | 3-col chatv2 shell w/ Inspector | 🟢 PARITY | Byte-identical; shell from Sprint 57.30 verbatim re-point unchanged |
| 4 | `/orchestrator` | AppShellV2 + content render | AppShellV2 + content render | 🟢 PARITY | Shell unchanged |
| 5 | `/subagents` | "Something went wrong / Cannot read properties of undefined (reading 'length')" | identical error UI | ⚪ Pre-existing fail | Sprint 57.29 carryover `AD-Overview-PreExisting-Route-Crashes`; out-of-scope this sprint |
| 6 | `/loop-debug` | AppShellV2 + LoopVisualizer | AppShellV2 + LoopVisualizer | 🟢 PARITY | Shell unchanged |
| 7 | `/memory` | "Something went wrong" same crash UI | identical error UI | ⚪ Pre-existing fail | Same carryover; out-of-scope |
| 8 | `/state-inspector` | AppShellV2 + StateInspector | AppShellV2 + StateInspector | 🟢 PARITY | Shell unchanged |
| 9 | `/compaction` (PROP stub via `prop-stub-compaction.png`) | PROP stub renderer with "Open mockup in new tab" link | identical | 🟢 PARITY | PROP stub component unchanged |
| 10 | `/governance` | AppShellV2 + governance content | identical | 🟢 PARITY | Shell unchanged |
| 11 | `/verification` | "Something went wrong" same crash UI | identical error UI | ⚪ Pre-existing fail | Same carryover; out-of-scope |
| 12 | **`/cost-dashboard`** | **Pre-rebuild scaffolding (Sprint 57.24 v2 strict-rebuild output) — translated Tailwind, misaligned AreaChart proportions, no route-pill + admin Badge in page-head, sparser TenantTopTable styling, missing thin-rule + LLM-neutrality disclosure** | **Verbatim mockup CSS — page-head with route-pill + admin scope Badge + By tenant/CSV actions; 4-stat .grid-stats KPI row; .grid-main rows w/ AreaChart "Spend over time" + CategoryBarsCard 6-row .bar-track; TenantTopTable .table w/ tenant icon chips + plan Badges + quota colors + anomaly dot; ProviderMixCard 4-row + .thin-rule + LLM-neutrality disclosure subtle; AP-2 BackendGapBanners** | 🟢 PARITY (target) | **Sprint 57.31 target re-point — see §`/cost-dashboard` Fidelity Verdict below for detailed evidence** |
| 13 | `/sla-dashboard` | AppShellV2 + 6 widgets render | identical | 🟢 PARITY | Shell + page (Sprint 57.25 rebuild) unchanged |
| 14 | `/admin-tenants` | AppShellV2 + admin table | identical | 🟢 PARITY | Shell unchanged |
| 15 | `/tenant-settings` | AppShellV2 + tenant settings tabs | identical | 🟢 PARITY | Shell unchanged |
| 16 | `/auth/login` | AuthShell + SAML/Microsoft/Google SSO + work-email form | identical | 🟢 PARITY | Auth shell (Sprint 57.23 rebuild) unchanged |
| 17 | `/auth/callback` | AuthShell processing card | identical | 🟢 PARITY | Auth shell unchanged |
| 18 | `/auth/mfa` | AuthShell + 6-digit input grid | identical | 🟢 PARITY | Auth shell unchanged |
| 19 | `/auth/register` | AuthShell + register form | identical | 🟢 PARITY | Auth shell unchanged |
| 20 | `/auth/invite` | AuthShell + invite-accept form | identical | 🟢 PARITY | Auth shell unchanged |
| 21 | `/auth/expired` | AuthShell + session-expired card | identical | 🟢 PARITY | Auth shell unchanged |
| 22 | `/auth/dev` | AuthShell + dev-login form | identical | 🟢 PARITY | Auth shell + dev-link gate (Sprint 57.23 R8) unchanged |

**Tally**: 🟢 PARITY × 18 (incl. target `/cost-dashboard`) + ⚪ Pre-existing fail × 3 (out-of-scope) + 🟢 PROP stub × 1 = **22 / 22 accounted, 0 Sprint-57.31-introduced regressions**.

---

## `/cost-dashboard` Fidelity Verdict

**Mockup canonical**: `reference/design-mockups/page-admin.jsx:201-320` — the `CostPage` const.
**Production**: `frontend/src/pages/cost-dashboard/index.tsx` + 6 components in `frontend/src/features/cost-dashboard/components/`.
**Evidence**: `screenshots/after/cost-dashboard.png` + `screenshots/day1-verify/day1-cost-dashboard-full.png` + `…-fold.png` + `…-table-anomaly.png`.

### Section mapping (mockup → production)

| Mockup section (line range) | Mockup elements | Production after-state evidence |
|----------------------------|-----------------|---------------------------------|
| **page-head** (L203-219) | `.page-head` w/ title "Cost Ledger" + subtitle "Range 12 · Token + tool spend · admin-only provider breakdown" + `.route-pill /cost-dashboard` + `<Badge tone="warning">admin scope</Badge>` + page-actions ("By tenant" filter + "CSV" download) | ✅ All 6 elements visible in `after/cost-dashboard.png`: title "Cost Ledger" / Range subtitle / `/cost-dashboard` route-pill chip / `admin scope` amber Badge / `By tenant` outline button w/ filter icon / `CSV` outline button w/ download icon |
| **grid-stats KPI row** (L221-225, 4 stats) | `<Stat>` × 4 (Spend MTD $2,847 +8.4% down / Tokens MTD 14.2 M +2.1M up / Cost per run $0.052 +$0.004 down / Cache hit rate 38% +4pp up) + each with `<Spark>` sparkline tone-coded | ✅ 4 KPI cards visible — `$2,847` + spark / `14.2 M` + spark / `$0.052` + spark / `38%` + spark; deltas with arrow direction tone-coded |
| **grid-main row 1 LEFT — AreaChart card** (L226-228) | `<Card title="Spend over time" subtitle="Daily · 30 days · stacked by category">` + `<AreaChart>` 30-point series tone=`var(--memory)` h=200 | ✅ "Spend over time" Card with subtitle + AreaChart curve visible top-left of grid-main row 1 |
| **grid-main row 1 RIGHT — CategoryBarsCard** (L230-251) | `<Card title="Spend by category" subtitle="Last 7 days">` + 6 rows (Inference input 44% / Inference output 27% / Thinking tokens 14% / Tool runs 10% / Embeddings 3% / Sandbox compute 2%) each with color dot + name + `$cost` + `.bar-track` pct | ✅ 6-row bar list w/ colored dots matching mockup palette (var(--thinking) / --primary / --info / --tool / --memory / --warning); right-aligned $ amounts in mono-tnum |
| **AP-2 BackendGapBanner row** (production-only honest gap) | n/a (production decision per Sprint 57.24 v2) | ✅ 2 amber AP-2 banners visible flagging backend pending for "Cost ledger by category" + "TenantTop quota%" — per AP-2 rule |
| **grid-main row 2 — TenantTopTable** (L253-294) | `<Card title="Spend by tenant" subtitle="MTD · top 8" bodyClass="flush">` + `.table` 8-row w/ Tenant (icon chip + mono name + optional anomaly Badge.danger.dot) / Plan Badge / Tokens (right tnum) / Cost (right tnum) / Quota used % tone-colored / `.bar-track` quota% | ✅ Visible: tenant icon chips (square w/ first-letter), mono tenant names (acme-prod / globex-eu / initech-jp / umbrella-us / wonka-apac / stark-prod / wayne-corp / tenant_3kp9), Plan Badges (Pro / Enterprise / Starter), right-aligned token/cost columns, quota% tone-colored (>100 red on wonka-apac & tenant_3kp9; >80 amber; default subtle), `anomaly` Badge.danger.dot on tenant_3kp9 (320% quota >100%) |
| **grid-main row 3 LEFT — ProviderMixCard** (L295-318) | `<Card title="Provider mix" subtitle="<Icon name='shield' size=11/> Admin-only · UI shields from operators">` + 4 rows (provider-A 57% / provider-B 31% / provider-C 9% / self-hosted 3%) each w/ color dot + mono name + cost + token-subtle + `.bar-track`; followed by `.thin-rule` + subtle LLM-neutrality disclosure | ✅ All visible: 4 provider rows w/ tone-coded bar fills (primary / thinking / tool / memory), cost + tokens-subtle right-aligned, `.thin-rule` divider, "Provider identity is redacted in operator views to enforce LLM-neutrality" subtle disclosure |
| **CostBreakdownTable** (production-only, D4 RED decided (c)) | n/a in mockup; production shows real backend `by_type` 2-level drill-down | ✅ Visible w/ mockup `.table` vocabulary; cost_type + sub_type + quantity + total_cost_usd + entry_count columns; no AP-2 banner needed (real backend data, no gap) |
| **MonthPicker** (production-only, D5 YELLOW) | n/a in mockup | ✅ Visible w/ mockup var(--*) token vocabulary inline (top-right of page near actions, "Month: May 2026" pill) |

### 8-12 visible mockup elements (evidence checklist)

1. ✅ `.page-head` w/ "Cost Ledger" title (24px h1)
2. ✅ `.route-pill /cost-dashboard` chip in subtitle
3. ✅ `<Badge tone="warning">admin scope</Badge>` amber pill
4. ✅ `.page-actions` w/ "By tenant" + "CSV" outline buttons + filter/download icons
5. ✅ `.grid-stats` 4-stat row (Spend MTD / Tokens MTD / Cost/run / Cache hit rate) w/ sparklines + tone-coded deltas
6. ✅ `<AreaChart>` "Spend over time" 30-point curve, tone `var(--memory)`
7. ✅ `<Card title="Spend by category">` 6-row `.bar-track` list w/ mockup color palette
8. ✅ `<Card title="Spend by tenant">` `.table` 8-row w/ tenant icon chips + plan Badges + quota colors + anomaly Badge.danger.dot
9. ✅ `<Card title="Provider mix">` 4-row + `.thin-rule` + LLM-neutrality disclosure subtle
10. ✅ Quota%-tone-coded text (var(--danger) >100%, var(--warning) >80%, var(--fg-muted) default)
11. ✅ `<Icon name="shield">` 11px subtitle inline in Provider mix Card
12. ✅ Mono `.tnum` tabular-numeric alignment on all $ amounts

**Verdict on `/cost-dashboard`: 🟢 PARITY** — all 5 mockup sections rendered structurally + visually matching mockup `page-admin.jsx:201-320` CostPage canonical. Production-only widgets (CostBreakdownTable / MonthPicker) use mockup token vocabulary correctly per AP-2 honesty rule (CostBreakdownTable has real backend so no AP-2 banner; MonthPicker is UI affordance so no AP-2 banner). Sprint 57.24 v2 reusable primitives (`<Stat>` / `<Spark>` / `<AreaChart>` / `<Card>` / `<Badge>` / `<Icon>` / `<BarTrack>` / `<BackendGapBanner>`) consumed without modification — pattern-reuse compounding validated 3rd application.

---

## Known structural deltas (production-only, by design)

These are **not regressions** and **not mockup-fidelity violations** — they are deliberate production-only additions per Day 0 三-prong findings D4 + D5 with explicit decisions captured in `progress.md`:

| Widget | Mockup status | Production decision | AP-2 banner? | Rationale |
|--------|---------------|---------------------|--------------|-----------|
| **CostBreakdownTable** | No mockup equivalent | Decision (c) production-only-by-design | **No** | Real backend data (`by_type` 2-level drill-down via authenticated tenant `/api/v1/cost-ledger`). Mockup `.table` vocabulary applied verbatim. No backend gap to surface. |
| **MonthPicker** | No mockup equivalent | Production-only UI affordance | **No** | Filter UI is a legitimate production-only widget (mockup omitted for layout simplification). Uses mockup `var(--fg-muted)` / `var(--border)` / `var(--bg-1)` token vocabulary inline. Not a backend gap. |
| AP-2 BackendGapBanner × 2 | No mockup equivalent | Honest backend gap surface | **Yes** (amber banner copy) | Sprint 57.24 v2 introduced banner pattern for cost-ledger-by-category aggregation + TenantTop quota% backend extension. Both real Phase 58+ carryovers per `AD-Overview-Backend-Extensions-Phase58` family. |

Per AP-2 rule (`anti-patterns-checklist.md`): production may add real-backend widgets without AP-2 banner; production may add UI affordances without AP-2 banner; production must add AP-2 banner only when surfacing a real backend gap. All three above comply.

---

## Sprint 57.31 NEW vs Sprint 57.30

| Aspect | Sprint 57.30 close state | Sprint 57.31 close state | Delta |
|--------|--------------------------|--------------------------|-------|
| **Vitest spec count** | 452/452 (94 files) | 452/452 (94 files) | 0 (testid + class-membership contracts preserved on cost-dashboard re-point) |
| **HEX_OKLCH_BASELINE** | 25 occurrences | 25 occurrences | 0 (no new oklch literals; all colors via `var(--*)` tokens) |
| **`check:mockup-fidelity` diff** | byte-identical | byte-identical | 0 (styles-mockup.css unchanged this sprint) |
| **Bundle KB** | (Sprint 57.30 -116.87 KB from Radix DropdownMenu drop) | unchanged from 57.30 baseline | 0 (no orphan cleanup this sprint — Sprint 57.30 already extracted the Radix bonus; nothing further to drop here) |
| **Vite build wall-clock** | (varies) | 3.15s | within ±0.3s of 57.30 baseline; no regression |
| **`tsc --strict`** | only pre-existing TS6310 carryover | only pre-existing TS6310 carryover | 0 |
| **ESLint** | exit 0 | exit 0 | 0 |
| **22-route regression sweep** | 0 catastrophic / 0 structural / 0 cosmetic | 0 catastrophic / 0 structural / 0 cosmetic | 0 |
| **Pre-existing crash routes** | 3 (subagents / memory / verification) | 3 (subagents / memory / verification) | 0 (still out-of-scope for this Phase-2 epic; `AD-Overview-PreExisting-Route-Crashes` carryover preserved for dedicated future sprint) |

No orphan cleanup this sprint — by design. Sprint 57.30 already harvested the Radix DropdownMenu / Drawer drop bonus when its shell re-point exposed unused dependencies. Sprint 57.31 cost-dashboard re-point swapped translated-Tailwind for verbatim mockup CSS classes but did not unlock new orphan removal targets — Sprint 57.24 v2 primitives (`<Stat>` / `<Spark>` / `<AreaChart>` / `<Card>` / `<BarTrack>`) are reused, not replaced. Bundle size unchanged is **the expected outcome** for a verbatim-CSS re-point sprint when the underlying scaffolding was already strict-rebuilt.

---

## Closing

**Totals**:
- 🟢 PARITY: **18** (incl. target `/cost-dashboard`) + 1 PROP stub = **19 routes byte/pixel-identical or mockup-aligned**
- 🟡 acceptable-cosmetic: **0**
- 🟠 structural-regression: **0**
- 🔴 catastrophic: **0**
- ⚪ Pre-existing fail (unchanged before == after): **3** (`/subagents` / `/memory` / `/verification` — out-of-scope per Sprint 57.29 `AD-Overview-PreExisting-Route-Crashes` carryover)

**Recommendation for Sprint 57.32**: continue Phase-2 per-page verbatim-CSS re-point epic on a 4th candidate. Per Sprint 57.30 + 57.31 retro pattern (frontend-verbatim-css-repoint 0.60 class 3-data-point evaluation pending Day 4 closeout), candidates include:
- **Bimodal-watch follow-on** — `/sla-dashboard` would test "rich-dashboard upper band" hypothesis again (already strict-rebuilt Sprint 57.25; same shape as `/overview` + `/cost-dashboard`)
- **AppShellV2 medium-shell routes** — `/orchestrator` / `/loop-debug` / `/state-inspector` / `/governance` (currently shell-rendered but with potentially-shadcn-translated content)
- **Crash-route fix** — dedicated sprint to repair `/subagents` / `/memory` / `/verification` per `AD-Overview-PreExisting-Route-Crashes` (out-of-scope this epic but high operator value)

Selection should weigh user-value ROI + 3rd-data-point bimodal calibration impact (per `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` Sprint 57.30 carryover ⇒ resolved this sprint per Day 4 retrospective Q2).

---

**Sign-off**: 🟢 Sprint 57.31 ready for commit + PR. Zero Sprint-57.31-introduced regressions. `/cost-dashboard` mockup-fidelity verdict PARITY. All 5 quality gates green. Pattern-reuse compounding validated 3rd Phase-2 application.

**Related**:
- Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-31-plan.md`
- Checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-31-checklist.md`
- Progress: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-31/progress.md`
- Mockup canonical: `reference/design-mockups/page-admin.jsx:201-320` (CostPage const)
- Predecessor reports: Sprint 57.29 `/overview` REPOINT-REPORT, Sprint 57.30 `/chat-v2` REPOINT-REPORT (Phase-2 epic)
