# Sprint 57.70 Plan — Real Per-Tenant Agent Catalog (DB-backed) + Admin CRUD API + FE Manage-Agents Page

**Purpose**: Replace the hardcoded 3-entry persona stand-in (`platform_layer/handoff/persona_registry.py`, Sprint 57.68) with a **real DB-backed per-tenant agent catalog**: a new `agent_catalog` table (per-tenant, RLS), an `AgentCatalogRepository`, async tenant-scoped persona resolution (rewiring `resolve_persona`'s two consumers — `HandoffService.boot_handoff` + `handler.resolve_session_persona` — while PRESERVING the `None`=reject / DEMO-fallback contract), the 3 default agents materialized per tenant (data migration + hardcoded fallback so an empty catalog still works), an **admin CRUD API** (mirroring `admin/tenants.py`), and a **"Manage Agents" FE page** (mirroring the `admin-tenants` page) so a platform admin can list/create/edit/delete a tenant's agents. This makes handoff targets real + per-tenant configurable instead of a global hardcoded dict. This is a **feature-continuation sprint** (it composes established patterns — per-tenant table + RLS + repository + admin CRUD + admin FE page — NOT a new mechanism), so **no design note** is required (per `sprint-workflow.md §Step 5.5`).
**Category / Scope**: Cat 11 (HANDOFF persona resolution) + platform-layer agent catalog (service + repository) + DB (Alembic `0023`, new per-tenant RLS table) + API (admin CRUD) + Frontend (Manage-Agents page) + governance (audit on mutations); Phase 57.70
**Created**: 2026-06-02
**Status**: Draft (user-approved scope: "+ Admin CRUD API + FE page" — the full vertical; **internal slice boundary**: Day 1-2 = backend catalog + CRUD API [a complete shippable unit], Day 3-4 = FE page; if Day-1 overruns, FE slices to 57.71 + re-confirm — §8/§9; code execution gated on Day-0 GO)
**Source**: A-3b carryover (design note `18-handoff-design.md §5`: "real agent/persona catalog") + **two-round Day-0 reality audit (2 codebase-researchers, 2026-06-02)** (persona/agent concept + `resolve_persona` consumers map; per-tenant table + RLS + seed + admin CRUD conventions map) + user AskUserQuestion decisions 2026-06-02 (next sprint = real per-tenant agent catalog; scope = + Admin CRUD API + FE page)

> **Modification History**
> - 2026-06-02: Initial creation — DB-backed per-tenant agent catalog + admin CRUD API + FE Manage-Agents page; feature-continuation (no design note); folds the Day-0 audit (AgentSpec exists / no agent table / resolve_persona sync→async + tenant_id / RLS 2-policy pattern / next migration 0023 / admin CRUD convention exists) into §0

---

## 0. Background

Sprint 57.68 (A-3b slice 1) introduced a **minimal hardcoded 3-entry persona stand-in** (`persona_registry.py`: `PERSONA_REGISTRY: dict[str, str]` = researcher/reviewer/planner; `resolve_persona(target_agent) -> str | None`, sync, global, tenant-agnostic) — explicitly flagged as a thin stand-in (design note `18-handoff-design.md §5`: "a DB-backed per-tenant catalog is future work"). The user chose to build that catalog (full vertical: backend + admin CRUD API + FE page).

### ⚠️ Day-0 audit findings (two researcher rounds, folded per `sprint-workflow.md §Step 2.5`)

- **D1 — `AgentSpec` already exists** (`_contracts/subagent.py:74-86`, `@dataclass(frozen=True)`: `role`, `prompt`, `model`, `metadata`; docstring anticipates tools/scopes/risk). → build the catalog AROUND this shape; the catalog row maps to an `AgentSpec`-like record (no new contract type; richer fields go in JSONB `meta_data`).
- **D2 — NO agent/persona table exists** (full `__tablename__` scan; closest is RBAC `roles`/`user_roles` in `identity.py`, unrelated). → CREATE `agent_catalog` (per-tenant + RLS). Latest Alembic head = `0022_session_handoff_linkage` → next = **`0023`**.
- **D3 — `resolve_persona` is SYNC + global; two consumers** — `service.py:131` (`HandoffService.boot_handoff`, async method, calls it sync; `None` → `raise HandoffError` BEFORE any write; stores only the `target_agent` STRING in `meta_data["agent_role"]`, NOT the prompt) + `handler.py:405` (`resolve_session_persona`, async; `None` → `DEMO_SYSTEM_PROMPT` fallback). → a DB-backed lookup must become **async + tenant-scoped**; both call sites are already in async methods (clean to `await`). **The `None`=reject / DEMO-fallback contract MUST be preserved.**
- **D4 — per-tenant table + RLS conventions** — `TenantScopedMixin` (`base.py:51-78`); RLS = TWO policies (`tenant_isolation_<t>` USING + `tenant_insert_<t>` WITH CHECK) + `FORCE ROW LEVEL SECURITY`, `current_setting('app.tenant_id', true)::uuid` — **lint-enforced** (`check_rls_policies`); template `0019_rate_limit_configs.py`. Repository template `session_repository.py` (async, required `tenant_id` kw-only, tenant filter in every WHERE, caller-owned commit).
- **D5 — no real per-tenant seed mechanism** (provisioning steps are stubs). → seed the 3 defaults via a 0019-style data migration (existing tenants get editable DB rows) **PLUS** keep the hardcoded defaults as a resolver fallback so an empty/new-tenant catalog still resolves (no lazy-write in read paths). Design: **resolver = DB catalog (tenant override/extend) → hardcoded `DEFAULT_AGENTS` fallback → `None`**; the hardcoded defaults always work; the DB catalog lets a tenant override a default's prompt or add new agents.
- **D6 — admin CRUD convention exists** — `backend/src/api/v1/admin/tenants.py` (`APIRouter(prefix="/admin/tenants")`, Pydantic `XCreateRequest`/`XResponse`, `Depends(require_admin_platform_role)`, `require_tenant_match_or_platform_admin`, `append_audit` on mutations, `db.flush()`). FE: `frontend/src/pages/admin-tenants/index.tsx` (+ `tenant-settings`). → mirror both for the agents CRUD API + the Manage-Agents page.
- **D7 — DEMO chat persona is separate** — the default (non-handoff) chat session uses the hardcoded `DEMO_SYSTEM_PROMPT` (`handler.py:96`), independent of any catalog. → this slice does NOT back the default chat persona with the catalog (YAGNI; only handoff targets resolve from the catalog) — documented out-of-scope (§9).

**Net**: a coherent full vertical — (backend) `agent_catalog` table (per-tenant, RLS, `0023`) + `AgentCatalogRepository` + an async tenant-scoped resolver that prefers the DB catalog then falls back to the hardcoded `DEFAULT_AGENTS` then `None`, rewired into `boot_handoff` + `resolve_session_persona`; a data migration materializes the 3 defaults per existing tenant; (API) an admin CRUD router for per-tenant agents; (FE) a Manage-Agents page. Multi-tenant 鐵律 throughout. Internal slice boundary at Day 2 (backend + API shippable alone if FE overruns).

---

## 1. Sprint Goal

Stand up a real DB-backed per-tenant agent catalog and wire it behind the existing HANDOFF persona resolution + expose it for management: create the `agent_catalog` table (per-tenant, RLS, Alembic `0023`) + `AgentCatalogRepository`; replace the global sync `resolve_persona` with an async tenant-scoped resolver (DB catalog → hardcoded `DEFAULT_AGENTS` fallback → `None`), rewiring `HandoffService.boot_handoff` (reject unknown) + `handler.resolve_session_persona` (DEMO fallback) while preserving their contracts; materialize the 3 default agents per existing tenant via a data migration; expose an admin CRUD API (`/admin/.../agents`, mirroring `admin/tenants.py` — `require_admin_platform_role`, Pydantic schemas, `append_audit`); and build a "Manage Agents" FE page (mirroring `admin-tenants`) to list/create/edit/delete a tenant's agents. Prove it with backend tests (table/RLS/repo/seed/resolution/CRUD/multi-tenant) + FE tests + the HANDOFF flow still resolving the target persona from the DB. **Multi-tenant 鐵律: every catalog row + query is tenant-scoped; cross-tenant access forbidden (RLS + repo filter).** The default (non-handoff) chat persona stays the hardcoded DEMO (§9).

---

## 2. User Stories

- **US-1 (catalog table + migration)** — As the platform, I want an `agent_catalog` table (per-tenant, RLS) so each tenant's agents are isolated + durable. → `infrastructure/db/models/agent_catalog.py` (NEW, `Base, TenantScopedMixin`) + Alembic `0023` (create + RLS 2 policies + FORCE + indexes).
- **US-2 (repository + default seed)** — As the platform, I want an `AgentCatalogRepository` (async, tenant-scoped CRUD) + the 3 default agents materialized per existing tenant, so the catalog is queryable + pre-populated. → `AgentCatalogRepository`; `DEFAULT_AGENTS` (moved from `PERSONA_REGISTRY`); `0023` data migration seeds existing tenants.
- **US-3 (async tenant-scoped resolution)** — As the HANDOFF flow, I want persona resolution to read the tenant's catalog (override/extend) then fall back to the hardcoded defaults then reject, so handoff targets are per-tenant configurable WITHOUT breaking the `None`=reject / DEMO-fallback contract. → async `resolve_persona(db, tenant_id, key)`; rewire `boot_handoff` (`service.py:131`) + `resolve_session_persona` (`handler.py:405`).
- **US-4 (admin CRUD API)** — As a platform admin, I want CRUD endpoints for a tenant's agents (list/create/update/delete) so the catalog is manageable. → `api/v1/admin/agents.py` (mirror `admin/tenants.py`: `require_admin_platform_role`, Pydantic, `append_audit`).
- **US-5 (FE Manage-Agents page)** — As a platform admin, I want a page to view + manage a tenant's agents so I don't edit the DB by hand. → a Manage-Agents page (mirror `admin-tenants`); API client; mockup-fidelity (or AP-2 honesty if no mockup).
- **US-6 (validation)** — As a reviewer, I want backend tests (table/RLS/repo/seed/resolution/CRUD/multi-tenant) + FE tests + a HANDOFF integration test proving the target persona resolves from the DB catalog (override) and falls back to defaults, so the catalog is real (non-Potemkin) and the contract is preserved.

---

## 3. Technical Specifications

### 3.0 Architecture

```
                       ┌──────────────── agent_catalog (per-tenant, RLS, 0023) ─────────────┐
                       │ id · tenant_id · key · name · system_prompt · model · meta_data    │
                       │ (allowed_tools/risk in JSONB) · is_active · created/updated_at      │
                       └────────────────────────────────────────────────────────────────────┘
                                 ▲ CRUD (tenant-scoped)                 ▲ read (tenant-scoped)
   FE Manage-Agents page ──────► /admin/.../agents (CRUD API) ──► AgentCatalogRepository ◄── async resolver
   (mirror admin-tenants)         (require_admin_platform_role,                              │
                                   Pydantic, append_audit)            resolve_persona(db, tenant_id, key):
                                                                       1. DB catalog row (active) → system_prompt
                                                                       2. else DEFAULT_AGENTS[key]  (hardcoded fallback)
                                                                       3. else None  (reject)
                                                                          ▲                    ▲
                                            HandoffService.boot_handoff ───┘   handler.resolve_session_persona ──┘
                                            (None → HandoffError, reject)      (None → DEMO_SYSTEM_PROMPT)
```

The resolver prefers the per-tenant DB row, falls back to the always-present hardcoded `DEFAULT_AGENTS`, then `None` — so an empty / new-tenant catalog still resolves the 3 defaults (the contract is preserved without a lazy-write in any read path). The data migration materializes the defaults as editable rows for existing tenants (so the FE shows + edits them). The default (non-handoff) chat persona stays DEMO (§9).

### 3.1 Catalog table + migration (US-1) — `agent_catalog.py` (NEW) + Alembic `0023`
- `AgentCatalog(Base, TenantScopedMixin)`: `id` UUID PK (`server_default gen_random_uuid()`), `tenant_id` (mixin), `key` String(64) (the role key, e.g. "researcher"), `name` String(128), `system_prompt` Text, `model` String(128) nullable, `meta_data` JSONB (physical `"metadata"` alias; holds allowed_tools/risk/etc.), `is_active` Boolean default true, `created_at`/`updated_at` (`server_default func.now()`). `__table_args__`: `UniqueConstraint("tenant_id", "key", name="uq_agent_catalog_tenant_key")` + `Index("idx_agent_catalog_tenant", "tenant_id")`. (Day-0 Prong-3 confirms the domain-group file per `09-db-schema-design.md`.)
- Alembic `0023_agent_catalog` (`down_revision="0022_session_handoff_linkage"`): create table + indexes + the TWO RLS policies (`tenant_isolation_agent_catalog` USING + `tenant_insert_agent_catalog` WITH CHECK) + `FORCE ROW LEVEL SECURITY` (mirror `0019`); `downgrade` drops policies then table. Verified up/down/re-up Day-0/Day-1.

### 3.2 Repository + default seed (US-2) — `AgentCatalogRepository` + `DEFAULT_AGENTS`
- `AgentCatalogRepository(db: AsyncSession)` (mirror `SessionRepository`): async, `tenant_id` required kw-only on every query, tenant filter in every WHERE, caller-owned commit (`flush`). Methods: `list_by_tenant(tenant_id)`, `get_by_key(tenant_id, key)`, `create(tenant_id, key, name, system_prompt, model, meta_data)`, `update(tenant_id, agent_id, ...)`, `delete(tenant_id, agent_id)`.
- `DEFAULT_AGENTS` (moved from `PERSONA_REGISTRY` — same 3 researcher/reviewer/planner prompts; `persona_registry.py` becomes the canonical default-source module + the async resolver). The `0023` data migration loops existing tenants and INSERTs the 3 defaults as rows (0019 pattern; raw SQL quotes `"metadata"` for the JSONB column — Day-0 D-DAY0 alias note).

### 3.3 Async tenant-scoped resolution (US-3) — `resolve_persona` rewire
- NEW async `resolve_persona(db: AsyncSession, tenant_id: UUID, key: str) -> str | None`: (1) `AgentCatalogRepository(db).get_by_key(tenant_id, key)` → if active → `system_prompt`; (2) else `DEFAULT_AGENTS.get(key)`; (3) else `None`. Keep a sync `resolve_default_persona(key) -> str | None` (the pure hardcoded fallback, for tests / no-DB paths).
- Rewire `service.py:131` (`boot_handoff`): `await resolve_persona(db, tenant_id, target_agent)`; `None` → `HandoffError` (unchanged semantics; it's already async + has `db`/`tenant_id`).
- Rewire `handler.py:405` (`resolve_session_persona`, already async): `await resolve_persona(db, tenant_id, str(agent_role))`; `None` → `DEMO_SYSTEM_PROMPT` (unchanged). Day-0 Prong-2 reads both call sites' exact async context + the `__init__` re-export.

### 3.4 Admin CRUD API (US-4) — `api/v1/admin/agents.py` (NEW)
- `APIRouter(prefix="/admin/.../agents")` (Day-0 confirms the exact prefix vs `admin/tenants.py`; likely `/admin/tenants/{tenant_id}/agents` or `/admin/agents` with tenant in body — mirror the existing sub-resource pattern). Pydantic `AgentCreateRequest`/`AgentUpdateRequest`/`AgentResponse`. Endpoints: `GET` list, `POST` create, `PUT` update, `DELETE`. Guards: `Depends(require_admin_platform_role)` + `require_tenant_match_or_platform_admin` (tenant scoping). `append_audit` on create/update/delete (`operation="agent_catalog.create"` etc.). `db.flush()`; tenant-scoped via the repo.

### 3.5 FE Manage-Agents page (US-5)
- A page mirroring `admin-tenants` (`frontend/src/pages/...` + `frontend/src/features/.../components/`): list the tenant's agents (table), create/edit (form/modal), delete (confirm). API client (mirror the admin-tenants service). Route + nav entry. **Mockup-fidelity**: Day-0 checks `reference/design-mockups/` for an agents/personas page; if none exists, compose from the admin-tenants design-system patterns + AP-2 honesty (production-only, no mockup source) + run `check:mockup-fidelity` (no NEW oklch/hex literals beyond the existing baseline; bump + document only if unavoidable). i18n per the existing FE convention (Day-0 confirms keyed vs inline).

### 3.6 Lint / neutrality / doc single-source
- `check_rls_policies` green (the 2-policy + FORCE pattern). `check_llm_sdk_leak` 0 (catalog + repo + resolver are provider-free; `agent_harness/**` untouched — the resolver lives in `platform_layer`). All 10 V2 lints green; no codegen change. FE `check:mockup-fidelity` ✓ (run it — D-DAY2-1 / Sprint 57.69 lesson: FE work must run ALL CI gates).
- **Doc single-source**: 17.md unchanged unless the persona-resolution signature is a registered cross-category contract (Day-0 confirms — it is a platform-layer concern, likely not in 17.md). `09-db-schema-design.md` += the `agent_catalog` table (new per-tenant table → document per the schema-design doc convention).

### 3.7 Validation (US-6)
- **Backend unit**: `AgentCatalogRepository` (CRUD + tenant filter); `resolve_persona` (DB hit / DB miss→default fallback / unknown→None / inactive→fallback); `DEFAULT_AGENTS` integrity. **Backend integration**: the `0023` migration up/down; RLS enforced (cross-tenant SELECT blocked); the CRUD API (create/list/update/delete + `require_admin_platform_role` 403 + cross-tenant 404 + audit rows); the HANDOFF flow resolves the target from the DB catalog (override) AND from defaults (empty catalog) — extend `test_chat_handoff.py`. **Multi-tenant**: tenant A's agent invisible to tenant B (RLS + repo).
- **Frontend**: Manage-Agents page tests (list render, create/edit/delete actions, API client); the existing handoff/store tests unchanged.

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/infrastructure/db/models/agent_catalog.py` | **NEW** — `AgentCatalog` ORM (per-tenant, JSONB meta_data) (US-1) |
| `backend/src/infrastructure/db/migrations/versions/0023_agent_catalog.py` | **NEW** — create table + RLS 2 policies + FORCE + indexes + data-seed existing tenants (US-1/US-2) |
| `backend/src/infrastructure/db/repositories/agent_catalog_repository.py` | **NEW** — `AgentCatalogRepository` (async, tenant-scoped CRUD) (US-2) |
| `backend/src/platform_layer/handoff/persona_registry.py` | **EDIT** — `PERSONA_REGISTRY`→`DEFAULT_AGENTS`; NEW async `resolve_persona(db, tenant_id, key)` (DB→default→None) + sync `resolve_default_persona`; keep `__all__` (US-2/US-3) |
| `backend/src/platform_layer/handoff/service.py` | **EDIT** (`:131`) — `await resolve_persona(db, tenant_id, target_agent)` (US-3) |
| `backend/src/platform_layer/handoff/__init__.py` | **EDIT** — re-export updates (US-3) |
| `backend/src/api/v1/chat/handler.py` | **EDIT** (`:405`) — `await resolve_persona(db, tenant_id, agent_role)` (US-3) |
| `backend/src/api/v1/admin/agents.py` | **NEW** — admin CRUD router (US-4) |
| `backend/src/api/v1/admin/__init__.py` (or app router include) | **EDIT** — register the agents router (US-4) |
| `frontend/src/pages/.../agents` + `frontend/src/features/.../components/*` | **NEW** — Manage-Agents page + components (US-5) |
| `frontend/src/.../services/*` (agents API client) + route/nav + i18n | **NEW/EDIT** (US-5) |
| `backend/tests/unit/...` + `backend/tests/integration/...` | **NEW/extend** — repo + resolver + migration + RLS + CRUD + multi-tenant + handoff-from-DB (US-6) |
| `backend/tests/integration/api/test_chat_handoff.py` | **EXTEND** — target resolves from DB catalog (override) + default fallback (US-6) |
| `frontend/tests/unit/...` | **NEW** — Manage-Agents page/component tests (US-6) |
| `docs/03-implementation/agent-harness-planning/09-db-schema-design.md` | **EDIT** — document the `agent_catalog` table |
| `claudedocs/4-changes/feature-changes/CHANGE-038-agent-catalog.md` | **NEW** — change record |

**No new wire-type / no codegen / no SSE change.** No `agent_harness/**` edit (resolver is platform-layer). **Internal slice boundary**: rows above the FE rows = Day 1-2 (backend + API, shippable alone); FE rows = Day 3-4.

---

## 5. Acceptance Criteria

- `agent_catalog` table exists (per-tenant, RLS 2 policies + FORCE); Alembic `0023` up/down/re-up clean; `check_rls_policies` green.
- `AgentCatalogRepository` is async + tenant-scoped (every query filters `tenant_id`); the 3 defaults are materialized per existing tenant by the `0023` data migration.
- Async `resolve_persona(db, tenant_id, key)` resolves DB catalog (override) → hardcoded `DEFAULT_AGENTS` → `None`; `boot_handoff` still rejects unknown targets; `resolve_session_persona` still falls back to DEMO; an EMPTY catalog still resolves the 3 defaults (contract preserved).
- Admin CRUD API: create/list/update/delete a tenant's agents; `require_admin_platform_role` enforced (403 without); cross-tenant access blocked (404/RLS); `append_audit` rows written on mutations.
- FE Manage-Agents page: lists the tenant's agents + create/edit/delete; API client works; `check:mockup-fidelity` ✓ (no silent baseline overflow — run it).
- The HANDOFF flow resolves the target persona from the DB catalog (override proven) + from defaults (empty-catalog proven) — `test_chat_handoff.py` extended.
- All existing tests green; `mypy --strict src/` 0; 10/10 V2 lints (LLM SDK leak 0); FE lint exit 0 + Vitest green + build ✓. **Multi-tenant**: tenant A's agents invisible to tenant B.

---

## 6. Deliverables

- [ ] `agent_catalog.py` ORM + Alembic `0023` (table + RLS + seed) (US-1/US-2)
- [ ] `AgentCatalogRepository` (US-2)
- [ ] `persona_registry.py` rewire (`DEFAULT_AGENTS` + async `resolve_persona`) + `service.py`/`handler.py` await rewire (US-3)
- [ ] `api/v1/admin/agents.py` CRUD router + registration (US-4)
- [ ] FE Manage-Agents page + components + API client + route/nav + i18n (US-5)
- [ ] backend tests (repo/resolver/migration/RLS/CRUD/multi-tenant/handoff-from-DB) + FE tests (US-6)
- [ ] `09-db-schema-design.md` += agent_catalog; CHANGE-038 + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: **`agent-catalog-fullstack` (0.50, NEW — pending validation)** — a large multi-domain feature-continuation (new per-tenant RLS table + migration + repo + async resolver rewire + seed + admin CRUD API + FE management page + tests both sides), composing established patterns (no new mechanism). Lower multiplier (0.50) reflects the breadth + the established-pattern reuse (much is mechanical mirroring of `admin/tenants.py` + `admin-tenants` page + `0019`/`session_repository` templates). **Agent-delegated: yes** (staged: Stage-1 backend — table + migration + repo + resolver rewire + seed + CRUD API + backend tests; Stage-2 frontend — Manage-Agents page + client + FE tests; parent independent re-verify each stage). `agent_factor` **`mechanical-greenfield-design-decisions` 0.65** (genuine design: table schema, resolver fallback chain, CRUD shape, FE page; but heavy pattern-mirroring).

> Bottom-up est ~22 hr → class-calibrated commit ~11 hr (mult 0.50) → agent-adjusted commit ~7.2 hr (agent_factor 0.65).

Caveat (carried 57.63-57.69): agent-delegated sprints have no clean wall-clock (`AD-Calibration-AgentDelegated-WallClock-Measure`; would be 8th consecutive). The NEW `agent-catalog-fullstack` class is a single unvalidated point — record caveated. **If Day-1 backend proves the full vertical >1 sprint, slice: ship backend catalog + CRUD API (a complete shippable unit) in 57.70, FE page in 57.71 — re-confirm with the user** (the internal slice boundary at Day 2 makes this clean).

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Scope > 1 sprint** (full vertical: backend + API + FE) | internal slice boundary at Day 2 (backend + CRUD API shippable alone); if Day-1 overruns, FE → 57.71 + re-confirm (§7) |
| **`resolve_persona` sync→async ripple** | only 2 consumers (`service.py:131` + `handler.py:405`), both already async; Day-0 Prong-2 reads both + the `__init__` re-export before the rewire (`AD-Day0-Codegen-Existing-Shape-Capture`) |
| **Contract break** (None=reject / DEMO-fallback) | the DB→default→None fallback chain preserves both; an EMPTY catalog still resolves the 3 defaults (no behavior change for existing handoffs); tests assert all three branches |
| **RLS lint** | mirror the `0019` 2-policy + FORCE pattern exactly; `check_rls_policies` gates; Day-0 Prong-3 confirms the pattern + next migration `0023` |
| **JSONB column alias** | `meta_data` maps to physical `"metadata"`; raw SQL in the migration quotes `"metadata"` (Day-0 D-DAY0 alias note; 57.59/57.60 precedent) |
| **Seed coverage** (new tenants) | the hardcoded `DEFAULT_AGENTS` fallback covers new/empty tenants without a lazy-write; the data migration materializes editable rows for EXISTING tenants; provisioning-step seeding deferred (§9) |
| **Admin CRUD auth** | mirror `admin/tenants.py` exactly (`require_admin_platform_role` + `require_tenant_match_or_platform_admin`); cross-tenant 403/404 tested |
| **FE mockup-fidelity** | Day-0 checks for an agents-page mockup; if none → compose from `admin-tenants` patterns + AP-2 honesty; **run `check:mockup-fidelity`** (Sprint 57.69 D-DAY2-1 lesson — FE work runs ALL CI gates, not just lint/build/test) |
| **Multi-tenant leakage** | RLS + repo tenant-filter (double defense); integration asserts tenant A's agents invisible to B |
| **Test isolation** (new source DB call) | the resolver now does a DB read; ensure tests overriding `get_db_session` / TestClient suites don't leak connections (Risk Class C; Sprint 57.68 FIX-026 lesson) |

---

## 9. Out of Scope (this sprint; carryover)

- **Default (non-handoff) chat persona from the catalog** — the default chat session stays the hardcoded `DEMO_SYSTEM_PROMPT` (Day-0 D7); backing it with a catalog "default agent" is future work.
- **Wiring allowed_tools / memory_scopes / risk_limits into the loop** — the catalog STORES these (JSONB `meta_data`) but does NOT enforce them this slice (the loop's tool/risk wiring is a separate concern); columns/fields present, enforcement deferred.
- **Provisioning-step seeding for new tenants** — covered by the hardcoded fallback this slice; a real `ProvisioningWorkflow` seed step (the stubbed `seed_default_*`) is future work.
- **Tenant self-service management** — the CRUD API/page is platform-admin (`require_admin_platform_role`); tenant-admin self-service is future.
- **Other A-3b carryover** — user-visible transcript continuity (message-persistence subsystem), summarize-carry, target auto-first-turn, multi-hop chains + cycle guards, dedicated columns. Other Area-A: A-4 (loop tracer), A-5c (diagnostic Inspector UI), A-6.
- **FE page (conditional)** — if Day-1 overruns, the FE Manage-Agents page slices to 57.71 (§7).
