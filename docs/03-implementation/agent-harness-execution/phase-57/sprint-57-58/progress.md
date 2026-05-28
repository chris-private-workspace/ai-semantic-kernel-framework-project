# Sprint 57.58 — Progress

**Goal**: RateLimits RuntimeEnforcement D3 Full (Phase 58.x portfolio 1/5 deeper extensions)
**Class**: `mixed-multidomain-bundle` 0.65 (tier-2 4th data point)
**Agent-delegated**: yes (sequential 4-track via code-implementer)
**Agent-factor**: `mixed-multidomain-bundle-mechanical` 0.65 (tier-3 **1st validation**)
**Start date**: 2026-05-28

Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-58-plan.md`
Checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-58-checklist.md`

---

## Day 0 — 2026-05-28

### Today's Accomplishments

- Drafted plan v1 (~370 lines, 9-section structure mirror 57.57)
- Drafted checklist v1 (~250 lines, Day 0-2 structure mirror 57.57)
- User approve gate: ✅ approved 2026-05-28; proceed to Day 0 三-Prong Verify
- Day 0 三-Prong Verify executed (Prong 1 Path + Prong 2 Content; Prong 3 N/A — no DB schema change)

### Drift findings (Prong 1 + 2 — 9 findings; ratio 4 🔴 RED + 4 🆕 NOTABLE + 1 🚨 CRITICAL)

#### 🚨 D-DAY0-CRITICAL — `RateLimit` ORM Potemkin Feature (AP-4)

`infrastructure/db/models/api_keys.py:141` defines `class RateLimit(Base, TenantScopedMixin)` (table `rate_limits` per `09-db-schema-design.md L902-919`):
- Columns: `id` / `resource_type` / `window_type` / `quota` / `used` / `window_start` / `tenant_id` (via mixin)
- Re-exported in `infrastructure/db/models/__init__.py:26`
- **BUT NEVER USED in production**: grep shows `health_check.py` imports `ApiKey` (sibling) but no file instantiates / queries / writes `RateLimit`
- This is AP-4 Potemkin Feature from V1 lessons — table designed for runtime enforcement but never wired
- **Implication**: Sprint 57.58 has 2 paths (Path A activate dormant table OR Path B JSONB + Redis per plan v1)
- **Architectural decision needed** — affects §4 Technical Spec + §5 File Change List

#### 🔴 D-DAY0-A1 — Plan path `agent_harness/middleware/` does NOT exist

- Plan v1 §5 said `backend/src/agent_harness/middleware/rate_limit.py`
- **Reality**: directory absent. Actual middleware location = `backend/src/platform_layer/middleware/` (Cat 12 platform layer)
- Existing: `tenant_context.py` `TenantContextMiddleware(BaseHTTPMiddleware)`
- **Correction**: RateLimitMiddleware should go in `backend/src/platform_layer/middleware/rate_limit.py`

#### 🔴 D-DAY0-A2 — Plan path `backend/src/main.py` does NOT exist

- Plan v1 said "Register `RateLimitMiddleware` in main.py"
- **Reality**: actual FastAPI entry = `backend/src/api/main.py:111` `app.add_middleware(TenantContextMiddleware)`
- **Correction**: Add `app.add_middleware(RateLimitMiddleware)` immediately after L111

#### 🔴 D-DAY0-A3 — Plan path `agent_harness/tool/` does NOT exist

- Plan v1 §4.2 referenced "Cat 2 sandbox executor in `backend/src/agent_harness/tool/`"
- **Reality**: directory is `backend/src/agent_harness/tools/` (with 's')
- Cat 2 ABC: `tools/_abc.py:53` `class ToolExecutor(ABC)`
- Cat 2 impl: `tools/executor.py:105` `class ToolExecutorImpl(ToolExecutor)`
- Cat 2 sandbox: `tools/sandbox.py`
- **Correction**: trivial path correction (s/`tool`/`tools`/)

#### 🔴 D-DAY0-A4 — Plan path `backend/src/core/cache/` does NOT exist

- Plan v1 §5 said `backend/src/core/cache/rate_limit_lua.py`
- **Reality**: no `core/cache/` namespace. Redis client comes via DI from outside (caller injects `redis.asyncio.Redis`)
- Closest precedent: `platform_layer/tenant/quota.py:171` `async def record_usage` uses same DI pattern
- **Correction**: co-locate Lua script in `platform_layer/middleware/_rate_limit_counter.py` OR `platform_layer/tenant/rate_limit_counter.py` (Quota sibling)

#### 🆕 D-DAY0-J — JWT carries `roles`, NOT `scopes`

- Plan v1 §4.5 said "JWT `scopes` claim contains `admin` or `service`"
- **Reality**: `platform_layer/identity/jwt.py` JWT payload = `{sub, tenant_id, roles: list[str], iat, exp}` (`_RESERVED_CLAIMS = frozenset({"sub", "tenant_id", "roles", "iat", "exp"})`)
- No `scopes` claim
- **Correction**: bypass via `roles` claim — e.g. `if "admin" in current_user.roles or "service" in current_user.roles`
- `service` role status: need confirmation user-side (Phase 58.x defer if not present)

#### 🆕 D-DAY0-K — Precedent for live tracking exists in `quota.py`

- `platform_layer/tenant/quota.py:171` `async def record_usage(` exists
- Pattern: caller injects `redis.asyncio.Redis`; module owns no Redis singleton
- Track A `RateLimitCounter` should mirror this DI shape exactly
- **Implication**: Reduces design uncertainty — `quota.py:171+` is the template

#### 🆕 D-DAY0-L — FastAPI middleware ordering confirmed

- `api/main.py:111` `app.add_middleware(TenantContextMiddleware)`
- RateLimitMiddleware add immediately after (need tenant_id from TenantContext)
- BaseHTTPMiddleware pattern verified — `TenantContextMiddleware` is the template

#### 🆕 D-DAY0-M — Frontend hooks namespace already has 12 hooks

- `frontend/src/features/tenant-settings/hooks/` exists with 12 hooks
- Includes Sprint 57.48 `useRateLimits.ts` (read) + Sprint 57.57 `useRateLimitsSave.ts` (write)
- Live usage hook = NEW `useRateLimitsUsage.ts` sibling

#### 🆕 D-DAY0-N — TanStack `refetchInterval` polling precedent

- `useActiveLoops.ts:33` `refetchInterval: 10_000` (10s)
- `useApprovals.ts:53` `refetchInterval: POLL_INTERVAL_MS` (30s)
- Live usage 5s polling per plan v1 = consistent pattern

---

### Scope shift assessment

- Path drifts (A1-A4) = ~15% file path correction (mechanical s/old/new/)
- CRITICAL Potemkin Feature D-DAY0-CRITICAL = ~20-25% scope ambiguity (architectural decision)
- Total shift estimate: **~30-40% — between 20-50% bucket** → per Sprint Workflow Step 2.5: **revise plan + re-confirm with user**

### Decision resolved (user 2026-05-28 AskUserQuestion)

**Path B locked**: JSONB config + Redis sliding window counter per plan v1; AP-4 Potemkin defer to Sprint 57.59+ via NEW carryover AD.

### Plan v2 amendments applied (Day 0 closeout)

1. ✅ Path §5 corrected: `agent_harness/middleware/` → `platform_layer/middleware/`; `core/cache/` → `platform_layer/tenant/rate_limit_counter.py`; `agent_harness/tool/` → `agent_harness/tools/`; `backend/src/main.py` → `backend/src/api/main.py`
2. ✅ JWT bypass §4.5: `scopes` → `roles` claim per `platform_layer/identity/jwt.py:94`
3. ✅ R9 Risk added §8: AP-4 Potemkin `RateLimit` ORM defined since Phase 49 V2 baseline but never wired
4. ✅ Carryover added §9: NEW `AD-RateLimits-Potemkin-Migration-Phase58` (Sprint 57.59+ activate dormant ORM)
5. ✅ Scope unchanged: D3 Full + ~8-10 hr (`mixed-multidomain-bundle-mechanical` 0.65 tier-3 1st validation)

### Checklist v2 updates (Day 0 closeout)

1. ✅ 0.1 Plan + Checklist drafted + user approved 2026-05-28
2. ✅ 0.8 Day 0 三-Prong all 16 D-DAY0-* checks complete (Path 7 + Content 8 + Schema N/A)
3. ✅ 1.1 Track A paths corrected (3 file paths + mypy command + register-after-TenantContextMiddleware)
4. ✅ 1.2 Track B paths corrected (`tools/` with s + `ToolExecutorImpl:105` reference; `RateLimitExceededError` NEW confirmed by grep)

### Day 0 commit ready

Next action: Day 0 commit + Day 1 Track A code-implementer agent delegation.

### Day 0 Workload tracking

- Plan v1 drafting: ~30 min (parent)
- Checklist v1 drafting: ~20 min (parent)
- Day 0 三-Prong execution (parallel 11 Glob/Grep + 4 follow-up Grep): ~25 min (parent)
- Plan v2 + checklist v2 amendments: ~20 min (parent)
- **Total Day 0**: ~95 min (~1.6 hr) parent-only work; on track vs ~0.8 hr Workload §6 estimate (Day 0 slightly over due to critical Potemkin discovery + plan revision cycle but no rework — single revision pass)


