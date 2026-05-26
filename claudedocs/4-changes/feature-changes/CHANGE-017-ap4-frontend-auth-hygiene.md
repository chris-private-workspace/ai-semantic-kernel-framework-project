# CHANGE-017: AP-4 Lint False-Positive Fix (Frontend Auth Hygiene)

**Date**: 2026-05-26
**Sprint**: 57.48 (Track E)
**Scope**: Dev tooling (`scripts/lint/check_ap4_frontend_placeholder.py`)
**Closes**: `AD-Frontend-AP4-Pre-Existing-Lint` (carried since Sprint 57.46 — 1/9 V2 lint baseline)

## Problem
9 V2 lints baseline stuck at 8/9 green since Sprint 57.46. `check_ap4_frontend_placeholder.py` reported 7 findings across 3 auth pages (`frontend/src/pages/auth/{invite,login,register}/index.tsx`). Sprint 57.46+ left this as known pre-existing baseline.

## Root Cause
D-DAY0-6 finding: the AP-4 lint regex `\bplaceholder\b` (case-insensitive, word-boundary) matched legitimate HTML5 `placeholder="..."` JSX attribute on `<input>` elements + TypeScript object keys (e.g. `{ placeholder: "Some text" }` in `PLAN_OPTIONS`/region/size data). These are **valid web-standard usage**, NOT Potemkin Feature violations.

The lint was designed to catch UI body text like `<p>This is a placeholder for Phase 58+</p>` (a stub indicator), but its regex didn't distinguish content from attribute/key context.

The 3 auth pages had been deliberately refactored in Sprint 57.35 verbatim re-point — they're fully functional with WorkOS SSO + invite acceptance + tenant registration flow. The lint findings were ALWAYS false positives.

## Solution (engineering fix, NOT page-content change)
Extend `mask_comments()` in `check_ap4_frontend_placeholder.py` to ALSO mask:

1. `JSX_PLACEHOLDER_ATTR` regex: `placeholder\s*=\s*(?:"[^"]*"|'[^']*'|\{[^}]*\})` — handles `placeholder="text"`, `placeholder='text'`, `placeholder={expr}`
2. `TS_PLACEHOLDER_KEY` regex: `\bplaceholder\s*:` — handles `{ placeholder: ... }` object literal keys

Both new masks run AFTER comment masking (so they don't accidentally unmask comment content) and BEFORE the forbidden-pattern scan.

## Verification
- BEFORE: `python scripts/lint/run_all.py` → 8/9 green (7 false-positive findings)
- AFTER: `python scripts/lint/run_all.py` → **9/9 green** ✅
- Spot-check: `\bplaceholder\b` correctly still catches UI-visible text (e.g. inserting `<p>This is a placeholder</p>` into a page would still trigger — verified via mental walk of the masking pipeline)
- Frontend Vite build: succeeds (unchanged; no page touched)
- Frontend `npm run lint`: succeeds (Track E changed NO frontend pages)

## Impact
- **Dev tooling only**; zero frontend behaviour change
- Lint baseline returns to 9/9 green (sprint workflow `Before Commit` checklist AC-5 satisfied)
- Future sprints can rely on AP-4 lint as a real signal (no "noise" pre-existing baseline)
- D-DAY0-6 drift handled at the right layer (broken detector, not legitimate code)

## Why this approach (vs renaming `placeholder` attributes)
- HTML5 `placeholder` attribute is a W3C standard; renaming it would break accessibility + visual UX
- TS object key `placeholder:` is API-style data shape (e.g. plan option labels)
- The lint exists to catch **Potemkin Features** (stub UI body), NOT to ban a CSS/HTML attribute name
- "Fix the detector, not the legitimate code" is the correct engineering response

## File Touches
- `scripts/lint/check_ap4_frontend_placeholder.py` — +JSX_PLACEHOLDER_ATTR regex + TS_PLACEHOLDER_KEY regex + extended `mask_comments()` (~14 lines net add); docstring + MHist updated
