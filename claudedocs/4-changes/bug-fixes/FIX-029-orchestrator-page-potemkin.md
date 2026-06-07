# FIX-029: /orchestrator AP-4 Potemkin — unlabeled fixture config surface

**Date**: 2026-06-07
**Sprint**: post-57.87 (drive-through audit follow-up)
**Scope**: Frontend / pages / orchestrator (AP-4 honesty)

## Problem
The 2026-06-06 35-page drive-through audit flagged `/orchestrator` as the **lone
unlabeled Potemkin among 15 full-impl pages**: the entire page (4 KPI stats + all
6 config tabs Config / Prompt / Tools / Subagents / Budgets / Policies + the
header Test / View-in-repo / **Deploy** actions) renders hardcoded fixture with
**no fixture/demo note**, and the action buttons have no `onClick` (dead). It
masquerades as a working, "live" orchestrator config + deploy surface.

## Root Cause
`OrchestratorPage.tsx` is a verbatim-CSS re-point of mockup `page-agents.jsx`
L1-340 (Sprint 57.19 → 57.34). It was shipped as a visual design surface: every
value is a literal `defaultValue` / `*_FIXTURE` constant; there is **no backend**
for orchestrator config or deploy (wiring one would be a whole new feature, out
of scope). Unlike every other fixture-backed page (cost-dashboard, sla-dashboard,
overview, verification, tenant-settings — all verbatim re-points too), this page
was the only one that never received the project's standard `BackendGapBanner`
AP-2 honesty marker, so its fixture nature was invisible to operators/reviewers.

## Solution
Add the canonical, already-ubiquitous honesty marker (used on 40+ widgets across
the app — `frontend/src/components/ui/BackendGapBanner.tsx`, `role="note"`,
warning tone). Because the *whole* surface is fixture (not just one widget), place
**one page-level `BackendGapBanner` above the tabs** (always visible regardless of
active tab), declaring: backend config/deploy API pending Phase 58+
(`AD-Orchestrator-Config-Backend`); settings are not persisted; Test / View-repo /
Deploy actions are non-functional.

Mockup-fidelity preserved: no mockup widget or button is deleted/mutated (the
banner is additive, exactly as on every other re-pointed page); the dead buttons
+ "live" badge stay visually mockup-faithful but are now honestly contextualized.

- `frontend/src/pages/orchestrator/OrchestratorPage.tsx`: import + render
  `<BackendGapBanner reason={t("orchestrator.backendGap")} />` after page-head.
- `frontend/src/i18n/locales/{en,zh-TW}/common.json`: new `orchestrator.backendGap` key.
- `frontend/tests/unit/pages/orchestrator/OrchestratorPage.test.tsx`: assert the
  banner renders (`backend-gap-banner` testid + "non-functional" text).

## Verification
- Vitest: `OrchestratorPage.test.tsx` (8 tests incl. new banner assertion) green.
- Gates: `npm run lint` (no `--silent`) + `npm run build` + `npm run check:mockup-fidelity` clean.
- **Drive-through** (real UI :3007 + real backend): `/orchestrator` renders the
  banner above the tabs (screenshot `shots/22-orchestrator-after-FIX-029.png`).

## Impact
Frontend-only, additive (one shared banner + 1 i18n key per locale). No mockup CSS
change → no oklch/HEX_OKLCH baseline impact. No backend / schema change. The page
remains a mockup-faithful design preview but is now honestly labeled, closing the
AP-4 Potemkin. Wiring a real orchestrator config/deploy backend stays a separate
Phase 58+ item (`AD-Orchestrator-Config-Backend`).
