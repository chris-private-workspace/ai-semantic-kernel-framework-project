# Sprint 57.49 — Checklist

[Plan](./sprint-57-49-plan.md) — Dual-track frontend migration wave (TenantSettings 5 tabs + AdminTenants Members drawer); **1st validation under NEW `mechanical-single-domain` 0.45 sub-class agent_factor** (Sprint 57.48 retro Option B).

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] Plan written `sprint-57-49-plan.md`
- [x] Checklist written (this file)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

**Prong 1 — Path Verify** (10 paths):
- [ ] `frontend/src/features/tenant-settings/` directory exists with 6 tab components
- [ ] `frontend/src/features/tenant-settings/_fixtures.ts` exists (current fixture source)
- [ ] `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` exists (or similar service module)
- [ ] `frontend/src/features/admin-tenants/components/TenantsTable.tsx` exists (Track B integration target)
- [ ] `frontend/src/features/admin-tenants/services/adminTenantsService.ts` exists
- [ ] `backend/src/api/v1/admin/tenants.py` 5 endpoints from Sprint 57.47/48 exist (HITLPolicies + FF + Quotas + RateLimits + Members)
- [ ] Existing Vitest spec files for tenant-settings tabs exist
- [ ] Existing Playwright e2e specs for /tenant-settings + /admin-tenants exist
- [ ] No existing TenantMembersDrawer component (target NEW for Track B)
- [ ] AppShellV2 + drawer/modal pattern reference component exists somewhere in `frontend/src/`

**Prong 2 — Content Verify** (8 claims):
- [ ] Sprint 57.48 5 endpoints Pydantic response shapes (FeatureFlagItem/QuotaItem/RateLimitItem/HITLPolicyItem/TenantMemberItem) — match frontend fixture shapes
- [ ] Current `tenantSettingsService.ts` has existing service function patterns to mirror
- [ ] Existing TanStack Query hooks in tenant-settings/hooks/ to extend
- [ ] Current GeneralTab.tsx — does it consume real backend (Sprint 57.46) OR still fixture? (CRITICAL — different work scope)
- [ ] Current FeatureFlagsTab/QuotasTab/HITLPoliciesTab/MembersTab — all consume `_fixtures.ts`?
- [ ] DangerZoneTab is UI-only (no data fetching) — confirm
- [ ] Existing AdminTenants modal/drawer pattern OR need to introduce one
- [ ] Loading/Error/Empty state component patterns reusable

**Prong 3 — Schema Verify** (N/A — no DB changes)

**Prong 2.5 — Frontend Tree Depth Audit** (MANDATORY for frontend page sprints):
- [ ] Read each of 6 TenantSettings tab components in full (depth-1 child component tree)
- [ ] Verify no Phase-2 verbatim-CSS or shadcn-utility token regressions during migration (cf. Sprint 57.39 D-DAY1-1 lesson)

**Drift findings catalog**:
- [ ] All findings logged to `progress.md` Day 0
- [ ] Go/no-go decision recorded

### 0.9 Branch + Day 0 commit
- [x] Branch `feature/sprint-57-49-frontend-backend-migration-wave` created
- [ ] Day 0 + Day 1 combined commit (small-scope precedent)

---

## Day 1 — Implementation (Code-Implementer Agent Delegation)

### 1.1 Track A — TenantSettings 5-Tab Migration

#### 1.1.1 GeneralTab verify + cleanup (Sprint 57.46 backend already real)
- [ ] Verify GeneralTab.tsx consumes Sprint 57.46 TenantResponse 12 fields
- [ ] Remove any residual `_fixtures.ts` imports (GENERAL/IDENTITY/SEATS sections)
- [ ] Add Vitest spec assertions for real backend consumption

#### 1.1.2 FeatureFlagsTab migration (Sprint 57.48 Track B endpoint)
- [ ] NEW service function `fetchFeatureFlags(tenant_id)`
- [ ] NEW hook `useFeatureFlags(tenant_id)`
- [ ] Update FeatureFlagsTab.tsx — fixture → hook
- [ ] Update Vitest spec
- [ ] CHANGE-019 record

#### 1.1.3 QuotasTab migration (combined Quotas + RateLimits — Sprint 57.48 Track C + D)
- [ ] NEW service functions `fetchQuotas` + `fetchRateLimits`
- [ ] NEW hooks `useQuotas` + `useRateLimits`
- [ ] Update QuotasTab.tsx (both sections)
- [ ] Vitest spec
- [ ] CHANGE-020 record

#### 1.1.4 HITLPoliciesTab migration (Sprint 57.48 Track A endpoint)
- [ ] NEW service function `fetchHITLPolicies`
- [ ] NEW hook `useHITLPolicies`
- [ ] Update HITLPoliciesTab.tsx
- [ ] Vitest spec
- [ ] CHANGE-021 record

#### 1.1.5 MembersTab migration (Sprint 57.47 MEMBERS endpoint)
- [ ] NEW service function `fetchTenantMembers`
- [ ] NEW hook `useTenantMembers` (SHARED with Track B)
- [ ] Update MembersTab.tsx
- [ ] Vitest spec
- [ ] CHANGE-022 record

#### 1.1.6 _fixtures.ts cleanup
- [ ] Remove 5 migrated sections (GENERAL/IDENTITY/SEATS + FEATURE_FLAGS + QUOTAS + RATE_LIMITS + HITL_POLICIES + MEMBERS)
- [ ] Retain DANGER_OPS only with explicit comment "UI-only actions; no data fetch"
- [ ] CHANGE-018 record (General tab cleanup) covers this

### 1.2 Track B — AdminTenants Members Drawer

- [ ] NEW component `TenantMembersDrawer.tsx`
- [ ] Reuse `useTenantMembers` hook from Track A (SHARED)
- [ ] Modify `TenantsTable.tsx` — add row click handler → setSelectedTenantId
- [ ] Modify `AdminTenantsView.tsx` — mount drawer at view level
- [ ] Pagination controls in drawer footer
- [ ] Vitest spec for drawer + row click handler
- [ ] Playwright e2e update (click row → drawer opens → members visible)
- [ ] CHANGE-023 record

### 1.3 Day 1 Validation Sweep
- [ ] `cd frontend && npm run lint && npm run build` — exit 0; Vite bundle delta ±5 KB acceptable
- [ ] `cd frontend && npm run test` Vitest — all PASS; ≥14 NEW (10 Track A + 4 Track B)
- [ ] `cd frontend && npm run test:e2e` (if available locally) — tenant-settings + admin-tenants flows pass
- [ ] `python scripts/lint/run_all.py` — 9/9 GREEN (preserve Sprint 57.48 baseline)
- [ ] Manual smoke: open /tenant-settings + /admin-tenants in browser — verify no fixture defaults visible

### 1.4 Day 1 commit
- [ ] Commit: `feat(sprint-57-49): Day 1 frontend → backend migration wave (TenantSettings 5 tabs + AdminTenants Members)`

---

## Day 2 — Closeout

### 2.1 Validation
- [ ] Full frontend test suite passing
- [ ] No regressions in existing Vitest/Playwright

### 2.2 Retrospective
- [ ] Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-49/retrospective.md`
- [ ] **1st validation under `mechanical-single-domain` 0.45 sub-class** logged in Q4 (ratio + decision)
- [ ] **`medium-frontend` 0.65 data point** logged

### 2.3 Sprint-workflow.md updates
- [ ] File MHist entry
- [ ] Matrix MHist entry (`medium-frontend` 2nd data point + sub-class validation result)
- [ ] §Active Activation history entry (Sprint 57.49 1st validation of NEW sub-class table)

### 2.4 Memory + index
- [ ] `memory/project_phase57_49_*.md` subfile
- [ ] MEMORY.md pointer entry

### 2.5 CLAUDE.md
- [ ] Current Sprint row + Last Updated footer (navigator-only)

### 2.6 PR + merge
- [ ] Push branch + open PR
- [ ] Wait CI green
- [ ] User merges
- [ ] Local cleanup

### 2.7 Final
- [ ] Day 2 commit: `chore(sprint-57-49): Day 2 retro + closeout`
- [ ] All checklist `[x]` or 🚧

---

**Modification History**:
- 2026-05-26: Sprint 57.49 Day 0.1 — Initial draft (dual-track frontend migration wave; 1st validation NEW `mechanical-single-domain` 0.45 sub-class)
