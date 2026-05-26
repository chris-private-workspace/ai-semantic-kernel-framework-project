# CHANGE-013: TenantSettings HITLPolicies Admin GET Backend

**Date**: 2026-05-26
**Sprint**: 57.48 (Track A)
**Scope**: API Layer / Admin (`backend/src/api/v1/admin/tenants.py`) + integration tests
**Closes**: `AD-TenantSettings-HITLPolicies-Backend` (carried since Sprint 57.44 audit)

## Problem
TenantSettings `HITLPoliciesTab` was wired to `_fixtures.ts HITL_POLICIES` (4-row fixture). Sprint 57.44 audit identified this as 1 of 5 fixture-only tabs needing real backend support. No admin GET endpoint exposed per-tenant HITL policy state — `DBHITLPolicyStore` exists since Sprint 55.3 / Alembic 0013 but only consumed internally by `DefaultHITLManager`.

## Root Cause
Sprint 53.4-55.3 wired `DBHITLPolicyStore` for runtime policy resolution but never surfaced it via an admin read endpoint. The composite `HITLPolicy` dataclass (`auto_approve_max_risk` + `require_approval_min_risk` + `reviewer_groups_by_risk` + `sla_seconds_by_risk`) is single-row-per-tenant; the mockup IA is per-risk-level (4 rows).

## Solution
- Add `HITLPolicyItem` + `HITLPolicyListResponse` Pydantic models to `tenants.py`
- Add `GET /admin/tenants/{tenant_id}/hitl-policies` endpoint with `require_admin_platform_role`
- Project single `HITLPolicy` composite row → list of 4 per-RiskLevel items via `_project_hitl_policy_to_items()` helper:
  - `policy` = "auto" if risk ≤ auto_approve_max_risk else "always_ask" if risk ≥ require_approval_min_risk else "ask_once"
  - `reviewers` = joined `reviewer_groups_by_risk[risk]`
  - `sla_seconds` = `sla_seconds_by_risk[risk]` (None when unset)
- When no per-tenant row exists → empty list (AP-2 honesty: frontend falls back to fixture)
- Multi-tenant isolation: `DBHITLPolicyStore.get(tenant_id)` filters by tenant_id

## Verification
- 7 NEW integration tests in `test_admin_tenant_hitl_policies.py` (auth + 404 + empty + happy + shape + isolation + pagination) — ALL PASS
- 9/9 V2 lints green
- mypy --strict clean on tenants.py
- Full integration/api suite: 217 PASS (Sprint 57.47 baseline 188 + 29 new from Sprint 57.48 = 217; 0 regressions)

## Impact
- **Backend-only** addition; no frontend change this sprint
- Frontend `HITLPoliciesTab` may swap from fixture → live data in Phase 58+ (separate PR)
- D-DAY0-2 drift handled via projection helper (avoids changing `DBHITLPolicyStore` ABC surface)

## File Touches
- `backend/src/api/v1/admin/tenants.py` — +4 imports, +HITLPolicyItem/HITLPolicyListResponse models, +_project_hitl_policy_to_items, +_session_factory_from, +list_tenant_hitl_policies endpoint (~120 lines net add)
- `backend/tests/integration/api/test_admin_tenant_hitl_policies.py` — NEW file (216 lines, 7 tests)
