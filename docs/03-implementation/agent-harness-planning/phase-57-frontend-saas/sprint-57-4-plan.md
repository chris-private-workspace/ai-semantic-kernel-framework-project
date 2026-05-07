# Sprint 57.4 — Phase 57+ SaaS Frontend 3rd: Admin Tenants Console List View Bundle (backend list endpoint + frontend console)

> **Sprint Type**: Phase 57+ third sprint — mixed scope class (backend + frontend bundle) for first admin tenants console list UX over 56.1+57.3 single-tenant CRUD stack;closes plan-time Prong 2 D1 RED finding (backend admin tenants.py 缺 GET `""` list endpoint);4th application of `mixed` 0.60 multiplier
> **Owner Categories**: §Frontend (16-frontend-design.md §Admin Tenants Console) / §Backend Admin API (extends 56.1+57.3 admin tenants endpoint set with list) / consumes 56.1 Tenant ORM + 56.2 RBAC + 57.3 single-tenant CRUD pattern
> **Phase**: 57 (Frontend SaaS — 3/N sprint;follow-on candidates: Onboarding self-serve wizard (still requires backend re-design) / Feature flags admin UI / Audit log frontend view / DR / GDPR;rolling planning per .claude/rules/sprint-workflow.md)
> **Workload**: 5 days (Day 0-4); bottom-up est ~14 hr → calibrated commit **~8 hr** (multiplier **0.60** per AD-Sprint-Plan-4 scope-class matrix `mixed` 4th application;3-data-point window mean **0.92** ✅ in band → KEEP 0.60 mid-band;若 ratio outside [0.85, 1.20] → AD-Sprint-Plan-N+1 logged)
> **Branch**: `feature/sprint-57-4-admin-tenants-list-bundle`
> **Plan Authority**: This document (per CLAUDE.md §Sprint Execution Workflow)
> **Roadmap Source**: 16-frontend-design.md §Admin Tenants Console + 56.1+57.3 admin tenants endpoint set + Sprint 57.3 retrospective Q5 (Phase 57.x candidate scope user-approved 2026-05-07 Option A pre-emptive bundle) + plan-time Prong 2 探勘 D1 RED 已 caught (backend admin tenants.py 缺 GET `""` list endpoint)
> **AD logging (sub-scope)**: AD-Sprint-Plan-4 scope-class matrix `mixed` 4th application(3-data-point window mean 0.92 KEEP 0.60 mid-band);Day 0 三-prong 探勘 v3 — Path + Content + Schema all attempted(Schema verdict = N/A 但 attempt 完成);此為 second fully-applied 三-prong sprint;ROI evidence accumulating

---

## Sprint Goal

Open the **first admin tenants console list UX surface** for Phase 57+ SaaS Frontend by bundling 1 backend list endpoint + 1 frontend Admin Tenants Console page in a single mixed-scope sprint:

- **US-1**: Backend `GET /admin/tenants` — paginated list of all tenants with optional filter by state / plan + ILIKE search on code+display_name;TenantListResponse Pydantic with items array + total count + limit + offset;require_admin_platform_role per 56.2 RBAC pattern;reuses Tenant ORM + TenantState/TenantPlan enum from 56.1 identity.py;6-8 unit + integration tests
- **US-2**: Frontend `frontend/src/features/admin-tenants/` infra — service + store + types mirroring 57.3 tenant-settings pattern(plain fetch + `_handleResponse<T>` + Zustand;query state + filters + items + pagination);types.ts mirror US-1 TenantListResponse + TenantListQuery;3 Vitest unit tests
- **US-3**: Frontend `features/admin-tenants/components/TenantListTable.tsx`(table with rows: code / display_name / state badge / plan badge / created_at / view button → navigate `/tenant-settings/{id}`)+ `TenantListFilters.tsx`(state dropdown + plan dropdown + search input + apply button);table empty-state + loading skeleton;3 Vitest unit tests
- **US-4**: Frontend `pages/admin-tenants/index.tsx`(layout: filters bar top + table center + pagination bottom)+ `TenantListPagination.tsx`(prev/next + page indicator + total count display);URL query string sync(filters reflected in URL per shareability);2 Vitest unit tests
- **US-5**: Routing + Playwright e2e + closeout — App.tsx 加 `/admin-tenants` route + Home nav link(always visible per 57.1 D10 Option C);3 Playwright e2e specs(`admin_tenants_list.spec.ts` happy + filter + click-row navigation + empty state);retrospective(6 必答 + AD-Sprint-Plan-4 mixed 4th app verify + Phase 57.x next-sprint candidates Q5)+ memory snapshot + SITUATION-V2 + CLAUDE.md sync

Sprint 結束後:
- (a) **Admin Tenants Console 主流量 functional** — admin user 可 browse `/admin-tenants` → 看 paginated tenant list → filter by state/plan → search by code → click row → navigate to `/tenant-settings/{id}` → 編輯後返回 list
- (b) **Backend admin tenants.py 補齊 R(list) surface** — GET `""` 補齐 56.1+57.3 missing list capability;為後續 Onboarding self-serve / multi-tenant impersonation / audit trace 鋪通用 list pattern
- (c) **AD-Sprint-Plan-4 `mixed` 4th-data-point** — 3-data-point window 平均 0.92 in band;若 ratio in band → 4-data-point window 形成 mid-band 穩定信號(若連續 4 in-band 可考慮 evaluate band tightening per matrix 紀律;若 outside → AD-Sprint-Plan-N+1 logged)
- (d) **D1 RED finding plan-time closed** — 與 57.3 同樣 plan-time Prong 2 探勘 catch;Option A pre-emptive bundle user-approved 2026-05-07 → 17.md single-source 不變;可作為 plan-time 探勘 ROI evidence 第 4 個 data point
- (e) **Frontend SaaS 3/N rolling planning continues** — Sprint 57.4 retro Q5 列出 Phase 57.x candidate scope(Onboarding self-serve wizard requires backend self-serve API design / Feature flags admin UI / Audit log frontend view / DR / GDPR / SaaS Stage 2);user approval required per rolling planning 紀律

**主流量驗收標準**:
- `npm run dev` → admin user browse `/admin-tenants` → see all tenants in paginated table(預設 limit=50 / offset=0)
- `npm run dev` → admin user filter by state=ACTIVE → table refreshes only ACTIVE tenants
- `npm run dev` → admin user filter by plan=ENTERPRISE → table refreshes only ENTERPRISE tenants
- `npm run dev` → admin user search "ACME" → table refreshes ILIKE match
- `npm run dev` → admin user click row → navigate to `/tenant-settings/{id}` → 57.3 view+edit functional
- `pytest backend/tests/integration/api/test_admin_tenant_list.py` ≥ 6 new tests pass
- Playwright e2e 3-4 tests pass(happy + filter + click-row + empty)< 30s each
- `npm run lint && npm run build` clean
- `npm run test` (Vitest unit) ≥ 8 new tests pass
- Backend pytest baseline 1589 → 1595+(+6 from US-1)
- 8 V2 lints baseline 8/8 unchanged

---

## Background

### V2 進度

- **22/22 sprints (100%) main progress completed** + **Phase 56-58 SaaS Stage 1 3/3 ✅ CLOSED** (Sprint 56.3) + **Phase 57+ Frontend SaaS 2/N completed**(Sprint 57.1 v2 Cost+SLA dashboards + Sprint 57.3 Tenant Settings bundle)
- main HEAD: `a558f98b` (Sprint 57.3 closeout PR #109) — Day 0 verified
- pytest baseline 1589 / mypy --strict 0/295 source files / 8 V2 lints 8/8 green / LLM SDK leak 0
- Vitest baseline 23 / Playwright e2e baseline 15 / Vite build 69 modules / 203.02 kB
- 57.3 calibration `mixed` 0.60 mid-band 3rd application ratio **0.57** under band (3-data-point mean **0.92 ✅** in band — KEEP 0.60 per matrix discipline single-sprint not enough to shift mid-band)
- 14-sprint cumulative window 8/14 (57%) in-band slipped below 60% threshold for first time after 3 consecutive sprints in-band
- **本 sprint = Phase 57+ SaaS Frontend 第 3 個 sprint**(3/N rolling;57.1 v2 Cost+SLA + 57.3 Tenant Settings bundle delivered;57.4 Admin Tenants Console list view)

### 為什麼 57.4 是 Admin Tenants Console list bundle 而非純 frontend

User approved 2026-05-07 Option A(`backend list endpoint + frontend Admin Tenants Console page bundle` — pre-emptive pivot from naive medium-frontend assumption per plan-time Prong 2 catch):

1. **57.4 plan-time Prong 2 catch** — Day 0 plan-time content verify 揭露 56.1+57.3 admin tenants.py 既有 endpoints (POST `""` create + GET `/{id}/onboarding-status` + POST `/{id}/onboarding/{step}` + GET `/{id}` + PATCH `/{id}`),**沒有** GET `""` list endpoint;Admin Tenants Console UI 必要的 list+filter+pagination 完全不存在;類比 57.3 v1 D1 RED catch
2. **Option A pre-emptive bundle 解決真正 backend gap** — 而非 abort;新增 GET `""` list 後 future Onboarding self-serve admin / impersonation / audit list view / multi-tenant compliance dashboard 全可重用 list pattern;ROI 高
3. **Mixed scope class 4th data point** — `mixed` 多 backend + frontend 比例對於 Phase 57+ 持續 frontend SaaS 推進是常見組合;補強 calibration matrix mixed 軸從 3-data-point → 4-data-point window
4. **Conservative US-1 scope** — 為避免 over-推測,US-1 list endpoint 只暴露 必要 query params(state / plan / search / limit / offset);不在 list endpoint 跨界(no per-tenant detail data;list-only;rich detail 走 57.3 GET `/{id}`)
5. **AD-Plan-3 + AD-Plan-4 兩+三 prong already fold-in to sprint-workflow.md §Step 2.5 (Sprint 55.6 + 57.1 v2)** — 此 sprint 為 second fully-applied Day 0 三-prong 探勘 sprint(Path + Content + Schema all attempted);可作為 process AD ROI 第 4 個 data point(57.3 為 first;57.4 為 second)

### 既有結構(Day 0 plan-time 探勘 grep 已驗證以下事實)

✅ **以下 layout 是 plan-time 已 verified via Day 0 三-prong 探勘**:

```
backend/src/api/v1/admin/                          # ✅ 56.1+56.2+56.3+57.3 既有
├── tenants.py                                     # ⚠️ MODIFY (US-1: add GET "" list endpoint)
│   ├── @router.post("")                           # ✅ existing (56.1 create_tenant)
│   ├── @router.get("/{id}/onboarding-status")     # ✅ existing (56.1)
│   ├── @router.post("/{id}/onboarding/{step}")    # ✅ existing (56.1)
│   ├── @router.get("/{id}")                       # ✅ existing (57.3)
│   ├── @router.patch("/{id}")                     # ✅ existing (57.3)
│   ├── @router.get("")                            # ❌ NEW (US-1 list endpoint)
│   ├── class TenantResponse                       # ✅ existing (57.3 reusable for /{id})
│   ├── class TenantListItem                       # ❌ NEW (US-1 lightweight subset)
│   └── class TenantListResponse                   # ❌ NEW (US-1 items+pagination wrapper)
├── cost_summary.py                                # ✅ existing (56.3)
└── sla_reports.py                                 # ✅ existing (56.3)

backend/src/platform_layer/identity/auth.py        # ✅ 56.2 existing
└── require_admin_platform_role                    # ✅ existing reusable

backend/src/infrastructure/db/models/identity.py   # ✅ 56.1 existing (no migration needed)
├── class Tenant                                   # ✅ existing (filter+search target)
├── class TenantState (enum)                       # ✅ existing reusable
└── class TenantPlan (enum)                        # ✅ existing reusable

frontend/src/                                      # ✅ 57.1 v2 + 57.3 既有 + Vitest setup
├── features/
│   ├── chat_v2/                                   # ✅ existing
│   ├── governance/                                # ✅ existing (53.5)
│   ├── cost-dashboard/                            # ✅ existing (57.1 v2)
│   ├── sla-dashboard/                             # ✅ existing (57.1 v2)
│   ├── tenant-settings/                           # ✅ existing (57.3)
│   └── admin-tenants/                             # ❌ NEW (US-2 + US-3 + US-4)
│       ├── components/TenantListTable.tsx         # ❌ NEW
│       ├── components/TenantListFilters.tsx       # ❌ NEW
│       ├── components/TenantListPagination.tsx    # ❌ NEW
│       ├── services/adminTenantsService.ts        # ❌ NEW (plain fetch + _handleResponse)
│       ├── store/adminTenantsStore.ts             # ❌ NEW (Zustand with filters + pagination)
│       └── types.ts                               # ❌ NEW (mirror US-1 TenantListResponse)
├── pages/
│   ├── chat-v2/index.tsx                          # ✅ existing
│   ├── governance/index.tsx                       # ✅ existing
│   ├── verification/index.tsx                     # ✅ existing
│   ├── cost-dashboard/index.tsx                   # ✅ existing
│   ├── sla-dashboard/index.tsx                    # ✅ existing
│   ├── tenant-settings/index.tsx                  # ✅ existing (57.3)
│   └── admin-tenants/index.tsx                    # ❌ NEW (US-4)
└── App.tsx                                        # ⚠️ MODIFY (US-5: add 1 route + 1 nav link)

frontend/tests/                                     # ✅ existing (57.1 v2 + 57.3 Vitest setup)
├── e2e/
│   ├── chat/, governance/, cost_dashboard/, sla_dashboard/, tenant-settings/  # ✅ existing
│   └── admin_tenants/admin_tenants_list.spec.ts   # ❌ NEW (US-5)
└── unit/  (Vitest)                                 # ✅ existing (23 tests baseline)
```

### Sprint 57.3 retrospective Q5 對齊確認

Sprint 57.3 retrospective Q5 列出 Phase 57.x candidate scope:
- Admin tenant console list view (medium-frontend ~10-12 hr × 0.65) ✅ **此 sprint US-1~US-5(pivoted to mixed bundle 0.60 per Day 0 plan-time D1)**
- Onboarding self-serve wizard ⛔ defer pending backend self-serve API
- Feature flags admin UI ⛔ defer Phase 57.x
- Audit log frontend view ⛔ defer Phase 57.x
- DR + WAL streaming (large multi-domain) ⛔ defer Phase 57.x
- Compliance partial GDPR (medium-backend) ⛔ defer Phase 57.x
- SaaS Stage 2 Stripe + 月結 ⛔ defer Phase 57++
- AD-Cat10-VisualVerifier + Frontend-Panel ⛔ defer Phase 57.x Group F
- AD-Cat11-Multiturn / SSEEvents / ParentCtx ⛔ defer Phase 57.x Cat 11 bundle
- AD-CI-6 production launch ⛔ defer Phase 58 dedicated sprint

### V2 紀律 9 項對齊確認

1. **Server-Side First** ✅ Backend GET list 完全 server-side;tenant_id filter 由 require_admin_platform_role JWT 驗證(super-admin 看所有 tenants 是合法 admin operation per 56.2 RBAC pattern)
2. **LLM Provider Neutrality** ✅ 此 sprint 不動 LLM 鏈路
3. **CC Reference 不照搬** ✅ Admin tenants list 為標準 SaaS admin console pattern;plain fetch + Zustand stack 既有
4. **17.md Single-source** ✅ 此 sprint 不新增 cross-category interface;TenantListItem + TenantListResponse 為 admin API 內部 DTO,non-cross-category;不影響 17.md
5. **11+1 範疇歸屬** ✅ US-1 §API admin layer(non-範疇)+ US-2~US-5 全 §Frontend(16-frontend-design.md);無範疇 1-12 backend module 變更;每檔案明確歸屬;無 AP-3
6. **04 anti-patterns** ✅ AP-3 範疇歸屬合規 / AP-4(Potemkin)— 全有實際 wire-up + Playwright e2e + backend pytest 強制驗證 / AP-6(Hybrid Bridge Debt)— 不為 Stage 2 預寫 abstraction;list 嚴格限制 query params;不暴露 list-vs-detail 跨界 logic / AP-9(Verification)— Pydantic v2 query validation + Playwright + 422 invalid query test 強制 verify / AP-11(命名一致)— `admin-tenants` consistent naming(對齊 backend `admin/tenants.py` 路徑 + frontend `pages/admin-tenants/`)
7. **Sprint workflow** ✅ plan → checklist → Day 0 三-prong 探勘(Path + Content + Schema all DONE)→ code → progress → retro;本文件依 57.3 plan 結構鏡射(14 sections / 5 days Day 0-4)
8. **File header convention** ✅ 所有 new 檔案含 file header docstring;modify 檔案加 Modification History entry;MHist 1-line max per AD-Lint-3 + char-count guidance per AD-Lint-MHist-Verbosity
9. **Multi-tenant rule** ✅ tenants 表本身非 TenantScopedMixin(它**就是** tenant);US-1 list 安全靠 require_admin_platform_role super-admin RBAC;non-admin 401/403;RLS check 8 V2 lint check_rls_policies 不適用 tenants 表(56.1 US-5 baseline)

---

## User Stories

### US-1: Backend GET /admin/tenants list endpoint

**As** a SaaS platform super-admin
**I want** a paginated list endpoint that returns all tenants with optional filters by state / plan + ILIKE search
**So that** I can browse + manage all tenants from web UI without DB tools,and frontend Admin Tenants Console page can render the table

**Acceptance**:
- `backend/src/api/v1/admin/tenants.py` 新增 `@router.get("", response_model=TenantListResponse)` endpoint
- Pydantic `TenantListItem`(lightweight subset of TenantResponse)— `id` (UUID) / `code` (str) / `display_name` (str) / `state` (TenantState) / `plan` (TenantPlan) / `created_at` (datetime) / `updated_at` (datetime);**non-include** `provisioning_progress` / `onboarding_progress` / `meta_data`(reduce payload size for list view)
- Pydantic `TenantListResponse` — `items: list[TenantListItem]` / `total: int` / `limit: int` / `offset: int`
- Query parameters:
  - `state: TenantState | None = Query(None)` — filter by exact state
  - `plan: TenantPlan | None = Query(None)` — filter by exact plan
  - `search: str | None = Query(None, max_length=128)` — ILIKE on `code` OR `display_name`
  - `limit: int = Query(50, ge=1, le=200)` — pagination size
  - `offset: int = Query(0, ge=0)` — pagination start
- Auth dependency:`require_admin_platform_role` per 56.2 RBAC pattern(super-admin only;non-platform-admin → 401/403)
- ORDER BY `created_at DESC`(newest first)
- 6-8 tests:happy path no filter / filter by state / filter by plan / search by code substring / pagination limit+offset / 401 unauth / 403 wrong role / response shape assertion / empty result
- `pytest backend/tests/integration/api/test_admin_tenant_list.py` pass
- Backend pytest baseline 1589 → 1595+

### US-2: Frontend Admin Tenants Infrastructure

**As** the React app
**I want** per-feature folder skeleton for admin-tenants mirroring tenant-settings pattern(infra reuse from 57.3)
**So that** Admin Tenants Console UI has consistent code organization,types match US-1 TenantListResponse,store handles filters+pagination+items lifecycle

**Acceptance**:
- `frontend/src/features/admin-tenants/` skeleton:components/ services/ store/ types.ts
- `types.ts`:mirror US-1 TenantListItem + TenantListResponse + `TenantListQuery` interface(state? / plan? / search? / limit / offset);re-export TenantState + TenantPlan from `tenant-settings/types`(no duplicate enum per 17.md spirit + AP-11 命名一致)
- `adminTenantsService.ts`:`listTenants(query: TenantListQuery)` 構建 URLSearchParams 並 fetch GET;mirror `tenantSettingsService.ts` plain fetch + `_handleResponse<T>` pattern;`API_BASE = "/api/v1/admin"`
- `adminTenantsStore.ts`:Zustand state(`query / items / total / loading / error`;actions:`setFilter / setPagination / loadData / reset`);mirror tenant-settings store pattern
- 3 Vitest unit tests:listTenants happy + URLSearchParams construction + store loadData action

### US-3: Frontend Admin Tenants Components (Table + Filters)

**As** a SaaS platform super-admin
**I want** a sortable table with state/plan badges + filter dropdowns + search input
**So that** I can quickly find specific tenants and navigate to their detail page

**Acceptance**:
- `frontend/src/features/admin-tenants/components/TenantListTable.tsx`:
  - Columns: Code (monospace) / Display Name / State (badge color: ACTIVE green / PROVISIONING+REQUESTED amber / SUSPENDED+ARCHIVED gray) / Plan (badge color: ENTERPRISE blue / STANDARD gray) / Created At (relative date) / View(button → `/tenant-settings/{id}`)
  - Empty state:若 items.length === 0 → "No tenants match current filter" 提示 + Reset Filters 按鈕
  - Loading skeleton:5 placeholder rows when `loading === true`
- `frontend/src/features/admin-tenants/components/TenantListFilters.tsx`:
  - State dropdown(All / PROVISIONING / REQUESTED / ACTIVE / SUSPENDED / ARCHIVED)
  - Plan dropdown(All / STANDARD / ENTERPRISE)
  - Search input(maxLength=128;debounced 300ms 後 trigger applyFilters)
  - Apply button + Reset button(reset filters → reload)
- 3 Vitest unit tests:TenantListTable render with mock data(rows + badges)+ TenantListTable empty state + TenantListFilters interactions(select state / search input)

### US-4: Frontend Admin Tenants Page (Layout + Pagination)

**As** a SaaS platform super-admin
**I want** the page layout combining filters + table + pagination with URL query string sync
**So that** I can share filter URLs with team members and navigate naturally

**Acceptance**:
- `frontend/src/pages/admin-tenants/index.tsx` page wrapper:
  - Layout:`<TenantListFilters />` 上 + `<TenantListTable />` 中 + `<TenantListPagination />` 下
  - On mount:解析 URL query string → set store filters → loadData
  - On filter/pagination change:更新 URL query string(history.replaceState)+ trigger loadData
- `frontend/src/features/admin-tenants/components/TenantListPagination.tsx`:
  - Prev button(disabled if offset === 0)
  - Next button(disabled if offset + limit >= total)
  - Page indicator: "{offset+1}-{min(offset+limit,total)} of {total}"
- 2 Vitest unit tests:page mount → loadData called + Pagination prev/next click → setPagination called

### US-5: Routing + Playwright E2E + Closeout Ceremony

**As** the V2 sprint executor
**I want** App.tsx route + Home nav + Playwright e2e tests + retrospective + AD-Sprint-Plan-4 mixed 4th app calibration verify
**So that** Sprint 57.4 closes Phase 57+ SaaS Frontend 3/N with full audit trail

**Acceptance**:
- `frontend/src/App.tsx`:add `<Route path="/admin-tenants" element={<AdminTenantsPage />} />`(non-wildcard)
- Home page nav:add `<Link to="/admin-tenants">Admin Tenants Console</Link>` — always visible per 57.1 D10 Option C(no frontend role gate;backend 401/403 surfaces as Error UX)
- `frontend/tests/e2e/admin_tenants/admin_tenants_list.spec.ts`:
  - happy path:admin auth → load `/admin-tenants` → assert table rendered with mock data 
  - filter:select state=ACTIVE → assert table re-renders with filtered rows
  - click row:click View button → assert URL navigates to `/tenant-settings/{id}` 
  - empty state:filter with no match → assert empty state UI visible
- retrospective.md(6 必答 + AD-Sprint-Plan-4 mixed 4th app calibration verify + Phase 57.x next-sprint candidates Q5 + Day 0 三-prong 探勘 second fully-applied sprint observations)
- Memory snapshot `memory/project_phase57_4_admin_tenants_list.md`
- SITUATION-V2 §9 + CLAUDE.md sync to **Phase 57+ SaaS Frontend 3/N (Sprint 57.4 closed — Admin Tenants Console list bundle)**

---

## Technical Specifications

### Backend Endpoint Pattern (mirror 56.1 + 56.2 + 56.3 + 57.3)

```python
# backend/src/api/v1/admin/tenants.py — NEW additions

class TenantListItem(BaseModel):
    """Lightweight item for tenant list (subset of TenantResponse)."""
    id: UUID
    code: str
    display_name: str
    state: TenantState
    plan: TenantPlan
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    """Paginated list response wrapper."""
    items: list[TenantListItem]
    total: int
    limit: int
    offset: int


@router.get(
    "",
    response_model=TenantListResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def list_tenants(
    state: TenantState | None = Query(None),
    plan: TenantPlan | None = Query(None),
    search: str | None = Query(None, max_length=128),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> TenantListResponse:
    base_stmt = select(Tenant)
    if state is not None:
        base_stmt = base_stmt.where(Tenant.state == state)
    if plan is not None:
        base_stmt = base_stmt.where(Tenant.plan == plan)
    if search is not None:
        like = f"%{search}%"
        base_stmt = base_stmt.where(
            or_(Tenant.code.ilike(like), Tenant.display_name.ilike(like))
        )

    # Total count for pagination
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated items (newest first)
    page_stmt = (
        base_stmt.order_by(Tenant.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(page_stmt)).scalars().all()

    return TenantListResponse(
        items=[TenantListItem.model_validate(t) for t in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
```

### Service Pattern (mirror 57.3 tenantSettingsService.ts)

```typescript
// frontend/src/features/admin-tenants/services/adminTenantsService.ts
import type { TenantListQuery, TenantListResponse } from "../types";

const API_BASE = "/api/v1/admin";

async function _handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export async function listTenants(query: TenantListQuery): Promise<TenantListResponse> {
  const params = new URLSearchParams();
  if (query.state) params.set("state", query.state);
  if (query.plan) params.set("plan", query.plan);
  if (query.search) params.set("search", query.search);
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));

  const response = await fetch(
    `${API_BASE}/tenants?${params.toString()}`,
    { credentials: "include" },
  );
  return _handleResponse<TenantListResponse>(response);
}
```

### Zustand Store Pattern (mirror 57.3 tenantSettingsStore.ts)

```typescript
// frontend/src/features/admin-tenants/store/adminTenantsStore.ts
import { create } from "zustand";
import type { TenantListQuery, TenantListItem } from "../types";
import { listTenants } from "../services/adminTenantsService";

interface AdminTenantsState {
  query: TenantListQuery;
  items: TenantListItem[];
  total: number;
  loading: boolean;
  error: string | null;
  setFilter: (partial: Partial<Omit<TenantListQuery, "limit" | "offset">>) => void;
  setPagination: (partial: { limit?: number; offset?: number }) => void;
  loadData: () => Promise<void>;
  reset: () => void;
}

const DEFAULT_QUERY: TenantListQuery = {
  state: undefined,
  plan: undefined,
  search: undefined,
  limit: 50,
  offset: 0,
};

export const useAdminTenantsStore = create<AdminTenantsState>((set, get) => ({
  query: { ...DEFAULT_QUERY },
  items: [],
  total: 0,
  loading: false,
  error: null,
  setFilter: (partial) =>
    set((s) => ({ query: { ...s.query, ...partial, offset: 0 } })),
  setPagination: (partial) =>
    set((s) => ({ query: { ...s.query, ...partial } })),
  loadData: async () => {
    set({ loading: true, error: null });
    try {
      const data = await listTenants(get().query);
      set({ items: data.items, total: data.total, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
  },
  reset: () => set({ query: { ...DEFAULT_QUERY }, items: [], total: 0, loading: false, error: null }),
}));
```

### Risk Class A/B/C — A retired, B+C still N/A

- Risk Class A: paths-filter retired by 55.6 Option Z;此 sprint 不適用
- Risk Class B: cross-platform mypy unused-ignore — 此 sprint 涉及 backend(US-1);若 import drift(`from sqlalchemy import or_, func` 既有 56.x 用過;低概率)→ 套 `# type: ignore[import-not-found, unused-ignore]` 雙 code per code-quality.md;mitigation 於 Day 1 sanity check 階段
- Risk Class C: module-level singleton — backend 部分若 query helpers 涉及 module-level cache(56.x ServiceFactory pattern);US-1 list endpoint integration test 應在 `tests/integration/api/conftest.py` 確認 autouse `_reset_module_singletons` fixture 已存在(53.6+57.3 baseline);Day 1 sanity check verify

### Day 0 三-prong 探勘 v3 capture (second fully-applied sprint)

Sprint 57.4 是 Day 0 三-prong 探勘 second fully-applied sprint(Path + Content + Schema all attempted;Schema verdict = N/A 但 attempt 完成):
- Prong 1 Path Verify ✅ done — 6 frontend folder existence checks + 2 backend file existence checks
- Prong 2 Content Verify ✅ done — 6 backend assertion grep checks(D1 RED catch — backend admin tenants.py 缺 GET `""` list endpoint)
- Prong 3 Schema Verify ✅ N/A — 無新 DB schema/migration;但 attempt 完成(per fold-in spirit;Tenant ORM 既有 7-9 fields verified for filter+search compatibility)

**ROI:** D1 catch via Prong 2 (~30 min cost) prevented 8-12 hr Day 1+ rework(類比 57.3 Day 0 catch 8-12 hr 57.1 v1-style abort);**ROI ≈ 16-24×**;Sprint 57.4 為 second fully-applied 三-prong sprint;ROI evidence 累積 → Sprint 58+ 可考慮 evaluate 三-prong 為 standard practice

---

## Acceptance Criteria

### Sprint-Wide

- [ ] V2 主進度 22/22 (100%) 不變;Phase 56-58 SaaS Stage 1 backend 3/3 不變;Phase 57+ Frontend SaaS 2/N → 3/N
- [ ] All 8 V2 lints green (新 backend code 不違反 LLM SDK / promptbuilder / sole_mutator / RLS gaps lints)
- [ ] Backend pytest baseline 1589 → 1595+ (≥+6 from US-1)
- [ ] Backend mypy --strict 0 errors (無新 source files;modify existing tenants.py only — 295 unchanged)
- [ ] Backend LLM SDK leak: 0 不變
- [ ] Anti-pattern checklist 11 項對齊
- [ ] 5 active CI checks green(含 Frontend E2E chromium headless per 53.7 baseline)
- [ ] Frontend `npm run lint && npm run build` clean
- [ ] Frontend Vitest ≥+8 new tests pass(3 US-2 + 3 US-3 + 2 US-4)
- [ ] Playwright e2e ≥3 tests pass(happy + filter + click-row + empty)
- [ ] AD-Sprint-Plan-4 `mixed` 4th application captured + verdict logged in retro Q2
- [ ] D1 RED finding plan-time closed(US-1 backend list endpoint production-ready)
- [ ] Day 0 三-prong 探勘 second fully-applied sprint observations documented in retro Q3

### Per-User-Story

詳見 §User Stories acceptance per US.

---

## Day-by-Day Plan

### Day 0 — Setup + Day-0 三-prong 探勘 + Pre-flight Verify

- 0.1 Branch + plan + checklist commit
- 0.2 Day-0 三-prong 探勘(per AD-Plan-3 + AD-Plan-4 fold-in promoted)— **Prong 1 Path Verify**:`features/admin-tenants/` + `pages/admin-tenants/` + `tests/e2e/admin_tenants/` 不存在(expect)/ admin endpoint helpers existing per 57.3 baseline / `require_admin_platform_role` 已存在 / Tenant ORM exists;**Prong 2 Content Verify**:`api/v1/admin/tenants.py` GET `""` (no path param) list endpoint 不存在(D1 RED already caught — 已 user-confirmed Option A pre-emptive bundle 2026-05-07)/ TenantPlan + TenantState enum 已定義 / Tenant ORM `code` + `display_name` columns ILIKE-able / `or_` + `func` from sqlalchemy 既有 56.x usage;**Prong 3 Schema Verify**:N/A 此 sprint(無新 DB schema/migration;但 attempt 完成 per fold-in spirit;Tenant ORM existing 7+ fields all reusable for list query)
- 0.3 Calibration multiplier pre-read(`mixed` 0.60 mid-band 4th application;3-data-point window mean 0.92 KEEP per AD-Sprint-Plan-4 matrix;若 ratio in band → 4-data-point window opens;若 outside → AD-Sprint-Plan-N+1 logged)
- 0.4 Pre-flight verify(backend pytest baseline 1589 / 8 V2 lints baseline / mypy baseline / LLM SDK leak baseline / frontend Vitest 23 + Playwright 15 + Vite build 69 modules / 203.02 kB)
- 0.5 Day 0 progress.md commit + push;catalogue D-findings(D1 closed by Option A pre-emptive bundle;D2-D8 informational);若 scope shift > 20% revise plan §Risks per AD-Plan-1 audit-trail

### Day 1 — US-1 Backend GET list endpoint

- 1.1 Add `class TenantListItem(BaseModel)` with 7 ORM-mirror fields + `from_attributes=True`
- 1.2 Add `class TenantListResponse(BaseModel)` wrapper(items+total+limit+offset)
- 1.3 Add `@router.get("", response_model=TenantListResponse)` endpoint with 5 query params + `require_admin_platform_role`
- 1.4 NEW test file `backend/tests/integration/api/test_admin_tenant_list.py`(6-8 tests:happy no filter / filter by state / filter by plan / search by code / pagination limit+offset / 401 unauth / 403 wrong role / response shape / empty result)
- 1.5 Day 1 sanity checks:`pytest backend/tests/integration/api/test_admin_tenant_list.py` pass / `mypy --strict backend/src/api/v1/admin/tenants.py` clean / 8 V2 lints unchanged
- 1.6 Day 1 commit + push + progress.md

### Day 2 — US-2 Frontend Infra (types + service + store)

- 2.1 `frontend/src/features/admin-tenants/` skeleton(components/ services/ store/ types.ts)
- 2.2 `types.ts` mirror US-1 TenantListItem + TenantListResponse + TenantListQuery interface;re-export TenantState + TenantPlan from `tenant-settings/types`(no duplicate enum)
- 2.3 `adminTenantsService.ts` plain fetch + URLSearchParams + `_handleResponse<T>` helper(mirror tenantSettingsService)
- 2.4 `adminTenantsStore.ts` Zustand store(query + items + pagination state + setFilter + setPagination + loadData actions)
- 2.5 3 Vitest unit tests US-2(listTenants happy + URLSearchParams construction + store loadData action)
- 2.6 Day 2 sanity checks:`npm run lint && npm run build` + Vitest pass
- 2.7 Day 2 commit + push + progress.md

### Day 3 — US-3 + US-4 Frontend Components + Page Layout

- 3.1 `TenantListTable.tsx`(rows + state/plan badges + View button + empty state + loading skeleton)
- 3.2 `TenantListFilters.tsx`(state dropdown + plan dropdown + search input + apply/reset buttons + 300ms debounce)
- 3.3 `TenantListPagination.tsx`(prev/next + page indicator + total count)
- 3.4 `pages/admin-tenants/index.tsx` page wrapper(URL query sync on mount + filter/pagination change)
- 3.5 5 Vitest unit tests(3 US-3 Table render + Empty state + Filters interaction;2 US-4 page mount + Pagination click)
- 3.6 Day 3 sanity checks:`npm run lint && npm run build` + Vitest pass
- 3.7 Day 3 commit + push + progress.md

### Day 4 — US-5 Routing + Playwright E2E + Closeout Ceremony

- 4.1 App.tsx route `/admin-tenants` + Home nav `<Link>`(always visible per 57.1 D10 Option C)
- 4.2 Playwright e2e `admin_tenants_list.spec.ts`(4 cases:happy + filter + click-row + empty)
- 4.3 Final pytest + lint + leak verify(backend 1589 → 1595+ / mypy 0 / 8 V2 lints / LLM SDK 0 / frontend lint+build + Vitest 23 → 31+ + Playwright 15 → 18+)
- 4.4 Retrospective.md(6 必答 + AD-Sprint-Plan-4 mixed 4th app verify + Day 0 三-prong second fully-applied sprint observations + Phase 57.x next-sprint candidates Q5)
- 4.5 Memory snapshot `memory/project_phase57_4_admin_tenants_list.md` + MEMORY.md index update
- 4.6 Open PR + CI green + solo-dev merge to main
- 4.7 Closeout PR(SITUATION-V2 §9 + CLAUDE.md sync to **Phase 57+ SaaS Frontend 3/N (Sprint 57.4 closed — Admin Tenants Console list bundle)**)

---

## File Change List

| File | Status | Lines (est) |
|------|--------|-------------|
| `backend/src/api/v1/admin/tenants.py` | MODIFIED | +90 (TenantListItem + TenantListResponse + 1 endpoint) |
| `backend/tests/integration/api/test_admin_tenant_list.py` | NEW | ~180 |
| `frontend/src/features/admin-tenants/types.ts` | NEW | ~40 |
| `frontend/src/features/admin-tenants/services/adminTenantsService.ts` | NEW | ~50 |
| `frontend/src/features/admin-tenants/store/adminTenantsStore.ts` | NEW | ~80 |
| `frontend/src/features/admin-tenants/components/TenantListTable.tsx` | NEW | ~140 |
| `frontend/src/features/admin-tenants/components/TenantListFilters.tsx` | NEW | ~100 |
| `frontend/src/features/admin-tenants/components/TenantListPagination.tsx` | NEW | ~60 |
| `frontend/src/pages/admin-tenants/index.tsx` | NEW | ~70 |
| `frontend/src/App.tsx` | MODIFIED | +6 (1 Route + 1 Link) |
| `frontend/tests/e2e/admin_tenants/admin_tenants_list.spec.ts` | NEW | ~140 |
| Vitest unit tests (~8 new across 5 files) | NEW | ~280 |
| `docs/.../sprint-57-4/{progress,retrospective}.md` | NEW | ~600 |
| `memory/project_phase57_4_admin_tenants_list.md` | NEW | ~60 |

**Total**: ~640 source LOC + ~600 test LOC + ~660 docs LOC

---

## Dependencies & Risks

### Dependencies (must exist before code starts)

- ✅ Phase 56.1 backend Tenant ORM model `class Tenant` (identity.py) — Day 0 verified
- ✅ Phase 56.1 backend `TenantState` + `TenantPlan` enum (identity.py) — Day 0 verified
- ✅ Phase 56.2 backend `require_admin_platform_role` auth dep (auth.py:140) — Day 0 verified
- ✅ Phase 57.3 backend `TenantResponse` Pydantic + GET `/{id}` + PATCH `/{id}` reusable for click-row navigation — Day 0 verified
- ✅ Phase 57.3 frontend `tenant-settings/types.ts` exports TenantState + TenantPlan enum reusable — Day 0 verified
- ✅ Phase 57.1 v2 frontend cost-dashboard service+store pattern reusable — Day 0 verified
- ✅ Phase 57.1 v2 frontend Vitest setup — Day 0 verified
- ✅ Phase 53.6 frontend Playwright auth fixture pattern reusable — Day 0 verified

### Risk Classes (per sprint-workflow.md §Common Risk Classes)

**Risk Class A (paths-filter vs required_status_checks)**: 已 closed by 55.6 Option Z (paths-filter retired 永久);此 sprint 不適用。

**Risk Class B (cross-platform mypy unused-ignore)**: 低概率 — 此 sprint backend 全用既有依賴(SQLAlchemy 2.x async / FastAPI / Pydantic v2 / 56.x query patterns);若新 import(`or_`, `func`)drift → 套 `# type: ignore[import-not-found, unused-ignore]` 雙 code per code-quality.md;mitigation 於 Day 1 sanity check 階段。

**Risk Class C (module-level singleton across event loops)**: 低概率 — 此 sprint backend 不引入新 module-level singleton;57.3+56.x integration suite already 含 autouse `_reset_module_singletons` fixture;Day 1 sanity check 階段 verify 0 cascade failures。

### Day 0 三-prong 探勘 D-findings v3 (catalogued during Day 0)

**D1** 🔴 RED — backend admin tenants.py 沒 GET `""` list endpoint (只有 POST `""` create + GET/PATCH /{id} for single);**Closed by Option A pre-emptive bundle**(user-approved 2026-05-07 — bundle 1 backend list endpoint + frontend Admin Tenants Console page 解決真正 backend gap)。Implication:此 sprint 多了 US-1 backend scope ~3-4 hr;multiplier shift `medium-frontend` 0.65 → `mixed` 0.60。

**D2** 🟢 GREEN — `require_admin_platform_role` exists at `auth.py:140`(56.2 RBAC pattern reused by 57.3)。Implication:US-1 list endpoint reuse;與 sla_reports + cost_summary + 57.3 GET/PATCH 一致;auth pattern 一致無需新增。

**D3** 🟢 GREEN — Tenant ORM `code` + `display_name` columns 既有 string 型別 + ILIKE-able。Implication:US-1 list endpoint search 用 SQLAlchemy `or_` + `ilike` 即可;不需 ORM column 改動。

**D4** 🟢 GREEN — TenantState + TenantPlan enum 已定義(identity.py)+ 57.3 frontend `tenant-settings/types.ts` re-exports。Implication:US-2 frontend types.ts 直接 re-export(no duplicate enum per 17.md spirit + AP-11 命名一致)。

**D5** 🟢 GREEN — `TenantResponse` Pydantic 既有 57.3 + GET `/{id}` 既有 57.3 — click-row navigation `/tenant-settings/{id}` 直接 functional 無需新 backend 工作。Implication:US-3 frontend View button → router push 即可;US-5 e2e click-row 測試 reuse 57.3 view path。

**D6** 🟠 YELLOW — tenants 表本身**無 RLS policy**(非 TenantScopedMixin — 它**就是** tenant — 56.1 US-5 baseline 0 gaps)。Implication:8 V2 lint check_rls_policies 不適用 tenants 表(已 whitelisted per 56.1 baseline);US-1 list endpoint 安全靠 require_admin_platform_role super-admin RBAC(JWT super-admin role check);non-admin 401/403;非 RLS 隔離(super-admin 看所有 tenants 是合法 admin operation)。

**D7** 🟢 GREEN — 57.3 frontend tenant-settings/store/tenantSettingsStore.ts pattern reusable for adminTenantsStore.ts(Zustand + plain fetch + saving/saveError state simplified to loading+error since list view non-mutating)。Implication:US-2 store 開發 ~30-40 min(pattern reuse 高);無新概念。

**D8** 🟠 YELLOW — Pagination URL query string sync(US-4)需 `history.replaceState` + `URLSearchParams` 處理;React Router 非預設提供 query state hook(較 React Router v6 新版功能 `useSearchParams` 可考慮);Day 3 first-thing 確認 React Router version + `useSearchParams` API 可用性;若不可用 → fallback 用 `window.history.replaceState` 直接操作。

**Cumulative scope shift** = +backend 3-4 hr(D1 → US-1)= **+25-30%** vs naive medium-frontend 假設(~10 hr × 0.65)→ pivot to `mixed` 0.60(3-data-point mean 0.92)→ ~14 hr × 0.60 = ~8 hr;< 50% threshold per AD-Plan-1(若 > 50% 則 abort);user-confirmed Option A 2026-05-07 → 繼續 Day 1+;no plan re-version required mid-sprint。

### Sprint-specific Risks

| Risk | Mitigation |
|------|-----------|
| US-1 ILIKE on Tenant.code 大表性能(若未來 tenants 表 > 10K) | 此 sprint 範圍內 tenants 表通常 < 100 rows(per-instance SaaS);Day 1 sanity check 不 benchmark;Phase 58+ scaling sprint 再評估 add `code` ILIKE index |
| URL query string sync 在 Playwright e2e 環境若 React Router v6 useSearchParams 不可用 | Day 3 first thing verify React Router version;若 v6+ → 用 `useSearchParams`;若 v5 → fallback `window.history.replaceState` + `useEffect` 監聽 location.search |
| Vitest unit test 對 Zustand store async loadData 的測試需要 `vi.mocked` adminTenantsService.listTenants | 既有 57.3 tenant-settings store 測試 pattern reusable;Day 2 直接 follow |
| Frontend bundle size 增量(~70 modules vs 69 baseline) | 控制 +6 modules;< 5% size 增加;Vite tree-shaking 應自動處理 |

---

## Definition of Done

詳見 §Acceptance Criteria — Sprint-Wide。

---

## References

- 16-frontend-design.md §Admin Tenants Console (per Phase 57+ candidate scope)
- 56.1 admin tenants endpoint set (POST create + GET onboarding-status + POST onboarding-step)
- 57.3 admin tenants single CRUD (GET /{id} + PATCH /{id})
- 56.2 RBAC pattern (require_admin_platform_role)
- 53.5/53.6 Frontend governance + Playwright e2e patterns
- 57.1 v2 frontend cost-dashboard + sla-dashboard infra patterns
- 57.3 frontend tenant-settings infra (Zustand + plain fetch + types)
- AD-Sprint-Plan-4 scope-class multiplier matrix (`mixed` 0.60 4th application)
- AD-Plan-3 + AD-Plan-4 sprint-workflow.md §Step 2.5 Prong 2 + 3 (promoted Sprint 55.6 + 57.1 v2 fold-in)
- .claude/rules/sprint-workflow.md §Common Risk Classes
- Sprint 57.3 plan + checklist (format template — 14 sections / 5 days Day 0-4)
