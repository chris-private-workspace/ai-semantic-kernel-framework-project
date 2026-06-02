# Sprint 57.70 — Checklist (Real Per-Tenant Agent-Spec Catalog + Admin CRUD API — backend slice; FE → 57.71)

**Plan**: [`sprint-57-70-plan.md`](./sprint-57-70-plan.md)
**Created**: 2026-06-02 · **Revised Day-0** (reframed to AgentSpec registry + backend-only; FE → 57.71)
**Status**: Draft (commit/push/PR user-gated)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Feature-continuation (established patterns) → **no design note**. Scope: backend registry + CRUD API (user re-confirmed after Day-0 drift); FE wiring of existing `/subagents` page → **57.71**.

---

## Day 0 — Plan-vs-Repo Verify + Branch + Reframe

### 0.1 Three-prong Day-0 verify (3 researcher rounds folded into plan §0)
- [x] **Prong 1 (path)**: `persona_registry.py` (PERSONA_REGISTRY + sync resolve_persona); `service.py:131` + `handler.py:405` consumers + `handoff/__init__.py`; `_contracts/subagent.py:74-86` AgentSpec; `infrastructure/db/models/` (no registry table — confirmed) + `base.py` TenantScopedMixin; migration head 0022 (next 0023); `0019_rate_limit_configs.py` (RLS+seed template); `session_repository.py` (repo template); `api/v1/admin/tenants.py` (CRUD template) + `require_admin_platform_role`; existing `api/v1/subagents.py` (invocations STUB) + FE `pages/subagents/SubagentsPage.tsx` (read-only fixture)
- [x] **Prong 2 (content)**: `/subagents` GET = STUB (empty + not_implemented_reason), shape = invocations NOT definitions (distinct concern, untouched); FE page fixture-primary, 4 detail tabs read-only, zero CRUD; mockup `page-agents.jsx:311-438` SubagentsRegistry = AgentSpec fields (role/model/system_prompt/modes/status + budget/tools); resolve_persona consumers both async (db/tenant_id in scope); admin/tenants.py sub-resource `/admin/tenants/{id}/X` + require_admin_platform_role + Pydantic + append_audit
- [x] **Prong 3 (schema)**: next migration `0023` (down_revision `0022_session_handoff_linkage`); RLS 2-policy + FORCE from `0019`; `meta_data` JSONB physical `"metadata"` alias (raw SQL quotes it); UniqueConstraint(tenant_id, key) + tenant index; 09-schema Group 9 Subagent is the home
- [x] **Doc-location**: `09-db-schema-design.md §Group 9` (add agent_catalog); 17.md (resolve_persona NOT a registered contract — platform-layer); CHANGE-038; mockup = `page-agents.jsx` (FE wiring → 57.71)
- [x] Catalogued drift D1-D7 in plan §0 + progress.md; **go/no-go = GO** (>20% drift → plan REVISED + user re-confirmed backend-only, FE → 57.71)

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-70-agent-catalog` from `3090e8b7`
- [ ] revised plan+checklist commit; Day-0 progress commit
- [ ] Decisions: catalog = AgentSpec registry (Group 9, fields per mockup); resolver = DB→DEFAULT_AGENTS→None (empty still works, no lazy-write); seed = 0023 data-migration + hardcoded fallback; CRUD = admin (`/admin/.../agents`, distinct from invocations STUB); default chat persona stays DEMO; **FE → 57.71**; **Agent-delegated: yes** (Stage-1a backend / Stage-1b CRUD API; parent re-verify each)

---

## Day 1 — Table + repo + resolver (Stage 1a)

### 1.1 Table + migration (US-1)
- [x] `agent_catalog.py` (NEW) — `AgentCatalog(Base, TenantScopedMixin)` (Group 9): key/name/model/system_prompt/allowed_modes(JSONB)/status/meta_data(physical "metadata" JSONB budget+tools)/is_active/timestamps; UniqueConstraint(tenant_id, key) + tenant index
- [x] Alembic `0023_agent_catalog` — create table + index + RLS 2 policies (`tenant_isolation_agent_catalog` USING + `tenant_insert_agent_catalog` WITH CHECK) + FORCE (mirror 0019); verified up/down/re-up vs live Postgres (RLS present + FORCE=True); `check_rls_policies` green

### 1.2 Repository (US-2)
- [x] `AgentCatalogRepository(db)` (mirror SessionRepository) — async, tenant_id required kw-only: `list_by_tenant`/`get_by_key`/`create`/`update`/`delete`; tenant filter in every WHERE; caller-owned flush
- [x] Unit (`test_agent_catalog_repository.py`, 9, DB-backed): CRUD + tenant filter (A not visible to B) + UniqueConstraint(tenant_id,key)

### 1.3 Default seed (US-2)
- [x] `persona_registry.py` — `PERSONA_REGISTRY`→`DEFAULT_AGENTS` (same 3 prompts); `0023` data migration loops existing tenants → INSERT 3 defaults (raw SQL quotes physical `"metadata"`; allowed_modes `["handoff"]`)
- [x] Migration data-seed verified (7599 rows = 2533 tenants × 3: planner/researcher/reviewer)

### 1.4 Async resolver rewire (US-3)
- [x] `persona_registry.py` — NEW async `resolve_persona(db, tenant_id, key)` (DB active row → prompt → else DEFAULT_AGENTS → else None; **DB-error fail-safe → DEFAULT_AGENTS**) + sync `resolve_default_persona(key)`; `__all__` + `__init__.py` re-export
- [x] `service.py:131` `boot_handoff` — `await resolve_persona(db, tenant_id, target_agent)`; None → HandoffError (unchanged; resolves before txn)
- [x] `handler.py:405` `resolve_session_persona` — `await resolve_persona(db, tenant_id, agent_role)`; None → DEMO (unchanged; carried_context append preserved)
- [x] Unit: resolver DB-hit / DB-miss→default / unknown→None / inactive→fallback / DB-error→fallback; boot_handoff reject; handler DEMO fallback; updated 57.68/69 tests for the async signature
- [x] Backend green (parent re-verified): black/isort/flake8 0; `mypy src/` 0/328; `run_all.py` 10/10 (`check_llm_sdk_leak` 0); 54 targeted + full unit 1456 pass

---

## Day 2 — Admin CRUD API + backend integration (Stage 1b)

### 2.1 CRUD API (US-4)
- [x] `api/v1/admin/agents.py` (NEW, separate router prefix `/admin/tenants`, mirrors `cost_summary.py`/`sla_reports.py` sibling convention) — `GET /{tenant_id}/agents` (`require_tenant_match_or_platform_admin`) + `POST` (201) + `PUT /{agent_id}` + `DELETE /{agent_id}` (204) (writes `require_admin_platform_role`); Pydantic Create(extra=forbid)/Update(partial)/Response(from_attributes); 409 IntegrityError+rollback; 404 tenant-scoped; `append_audit` (`agent_catalog.{create,update,delete}`) + commit; registered in `main.py`; **`/subagents` invocations STUB untouched**
- [x] Integration (`test_admin_agent_catalog_api.py`, 15): create/list/update/delete + 409 dup-key + 403 no-admin + 401 no-JWT + 3 cross-tenant; audit rows asserted

### 2.2 RLS + multi-tenant + handoff-from-DB (US-5)
- [x] Integration: RLS enforced (cross-tenant blocked); tenant A agents invisible to B (repo + RLS double defense — repo test + API cross-tenant tests)
- [x] `test_chat_handoff.py` EXTEND (+2) — target resolves from DB catalog (override proven) + empty-catalog default fallback (contract preserved)
- [x] Test-isolation: full sweep ordering clean (no conn leak); conftest `AGENT_PUT_%` cleanup sweep added (mirrors `QUOTA_PUT_%`)

---

## Day 3 — Full sweep + edge cases

- [x] Full `pytest tests/unit tests/integration` → **2049 passed / 4 skipped / 0 failed** (catalog + 57.68/69 + no regression)
- [x] Edge: empty catalog → defaults / inactive agent → fallback / cross-tenant reject / unknown key → None reject / DB-error → fallback / override (tenant row beats default) — covered by repo + resolver + integration tests
- [x] Parent decisive re-verify: pytest full 2049; `mypy src/` 0/329; `run_all.py` 10/10; black 603 unchanged + isort/flake8 0; Alembic 0023 up/down verified (Stage-1a); Vitest unchanged (no FE)
- [x] No drift beyond Day-0 D1-D7 (reframe) — Stage-1a/1b matched the revised plan

---

## Day 4 — Closeout

### 4.1 Closeout docs
- [ ] `09-db-schema-design.md §Group 9` += agent_catalog table; 17.md unchanged (confirmed); CHANGE-038
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7) — NO design note (feature-continuation)
- [ ] Calibration: `agent-catalog-backend` 0.55 (NEW, 1 pt) + `agent_factor` 0.65 (CAVEATED — 8th consecutive no-clean-wall-clock); recorded `calibration-log.md §3`
- [ ] MEMORY.md pointer + `project_phase57_70_*.md` subfile + CLAUDE.md lean (Current Sprint + footer)

### 4.2 Final verify + ship
- [ ] **Final-commit `black --check`** (AD-Final-Commit-Black-Check) + isort + flake8 + mypy src 0 + run_all 10/10
- [ ] commit (Day 1-4) + push + PR — **user-authorized**
- [ ] Carryover recorded: FE `/subagents` wiring → 57.71; allowed_modes/budget/tools loop-enforcement; AD-Subagent-RealList-Phase58; etc. (plan §9)
