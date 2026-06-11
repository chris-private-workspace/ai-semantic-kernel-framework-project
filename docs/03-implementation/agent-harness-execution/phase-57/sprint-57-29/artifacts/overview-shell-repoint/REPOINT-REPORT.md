# REPOINT-REPORT — Sprint 57.29 (AD-Overview-Verbatim-Repoint)

**Purpose**: Track the first verbatim-CSS Phase-2 per-page re-point — `/overview` content + the shared app shell (AppShellV2 + Sidebar + Topbar + 3 topbar overlays) — with 22-route before/after regression evidence + `/overview` mockup-fidelity verification.
**Sprint**: 57.29 (Phase 2 of `claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md` §5 — the first per-page re-point)
**Status**: ✅ COMPLETE — Day 0-5 done. `/overview` parity verdict = **PARITY**; 22-route sweep = 0 catastrophic / 0 structural regression.
**Created**: 2026-05-22

---

## 1. The verbatim re-point method (what this sprint applies)

Sprint 57.28 landed the **foundation** — `frontend/src/styles-mockup.css` is a byte-identical copy of `reference/design-mockups/styles.css` (251 classes incl. all 24 shell classes, oklch). But every page still consumed translated Tailwind utilities on top of it. This sprint executes **Phase 2 — per-page re-point** for `/overview` + the shell:

| Layer | Treatment |
|-------|-----------|
| **Visual layer** — mockup CSS classes (`styles-mockup.css`) + inline `style=` literals in the mockup `.jsx` | **Consumed verbatim** — `className="card"` / `className="sidebar"`; inline-style objects copied byte-for-byte. NEVER re-expressed as Tailwind utilities. |
| **Component-logic layer** — mockup `.jsx` behaviour (UMD React, `location.hash` routing, fixtures) | **Rewritten** to production idioms — `react-router` `<Link>`/`useLocation`, real hooks (`useActiveLoops`), `useTranslation` i18n, typed props, `cmdk`/Radix interaction layer for overlays. |

A re-pointed file = mockup DOM structure + mockup `className` strings + mockup inline styles, wired to production hooks. Reference: PoC `investigation/mockup-fidelity-poc` `pages/overview-poc/index.tsx` + `components.tsx` (proven byte-identical content-layer re-point).

**Scope**: `/overview` content (`OverviewPage` + 7 widgets + `_primitives.tsx`) + shell (`AppShellV2` + `Sidebar` + `Topbar`) + 3 overlays (`CommandPalette` + `NotificationsPanel` + `UserMenu`) + NEW `mockup-ui.tsx` verbatim primitives. The other 18 routes' content stays translated — only their shared shell chrome changes (verified by the regression sweep).

---

## 2. 22-route before/after regression matrix

Captured 1440×900 via `frontend/scripts/route-sweep.mjs`. Before = Day 0 (pre-re-point). After = Day 5 (post shell + `/overview` re-point).

Triage legend: 🟢 unchanged/improvement · 🟡 transition-drift (shell-chrome shift on a not-content-re-pointed route — expected Phase-2 backlog) · 🔴 catastrophic (in-sprint fix) · 🟠 structural-regression (carryover AD) · ⚪ not-assessable.

| # | Route | Shell | Before | After | Verdict |
|---|-------|-------|--------|-------|---------|
| 1 | `/` | Home | ✓ | ✓ | 🟢 unchanged |
| 2 | `/auth/login` | AuthShell | ✓ | ✓ | 🟢 AuthShell untouched |
| 3 | `/auth/callback` | AuthShell | ✓ | ✓ | 🟢 AuthShell untouched |
| 4 | `/auth/register` | AuthShell | ✓ | ✓ | 🟢 AuthShell untouched |
| 5 | `/auth/invite/:token` | AuthShell | ✓ | ✓ | 🟢 AuthShell untouched |
| 6 | `/auth/mfa` | AuthShell | ✓ | ✓ | 🟢 AuthShell untouched |
| 7 | `/auth/expired` | AuthShell | ✓ | ✓ | 🟢 AuthShell untouched |
| 8 | `/auth/dev` | AuthShell | ✓ | ✓ | 🟢 AuthShell untouched |
| 9 | `/overview` | AppShellV2 | ✓ | ✓ | 🟢 **TARGET — full verbatim re-point; fidelity = PARITY (§3)** |
| 10 | `/chat-v2` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; content unchanged (Phase-2 backlog) |
| 11 | `/orchestrator` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; content unchanged |
| 12 | `/subagents` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; pre-existing content crash (before == after) |
| 13 | `/loop-debug` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; empty-state renders |
| 14 | `/memory` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; pre-existing content crash (before == after) |
| 15 | `/state-inspector` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; content renders |
| 16 | `/governance` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; pre-existing "Failed to load approvals" (before == after) |
| 17 | `/verification` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; pre-existing content crash (before == after) |
| 18 | `/cost-dashboard` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; dashboard renders |
| 19 | `/sla-dashboard` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; dashboard renders |
| 20 | `/admin-tenants` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; content unchanged |
| 21 | `/tenant-settings` | AppShellV2 | ✓ | ✓ | 🟡 new shell chrome; content unchanged |
| 22 | `/compaction` (PROP stub) | AppShellV2 | ✓ | ✓ | 🟢 PROP stub unchanged |

**Result**: 22/22 routes captured both passes. **0 catastrophic (🔴) · 0 structural-regression (🟠)**. 9× 🟢 (8 AuthShell/Home/PROP-stub + `/overview` target) + 13× 🟡 (expected shell-chrome transition on the not-yet-content-re-pointed AppShellV2 routes — Phase-2 backlog).

**Pre-existing crashes (NOT a 57.29 regression)**: `/subagents`, `/memory`, `/verification` render an error boundary (`Cannot read properties of undefined (reading 'length')`) — **identically in the Day-0 pre-re-point baseline**. Logically confirmed not shell-caused: the shell is shared by all 19 AppShellV2 routes and renders correctly on 16 of them; only these 3 route-content components crash, and 57.29 did not touch their files. Logged as carryover `AD-Overview-PreExisting-Route-Crashes` (separate FIX, outside this sprint's scope).

---

## 3. /overview mockup-fidelity verification

Per `docs/rules-on-demand/frontend-mockup-fidelity.md` §DoD: mockup `:8080/#overview` vs production `:3007/overview` (auth-mocked), standalone Playwright 1440×900 (NOT MCP — AD #37), + computed-style measurement of representative elements.

**Computed-style measurement** — representative elements `.page-head` / first `.card` / first `.stat` / `.sidebar` / `.topbar`, mockup vs production:

- `backgroundColor`, `color` (oklch end-to-end), `fontSize` (13px baseline), `fontFamily` (Geist), `padding`, `borderRadius`, bounding-box `width` — **identical** mockup vs production on all 5 elements.
- 2 deltas, both classified **not drift**:
  - `borderColor` differs only on **zero-width (invisible) sides** of page-head/sidebar/topbar; the actual visible divider border `oklch(0.26 0.008 260)` is identical.
  - first `.card` height 361 px (mockup) vs 409 px (production) — fixture-data difference: the mockup ActiveLoops card has populated rows; production shows the empty "No running loops" state (`useActiveLoops` → not-yet-built `/api/v1/loops`). Layout/CSS identical.

**Visual screenshot comparison** (`screenshots/fidelity-mockup-overview.png` vs `fidelity-prod-overview.png`, kept local): sidebar, topbar, page-head, 4-tile KPI Stats row, and the widget grid all match the mockup in layout / structure / spacing / typography / colour. Text/data content differs (real i18n + hooks + fixture/empty states vs the mockup's hardcoded "Jamie Liu" / static numbers) — expected, not drift.

**Drift classification: PARITY.** No cosmetic drift, no structural drift. The verbatim-CSS re-point method succeeded for `/overview`.

---

## 4. Day 0 三-prong D-PRE findings

| ID | Sev | Finding | Implication |
|----|-----|---------|-------------|
| **Prong 1** | 🟢 | Path verify — 0 path drift. All 16 target files present as edits; `mockup-ui.tsx` absent (create); 5 mockup sources present. | GO. |
| **D-PRE-1** | 🟡 | Prong 2 testid enumeration — full `data-testid` contract = **10 testids** (`app-shell` / `sidebar-toggle` / `sidebar-tenant-switcher` / `topbar` / `topbar-cmdk` / `topbar-locale` / `topbar-theme` / `notifications-bell` / `notifications-panel` / `traffic-dot-${state}` dynamic). | Re-point preserved all 10. 0 scope shift. |
| **D-PRE-2** | 🟢 | Prong 4 — 13 in-scope unit specs + ~9 e2e specs traverse the shell. | Day 5 US-E1 — testids preserved → specs unaffected; 1 class-selector spec (HITL) adapted (see §findings below). |
| **D-PRE-3** | 🟢 | No dedicated `Topbar.test.tsx`. | Topbar verified via `AppShellV2.test.tsx` + e2e. |
| **Overlay classes** | 🟢 | `styles-mockup.css` == `styles.css` byte-identical → every overlay class present. | No class-existence risk. |

---

## 5. Final verdict (Day 5)

**Sprint 57.29 succeeded.** The first Phase-2 per-page verbatim re-point delivered:

- `/overview` (shell + page + 7 widgets) re-pointed to verbatim mockup CSS — fidelity verdict **PARITY** (computed-style identical; 0 cosmetic / 0 structural drift).
- 22-route regression sweep: **0 catastrophic / 0 structural-regression**; the shared shell re-point is clean (16/16 non-crashing AppShellV2 routes render correctly; 3 pre-existing route-content crashes are unrelated to 57.29).
- The verbatim re-point method is **validated as the Phase-2 per-page template**: visual layer (mockup class names + inline-style literals) copied verbatim; component-logic layer (hooks / routing / i18n / Radix+cmdk interaction) kept as production idioms. A latent gap — `mockup-ui.tsx` `Stat.spark` needing a `Spark` SVG — was caught + fixed in-sprint (D-DAY3-1); a stale class-selector spec was adapted to the verbatim form (D-DAY4-1).

**Re-point method / template for the next Phase-2 sprint**: (1) Day-0 三-prong including a full testid + a11y-attribute contract enumeration; (2) delegate per-group implementation to `code-implementer` with the contracts explicitly listed in the brief; (3) orchestrator hard-verifies all 5 gates + reviews verbatim fidelity against the mockup source; (4) `code-implementer` MUST run Vitest itself (D-DAY1-1 lesson); (5) when a mockup primitive is incomplete, fix the primitive in-sprint rather than deferring; (6) when a stale spec asserts a translated class, adapt the spec to the verbatim form (sanctioned, not a test deletion).

**Carryover** (→ `claudedocs/1-planning/next-phase-candidates.md`): `AD-Inline-Style-Rule-vs-Verbatim-Method` (the `no-restricted-syntax` ESLint ban vs the verbatim method's required inline-style literals — currently per-file `eslint-disable`); `AD-UserMenu-Mockup-Structural-Deltas` (UserMenu retains theme-toggle + "Signed in as" + identity-card role badges not in the mockup); `AD-MockupFidelity-Guard-TokenRelative-Oklch` (the `check-mockup-fidelity` grep could exclude `oklch(from var(--token) …)` token-relative literals from the count); `AD-Overview-PreExisting-Route-Crashes` (`/subagents` `/memory` `/verification` content crashes — separate FIX); next Phase-2 page-port candidates.
