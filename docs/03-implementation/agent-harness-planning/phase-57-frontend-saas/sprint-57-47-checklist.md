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
- [ ] `backend/src/api/v1/admin/tenants.py` exists ✓ (Sprint 57.46 already touched)
- [ ] `backend/src/infrastructure/db/models/identity.py` exists (Tenant ORM with 5 new cols from Sprint 57.46)
- [ ] `backend/tests/integration/api/test_admin_tenant_*.py` exists (LIST endpoint test pattern reference)
- [ ] `backend/src/agent_harness/.../quota.py` exists (Track B QUOTAS tab investigation)
- [ ] `backend/src/agent_harness/hitl/` directory exists (Track B HITL_POLICIES tab investigation)
- [ ] `frontend/src/features/tenant-settings/_fixtures.ts` exists (Track B fixture source reference)

**Prong 2 — Content Verify** (5 claims):
- [ ] Tenant ORM has 5 new cols (region/locale/retention_days/sso_enabled/seats) — verify Sprint 57.46 work landed correctly
- [ ] TenantListItem current 7 fields (id/code/display_name/state/plan/created_at/updated_at) — confirm baseline before extension
- [ ] `from_attributes=True` on TenantListItem → confirms auto-mapping for new ORM cols (no manual mapping needed)
- [ ] Existing list endpoint filters (state/plan/search) pattern — confirms how to add region filter
- [ ] TenantSettings _fixtures.ts current sections (FEATURE_FLAGS/QUOTAS/RATE_LIMITS/HITL_POLICIES/MEMBERS/DANGER_OPS) — confirm 6 tabs scope per Sprint 57.44 memory

**Prong 3 — Schema Verify** (N/A this sprint — no new tables planned in Track A; Track B may add tables based on Day 0.8 decision, then add Prong 3 follow-up):
- [ ] No new tables in Track A (TenantListItem extension is Pydantic-only on existing Tenant ORM); skip Prong 3 unless Track B triggers new table
- [ ] If Track B Day 0.8 audit finds cheapest fixture-only tab needs new table → Prong 3 schema verify on the proposed table before Day 1 code

**Prong 2.5 — Frontend Tree Depth Audit** (N/A — pure backend sprint; no frontend page re-point)

**Drift findings catalog**:
- [ ] All findings logged to `progress.md` Day 0 §Drift findings (D-DAY0-N format)
- [ ] Go/no-go decision recorded

### 0.8b Day 0 TenantSettings 6-Tab Backend Audit (Track B investigation)

For each of 6 tabs, fill table in progress.md Day 0 §TenantSettings backend audit section:

- [ ] **FEATURE_FLAGS**: Verdict + backend file ref or fixture-only + Phase 58+ scope hr
- [ ] **QUOTAS**: Verdict + ref to Phase 56.1 quota.py? + scope
- [ ] **RATE_LIMITS**: Verdict + ref? + scope
- [ ] **HITL_POLICIES**: Verdict + ref to agent_harness/hitl? + scope
- [ ] **MEMBERS**: Verdict + ref to users/tenant_users? + scope
- [ ] **DANGER_OPS**: Verdict (likely N/A UI actions)

Decision rule:
- If cheapest fixture-only tab ≤ 2 hr → Track B Day 1 stretch goal: implement it
- If all fixture-only tabs > 2 hr → defer ALL Track B impl; investigation-only deliverable

### 0.9 Branch + Day 0 commit
- [x] Branch `feature/sprint-57-47-admin-tenants-list-schema-extension` created ✓
- [ ] Day 0.1 + 0.8 commit: `chore(sprint-57-47): Day 0 plan + checklist + 三-prong verify + TenantSettings audit`

---

## Day 1 — Implementation (Code-Implementer Agent Delegation)

### 1.1 Track A US-1: TenantListItem 5-Column Exposure
- [ ] **Extend `TenantListItem` Pydantic** with 5 new fields (region/locale/retention_days/sso_enabled/seats)
  - DoD: 12 total fields; `from_attributes=True` preserved; types match Tenant ORM
  - Verify: grep 5 new field names in tenants.py TenantListItem class
- [ ] **No endpoint logic change for US-1** (from_attributes auto-maps; just Pydantic schema extension)
  - DoD: existing query still works; new cols auto-included
- [ ] **≥5 NEW pytest tests** for new fields in list response
  - DoD: GET /admin/tenants → response[0] has 12 keys; each new field value matches Tenant ORM source
  - Verify: pytest count ≥ 5

### 1.2 Track A US-2: Region Filter
- [ ] **Add `region: str | None = Query(None)` param** to list_tenants signature
  - DoD: Param appears in signature; in OpenAPI schema if visible
- [ ] **Add region filter logic** `if region is not None: base_stmt = base_stmt.where(Tenant.region == region)`
  - DoD: Filter applied; verified by pytest
- [ ] **≥2 NEW pytest tests for region filter** (positive match + no match)
  - DoD: pytest count ≥ 2
  - Verify: pytest output

### 1.3 Track B (Day 0.8 decision-gated)

**If Day 0.8 audit determines cheapest tab ≤ 2 hr**:
- [ ] **Implement cheapest fixture-only tab backend endpoint** (TBD from audit)
  - DoD: GET endpoint + Pydantic schema + ≥3 NEW pytest tests
  - Verify: pytest count ≥ 3
- [ ] **CHANGE-012 record** for the cheapest-tab implementation

**Else (all fixture-only tabs > 2 hr)**:
- [ ] Mark Track B Day 1 stretch as 🚧 deferred with reason in progress.md
- [ ] Log carryover AD per fixture-only tab: `AD-TenantSettings-<TabName>-Backend` for each

### 1.4 Documentation
- [ ] **CHANGE-010** `claudedocs/4-changes/feature-changes/CHANGE-010-admin-tenants-list-schema-extension.md`
  - DoD: Problem / Root cause / Solution / Verification / Impact
- [ ] **CHANGE-011** `claudedocs/4-changes/feature-changes/CHANGE-011-tenant-settings-tabs-backend-audit.md`
  - DoD: 6-tab audit table + verdicts + scope estimates
- [ ] **File headers updated** per convention (modified files; MHist 1-line)
  - DoD: tenants.py MHist 1-line entry

### 1.5 Day 1 Validation Sweep
- [ ] Backend lint chain: `black backend/src backend/tests && isort backend/src backend/tests && flake8 backend/src backend/tests`
  - DoD: exit 0
- [ ] Backend mypy --strict: `mypy backend/src`
  - DoD: 0 errors (cross-platform `unused-ignore` pattern if needed)
- [ ] 9 V2 lints: `python scripts/lint/run_all.py`
  - DoD: 9/9 green OR same baseline as Sprint 57.46 (8/9 with pre-existing AP-4 unchanged)
- [ ] Backend pytest: integration/api/ + admin/
  - DoD: ≥10 NEW (Track A) + 0 regressions; ≥3 if Track B stretch
- [ ] LLM SDK leak guard: 0 imports
- [ ] Existing TenantListResponse shape tests (if any) — update for 12-field schema (mirror Sprint 57.46 `test_get_tenant_response_shape` 10 → 15 pattern)

### 1.6 Day 1 commit
- [ ] Commit: `feat(sprint-57-47): Day 1 admin-tenants LIST schema extension + TenantSettings 6-tab audit`

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
