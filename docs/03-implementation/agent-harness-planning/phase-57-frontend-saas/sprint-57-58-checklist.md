# Sprint 57.58 — Checklist

Plan: [`sprint-57-58-plan.md`](./sprint-57-58-plan.md)

**Class**: `mixed-multidomain-bundle` 0.65 (tier-2; 3 backend tracks + 1 frontend track)
**Agent-delegated**: yes (sequential 3-4 code-implementer agents)
**Agent-factor**: `mixed-multidomain-bundle-mechanical` 0.65 (tier-3 1st validation)
**Template**: mirrors `sprint-57-57-checklist.md` Day 0-2 structure

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] **Draft `sprint-57-58-plan.md` v1**
  - DoD: 9-section structure mirroring 57.57; scope D3 Full locked per user 2026-05-27 4-question decisions
  - Verify: `grep -n "^## " sprint-57-58-plan.md | wc -l` → 9
- [x] **Draft `sprint-57-58-checklist.md` v1** (this file)
  - DoD: Day 0-2 structure mirroring 57.57; tasks granular DoD/Verify per checkpoint
- [x] **User approve plan v1 + checklist v1** (approved 2026-05-28)
  - Gate: user explicit `approve` before Day 0 三-Prong execution ✅
- [x] **Plan v2 revision applied** (path corrections + JWT roles + R9 Potemkin Risk + AD-RateLimits-Potemkin-Migration-Phase58 carryover; Path B locked per user 2026-05-28 architectural decision)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

#### Prong 1 — Path Verify
- [x] **D-DAY0-A**: `backend/src/agent_harness/middleware/` module — exists?
  - Verify: `ls backend/src/agent_harness/middleware/` (expected: missing or empty `__init__.py`)
- [x] **D-DAY0-B**: `backend/src/agent_harness/middleware/rate_limit.py` — should NOT exist (NEW)
  - Verify: `[ ! -f backend/src/agent_harness/middleware/rate_limit.py ]`
- [x] **D-DAY0-C**: `backend/src/core/cache/` — Redis client location
  - Verify: `ls backend/src/core/cache/` OR `find backend/src -name "*redis*" -type f`
- [x] **D-DAY0-D**: Cat 2 sandbox/tool executor file path resolution
  - Verify: `grep -rn "class.*ToolExecutor\|class.*Sandbox\|_execute_tool\|tool_calls" backend/src/agent_harness/tool/`
  - Risk Class D mitigation (Sprint 57.50 lesson — cite `09-db-schema-design.md` style if multiple files)
- [x] **D-DAY0-E**: `frontend/src/features/tenant-settings/components/QuotasTab.tsx` — exists (baseline)
  - Verify: `[ -f frontend/src/features/tenant-settings/components/QuotasTab.tsx ]`
- [x] **D-DAY0-F**: `frontend/src/features/tenant-settings/hooks/` — directory exists
  - Verify: `ls frontend/src/features/tenant-settings/hooks/`
- [x] **D-DAY0-G**: Auth middleware ordering reference in `main.py` / `app.py`
  - Verify: `grep -n "add_middleware\|app.middleware" backend/src/main.py backend/src/app.py 2>/dev/null`

#### Prong 2 — Content Verify
- [x] **D-DAY0-H**: `tenant.meta_data["rate_limits"]["items"]` shape confirmed (Sprint 57.48+57.57 storage)
  - Verify: `grep -A 5 "rate_limits" backend/src/api/v1/admin/tenants.py | head -30`
- [x] **D-DAY0-I**: JWT `scopes` claim location in `request.state`
  - Verify: `grep -rn "jwt_scopes\|request.state.scopes\|current_user.*scopes" backend/src/`
- [x] **D-DAY0-J**: Existing `RateLimitExceededError` exception class?
  - Verify: `grep -rn "RateLimitExceededError\|RateLimitExceeded" backend/src/`
- [x] **D-DAY0-K**: Cat 8 ErrorPolicy handling for tool errors (Track B integration point)
  - Verify: `grep -n "ErrorPolicy\|_handle_tool_error" backend/src/agent_harness/error_handling/`
- [x] **D-DAY0-L**: Redis client interface (`redis.asyncio` or sync? lua_eval method?)
  - Verify: `grep -A 3 "class.*RedisClient\|import redis" backend/src/core/cache/*.py`
- [x] **D-DAY0-M**: Existing FastAPI middleware patterns in repo (template)
  - Verify: `grep -rn "BaseHTTPMiddleware\|class.*Middleware" backend/src/`
- [x] **D-DAY0-N**: TanStack Query polling pattern from prior sprints
  - Verify: `grep -rn "refetchInterval" frontend/src/features/`
- [x] **D-DAY0-O**: HEX_OKLCH baseline preservation (NO frontend foundation change)
  - Verify: `git diff $(git merge-base main HEAD)..HEAD -- 'frontend/src/**' | grep -cE '^\+[^+].*oklch\('` → 0
  - Run AFTER Day 1 (this is acceptance criterion verification, not plan-time)

#### Prong 3 — Schema Verify
- [x] **D-DAY0-P**: N/A (no DB schema change — uses existing `tenants.meta_data` JSONB)
  - Skip with documented justification

#### Day 0 Drift Catalog
- [ ] **Catalog findings** in `progress.md` Day 0 entry under `Drift findings` header
  - Format: `D-DAY0-{X}: <finding> → <implication>`
  - Cross-reference plan §8 Risks if scope shifts
- [ ] **Decide go/no-go for Day 1**
  - ≤20% scope shift → continue with risk noted
  - 20-50% → revise plan §Acceptance + §Workload + re-confirm with user
  - >50% → abort + redraft

### 0.9 Branch + Day 0 commit
- [ ] **Create feature branch**
  - Command: `git checkout -b feature/sprint-57-58-rate-limits-runtime-enforcement`
- [ ] **Day 0 commit** (plan + checklist + Day 0 progress)
  - Files: `sprint-57-58-plan.md` + `sprint-57-58-checklist.md` + `sprint-57-58/progress.md`
  - Message: `chore(sprint-57-58): Day 0 plan + checklist + 三-Prong findings`

---

## Day 1 — Implementation (Agent-Delegated: yes — sequential 4-track via code-implementer)

### 1.1 Track A — Backend Middleware NEW (code-implementer agent delegation #1) — paths corrected per Day 0 D-DAY0-A1/A2/A4

- [ ] **NEW** `backend/src/platform_layer/middleware/_rate_limit_contracts.py`
  - DoD: `RateLimitCounter` ABC + `RateLimitDecision` dataclass + `RateLimitCounterState` dataclass
- [ ] **NEW** `backend/src/platform_layer/tenant/rate_limit_counter.py`
  - DoD: `SLIDING_WINDOW_SCRIPT` constant + `RedisRateLimitCounter(RateLimitCounter)` impl using DI pattern mirror `quota.py:171 record_usage` + script SHA cache
- [ ] **NEW** `backend/src/platform_layer/middleware/rate_limit.py`
  - DoD: `RateLimitMiddleware(BaseHTTPMiddleware)` + `_load_rate_limits` 60s cache + `_infer_resource` + 429 + headers + bypass via `roles` claim (NOT `scopes` per D-DAY0-J)
- [ ] **EDIT** `backend/src/api/main.py`
  - DoD: `app.add_middleware(RateLimitMiddleware, ...)` inserted immediately AFTER L111 `app.add_middleware(TenantContextMiddleware)`; doc-comment ordering rationale (needs tenant_id)
- [ ] **NEW** `backend/tests/integration/agent_harness/test_rate_limit_middleware.py`
  - DoD: 6 tests — enforce_pass / enforce_block / bypass_admin / bypass_no_tenant / multi_tenant_isolation / 429_response_shape
- [ ] **Verify pytest** Track A subset GREEN
  - Command: `pytest backend/tests/integration/agent_harness/test_rate_limit_middleware.py -v`
- [ ] **Verify mypy --strict** Track A files
  - Command: `mypy backend/src/platform_layer/middleware/rate_limit.py backend/src/platform_layer/tenant/rate_limit_counter.py`

### 1.2 Track B — Cat 2 Tool Layer Integration (code-implementer agent delegation #2) — path resolved Day 0 D-DAY0-A3
- [ ] **EDIT** `backend/src/agent_harness/tools/sandbox.py` OR `tools/executor.py` (`ToolExecutorImpl:105` is the impl; agent selects site per call flow analysis at Day 1)
  - DoD: `_check_rate_limit_pre_call(tenant_id, tool_name)` raises `RateLimitExceededError` on over-limit
  - DoD: Reuses `RedisRateLimitCounter` from Track A (DRY)
  - DoD: Resource keys `tool_calls.<tool_name>` + `tool_calls` aggregate
- [ ] **NEW** `RateLimitExceededError` exception (NOT exists per D-DAY0-J grep — only openai SDK `RateLimitError` type exists in `adapters/azure_openai/error_mapper.py`)
  - DoD: Inherits from Cat 8 base error; carries `resource` + `limit` + `retry_after` attributes
- [ ] **EDIT** Cat 8 error handler if needed
  - DoD: `RateLimitExceededError` → no LLM retry (terminate gracefully)
- [ ] **NEW** `backend/tests/integration/agent_harness/test_tool_rate_limit_enforce.py`
  - DoD: 4 tests — tool_allowed / tool_blocked / per_tool_isolation / no_tenant_skip
- [ ] **Verify pytest** Track B subset GREEN

### 1.3 Track C — GET Live Usage Endpoint (code-implementer agent delegation #3 OR bundle with Track A)
- [ ] **EDIT** `backend/src/api/v1/admin/tenants.py`
  - DoD: NEW `GET /admin/tenants/{tid}/rate-limits/usage` endpoint
  - DoD: Reuses `_load_tenant_or_404` + `_session_factory_from`
  - DoD: NEW Pydantic `RateLimitsUsageItem` + `RateLimitsUsageResponse` models
  - DoD: Counter peek (no increment) via `RedisRateLimitCounter.peek`
- [ ] **NEW** `backend/tests/integration/api/test_admin_tenant_rate_limits_usage.py`
  - DoD: 3 tests — auth_required / 404_tenant_not_found / populated_response_shape
- [ ] **EDIT** `backend/tests/integration/api/conftest.py`
  - DoD: Add `RATE_LIMIT_USAGE_%` LIKE sweep (parallel to `RATE_PUT_%` Sprint 57.57 pattern)
- [ ] **Verify pytest** Track C subset GREEN

### 1.4 Track D — Frontend Live Usage Card (code-implementer agent delegation #4)
- [ ] **EDIT** `frontend/src/features/tenant-settings/types.ts`
  - DoD: Add `RateLimitsUsageItem` + `RateLimitsUsageResponse` types matching backend Pydantic
- [ ] **EDIT** `frontend/src/features/tenant-settings/services/tenantSettingsService.ts`
  - DoD: NEW `fetchRateLimitsUsage(tenantId)` function
- [ ] **NEW** `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.ts`
  - DoD: TanStack `useQuery` 5-second refetchInterval + 4-second staleTime
- [ ] **EDIT** `frontend/src/features/tenant-settings/_fixtures.ts`
  - DoD: Add `LIVE_USAGE_FIXTURE` for tests + storybook scenarios
- [ ] **EDIT** `frontend/src/features/tenant-settings/components/QuotasTab.tsx`
  - DoD: Insert Live usage Card BELOW existing RateLimits Card
  - DoD: RateLimits Card UNCHANGED bit-for-bit (scope guard)
  - DoD: Progress bar color-coded (green/yellow/red thresholds)
  - DoD: Reset countdown using `Intl.DateTimeFormat` or human-readable duration
  - DoD: Empty state handled
- [ ] **NEW** `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.test.tsx`
  - DoD: 3 tests — initial fetch / polling refetch / error handling
- [ ] **EDIT** `frontend/src/features/tenant-settings/services/tenantSettingsService.test.ts`
  - DoD: +2 tests — fetchRateLimitsUsage success / error
- [ ] **EDIT** `frontend/src/features/tenant-settings/components/QuotasTab.test.tsx`
  - DoD: +5 tests Live usage Card (render / progress / countdown / empty state / color thresholds) + 1 scope-guard test asserting RateLimits Card behavior UNCHANGED
- [ ] **Verify Vitest** Track D subset GREEN
  - Command: `pnpm vitest run frontend/src/features/tenant-settings/`

### 1.5 Day 1 Validation Sweep (full cross-track)
- [ ] **pytest full**: 1806 → 1819+ (>= +12 NEW)
  - Command: `pytest backend/tests/ -q`
- [ ] **mypy --strict**: 0/310+ (no new errors)
  - Command: `mypy backend/src/`
- [ ] **9/9 V2 lints GREEN**
  - Command: `python scripts/lint/run_all.py`
- [ ] **Vitest full**: 663 → 673+ (>= +10 NEW)
  - Command: `pnpm vitest run`
- [ ] **ESLint clean**
  - Command: `pnpm lint` (NOT `--silent`)
- [ ] **Vite build clean**
  - Command: `pnpm build`
- [ ] **HEX_OKLCH baseline 47 preserved**
  - Command: `git diff main -- 'frontend/src/**' | grep -cE '^\+[^+].*oklch\('` → 0
- [ ] **LLM SDK leak 0**
  - Command: `grep -rn "import openai\|import anthropic" backend/src/agent_harness/` → 0

### 1.6 Day 1 commit
- [ ] **Commit all Day 1 work**
  - Files: backend NEW + EDIT + frontend NEW + EDIT + all NEW tests
  - Message: `feat(rate-limits, sprint-57-58): runtime enforcement middleware + Cat 2 tool layer + GET usage + frontend Live usage Card`

---

## Day 2 — Closeout (parent assistant)

### 2.1 Final Validation Sweep
- [ ] **Re-run all Day 1.5 checks** (sanity after any final commits)
- [ ] **mockup-fidelity DUAL CLEAN 22/22 PARITY preserved 14 consecutive sprints 57.45-57.58**
  - Command: Reference Sprint 57.57 sweep pattern; document in retrospective Q1

### 2.2 Retrospective (Q1-Q6 mandatory; Q7 N/A SKIP per feature ship)
- [ ] **NEW** `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-58/retrospective.md`
  - Q1: What went well (3-5 items)
  - Q2: What didn't go well + calibration ratio (actual/agent-adjusted vs band [0.85, 1.20])
  - Q3: Lessons learned (generalizable; codify into rules if 2-3 sprint pattern)
  - Q4: Audit Debt deferred (5 RateLimits Phase 58+ extensions remaining + carryover ADs)
  - Q5: Next steps (carryover candidate list only; rolling planning §6 — no specific Sprint 57.59 tasks)
  - Q6: Solo-dev policy validation
  - Q7: N/A SKIP (8th consecutive feature ship NOT spike)

### 2.3 sprint-workflow.md updates
- [ ] **EDIT** `.claude/rules/sprint-workflow.md`
  - MHist entry: 1-line per AD-Lint-MHist-Verbosity char budget
  - Scope-class multiplier matrix update: `mixed-multidomain-bundle` 0.65 4th data point
  - §Active block: `mixed-multidomain-bundle-mechanical` 0.65 tier-3 1st validation
  - `medium-backend` 0.80 11th data point + `medium-frontend` 0.65 8th data point

### 2.4 sprint-workflow.md PROMOTIONS (Day 2 docs track — SKIP-eligible)
- [ ] **Confirm 0 PROMOTION-CANDIDATE reach 3-data-point threshold**
  - Tier-4 SPLIT FULLY VALIDATED (no further structural action)
  - SKIP this sub-task per Sprint 57.58 §2.7 plan rationale

### 2.5 Memory + index
- [ ] **NEW** `memory/project_phase57_58_rate_limits_runtime_enforcement.md`
  - Format: per Sprint 57.57 memory subfile structure (Sprint coord / Goal / Day 0 三-Prong / Day 1 / Day 2 / ratio / ADs / lessons)
- [ ] **EDIT** `memory/MEMORY.md`
  - Add 1-entry pointer ~250-300 char per §Sprint Closeout policy
  - Keywords: rate-limits, runtime enforcement, middleware, Redis sliding window, Cat 2 tool layer, Live usage, mixed-multidomain-bundle-mechanical, tier-3 1st validation

### 2.6 CLAUDE.md (navigator-only per §Sprint Closeout)
- [ ] **EDIT** `CLAUDE.md`
  - Update `Current Sprint` row → next sprint id placeholder
  - Update `Last Updated` footer (1 line; sprint goal short summary)
  - Update `Phase` row if milestone (Phase 58.x portfolio remaining 4 of 5 RateLimits extensions)
  - NO sprint-by-sprint history dump
  - NO calibration ratio in cells

### 2.7 next-phase-candidates.md
- [ ] **EDIT** `claudedocs/1-planning/next-phase-candidates.md`
  - Mark `AD-RateLimits-RuntimeEnforcement-Phase58` CLOSED
  - Update PARTIAL-CLOSE `AD-RateLimits-LiveUsageTracking-Phase58` (live usage exposure DONE; alerting threshold remains)
  - Add NEW carryover candidates from §9 of plan + retrospective Q4

### 2.8 CHANGE-028 record
- [ ] **NEW** `claudedocs/4-changes/feature-changes/CHANGE-028-sprint-57-58-rate-limits-runtime-enforcement.md`
  - Format: 1-page (Problem / Root Cause / Solution / Verification / Impact)
  - Per `CLAUDE.md §Change Record Conventions`

### 2.9 PR + merge (user action)
- [ ] **Push branch + open PR**
  - Command: `git push -u origin feature/sprint-57-58-rate-limits-runtime-enforcement`
  - PR title: `feat(rate-limits, sprint-57-58): RateLimits Runtime Enforcement — middleware + Cat 2 tool layer + Live usage Card (Phase 58.x portfolio 1/5)`
- [ ] **Wait for CI** (5 required checks green)
- [ ] **User merge** (solo-dev policy review_count=0; enforce_admins=true active)
- [ ] **Branch cleanup** (post-merge; local + remote delete; main fast-forward)

### 2.10 Final closeout
- [ ] **Day 2 commit** (all docs)
  - Files: retrospective.md + memory subfile + MEMORY.md + CLAUDE.md + next-phase + sprint-workflow.md + CHANGE-028 + checklist final tick
  - Message: `chore(docs, sprint-57-58): Day 2 closeout — retro + memory + matrix update + CHANGE-028`
- [ ] **Verify Working tree clean on main after merge**
  - Command: `git status` → clean
- [ ] **Mark Sprint 57.58 CLOSED** in `next-phase-candidates.md` index

---

## Open items / 🚧 Deferred (none yet; updated end of Day 0 三-Prong)

(Will accumulate during Day 0 + Day 1 — only `[ ]` → `[x]` allowed; never delete unchecked. 🚧 markers acceptable with reason.)
