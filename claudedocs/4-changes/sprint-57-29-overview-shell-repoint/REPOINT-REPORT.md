# REPOINT-REPORT — Sprint 57.29 (AD-Overview-Verbatim-Repoint)

**Purpose**: Track the first verbatim-CSS Phase-2 per-page re-point — `/overview` content + the shared app shell (AppShellV2 + Sidebar + Topbar + 3 topbar overlays) — with 22-route before/after regression evidence + `/overview` mockup-fidelity verification.
**Sprint**: 57.29 (Phase 2 of `claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md` §5 — the first per-page re-point)
**Status**: Day 0 — plan + checklist + 三-prong + before-baseline complete. Day 1-5 pending.
**Created**: 2026-05-22

---

## 1. The verbatim re-point method (what this sprint applies)

Sprint 57.28 landed the **foundation** — `frontend/src/styles-mockup.css` is a byte-identical copy of `reference/design-mockups/styles.css` (251 classes incl. all 24 shell classes, oklch). But every page still consumed translated Tailwind utilities on top of it. This sprint executes **Phase 2 — per-page re-point** for `/overview` + the shell:

| Layer | Treatment |
|-------|-----------|
| **Visual layer** — mockup CSS classes (`styles-mockup.css`) + inline `style=` literals in the mockup `.jsx` | **Consumed verbatim** — `className="card"` / `className="sidebar"`; inline-style objects copied byte-for-byte. NEVER re-expressed as Tailwind utilities. |
| **Component-logic layer** — mockup `.jsx` behaviour (UMD React, `location.hash` routing, fixtures) | **Rewritten** to production idioms — `react-router` `<Link>`/`useLocation`, real hooks (`useActiveLoops`), `useTranslation` i18n, typed props, `cmdk`/Radix interaction layer for overlays. |

A re-pointed file = mockup DOM structure + mockup `className` strings + mockup inline styles, wired to production hooks. Reference: PoC `investigation/mockup-fidelity-poc` `pages/overview-poc/index.tsx` + `components.tsx` (proven byte-identical content-layer re-point).

**Scope**: `/overview` content (`OverviewPage` + 9 widgets + `_primitives.tsx`) + shell (`AppShellV2` + `Sidebar` + `Topbar`) + 3 overlays (`CommandPalette` + `NotificationsPanel` + `UserMenu`) + NEW `mockup-ui.tsx` verbatim primitives. The other 18 routes' content stays translated — only their shared shell chrome changes (verified by the regression sweep).

---

## 2. 22-route before/after regression matrix

Captured 1440×900 via `frontend/scripts/route-sweep.mjs`. Before = Day 0 (pre-re-point). After = Day 5 (post shell + `/overview` re-point).

Triage legend: 🟢 unchanged/improvement · 🟡 transition-drift (shell-chrome shift on a not-content-re-pointed route — expected, Phase-2 backlog) · 🔴 catastrophic (in-sprint fix) · 🟠 structural-regression (carryover AD) · ⚪ not-assessable.

| # | Route | Shell | Before (Day 0) | After (Day 5) | Verdict |
|---|-------|-------|----------------|---------------|---------|
| 1 | `/` | Home | ✓ | _(Day 5)_ | _(pending)_ |
| 2 | `/auth/login` | AuthShell | ✓ | _(Day 5)_ | _(pending)_ |
| 3 | `/auth/callback` | AuthShell | ✓ | _(Day 5)_ | _(pending)_ |
| 4 | `/auth/register` | AuthShell | ✓ | _(Day 5)_ | _(pending)_ |
| 5 | `/auth/invite/:token` | AuthShell | ✓ | _(Day 5)_ | _(pending)_ |
| 6 | `/auth/mfa` | AuthShell | ✓ | _(Day 5)_ | _(pending)_ |
| 7 | `/auth/expired` | AuthShell | ✓ | _(Day 5)_ | _(pending)_ |
| 8 | `/auth/dev` | AuthShell | ✓ | _(Day 5)_ | _(pending)_ |
| 9 | `/overview` | AppShellV2 | ✓ | _(Day 5)_ | **_(target — full re-point)_** |
| 10 | `/chat-v2` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 11 | `/orchestrator` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 12 | `/subagents` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 13 | `/loop-debug` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 14 | `/memory` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 15 | `/state-inspector` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 16 | `/governance` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 17 | `/verification` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 18 | `/cost-dashboard` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 19 | `/sla-dashboard` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 20 | `/admin-tenants` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 21 | `/tenant-settings` | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |
| 22 | `/compaction` (PROP stub) | AppShellV2 | ✓ | _(Day 5)_ | _(pending)_ |

**Before-baseline**: 22/22 routes captured without harness error (`screenshots/before/`, Day 0). Triage + after-column populated Day 5 (US-D1).

---

## 3. /overview mockup-fidelity verification

_(Day 5 — US-D2 — pending)_ Per `docs/rules-on-demand/frontend-mockup-fidelity.md` §DoD: mockup `:8080` vs production `:3007/overview` screenshot 1440×900 + computed-style measurement of representative elements (`.page-head` / a `.card` / a `.stat` / `.sidebar` / `.topbar`) + overlays opened + drift classification + parity verdict.

---

## 4. Day 0 三-prong D-PRE findings

| ID | Sev | Finding | Implication |
|----|-----|---------|-------------|
| **Prong 1** | 🟢 | Path verify — 0 path drift. All 16 target files exist as edits (`AppShellV2.tsx` / `Sidebar.tsx` / `layout/Topbar.tsx` / `topbar/CommandPalette.tsx` / `topbar/NotificationsPanel.tsx` / `UserMenu.tsx` / `pages/overview/OverviewPage.tsx` / 7 `features/overview/components/` widgets / `route-sweep.mjs`); `mockup-ui.tsx` absent (create); 5 mockup sources (`app.jsx`/`page-overview.jsx`/`shell.jsx`/`topbar-overlays.jsx`/`ui.jsx`) present. | GO. |
| **D-PRE-1** | 🟡 | Prong 2 testid enumeration — the full `data-testid` contract is **10 testids**, more than the plan's illustrative list: `app-shell` (AppShellV2) · `sidebar-toggle` + `sidebar-tenant-switcher` (Sidebar) · `topbar` + `topbar-cmdk` + `topbar-locale` + `topbar-theme` + `notifications-bell` (Topbar) · `notifications-panel` (NotificationsPanel) · `traffic-dot-${state}` dynamic (ProvidersCard). `CommandPalette`/`UserMenu` have no own testid (triggers live on Topbar). | Re-point MUST preserve all 10 on the same DOM node. 0 scope shift — plan R3 already mandates "every testid"; this is the planned Prong-2 enumeration deliverable. |
| **D-PRE-2** | 🟢 | Prong 4 test-selector — 13 in-scope unit specs (`AppShellV2` / `Sidebar` / `UserMenu` / `CommandPalette` / `NotificationsPanel` / `OverviewPage` + 7 overview widget specs) + ~9 e2e specs traverse the shell (a11y / visual-regression / connectivity / chat-v2 / locale-switch / memory / loop-debug / verification / sla). | Day 5 US-E1 adapts any class-selector spec; testid-based specs unaffected (testids preserved). |
| **D-PRE-3** | 🟢 | No dedicated `Topbar.test.tsx` unit spec — Topbar coverage is via `AppShellV2.test.tsx` + e2e. | Minor; Topbar re-point verified by `AppShellV2.test.tsx` + e2e + Day 3 shell spot-check. |
| **Overlay classes** | 🟢 | `styles-mockup.css` == `styles.css` byte-identical (57.28 CI diff guard); the mockup overlays were authored against the same `styles.css` → every class they use is present by the verbatim-copy invariant. | No class-existence risk for the overlay re-point. |

**Go/No-Go**: 🟢 **GO** — 0 path drift, testid contract fully enumerated, no blocking finding, scope shift 0%.

---

## 5. Final verdict (Day 5)

_(Day 5 — US-E2 — pending)_ Per-route sweep verdict + `/overview` parity verdict + the re-point method/template for the next Phase-2 sprint.
