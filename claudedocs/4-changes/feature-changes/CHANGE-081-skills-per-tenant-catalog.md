# CHANGE-081: Per-Tenant Skills Catalog

**Date**: 2026-06-13
**Sprint**: 57.114
**Scope**: Cat 5 (Prompt/Skills) + Cat 2 (Tool) + platform_layer + admin API + frontend (tenant-settings) + DB

## Problem

Sprint 57.113 opened the Skills System epic with a **system-global** bundled registry (every tenant sees the same `code-review` + `summarize`). Enterprise tenants need their OWN skills (and to override a built-in one) without a code change. `AD-Skills-Per-Tenant-Catalog` tracked the gap.

## Solution

A per-tenant overlay layered on the bundled set, resolved per chat request:

- **Cat 5 overlay** — `SkillRegistry.with_overlay(extra)` (`agent_harness/skills/registry.py:111`): pure name-keyed merge (`{base} | {extra}`) → a fresh registry; a same-name tenant skill shadows a bundled one; no mutation of the bundled singleton; deterministic `list()` order.
- **DB** — `TenantSkill(Base, TenantScopedMixin)` (`infrastructure/db/models/skill.py:51`), `tenant_skills` table, `UNIQUE(tenant_id, name)`; migration `0030_tenant_skills` with RLS two-policy (USING + WITH CHECK) **minus a sentinel escape** (strict per-tenant — no guest/cross-tenant lookup path).
- **Service** — `TenantSkillService` (`platform_layer/skills/service.py:87`): RLS-scoped `list_skills`/`create`/`update`/`delete` (`_set_tenant` per method, mirrors `TOTPService`); typed `DuplicateSkillError` (409) / `SkillNotFoundError` (404).
- **Resolver** — `resolve_tenant_skill_registry(db, tenant_id)` (`service.py:233`): TTL-cached (`_SkillRegistryCache`, injectable clock, `service.py:199`); fail-open to `get_default_skill_registry()` on db/tenant None or any error; `invalidate_tenant_skill_registry` (`service.py:255`) called by every admin mutation.
- **Admin CRUD** — `api/v1/admin/tenants.py:1857-2038`: `GET/POST /{id}/skills` + `PUT/DELETE /{id}/skills/{sid}`; each `require_admin_platform_role` + `_load_tenant_or_404` + `append_audit("tenant_skill_*")` + commit + cache invalidate. **The response is projected BEFORE `db.commit()`** — `expire_on_commit` would otherwise reload the RLS-protected row under no tenant ctx (new txn) and fail.
- **Router swap (主流量)** — `api/v1/chat/router.py:264` resolves the overlay; `:308` passes it to `build_handler`. `handler.py` / `make_default_executor` / `loop.py` **UNTOUCHED** (the registry was already a parameter since 57.113).
- **Frontend** — a "Skills" tab (9th) in tenant settings: `SkillsTab.tsx` (list-CRUD: add form + per-row Edit + 2-step Delete), `useTenantSkills.ts` (read + 3 mutations), `tenantSettingsService.ts` (4 client fns), `types.ts` (snake_case-direct `Skill`).

## Verification

- **Gate**: mypy 0 · black/isort/flake8 0 · `run_all.py` 10/10 (wire count 24 unchanged) · backend pytest **2602+5skip** (+36) · FE lint 0 / build clean / Vitest **851** (+11) / mockup-fidelity 51 · migration 0030 reversible.
- **Drive-through (real chat-v2 :3007 + real Azure gpt-5.2, 2 dev-login tenants) — ALL 3 legs PASS**:
  - **A**: tenant authored `release-notes` via the tab → chat `read_skill("release-notes")` → output followed `## Summary/## Highlights/## Upgrade steps`.
  - **B**: a second tenant's identical request called `read_skill` **0×** (no leak); its `code-review` request loaded the **bundled** body.
  - **C**: a `code-review` override (numbered-checklist) → chat loaded the **overridden** body → output a pure numbered checklist.
  - CRUD controls all live (Add/Edit/Delete + Save-disabled-until-complete). Screenshots in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-114/artifacts/`.

## Impact

- Full-stack (DB + service + admin API + chat 主流量 + FE). No new wire event (count 24), no codegen, no `loop.py` change.
- Closes `AD-Skills-Per-Tenant-Catalog`. Deferred (carried): per-tenant authoring richness (bundled scripts), slash-command invocation, Inspector affordance, an authoring UI beyond raw text.
- Design note: `docs/03-implementation/agent-harness-planning/32-skills-per-tenant-catalog.md`.
