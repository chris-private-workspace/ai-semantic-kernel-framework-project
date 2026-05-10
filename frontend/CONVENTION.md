# Frontend Convention

> **Operational rules** for V2 frontend development. For design philosophy + page roadmap,
> see [`docs/03-implementation/agent-harness-planning/16-frontend-design.md`](../docs/03-implementation/agent-harness-planning/16-frontend-design.md).
> For visual + UX style rules, see [`STYLE.md`](./STYLE.md).

**Created**: 2026-05-09 (Sprint 57.10 codified from Sprint 57.7+57.8+57.9 emergent patterns)
**Last Modified**: 2026-05-10
**Status**: Active

> **Modification History (newest-first)**
> - 2026-05-10: Sprint 57.14 post-merge — §8 visual-baseline note: job opens a PR (was: direct push to protected main; FIX-008)
> - 2026-05-10: Sprint 57.14 — §8 add "hermetic API mocking" + "visual regression baselines" sub-sections (AD-Frontend-E2E-Sweep / AD-Visual-Baseline-Generation)
> - 2026-05-10: Sprint 57.13 — add §10 design-system / §11 i18n / §12 a11y / §13 performance
> - 2026-05-09: Initial creation (Sprint 57.10 — closes convention drift identified by user 2026-05-09 reality check)

---

## Purpose

Frontend conventions historically lived as "documented-by-precedent" — each new sprint's
plan + checklist had to be grep'd from history to absorb patterns. This caused drift
(e.g. D-PRE-13 in Sprint 57.10 Day 0 探勘 found chat-v2 silently dropping verification SSE
events for 3+ sprints because no one codified the chatStore.mergeEvent reducer + KNOWN
event filter contract).

This document codifies emergent patterns from Sprint 57.7 (IAM + frontend foundation),
Sprint 57.8 (AppShellV2 architecture + chat-v2 real ship), and Sprint 57.9 (governance
real ship + TanStack Query 4-page migration) into 9 operational sections. Future
sprints reference this doc instead of grep-ing 6-8 sprint commits.

---

## 1. Page Architecture Pattern

**Every `active: true` route in `routes.config.ts` MUST be auth-gated** (Sprint 57.13 US-A2 —
no `active` page renders for an unauthenticated visitor). Wrap the page in `<RequireAuth>`
then `<AppShellV2>`:

```tsx
import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";

export default function MyPage(): JSX.Element {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="My Page">
        {/* page content */}
      </AppShellV2>
    </RequireAuth>
  );
}
```

`<RequireAuth>` reads `authStore.status` (resolved on app mount by `<AuthBootstrap>` in
`App.tsx` via `GET /auth/me`): `unknown` → loading spinner (don't redirect before bootstrap
finishes — flashes /auth/login); `anonymous` → `setPostLoginRedirect(path)` + `<Navigate
to="/auth/login?redirect_to=...">`; `authenticated` → renders children. (Pre-Sprint-57.13
pages did the 3-branch logic inline via `isAuthenticated()`; that's been centralized.)

**Role-gated pages** (e.g. admin-tenants — platform-admin only): wrap in `<RequireAuth>`,
then inside check `useAuthStore((s) => s.roles)` and render a "needs permission" notice
instead of mounting the data hooks (so they don't fire a 403). Don't put role logic in
`<RequireAuth>` itself.

**Tenant-scoped pages** (cost-dashboard / sla-dashboard / tenant-settings): read the
tenant id from `useAuthStore((s) => s.tenant?.id ?? "")` — NOT from a URL `?tenant_id=`.
Inside `<RequireAuth>`, `tenant` is always set.

### Sub-routes (tabs)

For pages with tabs (governance / verification), use nested Routes inside the AppShellV2
(per Sprint 57.9 governance pattern):

```tsx
<AppShellV2 pageTitle="Governance">
  <nav className="mb-4 flex gap-2 border-b border-border">
    <NavLink
      to="approvals"
      className={({ isActive }) =>
        `px-4 py-2 text-sm font-medium ${
          isActive
            ? "border-b-2 border-primary text-primary"
            : "text-muted-foreground hover:text-foreground"
        }`
      }
    >
      Pending Approvals
    </NavLink>
    <NavLink to="audit-log" className={...}>Audit Log</NavLink>
  </nav>
  <Routes>
    <Route index element={<Navigate to="approvals" replace />} />
    <Route path="approvals" element={<ApprovalsPage />} />
    <Route path="audit-log" element={<AuditLogViewer />} />
  </Routes>
</AppShellV2>
```

### Page-level h1 ownership lesson (Sprint 57.8 D9 architectural fix)

`AppShellV2` already renders the page title as h1 via `pageTitle` prop. **Inner components
MUST NOT render their own h1** — doing so causes accessibility / SEO cascade conflict.

❌ **Wrong** (Sprint 57.8 SLAOverview + TenantSettingsView pre-fix):
```tsx
<AppShellV2 pageTitle="SLA Dashboard">
  <SLAOverview />  {/* internally renders <h1>SLA</h1> — duplicates pageTitle */}
</AppShellV2>
```

✅ **Right**:
```tsx
<AppShellV2 pageTitle="SLA Dashboard">
  <SLAOverview />  {/* uses h2 / h3 internally */}
</AppShellV2>
```

### Auth gate ordering rule

`<RequireAuth>` MUST be the OUTERMOST wrapper (outside `<AppShellV2>`). Putting the gate
inside AppShellV2 leaks the chrome (sidebar / user menu) to logged-out / still-bootstrapping
viewers. (Pre-57.13 the equivalent rule was "the `isAuthenticated()` early return must come
before the AppShellV2 wrap".)

---

## 2. features/&lt;X&gt;/ Folder Convention

Every feature lives under `frontend/src/features/<feature-name>/` with this fixed
sub-folder structure (per Sprint 57.3 tenant-settings + Sprint 57.7 cost-dashboard +
Sprint 57.9 governance):

```
frontend/src/features/<feature>/
├── types.ts              ← TypeScript interfaces / type unions / enum-like literals
├── services/
│   └── <feature>Service.ts  ← REST API client (fetchWithAuth wrapper)
├── hooks/
│   ├── use<X>.ts            ← TanStack Query hooks (one per logical query)
│   └── use<Y>Save.ts        ← TanStack Mutation hooks (one per logical mutation)
├── components/
│   ├── <ComponentName>.tsx  ← React components
│   └── ...
└── store/                ← Optional; only if feature needs UI-only client state
    └── <feature>Store.ts    ← Zustand store (see §4)
```

### 11 範疇 mapping (reference)

The features/ folder structure mirrors `16-frontend-design.md §159-220` 11 範疇 layout.
Some folders are stubs awaiting implementation:

| 範疇 | Folder | Status |
|------|--------|--------|
| Cat 1 Orchestrator | `features/orchestrator-loop/` | ❌ Stub (LoopVisualizer / TurnIndicator planned) |
| Cat 2 Tools | `features/tools/` | ❌ Stub (ToolPicker / SandboxLevelIndicator planned) |
| Cat 3 Memory | `features/memory/` | ❌ Stub (MemoryLayerViewer / MemorySearchPanel planned) |
| Cat 7 State Mgmt | `features/state-mgmt/` | ❌ Stub (CheckpointTimeline / TimeTravelControls planned) |
| Cat 9 Guardrails (HITL split) | `features/guardrails/` (stub) + `features/governance/` (✅ Sprint 57.9) | Partial |
| Cat 10 Verification | `features/verification/` | ❌ Stub (Sprint 57.11+ candidate per AD-Verification-RealShip-Deferred) |
| Cat 11 Subagent | `features/subagent/` | ❌ Stub (SubagentTree / HandoffArrow planned) |
| §HITL | `features/governance/` (combined with audit) | ✅ Sprint 57.9 ship |

### Feature naming convention split (project convention)

- `features/` uses **snake_case** (e.g. `features/chat_v2/`)
- `pages/` uses **kebab-case** (e.g. `pages/chat-v2/`)

This split is intentional and originates pre-Sprint 57. New features follow this
convention; do NOT mix.

### Imports between features

- ✅ Allowed: any feature can import `features/auth/services/authService` (used universally)
- ✅ Allowed: shared types from `@/components/AppShellV2` etc.
- ❌ Forbidden: cross-feature components (e.g. `governance` should not import a `cost-dashboard` component)
- ⚠️ Exception: shared sub-components live in `features/<feature>/components/` of the OWNER feature (e.g. `VerifierTypeBadge` lives in `features/verification/` and is imported by chat-v2 inline panel)

---

## 3. Routing Convention

All routes are declared in **`frontend/src/routes.config.ts`** as a single-source registry
(per Sprint 57.8 US-3). `App.tsx` generates `<Route>` elements via
`.filter(active && component).map()`. Sidebar nav links are also generated from the same
registry, grouped by `category`.

### Route entry shape

```ts
// frontend/src/routes.config.ts
import { ShieldCheck, Activity, ... } from "lucide-react";

export interface RouteEntry {
  name: string;          // displayed in sidebar
  path: string;          // base path (no trailing slash)
  icon?: LucideIcon;     // sidebar icon
  category: "operations" | "admin" | "settings" | "auth";
  active: boolean;       // false = placeholder, NOT included in App.tsx routes
  component?: () => Promise<{ default: ComponentType }>;  // lazy import
}

export const routes: RouteEntry[] = [
  {
    name: "Governance",
    path: "/governance",
    icon: ShieldCheck,
    category: "admin",
    active: true,
    component: () => import("./pages/governance"),
  },
  {
    name: "Verification",
    path: "/verification",
    icon: ShieldAlert,
    category: "operations",
    active: false,  // ← placeholder; Sprint 57.11+ flips to true
    // component omitted while active=false
  },
  // ... 11 entries total per Sprint 57.8
];
```

### Lazy import is mandatory

All page components are lazy-imported via `component: () => import("./pages/X")`.
Bundle splits per page → faster initial load. App.tsx wraps with `<Suspense>` for
loading state.

### Sidebar generation

`Sidebar.tsx` reads `routes.config.ts` and groups entries by `category`. New page =
add 1 entry to routes.config.ts → sidebar updates automatically.

### Page-internal sub-routes (tabs)

Sub-routes like `/governance/approvals` and `/governance/audit-log` are NOT in
routes.config.ts — they live as nested `<Route>` inside the page component (see §1).

---

## 4. State Management Convention

V2 frontend uses **two state systems** with strict separation (per Sprint 57.9 US-6
4-page TanStack migration):

### Server state → TanStack Query

Anything fetched from backend API (lists / detail / mutations) lives in TanStack Query.
Never duplicate server state into Zustand. See §5 for full TanStack Query convention.

### UI-only state → Zustand

Filter form draft, modal open/close, expanded section, current month picker, etc.
Zustand stores after Sprint 57.9 migration are reduced to **UI-only state**.

### Pre-57.9 anti-pattern (FIXED)

Pre-Sprint 57.9 stores held server state via `loadData() / data / loading / error`
fields + `useEffect` in components. This pattern is now **forbidden** — server state
goes through TanStack Query exclusively.

❌ **Wrong** (pre-57.9):
```ts
// store/myStore.ts
type MyStore = {
  data: MyData | null;       // ← server state in store
  loading: boolean;          // ← server state in store
  error: string | null;      // ← server state in store
  loadData: () => Promise<void>;  // ← imperative fetch
  filter: { status?: string };
  setFilter: (f) => void;
};
```

✅ **Right** (post-57.9):
```ts
// store/myStore.ts
type MyStore = {
  filter: { status?: string };       // ← UI-only
  setFilter: (f: Partial<Filter>) => void;
  reset: () => void;
};
// ... server state moved to features/<feature>/hooks/useMyData.ts (TanStack)
```

### Store API surface assertion sentinel test

Every Zustand store reduced post-57.9 has a sentinel test verifying it does NOT have
forbidden fields (per Sprint 57.9 D-PRE-15):

```ts
// tests/unit/<feature>/<feature>Store.test.ts
it("store API surface is UI-only (no data/loading/error/save/saving/loadData)", () => {
  const state = useMyStore.getState();
  expect(state).not.toHaveProperty("data");
  expect(state).not.toHaveProperty("loading");
  expect(state).not.toHaveProperty("error");
  expect(state).not.toHaveProperty("save");
  expect(state).not.toHaveProperty("saving");
  expect(state).not.toHaveProperty("loadData");
});
```

---

## 5. Server State Convention (TanStack Query)

### `*_QUERY_KEY_BASE` single-source export pattern (Sprint 57.9 US-3)

Every query hook exports a `*_QUERY_KEY_BASE` constant (`as const` tuple) for use as
the queryKey base AND for invalidation across the app.

```ts
// features/governance/hooks/useApprovals.ts
import { useQuery } from "@tanstack/react-query";
import { governanceService } from "../services/governanceService";

export const APPROVALS_QUERY_KEY = ["governance", "approvals"] as const;

export function useApprovals() {
  return useQuery({
    queryKey: APPROVALS_QUERY_KEY,
    queryFn: ({ signal }) => governanceService.listPending(signal),
    refetchInterval: 30_000,
  });
}
```

### Mutation with onSuccess invalidation

Mutations import the query key constant and invalidate after success:

```ts
// features/governance/hooks/useApprovalDecide.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { governanceService } from "../services/governanceService";
import { APPROVALS_QUERY_KEY } from "./useApprovals";

export function useApprovalDecide() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: DecideArgs) =>
      governanceService.decide(args.id, args.decision, args.reason),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: APPROVALS_QUERY_KEY });
    },
  });
}
```

### Paginated query convention (`*_QUERY_KEY_BASE` + filter spread)

For paginated / filtered queries, the queryKey includes the filter object so query
auto-refetches on filter change:

```ts
export const ADMIN_TENANTS_QUERY_KEY_BASE = ["admin-tenants"] as const;

export function useAdminTenants(filter: TenantListFilter) {
  return useQuery({
    queryKey: [...ADMIN_TENANTS_QUERY_KEY_BASE, filter],
    queryFn: ({ signal }) => adminTenantsService.fetchList(filter, signal),
    keepPreviousData: true,  // smooth pagination UX
  });
}
```

### Conditional query (`enabled` gate)

For queries that depend on user-provided values (e.g. session_id from URL), use
`enabled: !!value` so query waits until the value is provided:

```ts
export function useCorrectionTrace(sessionId: string | null) {
  return useQuery({
    queryKey: [...CORRECTION_TRACE_QUERY_KEY_BASE, sessionId],
    queryFn: () => verificationService.fetchCorrectionTrace(sessionId!),
    enabled: !!sessionId,
  });
}
```

### QueryClient global config

`main.tsx` configures QueryClient with SaaS-friendly defaults (per Sprint 57.9 US-6):

```ts
// frontend/src/main.tsx
const qc = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,              // surface failures immediately + per-page Retry button
      refetchOnWindowFocus: false,  // chat / dashboard don't auto-refetch
      staleTime: 30_000,
    },
    mutations: { retry: false },
  },
});
```

---

## 6. API Service Convention

### `fetchWithAuth` import path (Sprint 57.7 US-A2)

`fetchWithAuth` is exported from `features/auth/services/authService.ts` (NOT a
separate `fetchWithAuth.ts` file). It wraps `fetch` to inject the IAM JWT Bearer
header + `credentials: "include"`:

```ts
import { fetchWithAuth } from "@/features/auth/services/authService";

export async function fetchAuditLog(filter: AuditLogFilter) {
  const params = buildSearchParams(filter);  // omit-undefined helper
  const res = await fetchWithAuth(`/api/v1/audit/log?${params}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}
```

### URLSearchParams omit-undefined helper

Filter forms with optional fields use the canonical `buildSearchParams` helper that
omits undefined keys (avoids sending `?key=undefined` query strings):

```ts
function buildSearchParams(filter: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(filter)) {
    if (v !== undefined && v !== null && v !== "") {
      params.set(k, String(v));
    }
  }
  return params.toString();
}
```

### Error throwing convention

Always throw `Error` with the backend's `detail` message on non-2xx responses; let
TanStack Query surface it via `error` field:

```ts
if (!res.ok) {
  const detail = await res.json().catch(() => ({}));
  throw new Error(detail.detail ?? `HTTP ${res.status}: ${res.statusText}`);
}
```

### Service test convention

Service tests use `expect.objectContaining({ credentials: "include" })` to assert
fetchWithAuth wrap (per Sprint 57.9 D-PRE-15 codified):

```ts
expect(fetchSpy).toHaveBeenCalledWith(
  "/api/v1/audit/log?status=pending",
  expect.objectContaining({ credentials: "include" }),
);
```

---

## 7. SSE Event Convention (CRITICAL)

> **D-PRE-13 lesson (Sprint 57.10 Day 0 探勘)**: chat-v2 silently dropped backend
> verification_passed/failed SSE events for 3+ sprints (54.1 → 57.9) because adding
> a NEW SSE event variant requires **3 coordinated edits** that were never documented.
> This section codifies the pattern.

### chatStore.mergeEvent reducer single-point switch

All SSE events flow through `features/chat_v2/store/chatStore.ts:mergeEvent`. There
is ONE switch on `ev.type` that handles every known event variant. Hooks like
`useLoopEventStream` are just `streamChat + mergeEvent` wrappers — they do NOT route
events.

### KNOWN_LOOP_EVENT_TYPES set + parseSSEFrame filter

`chatService.parseSSEFrame` filters out unknown event types per
`types.ts:130-133` docstring:

> Unknown event types from later phases are filtered at the SSE parser
> (chatService.parseSSEFrame returns null) so the store never sees them —
> preserving discriminated-union narrowing inside mergeEvent's switch.

This means **adding a NEW SSE event variant requires 3 edits**:

1. **`features/chat_v2/types.ts`**:
   - Define new `<EventName>Event` interface with `type: "snake_case"` + `data` shape
   - Add to `LoopEvent` discriminated union
   - Add type-name string to `KNOWN_LOOP_EVENT_TYPES` set

2. **`features/chat_v2/store/chatStore.ts`**:
   - Add new `case "snake_case": { ... return { ...s, rawEvents, <slice> }; }` branch in `mergeEvent` switch

3. **(Optional) `features/<feature>/components/<EventConsumer>.tsx`**:
   - If event drives UI beyond `rawEvents` log, add component subscribing to chatStore selector

### Backend SSE event payload mapping

Backend `serialize_loop_event` in `backend/src/api/v1/chat/sse.py` maps Python
LoopEvent dataclass instances to `{ type: "snake_case", data: {...} }` shape.
Frontend must mirror exactly OR parseSSEFrame filters as unknown.

### Audit checklist when adding new SSE event

- [ ] Backend emits new event in agent_harness with proper LoopEvent dataclass
- [ ] Backend `sse.py` adds `isinstance(event, NewEvent)` branch to `serialize_loop_event`
- [ ] Frontend `types.ts` adds Event interface + LoopEvent union variant + KNOWN set entry
- [ ] Frontend `chatStore.ts` adds case branch in mergeEvent
- [ ] (Optional) Component subscribes to chatStore selector if UI drives off event
- [ ] Test: assert chatStore.mergeEvent processes new event type correctly

---

## 8. Test Convention

### Vitest unit tests

Location: `frontend/tests/unit/<feature>/<file>.test.{ts,tsx}` mirroring src structure.

Conventions:
- Import production code via `@/` path alias (NOT relative imports for src access)
- Use `describe` + `it` (not `test`) for consistency
- For TanStack hooks tests, wrap with `<QueryClientProvider client={qc}>` per test using a `makeWrapper()` helper

Example wrapper:
```tsx
function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}
```

### Playwright e2e tests

Location: `frontend/tests/e2e/<feature>-real-ship.spec.ts` (per Sprint 57.9 governance
naming convention).

For auth-gated pages, **always use `seedAuthJwt(page)` in `beforeEach`** (per Sprint
57.9 D-PRE-16 lesson — governance auth gate broke 5 prior e2e silently because beforeEach
JWT seed was missing):

```ts
import { test, expect } from "@playwright/test";
import { seedAuthJwt } from "../helpers/auth";

test.describe("Verification real ship", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthJwt(page);  // ← MUST for any auth-gated page
  });

  test("happy path renders 2 mocked rows", async ({ page }) => {
    await page.route("**/api/v1/verification/recent**", (route) =>
      route.fulfill({ json: { items: [...], total: 2, has_more: false } }),
    );
    await page.goto("/verification/recent");
    await expect(page.getByText("First verifier")).toBeVisible();
  });
});
```

### StrictMode mock pattern (`retryClicked` flag — Sprint 57.9 D-PRE-15)

React StrictMode double-renders in dev / tests. TanStack Query hooks fire `queryFn`
twice on mount → naive mock with `firstCall` flag becomes unreliable.

❌ **Wrong** (brittle):
```ts
let firstCall = true;
await page.route("**/api/v1/x", (route) => {
  if (firstCall) {
    firstCall = false;
    return route.fulfill({ status: 500 });
  }
  return route.fulfill({ json: { ... } });
});
```

✅ **Right** (robust under StrictMode):
```ts
let retryClicked = false;
await page.route("**/api/v1/x", (route) => {
  if (!retryClicked) {
    return route.fulfill({ status: 500 });
  }
  return route.fulfill({ json: { ... } });
});
// ... then in test:
await page.getByRole("button", { name: "Retry" }).click();
retryClicked = true;
// next click triggers refetch with success response
```

Pattern: gate mock behavior on a **user-action flag** (button click / explicit
trigger), not on call count. Survives any number of StrictMode double-renders.

### Hermetic API mocking (mock the catch-all, not just one route)

E2e specs run against the Vite dev server, which proxies `/api/**` to a backend
on `:8000` that may or may not be running locally. If a spec mocks only *some*
endpoints (e.g. `/api/v1/auth/me`) the rest fall through to the proxy → the real
backend (if up) sees no JWT → **401** → `fetchWithAuth`'s `handleAuthExpired()`
does `window.location='/auth/login'` → the page under test navigates away. So a
spec that walks several routes must mock **everything** under `/api/v1/**`, not
just the auth endpoint (Sprint 57.14 — `a11y-scan.spec.ts` was red locally for
exactly this reason). Pattern: register the catch-all first, the specific routes
after (the most-recently-registered matching handler wins):

```ts
await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "e2e mock" } }));
await page.route("**/api/v1/auth/me", (r) => r.fulfill({ status: 200, json: mockAuthMe }));
// /auth/me → 200 (specific, last-registered wins); everything else → 503 (catch-all)
```

After `page.goto(route)` for a page that may client-redirect (e.g. `/verification`
→ `/verification/recent`), `await page.waitForLoadState("networkidle")` before any
`AxeBuilder().analyze()` or screenshot — otherwise "Execution context was destroyed,
most likely because of a navigation" if the SPA route changes mid-call.

### Visual regression baselines (Sprint 57.14 — `visual-regression.spec.ts`)

`tests/e2e/visual/visual-regression.spec.ts` does `expect(page).toHaveScreenshot(...)`
against fixed-data renders. Its baselines (`visual-regression.spec.ts-snapshots/*.png`)
**MUST be generated on the Linux CI runner, never a dev machine** — font hinting / DPI
differ across OSes, so Windows/macOS-generated PNGs would all mismatch in CI.

- The spec **auto-skips** until the `-snapshots/` dir is committed (its guard does
  `existsSync(...)`), so push/PR e2e is never red on a missing baseline. Once the dir
  lands, the spec runs as part of the regular `e2e` job on every push/PR.
- To **regenerate** baselines (after a UI change that legitimately moves the
  screenshots): run the **`visual-baseline` job** in
  `.github/workflows/playwright-e2e.yml` (GitHub → Actions → "Playwright E2E" → Run
  workflow). It runs `RUN_VISUAL=1 playwright test visual --update-snapshots` on
  `ubuntu-latest` and opens a `chore/visual-baselines-<run_id>` PR with the updated
  `-snapshots/` dir (a human reviews/merges it — direct push to protected `main` is
  rejected; the run also uploads the PNGs as a `visual-baselines` artifact as a fallback).
- Locally on **Linux/WSL only** you can preview with `npm run e2e:visual:update` (the
  output PNGs match CI). **Do NOT commit Windows/macOS-generated baselines.**
- `.gitattributes` marks `*.png binary` so diffs aren't line-mangled.

### Sentinel tests (regression preservation)

After major refactors (e.g. Sprint 57.9 4-page TanStack migration), keep / add
sentinel tests asserting the new architecture invariant:
- Store API surface assertion (see §4)
- `*_QUERY_KEY_BASE` constant export verified

---

## 9. File Header MHist Convention

All TypeScript / TSX files use the project file header convention codified in
[`.claude/rules/file-header-convention.md`](../.claude/rules/file-header-convention.md):

```tsx
/**
 * File: frontend/src/features/<feature>/components/<Component>.tsx
 * Purpose: One-line purpose.
 * Category: Frontend / <feature> / components
 * Scope: Phase XX / Sprint XX.Y US-N
 *
 * Created: YYYY-MM-DD (Sprint XX.Y Day N)
 * Last Modified: YYYY-MM-DD
 *
 * Modification History:
 *   - YYYY-MM-DD: Sprint XX.Y - <verb> <scope> (closes AD-Foo if applicable)
 */
```

### MHist 1-line max rule

Each Modification History entry is **one line, ≤ 100 chars (E501)** including the
4-space indent. Sprint 55.3+ rule per file-header-convention.md.

❌ **Wrong** (multi-paragraph reason):
```
- 2026-05-09: Sprint 57.10 - add VerificationPanel
    This change introduces inline panel because chat-v2 was silently
    dropping verification_passed/failed events ... [paragraph]
```

✅ **Right** (one line):
```
- 2026-05-09: Sprint 57.10 - add VerificationPanel (closes D-PRE-13 SSE silent drop)
```

Detailed reasoning belongs in commit message body / `claudedocs/4-changes/FIX-XXX-*.md`,
NOT in MHist. Git log preserves the rich detail.

---

## 10. Design System Component Layer (`components/ui/`)

Since Sprint 57.13 US-B2 the loading / empty / error / button / badge / card primitives
live in `src/components/ui/` (shadcn-style; barrel `src/components/ui/index.ts`).

### Rule: feature pages MUST use `components/ui/` for loading / empty / error

| Need | Use | NOT |
|------|-----|-----|
| Page-level table loading | `<TableSkeleton rows cols>` (or `<Skeleton className="h-N">` rows inside an existing `<tbody>`) | bespoke `<div className="h-4 animate-pulse rounded bg-muted">` |
| Dashboard card loading | `<CardSkeleton count>` | a `<p>Loading…</p>` spinner-text |
| 0-items state | `<EmptyState title message? icon? action?>` | bare `<p>No data</p>` |
| Query `isError` (page-level) | `<ErrorRetry error onRetry={() => refetch()}>` | inline `Error: {message}` + hand-rolled retry button |
| Mutation failure (non-blocking) | `toastError(...)` from `lib/toast` (wired via `lib/queryClient` `mutationCache.onError`) | inline alert div |
| Button | `<Button variant size asChild?>` | raw `<button className="...">` for new code |
| Status pill (incl. risk levels) | `<Badge variant>` (`risk-low`/`-medium`/`-high`/`-critical` per STYLE.md §3) | new bespoke pill markup |
| Modal dialog | `<Dialog open onOpenChange><DialogContent>…</DialogContent></Dialog>` (Radix — focus trap / ESC / outside-click free) | hand-rolled `fixed inset-0` overlay + `stopPropagation` panel |
| Dropdown / popover menu | `<DropdownMenu><DropdownMenuTrigger/><DropdownMenuContent>…</DropdownMenuContent></DropdownMenu>` (Radix) | hand-rolled `useState`/`useRef`/`useEffect`-for-outside-click popover |

`<Skeleton>` is the base pulse box — compose it freely; `<TableSkeleton>` / `<CardSkeleton>`
are the canonical compositions from STYLE.md §6. `<Dialog>` / `<DropdownMenu>` wrap
`@radix-ui/react-dialog` / `@radix-ui/react-dropdown-menu` (Sprint 57.13 US-B3 — `DecisionModal`
+ `UserMenu` are the reference consumers). The dropdown surface uses `bg-background` (no
`popover` token in this app's tailwind.config). Vitest of Radix primitives needs the jsdom
polyfills in `tests/unit/setup.ts` (`hasPointerCapture` / `scrollIntoView` / `ResizeObserver`)
+ `@testing-library/user-event` (not `fireEvent`) to drive open/close.

### shadcn pattern note

`button.tsx` / `badge.tsx` export both the component and its `cva` `*Variants` — they carry
a file-level `/* eslint-disable react-refresh/only-export-components */` (standard shadcn;
the variants must be importable for `cn(buttonVariants(...), className)` composition).

### Existing per-feature badges

`AuditChainBadge` / `VerifierTypeBadge` / `MemoryScopeBadge` keep their own colour logic for
now (not yet migrated to `<Badge>`). New code should reach for `<Badge>` first.

### Codification basis

Sprint 57.9 ApprovalList + admin-tenants TenantListTable established the inline-skeleton /
empty / retry shapes (≥ 2 examples); STYLE.md §6-§8 documented them; Sprint 57.13 US-B2
extracted them into reusable components and adopted `<Skeleton>` across governance / verification
/ memory + `<TableSkeleton>`/`<EmptyState>` in admin-tenants + `<CardSkeleton>`/`<ErrorRetry>`
in cost / sla dashboards.

---

## 11. i18n Convention (`src/i18n/`)

Since Sprint 57.13 US-B5 the app is internationalized with **i18next + react-i18next**
(English + Traditional Chinese `zh-TW`). Bootstrap: `src/i18n/index.ts` (imported once
from `main.tsx` *before* render — synchronous since resources are bundled JSON, so no
`<Suspense>` boundary needed; `react.useSuspense: false` is set explicitly).

### Rules

| Need | Do | NOT |
|------|-----|-----|
| User-facing string in a component | `const { t } = useTranslation("common")` (or `"auth"`) → `{t("nav.costDashboard")}` | hard-coded English literal |
| Sidebar nav label | add `nameKey` to the `routes.config.ts` entry → `Sidebar` renders `t(entry.nameKey, entry.name)` (the `name` is the dev/debug fallback) | `entry.name` directly |
| New string | add the key to **both** `src/i18n/locales/en/<ns>.json` and `…/zh-TW/<ns>.json` (same key set — `i18n.test.ts` enforces parity) | add to `en` only |
| Interpolation | `t("devSection.errorFailed", { status })` ↔ JSON `"dev-login failed ({{status}})"` | string concat |
| Change locale | the `<UserMenu>` switcher items call `localStorage.setItem("ipa-locale", id)` + `i18n.changeLanguage(id)` (detector also caches it) | a custom locale store |

### Namespaces

- `common` — shell / sidebar nav (`nav.*`) / user menu / generic actions / cross-page bits
- `auth` — login + callback pages (incl. dev fake-login)

Feature-page string extraction beyond `cost-dashboard` + `verification` (the 2 demo
adopters) is a follow-up (`AD-i18n-Feature-Namespaces`) — add a `<feature>` namespace
when a page is migrated.

### Extraction tool

`npm run i18n:extract` runs `i18next-parser` (config: `i18next-parser.config.cjs` —
CommonJS on purpose since `package.json` is `"type": "module"`). It scans `src/**` for
`t(...)` calls and adds missing keys (English file: key text as default; other locales:
empty) without dropping existing translations (`keepRemoved: true`). Not run in CI — a
dev convenience; the source of truth is the hand-maintained JSON.

### Tests

`tests/unit/setup.ts` does `import "@/i18n"` so component tests render real strings (not
raw keys). A test that calls `i18n.changeLanguage(...)` MUST reset to `"en"` + clear the
`ipa-locale` localStorage key in `afterEach` (the singleton + localStorage leak across a
file's tests otherwise — see `UserMenu.test.tsx`). `i18n.test.ts` asserts en ≡ zh-TW key
parity + non-empty values + `changeLanguage` switching + interpolation + unknown-locale
fallback.

---

## 12. Accessibility Convention (a11y)

Since Sprint 57.13 US-B6, `eslint.config.js` includes `eslint-plugin-jsx-a11y`'s
recommended rule set (flat-config `jsxA11y.flatConfigs.recommended.rules`), so a11y
issues fail `npm run lint` (`--max-warnings 0`). Plus a Playwright + axe-core scan.

### Rules

| Need | Do | NOT |
|------|-----|-----|
| Clickable non-`<button>` element | a real `<button>`, OR `role="button"` + `tabIndex={0}` + `onKeyDown` (Enter/Space → same action as `onClick`) | `<div onClick>` with no keyboard handler (jsx-a11y `click-events-have-key-events` / `interactive-supports-focus`) |
| Form field | `<label htmlFor="x">` + `<input id="x">` (or nest the control inside `<label>`) | a bare `<label>` next to an `<input>` (jsx-a11y `label-has-associated-control`) |
| Heading wrapper component (e.g. `CardTitle` = `<h3 {...props}/>`) | content comes from `children` at call sites; the spread hides it from the linter → a targeted `// eslint-disable-next-line jsx-a11y/heading-has-content` with a reason is acceptable | a real empty `<h1></h1>` |
| Error / status region | `role="alert"` (already done in `<ErrorRetry>`) | a silent `<div>` |
| Decorative icon (lucide `<Icon/>`) | leave as-is (no jsx-a11y rule covers `<svg>`; lucide marks them `aria-hidden`) | `<img>` for an icon without `alt=""` |

### axe-core e2e scan

`tests/e2e/a11y/a11y-scan.spec.ts` runs `new AxeBuilder({ page }).analyze()` against
every shipped page (9 active routes with `/auth/me` mocked so `<RequireAuth>` renders
the shell + `/auth/login` + `/auth/callback?error=…`) and asserts **0 violations with
impact `critical` or `serious`** (moderate/minor are `console.warn`-ed for triage, not a
failure — baseline scope). Run via `npx playwright test a11y`. New pages MUST be added to
the route list.

---

## 13. Performance / Lighthouse Convention

Since Sprint 57.13 US-B7 there's a Lighthouse CI budget (`lighthouserc.cjs` —
CommonJS since `package.json` is `"type":"module"`, mirrors `i18next-parser.config.cjs`).
`npm run lhci` (= `lhci autorun`) builds nothing — it expects `dist/` to exist, then
`vite preview`s it and runs Lighthouse against `http://localhost:4173/auth/login` (the one
route that renders fully without auth/backend). Assertions: **accessibility ≥ 0.9 is a hard
`error` gate**; performance ≥ 0.7 / best-practices ≥ 0.8 / FCP ≤ 2000 ms / TTI ≤ 4000 ms
are `warn` (informational while the bundle is being trimmed — see `AD-Bundle-Size`).

`.github/workflows/frontend-lighthouse.yml` runs it on PRs touching `frontend/**` —
`continue-on-error: true`, so it's a budget tripwire, never a required check. Reports
upload to `temporary-public-storage` (no token). `frontend/.lighthouseci/` (run output) is
gitignored.

When you add a new public (no-auth) page, add its URL to `lighthouserc.cjs`'s `url` list.
Auth-gated pages can't be Lighthouse'd without a backend — out of scope for now.

---

## Cross-References

- Visual + UX rules → [`STYLE.md`](./STYLE.md)
- React basic rules (ESLint / TypeScript / no inline styles) → [`.claude/rules/frontend-react.md`](../.claude/rules/frontend-react.md)
- Project file header rules → [`.claude/rules/file-header-convention.md`](../.claude/rules/file-header-convention.md)
- Sprint workflow + Day 0 三-prong + calibration matrix → [`.claude/rules/sprint-workflow.md`](../.claude/rules/sprint-workflow.md)
- Frontend design philosophy + page roadmap → [`docs/03-implementation/agent-harness-planning/16-frontend-design.md`](../docs/03-implementation/agent-harness-planning/16-frontend-design.md)
- 17.md cross-category interfaces (single-source contracts) → [`docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md`](../docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md)

---

## Change Process

When a NEW pattern emerges (sprint introduces a 3rd consecutive use of a previously
ad-hoc technique), it should be added to this doc within the same sprint OR in the
next periodic Convention Drift Audit Cycle (per AD-Convention-Drift-Audit-Cycle, Phase
58.x periodic; every 4-6 sprints scan latest ships for emergent patterns NOT here).

**Threshold for codification**: pattern appears in ≥ 2 sprint examples (avoid premature
1-data-point baseline per AD-Plan-3).

**End of CONVENTION.md**
