---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-8-plan.md
Purpose: Sprint 57.8 plan — AppShell V2 + chat-v2 frontend real ship (Architecture-first frontend foundation expansion).
Category: Frontend / Architecture / chat-v2 ship
Scope: Phase 57 / Sprint 57.8

Description:
    Phase 57+ SaaS Frontend 5/N expansion. Sprint 57.7 delivered minimal AppShell
    (header + main + footer with hardcoded 3 nav links) sufficient for IAM spike.
    Sprint 57.8 expands to V1-style admin portal pattern (sidebar + collapse +
    categorized nav + user menu) and ships chat-v2 frontend integration for first
    end-to-end demo of IAM-authed real-LLM chat experience.

Created: 2026-05-10 (drafted)
Last Modified: 2026-05-10
Status: Draft (pending user approval)

Modification History (newest-first):
    - 2026-05-10: Initial creation (Sprint 57.8 drafting)

Related:
    - 16-frontend-design.md §V2 Ship Timeline (chat-v2 real ship priority slot)
    - 20-iam-deep-dive.md (Sprint 57.7 spike-extract, IAM JWT consumed by US-2)
    - sprint-57-7-plan.md (structural template per sprint-workflow.md §Step 1)
    - .claude/rules/frontend-react.md (Tailwind / shadcn / Zustand / TanStack Query rules)
---

# Sprint 57.8 — AppShell V2 + chat-v2 Frontend Real Ship (Architecture-first 5/N)

## Sprint Goal

Expand Sprint 57.7 minimal AppShell into V1-style admin portal pattern (sidebar +
collapse + categorized nav + user menu integrating Sprint 57.7 IAM), establish
single-source page registry (`routes.config.ts`) for 11 pages, migrate existing
4 pages to AppShell V2, and ship chat-v2 frontend real integration (auth gate +
SSE consume + ApprovalCard real wiring + Playwright e2e) — answering
Sprint 57.5 reality-check finding R4 (5 placeholder/未開發 pages scope decision)
and 16-frontend-design.md V2 Ship Timeline priority chat-v2 ~10-12 hr slot.

---

## Background

### Why architecture-first now

Sprint 57.7 closeout retrospective Q5 + user direction (2026-05-10 chat session):

1. **57.7 AppShell is "minimum viable spike"** — header + main + footer with 3
   hardcoded nav links (`/cost-dashboard`, `/sla-dashboard`, `/admin-tenants`).
   Designed for IAM Block A spike scope, NOT scalable to 11+ pages target.
2. **V1 admin portal pattern reference** — left sidebar (collapsible) + right
   main + categorized nav (Operations / Admin / Settings) + user profile +
   logout. Industry-standard SaaS layout pattern; users familiar.
3. **ROI** — Architecture-first 一次投資 → 11+ 頁 free benefit; vs piecemeal
   per-page migration when V1 admin portal is eventually rebuilt later.
4. **Sprint 57.5 reality-check R4** — 5 placeholder/未開發 frontend pages
   (chat-v2 / governance / verification / 等) scope decision; 57.6 deferred to
   "Phase 57.7-57.9 priority slots" per 16.md V2 Ship Timeline §section. 57.7
   delivered IAM unblock; 57.8 first ships under new architecture.

### What changed since Sprint 57.7

| Asset | 57.7 ship state | 57.8 needs |
|-------|-----------------|------------|
| `AppShell.tsx` | Header + main + footer; 3 hardcoded nav | Sidebar V2 + categorized nav + user menu |
| `App.tsx` | Routes hand-listed inline | Generated from `routes.config.ts` registry |
| `pages/chat-v2/index.tsx` | 21-line placeholder | Composed real chat ship |
| `features/chat_v2/*` | Components exist (ChatLayout / InputBar / MessageList / ToolCallCard / ApprovalCard / useLoopEventStream / chatService / chatStore) | Wired to AppShell V2 + auth gate + real SSE |
| User identity | JWT issued (57.7 OIDC flow) | Consumed by header user menu (avatar / username / logout) |
| Existing 4 pages | Use 57.7 AppShell | Auto-migrate via `routes.config.ts` (no per-page edit) |

### Why `mixed-pattern-reuse` calibration class proposed

Per Sprint 57.4 retrospective AD-Sprint-Plan-6 propose: `mixed` class split into
`mixed-greenfield` (0.60) vs `mixed-pattern-reuse` (~0.40) — pattern-reuse
acceleration evidence (60-70% velocity boost vs greenfield). Sprint 57.8 is the
first application after AD logged.

Sprint 57.8 has heavy reuse content (US-2 consume IAM, US-4 migrate 4 existing,
US-5 consume features/chat_v2 9 existing components) but novel architecture
content (US-1 sidebar V2, US-3 page registry). HYBRID weighted blend approach
(same as 57.7 `iam-frontend-spike` 0.60) more accurate than single class.

---

## User Stories

### US-1 (greenfield) — AppShell V2 sidebar layout

**As a** SaaS user navigating multiple platform features
**I want** a left sidebar with categorized nav (Operations / Admin / Settings),
collapsible to icon-only on narrow viewport, sticky to viewport
**So that** I can quickly switch between 11+ pages without scrolling header,
matching industry-standard SaaS admin portal pattern users expect

**Acceptance**:
- New `<AppShellV2>` component (renames or supersedes 57.7 `AppShell`)
- Sidebar fixed left, ~240px wide expanded, ~64px collapsed (icon-only)
- 3 categorized sections (Operations / Admin / Settings) — section headers visible
- Sidebar state (expanded/collapsed) persisted in Zustand store with localStorage
- Mobile breakpoint (<768px) sidebar fully collapses + becomes drawer overlay
- Header retains logo (left) + page title slot + user menu slot (right)
- Footer simplified or removed

### US-2 (reuse) — User menu + logout (consume 57.7 IAM)

**As an** authenticated user
**I want** an avatar dropdown in the header showing my email/name + logout button
**So that** I can confirm my identity at-a-glance and sign out cleanly

**Acceptance**:
- New `<UserMenu>` component in header right
- Avatar circle with initials (or email-derived) — falls back to icon if no name
- Click → dropdown showing: email, "Sign out" button
- Click "Sign out" → clear localStorage JWT (Sprint 57.7 keys) + redirect `/auth/login`
- Reads JWT claims via existing `authService` (sub / email / name)
- If unauthenticated (no JWT) → no UserMenu rendered (fallback to login redirect)

### US-3 (greenfield) — Page registry

**As a** developer adding a new frontend page
**I want** a single `routes.config.ts` listing all 11 pages with metadata
(name / path / icon / category / activeFlag)
**So that** sidebar nav, route generation, and feature-flagged ship pending
pages all consume the same source of truth

**Acceptance**:
- New `frontend/src/routes.config.ts` exporting `RouteEntry[]` with TypeScript
  types (name / path / icon / category / active)
- App.tsx imports config and generates `<Route>` elements via `.map()`
- AppShellV2 sidebar imports config and generates nav links via `.map()`,
  filtering by category — `active=false` entries shown disabled (gray + tooltip)
- 11 entries cover: Cost / SLA / Admin Tenants / Tenant Settings (4 active),
  chat-v2 (active after US-5 ships), governance / verification / audit-log /
  feature-flags / user-profile / mfa-settings (6 placeholders, active=false)
- Removing entry from config = removing from sidebar AND removing route — single source

### US-4 (reuse) — Migrate existing 4 pages to AppShell V2

**As an** existing Cost Dashboard / SLA / Admin Tenants / Tenant Settings user
**I want** my pages to use the new V2 sidebar layout instead of top-nav
**So that** UX is consistent across the platform

**Acceptance**:
- 4 page components (`pages/cost-dashboard/index.tsx`, etc.) wrap content in
  `<AppShellV2>` (was `<AppShell>` in 57.7 cost-dashboard, others ad-hoc)
- Existing Vitest unit tests pass unchanged (no behavior change)
- Existing Playwright e2e tests pass unchanged (UI layout pattern change only;
  data flow / button interactions / form validation untouched)
- No regressions: Vite bundle still under 500 kB JS (currently 273 kB; +50%
  budget unchanged from Sprint 57.7 Risk D)

### US-5 (reuse) — chat-v2 page real ship

**As an** authenticated user
**I want** to send messages to backend chat router via SSE, see thinking blocks,
tool calls with status, ApprovalCard inline when HITL triggers, and verification
status when Cat 10 verifies
**So that** I can demo the V2 platform end-to-end in real-LLM mode (not
placeholder) — answering Sprint 57.5 paper-vs-runtime drift R4

**Acceptance**:
- `pages/chat-v2/index.tsx` composed real (not 21-line placeholder):
  - Wraps in `<AppShellV2>` with page title "Chat (V2)"
  - Auth gate via existing `authService.isAuthenticated()` — redirect `/auth/login` if not authed
  - Hosts existing `<ChatLayout>` (which composes MessageList + InputBar)
  - Hosts existing `<ApprovalCard>` rendered inline when GuardrailTriggered SSE event arrives
  - Hosts NEW minimal verification status badge when VerificationResult SSE arrives (US-5 stretch — defer if time-bound)
- `useLoopEventStream` hook validated against real backend chat router (smoke test against `localhost:8000`)
- Playwright e2e ≥4 cases:
  1. Happy path mocked SSE: send message → receive thinking + tool_call + final
  2. Auth gate: unauthenticated user redirected to login
  3. ApprovalCard mocked SSE: GuardrailTriggered → ApprovalCard appears → click Approve → continues
  4. Network error mocked: SSE connection fails → user-visible error UI
- chatService passes JWT token in Authorization header (Bearer) to chat router

---

## Technical Specifications

### AppShellV2 layout structure

```tsx
// frontend/src/components/AppShellV2.tsx
<div className="flex min-h-screen bg-background text-foreground">
  <Sidebar />                                  {/* fixed left, 240px / 64px */}
  <div className="flex flex-1 flex-col">
    <Header>
      <PageTitle slot />                       {/* per-page set via prop */}
      <UserMenu />                             {/* right; consumes 57.7 IAM */}
    </Header>
    <main className="flex-1 p-6">{children}</main>
  </div>
</div>
```

### Sidebar structure (sketch)

```
┌─────────────────────┐
│ IPA Platform     [<]│  ← logo + collapse toggle
├─────────────────────┤
│ OPERATIONS          │  ← category header (small, muted)
│  💬 Chat (V2)       │  ← active page highlighted
│  📊 Cost Dashboard  │
│  📈 SLA Dashboard   │
├─────────────────────┤
│ ADMIN               │
│  🏢 Tenants         │
│  ⚙️  Tenant Settings│
│  📜 Audit Log     ⚪│  ← inactive (placeholder; gray + tooltip)
│  🚦 Feature Flags ⚪│
├─────────────────────┤
│ SETTINGS            │
│  👤 User Profile  ⚪│
│  🔐 MFA Settings  ⚪│
└─────────────────────┘
```

### routes.config.ts structure

```ts
// frontend/src/routes.config.ts
export type RouteCategory = "operations" | "admin" | "settings";

export interface RouteEntry {
  name: string;        // Display name (sidebar)
  path: string;        // React Router path
  icon: LucideIcon;    // lucide-react component
  category: RouteCategory;
  active: boolean;     // false = grayed out + tooltip "Coming soon"
  component?: () => Promise<{default: ComponentType}>; // lazy import for active
}

export const ROUTES: RouteEntry[] = [
  // operations
  { name: "Chat (V2)", path: "/chat-v2", icon: MessageSquare, category: "operations", active: true, component: () => import("./pages/chat-v2") },
  { name: "Cost Dashboard", path: "/cost-dashboard", icon: BarChart3, category: "operations", active: true, component: () => import("./pages/cost-dashboard") },
  { name: "SLA Dashboard", path: "/sla-dashboard", icon: Activity, category: "operations", active: true, component: () => import("./pages/sla-dashboard") },
  // admin
  { name: "Tenants", path: "/admin-tenants", icon: Building2, category: "admin", active: true, component: () => import("./pages/admin-tenants") },
  { name: "Tenant Settings", path: "/tenant-settings", icon: Settings2, category: "admin", active: true, component: () => import("./pages/tenant-settings") },
  { name: "Audit Log", path: "/audit-log", icon: ScrollText, category: "admin", active: false },
  { name: "Feature Flags", path: "/feature-flags", icon: ToggleLeft, category: "admin", active: false },
  { name: "Governance", path: "/governance", icon: ShieldCheck, category: "admin", active: false },
  { name: "Verification", path: "/verification", icon: CheckCheck, category: "admin", active: false },
  // settings
  { name: "User Profile", path: "/profile", icon: User, category: "settings", active: false },
  { name: "MFA Settings", path: "/mfa", icon: Lock, category: "settings", active: false },
];
```

### Zustand sidebar state

```ts
// frontend/src/store/uiStore.ts (NEW; module-level for whole-app)
interface UIState {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
}
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    { name: "ipa-ui-state" }
  )
);
```

### Auth gate hook for chat-v2 page

```tsx
// pages/chat-v2/index.tsx (composed from features/chat_v2)
import { Navigate } from "react-router-dom";
import { authService } from "@/features/auth/services/authService";

export default function ChatV2Page() {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/auth/login" replace />;
  }
  return (
    <AppShellV2 pageTitle="Chat (V2)">
      <ChatLayout />
    </AppShellV2>
  );
}
```

### SSE auth integration (chatService)

```ts
// features/chat_v2/services/chatService.ts (modify existing)
const headers = new Headers({
  "Content-Type": "application/json",
  Authorization: `Bearer ${authService.getToken()}`,  // NEW
});
```

---

## File Change List

### Frontend NEW

| File | Purpose | LOC est |
|------|---------|---------|
| `frontend/src/components/AppShellV2.tsx` | V2 layout (sidebar + header + main) | ~120 |
| `frontend/src/components/Sidebar.tsx` | Sidebar nav (consumes routes.config) | ~110 |
| `frontend/src/components/UserMenu.tsx` | Avatar dropdown (consumes IAM) | ~80 |
| `frontend/src/store/uiStore.ts` | Zustand sidebar state + persist | ~30 |
| `frontend/src/routes.config.ts` | 11-page registry | ~70 |
| `frontend/tests/unit/components/AppShellV2.test.tsx` | Vitest layout/collapse tests | ~50 |
| `frontend/tests/unit/components/Sidebar.test.tsx` | Vitest nav generation tests | ~50 |
| `frontend/tests/unit/components/UserMenu.test.tsx` | Vitest auth state tests | ~40 |
| `frontend/tests/unit/store/uiStore.test.ts` | Vitest persist tests | ~30 |
| `frontend/tests/e2e/chat-v2-real-ship.spec.ts` | Playwright 4+ cases | ~150 |

### Frontend MODIFY

| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Replace inline `<Route>` with `.map(ROUTES)` from registry |
| `frontend/src/pages/chat-v2/index.tsx` | 21-line placeholder → composed real ship |
| `frontend/src/pages/cost-dashboard/index.tsx` | `<AppShell>` → `<AppShellV2>` |
| `frontend/src/pages/sla-dashboard/index.tsx` | Add `<AppShellV2>` wrap |
| `frontend/src/pages/admin-tenants/index.tsx` | Add `<AppShellV2>` wrap |
| `frontend/src/pages/tenant-settings/index.tsx` | Add `<AppShellV2>` wrap |
| `frontend/src/features/chat_v2/services/chatService.ts` | Add JWT Bearer header |
| `frontend/src/components/AppShell.tsx` | DELETE or DEPRECATE (replaced by AppShellV2) |

### Backend NEW / MODIFY

None expected — Sprint 57.8 is frontend-only architecture + chat-v2 ship; backend unchanged.
(Risk: if Day 0 三-prong reveals chat router auth header mismatch with `chatService` Authorization Bearer, scope expands — see §Risk C.)

---

## Acceptance Criteria

### US-1 (AppShell V2 sidebar)
- [ ] `<AppShellV2>` renders sidebar (240px expanded / 64px collapsed)
- [ ] Sidebar collapse toggle button works; state persists across page refresh (Zustand persist)
- [ ] Mobile viewport (<768px) sidebar collapses + becomes drawer overlay
- [ ] 3 category sections display correct page entries
- [ ] Active page highlighted (per `useLocation()`)
- [ ] Vitest unit tests pass (≥4 tests)

### US-2 (User menu)
- [ ] `<UserMenu>` renders avatar with initials when authed
- [ ] Click → dropdown shows email + Sign out button
- [ ] Click Sign out → localStorage cleared + redirect `/auth/login`
- [ ] Unauthed → no UserMenu rendered (or fallback)
- [ ] Vitest unit tests pass (≥3 tests)

### US-3 (Page registry)
- [ ] `routes.config.ts` exports `RouteEntry[]` with 11 entries
- [ ] App.tsx generates routes from config (no inline `<Route>`)
- [ ] Sidebar generates nav from config
- [ ] Inactive entries shown grayed out + "Coming soon" tooltip
- [ ] Removing one entry = removing from both sidebar AND routes (single source)

### US-4 (Migrate 4 pages)
- [ ] cost-dashboard / sla-dashboard / admin-tenants / tenant-settings all wrap in AppShellV2
- [ ] All existing Vitest tests pass (no behavior change)
- [ ] All existing Playwright tests pass (no functional regression)
- [ ] Vite bundle JS < 500 kB (Sprint 57.7 budget)

### US-5 (chat-v2 ship)
- [ ] pages/chat-v2/index.tsx composed real (auth gate + AppShellV2 + ChatLayout)
- [ ] Unauthed user redirected to `/auth/login`
- [ ] chatService sends JWT Bearer header
- [ ] useLoopEventStream consumes real backend SSE in smoke test
- [ ] ApprovalCard renders when GuardrailTriggered SSE event arrives
- [ ] Playwright e2e ≥4 cases pass (happy / auth gate / ApprovalCard / network error)

### Sprint-wide
- [ ] pytest unchanged (frontend-only sprint; ~1622 baseline)
- [ ] mypy 0/300 unchanged
- [ ] 9/9 V2 lints green
- [ ] Vitest 41 → ≥51 (+10 from new component tests)
- [ ] Playwright 23 → ≥27 (+4 from chat-v2 e2e)
- [ ] LLM SDK leak 0
- [ ] Day 0 三-prong (Path + Content; Schema N/A) catalogued in progress.md

---

## Deliverables (checklist mapping)

| Day | Deliverable |
|-----|-------------|
| Day 0 | Branch + Day 0 三-prong + calibration commit |
| Day 1 | US-1 AppShellV2 + Sidebar + uiStore + US-3 routes.config.ts + App.tsx refactor |
| Day 2 | US-2 UserMenu + US-4 migrate 4 pages |
| Day 3 | US-5 chat-v2 page composition + auth gate + chatService JWT header + Playwright e2e |
| Day 4 | Closeout: retro Q1-Q7 + memory snapshot + 4 doc syncs + PR |

---

## Dependencies & Risks

### Dependencies
- Sprint 57.7 IAM working (JWT issued; localStorage keys; authService) ✅ MERGED
- Sprint 57.7 frontend foundation (Tailwind 4 + shadcn + lucide-react + Zustand persist) ✅ MERGED
- Existing `features/chat_v2/*` 9 components from Sprint 50.2 + 53.5 + 53.6 (ChatLayout / MessageList / InputBar / ToolCallCard / ApprovalCard / useLoopEventStream / chatService / chatStore / types) ✅ MAIN
- Backend chat router SSE 8-event stream (Sprint 50.2) + governance approval flow (Sprint 53.5/53.6) ✅ MAIN

### Risks

| ID | Risk | Mitigation |
|----|------|------------|
| **A** | Tailwind 4 sidebar collapse state with URL hash (avoid page refresh losing state) | Use Zustand persist (localStorage) — pattern reused from cost-dashboard `useCostStore` |
| **B** | 11-page registry config requires 4 ship-pending placeholder stub components OR sidebar inactive flag prevents click | Use `active: false` flag; sidebar renders disabled + tooltip; no stub component needed |
| **C** | chat-v2 SSE useLoopEventStream against real backend may surface user_id / auth header mismatch (D19 Sprint 57.7 cascade pattern) | Smoke test in Day 3 against localhost; fallback to mocked SSE if real-backend issue surfaces (defer real-LLM smoke to AD-Cat10-Frontend-Panel companion sprint) |
| **D** | `mixed-pattern-reuse` calibration class is in proposal status (AD-Sprint-Plan-6); 1st application uncertainty | Use HYBRID 0.50 weighted (mirrors Sprint 57.7 `iam-frontend-spike` 0.60 hybrid pattern); document delta in Day 4 retro Q2 |
| **E** | Vite bundle JS exceeding 500 kB after sidebar + lucide-react icons | Tree-shake lucide-react via per-import `import { MessageSquare } from "lucide-react"` (no namespace import); verify Day 1 build size |
| **F** | Existing 4 pages have inline page-title rendering; AppShellV2 page title slot may conflict | Day 0 Prong 2 grep "page title" patterns in 4 existing pages; if conflicts, narrow US-4 to defer page-title slot consolidation |
| **G** | Day 4 closeout pytest scope discipline (Sprint 57.7 D19 lesson) | Day 4 closeout MUST run full integration suite + Vitest full + Playwright full + 3 lint sweep before pushing — not `tests/unit/` only |
| **H** (Day 0 D3) | `authService.getToken()` 不存在;actual = `getJwt()` + `fetchWithAuth()` already adds Authorization Bearer header | US-2 use `getJwt()` for email decode + `clearJwt()` for logout. **US-5.2 simplified**: chatService swap raw `fetch` → `fetchWithAuth` (no manual header concat). ~30 min scope reduce. |
| **I** (Day 0 D4 — Decision A1 ratified) | 4 existing pages all 0 AppShell hits; cost-dashboard 57.7 wrap actually at `CostOverview.tsx` inner component | Page-level wrap convention adopted: US-4 unwind cost-dashboard CostOverview AppShell wrap + move to `pages/cost-dashboard/index.tsx`; sla-dashboard / admin-tenants / tenant-settings add wrap at page level. ~+1 hr scope addition. |
| **J** (Day 0 D5 — Decision B1 ratified) | `pages/auth/login/index.tsx` already uses AppShell; auth pages should NOT have sidebar (unauthed) | Rename `components/AppShell.tsx` → `components/AuthShell.tsx`; update 2 auth page imports (login + callback). AppShellV2 reserved for authenticated routes. ~+30 min scope addition. |

### Sprint 57.7 lesson carry-forward (mandatory)

Per Sprint 57.7 PR #116 5 CI fix commits (~$2-3 hr lost time):
- **Day 4 closeout pytest scope** — full `python -m pytest`, NOT `tests/unit/` only (caught D19 user_id + observer cascade misses too late)
- **Pre-push lint sweep** — full `python -m flake8 src tests` + `black --check src tests` + `isort --check-only src tests` before EVERY push, NOT only on touched files

These are committed as Phase 57.8 retrospective Q3 lesson capture; sprint-workflow.md §Step 5 expansion is candidate Phase 57.9+ AD.

---

## Workload (calibrated)

### Bottom-up estimate

| Story | LOC est | Hours |
|-------|---------|-------|
| US-1 AppShellV2 + Sidebar + uiStore | ~260 src + ~80 tests | ~3 hr |
| US-2 UserMenu + tests | ~80 src + ~40 tests | ~1 hr |
| US-3 routes.config + App.tsx refactor | ~70 src + minor edit | ~2 hr |
| US-4 migrate 4 pages + tests verify | ~30 LOC × 4 + test verify | ~3 hr |
| US-5 chat-v2 page + auth gate + chatService JWT + Playwright | ~50 src + ~150 e2e | ~4 hr |
| Day 0 三-prong + Day 4 closeout overhead | — | ~2 hr |
| **Total** | **~890 LOC** | **~15 hr** |

### Calibration: HYBRID `frontend-arch-spike` 0.50 (NEW class proposal)

| Component | Weight | Class | Multiplier | Calibrated hr |
|-----------|--------|-------|------------|---------------|
| US-1 AppShellV2 + US-3 routes.config (greenfield) | 5/15 | `medium-frontend` | 0.65 | 3.25 |
| US-2 + US-4 + US-5 (reuse) | 8/15 | `mixed-pattern-reuse` | 0.40 | 4.20 (10.5 hr × 0.40) |
| Day 0 + Day 4 overhead | 2/15 | `closeout` | 0.80 | 1.60 |
| **Bottom-up est** | — | — | — | **~9.05 hr** |

Or single HYBRID class `frontend-arch-spike` ≈ 0.50 mid-blend: 15 × 0.50 = **~7.5 hr**.

### Committed budget

**~8 hr** (mid-band of HYBRID 7.5 ↔ component-blend 9.05).

### Calibration class proposal (AD-Sprint-Plan-10)

NEW class `frontend-arch-spike` baseline 0.50 — opens with this sprint's 1-data-point.
Pending 2-3 sprint window evidence; potential expand if Phase 57.9 (governance ship)
or Phase 57.10 (verification ship) reuse same architecture-foundation + page-ship pattern.

If accepted as 1st-application baseline, Sprint 57.8 retrospective Q2 records ratio:

```
ratio = actual_hours / 8
- in-band [0.85, 1.20] → KEEP 0.50
- below 0.85 → re-eval as 0.40 next sprint
- above 1.20 → re-eval as 0.60 next sprint
```

---

## Open questions for user (pending plan approval)

1. **Branch name** — `feature/sprint-57-8-appshell-v2-chat-v2-ship` OK? (long but explicit)
2. **`AppShell.tsx` deletion** — DELETE (clean) or DEPRECATE with `@deprecated` JSDoc (gradual)? Default: DELETE since Sprint 57.7 only cost-dashboard consumed it (US-4 migrates).
3. **lucide-react icon set per route** — accepts my proposal in §Technical Specifications, or want different icons for any route?
4. **NEW calibration class `frontend-arch-spike`** — accept proposal at 0.50 1st-app baseline, or want different multiplier?
