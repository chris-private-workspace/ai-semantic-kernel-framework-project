# CHANGE-041: A-6 Frontend Real-Data Wiring (A-6a admin-tenants partial + A-6b memory matrix backend + wiring)

**Change Date**: 2026-06-03
**Change Type**: Feature Improvement (real-data wiring + 1 new backend read aggregate)
**Sprint**: 57.73
**Scope**: Frontend (admin-tenants + memory) + Cat 3 Memory REST facade (new read aggregate)
**Status**: ✅ Completed (PR pending — user-gated)

## Change Summary

Restored real backend data on the two pages the Sprint 57.18-57.43 mockup-rebuild epic left on fixtures, for the subset with a real (or cheaply-addable) producer — the final Area-A integration-gap item (A-6).

- **A-6a — admin-tenants partial wiring** (frontend-only): re-mounted the existing `useAdminTenants` hook (it was built but unmounted in the rebuild). The tenants table now renders real `GET /api/v1/admin/tenants` data — `name←display_name`, `id←code`, `plan`, `region`, `seats`, `status←state`, `created←created_at`. The two genuinely-unbacked columns (`agents`, `runs · 24h`) render a literal `"—"` (no fabricated numbers); the aggregate `TenantsStatsStrip` stays on fixtures (no aggregate-stats endpoint). Both gaps are declared via `BackendGapBanner` (honest AP-2). Loading / error / empty states are mockup-native rows.
- **A-6b — memory matrix backend + wiring** (backend + frontend): new `GET /api/v1/memory/matrix` Cat 3 read aggregate (COUNT GROUP BY over the 3 wired layers — system/tenant/user) feeds the `MemoryMatrix` 5×3 grid + `MemoryPageHeader` total via a new `useMemoryMatrix` TanStack hook. role/session layers are reported gapped (`gapped_layers`, 501 — no RLS path) and render an `n/a` indicator. `RecentMemoryOpsCard` + `TimeTravelScrubber` stay fixture-gapped because they render an operation/version timeline that has **no backend producer** (deferred — see Carryover).

## Change Reason

A-6 (frontend real-data wiring) is the final Area-A integration-gap item. The mockup-rebuild epic verbatim-ported pages from JSX and dropped the real hooks on `admin-tenants` + `memory`. This sprint restores the lost wiring where a backend producer exists, and adds the one cheap backend aggregate (memory matrix counts) the memory page needs.

The original analysis over-claimed both pages as clean "pure-wiring". Two Day-0 ground-truth passes refuted this:
- admin-tenants: backend has region+seats (added 57.46/57.47 — better than the analysis said) but still lacks `agents`/`runs24` + any aggregate-stats endpoint → A-6a is *partial*, not a clean full re-mount.
- memory: the 5 components render matrix/ops-timeline/time-travel shapes; the backend has only flat entry rows + 3 wired layers, and **memory writes emit zero audit rows / no version history** → only matrix + header counts are cheaply backable; the ops/time-travel widgets need a separate Cat 3 write-path-instrumentation feature.

Scope was re-confirmed with the user (2 AskUserQuestion) before drafting: A-6a partial + A-6b matrix-only backend; ops/time-travel deferred.

## Detailed Changes

### A-6a admin-tenants (frontend-only)
- `AdminTenantsView.tsx` — mount `useAdminTenants()`; thread `items`/`isLoading`/`isError`/`refetch` to `TenantsTable`.
- `TenantsTable.tsx` — accept `tenants: TenantListItem[]` + loading/error/onRetry props (was a direct `TENANTS_FIXTURE` import); field-map real fields; `"—"` (`var(--fg-subtle)`) for `agents`/`runs24`; mockup-native loading (skeleton rows) / error (inline + Retry) / empty states (English copy, matching the codebase convention); reworded `BackendGapBanner` to name the gapped columns.
- `TenantsStatsStrip.tsx` — added `BackendGapBanner` (stays `STATS_FIXTURE`; no aggregate endpoint).
- `types.ts` — synced `TenantListItem` to the real backend contract (added region/locale/retention_days/sso_enabled/seats — the FE type was stale at Sprint 57.4's 7 fields).
- `_fixtures.ts` — removed the now-orphan `TENANTS_FIXTURE` (kept `STATS_FIXTURE`).
- `pages/admin-tenants/index.tsx` — updated the stale "unmounted in this rebuild" comment.

### A-6b memory matrix (backend)
- `backend/src/api/v1/memory.py` — new `MemoryMatrixCell` / `MemoryMatrixResponse` Pydantic models + `GET /matrix` endpoint (mirrors `/recent`'s `current_tenant` + `require_audit_role` + `get_db_session_with_tenant` deps trio). Aggregate: `count()` for system (global) + tenant (`WHERE tenant_id == current_tenant`, RLS + defense-in-depth) → permanent; `count() GROUP BY case(expires_at buckets)` for user → permanent/quarterly/daily (same predicate as `/by-time`). `gapped_layers=[role,session]` reported, not queried. Zero-count cells omitted. No DB migration (read aggregate).

### A-6b memory (frontend)
- `types.ts` — `MemoryMatrixCell` / `MemoryMatrixResponse` (backend vocab `permanent|quarterly|daily`).
- `services/memoryService.ts` — `fetchMatrix()`.
- `hooks/useMemoryMatrix.ts` (NEW; first file in the new `memory/hooks/` dir) — `useQuery` key `["memory","matrix"]`, mirrors `useCostSummary`.
- `MemoryMatrix.tsx` — consumes `useMemoryMatrix`; 5×3 grid with real counts for system/tenant/user (0 for absent cells → "— empty"), `n/a` for role/session (`gapped_layers`, never fabricated); reworded banner ("system/tenant/user live; role/session no backend path (501)"); mockup-native loading/error/empty.
- `MemoryPageHeader.tsx` — real `total` (same dedup'd query).
- `MemoryView.tsx` — dropped the fixture-only `cursor` entry-filter wiring.
- `RecentMemoryOpsCard.tsx` + `TimeTravelScrubber.tsx` — unchanged fixtures; banners reworded → `AD-Memory-OpsHistory-Backend` carryover.
- `_fixtures.ts` — removed orphan matrix/header fixtures (kept ops/timeline).

## Modified Files List

Backend (1 src + 1 test): `api/v1/memory.py`; `tests/integration/api/test_memory_matrix.py` (NEW, 6 tests).
Frontend admin-tenants (6 src + 3 test): `components/{AdminTenantsView,TenantsTable,TenantsStatsStrip}.tsx`, `types.ts`, `_fixtures.ts`, `pages/admin-tenants/index.tsx`; `tests/unit/admin-tenants/{TenantsTable,AdminTenantsView,_fixtures}.test.*`; `tests/e2e/admin-tenants.spec.ts` (NEW).
Frontend memory (6 src + 1 new hook + 4 test): `components/{MemoryMatrix,MemoryPageHeader,MemoryView,RecentMemoryOpsCard,TimeTravelScrubber}.tsx`, `types.ts`, `services/memoryService.ts`, `hooks/useMemoryMatrix.ts` (NEW); `tests/unit/memory/{useMemoryMatrix,MemoryMatrix,MemoryPageHeader,MemoryView,RecentMemoryOpsCard}.test.tsx`.

## Test Checklist

- [x] Backend `test_memory_matrix.py` 6/6 (counts per layer/time_scale; `gapped_layers`; cross-tenant isolation; empty → total 0; RBAC 403)
- [x] Memory regression: 28 passed (existing `test_memory.py` 13 + matrix 6 + query_extension 3 + chat wiring — facade intact)
- [x] `mypy src --strict` 0/329; `python scripts/lint/run_all.py` 10/10 (incl. `check_ap4_frontend_placeholder` — honest gaps pass; `check_llm_sdk_leak`; `check_rls_policies`)
- [x] Frontend `npm run build` tsc 0; Vitest admin-tenants+memory 72/72 (full suite 708)
- [x] `npm run lint` (no `--silent`) exit 0; `npm run check:mockup-fidelity` byte-identical + baseline 50 unchanged; CSS diff empty; grep 0 hardcoded hex/oklch
- [x] Playwright admin-tenants e2e (happy/error/empty) — 3/3 (Track A ran headlessly)

## Impact

- admin-tenants: most data-heavy admin page now shows real tenants; 2 columns + stats strip honestly gapped.
- memory: matrix + header are real (3 of 5 layers); ops/time-travel honestly gapped (deferred).
- No DB migration; multi-tenant isolation enforced on the new aggregate; no CSS change; no LLM dependency.

## Carryover

- `AD-Memory-OpsHistory-Backend` — memory op-history backend (5 layer `write()`/`evict()` + 2 tools emitting `append_audit(resource_type="memory_*")`, OR a new append-only `memory_ops` table; forward-only, no backfill) to back `RecentMemoryOpsCard` + `TimeTravelScrubber`.
- `AD-AdminTenants-Stats-Aggregate-Endpoint` — per-tenant `agents`/`runs24` counts + an aggregate-stats endpoint to back the gapped columns + `TenantsStatsStrip`.
- memory role/session layer backend (junction tables, 501); matrix cell drill-down (`fetchByScope`/`fetchByTime`); REST-type codegen for service DTOs.
