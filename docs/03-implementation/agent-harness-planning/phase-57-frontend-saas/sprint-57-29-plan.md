---
sprint: 57.29
phase: Phase 57+ Frontend SaaS 26/N (pending close)
title: AD-Overview-Verbatim-Repoint — /overview + App Shell (incl. topbar overlays) Phase-2 Per-Page Re-Point (1st application of the verbatim re-point method)
class: frontend-verbatim-css-repoint 0.60 (NEW class; 1st application; HYBRID weighted blend — shell re-point no-PoC ×0.65 ~25% + topbar overlays re-point ×0.60 ~15% + /overview content re-point PoC-precedented ×0.55 ~35% + ui.jsx verbatim primitive port ×0.55 ~10% + 22-route regression sweep ×0.50 ~8% + closeout ×0.80 ~7% ≈ 0.60)
duration_days: 6 (Day 0 plan + 三-prong + before-baseline / Day 1 shell primitives + AppShellV2 + Sidebar / Day 2 Topbar + 3 overlays / Day 3 shell spot-check + /overview primitives + OverviewPage / Day 4 9 widgets / Day 5 22-route sweep + /overview fidelity verify + Vitest + closeout)
related:
  - docs/rules-on-demand/frontend-mockup-fidelity.md (authoritative verbatim-CSS method + 4-layer protocol + DoD — this sprint executes Phase 2 per-page re-point)
  - claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md §5 Phase 2 (per-page re-point — this sprint is the 1st)
  - docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/artifacts/mockup-fidelity-foundation/FOUNDATION-SWITCH-REPORT.md (Phase 1 foundation; §5 Phase-2 backlog lists /overview as transition-drift)
  - investigation/mockup-fidelity-poc branch (commit 53ca61fc — proven /overview content re-point; pages/overview-poc/index.tsx + components.tsx — the content-layer template)
  - Sprint 57.28 plan + checklist (frontend-verbatim-css-foundation 0.55; closest prior class; route-sweep.mjs + 三-prong + before/after-sweep model reused)
  - Sprint 57.27 plan (the /overview structural rebuild — 215-line clean assembly this sprint re-points)
  - reference/design-mockups/page-overview.jsx (canonical /overview content — visual source)
  - reference/design-mockups/shell.jsx + app.jsx (canonical shell — Sidebar + Topbar + App grid — visual source)
  - reference/design-mockups/topbar-overlays.jsx (canonical CommandPalette + NotificationsPanel + UserMenu — visual source)
  - reference/design-mockups/ui.jsx (canonical primitive set — Icon/Button/Badge/Card/Stat/RiskBadge)
  - reference/design-mockups/styles.css == frontend/src/styles-mockup.css (Layer 2 — all 251 classes incl. 24 shell classes already verbatim-present)
  - .claude/rules/sprint-workflow.md §Scope-class multiplier matrix + §Step 2.5 (Day-0 three-prong verify)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-22 verbatim-CSS method)
---

# Sprint 57.29 — AD-Overview-Verbatim-Repoint

## Sprint Goal

Re-point `/overview` — **the page content AND the full shared app shell** (`AppShellV2` + `Sidebar` + `Topbar` + the 3 topbar overlays `CommandPalette` / `NotificationsPanel` / `UserMenu`) — from translated-Tailwind markup to **direct consumption of the verbatim mockup CSS classes** that Sprint 57.28 already loaded into the production build (`styles-mockup.css`). This makes `/overview` the **first fully mockup-faithful screen** (frame + content + overlays) and establishes the **per-page re-point method/template** for the rest of the Phase-2 epic. A 22-route regression sweep proves the shared-shell re-point ships with **0 catastrophic breakage** to the other 18 routes.

**Two-line philosophy**:

1. **Consume, do not translate** — Sprint 57.28 landed `styles-mockup.css` (251 classes incl. all 24 shell classes, byte-identical, oklch). The drift never came from execution; it came from re-expressing the mockup CSS as Tailwind utilities. This sprint deletes that step for `/overview` + the shell: components emit the mockup class names directly (`className="card"`, `className="sidebar"`); only the component-logic layer (hooks / API / i18n / routing) is rewritten — the CSS is consumed, never re-composed.
2. **Prove one screen end-to-end, then scale** — per user directive 2026-05-22: succeed on one full screen before re-pointing the rest. `/overview` is chosen because its content has a proven PoC re-point (`investigation/mockup-fidelity-poc`) and was already structurally rebuilt clean in Sprint 57.27. The shell + overlays are included so the proof covers a complete real screen; the shell is a one-time shared cost — after this sprint every subsequent page re-point is content-only.

## Background

### Why Sprint 57.29 (this sprint)

Sprint 57.28 landed **Phase 1 — the verbatim-CSS foundation only**: `frontend/src/styles-mockup.css` is now a byte-identical copy of `reference/design-mockups/styles.css`, imported globally. But Phase 1 did not touch any page markup — every `active` route still consumes translated Tailwind utilities layered on the new foundation. The FOUNDATION-SWITCH-REPORT classified 19 routes as 🟡 transition-drift and named **Phase 2 — per-page re-point** as the backlog: rewrite each page's markup to consume mockup classes directly, so it gets CSS fidelity "for free" from the correct foundation.

`/overview` is the **first** Phase-2 re-point because:
- **It has a proven content-layer template** — the `investigation/mockup-fidelity-poc` PoC re-pointed `/overview` content to byte-identical computed-style fidelity (`pages/overview-poc/index.tsx` + `components.tsx`); this sprint ports that proven pattern into the real `OverviewPage` and re-adds the i18n / API logic the PoC intentionally omitted.
- **Its structure is already clean** — Sprint 57.27 rebuilt `OverviewPage.tsx` into a 215-line assembly (AP-3 reversal complete); only the `className` layer needs swapping, not a structural rebuild.

**Σ bottom-up**: ~22.5 hr (mid) before calibration
**Calibrated commit**: ~22.5 hr × 0.60 ≈ ~13.5 hr (NEW class baseline)

### Why content + full shell together (Option B + overlays — user-approved 2026-05-22)

`/overview` re-point scope was decided by AskUserQuestion 2026-05-22: **Option B — page content + shell together**, then a follow-up confirmation to **also include the 3 topbar overlays**. Rationale recorded:
- The shell (`AppShellV2` + `Sidebar` + `Topbar` + overlays) wraps / is mounted by **all 19 authenticated routes**. Re-pointing it once is a one-time shared cost that benefits every page — after this sprint, every subsequent Phase-2 page re-point is **content-only**.
- The user's goal is a fully mockup-faithful **screen** (frame + content + the ⌘K palette / notifications / user-menu the topbar opens), not faithful content inside a translated frame.
- **Accepted cost**: the shell re-point has a 19-route blast radius and the overlays add ~620 LoC. This sprint therefore runs **6 days** and includes a **22-route regression sweep** (reuse `route-sweep.mjs`, before/after, same model as Sprint 57.28) to confirm 0 catastrophic breakage to the other 18 routes. Those 18 routes' **content stays translated** — only their shell chrome changes; expected chrome shift is catalogued as transition-drift, not fixed here.

### Scope boundaries

| | Scope |
|---|---|
| **IN** | `/overview` page content (`OverviewPage.tsx` + 9 `features/overview/` widgets + `_primitives.tsx`) · core shell (`AppShellV2` + `Sidebar` + `Topbar`) · 3 topbar overlays (`CommandPalette` + `NotificationsPanel` + `UserMenu`) · NEW verbatim primitive module ported from mockup `ui.jsx` · 22-route regression sweep · `/overview` computed-style fidelity verification vs mockup |
| **OUT — not touched** | shared `CardShell` / `PageHead` / `StatCard` (`/overview` stops importing them and uses the verbatim primitives instead; the files stay untouched for `/cost-dashboard` + `/sla-dashboard`, whose own Phase-2 sprints re-point them) · the other 18 routes' page **content** (only their shell chrome changes) · `backend/**` · routing / auth / i18n keys |

### Class baseline — NEW class `frontend-verbatim-css-repoint` 0.60

No prior class fits cleanly:
- `frontend-verbatim-css-foundation` 0.55 (Sprint 57.28) — the foundation switch (verbatim copy + token bridge + CI guard); this sprint is the per-page re-point that consumes that foundation — different work.
- `frontend-mockup-strict-rebuild` 0.60 (Sprint 57.23-57.27) — the **translate-rebuild** method now superseded by the verbatim method; the multiplier value is reused but the class is renamed because the method changed (verbatim re-point ≠ translate-rebuild).

→ NEW class `frontend-verbatim-css-repoint` 0.60, HYBRID weighted blend: shell re-point (no PoC precedent — greenfield-ish) ×0.65 (~25%) + topbar overlays re-point ×0.60 (~15%) + `/overview` content re-point (PoC-precedented) ×0.55 (~35%) + `ui.jsx` verbatim primitive port ×0.55 (~10%) + 22-route regression sweep ×0.50 (~8%) + closeout ×0.80 (~7%) ≈ 0.60. 1st application; Day 5 retrospective Q2 records the actual/committed ratio as the 1st data point; KEEP 0.60 baseline regardless (1 data point insufficient to adjust per `When to adjust` 3-sprint window rule).

### What is preserved (NOT changed)

| Layer | Specific | Reason |
|-------|----------|--------|
| Routing | `react-router-dom` `<Link>` / `useLocation()` — NOT the mockup's `location.hash` routing | Production routing model unchanged; only DOM/className ported |
| Auth | `RequireAuth` / `useAuthStore` (user / tenant / roles) | Untouched |
| Route registry | `routes.config.ts` (`ROUTES` + `CATEGORY_ORDER`) | Consumed as-is by the re-pointed `Sidebar` |
| `data-testid` contracts | `app-shell` / `sidebar-toggle` / `topbar` / `topbar-cmdk` / `topbar-theme` / `notifications-bell` / `auth-shell` + every overview + overlay testid | Playwright e2e + Vitest depend on them; re-point swaps `className` only, NEVER drops a testid |
| Library interaction layer | `cmdk` (CommandPalette) + Radix `Dialog`/`DropdownMenu` primitives | Re-point ports the VISUAL (mockup classes + inline styles); the library interaction/keyboard/focus layer is preserved |
| Component logic | `useUIStore` collapse · ⌘K hotkey + overlay open/close state · `useTheme` toggle · `useActiveLoops(10)` real data hook + loading/error/empty branches · live-clock `useEffect` · KPI sparkline fixtures · notification fixtures · tenant-switch handler · all `navigate()` handlers | Only the `className` / DOM-structure / inline-style layer is re-pointed |
| i18n | `frontend/src/i18n/**` — every `nav.*` / `shell.*` / `topbar.*` / `overview.*` key | 0 i18n key changes — `t()` calls preserved verbatim |
| Other 18 routes' content | every non-`/overview` page body | Only their shared shell chrome changes |
| `Spark.tsx` | `components/charts/Spark.tsx` | Token-neutral pure SVG — reused as-is, 0 change |
| `CardShell` / `PageHead` / `StatCard` | the old shared primitives | `/overview` stops importing them; files untouched for cost/sla dashboards |
| Backend | `backend/**` | 0 backend changes |
| `investigation/mockup-fidelity-poc` branch | the PoC | Left as reference; NOT merged |

### What gets changed (this sprint scope)

| Area | File | Approach |
|------|------|----------|
| Primitives | NEW `frontend/src/components/mockup-ui.tsx` | Typed-TSX verbatim port of `reference/design-mockups/ui.jsx` (`Icon` / `Button` / `Badge` / `Card` / `Stat` / `RiskBadge`); emits mockup class strings verbatim. Reference: PoC `pages/overview-poc/components.tsx` |
| Shell | `frontend/src/components/AppShellV2.tsx` | Re-point to `.app` / `.main` / `.content` (+ `.fullbleed`); preserve `data-collapsed`, `fullBleed` prop, `app-shell` testid |
| Shell | `frontend/src/components/Sidebar.tsx` | Re-point to `.sidebar` / `.sidebar-head` / `.brand-*` / `.tenant-switcher` / `.nav` / `.nav-section` / `.nav-item` / `.nav-icon` / `.nav-label` / `.nav-badge` / `.sidebar-foot` / `.user-card` + verbatim inline-style nav-badge / avatar; preserve `<Link>`/`useLocation` active state, `routes.config.ts` registry, `useUIStore` collapse, i18n, `sidebar-toggle` testid |
| Shell | `frontend/src/components/layout/Topbar.tsx` | Re-point to `.topbar` / `.crumb` / `.here` / `.route-pill` / `.tenant-pill` / `.topbar-spacer` / `.cmdk` / `.kbd` / `.avatar` + verbatim inline locale / theme divider / bell badge; preserve ⌘K, theme toggle, overlay triggers, `topbar` / `topbar-cmdk` / `topbar-theme` / `notifications-bell` testids |
| Overlay | `frontend/src/components/topbar/CommandPalette.tsx` | Re-point to the verbatim mockup `topbar-overlays.jsx` `CommandPalette` markup (classes + inline styles); preserve the `cmdk` library + Radix `Dialog` interaction layer + ⌘K hotkey + navigation |
| Overlay | `frontend/src/components/topbar/NotificationsPanel.tsx` | Re-point to verbatim mockup `NotificationsPanel` markup; preserve open/close state, notification fixtures, mark-all handler |
| Overlay | `frontend/src/components/UserMenu.tsx` | Re-point to verbatim mockup `UserMenu` markup; preserve `useAuthStore`, tenant-switch handler, nav items |
| Page | `frontend/src/pages/overview/OverviewPage.tsx` | Re-point to `.page-head` / `.page-title` / `.page-sub` / `.route-pill` / `.page-actions` + verbatim inline `overviewStyles` (`page` / `kpiRow` / `grid2` / `grid2eq`); preserve i18n / `navigate` / `authStore` / live-clock |
| Page widgets | `frontend/src/features/overview/components/` ×9 (`ActiveLoopsCard` / `HITLQueueCard` / `ProvidersCard` / `IncidentsCard` / `QuickActionsStrip` / `CostBurnChart` / `ErrorTrendChart` + `_primitives.tsx`) | Re-point to `.card` / `.card-head` / `.card-title` / `.card-sub` / `.card-body` (`.dense`/`.flush`) / `.row` / `.col` / `.mono` / `.subtle` / `.muted` / `.badge` / `.stat` + verbatim inline tints (`loopRow` / `miniBar` / `quickBtn` / `oklch()` risk tints / `trafficDot()`); preserve `useActiveLoops`, fixtures, `BackendGapBanner`, navigation |
| Test | `frontend/tests/unit/**` shell/overview/overlay specs | Adapt selectors/assertions for re-pointed class names (NOT delete; testids preserved so most specs unaffected) |
| Harness | `frontend/scripts/route-sweep.mjs` | `OUT_DIR` re-point 57.28 → 57.29 + header MHist (same as 57.28 did) |

## User Stories

### Group A — Day 0 plan + 三-prong + before-baseline (PRE-WORK)

**US-A1**: As the Sprint 57.29 owner, I want plan + checklist landed, a Day-0 三-prong verify (Prong 1 path verify on all ~16 target files + `mockup-ui.tsx`-absent; Prong 2 content verify — every mockup class used by `page-overview.jsx` / `shell.jsx` / `app.jsx` / `topbar-overlays.jsx` confirmed present in `styles-mockup.css`, the full `data-testid` contract enumerated, the current translated-`className` inventory, the `ui.jsx` primitive set; Prong 4 test-selector verify on shell/overview/overlay Vitest specs), a before-baseline 1440×900 screenshot of all 22 routes via the reused `route-sweep.mjs`, and a REPOINT-REPORT skeleton — so that Day 1+ builds on a verified baseline and the before/after sweep + `/overview` fidelity verification have a fixed reference set.

### Group B — Shell + overlays re-point (Day 1-3)

**US-B1**: As a frontend operator, I want NEW `frontend/src/components/mockup-ui.tsx` — the mockup `ui.jsx` primitives (`Icon` / `Button` / `Badge` / `Card` / `Stat` / `RiskBadge`) ported to typed TSX that emit mockup class strings verbatim — so that the shell, the overlays, and `/overview` consume one verbatim primitive set instead of translated Tailwind components (reference: PoC `pages/overview-poc/components.tsx`).

**US-B2**: As a frontend operator, I want `AppShellV2.tsx` re-pointed to consume `.app` / `.main` / `.content` (+ `.fullbleed`) directly — preserving `data-collapsed`, the `fullBleed` prop, and the `app-shell` testid — so that the screen frame's outermost grid matches the mockup `app.jsx` verbatim.

**US-B3**: As a frontend operator, I want `Sidebar.tsx` re-pointed to consume the verbatim mockup sidebar classes (`.sidebar` / `.sidebar-head` / `.brand-mark` / `.brand-text` / `.brand-name` / `.brand-sub` / `.tenant-switcher` / `.tenant-avatar` / `.nav` / `.nav-section` / `.nav-item`[`data-active`] / `.nav-icon` / `.nav-label` / `.nav-badge` / `.sidebar-foot` / `.user-card`) plus the verbatim inline styles (nav-badge PROP/DRAFT colours, sidebar-foot avatar gradient) — preserving `react-router` `<Link>`/`useLocation` active-state, the `routes.config.ts` registry + `CATEGORY_ORDER` 6-group nav, `useUIStore` collapse, i18n `nav.*` keys, and the `sidebar-toggle` testid — so that the sidebar matches the mockup `shell.jsx` `Sidebar` verbatim.

**US-B4**: As a frontend operator, I want `Topbar.tsx` re-pointed to consume the verbatim mockup topbar classes (`.topbar` / `.crumb` / `.here` / `.route-pill` / `.tenant-pill` / `.dot` / `.topbar-spacer` / `.cmdk` / `.kbd` / `.avatar`) plus the verbatim inline styles (locale button, theme divider, bell unread badge) — preserving the ⌘K hotkey + command-palette trigger, the theme toggle, the notifications + user-menu triggers, i18n `topbar.*` keys, and the `topbar` / `topbar-cmdk` / `topbar-theme` / `notifications-bell` testids — so that the topbar matches the mockup `shell.jsx` `Topbar` verbatim.

**US-B5**: As a frontend operator, I want the 3 topbar overlays — `CommandPalette.tsx` / `NotificationsPanel.tsx` / `UserMenu.tsx` — re-pointed to consume the verbatim mockup `topbar-overlays.jsx` markup (classes + inline styles) — preserving the `cmdk` library + Radix `Dialog`/`DropdownMenu` interaction layer, the ⌘K hotkey, navigation, the notification fixtures + mark-all handler, and the `useAuthStore` tenant-switch handler — so that opening the ⌘K palette / notifications / user-menu from the re-pointed topbar shows verbatim-mockup overlays, completing the `/overview` screen experience.

### Group C — /overview content re-point (Day 3-4)

**US-C1**: As a frontend operator, I want `OverviewPage.tsx` re-pointed — `.page-head` / `.page-title` / `.page-sub` / `.route-pill` / `.page-actions` + the verbatim inline `overviewStyles` object (`page` / `kpiRow` / `grid2` / `grid2eq`) ported from `page-overview.jsx` — preserving `useTranslation`, `useNavigate`, `useAuthStore`, the live-clock `useEffect`, and `RequireAuth`+`AppShellV2` wrapping — so that the `/overview` page-head + grid layout match the mockup verbatim.

**US-C2**: As a frontend operator, I want the 9 `features/overview/` widgets re-pointed to consume `.card` / `.card-head` / `.card-title` / `.card-sub` / `.card-body`(`.dense`/`.flush`) / `.row` / `.col` / `.mono` / `.subtle` / `.muted` / `.tnum` / `.badge` / `.stat`* + the verbatim inline tints (`loopRow` / `miniBar` / `quickBtn` / risk `oklch()` tints / `trafficDot()`) — preserving `useActiveLoops(10)` real data + loading/error/empty branches, the HITL/Providers/Incidents/Error fixtures, `BackendGapBanner`, the SVG charts (already token-correct), and all navigation — so that every `/overview` widget matches the mockup verbatim. `_primitives.tsx` is re-pointed or deleted-if-orphaned once superseded by `mockup-ui.tsx`.

### Group D — Regression sweep + /overview fidelity verification (Day 5)

**US-D1**: As the Sprint 57.29 owner, I want all 22 routes re-screenshotted at 1440×900 after the shell re-point and diffed against the Day-0 before-baseline, then triaged — catastrophic breakage (page crash / unusable) fixed in-sprint; expected shell-chrome transition-drift on the 18 not-content-re-pointed routes catalogued in the REPOINT-REPORT; structural regressions logged as carryover ADs — so that the shared-shell re-point ships with 0 catastrophic breakage (NOT silently shipped).

**US-D2**: As the Sprint 57.29 owner, I want `/overview` verified against the mockup per the Mockup-Fidelity DoD — Playwright screenshot of the mockup (`:8080`) vs production (`:3007`) at 1440×900, plus **computed-style measurement** of representative elements (page-head, a card, a stat, the sidebar, the topbar) and layout dimensions, plus the ⌘K palette / notifications / user-menu overlays opened and compared — with drift classified and a parity verdict recorded in the REPOINT-REPORT — so that "the `/overview` screen reproduces the mockup" is proven by measurement, not by eye.

### Group E — Vitest + closeout (Day 5)

**US-E1**: As the Sprint 57.29 owner, I want the Vitest baseline (457/457 from Sprint 57.28) preserved — adapting any shell/overview/overlay spec whose selector changed (testids preserved, so most specs are unaffected; NOT deleting tests) — plus `npm run lint` exit 0, `npm run build` green, `npm run check:mockup-fidelity` green, and the bundle KB delta recorded — so that the re-point ships without test / build / guard regression.

**US-E2**: As the Sprint 57.29 owner, I want the REPOINT-REPORT finalised (per-route sweep verdict + `/overview` parity verdict + the established re-point method/template for the next Phase-2 sprint), commits + retrospective Q1-Q7 with the 1st-data-point calibration ratio for the NEW `frontend-verbatim-css-repoint` class, memory snapshot + MEMORY.md +1 quality pointer, `.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row, CLAUDE.md Current Sprint row + Last Updated footer (REFACTOR-001 §Sprint Closeout minimal touch), and `next-phase-candidates.md` updated (`/overview` re-point closed; next Phase-2 page candidates) — so that Sprint 57.29 = COMPLETE and the Phase-2 epic has a proven template.

## Technical Specifications

### Verbatim re-point method (the rule this sprint applies)

Per `docs/rules-on-demand/frontend-mockup-fidelity.md` — the mockup is **two layers, opposite treatment**:
- **Visual layer** = the CSS classes in `styles.css` (== `styles-mockup.css`, already loaded by Sprint 57.28) + the inline `style=` literals in the mockup `.jsx`. → **consumed verbatim**: components write `className="card"` and copy inline-style objects byte-for-byte. NEVER re-expressed as Tailwind utilities.
- **Component-logic layer** = the mockup `.jsx` behaviour (UMD React, `location.hash` routing, fixture data). → **rewritten** to production idioms: `react-router` `<Link>`/`useLocation`, real hooks (`useActiveLoops`), `useTranslation` i18n, typed props, the `cmdk`/Radix interaction layer for the overlays.

A re-pointed file = mockup DOM structure + mockup `className` strings + mockup inline styles, wired to production hooks. The PoC `pages/overview-poc/index.tsx` + `components.tsx` is the proven content-layer worked example.

### US-B1 — `mockup-ui.tsx` verbatim primitive port

NEW `frontend/src/components/mockup-ui.tsx` — typed-TSX port of `reference/design-mockups/ui.jsx`. Each primitive emits mockup class strings verbatim:
- `Icon` — `className="nav-icon"` / sized variants; mockup icon set.
- `Button` — `` `btn ${variant}` `` (`primary` / `ghost` / `outline`), `[data-size]`, `.ico`.
- `Badge` — `` `badge ${tone} ${dot ? "dot" : ""}` `` (`success` / `warning` / `danger` / `thinking` / `risk-*`).
- `Card` — `` `card ${className}` `` → `.card-head` / `.card-title` / `.card-sub` / `` `card-body ${bodyClass}` `` (`dense` / `flush`).
- `Stat` — `.stat` / `.stat-label` / `.stat-value tnum` / `.stat-delta` (`up`/`down`) / `.stat-spark`.
- `RiskBadge` — `.sev-dot sev-${level}` + label.

Typed props; no Tailwind; no shadcn. Reference implementation: PoC `pages/overview-poc/components.tsx` (231 lines — already did this port; adapt, add i18n where the PoC hardcoded English).

### US-B2/B3/B4 — shell re-point

The mockup shell is `reference/design-mockups/shell.jsx` (`Sidebar` + `Topbar`, 227 lines) + `app.jsx` (`App` root — `.app` grid). All 24 shell classes already exist verbatim in `styles-mockup.css`. The re-point is a **mechanical DOM + className port**, wired to production logic:

| Mockup behaviour | Production replacement (PRESERVE) |
|------------------|-----------------------------------|
| `location.hash` routing | `react-router` `<Link>` + `useLocation()` — DO NOT adopt hash routing |
| `route === r.id` → `data-active` | `useLocation().pathname` match → `data-active` on `.nav-item` |
| `CATEGORY_ORDER` 6-group nav | existing `routes.config.ts` `ROUTES` + `CATEGORY_ORDER` |
| collapse state | `useUIStore` `sidebarCollapsed` / `toggleSidebar` → `data-collapsed` on `.app` |
| ⌘K listener / overlay state | existing `paletteOpen` / `notifOpen` state + hotkey |
| inline `style=` (nav-badge, avatar gradient, locale btn, theme divider, bell badge) | **port verbatim** as inline styles — they are mockup visual-layer literals |
| hardcoded brand / tenant / user text | `useTranslation` + `useAuthStore` |

`data-testid` rule: every existing testid (`app-shell` / `sidebar-toggle` / `topbar` / `topbar-cmdk` / `topbar-theme` / `notifications-bell`) MUST survive the re-point on the same DOM node — Day-0 Prong 2 enumerates the full set; Vitest + e2e verify. The production-only collapse-toggle button (mockup has none) is KEPT.

### US-B5 — topbar overlays re-point

The mockup overlay source is `reference/design-mockups/topbar-overlays.jsx` (`CommandPalette` / `NotificationsPanel` / `UserMenu`). The mockup overlays are hand-rolled with classes + heavy inline styles; production uses the `cmdk` library + Radix `Dialog`/`DropdownMenu`. The re-point:
- **Ports the visual layer verbatim** — mockup overlay classes + inline-style literals → the production component's rendered markup.
- **Keeps the library interaction layer** — `cmdk` command list + filtering, Radix `Dialog` focus-trap/escape, `DropdownMenu` positioning — production keeps these; only what they *render* changes to mockup markup.
- Day-0 Prong 2 enumerates the exact overlay classes / inline styles (the shell discovery flagged them as inline-style-heavy) so Day 2 has the exact port targets.
- Preserve: ⌘K hotkey, route navigation from palette, notification fixtures + mark-all, `useAuthStore` tenant-switch, every overlay `data-testid`.

### US-C1/C2 — /overview content re-point

`OverviewPage.tsx` (223 lines, Sprint 57.27 clean assembly) → port `page-overview.jsx` structure: `.page-head` block, the inline `overviewStyles` object (`page` `{padding:18}` / `kpiRow` grid / `grid2` `1.4fr 1fr` / `grid2eq` `1fr 1fr`), `.route-pill`, `.page-actions`. Keep `useTranslation` / `useNavigate` / `useAuthStore` / live-clock `useEffect`.

9 widgets in `features/overview/components/` → port each from its `page-overview.jsx` sub-block: `.card` + `bodyClass` (`flush`/`dense`), `.row`/`.col`/`.mono`/`.subtle`, `loopRow`/`miniBar`/`miniBarFill` inline styles, `oklch()` risk tints (HITL card), `trafficDot(state)` (Providers), `<RiskBadge>`/`<Badge>` (Incidents), `quickBtn` inline (QuickActions). `CostBurnChart`/`ErrorTrendChart` SVG paths already use `var(--*)` — only the legend `.row`/`.mono` + `.col` wrapper re-point. `Spark.tsx` reused unchanged. `BackendGapBanner` has no mockup equivalent — kept as-is. `_primitives.tsx` — re-point its Badge/RiskBadge OR delete if fully superseded by `mockup-ui.tsx` (Karpathy §3 orphan cleanup — decided Day 4 once `mockup-ui.tsx` exports are confirmed).

### US-D2 — /overview fidelity verification (Mockup-Fidelity DoD)

Per `docs/rules-on-demand/frontend-mockup-fidelity.md` §DoD:
1. Mockup `:8080` (`cd reference/design-mockups && python -m http.server 8080`) vs production `:3007/overview`, Playwright screenshot 1440×900, fresh context (no cache).
2. **computed-style measurement** — for representative elements (`.page-head`, a `.card`, a `.stat`, `.sidebar`, `.topbar`): `getComputedStyle` of colour / font / spacing / border-radius + bounding-box dimensions; production vs mockup, item-by-item.
3. Overlays opened (⌘K palette, notifications, user-menu) + compared.
4. Drift classified (none / cosmetic / structural) + parity verdict recorded in REPOINT-REPORT.
5. Fundamental drift → method re-examined before continuing (do not redo with a drifting method).

### route-sweep.mjs reuse

Reuse `frontend/scripts/route-sweep.mjs` (Sprint 57.26/57.28). Day 0 `before` → `screenshots/before/`; Day 5 `after` → `screenshots/after/`. Fresh Playwright contexts. Triage rule (same as 57.28): catastrophic → fix in-sprint; transition-drift (shell chrome shift on the 18 not-content-re-pointed routes) → catalogue; structural regression → carryover AD.

## File Change List

### NEW files (~2 + screenshots)

1. `frontend/src/components/mockup-ui.tsx` — verbatim-TSX port of mockup `ui.jsx` primitives
2. `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-29/artifacts/overview-shell-repoint/REPOINT-REPORT.md` — Day 0 skeleton → Day 5 sweep matrix + `/overview` parity verdict + re-point method template
   + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-29/artifacts/overview-shell-repoint/screenshots/` — before/ + after/ + `/overview` mockup-vs-prod captures (local evidence, NOT committed — per Sprint 57.26/57.28 pattern)

### MODIFIED files (~16-17)

Shell (3): `frontend/src/components/AppShellV2.tsx` · `frontend/src/components/Sidebar.tsx` · `frontend/src/components/layout/Topbar.tsx`
Overlays (3): `frontend/src/components/topbar/CommandPalette.tsx` · `frontend/src/components/topbar/NotificationsPanel.tsx` · `frontend/src/components/UserMenu.tsx`
`/overview` page (1): `frontend/src/pages/overview/OverviewPage.tsx`
`/overview` widgets (7): `features/overview/components/` — `ActiveLoopsCard.tsx` · `HITLQueueCard.tsx` · `ProvidersCard.tsx` · `IncidentsCard.tsx` · `QuickActionsStrip.tsx` · `CostBurnChart.tsx` · `ErrorTrendChart.tsx`
Harness (1): `frontend/scripts/route-sweep.mjs` — `OUT_DIR` 57.28 → 57.29 + header MHist
Test (1-2): shell/overview/overlay Vitest spec(s) — adapt selectors if changed (exact files from Day-0 Prong 4)

### DELETED files (0-1)

`frontend/src/features/overview/components/_primitives.tsx` — DELETE only if fully superseded by `mockup-ui.tsx` (Karpathy §3 orphan cleanup; decided Day 4). If it retains overview-specific logic, re-point instead.

### PRESERVED (not touched)

- shared `CardShell.tsx` / `PageHead.tsx` / `StatCard.tsx` — `/overview` stops importing them; files untouched for cost/sla dashboards
- `components/charts/Spark.tsx` — token-neutral; reused as-is
- `components/ui/BackendGapBanner.tsx` — no mockup equivalent; kept
- the other 18 routes' page content
- `backend/**` · `App.tsx` / `RequireAuth` / `authStore` · `routes.config.ts` · `frontend/src/i18n/**`
- `styles-mockup.css` / `index.css` / `tailwind.config.ts` — the Sprint 57.28 foundation, consumed as-is
- `investigation/mockup-fidelity-poc` branch — reference only; NOT merged

## Acceptance Criteria

1. ✅ Plan + checklist landed; Day-0 三-prong (Prong 1 path + Prong 2 content/class/testid enumeration + Prong 4 test-selector) complete; drift findings catalogued in progress.md Day 0
2. ✅ Before-baseline 22-route 1440×900 sweep captured (`screenshots/before/`); REPOINT-REPORT skeleton landed
3. ✅ `mockup-ui.tsx` exists — verbatim primitive port; emits mockup class strings; 0 Tailwind / 0 shadcn
4. ✅ `AppShellV2` / `Sidebar` / `Topbar` re-pointed — consume verbatim mockup shell classes directly; every `data-testid` contract preserved on the same node; routing / collapse / ⌘K / theme / i18n logic intact
5. ✅ 3 overlays (`CommandPalette` / `NotificationsPanel` / `UserMenu`) re-pointed — verbatim mockup overlay markup; `cmdk`/Radix interaction layer + hotkey + navigation + fixtures + tenant-switch preserved
6. ✅ `OverviewPage.tsx` + 9 widgets re-pointed — consume verbatim mockup classes + verbatim inline styles; `useActiveLoops` real data + loading/error/empty branches intact; `_primitives.tsx` re-pointed or deleted-if-orphaned
7. ✅ `/overview` consumes 0 translated Tailwind colour/spacing utilities for mockup-covered elements (verified by grep + `check:mockup-fidelity`); `HEX_OKLCH_BASELINE` lowered if `/overview` literals removed
8. ✅ 22-route after-sweep captured + diffed vs before-baseline; triaged — 0 catastrophic breakage shipped; shell-chrome transition-drift catalogued; structural regressions → carryover AD
9. ✅ `/overview` fidelity verified vs mockup `:8080` — screenshot + computed-style measurement of representative elements + overlays opened; drift classified + parity verdict in REPOINT-REPORT
10. ✅ Vitest 457/457 preserved (shell/overview/overlay specs adapted, NOT deleted); `npm run lint` exit 0; `npm run build` green; `npm run check:mockup-fidelity` green; bundle KB delta recorded
11. ✅ REPOINT-REPORT final — per-route sweep verdict + `/overview` parity verdict + the re-point method/template for the next Phase-2 sprint
12. ✅ Commits + retrospective Q1-Q7 with 1st-data-point calibration ratio for NEW `frontend-verbatim-css-repoint` class + memory snapshot + MEMORY.md +1 + sprint-workflow.md calibration matrix +1 NEW class row + CLAUDE.md minimal touch + next-phase-candidates.md update + PR landed

## Deliverables

- [ ] Plan + checklist drafted (Day 0)
- [ ] Day-0 三-prong (Prong 1 path + Prong 2 content/class/testid + Prong 4 test-selector) + before-baseline 22-route sweep + REPOINT-REPORT skeleton
- [ ] `mockup-ui.tsx` — verbatim primitive port
- [ ] `AppShellV2` re-pointed
- [ ] `Sidebar` re-pointed
- [ ] `Topbar` re-pointed
- [ ] 3 overlays (`CommandPalette` / `NotificationsPanel` / `UserMenu`) re-pointed
- [ ] shell spot-check — all 19 routes' shell renders, testids + interactions intact
- [ ] `OverviewPage.tsx` re-pointed
- [ ] 9 `/overview` widgets re-pointed; `_primitives.tsx` re-pointed or deleted-if-orphaned
- [ ] 22-route after-sweep + before/after triage (catastrophic fixed / transition-drift catalogued / structural → AD)
- [ ] `/overview` fidelity verification vs mockup — screenshot + computed-style measurement + overlays + parity verdict
- [ ] Vitest 457/457 preserved; lint + build + `check:mockup-fidelity` green; bundle delta recorded
- [ ] REPOINT-REPORT final + re-point method template
- [ ] Retrospective Q1-Q7 + 1st-data-point calibration + memory snapshot + MEMORY.md +1 + calibration matrix NEW class row + CLAUDE.md minimal touch + next-phase-candidates.md update
- [ ] PR opened + CI green + merge + post-merge cleanup

## Dependencies & Risks

### Dependencies

- `frontend/src/styles-mockup.css` present on the branch (Sprint 57.28 — all 251 classes incl. 24 shell classes; verified Day 0 Prong 1)
- `reference/design-mockups/` — `page-overview.jsx` / `shell.jsx` / `app.jsx` / `topbar-overlays.jsx` / `ui.jsx` / `styles.css` present + current (visual source)
- `investigation/mockup-fidelity-poc` branch (`53ca61fc`) readable — PoC `pages/overview-poc/` is the content-layer template
- `frontend/scripts/route-sweep.mjs` present on main (Sprint 57.26/57.28 — verified Day 0 Prong 1)
- Mockup `:8080` http server reachable + production dev server `:3007` running (Day 0 + Day 5 fidelity verification)

### Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R1** | **Shell re-point has NO PoC precedent** — the PoC only re-pointed `/overview` content; `AppShellV2`/`Sidebar`/`Topbar` are the first verbatim shell re-point. Risk of missing a shell class or breaking a shell interaction. | HIGH | Mockup `shell.jsx` (227 lines) + `app.jsx` are small + mechanical to port; Day-0 Prong 2 enumerates every shell class (confirmed present in `styles-mockup.css`) + every interaction; spot-check the shell on multiple routes after each shell file; the 22-route sweep is the safety net |
| **R2** | **Shell blast radius** — re-pointing the shared shell changes the chrome of all 19 routes at once | MEDIUM | 22-route before/after sweep catalogues every shift; the 18 non-`/overview` routes' content stays translated — only chrome changes (expected transition-drift, accepted under Option B); only catastrophic breakage is in-sprint work |
| **R3** | **`data-testid` contract breakage** — re-pointing `className` could drop a testid Playwright e2e / Vitest depends on (`app-shell` / `sidebar-toggle` / `topbar` / `topbar-cmdk` / `topbar-theme` / `notifications-bell` + overlay testids) | HIGH | Day-0 Prong 2 enumerates the full testid set; the re-point swaps `className` ONLY and keeps every `data-testid` on the same DOM node; Vitest + e2e (`npm run test`) verify before commit |
| **R4** | Mockup uses `location.hash` routing + UMD React; a mechanical port could accidentally import the hash-routing model | MEDIUM | §Technical Specifications mandates `react-router` `<Link>`/`useLocation` preserved; only DOM structure + `className` + inline styles are ported, never the routing/data model; PoC `index.tsx` shows the correct production wiring |
| **R5** | Mockup inline `style=` literals (gradients / tints / badge colours) mis-handled — translated instead of copied | LOW | The rule (`frontend-mockup-fidelity.md`): mockup inline styles are visual-layer literals → copied verbatim as inline-style objects, NOT re-expressed; checklist DoD calls this out per widget/overlay |
| **R6** | `/overview` real-data widget (`useActiveLoops`) loses its loading/error/empty branches in the re-point | MEDIUM | Re-point swaps `className` only; the hook + all state branches are preserved; `ActiveLoopsCard` re-point DoD explicitly verifies loading/error/empty still render |
| **R7** | 22-route sweep finds many shell-chrome shifts on the 18 other routes → Day 5 over-runs | MEDIUM | Sweep batch-screenshots in one ~2-3 min run; triage by severity; only catastrophic fixed in-sprint; chrome transition-drift is catalogue-only |
| **R8** | Browser-cache staleness masks the re-point during verification (the 2026-05-20 false-alarm class) | LOW | Sweep + fidelity verification use fresh Playwright contexts; PR body carries a hard-refresh verification note |
| **R9** | `_primitives.tsx` delete-vs-re-point ambiguity creates an orphan or a broken import | LOW | Day 4 decides after `mockup-ui.tsx` exports are final; grep confirms 0 importers before delete (Karpathy §3) |
| **R10** | Overlay re-point — the mockup overlays are hand-rolled but production uses `cmdk` + Radix `Dialog`/`DropdownMenu`; porting the visual without breaking the library focus-trap/keyboard layer | MEDIUM | Re-point ports ONLY what the library renders (markup → mockup classes/inline styles); the `cmdk`/Radix interaction layer is untouched; Day-0 Prong 2 enumerates the overlay class/inline-style targets; spot-check ⌘K open/filter/escape + notifications + user-menu after the re-point |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Risk Class A** (paths-filter vs `required_status_checks`): N/A — Sprint 55.6 AD-CI-5 retired the `paths:` filter; `backend-ci` + `playwright-e2e` now always trigger. This PR is frontend-only and CI fires normally.
- **Risk Class B** (cross-platform mypy unused-ignore): N/A — frontend-only.
- **Risk Class C** (module-level singleton across test event loops): N/A — frontend Vitest.

## Workload

| Group | Bottom-up est | Class haircut 0.60 | Day allocation |
|-------|---------------|--------------------|----------------|
| Group A (Day 0 plan + 三-prong + before-baseline) | ~1.5 hr | ~0.9 hr | Day 0 |
| Group B shell (`mockup-ui.tsx` + AppShellV2 + Sidebar + Topbar) | ~6.5 hr | ~3.9 hr | Day 1-2 |
| Group B overlays (CommandPalette + NotificationsPanel + UserMenu) | ~4.0 hr | ~2.4 hr | Day 2-3 |
| Group C (OverviewPage + 9 widgets) | ~6.5 hr | ~3.9 hr | Day 3-4 |
| Group D (22-route sweep + `/overview` fidelity verify) | ~2.5 hr | ~1.5 hr | Day 5 |
| Group E (Vitest + closeout) | ~1.5 hr | ~0.9 hr | Day 5 |
| **Σ Bottom-up** | **~22.5 hr** | **~13.5 hr** | **6 working days (Day 0-5)** |

**Bottom-up est ~22.5 hr → calibrated commit ~13.5 hr (multiplier 0.60 — NEW class baseline)**

> Day count is 6 (vs Sprint 57.28's 5) — a content-driven not structural change: the scope is content + full shell + 3 overlays + a 22-route sweep, materially larger than 57.28's foundation-only scope. Section structure mirrors Sprint 57.28 exactly.

Day 5 retrospective Q2: record actual / committed ratio as the **1st data point** for the NEW `frontend-verbatim-css-repoint` class. Expected band [0.85, 1.20]; KEEP 0.60 baseline regardless (1 data point insufficient to adjust per `When to adjust` 3-sprint window rule).

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + before-baseline

- [ ] Plan + checklist drafted (mirror Sprint 57.28 structure) — user-approved
- [ ] Day-0 三-prong — Prong 1 path verify (all ~16 target files exist; `mockup-ui.tsx` absent; `route-sweep.mjs` + `styles-mockup.css` present) + Prong 2 content verify (every class used by `page-overview.jsx`/`shell.jsx`/`app.jsx`/`topbar-overlays.jsx` present in `styles-mockup.css`; full `data-testid` set enumerated; current translated-`className` inventory; `ui.jsx` primitive set) + Prong 4 test-selector verify (shell/overview/overlay Vitest specs)
- [ ] Read PoC `pages/overview-poc/index.tsx` + `components.tsx` as the content-layer template
- [ ] Before-baseline sweep — 22 routes at 1440×900 via `route-sweep.mjs before`
- [ ] REPOINT-REPORT skeleton + D-PRE findings catalogued in progress.md Day 0
- [ ] Day 0 commit

### Day 1 — Group B (primitives + AppShellV2 + Sidebar)

- [ ] US-B1 `mockup-ui.tsx` — verbatim port of `ui.jsx` primitives
- [ ] US-B2 `AppShellV2` re-point — `.app`/`.main`/`.content`
- [ ] US-B3 `Sidebar` re-point — verbatim sidebar classes + inline styles; routing/collapse/i18n/testids preserved
- [ ] Day 1 spot-check (`/overview` + 2 other routes' shell) + commit

### Day 2 — Group B (Topbar + overlays start)

- [ ] US-B4 `Topbar` re-point — verbatim topbar classes + inline styles; ⌘K/theme/overlay triggers/testids preserved
- [ ] US-B5 overlays — `CommandPalette` + `NotificationsPanel` re-point
- [ ] Day 2 spot-check + commit

### Day 3 — Group B finish + Group C start

- [ ] US-B5 overlays — `UserMenu` re-point
- [ ] Shell spot-check — all 19 routes' shell renders; testids + interactions intact; ⌘K/notifications/user-menu open correctly
- [ ] US-C1 `OverviewPage.tsx` re-point — `.page-head` + inline `overviewStyles`
- [ ] Day 3 spot-check + commit

### Day 4 — Group C (9 widgets)

- [ ] US-C2 9 widgets re-pointed — `.card`/`.row`/`.col`/`.badge`/`.stat` + verbatim inline tints; `useActiveLoops` + fixtures + BackendGapBanner preserved
- [ ] `_primitives.tsx` re-pointed or deleted-if-orphaned (grep 0 importers)
- [ ] Day 4 spot-check + commit

### Day 5 — Group D + E + closeout

- [ ] US-D1 after-switch 22-route sweep + before/after diff + triage (catastrophic fixed / transition-drift catalogued / structural → AD)
- [ ] US-D2 `/overview` fidelity verification — mockup `:8080` vs production screenshot + computed-style measurement + overlays opened + parity verdict
- [ ] US-E1 Vitest 457/457 (adapt shell/overview/overlay specs) + lint + build + `check:mockup-fidelity` + bundle delta
- [ ] US-E2 REPOINT-REPORT final + re-point method template
- [ ] retrospective.md Q1-Q7 + Q2 1st-data-point calibration ratio
- [ ] memory snapshot `memory/project_phase57_29_overview_shell_repoint.md` + MEMORY.md +1 quality pointer
- [ ] `.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row (`frontend-verbatim-css-repoint` 0.60) + MHist
- [ ] `claudedocs/1-planning/next-phase-candidates.md` update (`/overview` re-point closed; next Phase-2 page candidates)
- [ ] CLAUDE.md Current Sprint row + Last Updated footer (REFACTOR-001 §Sprint Closeout minimal touch)
- [ ] PR open + CI green + merge + post-merge cleanup

---

**Plan drafted**: 2026-05-22 Day 0
**Sprint duration target**: 6 working days from Day 0 plan/checklist commit to PR merged
**Class**: `frontend-verbatim-css-repoint` 0.60 (NEW class; 1st application; HYBRID weighted blend)
