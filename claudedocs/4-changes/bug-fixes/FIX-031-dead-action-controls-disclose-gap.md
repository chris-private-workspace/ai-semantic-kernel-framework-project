# FIX-031: Dead action controls on subagents / admin-tenants / orchestrator disclose backend gap

**Date**: 2026-06-07
**Severity**: Medium (AP-4 Potemkin — honesty/UX, not data-corruption)
**Status**: ✅ Fixed
**Scope**: Frontend (Cat 12 observability-adjacent UX honesty) — 3 pages, no backend change

## Problem

The 2026-06-07 deep drive-through (`claudedocs/5-status/drive-through-20260606/deep-audit-15-fullimpl.md`) found 3 pages whose **data layer is real** but whose **action controls are clickable yet do nothing** (no modal / toast / network) **and carry no disclosure** — an AP-4 dead-control trap (a control that looks functional but isn't, with nothing telling the operator so):

- **NEW-1 /subagents** — `Sync from repo`, `New subagent`, `Test invoke` (+ `Attach tool`) silently no-op.
- **NEW-2 /admin-tenants** — toolbar: `Filter by name, id, region…` is a static `<span>` *faking a search input* (no `<input>` exists), plus `Plan: all` / `Sort: runs (24h)` buttons with no effect.
- **NEW-3 /orchestrator** — header `Test in Chat` / `View in repo` / `Deploy` (+ PromptTab `History` / `Test`) silently no-op. FIX-029 already added a page-level `BackendGapBanner`, but per the Drive-Through DoD a clickable-but-silent control is still a trap even with a page banner.

## Root Cause

These surfaces were ported mockup-faithfully (verbatim-CSS epic) with their action buttons left as visual stubs — the buttons render but were never given an `onClick`, and no backend exists for them yet (all are Phase 58+ features). The pages with real *read* data (agent_catalog / tenant list / config) made the dead *write/action* controls easy to miss in gate-only review; only per-control drive-through clicking surfaced them.

## Solution

Adopt the codebase's existing **GOLD honesty pattern** (already used by `memory` New-entry, `admin-tenants` header Export/New-tenant, `verification`, `tenant-settings` tabs, `governance`): each dead action control discloses the gap on click via

```ts
window.alert("<Action>: backend gap (Phase 58+) — <endpoint> pending")
```

**Visual layer untouched** (mockup-fidelity preserved — no CSS/color/class change; `check:mockup-fidelity` oklch baseline 53 unchanged). Only component-logic-layer `onClick` handlers added.

| File | Controls wired |
|------|----------------|
| `frontend/src/pages/subagents/SubagentsPage.tsx` | Sync from repo / New subagent / Test invoke / Attach tool |
| `frontend/src/features/admin-tenants/components/TenantsTable.tsx` | `discloseToolbarGap()` helper → Filter cmdk (now `role="button"` + `tabIndex` + `onKeyDown` for a11y, `cursor:pointer`) + Plan: all + Sort: runs (24h) |
| `frontend/src/pages/orchestrator/OrchestratorPage.tsx` | module-level `discloseOrchestratorGap()` → Test / View repo / Deploy (header) + Prompt history / Test prompt (PromptTab) |

Backend wiring for these features stays Phase 58+ (carryover ADs: `AD-Subagents-DeadControls-Disable-Or-Alert`, `AD-AdminTenants-Toolbar-Filter-Sort-Wire-Or-Disable`, `AD-Orchestrator-Config-Backend` / `AD-Orchestrator-DeadControls-Disable-Or-Toast`). This FIX only removes the AP-4 trap by disclosing the gap.

## Tests

Added one Vitest case per component (spy `window.alert`, click control, assert disclosure message):
- `frontend/tests/unit/pages/subagents/SubagentsPage.test.tsx` — Sync/New/Test invoke
- `frontend/tests/unit/admin-tenants/TenantsTable.test.tsx` — Filter/Plan/Sort
- `frontend/tests/unit/pages/orchestrator/OrchestratorPage.test.tsx` — Deploy/View repo

## Verification

Gates (all green):
- `npm run lint` → exit 0 (no errors/warnings)
- `npm run build` (tsc + vite) → exit 0
- `npm run test` (vitest) → **766 passed / 0 failed** (763 baseline + 3 new)
- `npm run check:mockup-fidelity` → pass; **oklch baseline 53 unchanged** (no visual-layer change)

**Drive-Through** (real UI :3007 + dev-login, per CLAUDE.md §Drive-Through Acceptance):
- /subagents → "New subagent" → alert `New subagent: backend gap (Phase 58+) — subagent create endpoint pending` ✅
- /admin-tenants → "Plan: all" → alert `Plan filter: backend gap (Phase 58+) — admin tenant filter/sort endpoint pending` ✅; the formerly-dead `<span>` "Filter by name…" search box → alert `Filter: backend gap (Phase 58+) — …` ✅
- /orchestrator → "Deploy" → alert `Deploy: backend gap (Phase 58+) — orchestrator config/deploy endpoint pending` ✅

## Impact

Frontend-only, 3 pages. No backend / DB / API change. No mockup-CSS change. Closes the 3 dead-control findings from the deep drive-through; the underlying features remain Phase 58+ work (tracked via the carryover ADs above).
