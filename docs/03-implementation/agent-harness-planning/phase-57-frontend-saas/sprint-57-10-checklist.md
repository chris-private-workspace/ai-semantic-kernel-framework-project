---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-10-checklist.md
Purpose: Sprint 57.10 day-by-day checklist — Verification real ship (standalone page + chat-v2 inline panel + NEW REST + Alembic 0017).
Category: Frontend / Backend / Cat 10 ship
Scope: Phase 57 / Sprint 57.10

Created: 2026-05-09 (drafted — pending user approval before Day 0 commit)
Last Modified: 2026-05-09

Modification History (newest-first):
    - 2026-05-09: Initial creation (Sprint 57.10)

Related: sprint-57-10-plan.md
---

# Sprint 57.10 — Checklist (Verification Real Ship — Frontend 7/N)

[See sprint-57-10-plan.md for full goal / USs / acceptance / risks / workload]

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation

- [ ] `git checkout main && git pull origin main` (verify HEAD f4b0467b post-PR #121 merge OR newer)
- [ ] `git checkout -b feature/sprint-57-10-verification-real-ship`
- [ ] Verify clean working tree: `git status` empty
- [ ] Verify branch base: `git log --oneline -3` shows f4b0467b at top

### 0.2 Pre-flight baseline capture

- [ ] Backend baseline: `cd backend && python -m pytest --co -q 2>&1 | tail -3` → record collected count (expect **1622 passed + 4 skipped** post-57.9)
- [ ] Frontend baseline: `cd frontend && npm run test -- --run 2>&1 | tail -5` → record Vitest count (expect **93 passed**)
- [ ] Playwright baseline: `cd frontend && npx playwright test --list 2>&1 | tail -3` → record e2e count (expect **27 specs**)
- [ ] V2 lint baseline: `python scripts/lint/run_all.py` → record `9/9 green` + total time
- [ ] Bundle baseline: `cd frontend && npm run build 2>&1 | grep "main"` → record main chunk kB (expect **240.86 kB**)
- [ ] Type check baseline: `cd frontend && npx tsc --noEmit 2>&1 | tail -3` → record errors (expect **0**)
- [ ] LLM SDK leak baseline: `python scripts/lint/check_llm_sdk_leak.py` → expect **0 leaks**

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)

#### Prong 1 — Path Verify (AD-Plan-2)

- [ ] Backend Cat 10 paths exist:
  - `Glob("backend/src/agent_harness/verification/correction_loop.py")` → 1 result ✓
  - `Glob("backend/src/api/v1/chat/_verifier_factory.py")` → 1 result ✓
  - `Glob("backend/src/agent_harness/_contracts/events.py")` → 1 result ✓
- [ ] Backend NEW paths do NOT exist (creates):
  - `Glob("backend/src/api/v1/verification.py")` → 0 results ✓
  - `Glob("backend/src/infrastructure/db/models/verification_log.py")` → 0 results ✓
  - `Glob("backend/src/infrastructure/db/repositories/verification_log.py")` → 0 results ✓
- [ ] Frontend stub path exists (modify):
  - `Glob("frontend/src/pages/verification/index.tsx")` → 1 result ✓
- [ ] Frontend NEW paths do NOT exist (creates):
  - `Glob("frontend/src/features/verification/**")` → 0 results ✓
  - `Glob("frontend/tests/e2e/verification-real-ship.spec.ts")` → 0 results ✓
- [ ] chat-v2 modify paths exist:
  - `Glob("frontend/src/pages/chat-v2/index.tsx")` → 1 result ✓
  - `Glob("frontend/src/features/chat-v2/store/chatStore.ts")` → 1 result ✓
  - `Glob("frontend/src/features/chat-v2/hooks/useChatStream.ts")` → 1 result ✓

#### Prong 2 — Content Verify (AD-Plan-3)

- [ ] Verify SSE events `verification_passed` + `verification_failed` actually emit from chat router (Day 0 critical):
  - `Grep("verification_passed|verification_failed", path="backend/src/api/v1/chat/sse.py")` → ≥2 hits expected (mapping in `serialize_loop_event`)
  - `Grep("VerificationPassed|VerificationFailed", path="backend/src/agent_harness/verification/correction_loop.py")` → ≥2 hits expected (yield sites)
- [ ] Verify NO `VerificationStarted` event exists (US-5 inline panel does NOT need it):
  - `Grep("VerificationStarted|verification_started", path="backend/src/agent_harness")` → 0 results expected
- [ ] Verify `correction_loop.run_with_verification()` signature for write hook insertion point:
  - `Grep("async def run_with_verification", path="backend/src/agent_harness/verification/correction_loop.py")` → 1 hit + read 30 lines after for state.tenant_id reachability
- [ ] Verify `useChatStream` SSE event iteration pattern (US-5 mod target):
  - `Grep("type === \"|switch.*event.type", path="frontend/src/features/chat-v2/hooks/useChatStream.ts")` → confirm if/switch pattern for adding 2 branches
- [ ] Verify ChatLayout structure (US-5 mount slot):
  - `Read("frontend/src/pages/chat-v2/index.tsx")` → identify where to mount `<VerificationPanel />` (likely below event stream, above input box)
- [ ] Verify routes.config.ts entry shape for verification (US-6):
  - `Grep("verification|Verification", path="frontend/src/routes.config.ts")` → confirm placeholder entry exists with `active: false`
- [ ] Verify audit endpoint pattern for RBAC reuse (US-2):
  - `Grep("require_audit_role", path="backend/src/api/v1")` → confirm helper available
- [ ] Verify `get_db_session_with_tenant` available for correction_loop write hook:
  - `Grep("get_db_session_with_tenant|get_db_session\\b", path="backend/src/infrastructure/db")` → confirm helper signature
- [ ] Verify `fetchWithAuth` helper exists for verificationService:
  - `Glob("frontend/src/features/auth/services/fetchWithAuth.ts")` → 1 result expected
- [ ] Verify `AppShellV2` component exists for page wrap:
  - `Glob("frontend/src/components/AppShellV2.tsx")` → 1 result expected

#### Prong 3 — Schema Verify (AD-Plan-4 — mandatory due to NEW table)

- [ ] Verify Alembic head version (next migration number):
  - `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3` → identify next available `00XX_*` number (plan assumes 0017; confirm or shift to 0018)
- [ ] Verify `tenants` table exists for FK reference:
  - `Grep("CREATE TABLE tenants|class Tenant\\(", path="backend/src/infrastructure/db")` → 1+ hits expected
- [ ] Verify RLS pattern (multi-tenant 鐵律):
  - `Grep("ENABLE ROW LEVEL SECURITY|tenant_isolation_", path="backend/src/infrastructure/db/migrations/versions")` → confirm prior migration RLS pattern (mirror in 0017)
- [ ] Verify check_rls_policies.py 8th lint baseline:
  - `python backend/scripts/check_rls_policies.py` → expect 0 gaps + record table count baseline
- [ ] Verify NO `verification_log` table exists yet:
  - `Grep("verification_log|VerificationLog", path="backend/src/infrastructure/db")` → 0 results expected (plan-time)
- [ ] Verify `sessions` table state (FK or no-FK decision per plan §US-1):
  - `Grep("class Session\\(|CREATE TABLE sessions", path="backend/src/infrastructure/db")` → confirm sessions table presence; decide whether session_id FK or just UUID column

#### Catalog drift findings

- [ ] In progress.md Day 0 entry, catalog any drift findings as `D-PRE-N` with severity (🔴 RED critical / 🟠 YELLOW informational / 🟢 GREEN well-aligned)
- [ ] If drift findings shift scope > 20% → revise plan §Acceptance Criteria + §Workload + re-confirm with user
- [ ] If drift findings shift scope 10-20% → note in plan §Risks + proceed
- [ ] If drift findings shift scope < 10% → proceed Day 1 with risk noted

### 0.4 Calibration baseline confirmation

- [ ] Confirm `large multi-domain` 0.55 baseline applies (4th data point validation)
- [ ] Confirm bottom-up est ~28 hr × 0.55 = ~16.9 hr commit (round to ~17 hr; +1 hr OVER user's "~14-16 hr" budget acceptable per multi-domain compounding)
- [ ] Document in progress.md Day 0 entry: "Calibration `large multi-domain` 0.55 4th data point; expected ratio range [0.85, 1.20]; bottom-up est 28 hr / committed ~17 hr"

### 0.5 User decision points cleared (pre-confirmed via plan §Open questions)

- [ ] Q1 Page entry = **Both** standalone + inline panel ✅
- [ ] Q2 Backend depth = **NEW REST endpoint /api/v1/verification** ✅
- [ ] Q3 Sprint scope = **~14-16 hr extended ship** (calibrated ~17 hr +1 OVER) ✅
- [ ] Q4 Day 0 verify = **Full 三-prong including Schema** (Prong 3 mandatory) ✅

### 0.6 Day 0 commit

- [ ] Stage plan + checklist + progress.md Day 0 entry: `git add docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-10-{plan,checklist}.md docs/03-implementation/agent-harness-execution/phase-57/sprint-57-10/progress.md`
- [ ] Commit: `git commit -m "chore(sprint-57-10, planning): Day 0 plan + checklist + 三-prong findings"`

---

## Day 1 — US-1 + US-2 Backend (Alembic 0017 + REST + write hook)

### 1.1 US-1: VerificationLog ORM model

- [ ] Create `backend/src/infrastructure/db/models/verification_log.py` with `VerificationLog(Base)` ORM class
  - Columns: id BIGSERIAL PK / tenant_id UUID NOT NULL FK / session_id UUID NOT NULL / turn_index INT default 0 / verifier_name VARCHAR(128) / verifier_type VARCHAR(32) / passed BOOLEAN / score DOUBLE PRECISION nullable / reason TEXT nullable / suggested_correction TEXT nullable / correction_attempt INT default 0 / created_at TIMESTAMPTZ default NOW()
  - File header MHist 1-line max per .claude/rules/file-header-convention.md
- [ ] Verify import works: `python -c "from infrastructure.db.models.verification_log import VerificationLog; print(VerificationLog.__tablename__)"` → `verification_log`
- [ ] DoD: import zero error + tablename verified

### 1.2 US-1: Alembic 0017 migration

- [ ] Create `backend/src/infrastructure/db/migrations/versions/0017_verification_log.py` (or 0018 per Day 0 Prong 3 head verify)
  - upgrade(): CREATE TABLE verification_log + ALTER TABLE ENABLE ROW LEVEL SECURITY + CREATE POLICY tenant_isolation_verification_log + 3 indexes
  - downgrade(): DROP POLICY + DISABLE RLS + DROP INDEX × 3 + DROP TABLE
- [ ] Test migration: `cd backend && alembic upgrade head` → verify table created via `psql -c "\d+ verification_log"`
- [ ] Test downgrade: `alembic downgrade -1 && alembic upgrade head` → verify clean roundtrip
- [ ] DoD: migration up/down clean + RLS policy verified

### 1.3 US-1: VerificationLogRepository

- [ ] Create `backend/src/infrastructure/db/repositories/verification_log.py` with:
  - `class VerificationLogRepository:`
  - `async def insert(session, tenant_id, session_id, turn_index, verifier_name, verifier_type, passed, score, reason, suggested_correction, correction_attempt) -> int` returns inserted id
  - `async def list_recent(session, tenant_id, session_id_filter, verifier_type_filter, passed_filter, limit, offset) -> tuple[list[VerificationLog], int, bool]` returns (items, total, has_more)
  - `async def list_correction_trace(session, tenant_id, session_id) -> list[VerificationLog]` returns sorted entries
- [ ] DoD: 3 methods importable + zero mypy strict errors

### 1.4 US-1: 8th V2 lint check + 1 unit test

- [ ] Run `python backend/scripts/check_rls_policies.py` → expect 0 gaps (verification_log policy detected)
- [ ] Create `backend/tests/unit/infrastructure/db/test_verification_log_schema.py` with 1 test verifying ORM model + tablename + RLS policy presence (via inspect schema)
- [ ] Run `cd backend && python -m pytest tests/unit/infrastructure/db/test_verification_log_schema.py -v` → 1/1 pass
- [ ] DoD: 9/9 V2 lints green + +1 pytest

### 1.5 US-2: NEW /api/v1/verification router

- [ ] Create `backend/src/api/v1/verification.py` with:
  - Pydantic models: `VerificationLogItem` (12 fields) + `VerificationLogPage` (items / total / has_more) + `CorrectionTraceResponse` (session_id / entries)
  - Router: `GET /recent` with Query params session_id / verifier_type / passed / limit / offset + Depends(get_current_user) + Depends(require_audit_role)
  - Router: `GET /{session_id}/correction-trace` + 404 if empty + same RBAC
- [ ] Register router in `backend/src/api/v1/__init__.py` or `backend/src/api/v1/router.py`
- [ ] Verify endpoint: `cd backend && python -m uvicorn api.main:app --port 8000 &` then `curl http://localhost:8000/openapi.json | jq '.paths."/api/v1/verification/recent"'` → endpoint registered
- [ ] DoD: 2 endpoints in OpenAPI schema + RBAC dep wired

### 1.6 US-2: correction_loop write hook

- [ ] Add `VERIFICATION_LOG_PERSIST_ENABLED: bool = True` to `backend/src/core/config.py` Settings
- [ ] Modify `backend/src/agent_harness/verification/correction_loop.py`:
  - Import VerificationLogRepository + get_db_session_with_tenant + settings + logger
  - After each `yield VerificationPassed(...)` AND `yield VerificationFailed(...)`, add best-effort try/except write hook (per plan §Technical Specifications)
  - Pass `attempt_num` correctly (0 for first attempt, 1 for first correction, ...)
- [ ] DoD: write hook compiles + zero mypy strict errors + existing 54.1 Cat 10 unit tests pass (regression sentinel)

### 1.7 US-2: 8-10 integration tests + 3 best-effort hook unit tests

- [ ] Create `backend/tests/integration/api/test_verification.py` with:
  - test_recent_happy: insert 2 + GET /recent + assert 2 items + has_more false
  - test_recent_filter_session: insert 3 (2 in session A + 1 in session B) + filter session_id → 2 items
  - test_recent_filter_verifier_type: filter `rules_based` only → exclude llm_judge entries
  - test_recent_filter_passed: filter passed=false → only failed entries
  - test_recent_pagination: insert 60 + limit=50 offset=0 → 50 items + has_more true; offset=50 → 10 items + has_more false
  - test_recent_403_without_audit_role: dummy user without audit role → 403
  - test_correction_trace_404_empty: GET /{uuid}/correction-trace → 404
  - test_correction_trace_happy: insert 3 entries (turn 0 attempt 0 / turn 0 attempt 1 / turn 1 attempt 0) + GET → sorted correctly
  - test_recent_multi_tenant_rls: Tenant A insert + Tenant B GET → 0 items (RLS enforced)
- [ ] Create `backend/tests/unit/agent_harness/verification/test_correction_loop_persist.py` with:
  - test_persist_passed: simulate verifier passed → verification_log inserted
  - test_persist_failed: simulate verifier failed → verification_log inserted
  - test_persist_failure_silent: mock VerificationLogRepository.insert raising → loop continues (no exception bubbles)
- [ ] Run `cd backend && python -m pytest tests/integration/api/test_verification.py tests/unit/agent_harness/verification/test_correction_loop_persist.py -v` → 11-13/11-13 pass
- [ ] DoD: pytest 1622 → 1633+ baseline raised by 11-13

### 1.8 Day 1 wrap

- [ ] Run full backend regression: `cd backend && python -m pytest -q` → expect 1633+ pass / 4 skip / 0 fail
- [ ] Run mypy strict: `cd backend && python -m mypy src --strict` → 0 errors
- [ ] Run flake8 + black + isort: `cd backend && black --check src && isort --check src && flake8 src` → all silent
- [ ] V2 lints: `python scripts/lint/run_all.py` → 9/9 green
- [ ] Commit Day 1: `git add backend/ && git commit -m "feat(sprint-57-10, US-1+US-2): backend Alembic 0017 verification_log + REST router + correction_loop write hook + 11-13 tests"`

---

## Day 2 — US-3 Frontend Infra + US-4 Page Wrap + 1 Component

### 2.1 US-3: features/verification/types.ts

- [ ] Create `frontend/src/features/verification/types.ts` with:
  - `VerifierType` type union (`'rules_based' | 'llm_judge' | 'external'`)
  - `VerificationLogItem` interface (12 fields mirror backend Pydantic)
  - `VerificationLogPage` interface (items / total / has_more)
  - `VerificationLogFilter` interface (session_id? / verifier_type? / passed? / limit / offset)
  - `CorrectionTraceResponse` interface (session_id / entries)
  - `VerificationEvent` interface (mirrors SSE payload from sse.py:248-265)
- [ ] DoD: `cd frontend && npx tsc --noEmit` → 0 errors

### 2.2 US-3: verificationService.ts

- [ ] Create `frontend/src/features/verification/services/verificationService.ts` with:
  - `fetchVerificationRecent(filter, signal?)` consuming GET `/api/v1/verification/recent` via fetchWithAuth + URLSearchParams omit-undefined helper
  - `fetchCorrectionTrace(sessionId)` consuming GET `/api/v1/verification/{session_id}/correction-trace`
  - Both throw Error with detail message on non-2xx
- [ ] Create `frontend/tests/unit/verification/verificationService.test.ts` (mirror Sprint 57.9 service test pattern with `expect.objectContaining({ credentials: "include" })`)
- [ ] DoD: 2 service tests pass + tsc 0 errors

### 2.3 US-3: useVerificationRecent + useCorrectionTrace hooks

- [ ] Create `frontend/src/features/verification/hooks/useVerificationRecent.ts` with `VERIFICATION_RECENT_QUERY_KEY_BASE` single-source export
- [ ] Create `frontend/src/features/verification/hooks/useCorrectionTrace.ts` with `CORRECTION_TRACE_QUERY_KEY_BASE` single-source export
- [ ] Create `frontend/tests/unit/verification/useVerificationRecent.test.tsx` (3 tests: BASE export / filter changes refetch / disabled when filter invalid)
- [ ] Create `frontend/tests/unit/verification/useCorrectionTrace.test.tsx` (3 tests: BASE export / enabled gate when sessionId null / fetch when provided)
- [ ] DoD: 4 NEW Vitest pass; Vitest 93 → 97+

### 2.4 US-3 + US-4: VerifierTypeBadge component (shared US-4 + US-5)

- [ ] Create `frontend/src/features/verification/components/VerifierTypeBadge.tsx` with 3 type variants (Tailwind utility classes; no inline styles per .claude/rules/frontend-react.md)
  - rules_based → blue: `bg-blue-100 text-blue-800`
  - llm_judge → purple: `bg-purple-100 text-purple-800`
  - external → gray: `bg-gray-100 text-gray-800`
- [ ] Create `frontend/tests/unit/verification/VerifierTypeBadge.test.tsx` (3 tests for variants)
- [ ] DoD: 3 NEW Vitest pass; Vitest 97 → 100+

### 2.5 US-4: pages/verification/index.tsx page wrap

- [ ] REPLACE `frontend/src/pages/verification/index.tsx` with composed real ship per plan §Technical Specifications:
  - Auth gate via Navigate to /auth/login + setPostLoginRedirect("/verification")
  - AppShellV2 wrap pageTitle="Verification"
  - 2-tab NavLink (Recent / Correction Trace)
  - Nested Routes index → Navigate to "recent" / "recent" → VerificationList stub / "timeline" → CorrectionTraceView stub
- [ ] Update `frontend/src/pages/verification/README.md` (Phase reference 54.1 → 57.10 shipped)
- [ ] DoD: page mounts via routes; auth gate redirects when not authenticated; 2 tabs visible

### 2.6 US-4: VerificationList + CorrectionTraceView stubs

- [ ] Create `frontend/src/features/verification/components/VerificationList.tsx` STUB (returns `<div>VerificationList Day 3</div>` for now; full impl Day 3)
- [ ] Create `frontend/src/features/verification/components/CorrectionTraceView.tsx` STUB (same pattern)
- [ ] DoD: stubs importable + 0 tsc errors; allows page to mount Day 2 wrap test

### 2.7 Day 2 wrap

- [ ] Run frontend Vitest: `cd frontend && npm run test -- --run` → 100+ pass
- [ ] Run tsc strict: `cd frontend && npx tsc --noEmit` → 0 errors
- [ ] Run ESLint: `cd frontend && npm run lint` → silent
- [ ] Commit Day 2: `git add frontend/ && git commit -m "feat(sprint-57-10, US-3+US-4 partial): verification feature folder infra + page wrap + VerifierTypeBadge + Day 3 stubs"`

---

## Day 3 — US-4 Complete + US-5 Inline Panel

### 3.1 US-4: VerificationList full implementation

- [ ] Replace stub with full implementation:
  - useVerificationRecent hook consumption
  - Filter form: 3 fields (session_id input / verifier_type dropdown / passed dropdown {Any / Passed / Failed})
  - Apply / Reset buttons (no debounce per AP-6)
  - Paginated table: 50 rows default; 6 columns (timestamp / session_id truncated / verifier_name / VerifierTypeBadge / passed badge / score / reason snippet 80 chars)
  - Click row → navigate to `/verification/timeline?session_id={id}`
  - Empty state with Reset Filters button
  - Loading skeleton (5-row mirror Sprint 57.9 ApprovalList)
  - Error retry UX with `retryClicked` flag pattern (Sprint 57.9 D-PRE-15)
  - Prev / Next pagination footer
- [ ] Create `frontend/tests/unit/verification/VerificationList.test.tsx` (3 tests: renders + filter form + click row navigates)
- [ ] DoD: 3 NEW Vitest pass; Vitest 100 → 103+

### 3.2 US-4: CorrectionTraceView full implementation

- [ ] Replace stub with full implementation:
  - useCorrectionTrace hook consumption (session_id from useSearchParams)
  - Vertical timeline UI: entries grouped by turn_index then sorted by correction_attempt
  - Each entry card: verifier_name + VerifierTypeBadge + passed/failed icon (✅/❌) + reason (if failed) + suggested_correction (if failed) + score (if present) + correction_attempt indicator
  - Visual distinction: passed entries = green left border; failed = red left border
  - Empty state: "No correction trace for session {id}" if 404 / null sessionId
- [ ] Create `frontend/tests/unit/verification/CorrectionTraceView.test.tsx` (3 tests: renders timeline + grouped by turn / 404 empty / null sessionId)
- [ ] DoD: 3 NEW Vitest pass; Vitest 103 → 106+

### 3.3 US-5: chatStore.ts verifications slice + reducers

- [ ] Modify `frontend/src/features/chat-v2/store/chatStore.ts`:
  - Add `verifications: VerificationEvent[]` to ChatStore interface
  - Add `appendVerification(event: VerificationEvent)` reducer
  - Add `clearVerifications()` reducer (called on session reset / new chat)
- [ ] Update `frontend/tests/unit/chat-v2/chatStore.test.ts` with 2 NEW tests (appendVerification + clearVerifications)
- [ ] DoD: 2 NEW Vitest pass; Vitest 106 → 108+

### 3.4 US-5: useChatStream.ts SSE event branches

- [ ] Modify `frontend/src/features/chat-v2/hooks/useChatStream.ts`:
  - Add 2 SSE event type branches: `verification_passed` + `verification_failed`
  - Map SSE payload → VerificationEvent → call `chatStore.appendVerification()`
  - Verify Day 0 探勘 confirmed iteration pattern (if/switch based on event.type)
- [ ] Add 1 Vitest test in `frontend/tests/unit/chat-v2/useChatStream.test.ts` (or new file): SSE verification_passed routes to store
- [ ] DoD: +1 Vitest pass; Vitest 108 → 109+

### 3.5 US-5: VerificationPanel component + chat-v2 mount

- [ ] Create `frontend/src/features/verification/components/VerificationPanel.tsx`:
  - Subscribes to chatStore selector for verifications array
  - Compact card per entry: verifier_name + VerifierTypeBadge + passed/failed icon + reason snippet if failed + correction_attempt counter
  - Hidden when verifications.length === 0 (no empty card; conditional render at top)
  - Tailwind utility classes
- [ ] Modify `frontend/src/pages/chat-v2/index.tsx`:
  - Mount `<VerificationPanel />` inside ChatLayout below event stream (exact slot per Day 0 探勘 D-PRE-N finding)
- [ ] Create `frontend/tests/unit/verification/VerificationPanel.test.tsx` (3 tests: renders 2 events / hidden when empty / VerifierTypeBadge integration)
- [ ] DoD: 3 NEW Vitest pass; Vitest 109 → 112+

### 3.6 Day 3 wrap

- [ ] Run frontend Vitest: `cd frontend && npm run test -- --run` → 112+ pass
- [ ] Run tsc strict: 0 errors
- [ ] Run ESLint: silent
- [ ] Run Vite build: `cd frontend && npm run build` → check main chunk ≤ 285 kB
- [ ] Commit Day 3: `git add frontend/ && git commit -m "feat(sprint-57-10, US-4 complete + US-5): VerificationList + CorrectionTraceView + VerificationPanel + chatStore + useChatStream"`

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

- [ ] Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-10/retrospective.md` with Q1-Q7:
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
  - Body: Sprint 57.10 closure summary (USs delivered / pytest delta / Vitest delta / Playwright delta / calibration ratio / D-PRE findings / new ADs)
- [ ] Update `MEMORY.md` index: +1 line entry under ~150 chars

### 4.7 Doc syncs (3/4; CLAUDE.md deferred to post-merge closeout PR per 57.7+57.8+57.9 pattern)

- [ ] Update `.claude/rules/sprint-workflow.md` §Calibration matrix:
  - Add 1 row: `large multi-domain` 0.55 4th data point 57.10=X.XX (whatever Day 4 ratio)
  - Update 3-data-point mean to 4-data-point mean
- [ ] Update `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md`:
  - §9 milestones table: NEW row Sprint 57.10 entry
  - §11 (or wherever Open Items live): NEW carryover ADs
- [ ] Update `docs/03-implementation/agent-harness-planning/16-frontend-design.md`:
  - V2 Ship Timeline 6/N → 7/N
  - Verification promoted from "placeholder" to "shipped" with main HEAD SHA (post-merge)
- [ ] CLAUDE.md sync DEFERRED to post-merge closeout PR per Sprint 57.7+57.8+57.9 pattern

### 4.8 PR open + closeout sync

- [ ] Commit Day 4: `git add . && git commit -m "feat(sprint-57-10, US-6 + closeout): routing + Playwright e2e + 3 doc syncs + retrospective + memory snapshot"`
- [ ] Push branch: `git push -u origin feature/sprint-57-10-verification-real-ship`
- [ ] Open PR via `gh pr create` with title "Sprint 57.10 — Verification Real Ship + NEW /verification REST + Alembic 0017 + chat-v2 inline Panel" + body summary
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

**End of Sprint 57.10 Checklist**
