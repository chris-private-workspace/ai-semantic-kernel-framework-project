# Sprint 57.73 — Checklist (A-6 Frontend Real-Data Wiring: A-6a admin-tenants partial + A-6b memory matrix backend + wiring)

**Plan**: [`sprint-57-73-plan.md`](./sprint-57-73-plan.md)
**Created**: 2026-06-03
**Status**: Draft (commit/push/PR user-gated)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Backend+frontend feature-continuation (matrix endpoint mirrors the Sprint-57.12 `/memory/recent` facade; admin re-mount is pure wiring) → **no design note**. Mockup-Fidelity Hard Constraint applies (`docs/rules-on-demand/frontend-mockup-fidelity.md`). Scope: A-6a admin-tenants partial + A-6b memory matrix (backend + wire); ops/time-travel widgets stay fixture-gapped (no producer — carryover).

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (two researcher ground-truth passes, main `7b0c326e`)
- [x] **Prong 1 (path)**: `frontend/src/features/admin-tenants/{hooks/useAdminTenants,services/adminTenantsService,_fixtures,store/adminTenantsStore,components/{TenantsTable,TenantsStatsStrip,AdminTenantsView}}.tsx`; `pages/admin-tenants/index.tsx`; `frontend/src/features/memory/{services/memoryService,types,_fixtures}.ts` + `components/{MemoryMatrix,MemoryPageHeader,RecentMemoryOpsCard,TimeTravelScrubber,GdprErasureCard}.tsx` (NO `hooks/` dir); `backend/src/api/v1/{admin/tenants.py,memory.py}`; `backend/src/infrastructure/db/models/memory.py`; mockups `page-admin.jsx`/`page-governance.jsx`; `useCostSummary.ts` (hook template); `check-mockup-fidelity.mjs`
- [x] **Prong 2 (content)**: D1 `useAdminTenants` exists+unmounted (`index.tsx:13`); D2 components import fixtures directly; D3 backend has region+seats (DRIFT — analysis wrong), missing agents/runs24 + NO stats endpoint; D4 status←state mapping; D5 memory hooks dir absent, service+types exist; D6 5 components render matrix/ops/timeline shapes; D7 **memory write()=plain INSERT, ZERO audit emit, no version history** (ops/time-travel UNBACKABLE cheaply); D8 per-widget verdict (matrix+header feasible, ops+timeline gap); D9 `/recent` router conventions + `useCostSummary` template; D10 shadcn-residue grep=0 both dirs, shared skeleton/error carry shadcn tokens (use mockup-native)
- [x] **Prong 3 (schema)**: N/A — no DB / migration / ORM change (`/memory/matrix` is a read aggregate over existing tables)
- [x] **Mockup-fidelity**: D10 `styles-mockup.css` byte-identical (diff empty); data-only wiring → no CSS change; `HEX_OKLCH_BASELINE = 50` must stay; loading/empty markup MUST be mockup-native (NOT shadcn `TableSkeleton`/`EmptyState` — residue risk)
- [x] **Doc-location**: CHANGE-041; mockups canonical = `page-admin.jsx`/`page-governance.jsx`; new `/matrix` follows 57.12 facade precedent (router + FE service single-source, not 17.md)
- [x] Catalogued drift D1-D10 in plan §0; **go/no-go = GO (re-scoped via 2 AskUserQuestion)**: A-6a partial + A-6b matrix-only backend; ops/time-travel deferred. The >50% A-6b drift (analysis's "pure-wiring" premise false) was surfaced + re-confirmed with user before drafting

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-73-a6-real-data-wiring` from `7b0c326e`
- [x] plan + checklist commit; Day-0 progress commit
- [x] Decisions: A-6a = partial wiring (real list fields, `"—"` for agents/runs24, stats strip stays fixture+banner); A-6b = new `/memory/matrix` aggregate (system/tenant/user; role/session gapped; time-scale via expires_at) + wire matrix+header, ops/timeline stay fixture+banner; mockup-native states (no shadcn residue); no migration; **Agent-delegated: yes** (3 sequential code-implementer tracks + parent re-verify)

---

## Day 1 — A-6a admin-tenants wiring (US-1/US-2)

### 1.1 Re-mount hook + thread data (US-1)
- [x] `AdminTenantsView.tsx` — mount `useAdminTenants()`; thread `data.items`/`isLoading`/`isError`/`refetch` to `TenantsTable`
- [x] `pages/admin-tenants/index.tsx` — replace "unmounted in this rebuild" comment with "wired Sprint 57.73; agents/runs24/stats gapped"

### 1.2 TenantsTable real fields + honest gaps + states (US-1/US-2)
- [x] `TenantsTable.tsx` — accept `tenants: TenantListItem[]` (+ loading/error/onRetry) prop; drop `TENANTS_FIXTURE` import
- [x] Field map: name←display_name, id←code, plan, region, seats, status←state (→ existing pill), created←created_at (format)
- [x] `agents`/`runs24` → render `"—"` (`var(--fg-subtle)`); NOT fixture values; reword `BackendGapBanner` (`:159`) to name the 2 gapped cols + stats strip
- [x] Mockup-native states: loading (skeleton rows via `.subtle`), error (inline + retry), empty ("no tenants" row) — NOT shadcn `TableSkeleton`/`EmptyState`
- [x] `TenantsStatsStrip.tsx` — ensure `BackendGapBanner` present (stays `STATS_FIXTURE`; no aggregate endpoint)
- [x] `_fixtures.ts` — remove orphan `TENANTS_FIXTURE` (keep `STATS_FIXTURE`; move to test if a Vitest needs it)

### 1.3 Playwright e2e (US-6)
- [x] ≥2 hermetic e2e mocking `**/api/v1/admin/tenants**`: happy (rows render) + error/empty (500 / `items:[]` → states)

---

## Day 2 — A-6b memory matrix backend (US-3)

### 2.1 Endpoint + models (US-3)
- [x] `memory.py` — new `GET /memory/matrix` mirroring `/recent` deps trio (`get_current_tenant` + `require_audit_role` + `get_db_session_with_tenant`)
- [x] Pydantic `MemoryMatrixCell{layer,time_scale,count}` + `MemoryMatrixResponse{cells,total,gapped_layers}`
- [x] Aggregate: `MemorySystem` count → (system,permanent); `MemoryTenant` count (RLS) → (tenant,permanent); `MemoryUser` GROUP BY expires_at buckets → (user, permanent|quarterly|daily); `gapped_layers=[role,session]`; `total=Σ`

### 2.2 Backend tests (US-6)
- [x] `test_memory_matrix.py` — correct counts per (layer,time_scale); role/session in `gapped_layers`; **cross-tenant isolation** (A excludes B); empty → total 0
- [x] `mypy src/ --strict` 0; `python scripts/lint/run_all.py` (V2 lints incl. `check_llm_sdk_leak`) green

---

## Day 3 — A-6b memory frontend wiring (US-4/US-5)

### 3.1 Hook + service + types (US-4)
- [x] `memoryService.ts` — `fetchMatrix(signal)` → `GET /memory/matrix`
- [x] `types.ts` — `MemoryMatrixCell`/`MemoryMatrixResponse` (backend vocab permanent|quarterly|daily)
- [x] `hooks/useMemoryMatrix.ts` (NEW; first file in new `memory/hooks/`) — `useQuery` key `["memory","matrix"]`, mirror `useCostSummary`

### 3.2 Wire components (US-4/US-5)
- [x] `MemoryMatrix.tsx` — consume `useMemoryMatrix`; real counts system/tenant/user (default 0 for absent cells); role/session → gap indicator via `gapped_layers` (NOT fabricated); remove/reword Phase-58 banner; mockup-native loading/error/empty
- [x] `MemoryPageHeader.tsx` — real `total` (same query, dedup)
- [x] `RecentMemoryOpsCard.tsx` + `TimeTravelScrubber.tsx` — UNCHANGED fixtures; reword banners → carryover (memory op-history)
- [x] `_fixtures.ts` — remove orphan matrix/header fixtures (keep ops/timeline)

### 3.3 Vitest (US-6)
- [x] `useMemoryMatrix` (mocked fetch); `MemoryMatrix` (seeded → 3-layer counts + role/session gap); `MemoryPageHeader` (real total); `TenantsTable` (props → rows + "—" + states); assert RecentOps/TimeTravel still fixtures

---

## Day 4 — Mockup-fidelity sweep + Closeout

### 4.1 Mockup-fidelity + full sweep (US-6)
- [x] **CSS diff**: `diff styles.css styles-mockup.css` → empty (parent-verified)
- [x] **grep guard**: no hardcoded hex/oklch in edited components + new hook (all `var(--*)`)
- [x] **`check:mockup-fidelity`**: baseline unchanged (50=50, byte-identical) — parent-run
- [x] **computed-style**: tenants row + memory matrix cell vs mockups (`page-admin.jsx`/`page-governance.jsx`); no shadcn-token residue introduced
- [x] `npm run lint` (no `--silent`) EXIT 0 + `npm run build` tsc 0 + Vitest green — parent-run
- [x] Backend `pytest` (matrix + isolation) green; mypy 0; V2 lints green — parent-run
- [x] Parent re-verify: aggregate-query correctness + tenant isolation + re-mount logic + honest gaps (no fabricated data)

### 4.2 Closeout docs
- [x] CHANGE-041 created; no 17.md/02.md/01.md change (facade precedent; pure read aggregate)
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7) — NO design note (feature-continuation)
- [x] Calibration: `mixed-multidomain-bundle` 0.65 + `agent_factor` `mixed-multidomain-bundle-mechanical` 0.45 (CAVEATED — 11th consecutive no-clean-wall-clock; if <0.7 → escalate per 57.59 note); recorded `calibration-log.md §3`
- [x] MEMORY.md pointer + `project_phase57_73_*.md` subfile + CLAUDE.md lean (Current Sprint row + footer)
- [x] Carryover recorded (plan §9 + retrospective §Q5): `AD-Memory-OpsHistory-Backend` (ops/time-travel write-path instrumentation) + `AD-AdminTenants-Stats-Aggregate-Endpoint` (agents/runs24 + stats strip) + memory role/session layers + matrix cell drill-down + REST-type codegen + A-5c Trace/Memory tabs + FE /subagents wiring + capstone key chains (C-11 / billing bundle)

### 4.3 Ship
- [x] Final verify (parent-run): CSS diff empty + build tsc 0 + Vitest green + `check:mockup-fidelity` 50 + lint (no `--silent`) EXIT 0 + backend pytest/mypy/V2-lints green + grep 0 hardcoded color
- [ ] commit (Day 1-4) + push + PR — **user-authorized** (closeout commit done; push/PR pending user approval)
