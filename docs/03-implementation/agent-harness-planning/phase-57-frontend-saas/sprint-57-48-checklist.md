# Sprint 57.48 — Checklist

[Plan](./sprint-57-48-plan.md) — 5-track wave (HITLPolicies + FF + Quotas + RateLimits + AP-4 hygiene); 2nd `agent_factor = 0.65` validation; 4th `medium-backend 0.80` data point.

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] **Plan written** `sprint-57-48-plan.md`
- [x] **Checklist written** (this file)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

**Prong 1 — Path Verify** (8 paths):
- [x] `backend/src/api/v1/admin/tenants.py` exists (extension target)
- [x] `backend/src/agent_harness/hitl/` directory exists (ABC only; concrete `DBHITLPolicyStore` lives at `platform_layer/governance/hitl/policy_store.py` per D-DAY0-2)
- [x] `backend/src/infrastructure/db/models/feature_flag.py` ORM file exists
- [x] `backend/src/platform_layer/tenant/quota.py` exists (Redis-only — D-DAY0-4)
- [x] `frontend/src/pages/auth/{invite,login,register}/index.tsx` exist (subdir not flat per D-DAY0-1)
- [x] `backend/tests/integration/api/test_admin_tenant_members.py` exists (MEMBERS template)
- [x] `frontend/src/features/tenant-settings/_fixtures.ts` exists
- [x] Migration head = `0018_tenant_settings_extension.py` (next slot 0019 NOT needed per Track D Option A)

**Prong 2 — Content Verify** (7 claims):
- [x] DBHITLPolicyStore returns SINGLE composite `HITLPolicy | None` (NOT list) — D-DAY0-2 pivot via projection helper
- [x] `feature_flags` is global registry with `tenant_overrides JSONB` (NOT per-tenant rows) — D-DAY0-3 pivot via JSONB resolution
- [x] `quota.py` is Redis-only; structured config via `PlanLoader.get_plan().quota` — D-DAY0-4 pivot
- [x] NO existing `rate_limit*.py` module — D-DAY0-5 Option A locked
- [x] AP-4 violations re-classified: lint regex `\bplaceholder\b` matched HTML5 `placeholder=` JSX attr + TS keys — D-DAY0-6 (false positives, fix detector not pages)
- [x] Sprint 57.47 MEMBERS pattern confirmed (5-step: Item + ListResponse + endpoint + paginate + tenant_id filter)
- [x] `_fixtures.ts` field shapes mapped to Pydantic models

**Prong 3 — Schema Verify** (conditional on Track D):
- [x] Track D Option A locked → N/A (no new ORM); Prong 3 skipped

**Prong 2.5 — Frontend Tree Depth Audit**:
- [x] Applied to Track E: read each of 3 auth `index.tsx` files in full; identified lint false-positive root cause

**Drift findings catalog**:
- [x] D-DAY0-1 through D-DAY0-6 logged to `progress.md` Day 0 §Drift findings
- [x] Track D scope decision = Option A (fixture-projection from `tenants.meta_data`)
- [x] Go/no-go: ✅ GO (scope shift < 20%)

### 0.9 Branch + Day 0 commit
- [x] Branch `feature/sprint-57-48-tenant-settings-backend-completion-wave` created
- [x] Day 0 + Day 1 combined commit (small-scope precedent from Sprint 57.47)

---

## Day 1 — Implementation (Code-Implementer Agent Delegation)

### 1.1 Track A — HITLPolicies Backend (cheapest, first)
- [x] Add `HITLPolicyItem` + `HITLPolicyListResponse` Pydantic models to `tenants.py`
- [x] Add `GET /admin/tenants/{tenant_id}/hitl-policies` endpoint
- [x] Add 7 NEW pytest tests in `test_admin_tenant_hitl_policies.py` (≥6 target)
- [x] CHANGE-013 record

### 1.2 Track B — FeatureFlags Admin GET
- [x] Add `FeatureFlagItem` + `FeatureFlagListResponse` models
- [x] Add `GET /admin/tenants/{tenant_id}/feature-flags` endpoint
- [x] 8 NEW pytest tests in `test_admin_tenant_feature_flags.py` (≥6 target)
- [x] CHANGE-014 record

### 1.3 Track C — Quotas Admin GET
- [x] Add `QuotaItem` + `QuotaListResponse` models
- [x] Add `GET /admin/tenants/{tenant_id}/quotas` endpoint
- [x] 8 NEW pytest tests in `test_admin_tenant_quotas.py` (≥6 target)
- [x] CHANGE-015 record

### 1.4 Track D — RateLimits Backend (Day 0.8 decision-gated)

**Option A LOCKED (fixture-projection from `tenants.meta_data` JSON)**:
- [x] Add `RateLimitItem` + `RateLimitListResponse` models
- [x] Add `GET /admin/tenants/{tenant_id}/rate-limits` endpoint (reads from meta_data with DEFAULT_RATE_LIMITS fallback)
- [x] 6 NEW pytest tests in `test_admin_tenant_rate_limits.py` (≥4 target)
- [x] CHANGE-016 record

### 1.5 Track E — AP-4 Lint False-Positive Fix
- [x] Read each of 3 `auth/{X}/index.tsx` files (Prong 2.5 depth audit)
- [x] Identified root cause: lint regex matching HTML5 `placeholder=` attribute (D-DAY0-6 false positive, NOT Potemkin)
- [x] Applied fix to LINT SCRIPT (`check_ap4_frontend_placeholder.py` — added `JSX_PLACEHOLDER_ATTR` + `TS_PLACEHOLDER_KEY` masks)
- [x] 0 frontend pages touched (behaviour preserved by construction)
- [x] `python scripts/lint/run_all.py` → **9/9 green** ✅
- [x] Vite build unchanged (no frontend file touched)
- [x] CHANGE-017 record

### 1.6 Day 1 Validation Sweep
- [x] black + isort + flake8 — exit 0
- [x] mypy --strict — 0 errors
- [x] **9 V2 lints: 9/9 green** ✅
- [x] pytest integration/api/ — 217 PASS (29 NEW: 7+8+8+6 across A-D; 0 regressions vs Sprint 57.47 baseline 188)
- [x] LLM SDK leak: 0
- [x] Frontend `npm run lint` + `npm run build` exit 0

### 1.7 Day 1 commit
- [x] Commit: `feat(sprint-57-48): Day 1 — TenantSettings 4-tab backend completion wave + AP-4 hygiene`

---

## Day 2 — Closeout

### 2.1 Validation
- [ ] Full backend test suite passing
- [ ] No regressions in existing admin tenant tests
- [ ] Frontend Vite build clean

### 2.2 Retrospective
- [ ] **Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-48/retrospective.md`**
  - DoD: Q1-Q7 6 必答 format
- [ ] **2nd validation under `agent_factor = 0.65`** logged in Q4
  - DoD: Ratio + rollback decision (KEEP / tighten 0.55 / tighten 0.45 / Option B sub-class split)
- [ ] **4th `medium-backend 0.80` data point** logged in Q4 calibration table
  - DoD: Cumulative 4-pt mean + decision (KEEP / propose lift)

### 2.3 Sprint-workflow.md updates
- [ ] Add file MHist entry (1-line)
- [ ] Add matrix MHist entry (longer)
- [ ] Add §Active Activation history entry with Sprint 57.48 2nd validation results
- [ ] If 2nd consec < 0.7 → tighten `agent_factor` value in formula block (0.65 → 0.55 OR 0.45)
- [ ] If sub-class split decision → add NEW sub-class rows to matrix (parallel to Sprint 57.38 precedent)

### 2.4 Memory + index
- [ ] Write `memory/project_phase57_48_*.md`
- [ ] Add MEMORY.md pointer entry

### 2.5 CLAUDE.md
- [ ] Update Current Sprint row + Last Updated footer (navigator-only per Sprint Closeout policy)

### 2.6 PR + merge
- [ ] Push branch + open PR
- [ ] Wait CI green
- [ ] User merges (per session convention)
- [ ] Local cleanup

### 2.7 Final
- [ ] Day 2 commit: `chore(sprint-57-48): Day 2 retro + closeout`
- [ ] All checklist items `[x]` or 🚧

---

**Modification History**:
- 2026-05-26: Sprint 57.48 Day 0.1 — Initial draft (5-track wave; mirrors Sprint 57.46/57 structure)
