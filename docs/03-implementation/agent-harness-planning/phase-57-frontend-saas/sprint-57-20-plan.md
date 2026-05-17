---
sprint: 57.20
phase: Phase 57+ Frontend SaaS 17/N (pending close)
title: AD-Mockup-Direct-Port Foundation — Shell Rewrite + 2 Anchor Pages (Option W; Frontend-Led, Backend-Follows)
class: frontend-mockup-direct-port (NEW 0.55 1st application; HYBRID weighted blend)
duration_days: 5 (Day 0 setup + Day 1 shell rewrite + Day 2 anchor page 1 + Day 3 anchor page 2 + Day 4 closeout)
related:
  - sprint-57-20-plan.aborted-option-Y-retrofit.md (aborted predecessor; reasons in §Background)
  - Sprint 57.19 retrospective Q4 + Q5 (10 NEW carryover ADs)
  - Sprint 57.19 US-F1 DRIFT-REPORT.md (Tier 1 ~10.5 hr — superseded by direct-port philosophy)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17)
  - memory/feedback_frontend_mockup_fidelity_hard_constraint.md
  - .claude/rules/sprint-workflow.md calibration matrix
  - Sprint 57.20 Day 0 runtime capture findings (shell-level drift 5 dimensions)
---

# Sprint 57.20 — AD-Mockup-Direct-Port Foundation (Shell Rewrite + 2 Anchor Pages)

## Sprint Goal

Establish the **mockup-direct port pattern + new app shell** as the canonical frontend rendering foundation, validated by 2 anchor pages (`/overview` + `/chat-v2`) rebuilt 100% from `reference/design-mockups/` while reusing all existing functional infrastructure (auth / TanStack hooks / SSE / features layer / i18n / telemetry / tests / backend endpoints).

**Two-line philosophy** (user 2026-05-17 directive):
1. **Frontend leads** — presentation layer rewritten 1:1 from mockup; no incremental patching.
2. **Backend follows** — existing functional layer reused; backend gaps deferred to Sprint 57.21+ wire ADs.

## Background

### Why Option Y (retrofit) was aborted

Sprint 57.20 Day 0 first runtime capture via Playwright MCP revealed **5 dimensions of shell-level drift** that incremental page retrofit cannot fix:

1. **Theme**: mockup dark default vs production light default
2. **AppShell layout**: production max-w container vs mockup edge-to-edge full-screen
3. **Top toolbar**: production page-title+bell+avatar vs mockup full-width breadcrumb+tenant-badge+role-badge+search+locale
4. **Sidebar**: production "IPA" + 6-cat vs mockup "IPA Platform V2" + LOOP-FIRST badge + tenant switcher pill + bottom user identity
5. **Typography**: Geist + Noto Sans TC declared in `tailwind.config.ts` but **never wired to body**

DRIFT-REPORT.md Tier 1 ~10.5 hr (cosmetic/structural patching of 5 pages) addressed page-level diff but **not shell-level diff**. Continuing per-page retrofit on the wrong shell = wasted work. User clarified intent 2026-05-17: rewrite **頁面顯示效果** (presentation), not patch existing — Option W = **Frontend-Led, Backend-Follows direct-port**.

### What is preserved (NOT rewritten)

| Layer | Specific | Reuse mechanism |
|-------|----------|-----------------|
| Auth | WorkOS OIDC + dev-login + `RequireAuth` + `authStore` | Wrap new pages |
| API client | `fetchWithAuth` + tenant_id header + 401 redirect | Direct import |
| TanStack Query | `QueryClient` + invalidation + retry | Provider stays at app root |
| Features layer | Sprint 57.19 NEW: `features/loops` + `features/subagents` + `features/state`; existing: `features/auth/chat-v2/memory/verification/governance/cost-dashboard/sla-dashboard/admin-tenants/tenant-settings` | `import { useLoops } from "@/features/loops"` directly |
| Backend endpoints | Sprint 57.19 NEW 4 (loops/memory/state/subagents) + existing 18+ | 0 backend change this sprint |
| i18n | i18next mechanism + LOCALE_STORAGE_KEY + language switcher | Keys per mockup `i18n.jsx` |
| Telemetry | Sentry + Web Vitals + Cat 12 trace span | Inherits via app root provider |
| a11y | jsx-a11y + Lighthouse CI + axe scan | Enforces on new pages automatically |
| shadcn primitives | Card / Button / Badge / Dialog / DropdownMenu / Tabs / EmptyState / Skeleton + Sprint 57.19 cmdk Command | Direct import |
| Test infrastructure | Vitest setup + jest-dom + userEvent + MemoryRouter fixture | Preserved pattern; new test selectors per new copy |

### What gets rewritten (this sprint scope)

| Layer | Specific | Approach |
|-------|----------|----------|
| App shell | `AppShellV2.tsx` → V3 clean rewrite + NEW `Topbar.tsx` + Sidebar enrichment | 1:1 port from mockup `shell.jsx` |
| Theme | `index.css` dark default + `[data-variant]` mechanism (4 mockup variants) | Mockup `styles.css` token tree |
| Typography | Wire Geist + Noto Sans TC to body / heading classes | `tailwind.config.ts` already has fontFamily array — extend |
| Page render: `/overview` | Anchor page 1 — full JSX rewrite | 1:1 port from mockup `page-overview.jsx`; reuse `useLoops` |
| Page render: `/chat-v2` | Anchor page 2 — full JSX rewrite | 1:1 port from mockup `page-chat.jsx`; reuse SSE + InputBar state + HITL workflow |

### 17.md / V2 紀律對齊

- **約束 1 單一範疇歸屬**: 純 frontend sprint; new shell + 2 anchor pages 全在 frontend `src/`
- **約束 2 主流量驗證**: `/overview` + `/chat-v2` 在 UnifiedChat-V2 主流量; runtime Playwright MCP pair-verify required at Day 2 + Day 3 closeout
- **約束 3 LLM Provider Neutrality**: frontend 0 SDK import; preserved
- **約束 4 Anti-Pattern checklist**: AP-2 (no Potemkin — new pages must consume real data via reused hooks, NOT mocked fixtures shipped) + AP-4 (rename-only refactors prohibited; full presentation rewrite is the explicit goal); AP-3 (cross-directory scattering — new shell stays in `components/layout/`)
- **約束 5 測試優先**: Vitest baseline 277 preserved; new pages adapt existing tests (struct preserved, selectors updated); Playwright MCP fidelity pair-verify recorded as audit artifact in `claudedocs/4-changes/sprint-57-20-direct-port-foundation/screenshots/`

## User Stories

### Group A — Setup + Playwright MCP pipeline (Day 0)

**US-A1**: As a Sprint 57.20 owner, I want plan/checklist landed + branch created + Day 0 三-prong + Playwright MCP screenshot pipeline confirmed + mockup `shell.jsx` + `page-overview.jsx` + `page-chat.jsx` reference captures saved so that Day 1+ work has visual ground truth artifacts.

### Group B — Shell rewrite (Day 1)

**US-B1**: As an operator, I want the app shell (`AppShellV2.tsx` V3 + NEW `Topbar.tsx` + Sidebar enrichment) to match mockup `shell.jsx` 1:1 (dark theme default, edge-to-edge layout, full-width topbar with breadcrumb+tenant+role+search+locale, sidebar with brand block + tenant switcher pill + bottom user identity), so that any new or retrofitted page automatically inherits the correct chrome.

**US-B2**: As a developer, I want Geist + Noto Sans TC font stack actually wired to `body` + heading classes (currently declared in `tailwind.config.ts` but unused) so that typography matches mockup at runtime.

**US-B3**: As a designer, I want `[data-variant]` theme mechanism + `[data-density]` density mechanism on `<html>` root (per mockup `tweaks-panel.jsx`) so that future theme/density variants can be added without per-component rewrites.

### Group C — Anchor page 1: /overview mockup-direct port (Day 2)

**US-C1**: As an operator viewing the Loop-First Operations Overview, I want `/overview` to render 1:1 per mockup `page-overview.jsx` (loop KPI strip + active loops table + recent memory writes panel + sub-agent activity stream + cost burn micro-chart) using the existing `useLoops` + `useMemory` + `useSubagents` + `useCostBurn` hooks (reuse Sprint 57.19 features layer + Sprint 57.1 cost hooks), so that the page is the canonical mockup-port reference + delivers full mockup fidelity.

### Group D — Anchor page 2: /chat-v2 mockup-direct port (Day 3)

**US-D1**: As an operator using chat-v2, I want `/chat-v2` to render 1:1 per mockup `page-chat.jsx` (3-column layout: sessions list / message thread / inspector pane; mockup-faithful MessageList bubbles + ToolCallCard collapse UX + InputBar status pill + HITL approval modal) while **preserving 100% of existing functional behavior** (SSE event handler + InputBar state machine + HITL approval workflow + Cat 9 audit logging), so that the most behaviorally complex page validates the direct-port pattern.

### Group E — Sprint 57.19 runtime fidelity inheritance check + closeout (Day 4)

**US-E1**: As a Sprint 57.19 author closing the L3 verification gap, I want Playwright MCP screenshot pairs (production POST-Sprint-57.20 / mockup target) for the 7 Sprint 57.19 outputs (4 Operations pages + 3 Topbar overlays) confirming they auto-inherit the NEW shell's theme/typography/layout, with remaining page-level cosmetic gaps catalogued as Sprint 57.21+ AD-Mockup-Direct-Port-Round-2 candidates.

**US-E2**: As a Sprint 57.20 owner, I want commits + retrospective.md + memory snapshot + in-sprint doc syncs (CLAUDE.md / MEMORY.md / sprint-workflow.md calibration matrix +1 row) landed so that Sprint 57.20 = COMPLETE and Phase 57+ Frontend 17/N opens cleanly.

## Technical Specifications

### Shell rewrite — file change list

- **REWRITE** `frontend/src/components/AppShellV2.tsx` (~84 → ~200 lines) — V3 layout: full-screen grid `[sidebar 240px | main 1fr]`, edge-to-edge, dark default
- **NEW** `frontend/src/components/layout/Topbar.tsx` (~150 lines) — breadcrumb + tenant badge + role badge + global search input + locale dropdown + bell + avatar (reuse existing CommandPalette/NotificationsPanel/UserMenu)
- **REWRITE** `frontend/src/components/Sidebar.tsx` (~180 → ~280 lines) — brand block "IPA Platform V2" + LOOP-FIRST badge + tenant switcher pill (reuse `features/auth/tenants` if exists else fixture for Sprint 57.20) + 6-cat nav (preserve Sprint 57.18 PROP/DRAFT/SOON badges) + bottom user identity card
- **REWRITE** `frontend/src/index.css` — dark default in `:root` (currently `.dark` only) + `[data-variant]` selector layer + `[data-density]` selector layer (mockup `styles.css` token tree)
- **EDIT** `frontend/tailwind.config.ts` — fontFamily already declared; add `extend.fontFamily.sans` to apply globally via Tailwind base layer; OR `@layer base { body { font-family: ... } }` in `index.css`
- **EDIT** `frontend/src/main.tsx` or `App.tsx` — set `<html data-variant="indigo" data-density="comfortable" class="dark">` defaults

### Anchor page 1 — file change list

- **REWRITE** `frontend/src/pages/overview/index.tsx` — full JSX rewrite per mockup `page-overview.jsx`; import `useLoops` / `useMemory` / `useSubagents` from `features/` (no new hooks); reuse shadcn Card / Badge primitives
- **EDIT** `frontend/src/i18n/en/common.json` + `zh-TW/common.json` — add `overview.*` keys per mockup vocabulary (~20-30 keys per locale)
- **EDIT or NEW** `frontend/src/pages/overview/index.test.tsx` — adapt to new selectors; keep structural pattern (render + assert hook called + assert key elements present)

### Anchor page 2 — file change list

- **REWRITE** `frontend/src/pages/chat-v2/index.tsx` + relevant `features/chat_v2/components/{MessageList,InputBar,ToolCallCard,SessionsPanel,InspectorPanel}.tsx` — full JSX rewrite per mockup `page-chat.jsx` 3-column layout; **preserve all behavioral logic** (event handlers, state machines, SSE wiring, HITL approval workflow)
- **EDIT** `frontend/src/i18n/en/common.json` + `zh-TW/common.json` — add/update `chat.*` keys per mockup vocabulary
- **EDIT** existing chat-v2 vitest + Playwright specs — adapt selectors to new DOM; keep behavioral assertions intact (SSE message dispatch, approval card render, error retry)

### File header convention

Every NEW or REWRITTEN file requires standard Python/TypeScript header per `.claude/rules/file-header-convention.md` (Purpose / Category / Scope / Created / Modification History 1-line max).

### Backend impact

**0 backend changes this sprint**. All wiring uses existing endpoints. Backend wire ADs (AD-Overview-Backend-Wire / AD-Orchestrator-Backend-Wire / AD-Subagent-RealList-Phase58 / AD-Loop-Session-Enrich-Phase58 / AD-State-VersionChain-Phase58 / AD-CommandPalette-Backend-Wire / AD-NotificationsPanel-Backend-Feed / AD-UserMenu-Tenant-Switch) remain Sprint 57.21+ deferred.

## File Change List (summary)

- **NEW**: `components/layout/Topbar.tsx` (1 file)
- **REWRITE**: `components/AppShellV2.tsx` + `components/Sidebar.tsx` + `pages/overview/index.tsx` + `pages/chat-v2/index.tsx` + relevant `features/chat_v2/components/*.tsx` (~5-7 files)
- **EDIT**: `index.css` + `tailwind.config.ts` + `main.tsx` + `i18n/{en,zh-TW}/common.json` + existing chat-v2 + overview vitest/playwright specs (~6-10 files)
- **NEW docs**: `progress.md` + `retrospective.md` + `claudedocs/4-changes/sprint-57-20-direct-port-foundation/` (~3 files + screenshot artifacts)
- **EDIT docs**: CLAUDE.md (Phase 16/N→17/N + Latest/Prev Sprint shift + Next Phase 候選) + MEMORY.md (+1 line) + sprint-workflow.md calibration matrix (+1 row) + SITUATION §第八部分 (~4 files)

Sprint total: ~20-25 file touches.

## Acceptance Criteria

1. NEW shell (AppShellV2 V3 + Topbar + enriched Sidebar) visually matches mockup `shell.jsx` at 1440×900 — Playwright MCP pair-verify recorded
2. `/overview` visually matches mockup `page-overview.jsx` at 1440×900 — Playwright MCP pair-verify recorded
3. `/chat-v2` visually matches mockup `page-chat.jsx` at 1440×900 — Playwright MCP pair-verify recorded
4. All preserved functional behavior (auth / SSE / HITL / state machines / data hooks) works on the new pages — Vitest + Playwright e2e green
5. Geist + Noto Sans TC rendered at runtime (DevTools "Computed font-family" check)
6. Vitest 277/277 baseline preserved or grown (no regression)
7. Build < 4s + main bundle within +30 KB of Sprint 57.19 baseline (320.76 kB)
8. Sprint 57.19 7 outputs runtime-verified to inherit NEW shell theme/typography/layout
9. Page-level cosmetic gaps in Sprint 57.19 outputs + 14 other in-scope pages catalogued as Sprint 57.21+ candidates
10. Commits + retrospective + memory snapshot + 4 doc syncs landed

## Workload

- Bottom-up estimate: ~18-22 hr (Day 0 setup 2 hr + Day 1 shell rewrite 5-6 hr + Day 1.5 theme/font wire 1 hr + Day 2 /overview 4-5 hr + Day 3 /chat-v2 5-6 hr + Day 4 verification + closeout 3-4 hr)
- Calibration multiplier: **0.55** (NEW class `frontend-mockup-direct-port` HYBRID weighted blend: shell rewrite × 0.55 ~35% + per-page mockup-direct port × 0.50 ~50% + closeout × 0.80 ~15%)
- Calibrated commit: ~10-12 hr (matches Sprint 57.19 pace = 5-day solo-dev sprint)

**Calibration note**: 1st application of NEW class `frontend-mockup-direct-port`. Pending 2-3 sprint window validation per `When to adjust` 3-sprint rule. Sprint 57.21+ likely repeats class if Round 2 per-page port batch happens.

## Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R1 | Shell rewrite breaks existing 14 active pages' rendering | High | High | (a) Keep AppShellV2 prop interface backward compat; (b) Day 1 EOD smoke test all 14 pages render without crash before Day 2 starts |
| R2 | `/chat-v2` behavioral regression (SSE / HITL) when rewriting JSX | Medium | High | Preserve existing event handlers + state machine; only swap JSX; e2e test must pass before Day 3 close |
| R3 | Mockup `page-overview.jsx` references data shapes not in existing hooks | Medium | Medium | Day 2 first action = grep mockup against `features/loops/types.ts`; if drift > 30% → adjust scope to subset of widgets + defer rest to Sprint 57.21 |
| R4 | Dark default breaks existing tests that assert light-theme colors | Medium | Low | Wrap test fixtures with `<ThemeProvider variant="indigo" theme="dark">`; D-DAY5-2 pattern from Sprint 57.19 |
| R5 | Geist font wire requires CDN/local font file not currently bundled | Low | Medium | Check `frontend/public/fonts/` first; if missing use system fallback + log AD for font asset addition |
| R6 | Sprint 57.19 7 outputs need light cosmetic adjustment to fit new shell | High | Low | Catalogue as Sprint 57.21+ AD-Mockup-Direct-Port-Round-2 (Operations 4 + Topbar 3 polish); do NOT patch in this sprint (scope discipline) |
| R7 | Anti-Pattern AP-4 violation (rewriting JSX without real fidelity gain) | Low | High | Each rewrite MUST have Playwright MCP pair-verify artifact + DRIFT verdict (cosmetic/structural/parity) in progress.md |

### Common Risk Classes referenced (sprint-workflow.md)

- **Risk Class A (paths-filter)**: N/A — pure frontend, no CI yml changes expected
- **Risk Class B (mypy unused-ignore)**: N/A — no Python changes
- **Risk Class C (singleton across test loops)**: Possibly relevant if chat-v2 tests share QueryClient — confirm conftest.ts `beforeEach` resets

## Dependencies

- Sprint 57.19 merged (✅ `24d554f6` main HEAD `23e61603`)
- mockup files present at `reference/design-mockups/*.jsx` (✅ confirmed Day 0)
- Playwright MCP browser tools loadable (✅ confirmed Day 0)
- Mockup http.server runnable at port 8000-8080 (✅ confirmed Day 0 — logs show `GET /shell.jsx HTTP/1.1 304`)
- Dev server runnable at port 3007 (⚠️ Day 0 found port 3007 already in use — Day 0 sub-task = identify + free port OR fallback to 3005)

## Cross-Sprint Carryovers

**Preserved from Sprint 57.19** (10 NEW carryover ADs + 5 reaffirmed):
- 🔴 **AD-Mockup-Existing-Pages-Retrofit Tier 1** — REFRAMED into Sprint 57.20 W (this plan); per-page polish becomes Sprint 57.21+ Round 2 work
- AD-Subagent-RealList-Phase58 / AD-Loop-Session-Enrich-Phase58 / AD-Overview-Backend-Wire / AD-Orchestrator-Backend-Wire / AD-State-VersionChain-Phase58 / AD-CommandPalette-Backend-Wire / AD-NotificationsPanel-Backend-Feed / AD-UserMenu-Tenant-Switch — all Sprint 57.21+ backend wire deferred
- AD-Sprint-Plan-NEW-mockup-port-class — superseded by `frontend-mockup-direct-port` 0.55 class established this sprint
- Reaffirmed: AD-Post-Hotfix-Token-Audit (folds INTO this work) / AD-CI-7-GHA-PR-Permission / AD-Tailwind-v4-Config-Migration / AD-Lighthouse-Visual-Hard-Gate / AD-A11y-Structural-Nits

**Opens this sprint** (likely):
- AD-Mockup-Direct-Port-Round-2 (Sprint 57.19 7 outputs polish per new shell)
- AD-Mockup-Direct-Port-Round-3+ (remaining 14 active pages per-page port; Sprint 57.21+)
- AD-Font-Asset-Bundling (if Geist requires self-hosted font files)
- AD-Theme-Variant-Mechanism (mockup 4 variants) — partial closure via `[data-variant]` mechanism
- AD-Density-Variant-Mechanism (mockup 3 densities) — partial closure via `[data-density]` mechanism

## Out of Scope (Explicit)

- ❌ Sprint 57.19 7 outputs **page-level cosmetic patching** (auto-inherit shell only; defer polish to Sprint 57.21+)
- ❌ Remaining 14 active pages (memory / verification / governance / cost-dashboard / sla-dashboard / admin-tenants / tenant-settings / auth-extras / etc.) per-page port — Sprint 57.21+
- ❌ All backend wire ADs — Sprint 57.21+
- ❌ Tailwind v4 `@theme inline {}` full config migration — separate AD
- ❌ 18 PROP stubs activation (still ComingSoonPlaceholder)
- ❌ Visual regression baseline regeneration in CI (Sprint 57.14 mechanism; can run end-of-sprint if needed but not required deliverable)

## Definition of Sprint Complete

- [ ] All Acceptance Criteria 1-10 met
- [ ] Anti-Pattern checklist 11/11 PASS
- [ ] 4 doc syncs landed (CLAUDE.md / MEMORY.md / sprint-workflow.md calibration / SITUATION)
- [ ] PR opened against main + CI 7 checks green
- [ ] Closeout PR (chore) opened with doc syncs
- [ ] Phase 57+ Frontend status updated 16/N → 17/N
