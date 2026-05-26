# Sprint 57.47 — Phase 58+ Backend Schema Extension Wave (Admin-Tenants LIST + TenantSettings Round 2)

**Phase**: 57+ Frontend SaaS / Phase 58+ Backend Schema Extension (combined wave)
**Goal**: Close `AD-AdminTenants-Backend-Schema-Extension` (BLOCKING) + Round 2 of `AD-TenantSettings-Backend-Schema-Extension` (continued from Sprint 57.46 subset). Expose Sprint 57.46's 5 new Tenant columns via admin-tenants LIST endpoint + investigate/close remaining backend gaps in TenantSettings 6-tab view.
**Branch**: `feature/sprint-57-47-admin-tenants-list-schema-extension`
**Class**: `medium-backend` 0.80 (single-domain backend extension; 3-data-point mean 1.03 in band; KEEP per matrix)
**Date**: 2026-05-26 (Sprint 57.46 closeout day)
**Prior sprint reference**: Sprint 57.46 (Tenant ORM +5 cols groundwork) + Sprint 57.43 D-DAY0-6 (9-col LIST gap source)

---

## 1. Sprint Goal

```
AS a backend engineer working Phase 58+ Backend Schema Extension wave
I WANT (Track A) Sprint 57.46's 5 new Tenant ORM columns exposed via admin-tenants
   LIST endpoint TenantListItem + optional region filter + ≥10 NEW pytest tests,
   AND (Track B) TenantSettings backend completion Round 2 investigated and any
   remaining backend gaps closed (or formally deferred Phase 58+ if scope > sprint)
SO THAT admin-tenants LIST page can switch from current 7-column basic view to
   full 12-column view (id/code/display_name/state/plan/created_at/updated_at +
   region/locale/retention_days/sso_enabled/seats), AND TenantSettings 6-tab
   page has clear backend backing for each tab (FEATURE_FLAGS/QUOTAS/RATE_LIMITS/
   HITL_POLICIES/MEMBERS/DANGER_OPS), unblocking Phase 58+ frontend real-data
   migration work. Also: generate 1st validation data point under rolled-back
   `agent_factor = 0.65` (Sprint 57.46 retro Q4 rollback decision).
```

## 2. Background & Context

### 2.1 2 ADs in this wave

| AD | Source | Scope this sprint |
|---|---|---|
| 🔴 **AD-AdminTenants-Backend-Schema-Extension** | Sprint 57.43 D-DAY0-6 (BLOCKING) | Extend `TenantListItem` Pydantic + GET `/admin/tenants` LIST endpoint with 5 new cols from Sprint 57.46 (Tenant ORM); add `region` filter; ≥10 NEW pytest tests |
| **AD-TenantSettings-Backend-Schema-Extension Round 2** | Sprint 57.46 (subset closed) | Day 0.8 investigation: for each of 6 TenantSettings tabs (FEATURE_FLAGS/QUOTAS/RATE_LIMITS/HITL_POLICIES/MEMBERS/DANGER_OPS), confirm backend-backed vs fixture-only; close 1-2 cheapest gaps OR formally defer Phase 58+ |

### 2.2 Why bundle in one sprint

- Track A is direct continuation of Sprint 57.46 Track B (Tenant ORM +5 cols groundwork done; only TenantListItem exposure missing)
- Track B is opportunistic — Day 0.8 investigation tells us what's actually pending (Sprint 57.46 D-DAY0-5 lesson: investigate before assuming work exists)
- Single backend PR; shared validation sweep
- 1st validation goal under newly-rolled-back `agent_factor = 0.65`

### 2.3 `agent_factor = 0.65` 1st validation

Per `.claude/rules/sprint-workflow.md` §Active Agent Delegation Factor Modifier:
- Sprint 57.46 (1st validation at 0.45) ratio ~1.60 ABOVE band by 0.40 → rollback to 0.65 single-data-point caution rule MET
- **Sprint 57.47 = 1st validation under 0.65**:
  - If ratio in [0.85, 1.20] → 0.65 validated; preserve
  - If ratio < 0.7 → tighten back to 0.55
  - If ratio > 1.20 → roll back further to 1.0 (drop modifier; class-multiplier alone)

Sprint 57.47 is also `medium-backend` 0.80 single-domain (NOT multi-track bundle like Sprint 57.46); class structure closer to mechanical-mockup-rebuild evidence where 0.45 fit. Predict ratio ~0.7-1.0 range; preserve 0.65 likely.

---

## 3. User Stories

### US-1: Admin-Tenants LIST 5-Column Exposure (Track A primary)

```
AS a platform admin viewing /admin-tenants LIST page
I WANT the LIST endpoint to return region/locale/retention_days/sso_enabled/seats
   for each tenant (in addition to existing 7 cols id/code/display_name/state/
   plan/created_at/updated_at)
SO THAT the frontend table can display these governance columns without making
   N+1 GET /tenants/{id} calls per row, and ops teams can quickly scan tenant
   region+plan+sso+seats from a single view.
```

**Acceptance**:
- `TenantListItem` extended from 7 fields → 12 fields (5 new columns added)
- `model_config = ConfigDict(from_attributes=True)` preserved
- GET `/admin/tenants` LIST endpoint returns 12-field items per tenant
- No N+1 query (single ORM query continues; from_attributes maps additional cols cheaply)
- ≥5 NEW pytest tests verifying each new field present + value matches Tenant ORM
- Multi-tenant isolation preserved (Tenant is global; admin-only; existing pattern)
- mypy --strict 0 errors

### US-2: Admin-Tenants LIST Region Filter (Track A continuation)

```
AS a platform admin investigating regional rollouts
I WANT a `region` query param on GET /admin/tenants alongside existing
   state/plan/search params
SO THAT I can filter to a specific region (e.g. apac) when investigating
   region-scoped issues without scrolling through global tenant list.
```

**Acceptance**:
- New optional `region: str | None = Query(None)` param
- ILIKE or exact match on Tenant.region (decide in Day 0.8 — exact match preferred since region is enum-bounded)
- ≥2 NEW pytest tests: filter by region returns matching only; filter with no matches returns empty
- Backward compatibility: no `region` param = no filter (existing behavior preserved)

### US-3: TenantSettings 6-Tab Backend Audit (Track B investigation)

```
AS a future frontend engineer working /tenant-settings page real-data migration
I WANT a written audit (in progress.md or audit doc) of each of the 6 TenantSettings
   tabs (FEATURE_FLAGS/QUOTAS/RATE_LIMITS/HITL_POLICIES/MEMBERS/DANGER_OPS)
   with verdict: "real-backed" / "fixture-only" / "partial" — and for each
   fixture-only tab a recommended next-sprint scope estimate
SO THAT Phase 58+ frontend migration can prioritize tabs by backend readiness
   instead of trial-and-erroring per tab.
```

**Acceptance**:
- Day 0.8 audit table: 6 tabs × verdict × backend file references (if real) × Phase 58+ scope hr estimate (if fixture)
- For each "real-backed" tab — confirm via test (e.g. existing Quota service test passes for tenant_a sample data)
- For 1 cheapest fixture-only tab — implement backend if ≤ 2 hr (Day 1 stretch goal); otherwise defer
- Audit doc written to `progress.md` Day 0.8 §TenantSettings backend audit section + cross-referenced in retro Q4

### US-4: Validation Sweep + Documentation

```
AS the parent AI assistant maintaining Sprint workflow discipline
I WANT a clean validation sweep + retro + memory + 3 CHANGE records + sprint-workflow
   calibration update for Sprint 57.47
SO THAT Sprint 57.48+ can proceed cleanly without leftover technical debt or
   undocumented decisions.
```

**Acceptance**:
- Standard validation chain: black + isort + flake8 + mypy --strict + 9 V2 lints + pytest + LLM SDK leak guard + alembic upgrade head (if migration needed)
- 1 CHANGE record per Track A + 1 audit doc per Track B
- retrospective.md Q1-Q7 with `agent_factor 0.65` 1st validation ratio + decision
- sprint-workflow.md §Active Activation history Sprint 57.47 entry
- memory/project_phase57_47_*.md subfile

---

## 4. Technical Specification

### 4.1 Track A: Admin-Tenants LIST Schema Extension

**Target file**: `backend/src/api/v1/admin/tenants.py`

**Current TenantListItem (Sprint 57.4)** lines 165-181:
```python
class TenantListItem(BaseModel):
    id: UUID
    code: str
    display_name: str
    state: TenantState
    plan: TenantPlan
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**Sprint 57.47 extension** (add 5 fields after `plan`, before `created_at` for grouped readability):
```python
class TenantListItem(BaseModel):
    id: UUID
    code: str
    display_name: str
    state: TenantState
    plan: TenantPlan
    region: str            # NEW (Sprint 57.46 ORM col)
    locale: str            # NEW
    retention_days: int    # NEW
    sso_enabled: bool      # NEW
    seats: int             # NEW
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**LIST endpoint extension** lines 198-205:
```python
async def list_tenants(
    state: TenantState | None = Query(None),
    plan: TenantPlan | None = Query(None),
    region: str | None = Query(None),   # NEW
    search: str | None = Query(None, max_length=128),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> TenantListResponse:
```

Filter logic (after existing state/plan filters):
```python
if region is not None:
    base_stmt = base_stmt.where(Tenant.region == region)
```

### 4.2 Track B: TenantSettings 6-Tab Backend Audit

Day 0.8 investigation must produce a table like this (filled in by code-implementer agent during Day 0.8):

| Tab | Verdict | Backend file ref (if real) | Phase 58+ scope (if fixture) |
|---|---|---|---|
| FEATURE_FLAGS | TBD | `backend/src/.../feature_flags.py` ? | ? hr |
| QUOTAS | TBD | `backend/src/agent_harness/.../quota.py` (Phase 56.1) ? | ? hr |
| RATE_LIMITS | TBD | ? | ? hr |
| HITL_POLICIES | TBD | `backend/src/agent_harness/hitl/*.py` ? | ? hr |
| MEMBERS | TBD | `users` table + `tenant_users` join? | ? hr |
| DANGER_OPS | TBD | N/A (UI actions, not data) | N/A |

For each tab marked "real-backed":
- Verify by running 1 existing test OR write 1 NEW integration test that queries the backend for sample tenant data

For 1 cheapest fixture-only tab found during Day 0.8 (if ≤ 2 hr scope):
- Implement minimal read-only backend endpoint (e.g. GET tenant members LIST if `users` table already has `tenant_id` and we just need a thin admin endpoint)
- Add ≥3 NEW pytest tests
- Update CHANGE record

For all others:
- Formally defer Phase 58+ with named follow-up AD (`AD-TenantSettings-<TabName>-Backend`)

### 4.3 No new migration expected

Sprint 57.46 already shipped Alembic 0018 with all 5 new Tenant ORM columns. Sprint 57.47 is pure Pydantic + endpoint extension; no new migration. **Unless** Track B 1-cheapest-fixture-only-tab implementation requires new table (in which case Alembic 0019); decision made in Day 0.8.

---

## 5. File Change List

### Modified files
- `backend/src/api/v1/admin/tenants.py` (Track A: TenantListItem +5 fields + LIST endpoint region filter)
- `backend/tests/integration/api/test_admin_tenant_list.py` (Track A: existing list tests + ≥10 NEW for new fields + filter)

### Conditional new files (Track B; Day 0.8 decision)
- `backend/src/api/v1/admin/tenant_*.py` (1 NEW endpoint if cheapest-fixture-tab implemented)
- `backend/tests/integration/api/test_admin_tenant_*_extension.py` (≥3 NEW tests if Track B endpoint added)
- `backend/src/infrastructure/db/migrations/versions/0019_*.py` (only if Track B requires new table — Day 0.8 decision)

### New documentation
- `claudedocs/4-changes/feature-changes/CHANGE-010-admin-tenants-list-schema-extension.md`
- `claudedocs/4-changes/feature-changes/CHANGE-011-tenant-settings-tabs-backend-audit.md` (Track B audit doc)
- (Optional) `claudedocs/4-changes/feature-changes/CHANGE-012-<cheapest-tab>-backend.md` (only if Track B Day 1 stretch)

---

## 6. Workload

**Bottom-up est**: ~8 hr
- Track A US-1 (TenantListItem +5 fields + Pydantic tests): 2 hr
- Track A US-2 (region filter + tests): 1.5 hr
- Track B US-3 (Day 0.8 6-tab audit): 1 hr investigation + 0.5 hr audit doc writing
- Track B optional cheapest-tab impl: 0-2 hr (Day 1 stretch; defer if > 2 hr)
- Track A + B tests + validation sweep: 1.5 hr
- Day 0 三-prong: 0.5 hr
- Day 2 closeout (retro + memory + commits): 1 hr

**Class-calibrated commit** (`medium-backend` 0.80):
- 8 × 0.80 = **~6.4 hr committed**

**Agent-adjusted commit** (`agent_factor = 0.65` — post-Sprint-57.46 rollback):
- 6.4 × 0.65 = **~4.2 hr agent-adjusted**

**4-segment form**:
> Bottom-up est ~8 hr → class-calibrated commit ~6.4 hr (mult 0.80) → agent-adjusted commit ~4.2 hr (`agent_factor` 0.65)

**`agent_factor = 0.65` 1st validation goal**:
- Sprint 57.47 retro Q4 will compute ratio actual/committed-with-agent-factor
- Predicted bullseye if 0.65 calibrated correctly: ~1.0 (actual ~4.2 hr)
- Per rollback rule: if > 1.20 → roll back further 1.0; if < 0.7 → tighten back 0.55

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | TenantListItem has 5 new fields (region/locale/retention_days/sso_enabled/seats) | grep target fields in tenants.py → 5 matches in TenantListItem block |
| AC-2 | GET /admin/tenants LIST returns 12 fields per item | pytest assertion on response[0] keys = 12 |
| AC-3 | `region` query filter works (returns only matching) | pytest filter test |
| AC-4 | ≥10 NEW pytest tests Track A (US-1 + US-2 combined) | pytest count delta ≥ 10 |
| AC-5 | TenantSettings 6-tab backend audit table written | Read progress.md Day 0.8 §TenantSettings audit section |
| AC-6 | For each "real-backed" tab — 1 verification test passes (existing or NEW) | pytest output |
| AC-7 | For "fixture-only" tabs — formal carryover AD logged | retro Q4 + memory subfile |
| AC-8 | Track B cheapest-tab implementation (if scope ≤ 2 hr) — endpoint + ≥3 tests | pytest count delta ≥ 3 if applicable; ELSE 🚧 with reason |
| AC-9 | mypy --strict 0 errors | mypy output |
| AC-10 | Backend lint clean | black + isort + flake8 exit 0 |
| AC-11 | 9 V2 lints all green (Sprint 57.46 had 1 pre-existing AP-4; verify same baseline) | run_all.py |
| AC-12 | pytest integration/api/ + admin/ — full suite passing | pytest exit 0 |
| AC-13 | LLM SDK leak: 0 | existing check |
| AC-14 | Multi-tenant isolation preserved (Tenant is global; admin-only) | existing pattern |
| AC-15 | File headers updated per convention | Read 3 files |
| AC-16 | 2 CHANGE records (CHANGE-010 + CHANGE-011) | ls dir |
| AC-17 | Day 0 三-prong report logged in progress.md | Read progress.md |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `from_attributes=True` does not auto-include new fields | Low | Pydantic v2 with `from_attributes=True` should auto-map; verify Day 0.8 by Read existing Sprint 57.46 TenantResponse extension |
| Existing list tests break due to schema-shape change | Medium | Same pattern as Sprint 57.46 `test_get_tenant_response_shape` 10→15 update — expected to surface 1-2 tests requiring shape-key count update; agent should update them |
| `region` exact-match insensitive to case (e.g. "APAC" vs "apac") | Low | Region values are enum-bounded {apac/emea/americas/global}; exact match safe |
| Track B 6-tab audit reveals more work than expected (>2 hr cheapest tab) | Medium-High | Day 0.8 has scope decision rule: if cheapest tab > 2 hr → defer ALL Track B impl; investigation-only deliverable |
| `agent_factor = 0.65` under-corrects → ratio > 1.20 | Medium | 1st validation under 0.65; per rollback rule single > 1.20 → roll back to 1.0 (drop modifier) |
| `agent_factor = 0.65` over-corrects → ratio < 0.7 | Medium | Per rollback rule: 1 sprint < 0.7 → consider tighten back to 0.55 for 2-sprint window |
| Risk Class B (cross-platform mypy `unused-ignore`) | Low | Standard `# type: ignore[X, unused-ignore]` pattern per code-quality.md |

---

## 9. Carryover ADs (for Sprint 57.48+ pickup)

If Sprint 57.47 closes cleanly:

- Per Track B Day 0.8 audit results: 1 carryover AD per fixture-only tab not closed (e.g. `AD-TenantSettings-Quotas-Backend`, `AD-TenantSettings-Members-Backend` etc)
- `AD-AgentFactor-Sub-Class-Calibration` (Sprint 57.46 carryover) — 2nd data point after Sprint 57.47 validates 0.65 or further rolls back
- Potential NEW from Sprint 57.47 Day 0.8 三-prong findings

---

**Modification History**:
- 2026-05-26: Sprint 57.47 Day 0.1 — Initial draft (Phase 58+ Backend Schema Extension wave; combined admin-tenants LIST + TenantSettings audit; 1st `agent_factor = 0.65` validation)
