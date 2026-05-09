---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-9-plan.md
Purpose: Sprint 57.9 plan — Governance real ship + TanStack Query 4-page migration (Phase 57+ Frontend SaaS 6/N).
Category: Frontend / Governance ship / TanStack Query migration
Scope: Phase 57 / Sprint 57.9

Description:
    Phase 57+ SaaS Frontend 6/N expansion. Sprint 57.8 delivered AppShellV2
    architecture + chat-v2 real ship (first auth-gated page). Sprint 57.9
    leverages free architectural benefit to ship governance frontend (HITL
    approver queue + audit log viewer + chain verify badge) and closes
    AD-Cost-Dashboard-UseQuery via TanStack Query 4-page migration.

    Closes: 16-frontend-design.md V2 Ship Timeline priority slot 1 of 2
    remaining (governance ~10-12 hr after chat-v2 closed Sprint 57.8;
    verification slated for Phase 57.10).

Created: 2026-05-09 (drafted)
Last Modified: 2026-05-09
Status: Draft (pending user approval)

Modification History (newest-first):
    - 2026-05-09: Initial creation (Sprint 57.9 drafting)

Related:
    - 16-frontend-design.md §V2 Ship Timeline (governance real ship priority slot)
    - sprint-57-8-plan.md (structural template per sprint-workflow.md §Step 1)
    - .claude/rules/frontend-react.md (Tailwind / shadcn / Zustand / TanStack Query rules)
    - AD-Cost-Dashboard-UseQuery (logged Sprint 57.7; closes via US-6)
---

# Sprint 57.9 — Governance Real Ship + TanStack Query 4-page Migration (Frontend 6/N)

## Sprint Goal

Promote `/governance/*` from Sprint 53.5 inline-styled placeholder to production-grade
real-ship — wrap in AppShellV2 (auth-gated), migrate 3 existing components
(ApprovalsPage / ApprovalList / DecisionModal) from inline styles to Tailwind,
introduce TanStack Query for governance + 4 existing pages (cost / sla / admin-tenants
/ tenant-settings), build NEW audit log viewer + chain verify badge consuming Sprint 53.5
backend `/audit/log` paginated + `/audit/verify-chain` endpoints — closing
AD-Cost-Dashboard-UseQuery + 16.md V2 Ship Timeline governance priority slot.

---

## Background

### Why governance + TanStack now

Sprint 57.8 closeout retrospective Q5 + user direction (2026-05-09 chat session):

1. **Architecture compound ROI** — Sprint 57.8 invested 12 hr in AppShellV2; every
   page-ship sprint after gets sidebar + sticky header + auth gate FREE. governance
   is the natural first beneficiary (HITL is V2 core differentiation).
2. **Backend 100% production-ready** — Sprint 53.5 delivered governance + audit
   endpoints (4 endpoints total: list/decide approvals + paginated audit log +
   chain verify). Frontend ship is the remaining 15% runtime gap (per Sprint 57.5
   dual scoring evidence: code 95% / runtime 85%).
3. **Pattern reuse momentum** — 5 prior frontend ships established `features/*`
   folder pattern + AppShellV2 wrap + auth gate (Sprint 57.3 / 57.4 / 57.7 / 57.8).
   Sprint 57.9 = 6th application; calibration converging.
4. **TanStack Query already wired** — Sprint 57.7 US-B2 installed `@tanstack/react-query`
   ^5.100.9 + wrapped `<QueryClientProvider>` in main.tsx with sensible defaults
   (staleTime 30s + refetchOnWindowFocus false). 4 existing pages defer migration
   per AD-Cost-Dashboard-UseQuery (logged 57.7) — Sprint 57.9 bundles closure.

### What changed since Sprint 57.8

| Asset | 57.8 ship state | 57.9 needs |
|-------|-----------------|------------|
| `pages/governance/index.tsx` | 40-line inline-styled placeholder + nested Routes (53.5) | AppShellV2 wrap + auth gate + 2-tab URL routes (approvals / audit-log) |
| `features/governance/components/ApprovalsPage.tsx` | 121-line inline styles + setInterval polling + AbortController (53.5) | Tailwind utility classes + `useApprovals` TanStack hook (drops setInterval/AbortController) |
| `features/governance/components/ApprovalList.tsx` | 115-line inline styles (53.5) | Tailwind |
| `features/governance/components/DecisionModal.tsx` | 192-line inline styles (53.5) | Tailwind + `useApprovalDecide` mutation hook (drops manual decide call + refetch) |
| `features/governance/services/governanceService.ts` | direct fetch + listPending + decide (53.5) | Swap raw `fetch` → `fetchWithAuth` (consume 57.7 IAM JWT — mirror chat-v2 D3 pattern) |
| **NEW** `features/governance/components/AuditLogViewer.tsx` | n/a | Filter form (4 fields) + paginated table consuming `/audit/log` |
| **NEW** `features/governance/components/AuditChainBadge.tsx` | n/a | Chain verify status badge (✅ Valid / ⚠️ Broken at row N / ⏳ Loading) |
| **NEW** `features/governance/services/auditService.ts` | n/a | `fetchAuditLog(filter)` + `fetchVerifyChain()` REST clients via `fetchWithAuth` |
| **NEW** `features/governance/hooks/useApprovals.ts` | n/a | TanStack `useQuery` wrapper with refetchInterval 30s |
| **NEW** `features/governance/hooks/useApprovalDecide.ts` | n/a | TanStack `useMutation` wrapper with onSuccess invalidateQueries |
| **NEW** `features/governance/hooks/useAuditLog.ts` | n/a | TanStack `useQuery` wrapper for paginated audit log (key includes filter) |
| `routes.config.ts` | governance `active: false` placeholder (57.8) | governance `active: true` + lazy `component:` import |
| 4 existing pages (`cost-dashboard` / `sla-dashboard` / `admin-tenants` / `tenant-settings`) | Direct fetch via per-feature service + Zustand `loadData` action + `useEffect` (57.1 / 57.3 / 57.4 / 57.7 US-B3) | TanStack `useQuery` wrap; Zustand stores reduced to UI-only state (filter / month picker / form draft) |

### Why `frontend-feature-with-migration` calibration class proposed (NEW)

Per Sprint 57.8 retrospective AD-Sprint-Plan-10 propose: 57.8 actual ratio 1.50
OVER band by 0.30 → split `frontend-arch-spike` 0.50 into `frontend-arch-greenfield`
(0.45) vs `frontend-arch-reuse-ship` (0.35) after 2-3 more data points. Sprint 57.9
is HYBRID (3 components reuse + 3 NEW + 4-page mechanical migration); single class
inadequate.

NEW class `frontend-feature-with-migration` baseline 0.50 weighted blend:
- US-1+US-2 lean polish reuse (≈3 hr × 0.40)
- US-3 TanStack governance hooks (≈3 hr × 0.45)
- US-4 NEW audit log viewer (≈4 hr × 0.55 medium-frontend)
- US-5 chain verify badge (≈1.5 hr × 0.45)
- US-6 4-page TanStack mechanical migration (≈6 hr × 0.30)
- Day 0+4 fixed offset (≈4 hr × 0.85)

Bottom-up est ~22 hr; weighted blend yields ~10.6 hr commit. Round to **~10.5 hr** mid-band.

---

## User Stories

### US-1 (reuse) — Governance page AppShellV2 wrap + auth gate + 2-tab routes

**As an** authenticated approver / auditor user
**I want** the governance page to use the V2 sidebar layout with sticky header,
gated by auth, with 2 sub-routes (Pending Approvals / Audit Log) URL-addressable
**So that** UX is consistent with chat-v2 / cost / sla / admin-tenants / tenant-settings,
the page is auth-protected (per Sprint 57.7 IAM), and tabs are bookmarkable

**Acceptance**:
- `pages/governance/index.tsx` wraps in `<AppShellV2 pageTitle="Governance">`
- Auth gate via existing `isAuthenticated() + setPostLoginRedirect("/governance")`
  + `<Navigate to="/auth/login" replace />` (mirror chat-v2 Sprint 57.8 US-5 pattern)
- 2 nested routes: `/governance/approvals` (default redirect from `/governance`) +
  `/governance/audit-log` (NEW — US-4 dependency)
- Tab nav UI in page (header actions slot or inline tabs above content):
  2 nav links with active state via `useLocation()`
- routes.config.ts updated: governance `active: true` + lazy `component: () => import("./pages/governance")`
- `<Navigate to="approvals" replace />` for `/governance` index match (preserve 53.5 default)

### US-2 (reuse) — Inline styles → Tailwind migration (3 components)

**As a** maintainer
**I want** ApprovalsPage / ApprovalList / DecisionModal to use Tailwind utility
classes instead of inline `style={{}}` objects
**So that** governance complies with `.claude/rules/frontend-react.md` "no inline styles"
rule, matches Sprint 57.7 US-B3 cost-dashboard precedent, and styles are tree-shakeable

**Acceptance**:
- `ApprovalsPage.tsx` — drop `pageStyle / headerRow / buttonStyle` const objects;
  replace with Tailwind utilities (`p-6 font-sans` / `flex items-baseline justify-between mb-4` / etc.)
- `ApprovalList.tsx` — drop inline styles; use shadcn `<Table>` primitives or Tailwind
- `DecisionModal.tsx` — drop inline styles; use shadcn `<Dialog>` primitive (or Tailwind
  if `<Dialog>` adds bundle weight; document choice in plan §Risks)
- All risk badge colors preserved (#2e7d32 LOW / #ed6c02 MEDIUM / #d84315 HIGH / #b71c1c CRITICAL)
  via Tailwind `text-green-700 / text-orange-600 / text-orange-800 / text-red-800` or arbitrary values
- Existing Vitest unit tests pass unchanged (regression sentinel)

### US-3 (reuse) — TanStack Query governance hooks

**As a** developer maintaining governance UX
**I want** `useApprovals` (query) + `useApprovalDecide` (mutation) hooks
**So that** ApprovalsPage drops manual `useEffect / useState / setInterval / AbortController`
boilerplate, decision submit auto-invalidates approvals query, and UX is
declarative + cache-aware

**Acceptance**:
- `features/governance/hooks/useApprovals.ts` NEW:
  - `useQuery({ queryKey: ['governance', 'approvals'], queryFn: () => governanceService.listPending(), refetchInterval: 30_000 })`
  - Returns `{ data: ApprovalSummary[] | undefined, isLoading, error, refetch }`
- `features/governance/hooks/useApprovalDecide.ts` NEW:
  - `useMutation({ mutationFn: ({ id, decision, reason }) => governanceService.decide(id, decision, reason), onSuccess: () => qc.invalidateQueries({ queryKey: ['governance', 'approvals'] }) })`
- ApprovalsPage refactored to consume `useApprovals` (drop useState/useEffect/setInterval/AbortController)
- DecisionModal refactored to consume `useApprovalDecide` (drop manual `await decide + refresh`)
- governanceService.ts: swap raw `fetch` → `fetchWithAuth` (Sprint 57.7 IAM JWT injection)
- Existing 5 Vitest unit tests for governance components pass unchanged
- 3 NEW Vitest unit tests for hooks (useApprovals / useApprovalDecide / refactored ApprovalsPage smoke)

### US-4 (greenfield) — Audit log viewer with filter + pagination

**As an** auditor / compliance role
**I want** a paginated audit log viewer with filters (operation / resource_type /
date range / user_id) consuming `/api/v1/audit/log`
**So that** I can investigate operations chronologically + filter by criteria
without writing SQL — replacing 53.5 placeholder text "Audit log + risk policy
management land in subsequent sprints"

**Acceptance**:
- `features/governance/services/auditService.ts` NEW:
  - `fetchAuditLog(filter: AuditLogFilter): Promise<AuditLogPage>` consuming GET `/api/v1/audit/log`
  - Filter shape: `{ operation?: string; resource_type?: string; user_id?: string; from_ts_ms?: number; to_ts_ms?: number; offset: number; page_size: number }`
  - Uses `fetchWithAuth` for IAM JWT
- `features/governance/hooks/useAuditLog.ts` NEW:
  - `useQuery({ queryKey: ['governance', 'audit-log', filter], queryFn: () => auditService.fetchAuditLog(filter) })`
  - Cursor-style pagination: page state lives in component; query key includes filter (auto-refetch on change)
- `features/governance/components/AuditLogViewer.tsx` NEW:
  - Filter form: 4 fields (operation dropdown if known set / resource_type dropdown / date range pickers / user_id input)
  - Paginated table: 50 rows default; columns = timestamp / operation / resource_type / resource_id / user_id / current_log_hash (truncated)
  - Next/Prev buttons; disabled when not applicable; `has_more` indicator
  - Loading skeleton + error retry UX (mirror cost-dashboard CostOverview pattern)
- 1 Vitest unit test for AuditLogViewer (renders + filter form interaction)
- 1 Vitest unit test for useAuditLog (queryKey structure / refetch on filter change)

### US-5 (greenfield) — Audit chain verify badge

**As an** auditor / compliance role
**I want** a top-level chain verify badge showing whether the tenant's audit
chain is intact (✅ Valid / ⚠️ Broken at row N / ⏳ Loading)
**So that** I can quickly assess data integrity before / after investigations

**Acceptance**:
- `features/governance/components/AuditChainBadge.tsx` NEW:
  - Calls `auditService.verifyChain()` once on mount (no auto-refresh — heavy operation per backend docstring)
  - Displays badge: `✅ Chain valid (N entries)` / `⚠️ Chain broken at row {broken_at_id}` / `⏳ Verifying chain…` / `❌ Verify failed: {error}`
  - Tailwind utility-class badge (no inline styles)
  - Optional manual `Re-verify` button (calls `refetch()` on TanStack)
- `auditService.ts` extends with `verifyChain(): Promise<ChainVerifyResult>` consuming GET `/api/v1/audit/verify-chain`
- Mounted in `AuditLogViewer` page header (top-right of filter form area)
- 1 Vitest unit test (renders 3 states: valid / broken / loading)

### US-6 (mechanical) — TanStack Query 4-page migration

**As a** maintainer
**I want** cost-dashboard / sla-dashboard / admin-tenants / tenant-settings to
use TanStack Query for server state instead of Zustand `loadData` actions +
`useEffect` patterns
**So that** AD-Cost-Dashboard-UseQuery (logged Sprint 57.7) closes,
all pages get cache-aware refetch + invalidation primitives, and Zustand
stores are reduced to pure UI state (filter / month picker / form draft)

**Acceptance**:
- 4 NEW hook files `features/<page>/hooks/use<X>.ts`:
  - `useCostSummary(tenantId, month)` for cost-dashboard
  - `useSLAOverview(tenantId)` for sla-dashboard
  - `useTenantList(filter)` for admin-tenants (filter dimensions: state / plan / search / offset / page_size)
  - `useTenant(tenantId)` for tenant-settings (single GET)
- 4 components refactored: `CostOverview.tsx` / `SLAOverview.tsx` / `AdminTenantsPage` (or wherever list lives) / `TenantSettingsView`
  - Drop `useEffect + useStore.loadData` pattern
  - Use hook + render `data / isLoading / error` declaratively
- Zustand stores reduced (per page):
  - costStore: keep `currentMonth` UI state; drop `data / loading / error` server state
  - slaStore: keep `tenant_id` UI state if any; drop server state
  - adminTenantsStore: keep filter UI state (state / plan / search / offset); drop list server state
  - tenantSettingsStore: keep `editDraft` form state; drop server `data / loading / error`
- Existing Vitest unit tests + Playwright e2e tests pass unchanged (regression sentinel)
- Vite bundle JS ≤ 280 kB main (Sprint 57.8 baseline 246.19 kB + 30 kB headroom)
- AD-Cost-Dashboard-UseQuery closes (logged 57.7)

---

## Technical Specifications

### Pages folder structure

```
frontend/src/pages/governance/
├── index.tsx                  ← AppShellV2 wrap + auth gate + nested Routes container
└── (no other files; sub-page components live in features/governance/)

frontend/src/features/governance/
├── components/
│   ├── ApprovalsPage.tsx      ← MIGRATE: Tailwind + useApprovals hook
│   ├── ApprovalList.tsx       ← MIGRATE: Tailwind
│   ├── DecisionModal.tsx      ← MIGRATE: Tailwind + useApprovalDecide hook
│   ├── AuditLogViewer.tsx     ← NEW: filter form + paginated table
│   └── AuditChainBadge.tsx    ← NEW: chain verify status
├── hooks/                     ← NEW directory
│   ├── useApprovals.ts        ← NEW: TanStack useQuery wrapper
│   ├── useApprovalDecide.ts   ← NEW: TanStack useMutation wrapper
│   └── useAuditLog.ts         ← NEW: TanStack useQuery wrapper
├── services/
│   ├── governanceService.ts   ← MODIFY: fetchWithAuth swap
│   └── auditService.ts        ← NEW: fetchAuditLog + verifyChain
└── types.ts                   ← MODIFY: extend with AuditLogFilter / AuditLogPage / ChainVerifyResult / AuditLogEntry
```

### useApprovals hook (TanStack)

```ts
// frontend/src/features/governance/hooks/useApprovals.ts
import { useQuery } from "@tanstack/react-query";
import { governanceService } from "../services/governanceService";

export const APPROVALS_QUERY_KEY = ["governance", "approvals"] as const;

export function useApprovals() {
  return useQuery({
    queryKey: APPROVALS_QUERY_KEY,
    queryFn: ({ signal }) => governanceService.listPending(signal),
    refetchInterval: 30_000,  // mirror Sprint 53.5 polling cadence
  });
}
```

### useApprovalDecide hook (TanStack mutation)

```ts
// frontend/src/features/governance/hooks/useApprovalDecide.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { governanceService } from "../services/governanceService";
import { APPROVALS_QUERY_KEY } from "./useApprovals";
import type { DecisionLabel } from "../types";

interface DecideArgs {
  id: string;
  decision: DecisionLabel;
  reason?: string;
}

export function useApprovalDecide() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, decision, reason }: DecideArgs) =>
      governanceService.decide(id, decision, reason),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: APPROVALS_QUERY_KEY });
    },
  });
}
```

### Pages governance/index.tsx (composed real ship)

```tsx
// frontend/src/pages/governance/index.tsx
import { Navigate, Route, Routes, NavLink } from "react-router-dom";
import { AppShellV2 } from "@/components/AppShellV2";
import { isAuthenticated, setPostLoginRedirect } from "@/features/auth/services/authService";
import { ApprovalsPage } from "@/features/governance/components/ApprovalsPage";
import { AuditLogViewer } from "@/features/governance/components/AuditLogViewer";

export default function GovernancePage(): JSX.Element {
  if (!isAuthenticated()) {
    setPostLoginRedirect("/governance");
    return <Navigate to="/auth/login" replace />;
  }
  return (
    <AppShellV2 pageTitle="Governance">
      <nav className="mb-4 flex gap-2 border-b border-border">
        <NavLink
          to="approvals"
          className={({ isActive }) =>
            `px-4 py-2 text-sm font-medium ${
              isActive ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`
          }
        >
          Pending Approvals
        </NavLink>
        <NavLink
          to="audit-log"
          className={({ isActive }) =>
            `px-4 py-2 text-sm font-medium ${
              isActive ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`
          }
        >
          Audit Log
        </NavLink>
      </nav>
      <Routes>
        <Route index element={<Navigate to="approvals" replace />} />
        <Route path="approvals" element={<ApprovalsPage />} />
        <Route path="audit-log" element={<AuditLogViewer />} />
      </Routes>
    </AppShellV2>
  );
}
```

### routes.config.ts update

```ts
// frontend/src/routes.config.ts (modify)
{
  name: "Governance",
  path: "/governance",  // base; sub-routes handled by GovernancePage internally
  icon: ShieldCheck,
  category: "admin",
  active: true,         // was false in Sprint 57.8
  component: () => import("./pages/governance"),
}
```

Note: AppShellV2 wrap is INSIDE GovernancePage (per Sprint 57.8 A1 page-level
wrap convention). Sub-routes (`/governance/approvals` and `/governance/audit-log`)
both render inside the same AppShellV2 instance (single mount; tab swap is just
nested route swap).

### Audit log filter UI sketch

```
┌──────────────────────────────────────────────────────┐
│ Filter                                  [Re-verify ↻] │  ← AuditChainBadge top-right
│ ┌──────────┬──────────┬─────────┬─────────────────┐  │
│ │Operation │Resource  │User ID  │Date range       │  │
│ │[dropdown]│[dropdown]│[input]  │[from] → [to]    │  │
│ └──────────┴──────────┴─────────┴─────────────────┘  │
│   [Apply] [Reset]                                     │
├──────────────────────────────────────────────────────┤
│ ✅ Chain valid (N entries)         ← AuditChainBadge  │
├──────────────────────────────────────────────────────┤
│ Time     │ Operation │ Resource │ Hash (truncated)   │
│ ─────────┼───────────┼──────────┼───────────────     │
│ 12:34:56 │ session_start │ session │ 3a4f...          │
│ 12:35:01 │ approval_decided │ ... │ 7b2c...          │
│ ...                                                   │
├──────────────────────────────────────────────────────┤
│ ← Prev    Page X / has_more=true     Next →          │
└──────────────────────────────────────────────────────┘
```

### TanStack 4-page migration pattern (canonical)

```tsx
// BEFORE (cost-dashboard CostOverview.tsx pre-57.9):
const { currentMonth, data, loading, error, loadData } = useCostStore();
useEffect(() => {
  if (tenantId) void loadData(tenantId);
}, [tenantId, currentMonth, loadData]);

// AFTER (cost-dashboard CostOverview.tsx 57.9):
const { currentMonth } = useCostStore();  // UI state only
const { data, isLoading, error, refetch } = useCostSummary(tenantId, currentMonth);
// (no useEffect; useQuery handles fetch on mount + on key change)
```

### Calibration: HYBRID `frontend-feature-with-migration` 0.50 (NEW class proposal)

| Component | Weight | Class | Multiplier | Calibrated hr |
|-----------|--------|-------|------------|---------------|
| US-1 + US-2 (lean polish reuse) | 3/22 | `mixed-pattern-reuse` | 0.40 | 1.20 |
| US-3 TanStack governance hooks (medium reuse) | 3/22 | `mixed-pattern-reuse` (slight more) | 0.45 | 1.35 |
| US-4 audit log NEW (greenfield-ish) | 4/22 | `medium-frontend` | 0.55 | 2.20 |
| US-5 chain badge (small NEW) | 1.5/22 | `mixed-pattern-reuse` | 0.45 | 0.68 |
| US-6 4-page mechanical migration | 6/22 | `frontend-page-migration` (NEW sub-class candidate) | 0.30 | 1.80 |
| Day 0 + Day 4 closeout overhead | 4.5/22 | `closeout` | 0.85 | 3.83 |
| **Bottom-up est** | **22 hr** | — | — | **~11.06 hr** |

Or single HYBRID class `frontend-feature-with-migration` 0.50: 22 × 0.50 = **~11 hr**.

Both methods converge on **~11 hr**. Round to **~10.5 hr** mid-band.

---

## File Change List

### Frontend NEW

| File | Purpose | LOC est |
|------|---------|---------|
| `frontend/src/features/governance/hooks/useApprovals.ts` | TanStack useQuery wrapper | ~30 |
| `frontend/src/features/governance/hooks/useApprovalDecide.ts` | TanStack useMutation wrapper | ~35 |
| `frontend/src/features/governance/hooks/useAuditLog.ts` | TanStack useQuery wrapper | ~40 |
| `frontend/src/features/governance/services/auditService.ts` | REST client (audit/log + verify-chain) | ~60 |
| `frontend/src/features/governance/components/AuditLogViewer.tsx` | Filter + table component | ~150 |
| `frontend/src/features/governance/components/AuditChainBadge.tsx` | Chain verify badge | ~60 |
| `frontend/src/features/cost-dashboard/hooks/useCostSummary.ts` | TanStack useQuery wrapper | ~30 |
| `frontend/src/features/sla-dashboard/hooks/useSLAOverview.ts` | TanStack useQuery wrapper | ~30 |
| `frontend/src/features/admin-tenants/hooks/useTenantList.ts` | TanStack useQuery wrapper | ~40 |
| `frontend/src/features/tenant-settings/hooks/useTenant.ts` | TanStack useQuery wrapper | ~30 |
| `frontend/tests/unit/governance/useApprovals.test.tsx` | Vitest hook tests | ~40 |
| `frontend/tests/unit/governance/useApprovalDecide.test.tsx` | Vitest mutation tests | ~40 |
| `frontend/tests/unit/governance/useAuditLog.test.tsx` | Vitest hook tests | ~40 |
| `frontend/tests/unit/governance/AuditLogViewer.test.tsx` | Vitest component tests | ~50 |
| `frontend/tests/unit/governance/AuditChainBadge.test.tsx` | Vitest component tests | ~40 |
| `frontend/tests/e2e/governance/governance-real-ship.spec.ts` | Playwright 4 cases | ~150 |

### Frontend MODIFY

| File | Change |
|------|--------|
| `frontend/src/pages/governance/index.tsx` | 40-line placeholder → AppShellV2 wrap + auth gate + 2-tab nested Routes |
| `frontend/src/features/governance/components/ApprovalsPage.tsx` | Inline → Tailwind + drop useEffect/useState/setInterval/AbortController → useApprovals hook |
| `frontend/src/features/governance/components/ApprovalList.tsx` | Inline → Tailwind |
| `frontend/src/features/governance/components/DecisionModal.tsx` | Inline → Tailwind + drop manual decide call → useApprovalDecide mutation |
| `frontend/src/features/governance/services/governanceService.ts` | Raw `fetch` → `fetchWithAuth` (consume 57.7 IAM JWT) |
| `frontend/src/features/governance/types.ts` | Extend with AuditLogFilter / AuditLogPage / AuditLogEntry / ChainVerifyResult |
| `frontend/src/routes.config.ts` | governance entry: `active: false` → `active: true` + lazy `component:` |
| `frontend/src/features/cost-dashboard/components/CostOverview.tsx` | Drop useEffect/loadData → useCostSummary hook |
| `frontend/src/features/cost-dashboard/store/costStore.ts` | Reduce to UI-only state (currentMonth + setMonth); drop data/loading/error/loadData |
| `frontend/src/features/sla-dashboard/components/SLAOverview.tsx` | Same pattern as cost |
| `frontend/src/features/sla-dashboard/store/slaStore.ts` | Same reduction |
| `frontend/src/features/admin-tenants/pages/<list>.tsx` (TBD via Day 0 path verify) | useEffect/loadList → useTenantList hook |
| `frontend/src/features/admin-tenants/store/adminTenantsStore.ts` | Reduce to UI state (filter + offset); drop list server state |
| `frontend/src/features/tenant-settings/components/TenantSettingsView.tsx` | useEffect/loadTenant → useTenant hook |
| `frontend/src/features/tenant-settings/store/tenantSettingsStore.ts` | Reduce to UI state (editDraft); drop server state |

### Backend NEW / MODIFY

None expected — Sprint 57.9 is frontend-only ship; backend Sprint 53.5 governance
+ audit endpoints + Sprint 57.7 IAM all production-ready.

(Risk: if Day 0 三-prong reveals `fetchWithAuth` adds JWT but backend audit/governance
requires explicit role JWT claim mismatch with current 57.7 IAM `roles` claim shape,
scope expands — see §Risk D.)

---

## Acceptance Criteria

### US-1 (governance AppShellV2 + auth gate + tabs)
- [ ] `pages/governance/index.tsx` wraps in `<AppShellV2 pageTitle="Governance">`
- [ ] Unauthed visit → `/auth/login` redirect (smoke test)
- [ ] `/governance` redirects to `/governance/approvals`
- [ ] `/governance/audit-log` renders AuditLogViewer
- [ ] Tab nav active state highlights via `useLocation()`
- [ ] routes.config.ts: governance `active: true` + lazy component import

### US-2 (Tailwind migration)
- [ ] ApprovalsPage / ApprovalList / DecisionModal: 0 inline `style={{}}` survives
  - Verify: `grep -n "style={{" frontend/src/features/governance/components/`
- [ ] Risk badge colors preserved (LOW/MEDIUM/HIGH/CRITICAL palette mapped to Tailwind)
- [ ] Existing 5 Vitest tests for governance components pass unchanged

### US-3 (TanStack governance hooks)
- [ ] useApprovals + useApprovalDecide hooks created
- [ ] ApprovalsPage drops setInterval/AbortController/useEffect
- [ ] DecisionModal drops manual decide+refresh; uses mutation
- [ ] governanceService swaps `fetch` → `fetchWithAuth`
- [ ] 3 Vitest unit tests for hooks pass
- [ ] AD-Front-1 polling pattern (Sprint 53.5 deferred SSE) replaced by TanStack refetchInterval

### US-4 (audit log viewer)
- [ ] AuditLogViewer component renders filter form + table + pagination
- [ ] Filter form 4 fields: operation / resource_type / user_id / date range
- [ ] Apply button triggers refetch via key-include filter pattern
- [ ] Pagination Next/Prev disabled at boundaries; has_more indicator visible
- [ ] auditService.ts uses fetchWithAuth
- [ ] 2 Vitest unit tests pass

### US-5 (chain verify badge)
- [ ] AuditChainBadge renders 3 states (loading / valid / broken)
- [ ] Mounted in AuditLogViewer header
- [ ] Re-verify button triggers refetch
- [ ] 1 Vitest unit test passes

### US-6 (4-page TanStack migration)
- [ ] 4 NEW hook files (useCostSummary / useSLAOverview / useTenantList / useTenant)
- [ ] 4 components refactored to consume hooks
- [ ] 4 Zustand stores reduced to UI-only state
- [ ] All existing Vitest tests pass unchanged
- [ ] All existing Playwright e2e tests pass unchanged
- [ ] Vite bundle JS main ≤ 280 kB
- [ ] AD-Cost-Dashboard-UseQuery formally closes

### Sprint-wide
- [ ] pytest unchanged (frontend-only sprint; ~1622 baseline maintained)
- [ ] mypy 0/300 unchanged
- [ ] 9/9 V2 lints green
- [ ] Vitest 57 → ≥65 (+8 from 7 NEW unit tests; +1 ApprovalsPage smoke = ≥+8)
- [ ] Playwright 27 → ≥31 (+4 from governance e2e)
- [ ] LLM SDK leak 0
- [ ] Day 0 三-prong (Path + Content + Schema N/A) catalogued in progress.md
- [ ] AD-Cost-Dashboard-UseQuery closes (US-6 deliverable)
- [ ] AD-Front-1 polling-vs-SSE Sprint 53.5 deferred — TanStack refetchInterval is interim solution; SSE upgrade still candidate Phase 58.x carryover (NOT closed by this sprint)

---

## Deliverables (checklist mapping)

| Day | Deliverable |
|-----|-------------|
| Day 0 | Branch + Day 0 三-prong + calibration commit |
| Day 1 | US-1 AppShellV2 wrap + auth gate + 2-tab routes + US-2 Tailwind migration (3 components) |
| Day 2 | US-3 TanStack governance hooks + ApprovalsPage/DecisionModal refactor + governanceService fetchWithAuth |
| Day 3 | US-4 AuditLogViewer + auditService + useAuditLog + US-5 AuditChainBadge |
| Day 4 (or Day 3 stretch) | US-6 4-page TanStack migration + closeout sweep + retrospective + memory + 4 doc syncs + PR |

---

## Dependencies & Risks

### Dependencies

- Sprint 57.8 AppShellV2 architecture ✅ MERGED (`caf95706`)
- Sprint 57.7 IAM `isAuthenticated()` + `setPostLoginRedirect()` + `fetchWithAuth()` ✅ MERGED
- Sprint 57.7 TanStack Query install + main.tsx Provider wire ✅ MERGED (US-B2)
- Sprint 53.5 governance backend (`/governance/approvals` GET + POST decide) ✅ MAIN
- Sprint 53.5 audit backend (`/audit/log` paginated + `/audit/verify-chain`) ✅ MAIN
- Sprint 53.5 governance frontend ApprovalsPage / ApprovalList / DecisionModal / governanceService ✅ MAIN
- Sprint 57.8 routes.config.ts (governance entry exists with `active: false` placeholder) ✅ MERGED

### Risks

| ID | Risk | Mitigation |
|----|------|------------|
| **A** | Sprint 53.5 governance components have hidden coupling that breaks during Tailwind migration (e.g. inline style sets specific px values needed for layout) | Day 1 carefully migrate ONE component at a time + run Vitest after each; if regression surfaces in DecisionModal modal positioning, document delta + use Tailwind arbitrary values (`top-[2rem]` etc.) |
| **B** | TanStack `useMutation` + `invalidateQueries` may double-fetch if user clicks Approve rapidly (race vs refetchInterval) | Use mutation `onSuccess` + `qc.cancelQueries` before invalidate; document mutation idempotency in hook docstring |
| **C** | shadcn `<Dialog>` adds ~15-20 kB bundle weight; DecisionModal previously 192 LOC inline impl | Day 1 Prong 2 grep `Dialog` usage in existing components — if NOT used elsewhere, prefer Tailwind impl (`fixed inset-0` + portal pattern) over shadcn primitive to avoid bundle weight; mirror Sprint 57.8 UserMenu YAGNI decision |
| **D** | `fetchWithAuth` adds Bearer header but backend governance/audit endpoints require specific JWT claims (`tenant_id` + `roles`); 57.7 IAM JWT shape may differ from 53.5 expected | Day 0 Prong 2 grep both 57.7 `_to_internal_jwt` claims output + 53.5 `require_approver_role` / `require_audit_role` JWT claim checks; if mismatch surfaces, scope expands to claim mapping fix (~1-2 hr) — flag as Day 0 D-finding RED |
| **E** | Audit log volume in dev DB may be empty (no fixture) → AuditLogViewer empty state always shown; Playwright e2e cases need mocked SSE/REST | Mock `auditService.fetchAuditLog` via Playwright `page.route()` (mirror Sprint 53.6 D11 + 57.8 D11 mocking pattern); document mock fixture in `tests/e2e/fixtures/audit-fixtures.ts` |
| **F** | TanStack 4-page migration may break existing Playwright e2e tests if `data-testid` / accessible queries depend on Zustand selector timing (mount-then-load pattern) | Day 4 closeout: run full Playwright sweep BEFORE pushing; if regressions surface, revert offending page to Zustand pattern + log AD for follow-up |
| **G** | `mixed-pattern-reuse` calibration class is in proposal status (AD-Sprint-Plan-6); 1st application uncertainty (similar to Sprint 57.8 `frontend-arch-spike` 0.50 1st-app surprised at 1.50 over band) | Use HYBRID 0.50 weighted blend (mirrors Sprint 57.7 `iam-frontend-spike` 0.60 + 57.8 `frontend-arch-spike` 0.50 hybrid pattern); document delta in Day 4 retro Q2 |
| **H** | Day 4 closeout pytest scope discipline (Sprint 57.7 D19 + 57.8 D13 lessons) | Day 4 closeout MUST run **full** Playwright + Vitest + pytest + 9 V2 lints + 3 backend lint sweep before pushing — not subset |
| **I** | admin-tenants page file path unknown until Day 0 grep (US-6 dependency) | Day 0 Prong 1 path verify `frontend/src/features/admin-tenants/` + `pages/admin-tenants/`; document actual file structure for hook integration target |

### Sprint 57.7 + 57.8 lesson carry-forward (mandatory)

Per Sprint 57.7 PR #116 5 CI fix commits + Sprint 57.8 D13 dev DB pollution discovery:

- **Day 4 closeout pytest scope** — full `python -m pytest`, NOT `tests/unit/` only
- **Pre-push lint sweep** — full `python -m flake8 src tests` + `black --check src tests` + `isort --check-only src tests` before EVERY push
- **Dev DB cleanup** — Sprint 57.8 D13 surfaced leftover test rows in dev DB causing -4 pytest baseline drift; Day 0 baseline capture should note any pre-existing test pollution + clean OR document delta

These are committed as Sprint 57.9 retrospective Q3 lesson carry-forward; `sprint-workflow.md` §Step 5 expansion is candidate Phase 58+ AD if pattern holds.

---

## Workload (calibrated)

### Bottom-up estimate

| Story | LOC est | Hours |
|-------|---------|-------|
| US-1 governance AppShellV2 + auth gate + 2-tab routes | ~80 src | ~1 hr |
| US-2 Tailwind migration (3 components) | ~3 × ~30 LOC swap | ~2 hr |
| US-3 TanStack governance hooks + refactor + governanceService swap + 3 tests | ~150 src + ~120 tests | ~3 hr |
| US-4 audit log viewer + service + hook + 2 tests | ~280 src + ~90 tests | ~4 hr |
| US-5 chain verify badge + auditService extension + 1 test | ~80 src + ~40 tests | ~1.5 hr |
| US-6 4-page TanStack migration (4 hooks + 4 component refactors + 4 store reductions) | ~130 NEW + ~120 swap | ~6 hr |
| Day 0 三-prong + Day 4 closeout overhead | — | ~4.5 hr |
| **Total** | **~1080 LOC** | **~22 hr** |

### Calibration: HYBRID `frontend-feature-with-migration` 0.50 (NEW class proposal)

Per Sprint 57.7 `iam-frontend-spike` 0.60 + Sprint 57.8 `frontend-arch-spike` 0.50
HYBRID precedent. NEW class baseline 0.50 mid-blend.

**Bottom-up est ~22 hr → calibrated commit ~11 hr (multiplier 0.50)**

Round to **~10.5 hr** mid-band budget.

### Calibration class proposal (extends AD-Sprint-Plan-10)

NEW class `frontend-feature-with-migration` baseline 0.50 — opens with this sprint's
1-data-point. Pending 2-3 sprint window evidence; potential split if Phase 57.10
(verification ship) reuses same governance-ship + cross-cutting-migration pattern.

If accepted as 1st-application baseline, Sprint 57.9 retrospective Q2 records ratio:

```
ratio = actual_hours / 10.5
- in-band [0.85, 1.20] → KEEP 0.50
- below 0.85 → re-eval as 0.40 next sprint
- above 1.20 → re-eval as 0.60 next sprint
```

---

## Open questions for user (pending plan approval)

1. **Branch name** — `feature/sprint-57-9-governance-ship-tquery-migration` confirmed (per Q1 user select A)
2. **Audit log viewer UI** — Filter form + paginated table confirmed (per Q2 user select A)
3. **Tab UX** — URL-based 2 sub-routes (`/governance/approvals` + `/governance/audit-log`) confirmed (per Q3 user select A)
4. **NEW calibration class `frontend-feature-with-migration`** — 0.50 1st-app baseline confirmed (per Q4 user select A)
5. **shadcn `<Dialog>` vs Tailwind Modal for DecisionModal** — pending Day 0 Prong 2 bundle-weight grep; default Tailwind impl per YAGNI
6. **AD-Cost-Dashboard-UseQuery scope** — close fully (all 4 pages + governance) OR partial (governance only, defer cost-dashboard per inertia)? Default: close fully per Q2-C user choice
