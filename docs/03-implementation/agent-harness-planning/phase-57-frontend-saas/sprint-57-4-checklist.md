# Sprint 57.4 — Checklist

> [Sprint Plan](./sprint-57-4-plan.md)

**Sprint Goal**: Open Phase 57+ SaaS Frontend 3/N — Admin Tenants Console list bundle(backend GET `""` list endpoint + frontend Admin Tenants Console page);closes plan-time D1 RED finding(57.4 Day 0 plan-time Prong 2 catch);4th application of `mixed` 0.60 multiplier。

---

## Day 0 — Setup + Day-0 三-prong 探勘 + Pre-flight Verify

### 0.1 Branch + plan + checklist commit
- [ ] **Branch from main(a558f98b)**
  - DoD:`git checkout -b feature/sprint-57-4-admin-tenants-list-bundle`
  - Verify:`git branch --show-current` → `feature/sprint-57-4-admin-tenants-list-bundle`
- [ ] **Commit plan + checklist**
  - DoD:both files staged + committed with conventional message `docs(plan, sprint-57-4): add plan + checklist for Admin Tenants Console list bundle`
  - Verify:`git log --oneline -1` shows commit;`git status --short` clean

### 0.2 Day-0 三-prong 探勘 v3(per AD-Plan-3 + AD-Plan-4 fold-in promoted;57.4 second fully-applied sprint)
- [ ] **Prong 1 Path Verify**(per AD-Plan-2 path verify)
  - `frontend/src/features/admin-tenants/` 不存在(expect — NEW US-2+US-3+US-4)
  - `frontend/src/pages/admin-tenants/` 不存在(expect — NEW US-4)
  - `frontend/tests/e2e/admin_tenants/admin_tenants_list.spec.ts` 不存在(expect — NEW US-5)
  - `backend/tests/integration/api/test_admin_tenant_list.py` 不存在(expect — NEW US-1)
  - `backend/src/api/v1/admin/tenants.py` exists(expect — MODIFY US-1)
  - `backend/src/platform_layer/identity/auth.py:140 require_admin_platform_role` exists(56.2 reuse)
  - `backend/src/infrastructure/db/models/identity.py class Tenant` exists with code/display_name string columns(56.1 reuse)
  - `frontend/src/features/tenant-settings/types.ts` exports TenantState + TenantPlan(57.3 re-export source)
  - Verify:Glob + Grep results;0 unexpected drift(若有 → catalogue D9+)
- [ ] **Prong 2 Content Verify**(per AD-Plan-3 content verify promoted)
  - `tenants.py` GET `""` (no path param) list endpoint 不存在(D1 RED already caught — already user-confirmed Option A pre-emptive bundle)
  - `tenants.py` 既有 5 endpoints(POST `""` / GET `/{id}/onboarding-status` / POST `/{id}/onboarding/{step}` / GET `/{id}` / PATCH `/{id}`)— grep 確認
  - `TenantState` + `TenantPlan` enum 已定義 in `identity.py`(grep `class TenantState` + `class TenantPlan`)
  - Tenant ORM `code` + `display_name` columns string 型別 ILIKE-able(grep `code:.*Mapped\[str\]` + `display_name:.*Mapped\[str\]`)
  - `from sqlalchemy import or_` + `from sqlalchemy import func` 在 56.x usage 既有(grep verify import path)
  - Pydantic v2 `Query(...)` + `ConfigDict(from_attributes=True)` 既有 56.x+57.3 慣例 grep verify
  - Verify:0 new wrong-content drift(D1 RED catch already user-confirmed Option A pre-emptive bundle 2026-05-07)
- [ ] **Prong 3 Schema Verify**(per AD-Plan-4-Schema-Grep promoted)
  - 此 sprint 無新 DB schema/migration → Schema verify N/A
  - **但 attempt 完成** per fold-in spirit:Grep `migrations/versions/0017_*.py` 不存在 confirm;Grep `class Tenant` ORM 7+ fields(id/code/display_name/state/plan/created_at/updated_at)全 verified for list query compatibility
  - Verify:N/A verdict logged in progress.md;not skip silently

### 0.3 Calibration multiplier pre-read
- [ ] **`mixed` 0.60 mid-band 4th application**
  - 3-data-point evidence:53.7 mixed 0.55 ratio 1.01(1st)+ 56.2 mixed 0.60 ratio 1.17(2nd)+ 57.3 mixed 0.60 ratio 0.57(3rd)= mean **0.92 ✅** in band → KEEP 0.60 mid-band per AD-Sprint-Plan-4 matrix discipline
  - 此 sprint:bottom-up ~14 hr × 0.60 = **~8.4 hr** commit
  - Day 4 retro Q2 verify:若 ratio in band → 4-data-point window opens;若 mean shift → AD-Sprint-Plan-N+1 logged

### 0.4 Pre-flight verify(main green baseline)
- [ ] **Backend baselines**
  - `python -m pytest backend/tests/ -q --tb=no` → 1589 collected / 0 failures(Sprint 57.3 baseline)
  - `python -m mypy backend/src --strict` → 0 errors / 295 source files
  - `python scripts/lint/run_all.py` → 8 V2 lints 8/8 green
  - `grep -rn "import openai\|import anthropic" backend/src/agent_harness/` → 0 results(LLM SDK leak)
  - Verify:All 4 baselines documented in progress.md ✅ (1589 / 0/295 / 8/8 / 0)
- [ ] **Frontend baselines**
  - `cd frontend && npm run lint` → clean
  - `cd frontend && npm run build` → success / 69 modules / 203.02 kB
  - `cd frontend && npm run test` → 23 unit tests pass(57.3 baseline)
  - Playwright e2e 15 tests baseline(57.3 closeout)
  - Verify:All 4 baselines documented in progress.md ✅ (ESLint clean / Vite 69 modules 203.02 kB / Vitest 23/23 / Playwright 15)

### 0.5 Day 0 progress.md commit + push
- [ ] **Catalogue D-findings + cross-reference plan-time catch**
  - D1 closed by user-confirmed Option A pre-emptive bundle 2026-05-07
  - D2-D8 informational(per plan §Risks)
  - Document Day 0 三-prong second fully-applied sprint attempt time + findings count
  - Verify:`docs/03-implementation/agent-harness-execution/phase-57/sprint-57-4/progress.md` exists with Day 0 section ✅
- [ ] **Day 0 commit + push**
  - DoD:progress.md staged + committed `docs(progress, sprint-57-4): Day 0 三-prong 探勘 + pre-flight baseline verify`
  - Verify:`git log --oneline -1` shows commit;remote up-to-date(branch pushed to origin)

---

## Day 1 — US-1 Backend GET list endpoint

### 1.1 TenantListItem Pydantic model
- [ ] **Add `class TenantListItem(BaseModel)` to tenants.py**
  - 7 fields:id (UUID) / code (str) / display_name (str) / state (TenantState) / plan (TenantPlan) / created_at (datetime) / updated_at (datetime)
  - **Non-include**:provisioning_progress / onboarding_progress / meta_data(reduce list payload size)
  - `model_config = ConfigDict(from_attributes=True)` for ORM serialization
  - File header MHist:`+ N+1 line: 2026-05-08: Sprint 57.4 — add TenantListItem + TenantListResponse + GET list endpoint (closes D1 RED)`
  - Verify:`grep -n "class TenantListItem" backend/src/api/v1/admin/tenants.py` → 1 result

### 1.2 TenantListResponse Pydantic wrapper
- [ ] **Add `class TenantListResponse(BaseModel)` to tenants.py**
  - 4 fields:`items: list[TenantListItem]` / `total: int` / `limit: int` / `offset: int`
  - Verify:`grep -n "class TenantListResponse" backend/src/api/v1/admin/tenants.py` → 1 result

### 1.3 GET `""` list endpoint with query params
- [ ] **Add `@router.get("", response_model=TenantListResponse)` endpoint**
  - Path:`""` (no path param) accepts query string
  - Auth:`dependencies=[Depends(require_admin_platform_role)]` per 56.2 RBAC pattern
  - Query params:`state: TenantState | None = Query(None)` / `plan: TenantPlan | None = Query(None)` / `search: str | None = Query(None, max_length=128)` / `limit: int = Query(50, ge=1, le=200)` / `offset: int = Query(0, ge=0)`
  - Body:base_stmt = select(Tenant) + apply filters + count_stmt for total + page_stmt order_by created_at.desc().limit().offset() → return TenantListResponse
  - Imports:`from sqlalchemy import or_, func` + `from fastapi import Query`
  - Verify:`grep -n "@router.get(\"\"," backend/src/api/v1/admin/tenants.py` shows new entry + endpoint listed in Sprint 57.4 spec

### 1.4 NEW test file test_admin_tenant_list.py
- [ ] **Create `backend/tests/integration/api/test_admin_tenant_list.py`**(D9 path follows existing 56.x flat convention per 57.3)
  - Test 1:`test_list_tenants_happy_no_filter` — admin user no query → 200 + total >= 1 + items array
  - Test 2:`test_list_tenants_filter_by_state` — query `state=ACTIVE` → all items have state=ACTIVE
  - Test 3:`test_list_tenants_filter_by_plan` — query `plan=ENTERPRISE` → all items have plan=ENTERPRISE
  - Test 4:`test_list_tenants_search_by_code` — fixture seed tenant code="ACME_TEST" + query `search=ACME` → 1 match
  - Test 5:`test_list_tenants_pagination` — seed 3 tenants + query `limit=2&offset=0` → 2 items + total=3+ + offset=0;then `offset=2` → 1+ items
  - Test 6:`test_list_tenants_401_unauthenticated` — no Authorization header → 401
  - Test 7:`test_list_tenants_403_wrong_role` — non-admin role JWT → 403
  - Test 8:`test_list_tenants_response_shape` — assert response keys match TenantListResponse fields exactly
  - Test 9 (optional):`test_list_tenants_empty_filter` — query `search=NONEXISTENT_TENANT_99999` → items=[] + total=0
  - Verify:`python -m pytest backend/tests/integration/api/test_admin_tenant_list.py -v` → ≥6 pass / 0 fail

### 1.5 Day 1 sanity checks
- [ ] **Backend baselines verify**
  - `python -m pytest backend/tests/ -q --tb=no` → 1595+ collected / 0 failures(+6)
  - `python -m mypy backend/src/api/v1/admin/tenants.py --strict` → 0 errors
  - `python scripts/lint/run_all.py` → 8 V2 lints 8/8 green
  - `grep -rn "import openai\|import anthropic" backend/src/agent_harness/` → 0(LLM SDK leak)
  - Verify:All 4 sanity checks pass + recorded in progress.md

### 1.6 Day 1 commit + push + progress.md
- [ ] **Commit US-1 + push**
  - Commit message:`feat(api, sprint-57-4): add GET /admin/tenants list endpoint with TenantListItem + filters + pagination (US-1 closes D1)`
  - Co-author:`Co-Authored-By: Claude <noreply@anthropic.com>`
  - progress.md Day 1 section recorded(actual_hr / est_hr ratio note)
  - Verify:`git log main..HEAD --oneline` shows new commit + previous Day 0;remote up-to-date

---

## Day 2 — US-2 Frontend Infra (types + service + store)

### 2.1 features/admin-tenants/ skeleton
- [ ] **Create folder structure**
  - `frontend/src/features/admin-tenants/{components,services,store}/`
  - Verify:`ls frontend/src/features/admin-tenants/` shows 3 subdirs

### 2.2 types.ts mirror US-1 TenantListResponse
- [ ] **Create `frontend/src/features/admin-tenants/types.ts`**
  - Re-export `TenantState` + `TenantPlan` from `../tenant-settings/types`(no duplicate enum per 17.md spirit + AP-11)
  - `interface TenantListItem { id / code / display_name / state / plan / created_at / updated_at }`
  - `interface TenantListResponse { items / total / limit / offset }`
  - `interface TenantListQuery { state? / plan? / search? / limit / offset }`
  - File header docstring per file-header-convention.md
  - Verify:`cat frontend/src/features/admin-tenants/types.ts` ≥ 30 lines

### 2.3 adminTenantsService.ts plain fetch with URLSearchParams
- [ ] **Create `services/adminTenantsService.ts`**
  - Mirror tenant-settings `_handleResponse<T>` helper(per 57.3 D6)
  - `listTenants(query: TenantListQuery)` 構建 URLSearchParams 並 fetch GET
  - URLSearchParams logic:if state set → params.set("state", value);same for plan/search;always set limit+offset
  - `API_BASE = "/api/v1/admin"` + `credentials: "include"` for auth cookie
  - Verify:`npm run lint` clean for new file

### 2.4 adminTenantsStore.ts Zustand
- [ ] **Create `store/adminTenantsStore.ts`**
  - State:`query` (TenantListQuery with defaults) / `items` (TenantListItem[]) / `total` / `loading` / `error`
  - Actions:`setFilter` (resets offset to 0) / `setPagination` (changes limit/offset) / `loadData` (calls listTenants) / `reset`
  - Default query:`{ state: undefined, plan: undefined, search: undefined, limit: 50, offset: 0 }`
  - Mirror tenant-settings store pattern(57.3)
  - Verify:`npm run build frontend/` clean(no TS errors)

### 2.5 3 Vitest unit tests US-2
- [ ] **Create `frontend/tests/unit/admin-tenants/adminTenantsService.test.ts`**
  - Test 1:`listTenants` happy path with all filters → URLSearchParams string verified + fetch called with correct URL
  - Test 2:`listTenants` happy with no filter → only limit+offset in URL
  - Verify:`npm run test -- adminTenantsService` ≥ 2 pass

- [ ] **Create `frontend/tests/unit/admin-tenants/adminTenantsStore.test.ts`**
  - Test 3:store loadData success → items + total populated + loading=false
  - Verify:`npm run test -- adminTenantsStore` ≥ 1 pass

### 2.6 Day 2 sanity checks
- [ ] **Frontend baselines verify**
  - `cd frontend && npm run lint` clean
  - `cd frontend && npm run build` success / 69 → 71+ modules
  - `cd frontend && npm run test` → 23 → 26+ tests pass(+3)
  - Verify:All 3 sanity checks recorded in progress.md

### 2.7 Day 2 commit + push + progress.md
- [ ] **Commit US-2 + push**
  - Commit message:`feat(frontend, sprint-57-4): add admin-tenants infra (types/service/store + 3 Vitest) (US-2)`
  - progress.md Day 2 section + actual_hr ratio note
  - Verify:`git log main..HEAD --oneline` shows commit;remote up-to-date

---

## Day 3 — US-3 + US-4 Frontend Components + Page Layout

### 3.1 TenantListTable component
- [ ] **Create `components/TenantListTable.tsx`**
  - Columns:Code (monospace) / Display Name / State (badge: ACTIVE green / PROVISIONING+REQUESTED amber / SUSPENDED+ARCHIVED gray) / Plan (badge: ENTERPRISE blue / STANDARD gray) / Created At (relative date or ISO) / View(button → navigate `/tenant-settings/{id}`)
  - Empty state:items.length === 0 → "No tenants match current filter" + Reset Filters 按鈕(call store.reset + loadData)
  - Loading skeleton:5 placeholder rows when `loading === true`
  - Verify:File ≥ 100 lines + lint clean

### 3.2 TenantListFilters component
- [ ] **Create `components/TenantListFilters.tsx`**
  - State dropdown(All / PROVISIONING / REQUESTED / ACTIVE / SUSPENDED / ARCHIVED)
  - Plan dropdown(All / STANDARD / ENTERPRISE)
  - Search input(maxLength=128;onChange + 300ms debounce → trigger setFilter)
  - Apply button(triggers loadData immediately)
  - Reset button(call store.reset → reloadData)
  - Verify:File ≥ 80 lines + lint clean

### 3.3 TenantListPagination component
- [ ] **Create `components/TenantListPagination.tsx`**
  - Prev button(disabled if offset === 0;onClick setPagination({ offset: offset - limit }) + loadData)
  - Next button(disabled if offset + limit >= total;onClick setPagination({ offset: offset + limit }) + loadData)
  - Page indicator: `"{offset+1}-{min(offset+limit,total)} of {total}"`
  - Verify:File ≥ 50 lines + lint clean

### 3.4 pages/admin-tenants/index.tsx page layout
- [ ] **Create `pages/admin-tenants/index.tsx`**
  - Layout:`<TenantListFilters />` 上 + `<TenantListTable />` 中 + `<TenantListPagination />` 下
  - On mount(useEffect):解析 `window.location.search` URLSearchParams → set store filters → loadData
  - On filter/pagination change(subscribe store):更新 URL via `window.history.replaceState` + state object
  - Verify:File ≥ 60 lines + lint clean

### 3.5 5 Vitest unit tests (3 US-3 + 2 US-4)
- [ ] **Create `frontend/tests/unit/admin-tenants/TenantListTable.test.tsx`**
  - Test 1:render with mock items(2 rows)→ assert rows + state badges + plan badges visible
  - Test 2:render with empty items → assert empty state text + Reset Filters button visible
  - Verify:`npm run test -- TenantListTable` ≥ 2 pass

- [ ] **Create `frontend/tests/unit/admin-tenants/TenantListFilters.test.tsx`**
  - Test 3:select state dropdown → assert setFilter called with state value
  - Verify:`npm run test -- TenantListFilters` ≥ 1 pass

- [ ] **Create `frontend/tests/unit/admin-tenants/AdminTenantsPage.test.tsx`**
  - Test 4:page mount → loadData called(spyOn store)
  - Test 5:Pagination next click → setPagination + loadData called
  - Verify:`npm run test -- AdminTenantsPage` ≥ 2 pass

### 3.6 Day 3 sanity checks
- [ ] **Frontend baselines verify**
  - `cd frontend && npm run lint` clean
  - `cd frontend && npm run build` success / 71 → 76+ modules
  - `cd frontend && npm run test` → 26 → 31+ tests pass(+5)
  - Verify:All 3 sanity checks recorded in progress.md

### 3.7 Day 3 commit + push + progress.md
- [ ] **Commit US-3 + US-4 + push**
  - Commit message:`feat(frontend, sprint-57-4): add admin-tenants components + page layout + 5 Vitest (US-3 + US-4)`
  - progress.md Day 3 section + actual_hr ratio note
  - Verify:`git log main..HEAD --oneline` shows commit;remote up-to-date

---

## Day 4 — US-5 Routing + Playwright E2E + Closeout Ceremony

### 4.1 App.tsx route + Home nav Link
- [ ] **Modify `frontend/src/App.tsx`**
  - Add import: `import { AdminTenantsPage } from "./pages/admin-tenants";` (or direct path)
  - Add Route: `<Route path="/admin-tenants" element={<AdminTenantsPage />} />`
  - Add Home nav `<Link to="/admin-tenants">Admin Tenants Console</Link>`(always visible per 57.1 D10 Option C — backend 401/403 surfaces as Error UX)
  - File header MHist:`+ N+1 line: 2026-05-08: Sprint 57.4 — wire /admin-tenants route + Home Link (US-5)`
  - Verify:`grep -n "admin-tenants" frontend/src/App.tsx` shows Route + Link

### 4.2 Playwright e2e admin_tenants_list.spec.ts (4 cases)
- [ ] **Create `frontend/tests/e2e/admin_tenants/admin_tenants_list.spec.ts`**
  - Use `page.route()` browser-layer mock per 57.1 v2 D19 + 57.3 D13 pattern
  - Test 1 (happy path):mock GET → render table → assert ≥1 row + code + state badge visible
  - Test 2 (filter):click state dropdown → select ACTIVE → assert second mocked GET with `?state=ACTIVE` triggered
  - Test 3 (click row navigation):mock GET → click View button → assert URL contains `/tenant-settings/`
  - Test 4 (empty state):mock GET returns `items: [], total: 0` → assert "No tenants match" text + Reset button visible
  - Verify:`cd frontend && npx playwright test admin_tenants_list` ≥ 4 pass(< 30s each)

### 4.3 Final pytest + lint + leak verify
- [ ] **Backend final baselines**
  - `python -m pytest backend/tests/ -q --tb=no` → 1595+ collected / 0 failures(+6)
  - `python -m mypy backend/src --strict` → 0 errors / 295 source files unchanged
  - `python scripts/lint/run_all.py` → 8 V2 lints 8/8 green
  - LLM SDK leak grep → 0
  - Verify:Documented in progress.md ✅
- [ ] **Frontend final baselines**
  - `cd frontend && npm run lint` clean
  - `cd frontend && npm run build` success / 76+ modules / ~210 kB(estimated +6 KB)
  - `cd frontend && npm run test` → 31+ tests pass(+8)
  - Playwright e2e:15 → 19+ tests pass(+4)
  - Verify:Documented in progress.md ✅

### 4.4 Retrospective.md
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-4/retrospective.md`**
  - Q1 What went well
  - Q2 What didn't go well + AD-Sprint-Plan-4 mixed 4th application calibration verify(actual_hr / committed_hr ratio + 4-data-point window mean + KEEP/SHIFT recommendation)
  - Q3 What we learned + Day 0 三-prong second fully-applied sprint observations(time / drifts / ROI evidence vs 57.3 first application)
  - Q4 Audit Debt deferred(明確標 ID + target sprint)
  - Q5 Next steps + Phase 57.x next-sprint candidates(rolling planning;不寫具體未來 sprint 任務,只寫 carryover 候選)
  - Q6 Solo-dev policy validation
  - Verify:`wc -l retrospective.md` ≥ 200 lines

### 4.5 Memory snapshot + MEMORY.md index
- [ ] **Create `memory/project_phase57_4_admin_tenants_list.md`**
  - Same format as `project_phase57_3_tenant_settings.md`
  - Verify:File created + frontmatter complete
- [ ] **Update MEMORY.md index** add 1 line entry
  - Verify:`grep "phase57_4" MEMORY.md` shows 1 result

### 4.6 Open PR + CI green + solo-dev merge
- [ ] **Push branch + open PR**
  - Push:`git push -u origin feature/sprint-57-4-admin-tenants-list-bundle`
  - PR title:`Sprint 57.4 — Phase 57+ SaaS Frontend 3/N: Admin Tenants Console list bundle`
  - PR body:Sprint goal + 5 USs + acceptance + AD-Sprint-Plan-4 4th app verdict + D-findings reference
  - Verify:5 active CI checks green;solo-dev policy review_count=0 satisfied
- [ ] **Squash merge to main**
  - DoD:GitHub UI squash + merge;branch deleted post-merge
  - Verify:main HEAD updated;`git pull main` shows new commit

### 4.7 Closeout PR
- [ ] **Closeout branch + PR**
  - Branch:`chore/sprint-57-4-closeout`
  - Updates:SITUATION-V2 §9 milestones row + §11 Last Updated + Update history;CLAUDE.md Phase / Latest Sprint / main HEAD / Last Updated / Current Phase fields
  - Commit message:`docs(closeout, sprint-57-4): SITUATION-V2 + CLAUDE.md sync to Phase 57+ Frontend SaaS 3/N opens`
  - PR body:reference Sprint 57.4 PR + summary stats(pytest delta / Vitest delta / Playwright delta / Vite build modules delta / calibration ratio)
  - Verify:Squash merge to main;both branches deleted;working tree clean
