# CHANGE-042: admin-tenants stats aggregate endpoint + per-row agents/runs24 + strip wiring

**Change Date**: 2026-06-03
**Change Type**: New Feature (backend aggregate + frontend wiring)
**Sprint**: 57.74
**Scope**: Admin API aggregate (platform-layer admin read) + Frontend real-data wiring (admin-tenants)
**Status**: ✅ Completed (push/PR user-gated)

## Change Summary
Closes the Sprint 57.73 (A-6a) carryover `AD-AdminTenants-Stats-Aggregate-Endpoint`. Adds a new fleet-wide `GET /api/v1/admin/tenants/stats` (platform-admin, cross-tenant aggregate) and wires the admin-tenants stats strip + the two previously-gapped per-row columns (Agents, Runs · 24h) to it.

## Change Reason
Sprint 57.73 wired the admin-tenants list to real `GET /admin/tenants`, but the `TenantsStatsStrip` stayed on `STATS_FIXTURE` and the `Agents`/`Runs · 24h` table columns rendered a literal "—" because no aggregate backend existed. This closes that gap (Area-A #3 in the "process all carryover except A-4 Tier 2" program).

## Detailed Changes
**Backend** (`backend/src/api/v1/admin/tenants.py`):
- NEW `GET /admin/tenants/stats` → `TenantsStatsResponse{fleet, per_tenant, gapped}`.
  - `fleet.active_tenants` = count(Tenant state=ACTIVE); `fleet.total_seats` = coalesce(sum(Tenant.seats),0); `fleet.agents_deployed` = count(agent_catalog is_active).
  - `per_tenant[{tenant_id, agents, runs24}]` = agents GROUP BY (is_active) ⊎ runs24 GROUP BY (sessions started_at ≥ now(utc)−24h), merged on tenant_id union (missing side → 0).
  - `gapped = ["anomalies", "deltas"]` — no backend source; reported, never fabricated (AP-4).
- Deps: `require_admin_platform_role` + plain `get_db_session` (fleet-wide cross-tenant by design). Route placed after the list endpoint, before `/{tenant_id}` (Day-0 D-DAY0-1 path-order).

**Frontend** (`frontend/src/features/admin-tenants/`):
- `services/adminTenantsService.ts` — `fetchStats(signal)`; `types.ts` — `FleetStats`/`PerTenantStat`/`TenantsStatsResponse`; `hooks/useAdminTenantsStats.ts` (NEW, key `["admin-tenants","stats"]`).
- `TenantsStatsStrip.tsx` — 3 real stats (toLocaleString); `Anomalies` = subtle "—"; trend deltas omitted; `BackendGapBanner` names the gap; mockup-native loading/error; `STATS_FIXTURE` removed.
- `TenantsTable.tsx` — `statsByTenant` map prop fills Agents/Runs·24h (`renderCount`: real >0 / subtle "—" for absent/0); table gap banner dropped (strip owns the single banner).
- `AdminTenantsView.tsx` — mounts `useAdminTenantsStats`, threads `fleet` to strip + `per_tenant` reduce → `statsByTenant` to table; 57.73 list query untouched.

## Modified Files List
- `backend/src/api/v1/admin/tenants.py` (endpoint + 3 Pydantic models)
- `backend/tests/integration/api/test_admin_tenants_stats.py` (NEW, 6 tests)
- `frontend/src/features/admin-tenants/{services/adminTenantsService,types,_fixtures}.ts` + `hooks/useAdminTenantsStats.ts` (NEW) + `components/{TenantsStatsStrip,TenantsTable,AdminTenantsView}.tsx`
- `frontend/tests/unit/admin-tenants/{TenantsStatsStrip,TenantsTable,AdminTenantsView,useAdminTenantsStats}.test.tsx` + `_fixtures.test.ts` + `frontend/tests/e2e/admin-tenants.spec.ts`

## Verification (parent-run)
- Backend: `mypy src/` 0/329; `pytest` 29 passed (6 new + 23 list + 2 rbac); `scripts/lint/run_all.py` 10/10.
- Frontend: `check:mockup-fidelity` byte-identical + baseline 50 unchanged; `build` tsc 0; `lint` exit 0 (no `--silent`); Vitest 715 passed (129 files, +7 net).

## Impact
Backend + frontend; admin-tenants page only. No DB migration, no CSS change, no new dependency. Anomalies stat + trend deltas remain honest-gapped (NEW carryover `AD-AdminTenants-Anomalies-Stat-Backend` + `AD-AdminTenants-Stats-Trend-Deltas`).
