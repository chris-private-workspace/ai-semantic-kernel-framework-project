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
