# Sprint 57.48 — TenantSettings Backend Completion Wave + AP-4 Hygiene

**Phase**: 57+ Frontend SaaS / Phase 58+ Backend Schema Extension (closure wave)
**Goal**: Close 4 remaining TenantSettings tab backends (HITLPolicies + FeatureFlags + Quotas + RateLimits) using MEMBERS pattern reuse (Sprint 57.47) + bonus AP-4 frontend hygiene cleanup. Generate **2nd validation data point under rolled-back `agent_factor = 0.65`** + **4th data point for `medium-backend` 0.80 baseline**.
**Branch**: `feature/sprint-57-48-tenant-settings-backend-completion-wave`
**Class**: `medium-backend` 0.80 (4 of 5 tracks mechanical backend admin GET endpoints; Track E small frontend lint hygiene)
**Date**: 2026-05-26 (Sprint 57.47 closeout day)
**Prior sprint reference**: Sprint 57.47 (MEMBERS pattern reuse source) + Sprint 57.46/47 retro (agent_factor 0.65 + pendulum evidence)

---

## 1. Sprint Goal

```
AS a backend engineer closing Phase 58+ TenantSettings Backend Schema Extension wave
I WANT 4 remaining TenantSettings tab backends shipped (HITLPolicies + FeatureFlags +
   Quotas + RateLimits) using the MEMBERS pattern (admin GET endpoint per tab; mechanical
   reuse) + 1 bonus track AP-4 frontend lint hygiene cleanup
SO THAT all 5 fixture-only TenantSettings tabs (excl. DANGER_OPS UI-only) now have real
   backend support; Phase 58+ frontend real-data migration can proceed without further
   backend gaps; AND we generate the 2nd validation data point under `agent_factor = 0.65`
   to confirm/deny the sub-class hypothesis (AD-AgentFactor-Sub-Class-Calibration).
```

## 2. Background & Context

### 2.1 5 Tracks scope (sorted by Sprint 57.47 6-tab audit cost estimate)

| Track | AD | Estimate (Sprint 57.47 audit) | Pattern source |
|---|---|---|---|
| A | `AD-TenantSettings-HITLPolicies-Backend` | ~2-3 hr | MEMBERS (Sprint 57.47); ABC+DBHITLPolicyStore impl exists, no admin GET |
| B | `AD-TenantSettings-FeatureFlags-Backend-AdminGet` | ~3-4 hr | MEMBERS pattern; ORM ready, no admin GET |
| C | `AD-TenantSettings-Quotas-Backend` | ~3-5 hr | MEMBERS pattern; quota.py exists (Redis tokens-only — need to add structured GET) |
| D | `AD-TenantSettings-RateLimits-Backend` | ~4-6 hr | full-scratch (no backend module — needs Pydantic + endpoint + minimal ORM if persistence needed) |
| E | `AD-Frontend-AP4-Pre-Existing-Lint` | ~30 min | Frontend hygiene; carried since Sprint 57.46 |

Total bottom-up: **~12.5-18.5 hr** (mid ~15.5)

### 2.2 Items 5 + 7 (auto-tracked via Day 2 retro)

- **Item 5** `AD-AgentFactor-Sub-Class-Calibration` 2nd validation — Sprint 57.48 ratio under `agent_factor = 0.65` will be the 2nd data point post-rollback; per rollback rule "2 sprints with ratio < 0.7 → tighten to 0.45". If Sprint 57.48 also < 0.7 → MANDATORY tighten OR escalate sub-class split.
- **Item 7** `AD-medium-backend-Baseline-Recalibration` — Sprint 57.48 = 4th `medium-backend` 0.80 data point (55.5=1.14, 55.6=0.92, 57.47=0.16, 57.48=TBD). 3-pt mean was 0.74 below lower edge; if 4th continues < 0.7 → propose `medium-backend` 0.80 → 0.65 lift.

### 2.3 Day 0.8 scope decision rule

Per checklist §0.8 decision rule, if Day 0.8 三-prong reveals any track > 1.5× estimate (e.g. RateLimits scope balloons > 9 hr from full-scratch complexity), DEFER that specific track to Sprint 57.49+ with explicit 🚧 + reason. Other 4 tracks (incl. AP-4) still ship.

---

## 3. User Stories

### US-1: HITLPolicies Backend (Track A — cheapest, first)

```
AS a platform admin viewing /tenant-settings HITL Policies tab
I WANT a GET /admin/tenants/{tenant_id}/hitl-policies endpoint returning the
   tenant's HITL policy configuration (action threshold / approval requirements
   / auto-approve scopes)
SO THAT the frontend tab can switch from _fixtures.ts HITL_POLICIES (4 items)
   to real backend data, unblocking governance audit workflows.
```

**Acceptance**:
- New endpoint `GET /admin/tenants/{tenant_id}/hitl-policies` (paginated; admin-only)
- Pydantic `HITLPolicyItem` + `HITLPolicyListResponse` mirroring MEMBERS pattern (Sprint 57.47)
- ≥6 NEW pytest tests (auth + 404 + happy + shape + multi-tenant isolation + pagination + empty)
- Uses existing `DBHITLPolicyStore` (Sprint 57.47 audit verified concrete impl exists)
- Multi-tenant isolation rule preserved

### US-2: FeatureFlags Admin GET (Track B)

```
AS a platform admin viewing /tenant-settings Feature Flags tab
I WANT a GET /admin/tenants/{tenant_id}/feature-flags endpoint returning
   tenant-scoped feature flag values (per Phase 56.1 feature_flags table)
SO THAT the frontend tab can display real flag values per tenant instead of
   the 8-item _fixtures.ts FEATURE_FLAGS.
```

**Acceptance**:
- New endpoint `GET /admin/tenants/{tenant_id}/feature-flags`
- Pydantic `FeatureFlagItem` + `FeatureFlagListResponse`
- Uses existing `feature_flags` ORM (Sprint 56.1 + Sprint 57.47 audit confirmed)
- ≥6 NEW pytest tests
- Multi-tenant isolation preserved

### US-3: Quotas Admin GET (Track C)

```
AS a platform admin viewing /tenant-settings Quotas + Rate Limits tab
I WANT a GET /admin/tenants/{tenant_id}/quotas endpoint returning tenant's
   structured quota configuration (per Phase 56.1 quotas)
SO THAT the frontend tab can switch from _fixtures.ts QUOTAS (5 items)
   to real backend.
```

**Acceptance**:
- New endpoint `GET /admin/tenants/{tenant_id}/quotas`
- Pydantic `QuotaItem` + `QuotaListResponse`
- Maps to existing `platform_layer/tenant/quota.py` (Redis tokens-only currently — return structured view per Sprint 57.47 audit)
- ≥6 NEW pytest tests
- Multi-tenant isolation preserved

### US-4: RateLimits Backend (Track D — most complex, full-scratch)

```
AS a platform admin viewing /tenant-settings Rate Limits tab
I WANT a GET /admin/tenants/{tenant_id}/rate-limits endpoint returning tenant's
   rate limit configuration (per-resource thresholds)
SO THAT the frontend tab can switch from _fixtures.ts RATE_LIMITS (3 items)
   to real backend.
```

**Acceptance**:
- Day 0.8 decision: if pure read-only fixture-projection ≤ 4 hr → ship Track D
- If needs new ORM table → assess Day 0.8 Prong 3 schema verify; if > 6 hr → DEFER to Sprint 57.49 with 🚧 reason
- New endpoint `GET /admin/tenants/{tenant_id}/rate-limits` (if shipped)
- Pydantic `RateLimitItem` + `RateLimitListResponse`
- ≥4 NEW pytest tests (or 🚧 if deferred)

### US-5: AP-4 Frontend Hygiene (Track E — small bonus)

```
AS a frontend engineer maintaining V2 lint baseline
I WANT pre-existing AP-4 violations in `frontend/src/pages/auth/{invite,login,register}`
   fixed so 9 V2 lints baseline returns to 9/9 green (currently 8/9 since Sprint 57.46)
SO THAT future sprint Day 1 validation sweeps don't carry the "1 pre-existing" caveat.
```

**Acceptance**:
- Per `04-anti-patterns.md` §AP-4 (Potemkin Features): identify why these 3 frontend pages flag AP-4 + fix without breaking tests
- 9 V2 lints: 9/9 green (no pre-existing baseline)
- No frontend behavior change (Vitest + Playwright tests still PASS)
- Vite build unchanged ±1KB

### US-6: Validation + Documentation

```
AS the parent AI assistant maintaining Sprint workflow discipline
I WANT clean validation sweep + retro + memory + per-track CHANGE records +
   sprint-workflow calibration updates for Sprint 57.48
SO THAT Sprint 57.49+ can proceed cleanly with full TenantSettings backend stack.
```

**Acceptance**:
- Standard validation chain: black + isort + flake8 + mypy --strict + 9 V2 lints + pytest + LLM SDK leak + alembic upgrade head (if any migration)
- 1 CHANGE record per Track (CHANGE-013 to CHANGE-017)
- retrospective.md Q1-Q7 with **2nd validation under `agent_factor = 0.65` ratio + decision** + **`medium-backend` 4th data point trend assessment**
- sprint-workflow.md updates (MHist + matrix + Activation history)
- memory/project_phase57_48_*.md subfile
- MEMORY.md pointer entry
- CLAUDE.md Current Sprint row + Last Updated footer (navigator-only per Sprint Closeout policy)

---

## 4. Technical Specification

### 4.1 Pattern reuse from Sprint 57.47 MEMBERS

All 4 backend tracks (A-D) follow the same pattern from Sprint 57.47 `GET /admin/tenants/{tenant_id}/members`:

```python
class {Resource}Item(BaseModel):
    # fields exposed for admin LIST view
    model_config = ConfigDict(from_attributes=True)

class {Resource}ListResponse(BaseModel):
    items: list[{Resource}Item]
    total: int
    limit: int
    offset: int

@router.get(
    "/{tenant_id}/{resource_slug}",
    response_model={Resource}ListResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def list_tenant_{resource}(
    tenant_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> {Resource}ListResponse:
    # 1. verify tenant exists; 404 if not
    # 2. query resource scoped to tenant_id
    # 3. paginate + return
```

### 4.2 Per-track resource mapping

| Track | Resource slug | Source ORM/service | Fields to expose (initial) |
|---|---|---|---|
| A HITLPolicies | `hitl-policies` | `DBHITLPolicyStore` | id, action, threshold, requires_approval, scope, updated_at |
| B FeatureFlags | `feature-flags` | `feature_flags` table (Phase 56.1) | flag_name, enabled, scope, updated_at |
| C Quotas | `quotas` | `quota.py` Redis + ORM if exists | resource, limit, period, current_usage, updated_at |
| D RateLimits | `rate-limits` | TBD Day 0.8 (full-scratch) | resource, limit, window_sec |

### 4.3 Track D Day 0.8 decision tree

1. Read `frontend/src/features/tenant-settings/_fixtures.ts` RATE_LIMITS fixture → understand expected structure
2. Search for existing rate-limit module in `backend/src/`:
   - `platform_layer/middleware/rate_limit*.py`?
   - `agent_harness/guardrails/.../rate_limit*`?
3. If existing module found → minor adapter to expose tenant-scoped GET (~2-3 hr)
4. If full-scratch needed:
   - Option A: pure fixture-projection from `tenants.meta_data` JSON (~2-3 hr; defer real persistence Phase 58.x)
   - Option B: new `tenant_rate_limits` ORM + Alembic 0019 migration + endpoint (~5-6 hr)
   - **Decision rule**: Option A if Sprint 57.48 ≥ 80% complete by Day 1 mid-point; Option B 🚧 deferred Sprint 57.49

### 4.4 AP-4 cleanup approach (Track E)

Per `04-anti-patterns.md` §AP-4 (Potemkin Features = structure but no content):
1. Read each of 3 auth pages (`frontend/src/pages/auth/{invite,login,register}`) — identify why AP-4 flags
2. Common causes:
   - Empty/stub components imported but unused
   - Stub backend integration commented out
   - Mock data placeholders left in production code
3. Fix without breaking behavior — possibly delete unused imports / consolidate stubs
4. Verify: `python scripts/lint/run_all.py` returns 9/9 green

---

## 5. File Change List

### Modified
- `backend/src/api/v1/admin/tenants.py` (Tracks A/B/C/D — append 4 NEW endpoints + 8 NEW Pydantic models)
- `frontend/src/pages/auth/invite.tsx` (Track E — AP-4 fix)
- `frontend/src/pages/auth/login.tsx` (Track E — AP-4 fix)
- `frontend/src/pages/auth/register.tsx` (Track E — AP-4 fix)

### New
- `backend/tests/integration/api/test_admin_tenant_hitl_policies.py` (Track A — ≥6 tests)
- `backend/tests/integration/api/test_admin_tenant_feature_flags.py` (Track B — ≥6 tests)
- `backend/tests/integration/api/test_admin_tenant_quotas.py` (Track C — ≥6 tests)
- `backend/tests/integration/api/test_admin_tenant_rate_limits.py` (Track D — ≥4 tests OR 🚧)
- `claudedocs/4-changes/feature-changes/CHANGE-013-tenant-settings-hitl-policies-backend.md`
- `claudedocs/4-changes/feature-changes/CHANGE-014-tenant-settings-feature-flags-backend.md`
- `claudedocs/4-changes/feature-changes/CHANGE-015-tenant-settings-quotas-backend.md`
- `claudedocs/4-changes/feature-changes/CHANGE-016-tenant-settings-rate-limits-backend.md` (OR carryover memo)
- `claudedocs/4-changes/feature-changes/CHANGE-017-ap4-frontend-auth-hygiene.md`

### Conditional
- `backend/src/infrastructure/db/migrations/versions/0019_*.py` (only if Track D requires new table)

---

## 6. Workload

**Bottom-up est**: ~15.5 hr (mid of 12.5-18.5)
- Track A HITLPolicies: 2.5 hr
- Track B FeatureFlags: 3.5 hr
- Track C Quotas: 4 hr
- Track D RateLimits: 5 hr (mid; could be 4-6)
- Track E AP-4: 0.5 hr
- Day 0 三-prong: 0.5 hr
- Day 2 closeout: 1 hr

**Class-calibrated commit** (`medium-backend` 0.80):
- 15.5 × 0.80 = **~12.4 hr committed**

**Agent-adjusted commit** (`agent_factor = 0.65` — Sprint 57.47 1st validation, now 2nd validation):
- 12.4 × 0.65 = **~8.1 hr agent-adjusted**

**4-segment form**:
> Bottom-up est ~15.5 hr → class-calibrated commit ~12.4 hr (mult 0.80) → agent-adjusted commit ~8.1 hr (`agent_factor` 0.65)

**Predicted outcomes**:
- If 5-7× agent speedup (like Sprint 57.47 single-domain backend) → actual ~2-3 hr → ratio ~0.25-0.37 → **2nd consecutive < 0.7 → MANDATORY tighten** per rollback rule (2 sprints < 0.7 → 0.45)
- If 2-3× speedup (like Sprint 57.46 multi-track) → actual ~4-5 hr → ratio ~0.49-0.62 → still < 0.7 → same tighten trigger
- If ratio in band [0.85, 1.20] → 0.65 validated; preserve

**Strategic interpretation**: Sprint 57.48 is a **mechanical-single-domain pattern reuse-heavy** sprint (4 admin GET endpoints sharing MEMBERS pattern + small frontend lint). Per pendulum evidence (Sprint 57.46 multi-track 1.60 vs Sprint 57.47 single-domain 0.27), prediction: ratio likely < 0.7 again → 2nd consecutive trigger → tighten 0.65 → 0.45 OR validate `mechanical-single-domain` sub-class 0.45 / `mixed-multidomain-bundle` 0.65 split.

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | 4 NEW endpoints shipped (HITLPolicies + FF + Quotas + RateLimits) OR 3 + 🚧 RateLimits deferred | grep route paths in tenants.py |
| AC-2 | ≥6 NEW tests per Track A/B/C; ≥4 for Track D (or 🚧) | pytest count delta ≥ 22 |
| AC-3 | mypy --strict 0 errors | mypy output |
| AC-4 | Backend lint clean | black + isort + flake8 exit 0 |
| AC-5 | 9 V2 lints: 9/9 green (Track E AP-4 fix) | run_all.py |
| AC-6 | LLM SDK leak: 0 | existing check |
| AC-7 | Multi-tenant isolation preserved (all 4 endpoints filter by tenant_id) | pytest multi-tenant tests pass |
| AC-8 | File headers updated (tenants.py + 4 test files + 3 frontend pages) | grep MHist newest entries |
| AC-9 | 5 CHANGE records (or 4 + 🚧 carryover memo for RateLimits) | ls claudedocs/4-changes/ |
| AC-10 | Day 0 三-prong report logged | Read progress.md |
| AC-11 | Track E AP-4 fix verified by V2 lints | run_all.py exit 0 |
| AC-12 | Vite build unchanged ±1KB (no behavior change in auth pages) | npm run build before/after |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Track D RateLimits full-scratch > 6 hr | Medium-High | Day 0.8 decision tree §4.3; Option A (fixture-projection from meta_data) if Option B too costly; 🚧 defer Sprint 57.49 with explicit reason if both blow up |
| AP-4 fix breaks auth page Vitest/Playwright tests | Medium | Read each page carefully Day 1; run `npm run test` + `npm run test:e2e` (if available) after each fix |
| `feature_flags` table per-tenant scope vs global scope confusion | Low | Day 0.8 Prong 2 content-verify on Phase 56.1 feature_flags Pydantic; confirm whether `tenant_id` column exists |
| `quota.py` Redis-only currently — no structured GET available | Medium | Track C may need minor adapter; Day 0.8 will determine scope |
| `DBHITLPolicyStore` API surface different from MEMBERS pattern assumption | Low | Day 0.8 Prong 2 content-verify on DBHITLPolicyStore.list_policies or equivalent |
| **2nd consecutive < 0.7 under `agent_factor 0.65`** | High (predicted) | MANDATORY per rollback rule; Day 2 retro Q4 will tighten OR split sub-class |
| Risk Class B (cross-platform mypy `unused-ignore`) | Low | Standard pattern |

---

## 9. Carryover ADs (for Sprint 57.49+ pickup)

If Sprint 57.48 closes cleanly with all 4 backend tracks + AP-4:

- `AD-TenantSettings-{any-track}-Defer` (only if Track D 🚧)
- `AD-AgentFactor-Sub-Class-Calibration` 3rd data point (if 2nd validation triggers tighten or split, Sprint 57.49 validates new value)
- `AD-medium-backend-Baseline-Recalibration` (4th data point evidence; 5th in Sprint 57.49 if continued below band)
- Potential NEW from Day 0.8 三-prong

---

**Modification History**:
- 2026-05-26: Sprint 57.48 Day 0.1 — Initial draft (5-track wave: 4 TenantSettings backend tabs + 1 AP-4 hygiene; 2nd `agent_factor 0.65` validation; 4th `medium-backend 0.80` data point)
