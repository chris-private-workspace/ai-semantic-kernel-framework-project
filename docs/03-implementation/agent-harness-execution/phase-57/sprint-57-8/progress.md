# Sprint 57.8 Progress — AppShell V2 + chat-v2 Frontend Real Ship

**Plan**: [sprint-57-8-plan.md](../../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-8-plan.md)
**Checklist**: [sprint-57-8-checklist.md](../../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-8-checklist.md)
**Branch**: `feature/sprint-57-8-appshell-v2-chat-v2-ship`
**Branched from**: main `51162fd5` (Sprint 57.7 merged via PR #116, 2026-05-10)

---

## Day 0 — 2026-05-10

### Pre-flight baseline (per checklist 0.2)

| Check | Baseline | Status |
|-------|----------|--------|
| Backend pytest | 1622 (1615 passed + 3 admin_tenant_patch local DB pollution + 4 skipped) | ✅ matches Sprint 57.7 |
| Frontend Vitest | 41/41 passed | ✅ matches |
| Playwright e2e | 23/23 passed (8.0s) | ✅ matches |
| mypy --strict | 0 issues / 300 source files | ✅ matches |
| Vite build | 132 modules / 273.34 kB JS / gzip 84.20 kB | ✅ matches |
| 9 V2 lints | 9/9 green (with `check_ap1 --root backend/src`) | ✅ matches |
| frontend ESLint | 0 errors (silent) | ✅ pass |
| frontend typecheck | TS6310 pre-existing (D24 from Sprint 57.7 carryover) | ⚠️ pre-existing |

### Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)

#### Prong 1 — Path Verify (per AD-Plan-2)

- ✅ **NEW files (10)** all return 0 results — confirm fresh creation:
  - `frontend/src/components/AppShellV2.tsx` (NEW)
  - `frontend/src/components/Sidebar.tsx` (NEW)
  - `frontend/src/components/UserMenu.tsx` (NEW)
  - `frontend/src/store/uiStore.ts` (NEW)
  - `frontend/src/routes.config.ts` (NEW)
  - 4 NEW Vitest test files
  - `frontend/tests/e2e/chat-v2-real-ship.spec.ts` (NEW)
- ✅ **MODIFY files (8)** all return 1 result — exist for editing:
  - `frontend/src/App.tsx`, `pages/chat-v2/index.tsx`, `pages/cost-dashboard/index.tsx`,
    `pages/sla-dashboard/index.tsx`, `pages/admin-tenants/index.tsx`,
    `pages/tenant-settings/index.tsx`, `features/chat_v2/services/chatService.ts`,
    `components/AppShell.tsx`

#### Prong 2 — Content Verify (per AD-Plan-3 promoted Sprint 55.6)

| Check | Result | Drift? |
|-------|--------|--------|
| `features/chat_v2/*` 9 components export expected names | ✅ all 9 confirmed (ApprovalCard / ChatLayout / InputBar / MessageList / ToolCallCard / useLoopEventStream / streamChat / useChatStore / types) | ❌ no drift; ChatLayout/InputBar/MessageList/ToolCallCard use `export default` (not named) |
| `authService.getToken()` exists | ❌ NOT FOUND | 🔴 **D3 drift** |
| 4 existing pages AppShell wrap state | ❌ all 4 pages 0 hits; cost-dashboard wraps in `CostOverview.tsx` (inner component, NOT page) | 🔴 **D4 drift** |
| `chatService` Authorization Bearer state | ❌ raw `fetch("/api/v1/chat/", {...})` no auth | ⚠️ **D3 follow-on** (resolved by `fetchWithAuth`) |
| `App.tsx` Route count | 10 inline `<Route>` elements (registry refactor needed) | ✅ matches plan assumption |

#### Prong 3 — Schema Verify

N/A — frontend-only sprint, no DB schema changes.

### Drift findings catalog (6 D-findings)

| ID | Finding | Severity | Plan §Section affected | Resolution |
|----|---------|----------|------------------------|------------|
| **D1** | `npm run test:e2e` ≠ actual script `npm run e2e` | 🟢 trivial | checklist commands | ✅ Fix checklist 0.2 + 4.1 — use `npm run e2e` |
| **D2** | `backend/scripts/lint/run_all.py` 不存在(AD-Lint-1 wrapper from Sprint 53.7 never landed)— actual = 9 individual `scripts/lint/check_*.py` at project root, with `check_ap1` requiring `--root backend/src` arg | 🟢 trivial | checklist 0.2 + 4.1 | ✅ Fix checklist — use `for s in scripts/lint/check_*.py; do python "$s" ...; done` loop OR document explicit invocations |
| **D3** | `authService.getToken()` 不存在 — actual exports: `getJwt() / setJwt() / clearJwt() / isAuthenticated() / fetchWithAuth(url, init)`. **`fetchWithAuth` ALREADY adds Authorization Bearer header automatically.** | 🟡 scope-reduce | §US-2 + §US-5.2 | ✅ Plan §US-2 use `getJwt()` for email decode + `clearJwt()` for logout; **§US-5.2 simplified** from "add JWT Bearer header" to "swap raw `fetch` → `fetchWithAuth`" (~30 min savings) |
| **D4** | 4 existing pages all 0 AppShell hits; cost-dashboard 57.7 US-B3 wrap actually at `features/cost-dashboard/components/CostOverview.tsx` (inner component) NOT `pages/cost-dashboard/index.tsx` (outer route) | 🟠 architectural | §US-4 | ✅ **Decision A1 ratified** — page-level wrap convention; US-4 includes unwind of CostOverview AppShell wrap, move to `pages/cost-dashboard/index.tsx`. ~+1 hr scope addition. |
| **D5** | `pages/auth/login/index.tsx` already uses AppShell — auth pages should NOT have sidebar (user not authed yet) | 🟠 architectural | §US-1 + §US-4 | ✅ **Decision B1 ratified** — `AppShell.tsx` renamed to `AuthShell.tsx` for auth-only routes (login + callback). AppShellV2 reserved for authenticated routes. ~+30 min scope addition. |
| **D6** | tsconfig.json TS6310 pre-existing 57.7 D24 carryover (Referenced project tsconfig.node.json may not disable emit) | 🟢 informational | none | ⚠️ Pre-existing AD; not regression; deferred to AD-Frontend-Tsconfig (Phase 58.x) per 57.7 retro Q4 |

### Scope shift assessment

- D1 + D2 + D6: 0% shift (trivial / pre-existing)
- D3: -30 min (scope-reduce; chatService task simplified)
- D4 (A1): +1 hr (CostOverview wrap unwind)
- D5 (B1): +30 min (AppShell.tsx → AuthShell.tsx rename + 2 auth page updates)

**Net shift**: ~+1 hr (vs plan committed ~8 hr) → **~12% scope shift, within ≤20% threshold per sprint-workflow.md §Step 2.5** → **GO Day 1 with §Risks expansion** (Risk H + I + J added in plan revision below).

### Architectural decisions ratified by user (2026-05-10)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **A** (D4 wrap level) | **A1 — page-level wrap** | Standard React pattern: pages = layout/where, components = logic/what. Decouples component reuse from layout dependency. |
| **B** (D5 auth page handling) | **B1 — rename AppShell.tsx → AuthShell.tsx** | Two layout components: AuthShell (no sidebar) for unauthed routes, AppShellV2 (sidebar) for authenticated routes. Clean separation. |

### Open questions cleared (per plan §Open questions)

- Q1 Branch name `feature/sprint-57-8-appshell-v2-chat-v2-ship` ✅
- Q2 AppShell.tsx 處置 ✅ (B1 decision: RENAME to AuthShell.tsx, NOT delete)
- Q3 lucide-react 11 icon mapping ✅ (accepted)
- Q4 NEW class `frontend-arch-spike` 0.50 ✅ (accepted; AD-Sprint-Plan-10 candidate)
- Q-D4 wrap level ✅ (A1)
- Q-D5 auth page ✅ (B1)

### Day 0 actuals

- **Branch creation + baselines**: ~25 min
- **Day 0 三-prong verify**: ~35 min (catching D3+D4+D5 architectural drifts)
- **Drift findings catalog + ratification**: ~20 min
- **Plan + checklist update + progress.md**: ~15 min
- **Day 0 total**: ~95 min (~1.5 hr) vs plan estimate ~1 hr → +50% over (acceptable for first 三-prong application on architectural sprint scope)

### Next: Day 1

Day 1 scope per checklist:
- US-1.1 uiStore (Zustand sidebar state) + Vitest 3 tests
- US-1.2 Sidebar component + Vitest 3 tests
- US-1.3 AppShellV2 component + Vitest 4 tests
- US-3.1 routes.config.ts (11-page registry)
- US-3.2 App.tsx refactor (consume routes.config) + lazy-load
- Vite bundle size verify (≤ +30% headroom)

Day 1 estimate: ~5 hr (US-1 + US-3 foundation; greenfield-heavy).
