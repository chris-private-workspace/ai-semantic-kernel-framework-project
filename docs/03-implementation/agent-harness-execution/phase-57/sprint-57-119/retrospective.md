# Sprint 57.119 Retrospective — Skills System Visibility + Preview

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-119-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-119-checklist.md) · [Progress](./progress.md) · CHANGE-086

**Closed**: 2026-06-15 · **Branch**: `feature/sprint-57-119-skills-system-visibility` · **Base**: `main` `cf83b274` (post-#293)

---

## Q1 — What was delivered?

The Skills epic's **authoring-UX visibility leg** (ships the system-skills-visibility slice of `AD-Skills-Authoring-UI`, the chosen thin vertical via AskUserQuestion over versioning / hot-reload). The admin Skills tab gains a read-only **"System Skills"** section listing the bundled catalog (`code-review` / `digest` / `summarize`) with a "🔧 script" badge (`has_script`, 57.118) + a "shadowed by your skill" tag (per-tenant `overridden`), plus a **Preview** modal that renders any skill's full instructions (bundled or tenant) read-only. Backed by ONE new read-only `GET /admin/tenants/{tenant_id}/skills/system` over the existing `get_default_skill_registry()` + a `useSystemSkills` TanStack hook + a read-only tab section + an inline-overlay Preview modal. NO DB / migration / wire (count 24) / codegen. Tests +4 backend + 6 FE Vitest. Drive-through PASS (real admin tab).

## Q2 — Estimate accuracy / calibration

- Scope class **`skills-admin-readonly-surface` 0.55 — NEW, 1st data point**.
- Bottom-up est ~6.0 hr → class-calibrated commit ~3.3 hr (mult 0.55, 3-segment form; parent-direct `agent_factor` 1.0).
- Actual ≈ 3.2 hr — ratio **~0.97 IN band**. The slice ran clean: the Day-0 三-prong RESOLVED the #1 lint risk (api→Cat-5 import) via the `handler.py:96` precedent and caught 2 path/contingency drifts (D-fe-test-path: tests under `frontend/tests/unit/...` not co-located; D-modal-primitive: no `Modal` in mockup-ui → inline overlay). The only mid-Day friction was the modal a11y lint (4 jsx-a11y errors on the backdrop + stop-propagation divs) — resolved in ~10 min by mirroring the `TenantMembersDrawer` convention (window Escape listener + `role="dialog"` + the matching disables).
- **KEEP 0.55** (1st data point; pending 2-3 sprint validation). The class sits at the same 0.55 as `config-validation-hardening` (57.117 — a thin backend addition + an FE surface, no migration) — FE-heavier here (a new section + a modal vs a count/disable surface), but balanced by a thinner backend (one read endpoint, no service/error/constants). Lighter than 57.114's `per-tenant-catalog-table-backed` 0.60 (no table / migration / CRUD / RLS — read-only over what exists). If a 2nd read-only-surface sprint diverges > 30%, re-point.
- **Agent-delegated: no** (parent-direct; a bounded FE section + modal over a known tab + a thin read endpoint — small enough to keep parent-direct, and a drive-through that had to show live render of the badge/tag/modal).

## Q3 — What went well?

- **The Day-0 三-prong paid off twice**: it RESOLVED the #1 lint risk before code (the api→Cat-5 `get_default_skill_registry` import is an established green pattern — `handler.py:96` + `router.py:465` already do it, the latter being the exact `[X(name=s.name, description=s.description) for s in registry.list()]` projection I mirrored), and it caught the FE-test path drift (tests live under `frontend/tests/unit/...`, not co-located — the 57.114 lesson) + the missing `Modal` primitive (→ inline overlay) at Day 0, so neither surprised Day 2.
- **`overridden` made the tenant-scoped path honest**: a `/{tenant_id}/skills/system` endpoint returning system-GLOBAL data could read oddly, but computing `overridden` against the tenant's own skills makes the tenant_id meaningful ("the base set available to THIS tenant + which it has shadowed") — and the drive-through proved it (a live-created `code-review` tenant skill flipped the bundled `code-review` row's tag, digest stayed unshadowed).
- **Mirroring the `TenantMembersDrawer` a11y convention** turned a 4-error lint wall into a clean, accessible modal (window Escape + `role="dialog"` + targeted disables with justification) — no new dependency, no `Modal` primitive invented (YAGNI), consistent with the codebase.
- **Optional-vs-required + mock discipline**: the FE `SystemSkill` is a fresh type, but the component calls `useSystemSkills` on every render, so the existing 15 SkillsTab Vitest cases would crash without a default mock — adding `mockSystemSkills({skills:[]})` to BOTH `beforeEach` kept them green (the 57.116/117 "a new hook breaks existing tests" lesson, applied proactively).

## Q4 — What to improve / lessons

- **The modal a11y lint should have been anticipated at Day 0**: the plan's D-modal-primitive finding ("no Modal → inline overlay") correctly predicted a greenfield overlay, but didn't pre-note the jsx-a11y backdrop/stop-propagation requirement. A future "inline overlay" plan item should cite the `TenantMembersDrawer` a11y pattern (Escape listener + `role="dialog"` + the 2 disables) upfront so it's built right the first time, not lint-corrected. Net cost was small (~10 min) but avoidable.
- **`npm run build` after the FE change caught nothing this time** (tsc was already clean from the typed hooks), but running it remained the right discipline (the 57.116 build-not-just-Vitest lesson) — the oxc Vitest transform skips type-checking, so a required-field or union-narrowing error would only surface in `build`.

## Q5 — Anti-pattern audit (04-anti-patterns.md)

- **AP-1** (pipeline-as-loop) N/A. **AP-2** (side-track): ✅ the endpoint → the hook → the tab section + modal is one main flow; nothing dead. **AP-3** (cross-dir scatter): ✅ the read endpoint in the api admin layer (reading the Cat-5 registry — the chat-path precedent), the FE in tenant-settings; no scatter. **AP-4** (Potemkin): ✅ the drive-through proves every control is LIVE — the section data is from the real `/skills/system` endpoint (not a fixture), the "🔧 script" badge reflects the real `has_script`, the "shadowed by your skill" tag reflects the real per-tenant `overridden` (created+deleted live), and the Preview modal renders the real `digest.md` instructions. **AP-6** (speculative abstraction): ✅ read-only visibility + preview ONLY — no edit/disable/create of bundled skills, no script-source display, no versioning/hot-reload built (all deferred); reused the existing registry + the `TenantMembersDrawer` a11y pattern (no `Modal` primitive invented). **AP-7/8/9** N/A. **AP-10** (mock vs real): ✅ the Vitest mocks `useSystemSkills`; the integration test hits the real endpoint; the drive-through hits the real backend — all three agree. **AP-11** (version suffix): ✅ none.
- 0 violations.

## Q6 — Carryover + Closeout checklist

- `AD-Skills-Authoring-UI` **system-skills-visibility leg shipped**; the **versioning** leg (a `version` column + history table + rollback UI) + the **bundled-registry hot-reload** leg (an admin reload action) + a **per-tenant disable-toggle for a bundled skill** stay carried (🟡/🟢 — separate `AD-Skills-Authoring-UI` legs; hot-reload is low prod value as bundled skills are git-deployed).
- Remaining Skills epic ADs (2 left in the "順序執行" sequence): `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) · `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).
- **Closeout**: [x] CHANGE-086 · [x] NO design note (feature continuation — extends the 57.114 tab + a thin read endpoint; sprint-workflow §5.5, mirrors 57.116/117) · [x] retro Q1-Q7 + calibration (`skills-admin-readonly-surface` 0.55 1st data point) · [x] navigators (CLAUDE.md Current-Sprint + Last-Updated / MEMORY.md pointer + subfile / next-phase-candidates `AD-Skills-Authoring-UI` visibility-leg shipped + versioning/hot-reload/disable carried / sprint-workflow matrix `skills-admin-readonly-surface` 0.55 1st-point) · [x] 17.md N/A (an api read endpoint, no new cross-category contract) · [ ] PR (push on user authorization → CI green → merge, gh-verified MERGED before main sync)
