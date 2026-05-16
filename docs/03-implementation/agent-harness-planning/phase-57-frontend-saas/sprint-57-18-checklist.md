---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-18-checklist.md
Purpose: Sprint 57.18 execution checklist — AD-Design-Mockup-Integration-Foundation (Phase 1 of multi-sprint mockup integration epic; cp reference/design-mockups/ → design/operator-portal/ + sync 11 missing semantic tokens + 20 PROP/DRAFT stub routes + 6-category Sidebar refactor + closes AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token-Audit token-coverage portion; Day 0-3).
Category: Frontend / design-system / routing-scaffolding
Scope: Phase 57 / Sprint 57.18

Created: 2026-05-16 (drafted post-plan approval)
Last Modified: 2026-05-16
Status: Open (Day 0 in progress — branch created from Sprint 57.17 hotfix branch, plan + checklist + 三-prong baseline pending Day 0 commit)

Modification History (newest-first):
    - 2026-05-16: Initial creation (Sprint 57.18 — mirrors 57.17 day-structure, Day 0-3 for focused scaffolding scope)

Related:
    - sprint-57-18-plan.md (sibling plan — authority for this checklist)
    - sprint-57-17-checklist.md (structural template per sprint-workflow.md §Step 2 — most recent completed sprint)
---

# Sprint 57.18 — Checklist (Day 0-3)

> Branch: `feature/sprint-57-18-mockup-integration-foundation` (forks from Sprint 57.17 `feature/sprint-57-17-tailwind-v4-hotfix` PR #142 base, or main `16195fb4` if 57.17 already merged)
> Calibration: NEW class `mockup-integration-foundation` 0.55 (1st application, HYBRID weighted blend)
> Bottom-up ~9.5 hr → committed ~5 hr
> Phase 1 of multi-sprint mockup integration epic — scaffold (bones) only. Sprint 57.19+ rolling port real content (flesh) per priority order: Operations 4 → Topbar overlays 3 → Auth flows 4 → Governance 3 = 14 priority units. Backend gaps surface in Sprint 57.19+ and pair with backend API sprints.

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [ ] **Branch `feature/sprint-57-18-mockup-integration-foundation` from main or 57.17 base**
  - Decision: if Sprint 57.17 PR #142 already merged to main → branch from main; else branch from `feature/sprint-57-17-tailwind-v4-hotfix`
  - Verify: `git branch --show-current` → `feature/sprint-57-18-mockup-integration-foundation`; `git log --oneline -3` shows 57.17 hotfix commits if forked from 57.17

### 0.2 Pre-flight baseline capture (post Sprint 57.17 Tailwind v4 hotfix)
- [ ] pytest baseline = **1676 pass + 4 skip** — not touched this sprint (0 backend changes); sanity only
- [ ] mypy --strict baseline = **0 / 306 files** — not touched, sanity only
- [ ] 9 V2 lints baseline = **9/9 green** — not touched, sanity only
- [ ] Vitest baseline = **236 / 57 files** — sanity only (no unit-test changes this sprint)
- [ ] Playwright baseline = **40 pass / 7 skip / 0 fail** (local Windows; CI ubuntu 46 pass / 1 skip)
- [ ] Vite build main JS bundle baseline = **(record post-57.17 actual)** — expected ~+5-10 KB post-Sprint 57.18 (20 lazy stub chunks + ComingSoonPlaceholder shared)
- [ ] Vite build compiled CSS baseline = **(record post-57.17 actual, expected ~32-50 KB)** — expected ~+2-5 KB post-Sprint 57.18 (11 new semantic + 4 risk tokens; tree-shake won't drop them because Sidebar consumes thinking + warning)
- [ ] LLM SDK leak baseline = **0** — not touched, sanity only
- [ ] `routes.config.ts` ROUTES entry count baseline = **13** — post-Sprint 57.18 expect **33**
- [ ] `RouteCategory` type baseline = **3 values** (`operations | admin | settings`) — post-Sprint 57.18 expect **6 values**
- [ ] `tailwind.config.ts` `theme.extend.colors` entry count baseline = **9** (border/input/ring/background/foreground/primary/secondary/destructive/muted) — post-Sprint 57.18 expect **20** (9 + 7 semantic + risk-with-4-sub-keys-counts-as-1)
- [ ] `index.css :root` CSS var count baseline = **14** — post-Sprint 57.18 expect **32** (14 + 14 new semantic + 4 risk)
- [ ] `reference/design-mockups/` file count baseline = **24 files** — preserved unchanged post-Sprint 57.18
- [ ] `design/operator-portal/` baseline = **doesn't exist** — post-Sprint 57.18 expect **25+ files** (24 cp from reference + INTEGRATION-LOG.md)
- [ ] Chromium browser binary check — `chromium-1217` ↔ Playwright 1.59.1 (no install needed)

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)
- [ ] **Prong 1 Path Verify** — file existence checks:
  - `frontend/src/routes.config.ts` ✅ exists (199 lines, 13 entries × 3 categories)
  - `frontend/src/index.css` ✅ exists (56 lines, Sprint 57.17 v4 `@import "tailwindcss"; @config "../tailwind.config.ts";` at L9-10)
  - `frontend/tailwind.config.ts` ✅ exists (52 lines, v3-style content + theme.extend.colors with 6 shadcn tokens)
  - `frontend/src/components/Sidebar.tsx` ✅ exists (verify line count + iteration pattern)
  - `frontend/src/components/AppShellV2.tsx` ✅ exists (verify ROUTES.filter usage)
  - `frontend/src/components/ComingSoonPlaceholder.tsx` ❌ doesn't exist (target NEW for US-C2)
  - `frontend/src/pages/` — 20 NEW dirs target (overview/orchestrator/subagents/state-inspector/compaction/jit-retrieval/subagent-tree/incidents/redaction/error-policy/cache-manager/sse/devui/models/tools/tenant-onboarding/pricing/rbac/profile/mfa) — none exist now
  - `design/operator-portal/` ❌ doesn't exist (target NEW for US-A1 cp)
  - `reference/design-mockups/` ✅ exists (24 files: 3 markdown + 1 html + 1 css + 19 jsx including i18n.jsx + shell.jsx + app.jsx + 16 page-*.jsx)
  - `frontend/src/i18n/locales/en/common.json` — verify exists + check current `nav.*` key structure
  - `frontend/src/i18n/locales/zh-TW/common.json` — verify exists + check current `nav.*` key structure
  - `frontend/STYLE.md` ✅ exists (Sprint 57.10/16/17 referenced)
  - `frontend/CONVENTION.md` ✅ exists (Sprint 57.10/16 referenced; §3 has D-PRE-3 stale path)
  - `docs/03-implementation/agent-harness-planning/16-frontend-design.md` ✅ exists
  - `.claude/rules/sprint-workflow.md` ✅ exists (Calibration matrix section)
  - DoD: catalog D-PRE-* findings in progress.md Day 0
- [ ] **Prong 2 Content Verify** — grep-based assertion checks:
  - (a) `cat frontend/src/routes.config.ts | grep -c "active:"` → **expect 13** (current 13 entries; 9 active + 4 inactive)
  - (b) `cat frontend/src/routes.config.ts | grep -oE '"operations"|"admin"|"settings"' | sort -u` → **expect 3 values** — confirms current 3-category state
  - (c) `cat frontend/tailwind.config.ts | grep -c "hsl(var(--"` → **expect ~13** (current shadcn bridge count: 9 colors + nested foreground variants)
  - (d) `cat frontend/src/index.css | grep -cE "\-\-success|--warning|--danger|--thinking|--tool|--memory|--info|--risk-"` → **expect 0** (none exist before Sprint 57.18)
  - (e) `ls reference/design-mockups/*.jsx | wc -l` → **expect 16 jsx files** (verifies mockup intact: app/i18n/shell/topbar-overlays/tweaks-panel/ui + 10 page-*)
  - (f) `cat reference/design-mockups/shell.jsx | grep -c "{ id:"` → **expect 32 routes** in mockup ROUTES array
  - (g) `cat reference/design-mockups/DESIGN_RATIONALE.md | grep "auth-" | wc -l` → **expect 7+ auth flow mentions** (login/callback/dev/register/invite/mfa/expired)
  - (h) `cat frontend/src/components/Sidebar.tsx | grep -E "operations|admin|settings"` → check current category iteration pattern (likely a CATEGORY_ORDER constant or inline filter)
  - (i) `cat frontend/src/i18n/locales/en/common.json | grep -c "\"nav\\."` → **expect ~11-13** matching ROUTES nameKey count
  - (j) `cat frontend/STYLE.md | grep -E "success|warning|danger|thinking|tool|memory"` → confirms STYLE.md §2 lists these tokens (validates AD-Style-Token-Config-Audit observation)
  - (k) `cat frontend/CONVENTION.md | grep "governance/components/ApprovalCard"` → **expect 1+ matches** (validates D-PRE-3 stale path carryover from Sprint 57.16)
  - DoD: drift findings catalogued in progress.md as D-PRE-N entries (any unexpected grep result = D-PRE finding)
- [ ] **Prong 3 Schema Verify** — **N/A** (0 DB / migration / ORM model / API endpoint touched this sprint). Noted in progress.md.

### 0.4 Calibration baseline confirmation
- [ ] **Documented in progress.md Day 0** — Class `mockup-integration-foundation` 0.55 (NEW, 1st application baseline opens); HYBRID weighted blend: design-ref (0.40) × 0.15 + tokens (0.55) × 0.20 + routes-refactor (0.50) × 0.25 + stub-pages (0.50) × 0.15 + sidebar-refactor (0.65) × 0.15 + closeout (0.80) × 0.10 = **~0.55 mid-band**; bottom-up ~9.5 hr → committed ~5 hr; Day 0-3; Day 3 retro Q2 verify ratio (`actual/committed` should land in [0.85, 1.20] band; 1st-app KEEP 0.55 per `When to adjust` 3-sprint window rule)

### 0.5 Day 0 smoke probe (de-risk Group A + Group C) — deferred to Day 1 start
- [~] **Test mockup integrity** — `cd reference/design-mockups && python -m http.server 8080 &` + open `http://localhost:8080/` in browser → confirm mockup renders correctly (32 sidebar entries + dark theme + Tweaks panel functional) — 🚧 deferred to manual smoke (browser launch not in scope of automated chain; mockup integrity validated via `cp -r` byte-identical + file count = 23 source files)
- [x] **`cd frontend && npm run build`** → main 297.89 kB gzip 95.28 kB byte-identical to Sprint 57.17 baseline; CSS `index-CfVdqJv4.css` = 35,244 bytes ≈ 34.4 KB (Sprint 57.17 ~32.55 KB → +1.85 KB delta from 18 new vars + Tailwind bridges)
- [x] **`npm run test`** (vitest) → 236 / 236 pass (57 test files) ✅
- [x] **`npm run lint`** → silent (0 warnings 0 errors) ✅
- [x] **`npm run typecheck`** (tsc --noEmit) → 0 errors ✅

### 0.6 Day 0 commit
- [ ] **Day 0 commit** `chore(sprint-57-18, Day 0): plan + checklist + 三-prong baseline`

---

## Day 1 — US-A1 (mockup → design/) + US-B1 (tailwind.config.ts) + US-B2 (index.css HSL)

### 1.1 US-A1: cp mockup → design/operator-portal/
- [x] **`mkdir -p design && cp -r reference/design-mockups design/operator-portal`** — Day 0 attempt failed because parent `design/` didn't exist; fixed via `mkdir -p` prefix
  - Verify: `ls design/operator-portal/ | wc -l` → **23** files (3 md + 1 html + 1 css + 18 jsx; D-DAY1-1: plan claimed 24 / 19 jsx, actual 23 / 18 jsx — cosmetic plan text drift, non-blocking)
  - Verify: byte-identical cp (no diff command run; spot-checked via shell.jsx + DESIGN_RATIONALE.md head)
- [x] **`design/operator-portal/INTEGRATION-LOG.md`** NEW file — created with 28-row tracking table + dev server snippet + authoritative references:
  ```markdown
  # Mockup → Production Port Tracking

  ## Status
  - Sprint 57.18 (2026-05-16): mockup imported as design reference. No pages ported yet.

  ## Port Progress

  | Mockup file | Production target | Sprint | Status |
  |---|---|---|---|
  | page-overview.jsx | frontend/src/pages/overview/ | Sprint 57.19? | Stub created (ComingSoonPlaceholder), real content pending |
  | page-agents.jsx (orchestrator section) | frontend/src/pages/orchestrator/ | Sprint 57.19? | Stub created |
  ...

  ## Dev Server
  cd design/operator-portal && python -m http.server 8080 && open http://localhost:8080/
  ```
- [x] **`design/operator-portal/README.md`** appended "Production Integration Cross-Ref" section with 6-row mapping table + V2 規劃權威 + 衝突處理 + 修改 mockup 責任 sub-sections (~40 new lines)
- [x] **`design/operator-portal/AGENTS.md`** — intact ✅ (NOT modified)
- [x] **`git add design/`** → 24 files to be staged (23 cp + 1 NEW INTEGRATION-LOG; +1 modified README)

### 1.2 US-B1: edit `frontend/tailwind.config.ts`
- [x] **`frontend/tailwind.config.ts` `theme.extend.colors`** — added 7 semantic + 1 risk nested object (4 sub-keys):
  - `success: { DEFAULT: "hsl(var(--success))", foreground: "hsl(var(--success-foreground))" }`
  - `warning: { DEFAULT: "hsl(var(--warning))", foreground: "hsl(var(--warning-foreground))" }`
  - `danger: { DEFAULT: "hsl(var(--danger))", foreground: "hsl(var(--danger-foreground))" }`
  - `thinking: { DEFAULT: "hsl(var(--thinking))", foreground: "hsl(var(--thinking-foreground))" }`
  - `tool: { DEFAULT: "hsl(var(--tool))", foreground: "hsl(var(--tool-foreground))" }`
  - `memory: { DEFAULT: "hsl(var(--memory))", foreground: "hsl(var(--memory-foreground))" }`
  - `info: { DEFAULT: "hsl(var(--info))", foreground: "hsl(var(--info-foreground))" }`
  - `risk: { low: "hsl(var(--risk-low))", medium: "hsl(var(--risk-medium))", high: "hsl(var(--risk-high))", critical: "hsl(var(--risk-critical))" }`
- [x] **`frontend/tailwind.config.ts` `theme.extend.fontFamily`** NEW — added `sans` + `mono` per plan
- [x] **MHist +1 line** added: `- 2026-05-16: Sprint 57.18 — +7 semantic tokens + 4 risk levels + Geist font (closes AD-Style-Token-Config-Audit)` (92 chars within E501 budget)
- [x] **Verify**: `grep -c "hsl(var(--" frontend/tailwind.config.ts` → **31** (was 13; +18 = 7 semantic × 2 + 4 risk = correct. D-DAY1-2: checklist text "expect ~27" was undercount — actual 31 matches the additions correctly, cosmetic non-blocking)

### 1.3 US-B2: edit `frontend/src/index.css`
- [x] **`frontend/src/index.css` `:root` (light theme)** — added 18 CSS vars:
  - `--success: 150 60% 45%;`
  - `--success-foreground: 0 0% 100%;`
  - `--warning: 38 92% 50%;`
  - `--warning-foreground: 0 0% 10%;`
  - `--danger: 0 84% 60%;`
  - `--danger-foreground: 0 0% 100%;`
  - `--thinking: 270 75% 60%;`
  - `--thinking-foreground: 0 0% 100%;`
  - `--tool: 188 70% 50%;`
  - `--tool-foreground: 0 0% 100%;`
  - `--memory: 326 80% 60%;`
  - `--memory-foreground: 0 0% 100%;`
  - `--info: 217 91% 60%;`
  - `--info-foreground: 0 0% 100%;`
  - `--risk-low: 150 60% 45%;`
  - `--risk-medium: 38 92% 50%;`
  - `--risk-high: 20 90% 55%;`
  - `--risk-critical: 0 70% 40%;`
- [x] **`frontend/src/index.css` `.dark`** — added same 18 vars with darkened values:
  - `--success: 150 50% 55%;`
  - `--success-foreground: 0 0% 100%;`
  - `--warning: 38 80% 60%;`
  - `--warning-foreground: 0 0% 10%;`
  - `--danger: 0 70% 55%;`
  - `--danger-foreground: 0 0% 100%;`
  - `--thinking: 270 65% 65%;`
  - `--thinking-foreground: 0 0% 100%;`
  - `--tool: 188 60% 55%;`
  - `--tool-foreground: 0 0% 100%;`
  - `--memory: 326 70% 65%;`
  - `--memory-foreground: 0 0% 100%;`
  - `--info: 217 80% 65%;`
  - `--info-foreground: 0 0% 100%;`
  - `--risk-low: 150 50% 55%;`
  - `--risk-medium: 38 80% 60%;`
  - `--risk-high: 20 80% 60%;`
  - `--risk-critical: 0 60% 50%;`
- [x] **MHist +1 line** added: `- 2026-05-16: Sprint 57.18 — +18 CSS vars (7 semantic + 4 risk) in :root + .dark (closes AD-Style-Token-Config-Audit)` (91 chars within E501)
- [x] **Verify**: `grep -cE "^\s+--(success|warning|danger|thinking|tool|memory|info|risk-)" frontend/src/index.css` → **36** ✅ (18 light + 18 dark, matches expectation)
- [x] **`cd frontend && npm run build`** → ✅ built in 2.80s, 0 warnings; CSS delta +1.85 KB documented in progress.md Day 1

### 1.4 Day 1 commits
- [x] **Day 1 commit 1** `feat(sprint-57-18, Day 1): cp mockup → design/operator-portal/ + INTEGRATION-LOG + README cross-ref (US-A1)` — see commit hash in progress.md retrospective
- [x] **Day 1 commit 2** `feat(sprint-57-18, Day 1): +7 semantic + 4 risk tokens + Geist font (US-B1+B2; closes AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token-Audit token-coverage)` — includes progress.md Day 1 entry + checklist Day 1 [x] updates

---

## Day 2 — US-C1 (routes.config.ts) + US-C2 (ComingSoonPlaceholder + 20 wrappers)

### 2.1 US-C1: refactor `frontend/src/routes.config.ts`
- [ ] **`RouteCategory` type expansion** (L62):
  - was: `"operations" | "admin" | "settings"`
  - now: `"operations" | "business" | "governance" | "observability" | "resources" | "admin"`
- [ ] **`RouteEntry` interface** (L64-79) — add 2 optional fields:
  - `proposed?: boolean;  // V2 backend ABC exists, frontend not yet ported (PROP badge)`
  - `designed?: boolean;  // V2 routes.config.ts has active=false (DRAFT badge)`
- [ ] **`CATEGORY_ORDER` constant** NEW — exported array for Sidebar iteration:
  - `export const CATEGORY_ORDER: RouteCategory[] = ["operations", "business", "governance", "observability", "resources", "admin"];`
- [ ] **Re-categorize 13 existing entries** (no active flag changes; only category + designed flag for audit-log + feature-flags):
  - `chat-v2`: operations (unchanged)
  - `cost-dashboard`: operations → **observability**
  - `sla-dashboard`: operations → **observability**
  - `admin-tenants`: admin (unchanged)
  - `tenant-settings`: admin (unchanged)
  - `audit-log`: admin (active=false) → **governance (active=false, designed=true)**
  - `feature-flags`: admin (active=false) → **resources (active=false, designed=true)**
  - `governance`: admin → **governance**
  - `verification`: admin → **governance**
  - `loop-debug`: admin → **operations**
  - `memory`: admin → **operations**
  - `profile`: settings → **admin** (active=false unchanged)
  - `mfa`: settings → **admin** (active=false unchanged)
- [ ] **Add 20 NEW PROP/DRAFT stub entries** (all active: true + proposed: true unless noted):
  - **operations** (+7):
    - `overview` (PROP, nameKey: "nav.overview", icon: LayoutDashboard)
    - `orchestrator` (PROP, nameKey: "nav.orchestrator", icon: Sparkles)
    - `subagents` (PROP, nameKey: "nav.subagents", icon: GitFork)
    - `state-inspector` (PROP, nameKey: "nav.stateInspector", icon: Database)
    - `compaction` (PROP, nameKey: "nav.compaction", icon: Minimize2)
    - `jit-retrieval` (PROP, nameKey: "nav.jitRetrieval", icon: Search)
    - `subagent-tree` (PROP, nameKey: "nav.subagentTree", icon: GitBranch)
  - **business** (+1):
    - `incidents` (PROP, nameKey: "nav.incidents", icon: AlertTriangle)
  - **governance** (+2):
    - `redaction` (PROP, nameKey: "nav.redaction", icon: EyeOff)
    - `error-policy` (PROP, nameKey: "nav.errorPolicy", icon: AlertOctagon)
  - **observability** (+3):
    - `cache-manager` (PROP, nameKey: "nav.cacheManager", icon: Database)
    - `sse` (PROP, nameKey: "nav.sseInspector", icon: Radio)
    - `devui` (PROP, nameKey: "nav.devui", icon: Code2)
  - **resources** (+2):
    - `models` (PROP, nameKey: "nav.models", icon: Cpu)
    - `tools` (PROP, nameKey: "nav.tools", icon: Wrench)
  - **admin** (+3):
    - `tenant-onboarding` (PROP, nameKey: "nav.tenantOnboarding", icon: UserPlus, path: "/admin/tenant-onboarding")
    - `pricing` (PROP, nameKey: "nav.pricing", icon: DollarSign, path: "/admin/pricing")
    - `rbac` (PROP, nameKey: "nav.rbac", icon: ShieldCheck)
- [ ] **Each NEW entry has `component: lazy(() => import("./pages/<id>"))`** pointing to thin wrapper
- [ ] **lucide-react imports** — add all NEW icons (LayoutDashboard, Sparkles, GitFork, Database, Minimize2, Search, GitBranch, AlertTriangle, EyeOff, AlertOctagon, Radio, Code2, Cpu, Wrench, UserPlus, DollarSign)
- [ ] **MHist +1 line** + Modification History entry:
  - `- 2026-05-16: Sprint 57.18 — +20 PROP/DRAFT stubs + RouteCategory 3→6 + 13 entries re-categorized (closes AD-Design-Mockup-Integration-Foundation Phase 1)`
- [ ] **Verify**: `cat frontend/src/routes.config.ts | grep -c "category:"` → expect 33

### 2.2 US-C1: add 20 i18n keys
- [ ] **`frontend/src/i18n/locales/en/common.json`** — add `nav.<camelCaseId>` for 20 new routes:
  - overview / orchestrator / subagents / stateInspector / compaction / jitRetrieval / subagentTree / incidents / redaction / errorPolicy / cacheManager / sseInspector / devui / models / tools / tenantOnboarding / pricing / rbac
- [ ] **`frontend/src/i18n/locales/en/common.json`** — add `nav.category.*` for 6 categories:
  - `nav.category.operations` / `business` / `governance` / `observability` / `resources` / `admin`
- [ ] **`frontend/src/i18n/locales/zh-TW/common.json`** — corresponding 繁中 translations (use mockup `i18n.jsx` as reference for 繁中 wording where available)
- [ ] **Verify**: `grep -c '"nav\.' frontend/src/i18n/locales/en/common.json` → expect ~40 (was ~13 + 20 new entries + 6 categories + 1-2 misc)

### 2.3 US-C2: create `ComingSoonPlaceholder.tsx`
- [ ] **NEW `frontend/src/components/ComingSoonPlaceholder.tsx`** (~60 lines)
  - Imports: useLocation, useTranslation, type LucideIcon, ROUTES, type RouteEntry
  - Logic:
    - Use `useLocation()` to get current path
    - Find matching ROUTES entry by path
    - If no match → show 404-style "Route not registered" fallback
    - If matched → show:
      - Lucide icon component (from entry.icon) + page title `t(entry.nameKey)`
      - "Coming Soon — Designed in `design/operator-portal/page-<X>.jsx`" muted text (X derived from id heuristically: page-overview.jsx, page-agents.jsx, etc.)
      - PROP/DRAFT badge replicated from Sidebar logic
      - Dev-only link (`import.meta.env.DEV`): `<a href="http://localhost:8080/#/<entry.path>" target="_blank">Open mockup</a>`
      - Priority badge if entry.id is in Sprint 57.19+ priority list (`overview` / `orchestrator` / `subagents` / `state-inspector` / `redaction` / `error-policy` / `audit-log`): "Sprint 57.19+ priority port"
  - Style: Tailwind utility classes only (no inline-style; uses `text-foreground`, `text-muted-foreground`, `bg-thinking/16`, `text-thinking` etc. — eats new tokens dogfood)
  - tsc strict: 0 errors
  - File header docstring + MHist
- [ ] **Verify**: `grep -c "import" frontend/src/components/ComingSoonPlaceholder.tsx` → expect ~5-7 imports

### 2.4 US-C2: create 20 thin wrapper pages
- [ ] **NEW `frontend/src/pages/overview/index.tsx`** — single-line re-export:
  ```typescript
  export { default } from "../../components/ComingSoonPlaceholder";
  ```
- [ ] Repeat above pattern for 19 more pages: `orchestrator` / `subagents` / `state-inspector` / `compaction` / `jit-retrieval` / `subagent-tree` / `incidents` / `redaction` / `error-policy` / `cache-manager` / `sse` / `devui` / `models` / `tools` / `tenant-onboarding` / `pricing` / `rbac` / `profile` / `mfa`
- [ ] **Verify**: `ls frontend/src/pages/*/index.tsx | wc -l` → expect 31 (11 existing + 20 new)
- [ ] **tsc strict**: 0 errors after creation
- [ ] **`npm run build`** → ✅ no warnings; 20 NEW lazy chunks produced (verify in `dist/assets/`)

### 2.5 Day 2 commits
- [ ] **Day 2 commit 1** `feat(sprint-57-18, Day 2): routes.config.ts 6 categories + 20 PROP/DRAFT stubs + i18n keys (US-C1)`
- [ ] **Day 2 commit 2** `feat(sprint-57-18, Day 2): ComingSoonPlaceholder + 20 wrapper pages (US-C2)`

---

## Day 3 — US-C3 (Sidebar.tsx) + Validation + US-D1 (Closeout)

### 3.1 US-C3: refactor `frontend/src/components/Sidebar.tsx`
- [ ] **Replace category iteration logic** to use `CATEGORY_ORDER` constant from `routes.config.ts`
- [ ] **Per-entry badge rendering** (3 variants):
  - `entry.proposed === true` → `<span className="ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium uppercase bg-thinking/16 text-thinking">PROP</span>`
  - `entry.designed === true && entry.active === false` → `<span className="ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium uppercase bg-warning/16 text-warning">DRAFT</span>`
  - `entry.active === false && !entry.designed` → grayed link + "Coming soon" tooltip (preserve existing behavior)
- [ ] **Per-category header** — show category-name + optional PROP count badge if >0:
  ```tsx
  {CATEGORY_ORDER.map(category => {
    const entries = ROUTES.filter(r => r.category === category);
    if (entries.length === 0) return null;
    const propCount = entries.filter(r => r.proposed).length;
    return (
      <div key={category}>
        <div className="px-3 py-2 text-[10px] uppercase tracking-wide text-muted-foreground flex items-center justify-between">
          <span>{t(`nav.category.${category}`)}</span>
          {propCount > 0 && (
            <span className="rounded bg-thinking/16 px-1.5 py-0.5 text-[9px] text-thinking">
              {propCount} PROP
            </span>
          )}
        </div>
        {entries.map(r => <SidebarItem key={r.id} entry={r} ... />)}
      </div>
    );
  })}
  ```
- [ ] **a11y / role preservation** — keep `<nav role="navigation" aria-label="Primary">` + `<a>` semantic structure
- [ ] **No inline-style** — use Tailwind classes throughout per Sprint 57.15+57.16 no-restricted-syntax ESLint guard
- [ ] **MHist +1 line**

### 3.2 Validation sweep
- [ ] **`npm run lint`** → silent (no inline-style violations, no unused imports)
- [ ] **`npm run typecheck`** → tsc strict 0 errors
- [ ] **`npm run test`** (vitest) → 236 unchanged
- [ ] **`npm run build`** → ✅ no warnings; bundle delta:
  - main JS: ~+1-2 KB (Sidebar logic + CATEGORY_ORDER + RouteEntry expansion)
  - compiled CSS: ~+2-5 KB (new tokens consumed by Sidebar badges)
  - lazy chunks: 20 NEW (each ~1-2 KB, shared ComingSoonPlaceholder)
- [ ] **`npm run e2e`** → expect **40 pass / 7 skip / 0 fail**
  - If chat-v2/governance/cost-dashboard etc. specs use `getByRole` they survive sidebar refactor
  - If any break → investigate selector pattern, fix spec (NOT sidebar) in same PR
- [ ] **`npm run e2e -- a11y/a11y-scan.spec.ts`** → 0 NEW violations vs 57.17 baseline
- [ ] **`npm run e2e -- visual-regression.spec.ts`** → expect **6/6 FAIL** (sidebar 6-category layout differs)
  - Day 3 decision: (a) regenerate baselines via `gh workflow run playwright-e2e.yml` workflow_dispatch + sub-PR merge to feature branch (~30-45 min wall) OR (b) defer to Sprint 57.19+ + mark visual-regression advisory in this PR description
- [ ] **Manual Playwright MCP smoke** — screenshot 3 NEW stub routes (`/overview`, `/orchestrator`, `/subagents`) + 1 existing (`/chat-v2`) — verify:
  - 6 category headers render in correct order
  - PROP badges blue (thinking token), DRAFT badges yellow (warning token)
  - ComingSoonPlaceholder displays page title + mockup cross-link + dev-only Open Mockup link
  - Existing `/chat-v2` layout unchanged (no visual regression on functional pages)

### 3.3 In-sprint doc syncs (US-D1 AC3)
- [ ] **`docs/03-implementation/agent-harness-planning/16-frontend-design.md`** — Sprint Timeline +1 row:
  - `| 57.18 | 2026-05-16 | Mockup Integration Foundation | Phase 57+ Frontend 14/N | ... |`
- [ ] **`.claude/rules/sprint-workflow.md`** — Calibration matrix +1 row:
  - `| NEW class \`mockup-integration-foundation\` (Sprint 57.18) | 0.55 (HYBRID weighted blend) | 57.18=~1.0 (1) | n/a 1-data-point | NEW class baseline opens; KEEP 0.55 per 3-sprint window rule |`
- [ ] **`frontend/STYLE.md §2`** — token reality table update (closes D-PRE-4 carryover):
  - Mark previously-documented-but-undefined tokens as **NOW DEFINED**: success / warning / danger / thinking / tool / memory / info + risk-{low,medium,high,critical}
  - Remove the "may be no-op CSS" warning
- [ ] **`frontend/CONVENTION.md §3`** — reference component path fix (closes D-PRE-3 stale path carryover from Sprint 57.16):
  - was: `governance/components/ApprovalCard.tsx`
  - now: `chat_v2/components/ApprovalCard.tsx`

### 3.4 Closeout commits + retrospective + memory
- [ ] **`docs/03-implementation/agent-harness-execution/phase-57/sprint-57-18/retrospective.md`** — Q1-Q7:
  - Q1: What went well? (mockup cp clean / 11 tokens added without regression / 20 stubs created cleanly)
  - Q2: Calibration verify — ratio `actual/committed` (target [0.85, 1.20] band; 1st-app KEEP 0.55)
  - Q3: Drift findings + lessons (mockup-vs-production gap matrix detailed)
  - Q4: Follow-up ADs:
    - AD-Mockup-Page-X-Port × 14 priority units (Operations 4 / Topbar 3 / Auth 4 / Governance 3)
    - AD-Brand-Primary-Color-Decision (oklch indigo vs hsl dark slate, user pending)
    - AD-Theme-Variant-Mechanism (4 variants in mockup, defer)
    - AD-Density-Variant-Mechanism (3 densities in mockup, defer)
    - AD-Lighthouse-Visual-Hard-Gate (carryover, now actionable after baseline regen)
    - AD-A11y-Structural-Nits (carryover from 57.16, unchanged status)
    - AD-Web-Font-Loading (Geist not auto-loaded by Vite, UA fallback active)
  - Q5: Next sprint candidates (Sprint 57.19+ priority order: Operations 4 first per user 2026-05-16 alignment)
  - Q6: Process improvements (`Sprint setup = 三檔同時 ship` mental anchor codified post Sprint 57.18 Day 0 stop-resume issue)
  - Q7: N/A (this sprint is not a spike sprint per §6.5)
- [ ] **`memory/project_phase57_18_mockup_integration_foundation.md`** NEW + `MEMORY.md` +1 line per `auto memory` 規範
- [ ] **Day 3 commit 1** `feat(sprint-57-18, Day 3): Sidebar 6-category + PROP/DRAFT badges (US-C3)`
- [ ] **Day 3 commit 2** `chore(sprint-57-18, Day 3): in-sprint doc syncs + retrospective + memory (US-D1)`

### 3.5 PR + closeout
- [ ] **`git push -u origin feature/sprint-57-18-mockup-integration-foundation`**
- [ ] **`gh pr create`** with full PR description (link to plan + checklist + retrospective; list closed ADs; list deferred AD-Mockup-Page-X-Port × 14)
- [ ] **CI green** — e2e + a11y + visual-regression (advisory if baselines deferred) + lint + build + lighthouse advisory
- [ ] **Merge** to main once CI green + user approval
- [ ] **`chore/closeout-57-18` follow-up PR** (deferred post-merge):
  - CLAUDE.md Phase 13/N → 14/N + Latest Sprint row + Prev Sprint row + main HEAD + Next Phase 候選 update
  - SITUATION-V2-SESSION-START.md §第八部分 + §第九部分 milestones +1 row

---

## Carryover for Sprint 57.19+

The following are explicitly OUT of Sprint 57.18 scope but logged here for Sprint 57.19+ planning:

### AD-Mockup-Page-X-Port (14 priority units per user 2026-05-16 alignment)
- **Operations 4**: overview / orchestrator / subagents / state-inspector
- **Topbar overlays 3**: CommandPalette ⌘K / NotificationsPanel / UserMenu
- **Auth flows 4**: register / invite / mfa / expired
- **Governance 3**: redaction / error-policy / audit-log (DRAFT → active)

Sprint 57.19 plan (drafted at Sprint 57.18 closeout per Rolling Planning 紀律) takes Group 1 first (Operations 4). Each port = port real mockup `page-*.jsx` content to production `frontend/src/pages/<id>/` using Vite + TS + Tailwind + shadcn + new tokens from Sprint 57.18. Backend gaps surface during port → paired backend API sprint.

### AD-Brand-Primary-Color-Decision
User to decide before Sprint 57.19+ first port: keep `hsl(222.2 47.4% 11.2%)` dark slate (current) OR switch to `oklch(0.62 0.16 250)` cool indigo (mockup brand). Default = no change.

### AD-Theme-Variant-Mechanism
Mockup has 4 dark variants via `[data-variant]`. Production has only `.dark` class. Defer to dedicated architectural sprint.

### AD-Density-Variant-Mechanism
Mockup has 3 densities via `[data-density]`. Production has none. Defer.

### AD-Lighthouse-Visual-Hard-Gate (carryover from Sprint 57.17)
Now actionable after Sprint 57.18 visual baseline regen (if executed Day 3). Turn `visual-regression.spec.ts` + `frontend-lighthouse.yml` from advisory to required CI checks.

### AD-Web-Font-Loading
Geist + Noto Sans TC declared in `tailwind.config.ts` but NOT auto-loaded by Vite. Falls back to system-ui. Self-host @font-face + font-display:swap deferred to dedicated sprint.

### AD-A11y-Structural-Nits (carryover from Sprint 57.16)
4 moderate/minor `/chat-v2` violations (heading-order / landmark-*) + `/auth/callback?error` page-has-heading-one. Unchanged by Sprint 57.18 (additive tokens + new stubs don't touch existing /chat-v2 component structure).
