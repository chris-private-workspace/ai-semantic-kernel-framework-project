# Sprint 57.47 — Checklist

[Plan](./sprint-57-47-plan.md) — Phase 58+ Backend Schema Extension wave (admin-tenants LIST 5-col exposure + TenantSettings 6-tab audit); 1st `agent_factor = 0.65` validation.

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] **Sprint plan written** `sprint-57-47-plan.md`
  - DoD: 9 sections; 4-segment Workload form
- [x] **Sprint checklist written** (this file)
  - DoD: Day 0 / Day 1 / Day 2 structure

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

**Prong 1 — Path Verify** (6 paths):
- [x] `backend/src/api/v1/admin/tenants.py` exists ✓ (Sprint 57.46 already touched)
- [x] `backend/src/infrastructure/db/models/identity.py` exists (Tenant ORM with 5 new cols from Sprint 57.46)
- [x] `backend/tests/integration/api/test_admin_tenant_*.py` exists (LIST endpoint test pattern reference)
- [x] `backend/src/agent_harness/.../quota.py` exists (Track B QUOTAS tab investigation) — D-DAY0-1: actual path `backend/src/platform_layer/tenant/quota.py`
- [x] `backend/src/agent_harness/hitl/` directory exists (Track B HITL_POLICIES tab investigation)
- [x] `frontend/src/features/tenant-settings/_fixtures.ts` exists (Track B fixture source reference)

**Prong 2 — Content Verify** (5 claims):
- [x] Tenant ORM has 5 new cols (region/locale/retention_days/sso_enabled/seats) — verify Sprint 57.46 work landed correctly
- [x] TenantListItem current 7 fields (id/code/display_name/state/plan/created_at/updated_at) — confirm baseline before extension
- [x] `from_attributes=True` on TenantListItem → confirms auto-mapping for new ORM cols (no manual mapping needed)
- [x] Existing list endpoint filters (state/plan/search) pattern — confirms how to add region filter
- [x] TenantSettings _fixtures.ts current sections (FEATURE_FLAGS/QUOTAS/RATE_LIMITS/HITL_POLICIES/MEMBERS/DANGER_OPS) — confirm 6 tabs scope per Sprint 57.44 memory

**Prong 3 — Schema Verify** (N/A this sprint — no new tables planned in Track A; Track B may add tables based on Day 0.8 decision, then add Prong 3 follow-up):
- [x] No new tables in Track A (TenantListItem extension is Pydantic-only on existing Tenant ORM); skip Prong 3 unless Track B triggers new table
- [x] If Track B Day 0.8 audit finds cheapest fixture-only tab needs new table → Prong 3 schema verify on the proposed table before Day 1 code — Track B MEMBERS chose; User ORM already has needed fields, no new table

**Prong 2.5 — Frontend Tree Depth Audit** (N/A — pure backend sprint; no frontend page re-point)

**Drift findings catalog**:
- [x] All findings logged to `progress.md` Day 0 §Drift findings (D-DAY0-N format) — D-DAY0-1/2/3 logged
- [x] Go/no-go decision recorded — GO

### 0.8b Day 0 TenantSettings 6-Tab Backend Audit (Track B investigation)

For each of 6 tabs, fill table in progress.md Day 0 §TenantSettings backend audit section:

- [x] **FEATURE_FLAGS**: partial (real ORM, no admin GET); ~3-4 hr
- [x] **QUOTAS**: partial (Redis-only single-dim QuotaEnforcer); ~3-5 hr
- [x] **RATE_LIMITS**: fixture-only (no backend module); ~4-6 hr
- [x] **HITL_POLICIES**: partial (ABC + DBHITLPolicyStore impl, no admin GET); ~2-3 hr
- [x] **MEMBERS**: partial (User ORM ready); **~1.5-2 hr ← CHEAPEST**
- [x] **DANGER_OPS**: N/A (UI actions)

Decision rule:
- If cheapest fixture-only tab ≤ 2 hr → Track B Day 1 stretch goal: implement it
- If all fixture-only tabs > 2 hr → defer ALL Track B impl; investigation-only deliverable

### 0.9 Branch + Day 0 commit
- [x] Branch `feature/sprint-57-47-admin-tenants-list-schema-extension` created ✓
- [x] Day 0/Day 1 work combined into single commit (small-scope sprint)

---

## Day 1 — Implementation (Code-Implementer Agent Delegation)

### 1.1 Track A US-1: TenantListItem 5-Column Exposure
- [x] **Extend `TenantListItem` Pydantic** with 5 new fields (region/locale/retention_days/sso_enabled/seats) — 12 total fields confirmed
- [x] **No endpoint logic change for US-1** (from_attributes auto-maps)
- [x] **≥5 NEW pytest tests** for new fields in list response — shipped 6 (5 fields + 1 server_default)

### 1.2 Track A US-2: Region Filter
- [x] **Add `region: str | None = Query(None, max_length=32)` param** to list_tenants signature
- [x] **Add region filter logic** `if region is not None: base_stmt = base_stmt.where(Tenant.region == region)`
- [x] **≥2 NEW pytest tests for region filter** — shipped 6 (positive/no-match/2 combo/backward-compat/max-length)

### 1.3 Track B (Day 0.8 decision-gated)

Day 0.8 audit determined MEMBERS @ ~1.5-2 hr cheapest → **proceeded with stretch**.

- [x] **Implement MEMBERS endpoint** `GET /admin/tenants/{tenant_id}/members` returning TenantMemberListResponse (id/email/display_name/status/created_at × paginated)
- [x] **8 NEW pytest tests** in test_admin_tenant_members.py (auth + 404 + happy + shape + multi-tenant isolation + pagination + empty + invalid limit)
- [x] **CHANGE-012 record** for MEMBERS implementation
- [x] 4 non-MEMBERS tabs deferred → carryover ADs logged (FeatureFlags/Quotas/RateLimits/HITLPolicies Phase 58+)

### 1.4 Documentation
- [x] **CHANGE-010** admin-tenants-list-schema-extension
- [x] **CHANGE-011** tenant-settings-tabs-backend-audit (6-tab table + 4 carryover ADs)
- [x] **CHANGE-012** tenant-settings-members-backend
- [x] **File headers updated** — tenants.py MHist 1-line; new test_admin_tenant_members.py header complete

### 1.5 Day 1 Validation Sweep
- [x] Backend lint chain: black + isort + flake8 — exit 0
- [x] Backend mypy --strict on tenants.py — 0 errors
- [x] 9 V2 lints: **8/9 green; 1 pre-existing AP-4 frontend baseline unchanged** (matches Sprint 57.46)
- [x] Backend pytest integration/api/ — **188 PASSED + 0 regressions** (+20 NEW: 12 Track A + 8 Track B)
- [x] LLM SDK leak guard: 0 imports in `agent_harness/` (matches are doc comments only)
- [x] Existing happy-path shape assertion updated 7 → 12 keys

### 1.6 Day 1 commit
- [ ] Commit: `feat(sprint-57-47): Day 1 admin-tenants LIST schema extension + TenantSettings 6-tab audit + MEMBERS endpoint`

---

## Day 2 — Closeout

### 2.1 Validation
- [ ] Full backend test suite passing
- [ ] Frontend build unchanged (no frontend code change expected)
- [ ] No regressions in existing admin tenant tests

### 2.2 Retrospective
- [ ] **Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-47/retrospective.md`**
  - DoD: Q1-Q7 6 必答 format; ratio actual/committed-with-agent-factor computed
- [ ] **`agent_factor = 0.65` 1st validation data point** logged
  - DoD: Q4 explicit ratio + rollback decision (KEEP 0.65 / tighten back 0.55 / roll back further 1.0 / Option B per-class split)

### 2.3 Sprint-workflow.md updates
- [ ] **Update `medium-backend` 0.80 row** (3rd or 4th data point depending on prior count) — add Sprint 57.47 to data points list
- [ ] **Update §Active Agent Delegation Factor Modifier §Activation history** with Sprint 57.47 1st validation entry under 0.65

### 2.4 Memory + index
- [ ] **Write `memory/project_phase57_47_admin_tenants_list_schema_extension.md`**
- [ ] **Add MEMORY.md pointer entry**

### 2.5 CLAUDE.md Current Sprint row update
- [ ] **Update Current Sprint row + Last Updated footer** per Sprint Closeout policy navigator-only rule

### 2.6 PR + merge
- [ ] **Push branch + open PR** with description containing 2 AD closure status + ratio + calibration
- [ ] **Wait CI green** (backend-ci + V2 Lint)
- [ ] **Merge PR** (squash) — user-triggered per session convention
- [ ] **Cleanup**: delete local feature branch

### 2.7 Final
- [ ] **Day 2 commit**: `chore(sprint-57-47): Day 2 retro + memory + closeout`
- [ ] **All checklist items above**: `[x]` (or 🚧 with reason if deferred)

---

**Modification History**:
- 2026-05-26: Sprint 57.47 Day 0.1 — Initial draft (mirrors Sprint 57.46 Day 0/1/2 structure; class `medium-backend` 0.80 + `agent_factor` 0.65 1st validation)
