# Sprint 57.49 — Frontend → Backend Real-Data Migration Wave (TenantSettings 5 tabs + AdminTenants Members)

**Phase**: 57+ Frontend SaaS / Phase 58+ Backend Schema Extension (frontend consumption closure)
**Goal**: Migrate frontend pages from `_fixtures.ts` to real backend endpoints shipped Sprint 57.46/47/48 — 5 TenantSettings tabs (General/FF/Quotas+RateLimits/HITL/Members) + AdminTenants Members tab/drawer.
**Branch**: `feature/sprint-57-49-frontend-backend-migration-wave`
**Class**: `medium-frontend` 0.65 (multi-track frontend migration; pattern reuse from existing `tenantSettingsService` infrastructure)
**Sub-class**: `mechanical-single-domain` (high pattern-reuse + frontend service migration; same-domain frontend) → **`agent_factor = 0.45`** (NEW sub-class table from Sprint 57.48 retro — **1st validation**)
**Date**: 2026-05-26 (Sprint 57.48 closeout day)
**Prior sprint reference**: Sprint 57.48 (5 backend endpoints) + Sprint 57.47 (MEMBERS endpoint) + Sprint 57.46 (Tenant ORM extension) + Sprint 57.44 (frontend /tenant-settings 6-tab rebuild fixture source)

---

## 1. Sprint Goal

```
AS a frontend engineer closing Phase 58+ Real-Data Migration wave
I WANT 5 TenantSettings tabs (General/FeatureFlags/Quotas+RateLimits/HITL/Members) switched
   from `_fixtures.ts` to real backend service hooks (consuming Sprint 57.46-57.48
   endpoints) PLUS AdminTenants Members tab/drawer added to expose Sprint 57.47 MEMBERS
   endpoint as user-visible feature
SO THAT /tenant-settings 6-tab page displays real tenant configuration data per page
   load (no more fixture defaults visible to platform admins), AND /admin-tenants page
   exposes per-tenant member list, AND we generate the 1st validation data point under
   the NEW `mechanical-single-domain` 0.45 sub-class agent_factor (Sprint 57.48 retro
   Option B structural split).
```

## 2. Background & Context

### 2.1 Track A — TenantSettings 5-Tab Migration

Per Sprint 57.44 frontend rebuild:
- 6 tab components exist in `frontend/src/features/tenant-settings/`
- All consume `_fixtures.ts` (GENERAL/IDENTITY/SEATS + FEATURE_FLAGS 8 + QUOTAS 5 + RATE_LIMITS 3 + HITL_POLICIES 4 + MEMBERS 8 + DANGER_OPS 4)

Backend now exists for 5 sections (DANGER_OPS is N/A UI-only):

| Tab | Fixture sections | Backend endpoint | Sprint shipped |
|---|---|---|---|
| GeneralTab | GENERAL + IDENTITY + SEATS | GET `/admin/tenants/{tenant_id}` (region/locale/retention_days/sso_enabled/seats fields) | 57.46 Track B |
| FeatureFlagsTab | FEATURE_FLAGS (8) | GET `/admin/tenants/{tenant_id}/feature-flags` | 57.48 Track B |
| QuotasTab (combined) | QUOTAS (5) + RATE_LIMITS (3) | GET `/admin/tenants/{tenant_id}/quotas` + `/rate-limits` | 57.48 Track C + D |
| HITLPoliciesTab | HITL_POLICIES (4) | GET `/admin/tenants/{tenant_id}/hitl-policies` | 57.48 Track A |
| MembersTab | MEMBERS (8) | GET `/admin/tenants/{tenant_id}/members` | 57.47 Track B |
| DangerZoneTab | DANGER_OPS (4 UI actions) | N/A — existing action endpoints | n/a |

### 2.2 Track B — AdminTenants Members Tab/Drawer

Sprint 57.47 backend added GET `/admin/tenants/{tenant_id}/members` but no frontend exposure yet. Frontend /admin-tenants page currently only shows tenant LIST view; users cannot drill down into members per tenant from the LIST page.

Sprint 57.49 adds a Members drawer/modal triggered from tenant row click — shows the paginated members list inline with the LIST page.

### 2.3 1st validation under NEW sub-class `mechanical-single-domain` 0.45

Per Sprint 57.48 retro Q4 Option B activation:
- Sprint 57.49 = 1st validation under NEW sub-class table
- Both tracks are `mechanical-single-domain` work shape (high pattern-reuse via existing `tenantSettingsService` / TanStack Query hook patterns; single frontend domain — no context-switching like Sprint 57.46 was)
- If Sprint 57.49 ratio lands in [0.85, 1.20] band → validates new sub-class table
- If ratio < 0.7 OR > 1.20 → tier 2 refinement evidence

---

## 3. User Stories

### US-1: TenantSettings 5-Tab Migration (Track A primary)

```
AS a platform admin viewing /tenant-settings for tenant X
I WANT each of 5 tabs (General/FF/Quotas+RateLimits/HITL/Members) to display REAL
   tenant data fetched from backend (not _fixtures.ts defaults)
SO THAT I can trust the page reflects actual tenant configuration; changes I make
   via PATCH (Sprint 57.44 EditForm — already real backed) round-trip correctly.
```

**Acceptance**:
- 5 NEW TanStack Query hooks (or extend existing `tenantSettingsService` patterns): `useFeatureFlags(tenant_id)`, `useQuotas(tenant_id)`, `useRateLimits(tenant_id)`, `useHITLPolicies(tenant_id)`, `useMembers(tenant_id)`
- 5 NEW service functions in `tenantSettingsService.ts` calling endpoints
- 5 tab components updated: remove `_fixtures.ts` imports for these sections; consume hook data instead
- Loading/error states per tab (mirror Sprint 57.44 patterns)
- GeneralTab already mostly consumes real data (Sprint 57.46 backend) — verify + remove any residual fixture fallbacks
- ≥10 NEW Vitest tests covering hook calls + loading/error/success states + tab render with real data
- Playwright e2e: /tenant-settings page loads each tab without fixture defaults visible
- `_fixtures.ts` retains DANGER_OPS only (N/A backend); other 5 sections removed OR kept for Storybook only with explicit comment

### US-2: AdminTenants Members Drawer/Tab (Track B)

```
AS a platform admin viewing /admin-tenants LIST page
I WANT to click on a tenant row to open a Members drawer showing the paginated list
   of members for that tenant (using Sprint 57.47 endpoint)
SO THAT I can quickly audit who has access to each tenant without navigating to a
   separate page; pagination handled inline.
```

**Acceptance**:
- NEW `TenantMembersDrawer` (or modal) component
- Click handler on TenantsTable rows opens drawer with selected tenant_id
- Service hook `useTenantMembers(tenant_id)` calling Sprint 57.47 endpoint
- Pagination controls (next/prev) wired to backend `limit`/`offset` params
- Empty state + loading + error states
- ≥4 NEW Vitest tests
- Playwright e2e: click tenant row → drawer opens → members visible
- Multi-tenant visual verification: tenant_a admin sees only tenant_a members (backend already enforces; verify UI follows)

### US-3: Validation + Documentation

```
AS the parent AI assistant maintaining Sprint workflow discipline
I WANT clean validation sweep + retro + memory + per-track CHANGE records + sprint-workflow
   1st validation entry under new sub-class table
SO THAT Sprint 57.50+ has data to confirm/deny the new sub-class agent_factor 0.45.
```

**Acceptance**:
- Standard validation chain: ESLint + tsc + Vitest + Playwright + Vite build + V2 lints (preserve 9/9 GREEN)
- 6 CHANGE records (CHANGE-018 to CHANGE-023; one per tab + AdminTenants drawer)
- retrospective.md Q1-Q7 with **1st validation under `mechanical-single-domain` 0.45 ratio + decision** + **`medium-frontend` 0.65 2nd-or-3rd data point trend assessment**
- sprint-workflow.md updates (MHist + matrix MHist + Activation history)
- memory/project_phase57_49_*.md subfile
- MEMORY.md pointer
- CLAUDE.md Current Sprint row + Last Updated footer (navigator-only)

---

## 4. Technical Specification

### 4.1 Pattern reuse from Sprint 57.44 + existing tenantSettingsService

Sprint 57.44 frontend rebuild used patterns:
- `tenantSettingsService` (already exists)
- TanStack Query hooks (already exists for some sections)
- Loading/Error/Empty state components (already exists)

Sprint 57.49 reuses these patterns mechanically — no new infrastructure; only NEW hooks + service functions + tab integration.

### 4.2 Per-Tab Migration Steps (mechanical pattern for each of 5 tabs)

For each Tab X:
1. Add `useX(tenant_id)` TanStack Query hook
2. Add `fetchX(tenant_id, limit, offset)` service function in `tenantSettingsService.ts`
3. Update `XTab.tsx`:
   - Remove `import { X_FIXTURE } from '../_fixtures'`
   - Add hook call: `const { data, isLoading, error } = useX(tenantId)`
   - Replace fixture data references with hook data
   - Add loading skeleton + error state (reuse existing patterns)
4. Update existing Vitest spec OR add NEW spec
5. Verify Playwright e2e doesn't break (re-run sprint test)

### 4.3 Track B — AdminTenants Members Drawer

```typescript
// New component frontend/src/features/admin-tenants/components/TenantMembersDrawer.tsx
// Trigger: TenantsTable row click → setSelectedTenantId(id) → open drawer
// Drawer fetches members via useTenantMembers hook
// Pagination controls embedded in drawer footer
```

Modify `TenantsTable.tsx` to expose row click handler.

### 4.4 No backend changes expected

Sprint 57.49 is pure frontend migration. No new Alembic migrations; no backend code changes. If any backend gap discovered (e.g. missing pagination on existing endpoint), STOP and add new Day 0.8 finding D-DAY0-N + assess scope.

---

## 5. File Change List

### Modified (TenantSettings — Track A)
- `frontend/src/features/tenant-settings/_fixtures.ts` (remove 5 sections; keep DANGER_OPS only with comment)
- `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` (5 NEW service functions; or split into per-resource service files)
- `frontend/src/features/tenant-settings/hooks/use*.ts` (5 NEW TanStack Query hooks)
- `frontend/src/features/tenant-settings/components/GeneralTab.tsx` (verify real backend consumption; remove any residual fixture refs)
- `frontend/src/features/tenant-settings/components/FeatureFlagsTab.tsx` (fixture → hook)
- `frontend/src/features/tenant-settings/components/QuotasTab.tsx` (combined Quotas + RateLimits; 2 hooks consumed)
- `frontend/src/features/tenant-settings/components/HITLPoliciesTab.tsx` (fixture → hook)
- `frontend/src/features/tenant-settings/components/MembersTab.tsx` (fixture → hook)
- 5 Vitest spec files updated

### New (AdminTenants — Track B)
- `frontend/src/features/admin-tenants/components/TenantMembersDrawer.tsx`
- `frontend/src/features/admin-tenants/hooks/useTenantMembers.ts`
- `frontend/src/features/admin-tenants/services/adminTenantsService.ts` extension (add `fetchTenantMembers`)
- `frontend/src/features/admin-tenants/components/TenantsTable.tsx` (add row click handler)
- NEW Vitest spec for drawer + hook
- Playwright e2e update for tenant member drill-down

### Documentation
- `claudedocs/4-changes/feature-changes/CHANGE-018-tenant-settings-general-frontend-migration.md`
- `claudedocs/4-changes/feature-changes/CHANGE-019-tenant-settings-feature-flags-frontend-migration.md`
- `claudedocs/4-changes/feature-changes/CHANGE-020-tenant-settings-quotas-ratelimits-frontend-migration.md`
- `claudedocs/4-changes/feature-changes/CHANGE-021-tenant-settings-hitl-policies-frontend-migration.md`
- `claudedocs/4-changes/feature-changes/CHANGE-022-tenant-settings-members-frontend-migration.md`
- `claudedocs/4-changes/feature-changes/CHANGE-023-admin-tenants-members-drawer.md`

---

## 6. Workload

**Bottom-up est**: ~12 hr (mid of user 9-14 range)
- Track A 5 tabs migration: ~7 hr (1.4 hr per tab average; pattern reuse-heavy)
- Track B AdminTenants Members drawer: ~3 hr
- Day 0 三-prong: 0.5 hr
- Day 2 closeout: 1 hr
- Validation sweep: 0.5 hr

**Class-calibrated commit** (`medium-frontend` 0.65):
- 12 × 0.65 = **~7.8 hr committed**

**Agent-adjusted commit** (`agent_factor = 0.45` NEW `mechanical-single-domain` sub-class):
- 7.8 × 0.45 = **~3.5 hr agent-adjusted**

**4-segment form**:
> Bottom-up est ~12 hr → class-calibrated commit ~7.8 hr (mult 0.65) → agent-adjusted commit ~3.5 hr (`agent_factor` 0.45 NEW sub-class `mechanical-single-domain`)

**1st validation prediction**:
- If sub-class table calibrated correctly → ratio ~0.85-1.20 (actual ~3-4.2 hr)
- If observed speedup ~11× (Sprint 57.48 pattern-reuse-heavy precedent) → actual ~1.1 hr → ratio ~0.31 → below band; tier 2 sub-class refinement evidence
- If observed speedup ~5-7× (Sprint 57.47 single-domain precedent) → actual ~1.7-2.4 hr → ratio ~0.49-0.69 → still below band but less so
- Mid-prediction: actual ~2-3 hr → ratio ~0.57-0.86 → lower edge of band

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | 5 NEW TanStack Query hooks shipped | grep `useFeatureFlags\|useQuotas\|useRateLimits\|useHITLPolicies\|useMembers` |
| AC-2 | 5 TenantSettings tabs consume real backend (no fixture imports for these sections) | grep `_fixtures` in 5 tab .tsx files → 0 matches |
| AC-3 | `_fixtures.ts` retains DANGER_OPS only | grep visible sections in `_fixtures.ts` |
| AC-4 | TenantMembersDrawer component shipped + wired to TenantsTable | grep TenantMembersDrawer + row click handler |
| AC-5 | ≥14 NEW Vitest tests (10 Track A + 4 Track B) | Vitest count delta |
| AC-6 | Playwright e2e passing (tenant-settings + admin-tenants) | npm run test:e2e (if available) |
| AC-7 | ESLint + tsc clean | exit 0 |
| AC-8 | Vite build successful (size delta ±5 KB acceptable for added components) | npm run build |
| AC-9 | 9 V2 lints preserved (9/9 from Sprint 57.48) | run_all.py exit 0 |
| AC-10 | 6 CHANGE records | ls dir |
| AC-11 | Day 0 三-prong report logged | Read progress.md |
| AC-12 | All loading/error/empty states verified per tab + drawer | manual verify or Vitest |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Existing GeneralTab still uses _fixtures.ts as fallback | Medium | Day 0.8 Prong 2 read GeneralTab.tsx full content; if residual fixture fallbacks → remove |
| Sprint 57.48 endpoints don't return all fields frontend expects | Medium | Day 0.8 Prong 2 cross-check Pydantic models (HITLPolicyItem/FeatureFlagItem/QuotaItem/RateLimitItem/TenantMemberItem) vs frontend tab fixture shapes |
| MembersTab + AdminTenants Members drawer have duplicate logic | Low-Medium | Refactor to shared `useTenantMembers` hook (Track A + Track B can reuse) |
| Drawer/modal pattern not yet established in admin-tenants | Medium | Day 0.8 Prong 2 read TenantsTable.tsx + AdminTenantsView.tsx; if no drawer pattern → use existing modal patterns from Sprint 57.40-44 frontend rebuild |
| TanStack Query hook ordering issue (mounting drawer + simultaneous main fetch) | Low | Standard `enabled` flag pattern (only fetch when selectedTenantId set) |
| Playwright e2e drift if test selectors rely on fixture data | Medium | Day 0.8 Prong 2 read e2e specs to confirm |
| **1st validation under NEW sub-class 0.45 lands < 0.7** | High (predicted) | Tier 2 sub-class refinement evidence; not actionable single-data-point; flag Sprint 57.50+ for 2nd validation |
| **1st validation lands > 1.20** | Low | Would suggest 0.45 too aggressive for frontend `mechanical-single-domain`; tier 2 split (frontend vs backend mechanical) |

---

## 9. Carryover ADs (for Sprint 57.50+ pickup)

- `AD-AgentFactor-Sub-Class-Validation-Sprint-57.50` (2nd data point under new sub-class)
- `AD-medium-frontend-Baseline-Recalibration` (Sprint 57.13 baseline + Sprint 57.49 = 2nd data point)
- `AD-Lint-Detector-Code-Aware-Masking-Rule` (Sprint 57.48 carryover — `.claude/rules/` codification)
- `AD-MockupCapture-Frontend-Visual-Diff-Pipeline` (Phase 58+ deferred)
- Potential NEW from Sprint 57.49 Day 0.8

---

**Modification History**:
- 2026-05-26: Sprint 57.49 Day 0.1 — Initial draft (dual-track frontend migration wave; 1st validation of NEW `mechanical-single-domain` 0.45 sub-class from Sprint 57.48 Option B activation)
