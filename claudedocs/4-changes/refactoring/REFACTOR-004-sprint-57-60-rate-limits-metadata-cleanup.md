# REFACTOR-004: RateLimits transitional meta_data fallback retirement

**Date**: 2026-05-29
**Sprint**: 57.60
**Scope**: Backend — Cat 2 (Tool Layer rate-limit gate) + Cat 12 (middleware) + platform_layer/tenant + infrastructure/db (migration); single-domain
**Type**: Refactoring (transitional-code removal + data-cleanup migration)
**Closes**: `AD-RateLimits-MetaData-Cleanup-Phase58` (Sprint 57.59 carryover)

## Problem

Sprint 57.59 split RateLimits config into the `rate_limit_configs` table and re-pointed all read/write paths to it, but **deliberately retained `tenant.meta_data["rate_limits"]` JSONB as a transitional read-fallback + kept the PUT dual-write** as a one-cycle migration safety net (57.59 plan §2.6). After 1 sprint validating the table path is stable, the fallback is dead weight: it (a) keeps a stale config blob in sync, (b) creates a second source of truth that can silently diverge, (c) clutters 5 call sites with `if config-empty: read meta_data` branches.

## Root Cause

Intentional transitional design (not a bug) — 57.59's additive-migration safety pattern. The cleanup was pre-scheduled as a named carryover AD.

## Solution

**US-1 — Remove the 5 transitional sites** (the meta_data MIDDLE tier; config-table read + terminal kept):

| # | Site | File | After |
|---|------|------|-------|
| 1 | GET `list_tenant_rate_limits` | `api/v1/admin/tenants.py` | `config → DEFAULT_RATE_LIMITS` |
| 2 | usage GET `get_rate_limits_usage` | `api/v1/admin/tenants.py` | `config → DEFAULT_RATE_LIMITS` |
| 3 | middleware `_load_rate_limits` | `platform_layer/middleware/rate_limit.py` | `config → []` (no phantom enforcement) |
| 4 | Cat 2 gate `_load_tool_limits` | `platform_layer/tenant/tool_rate_limit_gate.py` | `config → {}` |
| 5 | PUT `upsert_tenant_rate_limits` | `api/v1/admin/tenants.py` | config write only (dual-write removed) |

Orphan cleanup (Karpathy §3, only this-change orphans): unused `tenant` bindings → bare `await _load_tenant_or_404(...)` (404 contract kept); orphaned `select`/`Tenant` imports dropped; vestigial `db.refresh(tenant)` + redundant `db.flush()` (confirmed `replace_configs` flushes internally) removed from PUT.

**US-2 — Alembic `0020_clear_rate_limits_meta_data.py`** (data-only; down_revision `0019`):
- `upgrade()`: `UPDATE tenants SET "metadata" = "metadata" - 'rate_limits' WHERE "metadata" ? 'rate_limits'` (idempotent; physical column `"metadata"` per `AD-Day0-Prong3-Physical-Column-Read`)
- `downgrade()`: reverse-populate `meta_data["rate_limits"]` from `rate_limit_configs` via inline `_inline_project` (inverse of `0019._parse_item`; lossy for custom labels, dev-only). Uses `CAST(:items AS jsonb)` (asyncpg named-param compat).
- Dep-light (no service/Redis import — Sprint 57.59 D-DAY0-N rule).

## Verification

- pytest 1840 → **1848** (+8: 7 new `0020` migration tests + 1 new ignore-stale-meta_data test; 5 files of assertion conversions; 0 regressions)
- mypy `src/ --strict` 0/317 (CI parity per `backend-ci.yml:152`)
- 9/9 V2 lints green (`check_rls_policies` 20 tables unchanged — data-only migration; `check_llm_sdk_leak` 0)
- black/isort/flake8 clean
- Alembic live `0019→0020→0019→0020` round-trip clean
- 0 frontend files touched (API `{label, value}` shapes preserved) → Vitest 675 unaffected; HEX_OKLCH baseline 48; DUAL CLEAN 22/22 PARITY 16 consec

## Impact

- Backend-only. RateLimits config now has a single source of truth (`rate_limit_configs`); 0 transitional fallback branches.
- API contracts unchanged → frontend untouched.
- Completes the Phase 58.x RateLimits arc (57.58 runtime + 57.59 split + 57.60 cleanup) for config storage.

## Deviations / Findings

- `:items::jsonb` → `CAST(:items AS jsonb)` (asyncpg named-param × `::` cast collision; equivalent SQL, both drivers).
- Pre-existing (NOT this sprint, since 57.53): `mypy --strict .` whole-dir duplicate-conftest collection error (CI unaffected — runs `mypy src/`); flagged as `AD-Mypy-WholeDir-Conftest-Collision` Phase 58+ candidate.
