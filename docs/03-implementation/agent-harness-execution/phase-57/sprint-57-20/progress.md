# Sprint 57.20 Progress

**Sprint**: 57.20 — AD-Mockup-Direct-Port Foundation (Shell Rewrite + 2 Anchor Pages; Option W)
**Branch**: `feature/sprint-57-20-mockup-existing-pages-retrofit`
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-20-plan.md`
**Checklist**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-20-checklist.md`
**Aborted Predecessor**: `sprint-57-20-{plan,checklist}.aborted-option-Y-retrofit.md` (Option Y / per-page retrofit — superseded after Day 0 runtime capture revealed shell-level drift)

---

## Day 0 — 2026-05-17 — Setup + 三-prong + Playwright MCP pipeline

### Today's accomplishments

**Pivot decision documented**:
- Original Sprint 57.20 plan (Option Y / Tier 1 page retrofit) aborted after Day 0 runtime Playwright MCP capture revealed 5 shell-level drift dimensions that per-page patching cannot address
- User 2026-05-17 selected Option W (Frontend-Led, Backend-Follows direct-port philosophy)
- New plan + checklist drafted; old archived with `.aborted-option-Y-retrofit.md` suffix for audit trail

**Three-prong scope verify** (per `.claude/rules/sprint-workflow.md` §Step 2.5):

#### Prong 1 — Path verify
| Asset | Expected | Actual | Status |
|-------|----------|--------|--------|
| `frontend/src/components/AppShellV2.tsx` | exists | exists | ✅ |
| `frontend/src/components/Sidebar.tsx` | exists | exists | ✅ |
| `frontend/src/components/UserMenu.tsx` | exists | exists | ✅ |
| `frontend/src/components/layout/` | empty dir ready for NEW Topbar.tsx | empty dir present | ✅ |
| `frontend/src/components/topbar/` | CommandPalette + NotificationsPanel (Sprint 57.19 NEW) | confirmed both present | ✅ |
| `frontend/src/components/ui/` | shadcn primitives (Card / Button / Badge / Dialog / DropdownMenu / EmptyState / ErrorRetry / Skeleton / Tabs) | all 9 + index.ts present | ✅ |
| `frontend/src/pages/overview/index.tsx` | Sprint 57.19 US-C1 ship | exists | ✅ |
| `frontend/src/pages/chat-v2/index.tsx` | Sprint 57.8 ship | exists | ✅ |
| `reference/design-mockups/{shell,page-overview,page-chat,i18n,styles,tweaks-panel,topbar-overlays}.{jsx,css}` | mockup canonical sources | all present | ✅ |
| `frontend/public/fonts/` | font assets for Geist + Noto Sans TC | **MISSING** | ⚠️ D-PRE-5 |

#### Prong 2 — Content verify
| Plan claim | Grep verify | Result |
|-----------|-------------|--------|
| `tailwind.config.ts` declares Geist + Noto Sans TC fontFamily | grep `fontFamily` in config | ✅ confirmed (Sprint 57.18) |
| `index.css` `:root` currently light default | head -50 | ✅ confirmed — `--background: 0 0% 100%` (white); dark only in `.dark` class |
| `index.css` `--primary: 234 89% 60%` indigo from Sprint 57.19 US-A1 | grep `--primary` | ✅ confirmed |
| `features/chat-v2/` (hyphen) for chat module | ls | ❌ **D-PRE-1 (CRITICAL)** — actual is `features/chat_v2/` (underscore); pages dir uses hyphen `pages/chat-v2/` but features module uses underscore |
| `features/loops/types.ts` + `subagents/types.ts` + `state/types.ts` (Sprint 57.19 NEW) | ls | ✅ all 3 present with hooks/services/types.ts structure |
| `features/memory/` exists | ls | ✅ + has components/hooks/services/types.ts + README.md |
| `features/auth/` exists | ls | ✅ present |

#### Prong 3 — Schema verify
**N/A** — pure frontend sprint, 0 DB schema work, 0 backend changes.

### Drift findings catalogued

- **D-PRE-1 (CRITICAL — naming convention)**: `features/chat_v2/` uses underscore (Python module style) but `pages/chat-v2/` uses hyphen (URL route style). Sprint 57.20 plan + checklist mention `features/chat-v2/` (hyphen) in several places — must use `features/chat_v2/` (underscore) in Day 3 actual code. **Scope impact**: 0% shift; documentation correction only.
- **D-PRE-2 (info)**: `frontend/src/components/layout/` already exists as empty dir — NEW Topbar.tsx slot ready (no mkdir needed Day 1).
- **D-PRE-3 (info)**: `features/` has additional modules not mentioned in plan: `guardrails / orchestrator-loop / state-mgmt / subagent` (singular). Some appear to be legacy or pre-Sprint-57.19 names (e.g. `subagent` singular vs `subagents` plural NEW Sprint 57.19). **Scope impact**: 0% — Sprint 57.20 anchor pages use only `loops / memory / subagents / state / chat_v2`; legacy modules untouched.
- **D-PRE-4 (info)**: shadcn `ui/` has `tabs.tsx` (Sprint 57.19 NEW for Orchestrator 6 sub-tabs) + `dropdown-menu.tsx` (cmdk + UserMenu) — both available for Day 1 Topbar.tsx (locale dropdown) and Day 2 /overview (KPI tabs if mockup uses).
- **D-PRE-5 (BLOCKER for fidelity)**: `frontend/public/fonts/` directory does NOT exist. Geist + Noto Sans TC declared in `tailwind.config.ts` but **no font asset files bundled**. Day 1 US-B2 Geist wiring must either (a) add CDN `@import` in `index.css`, (b) install self-hosted font assets and reference via `@font-face`, or (c) accept system fallback for this sprint and open AD-Font-Asset-Bundling carryover. **Scope decision**: Option (a) CDN @import for Sprint 57.20 — faster + zero asset commits; if CDN unreliable in prod → AD upgrade to self-hosted Phase 58+.
- **D-PRE-6 (verified)**: `tailwind.config.ts` fontFamily Geist + Noto Sans TC declared correctly (Sprint 57.18). Day 1 US-B2 only needs `@layer base { body { font-family: theme('fontFamily.sans') } }` + `@import` line — no config change.
- **D-PRE-7 (verified — driver of shell rewrite)**: `index.css` `:root` is light default; dark theme only via `.dark` class on `<html>`. Mockup default = dark + `[data-variant]` mechanism. Day 1 US-B3 rewrite `index.css` for dark default in `:root` + `[data-variant]` + `[data-density]` selectors.
- **D-PRE-8 (verified)**: `index.css` already has Sprint 57.18 semantic tokens (`--success` / `--warning` / `--danger` / `--thinking` / `--tool` / `--memory` / `--info`) + risk tokens (`--risk-low` / `--risk-medium` / `--risk-high` / `--risk-critical`). Day 2 /overview + Day 3 /chat-v2 anchor pages can consume directly.
- **D-PRE-9 (port conflict — resolved as benign)**: Port 3007 LISTENING = PID 50796 (node.exe, started 5/17 01:35 AM). This IS the running Vite dev server. Per CLAUDE rule **do NOT kill node.js processes**. Vite HMR will pick up Sprint 57.20 source changes automatically → no need to spin up second dev server. ✅ Use existing 3007.
- **D-PRE-10 (verified)**: Port 8080 LISTENING = PID 44700 (python.exe, started 5/17 18:29). This is the mockup `python -m http.server 8080` running from `reference/design-mockups/`. Day 0 capture confirmed `GET /shell.jsx` returns 304. ✅
- **D-PRE-11 (verified)**: Port 8000 LISTENING = PID 41528 (python.exe, started 5/16). Likely backend uvicorn — irrelevant to Sprint 57.20 (0 backend changes).
- **D-PRE-12 (BLOCKER for capture)**: Initial Playwright MCP capture attempt with `..` prefix failed — playwright-mcp resolves `..` from `.playwright-mcp/` as project parent dir (not project root parent of `.playwright-mcp`). Resolution: use project-root-relative path `claudedocs/...` (no leading `..`). ✅ Pattern documented for Day 1-4 captures.

### Go/no-go decision

**Scope shift**: 0% (all 12 drift findings are documentation corrections, environment confirmations, or already-anticipated rewrite scope).

**Decision**: ✅ **GO** Day 1 — proceed with shell rewrite as planned. D-PRE-1 naming correction applies to Day 3 chat-v2 work; D-PRE-5 Geist asset gap resolved via CDN `@import` Option (a).

### Playwright MCP reference captures (US-A1 complete)

All 6 baseline captures at 1440×900 viewport saved to `claudedocs/4-changes/sprint-57-20-direct-port-foundation/screenshots/`:

| File | Size | Purpose |
|------|------|---------|
| `shell/mockup-shell-default.png` | 204 KB | Mockup default theme baseline for Day 1 shell rewrite reference |
| `shell/prod-shell-pre.png` | 102 KB | Production pre-Sprint-57.20 shell — Day 4 before/after comparison |
| `overview/mockup-overview.png` | 204 KB | Mockup `page-overview.jsx` rendered — Day 2 anchor page 1 target |
| `overview/prod-overview-pre.png` | 176 KB | Production `/overview` (Sprint 57.19 ship) — Day 4 comparison |
| `chat-v2/mockup-chat-v2.png` | 77 KB | Mockup `page-chat.jsx` rendered — Day 3 anchor page 2 target |
| `chat-v2/prod-chat-v2-pre.png` | 91 KB | Production `/chat-v2` (Sprint 57.8 ship, requires auth) — Day 4 comparison |

**Note on mockup-shell-default.png**: Mockup ships only one theme variant by default at `/` (no auto-switching dark/light toggle visible in console). Day 1 will use this single baseline; if 4 mockup variants (indigo / forest / violet / dawn per `tweaks-panel.jsx`) become Day 1+ work scope, additional baselines can be captured by JS-injecting `document.documentElement.dataset.variant = "forest"` etc. via `browser_evaluate`.

### Remaining for Day 1

- US-B1: AppShellV2 V3 + Topbar.tsx + Sidebar enrichment per mockup `shell.jsx` (~5-6 hr)
- US-B2: Geist + Noto Sans TC font wire via CDN `@import` + `@layer base { body }` (~1 hr)
- US-B3: `[data-variant]` + `[data-density]` mechanism + dark default in `:root` (~1 hr)
- Day 1 EOD: 14 active pages smoke test + Playwright capture POST-Day-1 shell

### Notes

- Anti-stop rule continued validation: 6 Bash + multiple Playwright tool calls executed without frequent stops — `memory/feedback_tool_result_is_not_turn_boundary.md` continues to apply correctly.
- Console errors observed on production overview (~156-162): backend cost endpoints 500 — known carryover, irrelevant to Sprint 57.20 (0 backend changes).
- Plan/checklist correction needed: replace `features/chat-v2` → `features/chat_v2` (underscore) in checklist Day 3 references. Will apply in Day 1 commit batch.

---

## Day 1 — 2026-05-17 — Shell rewrite + theme/font wire + cascade fix

### Today's accomplishments

**B1a (research, 0 file change)**:
- Read mockup `shell.jsx` (226L) + `styles.css` head (220L tokens + variants + density + layout) + current AppShellV2.tsx (99L) + Sidebar.tsx (202L) + UserMenu.tsx (178L; Sprint 57.19 extended)
- Synthesized: mockup uses grid `[232px sidebar | 1fr main]` 100vh edge-to-edge; sidebar = brand + tenant-switcher + nav + sidebar-foot (user-card); topbar = breadcrumb + tenant-pill + cmdk + locale + theme + bell + tweaks + avatar
- Identified reuse: UserMenu (Sprint 57.19 extended) handles avatar dropdown completely; Topbar avatar slot delegates; CommandPalette + NotificationsPanel mount points preserved

**B1b + B1c + B1d (commit `19c30990`)** — Shell rewrite:
- REWRITE `AppShellV2.tsx` (99→90 lines): full-screen CSS grid `[240px | 1fr]`, height:100vh, dark default, drop inline `<header>` → Topbar component. Preserve: prop interface, CommandPalette + NotificationsPanel mount, ⌘K hotkey, data-testid
- NEW `components/layout/Topbar.tsx` (~180 lines): breadcrumb + tenant pill (acme-prod · role fixture) + ⌘K cmdk button + EN/中 locale toggle + sun/moon theme toggle + divider + bell w/ unread badge + UserMenu avatar
- REWRITE `Sidebar.tsx` (202→236 lines): add mockup `.sidebar-head` brand block (LOOP-FIRST sub) + `.tenant-switcher` fixture pill + `.sidebar-foot` user identity card consuming authStore. Preserve CATEGORY_ORDER + PROP/DRAFT/SOON badges (Sprint 57.18) + collapse state

**B1e + B1f (commit `a361455c`)** — Theme + font wire:
- `index.css`: add 11 mockup layout tokens × 2 modes (`--bg/--bg-1/--bg-2/--bg-3/--bg-hover/--fg/--fg-muted/--fg-subtle/--border-strong/--primary-soft/--shadow`); add `[data-density="compact"|"comfortable"]` mechanism; add `@layer base body { font-family: Geist, Noto Sans TC, ... }`; add Noto Sans TC Google Fonts `@import`. Preserve all Sprint 57.18 semantic + risk + existing shadcn tokens
- `tailwind.config.ts`: add 11 mockup color mappings (`bg` nested + `fg` nested + `border-strong` + `primary-soft`)
- `index.html`: add `class="dark" data-variant="linear" data-density="default"` to `<html>` (first paint dark; ThemeProvider override still works)

**B1g — Cascade fix + smoke test**:
- Vitest initial run: 275/277 (2 fail in `AppShellV2.test.tsx`)
  - L52 `getByRole("heading", { level: 1 })` — V3 Topbar title was `<span>`
  - L63 `userMenu={...}` slot — V3 dropped slot rendering
- Fix: Topbar title `<span>` → `<h1>` (preserves a11y page-title-is-h1 contract); thread `userMenu` prop through AppShellV2 → Topbar override slot (default canonical `<UserMenu />`)
- Re-run: **Vitest 277/277 PASS** ✅ (the AuthShell.test "kaboom" stack trace is intentional error-boundary test fixture, not a real failure)
- `npm run build` 2.79s ✅, main bundle 320.76 kB (unchanged from Sprint 57.19 baseline; token additions absorbed by tree-shaking)
- `npm run lint` silent ✅ (--max-warnings 0)

**Playwright MCP smoke captures (4 critical pages) at 1440×900**:
- `shell/prod-shell-post-day1.png` — `/` shell baseline
- `shell/prod-overview-post-day1.png` — `/overview` (Sprint 57.19 Operations page) on new shell
- `shell/prod-cost-dashboard-post-day1.png` — `/cost-dashboard` (Sprint 57.1 ship) on new shell
- `shell/prod-governance-post-day1.png` — `/governance` (auto-redirect to /governance/approvals; Sprint 57.9 ship) on new shell
- All 4 pages: navigate succeeded, page-title set, no fatal errors (cost-dashboard 2-3 console errors = carryover backend 500 from `/api/v1/cost/*` endpoints; unrelated to Sprint 57.20)

### Anti-Pattern self-check (Day 1 scope)

- **AP-1 No god component**: Topbar 180L (under 250), AppShellV2 90L (under 100), Sidebar 236L (under 250) ✅
- **AP-2 No Potemkin**: All shell features consume real data: tenant pill from authStore.roles, bottom user card from authStore.user, breadcrumb from useLocation + ROUTES; tenant name itself is fixture documented as Sprint 57.21+ AD-UserMenu-Tenant-Switch ✅
- **AP-3 No cross-directory scattering**: Topbar in `components/layout/`; CommandPalette + NotificationsPanel in `components/topbar/` (Sprint 57.19); Sidebar + AppShellV2 + UserMenu remain in `components/` ✅
- **AP-4 No rename-only refactor**: AppShellV2 changed from flex+sticky → grid; Sidebar +3 new sections; both deliver visible mockup-fidelity gains ✅
- **AP-5 No hardcoded secrets**: 0 env/config changes ✅
- **AP-6 No silent backend assumptions**: 0 backend changes ✅
- **AP-7 No prop drilling > 2 levels**: AppShellV2 → Topbar (1 level); Topbar consumes authStore/ThemeProvider via hooks (no prop drilling) ✅
- **AP-8 No event handler swallowing errors**: ⌘K hotkey preserved, callbacks plain delegation ✅
- **AP-9 No race conditions**: state via useState + ThemeProvider context ✅
- **AP-10 No untested critical path**: AppShellV2 has Vitest cases (277 pass) ✅
- **AP-11 No TypeScript `any` leak**: 0 new `any`; tsc 0 errors ✅

### Drift findings catalogued

- **D-DAY1-1 (info)**: vitest `--reporter=basic` flag doesn't exist this version; use `npm test -- --run` (default reporter). Documented for Day 2-4 test command.
- **D-DAY1-2 (info)**: `AuthShell.test.tsx` outputs intentional "kaboom" error trace as part of error-boundary test fixture — looks like a failure in `tail` output but actual file count "63 passed" confirms no regression.
- **D-DAY1-3 (deferred)**: Detailed visual parity pair-verify (prod-post vs mockup target) for shell deferred to Day 4 US-E1 inheritance check + Day 2 (post-anchor-page-1) + Day 3 (post-anchor-page-2). Day 1 captures are baseline screenshots only; verdict in Day 4 retrospective.
- **D-DAY1-4 (info)**: Cost-dashboard console errors (2-3) are pre-existing backend 500s on `/api/v1/cost/*` endpoints; unrelated to Sprint 57.20 shell rewrite. NOT a regression.

### Remaining for Day 2

- US-C1: REWRITE `/overview` mockup-direct port (mockup `page-overview.jsx` 381 lines)
  - Read mockup analog + grep `features/loops/types.ts` + `subagents/types.ts` + `memory/types.ts` to confirm data shape
  - REWRITE `pages/overview/index.tsx` JSX 100% per mockup; reuse existing hooks
  - Add `overview.*` i18n keys (en + zh-TW)
  - Adapt Vitest spec
  - Playwright MCP pair-verify
- Carryover from Day 1: visual fidelity verdict (Day 4 audit)

### Notes

- Branch on track: 4 commits (Day 0 `c0c79829` + Day 1 B1b-d `19c30990` + B1e-f `a361455c` + pending B1g)
- 0 backend changes ✅
- 0 features layer touched ✅
- 14 active pages prop interface backward compat preserved (`pageTitle` / `headerActions` / `userMenu` all still work)
- Anti-stop rule continued validation: 5+ Bash + 8+ Playwright tool calls within aligned scope, 0 user-blocking interruptions
- 1 NEW carryover opened: **AD-Geist-Font-Asset-Bundling** Phase 58+ (self-host via `@fontsource/geist-sans` for offline + perf; currently CDN Noto Sans TC + system Geist fallback works for online dev)

---

## Day 2 — 2026-05-17 — `/overview` token migration + visual refinement

### Today's accomplishments

**Discovery**: Sprint 57.19 US-C1 OverviewPage.tsx **already ships 1:1 mockup port** (726 lines: 4 KPI cards + ActiveLoops with real `useActiveLoops` hook + HITL fixture + Cost burn SVG + Providers fixture + Incidents fixture + Error trend SVG + Quick actions strip). Day 2 真正 scope **reduces** from "full rewrite" to **token migration shadcn → mockup tree** for visual consistency with new shell + visual refinements.

**Token migration (8 `replace_all` edits)**:
- `bg-card text-card-foreground` → `bg-bg-1 text-foreground` (Card containers)
- `border border-border bg-card` → `border border-border bg-bg-1` (Stat cards)
- Added `shadow-sm` to Stat cards for mockup parity
- `text-muted-foreground` → `text-fg-muted` (primary muted text)
- `hsl(var(--muted-foreground))` → `hsl(var(--fg-subtle))` (SVG text fills — finer subtle gray per mockup `var(--fg-subtle)`)
- `hover:bg-muted/40` → `hover:bg-bg-hover` (interactive surfaces)
- `bg-muted/30` → `bg-bg-2` (secondary surface)
- `bg-muted` → `bg-bg-2` (general muted bg; e.g. mini progress bar tracks)

**MHist entry** in OverviewPage.tsx 1-line per file-header-convention.md.

**Data sources preserved**:
- `useActiveLoops(10)` — real backend (Sprint 57.19 US-B1 GET /api/v1/loops) ✅
- HITL_QUEUE / RECENT_INCIDENTS / PROVIDERS / ERROR_24H — fixtures unchanged; AD-Overview-Backend-Wire Sprint 57.21+ deferred
- CostBurnChart inline SVG — fixture math unchanged (D-DAY1-4: backend cost endpoints 500 — defer real wire)

### Anti-Pattern self-check (Day 2 scope)

- **AP-1 No god component**: OverviewPage.tsx 727 lines = component-per-card pattern (ActiveLoopsCard / HITLQueueCard / ProvidersCard / IncidentsCard) + 2 inline SVG charts; each under 150 lines ✅
- **AP-2 No Potemkin**: All non-fixture data uses real hook (useActiveLoops); fixtures explicitly documented as Sprint 57.21+ wire ADs ✅
- **AP-3 No cross-directory scattering**: page in `pages/overview/`; uses `features/loops/` hook + types ✅
- **AP-4 No rename-only refactor**: Token migration delivers visible visual consistency gain (Card backgrounds now match new shell dark theme; previously rendered as transparent due to bg-card token gap) ✅
- **AP-5 No hardcoded secrets**: 0 ✅
- **AP-6 No silent backend assumptions**: 0 backend changes; fixture banners surface AD references ✅
- **AP-7 No prop drilling**: hooks consume directly ✅
- **AP-8 No event handler swallowing errors**: useActiveLoops error → `<div role="alert">{error.message}</div>` ✅
- **AP-9 No race conditions**: TanStack Query refetch interval 10s + staleTime 5s ✅
- **AP-10 No untested critical path**: 277 Vitest pass including overview test cases ✅
- **AP-11 No TS any**: 0 ✅

### Tests + build + visual

- **Vitest 277/277 PASS** ✅ (no test changes needed — assertions test text content + tone classes which are preserved)
- **Build 2.70s** ✅ / main bundle **320.76 kB unchanged** ✅
- **Lint silent** ✅
- **Playwright POST capture** at 1440×900 → `screenshots/overview/prod-overview-post-day2.png` (after dev-login flow to authenticate; RequireAuth wrapper enforces auth)

### Drift findings Day 2

- **D-DAY2-1 (info)**: Sprint 57.19 OverviewPage used `bg-card` (undefined token; rendered transparent in dark theme — visually broken before Sprint 57.20 shell tokens). Token migration fixes this — was a silent latent visual bug.
- **D-DAY2-2 (deferred)**: Cost burn chart uses fixture math; AD-Cost-Backend-Wire (folds into AD-Overview-Backend-Wire bundle) Sprint 57.21+ when /api/v1/cost/* endpoints fixed (D-DAY1-4 carryover).
- **D-DAY2-3 (deferred)**: useCostSummary hook exists (`features/cost-dashboard/hooks/useCostSummary.ts`) — could replace fixture in Sprint 57.21+ once backend cost endpoint stabilizes.

### Remaining for Day 3

- US-D1: `/chat-v2` mockup-direct port (mockup `page-chat.jsx` 533 lines) — REWRITE preserving SSE/HITL/state machine 100%
- Use `features/chat_v2/` (underscore — D-PRE-1 correction)
- Adapt Vitest + Playwright spec selectors per new DOM
- Playwright MCP pair-verify chat-v2

### Notes

- Day 2 was lighter-than-expected scope (3 hr → 1.5 hr) because Sprint 57.19 already shipped the structural port. Day 2 = visual consistency layer.
- Calibration implication: if Day 3 (chat-v2) is similar (already partially mockup-ported in Sprint 57.8 + Sprint 57.16 inline-style sweep), Sprint 57.20 total may finish under bottom-up estimate. Will recompute ratio at Day 4 retrospective.
- 0 backend changes; 0 features layer touched; 0 i18n keys added (Sprint 57.19 keys reused)
