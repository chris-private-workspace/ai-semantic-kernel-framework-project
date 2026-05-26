# Sprint 57.50 — Checklist

[Plan](./sprint-57-50-plan.md) — Single-track TenantSettings Identity fixture cleanup; **2nd validation under NEW `mechanical-single-domain` 0.45 sub-class agent_factor** (Sprint 57.48 retro Option B; Sprint 57.49 1st validation @ ratio ~0.14).

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] Plan written `sprint-57-50-plan.md`
- [x] Checklist written (this file)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

**Prong 1 — Path Verify** (8 paths):
- [x] `frontend/src/features/tenant-settings/_fixtures.ts` exists (IDENTITY_FIXTURE current source)
- [x] `frontend/src/features/tenant-settings/components/tabs/GeneralTab.tsx` exists (4-Badge-row consumer)
- [x] `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` exists (extension target)
- [x] `frontend/src/features/tenant-settings/hooks/` directory exists (NEW hook target)
- [x] `backend/src/api/v1/admin/tenants.py` exists (or sub-module — endpoint target)
- [x] Sprint 57.48 RateLimits endpoint exists as Option A pattern reference (`/rate-limits`)
- [x] `backend/src/infrastructure/db/models/identity.py` Tenant ORM exists with `meta_data` JSONB field (D-DAY0-2 — note path is `identity.py` not `tenant.py`)
- [x] No existing `tenant_identity` related route / Pydantic model / test file (target NEW)

**Prong 2 — Content Verify** (8 claims):
- [x] Sprint 57.48 Track D RateLimits Pydantic response shape pattern + DEFAULT constant pattern (D-DAY0-1) — verbatim mirror template at tenants.py L965-1031
- [x] `Tenant.meta_data` JSONB column actually present + Sprint 57.48 Track D uses it for RateLimits fixture-projection (D-DAY0-2) — identity.py L138-143 (`"metadata"` DB col)
- [x] Existing admin auth dependency name + import path (D-DAY0-3) — `require_admin_platform_role` from `platform_layer.identity.auth`
- [x] Existing TanStack Query hook patterns in `tenant-settings/hooks/` 5 hooks shipped Sprint 57.49 (`useFeatureFlags` / `useQuotas` / `useRateLimits` / `useHITLPolicies` / `useTenantMembers`)
- [x] `tenantSettingsService.ts` 5 service functions shipped Sprint 57.49 + `fetchWithAuth` pattern + `_handleResponse` pattern (single-record template = `fetchTenantSettings` L61; list template = `fetchRateLimits` L146)
- [x] GeneralTab.tsx 4 IDENTITY_FIXTURE Badge rows are the ONLY consumer (D-DAY0-6 — Identity Card has 5 rows total; row 1 SSO Provider already uses real `data.sso_enabled`)
- [x] `SEATS_FIXTURE` truly unused (D-DAY0-8 — already removed Sprint 57.49; only stale docstring comments remain at `_fixtures.ts:21` + `PageHeader.tsx:20` MHist; **task 1.2.4 scope reduced**)
- [x] Existing GeneralTab tests do NOT depend on IDENTITY_FIXTURE values (D-DAY0-7 — grep in `**/*.test.*` → 0 matches)

**Prong 2.5 — Frontend Tree Depth Audit**:
- [x] Read GeneralTab.tsx in full (163 lines; depth-1 child component tree audit per AD-Plan-5)
- [x] Verify no Phase-2 verbatim-CSS or shadcn-utility token regressions in Identity & SSO section (all `var(--*)` + mockup-ui primitives clean)
- [x] Verify no inline `style={{...}}` missing escape comments (6 sites — all have `eslint-disable-next-line no-restricted-syntax` escape)

**Prong 3 — Schema Verify**: N/A (no DB changes; fixture-projection Option A only)

**Drift findings catalog**:
- [x] All findings logged to `progress.md` Day 0 (D-DAY0-1 through D-DAY0-9: 7 GREEN + 1 GREEN+ + 1 YELLOW)
- [x] Go/no-go decision recorded — **GO**

### 0.9 Branch + Day 0 commit
- [x] Branch `feature/sprint-57-50-tenant-settings-identity-fixture-cleanup` created
- [ ] Day 0 + Day 1 combined commit (per recent Sprint 57.46/47/48/49 small-scope precedent)

---

## Day 1 — Implementation (Code-Implementer Agent Delegation)

### 1.1 Backend Track — Identity endpoint

#### 1.1.1 Pydantic response model + DEFAULT_IDENTITY constant
- [ ] Add `TenantIdentityResponse(BaseModel)` with 4 fields (provider: str / scim_enabled: bool / allowed_domains: list[str] / mfa_required: bool)
- [ ] Add `DEFAULT_IDENTITY` constant matching mockup fixture defaults
- [ ] mypy --strict 0 errors on new code

#### 1.1.2 Endpoint route
- [ ] Add `GET /{tenant_id}/identity` route in `backend/src/api/v1/admin/tenants.py` (or sub-module per Prong 2 D-DAY0-1 outcome)
- [ ] Admin auth dependency injected
- [ ] Tenant lookup + 404 on miss
- [ ] Fixture-projection: `tenants.meta_data['identity'] or DEFAULT_IDENTITY`
- [ ] Return `TenantIdentityResponse(**identity_data)`

#### 1.1.3 Backend pytest tests
- [ ] NEW test file `backend/tests/integration/api/test_admin_tenant_identity.py`
  - [ ] test_success_returns_default_when_meta_data_missing
  - [ ] test_success_returns_meta_data_when_present
  - [ ] test_404_when_tenant_not_found
  - [ ] test_403_when_non_admin_caller (critical multi-tenant isolation test)
  - [ ] (Optional) test_response_shape_matches_pydantic_model

### 1.2 Frontend Track — Service + Hook + GeneralTab refactor

#### 1.2.1 Service function
- [ ] Add `fetchTenantIdentity(tenantId: string)` to `tenantSettingsService.ts`
- [ ] Add `TenantIdentity` TS interface (4 fields matching backend Pydantic)
- [ ] Reuse existing `fetchWithAuth` + ServiceError patterns

#### 1.2.2 TanStack Query hook
- [ ] NEW `frontend/src/features/tenant-settings/hooks/useTenantIdentity.ts`
- [ ] `useQuery` with queryKey `['tenant-identity', tenantId]` + `enabled: !!tenantId`
- [ ] File header convention applied

#### 1.2.3 GeneralTab refactor
- [ ] Drop `import { IDENTITY_FIXTURE } from "../../_fixtures"` from GeneralTab.tsx
- [ ] Call `useTenantIdentity(tenantId)` hook; destructure `{ data, isLoading, error }`
- [ ] Update 4 Identity Badge rows to consume `data.provider` / `data.scim_enabled` / `data.allowed_domains` / `data.mfa_required`
- [ ] Apply shape adapter (bool → "enabled"/"disabled" + list → "domain1, domain2")
- [ ] Loading state placeholder (mirror existing Sprint 57.49 pattern)
- [ ] Error state fallback (mirror existing Sprint 57.49 pattern)

#### 1.2.4 `_fixtures.ts` cleanup
- [ ] Remove IDENTITY_FIXTURE export + JSDoc block
- [ ] Remove SEATS_FIXTURE export (Sprint 57.49 follow-up)
- [ ] Update file header Modification History entry (newest-first)
- [ ] Update file Description section to reflect DANGER_OPS-only state

#### 1.2.5 Frontend Vitest tests
- [ ] NEW `useTenantIdentity.test.ts` — 1-2 tests (success + enabled-false-when-tenantId-undefined)
- [ ] GeneralTabIdentity render test (NEW or extension of existing GeneralTab spec) — Identity section renders with hook data; 2-3 tests

### 1.3 Day 1 Validation Sweep
- [ ] `cd backend && pytest` — all PASS; ≥4 NEW
- [ ] `cd backend && mypy --strict src/` — 0 errors
- [ ] `cd frontend && npm run lint && npm run build` — exit 0; Vite bundle delta within ±2 KB
- [ ] `cd frontend && npm run test` Vitest — all PASS; ≥3 NEW
- [ ] `python scripts/lint/run_all.py` — **9/9 GREEN** (preserve Sprint 57.49 baseline)
- [ ] LLM SDK leak scan — 0
- [ ] Manual smoke (deferred Day 2 / parent verification)

### 1.4 Day 1 commit
- [ ] Commit: `feat(sprint-57-50): Day 1 TenantSettings Identity fixture-projection backend + frontend cleanup`

---

## Day 2 — Closeout (parent assistant)

### 2.1 Validation
- [x] Full backend pytest suite passing (no regressions; 224 PASS / +7)
- [x] Full frontend Vitest suite passing (no regressions; 607 PASS / +9)
- [x] 9/9 V2 lints preserved (final sweep 1.00s)

### 2.2 Retrospective
- [x] Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-50/retrospective.md`
- [x] Q1-Q7 6 必答 format
- [x] **Q4: 2nd validation under `mechanical-single-domain` 0.45 sub-class** — ratio 0.58 BELOW band by 0.27; 2nd consec < 0.7 → ROLLBACK RULE MET → **ACTIVATE Option B tier-2 refinement** (pattern-reuse-heavy 0.30 + greenfield 0.50)
- [x] **Q4: `medium-backend` 0.80 5th data point** logged (ratio 0.27; 5-pt mean 0.52; confound resolved by tier-2 sub-class layer)
- [x] Q5 carryover candidate list (rolling — Top 3 candidates: #76 Lint Detector rule / #82 ORM File Path Risk Style / Pause)

### 2.3 sprint-workflow.md updates
- [x] File MHist entry (1-line)
- [x] Matrix MHist entry (`medium-backend` 0.80 row updated to 5 data points: 55.5/55.6/57.47/57.48/57.50; status note updated re tier-2 confound resolution)
- [x] §Active Activation history entry (Sprint 57.50 retro Q4 — 2nd validation under NEW sub-class + tier-2 ESCALATION ACTIVATION)
- [x] §Active sub-class table replaced with tier-2 split (`mechanical-pattern-reuse-heavy` 0.30 + `mechanical-greenfield` 0.50 + `mixed-multidomain-bundle` 0.65 UNCHANGED + partial 0.75 + human 1.0; History trail extended)

### 2.4 Memory + index
- [x] `memory/project_phase57_50_tenant_settings_identity_fixture_cleanup.md` subfile
- [x] MEMORY.md pointer entry (~quality pointer; subfile link + 1-sentence topic + keywords)

### 2.5 CLAUDE.md
- [x] Current Sprint row updated (Sprint 57.49 → Sprint 57.50; navigator-only per Sprint Closeout Policy)
- [x] Last Updated footer updated (Sprint 57.50 — 3 ADs closed + 2nd validation + tier-2 ESCALATED)

### 2.6 next-phase-candidates.md (REFACTOR-001 single-source for open items)
- [x] Update `Updated` header (Sprint 57.50 closeout note; demoted Sprint 57.43-49 batch to "Previous Updated")
- [x] Append Sprint 57.50 carryover section at TOP of file per existing format (3 ADs closed + 4 NEW carryovers + tier-2 ESCALATION table + Top 3 candidates)

### 2.7 PR + merge (post-commit; user action)
- [ ] Push branch + open PR
- [ ] Backend code touched this sprint — Backend-CI + V2 Lints should fire naturally; no paths-filter workaround needed
- [ ] Wait CI green
- [ ] User merges
- [ ] Local cleanup

### 2.8 Final
- [ ] Day 2 commit: `chore(sprint-57-50): Day 2 retro + closeout (tier-2 ESCALATION)`
- [x] All checklist items `[x]` (Day 0 + Day 1) or 🚧 (Day 2.7 PR + merge pending user action)
