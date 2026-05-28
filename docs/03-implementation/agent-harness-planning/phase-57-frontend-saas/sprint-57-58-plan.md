# Sprint 57.58 — Plan

**Phase**: 57+ Frontend SaaS / Phase 58.x Portfolio Deeper Extensions
**Sprint**: 57.58 (post-57.57 RateLimits WRITE FINAL 4/4 closure)
**Branch**: `feature/sprint-57-58-rate-limits-runtime-enforcement`
**Class**: `mixed-multidomain-bundle` 0.65 (tier-2; 3 tracks bundle)
**Agent-delegated**: yes (≥80% Day 1 via code-implementer; sequential)
**Agent-factor**: `mixed-multidomain-bundle-mechanical` 0.65 (tier-3 ACTIVATED Sprint 57.52)
**Plan version**: v1 — drafted 2026-05-27 Day 0 (pre-三-Prong)
**Template**: mirrors `sprint-57-57-plan.md` 9-section structure

---

## 1. Sprint Goal

Ship **RateLimits RuntimeEnforcement** (Phase 58.x portfolio item #1 — first of 5 deeper RateLimits extensions; closes `AD-RateLimits-RuntimeEnforcement-Phase58`).

Transforms `tenant.meta_data["rate_limits"]` from **admin-display-only** (Sprint 57.48+57.57 WRITE-side storage) into **runtime-enforced** via:

- **Backend Track A**: FastAPI middleware reading `tenant.meta_data["rate_limits"]["items"]` per request → Redis sliding window via Lua script → 429 + standard `Retry-After` + `X-RateLimit-*` headers
- **Backend Track B**: Cat 2 sandbox tool layer integration — same Redis-backed counter; per-tool resource keys (e.g. `tool_calls.<name>`)
- **Backend Track C**: NEW `GET /admin/tenants/{tid}/rate-limits/usage` endpoint exposing live counters for frontend display
- **Frontend Track D**: QuotasTab Live usage Card — per-resource progress bar + countdown to reset; 5-second polling via TanStack Query
- **Bypass**: JWT scope `admin`/`service` skip + tenant_id-missing internal-call skip
- **D3 Full scope** per user 2026-05-27 plan-drafting decision (user-locked all 4 dimensions before plan v1; zero rework cycle precedent from Sprint 57.57)

---

## 2. Background & Context

### 2.1 RateLimits baseline state (verified Sprint 57.57 Day 0 Prong 2 content verify — all GREEN)

- ✅ Storage: `tenant.meta_data["rate_limits"]["items"]` — list of `{resource, window, limit}` dicts (Sprint 57.48 Track D + Sprint 57.57 PUT)
- ✅ WRITE endpoint: `PUT /admin/tenants/{tid}/rate-limits` composite-replace semantics
- ✅ READ endpoint: `GET /admin/tenants/{tid}/rate-limits` (paired GET from Sprint 57.48 Track D)
- ✅ Frontend: QuotasTab RateLimits Card edit mode (Sprint 57.57)
- ❌ **Runtime enforcement**: NONE — `meta_data` is admin-display-only; no middleware reads it; no 429 ever returned
- ❌ **Live usage exposure**: NONE — no counter visible to admin
- ❌ **Cat 2 tool layer integration**: NONE — tools execute regardless of limits

### 2.2 True Phase 58.x gap (per Sprint 57.57 retro Q5 + carryover candidate AD #2)

Quote from `next-phase-candidates.md` L63:
> `AD-RateLimits-RuntimeEnforcement-Phase58` (NEW — currently `tenant.meta_data["rate_limits"]` is admin display only; no runtime enforcement; needs runtime middleware reading the override list)

This is the **single most valuable Phase 58.x extension** of the 5 RateLimits NEW carryover ADs because it transforms the entire RateLimits subsystem from a storage-only feature into actual runtime governance.

### 2.3 Why `mixed-multidomain-bundle-mechanical` 0.65 (tier-3)

Sprint 57.58 has **3 independent backend tracks + 1 frontend track** with mechanical pattern reuse:

| Track | Pattern source | Mechanical reuse |
|-------|---------------|-----------------|
| A: API middleware | NEW (no prior FastAPI middleware in repo for runtime governance) | Partial — borrow `BaseHTTPMiddleware` pattern from FastAPI docs |
| B: Cat 2 tool layer | Existing Cat 9 guardrail pre-call hook pattern | High — mirror `_apply_pre_call_guardrails` shape |
| C: GET usage endpoint | Sprint 57.57 GET `/rate-limits` precedent | High — same `_load_tenant_or_404` + projection pattern |
| D: Frontend Live usage Card | Sprint 57.56 `useQuotasSave` + Sprint 57.57 `useRateLimitsSave` query hook precedent | High — TanStack Query polling pattern |

Per tier-3 `mixed-multidomain-bundle-mechanical` 0.65 definition (3+ independent tracks WITH mechanical pattern reuse component). Sprint 57.46 (3-track docs+ORM+capture) and Sprint 57.51 (3-track docs/audit) precedents.

### 2.4 Pattern-reuse capture (Sprint 57.46-57.57 multi-track wave precedents)

- **Sprint 57.46** mixed-multidomain-bundle (3 tracks): ratio actual/class-committed = 0.73 (below band by 0.12; KEEP); under agent_factor 0.45 was 1.60 → rollback triggered
- **Sprint 57.51** non-mechanical bundle: ratio 0.97 IN BAND middle ✅ — tier-3 SPLIT later separated non-mechanical to 1.0
- **Sprint 57.52** non-mechanical: ratio ~1.85 → tier-3 SPLIT ACTIVATED (`-mechanical` 0.65 retained vs `-non-mechanical` 1.0)
- **Sprint 57.58** = 1st validation of `mixed-multidomain-bundle-mechanical` 0.65 tier-3 sub-class

### 2.5 Sprint 57.57 carryover chain context

- `AD-AgentFactor-Tier-4-Validation-Sprint-57.58` (CONDITIONAL — informational tracking only since tier-4 SPLIT FULLY VALIDATED 2 consec IN band; NOT blocking but Sprint 57.58 produces 3rd data point for tier-4 if `mechanical-greenfield-design-decisions` sub-track separates)
- Sprint 57.58 PRIMARY validation = `mixed-multidomain-bundle-mechanical` 0.65 tier-3 1st validation
- NO Sprint 57.57 PROMOTION ADs reach 3-data-point threshold here (Day 2 docs PROMOTION track SKIP-eligible)

### 2.6 Class baseline tracking continuation

- `medium-backend` 0.80 11th data point (last-3 mean ~0.72; KEEP per 3-sprint window rule)
- `medium-frontend` 0.65 8th data point (confound-resolved at sub-class layer per discipline; KEEP)
- `mixed-multidomain-bundle` 0.65 4th data point (3-data history: 57.46=0.73 / 57.51=0.97 / 57.52=~1.20)
- `mixed-multidomain-bundle-mechanical` 0.65 tier-3 **1st validation** (sub-class agent_factor)

### 2.7 Day 2 docs track scope

NO PROMOTION-CANDIDATE reaches 3-data-point threshold this sprint:
- Sprint 57.57 PROMOTIONS already codified
- Tier-4 SPLIT FULLY VALIDATED (no further structural action needed)
- Normal Day 2 closeout only (retrospective + memory + CLAUDE.md + next-phase-candidates + CHANGE record)

---

## 3. User Stories

### US-1: Backend Track A — FastAPI middleware runtime enforcement

**As a** platform operator
**I want** every authenticated API request to be runtime-rate-limit-checked against `tenant.meta_data["rate_limits"]`
**So that** abusive tenants are throttled with standard 429 + `Retry-After` semantics instead of soaking infrastructure unchecked.

**Acceptance**:
- NEW `RateLimitMiddleware(BaseHTTPMiddleware)` in `backend/src/agent_harness/middleware/rate_limit.py`
- Reads tenant_id from `request.state` (set by upstream auth middleware)
- Per-tenant counter keyed `rate_limit:{tenant_id}:{resource}:{window_bucket}` in Redis
- Sliding window via Lua script (atomic ZADD + ZREMRANGEBYSCORE old entries + ZCARD)
- Bypass: JWT `scopes` claim contains `admin` or `service` → skip; tenant_id missing → skip
- 429 response: `{error: "rate_limit_exceeded", resource, limit, retry_after_seconds, window}` + `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers
- Registered in `main.py` AFTER auth middleware (needs tenant_id)
- ~6-8 NEW pytest tests covering enforce-pass / enforce-block / bypass-admin / bypass-no-tenant / multi-tenant isolation / headers / 429 response shape

### US-2: Backend Track B — Cat 2 sandbox tool layer integration

**As a** tenant administrator
**I want** LLM tool calls (not just API requests) to consume the tool-call resource budget defined in RateLimits
**So that** budget enforcement covers the full request flow not just the HTTP edge.

**Acceptance**:
- Modify Cat 2 sandbox tool executor (find via Day 0 Prong 2): add `_check_rate_limit_pre_call(tenant_id, tool_name)` raising `RateLimitExceededError`
- Resource keys: `tool_calls.<tool_name>` (per-tool granularity) AND `tool_calls` aggregate
- Uses same `RateLimitCounter` helper as Track A middleware (DRY)
- Failed tool call surfaces as Cat 8 ErrorPolicy decision → no further LLM retry on RateLimitExceeded
- ~4-5 NEW pytest tests covering tool-allowed / tool-blocked / per-tool isolation / no-tenant skip

### US-3: Backend Track C + Frontend Track D — Live usage exposure + QuotasTab Card

**As a** tenant administrator
**I want** to see current consumption per rate-limit resource in real time
**So that** I can proactively raise limits before tenants hit 429 in production.

**Acceptance**:
- Backend: NEW `GET /admin/tenants/{tid}/rate-limits/usage` endpoint returning `{items: [{resource, current, limit, window, reset_at}]}`
- Frontend: NEW Live usage Card in `QuotasTab.tsx` BELOW existing RateLimits Card (DOES NOT modify existing Card)
- NEW `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.ts` — TanStack Query polling 5-second interval
- NEW `fetchRateLimitsUsage` in `tenantSettingsService.ts`
- NEW `RateLimitsUsageResponse` type in `types.ts`
- Display per-resource: progress bar (current/limit) + reset countdown
- ~3-4 NEW pytest tests (GET endpoint auth/404/empty/populated) + ~8-10 NEW Vitest tests (hook + service + Card render + progress + countdown)
- BackendGapBanner softened copy (no more "Phase 58+ remaining" for runtime enforcement)

---

## 4. Technical Specification

### 4.1 Backend Track A — Middleware design

**File** (NEW): `backend/src/agent_harness/middleware/rate_limit.py`

```python
# === RateLimitMiddleware: Cat 9 runtime enforcement ===
# Why: tenant.meta_data["rate_limits"] (Sprint 57.48+57.57) is admin-display-only
# until this middleware. Reads override list per request, atomic-check via Redis
# Lua sliding window, returns 429 + Retry-After on over-limit. Standard pattern
# for enterprise SaaS rate limiting.
# Alternative considered:
#   - Per-endpoint decorator — rejected: must be applied to ALL routes (error-prone)
#   - DB-backed counter — rejected: per-request DB write impractical at scale
#   - In-memory dict — rejected: multi-worker FastAPI = inconsistent counts
# Reference: 14-security-deep-dive.md §Rate Limiting / 17.md Contract 9
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Bypass: no tenant_id OR JWT admin/service scope
        tenant_id = getattr(request.state, "current_tenant_id", None)
        scopes = getattr(request.state, "jwt_scopes", set())
        if tenant_id is None or scopes & {"admin", "service"}:
            return await call_next(request)

        # 2. Load rate limits from tenant.meta_data (cached 60s)
        items = await self._load_rate_limits(tenant_id)
        if not items:
            return await call_next(request)

        # 3. Per-resource sliding window check via Lua script
        resource = self._infer_resource(request)  # "api_requests" for HTTP
        for item in items:
            if item["resource"] != resource:
                continue
            decision = await self._counter.check_and_increment(
                tenant_id, resource, item["window"], item["limit"]
            )
            if not decision.allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "resource": resource,
                        "limit": item["limit"],
                        "window": item["window"],
                        "retry_after_seconds": decision.retry_after,
                    },
                    headers={
                        "Retry-After": str(decision.retry_after),
                        "X-RateLimit-Limit": str(item["limit"]),
                        "X-RateLimit-Remaining": str(decision.remaining),
                        "X-RateLimit-Reset": str(decision.reset_at),
                    },
                )

        return await call_next(request)
```

**Lua sliding window script** (`backend/src/core/cache/rate_limit_lua.py`):

```python
# Atomic sliding window: ZADD now + ZREMRANGEBYSCORE old + ZCARD + EXPIRE
SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local cutoff = now - window * 1000

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)
if count < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window + 1)
    return {1, limit - count - 1, 0}
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry = math.ceil((tonumber(oldest[2]) + window * 1000 - now) / 1000)
    return {0, 0, retry}
end
"""
```

### 4.2 Backend Track B — Cat 2 tool layer

Find existing Cat 2 sandbox executor via Day 0 Prong 2 grep:
- Target: `backend/src/agent_harness/tool/sandbox.py` OR `executor.py` OR similar
- Inject `_check_rate_limit_pre_call(tenant_id, tool_name)` at tool execution entry
- Use same `RateLimitCounter` helper (DRY across Track A + B)
- Raise `RateLimitExceededError` (Cat 8 catches → returns user-friendly error)

### 4.3 Backend Track C — GET usage endpoint

**File EDIT**: `backend/src/api/v1/admin/tenants.py`

NEW endpoint:
```python
@router.get("/{tenant_id}/rate-limits/usage", response_model=RateLimitsUsageResponse)
async def get_rate_limits_usage(...):
    """Returns live counter state from Redis for each configured resource."""
    tenant = await _load_tenant_or_404(...)
    items = tenant.meta_data.get("rate_limits", {}).get("items", [])
    usage = []
    for item in items:
        counter_state = await counter.peek(tenant_id, item["resource"], item["window"])
        usage.append({
            "resource": item["resource"],
            "window": item["window"],
            "limit": item["limit"],
            "current": counter_state.count,
            "reset_at": counter_state.reset_at,
        })
    return {"items": usage}
```

### 4.4 Frontend Track D — Live usage Card

**Files**:
- NEW `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.ts`
- NEW `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.test.tsx`
- EDIT `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` (add `fetchRateLimitsUsage`)
- EDIT `frontend/src/features/tenant-settings/services/tenantSettingsService.test.ts` (+2 tests)
- EDIT `frontend/src/features/tenant-settings/types.ts` (add `RateLimitsUsageResponse`)
- EDIT `frontend/src/features/tenant-settings/components/QuotasTab.tsx` (insert Live usage Card; RateLimits Card UNCHANGED)
- EDIT `frontend/src/features/tenant-settings/components/QuotasTab.test.tsx` (+4-6 Live usage tests)
- EDIT `frontend/src/features/tenant-settings/_fixtures.ts` (NEW `LIVE_USAGE_FIXTURE`)

Hook shape (mirror Sprint 57.57 `useTenantRateLimits` query hook):
```ts
export function useRateLimitsUsage(tenantId: string) {
  return useQuery({
    queryKey: [...RATE_LIMITS_USAGE_QUERY_KEY_BASE, tenantId],
    queryFn: () => fetchRateLimitsUsage(tenantId),
    refetchInterval: 5000,  // 5-second polling
    staleTime: 4000,
  });
}
```

Card shape (visual sketch — refine per existing QuotasTab Card pattern):
- Heading: "Live usage"
- Per resource:
  - Resource name + window
  - Progress bar: `current / limit` (color: green <70% / yellow 70-90% / red >90%)
  - Reset countdown: `Resets in {duration}`
- Empty state: "No rate limits configured — set them in the RateLimits card above."

### 4.5 Bypass logic spec (corrected per Day 0 D-DAY0-J — JWT carries `roles`, NOT `scopes`)

| Condition | Behavior | Implementation |
|-----------|----------|----------------|
| `request.state.current_tenant_id is None` | Skip enforcement | `if tenant_id is None: return await call_next(request)` |
| JWT `roles` claim includes `admin` OR `service` | Skip enforcement | `if {"admin", "service"} & set(current_user.roles): return await call_next(request)` — uses `payload.roles: list[str]` per `platform_layer/identity/jwt.py:94` |
| Health check / static route (`/_health`, `/static/*`) | Skip enforcement | Route prefix allowlist in middleware config |
| Resource not in tenant's `items` | Allow (no rate limit defined) | Per-resource lookup; skip if missing |

**Note**: `service` role status — if not present in current RBAC role catalog (Day 1 Track A agent verifies via `core/rbac.py` or similar), bypass on `admin` role only; defer `service` to Phase 58.x.

### 4.6 Verification

- ~12 NEW pytest tests (Track A: 6 / Track B: 4 / Track C: 3 — actually 13 with margin)
- ~10 NEW Vitest tests (hook 3 + service 2 + Card render 5)
- pytest baseline 1806 → ~1819+ (per +12 NEW)
- Vitest baseline 663 → ~673+ (per +10 NEW)
- mypy --strict 0/310 preserved
- 9/9 V2 lints GREEN
- HEX_OKLCH baseline 47 preserved (NO frontend foundation change)
- LLM SDK leak 0
- Vite build clean
- mockup-fidelity DUAL CLEAN 22/22 PARITY preserved (14 consecutive sprints 57.45-57.58)

### 4.7 Risk mitigation strategies

| Risk | Mitigation |
|------|-----------|
| Redis unavailable | Fail-open: log warning + allow request (rate limits MUST NOT break service) |
| Lua script error | Fail-open: same as Redis unavailable |
| Counter peek inconsistent with enforce | Track A and Track C both use same Lua script; ZCARD inside transaction |
| Frontend polling overhead | 5-second interval + `staleTime: 4000` (TanStack auto-dedupe) |
| Test pollution across event loops | conftest.py `RATE_LIMIT_USAGE_%` cleanup sweep (mirror Sprint 57.57 `RATE_PUT_%` pattern) |
| Middleware ordering | Document in `main.py` register order: `AuthMiddleware` → `RateLimitMiddleware` → routes |

---

## 5. File Change List

### Backend (NEW + EDIT)

**NEW** (paths corrected per Day 0 Prong 1 — see progress.md D-DAY0-A1/A2/A3/A4):
- `backend/src/platform_layer/middleware/rate_limit.py` (Cat 12 platform layer; sibling of `tenant_context.py`)
- `backend/src/platform_layer/middleware/_rate_limit_contracts.py` (RateLimitCounter ABC + dataclasses)
- `backend/src/platform_layer/tenant/rate_limit_counter.py` (Lua script + RedisRateLimitCounter impl; DI pattern mirror `quota.py:171 record_usage`)
- `backend/tests/integration/api/test_admin_tenant_rate_limits_usage.py` (~3 tests)
- `backend/tests/integration/agent_harness/test_rate_limit_middleware.py` (~6 tests)
- `backend/tests/integration/agent_harness/test_tool_rate_limit_enforce.py` (~4 tests)

**EDIT**:
- `backend/src/api/main.py` — register `RateLimitMiddleware` immediately after L111 `app.add_middleware(TenantContextMiddleware)`
- `backend/src/api/v1/admin/tenants.py` — NEW `GET /{tid}/rate-limits/usage` endpoint
- `backend/src/agent_harness/tools/sandbox.py` OR `tools/executor.py` (`ToolExecutorImpl:105`) — pre-call hook injection (Day 0 D-DAY0-A3 confirms `tools/` path; specific file finalized Day 1 by Track B agent)
- `backend/tests/integration/api/conftest.py` — extend with `RATE_LIMIT_USAGE_%` LIKE sweep

### Frontend (NEW + EDIT)

**NEW**:
- `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.ts`
- `frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.test.tsx`

**EDIT**:
- `frontend/src/features/tenant-settings/types.ts` (+ `RateLimitsUsageItem`, `RateLimitsUsageResponse`)
- `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` (+ `fetchRateLimitsUsage`)
- `frontend/src/features/tenant-settings/services/tenantSettingsService.test.ts` (+ 2 tests)
- `frontend/src/features/tenant-settings/components/QuotasTab.tsx` (+ Live usage Card; RateLimits Card UNCHANGED scope-guard verified by test)
- `frontend/src/features/tenant-settings/components/QuotasTab.test.tsx` (+ ~5 Live usage tests + 1 scope-guard test asserting RateLimits Card unchanged behavior)
- `frontend/src/features/tenant-settings/_fixtures.ts` (+ `LIVE_USAGE_FIXTURE`)

### Sprint artifacts (Day 0 + Day 2)

- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-58-plan.md` (this file)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-58-checklist.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-58/progress.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-58/retrospective.md`
- `memory/project_phase57_58_rate_limits_runtime_enforcement.md`
- `claudedocs/4-changes/feature-changes/CHANGE-028-sprint-57-58-rate-limits-runtime-enforcement.md`

---

## 6. Workload

**Agent-delegated: yes** (≥80% Day 1 via code-implementer; sequential 3-track delegation Track A → B → C → D)

**Bottom-up est ~15 hr** → class-calibrated commit ~9.75 hr (mult 0.65 `mixed-multidomain-bundle`) → **agent-adjusted commit ~6.3 hr** (`agent_factor` 0.65 `mixed-multidomain-bundle-mechanical` tier-3 1st validation)

| Task | Bottom-up | Class-calibrated | Agent-adjusted |
|------|-----------|-----------------|---------------|
| Day 0 三-Prong (Path 6 + Content 8 + Schema N/A) + plan draft | 0.8 hr | 0.8 hr | 0.8 hr (parent) |
| Track A: Middleware NEW + Lua + tests | 5 hr | 3.25 hr | 2.1 hr |
| Track B: Cat 2 tool layer integration + tests | 3 hr | 1.95 hr | 1.3 hr |
| Track C: GET usage endpoint + tests | 1.5 hr | 1.0 hr | 0.6 hr |
| Track D: Frontend Live usage Card + hook + tests | 3.5 hr | 2.3 hr | 1.5 hr |
| Day 1 validation sweep | 0.5 hr | 0.5 hr | parent |
| Day 2 closeout (retro + memory + CLAUDE.md + next-phase + CHANGE) | 0.7 hr | 0.7 hr | 0.7 hr (parent) |
| **Total** | **15 hr** | **9.75 hr** | **~6.3 hr** |

Agent-adjusted breakdown assumes 4 sequential code-implementer agent delegations (Track A ~25 min + Track B ~20 min + Track C ~15 min + Track D ~25 min ≈ 1.5 hr wall-clock for Day 1 implementation; plus ~25 min Day 0 parent + ~30-40 min Day 2 parent = ~2.5-3 hr total agent + parent wall-clock).

Validation threshold: `actual/agent-adjusted` ratio in [0.85, 1.20] band acceptable; ratio < 0.7 OR > 1.20 triggers `mixed-multidomain-bundle-mechanical` 0.65 single-data-point caution rule.

---

## 7. Acceptance Criteria

### Functional
- [ ] 429 returned with correct `Retry-After` + `X-RateLimit-*` headers when limit exceeded
- [ ] Limit-pass requests transparent (no headers added — unless we decide to always add `X-RateLimit-Remaining`)
- [ ] Admin/service JWT bypass works (no rate limit applied)
- [ ] No-tenant request bypass works (internal calls unaffected)
- [ ] Per-tenant isolation: tenant A hitting limit does NOT affect tenant B
- [ ] Per-resource isolation: `api_requests` limit does NOT affect `tool_calls` budget
- [ ] Tool call rejection on tool-budget exceed surfaces as Cat 8 error (not LLM retry loop)
- [ ] GET `/rate-limits/usage` returns accurate live state matching enforcement view
- [ ] Frontend Live usage Card displays per-resource progress + countdown
- [ ] Frontend 5-second polling updates Card without flicker
- [ ] QuotasTab RateLimits Card behavior UNCHANGED (scope-guard test passes)

### Quality
- [ ] pytest baseline 1806 → 1819+ (NO regressions)
- [ ] Vitest baseline 663 → 673+ (NO regressions)
- [ ] mypy --strict 0/310 preserved
- [ ] 9/9 V2 lints GREEN
- [ ] Vite build clean + ESLint 0
- [ ] HEX_OKLCH baseline 47 preserved
- [ ] LLM SDK leak 0
- [ ] mockup-fidelity DUAL CLEAN 22/22 PARITY preserved (14 consec)

### Process
- [ ] Day 0 三-Prong verify executed (Path + Content; Schema N/A)
- [ ] Sequential code-implementer agent delegation (≥3 agents; chain 22nd-25th consecutive)
- [ ] Day 2 closeout artifacts all written (retro Q1-Q6 + memory subfile + MEMORY.md pointer + CLAUDE.md navigator-only + next-phase-candidates.md + CHANGE-028)
- [ ] PR opened + CI green + merge

---

## 8. Risks

| # | Risk | Class | Mitigation |
|---|------|-------|-----------|
| R1 | Redis unavailable during request → 500 cascade | Infra | Fail-open: log warning + allow request (rate limits MUST NOT break service) |
| R2 | Cat 2 sandbox executor path unknown until Day 0 Prong 2 | Risk Class D (ORM file path style — Sprint 57.50) | Day 0 Prong 2 grep before Track B plan finalization; cite `09-db-schema-design.md` style if applicable |
| R3 | Middleware ordering wrong (rate limit BEFORE auth) → tenant_id unavailable | Logic | Document in `main.py` + add test asserting tenant_id-not-set bypass works |
| R4 | Frontend polling thrashes Redis (N tenants × every 5s) | Performance | Cache GET response at HTTP layer 4s; TanStack `staleTime: 4000` dedupes within tab |
| R5 | Test pollution between event loops (committed Redis keys) | Risk Class C (Module-level Singleton — Sprint 53.6) | conftest.py `RATE_LIMIT_USAGE_%` + Redis FLUSHDB autouse for rate limit test namespace |
| R6 | `mixed-multidomain-bundle-mechanical` 0.65 1st validation may surface > 1.20 OR < 0.7 | Calibration | Single-data-point caution rule: KEEP 0.65; flag Sprint 57.59+ for 2nd validation. If > 1.20 → rollback to 1.0 (drop modifier). If < 0.7 → tighten to 0.45. |
| R7 | Lua script bug in production | Code quality | 6+ pytest tests covering edge cases (boundary / zero / max / concurrent). Mock Redis for unit tests; embedded Redis or `fakeredis` for integration. |
| R8 | Per-route `X-RateLimit-*` headers conflict with FastAPI response_model auto-headers | Integration | Test 200 response shape preserved; headers added via middleware (not endpoint) |
| R9 | **🚨 D-DAY0-CRITICAL: `RateLimit` ORM table is AP-4 Potemkin Feature** — defined at `infrastructure/db/models/api_keys.py:141` (table `rate_limits`) per `09-db-schema-design.md L902-919` but NEVER queried/written in production code | V1-lesson AP-4 | Sprint 57.58 = Path B (JSONB + Redis) per user 2026-05-28 Day 0 decision; Potemkin migration deferred to Sprint 57.59+ via NEW carryover `AD-RateLimits-Potemkin-Migration-Phase58` (activate dormant ORM + close AP-4) |

---

## 9. Carryover ADs (for Sprint 57.59+ pickup)

| ID | Status | Notes |
|----|--------|-------|
| **NEW**: `AD-RateLimits-SyntaxValidation-Phase58` | CARRYOVER | PUT-time validation (Group A #1; ~2 hr port-style) — Sprint 57.59+ candidate |
| **NEW**: `AD-RateLimits-LiveUsageTracking-Phase58` | PARTIAL-CLOSE | Live usage exposure DONE this sprint; alerting threshold remains for Phase 58.x |
| **NEW**: `AD-RateLimits-Alerting-Phase58` | CARRYOVER | SSE event emit when 80% threshold crossed (~2-3 hr) — Sprint 57.59+ candidate |
| **NEW**: `AD-RateLimits-DedicatedTable-Phase58` | CONDITIONAL | Migrate JSONB → dedicated `tenant_rate_limits` table only if DB load > threshold |
| `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Validation-Sprint-57.59` | NEW | 2nd validation for `mixed-multidomain-bundle-mechanical` 0.65 (Sprint 57.58 1st validation) |
| `AD-AgentFactor-Tier-4-Validation-Sprint-57.59` | CONDITIONAL | 3rd `mechanical-greenfield-design-decisions` 0.65 data point IF Sprint 57.59 is single-domain greenfield (NOT bundle) |
| `AD-MediumBackend-AICadence-Recalibration` | CONTINUES | Phase 58+ revisit `medium-backend` 0.80 baseline |
| `AD-Quotas-LiveUsageTracking-Phase58` | CONTINUES | Parallel to RateLimits live tracking; can fold into Sprint 57.59+ if pattern shared |
| `AD-FeatureFlags-PerFlag-AuditLog-Phase58` | CONTINUES | Sprint 57.55 carryover |
| `AD-Identity-Persistence-Phase58` | CONTINUES | SSO admin schema; Sprint 57.50 carryover |
| `AD-Test-Cleanup-Pattern-Shared-Helper` | CONTINUES | Phase 58.x — extract `_clear_committed_test_tenants` shared helper |
| **NEW**: `AD-RateLimits-Potemkin-Migration-Phase58` | CARRYOVER (added Sprint 57.58 Day 0 per D-DAY0-CRITICAL) | Activate dormant `RateLimit` ORM at `infrastructure/db/models/api_keys.py:141` (table `rate_limits` defined since Phase 49 V2 baseline per `09-db-schema-design.md L902-919` but never wired) — closes AP-4 Potemkin. Sprint 57.59+ scope ~5-8 hr (ORM service layer + migration of meta_data items → table rows OR keep meta_data config + use table for persistence). |

---

**Plan v2 status**: revised 2026-05-28 Day 0 (post-Day 0 三-Prong Verify; Path B locked per user decision)

**Day 0 三-Prong corrections applied** (audit trail per AD-Plan-1):
1. ✅ Path corrections §5: `agent_harness/middleware/` → `platform_layer/middleware/` (Cat 12 sibling of `tenant_context.py`); `core/cache/` → `platform_layer/tenant/rate_limit_counter.py` (DI pattern mirror `quota.py:171`); `agent_harness/tool/` → `agent_harness/tools/` (with `s`); `backend/src/main.py` → `backend/src/api/main.py:111+`
2. ✅ JWT bypass correction §4.5: `scopes` claim → `roles` claim per `platform_layer/identity/jwt.py:94`
3. ✅ R9 added §8 Risks: AP-4 Potemkin (`RateLimit` ORM defined but never used)
4. ✅ Carryover added §9: NEW `AD-RateLimits-Potemkin-Migration-Phase58` (Sprint 57.59+)
5. ✅ Scope locked: Path B (JSONB config + Redis sliding window counter) — original D3 Full + ~8-10 hr unchanged

**Original 3 user decision points** — all resolved Day 0:
1. ✅ Scope locked Day 0 (D3 Full + 4-question user lock 2026-05-27 still valid)
2. ✅ Agent delegation: sequential 4-agent (Track A → B → C → D) per checklist §1.1-1.4
3. ⏸ PR-time real-LLM e2e — defer to Day 2 final closeout (basic 429 test via pytest mock-redis; live spam e2e nice-to-have not blocking)
