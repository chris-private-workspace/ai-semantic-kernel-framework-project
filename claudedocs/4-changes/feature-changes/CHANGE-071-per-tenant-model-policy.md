# CHANGE-071: Per-tenant model policy (C1 — config tiering)

**Date**: 2026-06-11
**Sprint**: 57.104 (C1 — harness-deepening Workflow C slice C1)
**Scope**: 範疇 4 (model selection) × adapters × platform_layer (config tiering) × api/v1/admin × Frontend (tenant-settings)
**Status**: ✅ Completed (drive-through PASS)

## Change Summary

Make Sprint 57.97's env-only `ModelProfile{action, cheap}` **tenant-governable**: a platform admin sets a per-tenant `{action, cheap}` model policy (Azure deployment + canonical model name) via an admin-gated, pricing-validated write-side; the policy persists in `tenant.meta_data["model_policy"]` (JSONB), is resolved per-request (TTL-cached, PUT-invalidated) inside `build_real_llm_handler`, and is built into that request's `ModelProfile`. The admin write/read is UI-drivable via a new "Model Policy" tab in the tenant-settings operator IA.

## Change Reason

Before C1, model selection was system-wide + env-only (`AZURE_OPENAI_*` / `AZURE_OPENAI_CHEAP_*`): every tenant ran the same deployment, with no governance seam. C1 is the first config-tiering vertical (the template C3's per-tenant verification/HITL/guardrail policy follows). Governance invariant: a tenant must not route to a model the cost ledger can't price → the write-side validates each `*_model` against `config/llm_pricing.yml` (422 on unknown).

## Detailed Changes

**Backend (resolution chain)**
- `adapters/_base/model_policy.py` (NEW): neutral `ModelPolicy` value object (`{action,cheap}_{deployment,model}: str|None`; `from_dict`/`to_dict`/`is_empty`).
- `platform_layer/billing/model_policy.py` (NEW): `resolve_tenant_model_policy(db, tenant_id)` reading `meta_data["model_policy"]` behind a `_ModelPolicyCache` (~60s TTL, injectable clock — D7) + `invalidate_tenant_model_policy` + `reset_model_policy_cache`. Mirrors `resolve_session_persona` (async-resolve-before-build, fail-open).
- `adapters/azure_openai/profile.py`: `build_azure_model_profile(policy=None)` builds action + cheap from policy ∪ env (`_azure_config` conditional-kwargs — D3: never pass None to BaseSettings); all-None byte-identical to 57.97.
- `api/v1/chat/handler.py` + `router.py`: the router resolves the policy BEFORE `build_handler` (mirrors `resolve_session_persona`); `model_policy` threads through `build_handler` → `build_real_llm_handler` → `build_azure_model_profile`; `chat_client = profile.action`. `loop.py` untouched; cost_ledger sub_type flows from `event.model` (D6, no router wiring).
- `api/v1/admin/tenants.py`: `PUT`/`GET /{tenant_id}/model-policy` (`extra="forbid"` + pricing-validated 422 + meta_data JSONB identity-swap + `append_audit(tenant_model_policy_upsert)` + composite-replace + cache invalidate). Mirrors the `PUT /quotas` 57.56 pattern.

**Frontend (operator tab)**
- `tenant-settings/components/tabs/ModelPolicyTab.tsx` (NEW) + `useModelPolicy`/`useModelPolicySave` hooks + `tenantSettingsService` `getModelPolicy`/`putModelPolicy` (snake↔camel + composite-replace blank-drop + 422-detail surfacing) + `TenantSettingsView` 7th tab registration. View (null→"System default") + edit + inline 422 banner; no dead controls; mirrors `QuotasTab` (operator-portal style authority).

## Verification

- Backend unit (27): value-object 8 + resolver/cache 11 + builder 8 (converted to the policy signature). Integration (13): PUT auth/404/persist/composite-replace/clear/extra-forbid/422-unpriced/200-priced/isolation/audit + GET 404/empty/reflects-PUT.
- Frontend Vitest (full suite 809): `ModelPolicyTab` view/edit/Save/422 + service mapping + tab registration.
- Gate: mypy `src` 0/357 · flake8 clean · `run_all` 10/10 (event count unchanged) · `check_llm_sdk_leak` 0 · `check_cross_category_import` green · FE lint 0 · build 0 · `check:mockup-fidelity` 53.
- **Drive-through PASS** (real UI + real Azure, Playwright): `acme-prod` policy nano → chat action turn `azure_openai_gpt-5.4-nano`; change to mini (cache invalidated) → chat action turn `azure_openai_gpt-5.4-mini`; 422 unpriced inline; clear→default. See `sprint-57-104/progress.md` Day 3 + `artifacts/dt57104-*.png`.

## Impact

- Backend (adapters + platform_layer + api) + Frontend (tenant-settings tab). No DB migration (JSONB on existing `tenants.metadata`). No new wire event. `loop.py` diff 0.
- **Open invariant (`AD-RBAC-DB-To-JWT-Wiring-Phase58`)**: the admin endpoint gates on `require_admin_platform_role` (JWT roles). In dev (dev-login carries `platform_admin`) it is fully drivable; in production-OIDC a real admin's JWT carries `roles=["user"]` (`auth.py:302` hardcode) → 403. This is a PRE-EXISTING, SHARED gap (already affects the 57.55-57.57 admin PUTs), NOT introduced by C1; tracked separately. C1 does not make it worse.
- Eventual-consistency window: the TTL cache means a policy change without the PUT-invalidate would take ≤60s; the PUT invalidates so the change is instant on the next request (drive-through-proven).
