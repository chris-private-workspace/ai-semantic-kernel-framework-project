---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-18-plan.md
Purpose: Sprint 57.18 plan — AD-Design-Mockup-Integration-Foundation (Phase 1 of multi-sprint mockup integration epic). Integrate the `reference/design-mockups/` 32-sidebar-route + 7-auth + 3-topbar-overlay design prototype into production as long-term design reference + sync 11 missing semantic design tokens (success/warning/danger/thinking/tool/memory/info + 4 risk levels) from mockup styles.css to production `tailwind.config.ts` + `index.css` (closes AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token-Audit dual-AD) + add 20 PROP/DRAFT stub route entries to `routes.config.ts` + expand `RouteCategory` enum from 3 → 6 categories (business/governance/observability/resources NEW) + refactor `Sidebar.tsx` to render PROP/DRAFT badge visual + 6-category headers per `reference/design-mockups/shell.jsx` ROUTES — scaffold complete for Sprint 57.19+ rolling port of priority UI units (Operations 4 + Topbar overlays 3 + Auth flows 4 + Governance 3 = 14 units per user 2026-05-16 alignment). Strategy C staged approach: this sprint = bones; Sprint 57.19+ = flesh.
Category: Frontend / design-system / routing-scaffolding
Scope: Phase 57 / Sprint 57.18

Description:
    Sprint 57.17 closeout (2026-05-15) restored Tailwind v4 utility CSS emission
    via 1-line `@import "tailwindcss"; @config "../tailwind.config.ts";` fix.
    Pages now render with shadcn slate base + AppShellV2 layout. Sprint 57.17
    discovery surfaced 2 known token-coverage gaps as carryover ADs:

    - **AD-Style-Token-Config-Audit** (NEW Sprint 57.16 D-PRE-4): `STYLE.md §2`
      documents `success`/`warning`/`danger`/`card`/`accent`/`thinking`/`tool`/
      `memory` tokens NOT defined in `tailwind.config.ts` + `src/index.css`.
      Sprint 57.15+57.16 use `bg-success` / `bg-warning` / `bg-danger` etc. =
      Tailwind silently ignores unknown classes → likely no-op CSS at runtime.
      Sprint 57.16 strategically used only verified shadcn tokens for the
      `/chat-v2` color-contrast critical path, did NOT extend the config.
    - **AD-Post-Hotfix-Token-Audit** (NEW Sprint 57.17): after the Tailwind v4
      fix, `text-muted-foreground` on `bg-muted` measured 3.89:1 sub-AA (vs
      57.16 MHist 4.6:1 theoretical claim that was never rendered). Cascade
      surfaced 2nd sub-AA pair `text-red-500 #ef4444` on white = 3.76:1 +
      borderline `text-muted-foreground` on white = 4.43:1. Sprint 57.17
      re-added `disableRules(["color-contrast"])` to a11y-scan as broader
      shadcn slate audit deferred.

    Concurrent 2026-05-16 user discovery: `reference/design-mockups/` directory
    contains a complete hi-fi React + Babel prototype (24 files, no build step)
    with **32 sidebar routes across 6 categories** + 7 auth flows (independent
    AuthShell) + 3 topbar overlays (CommandPalette ⌘K + NotificationsPanel +
    UserMenu). The prototype was authored to align 1:1 with V2 12-範疇 spec:
    11 routes match `frontend/src/routes.config.ts` (V2 Ship), 17 are PROP
    (V2 backend ABC exists but frontend not shipped), 4 are DRAFT (in
    routes.config.ts but `active=false`). DESIGN_RATIONALE.md (192 lines)
    documents every menu entry's rationale + 12-範疇 mapping.

    The prototype establishes a token vocabulary missing from production:

    | Token category | Mockup (target) | Production (current) | Gap |
    |---|---|---|---|
    | Semantic | 8 (success/warning/danger/thinking/tool/memory/info + brand-primary as oklch indigo) | 6 shadcn (background/foreground/primary slate/secondary/destructive/muted) | **🔴 +7** |
    | Risk severity | 4 levels (low/medium/high/critical) | 0 explicit | **🔴 +4** |
    | Font family | "Geist" + "Noto Sans TC" | UA fallback (none set) | ⚠️ inconsistent |
    | Theme variants | 4 (linear/strict/refined/shadcn) | 1 (light/dark only) | ⚠️ deferred AD-Theme-Variant |
    | Density | 3 (compact/normal/comfortable) | 1 | ⚠️ deferred AD-Density-Variant |

    And a 32-route structure missing from production:

    | Mockup category | Mockup count | Production current | Stub to add |
    |---|---|---|---|
    | operations | 10 (overview/chat-v2/orchestrator/subagents/loop-debug/memory/state-inspector/compaction/jit-retrieval/subagent-tree) | 3 (chat-v2/cost-dashboard/sla-dashboard) | **+7** (move cost+sla → observability; move loop-debug+memory → operations from admin) |
    | business | 1 (incidents) | 0 | **+1** |
    | governance | 5 (governance/audit-log/verification/redaction/error-policy) | 3 (governance/audit-log/verification) all in admin | **+2** (move 3 → governance) |
    | observability | 5 (sla-dashboard/cost-dashboard/cache-manager/sse/devui) | 0 explicit | **+3** (move cost+sla → here) |
    | resources | 3 (models/tools/feature-flags) | 1 (feature-flags) in admin | **+2** (move feature-flags → resources) |
    | admin | 7 (admin-tenants/tenant-onboarding/tenant-settings/pricing/rbac/profile/mfa) | 4 (admin-tenants/tenant-settings in admin; profile+mfa in settings) | **+3** (move profile+mfa → admin) |

    **Total: 20 NEW stub route entries + 13 existing entries re-categorized + 3
    NEW categories (business/governance/observability/resources).**

    This sprint executes Phase 1 of the staged "Strategy C" integration plan
    chosen by user 2026-05-16: scaffold (bones) now, Sprint 57.19+ rolling
    port real content (flesh) per priority order:

    - Operations core 4: overview / orchestrator / subagents / state-inspector
    - Topbar overlays: CommandPalette ⌘K / NotificationsPanel / UserMenu
    - Auth flows補完: register / invite / mfa / expired
    - Governance補完: redaction / error-policy / audit-log (DRAFT→active)

    This sprint:

    A. **Mockup as design reference** (US-A1): `cp -r reference/design-mockups/
       design/operator-portal/` (preserve `reference/` for future iterations,
       NOT mv). Add INTEGRATION-LOG.md to track which pages have been ported.
       Append README.md cross-ref pointing to `frontend/src/routes.config.ts`
       + 11+1 範疇 spec.

    B. **Design token sync** (US-B1 + US-B2): Add 11 missing semantic tokens
       (success/warning/danger/thinking/tool/memory/info + 4 risk levels) to
       `tailwind.config.ts` `theme.extend.colors` as shadcn-style CSS-var
       bridges (`hsl(var(--success))` etc.). Add corresponding `--success` /
       `--warning` / ... `--risk-critical` HSL values to `index.css` `:root`
       + `.dark`. Add Geist + Noto Sans TC font-family. Closes AD-Style-Token-
       Config-Audit + AD-Post-Hotfix-Token-Audit (token coverage portion;
       contrast-ratio re-evaluation in follow-up sprint per AppShellV2 actual
       usage).

    C. **Routes stub scaffolding** (US-C1 + US-C2 + US-C3): Expand
       `RouteCategory` enum from 3 → 6 (`operations` | `business` |
       `governance` | `observability` | `resources` | `admin`). Add `proposed?:
       boolean` + `designed?: boolean` optional fields to `RouteEntry`. Add
       20 NEW stub entries with appropriate flags. Re-categorize 13 existing
       entries per mockup `shell.jsx` CATEGORY_ORDER. Create
       `ComingSoonPlaceholder.tsx` universal stub page rendering route ID +
       cross-link to mockup `design/operator-portal/page-X.jsx`. Create 20
       thin wrapper `pages/<id>/index.tsx` files (1-line each). Refactor
       `Sidebar.tsx` to render PROP (blue thinking-token) + DRAFT (yellow
       warning-token) badges, 6 category headers per CATEGORY_ORDER, optional
       "N PROP" count per category header. Existing test specs (chat-v2,
       governance, cost-dashboard, etc.) use `getByRole` / `getByText` so
       sidebar re-categorization should NOT break — verify in Day 3.

    D. **Closeout** (US-D1): retrospective Q1-Q7 + memory snapshot + 4
       in-sprint doc syncs (16-frontend-design.md timeline / sprint-workflow.md
       calibration NEW class `mockup-integration-foundation` 0.55 1st app /
       STYLE.md §2 update token reality table / CONVENTION.md §3 ApprovalCard
       reference path fix per D-PRE-3 carryover) + PR + 2 deferred post-merge
       syncs (CLAUDE.md / SITUATION-V2-SESSION-START.md).

    Deferred OUT of this sprint (explicitly):

    - **AD-Mockup-Page-X-Port** (NEW, multi-sprint): Sprint 57.19+ port of
      real mockup page content (Operations 4 + Topbar overlays 3 + Auth 4 +
      Governance 3 = 14 priority units per user alignment). Each port = 1
      sprint of ~2-3 units. Backend gaps surface during port and get logged
      as AD-Backend-Gap-N → backend-paired follow-up sprints.
    - **AD-Brand-Primary-Color-Decision**: mockup uses `oklch(0.62 0.16 250)`
      cool indigo; production current `hsl(222.2 47.4% 11.2%)` dark slate.
      Open question for user (not blocking this sprint). Logged in §Open
      Questions.
    - **AD-Theme-Variant-Mechanism**: mockup has 4 dark variants (linear /
      strict / refined / shadcn) + matching light variants via
      `[data-variant="..."]` attribute. Production has only `.dark` class.
      Architectural decision deferred — not needed for this sprint's
      scaffolding scope.
    - **AD-Density-Variant-Mechanism**: mockup has 3 densities (compact /
      normal / comfortable) via `[data-density]`. Production no equivalent.
      Same architectural decision deferral.
    - **AD-Lighthouse-Visual-Hard-Gate** (carryover from Sprint 57.17): turn
      `visual-regression.spec.ts` from advisory to required CI gate. This
      sprint will likely trigger 6/6 baseline FAIL (sidebar 6-category
      refactor changes layout) → opportunity to regenerate baselines via
      57.14 workflow_dispatch pattern + then promote AD-Lighthouse-Visual-
      Hard-Gate. Action deferred to Sprint 57.19+.
    - **AD-CI-7-GHA-PR-Permission** (carryover from Sprint 57.17): GitHub
      Actions cannot auto-create PRs without elevated permissions; manual
      `gh pr create` workaround. Infrastructure track, no sprint binding.
    - **AD-A11y-Structural-Nits** (carryover from Sprint 57.16): `/chat-v2`
      `heading-order` / `landmark-*` moderate/minor violations + `/auth/
      callback?error` `page-has-heading-one`. Not affected by this sprint's
      additive token + stub-route changes. Continues as Phase 57.19+
      candidate.

## Sprint Goal

Phase 57+ Frontend SaaS 14/N opens — integrate `reference/design-mockups/` 32-sidebar-route + 7-auth + 3-topbar-overlay design prototype as production design reference (cp to `design/operator-portal/`) + sync 11 missing semantic design tokens (success/warning/danger/thinking/tool/memory/info + 4 risk levels) into `tailwind.config.ts` + `index.css` (closes AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token-Audit token-coverage portion) + add 20 PROP/DRAFT stub route entries to `routes.config.ts` + expand `RouteCategory` enum from 3 → 6 categories (business/governance/observability/resources NEW) + refactor `Sidebar.tsx` to render PROP/DRAFT badges + 6-category headers per mockup `shell.jsx` CATEGORY_ORDER + create `ComingSoonPlaceholder.tsx` universal stub component + 20 thin wrapper page files. Phase 1 of multi-sprint mockup integration epic — scaffold complete (bones), Sprint 57.19+ port priority units (flesh).

## Background

### 為什麼這個 sprint 存在（用戶 2026-05-16 直接指示）

User 2026-05-16 statement: "現在我們可以先把 `reference\design-mockups` 的內容先進行實作，因為之前即使把項目的規劃內容都準備了大部分，但是前端的部分其實一直都沒有規劃好，而且也不太能夠表達項目所實現了的功能流程，現在可以完整地去運用這些 mockup 內容，把這些前端的部分都完整地準備出來，之後再逐一把裡面的 UIUX 流程對應到不同的後端功能部分，當然如果發現是現在的後端功能還不支援，就會思考和規劃如何能夠讓它們能被實現，這就是我們接下來要最高優先去執行的工作".

Strategy alignment session via AskUserQuestion 2026-05-16:
- **Q1 整體策略**: 用戶選 C 階段式 (NOT B 全 port / NOT A 純 ref / NOT D 只 tokens)
- **Q2 第一輪 port 優先序**: 全部 4 組都選 = 14 個單元 (Operations 4 + Topbar 3 + Auth 4 + Governance 3)
- **Q3 後端 gap 處理**: 前後端同 sprint (每個 Sprint 57.19+ 同時補後端 API + frontend page)

This sprint = Phase 1 only. Phase 2 (Sprint 57.19+) = rolling port real content.

### 為什麼這個 sprint *不* 在 Phase 57.17+ 候選 list（突發 user-driven scope）

CLAUDE.md Phase 57.17+ 候選 row lists 8 alternatives: AD-Lighthouse-Visual-Hard-Gate / IAM Block B / Bundle-Size / Tier 1 IaC + DR drill / SOC 2 + SBOM / i18n Feature Namespaces / AD-Style-Token-Config-Audit / AD-A11y-Structural-Nits. **This sprint preempts 1 of those 8 directly (AD-Style-Token-Config-Audit) + folds in AD-Post-Hotfix-Token-Audit (57.17 carryover) + opens a multi-sprint mockup integration epic that was not in the candidate list at all**. User's 2026-05-16 direct指示 promoted it to top priority over the prior 8 candidates.

Post-merge: CLAUDE.md Phase 57.18+ 候選 row should re-promote AD-Lighthouse-Visual-Hard-Gate (now actionable after this sprint's baseline regen if triggered) + IAM Block B + Bundle-Size + AD-A11y-Structural-Nits.

### 17.md / V2 紀律對齊

- **Cat 12 Observability**: token additions don't affect runtime telemetry. Sidebar refactor may marginally change LCP/CLS measured by `reportWebVitals()` (sidebar render path more complex with 6 categories + badges) — observe but don't gate.
- **Frontend Foundation 1/N (Sprint 57.13) + Tailwind v4 hotfix (Sprint 57.17)**: foundation now stands on working CSS engine + correct token resolution. This sprint extends foundation's token vocabulary; future ports build on it.
- **Sprint 57.5 Reality Check methodology**: dual scoring — code-level (token additions / lint / build / e2e green) vs runtime-level (manual browser inspection of new sidebar 6-category layout + 20 stub routes + ComingSoonPlaceholder render). Day 3 verify via Playwright MCP screenshot of `/chat-v2` (existing) + 3 new stubs (e.g. `/overview`, `/orchestrator`, `/subagents`).
- **Rolling Planning 紀律**: NOT pre-writing Sprint 57.19+ plan/checklist — only logging priority order in retrospective Q5. Sprint 57.19 plan drafted at Sprint 57.18 closeout, NOT now.
- **§AGENTS.md mockup守則對齊**: mockup's 3-状態 (active / proposed / designed) maps to production `RouteEntry` interface fields. `cp` preserves mockup as authoritative design source; production routes.config.ts becomes consumer.

## User Stories

### Group A — Mockup as Design Reference (US-A1)

- **US-A1**: As a maintainer, I want `reference/design-mockups/` integrated into project as `design/operator-portal/` so stakeholders + future AI assistants can visually see the design vocabulary without spinning up production frontend.
  - AC1: `cp -r reference/design-mockups/ design/operator-portal/` — preserve `reference/` directory (NOT `mv`)
  - AC2: `design/operator-portal/INTEGRATION-LOG.md` NEW file — tracks which mockup pages have been ported to production (`frontend/src/pages/<id>/`) with date + sprint reference
  - AC3: `design/operator-portal/README.md` append a "Production integration cross-ref" section pointing to `frontend/src/routes.config.ts` + `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md`
  - AC4: 1-line dev server script note in INTEGRATION-LOG.md: `cd design/operator-portal && python -m http.server 8080 && open http://localhost:8080`
  - AC5: `git add -A design/` → verify 24+ files staged (mockup directory full)
  - AC6: `design/operator-portal/AGENTS.md` (already exists from cp) — verify intact, NOT modified this sprint (it's the authoritative mockup dev守則 for prototype-only edits)

### Group B — Design Token Sync (US-B1 + US-B2)

- **US-B1**: As a developer, I want `tailwind.config.ts` to declare 11 missing semantic tokens + 4 risk levels + Geist font family so Tailwind utility classes (`bg-success` / `text-thinking` / `border-risk-critical` etc.) actually emit CSS.
  - AC1: `theme.extend.colors` gains 7 new top-level entries: `success` / `warning` / `danger` / `thinking` / `tool` / `memory` / `info` — each `{ DEFAULT: "hsl(var(--<token>))", foreground: "hsl(var(--<token>-foreground))" }`
  - AC2: `theme.extend.colors.risk` nested object with 4 sub-keys: `low` / `medium` / `high` / `critical` — each `"hsl(var(--risk-<level>))"`
  - AC3: `theme.extend.fontFamily.sans` = `['"Geist"', '"Noto Sans TC"', "ui-sans-serif", "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"]`
  - AC4: `theme.extend.fontFamily.mono` = `['"Geist Mono"', "ui-monospace", '"JetBrains Mono"', "Menlo", "monospace"]`
  - AC5: existing 6 shadcn token entries (border/input/ring/background/foreground/primary/secondary/destructive/muted) preserved unchanged
  - AC6: MHist +1 line per `.claude/rules/file-header-convention.md` budget (≤ 100 chars)

- **US-B2**: As a developer, I want `frontend/src/index.css` `:root` + `.dark` to declare 12 corresponding CSS variables (7 semantic + 7 -foreground + 4 risk) so the `hsl(var(--<token>))` bridges in tailwind.config.ts actually resolve.
  - AC1: `:root` (light) adds 14 vars: `--success` / `--success-foreground` / `--warning` / `--warning-foreground` / `--danger` / `--danger-foreground` / `--thinking` / `--thinking-foreground` / `--tool` / `--tool-foreground` / `--memory` / `--memory-foreground` / `--info` / `--info-foreground` + 4 `--risk-{low,medium,high,critical}`
  - AC2: `.dark` (dark) adds same 18 vars with darkened HSL values (slight desaturation + lightness shift per shadcn slate pattern)
  - AC3: HSL values approximated from mockup `styles.css` oklch values (e.g. `--success: oklch(0.72 0.16 155)` → `150 60% 45%` light / `150 50% 55%` dark)
  - AC4: existing 13 shadcn CSS vars unchanged
  - AC5: closes **AD-Style-Token-Config-Audit** (57.16 D-PRE-4) — STYLE.md §2 token table now matches reality
  - AC6: closes **AD-Post-Hotfix-Token-Audit** token-coverage portion only (contrast-ratio audit of existing components using these new tokens deferred to Sprint 57.19+ when first port consumes them)
  - AC7: e2e visual baselines unchanged in this US (additive tokens only, no existing component changes their colors) — sidebar refactor in US-C3 is what triggers baseline regen

### Group C — Routes Stub Scaffolding (US-C1 + US-C2 + US-C3)

- **US-C1**: As a developer, I want `routes.config.ts` to declare 33 entries (13 existing re-categorized + 20 NEW stub) across 6 categories so `Sidebar.tsx` renders complete navigation matching mockup `shell.jsx`.
  - AC1: `RouteCategory` type expanded: `"operations" | "business" | "governance" | "observability" | "resources" | "admin"` (was `"operations" | "admin" | "settings"`)
  - AC2: `RouteEntry` interface adds 2 optional fields: `proposed?: boolean` (V2 backend ABC exists, frontend pending) + `designed?: boolean` (V2 routes.config.ts has active=false, this sprint preserves designed=true flag)
  - AC3: 13 existing entries re-categorized:
    | id | Was | Now | Active change? |
    |---|---|---|---|
    | chat-v2 | operations | operations | no |
    | cost-dashboard | operations | observability | no |
    | sla-dashboard | operations | observability | no |
    | admin-tenants | admin | admin | no |
    | tenant-settings | admin | admin | no |
    | audit-log | admin (active=false) | governance (active=false, designed=true) | no (still active=false this sprint) |
    | feature-flags | admin (active=false) | resources (active=false, designed=true) | no |
    | governance | admin | governance | no |
    | verification | admin | governance | no |
    | loop-debug | admin | operations | no |
    | memory | admin | operations | no |
    | profile | settings (active=false) | admin (active=false) | no |
    | mfa | settings (active=false) | admin (active=false) | no |
  - AC4: 20 NEW stub entries added, all `active: true` + `proposed: true` (PROP) or `designed: true` (DRAFT) per AGENTS.md §5 三-狀態 conventions:
    | Category | NEW entries | Mockup file |
    |---|---|---|
    | operations | overview / orchestrator / subagents / state-inspector / compaction / jit-retrieval / subagent-tree | page-overview.jsx / page-agents.jsx |
    | business | incidents | page-extras.jsx |
    | governance | redaction / error-policy | page-governance.jsx / page-platform.jsx |
    | observability | cache-manager / sse / devui | page-models.jsx / page-sse.jsx / page-platform2.jsx |
    | resources | models / tools | page-models.jsx / page-tools.jsx |
    | admin | tenant-onboarding / pricing / rbac | page-platform2.jsx / page-admin.jsx |
  - AC5: each NEW entry has `component: lazy(() => import("./pages/<id>"))` pointing to thin wrapper (per US-C2)
  - AC6: each NEW entry has `nameKey: "nav.<camelCaseId>"` matching `frontend/src/i18n/locales/en/common.json` keys (verify i18n keys exist or add in this US)
  - AC7: file-header docstring + MHist +1 line + Modification History entry

- **US-C2**: As a developer, I want a universal `ComingSoonPlaceholder.tsx` component + 20 thin wrapper pages so stub routes have minimal but informative content (page title + mockup cross-link).
  - AC1: NEW `frontend/src/components/ComingSoonPlaceholder.tsx` (~60 lines) — renders:
    - `<h1>` route name + lucide icon (passed via routeId lookup from `routes.config.ts`)
    - "Coming Soon — Designed in `design/operator-portal/page-<X>.jsx`" muted text
    - Sprint 57.19+ priority badge if route is in user's priority list (overview/orchestrator/subagents/state-inspector/redaction/error-policy/audit-log)
    - Cross-link button: "Open mockup at http://localhost:8080/#/<id>" (dev-only via `import.meta.env.DEV`)
  - AC2: 20 NEW `frontend/src/pages/<id>/index.tsx` thin wrappers — each 1 line: `export { default } from "../../components/ComingSoonPlaceholder";` (component reads route via React Router `useLocation()` + matches against ROUTES)
  - AC3: alternative pattern if 1-line wrapper too thin for lazy() type inference: `export default function StubPage() { return <ComingSoonPlaceholder /> }`
  - AC4: tsc strict 0 errors after creation
  - AC5: bundle size impact: ~1 KB per wrapper (lazy-chunked) — verify in Day 3 build

- **US-C3**: As a developer, I want `Sidebar.tsx` refactored to render PROP/DRAFT badges + 6-category headers + optional "N PROP" count per category header, per mockup `shell.jsx` Sidebar pattern.
  - AC1: 6 category headers rendered in order: Operations → Business → Governance → Observability → Resources → Admin (per `CATEGORY_ORDER` constant)
  - AC2: each category header shows category-name + optional PROP count badge if >0 (e.g. "Operations · 7 PROP")
  - AC3: per-entry badge rendering:
    - `proposed: true` (PROP) → blue badge with `bg-thinking/16 text-thinking` styling (`thinking` token from US-B1)
    - `designed: true, active: false` (DRAFT) → yellow badge with `bg-warning/16 text-warning` styling
    - `active: false` only (no designed flag) → grayed link + "Coming soon" tooltip (preserve existing behavior)
    - default (V2 Ship, active: true, no proposed) → normal link
  - AC4: aria-label / role conformance preserved — `<nav role="navigation" aria-label="Primary">` + `<a>` links semantic structure unchanged from current `Sidebar.tsx`
  - AC5: test specs using `getByRole('link', { name: '...' })` / `getByText(...)` should NOT break — verify in Day 3 by running full e2e suite
  - AC6: visual-regression baselines for `app-shell.png` will likely fail (new sidebar layout) — expected; regenerate in closeout or defer to Sprint 57.19+
  - AC7: MHist +1 line

### Group D — Closeout (US-D1)

- **US-D1**: As a maintainer, I want full closeout discipline (retrospective + memory + in-sprint doc syncs + PR + deferred post-merge syncs).
  - AC1: `retrospective.md` Q1-Q7 with Q3 detailed mockup-vs-production gap matrix + Q4 listing follow-up ADs (AD-Mockup-Page-X-Port × N priority units, AD-Brand-Primary-Color-Decision, AD-Theme-Variant-Mechanism, AD-Density-Variant-Mechanism, AD-Lighthouse-Visual-Hard-Gate)
  - AC2: `memory/project_phase57_18_mockup_integration_foundation.md` + `MEMORY.md` index +1 line (per `auto memory` 規範)
  - AC3: in-sprint doc syncs:
    - `docs/03-implementation/agent-harness-planning/16-frontend-design.md` Sprint Timeline +1 row (57.18)
    - `.claude/rules/sprint-workflow.md` Calibration Matrix +1 row (NEW class `mockup-integration-foundation` 0.55 1st app)
    - `frontend/STYLE.md §2` token reality table update — new tokens registered (closes D-PRE-4)
    - `frontend/CONVENTION.md §3` reference component path fix (closes D-PRE-3 stale path carryover from Sprint 57.16)
  - AC4: deferred post-merge doc syncs (via `chore/closeout-57-18` follow-up PR):
    - `CLAUDE.md` (Phase 13/N → 14/N + Latest Sprint row + Prev Sprint row + main HEAD + Next Phase 候選 update)
    - `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` (§第八部分 carryover update + §第九部分 milestones +1 row 57.18)
  - AC5: PR open + CI green (e2e + a11y + visual baseline regen if triggered + lint + build + lighthouse advisory) + merge → followup chore PR

## Technical Specifications

### Mockup token vocabulary → production HSL mapping (US-B2)

Mockup `styles.css :root` uses oklch (variant-aware via `[data-theme][data-variant]`). Production `index.css` uses HSL with simple `.dark` class. Strategy: extract DEFAULT (no variant) oklch values + convert to HSL approximations, drop variant mechanism (defer to AD-Theme-Variant-Mechanism).

Conversion table (mockup oklch → light HSL → dark HSL):

| Token | Mockup oklch | Light HSL | Dark HSL |
|---|---|---|---|
| success | oklch(0.72 0.16 155) | 150 60% 45% | 150 50% 55% |
| success-foreground | (derived white) | 0 0% 100% | 0 0% 100% |
| warning | oklch(0.78 0.16 75) | 38 92% 50% | 38 80% 60% |
| warning-foreground | (derived black) | 0 0% 10% | 0 0% 10% |
| danger | oklch(0.65 0.21 25) | 0 84% 60% | 0 70% 55% |
| danger-foreground | (derived white) | 0 0% 100% | 0 0% 100% |
| thinking | oklch(0.65 0.20 295) | 270 75% 60% | 270 65% 65% |
| thinking-foreground | (derived white) | 0 0% 100% | 0 0% 100% |
| tool | oklch(0.72 0.13 210) | 188 70% 50% | 188 60% 55% |
| tool-foreground | (derived white) | 0 0% 100% | 0 0% 100% |
| memory | oklch(0.68 0.20 350) | 326 80% 60% | 326 70% 65% |
| memory-foreground | (derived white) | 0 0% 100% | 0 0% 100% |
| info | oklch(0.68 0.15 240) | 217 91% 60% | 217 80% 65% |
| info-foreground | (derived white) | 0 0% 100% | 0 0% 100% |
| risk-low | (= success) | 150 60% 45% | 150 50% 55% |
| risk-medium | (= warning) | 38 92% 50% | 38 80% 60% |
| risk-high | oklch(0.65 0.20 40) | 20 90% 55% | 20 80% 60% |
| risk-critical | oklch(0.55 0.22 25) #B71C1C | 0 70% 40% | 0 60% 50% |

Conversion methodology: take oklch L (lightness 0-1) × 100 to get HSL L%, take hue rotation from oklch hue (0-360), approximate chroma via heuristic (high chroma → high saturation %). Cross-verify with hex literal where mockup comments specify (e.g. `#10B981 verified, approved` for success).

### tailwind.config.ts theme.extend.colors structure (US-B1)

```typescript
colors: {
  // Existing 6 shadcn tokens — unchanged
  border: "hsl(var(--border))",
  input: "hsl(var(--input))",
  ring: "hsl(var(--ring))",
  background: "hsl(var(--background))",
  foreground: "hsl(var(--foreground))",
  primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
  secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
  destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
  muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },

  // NEW Sprint 57.18 — mockup semantic tokens
  success: { DEFAULT: "hsl(var(--success))", foreground: "hsl(var(--success-foreground))" },
  warning: { DEFAULT: "hsl(var(--warning))", foreground: "hsl(var(--warning-foreground))" },
  danger: { DEFAULT: "hsl(var(--danger))", foreground: "hsl(var(--danger-foreground))" },
  thinking: { DEFAULT: "hsl(var(--thinking))", foreground: "hsl(var(--thinking-foreground))" },
  tool: { DEFAULT: "hsl(var(--tool))", foreground: "hsl(var(--tool-foreground))" },
  memory: { DEFAULT: "hsl(var(--memory))", foreground: "hsl(var(--memory-foreground))" },
  info: { DEFAULT: "hsl(var(--info))", foreground: "hsl(var(--info-foreground))" },

  // NEW Sprint 57.18 — mockup risk severity tokens (flat sub-keys)
  risk: {
    low: "hsl(var(--risk-low))",
    medium: "hsl(var(--risk-medium))",
    high: "hsl(var(--risk-high))",
    critical: "hsl(var(--risk-critical))",
  },
},
```

### routes.config.ts 6-category structure (US-C1)

```typescript
export type RouteCategory =
  | "operations"     // daily operator workflow — agent/loop/memory/state
  | "business"       // IPA 5 domains — incidents (patrol/correlation/RCA/audit/incident sub-domains)
  | "governance"     // HITL + audit + verification + safety guardrails
  | "observability"  // Cat 12 dashboards — cost/SLA + cache/SSE/devui
  | "resources"      // platform resources — models/tools/flags
  | "admin";         // tenant + identity + pricing — admin-tenants/onboarding/settings/pricing/rbac/profile/mfa

export const CATEGORY_ORDER: RouteCategory[] = [
  "operations",
  "business",
  "governance",
  "observability",
  "resources",
  "admin",
];

export interface RouteEntry {
  name: string;
  nameKey: string;
  path: string;
  icon: LucideIcon;
  category: RouteCategory;
  active: boolean;
  proposed?: boolean;   // V2 backend ABC exists, frontend not yet ported (PROP badge)
  designed?: boolean;   // V2 routes.config.ts has active=false (DRAFT badge)
  component?: LazyExoticComponent<ComponentType<unknown>>;
}
```

### Sidebar.tsx badge rendering (US-C3)

Use `cn()` utility from `@/lib/utils` for class composition. Badge styling reference:

```tsx
// Inside Sidebar entry rendering:
{entry.proposed && (
  <span className="ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium uppercase bg-thinking/16 text-thinking">
    PROP
  </span>
)}
{entry.designed && !entry.active && (
  <span className="ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium uppercase bg-warning/16 text-warning">
    DRAFT
  </span>
)}
{!entry.active && !entry.designed && (
  <span className="ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium uppercase bg-muted/40 text-muted-foreground">
    SOON
  </span>
)}

// Category header:
{CATEGORY_ORDER.map(category => {
  const entries = ROUTES.filter(r => r.category === category);
  if (entries.length === 0) return null;
  const propCount = entries.filter(r => r.proposed).length;
  return (
    <div key={category} className="px-3 py-2 text-[10px] uppercase tracking-wide text-muted-foreground flex items-center justify-between">
      <span>{t(`nav.category.${category}`)}</span>
      {propCount > 0 && (
        <span className="rounded bg-thinking/16 px-1.5 py-0.5 text-[9px] text-thinking">
          {propCount} PROP
        </span>
      )}
    </div>
  );
})}
```

### Calibration class

NEW scope class: **`mockup-integration-foundation`** — multi-domain frontend scaffolding sprint (design ref cp + tailwind tokens + routes refactor + sidebar refactor + stub pages). HYBRID weighted blend:

- design ref (mockup cp + READMEs): 0.40 audit-cycle (mostly mechanical) ~15% weight
- tailwind tokens + index.css HSL conversion: 0.55 medium-frontend ~20% weight
- routes.config.ts 20 stubs + 6 categories + 13 re-categorize: 0.50 frontend-refactor-mechanical ~25% weight
- ComingSoonPlaceholder + 20 wrapper pages: 0.50 frontend-refactor-mechanical ~15% weight
- Sidebar.tsx refactor: 0.65 medium-frontend ~15% weight
- closeout: 0.80 closeout-ceremony ~10% weight

Weighted: (0.40 × 0.15) + (0.55 × 0.20) + (0.50 × 0.25) + (0.50 × 0.15) + (0.65 × 0.15) + (0.80 × 0.10) = 0.06 + 0.11 + 0.125 + 0.075 + 0.0975 + 0.08 = **~0.55 mid-band**.

1st application opens this sprint. KEEP 0.55 per `When to adjust` 3-sprint window rule. Pending 2-3 sprint validation if recurs in future similar mockup-integration sprints.

### Bottom-up estimate per US

| US | Bottom-up | Notes |
|----|-----------|-------|
| US-A1 (mockup → design/) | ~0.5 hr | cp + README append + INTEGRATION-LOG.md create + git add |
| US-B1 (tailwind.config.ts) | ~0.5 hr | 7 semantic + 4 risk + 2 font family + MHist |
| US-B2 (index.css HSL conversion) | ~1 hr | 14 :root vars + 14 .dark vars + oklch→HSL conversion + MHist |
| US-C1 (routes.config.ts 20 stubs + 6 categories + 13 re-categorize) | ~2 hr | structural refactor + 20 new entries × ~3 min each + nameKey i18n alignment + MHist |
| US-C2 (ComingSoonPlaceholder + 20 wrappers) | ~1 hr | 1 component ~60 lines + 20 × 1-line wrappers + lazy import wiring |
| US-C3 (Sidebar.tsx PROP/DRAFT badges + 6 category headers) | ~1.5 hr | badge logic + category iteration + i18n nav.category.X keys + visual review |
| Validation (npm build + e2e + manual screenshot) | ~1 hr | full e2e suite run + manual Playwright MCP screenshot of 3 new stub routes |
| US-D1 (closeout) | ~2 hr | retro + memory + 4 in-sprint doc syncs + PR + smoke CI feedback |

**Bottom-up total: ~9.5 hr**

### Calibrated commit

Bottom-up est ~9.5 hr → calibrated commit **~5 hr** (multiplier 0.55 — NEW class `mockup-integration-foundation` 1st application, mid-band).

Day distribution:
- Day 0: ~1 hr (US-A1 partial + 三-prong + plan/checklist + branch + Day 0 commit)
- Day 1: ~1.5 hr (US-A1 finish + US-B1 + US-B2)
- Day 2: ~1.5 hr (US-C1 + US-C2)
- Day 3: ~1 hr (US-C3 + validation + closeout pre-PR)

## File Change List

### MODIFIED Frontend — src (4 files, ~+330 lines net)

- `frontend/src/index.css` (+30 lines :root + +30 lines .dark = +60 net) — 14 light + 14 dark + 4 risk
- `frontend/tailwind.config.ts` (+30 lines theme.extend.colors + +5 lines fontFamily = +35 net) — 7 semantic + 4 risk + 2 font family
- `frontend/src/routes.config.ts` (+20 entries × ~10 lines + RouteCategory enum expansion = ~+220 net, refactor 13 existing categories) — 33 total entries × 6 categories
- `frontend/src/components/Sidebar.tsx` (+~30 lines badge + category logic) — PROP/DRAFT badge + 6 category iteration

### NEW Frontend — src (21 files)

- `frontend/src/components/ComingSoonPlaceholder.tsx` (~60 lines)
- `frontend/src/pages/overview/index.tsx` (1-line wrapper)
- `frontend/src/pages/orchestrator/index.tsx`
- `frontend/src/pages/subagents/index.tsx`
- `frontend/src/pages/state-inspector/index.tsx`
- `frontend/src/pages/compaction/index.tsx`
- `frontend/src/pages/jit-retrieval/index.tsx`
- `frontend/src/pages/subagent-tree/index.tsx`
- `frontend/src/pages/incidents/index.tsx`
- `frontend/src/pages/redaction/index.tsx`
- `frontend/src/pages/error-policy/index.tsx`
- `frontend/src/pages/cache-manager/index.tsx`
- `frontend/src/pages/sse/index.tsx`
- `frontend/src/pages/devui/index.tsx`
- `frontend/src/pages/models/index.tsx`
- `frontend/src/pages/tools/index.tsx`
- `frontend/src/pages/tenant-onboarding/index.tsx`
- `frontend/src/pages/pricing/index.tsx`
- `frontend/src/pages/rbac/index.tsx`
- `frontend/src/pages/profile/index.tsx`
- `frontend/src/pages/mfa/index.tsx`

### NEW Design reference (24+ files via cp from reference/)

- `design/operator-portal/` (cp -r reference/design-mockups/ → preserves 24 files including AGENTS.md / DESIGN_RATIONALE.md / README.md / *.jsx / styles.css / i18n.jsx / index.html)
- `design/operator-portal/INTEGRATION-LOG.md` (NEW — tracks port progress)
- `design/operator-portal/README.md` (append production cross-ref section)

### MODIFIED i18n (1 file)

- `frontend/src/i18n/locales/en/common.json` — add `nav.<id>` keys for 20 new routes + `nav.category.{operations,business,governance,observability,resources,admin}` keys
- `frontend/src/i18n/locales/zh-TW/common.json` — corresponding 繁中 translations

### NOT touched (intentional scope hold)

- `backend/**` — 0 changes (pure frontend scaffolding; backend gaps surface in Sprint 57.19+ when porting real content)
- `reference/design-mockups/` — preserved (cp not mv; future mockup iterations can update reference/)
- existing `/chat-v2` / `/loop-debug` / `/memory` / `/governance` / etc. page components — token additions are additive, no existing component changes their colors this sprint
- `frontend/postcss.config.cjs` / `vite.config.ts` / `package.json` — unchanged
- e2e specs — verify don't break via Day 3 full e2e run; expected to survive due to `getByRole` / `getByText` selector patterns
- `eslint.config.js` — no-restricted-syntax guard from Sprint 57.15+57.16 still applies (no inline-style regression)
- `AppShellV2.tsx` route generation — unchanged (ROUTES.filter(r => r.active).map(<Route>) pattern preserved)

### Doc syncs (in-sprint)

- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` — Sprint Timeline +1 row (57.18 Mockup Integration Foundation)
- `.claude/rules/sprint-workflow.md` — Calibration matrix +1 row (`mockup-integration-foundation` 0.55 1st app, HYBRID weighted blend documented)
- `frontend/STYLE.md §2` — token reality table update (closes D-PRE-4 carryover; 11 new tokens registered)
- `frontend/CONVENTION.md §3` — reference component path fix (`governance/components/ApprovalCard.tsx` → `chat_v2/components/ApprovalCard.tsx`, closes D-PRE-3 carryover from Sprint 57.16)

### Doc syncs (deferred post-merge via `chore/closeout-57-18` PR)

- `CLAUDE.md` — Phase 13/N → 14/N + Latest Sprint row + Prev Sprint row + main HEAD + Next Phase 候選 update (removes AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token from candidates; adds AD-Mockup-Page-X-Port × 14 priority units + AD-Brand-Primary-Color-Decision + AD-Theme-Variant-Mechanism + AD-Density-Variant-Mechanism)
- `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` — §第八部分 carryover update + §第九部分 milestones +1 row 57.18

## Acceptance Criteria

### Functional

- [ ] `design/operator-portal/` contains 24+ mockup files + `INTEGRATION-LOG.md` + README.md cross-ref
- [ ] `python -m http.server 8080` from `design/operator-portal/` serves index.html with shadcn-styled mockup pages
- [ ] `tailwind.config.ts` contains 11 new semantic tokens + 4 risk levels + 2 font-family arrays
- [ ] `index.css` `:root` + `.dark` contain 18 new HSL CSS vars (14 semantic + 4 risk)
- [ ] `routes.config.ts` contains 33 entries (13 existing + 20 new stub) across 6 categories with `proposed?` + `designed?` flags
- [ ] `RouteCategory` type expanded to 6 values + `CATEGORY_ORDER` constant exported
- [ ] `Sidebar.tsx` renders 6 category headers + PROP (blue) / DRAFT (yellow) / SOON (gray) badges + optional "N PROP" count per category
- [ ] 20 stub pages accessible at their routes + display `ComingSoonPlaceholder` with mockup cross-link
- [ ] `npm run build` succeeds; bundle size delta documented (expected ~+2-5 KB compiled CSS for new tokens + ~+5-10 KB for 20 lazy stubs)
- [ ] `npm run e2e`: 40 pass / 7 skip / 0 fail (sidebar 6-category refactor should NOT break existing test specs using `getByRole` / `getByText`)
- [ ] `npm run lint`: silent (no ESLint warnings or no-restricted-syntax violations)
- [ ] `npm run test` (Vitest): 236 unchanged (no unit-test changes this sprint)

### Non-functional

- [ ] `npm run e2e -- a11y/a11y-scan.spec.ts`: 0 NEW violations vs Sprint 57.17 baseline (new tokens additive only)
- [ ] `npm run e2e -- visual-regression.spec.ts`: 6/6 expected to FAIL (sidebar 6-category layout differs) → regenerate via Sprint 57.14 workflow_dispatch pattern OR defer to Sprint 57.19+ if Day 3 time runs out
- [ ] `tsc --strict`: 0 errors after all changes (interfaces + RouteEntry expanded with optional fields)
- [ ] Bundle size: compiled CSS ~+2-5 KB delta, main JS ~flat (new stub pages lazy-chunked, only category enum + Sidebar logic in main bundle)
- [ ] Manual Playwright MCP screenshot of 3 stub routes (`/overview`, `/orchestrator`, `/subagents`) + 1 existing route (`/chat-v2`) — verify sidebar renders correctly with PROP/DRAFT badges visible

### Sprint workflow discipline

- [ ] Plan file exists before any code change (this file ✅)
- [ ] Checklist file exists before Day 1 code
- [ ] Day 0 三-prong (path + content + N/A schema) drift findings catalogued in progress.md
- [ ] Per-day progress.md entries
- [ ] Day 3 retrospective Q1-Q7 complete with Q3 mockup-vs-production gap matrix + Q4 follow-up AD list
- [ ] No deletion of unchecked `[ ]` items (only `[ ]→[x]` or `🚧` annotation)

### V2 Anti-pattern 11 項 self-check (each commit + PR)

- [ ] AP-1 (Pipeline-vs-Loop): N/A (frontend scaffolding, no LLM call)
- [ ] AP-2 (Side-track code): **PASSED** — 20 stub pages are traceable from `routes.config.ts` → `AppShellV2.tsx` → Sidebar nav links → React Router routes. Not orphan code.
- [ ] AP-3 (Cross-directory scattering): **PASSED** — tokens concentrated in `index.css` + `tailwind.config.ts`; stub pages share single `ComingSoonPlaceholder` component; routes in single registry.
- [ ] AP-4 (Potemkin Features): **EVALUATED + intentional** — 20 stub pages render placeholder content (Coming Soon + mockup cross-link). This is technically a Potemkin pattern, but intentionally so + has a clear unwind: each stub has a Sprint 57.19+ scheduled port deadline (priority units listed in retro Q5). Pattern is "scaffold awaiting flesh", not "structure槽位 forgotten without content". AP-4 mitigation: explicit AD-Mockup-Page-X-Port follow-up + INTEGRATION-LOG.md tracking + AGENTS.md §9 user-不要-的-事情 cross-ref ("不要把 PROP 頁面當垃圾刪—它們是設計擴充，有保留理由").
- [ ] AP-5 (PoC accumulation): N/A
- [ ] AP-6 (Hybrid Bridge Debt): N/A — new tokens are first-party design system extensions, not "future provider switch" abstractions
- [ ] AP-7 (Context Rot): N/A (frontend, no LLM)
- [ ] AP-8 (No Centralized PromptBuilder): N/A
- [ ] AP-9 (No Verification Loop): N/A (frontend)
- [ ] AP-10 (Mock-vs-Real Divergence): N/A — design reference is intentional mock; production routes are real
- [ ] AP-11 (Naming version suffix): **PASSED** — no `_v1` / `_v2` / `_old` suffixes in any new file

## Deliverables (checklist mapping)

- [ ] **Group A (US-A1)** — mockup → `design/operator-portal/` + INTEGRATION-LOG + README cross-ref
- [ ] **Group B (US-B1)** — `tailwind.config.ts` 11 semantic + 4 risk + 2 font-family
- [ ] **Group B (US-B2)** — `index.css` 18 new HSL CSS vars (closes AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token-Audit token-coverage portion)
- [ ] **Group C (US-C1)** — `routes.config.ts` 33 entries × 6 categories + RouteCategory expansion + RouteEntry interface fields
- [ ] **Group C (US-C2)** — `ComingSoonPlaceholder.tsx` + 20 stub page wrappers + lazy imports
- [ ] **Group C (US-C3)** — `Sidebar.tsx` 6 category headers + PROP/DRAFT/SOON badge rendering
- [ ] **Group D (US-D1)** — retrospective + memory + 4 in-sprint doc syncs + PR
- [ ] **Deferred post-merge** — CLAUDE.md + SITUATION sync via `chore/closeout-57-18` PR

## Dependencies & Risks

### External dependencies

- **`reference/design-mockups/` directory**: present at sprint start (verified 2026-05-16, 24 files); `cp -r` preserves it
- **Sprint 57.14 visual-baseline workflow**: GitHub Actions `playwright-e2e.yml` job at L114-194; FIX-008 PR-not-push pattern; manual `gh pr create` fallback per Sprint 57.17 AD-CI-7
- **Geist + Noto Sans TC fonts**: declared in CSS font-family but NOT auto-loaded by Vite (consumers need to add font-display + @font-face if they want self-hosted; UA falls back to system-ui/sans-serif if not available). Fallback chain in tailwind.config.ts handles this. Loading Geist as actual web font deferred to AD-Web-Font-Loading future sprint.

### Risk matrix

| Risk | Severity | Mitigation |
|------|----------|------------|
| Sidebar 6-category refactor breaks existing e2e selectors | Medium | Day 3 full e2e run; selectors use `getByRole('link', { name: 'Chat (V2)' })` etc. which should survive layout changes. If breaks → fix specs in same PR (not the sidebar). |
| 20 lazy() stub imports significantly increase bundle | Low | Each stub re-exports same `ComingSoonPlaceholder` → tree-shake should collapse to ~1-2 KB chunk total. Verify in Day 3 build. If breaches budget → use static import + single dispatch component (alternative path). |
| HSL approximation vs mockup oklch causes visible color drift | Low | Tokens additive only this sprint (no existing components consume them yet). Sprint 57.19+ first port that consumes will visually validate. If drift unacceptable → conversion accuracy in followup sprint via design tool eyedropper. |
| visual-regression baselines 6/6 FAIL after Sidebar refactor | Medium | Expected — sidebar layout changes. Day 3 options: (a) regenerate baselines via Sprint 57.14 workflow_dispatch pattern (manual `gh workflow run playwright-e2e.yml` + PR merge to feature branch), (b) defer regen to Sprint 57.19+ (mark visual-regression as advisory in this sprint's PR description). |
| `RouteCategory` enum expansion breaks consumers expecting 3-value union | Low | TypeScript compile catches all consumers; tsc strict 0 errors gate. Only consumer is `Sidebar.tsx` (refactored in same sprint) + `AppShellV2.tsx` (just iterates ROUTES, doesn't care about category count). |
| 20 new i18n keys + 6 category keys missed in zh-TW translation file | Low | Day 2 grep check: `grep -c "nav\." frontend/src/i18n/locales/en/common.json` should match `zh-TW/common.json` count. If miss → add in Day 3 closeout. |
| Mockup `reference/design-mockups/` was modified between Day 0 and cp execution | Low | Day 0 三-prong Prong 1 captures git SHA of reference/ at sprint start; cp captures that SHA's contents. If reference/ updates mid-sprint → cherry-pick into design/operator-portal/ in Sprint 57.19+. |
| User decides mid-sprint to also do Sprint 57.19 scope (port real content for 1 page) | Medium | **Refuse scope creep**. Log as AD-Mockup-Page-X-Port for Sprint 57.19+. Rolling Planning 紀律 explicit. |
| `ComingSoonPlaceholder.tsx` reading route via `useLocation()` doesn't have access to icon at React Router level | Low | Component takes optional `routeId` prop; thin wrapper passes hardcoded routeId. Or use React Router `useMatch()` to introspect path against ROUTES. Day 2 decision based on which pattern is simpler. |

### Day 0 三-prong drift findings (to be filled in Day 0 of execution)

**Expected categories**:

- **Prong 1 (path verify)**: every file in §File Change List exists or doesn't-exist as expected
  - `frontend/src/routes.config.ts` ✅ exists (verified 2026-05-16 baseline read)
  - `frontend/src/index.css` ✅ exists (Sprint 57.17 state with v4 directive)
  - `frontend/tailwind.config.ts` ✅ exists (52 lines, v3-style content[])
  - `frontend/src/components/Sidebar.tsx` ✅ exists (verified via Glob)
  - `frontend/src/components/AppShellV2.tsx` ✅ exists
  - `frontend/src/components/ComingSoonPlaceholder.tsx` ❌ doesn't exist (target NEW)
  - `frontend/src/pages/<20 new ids>/` ❌ none exist (target NEW)
  - `design/operator-portal/` ❌ doesn't exist (target NEW)
  - `reference/design-mockups/` ✅ exists (24 files)
  - `frontend/src/i18n/locales/en/common.json` — verify in Day 0
  - `frontend/STYLE.md` ✅ exists
  - `frontend/CONVENTION.md` ✅ exists
- **Prong 2 (content verify)**: every Background claim grep-verified
  - (a) `cat frontend/src/routes.config.ts | grep -c "category:"` → expect 13 (current 13 entries) → post-Sprint 57.18 expect 33
  - (b) `cat frontend/src/routes.config.ts | grep -E "operations|admin|settings"` → confirms current 3-category state
  - (c) `cat frontend/tailwind.config.ts | grep -c "hsl(var(--"` → expect ~13 (current shadcn bridge count) → post-Sprint 57.18 expect ~27
  - (d) `cat frontend/src/index.css | grep -c "\\-\\-success\\|--warning\\|--danger\\|--thinking\\|--tool\\|--memory\\|--info\\|--risk-"` → expect 0 → post-Sprint 57.18 expect 28 (14 light × 2)
  - (e) `ls reference/design-mockups/*.jsx | wc -l` → expect 16 jsx files (verifies mockup intact)
  - (f) `cat reference/design-mockups/shell.jsx | grep -c "category:"` → expect 32 (mockup ROUTES count)
  - (g) `cat reference/design-mockups/DESIGN_RATIONALE.md | grep "auth-" | wc -l` → expect 7 (auth flow count)
  - (h) verify `Sidebar.tsx` import structure — does it currently iterate ROUTES via filter+map per category?
- **Prong 3 (schema verify)**: **N/A** (0 DB / migration / ORM / API endpoint changes this sprint)

### Roll-back plan

If sprint goal cannot be met by Day 3:

1. `git revert <Day-2-sidebar-commit>` to restore Sprint 57.17 sidebar state
2. Keep design/operator-portal/ as design reference only (skip token sync if conflicts)
3. Keep `routes.config.ts` 3-category state (defer 6-category to retry)
4. Phase 57+ Frontend 13/N → 13/N (no progress) + log full sprint as AD-Mockup-Integration-Foundation-Retry
5. Visual-regression baselines untouched (no sidebar change → no baseline regen needed)
6. Deferred OUT items (AD-Mockup-Page-X-Port × 14) remain in CLAUDE.md backlog for retry

## Workload (calibrated)

### Bottom-up estimate by US

| US | Bottom-up | Why |
|----|-----------|-----|
| US-A1 | ~0.5 hr | cp -r + README append + INTEGRATION-LOG create + git add |
| US-B1 | ~0.5 hr | 11 token entries + 2 font arrays + MHist |
| US-B2 | ~1 hr | 18 CSS vars × oklch→HSL conversion + edit + MHist |
| US-C1 | ~2 hr | RouteCategory enum + 20 new entries + 13 re-categorize + RouteEntry interface + 20 nameKey i18n keys + MHist |
| US-C2 | ~1 hr | ComingSoonPlaceholder 60 lines + 20 thin wrappers + lazy import wiring + tsc strict pass |
| US-C3 | ~1.5 hr | Sidebar refactor 6 categories + 3 badge variants + i18n category keys + visual eyeball |
| Validation | ~1 hr | npm build + full e2e + manual Playwright MCP 3 routes screenshot |
| US-D1 | ~2 hr | retro + memory + 4 in-sprint doc syncs + PR + smoke CI |

**Bottom-up total: ~9.5 hr**

### Calibrated commit

Bottom-up est ~9.5 hr → calibrated commit **~5 hr** (multiplier 0.55 — NEW class `mockup-integration-foundation` 1st application, mid-band per HYBRID weighted blend)

Day distribution:
- Day 0: ~1 hr (plan + checklist + 三-prong + branch + Day 0 commit)
- Day 1: ~1.5 hr (US-A1 + US-B1 + US-B2)
- Day 2: ~1.5 hr (US-C1 + US-C2)
- Day 3: ~1 hr (US-C3 + validation + closeout pre-PR)

## Open questions for user

1. **Brand primary color**: Mockup uses `oklch(0.62 0.16 250)` cool indigo as primary brand. Production currently uses `hsl(222.2 47.4% 11.2%)` dark slate (shadcn default). This sprint **preserves dark slate** to minimize blast radius. Decide before/at Sprint 57.19+ first port: keep dark slate / switch to mockup indigo / something else. Default this sprint = no change.

2. **Theme variant mechanism**: Mockup has 4 dark variants (linear / strict / refined / shadcn) selected via `[data-variant="..."]` attribute on `<html>`. Production has only `.dark` class. This sprint **defers variant mechanism** → AD-Theme-Variant-Mechanism. OK to defer?

3. **Density variant mechanism**: Mockup has 3 densities (compact / normal / comfortable) via `[data-density]`. Production has none. This sprint **defers** → AD-Density-Variant-Mechanism. OK to defer?

4. **Mockup integration path**: This sprint defaults to `cp -r reference/design-mockups/ design/operator-portal/` (preserves reference/ for future updates). Alternative: `mv` (single source of truth, but loses reference/ archival role). OK with cp default?

5. **visual-regression baseline regen**: Sidebar 6-category refactor will likely fail 6/6 baselines. Day 3 options: (a) **regenerate in this sprint** via workflow_dispatch + sub-PR merge to feature branch (Sprint 57.14+57.17 pattern, ~30-45 min wall time), (b) **defer to Sprint 57.19+** and mark visual-regression advisory in this PR description. Default = (a) regenerate this sprint if Day 3 time permits, else (b).

6. **ComingSoonPlaceholder cross-link**: dev-only link to `http://localhost:8080/#/<id>` (requires running mockup server) OR static text "Designed in design/operator-portal/page-X.jsx" only? Default = both (text + dev-only link via `import.meta.env.DEV`).

7. **Sprint 57.19+ first port priority**: User selected 14 priority units across 4 groups in 2026-05-16 alignment. Sprint 57.19 takes Group 1 (Operations 4) or different order? Default = follow user-stated priority (Ops 4 first) → Sprint 57.19 plan drafted at Sprint 57.18 closeout.
