# CHANGE-084: Skills catalog hardening — per-tenant quota + instructions body-size limit

**Date**: 2026-06-15
**Sprint**: 57.117
**Scope**: platform_layer.skills (Cat 5 service) + chat admin API + tenant-settings frontend
**Closes**: `AD-Skills-Per-Tenant-Quota`

## Problem

Sprint 57.114 shipped the per-tenant Skills catalog (`tenant_skills` table + the admin "Skills" CRUD tab + `resolve_tenant_skill_registry` overlay). But the write path has **no upper bounds**: a tenant can author an unbounded number of skills, and each `instructions` body is a `Text` column with only `min_length=1` — no cap on count or size. The registry overlay loads every row and injects the bundled `## Available Skills` block from them, so an unbounded count or a multi-megabyte instruction body is a resource / abuse risk and a missing enterprise-SaaS guardrail.

## Root Cause

`AD-Skills-Per-Tenant-Quota` (logged 57.114) flagged the gap: the 57.114 CRUD validated name/description sizes (`max_length=128`/`512`) and uniqueness, but never a per-tenant count nor an `instructions` size — the catalog shipped as an unbounded write surface.

## Solution

Env-overridable module constants → a service-layer count guard + a Pydantic-field `max_length` + a list-response that surfaces the effective limits → an admin "Skills" tab surface. **No migration / no wire / no codegen / no new table** (count 24 unchanged).

- **Count quota (US-1)** — `platform_layer/skills/service.py`: a `_env_int(name, default)` helper (the 57.109 `CHAT_COMPACTION_*` env-knob pattern: int-parse / non-positive / `ValueError` → default) reads `SKILLS_MAX_PER_TENANT` (50) + `SKILLS_MAX_INSTRUCTIONS_CHARS` (20_000). A new `SkillQuotaExceededError(TenantSkillError, status_code=409, detail="skill quota reached for this tenant")`. `TenantSkillService.create` does a tenant-scoped `select(func.count()).select_from(TenantSkill).where(TenantSkill.tenant_id == tenant_id)` under the existing `_set_tenant` RLS context and raises at/over the cap (the duplicate-name SELECT still runs as its own distinct 409). `__all__` extended; `platform_layer/skills/__init__.py` re-exports the 2 constants + the new error (the admin endpoint imports from the package).
- **Body-size (US-2)** — `api/v1/admin/tenants.py`: `SkillCreateRequest.instructions` and `SkillUpdateRequest.instructions` gain `max_length=SKILLS_MAX_INSTRUCTIONS_CHARS` (the sparse `default=None` on the update shape preserved). FastAPI emits the standard 422 when exceeded — the idiomatic API-boundary guard. The DB column stays `Text` (no migration). The constant is read at import (an env override needs a backend restart — Risk Class E, documented).
- **List-response limits (US-3)** — `tenants.py`: `SkillListResponse` gains `max_skills: int` + `max_instructions_chars: int`; the GET `/{tenant_id}/skills` handler populates both from the constants. This is the single-source the FE reads, so a low env override is visible in the tab without an FE redeploy (AP-4 honesty — not a hardcoded FE mirror). The admin POST endpoint's existing `except TenantSkillError as err: raise HTTPException(err.status_code, err.detail)` auto-maps the new quota error to a clean 409 — **no handler change**.
- **FE surface (US-4)** — `features/tenant-settings/types.ts`: `SkillListResponse` gains **optional** `max_skills?` + `max_instructions_chars?` (so existing Vitest mocks + an older cached response never crash — the tab falls back to `Infinity`, never falsely disables). `components/tabs/SkillsTab.tsx`: a "N / max skills" count; the Add control `disabled` + a "Skill limit reached" hint at the cap; the `instructions` `<textarea maxLength>` + a `{len} / {max}` counter; the **existing inline error banner** renders the backend detail verbatim (409 quota / 422 size — no custom status→copy mapping; the honest server message). The hook + service were **not** changed — `useTenantSkills` already returns the whole `SkillListResponse` via `useQuery`, so `SkillsTab` reads `skills.data?.max_skills` directly (1 fewer file than the plan's 2-file estimate).

## Verification

- **Unit/integration (+7 backend)**: `test_tenant_skill_service.py` (+4 — `create` at the limit → `SkillQuotaExceededError` via a low monkeypatch / tenant-scoped isolation / `_env_int` valid + fallback); `test_admin_tenant_skills.py` (+3 — POST at the cap → 409 / oversized `instructions` (default+1 chars) → 422 / GET list carries the two limit fields). FE Vitest `SkillsTab.test.tsx` (+4 — N/max count / Add disabled + hint at the cap / textarea `maxLength` + counter / a quota 409 renders inline).
- **Gates**: mypy `src` 0/370 · run_all 10/10 (count 24, no codegen change) · full pytest 2630+5skip (+7, 0 del) vs 2623 · FE lint 0 · build ✓ · Vitest 873 (+4) vs 869 · mockup-fidelity 51 holds (no CSS change — `var(--danger)` token). `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.
- **Drive-through (real admin "Skills" tab :3007 + a fresh repo-root backend with `SKILLS_MAX_PER_TENANT=2` + `SKILLS_MAX_INSTRUCTIONS_CHARS=200` so the caps are reachable, tenant acme-skills)** — BOTH legs PASS:
  - **Leg A (count quota)**: the tab showed "1 / 2 skills" + Add ENABLED → created a 2nd skill (`deploy-notes`) via the real Add form → list re-fetched → **"2 / 2 skills" + "Skill limit reached" hint + "+ Add skill" [disabled]**; a forced API `POST /{tid}/skills` at 2/2 (browser cookie) → **409 "skill quota reached for this tenant"**.
  - **Leg B (body-size)**: the Add form counter read "0 / 200"; typing a 254-char string into the instructions textarea **capped the value at 200** (`value.length==200`, `maxLength==200`, counter "200 / 200"); a forced API POST with 201-char instructions → **422 "String should have at most 200 characters"**.
  - Observed vs intended matched exactly: the count, the disable-at-cap + hint, and the textarea cap are all driven by the SERVER-sourced limits (the low env override surfaced through `SkillListResponse` into the UI, proving single-source — not a hardcoded FE constant); the 409 + 422 are real server rejections (the guardrails BLOCK, AP-4-safe, not decorative). Screenshots in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-117/artifacts/`. Cleanup: the drive-through `deploy-notes` skill deleted (204) → acme-skills restored to 1 skill.

## Impact

A write-path hardening of the 57.114 catalog: a per-tenant count quota + an `instructions` body-size cap, both env-overridable, surfaced to the admin tab via the list response. No migration, no wire/codegen change (count 24), no design note (a feature continuation of the 57.114 catalog + the 57.109 env-knob + the typed-error patterns). Closes `AD-Skills-Per-Tenant-Quota`'s first two asks. **Deferred**: the multi-worker shared cache-invalidation signal (`AD-Config-Cache-MultiWorker-Invalidation` — cross-cutting with `_ModelPolicyCache` + the harness-policy cache, YAGNI under single-worker) and a per-tenant-CONFIGURABLE quota (the 57.56 `meta_data` override pattern, YAGNI now).
