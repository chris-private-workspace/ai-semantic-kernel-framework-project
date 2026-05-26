# Sprint 57.47 Progress

**Sprint goal**: Phase 58+ Backend Schema Extension wave — (Track A) admin-tenants LIST 5-col exposure + (Track B) TenantSettings 6-tab backend audit.
**Branch**: `feature/sprint-57-47-admin-tenants-list-schema-extension`
**Class**: `medium-backend` 0.80 ; `agent_factor = 0.65` 1st validation

---

## Day 0 — 三-Prong Verify + 6-Tab Audit (2026-05-26)

### §Prong 1 — Path Verify (6 paths)

| Path | Exists | Notes |
|------|--------|-------|
| `backend/src/api/v1/admin/tenants.py` | ✅ | Sprint 57.46 touched (MHist 2026-05-26) |
| `backend/src/infrastructure/db/models/identity.py` | ✅ | 5 new cols at L145-169 (Sprint 57.46) |
| `backend/tests/integration/api/test_admin_tenant_list.py` | ✅ | + `_get.py` `_patch.py` `_settings_extension.py` exist |
| `backend/src/agent_harness/.../quota.py` | ❌→✅ | Actual path `backend/src/platform_layer/tenant/quota.py` (D-DAY0-1) |
| `backend/src/agent_harness/hitl/` | ✅ | `_abc.py` HITLManager + HITLPolicyStore present |
| `frontend/src/features/tenant-settings/_fixtures.ts` | ✅ | 6 array exports + GENERAL/IDENTITY/SEATS fixtures (Sprint 57.44) |

### §Prong 2 — Content Verify (5 claims)

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Tenant ORM has 5 new cols (region/locale/retention_days/sso_enabled/seats) | ✅ confirmed | `identity.py` L145-169 — all 5 mapped_column NOT NULL with server_default |
| TenantListItem current 7 fields baseline | ✅ confirmed | `tenants.py` L165-181 — id/code/display_name/state/plan/created_at/updated_at |
| `from_attributes=True` on TenantListItem | ✅ confirmed | `tenants.py` L181 — `ConfigDict(from_attributes=True)` |
| Existing list endpoint filters (state/plan/search) | ✅ confirmed | `tenants.py` L216-222 — pattern: `if X is not None: base_stmt = base_stmt.where(...)` |
| TenantSettings _fixtures.ts 6 sections + 3 single fixtures | ✅ confirmed | `_fixtures.ts` L72-135 — FEATURE_FLAGS/QUOTAS/RATE_LIMITS/HITL_POLICIES/MEMBERS/DANGER_OPS + GENERAL_FIXTURE/IDENTITY_FIXTURE/SEATS_FIXTURE |

### §Prong 3 — Schema Verify

N/A for Track A (Pydantic-only extension on existing Tenant ORM; Sprint 57.46 Alembic 0018 already landed). Re-evaluated for Track B Day 1 stretch (MEMBERS): **NOT triggered** — existing `User` ORM in `identity.py` L187-225 already has `tenant_id` (via `TenantScopedMixin`) + `email` + `display_name` + `status` + `created_at`. No new table/migration needed; only a read-only GET endpoint.

### §Prong 2.5 — Frontend Tree Depth Audit

N/A — pure backend sprint; no frontend page re-point.

### §Drift findings

- **D-DAY0-1** — Plan §0.8 Prong 1 referenced `backend/src/agent_harness/.../quota.py`; actual location is `backend/src/platform_layer/tenant/quota.py`. **Implication**: plan path was an outdated assumption; QUOTAS tab backend reference resolved correctly via `Glob backend/src/**/quota*.py`. No scope shift.
- **D-DAY0-2** — Plan §0.8 Prong 1 referenced `backend/src/agent_harness/hitl/`; directory exists ✅ but contains only ABCs (`_abc.py` HITLPolicyStore + HITLManager). **Implication**: ABC layer present; concrete `DBHITLPolicyStore` impl mentioned in `_abc.py` MHist as Sprint 55.3 deliverable — needs further grep to confirm scope of admin endpoint work. Carryover: minor; audit table below records "real ABC + impl, admin endpoint missing".
- **D-DAY0-3** — Plan §0.8 Prong 1 referenced `backend/src/**/rate_limit*.py`; **0 results**. **Implication**: RATE_LIMITS tab is fixture-only with NO backend module; scope ~4-6 hr (new table + service + endpoint). Carryover: `AD-TenantSettings-RateLimits-Backend` Phase 58+.

### §TenantSettings backend audit (Day 0.8b)

| Tab | Verdict | Backend file ref | Phase 58+ scope est | Notes |
|---|---|---|---|---|
| **FEATURE_FLAGS** | partial (real ORM, no admin GET endpoint) | `backend/src/infrastructure/db/models/feature_flag.py` (global registry + `tenant_overrides` JSONB) + `backend/src/core/feature_flags.py` | ~3-4 hr (new admin endpoint + Pydantic + tests) | Multi-tenant rule violates (global table with `tenant_overrides` JSONB pattern — DOC L8-14 explicitly notes "Multi-tenant rule §Rule 1: business tables MUST have tenant_id" — exception via override pattern); admin endpoint expose `{flag_key: {def, on_for_tenant}}` shape |
| **QUOTAS** | partial (Redis-only QuotaEnforcer, single-dimension) | `backend/src/platform_layer/tenant/quota.py` (D-DAY0-1 correction) | ~3-5 hr (extend to multi-dim Tokens/Runs/Subagents/Memory/Audit + per-tenant config table) | Current `QuotaEnforcer` only enforces `quota:tokens:{tenant_id}:{YYYY-MM-DD}`; fixture shows 5 dimensions (Tokens / Runs / Subagents / Memory / Audit); needs new `tenant_quotas` table + admin GET endpoint |
| **RATE_LIMITS** | fixture-only | NO backend module (D-DAY0-3) | ~4-6 hr (new table + service + admin endpoint) | API requests / Tool calls / SSE connections — likely needs Redis token-bucket layer + per-tenant `tenant_rate_limits` config table |
| **HITL_POLICIES** | partial (real ABC + DBHITLPolicyStore impl, no admin GET endpoint) | `backend/src/agent_harness/hitl/_abc.py` HITLPolicyStore | ~2-3 hr (new admin endpoint + DTO shape match fixture) | Concrete `DBHITLPolicyStore` exists (Sprint 55.3 AD-Hitl-7); admin endpoint should query by `tenant_id` and project to `{risk, policy, sla, approvers, off[]}` shape |
| **MEMBERS** | partial (real User ORM with full needed fields, no admin GET-by-tenant endpoint) | `backend/src/infrastructure/db/models/identity.py` L187-225 User ORM | **~1.5-2 hr** ← CHEAPEST | User has `tenant_id` (via TenantScopedMixin) + `email` + `display_name` + `status` + `created_at`; need only GET endpoint + Pydantic schema + tests; **NO new table/migration** |
| **DANGER_OPS** | N/A (UI actions, not data) | N/A | N/A | Suspend / Rotate API keys / Tombstone PII / Delete — these are admin actions; existing tenant lifecycle endpoints (POST suspend/archive in Sprint 56.1) partially cover |

### §Track B Day 1 decision

**Cheapest fixture-only/partial tab**: **MEMBERS** at ~1.5-2 hr (estimate within ≤ 2 hr threshold).

Per checklist §0.8b decision rule: **PROCEED with Track B Day 1 stretch on MEMBERS** — implement `GET /admin/tenants/{tenant_id}/members` read-only endpoint.

Carryover ADs (for non-MEMBERS tabs deferred):
- `AD-TenantSettings-FeatureFlags-Backend` Phase 58+ (~3-4 hr)
- `AD-TenantSettings-Quotas-Backend` Phase 58+ (~3-5 hr)
- `AD-TenantSettings-RateLimits-Backend` Phase 58+ (~4-6 hr)
- `AD-TenantSettings-HITLPolicies-Backend` Phase 58+ (~2-3 hr)

### §Go/No-Go

✅ **GO for Day 1**. Drift findings (D-DAY0-1/2/3) are doc-quality nits + carryover bookkeeping; no scope shift > 20% on Track A; Track B scope confirmed within bounds.

---

## Day 1 — Implementation

_To be filled as work progresses._

---

## Day 2 — Closeout

_To be filled at sprint end._
