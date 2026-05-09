---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-11-checklist.md
Purpose: Sprint 57.11 day-by-day checklist — Verification real ship + AD-Frontend-SSE-Silent-Drop-Fix bundle (standalone page + chat-v2 inline panel + NEW REST + Alembic 0017 + D-PRE-13 SSE silent drop fix per CONVENTION.md §7).
Category: Frontend / Backend / Cat 10 ship + SSE bug fix bundle
Scope: Phase 57 / Sprint 57.11

Created: 2026-05-09 (drafted from commit `6e11a9d9` Sprint 57.10 v1 checklist + AD-Frontend-SSE-Silent-Drop-Fix bundle context — pending user approval before Day 0 commit)
Last Modified: 2026-05-09

Modification History (newest-first):
    - 2026-05-09: base SHA refresh — main `412f26d6` → `7c6d0d50` (PR #124 Hybrid fix-up landed)
    - 2026-05-09: Sprint 57.11 — restored from commit `6e11a9d9` Sprint 57.10 v1 + add AD bundle Q5 + fresh Day 0 三-prong against main `412f26d6`
    - 2026-05-09: Initial creation (Sprint 57.10 v1; later PIVOTED to Convention Codification per user reality-check)

Related: sprint-57-11-plan.md
---

# Sprint 57.11 — Checklist (Verification Real Ship — Frontend 7/N)

[See sprint-57-11-plan.md for full goal / USs / acceptance / risks / workload]

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation

- [x] `git checkout main && git pull origin main` (verify HEAD `7c6d0d50` post-PR #124 Hybrid load fix-up squash merge OR newer)
- [x] `git checkout -b feature/sprint-57-11-verification-real-ship`
- [x] Verify clean working tree: `git status` empty (NB: Sprint 57.11 untracked drafts present, intentional — land in §0.6 commit)
- [x] Verify branch base: `git log --oneline -3` shows `7c6d0d50` at top (PR #124 Hybrid load fix-up squash) + `412f26d6` second (Sprint 57.10 closeout PR #123) + `7d85df4c` third (Sprint 57.10 PIVOTED main ship PR #122)

### 0.2 Pre-flight baseline capture (post Sprint 57.10 PIVOTED)

- [x] Backend baseline: `cd backend && python -m pytest --co -q 2>&1 | tail -3` → record collected count (expect **1622 passed + 4 skipped** baseline maintained Sprint 57.10) — actual: 1622 collected ✅
- [x] Frontend baseline: `cd frontend && npm run test -- --run 2>&1 | tail -5` → record Vitest count (expect **93 passed** Sprint 57.10 baseline maintained) — actual: 93 passed (28 files, 4.20s) ✅
- [x] Playwright baseline: `cd frontend && npx playwright test --list 2>&1 | tail -3` → record e2e count (expect **27 specs** Sprint 57.10 baseline maintained) — actual: 27 / 9 files ✅
- [x] V2 lint baseline: `python scripts/lint/run_all.py` → record `9/9 green` + total time (expect ~0.90s post Sprint 57.10) — actual: 9/9 green 0.92s ✅
- [x] Bundle baseline: `cd frontend && npm run build 2>&1 | grep "main"` → record main chunk kB (expect **240.89 kB** Sprint 57.10 baseline) — actual: 236K (~241.66 kB; ~0.3% var) ✅
- [x] Type check baseline: `cd frontend && npx tsc --noEmit 2>&1 | tail -3` → record errors (expect **0**) — actual: 0 ✅
- [x] LLM SDK leak baseline: `python scripts/lint/check_llm_sdk_leak.py` → expect **0 leaks** — actual: 0 (within V2 lints 9/9) ✅
- [x] CONVENTION.md / STYLE.md present check (Sprint 57.10 NEW): `Glob("frontend/CONVENTION.md")` + `Glob("frontend/STYLE.md")` → 1 result each ✓ — both present ✅

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)

#### Prong 1 — Path Verify (AD-Plan-2)

- [x] Backend Cat 10 paths exist:
  - `Glob("backend/src/agent_harness/verification/correction_loop.py")` → 1 result ✓
  - `Glob("backend/src/api/v1/chat/_verifier_factory.py")` → 1 result ✓
  - `Glob("backend/src/agent_harness/_contracts/events.py")` → 1 result ✓
- [x] Backend NEW paths do NOT exist (creates):
  - `Glob("backend/src/api/v1/verification.py")` → 0 results ✓
  - `Glob("backend/src/infrastructure/db/models/verification_log.py")` → 0 results ✓
  - `Glob("backend/src/infrastructure/db/repositories/verification_log.py")` → 0 results ✓
- [x] Frontend stub path exists (modify):
  - `Glob("frontend/src/pages/verification/index.tsx")` → 1 result ✓
- [x] Frontend NEW paths do NOT exist (creates):
  - `Glob("frontend/src/features/verification/**")` → 0 results ✓ (NB: `README.md` 1 found — innocuous, not blocking)
  - `Glob("frontend/tests/e2e/verification-real-ship.spec.ts")` → 0 results ✓
- [x] chat-v2 modify paths exist (⚠️ D-PRE-1 / D-PRE-2 drift — see progress.md):
  - `Glob("frontend/src/pages/chat-v2/index.tsx")` → 1 result ✓
  - `Glob("frontend/src/features/chat-v2/store/chatStore.ts")` → 0 results ⚠️ (real path uses underscore: `features/chat_v2/store/chatStore.ts`)
  - `Glob("frontend/src/features/chat-v2/hooks/useChatStream.ts")` → 0 results ⚠️ (real name: `features/chat_v2/hooks/useLoopEventStream.ts`)

#### Prong 2 — Content Verify (AD-Plan-3)

- [x] Verify SSE events `verification_passed` + `verification_failed` actually emit from chat router (Day 0 critical):
  - `Grep("verification_passed|verification_failed", path="backend/src/api/v1/chat/sse.py")` → 2 hits L250+L260 ✅ (mapping in `serialize_loop_event`)
  - `Grep("VerificationPassed|VerificationFailed", path="backend/src/agent_harness/verification/correction_loop.py")` → 4+ yield sites L13/44/58-59/84-85/149/156 ✅
- [x] Verify NO `VerificationStarted` event exists (US-5 inline panel does NOT need it):
  - `Grep("VerificationStarted|verification_started", path="backend/src/agent_harness")` → 0 results ✅
- [x] Verify `correction_loop.run_with_verification()` signature for write hook insertion point:
  - `Grep("async def run_with_verification", path="backend/src/agent_harness/verification/correction_loop.py")` → 1 hit L70-78 ✅; signature has `trace_context: TraceContext | None`; NO direct `tenant_id` param — resolved via D-PRE-4 `trace_context.tenant_id`
- [x] Verify `useChatStream` SSE event iteration pattern (US-5 mod target) — ⚠️ D-PRE-2 drift:
  - `Grep("type === \"|switch.*event.type", path="frontend/src/features/chat-v2/hooks/useChatStream.ts")` → 0 results ⚠️ (real name `useLoopEventStream.ts`; hook is thin pass-through; event-type dispatch in `chatStore.mergeEvent` per CONVENTION.md §7 — US-5 mod target shifts to store + chatService.parseSSEFrame)
- [x] Verify ChatLayout structure (US-5 mount slot):
  - `Read("frontend/src/pages/chat-v2/index.tsx")` → mount slot identification deferred to Day 3 US-5 implementation (header note for next-session AI)
- [x] Verify routes.config.ts entry shape for verification (US-6):
  - `Grep("verification|Verification", path="frontend/src/routes.config.ts")` → ✅ L140-145 found: `path: "/verification"`, `category: "admin"`, `active: false`
- [x] Verify audit endpoint pattern for RBAC reuse (US-2):
  - `Grep("require_audit_role", path="backend/src/api/v1")` → ✅ found at `platform_layer/identity/auth.py` (used by `audit.py:56,126`)
- [x] Verify `get_db_session_with_tenant` available for correction_loop write hook — ⚠️ D-PRE-6 drift:
  - `Grep("get_db_session_with_tenant|get_db_session\\b", path="backend/src/infrastructure/db")` → ✅ helper exists but at `platform_layer/middleware/tenant_context.py:179` (NOT `infrastructure/db/`). Re-import from `platform_layer.middleware`
- [x] Verify `fetchWithAuth` helper exists for verificationService — ⚠️ D-PRE-3 drift:
  - `Glob("frontend/src/features/auth/services/fetchWithAuth.ts")` → 0 results ⚠️ (real: exported from `authService.ts:74`; 7 prior services use `import { fetchWithAuth } from "../../auth/services/authService"`)
- [x] Verify `AppShellV2` component exists for page wrap:
  - `Glob("frontend/src/components/AppShellV2.tsx")` → 1 result ✅

#### Prong 3 — Schema Verify (AD-Plan-4 — mandatory due to NEW table)

- [x] Verify Alembic head version (next migration number):
  - `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3` → ✅ head = `0016_sla_and_cost_ledger.py`; **next = `0017`** (plan assumption confirmed; D-PRE-5)
- [x] Verify `tenants` table exists for FK reference:
  - `Grep("CREATE TABLE tenants|class Tenant\\(", path="backend/src/infrastructure/db")` → ✅ 2 hits (`models/identity.py` + `0014_phase56_1_saas_foundation.py`)
- [x] Verify RLS pattern (multi-tenant 鐵律):
  - `Grep("ENABLE ROW LEVEL SECURITY|tenant_isolation_", path="backend/src/infrastructure/db/migrations/versions")` → ✅ canonical at `0009_rls_policies.py` helper functions; recent example `0016_sla_and_cost_ledger.py` 3-table pattern (`sla_violations`/`sla_reports`/`cost_ledger`) — mirror in 0017
- [x] Verify check_rls_policies.py 8th lint baseline — ⚠️ D-PRE-7 path drift:
  - ~~`python backend/scripts/check_rls_policies.py`~~ → real path: `python scripts/lint/check_rls_policies.py` (already part of `scripts/lint/run_all.py` 9 lints) → ✅ 0 gaps; baseline `17 TenantScopedMixin / 18 RLS-protected / 13 whitelisted`
- [x] Verify NO `verification_log` table exists yet:
  - `Grep("verification_log|VerificationLog", path="backend/src/infrastructure/db")` → 0 results ✅ (plan-time clean)
- [x] Verify `sessions` table state (FK or no-FK decision per plan §US-1):
  - `Grep("class Session\\(|CREATE TABLE sessions", path="backend/src/infrastructure/db")` → ✅ exists at `models/sessions.py` — Day 1 US-1 decides FK vs no-FK per plan

#### Catalog drift findings

- [x] In progress.md Day 0 entry, catalog any drift findings as `D-PRE-N` with severity (🔴 RED critical / 🟠 YELLOW informational / 🟢 GREEN well-aligned) — 9 findings catalogued (0🔴/3🟠/6🟢)
- [x] If drift findings shift scope > 20% → revise plan §Acceptance Criteria + §Workload + re-confirm with user — N/A
- [x] If drift findings shift scope 10-20% → note in plan §Risks + proceed — N/A
- [x] If drift findings shift scope < 10% → proceed Day 1 with risk noted — ✅ scope shift < 5%; proceed Day 1 (drift detail in progress.md §Drift findings table)

### 0.4 Calibration baseline confirmation

- [x] Confirm `large multi-domain` 0.55 baseline applies (4th data point validation) — confirmed; 3-data-point window mean 0.94 ✅ in [0.85, 1.20] band
- [x] Confirm bottom-up est ~28 hr × 0.55 = ~16.9 hr commit (round to ~17 hr; +1 hr OVER user's "~14-16 hr" budget acceptable per multi-domain compounding) — confirmed
- [x] Document in progress.md Day 0 entry: "Calibration `large multi-domain` 0.55 4th data point; expected ratio range [0.85, 1.20]; bottom-up est 28 hr / committed ~17 hr" — ✅ documented in progress.md §0.4

### 0.5 User decision points cleared (pre-confirmed via plan §Open questions)

- [x] Q1 Page entry = **Both** standalone + inline panel ✅
- [x] Q2 Backend depth = **NEW REST endpoint /api/v1/verification** ✅
- [x] Q3 Sprint scope = **~14-16 hr extended ship** (calibrated ~17 hr +1 OVER) ✅
- [x] Q4 Day 0 verify = **Full 三-prong including Schema** (Prong 3 mandatory) ✅
- [x] **Q5 (NEW Sprint 57.11) AD bundle = AD-Frontend-SSE-Silent-Drop-Fix folded into US-5** per CONVENTION.md §7 codified 3-edit checklist ✅
- [x] User chose Option A (Bundle a+c) at chat session 2026-05-09: Sprint 57.11 = (a) Verification real ship + AD-Frontend-SSE-Silent-Drop-Fix bundle → Sprint 57.12 = (c) Agent Harness UI suite (LoopVisualizer + MemoryViewer + SubagentTree) ✅
- [x] Sprint 57.12 plan/checklist will be drafted at Sprint 57.11 closeout per rolling planning discipline (禁止預寫) ✅

### 0.6 Day 0 commit

- [x] Stage plan + checklist + progress.md Day 0 entry: `git add docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-11-{plan,checklist}.md docs/03-implementation/agent-harness-execution/phase-57/sprint-57-11/progress.md`
- [x] Commit: `git commit -m "chore(sprint-57-11, planning): Day 0 plan + checklist + 三-prong findings against main 7c6d0d50"` → ✅ commit `0dc110ea` (3 files / 1485 insertions)

---

## Day 1 — US-1 + US-2 Backend (Alembic 0017 + REST + write hook)

### 1.1 US-1: VerificationLog ORM model

- [x] Create `backend/src/infrastructure/db/models/verification_log.py` with `VerificationLog(Base)` ORM class
  - Columns: id BIGSERIAL PK / tenant_id UUID NOT NULL FK / session_id UUID NOT NULL / turn_index INT default 0 / verifier_name VARCHAR(128) / verifier_type VARCHAR(32) / passed BOOLEAN / score DOUBLE PRECISION nullable / reason TEXT nullable / suggested_correction TEXT nullable / correction_attempt INT default 0 / created_at TIMESTAMPTZ default NOW()
  - File header MHist 1-line max per .claude/rules/file-header-convention.md
- [x] Verify import works: 12 cols + 4 indexes + VerifierType enum confirmed via `python -c` import test ✅
- [x] DoD: import zero error + tablename verified — `verification_log` ✅

### 1.2 US-1: Alembic 0017 migration

- [x] Create `backend/src/infrastructure/db/migrations/versions/0017_verification_log.py`
  - upgrade(): CREATE TABLE + 4 indexes + RLS policy `verification_log_tenant_isolation` ✅
  - downgrade(): DROP POLICY + DISABLE RLS + DROP TABLE (indexes drop with table) ✅
- [x] Test migration: `alembic upgrade head` → 0017 applied; psql/SQLAlchemy verified RLS=true + policy + 5 indexes
- [x] Test downgrade: `alembic downgrade -1 && alembic upgrade head` → clean roundtrip verified
- [x] DoD: migration up/down clean + RLS policy verified ✅

### 1.3 US-1: VerificationLogRepository

- [x] Create `backend/src/infrastructure/db/repositories/verification_log.py` with:
  - `class VerificationLogRepository:` (DI pattern matching SessionRepository)
  - `async def insert(...) -> int` ✅
  - `async def list_recent(...) -> tuple[list[VerificationLog], int, bool]` ✅
  - `async def list_correction_trace(...) -> list[VerificationLog]` ✅
- [x] DoD: 3 methods importable + zero mypy strict errors ✅

### 1.4 US-1: 8th V2 lint check + 1 unit test

- [x] Run `python scripts/lint/check_rls_policies.py` (D-PRE-7 corrected path) → 0 gaps; baseline 17/18/13 → **18/19/13** ✅
- [x] Create `backend/tests/unit/infrastructure/db/test_verification_log_schema.py` — verifies tablename + RLS + policy + 5 indexes + CHECK constraint via pg_class/pg_policy/pg_indexes/pg_constraint
- [x] Run pytest schema test → 1/1 pass ✅
- [x] DoD: 9/9 V2 lints green + +1 pytest ✅

### 1.5 US-2: NEW /api/v1/verification router

- [x] Create `backend/src/api/v1/verification.py` with:
  - Pydantic models: `VerificationLogItem` (12 fields incl `created_at_ms` for JS Date interop) + `VerificationLogPage` (items / total / has_more / next_offset / page_size) + `CorrectionTraceResponse` (session_id / entries)
  - Router: `GET /recent` with Query params + `Depends(get_current_tenant)` + `Depends(require_audit_role)` + `Depends(get_db_session_with_tenant)` (D-PRE-6 corrected import)
  - Router: `GET /{session_id}/correction-trace` + 404 if empty + same RBAC ✅
- [x] Register router in `backend/src/api/main.py` (`include_router(verification_router, prefix="/api/v1")`)
- [x] Verify endpoint: `python -c create_app().openapi()` → `/api/v1/verification/recent` + `/api/v1/verification/{session_id}/correction-trace` registered ✅
- [x] DoD: 2 endpoints in OpenAPI schema + RBAC dep wired ✅

### 1.6 US-2: correction_loop write hook

- [x] Add `verification_log_persist_enabled: bool = True` to `backend/src/core/config/__init__.py` Settings (snake_case per existing convention; env override `VERIFICATION_LOG_PERSIST_ENABLED=false`)
- [x] Modify `backend/src/agent_harness/verification/correction_loop.py`:
  - Import logger + `get_settings` + `get_session_factory` + `text` + `VerificationLogRepository` ✅
  - Add `_persist_verification_event()` async helper (best-effort try/except + SET LOCAL app.tenant_id for RLS + repo.insert + commit; logs WARNING + returns on any Exception)
  - Call hook after each `yield VerificationPassed(...)` + `yield VerificationFailed(...)` site (verifier-level granularity per checklist)
  - Pass `correction_attempt=attempt` correctly; `tenant_id=trace_context.tenant_id if trace_context else None` (D-PRE-4 resolution); sentinel-skip if None
- [x] DoD: write hook compiles + zero mypy strict errors + existing 54.1 Cat 10 unit tests pass (46/46 regression sentinel ✅)

### 1.7 US-2: 8-10 integration tests + 3 best-effort hook unit tests

- [x] Create `backend/tests/integration/api/test_verification.py` (9 tests):
  - test_recent_happy ✅ / _filter_session ✅ / _filter_verifier_type ✅ / _filter_passed ✅
  - test_recent_pagination (60 rows / 50+10 split + has_more boundary) ✅
  - test_recent_403_without_audit_role ✅
  - test_correction_trace_404_empty ✅ / _happy_sorted (out-of-order insert verify ORDER BY) ✅
  - test_recent_multi_tenant_isolation (Tenant A insert / Tenant B GET → 0; WHERE clause filter) ✅
- [x] Create `backend/tests/unit/agent_harness/verification/test_correction_loop_persist.py` (3 tests):
  - test_persist_passed ✅ / test_persist_failed ✅ / test_persist_failure_silent (get_session_factory raises → loop unbroken) ✅
- [x] Run pytest → 12/12 pass + 1 schema test = 13/13 ✅
- [x] DoD: pytest 1622 → **1635** (+13; surpasses 1633+ target by 2) ✅

### 1.8 Day 1 wrap

- [x] Run full backend regression: pytest 1635 collected; 1627 passed + 4 skipped + 4 PRE-EXISTING failures (admin_tenant_patch ×3 + governance::test_list_rejects_non_approver_role; predates 7c6d0d50 main HEAD; AD-AdminTenant-Patch-Flake / AD-Governance-RBAC-Flake to be triaged at next audit cycle sprint)
- [x] Run mypy strict: 304 source files clean ✅
- [x] Run black + isort + flake8: all clean post-format ✅
- [x] V2 lints: 9/9 green (1.04s) ✅
- [x] Commit Day 1: ✅ commit `8a0ecaf3` (11 files / 1119 insertions) — `feat(sprint-57-11, US-1+US-2): backend Alembic 0017 verification_log + REST router + correction_loop write hook + 13 tests`

---

## Day 2 — US-3 Frontend Infra + US-4 Page Wrap + 1 Component

### 2.1 US-3: features/verification/types.ts

- [ ] Create `frontend/src/features/verification/types.ts` with:
  - `VerifierType` type union ✅
  - `VerificationLogItem` (12 fields mirror backend Pydantic incl created_at_ms epoch ms for JS Date) ✅
  - `VerificationLogPage` (items / total / has_more / next_offset / page_size) ✅
  - `VerificationLogFilter` ✅
  - `CorrectionTraceResponse` ✅
  - `VerificationEvent` discriminated union (mirrors sse.py:243-265) ✅
- [x] DoD: tsc --noEmit 0 errors ✅

### 2.2 US-3: verificationService.ts

- [x] Create verificationService.ts with fetchVerificationRecent + fetchCorrectionTrace + URLSearchParams omit-undefined helper (mirror Sprint 57.4 + 57.9 pattern); fetchWithAuth from authService.ts:74 (D-PRE-3 resolution)
- [x] Create verificationService.test.ts — **5 tests** (3 fetchVerificationRecent + 2 fetchCorrectionTrace) ✅
- [x] DoD: 5 service tests pass + tsc 0 errors ✅

### 2.3 US-3: useVerificationRecent + useCorrectionTrace hooks

- [x] Create useVerificationRecent.ts with VERIFICATION_RECENT_QUERY_KEY_BASE single-source ✅
- [x] Create useCorrectionTrace.ts with CORRECTION_TRACE_QUERY_KEY_BASE + enabled gate (sessionId !== null) ✅
- [x] useVerificationRecent.test.tsx (3 tests: BASE / fetch happy / error surface) ✅
- [x] useCorrectionTrace.test.tsx (3 tests: BASE / enabled-gate sessionId=null skip / fetch when provided) ✅
- [x] DoD: 6 NEW Vitest pass; Vitest 93 → 99 (passed §2.3 target 97+) ✅

### 2.4 US-3 + US-4: VerifierTypeBadge component (shared US-4 + US-5)

- [x] Create VerifierTypeBadge.tsx with 3 type variants (Tailwind utility classes; no inline styles per frontend-react.md) ✅
- [x] VerifierTypeBadge.test.tsx (3 tests for variants) ✅
- [x] DoD: 3 NEW Vitest pass; Vitest 99 → 102 (passed §2.4 target 100+) ✅

### 2.5 US-4: pages/verification/index.tsx page wrap

- [x] REPLACE Phase 49.1 placeholder with real ship: auth gate (Navigate /auth/login + setPostLoginRedirect("/verification")) + AppShellV2 wrap pageTitle="Verification" + 2-tab NavLink (Recent / Correction Trace) + nested Routes (mirror Sprint 57.9 governance/index.tsx) ✅
- [N/A] README.md update — file does not exist (verification page never had README); skip per scope-discipline (no orphan file creation)
- [x] DoD: page composes via routes; auth gate redirects when not authenticated; 2 tabs render ✅

### 2.6 US-4: VerificationList + CorrectionTraceView stubs

- [x] Create VerificationList.tsx STUB (Day 3 §3.1 full impl pending) ✅
- [x] Create CorrectionTraceView.tsx STUB (Day 3 §3.2 full impl pending) ✅
- [x] DoD: stubs importable + 0 tsc errors ✅

### 2.7 Day 2 wrap

- [x] Run frontend Vitest: 32 files / **107 passed** (Day 2 baseline 93 → 107; +14 surpasses 100+ §2.7 target by 7) ✅
- [x] Run tsc --noEmit: 0 errors ✅
- [x] Run ESLint: silent ✅
- [x] Commit Day 2: ✅ commit `9ea3f29b` (12 files / ~600 ins) — `feat(sprint-57-11, US-3+US-4 partial): verification feature folder infra + page wrap + VerifierTypeBadge + Day 3 stubs`

---

## Day 3 — US-4 Complete + US-5 Inline Panel

### 3.1 US-4: VerificationList full implementation ✅

- [x] Replace stub with full implementation: useVerificationRecent + 3-field filter form (session_id input / verifier_type dropdown / passed dropdown) + Apply/Reset buttons (no debounce per AP-6) + 6-col paginated table (50 rows; click row → navigate /verification/timeline?session_id=...) + empty state + 5-row loading skeleton + error retry UX (retryClicked per Sprint 57.9 D-PRE-15) + Prev/Next pagination footer ✅
- [x] VerificationList.test.tsx — 3 tests (renders + empty state + click navigates) ✅
- [x] DoD: 3 NEW Vitest pass; Vitest 102 → 105 ✅

### 3.2 US-4: CorrectionTraceView full implementation ✅

- [x] Replace stub with full implementation: useCorrectionTrace + useSearchParams session_id + entries grouped by turn_index (Map chunked) + per-entry card (icon + name + VerifierTypeBadge + reason + suggested_correction + score + correction_attempt indicator) + visual distinction (passed green / failed red left border) + 3 empty/missing states ✅
- [x] CorrectionTraceView.test.tsx — 3 tests (renders timeline grouped by turn / 404 empty / no-session) ✅
- [x] DoD: 3 NEW Vitest pass; Vitest 105 → 108 ✅

### 3.3 US-5: chatStore.ts verifications slice + reducers ✅

- [x] Modify `frontend/src/features/chat_v2/store/chatStore.ts` (D-PRE-1 corrected path: chat_v2 underscore): add `verifications: VerificationEvent[]` + appendVerification reducer + clearVerifications reducer + 2 NEW mergeEvent cases for verification_passed / verification_failed ✅
- [x] chatStore.verifications.test.ts — 3 tests (appendVerification + clearVerifications + mergeEvent SSE branch) ✅
- [x] DoD: 3 NEW Vitest pass; Vitest 108 → 111 ✅

### 3.4 US-5 + AD-Frontend-SSE-Silent-Drop-Fix bundle: types.ts + KNOWN events Set ✅

- [x] D-PRE-2 + D-PRE-8 resolved: SSE event-type dispatch in chatStore.mergeEvent (not useLoopEventStream hook). CONVENTION.md §7 codified 3-edit checklist applied:
  - chat_v2/types.ts: add VerificationPassedEvent + VerificationFailedEvent types to LoopEvent discriminated union ✅
  - chat_v2/types.ts: add "verification_passed" + "verification_failed" to KNOWN_LOOP_EVENT_TYPES Set ✅
  - chat_v2/store/chatStore.ts: 2 NEW mergeEvent cases (above §3.3) ✅
- [x] DoD: SSE silent-drop fixed; chatStore mergeEvent test verifies routing ✅ (covered in §3.3 test 3)

### 3.5 US-5: VerificationPanel component + chat-v2 mount ✅

- [x] Create VerificationPanel.tsx — subscribes to chatStore.verifications + compact per-entry card (verifier_name + VerifierTypeBadge + pass/fail icon + reason snippet if failed + suggested_correction + score) + hidden when empty (returns null) ✅
- [x] Modify pages/chat-v2/index.tsx — mount <VerificationPanel /> inside ChatLayout between MessageList and InputBar ✅
- [x] VerificationPanel.test.tsx — 3 tests (hidden empty / renders 2 entries with badge integration / score display) ✅
- [x] DoD: 3 NEW Vitest pass; Vitest 111 → 114 ✅

### 3.6 Day 3 wrap

- [x] Run frontend Vitest: 36 files / **119 passed** (Day 3 baseline 107 → 119; +12 surpasses 112+ §3.6 target by 7) ✅
- [x] Run tsc --noEmit: 0 errors ✅
- [x] Run ESLint: silent ✅
- [⚠️] Run Vite build: main chunk **294.96 kB** > 285 kB §3.6 ceiling by ~10 kB → AD-Bundle-Size-285kB-Carryover: Day 4 §4.1 lazy-load via routes.config.ts (mirror governance/audit-log pattern) expected to split verification chunk + drop main back under ceiling
- [x] Commit Day 3: ✅ commit `77e5a333` (10 files / ~1100 ins) — `feat(sprint-57-11, US-4 complete + US-5): VerificationList + CorrectionTraceView + VerificationPanel + chatStore + AD-Frontend-SSE-Silent-Drop-Fix bundle`

---

## Day 4 — US-6 Routing + e2e + Closeout

### 4.1 US-6: routes.config.ts wire-up

- [ ] Modify `frontend/src/routes.config.ts`:
  - verification entry: `active: false` → `active: true`
  - Add `component: () => import("./pages/verification")` lazy import
  - Add `icon: ShieldAlert` (or chosen icon per Day 0 探勘)
  - Confirm category (likely "operations")
- [ ] Verify sidebar shows verification link via `cd frontend && npm run dev` + browser visit `/`
- [ ] DoD: sidebar link visible + click navigates to /verification → auth gate fires

### 4.2 US-6: 4-6 Playwright e2e

- [ ] Create `frontend/tests/e2e/verification-real-ship.spec.ts` with:
  - `test('auth gate redirects to /auth/login when unauthenticated')`
  - `test('recent tab renders 2 mocked rows on happy path')` — mock GET /verification/recent
  - `test('filter verifier_type dropdown change refetches')` — assert 2nd fetch fires
  - `test('click recent table row navigates to /verification/timeline?session_id=...')` — assert URL change + correction trace renders
  - `test('empty state with Reset Filters button')` — mock empty response
  - (STRETCH) `test('chat-v2 inline panel renders verification_passed SSE event')` — if SSE mock injection too brittle → DEFER to AD-Verification-RealShip-E2E
- [ ] Each test uses `seedAuthJwt(page)` in beforeEach (Sprint 57.9 D-PRE-16 lesson)
- [ ] Run: `cd frontend && npx playwright test verification-real-ship.spec.ts --reporter=list` → 4-6 pass
- [ ] DoD: Playwright 27 → 31-33 (depending on stretch deferral)

### 4.3 US-6: chat-v2 e2e regression sentinel (Sprint 57.9 D-PRE-16 lesson)

- [ ] Run all chat-v2 e2e: `cd frontend && npx playwright test chat-v2 --reporter=list` → expect 4/4 pass (Sprint 57.8 baseline)
- [ ] If any fail (likely VerificationPanel mount changes ChatLayout selector) → fix selector in same PR (NOT defer)
- [ ] DoD: 4/4 chat-v2 e2e pass post-Panel mount

### 4.4 Full validation sweep (BLOCKER for Day 4 commit)

- [ ] Backend: `cd backend && python -m pytest -q && python -m mypy src --strict && black --check src && isort --check src && flake8 src` → all green; pytest 1633+ pass / 4 skip / 0 fail
- [ ] Frontend: `cd frontend && npm run test -- --run && npx tsc --noEmit && npm run lint && npm run build` → Vitest 112+ pass / tsc 0 / ESLint silent / build complete
- [ ] V2 lints: `python scripts/lint/run_all.py` → 9/9 green
- [ ] LLM SDK leak: `python scripts/lint/check_llm_sdk_leak.py` → 0 leaks
- [ ] Playwright: `cd frontend && npx playwright test --reporter=list` → 31-33 pass total (4-6 NEW + 27 existing)

### 4.5 Retrospective.md (Q1-Q7 mandatory format per Sprint 57.7+57.8+57.9 + sprint-workflow.md)

- [ ] Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-11/retrospective.md` with Q1-Q7:
  - Q1: What went well?
  - Q2: Calibration ratio = actual / committed; log 4-data-point `large multi-domain` mean update
  - Q3: What didn't go well? (include cascade lessons applied)
  - Q4: What carryover ADs? (e.g. AD-Verification-RealShip-E2E if SSE stretch deferred / AD-Cat10-Frontend-Panel partial close)
  - Q4.1: 16-frontend-design.md V2 Ship Timeline update
  - Q5: Phase 57.11+ direction — list 5 candidates per rolling planning 紀律 (do NOT commit; await user)
  - Q6: V2 紀律 9 項 self-check
  - Q7: Spike sprint design note? (N/A SKIP — feature ship NOT spike per Sprint 57.8+57.9 precedent)
- [ ] DoD: retrospective.md complete; all Q1-Q7 answered

### 4.6 Memory snapshot

- [ ] Create `C:\Users\Chris\.claude\projects\C--Users-Chris-Downloads-ai-semantic-kernel-framework-project\memory\project_phase57_10_verification_ship.md`
  - Frontmatter: name / description / type=project
  - Body: Sprint 57.11 closure summary (USs delivered / pytest delta / Vitest delta / Playwright delta / calibration ratio / D-PRE findings / new ADs)
- [ ] Update `MEMORY.md` index: +1 line entry under ~150 chars

### 4.7 Doc syncs (3/4; CLAUDE.md deferred to post-merge closeout PR per 57.7+57.8+57.9 pattern)

- [ ] Update `.claude/rules/sprint-workflow.md` §Calibration matrix:
  - Add 1 row: `large multi-domain` 0.55 4th data point 57.10=X.XX (whatever Day 4 ratio)
  - Update 3-data-point mean to 4-data-point mean
- [ ] Update `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md`:
  - §9 milestones table: NEW row Sprint 57.11 entry
  - §11 (or wherever Open Items live): NEW carryover ADs
- [ ] Update `docs/03-implementation/agent-harness-planning/16-frontend-design.md`:
  - V2 Ship Timeline 6/N → 7/N
  - Verification promoted from "placeholder" to "shipped" with main HEAD SHA (post-merge)
- [ ] CLAUDE.md sync DEFERRED to post-merge closeout PR per Sprint 57.7+57.8+57.9 pattern

### 4.8 PR open + closeout sync

- [ ] Commit Day 4: `git add . && git commit -m "feat(sprint-57-11, US-6 + closeout): routing + Playwright e2e + 3 doc syncs + retrospective + memory snapshot"`
- [ ] Push branch: `git push -u origin feature/sprint-57-11-verification-real-ship`
- [ ] Open PR via `gh pr create` with title "Sprint 57.11 — Verification Real Ship + NEW /verification REST + Alembic 0017 + chat-v2 inline Panel" + body summary
- [ ] After PR merge to main, capture main HEAD SHA
- [ ] Open closeout PR with CLAUDE.md sync (per Sprint 57.7+57.8+57.9 pattern)
- [ ] Merge closeout PR → main
- [ ] Update memory snapshot with merged main HEAD SHA

### 4.9 Day 4 closeout user decision points

- [ ] Confirm with user: Phase 57.11+ scope direction per Q5 retrospective 5 candidates (do NOT commit Phase 57.11 plan/checklist per rolling planning 紀律)
- [ ] Confirm with user: any of 4 NEW carryover ADs (Verification-RealShip-E2E / Cat10-Frontend-Panel partial close / etc.) need immediate attention vs Phase 57.x deferred

---

## 重要備註

### Rolling planning 紀律自檢(每 day 結束 + Day 4 closeout 必檢)

- ☐ 沒預寫 Phase 57.11+ plan/checklist
- ☐ 沒跳過 plan/checklist 直接 code
- ☐ 沒刪除未勾選的 [ ] 項目(stretch test 標 🚧 DEFERRED + AD reference)
- ☐ 沒在 retrospective.md Q5 寫具體 Phase 57.11 task(只列 5 candidates 等 user 選定)

### V2 紀律 9 項自檢(每 commit + 每 PR)

1. ☐ Server-Side First N/A frontend / ✅ backend (multi-tenant + RLS)
2. ☐ LLM Provider Neutrality ✅ (Cat 10 verifiers via ChatClient ABC; correction_loop write hook does NOT touch LLM SDK)
3. ☐ CC Reference 不照搬 N/A
4. ☐ 17.md Single-source ✅ (NEW VERIFICATION_RECENT_QUERY_KEY_BASE + CORRECTION_TRACE_QUERY_KEY_BASE exports + Cat 10 ABC unchanged)
5. ☐ 11+1 範疇 ✅ (Cat 10 Verification ship; backend/frontend separation per 02.md 5-layer)
6. ☐ 04 anti-patterns ✅ (AP-2 no orphan + AP-3 no scattering + AP-4 no Potemkin + AP-6 YAGNI no auth refactor + AP-9 verification preserved)
7. ☐ Sprint workflow ✅ (plan → checklist → Day 0 三-prong → code → progress → retro)
8. ☐ File header convention ✅ (MHist 1-line max per 55.3+ rule)
9. ☐ Multi-tenant rule ✅ (verification_log RLS + JWT via fetchWithAuth + tenant_id NOT NULL FK)

### Sprint 57.7 D19 + 57.8 D13 + 57.9 D-PRE-16 cascade lesson 強制執行(此 sprint 必行)

- **Sprint 57.7 D19 (assumed-blocked-but-not)** — Day 0 必驗證 correction_loop 是否能 reach state.tenant_id 寫入 verification_log;若已 reachable 則寫 hook ~30min 而非「假設需要 JWT extraction infra」
- **Sprint 57.8 D13 (dev DB pollution)** — Day 0 cleanup leftover verification_log rows BEFORE Day 1 (NEW table 此 sprint 無 issue;但 e2e fixtures 必須清理)
- **Sprint 57.9 D-PRE-16 (governance auth gate broke 5 prior e2e)** — Day 4 必行 4/4 chat-v2 e2e regression sentinel verification BEFORE PR open(VerificationPanel mount changes ChatLayout DOM)
- **Sprint 57.9 D-PRE-15 (TanStack StrictMode mock pattern)** — Day 4 e2e use `retryClicked` flag pattern for VerificationList error retry test(NOT firstCall flag)

### Open Items / Carry-forward(填入 retrospective Q4 + Q4.1)

- 🚧 **AD-Verification-RealShip-E2E** (POTENTIAL Day 4 deferral) — chat-v2 inline panel SSE injection test 可能因 brittle SSE mock 延後;mirror Sprint 57.9 governance e2e 4-case spec deferral
- 🚧 **AD-Cat10-Frontend-Panel** (PARTIAL CLOSE expected via this sprint) — original carryover from 54.1 retrospective; standalone page satisfies "verifier UI panel" intent + chat-v2 inline panel adds bonus live view
- 🚧 **AD-Verification-Log-Retention** (POTENTIAL NEW carryover) — verification_log 無 TTL / archival policy;production 增長後需 partition + retention strategy(Phase 58+ infrastructure scope)
- 🚧 **AD-Verification-AuditCorrelation** (POTENTIAL NEW carryover) — verification_log 與 audit_log 目前無 cross-reference;若需要「verifier failure → audit chain entry」可 Phase 58+ 加 join key
- 🚧 (其他 Day 4 retrospective Q4 catalogued ADs)

### Sprint workflow §Step 5 expansion candidate

- 若 retrospective Q7 N/A SKIP confirmed feature-ship pattern (3rd consecutive sprint after 57.8+57.9) → 可在 Phase 57.11+ 起 fold-in 「feature-ship vs spike sprint Day 4 closeout 對 design note 不同要求」明確 differential 到 sprint-workflow.md §Step 5.5

---

**End of Sprint 57.11 Checklist**
