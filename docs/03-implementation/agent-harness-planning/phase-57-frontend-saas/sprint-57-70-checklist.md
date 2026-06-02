# Sprint 57.70 — Checklist (Real Per-Tenant Agent Catalog + Admin CRUD API + FE Manage-Agents Page)

**Plan**: [`sprint-57-70-plan.md`](./sprint-57-70-plan.md)
**Created**: 2026-06-02
**Status**: Draft (commit/push/PR user-gated)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Feature-continuation (composes established patterns) → **no design note**. Scope: full vertical (+API+FE); **internal slice boundary at Day 2** (backend+API shippable alone; FE → 57.71 if Day-1 overruns + re-confirm).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [ ] **Prong 1 (path)**: `persona_registry.py` (PERSONA_REGISTRY + resolve_persona); `service.py:131` + `handler.py:405` (resolve_persona consumers) + `handoff/__init__.py` re-export; `_contracts/subagent.py:74-86` AgentSpec; `infrastructure/db/models/` (no agent table — confirm) + `base.py` TenantScopedMixin; `migrations/versions/` head = 0022 (next 0023); `0019_rate_limit_configs.py` (RLS+seed template); `session_repository.py` (repo template); `api/v1/admin/tenants.py` (CRUD template) + `require_admin_platform_role`; FE `pages/admin-tenants/index.tsx` + `features/admin-tenants/` (page template)
- [ ] **Prong 2 (content)**: read EXACT `resolve_persona` consumer contexts (both async? `db`/`tenant_id` in scope at `service.py:131` + `handler.py:405`?); `boot_handoff` txn + how `target_agent` flows; `admin/tenants.py` exact CRUD shape (router prefix, Pydantic, guards, append_audit, sub-resource PUT pattern); FE admin-tenants page structure (list/form/delete + API client + i18n keyed-vs-inline); `09-db-schema-design.md` domain-group convention (which file the ORM goes in)
- [ ] **Prong 3 (schema)**: confirm next migration `0023` (down_revision `0022_session_handoff_linkage`); RLS 2-policy + FORCE pattern from `0019`; `meta_data` JSONB physical `"metadata"` alias (raw SQL quotes it); UniqueConstraint(tenant_id, key) + tenant index; no column drift
- [ ] **Doc-location**: `09-db-schema-design.md` (add agent_catalog); 17.md (confirm resolve_persona is NOT a registered cross-category contract — platform-layer); CHANGE-038; **mockup check** — `reference/design-mockups/` for an agents/personas page (exists? → fidelity; none → AP-2 compose from admin-tenants)
- [ ] Catalogued D-DAY0-1..N in progress.md; **go/no-go = decide** (≤20% continue / 20-50% revise + re-confirm / >50% redraft)

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-70-agent-catalog` from `3090e8b7`
- [ ] plan+checklist commit; Day-0 progress commit
- [ ] Decisions: resolver = DB→DEFAULT_AGENTS→None (empty catalog still works, no lazy-write); seed = 0023 data-migration (existing tenants) + hardcoded fallback (new tenants); default chat persona stays DEMO (§9); CRUD = platform-admin only; **Agent-delegated: yes** (Stage-1 backend+API / Stage-2 FE; parent re-verify each); **internal slice boundary Day 2**

---

## Day 1 — Backend catalog + repo + resolver (Stage 1a)

### 1.1 Table + migration (US-1)
- [ ] `agent_catalog.py` (NEW) — `AgentCatalog(Base, TenantScopedMixin)`: id/key/name/system_prompt/model/meta_data(JSONB)/is_active/timestamps; UniqueConstraint(tenant_id, key) + tenant index; correct domain-group file per `09-db-schema-design.md`
- [ ] Alembic `0023_agent_catalog` — create table + indexes + RLS 2 policies (`tenant_isolation_agent_catalog` USING + `tenant_insert_agent_catalog` WITH CHECK) + FORCE; up/down/re-up clean vs live Postgres; `check_rls_policies` green

### 1.2 Repository (US-2)
- [ ] `AgentCatalogRepository(db)` (mirror SessionRepository) — async, tenant_id required kw-only: `list_by_tenant`/`get_by_key`/`create`/`update`/`delete`; tenant filter in every WHERE; caller-owned flush
- [ ] Unit: CRUD + tenant filter + UniqueConstraint(tenant_id,key)

### 1.3 Default seed (US-2)
- [ ] `persona_registry.py` — `PERSONA_REGISTRY`→`DEFAULT_AGENTS` (same 3 prompts); `0023` data migration loops existing tenants → INSERT 3 defaults (raw SQL quotes `"metadata"`)
- [ ] Migration data-seed verified (existing tenants get 3 rows)

### 1.4 Async resolver rewire (US-3)
- [ ] `persona_registry.py` — NEW async `resolve_persona(db, tenant_id, key) -> str | None` (DB row active → prompt → else DEFAULT_AGENTS → else None) + sync `resolve_default_persona(key)`; `__all__` + `__init__.py` re-export
- [ ] `service.py:131` `boot_handoff` — `await resolve_persona(db, tenant_id, target_agent)`; None → HandoffError (unchanged)
- [ ] `handler.py:405` `resolve_session_persona` — `await resolve_persona(db, tenant_id, agent_role)`; None → DEMO (unchanged)
- [ ] Unit: resolver DB-hit / DB-miss→default / unknown→None / inactive→fallback; boot_handoff reject; handler DEMO fallback
- [ ] Backend green: black/isort/flake8 0; `mypy src/` 0; `check_llm_sdk_leak` 0

---

## Day 2 — Admin CRUD API + backend integration (Stage 1b) — INTERNAL SLICE BOUNDARY

### 2.1 CRUD API (US-4)
- [ ] `api/v1/admin/agents.py` (NEW) — mirror `admin/tenants.py`: router prefix (per Day-0), Pydantic Create/Update/Response, `require_admin_platform_role` + `require_tenant_match_or_platform_admin`, GET/POST/PUT/DELETE, `append_audit` on mutations, `db.flush()`; register router
- [ ] Integration: CRUD happy path + `require_admin_platform_role` 403 + cross-tenant 404 + audit rows written

### 2.2 RLS + multi-tenant + handoff-from-DB (US-6)
- [ ] Integration: RLS enforced (cross-tenant SELECT blocked at DB); tenant A agents invisible to B (repo + RLS double defense)
- [ ] `test_chat_handoff.py` EXTEND — target resolves from DB catalog (override proven) + empty-catalog default fallback (contract preserved)
- [ ] Test-isolation: new resolver DB read doesn't leak conns in TestClient suites (Risk Class C, 57.68 FIX-026 lesson)

### 2.3 Backend sweep + slice decision
- [ ] Full `pytest tests/unit tests/integration` green; `run_all.py` 10/10; mypy src 0; Alembic 0023 up/down clean
- [ ] **Slice decision**: backend+API complete + shippable. If Day-1/2 overran → FE → 57.71, re-confirm with user; else continue Day 3 FE

---

## Day 3 — FE Manage-Agents page (Stage 2)

### 3.1 Page + components (US-5)
- [ ] Mockup check resolved (fidelity if mockup exists; AP-2 compose from `admin-tenants` if none — documented)
- [ ] Manage-Agents page (mirror `admin-tenants`): list table + create/edit form + delete confirm; route + nav entry
- [ ] API client (mirror admin-tenants service); i18n per FE convention

### 3.2 FE tests + sweep (US-6)
- [ ] Page/component tests (list render, create/edit/delete, API client); existing handoff/store tests unchanged
- [ ] FE green: `npm run lint` (NO `--silent`) exit 0; `npm run test` (Vitest); `npm run build`; **`npm run check:mockup-fidelity`** ✓ (57.69 D-DAY2-1 lesson — run ALL CI gates)

---

## Day 4 — Full sweep + Closeout

### 4.1 Full validation
- [ ] Parent decisive re-verify: pytest full / mypy src 0 / run_all 10/10 / FE lint+test+build+mockup-fidelity ✓ / Alembic 0023 up/down
- [ ] Edge: empty catalog (defaults) / inactive agent / cross-tenant / unknown key reject

### 4.2 Closeout
- [ ] `09-db-schema-design.md` += agent_catalog table; 17.md unchanged (confirmed); CHANGE-038
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7) — NO design note (feature-continuation)
- [ ] Calibration: `agent-catalog-fullstack` 0.50 (NEW, 1 pt) + `agent_factor` 0.65 (CAVEATED — 8th consecutive no-clean-wall-clock); recorded `calibration-log.md §3`
- [ ] MEMORY.md pointer + `project_phase57_70_*.md` subfile + CLAUDE.md lean (Current Sprint + footer)
- [ ] **Final-commit `black --check`** (AD-Final-Commit-Black-Check) + FE `check:mockup-fidelity` before push
- [ ] commit (Day 1-4) + push + PR — **user-authorized**
