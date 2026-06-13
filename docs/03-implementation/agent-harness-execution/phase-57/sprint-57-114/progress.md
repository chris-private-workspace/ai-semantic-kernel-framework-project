# Sprint 57.114 Progress — Per-Tenant Skills Catalog

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-114-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-114-checklist.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch (2026-06-13)

### Drift findings (三-prong, against `main` HEAD `be92ab08`)

| ID | Prong | Finding | Verdict / Implication |
|----|-------|---------|-----------------------|
| D-build-handler-uses | 2 (CRITICAL) | `build_real_llm_handler` uses `skill_registry` in EXACTLY 2 ways — `handler.py:481` → `make_default_executor(skill_registry=…)` + `:489-492` → `render_catalog_block(skill_registry.list())` on `system_prompt`; `build_handler` threads it at `:776`. No 3rd use. | 🟢 GREEN — **the router swap is the ONLY backend wiring change**; `handler.py`/`_register_all.py` UNTOUCHED |
| D-register-swap | 1 | `router.py:108` imports `get_default_skill_registry`, `:299` passes it to `build_handler` (its sole use), `:256` resolves harness_policy | 🟢 GREEN — insert resolver after `:256`, swap `:299`, drop the now-orphan import |
| D-migration-head | 3 | `ls versions/ \| sort -V \| tail` → `0029_user_mfa_totp` is head | 🟢 GREEN — `0030` free; applied + downgrade-reversed clean |
| D-cross-category | 2 | `platform_layer/ → agent_harness/` is an established pattern (25+ existing imports: governance/resume/handoff/observability) | 🟢 GREEN — `platform_layer/skills/` may import `agent_harness.skills` |
| D-rls-template | 3 | invites `0026` uses a two-policy RLS WITH a system-sentinel escape (for the guest token lookup) | 🟡 ADAPT — `tenant_skills` mirrors the two-policy idiom MINUS the sentinel escape (no guest/cross-tenant lookup → strict per-tenant is correct + more secure) |
| D-tenantscoped-mixin | 3 | `TenantScopedMixin` provides `tenant_id` via `@declared_attr` (FK + index) | 🟢 GREEN — the ORM does NOT declare `tenant_id`; the migration declares the physical column |
| D-placement | 3 | `09-db-schema-design` groups tenant-scoped tables; identity.py is the precedent but a domain file is allowed | 🟢 DECISION — `TenantSkill` in a NEW dedicated `infrastructure/db/models/skill.py` (cleaner domain split) + registered in `models/__init__.py` for Alembic metadata |
| D-test-rls-convention | 2 | `test_rbac.py:17-19` — unit tests assert app-level scoping; raw RLS is integration-only | 🟢 GREEN — unit service test asserts tenant-scoped `list_skills`; mandatory raw multi-tenant cases → Day-2 integration test |
| D-mypy-list-shadow | (Day-1 emergent) | `list[Skill]` annotation inside `SkillRegistry` resolves to the `list` METHOD (shadowing) for methods defined AFTER `list`; the existing `list` method's own `-> list[Skill]` escaped it (resolved before `list` is bound) | 🟡 FIXED — annotate `with_overlay(extra: Sequence[Skill])` to avoid the shadowed name (reusable lesson) |

**Go/no-go**: 🟢 GO — D-build-handler-uses confirms the elegant router-swap-only design; no scope shift > 20%.

### Branch
- `feature/sprint-57-114-skills-per-tenant-catalog` from `main` `be92ab08` ✅

---

## Day 1 — Backend: overlay + table/ORM/migration + service + resolver (2026-06-13)

### Accomplishments (US-1, US-2, US-3 + Day-2 US-3 resolver pulled forward)

- **US-1 `SkillRegistry.with_overlay`** — pure override-by-name overlay (`{base} | {extra}` name-keyed merge → fresh registry; no mutation of base/singleton; deterministic order). `registry.py` EDIT + MHist.
- **US-2 table/ORM/migration** — `infrastructure/db/models/skill.py:TenantSkill` (NEW, TenantScopedMixin; unique `(tenant_id, name)`); `migrations/versions/0030_tenant_skills.py` (NEW; table + index + RLS two-policy, no sentinel); `models/__init__.py` EDIT (import + `__all__`). Migration applies + `downgrade -1`/`upgrade head` reversible.
- **US-2 `TenantSkillService`** — `platform_layer/skills/service.py` (NEW): `list_skills`/`create`/`update`/`delete` RLS-scoped CRUD (`_set_tenant` per method, mirror InvitesService); typed `DuplicateSkillError` (409) + `SkillNotFoundError` (404). `platform_layer/skills/__init__.py` re-exports.
- **US-3 resolver (pulled fwd from Day-2 2.1)** — `resolve_tenant_skill_registry` (TTL-cached `_SkillRegistryCache` injectable-clock; fail-open to `get_default_skill_registry()`); `invalidate_*` + `reset_*`. Written in the same `service.py` (cohesive module).
- **Tests (20, all pass)** — `test_skills_overlay.py` (5: add/override/empty/no-mutate/order) · `test_tenant_skill_service.py` (7: CRUD round-trip/order/dup/clash/miss×2/scoping; real Postgres via `db_session`) · `test_resolve_tenant_skill_registry.py` (8: db-None/no-rows/overlay/override/fail-open/cache-hit/invalidate/TTL-clock).

### Gate (Day-1 partial)
- mypy `src` (skills modules) **0** · black/isort/flake8 **0** · new unit tests **20 pass** · migration 0030 applies + reversible.
- `loop.py` / `build_handler` / `make_default_executor` / `handler.py` / wire / codegen UNTOUCHED so far (router swap is Day-2).

### Notes
- Backend wiring blast radius confirmed at **1 line** (the Day-2 router swap) — `build_handler` already consumes whatever registry is passed.
- D-mypy-list-shadow is a reusable lesson: a `list[...]` annotation inside a class with a `list` method silently binds to the method for any method defined after it; prefer `Sequence[...]`.

---

## Day 2 — Backend: admin CRUD + router swap (2026-06-13)

### Accomplishments (US-4 + the already-done US-3 resolver)

- **US-4 admin CRUD** — `api/v1/admin/tenants.py`: 4 endpoints (`GET /{tid}/skills` list · `POST` create 201 · `PUT /{tid}/skills/{sid}` update · `DELETE …/{sid}` 204), each `require_admin_platform_role` + `_load_tenant_or_404` + `append_audit("tenant_skill_*")` + `db.commit()` + `invalidate_tenant_skill_registry`. Pydantic `SkillCreateRequest`/`SkillUpdateRequest` (`extra="forbid"` + kebab-name validator + min/max lengths) / `SkillResponse` / `SkillListResponse`. Typed errors → HTTPException (409 dup / 404 miss).
  - **Design note (post-commit RLS)**: the response is projected **before** `db.commit()` — `expire_on_commit` would otherwise reload the RLS-protected `tenant_skills` row under no tenant ctx (new txn) and fail. The model-policy precedent projects from a plain dict so it doesn't hit this; the table-backed catalog does.
- **US-4 router swap** — `api/v1/chat/router.py`: `skill_registry = await resolve_tenant_skill_registry(db, current_tenant)` (after harness_policy) → passed to `build_handler` (replaces `get_default_skill_registry()`); import swapped (`agent_harness.skills` → `platform_layer.skills`, isort-regrouped). `handler.py`/`make_default_executor`/`loop.py` **UNTOUCHED** (verified `git status` empty).
- **conftest** — `tests/integration/api/conftest.py`: `SKILL_ADMIN_%` committed-tenant sweep + `reset_skill_registry_cache()` in both reset fixtures (Risk Class C).
- **Tests (16, all pass)** — `test_admin_tenant_skills.py` (13: auth 401/403 · tenant-404 · create-201+list · dup-409 · non-kebab-422 · extra-field-422 · update-200 · update-404 · delete-204 · delete-404 · **multi-tenant isolation** (B never lists A's skill + cross-tenant PUT → 404) · audit-emitted · **cache-invalidated**) · `test_skills_per_tenant_wiring.py` (3: overlay reaches `loop._system_prompt` · no-custom == bundled byte-identical · tenant override → `read_skill` returns overridden body).

### Gate (Day-2 — backend complete)
- mypy `src` (changed) **0** · black/isort/flake8 **0** · `scripts/lint/run_all.py` **10/10** (count 24; cross-category + RLS + LLM-neutrality green) · full pytest **2602+5skip** (+36 vs 2566, 0 del) · `handler.py`/`make_default_executor`/`loop.py`/wire/codegen **UNTOUCHED** · migration 0030 reversible.

### Notes
- `check_rls_policies` green on the new `tenant_skills` two-policy (strict per-tenant, no sentinel).
- Multi-tenant mandatory cases land at the **endpoint** level (per `test_rbac.py` convention: unit = app-scoping, integration = endpoint isolation): cross-tenant read → empty list; cross-tenant write → 404.
