# CHANGE-028: RateLimits Runtime Enforcement (Sprint 57.58)

**Date**: 2026-05-28
**Sprint**: 57.58
**Scope**: Cat 12 (Observability/platform middleware) + Cat 2 (Tool Layer) + Cat 9 (admin endpoint) + Frontend (tenant-settings)

## Problem

`tenant.meta_data["rate_limits"]` (shipped Sprint 57.48 storage + 57.57 WRITE endpoint) was **admin-display-only**: no middleware read it, no request was ever throttled, no 429 ever returned, tool calls executed regardless of configured limits, and admins had no visibility into live consumption. The entire RateLimits subsystem was config-without-enforcement.

## Root Cause

The Sprint 57.48-57.57 WRITE-side wave deliberately scoped to storage only (admin CRUD over `meta_data` JSONB). Runtime enforcement was a named Phase 58.x carryover (`AD-RateLimits-RuntimeEnforcement-Phase58`). Additionally, Day 0 三-Prong surfaced that a fully-defined `RateLimit` ORM table (`api_keys.py:141`, since Phase 49 V2 baseline per `09-db-schema-design.md L902-919`) was an AP-4 Potemkin Feature — never wired in production.

## Solution

**Path B** (user-locked 2026-05-28): JSONB config + Redis sliding-window counter; dormant ORM left untouched (Potemkin migration deferred to `AD-RateLimits-Potemkin-Migration-Phase58`).

- **Track A — Middleware** (`platform_layer/middleware/rate_limit.py`): `RateLimitMiddleware(BaseHTTPMiddleware)` registered after `TenantContextMiddleware` in `api/main.py`; reads `tenant.meta_data["rate_limits"]`, runs per-resource sliding-window check via `RedisRateLimitCounter` (`platform_layer/tenant/rate_limit_counter.py`), returns 429 + `Retry-After`/`X-RateLimit-*` headers on over-limit; bypass via JWT `roles` claim (`admin`/`service`) + no-tenant; **fail-open** on Redis/error. Counter uses MULTI/EXEC pipeline reserve-then-rollback (fakeredis has no `EVAL`; matches `QuotaEnforcer` precedent). `parse_rate_limit_item()` normalizes the stored `{label, value}` UI strings (e.g. `"100 / min"`) into `(resource, limit, window_seconds)`.
- **Track B — Cat 2 tool layer** (`agent_harness/tools/executor.py`): LLM-neutral `RateLimitGate` Protocol pre-call hook (optional ctor injection keeps Cat 2 free of platform/Redis imports); `RedisToolRateLimitGate` (`platform_layer/tenant/tool_rate_limit_gate.py`) is the concrete adapter against `tool_calls.<name>` + `tool_calls` aggregate resources; `RateLimitExceededError` (`agent_harness/_contracts/errors.py`) registered FATAL in `error_handling/policy.py` (no LLM retry loop).
- **Track C — Live usage GET** (`api/v1/admin/tenants.py`): `GET /admin/tenants/{tid}/rate-limits/usage` returns `{items: [{resource, window, limit, current, reset_at}]}` via counter `peek` (no increment).
- **Track D — Frontend Live usage Card** (`tenant-settings/components/tabs/QuotasTab.tsx`): new Card below the (unchanged) Rate limits Card; `useRateLimitsUsage` hook polls every 5s; per-resource progress bar (reused `.bar-track` + `var(--success/--warning/--danger)` tokens; green<70%/yellow70-90%/red>90%) + reset countdown.

## Verification

- pytest 1806 → **1819** (+13 exact target: 6 middleware + 4 tool-layer + 3 GET usage) + 4 skip + 0 regressions
- Vitest 663 → **675** (+12: 3 hook + 2 service + 7 QuotasTab incl. RateLimits-Card-unchanged scope-guard)
- mypy --strict 0 / tsc 0 / 9/9 V2 lints green (incl. LLM SDK leak 0) / ESLint clean / Vite build 3.44s
- 0 new oklch (HEX_OKLCH baseline 48 unchanged) / mockup-fidelity DUAL CLEAN 22/22 PARITY preserved 14 consecutive sprints 57.45-57.58
- Multi-tenant isolation + per-resource isolation + admin-bypass + no-tenant-bypass all test-covered

## Impact

- Backend: NEW Cat 12 middleware + Cat 2 enforcement seam + 1 admin endpoint; LLM-neutrality preserved (Protocol/adapter split)
- Frontend: tenant-settings QuotasTab gains live observability; existing Rate limits Card untouched (bit-for-bit)
- Phase 58.x portfolio: 1/5 RateLimits deeper extensions shipped (RuntimeEnforcement)
- Deferred: AP-4 Potemkin `RateLimit` ORM migration (`AD-RateLimits-Potemkin-Migration-Phase58`); RateLimits SyntaxValidation + Alerting
- PR: (pending) `feature/sprint-57-58-rate-limits-runtime-enforcement`
