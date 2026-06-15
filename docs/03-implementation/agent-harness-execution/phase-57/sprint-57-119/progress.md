# Sprint 57.119 Progress — Skills System Visibility + Preview

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-119-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-119-checklist.md)

**Slice**: the chosen thin vertical of `AD-Skills-Authoring-UI` (AskUserQuestion 2026-06-15: **System skills 可見 + preview** over versioning / hot-reload). A read-only "System Skills" section in the admin Skills tab (bundled catalog + a "🔧 script" badge + a "shadowed by your skill" tag) + a Preview modal rendering any skill's full instructions. ONE read-only `GET /admin/tenants/{id}/skills/system` + a TanStack read hook + a read-only tab section + a Preview modal. NO DB / migration / wire / codegen. Feature continuation (NO design note). CHANGE-086.

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — 2026-06-15

### Prong 1 — path verify (against `main` HEAD `cf83b274`)
- ✅ All 5 EDIT targets exist: `api/v1/admin/tenants.py` · `types.ts` · `tenantSettingsService.ts` · `useTenantSkills.ts` · `SkillsTab.tsx`.
- ✅ Backend test `tests/integration/api/test_admin_tenant_skills.py` exists (EDIT).
- ✅ `CHANGE-086-*.md` free; no design note (feature continuation).
- 🔧 **D-fe-test-path** (drift): the FE SkillsTab test is NOT co-located. Actual: **`frontend/tests/unit/tenant-settings/tabs/SkillsTab.test.tsx`** (the project's FE tests live under `frontend/tests/unit/...`, not next to source — the 57.114 `FE-test-path-tests/unit-not-__tests__` lesson). File Change List #7 path corrected to this.

### Prong 2 — content verify (drift findings)
- ✅ **D-skills-routes**: `tenants.py` `SkillResponse` (`:1894`) / `SkillListResponse` (`:1905`) / `_project_skill` (`:1915`) / `GET /{tenant_id}/skills` → `list_tenant_skills` (`:1926`, deps `get_db_session` + `require_admin_platform_role` + `_load_tenant_or_404` + `tenant_skill_service.list_skills`). Confirmed the shape + auth to mirror for the system endpoint.
- ✅ **D-registry-list**: `get_default_skill_registry()` (`registry.py:189-194`) `.list()` → `Skill` objects carrying `.script` (57.118) → `has_script = s.script is not None`. Exported from `agent_harness.skills` (`__init__.py:15,31`).
- ✅ **D-cross-cat-import** (the #1 lint risk RESOLVED): `api/v1/chat/handler.py:96` ALREADY does `from agent_harness.skills import render_catalog_block, render_skill_instructions` + `:135` `SkillRegistry`; `router.py:465` projects `[ChatSkillItem(name=s.name, description=s.description) for s in registry.list()]` — the EXACT api→Cat-5-registry pattern to mirror. So `from agent_harness.skills import get_default_skill_registry` in `api/v1/admin/tenants.py` follows an established green precedent → `check_cross_category_import` clean.
- ✅ **D-fe-datalayer**: `fetchTenantSkills` (`tenantSettingsService.ts:458`) = `fetchWithAuth(`${API_BASE}/tenants/${tenantId}/skills`, {method:"GET", signal})` → `_handleResponse<SkillListResponse>` — mirror for `fetchSystemSkills`. `useTenantSkills` (`useTenantSkills.ts:48`) = `useQuery<SkillListResponse, Error>({ queryKey: [...TENANT_SKILLS_QUERY_KEY_BASE, tenantId], ... })` — add a `useSystemSkills` with a `["tenant-skills-system", tenantId]` key.
- ✅ **D-skillstab**: `SkillsTab.tsx` (`:68-458`) — a single `<Card title="Skills">` with the hint + count/Add row + add-form + the tenant list row map (`:336-452`). Insert a sibling Card "System Skills" + a `previewSkill` state + an inline overlay modal; add a Preview button to the tenant rows. No disturbance to the 57.114/117 idioms.
- 🔧 **D-modal-primitive** (confirmed contingency): `components/mockup-ui/` has NO `Modal`/`Dialog`/`Overlay` primitive → use an inline fixed-overlay panel (mirror the inline-form `var(--border)`/`var(--radius)`/`var(--shadow)` idiom; the 57.115 `SkillSlashMenu` greenfield-overlay precedent). NO new dependency.

### Prong 3 — N/A (no new table / migration / ORM — read-only over the existing registry + the existing `tenant_skills` read)

### Baselines (HEAD `cf83b274`, carried from 57.118 closeout; re-verify deltas at Day 2)
- full pytest **2644 passed, 5 skipped** · wire **24** · mypy `src` **0/371** · run_all **10/10** · mockup-fidelity **51** · FE Vitest **873 passed (142 files)** ✅ (confirmed at HEAD — matches the plan baseline).

### Catalog — drift summary
- 2 drifts, both PATH/contingency (non-scope-shifting): D-fe-test-path (test under `frontend/tests/unit/...`) + D-modal-primitive (no Modal → inline overlay, as planned). The #1 lint risk (api→Cat-5 import) RESOLVED green via the `handler.py:96` precedent.

### Go/no-go: 🟢 **GO** — the design holds end-to-end (one read-only GET over `get_default_skill_registry()` mirroring `list_tenant_skills`; the FE data layer + tab section + inline-overlay preview mirror established idioms; `check_cross_category_import` precedent confirmed green). No scope shift > 20%.

### Branch
- ✅ `git checkout -b feature/sprint-57-119-skills-system-visibility` (from `main` `cf83b274`).

## Day 1 — Backend: the system-skills read endpoint (US-1) — 2026-06-15

**`api/v1/admin/tenants.py`** (EDIT): `SystemSkillResponse` (`name`/`description`/`instructions`/`has_script`/`overridden`) + `SystemSkillListResponse` (`skills: list[...]`) + `GET /{tenant_id}/skills/system` → `list_system_skills` (same deps as `list_tenant_skills`: `get_db_session` + `require_admin_platform_role` + `_load_tenant_or_404`). Loads `tenant_names = {row.name for row in await tenant_skill_service.list_skills(db, tenant_id=tenant_id)}` + `bundled = get_default_skill_registry().list()`; projects each with `has_script = skill.script is not None` + `overridden = skill.name in tenant_names`. Read-only, no audit. Imported `get_default_skill_registry` from `agent_harness.skills` (the `handler.py:96` api→Cat-5 precedent → `check_cross_category_import` green). MHist + Last Modified updated.

**`tests/integration/api/test_admin_tenant_skills.py`** (EDIT +4): `test_system_skills_lists_bundled` (the 3 bundled skills; `digest.has_script` True, `code-review`/`summarize` False; instructions present; nothing overridden) · `test_system_skills_overridden_flag` (a tenant skill named `code-review` → `overridden` True for it only) · `test_system_skills_requires_admin` (no override → 401/403) · `test_system_skills_tenant_not_found` (bad tenant → 404). Scope header += 57.119.

**Gate (Day 1)**: mypy `src` **0/371** (Success) · black/isort/flake8 0 (the 1 E501 on the response docstring trimmed) · the 4 new system-skills tests **4 passed** (`pytest -k system`). `registry.py` UNTOUCHED (read-only consumer).

## Day 2 — Frontend: data layer + System Skills section + Preview modal (US-2/3/4/5) — 2026-06-15

**Data layer (US-2)**: `types.ts` += `SystemSkill` (`name`/`description`/`instructions`/`has_script`/`overridden`) + `SystemSkillListResponse`. `tenantSettingsService.ts` += `fetchSystemSkills(tenantId)` (mirrors `fetchTenantSkills`). `useTenantSkills.ts` += `useSystemSkills(tenantId)` (own `SYSTEM_SKILLS_QUERY_KEY_BASE` — the static bundled set needs no mutation invalidation).

**System Skills section + Preview modal (US-3/4)**: `SkillsTab.tsx` += a sibling `<Card title="System Skills">` (read-only) listing each bundled skill — name + a "🔧 script" badge (`has_script`) + a "shadowed by your skill" tag (`overridden`) + a Preview button; NO edit/delete. Plus a `previewSkill` state + an inline-overlay Preview modal (no `Modal` primitive in mockup-ui — D-modal-primitive) rendering any skill's `instructions` in a mono `<pre>`; a Preview button on the tenant rows too. **a11y**: followed the `TenantMembersDrawer` convention — a window Escape-key `useEffect` + `role="dialog"`/`aria-label` on the panel + the matching `jsx-a11y/click-events-have-key-events, jsx-a11y/no-(static|noninteractive)-element-interactions` disables on the backdrop + stop-propagation panel. Tokens `var(--bg)`/`var(--border)`/`var(--radius)`/`var(--shadow)` (the drawer's `--bg`, not a `--background` guess).

**Tests (US-5)**: `SkillsTab.test.tsx` +6 — section render / has-script badge on `digest` only / shadowed tag when overridden / Preview opens+shows instructions / tenant-row Preview + Close dismiss / system load-error. **D-fe-test-path fix**: the file is at `frontend/tests/unit/tenant-settings/tabs/` (NOT co-located). `mockSystemSkills` added to BOTH describe `beforeEach` (the component now calls `useSystemSkills` in every render → the existing 15 would crash without a default mock).

**Gate (Day 2)**: mypy `src` **0/371** · black/isort/flake8 0 · `run_all` **10/10** (count 24, no codegen) · `npm run lint` clean (the 4 jsx-a11y modal errors fixed) · `npm run build` ✅ (tsc — the 57.116 build-not-just-Vitest discipline) · Vitest **879 (142 files)** (+6 vs 873) · mockup-fidelity **51** (byte-identical + 51 baseline; no CSS) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · `check_cross_category_import` green (api→Cat-5 read).

## Day 3 — Drive-through (real admin Skills tab + real backend) — 2026-06-15

**Setup (Risk Class E clean restart)**: killed the stale 57.118 backend (uvicorn PID 41268, started 14:04 — pre-57.119, no `/skills/system`); `Win32_Process` sweep confirmed a single python.exe owned :8000, port freed cleanly. Started a fresh 57.119 backend from repo root (`PYTHONPATH=backend/src python -m uvicorn api.main:app --env-file .env`, no `--reload`); `Application startup complete`. API probe (dev-login acme-skills → `GET /admin/tenants/{id}/skills/system`) → **200** with `code-review`(script=F) / `digest`(**script=T**) / `summarize`(script=F), all `overridden=F` (the new code is live).

**Drive (real admin Skills tab :3007 + real backend, acme-skills)**: `/tenant-settings` → Skills tab.

| Control | Observed |
|---------|----------|
| **System Skills section** | Renders `code-review` / `digest` / `summarize` read-only below the tenant Skills, with the hint "Built-in skills available to every tenant…" |
| **🔧 script badge** | On `digest` ONLY (the 57.118 bundled script); `code-review`/`summarize` have none |
| **Preview (system)** | Click `digest` Preview → a `role="dialog"` modal renders `digest.md`'s verbatim instructions ("# Digest … Call `run_skill_script(\"digest\")` … Read the hex digest …"); Close dismisses it |
| **Preview (tenant)** | The tenant `release-notes` row gained a Preview button (alongside Edit/Delete) — opens the modal with its instructions |
| **shadowed tag** | Created a tenant skill named `code-review` (POST 201) → reload → the System Skills `code-review` row shows "shadowed by your skill"; `digest` does NOT (overridden=False); tenant count "2 / 50". Cleanup: deleted the tenant `code-review` (204) → acme-skills back to `release-notes` only |

**Observed vs intended**: intended = a read-only System Skills view (badge + shadowed tag) + a Preview of any skill's body. Observed = EXACTLY that — the section data is from the real `/skills/system` endpoint (not a fixture), the badge reflects the real `has_script`, the shadowed tag reflects the real per-tenant `overridden` (created+deleted live), and the modal renders the real instructions. No AP-4 Potemkin: every control is live (real fetch + real render), labels are real, results render.

**Evidence**: `artifacts/sprint-57-119-drivethrough-system-skills-preview.png` (System Skills section + the `digest` 🔧-script badge + the Preview modal open with digest.md instructions) · `artifacts/sprint-57-119-drivethrough-shadowed-tag.png` (the `code-review` System Skills row with the "shadowed by your skill" tag while a tenant `code-review` exists).

**Verdict**: ✅ **PASS** — Drive-Through Acceptance satisfied (real UI + real backend); the System Skills visibility + preview is genuinely usable, not gate-only.

## Day 4 — (pending: CHANGE-086 + retrospective + navigators + PR)
