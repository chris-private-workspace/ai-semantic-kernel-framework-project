# Sprint 57.29 — Checklist (AD-Overview-Verbatim-Repoint)

[Link to plan](./sprint-57-29-plan.md)

**Class**: `frontend-verbatim-css-repoint` 0.60 (NEW class; 1st application; HYBRID weighted blend)
**Workload**: Bottom-up ~22.5 hr → calibrated commit ~13.5 hr (multiplier 0.60)
**Day count**: 6 (Day 0 plan + 三-prong + before-baseline / Day 1 primitives + AppShellV2 + Sidebar / Day 2 Topbar + 2 overlays / Day 3 UserMenu + shell spot-check + OverviewPage / Day 4 9 widgets / Day 5 22-route sweep + fidelity verify + Vitest + closeout)
**1st-data-point watch**: Day 5 retro Q2 records actual/committed ratio as the NEW class's 1st data point; KEEP 0.60 regardless (1 data point insufficient to adjust per 3-sprint window rule)
**Scope**: `/overview` content + full shell (AppShellV2 + Sidebar + Topbar) + 3 topbar overlays (Option B + overlays, user-approved 2026-05-22)

---

## Day 0 — Plan + Checklist + 三-prong + before-baseline (2026-05-22)

### 0.1 Plan + Checklist
- [x] **Plan drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-29-plan.md` — mirror Sprint 57.28 structure; user-approved 2026-05-22 (incl. overlays-in-scope decision)
- [x] **Checklist drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-29-checklist.md` — Day 0-5 structure

### 0.2 Day 0 三-prong (Prong 1 path + Prong 2 content/class/testid + Prong 4 test selector)
- [x] **Prong 1 Path verify** — all ~16 target files exist as edits (`AppShellV2.tsx` / `Sidebar.tsx` / `layout/Topbar.tsx` / `topbar/CommandPalette.tsx` / `topbar/NotificationsPanel.tsx` / `UserMenu.tsx` / `pages/overview/OverviewPage.tsx` / 7 `features/overview/components/` widgets / `route-sweep.mjs`); `mockup-ui.tsx` absent (create); `styles-mockup.css` present (Sprint 57.28)
  - Verify: `Glob` each path; record 0 path drift in progress.md Day 0
- [x] **Prong 2 Content verify** — every mockup class used by `page-overview.jsx` / `shell.jsx` / `app.jsx` / `topbar-overlays.jsx` confirmed present in `frontend/src/styles-mockup.css`; full `data-testid` contract set enumerated from current shell/overview/overlay files; current translated-`className` inventory; `ui.jsx` primitive set listed
  - DoD: a class-list + testid-list table in progress.md Day 0; any class absent from `styles-mockup.css` → D-PRE finding
- [x] **Prong 4 Test-selector verify** — grep shell/overview/overlay Vitest specs for class-name selectors that the re-point will change (testids preserved → most specs unaffected); list specs needing Day-5 adaptation
- [x] **Read PoC reference** — `investigation/mockup-fidelity-poc` `pages/overview-poc/index.tsx` + `components.tsx` as the content-layer template

### 0.3 before-baseline sweep + REPOINT-REPORT skeleton
- [x] **Before-baseline sweep** — 22 routes at 1440×900 via `route-sweep.mjs before` → `screenshots/before/` (22 PNGs); `route-sweep.mjs` `OUT_DIR` re-pointed 57.28→57.29 + header MHist
  - Verify: `screenshots/before/` has 22 PNGs
- [x] **REPOINT-REPORT skeleton** at `claudedocs/4-changes/sprint-57-29-overview-shell-repoint/REPOINT-REPORT.md` — re-point method summary + 22-route before/after matrix skeleton + `/overview` fidelity-verdict section + D-PRE catalogue
- [x] **progress.md Day 0** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-29/progress.md` — Day 0 entry + Prong 1/2/4 results + D-PRE findings

### 0.4 Day 0 commit
- [x] **Day 0 commit** — plan + checklist + Day 0 progress + REPOINT-REPORT skeleton + `route-sweep.mjs` re-point (screenshots/ kept local, not committed — per Sprint 57.26/57.28 pattern)
  - Commit message: `chore(sprint-57-29, Day 0): plan + checklist + 三-prong + before-baseline`

---

## Day 1 — Group B (primitives + AppShellV2 + Sidebar)

### 1.1 US-B1 `mockup-ui.tsx` verbatim primitive port
- [ ] **NEW `frontend/src/components/mockup-ui.tsx`** — typed-TSX port of mockup `ui.jsx`
  - DoD: `Icon` / `Button` / `Badge` / `Card` / `Stat` / `RiskBadge` each emit mockup class strings verbatim (`btn ${variant}`, `badge ${tone}`, `card`/`card-head`/`card-body ${bodyClass}`, `stat`/`stat-value tnum`, `sev-dot sev-${level}`)
  - DoD: typed props; 0 Tailwind utility / 0 shadcn import
  - DoD: file header per `file-header-convention.md`; reference PoC `pages/overview-poc/components.tsx`
  - Verify: `npm run build` resolves the new module; `tsc` 0 errors

### 1.2 US-B2 `AppShellV2` re-point
- [ ] **`AppShellV2.tsx` → verbatim `.app` / `.main` / `.content`**
  - DoD: outer grid `className="app"` (+ `data-collapsed`), `.main`, `.content` (+ `fullbleed` when `fullBleed` prop set)
  - DoD: `app-shell` `data-testid` preserved on the same node; `fullBleed` prop behaviour unchanged
  - DoD: `useUIStore` collapse wiring intact
  - Verify: `/overview` renders inside the re-pointed shell; `tsc` 0

### 1.3 US-B3 `Sidebar` re-point
- [ ] **`Sidebar.tsx` → verbatim sidebar classes**
  - DoD: `.sidebar` / `.sidebar-head` / `.brand-mark` / `.brand-text` / `.brand-name` / `.brand-sub` / `.tenant-switcher` / `.tenant-avatar` / `.nav` / `.nav-section` / `.nav-item`[`data-active`] / `.nav-icon` / `.nav-label` / `.nav-badge` / `.sidebar-foot` / `.user-card` consumed directly
  - DoD: verbatim inline styles ported (nav-badge PROP/DRAFT colours, sidebar-foot avatar gradient) — copied as inline-style objects, NOT translated
  - DoD: preserved — `react-router` `<Link>` + `useLocation()` `data-active`; `routes.config.ts` `ROUTES` + `CATEGORY_ORDER` 6-group nav; `useUIStore` collapse; i18n `nav.*`; `sidebar-toggle` testid; production collapse-toggle button KEPT
  - Verify: nav active state follows route; collapse works; `tsc` 0

### 1.4 Day 1 spot-check + commit
- [ ] **Day 1 spot-check** — `/overview` + 2 other routes' shell render; sidebar nav + collapse work
- [ ] **Day 1 commit**
  - Commit message: `feat(frontend, sprint-57-29, Day 1, Group B): mockup-ui primitives + AppShellV2 + Sidebar verbatim re-point`
  - Verify: `git status` clean post-commit

---

## Day 2 — Group B (Topbar + CommandPalette + NotificationsPanel)

### 2.1 US-B4 `Topbar` re-point
- [ ] **`Topbar.tsx` → verbatim topbar classes**
  - DoD: `.topbar` / `.crumb` / `.here` / `.route-pill` / `.tenant-pill` / `.dot` / `.topbar-spacer` / `.cmdk` / `.kbd` / `.avatar` consumed directly
  - DoD: verbatim inline styles ported (locale button, theme divider, bell unread badge)
  - DoD: preserved — ⌘K hotkey + command-palette trigger; theme toggle; notifications + user-menu triggers; i18n `topbar.*`; `topbar` / `topbar-cmdk` / `topbar-theme` / `notifications-bell` testids
  - Verify: topbar renders; ⌘K + theme + bell + avatar triggers fire; `tsc` 0

### 2.2 US-B5 overlays — CommandPalette + NotificationsPanel
- [ ] **`CommandPalette.tsx` → verbatim mockup overlay markup**
  - DoD: mockup `topbar-overlays.jsx` `CommandPalette` classes + inline styles consumed; `cmdk` library + Radix `Dialog` interaction layer (filter / focus-trap / escape) untouched
  - DoD: preserved — ⌘K hotkey open; route navigation from palette; overlay testids
  - Verify: ⌘K opens; typing filters; Enter navigates; Escape closes
- [ ] **`NotificationsPanel.tsx` → verbatim mockup overlay markup**
  - DoD: mockup `NotificationsPanel` classes + inline styles consumed; open/close state + notification fixtures + mark-all handler preserved
  - Verify: bell opens panel; mark-all works; `notifications-bell` testid intact

### 2.3 Day 2 spot-check + commit
- [ ] **Day 2 spot-check** — topbar + ⌘K palette + notifications render correctly
- [ ] **Day 2 commit**
  - Commit message: `feat(frontend, sprint-57-29, Day 2, Group B): Topbar + CommandPalette + NotificationsPanel verbatim re-point`
  - Verify: `git status` clean post-commit

---

## Day 3 — Group B finish (UserMenu + shell spot-check) + Group C start (OverviewPage)

### 3.1 US-B5 overlays — UserMenu
- [ ] **`UserMenu.tsx` → verbatim mockup overlay markup**
  - DoD: mockup `topbar-overlays.jsx` `UserMenu` classes + inline styles consumed; Radix `DropdownMenu` interaction layer untouched
  - DoD: preserved — `useAuthStore` user/tenant; tenant-switch handler; nav items; overlay testid
  - Verify: avatar opens user-menu; tenant switch + nav items work

### 3.2 Shell spot-check (all 19 routes)
- [ ] **Shell renders on all 19 authenticated routes** — sidebar + topbar render; no crash
  - DoD: quick visual pass (dev server or sweep) confirms shell chrome renders on every route
  - DoD: ⌘K palette / notifications / user-menu open correctly from any route
  - DoD: all 6 shell testids resolve

### 3.3 US-C1 `OverviewPage.tsx` re-point
- [ ] **`OverviewPage.tsx` → verbatim `.page-head` + inline `overviewStyles`**
  - DoD: `.page-head` / `.page-title` / `.page-sub` / `.route-pill` / `.page-actions` consumed; inline `overviewStyles` object (`page` `{padding:18}` / `kpiRow` / `grid2` `1.4fr 1fr` / `grid2eq` `1fr 1fr`) ported verbatim from `page-overview.jsx`
  - DoD: preserved — `useTranslation` / `useNavigate` / `useAuthStore` / live-clock `useEffect` / `RequireAuth`+`AppShellV2` wrapping
  - Verify: `/overview` page-head + grid layout render; `tsc` 0

### 3.4 Day 3 spot-check + commit
- [ ] **Day 3 spot-check** — `/overview` page-head + shell render together correctly
- [ ] **Day 3 commit**
  - Commit message: `feat(frontend, sprint-57-29, Day 3, Group B+C): UserMenu re-point + shell spot-check + OverviewPage re-point`
  - Verify: `git status` clean post-commit

---

## Day 4 — Group C (9 widgets)

### 4.1 US-C2 chart + quick-action widgets
- [ ] **`CostBurnChart.tsx` + `ErrorTrendChart.tsx`** — legend `.row`/`.mono` + `.col` wrapper re-pointed (SVG paths already `var(--*)` — unchanged)
- [ ] **`QuickActionsStrip.tsx`** — `.row` + `quickBtn` inline style; navigate + i18n preserved

### 4.2 US-C2 card widgets
- [ ] **`ActiveLoopsCard.tsx`** — `.card`(`flush`) + `loopRow`/`miniBar`/`miniBarFill` inline; **`useActiveLoops(10)` real data + loading/error/empty branches preserved** (R6)
  - Verify: loading / error / empty / populated states all still render
- [ ] **`HITLQueueCard.tsx`** — `.card`(`dense`) + `.col` risk-tinted cards with verbatim `oklch()` inline tints; fixture + `BackendGapBanner` preserved
- [ ] **`ProvidersCard.tsx`** — `.card`(`dense`) + `.row` + `trafficDot(state)` verbatim inline; fixture preserved
- [ ] **`IncidentsCard.tsx`** — `.card`(`flush`) + `.row` rows + `<RiskBadge>`/`<Badge>` from `mockup-ui.tsx`; fixture preserved

### 4.3 `_primitives.tsx` orphan decision
- [ ] **`_primitives.tsx` re-pointed OR deleted-if-orphaned**
  - DoD: if fully superseded by `mockup-ui.tsx` → `grep` confirms 0 importers → DELETE (Karpathy §3); else re-point its remaining exports
  - Verify: `grep -rn "_primitives" frontend/src` → 0 stale imports

### 4.4 Day 4 spot-check + commit
- [ ] **Day 4 spot-check** — all 9 `/overview` widgets render with mockup classes
- [ ] **Day 4 commit**
  - Commit message: `feat(frontend, sprint-57-29, Day 4, Group C): /overview 9 widgets verbatim re-point + _primitives orphan cleanup`
  - Verify: `git status` clean post-commit

---

## Day 5 — Group D + E + closeout

### 5.1 US-D1 22-route regression sweep + triage
- [ ] **After-switch sweep** — all 22 routes via `route-sweep.mjs after` (fresh contexts, no cache) → `screenshots/after/`
  - DoD: `screenshots/after/` has 22 PNGs
- [ ] **Before/after matrix + triage** in REPOINT-REPORT
  - DoD: 22-route before/after matrix populated; triage — catastrophic (crash/unusable) fixed in-sprint; shell-chrome transition-drift on the 18 not-content-re-pointed routes catalogued; structural regression → carryover AD
  - DoD: 0 catastrophic breakage shipped

### 5.2 US-D2 `/overview` fidelity verification
- [ ] **`/overview` mockup-vs-production fidelity check**
  - DoD: mockup `:8080` vs production `:3007/overview` Playwright screenshot 1440×900 (fresh context)
  - DoD: computed-style measurement — representative elements (`.page-head` / a `.card` / a `.stat` / `.sidebar` / `.topbar`): colour / font / spacing / border-radius / bounding-box, production vs mockup item-by-item
  - DoD: ⌘K palette / notifications / user-menu overlays opened + compared
  - DoD: drift classified (none / cosmetic / structural) + parity verdict recorded in REPOINT-REPORT; fundamental drift → re-examine method before continuing

### 5.3 US-E1 Vitest + lint + build + guard
- [ ] **Vitest 457/457** — shell/overview/overlay specs adapted per Day-0 Prong 4 (testids preserved → most unaffected; NOT deleted)
  - Verify: `npm run test` exit 0
- [ ] **lint + build + mockup-fidelity guard**
  - DoD: `npm run lint` exit 0; `npm run build` green; `npm run check:mockup-fidelity` green; `HEX_OKLCH_BASELINE` lowered if `/overview` literals removed
  - DoD: bundle KB delta recorded in REPOINT-REPORT

### 5.4 US-E2 REPOINT-REPORT final + closeout
- [ ] **REPOINT-REPORT final verdict** — per-route sweep verdict + `/overview` parity verdict + the re-point method/template for the next Phase-2 sprint
- [ ] **retrospective.md Q1-Q7** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-29/retrospective.md`
  - DoD: Q2 records ratio actual/committed = 1st data point for NEW `frontend-verbatim-css-repoint` class
- [ ] **memory snapshot** `memory/project_phase57_29_overview_shell_repoint.md` + **MEMORY.md +1 quality pointer**
- [ ] **`.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row**
  - DoD: `frontend-verbatim-css-repoint` 0.60 row with 1st data point + MHist entry
- [ ] **`claudedocs/1-planning/next-phase-candidates.md` update** — `/overview` re-point closed; next Phase-2 page candidates
- [ ] **CLAUDE.md Current Sprint row + Last Updated footer** (REFACTOR-001 §Sprint Closeout minimal touch — NO history additions)
- [ ] **Day 5 commit** closeout
  - Commit message: `feat(frontend, sprint-57-29, Day 5): closeout — REPOINT-REPORT final + 22-route sweep + retrospective + calibration matrix NEW class`
  - Verify: `git status` clean post-commit

### 5.5 PR open + CI + merge
- [ ] **PR open** with body (Sprint 57.29 scope + verbatim re-point method + shell + overlays + `/overview` parity verdict + 22-route sweep result + NEW calibration class + browser-cache hard-refresh verification note)
- [ ] **CI green**: all required checks pass
- [ ] **Merge** (after CI green + user approval; squash per Sprint 57.23-57.28 pattern)
- [ ] **Post-merge cleanup**: local + remote feature branch delete

---

## Key Decisions Required During Sprint

| Decision Point | When | Default |
|----------------|------|---------|
| `_primitives.tsx`: re-point vs delete-if-orphaned | Day 4.3 | DELETE if `mockup-ui.tsx` fully supersedes it + grep 0 importers (Karpathy §3); else re-point remaining exports |
| Sweep regression: in-sprint fix vs catalogue vs carryover AD | Day 5.1 | Catastrophic → fix in-sprint; shell-chrome transition-drift → catalogue (Phase-2 backlog); structural → carryover AD |
| `/overview` fidelity: parity vs drift | Day 5.2 | Computed-style measurement decides; fundamental drift → re-examine method before continuing (do not redo with a drifting method) |
| Overlay re-point: how much of `cmdk`/Radix to keep | Day 2.2 / 3.1 | Keep the entire library interaction layer; port ONLY the rendered markup → mockup classes/inline styles |

---

**Plan + checklist drafted**: 2026-05-22 Day 0
**Class**: `frontend-verbatim-css-repoint` 0.60 (NEW class; 1st application)
**Target close**: 6 working days from Day 0 commit to PR merged
