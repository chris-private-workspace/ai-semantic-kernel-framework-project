---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-10-plan.md
Purpose: Sprint 57.10 plan — Verification real ship (standalone /verification page + chat-v2 inline panel + NEW /api/v1/verification REST + Alembic 0017 verification_log table). Phase 57+ Frontend SaaS 7/N.
Category: Frontend / Backend / Cat 10 Verification ship / Multi-domain
Scope: Phase 57 / Sprint 57.10

Description:
    Phase 57+ SaaS Frontend 7/N expansion. Sprint 57.9 closed governance real
    ship + AD-Cost-Dashboard-UseQuery via TanStack Query 4-page migration.
    Sprint 57.10 closes 16-frontend-design.md V2 Ship Timeline final priority
    slot — Cat 10 Verification frontend real ship — by combining standalone
    /verification page (admin retrospective view) with inline VerificationPanel
    inside chat-v2 (live verification status during agent loop).

    Closes:
    - 16-frontend-design.md §V2 Ship Timeline priority slot 3 of 3 (chat-v2
      Sprint 57.8 + governance Sprint 57.9 + verification Sprint 57.10)
    - AD-Cat10-Frontend-Panel (logged Sprint 54.1 retrospective; carryover for
      verifier UI panel)
    - Sprint 57.5 dual scoring runtime gap on 5 placeholder pages (now down to 4)

Created: 2026-05-09 (drafted — pending user approval before Day 0 commit)
Last Modified: 2026-05-09
Status: Draft (pending user approval)

Modification History (newest-first):
    - 2026-05-09: Initial creation (Sprint 57.10 drafting; user approved scope
      Q1-Q4 in chat session 2026-05-09 — Both pages + NEW REST endpoint +
      ~14-16 hr extended ship + Full 三-prong including Schema)

Related:
    - 16-frontend-design.md §V2 Ship Timeline (verification real ship priority slot)
    - sprint-57-9-plan.md (structural template per sprint-workflow.md §Step 1)
    - .claude/rules/frontend-react.md (Tailwind / shadcn / Zustand / TanStack Query rules)
    - .claude/rules/backend-python.md (FastAPI router / async / type hints)
    - .claude/rules/multi-tenant-data.md (NEW Alembic 0017 RLS rule)
    - 17-cross-category-interfaces.md §Cat 10 (Verifier ABC + VerificationResult contract)
    - AD-Cat10-Frontend-Panel (logged 54.1; closes via US-4 + US-5)
---

# Sprint 57.10 — Verification Real Ship: Standalone Page + chat-v2 Inline Panel + NEW /verification REST (Frontend 7/N)

## Sprint Goal

Promote Cat 10 Verification frontend from Sprint 49.1 placeholder ("Coming in
Phase 54.1 — Verifier results + self-correction trace.") to production-grade
real-ship — combining (a) standalone `/verification` page with 2-tab Routes
(`/verification/recent` retrospective table + `/verification/timeline`
correction trace detail) wrapped in AppShellV2 + auth gate, and (b) inline
`VerificationPanel` inside chat-v2 ChatLayout consuming SSE
`VerificationPassed` + `VerificationFailed` events. Backend introduces NEW
`verification_log` table (Alembic 0017 + RLS) + REST endpoints
`/api/v1/verification/recent` + `/api/v1/verification/{session_id}/correction-trace`
+ write hook in `correction_loop.run_with_verification()` — closing
AD-Cat10-Frontend-Panel + 16.md V2 Ship Timeline final priority slot.

---

## Background

### Why verification frontend now

Sprint 57.9 closeout retrospective Q5 + user direction (2026-05-09 chat session):

1. **Pattern reuse compound ROI** — Sprint 57.7 (IAM foundation + AppShellV2
   precursor) + Sprint 57.8 (AppShellV2 + auth gate) + Sprint 57.9 (governance
   + TanStack pattern) built infrastructure that this sprint inherits FREE.
   Per Sprint 57.9 Day 4 evidence: pattern reuse acceleration -50% velocity vs
   greenfield. Verification ship is the "last mile" of 16.md V2 Ship Timeline.
2. **Backend 100% production-ready** — Sprint 54.1 (RulesBasedVerifier +
   LLMJudgeVerifier + correction_loop) + Sprint 54.2 (verification observability)
   + Sprint 55.5 (chat router wire via _verifier_factory + always-call-wrapper
   pattern) delivered Cat 10 Level 4 production. Frontend ship is the
   remaining 15% runtime gap (per Sprint 57.5 dual scoring evidence:
   verification placeholder = 1 of 5 placeholder pages).
3. **Persistent verification history needed** — Cat 10 currently emits SSE
   events live during agent loop, but verification results are NOT persisted
   (correction_loop.py has no DB write hook; audit_log only logs
   `loop_completed` with stop_reason="verification_failed", not per-verifier
   detail). For admin retrospective UX (compliance investigation / verifier
   tuning), persistence is mandatory → NEW `verification_log` table (Alembic
   0017) + write hook in correction_loop.
4. **Calibration validation** — Sprint 57.9 introduced
   `frontend-feature-with-migration` 0.50 (1-data-point ratio 1.00 bullseye).
   Sprint 57.10 is genuine multi-domain (Backend Alembic + REST + Frontend
   page + inline panel) → use `large multi-domain` 0.55 (4th data point after
   56.1=1.00 / 56.3=1.04 / 57.2=0.77 / 3-data mean **0.94 ✅** in band) — NOT
   `frontend-feature-with-migration` since that class is frontend-only by definition.

### What changed since Sprint 57.9

| Asset | 57.9 ship state | 57.10 needs |
|-------|-----------------|------------|
| `pages/verification/index.tsx` | 11-line placeholder ("Coming in Phase 54.1") | AppShellV2 wrap + auth gate + 2-tab nested Routes (recent / timeline) |
| `features/verification/` folder | n/a (does NOT exist) | NEW: types / services / hooks / components |
| Cat 10 `correction_loop.run_with_verification()` | emits SSE events only; no persistence (verified Day 0 探勘) | + write hook persisting each verification to `verification_log` (best-effort try/except per Sprint 57.7 R1 sessions+tool_calls observer pattern) |
| `verification_log` table | does NOT exist | NEW Alembic 0017: id / tenant_id / session_id / turn_index / verifier_name / verifier_type / passed / score / reason / suggested_correction / correction_attempt / created_at + RLS policy + 3 indexes |
| `/api/v1/verification` router | does NOT exist | NEW: GET `/recent` (paginated) + GET `/{session_id}/correction-trace` |
| `pages/chat-v2/index.tsx` | 57.8 real ship; consumes SSE list display | + `<VerificationPanel />` mount below chat content (Day 0 will confirm exact slot) |
| `features/chat-v2/store/chatStore.ts` | tracks SSE events generic list | + `verifications: VerificationEvent[]` derived state from passed/failed events (or filter from existing event list — Day 0 picks pattern) |
| `routes.config.ts` | verification entry `active: false` placeholder | verification entry `active: true` + lazy `component:` import |

### Why `large multi-domain` 0.55 calibration class (NOT `frontend-feature-with-migration` 0.50)

Per 57.9 retrospective AD-Sprint-Plan-10 + matrix discipline (sprint-workflow.md §Calibration matrix L130-160):

- Sprint 57.10 scope = Backend Alembic 0017 + ORM model + RLS (~3 hr) + Backend
  REST router + 2 endpoints + write hook + integration tests (~5 hr) + Frontend
  page + inline panel + components (~12-13 hr) + e2e + closeout (~7-8 hr).
- This is genuine **multi-domain** (DB schema + backend REST + frontend page +
  cross-component state propagation + e2e). Single-class `frontend-feature-with-migration`
  doesn't fit since it presumes frontend-only with backend untouched.
- `large multi-domain` 0.55 has 3 prior data points (56.1=1.00 / 56.3=1.04 /
  57.2=0.77; 3-data mean **0.94 ✅** in [0.85, 1.20] band) — best fit for
  this scope class. Sprint 57.10 = 4th data point, validating mid-band 0.55.

### Sprint 57.7 D19 + 57.8 D13 + 57.9 D-PRE-16 cascade lesson carry-forward

Three accumulated lessons MUST be applied this sprint:

- **57.7 D19 (sessions/tool_calls observer "blocked" assumption was wrong)** —
  before assuming correction_loop write hook needs new infra (e.g. JWT user_id
  extraction), Day 0 探勘 MUST verify what's already wired. Likely outcome:
  TenantContextMiddleware (49.3) + get_current_user_id (52.5) already populate
  request.state.user_id reachable from chat router, AND correction_loop receives
  state.tenant_id → no new infra needed for verification_log INSERT.
- **57.8 D13 (dev DB pollution from prior failed test runs)** — Day 0 must
  cleanup any leftover verification_log rows BEFORE Day 1 starts (since table
  is NEW, this is a non-issue this sprint, but lesson applies to e2e fixtures).
- **57.9 D-PRE-16 (governance auth gate broke 5 prior e2e silently)** — Sprint
  57.10 adds verification page with auth gate via Navigate + adds VerificationPanel
  to chat-v2. ANY existing chat-v2 e2e MUST be re-verified Day 4 (chat-v2
  already auth-gated since 57.8, so seedAuthJwt fixture already in beforeEach;
  but Panel mount changes ChatLayout structure → potential selector drift).

---

## User Stories

### US-1 (greenfield) — Backend: verification_log table + Alembic 0017 + RLS

**As a** Cat 10 platform engineer
**I want** a `verification_log` table with multi-tenant RLS that persists every
verifier result emitted by `correction_loop.run_with_verification()`
**So that** admin retrospective UX (US-4) and correction trace view (US-4 timeline tab)
can query historical verification data without recomputing from audit_log

**Acceptance**:
- Alembic migration 0017 (Day 0 三-prong Prong 3 will confirm head version) creates `verification_log` with columns:
  - `id` BIGSERIAL PRIMARY KEY
  - `tenant_id` UUID NOT NULL FK to `tenants.id` ON DELETE CASCADE
  - `session_id` UUID NOT NULL (no FK to sessions per Sprint 57.7 sessions table state — verified Day 0 Prong 3)
  - `turn_index` INTEGER NOT NULL DEFAULT 0
  - `verifier_name` VARCHAR(128) NOT NULL
  - `verifier_type` VARCHAR(32) NOT NULL (`rules_based` / `llm_judge` / `external`)
  - `passed` BOOLEAN NOT NULL
  - `score` DOUBLE PRECISION NULL
  - `reason` TEXT NULL
  - `suggested_correction` TEXT NULL
  - `correction_attempt` INTEGER NOT NULL DEFAULT 0
  - `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- RLS policy `tenant_isolation_verification_log` enforced via `tenant_id = current_setting('app.tenant_id')::uuid`
- 3 indexes: `(tenant_id, session_id, created_at DESC)` + `(tenant_id, created_at DESC)` + `(tenant_id, passed)` for common filter access
- ORM model `VerificationLog(Base)` at `backend/src/infrastructure/db/models/verification_log.py`
- 8th V2 lint `check_rls_policies.py` passes (0 gaps after 0017)
- 1 unit test verifying migration up/down + RLS policy presence

### US-2 (greenfield) — Backend: NEW /api/v1/verification REST + correction_loop write hook

**As a** auditor / compliance / verifier-tuning operator
**I want** REST endpoints to query historical verification results paginated by
session + retrieve full correction loop trace for one session
**So that** retrospective frontend can display verifier history and admin can
investigate failures without log scraping

**Acceptance**:
- NEW `backend/src/api/v1/verification.py` router with 2 endpoints:
  - `GET /api/v1/verification/recent?session_id={uuid}&verifier_type={type}&passed={bool}&limit={int}&offset={int}`
    - Returns `VerificationLogPage`: `{ items: VerificationLogItem[], total: int, has_more: bool }`
    - `VerificationLogItem`: 12 fields mirroring DB columns
    - Default `limit=50`, max `limit=200`; `offset >= 0`
    - Filter combinators: AND semantics; all filters optional
    - ORDER BY `(created_at DESC, id DESC)` for deterministic pagination
    - Auth: `Depends(get_current_user)` + `require_audit_role` RBAC (mirror Sprint 53.5 audit endpoint pattern)
  - `GET /api/v1/verification/{session_id}/correction-trace`
    - Returns `CorrectionTraceResponse`: `{ session_id, entries: VerificationLogItem[] }` (sorted by `(turn_index ASC, correction_attempt ASC, created_at ASC)`)
    - 404 if no entries for session
- Pydantic models registered in `backend/src/api/v1/verification.py` (NOT extracted to schemas/ until 2nd consumer per AP-6)
- correction_loop.py write hook (best-effort try/except per Sprint 57.7 R1 pattern):
  ```python
  # After each verification (passed or failed), persist to verification_log:
  try:
      await VerificationLogRepository.insert(
          session=db_session, tenant_id=state.tenant_id, session_id=session_id,
          turn_index=state.turn_index, verifier_name=result.verifier,
          verifier_type=result.verifier_type, passed=result.passed,
          score=result.score, reason=result.reason,
          suggested_correction=result.suggested_correction,
          correction_attempt=attempt_num,
      )
  except Exception:
      logger.exception("verification_log insert failed (best-effort; not blocking)")
  ```
- Env flag `VERIFICATION_LOG_PERSIST_ENABLED` (default `true` for production; `false` for unit-test fixtures to avoid DB churn)
- 8-10 integration tests:
  - Recent endpoint: happy path 2-row insert + filter by session_id / verifier_type / passed / paginate
  - Correction-trace endpoint: 404 + happy 3-entry trace
  - RBAC enforcement (403 without audit role)
  - Multi-tenant RLS isolation (Tenant A inserts → Tenant B query 404)
  - Best-effort write hook: simulate insert failure → loop continues (no exception bubbles)

### US-3 (greenfield) — Frontend: features/verification/ infrastructure

**As a** developer maintaining verification frontend
**I want** `features/verification/` folder with types / service / 2 TanStack hooks
**So that** US-4 page components and US-5 inline panel can consume well-typed
data via cache-aware hooks

**Acceptance**:
- NEW `features/verification/types.ts`:
  - `VerificationLogItem` interface (12 fields mirror DB)
  - `VerificationLogPage` interface (items / total / has_more)
  - `CorrectionTraceResponse` interface (session_id / entries)
  - `VerificationLogFilter` interface (session_id? / verifier_type? / passed? / limit / offset)
  - `VerifierType` enum-like type union (`'rules_based' | 'llm_judge' | 'external'`)
- NEW `features/verification/services/verificationService.ts`:
  - `fetchVerificationRecent(filter: VerificationLogFilter): Promise<VerificationLogPage>` consuming GET `/api/v1/verification/recent`
  - `fetchCorrectionTrace(sessionId: string): Promise<CorrectionTraceResponse>` consuming GET `/api/v1/verification/{session_id}/correction-trace`
  - Both use `fetchWithAuth` (Sprint 57.7 IAM JWT injection)
  - URL building via shared `buildSearchParams` helper (mirror Sprint 57.4 admin-tenants pattern; omits undefined keys)
- NEW `features/verification/hooks/useVerificationRecent.ts`:
  - `VERIFICATION_RECENT_QUERY_KEY_BASE = ["verification", "recent"] as const`
  - `useVerificationRecent(filter: VerificationLogFilter)` returns TanStack `useQuery({ queryKey: [...BASE, filter], queryFn: ({ signal }) => verificationService.fetchVerificationRecent(filter), keepPreviousData: true })`
- NEW `features/verification/hooks/useCorrectionTrace.ts`:
  - `CORRECTION_TRACE_QUERY_KEY_BASE = ["verification", "correction-trace"] as const`
  - `useCorrectionTrace(sessionId: string | null)` returns TanStack `useQuery({ queryKey: [...BASE, sessionId], queryFn: () => verificationService.fetchCorrectionTrace(sessionId!), enabled: !!sessionId })`
- 4 NEW Vitest unit tests:
  - verificationService: URL build + fetchWithAuth wrap (objectContaining pattern per Sprint 57.9 D-PRE-15 lesson)
  - useVerificationRecent: QUERY_KEY_BASE single-source export + filter changes refetch
  - useCorrectionTrace: enabled gate when sessionId null + fetch when provided
  - types.ts: TypeScript-only sanity (interfaces exported correctly)

### US-4 (greenfield) — Frontend: standalone /verification page (AppShellV2 + 2-tab + 3 components)

**As an** auditor / compliance / verifier-tuning user
**I want** a standalone `/verification` page (auth-gated, AppShellV2 layout)
with 2 sub-routes (recent retrospective table + correction trace timeline)
**So that** I can investigate verification history independently of any active
chat session, mirror governance pattern, and bookmark deep links

**Acceptance**:
- `pages/verification/index.tsx` REPLACE 11-line stub with:
  - Auth gate via `isAuthenticated() + setPostLoginRedirect("/verification")` + `<Navigate to="/auth/login" replace />` (mirror Sprint 57.9 governance pattern)
  - `<AppShellV2 pageTitle="Verification">` wrap
  - 2 nested routes: `/verification/recent` (default redirect from `/verification`) + `/verification/timeline` (correction trace detail; reads `?session_id=` query param OR clicked from recent table row)
  - Tab nav UI in page header (mirror governance NavLink pattern; active state via `useLocation()`)
  - `<Navigate to="recent" replace />` for `/verification` index match
- NEW `features/verification/components/VerifierTypeBadge.tsx`:
  - Small reusable badge with Tailwind utility classes
  - `rules_based` → blue / `llm_judge` → purple / `external` → gray
  - Reusable in VerificationList AND VerificationPanel (US-5)
- NEW `features/verification/components/VerificationList.tsx`:
  - Filter form: 3 fields (session_id input / verifier_type dropdown / passed dropdown {Any / Passed / Failed})
  - Apply / Reset buttons (no debounce per AP-6)
  - Paginated table: 50 rows default; columns = timestamp / session_id (truncated) / verifier_name / `<VerifierTypeBadge />` / passed badge (✅ / ❌) / score (if present) / reason snippet (truncated 80 chars)
  - Click row → navigate to `/verification/timeline?session_id={id}` with focus on selected entry
  - Empty state: "No verification results match filters" + Reset button
  - Loading skeleton (mirror Sprint 57.9 ApprovalList pattern)
  - Error retry UX with `retryClicked` flag pattern (Sprint 57.9 D-PRE-15 codified)
- NEW `features/verification/components/CorrectionTraceView.tsx`:
  - Vertical timeline UI
  - Reads `session_id` from query param or location state
  - Entries grouped by `turn_index` then sorted by `correction_attempt`
  - Each entry card: verifier_name + `<VerifierTypeBadge />` + passed/failed icon + reason (if failed) + suggested_correction (if failed) + score (if present) + correction_attempt indicator
  - Visual distinction: passed entries = green left border; failed = red left border
  - Empty state: "No correction trace for session {id}" if 404
- routes.config.ts updated: verification `active: true` + lazy `component: () => import("./pages/verification")`
- 5-6 NEW Vitest unit tests:
  - VerificationList: renders + filter form interaction + empty state + click row navigates
  - CorrectionTraceView: renders timeline + groups by turn_index + 404 empty state
  - VerifierTypeBadge: 3 type variants

### US-5 (greenfield) — Frontend: inline VerificationPanel inside chat-v2

**As a** chat-v2 end user (operator running an agent loop)
**I want** an inline panel showing live verification status during the loop
(verifier passed/failed + correction attempts triggered)
**So that** I see verification verdict in-context next to the LLM final output
without switching to /verification page

**Acceptance**:
- NEW `features/verification/components/VerificationPanel.tsx`:
  - Subscribes to chatStore selector for `verifications: VerificationEvent[]`
  - Displays each verification as a compact card (verifier_name + `<VerifierTypeBadge />` + passed/failed icon + reason snippet if failed + correction_attempt counter)
  - Empty state: "No verifications yet" hidden behind condition `verifications.length > 0` (panel collapsed when empty)
  - Tailwind utility classes; placement below chat events list within ChatLayout
- `features/chat-v2/store/chatStore.ts` MODIFY:
  - Add `verifications: VerificationEvent[]` slice (interface defined in `features/verification/types.ts`)
  - Add reducer `appendVerification(event)` triggered from useChatStream hook
  - Add `clearVerifications()` reducer triggered on session reset
- `features/chat-v2/hooks/useChatStream.ts` MODIFY:
  - Add 2 isinstance branches for SSE event types `verification_passed` + `verification_failed`
  - Map SSE payload → VerificationEvent → call `chatStore.appendVerification()`
  - Day 0 探勘 will confirm whether useChatStream already iterates all SSE event types (likely yes per Sprint 53.6 SSE bootstrap)
- `pages/chat-v2/index.tsx` MODIFY:
  - Mount `<VerificationPanel />` inside ChatLayout below chat events list
  - Day 0 探勘 will confirm exact slot (likely between event stream and input box)
- `features/verification/types.ts` extend (US-3 base) with:
  - `VerificationEvent` interface (verifier / verifier_type / passed / score / reason / suggested_correction / correction_attempt — mirrors SSE payload shape from `sse.py:248-265`)
- 3 NEW Vitest unit tests:
  - VerificationPanel: renders 3 events from store / hidden when empty / VerifierTypeBadge integration
  - chatStore: appendVerification + clearVerifications reducers
  - useChatStream: verification_passed + verification_failed event routing

### US-6 (mechanical) — Routing + Playwright e2e + closeout doc syncs

**As a** Sprint 57.10 reviewer
**I want** verification routing wired to sidebar + 4-6 Playwright e2e covering
both standalone page (recent + timeline tabs) and inline panel inside chat-v2
**So that** Day 4 closeout has regression-protected coverage and 16.md V2 Ship
Timeline shows verification = real ship

**Acceptance**:
- routes.config.ts entry `verification` flipped `active: true` (was false in 57.8)
- Sidebar auto-includes verification link (categorized "operations" or "admin" — Day 0 探勘 picks based on existing routes.config category convention; default "operations")
- 4-6 Playwright e2e in `frontend/tests/e2e/verification-real-ship.spec.ts`:
  - Auth gate: unauthenticated visit to /verification → Navigate to /auth/login
  - Recent tab happy path: seedAuthJwt + navigate /verification/recent + 2 mocked rows render
  - Recent tab filter: change verifier_type dropdown → URL params update + refetch
  - Timeline tab from row click: click recent table row → URL changes to /verification/timeline?session_id=... + correction trace renders
  - chat-v2 inline panel: navigate /chat-v2 + simulate SSE verification_passed + Panel renders entry (note: requires SSE mock injection; if too brittle Day 4 → DEFERRED to AD-Verification-RealShip-E2E like Sprint 57.9 governance e2e deferral)
  - Empty state: filter to 0 results → "No verification results match filters" + Reset button works
- 16.md V2 Ship Timeline section UPDATED:
  - Verification: 5/N → 6/N (placeholder → shipped)
  - Add row to "shipped table" with Sprint 57.10 reference + main HEAD SHA (Day 4 post-merge update)
  - Decrement "remaining placeholder pages" count from 5 to 4 (or whatever Sprint 57.5 D22 baseline says — Day 0 探勘 confirms)
- Day 4 closeout 4 doc syncs (per Sprint 57.7+57.8+57.9 pattern):
  - sprint-workflow.md §Calibration matrix +1 row `large multi-domain` 0.55 4th data point
  - SITUATION-V2 §9 + §11 NEW entry
  - 16-frontend-design.md V2 Ship Timeline 6/N → 7/N + verification promoted to shipped
  - CLAUDE.md sync deferred to post-merge closeout PR (per 57.7+57.8+57.9 pattern)

---

## Technical Specifications

### Folder structure (NEW + MODIFY)

```
backend/src/
├── infrastructure/db/models/
│   └── verification_log.py              ← NEW: ORM model (US-1)
├── infrastructure/db/repositories/
│   └── verification_log.py              ← NEW: VerificationLogRepository.insert + query (US-1+US-2)
├── infrastructure/db/migrations/versions/
│   └── 0017_verification_log.py         ← NEW: Alembic migration (Day 0 Prong 3 confirms head)
├── api/v1/
│   └── verification.py                  ← NEW: router with /recent + /correction-trace (US-2)
├── agent_harness/verification/
│   └── correction_loop.py               ← MODIFY: write hook to verification_log (US-2)
└── core/config.py                       ← MODIFY: add VERIFICATION_LOG_PERSIST_ENABLED env flag

frontend/src/
├── pages/verification/
│   ├── index.tsx                        ← MODIFY: stub → real ship (US-4)
│   └── README.md                        ← MODIFY: update Phase reference 54.1 → 57.10 shipped
├── features/verification/                ← NEW directory (US-3+US-4+US-5)
│   ├── types.ts                         ← NEW: VerificationLogItem / Page / Filter / Event / VerifierType
│   ├── services/
│   │   └── verificationService.ts       ← NEW: fetchVerificationRecent + fetchCorrectionTrace
│   ├── hooks/
│   │   ├── useVerificationRecent.ts     ← NEW: TanStack useQuery wrapper
│   │   └── useCorrectionTrace.ts        ← NEW: TanStack useQuery wrapper
│   └── components/
│       ├── VerifierTypeBadge.tsx        ← NEW: small reusable badge (US-4+US-5)
│       ├── VerificationList.tsx         ← NEW: filter + paginated table (US-4)
│       ├── CorrectionTraceView.tsx      ← NEW: vertical timeline (US-4)
│       └── VerificationPanel.tsx        ← NEW: inline panel for chat-v2 (US-5)
├── pages/chat-v2/
│   └── index.tsx                        ← MODIFY: mount <VerificationPanel /> (US-5)
├── features/chat-v2/store/
│   └── chatStore.ts                     ← MODIFY: + verifications slice + reducers (US-5)
├── features/chat-v2/hooks/
│   └── useChatStream.ts                 ← MODIFY: + 2 SSE event branches (US-5)
└── routes.config.ts                     ← MODIFY: verification active=true + lazy import
```

### useVerificationRecent hook (TanStack)

```ts
// frontend/src/features/verification/hooks/useVerificationRecent.ts
import { useQuery } from "@tanstack/react-query";
import { verificationService } from "../services/verificationService";
import type { VerificationLogFilter, VerificationLogPage } from "../types";

export const VERIFICATION_RECENT_QUERY_KEY_BASE = ["verification", "recent"] as const;

export function useVerificationRecent(filter: VerificationLogFilter) {
  return useQuery<VerificationLogPage, Error>({
    queryKey: [...VERIFICATION_RECENT_QUERY_KEY_BASE, filter],
    queryFn: ({ signal }) => verificationService.fetchVerificationRecent(filter, signal),
    keepPreviousData: true,
  });
}
```

### useCorrectionTrace hook (TanStack)

```ts
// frontend/src/features/verification/hooks/useCorrectionTrace.ts
import { useQuery } from "@tanstack/react-query";
import { verificationService } from "../services/verificationService";
import type { CorrectionTraceResponse } from "../types";

export const CORRECTION_TRACE_QUERY_KEY_BASE = ["verification", "correction-trace"] as const;

export function useCorrectionTrace(sessionId: string | null) {
  return useQuery<CorrectionTraceResponse, Error>({
    queryKey: [...CORRECTION_TRACE_QUERY_KEY_BASE, sessionId],
    queryFn: () => verificationService.fetchCorrectionTrace(sessionId!),
    enabled: !!sessionId,
  });
}
```

### Pages verification/index.tsx (composed real ship)

```tsx
// frontend/src/pages/verification/index.tsx
import { Navigate, Route, Routes, NavLink } from "react-router-dom";
import { AppShellV2 } from "@/components/AppShellV2";
import { isAuthenticated, setPostLoginRedirect } from "@/features/auth/services/authService";
import { VerificationList } from "@/features/verification/components/VerificationList";
import { CorrectionTraceView } from "@/features/verification/components/CorrectionTraceView";

export default function VerificationPage(): JSX.Element {
  if (!isAuthenticated()) {
    setPostLoginRedirect("/verification");
    return <Navigate to="/auth/login" replace />;
  }
  return (
    <AppShellV2 pageTitle="Verification">
      <nav className="mb-4 flex gap-2 border-b border-border">
        <NavLink
          to="recent"
          className={({ isActive }) =>
            `px-4 py-2 text-sm font-medium ${
              isActive ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`
          }
        >
          Recent
        </NavLink>
        <NavLink
          to="timeline"
          className={({ isActive }) =>
            `px-4 py-2 text-sm font-medium ${
              isActive ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`
          }
        >
          Correction Trace
        </NavLink>
      </nav>
      <Routes>
        <Route index element={<Navigate to="recent" replace />} />
        <Route path="recent" element={<VerificationList />} />
        <Route path="timeline" element={<CorrectionTraceView />} />
      </Routes>
    </AppShellV2>
  );
}
```

### routes.config.ts update

```ts
// frontend/src/routes.config.ts (modify)
{
  name: "Verification",
  path: "/verification",
  icon: ShieldAlert,  // or CheckCircle2 — Day 0 picks
  category: "operations",  // Day 0 confirms convention
  active: true,           // was false in Sprint 57.8
  component: () => import("./pages/verification"),
}
```

### Backend correction_loop write hook

```python
# backend/src/agent_harness/verification/correction_loop.py (modify)
# After yielding VerificationPassed or VerificationFailed event, persist to DB:
if settings.VERIFICATION_LOG_PERSIST_ENABLED:
    try:
        async with get_db_session_with_tenant(state.tenant_id) as session:
            await VerificationLogRepository.insert(
                session=session,
                tenant_id=state.tenant_id,
                session_id=session_id,
                turn_index=getattr(state, "turn_index", 0),
                verifier_name=result.verifier_name,
                verifier_type=result.verifier_type,
                passed=result.passed,
                score=result.score,
                reason=result.reason,
                suggested_correction=result.suggested_correction,
                correction_attempt=attempt_num,
            )
    except Exception:
        logger.exception("verification_log INSERT failed (best-effort; not blocking)")
```

### chatStore verifications slice

```ts
// frontend/src/features/chat-v2/store/chatStore.ts (extend)
import type { VerificationEvent } from "@/features/verification/types";

interface ChatStore {
  // ... existing fields ...
  verifications: VerificationEvent[];
  appendVerification: (event: VerificationEvent) => void;
  clearVerifications: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  // ... existing ...
  verifications: [],
  appendVerification: (event) =>
    set((s) => ({ verifications: [...s.verifications, event] })),
  clearVerifications: () => set({ verifications: [] }),
}));
```

### Calibration: `large multi-domain` 0.55 (4th data point)

Bottom-up estimates per US:

| US | Description | Bottom-up est | Multiplier | Calibrated |
|----|-------------|---------------|------------|------------|
| US-1 | Backend Alembic 0017 + ORM + RLS + 1 unit test | 3 hr | 0.55 | 1.65 hr |
| US-2 | Backend REST + write hook + 8-10 integration tests | 5 hr | 0.55 | 2.75 hr |
| US-3 | Frontend types + service + 2 hooks + 4 Vitest tests | 3 hr | 0.55 | 1.65 hr |
| US-4 | Frontend page + 3 components + 5-6 Vitest + auth gate | 5 hr | 0.55 | 2.75 hr |
| US-5 | Inline panel + chatStore + useChatStream + 3 Vitest tests | 4 hr | 0.55 | 2.20 hr |
| US-6 | Routing + 4-6 Playwright e2e + Vitest sanity | 3 hr | 0.55 | 1.65 hr |
| Day 0 | 三-prong (Path + Content + Schema) + branch + baseline | 2 hr | 0.85 | 1.70 hr |
| Day 4 | Closeout (validation + retro + memory + 3 doc syncs) | 3 hr | 0.85 | 2.55 hr |
| **Total** | | **28 hr** | weighted | **~16.9 hr** |

Round to **~16-17 hr commit** (upper edge of user's "~14-16 hr extended" — at +0-1 hr OVER user's stated budget; Day 4 retrospective will validate).

If actual ratio falls within [0.85, 1.20] band: KEEP `large multi-domain` 0.55 baseline.
If actual ratio < 0.85: log AD-Sprint-Plan-11 propose lower-band candidate for next sprint.
If actual ratio > 1.20: log AD-Sprint-Plan-11 propose upper-band lift OR class refinement.

---

## File Change List

### Frontend NEW (10 files)

- `features/verification/types.ts`
- `features/verification/services/verificationService.ts`
- `features/verification/hooks/useVerificationRecent.ts`
- `features/verification/hooks/useCorrectionTrace.ts`
- `features/verification/components/VerifierTypeBadge.tsx`
- `features/verification/components/VerificationList.tsx`
- `features/verification/components/CorrectionTraceView.tsx`
- `features/verification/components/VerificationPanel.tsx`
- `tests/e2e/verification-real-ship.spec.ts`
- `tests/unit/verification/` (4-6 unit test files; exact count Day 4)

### Frontend MODIFY (5 files)

- `pages/verification/index.tsx` (stub → composed real ship)
- `pages/verification/README.md` (Phase reference update)
- `pages/chat-v2/index.tsx` (+ VerificationPanel mount)
- `features/chat-v2/store/chatStore.ts` (+ verifications slice)
- `features/chat-v2/hooks/useChatStream.ts` (+ 2 SSE event branches)
- `routes.config.ts` (verification active=true + lazy import)

### Backend NEW (4 files)

- `infrastructure/db/models/verification_log.py`
- `infrastructure/db/repositories/verification_log.py`
- `infrastructure/db/migrations/versions/0017_verification_log.py` (Day 0 Prong 3 confirms next available number)
- `api/v1/verification.py`
- `tests/integration/api/test_verification.py` (8-10 tests)
- `tests/unit/agent_harness/verification/test_correction_loop_persist.py` (3 tests; best-effort hook coverage)

### Backend MODIFY (3 files)

- `agent_harness/verification/correction_loop.py` (+ write hook)
- `core/config.py` (+ VERIFICATION_LOG_PERSIST_ENABLED env flag)
- `api/v1/__init__.py` or `api/v1/router.py` (register verification router)

### Docs UPDATE (4 files; Day 4 closeout)

- `.claude/rules/sprint-workflow.md` (+1 row to Calibration matrix)
- `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` (§9 + §11 NEW entry)
- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` (V2 Ship Timeline 6/N → 7/N)
- `CLAUDE.md` (post-merge closeout PR per 57.7+57.8+57.9 pattern)

---

## Acceptance Criteria

### US-1 (Backend Alembic + RLS)

- ✅ Alembic 0017 migration created; head version verified Day 0 Prong 3
- ✅ ORM model VerificationLog importable + tested
- ✅ RLS policy `tenant_isolation_verification_log` present + check_rls_policies.py 0 gaps
- ✅ 3 indexes created
- ✅ 1 unit test verifying schema + RLS

### US-2 (Backend REST + write hook)

- ✅ Both endpoints respond 200 with valid filters; 400 for invalid; 403 without audit role; 404 for missing trace
- ✅ Pagination has_more correct + ORDER BY deterministic
- ✅ Write hook persists each verifier result; failure does NOT bubble (best-effort)
- ✅ env flag `VERIFICATION_LOG_PERSIST_ENABLED` toggleable; default true production / false unit-test
- ✅ 8-10 integration tests + 3 best-effort hook unit tests pass
- ✅ Multi-tenant RLS: Tenant A insert + Tenant B query 404

### US-3 (Frontend infra)

- ✅ `features/verification/` folder created with types / service / 2 hooks
- ✅ `*_QUERY_KEY_BASE` exports as `as const` tuple (single-source pattern per Sprint 57.9)
- ✅ Service uses `fetchWithAuth` + URLSearchParams omit-undefined helper
- ✅ 4 Vitest unit tests pass (service URL build / hook query key / enabled gate / types sanity)

### US-4 (Frontend standalone page)

- ✅ /verification auth gate via Navigate to /auth/login (mirror Sprint 57.9 governance)
- ✅ AppShellV2 wrap with pageTitle="Verification"
- ✅ 2-tab nested Routes (recent default + timeline)
- ✅ VerificationList renders + filter form + pagination + empty state + click row navigates
- ✅ CorrectionTraceView renders vertical timeline + grouped by turn_index + 404 empty state
- ✅ VerifierTypeBadge 3 variants (rules_based blue / llm_judge purple / external gray)
- ✅ All Tailwind utility classes (no inline styles per .claude/rules/frontend-react.md)
- ✅ 5-6 Vitest unit tests pass

### US-5 (Inline VerificationPanel inside chat-v2)

- ✅ VerificationPanel renders 0+ entries from chatStore.verifications
- ✅ Hidden when verifications.length === 0 (no empty card)
- ✅ chatStore.appendVerification + clearVerifications reducers work
- ✅ useChatStream routes verification_passed + verification_failed SSE events to store
- ✅ Panel mounted in pages/chat-v2/index.tsx ChatLayout below event stream
- ✅ 3 Vitest unit tests pass
- ✅ Existing chat-v2 Playwright e2e (4 from 57.8) STILL PASS (regression sentinel — per Sprint 57.9 D-PRE-16 lesson)

### US-6 (Routing + e2e + closeout)

- ✅ routes.config.ts verification entry active=true + lazy import
- ✅ Sidebar shows verification link in chosen category
- ✅ 4-6 Playwright e2e pass; if SSE-mock injection too brittle → DEFERRED to AD-Verification-RealShip-E2E (Sprint 57.11+; mirror Sprint 57.9 governance e2e deferral pattern)
- ✅ 4 doc syncs Day 4 closeout

### Sprint-wide

- ✅ pytest baseline maintained or +18 (8-10 verification integration + 3 best-effort hook + 1 Alembic + 4 frontend Vitest if backend-side count includes ts tests)
- ✅ Vitest 93 → 105+ (+12 minimum: 4 US-3 + 5-6 US-4 + 3 US-5)
- ✅ Playwright 27 → 31-33 (+4-6 verification-real-ship.spec.ts)
- ✅ tsc strict 0 errors
- ✅ Vite build ≤ 285 kB main (Sprint 57.9 baseline 240.86 kB + 45 kB headroom for verification feature folder)
- ✅ 9 V2 lints 9/9 green (no NEW lint this sprint; check_rls_policies validates 0017)
- ✅ Backend flake8 + black + isort all silent
- ✅ LLM SDK leak 0 (verification touches Cat 10 which uses ChatClient ABC; no direct openai/anthropic import)
- ✅ Frontend ESLint silent
- ✅ mypy 0 strict errors

---

## Deliverables (checklist mapping)

- [ ] US-1 — Alembic 0017 verification_log + ORM + RLS (sprint-57-10-checklist.md §1.1-1.4)
- [ ] US-2 — REST router + write hook + integration tests (§1.5-1.7)
- [ ] US-3 — Frontend infra: types + service + hooks (§2.1-2.4)
- [ ] US-4 — Standalone page + 3 components + auth gate + AppShellV2 (§2.5-2.7 + §3.1-3.3)
- [ ] US-5 — Inline VerificationPanel + chatStore + useChatStream (§3.4-3.6)
- [ ] US-6 — routes.config + Playwright e2e + 4 doc syncs (§4.1-4.8)
- [ ] Day 0 — Branch + 三-prong + calibration baseline (§0.1-0.5)
- [ ] Day 4 — Full validation + retro + memory + PR (§4.4-4.10)

---

## Dependencies & Risks

### Dependencies

1. **Sprint 57.7 IAM JWT** — `fetchWithAuth` helper for verificationService; require_audit_role RBAC for /verification endpoints. Both verified working via Sprint 57.7+57.9 ship.
2. **Sprint 57.8 AppShellV2 + auth gate** — VerificationPage wraps in AppShellV2; auth gate via Navigate. Both verified working via Sprint 57.8+57.9 ship.
3. **Sprint 57.9 TanStack Query pattern** — verificationService + 2 hooks mirror Sprint 57.9 governance hook pattern (QUERY_KEY_BASE single-source export + `as const` tuple). Verified working.
4. **Sprint 54.1+54.2+55.5 Cat 10 backend** — RulesBasedVerifier + LLMJudgeVerifier + correction_loop.run_with_verification + chat router wire (always-call-wrapper at L197). Verified working.
5. **Sprint 53.5 audit endpoint pattern** — RBAC `require_audit_role` reused for /verification endpoints.

### Risks

| # | Risk | Likelihood | Mitigation |
|---|------|------------|------------|
| A | NEW correction_loop write hook breaks existing 54.1 loop tests (race condition / async session leak) | MEDIUM | Best-effort try/except wrap per Sprint 57.7 R1 pattern; env flag `VERIFICATION_LOG_PERSIST_ENABLED=false` for unit-test fixtures; Day 1 runs full Cat 10 test suite as regression sentinel |
| B | Alembic 0017 head version conflict (0017 already exists) | LOW | Day 0 Prong 3 verifies head version; if conflict use 0018 |
| C | chat-v2 inline panel introduces ChatLayout layout regression | MEDIUM | Day 0 探勘 confirms exact mount slot before Day 3 code; existing 4 chat-v2 e2e from Sprint 57.8 act as regression sentinel; if regression → revert Panel mount + e2e fix in same PR per 57.9 D-PRE-16 lesson |
| D | useChatStream already iterates SSE events; adding 2 branches may need refactor | LOW | Day 0 Prong 2 grep useChatStream + sse.py to confirm event iteration pattern |
| E | Vite bundle exceeds 285 kB (verification adds ~10 components) | LOW | Lazy import via routes.config.ts (verification page lazy-chunked); shared VerifierTypeBadge across page+panel keeps duplication minimal |
| F | Playwright e2e SSE injection too brittle for chat-v2 panel test | MEDIUM | Defer to AD-Verification-RealShip-E2E like Sprint 57.9 governance e2e; standalone page e2e (recent + timeline) proceeds either way |
| G | scope ratio > 1.20 (under-estimate; multi-domain compounded) | MEDIUM | Day 4 retrospective Q2 logs ratio; AD-Sprint-Plan-11 propose if needed |
| H | 0 chat-v2 e2e regression from Panel mount (cascade lesson 57.9 D-PRE-16) | MEDIUM | Day 4 explicit re-verification of all 4 chat-v2 e2e BEFORE PR open |

### Sprint 57.7 + 57.8 + 57.9 lesson carry-forward (mandatory)

- **Day 0 三-prong including Schema (Prong 3)** — mandatory because NEW DB table; 6 prior sprints (55.5 + 56.1 + 56.3 + 57.1 + 57.3 + 57.4 + 57.7 + 57.8 + 57.9) validated 12-24× ROI
- **Best-effort try/except for correction_loop write hook** — Sprint 57.7 R1 sessions+tool_calls observer pattern (zero blocking on auxiliary persistence)
- **TenantContextMiddleware already populates user_id** — Sprint 57.7 D19 lesson; do NOT assume new infra needed before Day 0 探勘 confirms reachability from chat router → correction_loop
- **chat-v2 e2e regression sentinel** — Sprint 57.9 D-PRE-16 lesson; ANY change adding Panel to ChatLayout MUST re-verify 4 existing e2e in same PR
- **TanStack StrictMode mock pattern** — Sprint 57.9 D-PRE-15 lesson; use `retryClicked` flag pattern for VerificationList error retry e2e (NOT firstCall flag)
- **`*_QUERY_KEY_BASE` single-source export** — Sprint 57.9 pattern; both useVerificationRecent + useCorrectionTrace export as `as const` tuple
- **MHist 1-line max** — file-header-convention.md Sprint 55.3+ rule; all NEW files / MODIFY files header MHist single line ≤ E501
- **Plan/checklist format consistency** — Sprint 52.1 + 57.1 v1→v3 rewrite lesson; this plan mirrors Sprint 57.9 plan structure exactly

---

## Workload (calibrated)

### Bottom-up estimate

Per US bottom-up sum (see §Calibration table above): **~28 hr**

### Calibration: `large multi-domain` 0.55 (4th data point validation)

Weighted blend:
- US-1+US-2 backend (Alembic + REST + write hook + tests) ~8 hr × 0.55 = 4.4 hr
- US-3+US-4 frontend page (infra + page + 3 components) ~8 hr × 0.55 = 4.4 hr
- US-5 inline panel (chat-v2 integration) ~4 hr × 0.55 = 2.2 hr
- US-6 routing + e2e + closeout ~3 hr × 0.55 = 1.65 hr
- Day 0 + Day 4 fixed offset ~5 hr × 0.85 = 4.25 hr

**Calibrated commit ~16.9 hr** (round to **~17 hr** upper edge of user's "~14-16 hr extended" budget; +1 hr OVER user budget acceptable per multi-domain compounding).

### Calibration class baseline (extends 56.x evidence)

Per sprint-workflow.md §Calibration matrix:

```
large multi-domain (4 data points after 57.10):
  56.1 = 1.00 ✅
  56.3 = 1.04 ✅
  57.2 = 0.77 ⚠️ (under band)
  57.10 = TBD (Day 4 retro Q2)
  3-data-point mean BEFORE 57.10 = 0.94 ✅ in [0.85, 1.20] band
```

**Action**: KEEP `large multi-domain` 0.55 mid-band baseline. Day 4 retro Q2 logs 4th data point + 4-data-point mean update.

If 4-data-point mean drops below 0.85 → AD-Sprint-Plan-11 propose 0.50 lower-band shift.
If 4-data-point mean rises above 1.05 → KEEP 0.55 (still in band).

---

## Open questions for user (pending plan approval)

✅ All 4 scope questions PRE-CONFIRMED in chat session 2026-05-09:

| Q | User answer |
|---|-------------|
| Q1 Page entry | **Both**: standalone /verification page + inline panel inside chat-v2 |
| Q2 Backend depth | **NEW REST endpoint** /api/v1/verification (NEW Alembic 0017 verification_log table) |
| Q3 Sprint scope | **~14-16 hr extended ship** (calibrated commit ~16.9 hr; +1 hr OVER acceptable) |
| Q4 Day 0 verify | **Full 三-prong including Schema** (Prong 3 mandatory due to NEW backend table) |

**No outstanding questions for user.** Ready for plan + checklist review + Day 0 三-prong execution.

---

**End of Sprint 57.10 Plan**
