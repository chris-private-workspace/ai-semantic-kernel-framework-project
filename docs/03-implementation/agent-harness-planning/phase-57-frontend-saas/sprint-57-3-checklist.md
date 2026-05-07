# Sprint 57.3 — Checklist

> [Sprint Plan](./sprint-57-3-plan.md)

**Sprint Goal**: Open Phase 57+ SaaS Frontend 2/N — Tenant Settings bundle(backend GET + PATCH + frontend Tenant Settings page);closes D1 RED finding(57.3 v1 Day 0 探勘);3rd application of `mixed` 0.60 multiplier。

---

## Day 0 — Setup + Day-0 三-prong 探勘 + Pre-flight Verify

### 0.1 Branch + plan + checklist commit
- [x] **Branch from main(57a5daaf)**
  - DoD:`git checkout -b feature/sprint-57-3-tenant-settings-bundle`
  - Verify:`git branch --show-current` → `feature/sprint-57-3-tenant-settings-bundle`
- [x] **Commit plan + checklist**
  - DoD:both files staged + committed with conventional message `docs(plan, sprint-57-3): add plan + checklist for Tenant Settings bundle`
  - Verify:`git log --oneline -1` shows commit `7b6361fc`;`git status --short` clean

### 0.2 Day-0 三-prong 探勘 v2(per AD-Plan-3 + AD-Plan-4 fold-in promoted)
- [x] **Prong 1 Path Verify**(per AD-Plan-2 path verify)
  - `frontend/src/features/tenant-settings/` 不存在(expect — NEW US-3+US-4)
  - `frontend/src/pages/tenant-settings/` 不存在(expect — NEW US-4)
  - `frontend/tests/e2e/tenant_settings_*.spec.ts` 不存在(expect — NEW US-5)
  - `backend/tests/integration/api/v1/admin/test_tenant_get.py` + `test_tenant_patch.py` 不存在(expect — NEW US-1+US-2)
  - `backend/src/api/v1/admin/tenants.py` exists(expect — MODIFY US-1+US-2)
  - `backend/src/platform_layer/identity/auth.py:140 require_admin_platform_role` exists(56.2 reuse)
  - `backend/src/infrastructure/db/audit_helper.py:90 append_audit` exists(53.5/53.6 reuse)
  - Verify:Glob + Grep results;0 unexpected drift(若有 → catalogue D9+)
- [x] **Prong 2 Content Verify**(per AD-Plan-3 content verify promoted)
  - `tenants.py` GET/PUT/PATCH for `/{id}` entity 不存在(D1 RED already caught — already user-confirmed Option B pivot)
  - `TenantState` + `TenantPlan` enum 已定義 in `identity.py:73 + 88`
  - `VALID_TRANSITIONS` 已定義 in `lifecycle.py:63`
  - `_load_tenant_or_404` helper 已存在 in `tenants.py:167`
  - `append_audit` signature 完整 reusable(check params:db, tenant_id, action, actor_user_id, details)
  - Pydantic v2 `ConfigDict(extra="forbid")` 用法 — 既有 56.x 慣例 grep verify
  - Verify:0 new wrong-content drift(D1 RED catch already user-confirmed Option B pivot 2026-05-07)
- [x] **Prong 3 Schema Verify**(per AD-Plan-4-Schema-Grep promoted)
  - 此 sprint 無新 DB schema/migration → Schema verify N/A
  - **但 attempt 完成** per fold-in spirit:Grep `migrations/versions/0017_*.py` 不存在 confirm;Grep `class Tenant` ORM 9 fields 全 verified
  - Verify:N/A verdict logged in progress.md;not skip silently

### 0.3 Calibration multiplier pre-read
- [x] **`mixed` 0.60 mid-band 3rd application**
  - 2-data-point evidence:53.7 mixed 0.55 ratio 1.01(1st)+ 56.2 mixed 0.60 ratio 1.17(2nd)= mean **1.09 ✅** in band
  - 此 sprint:bottom-up ~17 hr × 0.60 = **~10.2 hr** commit
  - Day 4 retro Q2 verify:若 ratio in band → 3-data-point window opens;若 mean < 1.05 in next 1-2 sprints → consider reduce 0.55(per AD-Sprint-Plan-4 matrix discipline)

### 0.4 Pre-flight verify(main green baseline)
- [x] **Backend baselines**
  - `python -m pytest backend/tests/ -q --tb=no` → 1574 collected / 0 failures(Sprint 57.2 baseline)
  - `python -m mypy backend/src --strict` → 0 errors / 295 source files
  - `python scripts/lint/run_all.py` → 8 V2 lints 8/8 green
  - `grep -rn "import openai\|import anthropic" backend/src/agent_harness/` → 0 results(LLM SDK leak)
  - Verify:All 4 baselines documented in progress.md ✅ (1574 / 0/295 / 8/8 / 0)
- [x] **Frontend baselines**
  - `cd frontend && npm run lint` → clean
  - `cd frontend && npm run build` → success
  - `cd frontend && npm run test` → 15 unit tests pass(57.1 v2 baseline)
  - Verify:All 3 baselines documented in progress.md ✅ (ESLint clean / Vite 196.55 kB / Vitest 15/15)

### 0.5 Day 0 progress.md commit + push
- [x] **Catalogue D-findings + cross-reference v1 abort**
  - D1 closed by user-confirmed Option B 2026-05-07
  - D2-D8 informational(per plan §Risks)
  - Document Day 0 三-prong first fully-applied sprint attempt time + findings count
  - Verify:`docs/03-implementation/agent-harness-execution/phase-57/sprint-57-3/progress.md` exists with Day 0 section ✅
- [x] **Day 0 commit + push**
  - DoD:progress.md staged + committed `docs(progress, sprint-57-3): Day 0 三-prong 探勘 + pre-flight baseline verify`
  - Verify:`git log --oneline -1` shows commit `92d1dc79`;remote up-to-date(branch pushed to origin)

---

## Day 1 — US-1 Backend GET endpoint

### 1.1 TenantResponse Pydantic model
- [x] **Add `class TenantResponse(BaseModel)` to tenants.py**
  - 9 fields:id (UUID) / code (str) / display_name (str) / state (TenantState) / plan (TenantPlan) / provisioning_progress (dict) / onboarding_progress (dict) / meta_data (dict) / created_at (datetime) / updated_at (datetime) — actual = 10 fields
  - `model_config = ConfigDict(from_attributes=True)` for ORM serialization
  - File header MHist:`+ N+1 line: 2026-05-08: Sprint 57.3 — add TenantResponse + TenantUpdateRequest + GET/PATCH endpoints (closes D1 RED)`
  - Verify:`grep -n "class TenantResponse" backend/src/api/v1/admin/tenants.py` → 1 result

### 1.2 GET /{tenant_id} endpoint
- [x] **Add `@router.get("/{tenant_id}", response_model=TenantResponse)` endpoint**
  - Path:`/{tenant_id}` accepts UUID
  - Auth:`Depends(require_admin_platform_role)` per 56.2 RBAC pattern
  - Body:`tenant = await _load_tenant_or_404(db, tenant_id); return TenantResponse.model_validate(tenant)`
  - Verify:`grep -n "@router.get" backend/src/api/v1/admin/tenants.py` shows new entry

### 1.3 NEW test file test_tenant_get.py
- [x] **Create `backend/tests/integration/api/test_admin_tenant_get.py`**(D9 path follows existing 56.x flat convention)
  - Test 1:`test_get_tenant_happy_path` — admin user + valid tenant_id → 200 + all 10 fields populated + correct types
  - Test 2:`test_get_tenant_404_not_found` — random UUID not in DB → 404
  - Test 3:`test_get_tenant_401_unauthenticated` — no Authorization header → 401
  - Test 4:`test_get_tenant_403_wrong_role` — non-admin role JWT → 403
  - Test 5:`test_get_tenant_response_shape` — assert response keys match TenantResponse fields exactly
  - Test 6 (optional):`test_get_tenant_meta_data_jsonb_round_trip` — populate meta_data with nested dict → fetch → assert round-trip preserved
  - Verify:`python -m pytest backend/tests/integration/api/v1/admin/test_tenant_get.py -v` → ≥5 pass / 0 fail

### 1.4 Day 1 sanity checks
- [x] **Backend baselines verify**
  - `python -m pytest backend/tests/ -q --tb=no` → 1579+ collected / 0 failures(+5)
  - `python -m mypy backend/src/api/v1/admin/tenants.py --strict` → 0 errors
  - `python scripts/lint/run_all.py` → 8 V2 lints 8/8 green
  - `grep -rn "import openai\|import anthropic" backend/src/agent_harness/` → 0(LLM SDK leak)
  - Verify:All 4 sanity checks pass + recorded in progress.md

### 1.5 Day 1 commit + push + progress.md
- [x] **Commit US-1 + push**
  - Commit message:`feat(api, sprint-57-3): add GET /admin/tenants/{id} endpoint with TenantResponse Pydantic (US-1)`
  - Co-author:`Co-Authored-By: Claude <noreply@anthropic.com>`
  - progress.md Day 1 section recorded(actual_hr / est_hr ratio note)
  - Verify:`git log main..HEAD --oneline` shows new commit + previous Day 0;remote up-to-date

---

## Day 2 — US-2 Backend PATCH endpoint

### 2.1 TenantUpdateRequest Pydantic model
- [ ] **Add `class TenantUpdateRequest(BaseModel)` to tenants.py**
  - Fields:`display_name: str | None = Field(None, min_length=1, max_length=256)` + `meta_data: dict[str, Any] | None = None`
  - `model_config = ConfigDict(extra="forbid")` rejects any other field with 422
  - Verify:`grep -n "class TenantUpdateRequest" backend/src/api/v1/admin/tenants.py` → 1 result

### 2.2 PATCH /{tenant_id} endpoint with audit chain
- [ ] **Add `@router.patch("/{tenant_id}", response_model=TenantResponse)` endpoint**
  - Auth:`Depends(require_admin_platform_role)`(returns admin_user_id)
  - Logic per plan §Technical Specifications: load tenant → diff request fields vs current → mutate ORM → flush(bump updated_at)→ append_audit with action="tenant_settings_updated" + details {changed_fields, old_values, new_values} → commit → return TenantResponse
  - No-op short-circuit:若無 changed_fields → return early without audit entry
  - Verify:`grep -n "@router.patch" backend/src/api/v1/admin/tenants.py` shows new entry

### 2.3 NEW test file test_tenant_patch.py
- [ ] **Create `backend/tests/integration/api/v1/admin/test_tenant_patch.py`**
  - Test 1:`test_patch_display_name_only` — payload `{"display_name": "New Name"}` → 200 + name changed + audit entry written
  - Test 2:`test_patch_meta_data_only` — payload `{"meta_data": {"foo": "bar"}}` → 200 + meta_data updated + audit entry
  - Test 3:`test_patch_both_fields` — payload `{"display_name": "X", "meta_data": {"y": "z"}}` → 200 + both updated + 1 audit entry with both fields in changed_fields
  - Test 4:`test_patch_immutable_field_rejected` — payload `{"plan": "ENTERPRISE"}` or `{"state": "ACTIVE"}` → 422(Pydantic extra="forbid" rejects)
  - Test 5:`test_patch_display_name_too_long` — 257 chars → 422
  - Test 6:`test_patch_404_not_found` — random UUID → 404
  - Test 7:`test_patch_no_op` — payload `{}` or unchanged values → 200 + no audit entry written
  - Test 8 (audit assertion):`test_patch_audit_entry_shape` — after PATCH check audit_log row count + details JSONB content matches
  - Verify:`python -m pytest backend/tests/integration/api/v1/admin/test_tenant_patch.py -v` → ≥7 pass / 0 fail

### 2.4 Module-level singleton reset pattern verify
- [ ] **Check audit_helper module-level cache**
  - `grep -n "_instance\|_factory\|module-level" backend/src/infrastructure/db/audit_helper.py` → check for cached singletons
  - If found:add autouse `_reset_*` fixture in `backend/tests/integration/api/v1/admin/conftest.py` per testing.md §Module-level Singleton Reset Pattern
  - If not found:document in progress.md "no module-level singleton risk" + skip
  - Verify:`pytest backend/tests/integration/api/v1/admin/ --tb=no` → 0 cascade failures across test files

### 2.5 Day 2 sanity checks
- [ ] **Backend baselines verify**
  - `python -m pytest backend/tests/ -q --tb=no` → 1584+ collected / 0 failures(+10 cumulative)
  - `python -m mypy backend/src/api/v1/admin/tenants.py --strict` → 0 errors
  - `python scripts/lint/run_all.py` → 8 V2 lints 8/8 green
  - `grep -rn "import openai\|import anthropic" backend/src/agent_harness/` → 0
  - Verify:All 4 sanity checks pass

### 2.6 Day 2 commit + push + progress.md
- [ ] **Commit US-2 + push**
  - Commit message:`feat(api, sprint-57-3): add PATCH /admin/tenants/{id} with audit chain (US-2 closes D1)`
  - progress.md Day 2 section + actual_hr ratio note
  - Verify:`git log main..HEAD --oneline` shows commit;remote up-to-date

---

## Day 3 — US-3 Frontend Infra + US-4 Page Display + Edit Form

### 3.1 features/tenant-settings/ skeleton
- [ ] **Create folder structure**
  - `frontend/src/features/tenant-settings/{components,services,store}/`
  - Empty `index.ts` if needed for re-export pattern
  - Verify:`ls frontend/src/features/tenant-settings/` shows 3 subdirs

### 3.2 types.ts mirror US-1 TenantResponse
- [ ] **Create `frontend/src/features/tenant-settings/types.ts`**
  - `enum TenantState { PROVISIONING, ACTIVE, SUSPENDED, ARCHIVED }` mirror backend
  - `enum TenantPlan { STANDARD, ENTERPRISE }` mirror backend
  - `interface TenantSettingsResponse { id / code / display_name / state / plan / provisioning_progress / onboarding_progress / meta_data / created_at / updated_at }`
  - `interface TenantUpdateRequest { display_name? / meta_data? }`
  - File header docstring per file-header-convention.md
  - Verify:`cat frontend/src/features/tenant-settings/types.ts` ≥ 30 lines

### 3.3 tenantSettingsService.ts plain fetch
- [ ] **Create `services/tenantSettingsService.ts`**
  - Mirror cost-dashboard `_handleResponse<T>` helper(per 57.1 v2 D6)
  - `fetchTenantSettings(tenantId)` → GET request
  - `updateTenantSettings(tenantId, payload)` → PATCH request with JSON body
  - `API_BASE = "/api/v1/admin"`
  - `credentials: "include"` for auth cookie
  - Verify:`npm run lint frontend/src/features/tenant-settings/services/tenantSettingsService.ts` clean

### 3.4 tenantSettingsStore.ts Zustand
- [ ] **Create `store/tenantSettingsStore.ts`**
  - State:`tenantId` / `data` / `loading` / `error` / `saving` / `saveError`
  - Actions:`setTenantId` / `loadData` / `save` / `reset`
  - Optimistic update on save success;error rollback by re-fetching
  - Mirror cost-dashboard chatStore pattern(57.1 v2)
  - Verify:`npm run build frontend/` clean(no TS errors)

### 3.5 3 Vitest unit tests US-3
- [ ] **Create unit tests**
  - `tenantSettingsService.test.ts`:fetchTenantSettings happy path + 401 error rejection
  - `tenantSettingsService.test.ts`:updateTenantSettings happy path with payload assertion
  - `tenantSettingsStore.test.ts`:loadData action + save action with optimistic update
  - Verify:`npm run test -- tenantSettings` → 3+ pass

### 3.6 pages/tenant-settings/index.tsx page wrapper
- [ ] **Create `frontend/src/pages/tenant-settings/index.tsx`**
  - `<Routes><Route index element={<TenantSettingsView />} /></Routes>` pattern per 57.1 v2 cost-dashboard wrapper
  - File header docstring
  - Verify:File created;import paths resolved

### 3.7 TenantSettingsView.tsx (read view)
- [ ] **Create `components/TenantSettingsView.tsx`**
  - URL param parsing:`useParams<{ tenantId: string }>()` 
  - Read sections per plan §US-4:
    - Tenant ID badge + Code (immutable label)
    - State badge(green/yellow/gray color by enum)
    - Plan badge(blue/gray color by enum)
    - created_at + updated_at formatted
    - provisioning_progress + onboarding_progress collapsed JSON `<pre>`
  - Edit toggle button → switches to TenantSettingsEditForm
  - Loading skeleton + error retry button mirror governance
  - Verify:render with mocked useTenantSettingsStore data passes Vitest test

### 3.8 TenantSettingsEditForm.tsx (edit form)
- [ ] **Create `components/TenantSettingsEditForm.tsx`**
  - display_name `<input>` with maxLength=256 + min 1 char validation
  - meta_data `<textarea>` with JSON parse on blur:invalid → red error message + disable save button
  - Save button(disabled while saving / invalid)
  - Cancel button reverts to view mode
  - Submit handler:`store.save({ display_name, meta_data })` + on success switch back to View mode
  - Verify:Form submit valid passes Vitest;JSON invalid case shows error message

### 3.9 3 Vitest unit tests US-4
- [ ] **Create unit tests**
  - `TenantSettingsView.test.tsx`:render with mock data + assert all read fields visible
  - `TenantSettingsEditForm.test.tsx`:submit valid form → store.save called with correct payload
  - `TenantSettingsEditForm.test.tsx`:invalid JSON in textarea → save button disabled + error message shown
  - Verify:`npm run test -- TenantSettings` → 3+ pass

### 3.10 Day 3 sanity checks
- [ ] **Frontend baselines verify**
  - `cd frontend && npm run lint` → clean
  - `cd frontend && npm run build` → success
  - `cd frontend && npm run test` → 15 + 6 = 21 unit tests pass
  - Verify:All 3 sanity checks pass

### 3.11 Day 3 commit + push + progress.md
- [ ] **Commit US-3 + US-4 + push**
  - Commit message:`feat(frontend, sprint-57-3): add tenant-settings feature folder + page + edit form (US-3 + US-4)`
  - progress.md Day 3 section + actual_hr ratio note
  - Verify:`git log main..HEAD --oneline` shows commit

---

## Day 4 — US-5 Routing + Playwright E2E + Closeout Ceremony

### 4.1 App.tsx routing + Home nav
- [ ] **Add wildcard route + nav link**
  - `App.tsx`:add `import TenantSettingsPage from './pages/tenant-settings'` + `<Route path="/tenant-settings/*" element={<TenantSettingsPage />} />`
  - Home page:add `<Link to="/tenant-settings/{TENANT_ID}">Tenant Settings</Link>` always visible per 57.1 D10 Option C
  - File header MHist update(MHist 1-line per AD-Lint-3)
  - Verify:`npm run build` clean;manual smoke `npm run dev` → click Tenant Settings link → loads URL

### 4.2 Playwright e2e tenant_settings_view.spec.ts
- [ ] **Create `frontend/tests/e2e/tenant_settings_view.spec.ts`**
  - Test 1 happy path:admin auth fixture + page.route() mock GET 200 → load `/tenant-settings/{tenant_id}` → assert all read fields visible(code label / state badge / plan badge / created_at)
  - Test 2 error path:page.route() mock GET 500 → assert retry button visible + click retry + mock 200 next call → assert recovery
  - Verify:`npx playwright test tenant_settings_view.spec.ts --project=chromium` → 2 pass < 30s each

### 4.3 Playwright e2e tenant_settings_edit.spec.ts
- [ ] **Create `frontend/tests/e2e/tenant_settings_edit.spec.ts`**
  - Test 1 happy path edit:admin auth + mock GET + click Edit toggle + modify display_name + click Save + mock PATCH 200 → assert UI shows new display_name in View mode
  - Test 2 error path JSON validate:click Edit + paste invalid JSON in meta_data textarea + blur → assert Save button disabled + red error message visible
  - Verify:`npx playwright test tenant_settings_edit.spec.ts --project=chromium` → 2 pass

### 4.4 Final pytest + lint + leak verify
- [ ] **All baselines green**
  - `python -m pytest backend/tests/ -q --tb=no` → 1584+ collected / 0 failures
  - `python -m mypy backend/src --strict` → 0 errors / 297+ source files
  - `python scripts/lint/run_all.py` → 8 V2 lints 8/8 green
  - `grep -rn "import openai\|import anthropic" backend/src/agent_harness/` → 0
  - `cd frontend && npm run lint && npm run build && npm run test` → all clean
  - `npx playwright test --project=chromium` → 15+4 = 19 e2e tests pass
  - Verify:All 6 baselines pass + recorded in progress.md final tally

### 4.5 Retrospective.md (6 必答 format)
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-3/retrospective.md`**
  - Q1 What went well(包含 Day 0 三-prong 探勘 first fully-applied + D1 catch + Option B pivot ROI)
  - Q2 What didn't go well + AD-Sprint-Plan-4 mixed 3rd app calibration verify(actual / 10 ratio + verdict in/outside band + 3-data-point window observation)
  - Q3 What we learned(generalizable lessons + Day 0 三-prong first-fully-applied sprint observations)
  - Q4 Audit Debt deferred(Phase 57.x Admin tenant console / Onboarding self-serve / etc.)
  - Q5 Next steps(rolling planning;不寫 57.4 plan task detail;只列 Phase 57.x candidate scope)
  - Q6 Solo-dev policy validation(or sprint-specific theme:bundle backend+frontend mixed scope class confidence)
  - Verify:6 必答 + AD-Sprint-Plan-4 verdict + Phase 57.x next-sprint candidates list documented

### 4.6 Memory snapshot + MEMORY.md index
- [ ] **Create memory file**
  - `memory/project_phase57_3_tenant_settings.md` per memory frontmatter format(name / description / type=project)
  - Content:Sprint summary + 5 USs delivery + calibration ratio + Day 0 三-prong first-fully-applied stats + D1 closure
  - Update `memory/MEMORY.md` index with 1-line entry under ~150 chars
  - Verify:Both files saved + grep "57.3" MEMORY.md → 1 result

### 4.7 Open PR + CI green + solo-dev merge
- [ ] **Open PR to main**
  - Title:`Sprint 57.3 — Phase 57+ SaaS Frontend 2/N: Tenant Settings Bundle (backend CRUD + frontend UI)`
  - Description per git-workflow.md template + closes D1 RED finding
  - Verify:5 active CI checks green(Backend Lint + Type + Test + V2 Lints + Frontend E2E chromium headless);per 53.7 baseline
- [ ] **Solo-dev merge to main**
  - Per 53.2 solo-dev policy(review_count=0 permanent;enforce_admins=true);no temp-relax bootstrap needed
  - Verify:`git log main --oneline -3` shows merge commit;remote up-to-date

### 4.8 Closeout PR
- [ ] **SITUATION-V2 + CLAUDE.md sync to Phase 57+ Frontend SaaS 2/N**
  - SITUATION-V2 §9 milestones row +Sprint 57.3
  - CLAUDE.md Last Updated entry + Latest Sprint update + Phase 57+ Frontend SaaS 1/N → 2/N
  - Verify:Closeout PR opened with sync + merged via solo-dev policy

---

## Sprint 57.3 Definition of Done(覆核)

- [ ] All 5 USs acceptance criteria met per [plan §Acceptance Criteria](./sprint-57-3-plan.md#acceptance-criteria)
- [ ] Backend pytest baseline 1574 → 1584+(≥+10 from US-1+US-2)
- [ ] Backend mypy --strict 0 errors;source files 295 → 297+
- [ ] 8 V2 lints green;LLM SDK leak: 0;all baselines unchanged
- [ ] Frontend `npm run lint && npm run build && npm run test` clean(15+6 = 21 unit tests pass)
- [ ] Playwright e2e 19 tests pass(15 既有 + 4 NEW;2 view + 2 edit happy/error)
- [ ] Audit chain assertion:US-2 PATCH 後 audit_log 確認有 entry with action="tenant_settings_updated"
- [ ] Anti-pattern checklist 11 項對齐
- [ ] AD-Sprint-Plan-4 `mixed` 3rd application captured + ratio verdict logged in retro Q2
- [ ] D1 RED finding fully closed(US-1 + US-2 backend endpoints production-ready)
- [ ] Day 0 三-prong 探勘 first fully-applied sprint observations documented in retro Q3
- [ ] PR + closeout PR merged via solo-dev policy
- [ ] SITUATION-V2 + memory + CLAUDE.md updated to **Phase 57+ Frontend SaaS 2/N (Sprint 57.3 closed — Tenant Settings bundle)**
- [ ] Phase 57.x next-sprint candidates documented in retrospective Q5(user approval required per rolling planning)
