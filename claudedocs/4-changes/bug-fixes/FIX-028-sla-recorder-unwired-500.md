# FIX-028: /sla-report 500 — SLAMetricRecorder never wired at startup

**Date**: 2026-06-07
**Sprint**: post-57.87 (drive-through audit follow-up)
**Scope**: Cat 12 Observability (platform_layer.observability) / api boundary

## Problem
`GET /api/v1/admin/tenants/{tenant_id}/sla-report?month=YYYY-MM` returns **HTTP 500**
for any (tenant, month) without a cached `SLAReport` row. Surfaced by the 2026-06-06
35-page drive-through audit: `/sla-dashboard` shows "Failed to load data"
(`slaService.ts` → endpoint 500). Reproduced: dev-login (platform_admin, 200) →
`sla-report?month=2026-06` → **500 "Internal Server Error"**.

## Root Cause
**AP-4 wired-but-never-activated — the twin of FIX-022 (pricing loader).** The
SLA recorder singleton's producer was never installed in production:

- `set_sla_recorder()` is called **only in 2 test files** (`test_admin_sla_reports.py`,
  `test_api_smoke.py`). It is **never** called anywhere in `backend/src`. `main.py`
  `_lifespan` wires `_wire_rate_limit_counter` / `_wire_pricing_loader` /
  `_wire_error_budget` / `_wire_billing_outbox` — but had **no `_wire_sla_recorder`**.
- So at runtime `_recorder` stays `None` (proved in-process:
  `get_sla_recorder()` → `RuntimeError: SLAMetricRecorder not initialised`).
- 500 chain: handler cache lookup misses (no `SLAReport` for the month) →
  on-demand generate path → `sla_reports.py:99` `recorder = get_sla_recorder()`
  (**strict** accessor) → `RuntimeError` → unhandled → HTTP 500.

**Why gates were green / nobody noticed**:
- AP-10 mock/real divergence: tests inject their own recorder (pytest green);
  production never wires it (real call 500s).
- strict-vs-lenient split: the chat router uses the **lenient**
  `maybe_get_sla_recorder()` → silently no-ops when unwired (so SLA recording was
  silently off, but nothing crashed); only the report endpoint's **strict**
  `get_sla_recorder()` hard-fails. So only this one path 500s — invisible until driven.
- Redis was NOT the cause (port 6379 reachable); the producer was simply unwired.

## Solution
Mirror `_wire_error_budget` (pure-Redis, fail-open):

- `backend/src/api/main.py`: add `_wire_sla_recorder()` (build a lazy
  `Redis.from_url(settings.redis_url)` client → `set_sla_recorder(SLAMetricRecorder(...))`;
  fail-open: on any error leave the singleton None + warn — the endpoint then
  surfaces the recorder gap rather than blocking startup) and call it in `_lifespan`
  alongside the other `_wire_*`.

## Verification
- **Regression guard**: `backend/tests/unit/api/test_main_lifespan.py::test_lifespan_wires_sla_recorder`
  — drives the FastAPI lifespan via `TestClient`; asserts `maybe_get_sla_recorder()`
  is `None` before startup and non-`None` after (mirrors the FIX-022 pricing guard).
- **Drive-through** (real backend :8000 + real Redis): dev-login → `sla-report?month=2026-06`
  now returns **200** with the report JSON; `/sla-dashboard` renders.
- Gates: `mypy .` 0 errors / `pytest` green / `python scripts/lint/run_all.py` 10/10.

## Impact
Backend-only (api boundary + Cat 12 wiring). One new startup wire + one regression
test. No schema / migration / frontend change. After the fix, SLA metric recording
(chat-router `maybe_get_sla_recorder()`) also becomes live (was a silent no-op),
so the report now reflects real recorded p99s instead of always all-`None`.

## Follow-on (not in this FIX)
- `AD-SLA-Report-CrossTenant-RLS-Check`: verify the on-demand generate path's
  `SLAReport`/`SLAViolation` INSERT under RLS when a platform_admin views a tenant
  **other than** their own JWT tenant (the drive-through covered same-tenant only).
- `AD-SLA-Report-Endpoint-Degrade-Lenient`: consider making the endpoint degrade
  (503 / empty) like the chat router rather than depending on the recorder being wired.
