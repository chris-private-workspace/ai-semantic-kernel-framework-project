# CHANGE-086: Skills system visibility + preview (admin authoring UX)

**Date**: 2026-06-15
**Sprint**: 57.119
**Scope**: api/v1/admin (read endpoint) + frontend tenant-settings (Skills tab)
**AD**: ships the system-skills-visibility leg of `AD-Skills-Authoring-UI` (3rd of the remaining Skills epic items; the chosen thin vertical via AskUserQuestion)

## Problem / Motivation

The admin Skills tab (57.114) lets a tenant author custom skills (name/description/instructions CRUD) but shows ONLY the tenant's own overlay skills. The system-bundled skills (`code-review` / `digest` / `summarize`) — the base set every tenant's skills overlay, and what the model actually sees — were invisible in any admin UI. An admin couldn't see the base catalog, which names would shadow a built-in one, or a skill's full instructions before saving.

## Solution

A read-only **"System Skills"** section in the admin Skills tab + a **Preview** modal.

- **`GET /admin/tenants/{tenant_id}/skills/system`** (`api/v1/admin/tenants.py` — `list_system_skills`, mirrors `list_tenant_skills` auth: `require_admin_platform_role` + `_load_tenant_or_404`) → `SystemSkillListResponse{skills: [SystemSkillResponse{name, description, instructions, has_script, overridden}]}`. Lists `get_default_skill_registry().list()` with `has_script = skill.script is not None` (57.118) + `overridden = skill.name in {tenant's skill names}` (the tenant_id makes it meaningful — which bundled skills this tenant has shadowed). Read-only, no audit. The api→Cat-5 import follows the `handler.py:96` precedent (`check_cross_category_import` green).
- **FE data layer**: `SystemSkill` + `SystemSkillListResponse` (`types.ts`); `fetchSystemSkills` (`tenantSettingsService.ts`); `useSystemSkills` + `SYSTEM_SKILLS_QUERY_KEY_BASE` (`useTenantSkills.ts`).
- **`SkillsTab.tsx`**: a read-only "System Skills" `<Card>` (name + a "🔧 script" badge when `has_script` + a "shadowed by your skill" tag when `overridden` + a Preview button; NO edit/delete) + a `previewSkill` state + an inline-overlay Preview modal (no `Modal` primitive in mockup-ui → inline overlay with `role="dialog"` + a window Escape listener + the matching `jsx-a11y` disables — the `TenantMembersDrawer` convention) rendering any skill's `instructions`; a Preview button on the tenant rows too.

Read-only, respects 57.118's tenant-script deferral (`has_script` is a boolean badge; the script source is never shown/edited). NO DB / migration / wire (count 24) / codegen.

## Verification

- **Gate**: mypy `src` **0/371** · black/isort/flake8 0 · `run_all` **10/10** (count 24; `check_cross_category_import` green) · `npm run lint` clean (the modal a11y matches `TenantMembersDrawer`) · `npm run build` ✅ (tsc) · backend pytest **2648 passed, 5 skipped** (+4 vs 2644) · FE Vitest **879 (142 files)** (+6 vs 873) · mockup-fidelity **51** (byte-identical, no CSS) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.
- **Tests**: backend +4 (`test_system_skills_lists_bundled` / `_overridden_flag` / `_requires_admin` / `_tenant_not_found`); FE Vitest +6 (section render / script badge on digest only / shadowed tag / Preview opens+shows instructions / tenant-row Preview + Close / system load-error).
- **Drive-through (real admin Skills tab :3007 + real backend, acme-skills)** — the System Skills section listed the 3 bundled skills read-only; `digest` showed the "🔧 script" badge only; a live-created tenant `code-review` skill made the System Skills `code-review` row show "shadowed by your skill" (digest did not), then cleaned up (204); the Preview modal rendered `digest.md`'s verbatim instructions; Close dismissed. Every control live (real fetch + real render). Screenshots: `…/sprint-57-119/artifacts/sprint-57-119-drivethrough-{system-skills-preview,shadowed-tag}.png`.

## Impact

api read endpoint + frontend (tenant-settings Skills tab); additive + read-only. No DB/migration/wire/codegen. Existing CRUD + quota idioms (57.114/117) untouched. The bundled-registry hot-reload + skill versioning legs of `AD-Skills-Authoring-UI` stay carried. NO design note (feature continuation — extends the 57.114 tab + a thin read endpoint over the existing registry).
