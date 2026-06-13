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

---

## Day 3 — Frontend: tenant-settings "Skills" tab (US-5) (2026-06-13)

### Prong-2.5 child-tree audit (deferred from Day 0)
- `TenantSettingsView` → 8 existing tab children (General/FF/Quotas/Model/Harness/HITL/Members/Danger) all on the mockup-ui `Card`+`grid-main`+inline-token idiom; no shadcn-utility residue, no mockup-fidelity drift (admin-internal免 mockup-fidelity). `SkillsTab` is a NEW 9th child → no vintage drift to audit. 🟢 GREEN, no scope expansion.

### Accomplishments (US-5)
- **types.ts** (EDIT) — `Skill{id,name,description,instructions,created_at,updated_at}` + `SkillListResponse{skills}` + `SkillCreateRequest` + `SkillUpdateRequest`. **Decision**: snake_case direct (mirrors `TenantMemberItem`/`QuotaItem`/`FeatureFlagItem` list-resource idiom), NOT camelCase+mapper (that's the sparse policy value-object idiom — overkill for a simple list-CRUD).
- **tenantSettingsService.ts** (EDIT) — `fetchTenantSkills`/`createTenantSkill`/`updateTenantSkill`/`deleteTenantSkill` via `fetchWithAuth` + `_handleResponse`. DELETE replicates the error-detail extraction inline (204 has no body so `_handleResponse`'s `.json()` would throw on success).
- **useTenantSkills.ts** (NEW) — one cohesive 4-op module: `useTenantSkills` read + `useTenantSkill{Create,Update,Delete}` mutations; each invalidates `[...TENANT_SKILLS_QUERY_KEY_BASE, tenantId]`.
- **SkillsTab.tsx** (NEW) — list-CRUD: "+ Add skill" toggle → inline create form (name + description + instructions `<textarea>`); per-row Edit (inline seeded form, one open at a time) + Delete (inline 2-step confirm); Save disabled until all 3 fields non-blank; create/update/delete errors surface inline (`var(--danger)`); loading/empty/error states; `data-testid` on every control. mockup-ui `Card`+`Button` + `btn-secondary`/`btn-primary` + inline tokens only; English copy. Mirrors QuotasTab idioms.
- **TenantSettingsView.tsx** (EDIT) — `TabId += "skills"`, `TAB_ITEMS += {id,label:"Skills"}` (9th, after Harness Policy), render guard + import.
- **SkillsTab.test.tsx** (NEW, ×11) — at `tests/unit/tenant-settings/tabs/` (**path corrected** from the checklist's co-located `__tests__/` — vite.config `include: tests/unit/**`). Mirrors `ModelPolicyTab.test.tsx` mock harness (vi.mock the hooks module).

### Gate (Day-3 — frontend complete)
- `npm run lint` (no `--silent`) **0 error** (only pre-existing jsx-ast-utils TSSatisfiesExpression noise) · `npm run build` **clean** (3.31s) · `npm run test` Vitest **851 passed (+11 vs 840; 138 files)** · `npm run check:mockup-fidelity` **51** holds (byte-identical + 51 baseline).
- An incidental stderr stack trace in the full Vitest run is from a pre-existing test's error-path render (NOT SkillsTab — isolated run = 11/11 clean, no console errors).

### Notes
- One lint fix mid-Day-3: the multi-line `style={{` panels need the `// eslint-disable-next-line no-restricted-syntax` directly above the `style=` line (not above the `<div` opening tag) — `eslint-disable-next-line` targets the line where the `no-restricted-syntax` node (the `style` attribute) actually sits. Single-line `style=` is fine on the same line as the element.
- No backend change Day 3 (`router.py`/`handler.py`/`loop.py` still UNTOUCHED). The tab is fully backed by the Day-2 admin CRUD endpoints.

---

## Day 4 — Multi-tenant drive-through (US-6) + closeout (2026-06-13)

### Clean restart (Risk Class E)
- Orphan sweep via `Get-CimInstance Win32_Process`: **ZERO python.exe processes** (no stale spawn-worker) + :8000 free; :3007 owned by the live frontend node (untouched). One stale MCP-profile Chrome (7 PIDs holding `mcp-chrome-903abde`) killed to free the Playwright browser.
- Fresh **no-reload single-process** backend (`PYTHONPATH=src python -m uvicorn api.main:app --port 8000`) PID 38756, sole owner of :8000. Startup log: `Application startup complete` + pricing loader / rate-limit counter / SLA recorder / billing outbox all wired, **0 error**.
- Migration `0030_tenant_skills` confirmed head + applied (`alembic current`). Two tenants via `POST /auth/dev-login` (roles `[user,admin,platform_admin]`): `acme-skills` (A) + `globex-skills` (B), both auto-created.

### Drive-through — ALL 3 legs PASS (real chat-v2 :3007 + real Azure gpt-5.2, provider:neutral)

| Leg | Observed vs intended | Verdict |
|-----|----------------------|---------|
| **A — author→appears→loaded→followed** | Admin (A) Skills tab → "+ Add skill" → `release-notes` (3-header instructions) → Save → list row appeared (cache invalidated). A's chat "Write release notes…" → model self-called `read_skill({"name":"release-notes"})` (Inspector tool card + Loop trace `tool_call_request: read_skill`) → loaded the tenant's body verbatim → answer followed EXACTLY `## Summary / ## Highlights / ## Upgrade steps`; verification llm_judge 0.99. | ✅ load+follow |
| **B — isolation + bundled intact** | B (globex-skills) identical release-notes request → **`read_skill` called 0×, `# Skill: release-notes` NOT loaded** (A's skill did not leak — RLS-scoped resolver). A separate B `code-review` request → `read_skill("code-review")` loaded the **BUNDLED** body (`# Code Review … report findings in this exact structure`), `isTenantAOverride:false`. | ✅ isolated + bundled intact |
| **C — override-by-name** | A add `code-review` override (`RESPOND ONLY WITH A NUMBERED CHECKLIST…`) → Save (list 2 rows, alphabetical) → A's chat code-review → `read_skill("code-review")` returned the **OVERRIDDEN** body (`loadedBundledShape:false`) → output a pure 7-line numbered checklist (no headers/table). Contrast with Leg B same name → bundled. | ✅ override shadows bundled |

### Control-by-control (Drive-Through-Acceptance — no dead control / no fixture / real LLM)
- **Add** (create): form opens, 3 fields, Save disabled until all 3 non-blank, create→persist→list re-fetch→next chat reflects (cache invalidate proven e2e). ✅
- **Edit** (update): `release-notes` description edited → Save → list shows `EDITED…` + form auto-closed. ✅
- **Delete** (2-step confirm): `code-review` Delete → Confirm affordance → Confirm → row gone (list back to 1). ✅
- Persistence across re-login: A's `release-notes` survived a tenant B round-trip + re-login (still listed). ✅

Screenshots in `artifacts/`: `legA-skills-tab-created.png`, `legA-chat-readskill-followed.png`, `legB-isolation-no-readskill.png`, `legB-bundled-codereview-intact.png`, `legC-override-created.png`, `legC-override-followed-checklist.png`.

### Notes
- The sidebar tenant-switcher chip still shows the `acme-prod / Pro` fixture (known `AD-FE-Tenant-Display-Fixture-Phase58`); the tenant-settings **page header + content** correctly showed the real `Dev Tenant (acme-skills)` / `acme-skills` from the authStore — the real tenant scoping was honored end-to-end (the chat read the right per-tenant overlay).
- `llm_request tokens_in=0` in the trace is the known `AD-LLMRequest-TokensIn-Zero` display nuance (the Inspector turn metadata showed the real `tokens.in 2,428`); unrelated to skills.
