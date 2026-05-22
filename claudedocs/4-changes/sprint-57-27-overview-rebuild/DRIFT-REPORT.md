# Sprint 57.27 — `/overview` Mockup-Fidelity DRIFT-REPORT

**Sprint**: 57.27 — AD-Mockup-Fidelity-Rebuild-Overview
**Mockup ref**: `reference/design-mockups/page-overview.jsx:74-379` + `styles.css` (`.card` / `.stat` / `.badge` / `.page-head`)
**Production ref**: `frontend/src/pages/overview/OverviewPage.tsx` (728-line all-in-one close port — Sprint 57.19 commit `f8949504` + 57.20 `d6cc70bd`)
**Status**: ✅ Day 3 closeout — final verdict **PARITY**
**Viewport**: 1440×900 (mockup `:8080` vs production `:3007`); pair-verify screenshots `sprint-57-27-{mockup,prod}-overview.png`

---

## §1 — 16-Drift list (Day 0 agent exploration)

| ID | Drift | Class | Closed by | Day 0 note |
|----|-------|-------|-----------|------------|
| D1 | In-page page-head title — mockup `:76` `.page-title` present; prod delegates to AppShellV2 topbar | structural | US-B1 | D-PRE-8: AUDIT-REPORT Unit 7 wrongly said mockup has no title; mockup DOES (`:76`). Render in-page. |
| D2 | Mono `tenant · role · clock` meta line missing (mockup `:80`) | cosmetic | US-B1 | Rendered inside PageHead `subtitle` ReactNode (D-PRE-4) |
| D3 | KPI sparklines — mockup Cost MTD (`:93`) + SLA p95 (`:94`) pass `spark`; prod inline Stat has no spark | functional/cosmetic | US-B1 | StatCard `spark` prop confirmed present (D-PRE-5) |
| D4 | Active Loops row content — mockup agent+session+tenant+model; prod session-id only | structural | US-B2 | D-PRE-6: backend `Loop` type has no `agent_name`/`model` → layout closed, agent/model placeholder |
| D5 | `stat-spark` styling absent | cosmetic | US-B1 | Via shared StatCard |
| D6 | Card radius literal `rounded-[12px]` vs `--radius-lg` token | cosmetic | US-D2 | CardShell already `rounded-[12px]` = 12px (visually OK; token-purity only) |
| D7 | Card-head padding `px-4 py-3` vs mockup `11px 14px` | cosmetic | US-D2 | In shared CardShell (D-PRE-5) |
| D8 | Card-title `text-sm` 14px vs mockup `.card-title` 12.5px | cosmetic | US-D2 / R9 | **In shared CardShell** — R9 Day 1 decision (change shared vs carryover) |
| D9 | Stat padding | cosmetic | US-D2 | StatCard `px-4 py-3.5` = 16/14px ≈ mockup `.stat` `14px 16px` — OK (D-PRE-5) |
| D10 | Stat delta glyph `▲/▼` → SVG icon | cosmetic | US-B1 | Shared StatCard already uses `<ArrowUp/Down>` SVG — auto-closed |
| D11 | Badge pill → mockup `.badge` 4px radius | cosmetic | US-C2 | — |
| D12 | RiskBadge tone map — prod `medium→info`; mockup `risk-medium→--warning` | cosmetic | US-C2 | — |
| D13 | HITL critical bg tint approximation | cosmetic | US-B2 | — |
| D14 | Page-wrapper `gap` vs mockup per-row `marginBottom` | cosmetic | US-D2 | — |
| D15 | Active Loops `maxTurns` hardcoded 50 | functional | carryover | Backend gap — AD-Loop-Session-Enrich-Phase58 |
| D16 | CostBurnChart + ErrorTrendChart drop x-axis labels + budget-line label | structural | US-C1 | — |
| D17 | CostBurnChart + ErrorTrendChart carry `<BackendGapBanner>` (NOT in mockup) | accepted addition | US-C1 | Day 2 decision: of 9 widgets only ActiveLoopsCard has real data; 8 are fixture-backed. AP-2/AP-4 honesty — fixture data must be declared. Banner is the project-wide honesty escape hatch (used Sprint 57.24/57.25). DRIFT-REPORT §4 already lists Cost Burn + Error Trend as backend gaps. Justified deliberate drift, not a fidelity defect. |

## §2 — 9-Widget mockup-vs-production matrix (filled Day 1-3)

| # | Widget | Mockup ref | Day | Verdict | Note |
|---|--------|-----------|-----|---------|------|
| A | page-head | `:74-87` | 3 | ✅ PARITY | `<PageHead>` in-page title + `/overview` route-pill + mono meta (real authStore `acme-prod · user · clock`) + Export/New Chat actions. D1+D2 closed; R7 topbar-dup suppressed. Pair-verify ✅. |
| B | KPI row 4-stat | `:90-95` | 3 | ✅ PARITY | 4× `<StatCard>` (14 loops / 3 approvals / $2,847 / 1.84s) + 2× `<Spark>` on Cost MTD + SLA p95. D3+D5+D10 closed. Pair-verify ✅. |
| C | Active Loops card | `:99-141` | 1 | ✅ PARITY (layout) | `ActiveLoopsCard.tsx`; 5-col loopRow layout + loading/error/empty states faithful. ⚠️ **Live render shows error state** — `useActiveLoops` → `GET /api/v1/loops?status=running` returns 404 (endpoint absent in dev backend). Pre-existing backend gap (Day 1 extraction preserved the hook from prior inline `OverviewPage`); NOT a Sprint 57.27 rebuild defect. → §4 carryover. |
| D | HITL Queue card | `:143-167` | 1 | ✅ PARITY | `HITLQueueCard.tsx`; 3 risk-tinted cards (HIGH/MEDIUM/CRITICAL), D13 critical tint closed; fixture + BackendGapBanner. Pair-verify ✅. |
| E | Cost Burn chart | `:172-178, 273-329` | 2 | ✅ PARITY | `CostBurnChart.tsx`; bespoke SVG burn line + budget diagonal + gridlines + axis labels (D16). +BackendGapBanner (D17 accepted). Pair-verify ✅. |
| F | Providers card | `:180-199` | 2 | ✅ PARITY | `ProvidersCard.tsx`; 4 traffic-dot rows, glow via `color-mix(in oklch …)` ≡ mockup `oklch(from …)`. Pair-verify ✅. |
| G | Recent Incidents card | `:204-225` | 2 | ✅ PARITY | `IncidentsCard.tsx`; 4 rows RiskBadge + id + title + status Badge + since; D11+D12 closed via `_primitives.tsx`. Pair-verify ✅. |
| H | Error Trend chart | `:227-233, 331-379` | 2 | ✅ PARITY | `ErrorTrendChart.tsx`; 24-bar histogram, tone-by-value, axis labels (D16). +BackendGapBanner (D17 accepted). Pair-verify ✅. |
| I | Quick Actions strip | `:236-266` | 2 | ✅ PARITY | `QuickActionsStrip.tsx`; 4-button flex strip (New Chat / Review / Tenants / Verification). Pair-verify ✅. |

## §3 — Final verdict (Day 3)

✅ **PARITY** — Playwright MCP pair-verify at 1440×900 (mockup `:8080` vs production `:3007`, dev-login `acme-prod`). Structural + cosmetic parity across all 9 widgets: page-head, 4-stat KPI row with 2 sparklines, grid2 (1.4fr+1fr), grid2eq×2, quick-actions strip — all faithfully reproduce the mockup layout.

- **Drift closure**: D1-D14 + D16 closed; D17 = accepted deliberate addition (BackendGapBanner honesty, not in mockup).
- **Carryover**: D15 (`maxTurns` hardcoded) + ActiveLoopsCard live-data 404 (see §4).
- **One noted divergence** (NOT a rebuild defect): Widget C (Active Loops) renders its designed **error state** in production because the backing `GET /api/v1/loops` endpoint is absent (404). The mockup shows the happy-path with 5 fixture loop rows; production shows the honest error panel. The widget's layout, 5-col row structure, and loading/error/empty states are all faithful to the mockup — the divergence is backend-data, not frontend fidelity.

## §4 — Carryover

- **D15** — Active Loops `maxTurns` hardcoded 50; backend `Session` ORM gap → existing `AD-Loop-Session-Enrich-Phase58`.
- **ActiveLoopsCard live-data 404** (NEW finding, Day 3 pair-verify) — `useActiveLoops` → `fetchLoops` → `GET /api/v1/loops?status=running` returns 404; the backend loops-list endpoint does not exist. Pre-existing (the hook + `loopsService` predate Sprint 57.27; Day 1 extraction preserved them). Resolution options for Phase 58: (a) build the `GET /api/v1/loops` list endpoint, or (b) fixture-back ActiveLoopsCard like the other 8 widgets until the endpoint exists. → fold into `AD-Overview-Backend-Extensions-Phase58`.
- **AD-Overview-Backend-Extensions-Phase58** (NEW; Day 3 → next-phase-candidates.md) — 8 fixture-backed `/overview` widgets (HITL Queue / Providers / Incidents / Error Trend / Cost Burn / KPI stats) + the absent `GET /api/v1/loops` endpoint need real backend aggregation/list APIs.
- **R9 outcome** — RESOLVED: Option A (user decision 2026-05-21). Shared `CardShell` card-title `text-sm` → `text-[12.5px]` (closes D8). Side-effect: `/cost-dashboard` (57.24) + `/sla-dashboard` (57.25) also consume `CardShell` → both shift toward mockup `.card-title` 12.5px. Pure mockup-fidelity correction (those 2 pages had the same D8 drift unnoticed), not a regression. **Carryover**: a light pair-verify pass on `/cost-dashboard` + `/sla-dashboard` to confirm the 12.5px title looks right — fold into the next dashboard-touching sprint or a shared-primitive token-audit AD.
