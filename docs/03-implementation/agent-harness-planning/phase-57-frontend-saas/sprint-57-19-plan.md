---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-19-plan.md
Purpose: Sprint 57.19 plan — AD-Mockup-Operations-Port-Round1 (Phase 2 of multi-sprint mockup integration epic; Sprint 57.18 was Phase 1 scaffold). Port real content for **Operations 4** (`overview` / `orchestrator` / `subagents` / `state-inspector`) + **Topbar overlays 3** (`CommandPalette ⌘K` / `NotificationsPanel` / `UserMenu`) = 7 of 14 priority units identified in user 2026-05-16 alignment Q2. Pair with full backend Cat 1 (loops list) + Cat 3 (memory query filter + pagination) + Cat 7 (state snapshot REST) + Cat 11 (subagent registry list) API gap fills per user 2026-05-16 Q3 「前後端同 sprint」alignment. Also resolves AD-Brand-Primary-Color-Decision (57.18 carryover) — user-confirmed decision (mockup oklch indigo vs production dark slate) propagated in same sprint per 2026-05-17 alignment. Removes 7 of the 18 stub ComingSoonPlaceholder entries (overview / orchestrator / subagents / state-inspector active=true with real component, plus existing chat-v2 topbar gets 3 overlay components).
Category: Frontend / Backend Cat 1+3+7+11 / Brand identity
Scope: Phase 57 / Sprint 57.19

Description:
    Sprint 57.18 closeout (2026-05-16, PR #145 → main `b5dc8a17`; closeout
    PR #146 → main `a3d7d954`) completed Phase 1 scaffold: 23 mockup files
    cp to `design/operator-portal/`, 7 semantic tokens + 4 risk levels in
    `tailwind.config.ts`, 18 CSS vars × 2 (light + dark) in `index.css`,
    `RouteCategory` enum 3→6, 18 PROP stub routes, `ComingSoonPlaceholder.tsx`
    universal stub component, 18 thin wrapper pages, Sidebar PROP/DRAFT/SOON
    3-state badge matrix. NEW calibration class `mockup-integration-foundation`
    0.55 1st application ratio 1.10 ✅ bullseye.

    Sprint 57.18 retro Q5 + CLAUDE.md Phase 57.19+ candidate row identified
    Sprint 57.19 = **Mockup Operations Port Round 1** with explicit scope:
    Operations 4 priority units + paired backend Cat 1/3/7 gap fills (per
    user 2026-05-16 Q3「前後端同 sprint」alignment). 2026-05-17 user
    scope-expansion via AskUserQuestion (Q1+Q2+Q3 answered B+B+B):

    - **Q1**: B — Operations 4 + Topbar overlays 3 = **7 ports** this sprint
      (NOT just Operations 4)
    - **Q2**: B — **Full Cat 1/3/7/11 APIs** with query + filter + pagination
      + RLS + tests (NOT thin mock; NOT fixture-only deferral)
    - **Q3**: B — AD-Brand-Primary-Color-Decision resolved **same sprint**
      (decision + cross-codebase propagation; mockup oklch vs dark slate)

    Operations 4 mockup source pages (verified Sprint 57.18 cp from
    `reference/design-mockups/`):

    | Mockup component | Mockup file | Production route | Backend dependency |
    |---|---|---|---|
    | `OverviewPage` | `design/operator-portal/page-overview.jsx` | `/overview` (stub→active) | Cat 1 loops list + Cat 9 HITL queue + Cat 12 telemetry (existing) + incidents (deferred fixture) |
    | `Orchestrator` (+ 6 sub-tabs: Config / Prompt / Tools / Subagents / Budgets / Policies) | `design/operator-portal/page-agents.jsx` | `/orchestrator` (stub→active) | Cat 1 loop detail + Cat 2 tool registry (existing) + Cat 9 policy (existing) |
    | `SubagentsRegistry` (+ `SubagentDetail` drawer) | `design/operator-portal/page-agents.jsx` | `/subagents` (stub→active) | Cat 11 subagent registry list (NEW) |
    | `StateInspector` | `design/operator-portal/page-platform.jsx` | `/state-inspector` (stub→active) | Cat 7 state snapshot REST (NEW) |

    Topbar overlay 3 mockup source (single file
    `design/operator-portal/topbar-overlays.jsx`):

    | Mockup component | Trigger | Production target | Wire-into |
    |---|---|---|---|
    | `CommandPalette` | ⌘K / Ctrl+K global keybind | Universal modal across all routes | `AppShellV2.tsx` + global hotkey hook |
    | `NotificationsPanel` | bell icon (Topbar) | Slide-down panel from Topbar bell | `Topbar.tsx` (existing in AppShellV2) |
    | `UserMenu` | avatar/name (Topbar) | Dropdown menu from Topbar user button | `Topbar.tsx` (existing) |

    Backend API gap fill (paired per Q3 alignment):

    | Category | Existing | NEW for Sprint 57.19 | Frontend consumer |
    |---|---|---|---|
    | **Cat 1** (Orchestrator Loop) | `POST /api/v1/chat` SSE stream (Sprint 50.2); no REST list | `GET /api/v1/loops` list with tenant_id RLS + filter (status / time-range) + pagination | OverviewPage `ACTIVE_LOOPS` widget + Orchestrator detail |
    | **Cat 3** (Memory) | `GET /api/v1/memory` per Sprint 57.12; role/session 501 | Extend `/memory` query with filter (scope / time-scale / tenant) + pagination (cursor-based) | Memory page (existing per Sprint 57.12) + Overview memory widget |
    | **Cat 7** (State Mgmt) | LoopState transient/durable split (Sprint 53.1); no REST | `GET /api/v1/sessions/{session_id}/state` snapshot + tenant_id RLS | StateInspector JSON tree + diff view |
    | **Cat 11** (Subagent Orchestration) | SubagentSpawned/Completed SSE events (Sprint 57.12); no REST | `GET /api/v1/subagents` list across sessions for tenant + filter (mode: code/research/architect/review) + pagination | SubagentsRegistry list + SubagentDetail drawer |

    Brand color decision propagation (US-A1):

    - Mockup uses `oklch(0.62 0.16 250)` cool indigo as `--accent` (also
      referenced as `bg-accent` + `text-accent-foreground` in mockup
      Sidebar.jsx — confirmed Sprint 57.18 D-PRE post-merge as
      `AD-Accent-Token-Gap` carryover)
    - Production currently uses `hsl(222.2 47.4% 11.2%)` (dark slate, shadcn
      default) for `--primary`; **NO** `--accent` defined (Tailwind sees
      `bg-accent` → silently no-op — confirmed Sprint 57.16 D-PRE-4)
    - 2026-05-17 user-confirmed decision: **adopt mockup oklch indigo**
      `oklch(0.62 0.16 250)` ≈ HSL `(234, 89%, 60%)` for `--primary` in
      `:root` + matching dark-mode variant in `.dark`. Update STYLE.md §2
      brand vocabulary entry. Closes AD-Brand-Primary-Color-Decision
      (Sprint 57.18 D-PRE-1 carryover).
    - Sidebar `bg-accent` references (Sprint 57.18 introduced) become
      first real consumer of accent token; closes AD-Accent-Token-Gap.
    - **Blast radius**: existing shadcn `Button variant="default"` uses
      `bg-primary` → buttons become indigo (not dark slate); `auth/login`
      WorkOS button + AppShellV2 active-route highlight + chat-v2 send
      button visually change. Sprint 57.17 Playwright MCP screenshots
      become the baseline pre-change reference.

    This sprint executes Phase 2 of "Strategy C" staged integration plan
    (per user 2026-05-16 Q1). Phase 3+ (Sprint 57.20+) = port remaining 7
    of 14 priority units (Auth 4 補完 + Governance 3 補完).

    A. **Brand color decision propagation** (US-A1): update `index.css`
       `:root --primary` from dark slate to mockup indigo HSL; update `.dark`
       primary variant; add `--accent` + `--accent-foreground` (currently
       missing — closes AD-Accent-Token-Gap); update STYLE.md §2 brand
       vocabulary; document blast radius in retrospective Q3.

    B. **Backend Cat 1/3/7/11 API gap fill** (US-B1 + US-B2 + US-B3 + US-B4):
       4 REST endpoints with tenant_id RLS + filter + pagination + integration
       tests (real PostgreSQL via testcontainers fixture per CONVENTION §8;
       NOT TestClient mocks per AP-10 + V2 testing rule). Each endpoint
       follows 17-cross-category-interfaces.md §Contract patterns.

    C. **Frontend Operations 4 port** (US-C1 + US-C2 + US-C3 + US-C4):
       activate the 4 stub routes (set `active: true` in routes.config.ts,
       remove `proposed: true`, replace ComingSoonPlaceholder wrapper with
       real component). Use TanStack Query `useQuery` for data fetching per
       57.9 pattern (frontend-feature-with-migration 0.50 class ratio 1.00
       bullseye). Loading / error / empty states for all 4 pages. Match
       mockup visual structure but use production shadcn + Tailwind tokens
       (NOT mockup `oklch()` colors directly — use the `hsl(var(--X))`
       tokens that 57.18 wired up).

    D. **Frontend Topbar 3 overlays** (US-D1 + US-D2 + US-D3):
       `CommandPalette` global ⌘K modal + fuzzy-search across ROUTES.active
       + keyboard nav (↑↓ arrows + Enter); `NotificationsPanel` slide-down
       from Topbar bell (initially fixture data + Cat 12 telemetry hook
       reserved for Sprint 57.20+); `UserMenu` dropdown from Topbar user
       button (logout + settings + theme toggle wrapper). Each component
       receives unit tests (Vitest) + 1 Playwright e2e spec.

    E. **Closeout** (US-E1): retrospective Q1-Q7 + memory snapshot + 4
       in-sprint doc syncs (16-frontend-design.md timeline / sprint-workflow.md
       calibration NEW class `mockup-page-port-with-backend-pairing` 0.62
       1st app / 17-cross-category-interfaces.md +4 new endpoints
       documentation / INTEGRATION-LOG.md port progress update 7/28 →
       11/28 status rows transitioning from `PROP` → `SHIPPED`) + PR + 2
       deferred post-merge syncs (CLAUDE.md / SITUATION-V2-SESSION-START.md).

    Deferred OUT of this sprint (explicitly):

    - **AD-Mockup-Page-X-Port-Round-2 (Sprint 57.20+)**: Auth 4 補完
      (register / invite / mfa / expired) — paired with IAM Block B
      (WorkOS SCIM / SAML / org-level RBAC). Per user 2026-05-16 Q3 sprint
      pairing rule.
    - **AD-Mockup-Page-X-Port-Round-3 (Sprint 57.21+)**: Governance 3 補完
      (redaction / error-policy / audit-log promotion DRAFT → active).
      Paired with Cat 9 endpoint extensions.
    - **AD-Mockup-Remaining-Stubs (multi-sprint)**: 7 other PROP stubs
      not in 14 priority list (compaction / jit-retrieval / subagent-tree /
      incidents / cache-manager / sse / devui + models / tools / pricing /
      rbac / tenant-onboarding). Lower priority; defer indefinitely.
    - **AD-Theme-Variant-Mechanism** (Sprint 57.18 D-PRE-2 carryover):
      mockup 4 dark variants (linear / strict / refined / shadcn) via
      `[data-variant]`. Architectural decision deferred.
    - **AD-Density-Variant-Mechanism** (Sprint 57.18 D-PRE-3 carryover):
      mockup 3 densities via `[data-density]`. Same architectural deferral.
    - **AD-Post-Hotfix-Token-Audit** (Sprint 57.17 carryover, contrast-ratio
      portion only): broader shadcn slate sub-AA pair audit (e.g.
      `text-red-500` on white 3.76:1). Not blocked by this sprint; opens
      after this sprint's brand-color change in case new pair surfaces.
    - **AD-CI-7-GHA-PR-Permission** (Sprint 57.17 carryover): GHA cannot
      auto-create PRs. Manual `gh pr create` workaround used. Infrastructure
      track.
    - **AD-Tailwind-v4-Config-Migration** (Sprint 57.17 carryover): full v4
      idiomatic `@theme inline {}` block migration. Same-class as 57.17
      hotfix; standalone sprint estimated ~6-8 hr.
    - **AD-Lighthouse-Visual-Hard-Gate**: turn `visual-regression.spec.ts`
      from advisory to required CI gate. Sprint 57.19's changes (brand color
      + Operations 4 + Topbar overlays) WILL trigger baseline regen; opt to
      regen + carry baselines forward, but DEFER hard-gate promotion to
      Sprint 57.20+ to avoid coupling 2 unknowns.
    - **AD-A11y-Structural-Nits**: `/chat-v2` `heading-order` / `landmark-*`
      pre-existing. Not affected by this sprint. Continues as candidate.
    - **AD-SITUATION-Milestones-Sync-Gap** (Sprint 57.18 closeout NEW):
      §第九部分 missing 57.13/57.14/57.15/57.16/57.17 rows. 5-sprint
      audit-cycle mini-sprint. Defer to Sprint 57.20+.

## Sprint Goal

Phase 57+ Frontend SaaS 15/N → **16/N** — port real content for 4 Operations pages (overview / orchestrator / subagents / state-inspector) + 3 Topbar overlays (CommandPalette ⌘K / NotificationsPanel / UserMenu) from `design/operator-portal/` mockup into production frontend, paired with full backend Cat 1 loops list + Cat 3 memory query filter+pagination + Cat 7 state snapshot REST + Cat 11 subagent registry list API gap fills (per user 2026-05-16 Q3 「前後端同 sprint」alignment), plus AD-Brand-Primary-Color-Decision resolution (adopt mockup `oklch(0.62 0.16 250)` ≈ HSL `(234, 89%, 60%)` indigo for `--primary` + add missing `--accent` token closing AD-Accent-Token-Gap). 7 of 14 priority units shipped (50%); INTEGRATION-LOG.md 4/28 → 11/28 SHIPPED rows. NEW calibration class `mockup-page-port-with-backend-pairing` 0.62 HYBRID weighted blend (frontend port 0.50 + backend medium 0.80 + brand decision 0.40 + closeout 0.80) opens 1st application.

## Background

### 為什麼這個 sprint 存在（用戶 2026-05-16 Q2 + Q3 alignment + 2026-05-17 scope expansion）

User 2026-05-16 AskUserQuestion alignment locked Strategy C staged integration; Q2 = first round port covers all 14 priority units (Operations 4 + Topbar 3 + Auth 4 + Governance 3) across **rolling sprints starting 57.19+**; Q3 = backend gap fills paired in same sprint. Sprint 57.18 CLAUDE.md candidate row name `AD-Mockup-Operations-Port-Sprint-57-19` locked the scope to Operations 4 + backend Cat 1/3/7 pairing.

2026-05-17 user re-affirmed scope via AskUserQuestion at Sprint 57.19 plan kickoff:

- **Q1 frontend scope**: B — Operations 4 + Topbar overlays 3 (NOT just Operations 4; NOT all 14 in one sprint)
- **Q2 backend depth**: B — full Cat 1/3/7/11 APIs with query + filter + pagination (NOT thin mock; NOT fixture-only deferral)
- **Q3 brand color**: B — same sprint resolution (NOT hold; mockup indigo adopted)

Resulting scope is the largest port sprint of Phase 57 to date. Calibration class new + multiplier needs validation.

### 為什麼這個 sprint 是 Phase 57.18+ 候選 list 的 top candidate

CLAUDE.md Sprint 57.18 closeout Next Phase 候選 row lists 14 alternatives. **Sprint 57.19 takes candidate (a) `AD-Mockup-Operations-Port-Sprint-57-19`** which was explicitly user-flagged as "top priority per Q2 alignment" in the Sprint 57.18 closeout summary. Folds in (b) `AD-Post-Hotfix-Token-Audit` contrast-ratio portion only IF the brand color change triggers a new sub-AA pair (else deferred), (c) `AD-Brand-Primary-Color-Decision` (resolved), (e) `AD-Density-Variant-Mechanism` (deferred), (f) `AD-Accent-Token-Gap` (closed by US-A1).

Post-merge: CLAUDE.md Phase 57.20+ 候選 row should re-promote `AD-Mockup-Page-X-Port-Round-2` (Auth 4 補完 + IAM Block B pairing) + `AD-Lighthouse-Visual-Hard-Gate` (baselines reliable after this sprint's regen) + `AD-SITUATION-Milestones-Sync-Gap` backfill.

### 17.md / V2 紀律對齊

- **Cat 1 (Orchestrator Loop)**: `GET /api/v1/loops` list REST endpoint extends existing SSE-only Cat 1 surface. 17.md §Cat 1 Contract 1 (ChatClient ABC + AgentLoop) unchanged; new endpoint reads from existing `LoopState` durable persistence (Sprint 53.1) via `LoopRepository` (existing). Tenant_id RLS via `multi-tenant-data.md` 鐵律.
- **Cat 3 (Memory)**: extension only (filter + pagination on existing `/api/v1/memory` per Sprint 57.12). 17.md §Cat 3 Contract 5 (Memory ABC) unchanged.
- **Cat 7 (State Mgmt)**: NEW REST `GET /api/v1/sessions/{session_id}/state` exposes existing LoopState snapshot for the StateInspector frontend. Tenant_id RLS enforced via session lookup → tenant join. 17.md §Cat 7 Contract 9 (StateRepository) unchanged; new endpoint is a read-only adapter.
- **Cat 11 (Subagent Orchestration)**: NEW REST `GET /api/v1/subagents` list aggregates from existing SubagentSpawned/Completed event log persistence (Sprint 57.12). 17.md §Cat 11 Contract 11 unchanged.
- **Cat 12 Observability**: new endpoints get standard `category_span()` instrumentation per `observability-instrumentation.md` (`category=Cat1`/`Cat3`/`Cat7`/`Cat11` span attribute).
- **Frontend Foundation (Sprint 57.13) + chat-v2 SSE (Sprint 50.2)**: real-data ports follow 57.12 TanStack Query `useQuery` pattern per CONVENTION §10 design-system + §11 i18n + §12 a11y.
- **Sprint 57.5 Reality Check methodology**: dual scoring — code-level (lint + build + e2e + pytest green) vs runtime-level (manual Playwright MCP screenshots of all 4 Operations pages + 3 Topbar overlays in browser, with brand-indigo `bg-primary` visually verified). Day 5 closeout includes Reality Check sub-section in retrospective Q4.
- **Rolling Planning 紀律**: NOT pre-writing Sprint 57.20+ plan/checklist — only logging next port-round priority order in retrospective Q5. Sprint 57.20 plan drafted at Sprint 57.19 closeout, NOT now.
- **17.md single-source**: 4 new REST endpoints documented in `17-cross-category-interfaces.md §Section-per-category` REST surface row. Do NOT define duplicate contracts elsewhere.
- **Multi-tenant rule (3 鐵律)**: every new endpoint MUST (a) tenant_id in query/path/JWT (b) all DB queries filter `WHERE tenant_id = ?` (c) `current_tenant` FastAPI Depends. 4 new endpoints × cross-tenant read denied test = 4 new tests in `tests/integration/multi_tenant/`.

## User Stories

### Group A — Brand Color Decision Propagation (US-A1)

- **US-A1**: As a brand owner, I want the mockup-defined cool indigo `oklch(0.62 0.16 250)` ≈ HSL `(234, 89%, 60%)` adopted as production `--primary` so the production frontend matches the design vocabulary established in Sprint 57.18, and I want the missing `--accent` + `--accent-foreground` tokens added so Sidebar.tsx (Sprint 57.18) and future components consuming `bg-accent` are no longer silent no-ops (closes AD-Brand-Primary-Color-Decision + AD-Accent-Token-Gap).

### Group B — Backend Cat 1/3/7/11 APIs (US-B1 + US-B2 + US-B3 + US-B4)

- **US-B1 (Cat 1 loops list)**: As a Frontend Operations Overview page, I want `GET /api/v1/loops` returning per-tenant active+recent loops list with status / time-range filter + cursor pagination so I can render the `ACTIVE_LOOPS` widget on `/overview` with real-time data (tenant_id RLS + max 100 per page).
- **US-B2 (Cat 3 memory query extension)**: As a Frontend Memory page consumer, I want `GET /api/v1/memory` extended with `scope=` (user|session|tenant|role|system) + `time_scale=` (permanent|quarterly|daily) + `cursor=` pagination filter parameters so the Memory page (Sprint 57.12) can paginate large stores instead of returning all rows.
- **US-B3 (Cat 7 state snapshot REST)**: As a Frontend State Inspector page, I want `GET /api/v1/sessions/{session_id}/state` returning the LoopState transient+durable JSON snapshot for a session so I can render JSON tree + per-field timeline (tenant_id RLS via session→tenant join).
- **US-B4 (Cat 11 subagent registry list)**: As a Frontend Subagents page, I want `GET /api/v1/subagents` returning per-tenant subagent invocation history list with mode filter (code/research/architect/review) + cursor pagination so I can render the `SubagentsRegistry` list + `SubagentDetail` drawer with real data (NOT mockup fixture).

### Group C — Frontend Operations 4 Ports (US-C1 + US-C2 + US-C3 + US-C4)

- **US-C1 (Overview page)**: As an operator, I want `/overview` route activated with real content ported from `design/operator-portal/page-overview.jsx` (4 widgets: ACTIVE_LOOPS / HITL_QUEUE / COST_BURN / ERROR_24H) using TanStack Query `useQuery` against US-B1 + existing Cat 9 governance + existing Cat 12 telemetry endpoints, so the route no longer shows ComingSoonPlaceholder.
- **US-C2 (Orchestrator page)**: As an operator, I want `/orchestrator` route activated with real content ported from `Orchestrator` + 6 sub-tabs (Config / Prompt / Tools / Subagents / Budgets / Policies) in `design/operator-portal/page-agents.jsx` using existing Cat 1 loop-detail-via-SSE (US-B1 for list, then per-loop click → existing SSE) + Cat 2 tool registry endpoints.
- **US-C3 (Subagents Registry page)**: As an operator, I want `/subagents` route activated with `SubagentsRegistry` list + `SubagentDetail` drawer ported from `page-agents.jsx`, consuming US-B4 endpoint.
- **US-C4 (State Inspector page)**: As an operator/debugger, I want `/state-inspector` route activated with JSON tree + diff view ported from `StateInspector` in `page-platform.jsx`, consuming US-B3 endpoint (query string `?session_id=X` selects the session).

### Group D — Frontend Topbar Overlays 3 (US-D1 + US-D2 + US-D3)

- **US-D1 (CommandPalette ⌘K)**: As a power user, I want a global ⌘K (Cmd+K on macOS, Ctrl+K on Windows/Linux) modal that opens a search palette across ROUTES (active=true entries) with fuzzy substring match + keyboard nav (↑↓ + Enter to navigate, Esc to close), so I can navigate without using the sidebar.
- **US-D2 (NotificationsPanel)**: As an operator, I want a slide-down panel from the Topbar bell icon showing recent system events (initially fixture data from `design/operator-portal/topbar-overlays.jsx` NOTIFICATIONS const + a Cat 12 telemetry-feed hook reserved for Sprint 57.20+ real wiring) with unread count + dismiss action per row.
- **US-D3 (UserMenu)**: As a logged-in user, I want a dropdown from the Topbar avatar/name button with Settings / Profile / Theme Toggle (light↔dark) / Logout options, replacing the current ad-hoc logout button that exists in AppShellV2.

### Group F — Existing Pages Drift Audit (US-F1) — NEW per user 2026-05-17 directive

- **US-F1 (Existing pages mockup-fidelity drift audit)**: As a brand owner, I want a comprehensive drift audit of the 8 existing ship pages developed in Sprint 57.1-57.12 (before mockup entered production design reference) — `/cost-dashboard` (57.1) + `/sla-dashboard` (57.1) + `/admin/tenants` list (57.4) + `/admin/tenants/settings` (57.3) + `/auth/login` + `/auth/callback` (57.7) + `/chat-v2` (57.8) + `/governance/*` 3 pages (57.9) + `/verification` (57.11) + `/memory` (57.12) — comparing each against its mockup canonical source in `reference/design-mockups/` along 3 axes (visual + functional flow + i18n copy) so Sprint 57.20+ can plan a `mockup-fidelity-retrofit` sprint with accurate ground-truth scope. Output: `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md` with per-page severity classification (cosmetic / structural / functional). **Audit-only — NO retrofit code changes in this sprint** (per Rolling Planning 紀律: surface the data, defer the fix). Closes the gap between user 2026-05-17 directive「完全按照 mockup」and current state.

### Group E — Closeout (US-E1)

- **US-E1 (Closeout)**: As a maintainer, I want Sprint 57.19 properly closed with retrospective Q1-Q7 (incl. Q3 Reality Check dual scoring + Q4 follow-up AD list + Q5 Sprint 57.20 retrofit-sprint candidate informed by US-F1 audit findings) + memory snapshot + 5 in-sprint doc syncs (16-frontend-design.md timeline / sprint-workflow.md calibration NEW class / 17.md +4 endpoints / INTEGRATION-LOG.md port progress 4→11 / NEW DRIFT-REPORT.md) + 2 deferred post-merge syncs (CLAUDE.md / SITUATION) + PR merge.

## Technical Specifications

### Brand color HSL conversion (US-A1)

Mockup `oklch(0.62 0.16 250)` → HSL approximation table (verified via online oklch→hsl converter + visual eyeball on representative button render):

| Token | Mockup oklch | Production HSL (target) | CSS var location |
|---|---|---|---|
| `--primary` (light) | `oklch(0.62 0.16 250)` | `234, 89%, 60%` (indigo-500-ish) | `index.css :root` |
| `--primary-foreground` (light) | `oklch(0.98 0.005 250)` | `0, 0%, 100%` (white) | `index.css :root` |
| `--primary` (dark) | `oklch(0.72 0.14 250)` | `234, 84%, 70%` (lighter for dark bg contrast) | `index.css .dark` |
| `--primary-foreground` (dark) | `oklch(0.18 0.02 250)` | `234, 30%, 12%` (very dark indigo) | `index.css .dark` |
| `--accent` (light) — **NEW** | `oklch(0.62 0.16 250 / 0.16)` | `234, 89%, 60%` (same hue, used via Tailwind `/16` opacity modifier) | `index.css :root` |
| `--accent-foreground` (light) — **NEW** | `oklch(0.42 0.18 250)` | `234, 89%, 40%` (darker for legibility on tinted bg) | `index.css :root` |
| `--accent` (dark) — **NEW** | `oklch(0.72 0.14 250 / 0.20)` | `234, 84%, 70%` | `index.css .dark` |
| `--accent-foreground` (dark) — **NEW** | `oklch(0.92 0.04 250)` | `234, 50%, 90%` | `index.css .dark` |

Sprint 57.18 already approximated oklch→HSL for the 7 semantic + 4 risk tokens. Sprint 57.19 re-uses the same conversion methodology + documents the indigo specifically.

Blast radius:
- `shadcn/Button variant="default"` → `bg-primary` now indigo (not slate)
- `AppShellV2.tsx` active-route highlight (currently shadcn primary)
- `/auth/login` WorkOS button + dev-login button
- `/chat-v2` send button
- All `<Link>` components using `text-primary`

Pre-change baseline: Sprint 57.17 Playwright MCP screenshots of `/auth/login` + `/chat-v2`. Post-change baseline: Sprint 57.19 Day 0 + Day 5 Playwright MCP screenshots same 2 routes + new active routes.

### Cat 1 loops list endpoint (US-B1)

```
GET /api/v1/loops?status={running|completed|failed|all}&since={iso8601}&cursor={opaque}&limit={1..100}
```

Response:
```json
{
  "items": [
    {
      "loop_id": "uuid",
      "session_id": "uuid",
      "tenant_id": "uuid",
      "status": "running" | "completed" | "failed",
      "started_at": "iso8601",
      "ended_at": "iso8601 | null",
      "turn_count": 5,
      "token_usage": {"prompt": 1234, "completion": 567},
      "last_event_at": "iso8601"
    }
  ],
  "next_cursor": "opaque | null"
}
```

Implementation:
- `backend/src/api/v1/loops.py` — NEW file (~80 lines)
- Repo: `backend/src/agent_harness/orchestrator_loop/repository.py` (Sprint 53.1; **read existing first**) — add `list_loops_for_tenant(tenant_id, status, since, cursor, limit)` method
- Tenant_id from `Depends(get_current_tenant)` per `multi-tenant-data.md`
- Cursor = base64-encoded (started_at, loop_id) tuple for stable pagination

### Cat 3 memory query extension (US-B2)

Existing per Sprint 57.12: `GET /api/v1/memory` returns flat list of records for tenant. Extension:

```
GET /api/v1/memory?scope={user|session|tenant|role|system}&time_scale={permanent|quarterly|daily}&cursor={opaque}&limit={1..100}
```

Implementation:
- Edit `backend/src/api/v1/memory.py` — add query params + cursor logic
- Existing Sprint 57.12 endpoint returned all → add pagination + filter
- `MemoryRepository.list_for_tenant()` (existing) extended with same params

### Cat 7 state snapshot REST (US-B3)

```
GET /api/v1/sessions/{session_id}/state
```

Response:
```json
{
  "session_id": "uuid",
  "tenant_id": "uuid",
  "state": {
    "transient": {...},
    "durable": {...}
  },
  "captured_at": "iso8601"
}
```

Implementation:
- `backend/src/api/v1/sessions.py` — NEW file (~50 lines) OR add to existing chat router (decide Day 0)
- `StateRepository.get_snapshot(session_id, tenant_id)` — existing per Sprint 53.1; reuse
- Tenant_id from JWT; cross-tenant 404 (not 403, per multi-tenant rule)

### Cat 11 subagent registry list (US-B4)

```
GET /api/v1/subagents?mode={code|research|architect|review|all}&cursor={opaque}&limit={1..100}
```

Response: list of subagent invocations with mode / parent session / token usage / status / timestamps.

Implementation:
- `backend/src/api/v1/subagents.py` — NEW file (~70 lines)
- Read source: Sprint 57.12 introduced SubagentSpawned/Completed event store; this aggregates
- `SubagentRepository.list_for_tenant()` — likely NEW method (verify Day 0 三-prong)

### Frontend Operations 4 page port pattern (US-C1-C4)

Each page follows same skeleton (mirrors Sprint 57.9 / 57.12 TanStack pattern):

```tsx
export const OverviewPage = () => {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: ["loops", { status: "running" }],
    queryFn: () => fetchLoops({ status: "running" }),
  });

  if (isLoading) return <PageSkeleton />;
  if (error) return <PageError error={error} retry={refetch} />;
  if (!data?.items.length) return <PageEmpty message={t("overview.empty")} />;

  return (
    <PageShell title={t("overview.title")}>
      <ActiveLoopsCard loops={data.items} />
      <HitlQueueCard ... />
      <CostBurnChart ... />
      <ErrorTrendChart ... />
    </PageShell>
  );
};
```

**Visual fidelity hard constraint (per user 2026-05-17 directive)**: pages MUST render visually 1:1 with `reference/design-mockups/` source (NOT `design/operator-portal/` which is a 57.18 cp; use `reference/` as the canonical reference since the user explicitly named it). Translate mockup `<div style={{...}}>` inline styles to **exact** Tailwind utility classes (using Sprint 57.18-wired tokens such as `bg-info/10` / `text-thinking` / `border-warning` / etc.) — NOT substitute with shadcn `Card` / `Badge` defaults if those produce visually different padding / radius / shadow / color. Where Sprint 57.18 token vocabulary has no equivalent to a mockup style value, prefer Tailwind arbitrary value `text-[#hex]` / `p-[12px]` / `rounded-[10px]` (per STYLE.md §3 escape hatch) over substitution. Day 3-4 mockup-vs-production visual parity verified via Playwright MCP screenshot pair (mockup served via `python -m http.server 8080` from `reference/design-mockups/` at one viewport vs production at same viewport). Charts via existing recharts dependency (per Sprint 57.1 cost-dashboard) **with same colors / axis labels / data shape as mockup**, not recharts defaults.

### CommandPalette ⌘K modal (US-D1)

Approach: shadcn `<Dialog>` + `<Command>` (from shadcn cmdk) if available, else custom. Verify dependency at Day 0 三-prong.

```tsx
useEffect(() => {
  const down = (e: KeyboardEvent) => {
    if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      setOpen((open) => !open);
    }
  };
  document.addEventListener("keydown", down);
  return () => document.removeEventListener("keydown", down);
}, []);
```

Wire-into: `AppShellV2.tsx` — always-mounted component reading ROUTES from `routes.config.ts` (filter active=true).

### US-F1 audit methodology (per user 2026-05-17 Audit Depth answer = Visual + Functional + i18n)

Per existing-page ground-truth process:

1. **Capture mockup target**: load `reference/design-mockups/<page-X>.jsx` via `python -m http.server 8080` running from `reference/design-mockups/`; Playwright MCP screenshot at 1440×900 viewport
2. **Capture current production**: load production at same path POST-brand-change (Day 5 timing so US-A1 indigo brand already applied); Playwright MCP screenshot at same viewport
3. **Visual axis**: side-by-side compare; classify drift as cosmetic (color/padding/radius diff) / structural (different widget layout / missing-extra widgets) / functional (button/copy semantically different)
4. **Functional flow axis**: click-through key flow (e.g. cost-dashboard: month-picker → filter → export); compare with mockup's documented `onNav` / interaction patterns; flag any missing user actions or behaviorally different ones
5. **i18n axis**: extract all visible text in production page; compare with mockup's `i18n.jsx` `en` + `zh-TW` translations; flag mismatched copy / missing translations / extra strings
6. **Drift severity matrix per page**: cosmetic (Tailwind class tweaks, ~30 min each) / structural (re-layout components, ~2-3 hr each) / functional (refactor behavior, ~3-5 hr each)
7. **Output**: `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md` — per-page table with all 3 axes + severity + Sprint 57.20 retrofit-effort estimate per page
8. **Sprint 57.20 input**: drift report becomes the `mockup-fidelity-retrofit` sprint plan §Workload + §Acceptance Criteria source (drafted at Sprint 57.19 closeout, NOT now per Rolling Planning)

8 pages × ~25 min audit each = ~3.5 hr bottom-up

### Calibration class

**NEW class**: `mockup-page-port-with-backend-pairing-and-audit` — multi-domain port sprint combining frontend pattern-reuse + backend medium + brand decision propagation + existing-page audit (per user 2026-05-17 scope addition US-F1). HYBRID weighted blend:

- US-A1 brand color: 0.40 audit-cycle / docs-mechanical ~6% weight
- US-B1-B4 backend Cat APIs: 0.80 medium-backend ~31% weight (per matrix row mean 1.03 in band)
- US-C1-C4 frontend Operations port: 0.50 frontend-feature-with-migration ~27% weight (per Sprint 57.9 ratio 1.00 bullseye)
- US-D1-D3 frontend Topbar overlays: 0.55 medium-frontend ~13% weight
- US-F1 existing-pages drift audit: 0.40 audit-cycle / docs / template ~11% weight (per 57.10 matrix row — 1-data-point 1.63 over band; pending AD-Sprint-Plan-12 0.40→0.50 lift after validation)
- Validation + Playwright MCP screenshots: 0.55 medium-frontend ~6% weight
- US-E1 closeout: 0.80 closeout-ceremony ~6% weight

Weighted: (0.40 × 0.06) + (0.80 × 0.31) + (0.50 × 0.27) + (0.55 × 0.13) + (0.40 × 0.11) + (0.55 × 0.06) + (0.80 × 0.06) = 0.024 + 0.248 + 0.135 + 0.0715 + 0.044 + 0.033 + 0.048 = **~0.60 mid-band**.

1st application opens this sprint. KEEP 0.60 per `When to adjust` 3-sprint window rule. Pending 2-3 sprint validation if recurs in future port-with-audit sprints.

### Bottom-up estimate per US

| US | Bottom-up | Notes |
|----|-----------|-------|
| US-A1 (brand color) | ~1.5 hr | index.css :root + .dark primary HSL update + new --accent vars + STYLE.md §2 update + visual eyeball + MHist on 2 files |
| US-B1 (Cat 1 loops list) | ~3 hr | endpoint + repo extension + tenant_id filter + cursor pagination + 3 integration tests (happy + cross-tenant denied + pagination) + Cat 12 instrumentation |
| US-B2 (Cat 3 memory query extension) | ~2 hr | existing endpoint extension + filter + pagination + 2 tests |
| US-B3 (Cat 7 state snapshot REST) | ~3 hr | NEW endpoint + repo reuse + cross-tenant 404 test + happy test + Cat 12 instrumentation |
| US-B4 (Cat 11 subagent registry) | ~2 hr | NEW endpoint + repo.list_for_tenant method extension + 2 tests |
| US-C1 (Overview page port) | ~3 hr | 4 widgets × TanStack useQuery + loading/empty/error states + i18n keys + Vitest unit test |
| US-C2 (Orchestrator page port) | ~2.5 hr | 6 sub-tabs (Config / Prompt / Tools / Subagents / Budgets / Policies); shadcn Tabs component; mostly read-only |
| US-C3 (Subagents page port) | ~2 hr | list + detail drawer (shadcn Sheet); useQuery against US-B4 |
| US-C4 (State Inspector port) | ~2 hr | JSON tree component (react-json-tree or custom recursive); useQuery against US-B3 |
| US-D1 (CommandPalette) | ~1.5 hr | shadcn Dialog + Command (or custom) + global hotkey hook + fuzzy match + Vitest + Playwright e2e |
| US-D2 (NotificationsPanel) | ~1 hr | slide-down panel + fixture data + dismiss action + Vitest |
| US-D3 (UserMenu) | ~0.5 hr | dropdown menu wrapper + existing logout button refactor |
| US-F1 (existing pages drift audit, Visual + Functional + i18n) | ~3.5 hr | 8 pages × ~25 min Playwright MCP screenshot pair + functional flow check + i18n copy compare + DRIFT-REPORT.md per-page severity table |
| Validation (npm build + e2e + pytest + manual Playwright MCP screenshots) | ~1.5 hr | full e2e + new backend tests + 7 routes manual screenshot |
| US-E1 (closeout) | ~2 hr | retro + memory + 5 in-sprint doc syncs + PR + smoke CI feedback |

**Bottom-up total: ~31 hr**

### Calibrated commit

Bottom-up est ~31 hr → calibrated commit **~18.5 hr** (multiplier 0.60 — NEW class `mockup-page-port-with-backend-pairing-and-audit` 1st application, HYBRID weighted blend).

Day distribution (6-day sprint, Day 0-5 = 6 actual days incl Day 0 setup):
- Day 0: ~1.5 hr (plan + checklist + 三-prong + branch + Day 0 commit + capture mockup target screenshots for both new ports AND existing 8 pages baseline)
- Day 1: ~4 hr (US-A1 brand color + US-B1 Cat 1 loops API)
- Day 2: ~3.5 hr (US-B2 memory ext + US-B3 state snapshot + US-B4 subagent registry — backend day)
- Day 3: ~3.5 hr (US-C1 Overview + US-C2 Orchestrator — frontend port day 1)
- Day 4: ~3.5 hr (US-C3 Subagents + US-C4 State Inspector — frontend port day 2)
- Day 5: ~2.5 hr (US-D1 + US-D2 + US-D3 Topbar 3 + US-F1 existing-pages drift audit + closeout pre-PR)

## File Change List

### MODIFIED Frontend — src (5 files, ~+250 lines net)

- `frontend/src/index.css` (+8 lines :root --primary + --accent vars + +8 lines .dark = +16 net) — brand color US-A1
- `frontend/src/routes.config.ts` (modify 4 entries: overview / orchestrator / subagents / state-inspector — flip `active: false` → `active: true` + remove `proposed: true` + add `component:` lazy import) — net ~+20 lines
- `frontend/src/components/AppShellV2.tsx` (+~30 lines for CommandPalette mount + global ⌘K hotkey hook + Topbar 3 overlays integration) — US-D1+D2+D3
- `frontend/src/components/Topbar.tsx` (+~40 lines bell icon + user button + dropdown anchors for NotificationsPanel + UserMenu) — US-D2+D3
- `frontend/STYLE.md` (§2 brand vocabulary entry update) — US-A1 doc

### NEW Frontend — src (12 files, ~+1000 lines)

- `frontend/src/pages/overview/OverviewPage.tsx` (~200 lines) — US-C1
- `frontend/src/pages/orchestrator/OrchestratorPage.tsx` (~180 lines) — US-C2
- `frontend/src/pages/subagents/SubagentsPage.tsx` (~150 lines) — US-C3
- `frontend/src/pages/state-inspector/StateInspectorPage.tsx` (~150 lines) — US-C4
- `frontend/src/pages/overview/index.tsx` — replace 1-line wrapper (re-export → real)
- `frontend/src/pages/orchestrator/index.tsx` — replace
- `frontend/src/pages/subagents/index.tsx` — replace
- `frontend/src/pages/state-inspector/index.tsx` — replace
- `frontend/src/components/topbar/CommandPalette.tsx` (~120 lines) — US-D1
- `frontend/src/components/topbar/NotificationsPanel.tsx` (~80 lines) — US-D2
- `frontend/src/components/topbar/UserMenu.tsx` (~60 lines) — US-D3
- `frontend/src/services/api/loops.ts` (~40 lines client) — US-B1 consumer
- `frontend/src/services/api/subagents.ts` (~40 lines client) — US-B4 consumer
- `frontend/src/services/api/sessions.ts` (~40 lines client) — US-B3 consumer (memory client already exists per Sprint 57.12)

### NEW Backend — src (3 files, ~+200 lines)

- `backend/src/api/v1/loops.py` (~80 lines) — US-B1
- `backend/src/api/v1/sessions.py` (~50 lines, state snapshot route) — US-B3
- `backend/src/api/v1/subagents.py` (~70 lines) — US-B4

### MODIFIED Backend — src (4 files, ~+100 lines)

- `backend/src/api/v1/__init__.py` (+3 lines router includes for loops + sessions + subagents) — US-B1+B3+B4
- `backend/src/api/v1/memory.py` (+30 lines query param + cursor + filter) — US-B2
- `backend/src/agent_harness/orchestrator_loop/repository.py` (+30 lines `list_loops_for_tenant`) — US-B1
- `backend/src/agent_harness/subagent_orchestration/repository.py` (+30 lines `list_for_tenant`; verify exists Day 0) — US-B4

### NEW Backend — tests (4 files, ~+300 lines)

- `backend/tests/integration/api/test_loops_list.py` (~70 lines: 3 tests) — US-B1
- `backend/tests/integration/api/test_memory_query_extension.py` (~50 lines: 2 tests) — US-B2
- `backend/tests/integration/api/test_state_snapshot.py` (~60 lines: 2 tests + cross-tenant 404) — US-B3
- `backend/tests/integration/api/test_subagent_registry.py` (~60 lines: 2 tests) — US-B4

### NEW Frontend — tests (7 files, ~+400 lines Vitest + ~+200 lines Playwright)

- `frontend/src/pages/overview/__tests__/OverviewPage.test.tsx` (Vitest) — US-C1
- `frontend/src/pages/orchestrator/__tests__/OrchestratorPage.test.tsx` (Vitest) — US-C2
- `frontend/src/pages/subagents/__tests__/SubagentsPage.test.tsx` (Vitest) — US-C3
- `frontend/src/pages/state-inspector/__tests__/StateInspectorPage.test.tsx` (Vitest) — US-C4
- `frontend/src/components/topbar/__tests__/CommandPalette.test.tsx` (Vitest) — US-D1
- `frontend/e2e/specs/operations-pages.spec.ts` (Playwright, 4 routes smoke) — US-C1-C4
- `frontend/e2e/specs/topbar-overlays.spec.ts` (Playwright, ⌘K + bell + user menu) — US-D1-D3

### MODIFIED i18n (2 files)

- `frontend/src/i18n/locales/en/common.json` — add `overview.*` + `orchestrator.*` + `subagents.*` + `stateInspector.*` + `topbar.commandPalette.*` + `topbar.notifications.*` + `topbar.userMenu.*` keys (~30 NEW keys)
- `frontend/src/i18n/locales/zh-TW/common.json` — matching 繁中 translations

### NOT touched (intentional scope hold)

- `reference/design-mockups/` — preserved as authoritative design source
- `design/operator-portal/` — updated only by `INTEGRATION-LOG.md` row transitions (PROP → SHIPPED)
- 18 PROP stub routes other than the 4 Operations ports — remain as ComingSoonPlaceholder
- 4 DRAFT routes (settings legacy / others) — unchanged
- `frontend/src/components/Sidebar.tsx` — Sprint 57.18 state; PROP→SHIPPED badge transitions are automatic via routes.config.ts `proposed?` field removal (sidebar reads from registry)
- `backend/src/agent_harness/**` core (Cat 1-12) — only adapter REST endpoints added; no LLM call / loop / tool / memory etc. core changes
- Sprint 57.13 auth flow — unchanged
- Sprint 50.2 chat-v2 SSE pipeline — unchanged

### Doc syncs (in-sprint)

- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` — Sprint Timeline +1 row (57.19 Mockup Operations Port Round 1)
- `.claude/rules/sprint-workflow.md` — Calibration matrix +1 row (`mockup-page-port-with-backend-pairing-and-audit` 0.60 1st app, HYBRID weighted blend documented)
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — REST surface section +4 endpoints (Cat 1 / Cat 3 ext / Cat 7 / Cat 11)
- `design/operator-portal/INTEGRATION-LOG.md` — 4 → 11 SHIPPED rows (overview / orchestrator / subagents / state-inspector / command-palette / notifications-panel / user-menu transitions)
- `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md` — NEW per-page drift analysis (8 existing ship pages × Visual + Functional + i18n axes; per US-F1)

### Doc syncs (deferred post-merge via `chore/closeout-57-19` PR)

- `CLAUDE.md` — Phase 15/N → 16/N + Latest Sprint row + Prev Sprint row + main HEAD + Next Phase 候選 update (removes AD-Brand-Primary-Color-Decision + AD-Accent-Token-Gap; promotes AD-Mockup-Page-X-Port-Round-2 Auth 4 + AD-Lighthouse-Visual-Hard-Gate now actionable)
- `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` — §第八部分 carryover update + §第九部分 milestones +1 row 57.19

## Acceptance Criteria

### Functional

- [ ] `index.css` `:root --primary` updated to HSL `(234, 89%, 60%)`; `.dark --primary` to `(234, 84%, 70%)`; `--accent` + `--accent-foreground` added in both contexts
- [ ] `STYLE.md §2` brand vocabulary entry updated; `AD-Brand-Primary-Color-Decision` marked closed
- [ ] `GET /api/v1/loops?status=running&limit=10` returns 10 per-tenant active loops + next_cursor when more exist
- [ ] `GET /api/v1/memory?scope=user&time_scale=permanent` returns filtered records
- [ ] `GET /api/v1/sessions/{session_id}/state` returns LoopState snapshot for tenant-owned session; returns 404 for cross-tenant
- [ ] `GET /api/v1/subagents?mode=code` returns code-mode subagent invocations
- [ ] `/overview` route renders OverviewPage with 4 widgets using real data (NOT mockup fixture)
- [ ] `/orchestrator` route renders Orchestrator page with 6 tabs
- [ ] `/subagents` route renders Registry list + Detail drawer
- [ ] `/state-inspector?session_id=X` renders JSON tree for session X
- [ ] ⌘K (Cmd+K mac / Ctrl+K win) opens CommandPalette modal on any route
- [ ] Topbar bell icon click opens NotificationsPanel
- [ ] Topbar user button click opens UserMenu dropdown
- [ ] All 7 new/changed routes pass full Playwright e2e suite (existing 40 pass + new ~10 = 50 pass / 7 skip / 0 fail expected)
- [ ] `npm run lint` silent (no ESLint warnings, no new no-restricted-syntax violations)
- [ ] `npm run test` (Vitest): 236 + ~30 new = ~266 pass
- [ ] `npm run build` succeeds; main bundle size delta ≤ +30 KB (4 page components + 3 overlay components + 4 API client modules, mostly lazy-chunked)
- [ ] `pytest backend/tests/integration/api/` — 4 new test files pass; existing baseline unchanged
- [ ] `mypy --strict backend/`: 0 errors
- [ ] `python scripts/lint/run_all.py`: 6/6 V2 lints green

### Non-functional

- [ ] `npm run e2e -- a11y/a11y-scan.spec.ts`: 0 NEW violations on the 7 new/changed routes vs Sprint 57.18 baseline. Brand-color change may surface new color-contrast violations — if so, log AD-Brand-Color-Contrast and add to defer list (do NOT block this sprint).
- [ ] `npm run e2e -- visual-regression.spec.ts`: 6/6 baselines expected to FAIL (sidebar active-route highlight indigo; AppShellV2 layout extended with Topbar overlay anchors). Regenerate via Sprint 57.14 workflow_dispatch pattern in Day 5; carry baselines forward in same sprint PR.
- [ ] `tsc --strict`: 0 errors
- [ ] Backend Cat 12 instrumentation: 4 new endpoints each emit 1 OTel span with `category` attribute = Cat1/Cat3/Cat7/Cat11
- [ ] Multi-tenant 3 鐵律 verified per endpoint: (a) tenant_id from JWT (b) all DB queries WHERE tenant_id (c) cross-tenant 404 test passes
- [ ] Manual Playwright MCP screenshot of all 7 new/changed routes + ⌘K palette open + brand-indigo button visible in `/auth/login` + `/chat-v2`

### Sprint workflow discipline

- [ ] Plan file exists before any code change (this file ✅)
- [ ] Checklist file exists before Day 1 code
- [ ] Day 0 三-prong (path + content + schema) drift findings catalogued in progress.md (Prong 3 schema-verify applies — 4 NEW endpoints touching DB queries)
- [ ] Per-day progress.md entries
- [ ] Day 5 retrospective Q1-Q7 complete with Q3 Reality Check dual scoring (code-level vs runtime browser-level) + Q4 follow-up AD list
- [ ] No deletion of unchecked `[ ]` items (only `[ ]→[x]` or `🚧` annotation)

### V2 Anti-pattern 11 項 self-check (each commit + PR)

- [ ] AP-1 (Pipeline-vs-Loop): N/A (no LLM call in new code; all endpoints are repo reads + adapter)
- [ ] AP-2 (Side-track code): **PASSED** — every new endpoint traceable from `api/v1/__init__.py` router include → consumer page component → user-visible route
- [ ] AP-3 (Cross-directory scattering): **PASSED** — each endpoint in `api/v1/<name>.py` single file; repos in respective category dirs; frontend pages each in own subdir
- [ ] AP-4 (Potemkin Features): **PASSED** — 4 endpoints + 4 pages + 3 overlays all have real implementation + tests; INTEGRATION-LOG.md 4→11 SHIPPED transitions documented
- [ ] AP-5 (PoC accumulation): N/A
- [ ] AP-6 (Hybrid Bridge Debt): N/A
- [ ] AP-7 (Context Rot): N/A (no LLM)
- [ ] AP-8 (No Centralized PromptBuilder): N/A
- [ ] AP-9 (No Verification Loop): N/A (read-only endpoints)
- [ ] AP-10 (Mock-vs-Real Divergence): **PASSED** — integration tests use real PostgreSQL via testcontainers per CONVENTION §8 + V2 testing rule; NOT TestClient mocks
- [ ] AP-11 (Naming version suffix): **PASSED** — no `_v1` / `_v2` / `_old` suffixes

## Deliverables (checklist mapping)

- [ ] **Group A (US-A1)** — brand color HSL update + STYLE.md §2 + AD-Brand-Primary-Color-Decision closed + AD-Accent-Token-Gap closed
- [ ] **Group B (US-B1)** — `GET /api/v1/loops` + repo extension + 3 tests (Cat 12 instrumentation)
- [ ] **Group B (US-B2)** — `/api/v1/memory` filter+pagination extension + 2 tests
- [ ] **Group B (US-B3)** — `GET /api/v1/sessions/{session_id}/state` + 2 tests + cross-tenant 404
- [ ] **Group B (US-B4)** — `GET /api/v1/subagents` + repo extension + 2 tests
- [ ] **Group C (US-C1)** — `/overview` activated with OverviewPage real component + Vitest
- [ ] **Group C (US-C2)** — `/orchestrator` activated + 6 tabs + Vitest
- [ ] **Group C (US-C3)** — `/subagents` activated + Registry list + Detail drawer + Vitest
- [ ] **Group C (US-C4)** — `/state-inspector` activated + JSON tree + diff view + Vitest
- [ ] **Group D (US-D1)** — CommandPalette ⌘K + AppShellV2 mount + Vitest + Playwright e2e
- [ ] **Group D (US-D2)** — NotificationsPanel + Topbar bell wiring + Vitest
- [ ] **Group D (US-D3)** — UserMenu + Topbar user button wiring + Vitest
- [ ] **Group F (US-F1)** — existing 8 ship pages drift audit (Visual + Functional + i18n) + DRIFT-REPORT.md per-page severity table + Sprint 57.20 retrofit scope input
- [ ] **Group E (US-E1)** — retrospective + memory + 5 in-sprint doc syncs + PR
- [ ] **Deferred post-merge** — CLAUDE.md + SITUATION sync via `chore/closeout-57-19` PR

## Dependencies & Risks

### External dependencies

- **Cat 1 LoopRepository** (Sprint 53.1): existing; verify `list_loops_for_tenant` interface doesn't exist already at Day 0 Prong 1
- **Cat 11 SubagentRepository** (Sprint 57.12): verify `list_for_tenant` interface at Day 0; if missing, add (within US-B4 scope)
- **shadcn cmdk** (CommandPalette dependency): verify `package.json` has `cmdk` at Day 0; if missing, add (within US-D1 scope) — `npm install cmdk` adds ~5 KB
- **react-json-tree** or equivalent (StateInspector JSON tree): verify at Day 0; if absent, custom recursive component (within US-C4 scope)

### Risk matrix

| Risk | Severity | Mitigation |
|------|----------|------------|
| Brand color change breaks WCAG contrast on existing pages | Medium | Day 1 axe scan post-US-A1; if new sub-AA pair → log AD-Brand-Color-Contrast for Sprint 57.20+ + keep current sprint scope |
| Backend Cat 11 SubagentRepository doesn't have list_for_tenant | Medium | Day 0 Prong 1+2 verify; if missing, US-B4 adds it (already in scope) |
| Cursor pagination opaque format conflicts with frontend types | Low | Define cursor as `string` in OpenAPI; frontend treats as opaque token |
| `cmdk` package not installed | Low | Day 0 verify; install in Day 1 if missing |
| Operations 4 pages exceed bundle budget | Medium | Each page lazy-chunked; verify Day 4 build; if exceeds, code-split charts (recharts) |
| visual-regression baselines fail 6/6 due to brand color | High (expected) | Plan-built: regenerate via Sprint 57.14 workflow_dispatch in Day 5; carry forward in same PR |
| Operations port surfaces backend bug not API-shape issue (data semantic mismatch) | Medium | Day 3-4 build pages → run against real backend → if logic mismatch, log AD-Cat-X-Semantic + decide patch-this-sprint vs defer |
| Subagent event store query performance with many tenants | Low | Pagination limit 100 + index on `(tenant_id, started_at desc)` |
| Mid-sprint scope creep to also port Auth 4 or Governance 3 | Medium | **Refuse**. Log as AD-Mockup-Page-X-Port-Round-2/3 for Sprint 57.20+. Rolling Planning 紀律 explicit. |
| User changes brand color mid-sprint after seeing Day 1 result | Low | Day 1 post-US-A1 Playwright MCP screenshot for user review; lock decision before Day 2 |

### Day 0 三-prong drift findings (to be filled in Day 0 of execution)

**Expected categories**:

- **Prong 1 (path verify)**: every file in §File Change List exists or doesn't-exist as expected
  - `backend/src/api/v1/loops.py` ❌ expect doesn't-exist
  - `backend/src/api/v1/sessions.py` ❌ expect doesn't-exist
  - `backend/src/api/v1/subagents.py` ❌ expect doesn't-exist
  - `backend/src/api/v1/memory.py` ✅ exists (Sprint 57.12)
  - `backend/src/agent_harness/orchestrator_loop/repository.py` ✅ verify
  - `backend/src/agent_harness/subagent_orchestration/repository.py` — Day 0 Prong 1 (may not exist; if not, plan adjust)
  - `frontend/src/pages/{overview,orchestrator,subagents,state-inspector}/index.tsx` ✅ exist (Sprint 57.18 wrappers; will be replaced)
  - `frontend/src/components/Topbar.tsx` — verify (likely exists in AppShellV2)
  - `frontend/package.json` cmdk dep — Day 0 verify
- **Prong 2 (content verify)**: every Background claim grep-verified
  - (a) `grep "active: true" frontend/src/routes.config.ts | wc -l` → expect 11 → post-57.19 expect 15 (+4 Operations active)
  - (b) `grep "proposed: true" frontend/src/routes.config.ts | wc -l` → expect 18 → post-57.19 expect 14 (-4)
  - (c) `grep -r "fetchLoops\|api/v1/loops" frontend/src/` → expect 0 (frontend client NEW)
  - (d) `grep "list_loops_for_tenant\|list_for_tenant" backend/src/agent_harness/` → confirm method existence/absence at sprint start
  - (e) `cat frontend/src/index.css | grep "hsl(222"` → expect 1 (current dark slate primary) → post-57.19 expect 0
  - (f) `cat backend/src/api/v1/__init__.py | grep "include_router"` → expect 8 → post-57.19 expect 11
- **Prong 3 (schema verify)**: **APPLIES** — 4 new endpoints touch DB queries
  - `LoopState` ORM model: verify `started_at` / `ended_at` / `status` / `turn_count` / `token_usage` columns exist + types match plan claim
  - `MemoryRecord` ORM model: verify `scope` / `time_scale` columns exist (Sprint 57.12 added)
  - `SubagentInvocation` ORM model: verify exists (Sprint 57.12 added event store; could be event log only, not stable model)
  - `sessions` table FK to `tenants(id)` confirmed (multi-tenant rule)
  - No new Alembic migration this sprint (read-only endpoints only); confirm via grep `class.*Base` in models

### Roll-back plan

If sprint goal cannot be met by Day 5:

1. `git revert <Day-1-brand-commit>` to restore Sprint 57.18 dark-slate primary state
2. Keep backend endpoints + tests; merge as `feature/sprint-57-19-backend-only` if frontend ports fail
3. Stash frontend port commits; carry to Sprint 57.20 retry
4. Phase 57+ Frontend 15/N → 15/N (no progress) + log full sprint as AD-Mockup-Operations-Port-Retry
5. Deferred OUT items remain in CLAUDE.md backlog for retry

## Workload (calibrated)

### Bottom-up estimate by US

| US | Bottom-up | Why |
|----|-----------|-----|
| US-A1 | ~1.5 hr | 2 file edits + visual eyeball + STYLE.md update + MHist |
| US-B1 | ~3 hr | new endpoint + repo method + cursor pagination + 3 tests + Cat 12 span |
| US-B2 | ~2 hr | existing endpoint extension + filter + cursor + 2 tests |
| US-B3 | ~3 hr | new endpoint + repo reuse + cross-tenant 404 + Cat 12 |
| US-B4 | ~2 hr | new endpoint + repo extension + 2 tests |
| US-C1 | ~3 hr | 4 widgets × TanStack + states + i18n + Vitest |
| US-C2 | ~2.5 hr | 6 tabs (mostly read-only) + Vitest |
| US-C3 | ~2 hr | list + drawer + Vitest |
| US-C4 | ~2 hr | JSON tree + diff view + Vitest |
| US-D1 | ~1.5 hr | ⌘K modal + hotkey hook + fuzzy match + Vitest + Playwright |
| US-D2 | ~1 hr | panel + fixture + Vitest |
| US-D3 | ~0.5 hr | dropdown wrapper + Vitest |
| Validation | ~1.5 hr | full e2e + pytest + Playwright MCP 7 routes + visual baseline regen |
| US-E1 | ~2 hr | retro + memory + 4 in-sprint doc syncs + PR + smoke CI |

**Bottom-up total: ~27.5 hr**

### Calibrated commit

Bottom-up est ~27.5 hr → calibrated commit **~17 hr** (multiplier 0.62 — NEW class `mockup-page-port-with-backend-pairing` 1st application, HYBRID weighted blend per §Calibration class above)

Day distribution (6-day sprint, Day 0-5):
- Day 0: ~1 hr (plan + checklist + 三-prong + branch + Day 0 commit)
- Day 1: ~4 hr (US-A1 brand color + US-B1 Cat 1 loops API)
- Day 2: ~3.5 hr (US-B2 memory ext + US-B3 state snapshot + US-B4 subagent registry)
- Day 3: ~3.5 hr (US-C1 Overview + US-C2 Orchestrator)
- Day 4: ~3.5 hr (US-C3 Subagents + US-C4 State Inspector)
- Day 5: ~1.5 hr (US-D1 + US-D2 + US-D3 + closeout pre-PR + visual baseline regen if scope permits)

## Open questions for user

1. **Cursor pagination format**: opaque base64-encoded `(timestamp, id)` tuple OR explicit `since=<iso8601>&last_id=<uuid>` query params? Default = opaque base64 (simpler frontend, stable across sort orders).

2. **CommandPalette dependency**: install `cmdk` (~5 KB, shadcn-recommended) OR custom implementation (no new dep, ~50 extra lines)? Default = `cmdk` install if not already in `package.json`.

3. **NotificationsPanel data source**: Sprint 57.19 fixture data only OR wire Cat 12 telemetry feed this sprint? Default = fixture (per US-D2; Cat 12 wiring deferred to Sprint 57.20+ to keep Sprint 57.19 scope contained).

4. **UserMenu theme toggle**: include light↔dark toggle in this sprint OR defer to AD-Theme-Variant-Mechanism follow-up? Default = simple light/dark toggle in US-D3 (mockup matches; AD-Theme-Variant-Mechanism is about 4-variant matrix, not 2-mode).

5. **State Inspector JSON tree library**: `react-json-tree` install (~10 KB) OR custom recursive component (~50 lines, no dep)? Default = custom recursive component (less dep churn; matches mockup's simpler tree visual).

6. **visual-regression baseline regen**: regenerate in this sprint Day 5 (workflow_dispatch + sub-PR) OR mark advisory in PR description and defer to Sprint 57.20+? Default = (a) regenerate Day 5 if time permits (brand color change requires it anyway; carry baselines forward in same PR).

7. **Sprint 57.20 first scope candidate**: Auth 4 補完 + IAM Block B pairing (per user 2026-05-16 Q3 「前後端同 sprint」 rule)? OR Governance 3 補完 + Cat 9 endpoint extensions? OR AD-SITUATION-Milestones-Sync-Gap audit-cycle mini-sprint? Default = follow user 2026-05-16 stated priority order (Auth 4 next). Sprint 57.20 plan drafted at Sprint 57.19 closeout, NOT now (per Rolling Planning 紀律).
