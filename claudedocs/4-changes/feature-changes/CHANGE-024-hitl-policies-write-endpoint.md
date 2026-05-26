# CHANGE-024: HITLPolicies Admin Write Endpoint + Frontend Edit Mode

**Date**: 2026-05-26
**Sprint**: 57.54
**Scope**: Cross-cutting — Cat 9 Guardrails (HITL Policy) + Platform layer (admin API) + Frontend (tenant-settings tab)
**Branch**: `feature/sprint-57-54-hitl-policies-full-persistence`
**Day 0+1 commit**: `f2f95b11`
**PR**: (pending; opens at Day 2.8)

## Problem

After Sprint 57.48 (admin GET endpoint) + Sprint 57.49 (frontend read-only tab migration), the HITLPolicies tab in tenant-settings was **read-only**:

- DBHITLPolicyStore had only `get(tenant_id) → HITLPolicy | None`; no `put/upsert/delete`
- Admin API only exposed `GET /admin/tenants/{tenant_id}/hitl-policies`
- Frontend tab displayed projected per-RiskLevel items but had no edit affordance
- `BackendGapBanner` copy on the tab explicitly stated "Off-platform channel routing + policy edit API: backend extension Phase 58+"

Admin operators could read effective per-tenant HITL policy state but could not configure overrides programmatically. Policy changes required direct DB writes.

## Root Cause

Sprint 55.3 (AD-Hitl-7) shipped the `hitl_policies` table + ORM + RLS + read-only `DBHITLPolicyStore.get()` first. The WRITE side was deliberately deferred as "Phase 58+ extension" pending product/UX clarification on policy edit UI requirements.

Sprint 57.48 + 57.49 extended the read path further (composite → list projection + frontend hook + tab UI) but kept the same Phase 58+ marker on writes — the table existed but had no admin write surface.

## Solution

**Backend Track A**:
1. NEW `DBHITLPolicyStore.put(tenant_id, policy) → HITLPolicy` async method using PostgreSQL `pg_insert.on_conflict_do_update` upsert pattern (with explicit `updated_at: func.now()` in `set_` clause for UPDATE path; `server_default` only fires on INSERT)
2. NEW Pydantic `HITLPolicyUpsertRequest` write schema (composite shape; `extra="forbid"` + `field_validator` on RiskLevel enum strings)
3. NEW `HITLPolicyUpsertResponse` (echoes both `saved_policy` composite + projected `items` list for cache hydration consistency with GET endpoint)
4. NEW `PUT /api/v1/admin/tenants/{tenant_id}/hitl-policies` endpoint using `Depends(require_admin_platform_role)` + `_load_tenant_or_404` + `_session_factory_from` + `_project_hitl_policy_to_items` reuse
5. `DBHITLPolicyStore.put()` defensive contract: ignores `policy.tenant_id` in favor of explicit `tenant_id` arg (prevents accidental cross-tenant writes)
6. Test conftest.py extension: `HITL_PUT_%` LIKE cleanup sweep in `_clear_committed_test_tenants()` (mirrors Sprint 57.12 + 57.53 `§Committed-Row Cleanup Pattern` at sibling scope; needed because `store.put()` commits via shared test session)
7. 12 NEW pytest integration tests covering: auth/404/upsert-create/upsert-update/projection/422 risk enum (2 fields)/422 extra field/multi-tenant isolation/idempotency/persistence verify/empty dicts

**Frontend Track B**:
1. NEW `HITLPolicyUpsertRequest` + `HITLPolicyUpsertResponse` TypeScript types
2. NEW `saveHITLPolicies(tenantId, payload, signal?)` service func using `fetchWithAuth` PUT (mirrors `updateTenantSettings` pattern)
3. NEW `useHITLPoliciesSave(tenantId)` TanStack mutation hook (mirror of `useTenantSettingsSave` Sprint 57.9 verbatim; `onSuccess` invalidates `[...HITL_POLICIES_QUERY_KEY_BASE, tenantId]`)
4. HITLPoliciesTab edit mode:
   - State: `editing: boolean` + `draft: HITLPolicyUpsertRequest | null`
   - `useEffect` reset both on tenantId change
   - Edit button populates draft from current items via reverse-projection (highest "auto" tier → `auto_approve_max_risk`; lowest "always_ask" → `require_approval_min_risk`; per-risk reviewer CSV → array; per-risk SLA number)
   - Edit form: 2 risk-threshold selects + 4 RiskLevel rows × (reviewer CSV input + SLA seconds input)
   - Save button: `saveMutation.mutate(draft)`; disabled while `isPending`; on success setEditing(false) + invalidation auto-refresh
   - Cancel button: reset draft + setEditing(false)
   - Error display: inline `var(--danger)` styled error message
5. `BackendGapBanner` copy softened:
   - From: "Off-platform channel routing + policy edit API: backend extension Phase 58+ — risk/policy/SLA shown are tenant-effective"
   - To: "Off-platform channel routing (Slack/email/SMS): Phase 58+ — risk/policy/SLA shown are tenant-effective + editable via Edit button"
6. 10 NEW Vitest tests: 3 hook tests + 2 service tests + 5 tab edit-mode tests (Edit-toggle / Cancel-reset / Save-call-mutation / Save-disabled-while-pending / Save-error-display + banner copy assertion update)

**Off-platform channel routing remains Phase 58+** per remaining BackendGapBanner copy (broader scope — Slack/email/SMS notification config; not in Sprint 57.54).

## Verification

### Backend
- `cd backend && pytest tests/integration/api/test_admin_tenant_hitl_policies.py -v` — all PASS (existing 18 + 12 NEW)
- `cd backend && pytest --tb=short -q` — **1772 PASS / 4 SKIP / 0 FAIL** (was baseline 1760; +12 NEW exact target)
- `cd backend && mypy --strict src/` — 0 errors / 310 source files
- `cd backend && black src/ tests/ && isort --profile black src/ tests/ && flake8 src/ tests/` — clean

### Frontend
- `cd frontend && npm run lint` (no `--silent`) — 0 ESLint errors (3 pre-existing jsx-ast-utils parser warnings unrelated)
- `cd frontend && npm run build` — tsc strict 0 errors + Vite build clean (3.36s)
- `cd frontend && npm run test` — **617 PASS / 0 FAIL** (was baseline 607; +10 NEW)

### V2 Architecture lints
- `python scripts/lint/run_all.py` — **9/9 GREEN** (0.98s)
- LLM SDK leak scan — 0
- HEX_OKLCH baseline 47 preserved (`check_ap4_frontend_placeholder.py` GREEN)
- AP-2 BackendGapBanner intact

## Impact

**Backend**:
- `backend/src/platform_layer/governance/hitl/policy_store.py` — +50 lines (NEW put method + imports)
- `backend/src/api/v1/admin/tenants.py` — +85 lines (NEW Pydantic + PUT endpoint + HITLPolicy import extension)
- `backend/tests/integration/api/test_admin_tenant_hitl_policies.py` — +320 lines (12 NEW tests + helpers)
- `backend/tests/integration/api/conftest.py` — +4 lines (HITL_PUT_% sweep)

**Frontend**:
- `frontend/src/features/tenant-settings/types.ts` — +18 lines (types)
- `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — +20 lines (saveHITLPolicies)
- `frontend/src/features/tenant-settings/hooks/useHITLPoliciesSave.ts` — NEW file (45 lines)
- `frontend/src/features/tenant-settings/components/tabs/HITLPoliciesTab.tsx` — full rewrite (+230 lines; edit mode)
- `frontend/tests/unit/tenant-settings/useHITLPoliciesSave.test.tsx` — NEW file (~70 lines, 3 tests)
- `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` — +48 lines (2 tests)
- `frontend/tests/unit/tenant-settings/tabs/HITLPoliciesTab.test.tsx` — +101 lines (5 NEW tests + banner update)

**Sprint artifacts**:
- Plan + Checklist + progress.md + retrospective.md + memory subfile + MEMORY.md pointer + sprint-workflow.md matrix update + CLAUDE.md update + next-phase-candidates.md update

**Total**: 14 files / +1933 / -18 (Day 0 + Day 1 combined commit `f2f95b11`)

## Lessons captured for future sprints

1. **Day 0 Prong 1 file-glob false-negative on `__tests__/` pattern**: actual repo convention is `frontend/tests/unit/<feature>/` mirror layout, not co-located `__tests__/`. Carryover `AD-Day0-Prong1-Test-Glob-Multi-Pattern` proposes multi-pattern test file glob codification in `.claude/rules/sprint-workflow.md §Step 2.5 Prong 1`.

2. **Phase 58.x WRITE-side pattern reusable template**: Sprint 57.54 = (backend) `pg_insert.on_conflict_do_update` + Pydantic write + PUT endpoint + 12 pytest; (frontend) mirror `useTenantSettingsSave` + service func PUT + edit mode tab + 10 Vitest. Same shape applies to FeatureFlags/Quotas/RateLimits WRITE-side. Carryover `AD-Phase58-Persistence-WriteSide-Pattern-Template` codifies this.

3. **`pg_insert.on_conflict_do_update` repo first usage** (D-DAY0-13 NOTABLE): pattern needs `set_["updated_at"] = func.now()` explicit because `server_default=func.now()` only fires on INSERT. Future devs hitting upsert should reference this pattern.

4. **Greenfield vs port speedup distinction**: pure mechanical port (Sprint 57.40-44) = ~5× speedup vs human; single greenfield NEW feature (Sprint 57.54) = ~2× speedup. Sub-class refinement candidate `mechanical-greenfield-port-style` (0.45) vs `mechanical-greenfield-design-decisions` (0.65) under conditional `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement` (defer to 2-3 data points).

5. **Sequential agent delegation works for backend → frontend type contract handoff**: agent reads backend Pydantic shape directly from admin/tenants.py + adapts TypeScript types. No drift detected across 2 sequential delegations.

## Related

- Sprint 57.48 (AD-TenantSettings-HITLPolicies-Backend; admin GET endpoint baseline)
- Sprint 57.49 (frontend HITLPoliciesTab fixture→hook migration)
- Sprint 55.3 / AD-Hitl-7 (table + ORM + RLS + read-only DBHITLPolicyStore.get baseline)
- Sprint 57.50 (Option A fixture-projection pattern precedent for single-record write endpoints)
- Sprint 57.52 retro Q4 (tier-3 SPLIT ACTIVATED; `mechanical-greenfield` 0.50 sub-class baseline opens; this sprint is 1st validation)
- Sprint 57.12 + 57.53 (`§Committed-Row Cleanup Pattern` precedents extended in Track A test infrastructure)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-54/retrospective.md` — full Q1-Q7 retrospective
- `memory/project_phase57_54_hitl_policies_write_endpoint.md` — subfile
