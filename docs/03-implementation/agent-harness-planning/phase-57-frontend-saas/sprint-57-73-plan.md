# Sprint 57.73 Plan — A-6 Frontend Real-Data Wiring (A-6a admin-tenants partial + A-6b memory matrix backend + wiring)

**Purpose**: Advance `A-6` (frontend real-data wiring, the final Area-A item) by restoring real backend data on the two pages the Sprint 57.18-57.43 mockup-rebuild epic left on fixtures — **admin-tenants** and **memory** — for the subset that has (or can cheaply gain) a real backend producer. **A-6a** (admin-tenants) is a *partial* re-mount: `useAdminTenants` + `GET /api/v1/admin/tenants` exist, so the tenant table is wired to real `display_name/code/plan/region/seats/state/created_at`, while the two genuinely-unbacked columns (`agents`/`runs24`) + the aggregate `TenantsStatsStrip` stay fixture-gapped with `BackendGapBanner` (honest AP-2 — no backend aggregate-stats endpoint exists). **A-6b** (memory) is a backend+frontend paired add: a new `GET /api/v1/memory/matrix` aggregate (COUNT GROUP BY over the 3 wired layers — system/tenant/user) feeds the `MemoryMatrix` 5×3 grid + `MemoryPageHeader` total; `RecentMemoryOpsCard` + `TimeTravelScrubber` stay fixture-gapped because they render an **operation/version timeline that has NO backend producer** (memory `write()` is a plain INSERT — zero audit emit, no version history) — backing them is a separate, larger Cat 3 write-path-instrumentation feature (deferred, carryover). This is a **backend+frontend feature-continuation sprint** (the matrix endpoint mirrors the existing Sprint-57.12 `/memory/recent` facade pattern; no new domain) → **no design note**; the frontend Mockup-Fidelity Hard Constraint applies (`docs/rules-on-demand/frontend-mockup-fidelity.md`).
**Category / Scope**: Frontend real-data wiring (admin-tenants) + Cat 3 Memory REST facade extension (new read aggregate) + Frontend wiring (memory); Phase 57.73
**Status**: Draft — code execution gated on Day-0 GO (Step 2.5). Ground-truth already gathered via two Day-0 researcher passes (see §0).
**Source**: A-6 deep-analysis `claudedocs/5-status/frontend-real-data-wiring-analysis-20260531.md` (§1 pure-wiring wins + §6 A-6a/A-6b recommendation + §7 per-page wiring DoD) + A+B+C capstone `integration-gap-capstone-abc-20260601.md` (A-6a = cheapest Area-A win) + **two Day-0 ground-truth researcher passes (2026-06-03)** (frontend wiring matrix + Cat 3 Memory backend feasibility) + user AskUserQuestion decisions 2026-06-03 (**scope = A-6a + A-6b together, A-6b WITH backend**)

> **Modification History**
> - 2026-06-03: Initial creation — A-6a admin-tenants partial wiring + A-6b memory matrix backend (new `/memory/matrix` aggregate) + wiring; ops/time-travel widgets deferred (no backend producer); backend+frontend feature-continuation (no design note)

---

## 0. Background

A-6 is the final Area-A item. Unlike A-1…A-5 (one backend seam each), A-6 is **breadth** — a portfolio of ~20 pages at different wiring stages. Per the Mockup-Fidelity rule, shipping a widget on fixtures + `BackendGapBanner` + a follow-up wiring sprint is the *intended* workflow, so most of A-6 is expected interim debt. The actionable-now core is the two pages whose real wiring the rebuild **dropped**: `admin-tenants` and `memory`. The user selected both, with backend added for memory where feasible.

### Day-0 ground-truth (two researcher passes, main `7b0c326e`)

**A-6a admin-tenants** (frontend audit pass):
- **D1 — hook exists, unmounted**: `hooks/useAdminTenants.ts:34-41` exists (`useQuery<TenantListResponse>`, key `["admin-tenants","list",query]`, `queryFn → listTenants(query, signal)`, `keepPreviousData`, reads `query` from `adminTenantsStore`) but is **imported nowhere** — `pages/admin-tenants/index.tsx:13-14` literally documents "useAdminTenants hook unmounted in this rebuild; backend wire deferred Phase 58+ via AP-2 BackendGapBanner".
- **D2 — components import fixtures directly**: `AdminTenantsView.tsx:38-52` mounts `TenantsPageHeader` + `TenantsStatsStrip` + `TenantsTable` + `TenantMembersDrawer` with no hook; `TenantsTable.tsx:35` imports `TENANTS_FIXTURE` directly (not a prop; only prop is `onRowClick?`), `.map` at `:94`, renders name/id/plan/region/seats/agents/runs24/status/created (`:101-154`) + a `BackendGapBanner` at `:159`; `TenantsStatsStrip.tsx:28,33` imports+maps `STATS_FIXTURE` directly (label/value/delta/deltaDir).
- **D3 — backend has MORE than the analysis claimed**: `tenants.py:227-275` `GET /admin/tenants` → `TenantListResponse{items,total,limit,offset}`; `TenantListItem:194-215` carries `id/code/display_name/state/plan/region/locale/retention_days/sso_enabled/seats/created_at/updated_at` (region+seats were added Sprint 57.46/57.47 — the analysis said they were missing → **DRIFT, in our favour**). **Still missing `agents`/`runs24`** (no per-tenant agent-count / 24h-run-count) and **NO aggregate-stats endpoint** anywhere.
- **D4 — field mapping**: table `status` ← backend `state` (real); `name`←`display_name`, `id`←`code`, `plan`/`region`/`seats`/`created`←direct. Only `agents` + `runs24` are truly unbacked per-row; the whole `TenantsStatsStrip` (multi-stat trend with delta/deltaDir) has no aggregate source.

**A-6b memory** (frontend audit + backend feasibility passes):
- **D5 — hooks don't exist; service does**: `frontend/src/features/memory/hooks/` does NOT exist; `services/memoryService.ts:70-119` has `memoryService.{fetchRecent,fetchByScope,fetchByTime}` → `/api/v1/memory/{recent,scope/{layer}/{id},by-time/{layer}/{scale}}` (all → `MemoryEntryPage`); `types.ts:34-71` defines `MemoryLayer`(5), `MemoryTimeScale=permanent|quarterly|daily`, `MemoryEntryItem`, `MemoryEntryPage`.
- **D6 — the 5 components render shapes the backend does NOT produce**: `MemoryMatrix.tsx` (5×3 grid of counts), `MemoryPageHeader.tsx` (TOTAL_ENTRIES), `RecentMemoryOpsCard.tsx` (op verb + scope + key + value + by-user + at-time), `TimeTravelScrubber.tsx` (ops-over-time + time-travel marks), `GdprErasureCard.tsx` (pure stub). Backend returns flat `MemoryEntryItem` rows only.
- **D7 — backend feasibility verdict (the decisive finding)**: memory has **5 separate tables** (`MemorySystem`/`MemoryTenant`/`MemoryRole`/`MemoryUser`/`MemorySessionSummary`, `infrastructure/db/models/memory.py`); only `MemoryUser` has `expires_at` (→ the permanent/quarterly/daily time-scale axis, logic at `memory.py:216-222`); only system/tenant/user have a wired API path (role/session → **501**, `memory.py:289-294,343-347`). **There is NO memory operation history**: `write()` is a plain INSERT (`user_layer.py:133-148`), `evict()` is a hard DELETE, no version increment, and **memory writes emit ZERO `audit_log` rows** (grep-confirmed — no `append_audit(resource_type="memory*")` anywhere). The `MemoryAccessed` SSE event (17.md:241) is runtime-only telemetry, not persisted.
- **D8 — per-widget feasibility**:

  | Widget | Backend producer | This sprint |
  |--------|------------------|-------------|
  | `MemoryMatrix` (5×3 counts) | ✅ new `GET /memory/matrix` = COUNT GROUP BY (one query / wired layer) | **WIRE** — system/tenant/user real; role/session gapped (501); time-scale axis real only for user (system/tenant → permanent column) |
  | `MemoryPageHeader` (total) | ✅ sum of the matrix counts (fold into same endpoint) | **WIRE** — 3 layers; will undercount vs the mockup's 6,514 (role/session gapped) |
  | `RecentMemoryOpsCard` (ops feed) | ❌ no ops/audit/version source | **GAP** (fixture + banner) |
  | `TimeTravelScrubber` (temporal) | ❌ same missing temporal log | **GAP** (fixture + banner) |

- **D9 — conventions**: new GET mirrors `memory.py:243-262` (`@router.get`, deps trio `get_current_tenant` + `require_audit_role` + `get_db_session_with_tenant` for RLS SET LOCAL). TanStack hook template = `useCostSummary.ts:39-45` (+ `useAdminTenants.ts:32-41`). The memory REST facade endpoints (`/recent`,`/scope`,`/by-time`) are NOT in 17.md (added Sprint 57.12 as a UI facade) — the new `/matrix` follows that precedent (router + FE service single-source, not a 17.md cross-category ABC). No DB migration (read aggregate over existing tables) → no Prong 3 schema verify.
- **D10 — mockup-fidelity infra**: shadcn-utility residue grep = **0** in both `features/admin-tenants` and `features/memory`; both use verbatim mockup classes + inline `style={{}}` with `eslint-disable no-restricted-syntax` headers. A DATA-only wiring change won't touch CSS. ⚠️ the shared `TableSkeleton`/`ErrorRetry`/`EmptyState` (`components/ui/`) carry shadcn Tailwind tokens (`bg-muted` etc.) → using them inside verbatim-mockup pages would inject residue; prefer **mockup-native** loading/empty markup. `check:mockup-fidelity` `HEX_OKLCH_BASELINE = 50` must stay (57.69 D-DAY2-1 lesson: a frontend sprint MUST run the gate). Mockups: `reference/design-mockups/page-admin.jsx` L322-409 (tenants), `page-governance.jsx` L462-597 (memory).

**Net**: (1) re-mount `useAdminTenants` in admin-tenants, map real fields, keep `agents`/`runs24` + `TenantsStatsStrip` fixture-gapped; (2) new `GET /memory/matrix` Cat 3 aggregate + (3) wire `MemoryMatrix` + `MemoryPageHeader` to it, keep `RecentMemoryOpsCard` + `TimeTravelScrubber` fixture-gapped. No DB migration, no CSS change.

---

## 1. Sprint Goal

Restore real backend data on the two pages the mockup-rebuild left on fixtures, for the subset with a real (or cheaply-addable) producer. **A-6a**: re-mount `useAdminTenants` in `admin-tenants`, render the tenant table from real `GET /admin/tenants` data (name/id/plan/region/seats/status/created), with mockup-native loading/error/empty states + Playwright e2e + CSS parity; keep the two unbacked columns (`agents`/`runs24`) + the aggregate `TenantsStatsStrip` fixture-gapped with `BackendGapBanner`. **A-6b**: add a new `GET /api/v1/memory/matrix` Cat 3 read aggregate (COUNT GROUP BY over system/tenant/user; role/session gapped; time-scale via `expires_at` for user) + wire `MemoryMatrix` (5×3 grid) + `MemoryPageHeader` (total) to it via a new `useMemoryMatrix` TanStack hook; keep `RecentMemoryOpsCard` + `TimeTravelScrubber` fixture-gapped (no backend op-history producer — deferred). Verify against the mockups via the Mockup-Fidelity DoD (CSS diff empty, `check:mockup-fidelity` baseline unchanged). No DB migration; multi-tenant isolation enforced on the new aggregate.

---

## 2. User Stories

- **US-1 (admin-tenants real list)** — As a platform admin, I want the tenants table to show real tenants from the backend (not 8 fixture rows) so the most data-heavy admin page reflects reality. → re-mount `useAdminTenants` in `AdminTenantsView`, pass real `items` to `TenantsTable`, map `display_name/code/plan/region/seats/state/created_at`.
- **US-2 (admin-tenants honest gaps + states)** — As a reviewer, I want the unbacked columns (`agents`/`runs24`) + the aggregate `TenantsStatsStrip` clearly gapped (not fabricated next to real data) and the table to show loading / error / empty states. → render "—" for `agents`/`runs24`, keep `BackendGapBanner`; `TenantsStatsStrip` stays fixture + banner; mockup-native skeleton/error/empty.
- **US-3 (memory matrix backend)** — As the frontend, I want a `GET /memory/matrix` aggregate returning per-(layer, time_scale) counts + a total so the Memory page can show real entry distribution. → new endpoint mirroring `/memory/recent`, COUNT GROUP BY over system/tenant/user (role/session reported gapped), tenant-isolated.
- **US-4 (memory matrix + header wiring)** — As an operator on the Memory page, I want the 5×3 matrix + the header total to reflect real entry counts. → new `useMemoryMatrix` hook + `memoryService.fetchMatrix`; wire `MemoryMatrix` (real counts for system/tenant/user, gap indicator for role/session) + `MemoryPageHeader` (real total); remove the matrix's Phase-58 banner.
- **US-5 (memory ops widgets honestly gapped)** — As a reviewer, I want `RecentMemoryOpsCard` + `TimeTravelScrubber` to stay on fixtures + `BackendGapBanner` (not fabricated) because no op-history backend exists. → unchanged fixtures, banners retained, documented carryover.
- **US-6 (mockup-fidelity + validation)** — As a reviewer, I want both pages to keep the Mockup-Fidelity Hard Constraint (verbatim classes, `var(--*)`, no new CSS, baseline 50 unchanged) + Vitest (hooks + components) + backend pytest (aggregate + tenant isolation) + Playwright e2e (admin happy/error/empty).

---

## 3. Technical Specifications

### 3.0 Architecture

```
A-6a (frontend-only):
  GET /api/v1/admin/tenants (exists)  ──▶  adminTenantsService.listTenants
        └ TenantListResponse{items: TenantListItem[], total, limit, offset}
                          │  useAdminTenants() (re-mounted; reads query from store)
                          ▼
  AdminTenantsView ──▶ TenantsTable items={data.items}  (name←display_name, id←code, status←state,
        plan/region/seats/created real;  agents/runs24 → "—" + BackendGapBanner)
                     └▶ TenantsStatsStrip  (STILL fixture + BackendGapBanner — no aggregate endpoint)
        + mockup-native loading / error / empty states

A-6b (backend + frontend):
  MemorySystem / MemoryTenant / MemoryUser  ──COUNT GROUP BY──▶  GET /api/v1/memory/matrix (NEW)
        └ MemoryMatrixResponse{cells:[{layer,time_scale,count}], total, gapped_layers:[role,session]}
                          │  useMemoryMatrix()  (TanStack, mirrors useCostSummary)
                          ▼
  MemoryMatrix  (5×3 grid: real counts system/tenant/user; gap indicator role/session)
  MemoryPageHeader  (total ← response.total)
  RecentMemoryOpsCard / TimeTravelScrubber  (UNCHANGED — fixture + BackendGapBanner; no op-history producer)
```

No DB migration. No new SSE event. No CSS / `styles-mockup.css` change.

### 3.1 A-6a admin-tenants wiring (US-1/US-2) — frontend

- `pages/admin-tenants/index.tsx` / `AdminTenantsView.tsx` (EDIT): re-mount `useAdminTenants()`; pass `data.items` + `isLoading` + `isError` + `refetch` down. Remove the "unmounted in this rebuild" comment (replace with a 1-line "wired Sprint 57.73; agents/runs24/stats gapped" note).
- `TenantsTable.tsx` (EDIT): accept `tenants: TenantListItem[]` (+ `isLoading`/`isError`/`onRetry`) as props instead of importing `TENANTS_FIXTURE`. Field map: `name`←`display_name`, `id`←`code`, `plan`←`plan`, `region`←`region`, `seats`←`seats`, `status`←`state` (map state enum → existing status pill), `created`←`created_at` (format). `agents`/`runs24` → render `"—"` (the subtle/`--fg-subtle` token; NOT fixture values). Keep the existing `BackendGapBanner` (`:159`) but reword it to name the 2 gapped columns + the stats strip. Loading → mockup-native skeleton rows (reuse the table's own row markup with `.subtle` placeholders — NOT the shadcn `TableSkeleton`, per D10); error → mockup-native inline error + retry; empty → mockup-native "no tenants" row.
- `TenantsStatsStrip.tsx` (UNCHANGED logic): stays on `STATS_FIXTURE` + a `BackendGapBanner` (add one if absent) — no aggregate-stats endpoint exists. Document as gapped.
- `_fixtures.ts`: keep `STATS_FIXTURE` (still used by the strip); `TENANTS_FIXTURE` becomes unused once the table takes props → **remove it** (Karpathy §3: don't leave orphan fixtures) unless a Vitest still needs it (then move to the test).

### 3.2 A-6b memory matrix endpoint (US-3) — backend (`memory.py`)

- New `GET /api/v1/memory/matrix` mirroring `/recent` (`memory.py:243-262`): deps `current_tenant=Depends(get_current_tenant)` + `_audit=Depends(require_audit_role)` + `db=Depends(get_db_session_with_tenant)` (RLS SET LOCAL).
- New Pydantic models (in the memory schema module alongside `MemoryEntryPage`): `MemoryMatrixCell{layer: MemoryLayer, time_scale: MemoryTimeScale, count: int}`, `MemoryMatrixResponse{cells: list[MemoryMatrixCell], total: int, gapped_layers: list[MemoryLayer]}`.
- Aggregate logic (one `SELECT count() GROUP BY` per wired layer; reuse the `/by-time` time-scale predicate `memory.py:216-222`):
  - `MemorySystem`: `count(*)` → one cell `(system, permanent, n)` (no `expires_at` → all permanent).
  - `MemoryTenant`: `count(*)` (RLS-scoped to current tenant) → `(tenant, permanent, n)`.
  - `MemoryUser`: `GROUP BY` the 3 time-scale buckets via `expires_at` (NULL→permanent; `> now+30d`→quarterly; `<= now+30d & not null`→daily) → up to 3 cells `(user, <scale>, n)`.
  - `gapped_layers = [role, session]` (junction tables, no RLS path, 501) — reported, not queried.
  - `total = Σ cells.count`.
- Tenant isolation: `MemoryTenant`/`MemoryUser` counts are RLS-scoped; `MemorySystem` is global (by design). A cross-tenant test asserts tenant A's tenant/user counts never include tenant B's rows.
- No migration (read-only aggregate).

### 3.3 A-6b memory wiring (US-4/US-5) — frontend

- `services/memoryService.ts` (EDIT): add `fetchMatrix(signal): Promise<MemoryMatrixResponse>` → `GET /api/v1/memory/matrix` (mirror `fetchRecent`).
- `types.ts` (EDIT): add `MemoryMatrixCell` / `MemoryMatrixResponse` (backend vocab `permanent|quarterly|daily`).
- `hooks/useMemoryMatrix.ts` (NEW — first file in the new `memory/hooks/` dir): `useQuery<MemoryMatrixResponse>`, key `["memory","matrix"]`, `queryFn: ({signal}) => memoryService.fetchMatrix(signal)`, `staleTime` per `useCostSummary`. Mirror `useCostSummary.ts:39-45`.
- `MemoryMatrix.tsx` (EDIT): consume `useMemoryMatrix()` instead of `SCOPES`/`TIME_SCALES`/`MEMORY_ENTRIES` fixtures. Render the 5×3 grid: for system/tenant/user use real cell counts (default 0 where a (layer,scale) cell is absent); for role/session render a gap indicator (`gapped_layers`) — `"—"` / a `.subtle` "n/a" with a tooltip-style note, NOT a fabricated number. **Remove the matrix's Phase-58 `BackendGapBanner`** (`:176`) now that it's wired (or reword to "role/session layers gapped — 501"). Mockup-native loading/error/empty.
- `MemoryPageHeader.tsx` (EDIT): consume the matrix `total` instead of `TOTAL_ENTRIES`. (Same `useMemoryMatrix` query — React Query dedups; no second request.)
- `RecentMemoryOpsCard.tsx` + `TimeTravelScrubber.tsx` (UNCHANGED): keep `_fixtures` + `BackendGapBanner` (US-5). Reword their banners to reference the carryover (memory op-history feature).
- `_fixtures.ts` (memory): keep the fixtures still used by RecentOps/TimeTravel; remove the matrix/header fixtures (`SCOPES`/`TIME_SCALES`/`MEMORY_ENTRIES`/`TOTAL_ENTRIES`) if now orphaned (Karpathy §3).

### 3.4 Mockup-fidelity DoD (US-6) — `frontend-mockup-fidelity.md`

- `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → empty (no CSS change; data-only wiring).
- Verbatim mockup classes only; colors via `var(--*)`; no hardcoded hex/oklch (grep guard on the edited components + new hook); no shadcn primitive as a style layer (loading/empty markup is mockup-native, NOT `TableSkeleton`/`EmptyState` — D10).
- `npm run check:mockup-fidelity` → baseline unchanged (`HEX_OKLCH_BASELINE = 50`) — **MUST run** (57.69 D-DAY2-1 lesson).
- computed-style spot-check of the tenants table row + the memory matrix cell vs the mockups (`page-admin.jsx` / `page-governance.jsx`).

### 3.5 Lint / validation

- Frontend: `npm run lint` (NO `--silent` — 57.40 lesson) + `npm run build` (tsc 0) + `npm run test` (Vitest) + `npm run check:mockup-fidelity`.
- **Vitest**: `useMemoryMatrix` hook (mocked fetch → cells/total); `MemoryMatrix` (seeded query → real counts for 3 layers + gap for role/session); `MemoryPageHeader` (real total); `TenantsTable` (props → real rows + "—" for agents/runs24 + loading/error/empty); assert RecentOps/TimeTravel still render fixtures (gapped, unchanged).
- **Backend**: `pytest` for `/memory/matrix` — correct counts per (layer, time_scale); role/session in `gapped_layers`; **cross-tenant isolation** (tenant A's counts exclude tenant B); empty → all zeros/total 0. `mypy src/ --strict` 0; `python scripts/lint/run_all.py` (V2 lints) — `check_llm_sdk_leak` (no LLM import in the aggregate), RLS lint N/A (no new table).
- **Playwright** (admin-tenants): ≥2 e2e (happy: real-shaped mock `**/api/v1/admin/tenants**` → rows render; error/empty: mock 500 / `items:[]` → error/empty states), hermetic API mock.

---

## 4. File Change List

| File | Change |
|------|--------|
| `frontend/src/pages/admin-tenants/index.tsx` | **EDIT** — re-mount note; pass hook data via View (US-1) |
| `frontend/src/features/admin-tenants/components/AdminTenantsView.tsx` | **EDIT** — mount `useAdminTenants`, thread `items`/loading/error to table (US-1/US-2) |
| `frontend/src/features/admin-tenants/components/TenantsTable.tsx` | **EDIT** — take `tenants` prop, field-map real fields, `"—"` for agents/runs24, mockup-native states, reword banner (US-1/US-2) |
| `frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx` | **EDIT (minimal)** — ensure `BackendGapBanner` present (stays fixture; no stats endpoint) (US-2) |
| `frontend/src/features/admin-tenants/_fixtures.ts` | **EDIT** — remove now-orphan `TENANTS_FIXTURE` (keep `STATS_FIXTURE`) (US-1) |
| `backend/src/api/v1/memory.py` (or its schema module) | **EDIT** — new `GET /memory/matrix` + `MemoryMatrixCell`/`MemoryMatrixResponse` + aggregate logic (US-3) |
| `frontend/src/features/memory/services/memoryService.ts` | **EDIT** — `fetchMatrix()` (US-4) |
| `frontend/src/features/memory/types.ts` | **EDIT** — `MemoryMatrixCell`/`MemoryMatrixResponse` (US-4) |
| `frontend/src/features/memory/hooks/useMemoryMatrix.ts` | **NEW** — TanStack hook (US-4) |
| `frontend/src/features/memory/components/MemoryMatrix.tsx` | **EDIT** — wire real counts + gap role/session + remove Phase-58 banner (US-4) |
| `frontend/src/features/memory/components/MemoryPageHeader.tsx` | **EDIT** — real total (US-4) |
| `frontend/src/features/memory/components/RecentMemoryOpsCard.tsx` | **EDIT (minimal)** — reword banner → carryover (US-5; stays fixture) |
| `frontend/src/features/memory/components/TimeTravelScrubber.tsx` | **EDIT (minimal)** — reword banner → carryover (US-5; stays fixture) |
| `frontend/src/features/memory/_fixtures.ts` | **EDIT** — remove now-orphan matrix/header fixtures (keep ops/timeline) (US-4) |
| Tests | **NEW/extend** — backend `test_memory_matrix.py` (counts + isolation); Vitest for hook + MemoryMatrix + MemoryPageHeader + TenantsTable; Playwright admin-tenants e2e (US-6) |

**No DB migration. No new SSE event / wire-type / codegen. No CSS / `styles-mockup.css` change. No new dependency.** RecentOps + TimeTravel widgets stay fixture-gapped (deferred carryover).

---

## 5. Acceptance Criteria

- **A-6a**: the tenants table renders real tenants from `GET /admin/tenants` (name/id/plan/region/seats/status/created); `agents`/`runs24` show `"—"` (not fabricated) and the `BackendGapBanner` names the gapped columns + the stats strip; loading/error/empty states present (mockup-native); `TenantsStatsStrip` stays fixture + banner. Playwright happy + error/empty pass.
- **A-6b backend**: `GET /memory/matrix` returns per-(layer, time_scale) counts for system/tenant/user + `total` + `gapped_layers=[role,session]`; tenant-isolated (cross-tenant test green); empty → total 0; `mypy src/ --strict` 0; V2 lints green.
- **A-6b frontend**: `MemoryMatrix` shows real counts for the 3 wired layers + a gap indicator for role/session (no fabricated numbers); the matrix Phase-58 banner is removed; `MemoryPageHeader` shows the real total; `RecentMemoryOpsCard` + `TimeTravelScrubber` unchanged (fixture + banner).
- **Mockup-fidelity**: `diff styles.css styles-mockup.css` empty; verbatim classes + `var(--*)`; no hardcoded hex/oklch (grep guard); `check:mockup-fidelity` baseline 50 unchanged; no shadcn-token residue introduced.
- `npm run lint` (no `--silent`) + `npm run build` tsc 0; Vitest green; backend pytest green (incl. isolation). No CSS change.

---

## 6. Deliverables

- [ ] A-6a: `useAdminTenants` re-mounted; `TenantsTable` real fields + `"—"` gaps + mockup-native states; banner reworded; orphan `TENANTS_FIXTURE` removed (US-1/US-2)
- [ ] A-6a: Playwright e2e (happy + error/empty) (US-6)
- [ ] A-6b backend: `GET /memory/matrix` + Pydantic models + aggregate + tenant-isolation test (US-3)
- [ ] A-6b frontend: `useMemoryMatrix` hook + `fetchMatrix` + types; `MemoryMatrix` + `MemoryPageHeader` wired; matrix banner removed; orphan matrix/header fixtures removed (US-4)
- [ ] A-6b: RecentOps + TimeTravel banners reworded → carryover; widgets unchanged (US-5)
- [ ] Vitest (hook + MemoryMatrix + MemoryPageHeader + TenantsTable) (US-6)
- [ ] Mockup-fidelity DoD pass (CSS diff empty + `check:mockup-fidelity` 50 + computed-style spot-check) (US-6)
- [ ] CHANGE-041 + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: **`mixed-multidomain-bundle` (0.65)** — three independent tracks (admin-tenants frontend wiring + memory backend aggregate + memory frontend wiring) with heavy pattern reuse (hook mirrors `useCostSummary`; endpoint mirrors `/memory/recent`; component wiring mirrors prior tenant-settings tabs). **Agent-delegated: yes** — sequential `code-implementer` agents (Track A admin frontend, Track B memory backend, Track C memory frontend); parent independently re-verifies (reads the aggregate query for correctness + tenant isolation, re-mounts logic, runs `check:mockup-fidelity` + pytest + Vitest). `agent_factor` **`mixed-multidomain-bundle-mechanical` 0.45** (the rolled-back tier-3 baseline since Sprint 57.59; this bundle is mostly mechanical pattern-reuse with one genuine-design component — the matrix aggregate).

> Bottom-up est ~15 hr → class-calibrated commit ~9.75 hr (mult 0.65) → agent-adjusted commit ~4.4 hr (agent_factor 0.45).

Caveat (carried 57.63-57.72): agent-delegated sprints have no clean wall-clock (`AD-Calibration-AgentDelegated-WallClock-Measure`; this would be the **11th consecutive**). `mixed-multidomain-bundle-mechanical` 0.45 has 2 below-band data points (57.58=0.49, 57.59=0.34) — per the 57.59 escalation note, if this 1st validation under 0.45 is also < 0.7 → escalate 0.30 OR fold into `mechanical-pattern-reuse-heavy`. Record caveated; re-evaluate in retro Q2.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Over-promising the memory backend** (ops-timeline / time-travel have NO producer) | Hard-scoped OUT this sprint (D7/D8); RecentOps + TimeTravel stay fixture + banner; documented as a separate Cat 3 write-path-instrumentation carryover. Do NOT fabricate op rows from entries (AP-4) |
| **Mixing real + fake per-row** (admin agents/runs24) | Render `"—"` for unbacked columns next to real data — NOT fixture values; `BackendGapBanner` names the gap (honest AP-2) |
| **shadcn-token residue via shared skeleton/error** (D10) | Use mockup-native loading/error/empty markup (mockup classes + `var(--*)`), NOT `TableSkeleton`/`EmptyState`; grep guard + `check:mockup-fidelity` baseline 50 |
| **Mockup-fidelity drift** (10-sprint drift root cause) | Data-only change; CSS diff empty; verbatim classes; `check:mockup-fidelity` MUST run (57.69 lesson) |
| **Matrix time-scale only real for user** | system/tenant → permanent column (semantically correct — they don't expire); role/session gapped via `gapped_layers`; frontend renders the honest grid, no fabricated quarterly/daily for system/tenant |
| **Multi-tenant leak on the aggregate** (`.claude/rules/multi-tenant-data.md`) | `get_db_session_with_tenant` (RLS SET LOCAL) for tenant/user counts; system is global by design; explicit cross-tenant isolation pytest |
| **`total` undercounts vs mockup 6,514** | Expected (role/session gapped); not a bug — the header shows the real wired-layer total |
| **17.md single-source** | New `/matrix` follows the Sprint-57.12 facade precedent (router + FE service, not a 17.md cross-category ABC); noted, not expanding scope to backfill the pre-existing facade rows |
| **TanStack double-fetch** (matrix used by 2 components) | Same `useMemoryMatrix` query key → React Query dedups; one request |
| **Risk Class C** (module singleton across test loops) | Backend matrix test uses the standard `get_db_session` override + per-suite reset if it touches a singleton (it shouldn't — pure read) |

---

## 9. Out of Scope (this sprint; carryover)

- **Memory ops-timeline + time-travel backend** (`RecentMemoryOpsCard` / `TimeTravelScrubber`) — NO backend producer today (memory `write()`/`evict()` emit zero audit rows, no version history). Backing them needs new write-path instrumentation across Cat 3 (5 layer `write()`/`evict()` + the `memory_write`/`memory_extract` tools emitting `append_audit(resource_type="memory_*")`, OR a new append-only `memory_ops` table), forward-only (no backfill). Separate larger feature → **carryover `AD-Memory-OpsHistory-Backend`**. Widgets stay fixture + banner.
- **admin-tenants `agents`/`runs24` columns + `TenantsStatsStrip` aggregate** — need per-tenant agent-count / 24h-run-count + an aggregate-stats endpoint that don't exist. → **carryover `AD-AdminTenants-Stats-Aggregate-Endpoint`** (a backend-paired feature). Stay `"—"` / fixture + banner.
- **memory role/session layers** — return 501 (junction tables, no RLS path); matrix reports them via `gapped_layers`. Backend layer support is the A-1/A-3 memory-backend track. Stays gapped.
- **memory `/scope` + `/by-time` deep wiring** — the matrix uses neither; per-cell drill-down (click a matrix cell → entry list via `fetchByScope`/`fetchByTime`) is a follow-up. → carryover.
- **REST-type codegen for memory/admin DTOs** (parallel to A-5b for events) — hand-written service DTOs carry the same drift risk; out of scope. → carryover.
- **Other Area-A**: A-5c Trace/Memory Inspector tabs (need their producers), the FE `/subagents` page wiring (57.70 carryover). Two high-priority capstone key chains remain untouched: C-11 (real-LLM enablement) + the billing-correctness bundle (B-7/B-8/C-15).
