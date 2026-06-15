# Sprint 57.117 — Checklist (Skills Per-Tenant Quota + Instructions Body-Size Limit: a per-tenant skill-count quota (`SKILLS_MAX_PER_TENANT`, env-overridable, enforced in `TenantSkillService.create` → `SkillQuotaExceededError` 409 auto-mapped by the existing admin POST) + an `instructions` body-size cap (`SKILLS_MAX_INSTRUCTIONS_CHARS`, a Pydantic `max_length` → 422) + `SkillListResponse` surfacing the effective limits → an admin "Skills" tab N/max + disable-Add + textarea-cap + 409/422 error render — catalog hardening, closes `AD-Skills-Per-Tenant-Quota`; multi-worker cache-invalidation + per-tenant-configurable quota deferred; NO migration / NO wire / NO design note)

[Plan](./sprint-57-117-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; no Prong-3 schema — no new table / migration) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `1cf58e22`) — catalogued in progress.md ✅
- [x] **Prong 1 — path verify**: all EDIT targets present (57.114 file set); **`.env.example` = repo-root** (where `CHAT_COMPACTION_*` `:85`/`:90` live); CHANGE-084 free; NO new test basenames (all EDITs)
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-service-create**: `create` (`:106-135`) dup-SELECT + `db.add`/flush/refresh confirmed; count guard slots cleanly; `__all__` (`:279`) to extend
  - [x] **D-service-imports** (real, design-confirming): `service.py` has **NO `import os`** (add for env constants) + **NO `func`** in the sqlalchemy import (add for `func.count`)
  - [x] **D-typed-errors**: `TenantSkillError`(`:58`, `status_code:int`+`detail`)/`DuplicateSkillError`(409)/`SkillNotFoundError`(404) → `SkillQuotaExceededError(409)` mirrors
  - [x] **D-request-fields**: `SkillCreateRequest.instructions=Field(min_length=1)` (`:1863`) + `SkillUpdateRequest.instructions=Field(default=None,min_length=1)` (`:1879`) → add `max_length`, keep sparse default
  - [x] **D-list-response**: `SkillListResponse` (`:1900-1903`) + GET (`:1917-1926`) construction → add + populate the two fields
  - [x] **D-endpoint-error-map**: POST `create_skill` `except TenantSkillError → HTTPException(err.status_code, err.detail)` (`:1956`) → new error **auto-maps 409, no handler change**
  - [x] **D-env-example**: append `SKILLS_MAX_*` near the `CHAT_COMPACTION_*` block (repo-root `.env.example`)
  - [x] **D-fe-skills** (exact shapes → Day-2 read-before-edit): FE files exist (57.114); snake_case direct (no mapper) → new fields `max_skills`/`max_instructions_chars`
- [x] **Prong 3 — N/A** (no new table / migration / ORM this sprint)
- [x] **Catalog drift**: 1 real design-confirming (D-service-imports: add `import os` + `func`); 0 scope-invalidating; §3 design holds
- [x] **Go/no-go**: 🟢 GO — design confirmed end-to-end; no scope shift > 20%

### 0.2 Branch ✅
- [x] `git checkout -b feature/sprint-57-117-skills-per-tenant-quota` (from `main` `1cf58e22`)

---

## Day 1 — Backend: count quota + body-size + list-response limits (US-1, US-2, US-3)

### 1.1 Count quota — constants + error + the `create` guard (US-1) ✅
- [x] **`platform_layer/skills/service.py`** (EDIT): added `import os` + `func`; `_env_int(name, default)` helper (57.109 pattern); `SKILLS_MAX_PER_TENANT` (50) + `SKILLS_MAX_INSTRUCTIONS_CHARS` (20_000) constants; `SkillQuotaExceededError(TenantSkillError, 409)`; in `create`, a `func.count` of the tenant's rows under `_set_tenant` + `where(tenant_id==)`, raise when `>= SKILLS_MAX_PER_TENANT`; `__all__` extended; WHY comment + MHist
- [x] **`tests/unit/platform_layer/skills/test_tenant_skill_service.py`** (EDIT +4): `create` at the limit → `SkillQuotaExceededError` (monkeypatch low) · tenant-scoped (B unaffected by A at cap) · `_env_int` valid env / fallback (absent / non-int / non-positive)
  - DoD: ✅ 11 unit pass; guard tenant-scoped; mypy 0

### 1.2 Body-size + list-response limits (US-2, US-3) ✅
- [x] **`api/v1/admin/tenants.py`** (EDIT): imported the 2 constants; `SkillCreate/UpdateRequest.instructions` += `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` (sparse `default=None` kept); `SkillListResponse` += `max_skills`/`max_instructions_chars`; GET populates both; POST docstring + MHist + Last Modified
- [x] **`.env.example`** (EDIT, repo-root): documented `# SKILLS_MAX_PER_TENANT=50` + `# SKILLS_MAX_INSTRUCTIONS_CHARS=20000` (after the `CHAT_COMPACTION_*` block)
- [x] **`platform_layer/skills/__init__.py`** (EDIT — Day-0 surfaced: `tenants.py` imports from the package): re-export the 2 constants + `SkillQuotaExceededError`
- [x] **`tests/integration/api/test_admin_tenant_skills.py`** (EDIT +3): POST at the limit → 409 · `instructions` over `max_length` (default+1 chars; Pydantic field is import-bound) → 422 · GET list → `max_skills` + `max_instructions_chars` == the constants
  - DoD: ✅ 16 integration pass; 409 (quota) + 422 (size) both fire; list carries the limits

### 1.3 Backend gate sweep (US-1..US-3) ✅
- [x] mypy `src` **0/370** · black/isort/flake8 0 (changed files) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen artifacts/migration UNTOUCHED · count SELECT tenant-scoped (multi-tenant)
- [x] targeted skills suites **27 passed** (11 unit + 16 integration). Full pytest + `run_all` 10/10 → run at the Day-2/3 closeout gate (after FE)
  - Verify: ✅ `python -m mypy src` (Success 370) · `python -m pytest tests/unit/platform_layer/skills tests/integration/api/test_admin_tenant_skills.py -q` (27 passed)

---

## Day 2 — Frontend: the Skills-tab quota / size surface + Vitest (US-4, US-5)

### 2.1 Type surfaces the limits (US-4) ✅
- [x] **`features/tenant-settings/types.ts`** (EDIT — Day-2 drift: the skills types live in `types.ts`, NOT `tenantSettingsService.ts` as the plan guessed): `SkillListResponse` += `max_skills?: number` + `max_instructions_chars?: number` (snake_case direct — 57.114; **optional** → tab falls back to `Infinity`, so existing mocks + an older cached response never falsely disable); MHist
- [x] **`useTenantSkills.ts` / `tenantSettingsService.ts`** — **NOT changed** (the hook returns the whole `SkillListResponse` via `useQuery`; `SkillsTab` reads `skills.data?.max_skills` directly — no pass-through wiring needed). Simpler than the plan's 2-file estimate.
  - DoD: ✅ tsc compiles (build green); the limits flow through the existing query

### 2.2 SkillsTab affordances (US-4) ✅
- [x] **`features/tenant-settings/components/tabs/SkillsTab.tsx`** (EDIT): `maxSkills`/`maxInstructionsChars` reads (`?? Infinity` fallback) + `atLimit`; a "N / max skills" count (`skills-count`); Add `disabled={isLoading || atLimit}` + a "Skill limit reached" hint (`skills-limit-hint`) at the cap; the `instructions` `<textarea maxLength>` + a `{len} / {max}` counter (`*-instructions-counter`); the existing inline error banner renders the backend detail (409 quota / 422 size — no custom status mapping needed; honest server message); WHY comment + MHist + Description
- [x] **`tests/unit/tenant-settings/tabs/SkillsTab.test.tsx`** (EDIT +4): "N / max" count · Add disabled + hint at the cap · textarea `maxLength` + counter from `max_instructions_chars` · a quota 409 create error renders inline
  - DoD: ✅ Vitest pass; affordances driven by the server-sourced limits
- [x] **Build-time check** (57.116 lesson): `npm run build` (tsc + vite) ran ✓ after the type change

### 2.3 FE gate sweep (US-5) ✅
- [x] `npm run lint` (NO `--silent`) 0 error (only the pre-existing `TSSatisfiesExpression` plugin noise) · `npm run build` ✓ (tsc + vite, 3.36s) · `npm run test` Vitest **873 (+4 vs 869)** · `npm run check:mockup-fidelity` **51** holds (byte-identical; no new colour literal — `var(--danger)` token)
  - Verify: ✅ `cd frontend && npm run lint && npm run build && npm run test && npm run check:mockup-fidelity`

---

## Day 3 — Drive-through (US-6) — real admin "Skills" tab + fresh backend (lowered env limit; Risk Class E clean restart)

### 3.1 Clean restart + probe ✅
- [x] Killed stale backend PID 38660 (57.116 code) via `Stop-Process`; port 8000 FREE + ZERO remaining python (`Win32_Process` sweep — no `--reload` workers / orphan spawn-workers, sole owner); restarted from **repo-root** `PYTHONPATH=backend/src python -m uvicorn api.main:app --env-file .env --host 0.0.0.0 --port 8000` with `$env:SKILLS_MAX_PER_TENANT=2` + `$env:SKILLS_MAX_INSTRUCTIONS_CHARS=200` set BEFORE start (task `bb4gef2bk`); startup-log "Application startup complete" + all-wired (fresh 57.117 process). dev-login `acme-skills`/jamie (roles user,admin,platform_admin); `GET /{tid}/skills` → **`max_skills==2` + `max_instructions_chars==200`** (the low limits are LIVE), count 1 (release-notes)

### 3.2 Drive-through 2 legs (real admin Skills tab :3007 + real backend + Playwright) ✅
- [x] **Leg A (count quota) PASS**: real Skills tab showed "1 / 2 skills" + Add ENABLED → created a 2nd skill (`deploy-notes`) via the UI → list re-fetched → **"2 / 2 skills" + "Skill limit reached" hint + "+ Add skill" [disabled]**; a forced API `POST /{tid}/skills` (browser cookie, at 2/2) → **409 "skill quota reached for this tenant"**. `artifacts/sprint-57-117-skills-1of2-add-enabled.png` + `...-legA-2of2-add-disabled-hint.png`
- [x] **Leg B (body-size) PASS**: typed a 254-char string into the instructions textarea → the browser **capped it at 200** (`value.length==200`, `maxLength==200`, counter **"200 / 200"**); a forced API POST with 201-char instructions → **422 "String should have at most 200 characters"**. `artifacts/sprint-57-117-skills-legB-textarea-capped-200.png`
- [x] Each control driven (real backend, no fixture): the Add disable is from the server `max_skills=2`; the textarea cap from `max_instructions_chars=200`; the 409 + 422 are real server rejections (Drive-Through-Acceptance — the guardrails BLOCK, not decorate). Cleanup: `deploy-notes` deleted (204) → acme-skills back to 1 skill
  - DoD: ✅ BOTH legs PASS + the limits are server-sourced (proven via the low env override visible in the UI)

---

## Day 4 — CHANGE-084 + closeout (NO design note — feature continuation)

### 4.1 CHANGE-084 ✅
- [x] **`claudedocs/4-changes/feature-changes/CHANGE-084-skills-per-tenant-quota.md`** (1-page, incl. the 2-leg drive-through)
- [x] (NO design note — feature continuation of the 57.114 catalog + the 57.109 env-knob + the typed-error patterns; sprint-workflow §5.5 → design note is spike-only)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`config-validation-hardening` 0.55 1st data point; ratio ~0.95-1.0 IN band → KEEP) + progress.md final
- [x] Final gate sweep: mypy 0/370 · run_all 10/10 (count 24) · full pytest **2630 passed, 5 skipped** (+7, 0 del) vs 2623 · Vitest 873 (+4) · mockup 51 holds
- [x] Navigators: CLAUDE.md Current-Sprint row + Last-Updated (minimal touch); MEMORY.md quality pointer + memory subfile `project_phase57_117_skills_per_tenant_quota.md`; next-phase-candidates — `AD-Skills-Per-Tenant-Quota` CLOSED + 57.117 carryover block (+ `AD-Config-Cache-MultiWorker-Invalidation` NEW + per-tenant-configurable-quota deferred) + remaining Skills ADs (118 bundled-scripts / 119 authoring-UI / 120 inspector-metadata / 121 slash-menu-mockup) carried; sprint-workflow matrix `config-validation-hardening` 0.55 1st-point add; 17.md — N/A (no new contract)
- [x] **Anti-pattern self-check** (retro Q5/Q7): AP-4 (drive-through proves the guardrails block — Add disabled from the server limit, real 409/422) · AP-2 (quota → create guard → endpoint map; size → request → 422; main flow) · AP-3 (quota/size in platform_layer.skills + api admin; FE in tenant-settings) · AP-6 (no speculative per-tenant-config / no multi-worker cache build) — **0 violations**
- [ ] PR (push + open on user authorization); CI → merge on green (gh-verified)
