# Design Note 32 — Per-Tenant Skills Catalog (DB-backed Cat-5 registry overlay)

**Purpose**: The FIRST DB-backed per-tenant overlay of a Cat-5 registry — how a tenant's custom skills layer on the bundled set, resolved per chat request, with strict RLS isolation and override-by-name semantics.
**Category / Scope**: Cat 5 (Prompt/Skills) + Cat 2 (Tool, read_skill consumer) + platform_layer / Sprint 57.114
**Created**: 2026-06-13
**Status**: Active (spike-extract from a shipped + drive-through-proven vertical)
**Verified ratio**: ~97% (every claim below has a file:line anchor + a gate or drive-through observation; the one Open item is explicitly fenced as NOT verified)

> **Modification History**
> - 2026-06-13: Initial extract (Sprint 57.114) — per-tenant overlay + resolver + admin CRUD + Skills tab; drive-through ALL 3 legs PASS

---

## 1. Spike summary (US — as wired in Sprint 57.114)

Sprint 57.113 shipped a **system-global** bundled `SkillRegistry` (Cat 5) + a `read_skill` tool (Cat 2) + a `## Available Skills` block on the `system_prompt`. This sprint adds the **per-tenant overlay**: a tenant authors skills via an admin tab → stored in a new `tenant_skills` table (RLS) → `resolve_tenant_skill_registry` overlays them on the bundled set per chat request → a 1-line router swap feeds the per-tenant registry to `build_handler`. Same-name tenant skill shadows the bundled one (override-by-name); others add.

The design constraint that shaped everything: **`build_handler` already consumed a `skill_registry` parameter since 57.113** (`api/v1/chat/handler.py` `build_real_llm_handler` uses it exactly twice — `make_default_executor(skill_registry=…)` + `render_catalog_block(skill_registry.list())`). So the entire backend wiring blast radius was **one line** (the router swap); `handler.py` / `make_default_executor` / `loop.py` are byte-unchanged.

---

## 2. Decision matrix — storage shape

| Option | Where | Pros | Cons | Decision |
|--------|-------|------|------|----------|
| **Dedicated `tenant_skills` table** | new table + RLS | clean per-row CRUD; `UNIQUE(tenant_id,name)` enforced in DB; RLS isolation; indexable | a migration + an ORM file | ✅ **CHOSEN** (user decision) — a skill is a first-class per-row entity with its own lifecycle (create/update/delete), not a settings blob |
| `tenants.meta_data["skills"]` JSONB | reuse the tenants row | no migration | no per-row uniqueness; no RLS-at-row; whole-blob read/write races; the model-policy/harness-policy precedent fits sparse *settings*, not a *collection* | ❌ rejected — collection-of-rows ≠ sparse-policy-blob (the 57.55/57.56 JSONB-on-registry precedent was for single sparse override maps) |

**RLS shape decision**: mirror the invites `0026` two-policy idiom (`USING` for read + `WITH CHECK` for insert) **minus the system-sentinel escape**. Invites needed a sentinel for the unauthenticated guest-token lookup; skills have **no cross-tenant / guest read path**, so strict `tenant_id = current_setting('app.current_tenant_id')` on both policies is correct and strictly more secure. Anchor: `infrastructure/db/migrations/versions/0030_tenant_skills.py`.

---

## 3. Verified invariants (file:line anchors)

### 3.1 Overlay is pure + override-by-name (Cat 5)
- `SkillRegistry.with_overlay(extra: Sequence[Skill]) -> SkillRegistry` at `backend/src/agent_harness/skills/registry.py:111`. Implementation: `{s.name: s for s in self.list()} | {s.name: s for s in extra}` → a NEW `SkillRegistry`. The bundled singleton is never mutated; same-name `extra` wins; `list()` order deterministic.
- **Verify**: `pytest backend/tests/unit/agent_harness/skills/test_skills_overlay.py` (5 cases: add / override / empty-extra==base / no-mutate-singleton / order).
- **Type lesson** (`Sequence[Skill]` not `list[Skill]`): a `list[...]` annotation inside a class that has a `list` method binds to the METHOD for any method defined AFTER `list` (Python name resolution). Use `Sequence` to avoid the shadow. (Day-0 emergent finding D-mypy-list-shadow.)

### 3.2 Resolver: TTL cache + fail-open (platform_layer)
- `resolve_tenant_skill_registry(db, tenant_id)` at `backend/src/platform_layer/skills/service.py:233`: db/tenant `None` → `get_default_skill_registry()`; cache hit → cached; else read RLS-scoped rows → `Skill(...)` list → `get_default_skill_registry().with_overlay(rows)`; **any exception → bundled** (fail-open — a broken tenant skill never breaks chat).
- `_SkillRegistryCache` at `service.py:199`: TTL, injectable `clock` (testable expiry); `invalidate_tenant_skill_registry(tenant_id)` at `service.py:255`; `reset_skill_registry_cache()` at `service.py:260` (test isolation, Risk Class C).
- **Verify**: `pytest backend/tests/unit/platform_layer/skills/test_resolve_tenant_skill_registry.py` (8 cases incl. cache-hit-no-DB, injectable-clock expiry, fail-open).
- Pattern parentage: mirrors `resolve_tenant_model_policy` / `_ModelPolicyCache` (Sprint 57.104) — router resolves before the sync `build_handler`.

### 3.3 Service: RLS-scoped CRUD + typed errors (platform_layer)
- `TenantSkillService` at `service.py:87`: `list_skills` (`:90`) / `create` (`:106`) / `update` (`:137`) / `delete` (`:178`), each `_set_tenant` per call (mirrors `TOTPService`/`InvitesService`). `DuplicateSkillError` (409, `:70`) on `UNIQUE(tenant_id,name)` violation; `SkillNotFoundError` (404, `:75`) on miss.
- **Verify**: `pytest backend/tests/unit/platform_layer/skills/test_tenant_skill_service.py` (7 cases incl. cross-tenant isolation under RLS, dup, miss×2).

### 3.4 Table + RLS (DB)
- `TenantSkill(Base, TenantScopedMixin)` at `infrastructure/db/models/skill.py:51`, `__tablename__ = "tenant_skills"` (`:54`), `UniqueConstraint("tenant_id","name", name="uq_tenant_skills_tenant_name")` (`:72`). `tenant_id` comes from `TenantScopedMixin` (`@declared_attr`); the migration declares the physical column + index.
- Migration `0030_tenant_skills.py`: `create_table` + index + `ENABLE`/`FORCE ROW LEVEL SECURITY` + `tenant_isolation_tenant_skills` (USING) + `tenant_insert_tenant_skills` (WITH CHECK), no sentinel. `downgrade` drops the table.
- **Verify**: `alembic upgrade head` + `alembic downgrade -1` reversible; `python backend/scripts/lint/run_all.py` → `check_rls_policies` green.

### 3.5 Admin CRUD + the pre-commit projection invariant (API)
- `api/v1/admin/tenants.py:1857-2038`: `SkillCreateRequest`/`SkillUpdateRequest` (`extra="forbid"` + kebab `_SKILL_NAME_RE` validator), `GET/POST /{id}/skills` + `PUT/DELETE /{id}/skills/{sid}`. Each mutation: `require_admin_platform_role` + `_load_tenant_or_404` + `append_audit("tenant_skill_*")` + `db.commit()` + `invalidate_tenant_skill_registry`.
- **Invariant**: `_project_skill(skill)` is called **before** `db.commit()` (e.g. `:1959`, `:1997`). `expire_on_commit` (the default) expires the ORM instance after commit; a post-commit attribute read issues a fresh SELECT in a NEW transaction that has no `app.current_tenant_id` set → the RLS `USING` policy hides the row → the read returns nothing / raises. The model-policy precedent never hit this (it projects from a plain dict), but a table-backed row does.
- **Verify**: `pytest backend/tests/integration/api/test_admin_tenant_skills.py` (13 cases incl. multi-tenant isolation + audit + cache-invalidate).

### 3.6 Router swap reaches 主流量 (約束 2)
- `api/v1/chat/router.py:136` imports `resolve_tenant_skill_registry` from `platform_layer.skills`; `:264` resolves the per-tenant registry (after `harness_policy`); `:308` passes it to `build_handler`.
- **Verify**: `pytest backend/tests/integration/api/test_skills_per_tenant_wiring.py` (3 cases: overlay reaches `loop._system_prompt`; no-custom == bundled byte-identical; override → `read_skill` returns the overridden body) + the drive-through (§5).

---

## 4. Cross-category contracts (17.md)

No NEW cross-category ABC contract. The seam is a **platform_layer composition** over the existing Cat-5 `SkillRegistry` (57.113) — the same shape as `resolve_tenant_model_policy` (57.104) and `resolve_tenant_harness_policy` (57.106), neither of which got a 17.md Contract row (they are per-request resolvers in `platform_layer`, not range-owned ABCs). `with_overlay` is a new method on the existing `SkillRegistry`, not a new contract. **Decision: no 17.md entry** (consistent with the model-policy / harness-policy resolver precedent). The `read_skill` tool + `SkillRegistry` themselves remain as recorded for 57.113.

---

## 5. Drive-through (real UI + real Azure gpt-5.2 + 2 tenants — ALL 3 legs PASS)

| Leg | Command path | Observed | Verdict |
|-----|--------------|----------|---------|
| A author→follow | tenant A tab adds `release-notes` → chat | `read_skill({"name":"release-notes"})` self-called → output `## Summary/## Highlights/## Upgrade steps` exactly; judge 0.99 | ✅ load+follow |
| B isolation | tenant B identical request | `read_skill` 0×, release-notes body not loaded; B's `code-review` → BUNDLED body | ✅ isolated |
| C override | tenant A adds `code-review` override → chat | `read_skill("code-review")` → OVERRIDDEN body → pure numbered checklist | ✅ override-by-name |

CRUD controls all driven (Add/Edit/Delete + Save-disabled-until-complete). Screenshots: `agent-harness-execution/phase-57/sprint-57-114/artifacts/sprint-57-114-leg{A,B,C}-*.png`. Reproduce: `POST /api/v1/auth/dev-login?tenant_code=<X>&email=<Y>` (dev only) → tenant-settings Skills tab → chat-v2 real_llm.

---

## 6. Open invariants (NOT verified this spike — deferred)

- **Per-tenant authoring richness** — bundled scripts / multi-file skill bundles (the CC `SKILL.md`-with-resources shape): NOT built. Only `{name, description, instructions}` text.
- **Slash-command invocation** + **Inspector skill affordance** + an **authoring UI beyond raw text**: deferred (carried in `next-phase-candidates.md`).
- **Skill body size / abuse limits**: `instructions` is `TEXT` (unbounded at DB; `min_length=1` only). No per-tenant skill-count quota. NOT verified under adversarial load.
- **Cache coherency across processes**: `_SkillRegistryCache` is in-process; a multi-worker deployment invalidates only the worker that served the mutation. Acceptable for the single-process dev/drive-through; a multi-worker deployment needs a shared invalidation signal (same latent limitation as `_ModelPolicyCache`, 57.104). NOT addressed.

## 7. Rollback

Revert the router swap (`router.py:264`+`:308` back to `get_default_skill_registry()`) → the system reverts to bundled-only (57.113 behavior) instantly; the `tenant_skills` table + admin endpoints + tab become dormant (no consumer). Drop the table via `alembic downgrade -1` if fully reverting. Est. < 30 min. The bundled set is the fail-open sentinel, so even a resolver bug degrades to bundled-only, never to a broken chat.

## 8. References

- `31-skills-system-spike.md` — the 57.113 bundled registry + `read_skill` + Available Skills block this overlays.
- `30-iam-mfa-spike.md` / model-policy (57.104) / harness-policy (57.106) — the `resolve_tenant_*` per-request resolver + admin-tab precedent.
- `.claude/rules/multi-tenant-data.md` — RLS two-policy + tenant_id 鐵律.
- CHANGE-081 — the 1-page change record.
