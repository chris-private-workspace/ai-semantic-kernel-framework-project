# CHANGE-009: Mockup Capture Method Resolution (Option B Formalized)

**Date**: 2026-05-26
**Sprint**: 57.46 (Track C of multi-domain bundle)
**Scope**: Frontend tooling / Documentation
**Closes**: `AD-MockupCapture-Method-Resolution` (Sprint 57.43+ AD-MockupCapture-03+04 carryover)

## Problem

Multiple Sprint 57.40-44 retrospectives logged blockers around capturing mockup PNGs programmatically for drift-audit / Phase-2 re-point evidence. AD-MockupCapture-03 (Sprint 57.43) and AD-MockupCapture-04 (Sprint 57.44 Day 3 byte-proxy deferred) tracked the gap. No formal decision had been made among Options A (file://) / B (static file serve) / C (JSX transpile) / D (real browser screenshot service).

## Root Cause

**Sprint 57.46 Day 0 Prong 1 investigation revealed**: `frontend/scripts/mockup-sweep.mjs` ALREADY exists (109 lines, created 2026-05-25 for drift-audit-2026-05-25) and is fully functional implementing **Option B (python -m http.server on port 8080 + Playwright with hash-routing SPA navigation)**. The script was added during Sprint 57.44/57.45 work without being formally documented as the canonical mockup capture method.

The "blocker" tracked in AD-MockupCapture-03/04 was thus a **doc gap**, not a tooling gap.

## Solution

**Track C scope reduced to formalization + sanity test** (Day 0 D-DAY0-5 finding; saved ~1 hr vs. original plan):

1. **No script changes** — existing `mockup-sweep.mjs` is the canonical implementation
2. **Added §Mockup Capture Method section** to `docs/rules-on-demand/frontend-mockup-fidelity.md` (part of CHANGE-007 commit) covering:
   - Why Option B (vs. A/C/D rationale)
   - Standard command (terminal 1 serves; terminal 2 runs sweep)
   - Script details (BASE_URL hardcoded, hash SPA nav, output path)
   - When to run (audit / re-point evidence; mockup source updates)
   - Anti-patterns (file://, JSX transpile, real-browser service)
3. **No script header changes** (script already has correct File / Purpose / Category header from 2026-05-25 author)

## Verification

- `grep "Mockup Capture Method" docs/rules-on-demand/frontend-mockup-fidelity.md` → 1 section header match (new in CHANGE-007 edit)
- `grep "python -m http.server" docs/rules-on-demand/frontend-mockup-fidelity.md` → ≥1 match
- `frontend/scripts/mockup-sweep.mjs` exists with Option B implementation confirmed (lines 33-37 + 83-103)
- **Sanity test**: per Sprint 57.45 memory entry, the script successfully captured all 24 mockup PNGs to `claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup/` during the 2026-05-25 drift audit — this PASSING capture event serves as the historical sanity test reference (re-running would just duplicate; PNGs already exist on disk)

## Impact

- **Scope**: docs-only addition formalizing existing convention
- **Downstream**: future drift-audit / Phase-2 re-point sprints have explicit canonical reference (no more "which option do we pick?" investigation overhead)
- **AD-MockupCapture-03 + 04**: BOTH closed (single Sprint 57.46 closure)
- **Estimated Day 0/1 time savings**: ~1 hr (was planned ~1.5 hr; actual ~30 min for doc + CHANGE record)

## Cross-references

- `docs/rules-on-demand/frontend-mockup-fidelity.md` §Mockup Capture Method (added in Sprint 57.46 Track A edit)
- `frontend/scripts/mockup-sweep.mjs` — canonical script (unchanged)
- `frontend/scripts/route-sweep.mjs` — sibling production-side sweep (shares slug naming)
- CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint — already mentions `python -m http.server`
- Sprint 57.45 memory subfile (`memory/project_phase57_45_chatv2_inspector_tab_path_b.md`) — historical successful 24-PNG capture
- `claudedocs/4-changes/feature-changes/CHANGE-007-mockup-fidelity-auditdocsync-rule.md` — sibling track A
