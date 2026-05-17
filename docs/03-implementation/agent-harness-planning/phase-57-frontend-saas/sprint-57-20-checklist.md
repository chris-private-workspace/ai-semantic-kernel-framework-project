# Sprint 57.20 — Checklist

**Plan**: `sprint-57-20-plan.md`
**Calibration**: NEW class `frontend-mockup-direct-port` 0.55 (HYBRID: shell rewrite ×0.55 ~35% + per-page mockup-direct ×0.50 ~50% + closeout ×0.80 ~15%) — bottom-up ~18-22 hr → calibrated commit ~10-12 hr (1st app; pending 2-3 sprint validation)
**Day count**: 5 (Day 0 setup + Day 1 shell + Day 2 /overview + Day 3 /chat-v2 + Day 4 verification + closeout)
**Branch**: `feature/sprint-57-20-mockup-existing-pages-retrofit` (rename consideration: kept original branch name to preserve Day 0 commits if any; retrospective Q1 will note philosophy pivot)

---

## Day 0 — Setup + 三-prong + Playwright MCP pipeline + reference captures

### 0.1 Plan + checklist landed
- [x] Old plan/checklist archived (`.aborted-option-Y-retrofit.md` suffix)
- [x] New plan drafted at `sprint-57-20-plan.md` (Option W; Frontend-Led, Backend-Follows)
- [x] New checklist drafted at `sprint-57-20-checklist.md` (this file)
- [x] User approval to proceed Day 0 三-prong + Day 1 code (2026-05-17)

### 0.2 Branch + initial doc files
- [x] Confirm branch `feature/sprint-57-20-mockup-existing-pages-retrofit` checked out
- [x] Create / update `progress.md` at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/progress.md` (Day 0 entry: aborted Option Y → pivoted Option W + Day 0 三-prong findings; 12 D-PRE findings catalogued)
- [x] Create `claudedocs/4-changes/sprint-57-20-direct-port-foundation/{screenshots/{shell, overview, chat-v2, sprint-57-19-inheritance}/}`

### 0.3 Day 0 三-prong scope verify (per sprint-workflow §Step 2.5)
- [x] **Prong 1 (Path verify)** — D-PRE-1 through D-PRE-5 catalogued in progress.md:
  - `frontend/src/components/AppShellV2.tsx` exists ✅ (Sprint 57.8)
  - `frontend/src/components/Sidebar.tsx` exists ✅ (Sprint 57.18 refactor)
  - `frontend/src/components/layout/` directory exists OR will be created Day 1
  - `frontend/src/pages/overview/index.tsx` exists ✅ (Sprint 57.19 US-C1)
  - `frontend/src/pages/chat-v2/index.tsx` + `features/chat_v2/components/*` exist ✅ (Sprint 57.8)
  - `reference/design-mockups/shell.jsx` + `page-overview.jsx` + `page-chat.jsx` + `i18n.jsx` + `styles.css` exist ✅
- [x] **Prong 2 (Content verify)** — D-PRE-1 + D-PRE-6 through D-PRE-8 catalogued; chat_v2 underscore correction applied to plan + checklist via Edit replace_all:
  - `tailwind.config.ts` fontFamily already declares Geist + Noto Sans TC (Sprint 57.18) — confirm
  - `index.css` `:root` does NOT currently have dark default — confirm
  - `features/loops/types.ts` + `features/subagents/types.ts` + `features/state/types.ts` (Sprint 57.19 NEW) exist + check data shape matches mockup overview widgets
  - `features/chat_v2/` SSE/HITL/InputBar state machine paths exist
- [x] **Prong 3 (Schema verify)**: N/A this sprint (pure frontend, 0 DB schema work, 0 backend changes)
- [x] Catalog Day 0 drift findings as `D-PRE-1` through `D-PRE-12` in `progress.md`
- [x] Go/no-go decision: scope shift = 0% (all 12 findings are documentation corrections / env confirmations / already-anticipated rewrite scope) → **GO Day 1**

### 0.4 Dev server + mockup server boot verification
- [x] Identify port 3007 occupant — PID 50796 (node.exe Vite dev server, started 5/17 01:35); **do NOT kill** per CLAUDE rule
- [x] Decision: use existing 3007 (Vite HMR will pick up Sprint 57.20 source changes automatically); no need for second dev server
- [x] Mockup server confirmed at port 8080 — PID 44700 (python http.server, started 5/17 18:29); `GET /shell.jsx` returned 304 in console logs (D-PRE-10)

### 0.5 Playwright MCP reference captures (US-A1)
- [x] Mockup reference at 1440×900:
  - `screenshots/shell/mockup-shell-default.png` (204 KB; single theme variant in mockup root — additional variants via `browser_evaluate` if needed Day 1+)
  - `screenshots/overview/mockup-overview.png` (204 KB)
  - `screenshots/chat-v2/mockup-chat-v2.png` (77 KB)
- [x] Pre-rewrite production baseline at 1440×900 (Day 4 before/after comparison):
  - `screenshots/shell/prod-shell-pre.png` (102 KB)
  - `screenshots/overview/prod-overview-pre.png` (176 KB)
  - `screenshots/chat-v2/prod-chat-v2-pre.png` (91 KB)
- [x] Commit Day 0 artifacts: `chore(sprint-57-20, Day 0): plan pivot Option Y→W + 三-prong + Playwright MCP reference captures` (commit landed)

---

## Day 1 — Shell rewrite (US-B1 + US-B2 + US-B3)

### 1.1 US-B1 AppShellV2 V3 + Topbar + Sidebar enrichment (~5-6 hr)
- [ ] Read `reference/design-mockups/shell.jsx` end-to-end; extract layout grid + token usage + structural composition
- [ ] **REWRITE** `frontend/src/components/AppShellV2.tsx`:
  - Full-screen edge-to-edge grid `[sidebar 240px | main 1fr]`
  - Top toolbar slot
  - Dark default class on root container
  - Preserve existing prop interface for 14 backward-compat pages (children prop, etc.)
- [ ] **NEW** `frontend/src/components/layout/Topbar.tsx` (~150 lines):
  - Breadcrumb (use react-router `useLocation` + ROUTES lookup)
  - Tenant badge (reuse `features/auth/tenants` if exists; else fixture)
  - Role badge (from authStore)
  - Global search input (visual placeholder; ⌘K hint; reuse existing CommandPalette behind it via hotkey)
  - Locale dropdown (reuse existing i18n switcher logic)
  - Bell icon (reuse existing NotificationsPanel)
  - Avatar (reuse existing UserMenu extended)
- [ ] **REWRITE** `frontend/src/components/Sidebar.tsx`:
  - Brand block "IPA Platform V2" + LOOP-FIRST badge
  - Tenant switcher pill ("acme-prod / Tenant_010b62 / Pro") — fixture for now; AD-UserMenu-Tenant-Switch Sprint 57.21+ wire
  - 6-cat nav (preserve Sprint 57.18 PROP/DRAFT/SOON badge matrix + propCount per cat header + i18n keys)
  - Bottom user identity card ("Jamie Liu / operator" — from authStore)
- [ ] Smoke test all 14 active pages render without crash (manual click-through via dev server)
- [ ] Commit: `feat(layout, sprint-57-20, Day 1): AppShellV2 V3 + Topbar + Sidebar enrichment per mockup shell.jsx 1:1`

### 1.2 US-B2 Geist + Noto Sans TC font wire (~1 hr)
- [ ] Check `frontend/public/fonts/` for Geist + Noto Sans TC font files
- [ ] If missing: use CDN @import in `index.css` (e.g. `@import url('https://rsms.me/inter/inter.css')` style) OR system fallback only + log AD for self-hosted asset addition
- [ ] `index.css` `@layer base { body { font-family: theme('fontFamily.sans') } }` to wire `tailwind.config.ts` fontFamily array to body
- [ ] Verify in DevTools "Computed" panel: body font-family resolves to Geist first, Noto Sans TC second
- [ ] Commit: `feat(typography, sprint-57-20, Day 1): wire Geist + Noto Sans TC to body via @layer base`

### 1.3 US-B3 Theme + density mechanism (~1 hr)
- [ ] `index.css` reorganize: move all token vars to `:root` (dark default); `:root[data-variant="forest"]` / `:root[data-variant="violet"]` / `:root[data-variant="dawn"]` for 4 mockup variants (initial: only indigo defined; others = AD-Theme-Variant-Mechanism Sprint 57.21+)
- [ ] `index.css` `:root[data-density="comfortable"]` / `:root[data-density="cozy"]` / `:root[data-density="compact"]` density vars (initial: comfortable default only; others = AD-Density-Variant-Mechanism Sprint 57.21+)
- [ ] `frontend/src/main.tsx` set `<html data-variant="indigo" data-density="comfortable" class="dark">` defaults
- [ ] Commit: `feat(theme, sprint-57-20, Day 1): [data-variant] + [data-density] mechanism + dark default + indigo theme baseline`

### 1.4 Day 1 closeout
- [x] `npm run build` succeeds (2.79s, main bundle 320.76 kB unchanged from Sprint 57.19 baseline)
- [x] `npm run test` (Vitest) 277 baseline preserved — initial 275/277 with 2 fails in AppShellV2.test.tsx, fixed in 1.5
- [x] `npm run lint` silent (no output = 0 warnings, --max-warnings 0 enforced)
- [x] Playwright MCP capture POST-Day-1 shell at 1440×900 → `screenshots/shell/prod-shell-post-day1.png` + 3 smoke pages (overview/cost-dashboard/governance)
- [ ] Pair-verify side-by-side parity verdict (deferred to Day 4 US-E1 inheritance check per D-DAY1-3; Day 1 baseline screenshots saved)

### 1.5 Vitest cascade fix (if needed)
- [x] AppShellV2.test.tsx L52 `<h1>` test — fixed by changing Topbar title `<span>` → `<h1>` (preserves pre-Sprint-57.20 a11y contract; visual identical)
- [x] AppShellV2.test.tsx L63 `userMenu` slot test — fixed by threading `userMenu` prop through AppShellV2 → Topbar override slot
- [x] Sidebar.test.tsx selectors — no fix needed (existing assertions on `aria-label="Primary navigation"` + NavLink structure preserved through rewrite)
- [x] Confirm 277 / 277 ALL PASS — ✅ verified before Day 2 starts

---

## Day 2 — /overview token migration + visual refinement (US-C1) — COMPLETED

**Day 2 scope reduced** from full rewrite to token migration after discovery that Sprint 57.19 US-C1 already shipped 1:1 mockup port. Day 2 delivers visual consistency with new shell via shadcn → mockup token tree migration.

### 2.1 Mockup analog deep read
- [ ] Read `reference/design-mockups/page-overview.jsx` end-to-end
- [ ] Identify widgets: loop KPI strip / active loops table / recent memory writes panel / sub-agent activity stream / cost burn micro-chart
- [ ] Grep against `features/loops/types.ts` + `features/subagents/types.ts` + `features/state/types.ts` + `features/memory/` (Sprint 57.19 NEW + existing) — confirm data shape sufficient
- [ ] If data shape insufficient: record gap, decide subset of widgets in scope vs defer to Sprint 57.21+ backend wire ADs

### 2.2 Rewrite /overview
- [ ] **REWRITE** `frontend/src/pages/overview/index.tsx`:
  - Import `useLoops` / `useMemory` / `useSubagents` from `features/`
  - JSX 100% per mockup `page-overview.jsx` (grid layout + widgets + tokens)
  - Use shadcn Card / Badge / Skeleton primitives + Sprint 57.18 semantic tokens
  - i18n: add `overview.*` keys per mockup vocabulary (~20-30 per locale)
- [ ] **EDIT** `frontend/src/i18n/en/common.json` + `zh-TW/common.json` — add `overview.*` keys
- [ ] Smoke test: navigate Playwright MCP to `/overview` — captures rendering with NEW shell + NEW page

### 2.3 Vitest adapt
- [ ] Update `pages/overview/index.test.tsx` selectors to match new DOM (preserve test structure: render + assert hooks called + assert key elements present)
- [ ] Confirm Vitest 277+ passing (no regression)

### 2.4 Day 2 closeout
- [ ] Playwright MCP pair-verify: `screenshots/overview/prod-overview-post.png` vs `screenshots/overview/mockup-overview.png`
- [ ] Parity verdict in `progress.md` Day 2 entry; cosmetic gaps catalogued as in-sprint iteration OR Sprint 57.21+ AD
- [ ] Commit: `feat(overview, sprint-57-20, Day 2): /overview 1:1 mockup-direct port reusing useLoops/useMemory/useSubagents`

---

## Day 3 — /chat-v2 mockup-direct port (US-D1) (~5-6 hr)

### 3.1 Mockup analog deep read + behavior inventory
- [ ] Read `reference/design-mockups/page-chat.jsx` end-to-end
- [ ] Identify 3-column layout (sessions list / message thread / inspector pane) + key UX (MessageList bubbles + ToolCallCard collapse + InputBar status pill + HITL approval modal)
- [ ] **Behavior inventory** (must preserve): SSE event handler / InputBar state machine / HITL approval workflow / Cat 9 audit logging / verification card / subagent tree
- [ ] Grep existing `features/chat_v2/components/*.tsx` — identify which files need rewrite vs preserve

### 3.2 Rewrite chat-v2 presentation layer (preserve behavior)
- [ ] **REWRITE** `frontend/src/pages/chat-v2/index.tsx` — 3-column layout per mockup
- [ ] **REWRITE** `frontend/src/features/chat_v2/components/MessageList.tsx` — bubble styling per mockup
- [ ] **REWRITE** `frontend/src/features/chat_v2/components/InputBar.tsx` — status pill + send button per mockup; **preserve existing state machine logic**
- [ ] **REWRITE** `frontend/src/features/chat_v2/components/ToolCallCard.tsx` — collapsed-detail UX per mockup
- [ ] **REWRITE** sessions list + inspector pane components if separate files (or inline in page)
- [ ] **EDIT** `frontend/src/i18n/en/common.json` + `zh-TW/common.json` — add/update `chat.*` keys
- [ ] **Preserve untouched**: SSE event handler hook + HITL approval modal logic + Cat 9 audit hooks + verification card data flow

### 3.3 Vitest + Playwright adapt
- [ ] Update chat-v2 Vitest spec selectors per new DOM (preserve behavioral assertions)
- [ ] Update chat-v2 Playwright e2e spec selectors (preserve SSE message dispatch / approval card render / error retry tests)
- [ ] Confirm Vitest 277+ + Playwright e2e baseline preserved

### 3.4 Day 3 closeout
- [ ] Playwright MCP pair-verify: `screenshots/chat-v2/prod-chat-v2-post.png` vs `screenshots/chat-v2/mockup-chat-v2.png`
- [ ] Parity verdict in `progress.md` Day 3 entry
- [ ] Manual smoke test: send message + observe SSE updates + approve HITL request — all behaviors preserved
- [ ] Commit: `feat(chat-v2, sprint-57-20, Day 3): /chat-v2 1:1 mockup-direct port preserving SSE/HITL/state machine`

---

## Day 4 — Sprint 57.19 inheritance check + closeout (US-E1 + US-E2)

### 4.1 Sprint 57.19 7-output runtime fidelity check (US-E1)
- [ ] Playwright MCP capture POST-Sprint-57.20 at 1440×900:
  - `screenshots/sprint-57-19-inheritance/{overview-already-day2, orchestrator, subagents, state-inspector}-post.png`
  - `screenshots/sprint-57-19-inheritance/{command-palette, notifications-panel, user-menu}-post.png` (trigger via ⌘K / bell click / avatar click)
- [ ] Pair-verify each vs `reference/design-mockups/` mockup target
- [ ] Catalogue page-level cosmetic gaps in NEW DRIFT-REPORT-ROUND-2.md at `claudedocs/4-changes/sprint-57-20-direct-port-foundation/DRIFT-REPORT-ROUND-2.md`
- [ ] Each gap → Sprint 57.21+ AD-Mockup-Direct-Port-Round-2 candidate

### 4.2 Test + build sanity
- [ ] `pytest backend/tests/` 0 regression (pure frontend sprint; backend untouched)
- [ ] `npm run test` Vitest 277+ PASS
- [ ] `npm run build` < 4s + main bundle within +30 KB of Sprint 57.19 baseline (320.76 kB)
- [ ] `npm run lint` silent
- [ ] LLM SDK leak check `grep -rn "import openai\|import anthropic" frontend/src/` = 0
- [ ] CI 7 checks projected green (verify after PR opens)

### 4.3 Retrospective + memory + doc syncs (US-E2)
- [ ] Create `retrospective.md` Q1-Q7 + Anti-Pattern 11/11 self-check + calibration analysis (1st app of `frontend-mockup-direct-port` 0.55 class — compute `actual/committed` ratio)
- [ ] Update `memory/project_phase57_20_mockup_direct_port_foundation.md` (new file)
- [ ] Update `memory/MEMORY.md` (+1 line for Sprint 57.20)
- [ ] Update `.claude/rules/sprint-workflow.md` calibration matrix (+1 row for `frontend-mockup-direct-port` 0.55 1st app)
- [ ] Update CLAUDE.md V2 Refactor Status table:
  - Phase 57+ Frontend 16/N → 17/N
  - Latest Sprint row = 57.20 detail
  - Prev Sprint row shift (57.19 → Prev)
  - main HEAD update
  - Next Phase 候選 row update (Sprint 57.21+ candidates)
- [ ] Update SITUATION-V2-SESSION-START.md §第八部分 (recent sprints + carryovers)
- [ ] Update `claudedocs/CLAUDE.md` index if needed

### 4.4 PR + closeout
- [ ] PR: `feat(frontend, sprint-57-20): Mockup-Direct-Port Foundation — shell rewrite + 2 anchor pages (Option W; Frontend-Led, Backend-Follows)`
- [ ] CI 7 checks green
- [ ] PR merged to main
- [ ] Closeout PR (chore): doc syncs (CLAUDE.md / MEMORY.md / sprint-workflow.md / SITUATION)
- [ ] Closeout PR merged to main

---

## Anti-Pattern self-check (per `.claude/rules/anti-patterns-checklist.md`)

- [ ] **AP-1 No god component**: NEW Topbar.tsx + AppShellV2 V3 stay under 250 lines each; Sidebar at ~280 lines max
- [ ] **AP-2 No Potemkin (real data, not mocked fixtures shipped)**: anchor pages consume real backend via reused hooks; tenant switcher fixture documented as Sprint 57.21+ wire (NOT silently mocked production)
- [ ] **AP-3 No cross-directory scattering**: NEW shell components in `components/layout/`; chat-v2 components stay in `features/chat_v2/components/`
- [ ] **AP-4 No rename-only refactor**: every JSX rewrite delivers visible mockup-fidelity gain (Playwright MCP pair-verify artifact required)
- [ ] **AP-5 No hardcoded secrets**: 0 changes to .env / config / token storage
- [ ] **AP-6 No silent backend assumptions**: 0 backend changes; existing hooks consume existing endpoints
- [ ] **AP-7 No prop drilling > 2 levels**: NEW Topbar consumes auth/tenant via store hooks (NOT props from AppShellV2)
- [ ] **AP-8 No event handler swallowing errors**: SSE / HITL handlers preserved verbatim
- [ ] **AP-9 No race conditions**: TanStack Query handles refetch; no manual `useEffect` data loops added
- [ ] **AP-10 No untested critical path**: anchor pages have Vitest + chat-v2 has Playwright e2e
- [ ] **AP-11 No TypeScript `any` leak**: 0 new `any`; tsc 0 errors required

---

## Carryover (preserve per CLAUDE sacred rule: 🚧 marker + reason)

🚧 **Sprint 57.19 US-D1/D2/D3 Playwright MCP fidelity verification** (deferred from 57.19) — covered by Day 4 US-E1
🚧 **Sprint 57.19 10 NEW carryover ADs** — Sprint 57.21+ (per 57.20 plan §Cross-Sprint Carryovers)
🚧 **AD-Tailwind-v4-Config-Migration** (Sprint 57.17 carryover) — Sprint 57.22+ candidate
🚧 **AD-CI-7-GHA-PR-Permission** (Sprint 57.17 carryover) — independent infra track
🚧 **AD-Lighthouse-Visual-Hard-Gate** (longstanding carryover) — Sprint 57.21+ candidate post-baseline stability
🚧 **AD-A11y-Structural-Nits** (Sprint 57.16 carryover) — Sprint 57.21+ when chat-v2 page rewrite addresses heading-order
🚧 **AD-Mockup-Existing-Pages-Retrofit Tier 2 (admin-tenants list + tenant-settings + sla-dashboard)** — Sprint 57.22+
🚧 **Backend wire ADs bundle** (8 total per 57.19 retro) — Sprint 57.21+
