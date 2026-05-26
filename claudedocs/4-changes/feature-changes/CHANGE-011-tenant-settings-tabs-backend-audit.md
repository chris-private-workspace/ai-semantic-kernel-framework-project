# CHANGE-011: TenantSettings 6-Tab Backend Audit

**Date**: 2026-05-26
**Sprint**: 57.47 (Day 0.8b Track B Investigation)
**Scope**: Backend audit — `frontend/src/features/tenant-settings/_fixtures.ts` 6 tabs vs backend modules
**Closes** (partial — Round 2): `AD-TenantSettings-Backend-Schema-Extension` (Sprint 57.46 carryover)

## Problem

Sprint 57.44's /tenant-settings 6-tab rebuild shipped Option A fixture-first
(per D-DAY0-4): only `display_name` is live-wired; FEATURE_FLAGS / QUOTAS /
RATE_LIMITS / HITL_POLICIES / MEMBERS / DANGER_OPS are all fixture-only with
AP-2 `BackendGapBanner` declaring Phase 58+ gap. Sprint 57.46 closed the
**Tenant ORM** half (5 new SaaS columns), but the per-tab backend readiness
was never formally audited. Phase 58+ frontend real-data migration risked
trial-and-error per tab without prioritization data.

## Root Cause

Sprint 57.44's plan only catalogued the gap; no follow-up sprint had been
scheduled to audit each tab's backend backing and produce a scope estimate.

## Solution

Day 0.8b 6-tab audit table (see also `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-47/progress.md` §TenantSettings backend audit):

| Tab | Verdict | Backend file ref | Phase 58+ scope | Notes |
|---|---|---|---|---|
| **FEATURE_FLAGS** | partial (ORM exists, no admin GET endpoint) | `backend/src/infrastructure/db/models/feature_flag.py` + `backend/src/core/feature_flags.py` | ~3-4 hr | Global registry with `tenant_overrides` JSONB pattern (multi-tenant rule §Rule 1 exception); admin endpoint expose per-tenant resolved values |
| **QUOTAS** | partial (Redis-only single-dim) | `backend/src/platform_layer/tenant/quota.py` | ~3-5 hr | Current `QuotaEnforcer` only enforces `quota:tokens:{tenant_id}:{date}`; fixture shows 5 dimensions; needs new `tenant_quotas` table + multi-dim service |
| **RATE_LIMITS** | fixture-only | NO backend module | ~4-6 hr | Highest cost — needs new table + Redis token-bucket layer + admin endpoint |
| **HITL_POLICIES** | partial (ABC + DBHITLPolicyStore impl, no admin GET) | `backend/src/agent_harness/hitl/_abc.py` HITLPolicyStore | ~2-3 hr | Concrete impl shipped Sprint 55.3 (AD-Hitl-7); admin endpoint should project to fixture `{risk, policy, sla, approvers, off[]}` shape |
| **MEMBERS** | partial (User ORM ready, no admin GET-by-tenant) | `backend/src/infrastructure/db/models/identity.py` L187-225 | **~1.5-2 hr** ← CHEAPEST | All needed fields on User ORM via TenantScopedMixin; only endpoint + Pydantic + tests needed |
| **DANGER_OPS** | N/A (UI actions) | N/A | N/A | Suspend / Rotate keys / Tombstone PII / Delete — covered by existing tenant lifecycle endpoints (Sprint 56.1 POST suspend/archive) |

## Track B Day 1 Decision

Per checklist §0.8b decision rule (cheapest ≤ 2 hr → implement; else defer all):

**MEMBERS** at ~1.5-2 hr is the cheapest fixture-only tab. **Proceeded with
Track B Day 1 stretch**; see CHANGE-012 for the implementation details.

## Carryover ADs (Phase 58+)

The 4 non-MEMBERS partial/fixture tabs deferred to Phase 58+ as named ADs:

- `AD-TenantSettings-FeatureFlags-Backend` (~3-4 hr)
- `AD-TenantSettings-Quotas-Backend` (~3-5 hr)
- `AD-TenantSettings-RateLimits-Backend` (~4-6 hr) — highest cost; consider deferring further until product confirms need
- `AD-TenantSettings-HITLPolicies-Backend` (~2-3 hr) — likely next-cheapest pickup after MEMBERS

Recommend pickup order by ROI: **HITL_POLICIES → FEATURE_FLAGS → QUOTAS → RATE_LIMITS**.

## Impact

- **Phase 58+ planning**: Frontend migration sprints can now prioritize tabs by backend readiness instead of discovering gaps mid-implementation
- **No code change** for this CHANGE (investigation deliverable; MEMBERS impl in CHANGE-012)
- **Frontend `_fixtures.ts`**: unchanged this sprint; per-tab migrations will swap fixture imports to real hooks as each backend lands
