# Sprint 57.74 Plan — admin-tenants stats aggregate endpoint + per-row agents/runs24 + stats-strip wiring (closes AD-AdminTenants-Stats-Aggregate-Endpoint)

**Purpose**: Close the Area-A carryover `AD-AdminTenants-Stats-Aggregate-Endpoint` left by Sprint 57.73 (A-6a). 57.73 wired the admin-tenants **list** to real `GET /api/v1/admin/tenants`, but two per-row columns (`Agents`, `Runs · 24h`) render a literal `"—"` and the aggregate `TenantsStatsStrip` still consumes `STATS_FIXTURE` — there is **no backend aggregate**. This sprint adds a new fleet-wide `GET /api/v1/admin/tenants/stats` (platform-admin, cross-tenant aggregate) returning both the **fleet aggregate** (for the strip) and a **per-tenant map** (agents + 24h-runs, for the two table columns), then wires the strip + table to it. The 3 backable stats (Active tenants / Total seats / Agents deployed) show real values; the un-backable bits (the `Anomalies` stat + every stat's `delta`/trend arrow — no historical source) stay an **honest gap** (placeholder + `BackendGapBanner`, no fabrication). This is a **backend+frontend feature-continuation sprint** (the endpoint mirrors the Sprint-57.73 `/memory/matrix` aggregate + `cost_summary` deps pattern; no new domain) → **no design note**; the frontend Mockup-Fidelity Hard Constraint applies (`docs/rules-on-demand/frontend-mockup-fidelity.md`).
**Category / Scope**: Admin API aggregate (platform-layer admin read) + Frontend real-data wiring (admin-tenants); Phase 57.74
**Status**: Draft — code execution gated on Day-0 GO (Step 2.5). Ground-truth already gathered via a Day-0 researcher pass (see §0).
**Source**: A-6 deep-analysis `claudedocs/5-status/frontend-real-data-wiring-analysis-20260531.md` + Sprint 57.73 carryover `AD-AdminTenants-Stats-Aggregate-Endpoint` (`sprint-57-73-plan.md` §9) + **Day-0 ground-truth researcher pass (2026-06-03)** (agent_catalog / sessions / admin endpoint / frontend shapes) + user AskUserQuestion decisions 2026-06-03 (**scope = strip + per-row columns**; **Runs·24h = sessions started in last 24h**; **un-backable Anomalies/deltas = honest gap**)

> **Modification History**
> - 2026-06-03: Initial creation — new `GET /admin/tenants/stats` fleet aggregate + per-tenant agents/runs24 map; wire `TenantsStatsStrip` (3 real stats) + `TenantsTable` (agents/runs24 columns); Anomalies + deltas honest-gapped; backend+frontend feature-continuation (no design note)

---

## 0. Background

`AD-AdminTenants-Stats-Aggregate-Endpoint` is the A-6a deferral from Sprint 57.73: the admin-tenants page shipped real per-row identity data but left `agents`/`runs24` as `"—"` and the stats strip on fixtures, because no aggregate endpoint existed. The user selected this carryover (#3 in the "process all carryover except A-4 Tier 2" program) and locked scope at Day-0: **fill both** the stats strip and the two per-row columns; **Runs·24h = sessions started in the last 24h**; **honest gap** for the un-backable Anomalies stat + trend deltas.

### Day-0 ground-truth (researcher pass, main `12324e50`)

- **D1 — agents-count source**: `agent_catalog` (`infrastructure/db/models/agent_catalog.py:71`, `AgentCatalog(Base, TenantScopedMixin)`, added Sprint 57.70 / migration `0023`). `tenant_id` (NOT NULL via mixin), `is_active: bool` default TRUE (`:104`), `status: str` default `'live'` (`:92`). **Use `is_active`, NOT `status`**, for "deployed". `idx_agent_catalog_tenant` (`:118`) covers the GROUP BY. Per-tenant: `SELECT tenant_id, count(*) FROM agent_catalog WHERE is_active GROUP BY tenant_id`. Fleet: `count(*) WHERE is_active`.
- **D2 — runs-24h source**: table = **`sessions`** (`infrastructure/db/models/sessions.py:74`, `Session`, **NOT partitioned** per `:72` docstring — `messages`/`message_events` are partitioned, the session root is not, so no partition concern). `tenant_id` via `TenantScopedMixin`; timestamp col = **`started_at`** (`:114`, `server_default=func.now()`). Per-tenant: `SELECT tenant_id, count(*) FROM sessions WHERE started_at >= now() - interval '24 hours' GROUP BY tenant_id`. `idx_sessions_tenant_user` (tenant_id, user_id) partially helps; a 24h window scan is acceptable at admin scale.
- **D3 — existing endpoint**: `backend/src/api/v1/admin/tenants.py:227` `GET ""` `list_tenants` → `TenantListResponse{items, total, limit, offset}` (`:218`), item = `TenantListItem` (`:194`, 12 fields incl. `state`/`seats`). Auth dep = `require_admin_platform_role` (`:230`, `platform_layer/identity/auth.py:142` — platform-admin, returns user_id, **NO tenant filter** → cross-tenant aggregate allowed). `TenantListItem` has **no** `agents`/`runs24` fields. The list endpoint is paged + intentionally lean (`:195-200` docstring) → **do NOT pollute it**.
- **D4 — endpoint decision**: a NEW `GET /admin/tenants/stats` (in `admin/tenants.py`) is cleaner than extending `list_tenants` (avoids per-row joins on the lean paged list + keeps 57.73's just-stabilized wiring untouched). Deps: `dependencies=[Depends(require_admin_platform_role)]` + `db: AsyncSession = Depends(get_db_session)` (plain session — fleet-wide, no RLS tenant scope, mirrors `list_tenants`).
- **D5 — frontend shapes**: `TenantsTable.tsx:124-125` columns `Agents` + `Runs · 24h` currently render `GAP_PLACEHOLDER` ("—"). `TenantListItem` (`types.ts:37`) has NO agents/runs24 fields (those are per-tenant stats, not list fields → carried via a separate map prop). `TenantsStatsStrip.tsx` consumes `STATS_FIXTURE` (`_fixtures.ts:36`): 4 stats each `{label: string, value: string, delta: string, deltaDir: "up"|"down"}` — labels `Active tenants` / `Total seats` / `Agents deployed` / `Anomalies`. `useAdminTenants.ts` wraps `listTenants` only (no stats query).
- **D6 — stat mapping + gaps** (user-locked):

  | Strip stat | Backend source | This sprint |
  |------------|----------------|-------------|
  | `Active tenants` | `count(tenants WHERE state = 'active')` | **REAL** |
  | `Total seats` | `sum(tenants.seats)` | **REAL** |
  | `Agents deployed` | `count(agent_catalog WHERE is_active)` | **REAL** |
  | `Anomalies` | ❌ no source | **GAP** (placeholder + banner, no fabrication) |
  | per-stat `delta`/`deltaDir` (trend) | ❌ no historical/period source | **GAP** (no arrow / subtle placeholder) |
  | table `Agents` column | per-tenant `agent_catalog` count map | **REAL** |
  | table `Runs · 24h` column | per-tenant `sessions` 24h count map | **REAL** |

- **D7 — precedent + conventions**: mirror Sprint-57.73 `GET /memory/matrix` (`memory.py:418`, inline Pydantic response, GROUP BY aggregate) for the response-model + aggregate style, and `list_tenants` for the deps (`require_admin_platform_role` + `get_db_session`). New TanStack hook mirrors `useAdminTenants.ts` / `useCostSummary.ts`. The admin-tenants stats endpoint is NOT a 17.md cross-category ABC (it's an admin read facade, same precedent as `/memory/matrix`, `cost_summary`). **No DB migration** (read aggregate over existing tables) → no Prong 3 schema verify.
- **D8 — mockup-fidelity infra**: shadcn-utility residue grep = 0 in `features/admin-tenants` (verbatim mockup classes + inline `style={{}}` with `eslint-disable no-restricted-syntax` headers). A DATA-only wiring change won't touch CSS. Loading/error/empty for the strip must be **mockup-native** (NOT shared `TableSkeleton`/`EmptyState`, which carry shadcn tokens — same D10 rule as 57.73). `check:mockup-fidelity` `HEX_OKLCH_BASELINE = 50` must stay unchanged (57.69 D-DAY2-1 lesson: a frontend sprint MUST run the gate; Before-Commit item 7). Mockup: `reference/design-mockups/page-admin.jsx` (tenants stats strip + table).

**Net**: (1) NEW `GET /admin/tenants/stats` returning `{fleet, per_tenant, gapped}`; (2) wire `TenantsStatsStrip` to `fleet` (3 real stats; Anomalies + deltas honest-gapped); (3) fill `TenantsTable` `agents`/`runs24` columns from the `per_tenant` map; (4) `useAdminTenantsStats` hook + service + types. No DB migration, no CSS change.

---

## 1. Sprint Goal

Close `AD-AdminTenants-Stats-Aggregate-Endpoint`: add a new fleet-wide `GET /api/v1/admin/tenants/stats` (platform-admin, cross-tenant) returning the fleet aggregate (`active_tenants` = count of `state='active'`, `total_seats` = Σ`seats`, `agents_deployed` = count of `agent_catalog WHERE is_active`) + a per-tenant map (`agents` = active-agent count, `runs24` = sessions started in the last 24h) + a `gapped` list naming the un-backable bits. Wire `TenantsStatsStrip` to the fleet aggregate (3 real stats; `Anomalies` + every `delta`/trend arrow stay honest-gapped with `BackendGapBanner`, no fabrication) and fill `TenantsTable`'s `Agents` + `Runs · 24h` columns from the per-tenant map (real numbers; `0` rendered as the subtle "—" only when a tenant has no agents/runs). Add `useAdminTenantsStats` (TanStack) + `adminTenantsService.fetchStats` + types. Verify against the mockup via the Mockup-Fidelity DoD (CSS diff empty, `check:mockup-fidelity` baseline 50 unchanged). No DB migration; platform-admin gate enforced (non-admin → 403).

---

## 2. User Stories

- **US-1 (fleet stats endpoint)** — As the admin-tenants frontend, I want `GET /admin/tenants/stats` to return the fleet aggregate so the stats strip shows real numbers. → new endpoint, `require_admin_platform_role`, `count`/`sum` over `tenants` + `agent_catalog`.
- **US-2 (per-tenant agents/runs24 map)** — As the frontend, I want per-tenant `agents` + `runs24` counts so the table's two gapped columns show real values. → same endpoint returns `per_tenant: [{tenant_id, agents, runs24}]` via two GROUP BY queries (agent_catalog `is_active`; sessions `started_at >= now()-24h`).
- **US-3 (stats strip wiring + honest gaps)** — As a platform admin, I want the stats strip to show real Active tenants / Total seats / Agents deployed, with the un-backable Anomalies stat + trend deltas clearly gapped (not fabricated). → wire `TenantsStatsStrip` to `fleet`; `Anomalies` + `delta`/`deltaDir` → placeholder + `BackendGapBanner`.
- **US-4 (table columns wiring)** — As a platform admin, I want the Agents + Runs·24h table columns filled from real per-tenant counts (not "—"). → `TenantsTable` takes a `statsByTenant` map prop, renders real counts (subtle "—" only for a genuine 0/absent tenant).
- **US-5 (hook + service + types)** — As the frontend, I want a `useAdminTenantsStats` TanStack hook + `fetchStats` service + typed response. → new hook (key `["admin-tenants","stats"]`), service method, `TenantsStatsResponse`/`FleetStats`/`PerTenantStat` types.
- **US-6 (auth + isolation correctness)** — As a security reviewer, I want the endpoint gated to platform admins (non-admin → 403) and the counts correct + cross-tenant by design (fleet-wide). → pytest: counts correctness, per-tenant map, non-admin 403, empty fleet → zeros.
- **US-7 (mockup-fidelity + validation)** — As a reviewer, I want the page to keep the Mockup-Fidelity Hard Constraint (verbatim classes, `var(--*)`, no new CSS, baseline 50 unchanged) + Vitest (hook + strip + table) + backend pytest + Playwright e2e (strip real values + table columns filled).

---

## 3. Technical Specifications

### 3.0 Architecture

```
tenants (identity.py: state, seats)  ──count/sum──┐
agent_catalog (is_active)  ──count + GROUP BY──────┤
sessions (started_at >= now()-24h) ──GROUP BY──────┤
                                                   ▼
                       GET /api/v1/admin/tenants/stats (NEW)
                         deps: [require_admin_platform_role] + get_db_session (fleet-wide, no RLS scope)
                         └ TenantsStatsResponse{
                               fleet: {active_tenants, total_seats, agents_deployed},
                               per_tenant: [{tenant_id, agents, runs24}],
                               gapped: ["anomalies", "deltas"]
                           }
                                       │  useAdminTenantsStats()  (TanStack, mirrors useAdminTenants)
                                       ▼
   TenantsStatsStrip  (Active tenants / Total seats / Agents deployed = real;
                       Anomalies + every delta/trend arrow = honest gap + BackendGapBanner)
   TenantsTable  (Agents ← per_tenant map; Runs·24h ← per_tenant map; subtle "—" only for genuine 0/absent)
```

No DB migration. No new SSE event / wire-type / codegen. No CSS / `styles-mockup.css` change.

### 3.1 Stats endpoint (US-1/US-2/US-6) — backend (`admin/tenants.py`)

- New `GET /admin/tenants/stats` (place ABOVE the `/{tenant_id}` path routes if any, to avoid path-param capture; `/stats` is a static segment so order-safe, but verify). Deps: `dependencies=[Depends(require_admin_platform_role)]` + `db: AsyncSession = Depends(get_db_session)` (plain session, fleet-wide — mirrors `list_tenants`; **NOT** `get_db_session_with_tenant`, this is intentionally cross-tenant).
- New Pydantic models (inline in `tenants.py` alongside `TenantListResponse`, mirroring `/memory/matrix` inline style):
  - `FleetStats{active_tenants: int, total_seats: int, agents_deployed: int}`
  - `PerTenantStat{tenant_id: UUID, agents: int, runs24: int}`
  - `TenantsStatsResponse{fleet: FleetStats, per_tenant: list[PerTenantStat], gapped: list[str]}`
- Aggregate logic (4 queries, all read-only):
  - `active_tenants` = `select(func.count()).select_from(Tenant).where(Tenant.state == TenantState.ACTIVE)`
  - `total_seats` = `select(func.coalesce(func.sum(Tenant.seats), 0))` (coalesce → 0 on empty fleet)
  - `agents_deployed` = `select(func.count()).select_from(AgentCatalog).where(AgentCatalog.is_active.is_(True))`
  - per-tenant agents map = `select(AgentCatalog.tenant_id, func.count()).where(is_active).group_by(tenant_id)`
  - per-tenant runs24 map = `select(Session.tenant_id, func.count()).where(Session.started_at >= now()-24h).group_by(tenant_id)`
  - merge the two maps into `per_tenant: [{tenant_id, agents, runs24}]` (union of tenant_ids appearing in either; missing side → 0). Use a tz-aware cutoff `datetime.now(timezone.utc) - timedelta(hours=24)` (NOT a DB `now()` literal string).
  - `gapped = ["anomalies", "deltas"]` (reported, not computed).
- `Tenant` ORM lives in `identity.py` (`09-db-schema-design.md §Group 1 Identity & Tenancy`); `state` is `TenantState` enum, `seats` int (added 57.46/57.47). `AgentCatalog` in `agent_catalog.py`; `Session` in `sessions.py`.
- No migration (read-only aggregate). No RLS scope (platform-admin fleet-wide, like `list_tenants`).

### 3.2 Stats strip wiring (US-3) — frontend

- `TenantsStatsStrip.tsx` (EDIT): accept a `fleet: FleetStats | undefined` (+ `isLoading`/`isError`) prop instead of importing `STATS_FIXTURE`. Render the 3 real stats: `Active tenants` ← `fleet.active_tenants`, `Total seats` ← `fleet.total_seats`, `Agents deployed` ← `fleet.agents_deployed` (format numbers per the mockup). `Anomalies` → subtle placeholder (`"—"` / `--fg-subtle`, NOT a fabricated number). Every stat's `delta`/trend arrow → **omit or subtle placeholder** (no historical source) — keep the mockup's stat-card layout (verbatim classes) but render no arrow / a `.subtle` em-dash where the delta was. Add/keep a `BackendGapBanner` naming the gapped bits (`Anomalies` + trend deltas). Mockup-native loading/error states (subtle placeholders in the existing card markup; NOT shadcn skeleton).
- `_fixtures.ts` (EDIT): `STATS_FIXTURE` becomes orphan once the strip takes props → **remove it** (Karpathy §3) unless a Vitest still needs it (then inline in the test).

### 3.3 Table columns wiring (US-4) — frontend

- `TenantsTable.tsx` (EDIT): accept an optional `statsByTenant?: Map<string, {agents: number; runs24: number}>` (or a plain record keyed by tenant id) prop. For the `Agents` + `Runs · 24h` cells (`:124-125`), look up the row's tenant id in the map: render the real count; render the subtle `"—"` (the existing `GAP_PLACEHOLDER`) only when the tenant is absent from the map OR count is 0 (genuine zero shows "—" to match the mockup's empty-cell convention — OR render `0`; decide at Day-0 spot-check vs mockup). **Reword the existing `BackendGapBanner`** (`:159` from 57.73, which named agents/runs24 + the stats strip) to drop the now-backed agents/runs24 mention and reference only the remaining strip gaps (Anomalies/deltas) — OR remove it from the table if the strip now owns the gap banner (decide to avoid double-banner). Field map + identity columns from 57.73 UNCHANGED.
- `AdminTenantsView.tsx` (EDIT): mount `useAdminTenantsStats()`; pass `data.fleet` (+ loading/error) to `TenantsStatsStrip` and build the `statsByTenant` map from `data.per_tenant` → pass to `TenantsTable`. Keep the 57.73 `useAdminTenants()` list wiring intact (two independent queries; React Query dedups each).

### 3.4 Hook + service + types (US-5) — frontend

- `services/adminTenantsService.ts` (or wherever `listTenants` lives) (EDIT): add `fetchStats(signal): Promise<TenantsStatsResponse>` → `GET /api/v1/admin/tenants/stats` (mirror `listTenants`).
- `types.ts` (EDIT): add `FleetStats`, `PerTenantStat`, `TenantsStatsResponse` (backend vocab; `tenant_id` string).
- `hooks/useAdminTenantsStats.ts` (NEW): `useQuery<TenantsStatsResponse>`, key `["admin-tenants","stats"]`, `queryFn: ({signal}) => adminTenantsService.fetchStats(signal)`, `staleTime` per `useAdminTenants`. Mirror `useAdminTenants.ts:34-41`.

### 3.5 Mockup-fidelity DoD (US-7) — `frontend-mockup-fidelity.md`

- `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → empty (no CSS change; data-only wiring).
- Verbatim mockup classes only; colors via `var(--*)`; no hardcoded hex/oklch (grep guard on the edited components + new hook); no shadcn primitive as a style layer (loading/empty markup mockup-native).
- `npm run check:mockup-fidelity` → baseline unchanged (`HEX_OKLCH_BASELINE = 50`) — **MUST run** (57.69 D-DAY2-1 lesson / Before-Commit item 7).
- computed-style spot-check of a stats-strip card + a table `Agents`/`Runs·24h` cell vs `page-admin.jsx`.

### 3.6 Lint / validation

- Frontend: `npm run lint` (NO `--silent` — 57.40 lesson) + `npm run build` (tsc 0) + `npm run test` (Vitest) + `npm run check:mockup-fidelity`.
- **Vitest**: `useAdminTenantsStats` (mocked fetch → fleet/per_tenant/gapped); `TenantsStatsStrip` (seeded fleet → 3 real values + Anomalies/delta gap markers + banner); `TenantsTable` (statsByTenant map → real agents/runs24, "—" for absent tenant + loading/error/empty unchanged from 57.73).
- **Backend**: `pytest test_admin_tenants_stats.py` — fleet counts correct (seed N active tenants / seats / agents); per_tenant map correct (agents from agent_catalog, runs24 from sessions in window, sessions outside 24h excluded); non-platform-admin → 403; empty fleet → zeros + empty per_tenant + gapped present. `mypy src/ --strict` 0; `python scripts/lint/run_all.py` (V2 lints) — `check_llm_sdk_leak` (no LLM import), RLS lint N/A (no new table). **Risk Class C** (Sprint 57.74 codified reinforcement): the new endpoint adds DB calls to the admin router — ensure the test suite's `get_db_session` override covers it (per the just-codified `AD-Source-DB-Call-Test-Isolation`).
- **Playwright** (admin-tenants): extend the 57.73 spec — mock `**/api/v1/admin/tenants/stats` (happy: fleet + per_tenant → strip shows real values + table columns filled; error: 500 → strip mockup-native error / table "—"), hermetic.

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/admin/tenants.py` | **EDIT** — new `GET /admin/tenants/stats` + `FleetStats`/`PerTenantStat`/`TenantsStatsResponse` + 4-query aggregate + per-tenant map merge (US-1/US-2/US-6) |
| `frontend/src/features/admin-tenants/services/adminTenantsService.ts` | **EDIT** — `fetchStats()` (US-5) |
| `frontend/src/features/admin-tenants/types.ts` | **EDIT** — `FleetStats`/`PerTenantStat`/`TenantsStatsResponse` (US-5) |
| `frontend/src/features/admin-tenants/hooks/useAdminTenantsStats.ts` | **NEW** — TanStack hook (US-5) |
| `frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx` | **EDIT** — take `fleet` prop, 3 real stats, Anomalies + deltas honest-gap + banner, mockup-native states (US-3) |
| `frontend/src/features/admin-tenants/components/TenantsTable.tsx` | **EDIT** — take `statsByTenant` map prop, fill agents/runs24 columns, reword/relocate gap banner (US-4) |
| `frontend/src/features/admin-tenants/components/AdminTenantsView.tsx` | **EDIT** — mount `useAdminTenantsStats`, thread `fleet` to strip + `per_tenant` map to table (US-3/US-4) |
| `frontend/src/features/admin-tenants/_fixtures.ts` | **EDIT** — remove now-orphan `STATS_FIXTURE` (keep any still-used) (US-3) |
| Tests | **NEW/extend** — backend `test_admin_tenants_stats.py` (counts + per-tenant map + 403 + empty); Vitest for hook + strip + table; extend Playwright admin-tenants e2e (US-7) |

**No DB migration. No new SSE event / wire-type / codegen. No CSS / `styles-mockup.css` change. No new dependency.** `Anomalies` stat + trend deltas stay honest-gapped (no fabrication).

---

## 5. Acceptance Criteria

- **US-1/US-2 backend**: `GET /admin/tenants/stats` returns `fleet{active_tenants, total_seats, agents_deployed}` (correct counts), `per_tenant[{tenant_id, agents, runs24}]` (agents from `agent_catalog WHERE is_active`; runs24 from `sessions WHERE started_at >= now()-24h`; sessions outside the window excluded), and `gapped=["anomalies","deltas"]`. `mypy src/ --strict` 0; V2 lints green.
- **US-6 auth**: non-platform-admin → 403; empty fleet → zeros + empty `per_tenant`.
- **US-3 strip**: `TenantsStatsStrip` shows real `Active tenants`/`Total seats`/`Agents deployed`; `Anomalies` + every trend delta show a subtle gap marker (NOT a fabricated number/arrow); `BackendGapBanner` names the gapped bits.
- **US-4 table**: `Agents` + `Runs · 24h` columns show real per-tenant counts; subtle "—" only for a genuinely absent/zero tenant; identity columns + states from 57.73 unchanged; no double gap-banner.
- **US-5**: `useAdminTenantsStats` hook + `fetchStats` + types; React Query dedups; list query (57.73) untouched.
- **Mockup-fidelity**: `diff styles.css styles-mockup.css` empty; verbatim classes + `var(--*)`; no hardcoded hex/oklch (grep guard); `check:mockup-fidelity` baseline 50 unchanged; no shadcn-token residue.
- `npm run lint` (no `--silent`) + `npm run build` tsc 0; Vitest green; backend pytest green (counts + 403 + isolation-by-design). No CSS change.

---

## 6. Deliverables

- [ ] Backend `GET /admin/tenants/stats` + Pydantic models + 4-query aggregate + per-tenant map merge (US-1/US-2)
- [ ] Backend pytest: fleet counts + per-tenant map + runs24 window + non-admin 403 + empty fleet (US-6)
- [ ] `useAdminTenantsStats` hook + `fetchStats` service + types (US-5)
- [ ] `TenantsStatsStrip` wired (3 real stats; Anomalies + deltas honest-gapped + banner; mockup-native states) (US-3)
- [ ] `TenantsTable` agents/runs24 columns filled from per-tenant map; gap banner reworded/relocated (US-4)
- [ ] `AdminTenantsView` mounts stats hook; orphan `STATS_FIXTURE` removed (US-3/US-4)
- [ ] Vitest (hook + strip + table) + extended Playwright e2e (US-7)
- [ ] Mockup-fidelity DoD pass (CSS diff empty + `check:mockup-fidelity` 50 + computed-style spot-check) (US-7)
- [ ] CHANGE-042 + progress.md + retrospective.md; close `AD-AdminTenants-Stats-Aggregate-Endpoint`

---

## 7. Workload Calibration

Scope class: **`mixed-multidomain-bundle` (0.65)** — backend aggregate endpoint + frontend strip wiring + frontend table-column wiring, heavy pattern reuse (endpoint mirrors `/memory/matrix` + `list_tenants` deps; hook mirrors `useAdminTenants`; component wiring mirrors 57.73). **Agent-delegated: yes** — sequential `code-implementer` agents (Track A backend `/stats` endpoint + tests; Track B frontend hook/service/types + strip + table + AdminTenantsView + Vitest/e2e); parent independently re-verifies (reads the 4-query aggregate + per-tenant merge for correctness, the 403 gate, runs `check:mockup-fidelity` + pytest + Vitest — per Before-Commit item 7). `agent_factor` **`mixed-multidomain-bundle-mechanical` 0.45** (tier-3 baseline since Sprint 57.59).

> Bottom-up est ~10 hr → class-calibrated commit ~6.5 hr (mult 0.65) → agent-adjusted commit ~2.9 hr (agent_factor 0.45).

Caveat (carried 57.63-57.73): agent-delegated sprints have no clean wall-clock (`AD-Calibration-AgentDelegated-WallClock-Measure`; this would be the **12th consecutive**; codified as a carryover this session). `mixed-multidomain-bundle-mechanical` 0.45 prior points (57.58=0.49, 57.59=0.34) sit below band; per the 57.59 escalation note, if this validation under 0.45 is also < 0.7 → escalate 0.30 OR fold into `mechanical-pattern-reuse-heavy`. Record caveated; re-evaluate in retro Q2.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Fabricating the un-backable bits** (Anomalies stat + trend deltas) | Hard-scoped OUT: render subtle placeholders + `BackendGapBanner`, never a fake number/arrow (AP-4 / honest AP-2, user-locked) |
| **Path-param capture** (`/stats` vs `/{tenant_id}`) | `/stats` is a static segment; register it explicitly and verify route order at Day-0 (grep the router for a `/{tenant_id}` GET that could shadow it) |
| **Per-tenant map size** (57.70 seeded ~2533 tenants) | The `per_tenant` map only includes tenants appearing in the agent/session GROUP BY (most tenants have agents from the seed → ~2533 small rows ≈ tens of KB; acceptable at admin scale). Page-scoped trimming is a future optimization (noted §9), not this sprint |
| **`now()` vs tz-aware cutoff** | Use `datetime.now(timezone.utc) - timedelta(hours=24)` as a bound param, not a DB-string `now()`; `started_at` is tz-aware (`server_default=func.now()`) |
| **shadcn-token residue via shared skeleton** (D8) | Strip loading/error uses mockup-native markup (mockup classes + `var(--*)`), NOT `TableSkeleton`/`EmptyState`; grep guard + `check:mockup-fidelity` baseline 50 |
| **Mockup-fidelity drift** (10-sprint drift root cause) | Data-only change; CSS diff empty; verbatim classes; `check:mockup-fidelity` MUST run (57.69 lesson / Before-Commit item 7) |
| **Double gap-banner** (table banner from 57.73 + new strip banner) | Decide ownership at Day-0: strip owns the Anomalies/deltas banner; table banner reworded to drop now-backed agents/runs24 (or removed) — single honest banner per gap |
| **Admin-role gate** (`.claude/rules/multi-tenant-data.md`) | `require_admin_platform_role` (fleet-wide by design, like `list_tenants`); explicit non-admin → 403 pytest; plain `get_db_session` (no RLS scope — intentional cross-tenant aggregate) |
| **Risk Class C** (DB-call test isolation — just codified `AD-Source-DB-Call-Test-Isolation`) | The new endpoint adds DB calls; ensure the admin-tenants test suite's `get_db_session` override / autouse session fixture covers it |
| **Double-fetch** (stats used by strip + table) | Same `useAdminTenantsStats` query key → React Query dedups; one request |

---

## 9. Out of Scope (this sprint; carryover)

- **`Anomalies` stat backend** — no source today; would need a definition (e.g. verification failures / guardrail blocks / SLA breaches per tenant) + an aggregate query. Honest-gapped this sprint. → carryover `AD-AdminTenants-Anomalies-Stat-Backend` (NEW, if pursued).
- **Trend deltas** (`delta`/`deltaDir` arrows) — need period-over-period historical comparison (e.g. snapshot table or time-windowed diff); no source. Honest-gapped. → carryover `AD-AdminTenants-Stats-Trend-Deltas` (NEW, if pursued).
- **Page-scoped per-tenant stats** — this sprint returns the full-fleet per_tenant map; trimming to the visible page (pass the paged tenant ids to the endpoint) is a perf optimization if the fleet grows. → carryover.
- **Other Area-A carryover** (the rest of the "process all except A-4 Tier 2" program): A-5c Inspector Trace tab (`AD-ChatV2-Inspector-Trace-Phase2`) + Memory tab (`AD-ChatV2-Inspector-Memory-Phase2`); A-6b memory ops-history backend (`AD-Memory-OpsHistory-Backend`); FE `/subagents` wiring (`AD-Subagent-RealList-Phase58`). Sequenced after this sprint.
- **A-4 Tier 2 real Jaeger export** — explicitly excluded from the program (routed to Area-C/DevOps).
