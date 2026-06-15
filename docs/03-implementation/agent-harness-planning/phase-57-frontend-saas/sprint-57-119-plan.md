# Sprint 57.119 Plan — Skills System Visibility + Preview (admin authoring UX): The Skills admin tab (57.114) lets a tenant author custom skills (name/description/instructions CRUD), but it shows ONLY the tenant's own overlay skills — the system-bundled skills (`code-review` / `digest` / `summarize`, the base set every tenant's skills overlay) are INVISIBLE in any admin UI. An admin authoring a skill can't see what bundled skills exist, which names would shadow a built-in one, or what a skill's full instructions actually say before saving. This slice — the chosen thin vertical of `AD-Skills-Authoring-UI` (which bundles versioning / hot-reload / authoring-UI; tenant CRUD already exists) — adds a read-only **"System Skills"** section to the tab (the bundled catalog with a "has script" badge + a "shadowed by yours" tag) + a **Preview** modal that renders any skill's full instructions (bundled or tenant). One new read-only GET endpoint over the existing `get_default_skill_registry()` + a read-only UI section + a preview modal. NO DB / migration / wire / codegen; read-only, respects 57.118's tenant-script deferral (no script editing). Versioning + hot-reload stay carried.

**Status**: Approved-to-execute (user 2026-06-15: "把 skills 相關工作完整地完成" — 57.119 of the remaining 119/120/121; scope aligned via AskUserQuestion 2026-06-15: **System skills 可見 + preview** over versioning / hot-reload)
**Branch**: `feature/sprint-57-119-skills-system-visibility`
**Base**: `main` HEAD `cf83b274` (post-#293 — Sprint 57.118 skills bundled scripts)
**Slice**: Skills System epic — **system-skills visibility + preview** (the chosen thin vertical of `AD-Skills-Authoring-UI`). 57.113 model-invoked lazy-load / 57.114 per-tenant overlay + the authoring tab / 57.115 `/skill-name` force-load / 57.116 user-turn chip / 57.117 catalog hardening / 57.118 bundled scripts. This rounds out the **authoring UX**: an admin can now SEE the base set their overlays apply on top of + preview any skill's body. Extends the existing 57.114 Skills tab + adds a thin read-only endpoint over the existing bundled registry — NO new domain, NO new execution/security model → a **feature continuation** (NO design note, mirrors 57.116/117; unlike 57.113/115/118 spikes). CHANGE-086.
**Scope decisions** (per the AskUserQuestion alignment + thin-vertical discipline): (a) **Visibility = read-only** — the system-bundled skills are git-deployed assets; the admin SEES them (name / description / has-script / shadowed-by-tenant) but does NOT edit/disable them here (editing bundled skills is a redeploy; a disable-toggle is a separate, larger governance slice). (b) **Preview = render the full instructions** of any skill (bundled or tenant) read-only in a modal — bundled instructions come from the new system endpoint; tenant instructions are ALREADY in the existing list response (`SkillResponse.instructions`). (c) **`overridden` is computed per-tenant** — the new endpoint cross-checks the tenant's skill names so a bundled skill the tenant has shadowed shows a "shadowed by your skill" tag (the tenant_id in the path is meaningful — it's "the base set available to THIS tenant"). (d) **NO script editing / NO script-source display** — `has_script` is a boolean badge only (57.118's tenant-script deferral holds; the script source is code, not shown). (e) **NO DB / NO migration / NO wire / NO codegen** — one read-only GET over `get_default_skill_registry()` + a TanStack read hook + a read-only tab section + a preview modal. Versioning + bundled-registry hot-reload stay carried (separate `AD-Skills-Authoring-UI` legs).

---

## 0. Background

The Skills System epic (Sprints 57.113-118) gave the platform CC-style skills: a system-global `SkillRegistry` loads bundled `SKILL.md` files (`Skill(name, description, instructions, script)`, a frozen value object — `registry.py:54-68`); the model lazy-loads a skill via `read_skill` (57.113) / force-loads via `/skill-name` (57.115); a per-tenant DB overlay (`tenant_skills`, 57.114) lets a tenant author custom skills that overlay the bundled set by name (`with_overlay`); 57.117 added count/size quotas; 57.118 let a system-bundled skill carry an executable `script` run via `run_skill_script`.

The per-tenant authoring UI — the tenant-settings **"Skills"** tab (`SkillsTab.tsx`, 57.114) — is a complete name/description/instructions CRUD (Add / inline Edit / 2-step Delete), quota-aware (N/max + disable-Add + textarea cap, 57.117). BUT it shows **only the tenant's own overlay skills** (`useTenantSkills` → `GET /admin/tenants/{id}/skills` → the `tenant_skills` rows). The **system-bundled skills** — `code-review` / `digest` / `summarize`, the base set the model actually sees and every tenant's overlay applies ON TOP of — are **invisible in any admin UI**. There is no read-only "system skills" view, no preview of a skill's rendered instructions, and no indication of which bundled names a tenant has shadowed.

`AD-Skills-Authoring-UI` (logged 57.113) asks for "skill versioning / hot-reload / an authoring admin UI (the registry loads once at first access; no reload)". The authoring CRUD already exists (57.114); the chosen thin vertical (AskUserQuestion 2026-06-15) is the **highest authoring-UX value + thinnest + safest** of the three: **system-skills visibility + preview**. You can't author well against a base set you can't see.

### Design decision (a NEW read-only `GET /admin/tenants/{tenant_id}/skills/system` over `get_default_skill_registry().list()` → `SystemSkillListResponse{skills:[{name, description, instructions, has_script, overridden}]}` (overridden = the name is in this tenant's skills) → a `useSystemSkills` TanStack hook → a read-only "System Skills" section in `SkillsTab.tsx` (has-script badge + shadowed tag + a Preview button) → a Preview modal rendering any skill's instructions; NO DB / NO migration / NO wire / NO codegen / NO new SSE event)

- **US-1 is "the backend can list the system skills for a tenant"** (api/platform): a NEW read-only `GET /admin/tenants/{tenant_id}/skills/system` (admin-gated, mirrors the sibling `GET /{tenant_id}/skills`). It loads the bundled skills from `get_default_skill_registry().list()` + the tenant's skill names from `tenant_skill_service.list_skills` (already used by the sibling GET) and returns `SystemSkillListResponse{skills:[SystemSkillResponse{name, description, instructions, has_script, overridden}]}` where `has_script = skill.script is not None` and `overridden = name in {tenant skill names}`. Read-only, no audit. The instructions ARE included (only ~3 bundled skills — small) so the preview needs no 2nd endpoint.
- **US-2 is "the FE can fetch them"** (frontend service + hook): `fetchSystemSkills(tenantId) -> SystemSkillListResponse` (`tenantSettingsService.ts`) + `useSystemSkills(tenantId)` (`useTenantSkills.ts`, TanStack — a 5th read hook alongside the existing 4). A new `SystemSkill` interface (`types.ts`).
- **US-3 is "the admin SEES the system skills"** (frontend): a read-only **"System Skills"** section in `SkillsTab.tsx` (a sibling block under the existing tenant-skills Card, or a second Card) listing each bundled skill: name (mono) + description (subtle) + a "🔧 script" badge when `has_script` + a "shadowed by your skill" tag when `overridden` + a **Preview** button. No edit/delete (read-only).
- **US-4 is "the admin can preview any skill's body"** (frontend): a **Preview** modal/panel (reused for system + tenant rows) that renders the selected skill's full `instructions` read-only (mono `<pre>`, scrollable). Bundled instructions come from `useSystemSkills`; tenant instructions are already in `useTenantSkills`' `SkillResponse.instructions`. A Preview button is added to the existing tenant rows too.
- **US-5 is "tests"**: backend (the new endpoint: returns the 3 bundled skills; `digest` has `has_script=true`, the others `false`; `instructions` present; `overridden=true` when the tenant has a same-name skill; admin-auth 403 for non-admin; 404 for a bad tenant) + frontend Vitest (the System Skills section renders the bundled skills; the has-script badge on `digest`; the shadowed tag when a tenant skill shares a name; the Preview modal opens + shows the instructions; Preview works for a tenant row).
- **US-6 is "the drive-through"** (real admin tab + real backend): open the tenant-settings Skills tab as a real admin (acme-skills) → see the "System Skills" section with `code-review` / `digest` / `summarize` → `digest` shows the "🔧 script" badge → (acme-skills has a `release-notes` tenant override; if a bundled name is shadowed it shows the "shadowed" tag) → click Preview on `digest` → the modal renders `digest.md`'s instructions → Preview a tenant skill too. Screenshots + observed-vs-intended in progress.md.
- **Rejected / deferred**: skill versioning + version history (a DB migration + a history table + UI — a separate `AD-Skills-Authoring-UI` leg); bundled-registry hot-reload (an admin reload action — low prod value, bundled skills are git-deployed; a separate leg); editing / disabling bundled skills from the UI (bundled = redeploy; a disable-toggle is a larger governance slice); displaying / editing the script SOURCE (57.118's tenant-script deferral holds — `has_script` is a boolean only); any wire / codegen / SSE / migration / new-table change.

### Ground truth (Day-0 head-start — 1 Explore-agent spike + direct reads, file:line on `main` HEAD `cf83b274`; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**Backend (US-1):**
- `agent_harness/skills/registry.py`: `Skill` frozen dataclass (`:54-68`, now `name`/`description`/`instructions`/`script: str | None`); `get_default_skill_registry()` (`:189-194`, lazy module-global, `.list()` → the bundled skills); `render_skill_instructions` (`:224`). → the system endpoint iterates `get_default_skill_registry().list()` and reads `.name`/`.description`/`.instructions`/`.script`.
- `api/v1/admin/tenants.py`: the skills router (`router = APIRouter(prefix="/admin/tenants")`, `:144`); `SkillResponse` (`:1894`, id/name/description/instructions/created_at/updated_at); `SkillListResponse` (`:1905`); `_project_skill` (`:1915`); `GET /{tenant_id}/skills` → `list_tenant_skills` (`:1926`, `Depends(get_db_session)` + `Depends(require_admin_platform_role)` + `_load_tenant_or_404` + `tenant_skill_service.list_skills`). → add `SystemSkillResponse` + `SystemSkillListResponse` + `GET /{tenant_id}/skills/system` → `list_system_skills` (mirror the auth + 404 + service.list_skills for the overridden cross-check).

**Frontend (US-2/US-3/US-4):**
- `frontend/src/features/tenant-settings/types.ts`: `Skill` (`:403-410`); `SkillListResponse` (`:412-422`). → add `SystemSkill` interface + `SystemSkillListResponse`.
- `frontend/src/features/tenant-settings/services/tenantSettingsService.ts`: `fetchTenantSkills` (`:458`) — the fetch shape to mirror. → add `fetchSystemSkills(tenantId)`.
- `frontend/src/features/tenant-settings/hooks/useTenantSkills.ts`: `useTenantSkills` (read) + 3 mutations (`:67-70` imports). → add `useSystemSkills(tenantId)` (TanStack read; queryKey `["tenant-skills-system", tenantId]`).
- `frontend/src/features/tenant-settings/components/tabs/SkillsTab.tsx` (`:68-458`): the Card + the tenant-skills list (`renderDraftFields` + the row map `:336-452`). → add a read-only "System Skills" section + a Preview modal + a Preview button on the tenant rows. Mockup-ui Card + inline tokens (admin-internal page; no mockup-fidelity CSS), English copy, mirrors the existing idioms.

**Tests + baselines:**
- Backend: the per-tenant skills tests (`tests/integration/api/test_admin_tenant_skills.py` — Glob the basename Day-0) — add the system-skills endpoint cases. FE: `SkillsTab.test.tsx` (Glob Day-0) — add the system-section + preview cases.
- **Baselines (57.118 closeout)**: full pytest **2644+5skip** · wire count **24** · FE Vitest **873** (note: 57.118 added no FE; 57.116 was 873 — re-verify Day-0) · mockup-fidelity **51** · mypy `src` **0/371** · run_all **10/10**. Re-verify Day-0.
- **No migration. No wire / codegen change (count 24). NO design note (feature continuation).** **CHANGE next free = 086** (085 = 57.118).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

(1) The exact `SkillResponse`/`SkillListResponse`/`_project_skill` shapes + the `list_tenant_skills` auth deps (`require_admin_platform_role` + `_load_tenant_or_404` + `tenant_skill_service.list_skills`) — to mirror for the system endpoint. (2) `get_default_skill_registry().list()` returns `Skill` objects with `.script` (57.118) — confirm `has_script = skill.script is not None` reads correctly. (3) The `SkillsTab.tsx` structure (the Card, the tenant list row map) — where to insert the System Skills section + the Preview button without disturbing the 57.114/117 add/edit/delete/quota idioms. (4) The FE `types.ts` Skill/SkillListResponse shapes + `tenantSettingsService.ts` fetch idiom + `useTenantSkills.ts` query-key convention — to mirror for `SystemSkill`/`fetchSystemSkills`/`useSystemSkills`. (5) The test basenames (`test_admin_tenant_skills.py` + `SkillsTab.test.tsx`) — Glob before any NEW file (the unique-basename lesson). (6) The FE Vitest baseline (873 vs the actual at HEAD `cf83b274`). (7) Whether a preview MODAL primitive already exists in mockup-ui (a `Modal`/`Dialog`) or whether to use an inline expandable panel (avoid a new dependency; mirror the existing inline-form pattern). (8) Baselines re-verify (pytest 2644+5skip / wire 24 / Vitest / mockup 51 / mypy 0/371 / run_all 10/10).

## 1. Sprint Goal

The admin Skills tab gains a read-only **"System Skills"** view — the bundled catalog (`code-review` / `digest` / `summarize`) with a "🔧 script" badge (`digest`) + a "shadowed by your skill" tag for any bundled name this tenant has overridden — plus a **Preview** modal that renders any skill's full instructions (bundled or tenant) read-only. Backed by ONE new read-only `GET /admin/tenants/{tenant_id}/skills/system` over the existing `get_default_skill_registry()` (computing `overridden` from the tenant's own skills) + a `useSystemSkills` TanStack hook + a read-only tab section + a Preview modal. Proven by a real admin-tab drive-through. Rounds out the Skills authoring UX (you can now see the base set you overlay + preview any body); skill versioning + bundled-registry hot-reload stay carried under `AD-Skills-Authoring-UI`. NO DB / NO migration / NO wire (count 24) / NO codegen. Feature continuation (NO design note). CHANGE-086.

## 2. User Stories

- **US-1**: 作為 platform，我希望後端能列出某 tenant 的 system skills：新唯讀 `GET /admin/tenants/{tenant_id}/skills/system`（admin-gated，鏡像 sibling `GET /{tenant_id}/skills`）載入 `get_default_skill_registry().list()` 的 bundled skills + 該 tenant 的 skill 名稱，回 `SystemSkillListResponse{skills:[{name, description, instructions, has_script, overridden}]}`（`has_script = script is not None`、`overridden = name 在該 tenant 的 skills 內`），以便 admin UI 能呈現 base set。
- **US-2**: 作為 frontend，我希望能 fetch：`fetchSystemSkills(tenantId)` + `useSystemSkills(tenantId)`（TanStack 第 5 個讀 hook）+ `SystemSkill` interface（types.ts），鏡像既有 `fetchTenantSkills`/`useTenantSkills` idiom，以便 tab 能消費。
- **US-3**: 作為 admin，我希望看到 system skills：`SkillsTab.tsx` 加一個唯讀「System Skills」區，列每個 bundled skill 的 name + description + 「🔧 script」badge（has_script 時）+ 「shadowed by your skill」tag（overridden 時）+ Preview 鈕（無 edit/delete），以便我 authoring 時看得到要 overlay 的 base set + 哪些 name 被我 shadow。
- **US-4**: 作為 admin，我希望預覽任何 skill 的完整 instructions：一個 Preview modal（system + tenant 共用）唯讀渲染選定 skill 的 `instructions`（mono `<pre>`、可捲動）；bundled instructions 來自 `useSystemSkills`，tenant instructions 已在 `useTenantSkills` 的 `SkillResponse.instructions`；tenant rows 也加 Preview 鈕，以便存檔前看清 skill body。
- **US-5**: 作為 platform，我希望測試守住：backend（新 endpoint：回 3 個 bundled skills / `digest` has_script=true 其餘 false / instructions present / tenant 有同名 skill 時 overridden=true / 非 admin 403 / 壞 tenant 404）+ FE Vitest（System Skills 區渲染 / digest 的 has-script badge / 同名時 shadowed tag / Preview modal 開 + 顯示 instructions / tenant row Preview），以便回歸受保護。
- **US-6**: 作為 reviewer，我希望真 drive-through（真 admin tab + 真 backend）：開 tenant-settings Skills tab（acme-skills）→ 見「System Skills」區含 code-review/digest/summarize → digest 有「🔧 script」badge →（被 shadow 的 bundled name 顯示 tag）→ 點 digest 的 Preview → modal 渲染 digest.md instructions → tenant skill 也能 Preview；截圖 + observed-vs-intended。

## 3. Technical Specifications

### 3.0 Architecture (a NEW read-only `GET /admin/tenants/{tenant_id}/skills/system` over `get_default_skill_registry()` → `SystemSkillListResponse` (with `has_script` + per-tenant `overridden`) → `fetchSystemSkills` + `useSystemSkills` → a read-only "System Skills" section + a Preview modal in `SkillsTab.tsx`; NO DB / NO migration / NO wire / NO codegen / NO new SSE event / NO new table)

```
api/v1/admin/tenants.py (EDIT): + SystemSkillResponse + SystemSkillListResponse + GET /{tenant_id}/skills/system → list_system_skills
frontend/src/features/tenant-settings/types.ts (EDIT): + SystemSkill + SystemSkillListResponse
frontend/src/features/tenant-settings/services/tenantSettingsService.ts (EDIT): + fetchSystemSkills(tenantId)
frontend/src/features/tenant-settings/hooks/useTenantSkills.ts (EDIT): + useSystemSkills(tenantId)
frontend/src/features/tenant-settings/components/tabs/SkillsTab.tsx (EDIT): + System Skills read-only section + Preview modal + Preview on tenant rows
agent_harness/skills/registry.py / loop.py / events.py / sse.py / event_wire_schema / codegen / migration / a new table: UNTOUCHED / NONE
```

### 3.1 The system-skills read endpoint (US-1)

- **`api/v1/admin/tenants.py`** `SystemSkillResponse(BaseModel)`: `name: str`, `description: str`, `instructions: str`, `has_script: bool`, `overridden: bool`. `SystemSkillListResponse(BaseModel)`: `skills: list[SystemSkillResponse]`.
- **`GET /{tenant_id}/skills/system` → `list_system_skills`**: same deps as `list_tenant_skills` (`Depends(get_db_session)` + `Depends(require_admin_platform_role)`); `await _load_tenant_or_404(db, tenant_id)`; `tenant_names = {row.name for row in await tenant_skill_service.list_skills(db, tenant_id=tenant_id)}`; `bundled = get_default_skill_registry().list()`; return `SystemSkillListResponse(skills=[SystemSkillResponse(name=s.name, description=s.description, instructions=s.instructions, has_script=s.script is not None, overridden=s.name in tenant_names) for s in bundled])`. Read-only, no audit. Import `get_default_skill_registry` from `agent_harness.skills` (Day-0 confirm the export).

### 3.2 The FE data layer (US-2)

- **`types.ts`**: `export interface SystemSkill { name: string; description: string; instructions: string; has_script: boolean; overridden: boolean; }` + `export interface SystemSkillListResponse { skills: SystemSkill[]; }`.
- **`tenantSettingsService.ts`**: `export async function fetchSystemSkills(tenantId: string): Promise<SystemSkillListResponse>` — `GET /admin/tenants/{tenantId}/skills/system` (mirror `fetchTenantSkills`).
- **`useTenantSkills.ts`**: `export function useSystemSkills(tenantId: string)` — `useQuery({ queryKey: ["tenant-skills-system", tenantId], queryFn: () => fetchSystemSkills(tenantId) })` (mirror `useTenantSkills`).

### 3.3 The System Skills read-only section (US-3)

- **`SkillsTab.tsx`**: under the existing tenant-skills Card (or a sibling Card "System Skills"), render `systemSkills.data?.skills` read-only: each row = name (mono) + description (subtle) + badges — a "🔧 script" badge when `has_script` (a subtle pill, `var(--border)`/`var(--muted)` tokens) + a "shadowed by your skill" tag when `overridden` (subtle, `var(--warning)`/`var(--muted)`) — + a "Preview" button (`btn-secondary`, opens the modal). No edit/delete. Loading / error states mirror the tenant list. `data-testid`s: `system-skills-section`, `system-skills-row-{name}`, `system-skill-script-badge-{name}`, `system-skill-shadowed-{name}`, `system-skill-preview-btn-{name}`.
- A short hint: "Built-in skills available to every tenant. Your custom skills above overlay these by name."

### 3.4 The Preview modal (US-4)

- **`SkillsTab.tsx`**: a `previewSkill: { name: string; instructions: string } | null` state. A Preview button (system rows + tenant rows) sets it; a modal/overlay renders `name` + a read-only mono `<pre>` of `instructions` (scrollable, max-height) + a Close button. Day-0: check mockup-ui for an existing `Modal`/`Dialog`; if none, an inline fixed-overlay panel (mirror the existing inline-form `var(--border)`/`var(--radius)` idiom; `data-testid="skill-preview-modal"` + `skill-preview-close-btn`). Tenant rows: a Preview button alongside Edit/Delete passing `{name, instructions}` from the tenant `Skill`.

### 3.5 Drive-through (US-6) — real admin tab + real backend

1. Real admin (acme-skills, dev-login) + a fresh repo-root backend (Risk Class E clean restart + `Win32_Process` orphan sweep + a startup probe). Open `/tenant-settings` → the Skills tab.
2. Observe the new **System Skills** section: `code-review` / `digest` / `summarize` listed read-only; `digest` shows the "🔧 script" badge; any bundled name this tenant has overridden shows the "shadowed by your skill" tag (acme-skills has a `release-notes` tenant override — not a bundled name — so create/keep a same-name override OR just confirm the tag logic via a tenant skill named after a bundled one if present).
3. Click **Preview** on `digest` → the modal renders `digest.md`'s instructions verbatim. Click Preview on a tenant skill → its instructions render. Confirm each control is live (real fetch, real render — not a fixture): screenshots + observed-vs-intended in progress.md.

### 3.6 What is explicitly NOT done

Skill versioning + version history (a DB migration + a history table + UI — a separate `AD-Skills-Authoring-UI` leg); bundled-registry hot-reload (an admin reload action — bundled skills are git-deployed, low prod value; a separate leg); editing / disabling / creating bundled skills from the UI (bundled = redeploy; a disable-toggle is a larger governance slice); displaying or editing the script SOURCE (57.118's tenant-script deferral holds — `has_script` is a boolean badge only); any wire / codegen / SSE / migration / new-table / new-DB-column change.

### 3.7 Validation (US-1..US-6)

Backend: the new endpoint returns the 3 bundled skills; `digest.has_script is True`, `code-review`/`summarize` `has_script is False`; `instructions` present (non-empty); `overridden is True` when the tenant has a same-name skill (and False otherwise); a non-admin → 403; a bad tenant → 404. FE Vitest: the System Skills section renders the bundled skills + the has-script badge on `digest` + the shadowed tag when a tenant skill shares a name; the Preview modal opens + shows the `instructions`; a tenant-row Preview works. Gates: mypy strict 0 · run_all 10/10 (count 24, NO codegen change) · full pytest +N (0 del) vs 2644 · Vitest +M vs the HEAD baseline · mockup-fidelity 51 holds (admin-internal tab — inline tokens, no mockup CSS) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · LLM-neutrality + `check_cross_category_import` green (the endpoint reads the Cat-5 registry from the api layer — same as the chat path; confirm Day-0 no boundary breach).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/v1/admin/tenants.py` | EDIT — `SystemSkillResponse` + `SystemSkillListResponse` + `GET /{tenant_id}/skills/system` → `list_system_skills` |
| 2 | `frontend/src/features/tenant-settings/types.ts` | EDIT — `SystemSkill` + `SystemSkillListResponse` |
| 3 | `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` | EDIT — `fetchSystemSkills(tenantId)` |
| 4 | `frontend/src/features/tenant-settings/hooks/useTenantSkills.ts` | EDIT — `useSystemSkills(tenantId)` |
| 5 | `frontend/src/features/tenant-settings/components/tabs/SkillsTab.tsx` | EDIT — System Skills read-only section + Preview modal + Preview on tenant rows |
| 6 | `backend/tests/integration/api/test_admin_tenant_skills.py` | EDIT — system endpoint cases (3 skills / has_script / overridden / 403 / 404) — Glob basename Day-0 |
| 7 | `frontend/src/features/tenant-settings/components/tabs/SkillsTab.test.tsx` | EDIT — system section + has-script badge + shadowed tag + Preview modal cases — Glob basename Day-0 |
| 8 | `claudedocs/4-changes/feature-changes/CHANGE-086-skills-system-visibility.md` | NEW — change record (incl. the drive-through) |
| — | `agent_harness/skills/registry.py` / `loop.py` / `events.py` / `sse.py` / `event_wire_schema` / codegen / migration / a new table / a design note | **UNTOUCHED / NONE** |

## 5. Acceptance Criteria

1. `GET /admin/tenants/{tenant_id}/skills/system` (admin-gated, 404 on a bad tenant) returns `SystemSkillListResponse` listing the bundled skills with `name`/`description`/`instructions`/`has_script`/`overridden`; `digest.has_script is True`, the text-only skills `False`; `overridden` reflects the tenant's same-name skills.
2. `fetchSystemSkills` + `useSystemSkills` + the `SystemSkill` type fetch it; the read hook mirrors the existing `useTenantSkills` convention.
3. `SkillsTab.tsx` shows a read-only "System Skills" section (name + description + a "🔧 script" badge + a "shadowed by your skill" tag) with NO edit/delete; a Preview button per row.
4. A Preview modal renders any skill's full `instructions` read-only (bundled from the system endpoint; tenant from the existing list); a Preview button is on the tenant rows too.
5. Unit/integration + Vitest cover: the endpoint (3 skills / has_script / overridden / 403 / 404), the section render + badges, the Preview modal.
6. Gates: mypy strict 0 · run_all 10/10 (count 24, NO codegen change) · full pytest +N (0 del) vs 2644 · Vitest +M · mockup-fidelity 51 holds · LLM-neutrality + `check_cross_category_import` green · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.
7. Real drive-through PASS: the admin Skills tab shows the System Skills section (code-review/digest/summarize, digest's script badge) + Preview renders a bundled skill's instructions + a tenant skill's; backend noted; screenshots + observed-vs-intended (the controls are live — real fetch + real render, not fixtures).
8. The `AD-Skills-Authoring-UI` system-skills-visibility leg shipped; NO design note (feature continuation); CHANGE-086; calibration recorded (`skills-admin-readonly-surface` 0.55, 1st data point); versioning + hot-reload + a disable-toggle carried.

## 6. Deliverables

- [ ] US-1 `SystemSkillResponse` + `SystemSkillListResponse` + `GET /{tenant_id}/skills/system` (over `get_default_skill_registry()`, `overridden` from the tenant's skills) + backend test (3 skills / has_script / overridden / 403 / 404)
- [ ] US-2 `SystemSkill` type + `fetchSystemSkills` + `useSystemSkills`
- [ ] US-3 the read-only "System Skills" section in `SkillsTab.tsx` (name/description/has-script badge/shadowed tag/Preview button)
- [ ] US-4 the Preview modal (system + tenant) + Preview on tenant rows
- [ ] US-5 (folded into US-1..US-4) — backend cases + FE Vitest (section render / badge / shadowed / Preview modal)
- [ ] US-6 drive-through PASS (admin tab → System Skills section + Preview render; backend noted; screenshots + observed-vs-intended)
- [ ] CHANGE-086 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates `AD-Skills-Authoring-UI` system-skills-visibility leg shipped + versioning/hot-reload/disable-toggle carried; 17.md N/A — an api read endpoint, no new contract)

## 7. Workload Calibration

- Scope class **`skills-admin-readonly-surface` 0.55** (NEW, 1st data point; pending 2-3 sprint validation). Shape: a full-stack read-only surface — ONE new read-only GET endpoint over the existing bundled registry (no DB / no migration / no CRUD) + a TanStack read hook + a service fn + a read-only admin tab section + a Preview modal. Kin to `config-validation-hardening` 0.55 (57.117 — FE surface + a thin backend addition, no migration) but FE-heavier (a new section + a modal vs a count/disable surface). Lighter than 57.114's `per-tenant-catalog-table-backed` 0.60 (no table / migration / CRUD / RLS — read-only over what exists). If a 2nd read-only-surface sprint diverges > 30% from 0.55, re-point.
- **Agent-delegated: no** (parent-direct; the slice is a bounded FE section + modal over a known tab + a thin read endpoint — small enough to keep parent-direct + a drive-through that must show live render). `agent_factor` 1.0 → §Workload uses the 3-segment form (class multiplier only).
- Bottom-up est ~6.0 hr (`tenants.py` 2 models + endpoint + `overridden` cross-check ~1.0 · backend test ~0.75 · `types.ts` SystemSkill ~0.25 · service `fetchSystemSkills` ~0.25 · hook `useSystemSkills` ~0.25 · `SkillsTab.tsx` System section + badges + Preview modal + tenant Preview ~1.75 · FE Vitest ~0.75 · drive-through ~0.75 · CHANGE-086 + closeout ~1.0) → class-calibrated commit ~3.3 hr (mult 0.55). Day-4 retro Q2 verifies (1st `skills-admin-readonly-surface` data point; if ratio diverges > 30% note for the matrix).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| A tenant-scoped path (`/{tenant_id}/skills/system`) returning system-GLOBAL data reads oddly | the tenant_id IS meaningful — `overridden` is computed against THIS tenant's skills (the response is "the base set available to this tenant + which it has shadowed"); the framing + the docstring make it clear; mirrors the sibling `/{tenant_id}/skills` auth + 404 |
| Putting full `instructions` in the LIST response is heavy | only ~3 bundled skills (tiny); avoids a 2nd preview endpoint; the tenant list ALREADY returns `instructions` (`SkillResponse`), so this is symmetric |
| No `Modal`/`Dialog` primitive in mockup-ui → a new dependency | Day-0 check mockup-ui; if none, an inline fixed-overlay panel mirroring the existing inline-form `var(--border)`/`var(--radius)`/`var(--shadow)` idiom (the 57.115 `SkillSlashMenu` precedent for a greenfield FE overlay) — NO new dep |
| The `overridden` cross-check needs the tenant's skills (a 2nd DB read) | `tenant_skill_service.list_skills` is already called by the sibling GET — reuse it (one read, names only); read-only, no audit, fail-open is N/A (admin endpoint, a tenant load 404s) |
| `check_cross_category_import` flags the api layer importing the Cat-5 registry | the chat path ALREADY imports `get_default_skill_registry` into the api/router layer (57.113+) — same precedent; confirm Day-0 the lint is green |
| Risk Class E — a stale `--reload` backend serves OLD code / no `/skills/system` at the drive-through | clean no-reload restart from repo-root + `Win32_Process` PID/PPID/StartTime orphan sweep + a startup probe (the 57.118 routine) before driving |
| The FE Vitest baseline (873) may differ at HEAD `cf83b274` | Day-0 re-run Vitest to capture the real baseline before adding tests (the +M is relative to it) |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Skill versioning + version history** (a `version` column + a history table + a rollback UI — a separate `AD-Skills-Authoring-UI` leg; deferred per the AskUserQuestion).
- **Bundled-registry hot-reload** (an admin reload action without a backend restart — bundled skills are git-deployed, low prod value; a separate leg).
- **Editing / disabling / creating bundled skills from the UI** (bundled = redeploy; a per-tenant disable-toggle for a bundled skill is a larger governance slice).
- **Displaying / editing the script SOURCE** (57.118's tenant-script deferral holds — `has_script` is a boolean badge; the source is code, not shown).
- Any wire / codegen / SSE / migration / new-table / new-DB-column change (count 24 unchanged).
- `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) / `AD-Skills-SlashMenu-Mockup` (57.121 — needs a mockup authored first) — the remaining Skills-epic items, executed in sequence.
