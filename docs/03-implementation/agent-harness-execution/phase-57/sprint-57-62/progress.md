# Sprint 57.62 Progress

**Sprint**: 57.62 — RateLimits Alerting (close `AD-RateLimits-Alerting-Phase58`)
**Branch**: `feature/sprint-57-62-rate-limits-alerting` (from main `2d99d626`)
**Class**: `medium-backend` 0.80 / agent-delegated yes (sequential Track A backend + Track B frontend) / agent-factor `mechanical-greenfield-design-decisions` 0.65 (4th validation, back to backend+frontend pair shape)

---

## Day 0 — Plan + Checklist + 三-Prong Verify (2026-05-29)

### Artifacts
- `sprint-57-62-plan.md` v1 (9-section; user-approved 2026-05-29 全採 — Option A persisted log / 2-tier severity / counter-write-through detection / 15s frontend poll / sequential 2-agent / CHANGE-030; grounded in pre-plan Explore recon)
- `sprint-57-62-checklist.md` v1
- This progress.md

### Day 0 三-Prong Verify — 16 checks (13 GREEN + 1 NOTABLE-simplification + 3 corrections; 0 CRITICAL-blocker); Prong 3 APPLIES (new table)

#### Prong 1 — Path Verify
- **D-DAY0-A** ✅ GREEN — `RateLimitAlert` / `rate_limit_alerts` / `RateLimitAlertStore` grep 0 matches → NEW
- **D-DAY0-B** ✅ GREEN — `RateLimit` (`api_keys.py:153`) + `RateLimitConfig` (`:210`) both `TenantScopedMixin` → new `RateLimitAlert` lands in same file for cohesion
- **D-DAY0-D** ✅ GREEN — `GET .../rate-limits/usage` + `_load_tenant_or_404` + `RateLimitsUsageItem` present in `tenants.py` (mirror auth for new alerts GET)
- **D-DAY0-E** ✅ GREEN + **path correction**: `backend/tests/unit/platform_layer/tenant/` exists (`test_rate_limit_parser_consistency.py` 57.61). Migration tests live in **`backend/tests/integration/api/`** (`test_rate_limit_config_migration.py` + `test_clear_rate_limits_meta_data_migration.py`), **NOT** a `tests/integration/db/` dir → plan §5 path corrected `db/` → `api/`.
- **D-DAY0-F** ✅ GREEN — `useRateLimitsUsage.ts` + `usageColorToken` (QuotasTab) + `tenantSettingsService.ts` + `var(--warning)`/`var(--danger)` tokens present → US-3 reuse, 0 new oklch
- **D-DAY0-N** ✅ GREEN — Alembic head `0020_clear_rate_limits_meta_data` → next `0021` free

#### Prong 2 — Content Verify
- **D-DAY0-G** ✅ 🔴 CRITICAL GREEN + **NOTABLE simplification** — hook site = **`_write_through(self, ..., limit, ...)`** (`rate_limit_counter.py:265`). It guards `if self._session_factory is None: return` (L282, fail-open), opens a session, computes `window_start, window_end = self._window_bounds(...)` (L289), and upserts `pg_insert(RateLimit).on_conflict_do_update(used=func.greatest(...))` (L298-311). **All 7 values in scope at the upsert**: `session` / `tenant_id` / `resource` / `window_type` / `used` / `limit` (= the quota, denormalised config snapshot per its docstring) / `window_start`. The whole method is already best-effort ("any DB error logs + continues"). → **NOTABLE: the alert store is stateless + the session is already present → NO ctor DI + NO `api/main.py` wiring needed** (the counter imports + calls `maybe_record(session, ...)` directly inside `_write_through`). Plan §4.4 + §5 `api/main.py` edit DROPPED (scope −~0.2 hr; parallels 57.61 D-DAY0-J micro-simplification).
- **D-DAY0-H** ✅ GREEN — `api/main.py:_wire_rate_limit_counter` L110 `set_rate_limit_counter(RedisRateLimitCounter(client, session_factory=get_session_factory))`; confirms the fail-open singleton install (no change needed — alert hook rides `_write_through`)
- **D-DAY0-I** ✅ GREEN + **refinement** — `SLAViolation` (`sla.py:83`): `threshold_pct`/`actual_pct` = `Numeric(8,4)`, `severity` = `String(32)` lowercase `minor`/`major`/`critical` + `CHECK severity IN (...)` (`ck_sla_violations_severity`), `detected_at` + `resolved_at`. → `RateLimitAlert` aligns: severity **lowercase `warning`/`critical`** + a `CHECK` constraint (mirror precedent; was uppercase in plan §4.1); keep `threshold_pct`/`actual_pct` as **`int`** (rate-limit pct is integer-grained — deliberate divergence from SLAViolation `Numeric(8,4)`, noted §8 R8 / CHANGE-030).
- **D-DAY0-J** ✅ GREEN + **correction** — `0019` RLS (L184-195): `ENABLE` + **`FORCE ROW LEVEL SECURITY`** + `CREATE POLICY tenant_isolation_<t> USING (tenant_id = current_setting('app.tenant_id', true)::uuid)` + `CREATE POLICY tenant_insert_<t> WITH CHECK (...)`. → `0021` must use **`current_setting('app.tenant_id', true)::uuid`** (WITH the `true` missing_ok arg) + `FORCE` (plan §4.2 had omitted both).
- **D-DAY0-K** ✅ GREEN — `from sqlalchemy.dialects.postgresql import insert as pg_insert` (`rate_limit_counter.py:63`) + `func.greatest` (L311) → same import path for the alert store
- **D-DAY0-L** ✅ GREEN — QuotasTab has Rate limits Card + Live usage Card (57.58); new Recent alerts Card adds BELOW; Track B scope-guard test asserts the 2 existing cards unchanged

#### Prong 3 — Schema Verify (NEW table)
- **D-DAY0-M/O** ✅ GREEN — `TenantScopedMixin` (`base.py:51`) `tenant_id` via `@declared_attr` `mapped_column(...)` NOT NULL UUID + index; standard mixin used by `RateLimit`/`RateLimitConfig`/`SLAViolation` → `RateLimitAlert` mirrors `RateLimit` exactly; **no physical-column alias trap** (clean `tenant_id`, unlike the `meta_data`→`metadata` case 57.59/57.60)
- **D-DAY0-N** ✅ GREEN (above) — head `0020` is `0021`'s down_revision
- **D-DAY0-P** ✅ GREEN — `check_rls_policies` baseline 20 tables (per 57.60/57.61); `0021` 2-policy add → 21

### Go/No-Go
**GO for Day 1.** 0 CRITICAL-blocker. Net scope shift ≈ **−3%** (dropped `api/main.py` wiring edit via D-DAY0-G stateless-store simplification; 3 factual corrections folded into plan: migration-test path `db/`→`api/`, RLS SQL `+, true` + `FORCE`, severity lowercase + CHECK). All corrections preserved here as audit trail; plan §4.1/§4.2/§4.4/§5 + checklist updated to reality.

### Day 0 commit
- (pending) plan + checklist + this progress.md Day 0 entry

---

## Day 1 — Implementation (pending — sequential Track A backend → Track B frontend)

## Day 2 — Closeout (pending)
