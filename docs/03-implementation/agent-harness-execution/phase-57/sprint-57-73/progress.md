# Sprint 57.73 Progress — A-6 Frontend Real-Data Wiring (A-6a admin-tenants partial + A-6b memory matrix backend + wiring)

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-73-plan.md`
**Checklist**: `.../sprint-57-73-checklist.md`
**Branch**: `feature/sprint-57-73-a6-real-data-wiring` (from main `7b0c326e`)

---

## Day 0 — 2026-06-03 — Plan-vs-Repo Verify + Re-scope + Branch

### Scope selection (2 AskUserQuestion, 2026-06-03)
- After A-5c (57.72) shipped, the user picked **A-6 frontend real-data wiring** as the next sprint (57.73). A-6 is breadth (a ~20-page portfolio); the analysis's actionable core is the 2 pages whose real wiring the mockup-rebuild dropped (`admin-tenants`, `memory`).
- **AskUserQuestion #1 (scope)**: user chose **A-6a + A-6b together**.
- Day-0 ground-truth then **refuted the analysis's "A-6b is pure-wiring" premise** (>50% drift): the 5 memory components render matrix/ops-timeline/time-travel shapes with NO backend producer (only flat entry rows + 3 wired layers). Surfaced this + the per-widget feasibility before drafting.
- **AskUserQuestion #2 (A-6b reality)**: user chose **"A-6a + A-6b 同 sprint 加後端"** — add backend for the feasible memory widgets, then wire. Per the feasibility verdict, the feasible backend is matrix + header counts (2 of 4 widgets); the ops-timeline + time-travel halves have no cheap producer and are deferred (carryover). Scope honored without ballooning into a Cat 3-wide write-path-instrumentation epic.

### Two-pass Day-0 三-prong verify — drift D1-D10 (researcher ground-truth, main `7b0c326e`)

**A-6a admin-tenants:**
- **D1** — `hooks/useAdminTenants.ts:34-41` exists (`useQuery<TenantListResponse>`, key `["admin-tenants","list",query]`, `keepPreviousData`) but imported NOWHERE; `pages/admin-tenants/index.tsx:13` documents the unmount.
- **D2** — `TenantsTable.tsx:35` imports `TENANTS_FIXTURE` directly (`.map` `:94`; only prop `onRowClick?`), banner `:159`; `TenantsStatsStrip.tsx:28,33` imports `STATS_FIXTURE` directly.
- **D3** 🔴 DRIFT (in our favour) — `tenants.py:227-275` `GET /admin/tenants` → `TenantListItem:194-215` HAS region+seats (analysis said missing; added 57.46/57.47). Still missing `agents`/`runs24` + **NO aggregate-stats endpoint**.
- **D4** — field map: `status`←`state` (real); name←display_name, id←code, plan/region/seats/created direct. Only `agents`+`runs24` unbacked per-row; whole `TenantsStatsStrip` (delta/deltaDir trend) unbacked.

**A-6b memory:**
- **D5** — `features/memory/hooks/` does NOT exist; `services/memoryService.ts:70-119` has fetchRecent/fetchByScope/fetchByTime; `types.ts:34-71` has MemoryLayer(5)/MemoryTimeScale(permanent|quarterly|daily)/MemoryEntryItem/MemoryEntryPage.
- **D6** — 5 components render matrix(5×3)/ops/timeline/time-travel shapes; backend returns flat `MemoryEntryItem` rows only.
- **D7** 🔴 DECISIVE — memory has 5 separate tables (`memory.py` models); only `MemoryUser` has `expires_at` (time-scale axis); only system/tenant/user have a wired path (role/session 501). **NO operation history**: `write()` plain INSERT (`user_layer.py:133-148`), hard-DELETE evict, no version increment, **ZERO `audit_log` emit** (grep-confirmed no `append_audit(resource_type="memory*")`). `MemoryAccessed` SSE = runtime telemetry, not persisted.
- **D8** — per-widget feasibility: MemoryMatrix ✅ (`GET /memory/matrix` COUNT GROUP BY) · MemoryPageHeader ✅ (sum) · RecentMemoryOpsCard ❌ (no producer) · TimeTravelScrubber ❌ (no producer).
- **D9** — `/recent` router conventions (`memory.py:243-262` deps trio) + `useCostSummary.ts:39-45` hook template. Memory REST facade NOT in 17.md (57.12 facade precedent) → `/matrix` follows it.
- **D10** — shadcn-residue grep = 0 in both feature dirs; data-only wiring won't touch CSS; shared `TableSkeleton`/`ErrorRetry`/`EmptyState` carry shadcn tokens → use mockup-native states; `HEX_OKLCH_BASELINE = 50` must stay (57.69 lesson).

### go/no-go = **GO (re-scoped, user-confirmed via 2 AskUserQuestion)**
- A-6a partial + A-6b matrix-only backend + wire; ops/time-travel deferred (carryover). The A-6b >50% drift was surfaced + re-confirmed BEFORE drafting (Day-0 abort-redraft discipline). Plan + checklist drafted to the confirmed reality baseline.

### Prong 3 (schema): N/A
- `/memory/matrix` is a read aggregate over existing tables — no migration / ORM / column change.

### Decisions
- A-6a = partial wiring (real list fields; `"—"` for agents/runs24; stats strip stays fixture+banner). A-6b = new `/memory/matrix` aggregate (system/tenant/user; role/session gapped; time-scale via expires_at for user, permanent for system/tenant) + wire matrix+header; ops/timeline stay fixture+banner. Mockup-native loading/error/empty (no shadcn residue). No migration.
- **Agent-delegated: yes** — 3 sequential `code-implementer` tracks (A admin frontend, B memory backend, C memory frontend); parent independently re-verifies (aggregate correctness + tenant isolation + re-mount + honest gaps + runs `check:mockup-fidelity` + pytest + Vitest).

---

## Day 1-3 — 2026-06-03 — Implementation (agent-delegated, 3 tracks + parent re-verify)

Track A + Track B launched in parallel (disjoint: admin-tenants frontend vs memory backend); Track C (memory frontend) ran after Track B confirmed the response shape.

### Track A — admin-tenants wiring (US-1/US-2, `code-implementer` aac54e42)
- `AdminTenantsView.tsx` mounts `useAdminTenants()` → threads `items`/`isLoading`/`isError`/`refetch` to `TenantsTable`. `TenantsTable.tsx` rewritten to take `tenants: TenantListItem[]` props (was direct `TENANTS_FIXTURE` import); field map name←display_name / id←code / plan / region / seats / status←state (→ existing pill tones) / created←created_at.slice(0,10); `agents`/`runs24` → `"—"` (`var(--fg-subtle)`, NOT fabricated); mockup-native skeleton/error/empty rows (NOT shadcn `TableSkeleton`/`EmptyState` — D10 residue avoidance); banner reworded. `types.ts` synced `TenantListItem` to the real backend contract (added region/locale/retention_days/sso_enabled/seats — FE type was stale at 57.4's 7 fields; required for tsc). `_fixtures.ts` dropped orphan `TENANTS_FIXTURE` (kept `STATS_FIXTURE`). Playwright e2e (happy/error/empty) 3/3.
- **Parent re-verify catch (D-DAY1-1)**: the agent wrote the loading/error/empty COPY in 繁中 ("載入租戶清單失敗。"/"重試"/"沒有任何租戶。") — inconsistent with the codebase convention (governance `AuditLogViewer` "Failed to load audit log", `VerificationRunsTable` "Failed to load verification runs.", `TenantSettingsView` "Retry" are all English) AND with the page's own English headers/banner. Parent grep-confirmed the convention + corrected the component + its Vitest + the e2e spec to English ("Failed to load tenants." / "Retry" / "No tenants found.").

### Track B — memory matrix backend (US-3, `code-implementer` a1a3c549)
- `memory.py` new `GET /matrix` (mirrors `/recent` deps trio) + `MemoryMatrixCell`/`MemoryMatrixResponse`. Aggregate: system `count()` global → (system, permanent); tenant `count() WHERE tenant_id==current` → (tenant, permanent); user `count() GROUP BY case(expires_at)` → permanent/quarterly/daily (same predicate as `/by-time`). `gapped_layers=[role,session]` reported not queried; zero-cells omitted. No migration. 6 pytest (counts + isolation + empty + RBAC). Parent verified the aggregate query + the explicit `tenant_id==current` defense-in-depth (alongside RLS) by reading `memory.py:418-501`.

### Track C — memory frontend wiring (US-4/US-5, `code-implementer` a3e29c76)
- `types.ts` matrix types; `memoryService.fetchMatrix`; NEW `hooks/useMemoryMatrix.ts` (key `["memory","matrix"]`, mirrors `useCostSummary`). `MemoryMatrix.tsx` consumes the hook: 5×3 grid, `${layer}:${time_scale}`→count lookup (absent → 0 "— empty"), role/session via `gapped_layers` → `n/a` across the row (never fabricated); banner reworded; mockup-native loading/error/empty (English copy). `MemoryPageHeader.tsx` real `total` (dedup'd query). `MemoryView.tsx` dropped fixture-only `cursor` filter. RecentOps/TimeTravel unchanged (fixture + reworded banner → carryover). `_fixtures.ts` dropped orphan matrix/header fixtures. Parent verified honest gaps + no shadcn import by reading `MemoryMatrix.tsx`.

---

## Day 4 — 2026-06-03 — Parent final verification + closeout

**Parent-run gates (decisive)**:
- Frontend: `npm run build` tsc 0 (3.92s); `npm run check:mockup-fidelity` **byte-identical + baseline 50 unchanged** ✅; `npm run lint` (no `--silent`) EXIT 0 (only pre-existing jsx-ast-utils `TSSatisfiesExpression` info noise); Vitest admin-tenants+memory **72/72** (full suite 708, +10 from 698); CSS diff empty; grep 0 hardcoded hex/oklch.
- Backend: `test_memory_matrix.py` **6/6**; memory regression **28 passed** (existing `test_memory.py` 13 + matrix 6 + query_extension 3 + chat wiring — facade intact); `mypy src --strict` **0/329**; `python scripts/lint/run_all.py` **10/10** (incl. `check_ap4_frontend_placeholder` — honest gaps pass AP-4; `check_llm_sdk_leak`; `check_rls_policies` unchanged — no new table).
- Verdict: **PASS**. Honest gaps confirmed (admin agents/runs24 + stats strip; memory role/session + ops/time-travel) — no fabricated data, all declared via `BackendGapBanner` (AP-4 detector green).

**Calibration**: scope `mixed-multidomain-bundle` 0.65; `agent_factor` `mixed-multidomain-bundle-mechanical` 0.45. Agent-delegated → no clean wall-clock (**11th consecutive** `AD-Calibration-AgentDelegated-WallClock-Measure`). See retrospective Q2 + `calibration-log.md §3`.
