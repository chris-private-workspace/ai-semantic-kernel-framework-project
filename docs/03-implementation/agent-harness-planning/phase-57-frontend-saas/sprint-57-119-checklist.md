# Sprint 57.119 — Checklist (Skills System Visibility + Preview: the admin Skills tab (57.114) shows ONLY the tenant's overlay skills — the system-bundled set (`code-review`/`digest`/`summarize`, the base every tenant overlays) is invisible. This slice — the chosen thin vertical of `AD-Skills-Authoring-UI` — adds a read-only "System Skills" section (a "🔧 script" badge + a "shadowed by your skill" tag) + a Preview modal rendering any skill's full instructions. ONE new read-only `GET /admin/tenants/{id}/skills/system` over `get_default_skill_registry()` (overridden = the tenant's same-name skills) + a TanStack read hook + a read-only tab section + a Preview modal. NO DB / NO migration / NO wire (count 24) / NO codegen. Feature continuation (NO design note); CHANGE-086)

[Plan](./sprint-57-119-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; Prong-3 schema N/A — no new table / migration) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `cf83b274`) — catalogued in progress.md ✅
- [x] **Prong 1 — path verify**: 5 EDIT targets present; backend test `test_admin_tenant_skills.py` EDIT; `CHANGE-086-*.md` free; NO design note. 🔧 **D-fe-test-path** drift: the FE test is NOT co-located → actual `frontend/tests/unit/tenant-settings/tabs/SkillsTab.test.tsx` (the `tests/unit` convention; File Change List #7 path corrected)
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-skills-routes**: `SkillResponse` (`:1894`) / `SkillListResponse` (`:1905`) / `_project_skill` (`:1915`) / `list_tenant_skills` (`:1926`, the deps) confirmed — the shape + auth to mirror
  - [x] **D-registry-list**: `get_default_skill_registry().list()` (`registry.py:189-194`) → `Skill` with `.script` → `has_script = s.script is not None`; exported `agent_harness.skills` (`__init__.py:15,31`)
  - [x] **D-skillstab**: `SkillsTab.tsx` single `<Card title="Skills">` (`:68-458`) + the tenant row map (`:336-452`) → insert a sibling "System Skills" Card + a `previewSkill` state + an inline overlay; add Preview to the tenant rows
  - [x] **D-fe-datalayer**: `fetchTenantSkills` (`:458`, `fetchWithAuth` + `_handleResponse`) + `useTenantSkills` (`:48`, `queryKey:[...BASE, tenantId]`) — mirror for `fetchSystemSkills`/`useSystemSkills` (`["tenant-skills-system", tenantId]`)
  - [x] **D-modal-primitive** (confirmed): `components/mockup-ui` has NO `Modal`/`Dialog`/`Overlay` → an inline fixed-overlay panel (the 57.115 `SkillSlashMenu` greenfield precedent), NO new dep
  - [x] **D-cross-cat-import** (#1 lint risk RESOLVED): `api/v1/chat/handler.py:96` ALREADY `from agent_harness.skills import ...` + `router.py:465` `[ChatSkillItem(name=s.name, description=s.description) for s in registry.list()]` — the exact api→Cat-5 pattern → `check_cross_category_import` green
- [x] **Prong 3 — N/A** (no new table / migration / ORM — read-only over the existing registry + the existing `tenant_skills` read)
- [x] **D-baselines**: at HEAD `cf83b274` — full pytest **2644+5skip** · wire **24** · FE Vitest **873 (142 files)** ✅ · mockup **51** · mypy `src` **0/371** · run_all **10/10**
- [x] **Catalog drift**: 2 drifts, both PATH/contingency (non-scope-shifting) — D-fe-test-path + D-modal-primitive; the #1 lint risk RESOLVED green
- [x] **Go/no-go**: 🟢 **GO** — design holds end-to-end; no scope shift > 20%

### 0.2 Branch ✅
- [x] `git checkout -b feature/sprint-57-119-skills-system-visibility` (from `main` `cf83b274`)

---

## Day 1 — Backend: the system-skills read endpoint (US-1)

### 1.1 `SystemSkillResponse` + `SystemSkillListResponse` + the endpoint ✅
- [x] **`backend/src/api/v1/admin/tenants.py`** (EDIT): `SystemSkillResponse(BaseModel)` (`name`/`description`/`instructions`/`has_script: bool`/`overridden: bool`) + `SystemSkillListResponse(BaseModel)` (`skills: list[...]`) + `GET /{tenant_id}/skills/system` → `list_system_skills` (same deps as `list_tenant_skills`); `tenant_names` from `tenant_skill_service.list_skills` + `bundled = get_default_skill_registry().list()`; `has_script = s.script is not None` + `overridden = s.name in tenant_names`; read-only, no audit. Imported `get_default_skill_registry` from `agent_harness.skills`. MHist + Last Modified
  - DoD: ✅ returns the 3 bundled skills; `digest.has_script` True; mypy 0/371
### 1.2 Backend test ✅
- [x] **`backend/tests/integration/api/test_admin_tenant_skills.py`** (EDIT +4): `test_system_skills_lists_bundled` (3 skills / has_script / instructions / nothing overridden) · `test_system_skills_overridden_flag` (a `code-review` tenant skill → overridden True for it only) · `test_system_skills_requires_admin` (401/403) · `test_system_skills_tenant_not_found` (404)
  - DoD: ✅ the 4 new cases pass (`pytest -k system`); flake8 clean

---

## Day 2 — Frontend: data layer + System Skills section + Preview modal (US-2, US-3, US-4, US-5)

### 2.1 FE data layer (US-2) ✅
- [x] **`types.ts`** (EDIT): `SystemSkill { name; description; instructions; has_script: boolean; overridden: boolean }` + `SystemSkillListResponse { skills: SystemSkill[] }`
- [x] **`tenantSettingsService.ts`** (EDIT): `fetchSystemSkills(tenantId)` (GET `/admin/tenants/{id}/skills/system`; mirrors `fetchTenantSkills`)
- [x] **`useTenantSkills.ts`** (EDIT): `useSystemSkills(tenantId)` + `SYSTEM_SKILLS_QUERY_KEY_BASE` (`["tenant-settings","skills-system"]`); no mutation invalidates it (static bundled set)
  - DoD: ✅ tsc clean (`npm run build`)

### 2.2 System Skills read-only section + Preview modal (US-3, US-4) ✅
- [x] **`SkillsTab.tsx`** (EDIT): a sibling `<Card title="System Skills">` listing each bundled skill — name (mono) + 🔧 script badge (`system-skill-script-badge-{name}`) + "shadowed by your skill" tag (`system-skill-shadowed-{name}`) + Preview button (`system-skill-preview-btn-{name}`); NO edit/delete; loading/error (`system-skills-section`/`system-skills-load-error`) mirror the tenant list. `previewSkill` state + an inline-overlay Preview modal (`skill-preview-modal`/`skill-preview-body`/`skill-preview-close-btn`, `role="dialog"` + a window Escape listener — the `TenantMembersDrawer` a11y convention) rendering any skill's `instructions`; a Preview button on the tenant rows too. Inline tokens (`var(--bg)`/`var(--border)`/`var(--radius)`/`var(--shadow)`); English copy; MHist
  - DoD: ✅ section renders; Preview opens + shows instructions; no disturbance to the 57.114/117 idioms; lint clean (a11y disables match `TenantMembersDrawer`)

### 2.3 FE Vitest + gate sweep (US-5) ✅
- [x] **`frontend/tests/unit/tenant-settings/tabs/SkillsTab.test.tsx`** (EDIT +6; path drift D-fe-test-path): section render · has-script badge on `digest` only · shadowed tag when overridden · Preview modal opens+shows `instructions` · tenant-row Preview + Close dismisses · system load-error. `mockSystemSkills` added to BOTH describe `beforeEach` (else the existing 15 crash). SkillsTab suite **21 passed** (15+6)
- [x] Gate sweep: mypy `src` **0/371** · black/isort/flake8 0 · `run_all` **10/10** (count 24, no codegen) · `npm run lint && npm run build` ✅ (no `--silent`; a11y fixed) · Vitest **879 (142 files)** (+6) · mockup-fidelity **51** (byte-identical + 51 baseline) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · `check_cross_category_import` green
  - Verify: ✅ `python scripts/lint/run_all.py` · `npx vitest run` (879) · `npm run build`

---

## Day 3 — Drive-through (US-6) — real admin tab + real backend

### 3.1 Clean restart + tab probe ✅
- [x] Risk Class E clean restart from repo-root (killed stale 57.118 PID 41268; `Win32_Process` sweep → single python.exe owned :8000, no orphan; `Application startup complete`); `GET /admin/tenants/{id}/skills/system` (dev-login acme-skills) → **200** code-review(F)/digest(**T**)/summarize(F) — new code live

### 3.2 Drive-through (real admin Skills tab + Playwright/real backend) ✅
- [x] **Leg (visibility + preview) PASS**: `/tenant-settings` → Skills tab (acme-skills) → System Skills lists code-review/digest/summarize read-only → `digest` "🔧 script" badge (only) → created a tenant `code-review` (201) → reload → System Skills `code-review` shows "shadowed by your skill" (digest does NOT) → cleanup deleted (204) → click `digest` Preview → `role="dialog"` modal renders `digest.md` instructions verbatim → Close dismisses → tenant `release-notes` Preview renders too. 2 screenshots in `artifacts/`
- [x] Each control driven (real fetch + real render, not a fixture/echo): section from the real `/skills/system`; badge = real `has_script`; shadowed tag = real per-tenant `overridden` (created+deleted live); modal = real instructions. Observed-vs-intended + backend noted in progress.md
  - DoD: ✅ section + badges + shadowed tag + Preview modal all live; screenshots captured

---

## Day 4 — CHANGE-086 + closeout (feature continuation — NO design note)

### 4.1 CHANGE-086 ✅
- [x] **`claudedocs/4-changes/feature-changes/CHANGE-086-skills-system-visibility.md`** (1-page, incl. the drive-through)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`skills-admin-readonly-surface` 0.55 1st data point) + progress.md final → ratio ~0.97 IN band, KEEP 0.55
- [x] Final gate sweep: mypy **0/371** · run_all **10/10** (count 24) · full pytest **2648 passed, 5 skipped** (+4) vs 2644 · Vitest **879** (+6) · mockup **51** holds
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + memory subfile `project_phase57_119_skills_system_visibility.md` · next-phase-candidates (`AD-Skills-Authoring-UI` visibility leg SHIPPED + versioning/hot-reload/disable carried + 120/121 carried) · sprint-workflow matrix `skills-admin-readonly-surface` 0.55 1st-point · 17.md N/A (api read endpoint, no new contract)
- [x] **Anti-pattern self-check** (retro Q5): AP-4 / AP-2 / AP-3 / AP-6 → **0 violations**
- [ ] PR (push + open on user authorization); CI → merge on green (gh-verified MERGED before main sync)
