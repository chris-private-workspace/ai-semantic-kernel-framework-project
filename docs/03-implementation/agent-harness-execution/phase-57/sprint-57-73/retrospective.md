# Sprint 57.73 Retrospective — A-6 Frontend Real-Data Wiring (A-6a admin-tenants partial + A-6b memory matrix backend + wiring)

**Closed**: 2026-06-03
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-73-plan.md`
**Branch**: `feature/sprint-57-73-a6-real-data-wiring` (from `7b0c326e`)

---

## Q1 — What was delivered?

The final Area-A integration-gap item (A-6), for the subset with a real producer. **A-6a** (frontend): re-mounted the built-but-unmounted `useAdminTenants` hook so the tenants table renders real `GET /admin/tenants` data (name/id/plan/region/seats/status/created); the 2 unbacked columns (`agents`/`runs24`) show `"—"` and the aggregate `TenantsStatsStrip` stays fixture, both declared via `BackendGapBanner`; loading/error/empty are mockup-native. **A-6b** (backend + frontend): new `GET /api/v1/memory/matrix` Cat 3 read aggregate (COUNT GROUP BY over system/tenant/user; role/session reported gapped; time-scale via `expires_at` for user) feeds `MemoryMatrix` (5×3 grid) + `MemoryPageHeader` (total) via a new `useMemoryMatrix` hook; `RecentMemoryOpsCard` + `TimeTravelScrubber` stay fixture-gapped (no op-history backend). No DB migration.

## Q2 — Estimate accuracy / calibration

- Scope class **`mixed-multidomain-bundle` (0.65)** — 3 tracks (admin frontend wiring + memory backend aggregate + memory frontend wiring) with heavy pattern reuse. `agent_factor` **`mixed-multidomain-bundle-mechanical` 0.45** (the rolled-back tier-3 baseline since Sprint 57.59). **Agent-delegated: yes** — 3 sequential `code-implementer` tracks (Track A admin frontend, Track B memory backend, Track C memory frontend); parent independently re-verified (read the aggregate query + tenant-isolation, the table field-map + honest gaps, the matrix gap-rendering; ran build + Vitest + check:mockup-fidelity + pytest + mypy + V2 lints).
- Plan: bottom-up ~15 hr → class-calibrated ~9.75 hr (0.65) → agent-adjusted ~4.4 hr (0.45).
- **No clean wall-clock** (agent-delegated) → **11th consecutive** agent-delegated no-clean-measure (57.63→57.73) → reinforces `AD-Calibration-AgentDelegated-WallClock-Measure`. CAVEATED. `mixed-multidomain-bundle-mechanical` 0.45 has 2 prior below-band data points (57.58=0.49, 57.59=0.34); this 1st validation under the tightened 0.45 had no clean wall-clock to add a 3rd → the 57.59 escalation watch (`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation`) continues to defer for lack of a measurable agent-delegated bundle. KEEP 0.45; no generalization.

## Q3 — What went well?

- **Two Day-0 passes caught a >50% premise error before any code.** The A-6 analysis (older commit, judgement estimates) framed both pages as clean "pure-wiring". Pass 1 found admin-tenants is *partial* (region+seats backed now, but agents/runs24 + stats strip have no backend). Pass 2 found the decisive fact: memory has **no operation history** (write()=plain INSERT, zero audit emit, no version log), so the ops-timeline + time-travel widgets have NO cheap producer — the analysis's "wire 3 hooks to 5 components" was infeasible. Surfacing this + re-confirming scope with the user (2 AskUserQuestion) before drafting avoided either fabricating data (AP-4) or silently shipping less than asked.
- **Honest gaps held under the AP-4 detector.** `agents`/`runs24` → `"—"`, role/session → `n/a`, ops/time-travel → fixture + reworded banner. `check_ap4_frontend_placeholder` stayed green — the gaps are declared (BackendGapBanner), not Potemkin features filled with fake data.
- **Parallel Track A + B + sequential C was clean.** Disjoint surfaces (admin frontend / memory backend / memory frontend) → A+B in parallel, C after B confirmed the response shape. All parent-run gates green; the only parent correction was an i18n consistency fix (Q4).
- **The matrix aggregate was a genuinely cheap, honest backend add** — one GROUP BY per wired layer, RLS + explicit `tenant_id==current` defense-in-depth, zero migration, mirrors `/recent`. Covers 3 of 5 layers truthfully.

## Q4 — What to improve / lessons

- **Agent-written user-facing copy drifted from the codebase language convention.** Track A wrote the loading/error/empty strings in 繁中 while the page (and every other wired feature's state copy — governance/verification/tenant-settings) is English. Parent caught it during re-verify (grep-confirmed the convention), but it required editing the component + Vitest + e2e spec. **Lesson**: agent prompts for state-copy work should specify the language convention explicitly (English for these UI strings); or a Day-0 note should pin it. Minor, but it's the 2nd agent-delegated "copy/locale" drift class worth a one-line prompt guard.
- **An over-optimistic analysis is a Day-0 liability, not a contract.** The A-6 analysis self-noted "effort figures are judgement estimates" and "verify high-impact claims" — and both pages drifted from it. The Day-0 abort-redraft discipline (>50% drift → re-confirm) did its job. Worth correcting the analysis doc itself (its A-6b "pure-wiring" claim) so it doesn't mislead a future reader — folded into the carryover.
- **The Memory page is now half-real, half-gapped by design** — matrix + header live, ops/time-travel fixture. The value of the gapped half is realized only when the op-history backend (`AD-Memory-OpsHistory-Backend`) lands; the banners now point at that carryover so the gap is legible.

## Q5 — Carryover / open items (plan §9)

- **`AD-Memory-OpsHistory-Backend`** (NEW) — memory op-history backend to back `RecentMemoryOpsCard` + `TimeTravelScrubber`: either `append_audit(resource_type="memory_*")` at every layer `write()`/`evict()` (5 layers) + the `memory_write`/`memory_extract` tools, OR a new append-only `memory_ops` table. Forward-only (no backfill). A larger Cat 3 write-path feature.
- **`AD-AdminTenants-Stats-Aggregate-Endpoint`** (NEW) — per-tenant `agents`/`runs24` counts + an aggregate-stats endpoint to back the gapped columns + `TenantsStatsStrip`.
- **memory role/session layers** — junction tables, no RLS path (501); matrix reports them via `gapped_layers`. Backend layer support overlaps the A-1/A-3 memory track.
- **matrix cell drill-down** — click a matrix cell → entry list via the existing `fetchByScope`/`fetchByTime`. Follow-up.
- **REST-type codegen for service DTOs** (parallel to A-5b for events) — hand-written DTOs carry drift risk (this sprint hit it: the FE `TenantListItem` was stale).
- **Correct the A-6 analysis doc** — its `frontend-real-data-wiring-analysis-20260531.md` A-6b "pure-wiring" claim was refuted; annotate it.
- **Other Area-A**: A-5c Trace/Memory Inspector tabs (need their producers); FE `/subagents` page wiring (57.70 carryover). Two high-priority capstone key chains remain untouched: **C-11 (real-LLM enablement)** + the **billing-correctness bundle (B-7/B-8/C-15)**.

## Q6 — Anti-pattern audit (04-anti-patterns.md)

- **AP-4 (Potemkin)**: the wired widgets render REAL data (admin table from `GET /admin/tenants`; matrix + header from `GET /memory/matrix`, Vitest seeds + asserts); the unbacked surfaces (admin agents/runs24 + stats strip; memory role/session + ops/time-travel) are DECLARED gaps (`BackendGapBanner`, `"—"`/`n/a`), NOT fake-data features. `check_ap4_frontend_placeholder` green. ✅
- **AP-2 (no orphan)**: removed orphan fixtures (`TENANTS_FIXTURE`; memory matrix/header fixtures) per Karpathy §3; the new hook + endpoint are wired into their only consumers. ✅
- **AP-3 (cross-dir scatter)**: changes cohered per track (admin-tenants feature / memory.py / memory feature). ✅
- **LLM neutrality**: the matrix aggregate is pure DB; `check_llm_sdk_leak` green. ✅
- **Multi-tenant**: explicit `tenant_id==current` + RLS on the aggregate; cross-tenant isolation test green; `check_rls_policies` unchanged (no new table). ✅
- **Mockup-fidelity**: verbatim classes + `var(--*)`; CSS diff empty; `check:mockup-fidelity` baseline 50 unchanged; no shadcn-token residue (mockup-native states). ✅

## Q7 — Final verification

Frontend: `npm run build` tsc 0; Vitest admin-tenants+memory 72/72 (full suite 708, +10); `npm run check:mockup-fidelity` byte-identical + baseline 50 unchanged; `npm run lint` (no `--silent`) EXIT 0; CSS diff empty; grep 0 hardcoded hex/oklch; Playwright admin-tenants e2e 3/3. Backend: `test_memory_matrix.py` 6/6; memory regression 28 passed; `mypy src --strict` 0/329; `python scripts/lint/run_all.py` 10/10. No design note (backend+frontend feature-continuation — matrix mirrors the 57.12 `/recent` facade; admin is pure wiring).
