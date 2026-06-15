# Sprint 57.117 Retrospective — Skills Per-Tenant Quota + Instructions Body-Size Limit

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-117-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-117-checklist.md) · [Progress](./progress.md) · CHANGE-084

**Closed**: 2026-06-15 · **Branch**: `feature/sprint-57-117-skills-per-tenant-quota` · **Base**: `main` `1cf58e22` (post-#291)

---

## Q1 — What was delivered?

The Skills epic's **catalog hardening** (closes `AD-Skills-Per-Tenant-Quota`): the 57.114 per-tenant Skills catalog — previously an unbounded write surface — gains two write-path guardrails. A per-tenant skill-count quota (`SKILLS_MAX_PER_TENANT`, default 50, env-overridable) enforced in `TenantSkillService.create` via a new `SkillQuotaExceededError` (409) that the admin POST endpoint's existing `except TenantSkillError` maps with no handler change; and an `instructions` body-size cap (`SKILLS_MAX_INSTRUCTIONS_CHARS`, default 20_000, env-overridable) as a `max_length` on the `SkillCreate/UpdateRequest` Pydantic field → 422. `SkillListResponse` surfaces both effective limits so the admin "Skills" tab shows "N / max", disables Add at the cap, caps the textarea, and renders the 409/422 errors from the SERVER value (not a hardcoded FE constant). NO migration / NO wire change (count 24) / NO new table. Tests +7 backend (4 unit + 3 integration) + 4 FE Vitest. Drive-through BOTH legs PASS (real admin tab + a lowered env limit).

## Q2 — Estimate accuracy / calibration

- Scope class **`config-validation-hardening` 0.55 — NEW, 1st data point**.
- Bottom-up est ~5.5 hr → class-calibrated commit ~3 hr (mult 0.55, 3-segment form; parent-direct `agent_factor` 1.0).
- Actual ≈ at/under the commit — ratio **~0.95-1.0 IN band**. The slice ran clean (Day-0 三-prong confirmed the design end-to-end; the only Day-2 surprise was a *simplification* — `useTenantSkills`/`tenantSettingsService` needed NO change because the hook already returns the whole `SkillListResponse`, so the FE was 1 file lighter than the plan's 2-file estimate). No scope shift, no rework detour.
- **KEEP 0.55** (1st data point; pending 2-3 sprint validation). If a 2nd `config-validation-hardening` sprint diverges > 30% from 0.55, re-point. The class sits below 57.114's `per-tenant-catalog-table-backed` 0.60 (no table / migration / resolver / overlay — this hardens what 57.114 built); the lower mult held.
- **Agent-delegated: no** (parent-direct; the work was ~5.5 hr of small precise edits across the known 57.114 file set — the only subtleties were the tenant-scoped `func.count` query + the FE limit-surface wiring, both better kept parent-direct).

## Q3 — What went well?

- **Day-0 三-prong confirmed the whole design before code**: the count guard auto-maps via the existing `except TenantSkillError` endpoint (no handler change), the body-size is a one-line Pydantic `max_length`, and the FE is single-source via `SkillListResponse`. The 1 real drift (`service.py` lacks `import os` + `func`) was a pure design-confirming add, caught Day-0. Prong-3 N/A (no new table — the DB column stays `Text`).
- **The list-response-surfaces-the-limits decision paid off at drive-through**: setting `SKILLS_MAX_PER_TENANT=2` on the backend and seeing the tab render "2 / 2" + disable Add proved the FE reads the server value, not a constant — the AP-4-honest shape (a hardcoded FE limit could never have shown the low env override).
- **The existing inline error banner already rendered the backend detail**: a 409 quota and a 422 size error both surface verbatim with no custom status→copy mapping needed — the honest server message, fewer FE lines, and AP-4-safe.
- **The drive-through gave decisive guardrail evidence**: a forced API POST at the cap → real 409, and a 201-char body → real 422 (Pydantic), proving the guards BLOCK at the server, not just the UI.

## Q4 — What to improve / lessons

- The plan estimated a 2-file FE change (`tenantSettingsService.ts` + `useTenantSkills.ts` + `SkillsTab.tsx`); the read-before-edit at Day-2 found the hook already passes the whole `SkillListResponse` through `useQuery`, so only `types.ts` + `SkillsTab.tsx` changed. **Lesson reinforced (the Day-0 Prong-2 child-component read discipline): trace the actual data path before estimating pass-through wiring — a React-Query hook that returns the raw response often needs no edit to surface a new field.** Net positive (under-estimate of simplicity), no rework.
- Making the FE type fields **optional** (`max_skills?`) was the right call: it kept every existing 57.114 Vitest mock (`{ skills: [...] }`) compiling AND protected against an older cached response shape (fallback `Infinity` → never falsely disables). A required field would have broken the mocks (the 57.116 `tsc -b` lesson, sidestepped here by choosing optional).

## Q5 — Anti-pattern audit (04-anti-patterns.md)

- **AP-1** (pipeline-as-loop) N/A. **AP-2** (side-track): ✅ both guards ride the 主流量 — quota: `create` count guard → the existing endpoint error map; size: the request field → 422; the list response → the FE surface. **AP-3** (cross-dir scatter): ✅ the quota/size constants + error in `platform_layer.skills`; the request/list-response in chat admin api; the FE in tenant-settings. **AP-4** (Potemkin): ✅ the drive-through proves the guards BLOCK (Add disabled from the server `max_skills`, a real 409 at the cap + a real 422 oversized) — the low env override visible in the tab proves the limit is server-sourced, not a decorative/hardcoded badge. **AP-6** (speculative abstraction): ✅ a global default quota (NOT a per-tenant-configurable mechanism) + a Pydantic `max_length` (NOT a DB migration) + the multi-worker cache signal explicitly deferred — no speculative build. **AP-7/8/9** N/A. **AP-10** (mock vs real): ✅ the integration TestClient 409/422 + the real-backend drive-through 409/422 agree. **AP-11** (version suffix): ✅ none.
- 0 violations.

## Q6 — Carryover

- `AD-Skills-Per-Tenant-Quota` **CLOSED** (the first two asks — the count quota + the body-size limit). Its third ask (the multi-worker shared cache-invalidation signal) is carried as a distinct **`AD-Config-Cache-MultiWorker-Invalidation`** (🟡 NEW) — cross-cutting with `_ModelPolicyCache` + the harness-policy cache, YAGNI under single-worker deploy.
- **Per-tenant-CONFIGURABLE quota** (🟢 carried) — this slice ships a global default; the 57.56 `tenants.meta_data` override pattern can add per-tenant configurability later if a real need appears.
- Remaining Skills epic ADs (the 4 left in the "順序執行" sequence): `AD-Skills-Bundled-Scripts` (57.118 — the largest CC gap; needs a sandbox-execution design) · `AD-Skills-Authoring-UI` (57.119) · `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) · `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).

## Q7 — Closeout checklist

- [x] CHANGE-084 · [x] NO design note (feature continuation — sprint-workflow §5.5) · [x] retro Q1-Q7 + calibration (`config-validation-hardening` 0.55 1st data point) · [x] navigators (CLAUDE.md Current-Sprint + Last-Updated / MEMORY.md pointer + subfile / next-phase-candidates `AD-Skills-Per-Tenant-Quota` CLOSED + `AD-Config-Cache-MultiWorker-Invalidation` NEW / sprint-workflow matrix `config-validation-hardening` 0.55 1st-point) · [x] 17.md N/A (no new contract) · [ ] PR (push on user authorization → CI green → merge, gh-verified)
