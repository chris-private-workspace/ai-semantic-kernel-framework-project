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
- [x] **Catalog findings** in `progress.md` Day 0 entry under `Drift findings` header — 9 findings (4 🔴 RED + 4 🆕 NOTABLE + 1 🚨 CRITICAL Potemkin)
- [x] **Decide go/no-go for Day 1** — 30-40% shift (20-50% bucket) → plan v2 revised + user re-confirmed Path B 2026-05-28 ✅

### 0.9 Branch + Day 0 commit
- [x] **Create feature branch** `feature/sprint-57-58-rate-limits-runtime-enforcement` (from main `ea2abaa9`)
- [x] **Day 0 commit** `f20ef896` (plan v2 + checklist v2 + progress.md; 3 files +858)

---

## Day 1 — Implementation (Agent-Delegated: yes — sequential 4-track via code-implementer)

### 1.1 Track A — Backend Middleware NEW (code-implementer agent delegation #1) — paths corrected per Day 0 D-DAY0-A1/A2/A4

- [x] **NEW** `backend/src/platform_layer/tenant/_rate_limit_contracts.py` ✅ (sited in `tenant/` not `middleware/` per D-DAY1-3 circular-import fix)
  - DoD: `RateLimitCounter` ABC + `RateLimitDecision` + `RateLimitCounterState` ✅
- [x] **NEW** `backend/src/platform_layer/tenant/rate_limit_counter.py` ✅
  - DoD: `RedisRateLimitCounter(RateLimitCounter)` MULTI/EXEC pipeline sliding window (D-DAY1-2: fakeredis no EVAL → reserve-then-rollback, QuotaEnforcer precedent) + `parse_rate_limit_item()` `{label,value}` parser + singleton accessors ✅
- [x] **NEW** `backend/src/platform_layer/middleware/rate_limit.py` ✅
  - DoD: `RateLimitMiddleware(BaseHTTPMiddleware)` + fail-open + 429 + headers + bypass via `roles` claim ✅
- [x] **NEW** `backend/src/platform_layer/tenant/tool_rate_limit_gate.py` ✅ (Track B adapter — not in original plan; LLM-neutral seam)
- [x] **EDIT** `backend/src/api/main.py` — register `RateLimitMiddleware` after `TenantContextMiddleware` + `_lifespan` Redis counter wiring ✅
- [x] **NEW** `backend/tests/integration/agent_harness/test_rate_limit_middleware.py` (6 tests) ✅
- [x] **Verify pytest** Track A subset GREEN ✅
- [x] **Verify mypy --strict** Track A files (0 errors) ✅

### 1.2 Track B — Cat 2 Tool Layer Integration (bundled into backend agent `rl-backend`) — path resolved Day 0 D-DAY0-A3 ✅ COMPLETE
- [x] **EDIT** `backend/src/agent_harness/tools/executor.py` (`ToolExecutorImpl.execute()` reads `ctx.tenant_id`) ✅
  - DoD: LLM-neutral `RateLimitGate` Protocol (optional ctor injection, default None) — keeps Cat 2 free of platform/Redis imports; `RedisToolRateLimitGate` (platform_layer) is concrete adapter ✅
  - DoD: Resource keys `tool_calls.<tool_name>` + `tool_calls` aggregate ✅
- [x] **NEW** `RateLimitExceededError` exception in `backend/src/agent_harness/_contracts/errors.py` ✅
  - DoD: carries `resource` + `limit` + `retry_after`; does NOT subclass `ToolExecutionError` ✅
- [x] **EDIT** `backend/src/agent_harness/error_handling/policy.py` — register `RateLimitExceededError` FATAL → `should_retry=False` (test-verified; no LLM retry loop) ✅
- [x] **NEW** `backend/tests/integration/agent_harness/test_tool_rate_limit_enforce.py` (4 tests) ✅
- [x] **Verify pytest** Track B subset GREEN ✅

### 1.3 Track C — GET Live Usage Endpoint (bundled into backend agent `rl-backend`) ✅ COMPLETE
- [x] **EDIT** `backend/src/api/v1/admin/tenants.py`
  - DoD: NEW `GET /admin/tenants/{tid}/rate-limits/usage` endpoint ✅
  - DoD: Reuses `_load_tenant_or_404` + session factory ✅
  - DoD: NEW Pydantic `RateLimitsUsageItem` + `RateLimitsUsageResponse` models ✅ (`{resource, window:int sec, limit, current, reset_at:int epoch}`)
  - DoD: Counter peek (no increment) via `RedisRateLimitCounter.peek` ✅
- [x] **NEW** `backend/tests/integration/api/test_admin_tenant_rate_limits_usage.py` (3 tests) ✅
- [x] **EDIT** `backend/tests/integration/api/conftest.py` — `RATE_LIMIT_USAGE_%` LIKE sweep ✅
- [x] **Verify pytest** Track C subset GREEN ✅

### 1.4 Track D — Frontend Live Usage Card (code-implementer agent `rl-frontend`) ✅ COMPLETE
- [x] **EDIT** `frontend/src/features/tenant-settings/types.ts` — `RateLimitsUsageItem` + `RateLimitsUsageResponse` ✅
- [x] **EDIT** `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — `fetchRateLimitsUsage(tenantId, signal)` ✅
- [x] **NEW** `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.ts` — `useQuery` 5s refetchInterval + 4s staleTime + `RATE_LIMITS_USAGE_QUERY_KEY_BASE` ✅
- [x] **EDIT** `frontend/src/features/tenant-settings/_fixtures.ts` — `LIVE_USAGE_FIXTURE` (3 color thresholds) ✅
- [x] **EDIT** `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` ✅ (path: `components/tabs/` not `components/`)
  - DoD: Live usage Card BELOW Rate limits Card ✅
  - DoD: RateLimits Card UNCHANGED bit-for-bit (scope guard test passes; only docstring lines changed) ✅
  - DoD: Progress bar color-coded via existing `.bar-track` + `var(--success/--warning/--danger)` (green <70% / yellow 70-90% / red >90%) ✅
  - DoD: Reset countdown `{m}m {s}s` from `reset_at − Date.now()` ✅
  - DoD: Empty state handled ✅
- [x] **NEW** `frontend/tests/unit/tenant-settings/useRateLimitsUsage.test.tsx` (3 tests; path `tests/unit/` not co-located) ✅
- [x] **EDIT** `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` (+2 tests) ✅
- [x] **EDIT** `frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx` (+7 tests: 5 Live usage + loading/error + scope-guard) ✅
- [x] **Verify Vitest** Track D subset GREEN ✅

### 1.5 Day 1 Validation Sweep (full cross-track) ✅ ALL GREEN
- [x] **pytest full**: 1806 → **1819** (+13 exact target) + 4 skip + 0 regressions ✅
- [x] **mypy --strict**: 0 errors ✅
- [x] **9/9 V2 lints GREEN** (1.03s; incl. LLM SDK leak) ✅
- [x] **Vitest full**: 663 → **675** (+12) ✅
- [x] **ESLint clean** (NO `--silent`; only pre-existing jsx-ast-utils warnings) ✅
- [x] **Vite build clean** (3.44s) ✅
- [x] **HEX_OKLCH baseline 48 preserved** (NOT 47 — bumped 47→48 Sprint 57.50 hotfix; 0 new oklch this sprint) ✅
- [x] **LLM SDK leak 0** (`grep agent_harness` = 0) ✅

### 1.6 Day 1 commit
- [x] **Commit all Day 1 work** ✅ `5e6fc72f` (24 files +2172/-106)

---

## Day 2 — Closeout (parent assistant)

### 2.1 Final Validation Sweep
- [x] **Re-run Day 1.5 checks** ✅ (Day 2 = docs-only; no code change since `5e6fc72f`; Day 1.5 sweep authoritative: pytest 1819 / Vitest 675 / mypy 0 / tsc 0 / 9/9 V2 lints / 0 oklch / 0 SDK leak)
- [x] **mockup-fidelity DUAL CLEAN 22/22 PARITY preserved 14 consecutive sprints 57.45-57.58** ✅ (0 new oklch; baseline 48 unchanged)

### 2.2 Retrospective (Q1-Q6 mandatory; Q7 N/A SKIP per feature ship)
- [x] **NEW** `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-58/retrospective.md` ✅
  - Q1: What went well (3-5 items)
  - Q2: What didn't go well + calibration ratio (actual/agent-adjusted vs band [0.85, 1.20])
  - Q3: Lessons learned (generalizable; codify into rules if 2-3 sprint pattern)
  - Q4: Audit Debt deferred (5 RateLimits Phase 58+ extensions remaining + carryover ADs)
  - Q5: Next steps (carryover candidate list only; rolling planning §6 — no specific Sprint 57.59 tasks)
  - Q6: Solo-dev policy validation
  - Q7: N/A SKIP (8th consecutive feature ship NOT spike)

### 2.3 sprint-workflow.md updates
- [x] **EDIT** `.claude/rules/sprint-workflow.md` ✅ (MHist + `mixed-multidomain-bundle` matrix 2nd data point + §Active block `mixed-multidomain-bundle-mechanical` tier-3 1st validation)
  - MHist entry: 1-line per AD-Lint-MHist-Verbosity char budget
  - Scope-class multiplier matrix update: `mixed-multidomain-bundle` 0.65 4th data point
  - §Active block: `mixed-multidomain-bundle-mechanical` 0.65 tier-3 1st validation
  - `medium-backend` 0.80 11th data point + `medium-frontend` 0.65 8th data point

### 2.4 sprint-workflow.md PROMOTIONS (Day 2 docs track — SKIP-eligible)
- [x] **Confirm 0 PROMOTION-CANDIDATE reach 3-data-point threshold** ✅ SKIPPED (tier-4 SPLIT FULLY VALIDATED; no structural action)

### 2.5 Memory + index
- [x] **NEW** `memory/project_phase57_58_rate_limits_runtime_enforcement.md` ✅ (user-home `.claude/projects/.../memory/`; NOT project mirror per convention)
- [x] **EDIT** `memory/MEMORY.md` ✅ (quality pointer + keywords)

### 2.6 CLAUDE.md (navigator-only per §Sprint Closeout)
- [x] **EDIT** `CLAUDE.md` ✅ (Current Sprint row + Last Updated footer; navigator-only, no history dump)
  - Update `Current Sprint` row → next sprint id placeholder
  - Update `Last Updated` footer (1 line; sprint goal short summary)
  - Update `Phase` row if milestone (Phase 58.x portfolio remaining 4 of 5 RateLimits extensions)
  - NO sprint-by-sprint history dump
  - NO calibration ratio in cells

### 2.7 next-phase-candidates.md
- [x] **EDIT** `claudedocs/1-planning/next-phase-candidates.md` ✅ (Sprint 57.58 Carryover section: RuntimeEnforcement CLOSED + LiveUsageTracking PARTIAL + 3 NEW carryovers)

### 2.8 CHANGE-028 record
- [x] **NEW** `claudedocs/4-changes/feature-changes/CHANGE-028-sprint-57-58-rate-limits-runtime-enforcement.md` ✅

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
