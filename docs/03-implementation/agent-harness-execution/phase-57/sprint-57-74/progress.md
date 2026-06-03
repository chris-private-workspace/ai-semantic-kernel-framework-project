# Sprint 57.74 Progress — admin-tenants stats aggregate endpoint

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-74-plan.md`
**Checklist**: `...sprint-57-74-checklist.md`
**Branch**: `feature/sprint-57-74-admin-tenants-stats` (from `main` `12324e50`)

---

## Day 0 — 2026-06-03 — Plan-vs-Repo Verify + Decisions

### Decisions (user-locked, 3× AskUserQuestion)
- **Scope** = stats strip + per-row Agents/Runs·24h columns (full `AD-AdminTenants-Stats-Aggregate-Endpoint` closure).
- **Runs·24h** = sessions started in last 24h (`sessions.started_at >= now()-24h`).
- **Un-backable** (Anomalies stat + per-stat trend deltas) = honest gap (placeholder + `BackendGapBanner`, no fabrication).
- NEW `GET /admin/tenants/stats` endpoint (not extend lean `list_tenants`).
- **Agent-delegated: yes** — Track A backend + Track B frontend (sequential code-implementer) + parent re-verify (Before-Commit item 7).

### Prong 1 (path) — GREEN, no drift
All confirmed via Glob: `backend/src/api/v1/admin/tenants.py` + `cost_summary.py`/`sla_reports.py`/`agents.py`; ORMs `agent_catalog.py`/`sessions.py`/`identity.py`; `frontend/src/features/admin-tenants/{services/adminTenantsService,hooks/useAdminTenants,types,_fixtures,components/{TenantsStatsStrip,TenantsTable,AdminTenantsView}}` — all exist. Service file IS `adminTenantsService.ts` (plan assumption confirmed). `frontend/tests/e2e/admin-tenants.spec.ts` (57.73) exists to extend.

### Prong 2 (content) — researcher pass (see plan §0 D1-D8)
- agent_catalog: `is_active` (`:104`) / `tenant_id` / `idx_agent_catalog_tenant` (`:118`) — use `is_active` for "deployed".
- sessions: `started_at` (`:114`) / `tenant_id`; session root NOT partitioned (`:72`).
- `list_tenants` (`:227-230`) deps `require_admin_platform_role` (no tenant filter → cross-tenant aggregate OK); `TenantListResponse` (`:218`); no agents/runs24 fields.
- frontend: `TenantsTable:124-125` agents/runs24 = `GAP_PLACEHOLDER`; `TenantsStatsStrip` consumes `STATS_FIXTURE` (`_fixtures.ts:36`, 4 stats `{label,value,delta,deltaDir}` incl Anomalies).

### Prong 2.5 (child-tree) — researcher: shadcn-residue grep = 0 in `features/admin-tenants` (57.73 just stabilized); backend agent re-greps before edit.

### Prong 3 (schema) — N/A (read aggregate over existing tables; no migration/ORM change).

### Drift findings
- **D-DAY0-1 (path-order, MUST honor)**: `admin/tenants.py` router prefix `/admin/tenants`; `GET ""` list at `:227`, a `GET` at `:315` (likely `/{tenant_id}` detail) + `PATCH /{tenant_id}` at `:515`. → the new `GET /stats` **must be registered after `:227` and BEFORE the `/{tenant_id}` GET (`:315`)** or `/stats` gets captured as `tenant_id="stats"`. Backend agent instructed accordingly.
- **D-DAY0-2 (favourable)**: `cost_summary.py` + `sla_reports.py` are sibling admin aggregate endpoints in the same router package → clean precedent to mirror for deps + inline Pydantic.
- No unfavourable scope drift; plan §0 D3 already noted region/seats present (from 57.46/47).

### go/no-go = **GO** (Day 1 backend). No scope change; D-DAY0-1 is an implementation-placement constraint, not a scope shift.

---

## Day 1 — Backend `/admin/tenants/stats` (Track A, agent-delegated) — `f322c6c0`

- code-implementer agent (Track A, ~4.6 min wall-clock) implemented `GET /admin/tenants/stats` in `admin/tenants.py` (L321, after list `:278`, before `/{tenant_id}` — D-DAY0-1 honored) + `FleetStats`/`PerTenantStat`/`TenantsStatsResponse` + 4-query aggregate + per-tenant union merge + `gapped=["anomalies","deltas"]`. NEW `test_admin_tenants_stats.py` (6 tests, mirrors `test_admin_tenant_list._build_app` — Risk Class C db override covered).
- **Parent re-verify (Before-Commit item 7)**: read endpoint + tests for correctness (tz-aware cutoff, union merge, 403 gate, no fabrication); re-ran mypy **0/329**, pytest **29 passed** (6 new + 23 list + 2 rbac), `run_all.py` **10/10**. No defect found (agent clean).

## Day 2 — Frontend hook/service/types + strip wiring (Track B part 1) — `8b4897ca`

- `adminTenantsService.fetchStats` + `types` (FleetStats/PerTenantStat/TenantsStatsResponse) + `useAdminTenantsStats` hook (key `["admin-tenants","stats"]`).
- `TenantsStatsStrip` → `fleet` prop; 3 real stats (toLocaleString); Anomalies subtle "—"; deltas omitted; BackendGapBanner; mockup-native states; `STATS_FIXTURE` removed.

## Day 3 — Table columns + View + Vitest + e2e (Track B part 2) — `8b4897ca`

- `TenantsTable` `statsByTenant` map prop + `renderCount` (real >0 / "—" absent-or-0); table gap banner dropped (strip owns single banner). `AdminTenantsView` mounts stats hook + threads fleet + per_tenant→statsByTenant; list query intact.
- Vitest: NEW `useAdminTenantsStats.test`; extended strip/table/view tests; e2e `/stats` mock + 2 scenarios.

## Day 4 — Sweep + Closeout

- **Parent re-verify (Before-Commit item 7)**: read all changed frontend code (3 real stats / no fabrication / English copy / mockup-native / single banner); CJK grep clean (only a pre-existing code comment); re-ran **check:mockup-fidelity byte-identical + baseline 50**, **build tsc 0**, **lint exit 0** (no `--silent`), **Vitest 715 passed** (129 files). No defect (agents clean).
- Calibration: `mixed-multidomain-bundle` 0.65 + `mixed-multidomain-bundle-mechanical` 0.45 — CAVEATED (12th consecutive no-clean-wall-clock; no escalation signal; both tracks first-pass clean).
- Closeout: CHANGE-042, retrospective.md (Q1-Q7), `AD-AdminTenants-Stats-Aggregate-Endpoint` → CLOSED + 2 NEW carryovers (`AD-AdminTenants-Anomalies-Stat-Backend` / `AD-AdminTenants-Stats-Trend-Deltas`). No design note (feature-continuation).
