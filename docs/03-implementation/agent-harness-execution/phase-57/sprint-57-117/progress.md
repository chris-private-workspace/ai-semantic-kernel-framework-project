# Sprint 57.117 Progress — Skills Per-Tenant Quota + Instructions Body-Size Limit

**Branch**: `feature/sprint-57-117-skills-per-tenant-quota` (from `main` `1cf58e22`)
**Plan**: [`sprint-57-117-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-117-plan.md) · **Checklist**: [`sprint-57-117-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-117-checklist.md)
**Slice**: Skills System epic — catalog hardening (item 1 of 5 in the "順序執行" sequence; closes `AD-Skills-Per-Tenant-Quota`)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — 2026-06-15

### Prong 1 — path verify (against `main` HEAD `1cf58e22`)
- ✅ EDIT targets present: `platform_layer/skills/service.py` · `api/v1/admin/tenants.py` · `tests/unit/platform_layer/skills/test_tenant_skill_service.py` · `tests/integration/api/test_admin_tenant_skills.py` · `tenantSettingsService.ts` · `useTenantSkills.ts` · `SkillsTab.tsx` · `SkillsTab.test.tsx` (all in the 57.114 file set).
- ✅ **`.env.example` path = repo-root** (`./.env.example`, where `CHAT_COMPACTION_TOKEN_BUDGET` `:85` / `CHAT_COMPACTION_KEEP_RECENT_TURNS` `:90` already live). The `reference/**` + `archived/**` `.env.example`s are NOT ours.
- ✅ NEW: `CHANGE-084` free (083 = inspector affordance). NO new test basenames (all EDITs) → no unique-basename collision risk (57.109/114 lesson N/A this sprint).

### Prong 2 — content verify (drift findings)
- **D-service-imports** 🟢 (real, design-confirming): `service.py` imports `time, datetime, typing.Callable, uuid.UUID, sqlalchemy(select, text, delete as sa_delete), AsyncSession` — **NO `import os`** (add for the env constants) + **NO `func`** in the sqlalchemy import (add for the `func.count` quota query). Not a design change — just two import additions.
- **D-typed-errors** 🟢: `TenantSkillError` (`:58`, `status_code:int=400` + `detail:str`) / `DuplicateSkillError` (409, `:70`) / `SkillNotFoundError` (404, `:75`) confirmed → `SkillQuotaExceededError(TenantSkillError)` with `status_code=409` mirrors cleanly.
- **D-service-create** 🟢: `create` (`:106-135`) does a pre-INSERT duplicate-name SELECT then `db.add`+`flush`+`refresh` under `_set_tenant`; the count guard slots before/after the dup check (cosmetic order); `__all__` (`:279`) to extend with `SkillQuotaExceededError` + the 2 constants.
- **D-request-fields** 🟢: `SkillCreateRequest.instructions = Field(min_length=1)` (`:1863`) + `SkillUpdateRequest.instructions = Field(default=None, min_length=1)` (`:1879`) — no `max_length` today → add `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` (keep the sparse `default=None`).
- **D-list-response** 🟢: `SkillListResponse` (`:1900-1903`, `skills: list[SkillResponse]`) + GET `/{tenant_id}/skills` (`:1917-1926`, returns `SkillListResponse(skills=[_project_skill(...) for ...])`) → add `max_skills`/`max_instructions_chars` to the model + populate in the GET construction.
- **D-endpoint-error-map** 🟢: POST `create_skill` (`:1936`) maps `except TenantSkillError as err: raise HTTPException(err.status_code, err.detail)` (`:1956`) → the new `SkillQuotaExceededError` **auto-maps to 409, NO handler change** (confirms the §3.1 design).
- **D-fe-skills** 🟢 (deferred to Day-2 read-before-edit): `tenantSettingsService.ts` / `useTenantSkills.ts` / `SkillsTab.tsx` exist (57.114); per the 57.114 memory pointer the skills FE consumes snake_case directly (no camelCase mapper) → the new fields are `max_skills`/`max_instructions_chars` on the FE type. Exact Add-control + textarea + error-display shapes read at Day-2 edit time.

### Prong 3 — N/A (no new table / migration / ORM)

### Catalog — drift summary
- 1 real (design-confirming, not scope-shifting): **D-service-imports** (`import os` + `func` absent → add). 0 scope-invalidating drifts; the §3 design holds in full.
- Baselines to re-verify at Day-1/2 gate: pytest 2623+5skip · Vitest 869 · mockup 51 · mypy 0/370 · run_all 10/10 (count 24).

### Go/no-go: 🟢 **GO** — design confirmed end-to-end (the count guard auto-maps via the existing endpoint; the body-size is a Pydantic `max_length`; the FE is single-source via `SkillListResponse`); no scope shift > 20%.

### Branch
- ✅ `git checkout -b feature/sprint-57-117-skills-per-tenant-quota` (from `main` `1cf58e22`).

---

## Day 1 — Backend: count quota + body-size + list-response limits — 2026-06-15

**US-1 count quota** (`platform_layer/skills/service.py`): `import os` + `func` added (Day-0 D-service-imports); `_env_int` helper (57.109 pattern); `SKILLS_MAX_PER_TENANT` (50) + `SKILLS_MAX_INSTRUCTIONS_CHARS` (20_000) env constants; `SkillQuotaExceededError(TenantSkillError, 409)`; `create` does a tenant-scoped `func.count` under `_set_tenant` → raises at/over the cap (the dup-name check still runs separately). `__all__` extended.

**US-2 body-size** (`api/v1/admin/tenants.py`): `SkillCreate/UpdateRequest.instructions` += `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` (the sparse `default=None` kept; wrapped for E501). The Pydantic field is import-bound (env override needs a restart — Risk Class E, documented).

**US-3 list limits** (`tenants.py`): `SkillListResponse` += `max_skills` + `max_instructions_chars`; GET `/{tenant_id}/skills` populates both from the constants (single-source for the FE). POST docstring updated (409 quota / 422 size). MHist + Last Modified bumped (57.114-116 had left the header stale — only my entry added, no retroactive patch).

**Day-0 surfaced edit**: `platform_layer/skills/__init__.py` re-exports the 2 constants + `SkillQuotaExceededError` (tenants.py imports from the package, not the module).

**`.env.example`** (repo-root): documented both knobs after the `CHAT_COMPACTION_*` block.

**Tests**: unit +4 (`test_tenant_skill_service.py` — quota-exceeded / tenant-scoped / `_env_int` valid+fallback); integration +3 (`test_admin_tenant_skills.py` — 409 over quota via monkeypatch / 422 oversized via default+1 chars / GET list carries the limits).

**Gate**: mypy `src` **Success 0/370** · black/isort/flake8 0 (changed files) · targeted suites **27 passed** (11 unit + 16 integration, real Postgres healthy). Full pytest + `run_all` 10/10 deferred to the Day-2/3 closeout gate (after FE). `loop.py`/`events.py`/`sse.py`/wire/codegen/migration UNTOUCHED (count 24).

**Commit**: `feat(skills, sprint-57-117): per-tenant quota + instructions body-size + list-response limits` (Day-1 backend).

## Day 2 — Frontend: the Skills-tab quota / size surface + Vitest — 2026-06-15

**Day-2 drift correction** (read-before-edit): the skills TS types live in `features/tenant-settings/types.ts`, NOT `tenantSettingsService.ts` (the plan's guess). And `useTenantSkills` returns the whole `SkillListResponse` via `useQuery` → `SkillsTab` reads `skills.data?.max_skills` directly, so **the hook + service needed NO change** (simpler than the plan's 2-file estimate — 1 type file + 1 component).

**US-4 type** (`types.ts`): `SkillListResponse` += `max_skills?` + `max_instructions_chars?` — **optional** so existing Vitest mocks (`{ skills: [...] }`) still compile AND an older/cached response never crashes; the tab falls back to `Infinity` (no cap).

**US-4 component** (`SkillsTab.tsx`): `maxSkills`/`maxInstructionsChars` (`?? Infinity`) + `atLimit = items.length >= maxSkills`; a "N / max skills" count; Add `disabled={isLoading || atLimit}` + a "Skill limit reached" hint at the cap; the `instructions` `<textarea maxLength>` + a `{len} / {max}` counter. The **existing inline error banner** already renders the mutation error message → a 409 quota / 422 size shows the backend detail verbatim (no custom status→copy mapping; honest server message, AP-4-safe).

**Tests** (`SkillsTab.test.tsx` +4): N/max count · Add disabled + hint at the cap · textarea `maxLength` + counter · a quota 409 create error renders inline.

**Gate**: `npm run lint` 0 error (only pre-existing `TSSatisfiesExpression` plugin noise) · `npm run build` ✓ tsc + vite (3.36s — the optional-field type change compiles) · `npm run test` Vitest **873 (+4 vs 869)** · `npm run check:mockup-fidelity` **51** holds (byte-identical, no new colour literal — `var(--danger)` token). No mockup CSS change.

**Commit**: `feat(skills, sprint-57-117): chat — Skills tab quota/size affordances (Day-2 FE)`.

## Day 3 — Drive-through (real admin Skills tab + fresh backend, lowered env limits) — 2026-06-15

**Clean restart (Risk Class E)**: killed stale backend PID 38660 (57.116 code) → port 8000 FREE + 0 remaining python (`Win32_Process` sweep, no `--reload`/spawn-worker orphans); restarted from repo-root with `$env:SKILLS_MAX_PER_TENANT=2` + `$env:SKILLS_MAX_INSTRUCTIONS_CHARS=200` (task `bb4gef2bk`) → startup complete + all-wired (fresh 57.117 process). Vite :3007 (PID 31616) left running.

**Session**: dev-login `acme-skills`/jamie via a browser `fetch('/api/v1/auth/dev-login...')` (Vite proxy → cookie); `/auth/me` 200, roles `user,admin,platform_admin`. API pre-probe `GET /{tid}/skills` → **`max_skills=2`, `max_instructions_chars=200`** (the LOW env override is live), 1 existing skill (release-notes).

**Drive (Playwright, real :3007 + real backend):** navigated `/tenant-settings` → tenant = acme-skills → clicked the **Skills** tab.

- **Leg A (count quota) PASS** — the tab rendered **"1 / 2 skills"** + Add ENABLED (server `max_skills=2`); created a 2nd skill (`deploy-notes`) via the real Add form → the list re-fetched → **"2 / 2 skills" + "Skill limit reached" hint + "+ Add skill" [disabled]**. A forced API `POST /{tid}/skills` at 2/2 (browser cookie) → **409 "skill quota reached for this tenant"**. Screenshots: `artifacts/sprint-57-117-skills-1of2-add-enabled.png` (start) + `...-legA-2of2-add-disabled-hint.png` (at cap).
- **Leg B (body-size) PASS** — opened the Add form (counter **"0 / 200"**); typed a **254-char** string into the instructions textarea → the browser **capped the value at 200** (`value.length==200`, `maxLength==200`, counter **"200 / 200"**). A forced API POST with **201-char** instructions → **422 "String should have at most 200 characters"** (Pydantic `max_length`). Screenshot: `artifacts/sprint-57-117-skills-legB-textarea-capped-200.png`.

**Observed vs intended**: matched exactly — the count, the disable-at-cap + hint, and the textarea cap are all driven by the SERVER-sourced limits (the low env override surfaced through `SkillListResponse` into the UI, proving single-source, not a hardcoded FE constant); the 409 + 422 are real server rejections (the guardrails BLOCK, AP-4-safe, not decorative).

**Cleanup**: deleted the drive-through `deploy-notes` skill (204) → acme-skills restored to 1 skill (release-notes). (Backend `bb4gef2bk` still runs with the low cap — to be restarted to defaults at closeout.)

## Day 4 — (pending)
