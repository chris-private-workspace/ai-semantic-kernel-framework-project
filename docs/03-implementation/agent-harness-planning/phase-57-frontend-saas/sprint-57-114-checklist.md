# Sprint 57.114 — Checklist (Per-Tenant Skills Catalog: a NEW `tenant_skills` table + RLS + `TenantSkillService` + a per-request `resolve_tenant_skill_registry` overlay (fail-open to bundled) + 4 admin CRUD endpoints + a 1-line router swap + a tenant-settings "Skills" tab — the second slice of the Skills System epic, closes `AD-Skills-Per-Tenant-Catalog`; authoring richness / slash command / wire event deferred)

[Plan](./sprint-57-114-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong incl. Prong 3 schema) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `be92ab08`) — catalogued in progress.md
- [x] **Prong 1 — path verify**: NEW absent (Glob-0) confirmed; EDIT present confirmed; design note 32 + CHANGE 081 free
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-build-handler-uses (CRITICAL)** 🟢: `build_real_llm_handler` uses the registry ONLY 2 ways (`:481` executor + `:489-492` catalog block) → router swap is the only backend wiring change
  - [x] **D-register-swap** 🟢: `router.py:299` passes `get_default_skill_registry()` (sole use) → swap + drop orphan import
  - [x] **D-resolver-template** 🟢: `_ModelPolicyCache` shape (get/put/invalidate/clear/reset) + `resolve_session_persona` fail-open mirrored
  - [x] **D-service-template** 🟢: `InvitesService`/`TOTPService` `_set_tenant` + stateless per-call + singleton mirrored
  - [x] **D-admin-template** 🟢 (recon): model/harness PUT/GET idiom + `require_admin_platform_role`/`_load_tenant_or_404`/`append_audit` (re-confirm exact lines at Day-2 2.2)
  - [x] **D-cross-category** 🟢: `platform_layer/ → agent_harness/` established (25+ imports); no reverse cycle
  - [x] **D-fe-tree (Prong-2.5)** (done Day-3 start): `TenantSettingsView` → 8 existing tab children all on the mockup-ui `Card`+`grid-main`+inline-token idiom; no shadcn-utility residue / no mockup-fidelity drift (admin-internal免). `SkillsTab` is a NEW child (no vintage drift). 🟢 GREEN — no scope expansion
- [x] **Prong 3 — schema verify** (NEW table):
  - [x] migration head `0029` → `0030` free (ls + alembic confirmed)
  - [x] RLS template `0026_invites.py` two-policy read; tenant_skills mirrors MINUS the sentinel escape (no guest path)
  - [x] `TenantScopedMixin` provides `tenant_id` via `@declared_attr` → ORM omits it, migration declares the physical column
  - [x] placement: NEW dedicated `infrastructure/db/models/skill.py` + registered in `models/__init__.py` for Alembic metadata
- [x] **Catalog drift** findings in progress.md Day 0 (9 D-IDs incl. emergent D-mypy-list-shadow)
- [x] **Go/no-go**: 🟢 GO — router-swap-only design confirmed; no scope shift > 20%

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-114-skills-per-tenant-catalog` (from `main` `be92ab08`) — HEAD confirmed on branch

---

## Day 1 — Backend: `with_overlay` + `tenant_skills` table/ORM/migration + `TenantSkillService` (US-1, US-2)

### 1.1 `SkillRegistry.with_overlay` (Cat 5, pure) ✅
- [x] **`agent_harness/skills/registry.py`** (EDIT): add `with_overlay(self, extra: list[Skill]) -> SkillRegistry` — name-keyed merge (`{s.name: s for s in self.list()} | {s.name: s for s in extra}`) → new `SkillRegistry`; same-name `extra` overrides; no mutation of `self` / the bundled singleton; deterministic `list()` order; MHist 1-line + WHY block
  - Verify: `mypy backend/src/agent_harness/skills/registry.py` 0 · `black --check`/`flake8` 0
- [x] **`tests/unit/agent_harness/skills/test_skills_overlay.py`** (NEW): base ∪ tenant-add (both present) · same-name override (tenant body wins) · empty extra == base · bundled singleton identity unchanged after overlay · order deterministic
  - DoD: tests pass; `pytest tests/unit/agent_harness/skills/test_skills_overlay.py -q`

### 1.2 `tenant_skills` table + `TenantSkill` ORM + migration 0030 ✅
- [x] **`infrastructure/db/models/skill.py`** (NEW, or identity.py per Day-0): `class TenantSkill(Base, TenantScopedMixin)` `__tablename__="tenant_skills"`; UUID PK (`server_default=text("gen_random_uuid()")`); `name VARCHAR(128)` / `description VARCHAR(512)` / `instructions TEXT` (all NOT NULL); `created_at`/`updated_at` (`server_default=func.now()`); `__table_args__` `UniqueConstraint("tenant_id","name", name="uq_tenant_skills_tenant_name")` + `Index("idx_tenant_skills_tenant","tenant_id")`; file header
- [x] **`infrastructure/db/models/__init__.py`** (EDIT if Alembic metadata requires): import `TenantSkill`
- [x] **`migrations/versions/0030_tenant_skills.py`** (NEW): `create_table` + `create_index` + `ENABLE`+`FORCE ROW LEVEL SECURITY` + `tenant_isolation_tenant_skills` (USING + sentinel) + `tenant_insert_tenant_skills` (WITH CHECK) — mirror invites 0026 exactly; `downgrade` drops the table; correct `down_revision=0029`
  - DoD: `alembic upgrade head` applies clean on a test DB; `alembic downgrade -1` reverses; `mypy`/`flake8` 0
  - Verify: a `select` smoke against the upgraded DB confirms the columns + the ORM maps

### 1.3 `TenantSkillService` (RLS-scoped CRUD) ✅
- [x] **`platform_layer/skills/__init__.py`** (NEW): re-exports (`TenantSkillService`, `tenant_skill_service`, `resolve_tenant_skill_registry`, `invalidate_tenant_skill_registry`, `reset_skill_registry_cache`, the typed errors)
- [x] **`platform_layer/skills/service.py`** (NEW — service half): `TenantSkillService` (stateless; module singleton `tenant_skill_service`); `_set_tenant` per method (mirror TOTPService); `list`/`create`/`update`/`delete` scoped by `(id, tenant_id)`; `DuplicateSkillError` (unique violation) + `SkillNotFoundError` (miss); file header + WHY
- [x] **`tests/unit/platform_layer/skills/test_tenant_skill_service.py`** (NEW): create→list→update→delete round-trip · cross-tenant isolation (A's row invisible under B's `_set_tenant` — RLS) · duplicate `(tenant_id,name)` → `DuplicateSkillError` · update/delete miss → `SkillNotFoundError`
  - DoD: tests pass; `pytest tests/unit/platform_layer/skills/test_tenant_skill_service.py -q`; mypy `src` 0

---

## Day 2 — Backend: resolver + cache + admin CRUD + router swap (US-3, US-4)

### 2.1 `resolve_tenant_skill_registry` + `_SkillRegistryCache` ✅ (done Day-1, same module)
- [x] **`platform_layer/skills/service.py`** (EDIT — resolver half): `_SkillRegistryCache` (TTL, injectable `clock`, `get`/`put`/`invalidate`/`clear`; module singleton `_cache`); `resolve_tenant_skill_registry(db, tenant_id)` — db/tenant None → `get_default_skill_registry()`; cache hit → return; else `try` list rows → `[Skill(...)]` → `get_default_skill_registry().with_overlay(...)`, `except` → bundled (fail-open); `put`+return; `invalidate_tenant_skill_registry` + `reset_skill_registry_cache`
- [x] **`tests/unit/platform_layer/skills/test_resolve_tenant_skill_registry.py`** (NEW): no rows → bundled set (fail-open) · db None → bundled · with rows → overlay present · TTL cache hit (2nd call no DB; injectable-clock expiry) · `invalidate` drops · `reset` clears
  - DoD: tests pass; mypy `src` 0

### 2.2 Admin CRUD endpoints ✅
- [x] **`api/v1/admin/tenants.py`** (EDIT): Pydantic `SkillCreateRequest`/`SkillUpdateRequest` (`extra="forbid"`)/`SkillResponse`/`SkillListResponse`; 4 endpoints — `GET /{tenant_id}/skills` (list, no audit) · `POST` (create, validate kebab `name`/non-empty, `DuplicateSkillError`→409) · `PUT /{tenant_id}/skills/{skill_id}` (update, `SkillNotFoundError`→404) · `DELETE …/{skill_id}` (→204); each `require_admin_platform_role` + `_load_tenant_or_404` + `append_audit("tenant_skill_*")` + `commit` + `invalidate_tenant_skill_registry`
- [x] **`tests/integration/api/test_admin_tenant_skills.py`** (NEW, ×13) + conftest `SKILL_ADMIN_%` sweep + `reset_skill_registry_cache`: create→list→update→delete happy path · `require_admin_platform_role` 401/403 non-admin · **multi-tenant mandatory** (cross-tenant read 404 / cross-tenant write 404 / RLS enforced — per `.claude/rules/multi-tenant-data.md`) · audit row per mutation · cache invalidated (create then `resolve_tenant_skill_registry` reflects) · duplicate-name → 409
  - DoD: tests pass; `pytest tests/integration/api/test_admin_tenant_skills.py -q`

### 2.3 Router swap (主流量, 約束 2) ✅
- [x] **`api/v1/chat/router.py`** (EDIT): after `harness_policy = await resolve_tenant_harness_policy(...)`, add `skill_registry = await resolve_tenant_skill_registry(db, current_tenant)`; change the `build_handler(...)` `skill_registry=get_default_skill_registry()` → `skill_registry=skill_registry`; drop the `get_default_skill_registry` import iff orphaned; comment
- [x] **`tests/integration/api/test_skills_per_tenant_wiring.py`** (NEW, ×3): router resolves the overlay → `build_handler` system text includes a tenant custom skill · a stubbed-LLM `read_skill("<custom>")` returns the custom body · a no-custom-skill tenant is byte-identical to the bundled path (regression)
  - DoD: tests pass; `build_handler`/`make_default_executor`/`handler.py` diff empty (only `router.py` changed)

### 2.4 Backend gate sweep ✅
- [x] mypy `src` 0 · black/isort/flake8 0 · `python scripts/lint/run_all.py` **10/10** (count 24) · full pytest **2602+5skip (+36, 0 del)** vs 2566 · `loop.py`/`handler.py`/`make_default_executor`/wire/codegen UNTOUCHED · migration 0030 the only new migration
  - Verify: `cd backend && mypy . && python scripts/lint/run_all.py && pytest -q`

---

## Day 3 — Frontend: tenant-settings "Skills" tab (US-5)

### 3.1 Service + types ✅
- [x] **`features/tenant-settings/types.ts`** (EDIT): `Skill{id,name,description,instructions,created_at,updated_at}` · `SkillListResponse{skills:Skill[]}` · `SkillCreateRequest` · `SkillUpdateRequest`
  - **Decision**: snake_case direct (`created_at`/`updated_at`) mirroring sibling list-resources (`TenantMemberItem`/`QuotaItem`/`FeatureFlagItem`), NOT camelCase + mapper (that's the sparse policy value-object idiom — overkill for a simple list-CRUD)
- [x] **`features/tenant-settings/services/tenantSettingsService.ts`** (EDIT): `fetchTenantSkills` · `createTenantSkill` · `updateTenantSkill` · `deleteTenantSkill` (all via `fetchWithAuth` + `_handleResponse`; DELETE replicates the error-detail extraction since 204 has no body)

### 3.2 SkillsTab + tab registration ✅
- [x] **`features/tenant-settings/hooks/useTenantSkills.ts`** (NEW, one cohesive 4-op module): `useTenantSkills` read + `useTenantSkill{Create,Update,Delete}` mutations (each invalidates the read)
- [x] **`features/tenant-settings/components/tabs/SkillsTab.tsx`** (NEW): list-CRUD — rows in `<Card title="Skills">` · "+ Add skill" toggle → inline form (name + description + instructions `<textarea>`) · per-row Edit(draft)/Save + Delete(inline 2-step confirm) · loading/empty/error (`var(--danger)`) · Save disabled until all 3 fields filled · `data-testid` on each control · mockup-ui `Card`+`grid-main`+inline tokens only · English copy
- [x] **`features/tenant-settings/components/TenantSettingsView.tsx`** (EDIT): `TabId += "skills"` · `TAB_ITEMS += {id:"skills",label:"Skills"}` (after harness, 9th) · `{tab === "skills" && <SkillsTab tenantId={tenantId} />}` · import
  - DoD: `npm run build` clean; the tab renders + switches ✅

### 3.3 Vitest + FE gates ✅
- [x] **`tests/unit/tenant-settings/tabs/SkillsTab.test.tsx`** (NEW, ×11) — **path corrected** (vite.config `include: tests/unit/**`, NOT co-located `__tests__/`): title · loading · load-error · empty · lists rows · Add opens form (3 fields) · Save disabled-until-complete + create-mutate · create error inline · Edit seeds + update-mutate · Delete 2-step confirm + delete-mutate · delete error inline
- [x] FE gates: `npm run lint` (NO `--silent`) 0 error · `npm run build` clean · `npm run test` Vitest **851 (+11 vs 840)** · `npm run check:mockup-fidelity` **51** holds (admin-internal, no mockup CSS)
  - Verify: `cd frontend && npm run lint && npm run build && npm run test && npm run check:mockup-fidelity`

---

## Day 4 — Multi-tenant drive-through (US-6) + CHANGE-081 + design note 32 + closeout

### 4.1 Drive-through (real chat-v2 :3007 + fresh single-process backend + real Azure LLM; Risk Class E clean restart; multi-tenant)
- [ ] **Clean restart + probe**: orphan sweep (`Win32_Process` PID/PPID/StartTime) → fresh no-reload backend sole owner of :8000; confirm migration 0030 applied; confirm a SECOND tenant login for the isolation leg
- [ ] **Leg A (author→appears→loaded→followed) PASS**: admin → tenant A Skills tab → add `release-notes` (distinctive shape) → Save → A's chat-v2 asks a matching request → `read_skill("release-notes")` (Inspector visible) → output in the custom shape. Screenshot
- [ ] **Leg B (isolation + bundled intact) PASS**: tenant B's chat — `release-notes` NOT in Available Skills + no `read_skill("release-notes")`; a B `code-review` request still loads the BUNDLED `code-review`. Screenshot
- [ ] **Leg C (override-by-name) PASS**: admin → tenant A add a `code-review` override (different instructions, e.g. numbered-checklist-only) → Save → A's chat code-review request → `read_skill("code-review")` returns the OVERRIDDEN body → output follows the overridden shape. Screenshot
- [ ] Each tab control verified to PERSIST + invalidate (the next chat turn reflects the change); no dead control / no fixture / no mislabeled output (Drive-Through-Acceptance); screenshots in `artifacts/` + observed-vs-intended in progress.md; teardown
  - DoD: per-tenant overlay + isolation + override drivable e2e on real UI+backend+LLM; output shape distinctly follows the per-tenant/overridden skill (load+follow + isolation proven, AP-4 guard)

### 4.2 CHANGE-081 + design note 32
- [ ] **`claudedocs/4-changes/feature-changes/CHANGE-081-skills-per-tenant-catalog.md`** (1-page, incl. the 3-leg multi-tenant drive-through)
- [ ] **Design note `32-skills-per-tenant-catalog.md`** (§5.5 8-point quality gate — the FIRST DB-backed per-tenant overlay of a Cat-5 registry pattern; file:line anchors; decision matrix table vs JSONB; verified ratio ≥ 95%)

### 4.3 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (NEW `per-tenant-catalog-table-backed` 0.60 1st data point — ratio + IN/OUT band verdict; agent-delegated: partial blended) + progress.md final
- [ ] Navigators: CLAUDE.md Current-Sprint row + Last-Updated (minimal touch); MEMORY.md quality pointer + memory subfile `project_phase57_114_skills_per_tenant_catalog.md`; next-phase-candidates — `AD-Skills-Per-Tenant-Catalog` CLOSED + remaining Skills ADs carried; sprint-workflow matrix NEW `per-tenant-catalog-table-backed` 0.60 1st data point; 17.md — add the `TenantSkillService`/`resolve_tenant_skill_registry` seam if it warrants a contract (else N/A, noted in the design note)
- [ ] **Anti-pattern self-check** (retro Q5/Q7): AP-4 (drive-through proves load+follow + isolation, not stub) · AP-2 (reachable from the router→build_handler main flow) · AP-3 (overlay in Cat 5 / DB service in platform_layer / endpoints in admin — no scattering) · multi-tenant 鐵律 (tenant_id + RLS + the 3 mandatory tests)
- [ ] PR (push + open on user authorization)
