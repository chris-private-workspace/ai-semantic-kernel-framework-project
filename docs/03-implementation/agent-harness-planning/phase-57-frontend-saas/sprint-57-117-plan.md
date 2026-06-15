# Sprint 57.117 Plan — Skills Per-Tenant Quota + Instructions Body-Size Limit: Sprint 57.114 shipped the per-tenant Skills catalog (`tenant_skills` table + admin CRUD tab), but a tenant can create UNBOUNDED skills and each `instructions` body is `Text` with only `min_length=1` — no upper bound on count or size. This slice hardens the write path: a per-tenant skill-count quota (enforced in `TenantSkillService.create` → a typed `SkillQuotaExceededError` 409, which the admin POST endpoint already maps to HTTP) + an `instructions` body-size cap (a `max_length` on the `SkillCreate/UpdateRequest` Pydantic field → 422 at the API boundary), both backed by env-overridable module constants (the 57.109 `CHAT_COMPACTION_*` knob precedent). The `SkillListResponse` surfaces the effective limits (`max_skills` + `max_instructions_chars`) so the admin "Skills" tab shows "N / max", disables Add at the limit, caps the textarea, and renders the quota / size errors — a server-sourced limit, NOT a magic FE constant. Closes `AD-Skills-Per-Tenant-Quota`; the multi-worker shared cache-invalidation signal (a cross-cutting concern shared with `_ModelPolicyCache` + the harness-policy cache) and a per-tenant-CONFIGURABLE quota stay deferred.

**Status**: Approved-to-execute (user selected 2026-06-15: "把 skills 的 5 個 pending 順序執行"; this is item 1 of 5 — the lowest-risk backend-hardening warmup on the 57.114 table)
**Branch**: `feature/sprint-57-117-skills-per-tenant-quota`
**Base**: `main` HEAD `1cf58e22` (post-#291 merge — Sprint 57.116 skills inspector affordance)
**Slice**: Skills System epic — **catalog hardening** (closes `AD-Skills-Per-Tenant-Quota`). 57.113 model-invoked lazy-load / 57.114 per-tenant overlay (the table this hardens) / 57.115 `/skill-name` force-load / 57.116 user-turn chip. Per the rolling-planning discipline (CLAUDE.md §"也不是再寫一批新規劃文件"): a **feature continuation** of the validated 57.114 per-tenant catalog + the validated env-knob + typed-error patterns — NOT a new pattern / spike → **no design note** (sprint-workflow §5.5 → design note is spike-only; mirrors 57.116's feature-continuation cadence; only CHANGE-084 + retrospective).
**Scope decisions** (per user "順序執行" + thin-vertical discipline): (a) **Count quota = a global default enforced per-tenant** (`SKILLS_MAX_PER_TENANT`, default 50, env-overridable) — NOT a per-tenant-configurable limit (the `meta_data` override pattern from 57.56 Quotas can add per-tenant configurability later if a real need appears; YAGNI now). (b) **Body-size = a `max_length` on the Pydantic request field** (`SKILLS_MAX_INSTRUCTIONS_CHARS`, default 20_000, env-overridable) — the idiomatic FastAPI 422 boundary; the DB column stays `Text` (NO migration). (c) **The `SkillListResponse` surfaces the effective limits** (`max_skills` + `max_instructions_chars`) so the FE is single-source against the server, not a hardcoded mirror constant (the honest, drive-through-able shape). (d) **Multi-worker cache-invalidation DEFERRED** — `_SkillRegistryCache` is in-process per worker (admin mutation on worker A leaves worker B stale up to the 60 s TTL); this is shared with `_ModelPolicyCache` + the harness-policy cache → a cross-cutting infra slice (`AD-Config-Cache-MultiWorker-Invalidation`), YAGNI under single-worker deploy. (e) **No new wire / codegen / migration** — pure write-path validation + a list-response field + the FE surface.

---

## 0. Background

Sprint 57.114 closed `AD-Skills-Per-Tenant-Catalog`: a tenant authors custom skills (name + description + a full `instructions` body) via the tenant-settings "Skills" admin tab; each row is a `TenantSkill` (`tenant_skills` table, RLS, `unique (tenant_id, name)`); `resolve_tenant_skill_registry` overlays them on the bundled set per chat request (`SkillRegistry.with_overlay`, TTL-cached, fail-open). The CRUD is real and drive-through-proven — but it has **no upper bounds**: a tenant can create any number of skills, and `instructions` is a `Text` column with only `min_length=1` (`SkillCreateRequest.instructions = Field(min_length=1)` — no `max_length`). An unbounded per-tenant skill count or a multi-megabyte instruction body is a resource / abuse risk (the registry overlay loads every row + injects the bundled `## Available Skills` block from them) and a missing enterprise-SaaS guardrail.

`AD-Skills-Per-Tenant-Quota` (logged 57.114) asks for: a per-tenant skill-count quota + an `instructions` body-size limit + a multi-worker shared cache-invalidation signal. This slice closes the first two (the write-path guardrails) and explicitly defers the third (a cross-cutting cache-coherency concern, not skills-specific).

### Design decision (env-overridable module constants → a service-layer count guard (`SkillQuotaExceededError` 409) + a Pydantic-field `max_length` body-size guard (422) → a `SkillListResponse` that surfaces the effective limits → an admin "Skills" tab that shows "N / max", disables Add at the limit, caps the textarea, and renders the errors; a real admin drive-through)

- **US-1 is "the count quota"** (backend, service layer): `TenantSkillService.create` counts the tenant's existing skills before INSERT; at/over `SKILLS_MAX_PER_TENANT` it raises a NEW `SkillQuotaExceededError(TenantSkillError, status_code=409)`. The admin POST endpoint already maps `except TenantSkillError as err: raise HTTPException(err.status_code, err.detail)` (`tenants.py:1956`) → the new error auto-maps to a clean 409 with a safe detail; NO endpoint change for the error path. The limit is a module constant `SKILLS_MAX_PER_TENANT = int(os.environ.get("SKILLS_MAX_PER_TENANT", 50))` (the 57.109 env-knob precedent; non-int / non-positive → default).
- **US-2 is "the body-size limit"** (backend, request layer): `SkillCreateRequest.instructions` + `SkillUpdateRequest.instructions` gain `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` (default 20_000, env-overridable, imported from the service module). FastAPI returns a standard 422 when the body exceeds the cap — the idiomatic API-boundary guard. The DB column stays `Text` (NO migration); the service create/update is only ever called from the validated endpoint, so no service-layer body-size double-guard (YAGNI).
- **US-3 is "the list response surfaces the limits"** (backend): `SkillListResponse` gains `max_skills: int` + `max_instructions_chars: int`; the GET `/{tenant_id}/skills` handler populates them from the constants. This makes the FE single-source against the server (the tab shows the real effective limit, disables Add at it, caps the textarea from it) — NOT a hardcoded FE mirror that would drift from an env override (AP-4 honesty).
- **US-4 is "the FE surface"**: `useTenantSkills` reads `max_skills` + `max_instructions_chars` from the list response; `SkillsTab` shows a "N / max skills" count, disables the Add control + shows a "limit reached" hint when `skills.length >= max_skills`, sets the instructions `<textarea maxLength={max_instructions_chars}>` (+ a char counter), and renders the 409 (quota) / 422 (size) errors from the mutation. The skills FE consumes snake_case directly (the 57.114 "no camelCase mapper" decision) → the new fields are `max_skills` / `max_instructions_chars` on the FE type too.
- **US-5 is "tests"**: backend unit (`TenantSkillService.create` raises `SkillQuotaExceededError` at the limit; under the limit it succeeds; the constants read the env) + integration (a POST when the tenant is at the limit → 409; an oversized `instructions` → 422; the GET list response carries `max_skills` + `max_instructions_chars`); FE Vitest (Add disabled + hint when at the limit; the textarea `maxLength`; the quota / size error renders).
- **US-6 is "the drive-through"** (real admin "Skills" tab + real backend, a LOWERED env limit so the cap is reachable): with `SKILLS_MAX_PER_TENANT` set low (e.g. 2), create skills up to the cap → the Add control disables + the "limit reached" hint shows + a forced API POST returns 409; paste an oversized `instructions` (> the lowered char cap) → the create is rejected with the size error. Screenshots + observed-vs-intended in progress.md.
- **Rejected / deferred**: a per-tenant-CONFIGURABLE quota via `tenants.meta_data` (the 57.56 Quotas pattern — deferred; the global default is the thin vertical, configurability is YAGNI now); a multi-worker shared cache-invalidation signal (`AD-Config-Cache-MultiWorker-Invalidation` — cross-cutting, shared with `_ModelPolicyCache` + the harness-policy cache, YAGNI under single-worker); a DB `CHECK`/`VARCHAR` constraint on `instructions` (a migration — the Pydantic `max_length` is the chosen boundary, `Text` stays); a description/name size change (they already have `max_length=512` / `128`); content-policy validation of the body (only size, not content — a separate concern).

### Ground truth (Day-0 head-start — direct greps, file:line on `main` HEAD `1cf58e22`; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**Backend (US-1/US-2/US-3):**
- `platform_layer/skills/service.py`: `TenantSkillError` (`:58`, `status_code` + `detail`), `DuplicateSkillError` (409, `:70`), `SkillNotFoundError` (404, `:75`); `TenantSkillService.create` (`:106-135`, does a pre-INSERT name-existence SELECT then `db.add` + flush). → add a count SELECT + `SkillQuotaExceededError(TenantSkillError, status_code=409)`; add module constants `SKILLS_MAX_PER_TENANT` + `SKILLS_MAX_INSTRUCTIONS_CHARS` (env-read; the `import os` + the 57.109 pattern). Export the new error + constants in `__all__` (`:279`).
- `api/v1/admin/tenants.py`: `SkillCreateRequest` (`:1857`, `instructions = Field(min_length=1)` `:1863` — no max) + `SkillUpdateRequest` (`:1873`, `instructions = Field(default=None, min_length=1)` `:1879`). → add `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` (import the constant). `SkillListResponse` (`:1900-1903`, `skills: list[SkillResponse]`) → add `max_skills: int` + `max_instructions_chars: int`. GET `/{tenant_id}/skills` (`:1917-1926`, returns `SkillListResponse(skills=[_project_skill(...)])`) → populate the two new fields. POST `/{tenant_id}/skills` (`create_skill` `:1936`) maps `TenantSkillError as err → HTTPException(err.status_code, err.detail)` (`:1956`) — the new `SkillQuotaExceededError` auto-maps; NO handler change.
- `.env.example`: documents `CHAT_COMPACTION_TOKEN_BUDGET` (`:85`) / `CHAT_COMPACTION_KEEP_RECENT_TURNS` (`:90`). → add `SKILLS_MAX_PER_TENANT` + `SKILLS_MAX_INSTRUCTIONS_CHARS` (commented, with the defaults).

**Frontend (US-4):**
- `features/tenant-settings/services/tenantSettingsService.ts`: the `SkillListResponse` / skill types (snake_case direct — 57.114 "no camelCase mapper"). → add `max_skills` + `max_instructions_chars` to the list-response type.
- `features/tenant-settings/hooks/useTenantSkills.ts`: the React-Query list hook. → expose the limits (return them alongside `skills`).
- `features/tenant-settings/components/tabs/SkillsTab.tsx`: the list-CRUD tab (Add / Edit / 2-step-Delete; 57.114). → "N / max" count + Add disabled + "limit reached" hint at the cap + `<textarea maxLength>` + char counter + 409 / 422 error render.

**Tests + baselines:**
- Backend: `tests/unit/platform_layer/skills/test_tenant_skill_service.py` (EDIT — quota cases) + `tests/integration/api/test_admin_tenant_skills.py` (EDIT — 409 at limit / 422 oversized / list carries limits). FE: `frontend/tests/unit/tenant-settings/tabs/SkillsTab.test.tsx` (EDIT — disabled-at-limit / error render). Glob each basename before any NEW file (the 57.109 / 57.114 unique-basename lesson) — this sprint EDITs existing test files, no NEW test basenames expected.
- **Baselines (57.116 closeout)**: full pytest **2623+5skip** · wire count **24** · FE Vitest **869** · mockup-fidelity **51** · mypy `src` **0/370** · run_all **10/10** (count 24). Re-verify Day-0.
- **No migration. No wire / codegen change (count 24). No design note** (feature continuation). **CHANGE next free = 084** (083 = inspector affordance).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

The exact `TenantSkillService.create` body + whether a count SELECT can reuse the existing list query or needs a `func.count` · the exact `SkillCreate/UpdateRequest` field defs (so `max_length` lands cleanly + the `Field(default=None, …)` sparse-update shape is preserved) · the exact `SkillListResponse` shape + the GET handler's construction call (so the two new fields are populated, not left defaulted) · whether `import os` is already in `service.py` · the `.env.example` section to append to · the FE `tenantSettingsService.ts` skills types (snake_case confirm) + the `useTenantSkills` return shape + the `SkillsTab` Add-control + the instructions `<textarea>` + the existing error-render path · the `SkillsTab.test.tsx` harness (mock the list hook's new limit fields) · a dev tenant with the Skills tab (reuse the 57.114/57.115 `acme-skills`) + a LOW env limit for the drive-through · baselines re-verify (pytest 2623+5skip / wire 24 / Vitest 869 / mockup 51 / mypy 0/370 / run_all 10/10).

## 1. Sprint Goal

A tenant's Skills catalog gains write-path guardrails: a per-tenant skill-count quota (`SKILLS_MAX_PER_TENANT`, default 50, env-overridable — enforced in `TenantSkillService.create` via a new `SkillQuotaExceededError` 409 that the admin POST endpoint already maps) and an `instructions` body-size cap (`SKILLS_MAX_INSTRUCTIONS_CHARS`, default 20_000, env-overridable — a `max_length` on the `SkillCreate/UpdateRequest` Pydantic field → 422), with the effective limits surfaced on `SkillListResponse` so the admin "Skills" tab shows "N / max", disables Add at the limit, caps the textarea, and renders the quota / size errors — proven by a real admin drive-through (a lowered env limit → Add disables + 409 at the cap; an oversized body → 422). Closes `AD-Skills-Per-Tenant-Quota`; the multi-worker cache-invalidation signal and a per-tenant-configurable quota stay deferred. NO migration / NO wire change (count 24) / NO design note.

## 2. User Stories

- **US-1**: 作為 platform，我希望每個租戶的 skill 數量有上限：`TenantSkillService.create` 在 INSERT 前先數該租戶現有 skill 數，達到/超過 `SKILLS_MAX_PER_TENANT`（module 常數，env 可覆寫，default 50；non-int/非正 → default）時 raise 新的 `SkillQuotaExceededError(TenantSkillError, status_code=409)`；admin POST 端點既有的 `TenantSkillError → HTTPException(status, detail)` 對映自動把它變成乾淨的 409（端點不改），以便防止無界 skill 累積。
- **US-2**: 作為 platform，我希望 `instructions` body 有大小上限：`SkillCreateRequest` + `SkillUpdateRequest` 的 `instructions` 欄位加 `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS`（module 常數，env 可覆寫，default 20_000），超過時 FastAPI 回標準 422（API 邊界守門）；DB 欄位維持 `Text`（無 migration），以便擋住多 MB 的指令 body。
- **US-3**: 作為 frontend，我希望 `SkillListResponse` 帶出有效上限：加 `max_skills: int` + `max_instructions_chars: int`，GET `/{tenant_id}/skills` handler 從常數填值，以便前端對「伺服器真實上限」single-source（不寫死、不會與 env 覆寫漂移）。
- **US-4**: 作為租戶 admin，我希望「Skills」tab 反映上限：`useTenantSkills` 取回 `max_skills`/`max_instructions_chars`；`SkillsTab` 顯示「N / max skills」、達上限時禁用 Add 並顯示「limit reached」提示、`instructions` textarea 套 `maxLength` + 字數計數、並渲染 409（quota）/ 422（size）錯誤，以便我清楚知道剩多少額度、為何被擋。
- **US-5**: 作為 platform，我希望單元 + 整合測試守住：backend（`create` 在達上限時 raise `SkillQuotaExceededError`、未達則成功、常數讀 env；POST 達上限 → 409、oversized `instructions` → 422、GET list 帶 `max_skills`+`max_instructions_chars`）；FE Vitest（達上限時 Add 禁用 + 提示、textarea `maxLength`、quota/size 錯誤渲染），以便回歸受保護。
- **US-6**: 作為 reviewer，我希望一個真 drive-through（真 admin「Skills」tab + 真後端，env 上限調低以便可達）證明：（A）建 skill 到上限 → Add 禁用 + 「limit reached」提示 + 強制 API POST 回 409；（B）貼超過字元上限的 `instructions` → 建立被擋 + size 錯誤訊息。截圖 + observed-vs-intended 記入 progress.md（證明 quota/size 真的擋住，非裝飾）。

## 3. Technical Specifications

### 3.0 Architecture (env-overridable module constants in `service.py` → a `create`-time count guard (`SkillQuotaExceededError` 409, auto-mapped by the existing endpoint) + a Pydantic-field `max_length` body-size guard (422) → `SkillListResponse` += `max_skills`/`max_instructions_chars` → an admin "Skills" tab surface; NO migration / NO wire / NO codegen / NO new SSE event / NO design note)

```
platform_layer/skills/service.py (EDIT): + SKILLS_MAX_PER_TENANT / SKILLS_MAX_INSTRUCTIONS_CHARS env constants + SkillQuotaExceededError(409) + count guard in create()
api/v1/admin/tenants.py (EDIT): SkillCreate/UpdateRequest.instructions += max_length=SKILLS_MAX_INSTRUCTIONS_CHARS; SkillListResponse += max_skills/max_instructions_chars; GET list populates them
.env.example (EDIT): document SKILLS_MAX_PER_TENANT (50) + SKILLS_MAX_INSTRUCTIONS_CHARS (20000)
frontend tenant-settings: tenantSettingsService.ts (list type += limits) + useTenantSkills.ts (expose limits) + SkillsTab.tsx (N/max + disable Add + textarea maxLength + error render)
loop.py / events.py / sse.py / event_wire_schema / codegen / migration / a new table / a design note: UNTOUCHED / NONE
```

### 3.1 Count quota — `SkillQuotaExceededError` + the `create` guard (US-1)

- **`service.py`** constants (module level, after the imports): `import os` (if absent); `SKILLS_MAX_PER_TENANT = _env_int("SKILLS_MAX_PER_TENANT", 50)` + `SKILLS_MAX_INSTRUCTIONS_CHARS = _env_int("SKILLS_MAX_INSTRUCTIONS_CHARS", 20_000)` with a tiny `_env_int(name, default)` helper (the 57.109 pattern: `try: v = int(os.environ.get(name, default)); return v if v > 0 else default; except ValueError: return default`). A WHY comment (env-overridable per-deploy; the 57.109 `CHAT_COMPACTION_*` precedent).
- **`SkillQuotaExceededError(TenantSkillError)`**: `status_code = 409`, `detail = "skill quota reached for this tenant"`. Placed alongside `DuplicateSkillError` / `SkillNotFoundError`.
- **`TenantSkillService.create`**: before the duplicate-name SELECT (or after — order is cosmetic), add a count of the tenant's rows (`select(func.count()).select_from(TenantSkill).where(TenantSkill.tenant_id == tenant_id)` under the same `_set_tenant` RLS context) and, if `count >= SKILLS_MAX_PER_TENANT`, raise `SkillQuotaExceededError()`. The duplicate check still runs (a duplicate name is a distinct 409 detail). The endpoint's existing `except TenantSkillError` maps it.

### 3.2 Body-size limit — Pydantic `max_length` (US-2)

- **`tenants.py`** `SkillCreateRequest.instructions`: `Field(min_length=1, max_length=SKILLS_MAX_INSTRUCTIONS_CHARS)`; `SkillUpdateRequest.instructions`: `Field(default=None, min_length=1, max_length=SKILLS_MAX_INSTRUCTIONS_CHARS)`. Import `SKILLS_MAX_INSTRUCTIONS_CHARS` from `platform_layer.skills` (add to the existing skills import block). FastAPI emits a 422 when exceeded (the standard validation envelope). The constant is read at import (env override honored at process start — Risk Class E: the backend restarts on an env change, same as the compaction knob).

### 3.3 List response surfaces the limits (US-3)

- **`tenants.py`** `SkillListResponse`: add `max_skills: int` + `max_instructions_chars: int`. The GET `/{tenant_id}/skills` handler constructs `SkillListResponse(skills=[...], max_skills=SKILLS_MAX_PER_TENANT, max_instructions_chars=SKILLS_MAX_INSTRUCTIONS_CHARS)`. Import `SKILLS_MAX_PER_TENANT` too. This is the single-source the FE reads (so a low env override is visible in the tab without an FE redeploy — the drive-through relies on it).

### 3.4 FE surface — `SkillsTab` quota / size affordances (US-4)

- **`tenantSettingsService.ts`**: the skills list-response type gains `max_skills: number` + `max_instructions_chars: number` (snake_case — 57.114 no-mapper decision).
- **`useTenantSkills.ts`**: return `maxSkills` / `maxInstructionsChars` (or the snake_case fields directly) alongside `skills` (read from the list response; sensible fallbacks if absent so the tab never crashes — e.g. `Infinity` / a large default → never falsely disables).
- **`SkillsTab.tsx`**: (a) a "N / max skills" count near the header; (b) the Add control `disabled` + a "limit reached" hint when `skills.length >= max_skills`; (c) the `instructions` `<textarea maxLength={max_instructions_chars}>` + a `{value.length} / {max}` char counter; (d) render the mutation error — a 409 → "Skill quota reached" / a 422 → "Instructions too long" (map from the error status / detail; reuse the tab's existing error-display path). Inline English copy (the codebase convention — the 57.73 lesson).

### 3.5 Drive-through (US-6) — real admin "Skills" tab + real backend (lowered env limit)

The "Skills" tab needs no mockup change (the count / hint / counter are net-new conditional affordances on the existing tab). The drive-through:
1. Real UI :3007 + a fresh single-process no-reload backend (Risk Class E clean restart + `Win32_Process` PID/PPID/StartTime orphan sweep + a startup probe) with `SKILLS_MAX_PER_TENANT=2` + `SKILLS_MAX_INSTRUCTIONS_CHARS=200` set BEFORE start (so the caps are reachable). Reuse the 57.114/57.115 dev tenant `acme-skills` (a tenant-admin session).
2. **Leg A (count quota)**: in the Skills tab, create skills until the tenant has 2 → the Add control disables + a "limit reached" hint shows + the "N / max" reads "2 / 2"; a forced API `POST /{tid}/skills` (curl, same cookie) returns **409**. Screenshot the disabled Add + the count.
3. **Leg B (body-size)**: attempt to create a skill with `instructions` > 200 chars → the create is rejected (the textarea caps typing at 200, and a forced over-cap API POST returns **422**). Screenshot the counter + the rejected create.
4. Screenshots (Add disabled at the cap / the 409 / the size rejection) + observed-vs-intended in progress.md. Verify the guardrails actually BLOCK (Drive-Through-Acceptance — not a dead/decorative control: the 409 + 422 are real server rejections, the Add disable is driven by the server-sourced `max_skills`).

### 3.6 What is explicitly NOT done

A per-tenant-CONFIGURABLE quota (the global default is the thin vertical; `tenants.meta_data` configurability is a separate slice); a multi-worker shared cache-invalidation signal (`AD-Config-Cache-MultiWorker-Invalidation` — cross-cutting with `_ModelPolicyCache` + the harness-policy cache); a DB `CHECK` / `VARCHAR` constraint on `instructions` (a migration — the Pydantic `max_length` is the boundary, `Text` stays); a name / description size change (already capped 128 / 512); content-policy validation of the body (only size); any wire / codegen / SSE change (count 24 unchanged); a design note (feature continuation).

### 3.7 Validation (US-1..US-6)

Unit (backend, CI-safe): `service.py` — `TenantSkillService.create` raises `SkillQuotaExceededError` when the tenant is at `SKILLS_MAX_PER_TENANT` (monkeypatch the constant low), succeeds under it; `_env_int` honors / falls back on a bad env. Integration (TestClient): a POST when the tenant is at the limit → 409 (the `SkillQuotaExceededError` detail); an `instructions` over `max_length` → 422; a GET list → `data.max_skills` + `data.max_instructions_chars` present + equal to the (test-patched) constants. FE (Vitest): `SkillsTab` — Add disabled + the hint when `skills.length >= max_skills`; the `<textarea maxLength>` set from `max_instructions_chars`; a 409 mutation → the quota error renders; a 422 → the size error renders. Gates: mypy strict 0 · run_all 10/10 (count 24; NO codegen change) · full pytest +N (0 del) vs 2623 · Vitest +M vs 869 · mockup-fidelity 51 holds (no CSS change) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/the codegen artifacts/any migration UNTOUCHED · LLM-neutrality lint green · `check_cross_category_import` green · multi-tenant lint green (the count SELECT is `tenant_id`-scoped under `_set_tenant`).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/platform_layer/skills/service.py` | EDIT — `_env_int` + `SKILLS_MAX_PER_TENANT` / `SKILLS_MAX_INSTRUCTIONS_CHARS` constants + `SkillQuotaExceededError(409)` + the count guard in `create`; `__all__` |
| 2 | `backend/src/api/v1/admin/tenants.py` | EDIT — `SkillCreate/UpdateRequest.instructions` += `max_length`; `SkillListResponse` += `max_skills` / `max_instructions_chars`; GET list populates them; import the constants |
| 3 | `backend/.env.example` (or repo-root `.env.example` per Day-0) | EDIT — document `SKILLS_MAX_PER_TENANT` (50) + `SKILLS_MAX_INSTRUCTIONS_CHARS` (20000) |
| 4 | `backend/tests/unit/platform_layer/skills/test_tenant_skill_service.py` | EDIT — `create` at-limit → `SkillQuotaExceededError`; under-limit ok; `_env_int` env / fallback |
| 5 | `backend/tests/integration/api/test_admin_tenant_skills.py` | EDIT — POST at limit → 409; oversized `instructions` → 422; GET list carries the two limit fields |
| 6 | `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` | EDIT — skills list-response type += `max_skills` / `max_instructions_chars` |
| 7 | `frontend/src/features/tenant-settings/hooks/useTenantSkills.ts` | EDIT — expose the limits alongside `skills` (safe fallbacks) |
| 8 | `frontend/src/features/tenant-settings/components/tabs/SkillsTab.tsx` | EDIT — "N / max" + Add disabled + hint at the cap + `<textarea maxLength>` + counter + 409 / 422 error render |
| 9 | `frontend/tests/unit/tenant-settings/tabs/SkillsTab.test.tsx` | EDIT — disabled-at-limit + hint + error-render cases |
| 10 | `claudedocs/4-changes/feature-changes/CHANGE-084-skills-per-tenant-quota.md` | NEW — change record (incl. the drive-through) |
| — | `loop.py` / `events.py` / `sse.py` / `event_wire_schema` / codegen artifacts / migration / a new table / a design note | **UNTOUCHED / NONE** |

## 5. Acceptance Criteria

1. `TenantSkillService.create` enforces `SKILLS_MAX_PER_TENANT` (default 50, env-overridable): at/over the limit it raises `SkillQuotaExceededError` (409); the admin POST endpoint maps it to a clean 409 with no handler change; under the limit, create still works (and a duplicate name is still its own 409).
2. `SkillCreate/UpdateRequest.instructions` carries `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` (default 20_000, env-overridable) → an oversized body → 422; the DB column stays `Text` (NO migration).
3. `SkillListResponse` carries `max_skills` + `max_instructions_chars`, populated from the constants by the GET list handler (single-source for the FE).
4. The admin "Skills" tab shows "N / max", disables Add + shows a "limit reached" hint at the cap, sets the instructions `<textarea maxLength>` + a counter, and renders the 409 / 422 errors — driven by the server-sourced limits (not a hardcoded FE constant).
5. Unit + integration + Vitest cover: the service count guard (at / under limit) + `_env_int`; the POST 409 at the limit; the 422 oversized body; the list-response limit fields; the FE disabled-at-limit + textarea maxLength + error render.
6. Gates: mypy strict 0 · run_all 10/10 (count 24, NO codegen change) · full pytest +N (0 del) vs 2623 · Vitest +M vs 869 · mockup-fidelity 51 holds · LLM-neutrality + `check_cross_category_import` + multi-tenant lint green.
7. Real drive-through PASS: (A) create to the lowered cap → Add disabled + hint + a forced POST → 409; (B) an oversized `instructions` → 422 + the size error. Screenshots + observed-vs-intended (proves the guardrails block, not decorate).
8. `AD-Skills-Per-Tenant-Quota` closed; CHANGE-084; calibration recorded (`config-validation-hardening` 0.55, 1st data point); the multi-worker cache-invalidation signal carried as `AD-Config-Cache-MultiWorker-Invalidation`; a per-tenant-configurable quota carried; remaining Skills ADs (bundled scripts / authoring UI / Inspector-panel metadata row / slash-menu mockup) carried.

## 6. Deliverables

- [ ] US-1 `SkillQuotaExceededError` (409) + `SKILLS_MAX_PER_TENANT` env constant + the `create` count guard + unit tests (at / under limit, `_env_int`)
- [ ] US-2 `SkillCreate/UpdateRequest.instructions` `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` + integration test (oversized → 422)
- [ ] US-3 `SkillListResponse` += `max_skills` / `max_instructions_chars` + GET populates + integration test (list carries them)
- [ ] US-4 `tenantSettingsService` + `useTenantSkills` + `SkillsTab` (N/max + disable Add + hint + textarea maxLength + counter + 409/422 render) + Vitest
- [ ] US-5 (folded into US-1..US-4 test bullets above)
- [ ] US-6 drive-through PASS (create to cap → Add disabled + 409 · oversized body → 422; screenshots + observed-vs-intended)
- [ ] CHANGE-084 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates `AD-Skills-Per-Tenant-Quota` closed + `AD-Config-Cache-MultiWorker-Invalidation` + per-tenant-configurable-quota + remaining Skills ADs carried; NO design note — feature continuation; 17.md N/A — no new contract)

## 7. Workload Calibration

- Scope class **`config-validation-hardening` 0.55** (NEW, 1st data point; pending 2-3 sprint validation). Shape: add count + size guardrails to an EXISTING per-tenant resource — env-overridable module constants + a service-layer count guard (a typed error the endpoint already maps) + a Pydantic-field `max_length` + a list-response that surfaces the limits + an FE limit-surface (count / disable / counter / error) + a lowered-limit drive-through; NO migration / NO wire / NO codegen / NO new table. Lighter than 57.114's `per-tenant-catalog-table-backed` 0.60 (no table / migration / resolver / overlay — this hardens what 57.114 built); kin to the WRITE-side config family but pure validation. If the 2nd hardening sprint diverges > 30% from the 0.55 baseline, re-point the class.
- **Agent-delegated: no** (parent-direct; ~5.5 hr of small precise edits across known files; the only subtlety is the count-query + the FE limit-surface wiring). `agent_factor` 1.0 → §Workload uses the 3-segment form (class multiplier only).
- Bottom-up est ~5.5 hr (`service.py` constants + error + count guard + unit ~1 · `tenants.py` max_length + list-response fields + GET populate + integration ~1.25 · `.env.example` ~0.1 · FE service/hook/tab limit-surface + Vitest ~1.75 · drive-through ~0.75 · CHANGE-084 + closeout ~0.65) → class-calibrated commit ~3 hr (mult 0.55). Day-4 retro Q2 verifies (1st `config-validation-hardening` data point; if ratio diverges > 30% note for the matrix).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| The count guard races (two concurrent POSTs both pass the count then both INSERT → over the limit) | Acceptable for a soft quota (a 1-2 over-count under a rare concurrent burst is not a correctness hazard); the `unique (tenant_id, name)` still holds; if a hard cap is ever needed, a DB-side trigger / advisory lock is a follow-up — out of scope for a soft guardrail |
| Pydantic `max_length` reads the constant at import → an env override needs a backend restart | Documented (the 57.109 Risk Class E discipline — the backend restarts on an env change); the constant default (20_000) is sane; the drive-through sets the env BEFORE the fresh start |
| The FE hardcodes the limit instead of reading the server value → drifts from an env override | the limits come from `SkillListResponse` (`max_skills` / `max_instructions_chars`); `useTenantSkills` surfaces them; the drive-through (a LOW env limit) proves the tab reflects the server value, not a constant (AP-4 honesty) |
| `func.count` query mis-scoped (counts other tenants' rows) → wrong quota | the count SELECT runs under the same `_set_tenant` RLS context + an explicit `where(TenantSkill.tenant_id == tenant_id)` (mirrors `list_skills`); a multi-tenant unit/integration case asserts isolation |
| A `null`/absent limit in the list response crashes the tab (older cached response shape) | `useTenantSkills` falls back to a large sentinel (never falsely disables) when a limit field is absent; a Vitest case covers the fallback |
| The 422 envelope (Pydantic) vs the 409 envelope (HTTPException detail) differ → the FE error mapping mishandles one | the FE maps by HTTP status (409 → quota copy, 422 → size copy) not by parsing the body; a Vitest case covers each status |
| Risk Class E — a stale `--reload` backend serves the OLD (no-quota) code / the default env at the drive-through | clean no-reload restart from repo-root (`--env-file .env` + the low `SKILLS_MAX_*` + `PYTHONPATH=backend/src`) + `Win32_Process` PID/PPID/StartTime orphan sweep + a startup probe (the 57.109/114/116 routine) before driving |
| Test isolation (Risk Class C) — module-constant patching leaks across tests | patch via `monkeypatch.setattr(service, "SKILLS_MAX_PER_TENANT", N)` (function-scoped, auto-undo) rather than mutating the env mid-suite; the integration test patches the imported constant where it is READ |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- A per-tenant-CONFIGURABLE quota via `tenants.meta_data` (the global default is the thin vertical; the 57.56 Quotas override pattern can add configurability later).
- A multi-worker shared cache-invalidation signal (`AD-Config-Cache-MultiWorker-Invalidation` — cross-cutting with `_ModelPolicyCache` + the harness-policy cache; YAGNI under single-worker deploy).
- A DB `CHECK` / `VARCHAR` constraint on `instructions` (a migration; the Pydantic `max_length` is the chosen boundary, `Text` stays).
- A name / description size change (already capped 128 / 512) or content-policy validation of the body (only size, not content).
- Any wire / codegen / SSE change (count 24 unchanged) or a design note (feature continuation).
- `AD-Skills-Bundled-Scripts` (Sprint 57.118) / `AD-Skills-Authoring-UI` (57.119) / `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) / `AD-Skills-SlashMenu-Mockup` (57.121) — the remaining Skills-epic items, executed in sequence.
