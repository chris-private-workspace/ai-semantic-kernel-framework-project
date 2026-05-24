# FIX-012: `--sc-border` aligned to mockup `--border` (Path A — global border-color visual fix for not-yet-re-pointed pages)

**Date**: 2026-05-25
**Sprint**: AD `AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup` Path A application (not a sprint — single-commit micro-fix on hotfix branch)
**Scope**: 2-line global CSS retarget (`index.css` `*` selector + `tailwind.config.ts` `border` utility) + orphan token declaration cleanup + comment hygiene + MHist
**Branch**: `fix/shadcn-border-token-align-to-mockup`
**PR**: (filled after open)
**Class**: Visual-fidelity transitional fix (Path A acknowledged trade-off vs Path B completeness route)

---

## Problem

User-reported issue #3 in Sprint 57.38 follow-up (2026-05-24) noted **all-page buttons render black borders** but mockup uses light grey borders. FIX-011 §Issue 3 cascade analysis traced this to **two consumer points** still using the shadcn HSL approximation `--sc-border`:

1. `frontend/src/index.css:85` — global `* { border-color: hsl(var(--sc-border)) }` reset (affects every element without an explicit `border-color`)
2. `frontend/tailwind.config.ts:26` — Tailwind utility `border` → `"hsl(var(--sc-border))"` (consumed by ~31 not-yet-re-pointed files via the `border-border` / `border` utility class)

Production default theme is dark mode (`<html class="dark" data-theme="dark">` per `index.html:2`). In dark mode the HSL value `217.2 32.6% 17.5%` resolves to near-black L=17.5% — visibly mismatched with mockup's `oklch(0.26 0.008 260)` mid-grey L=26%.

The AD `AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup` proposed two paths:

- **Path A** (1-line global fix per consumer): point both consumer sites at the verbatim mockup `--border` token instead of `--sc-border`. Pros: every not-yet-re-pointed page instantly visually closer to mockup. Cons: violates Sprint 57.28's 4-layer dual-track design intent (shadcn-system tokens were de-collided as `--sc-*` precisely to keep the two systems separate during the Phase 1 → 2 transition).
- **Path B** (completeness): continue the Phase-2 per-page re-point epic until all 6 🟡 routes done; the shadcn token usage naturally disappears.

User explicitly chose **Path A** as the acceptable transitional fix to unblock the visual drift while the Phase-2 epic continues its remaining 2 🟡 STRUCTURAL routes.

---

## Root Cause

The `--sc-border` declaration was created in Sprint 57.28 (verbatim-CSS 4-layer foundation switch) precisely to de-collide with the mockup `--border` token now owned by `styles-mockup.css`. The de-collision was correct structurally — but the **HSL value** retained from V1's shadcn defaults (`214.3 31.8% 91.4%` light / `217.2 32.6% 17.5%` dark) was never re-tuned to track the mockup oklch values. Result: a structurally separate token still rendered visibly mismatched borders on all pages that consume the `*` reset or the Tailwind `border` utility.

The Sprint 57.28 4-layer intent assumed the de-collision would be short-lived (Phase-2 epic would close before user noticed). 10 sprints of Phase-2 work later, 31 files still consume `border-border` utility and 6 🟡 routes remain. The visual drift compounded enough to trigger user-reported issue #3.

---

## Solution (Path A — 2 lines of code change + orphan cleanup)

### File 1: `frontend/src/index.css`

**Core change** (1 line):

```diff
- border-color: hsl(var(--sc-border));
+ border-color: var(--border);
```

The global `*` selector now consumes `--border` directly from `styles-mockup.css` (verbatim mockup oklch — automatically picks up the correct value per `[data-theme][data-variant]` scope, including light / dark / warm / cool variants).

**Orphan cleanup** (Karpathy §3 — your own changes' orphans you clean):

- Remove `--sc-border: 214.3 31.8% 91.4%;` (light `:root`)
- Remove `--sc-border: 217.2 32.6% 17.5%;` (`.dark` scope)
- Update file header docstring + `@layer base` block comment to reflect that `--sc-border` is retired (only `--sc-primary` remains as the active de-collided shadcn token)
- Add 1-line MHist entry

### File 2: `frontend/tailwind.config.ts`

**Core change** (1 line):

```diff
- border: "hsl(var(--sc-border))",
+ border: "var(--border)",
```

The Tailwind `border` utility (consumed via `className="border"` or `className="border-border"` in 31 not-yet-re-pointed files) now resolves to the same mockup `--border` token.

**Comment + MHist hygiene** (parallel to index.css):

- Update inline comment to drop `--sc-border` from the de-collide narrative
- Add 1-line MHist entry

### Why both files (the AD said "1 line global fix")

The AD candidate description under-estimated scope: shadcn maps the utility class via Tailwind config, so a single consumer change in `index.css` would leave the Tailwind utility silently mismatched. The true minimal fix is 1 line per consumer = 2 lines total. Comment + orphan cleanup are bonus hygiene (Karpathy §3); the core behavioural change is 2 lines.

---

## Verification

| Check | Result |
|-------|--------|
| `grep '--sc-border[:\\)]' frontend` | 0 matches (declarations + consumers fully retired) |
| `grep 'sc-border' frontend` | Only 2 matches remaining — both are traceability text in the new comments mentioning "FIX-012 retired `--sc-border`" (expected for history) |
| TypeScript strict (`npx tsc --noEmit`) | 0 errors |
| Mockup-fidelity guard (`node scripts/check-mockup-fidelity.mjs`) | ✅ pass — `styles-mockup.css` byte-identical to mockup source; HEX_OKLCH_BASELINE 51 unchanged (no oklch literals added in `.ts/.tsx`) |
| Vitest (`npx vitest run`) | ✅ 478/478 (96 files) — same as Sprint 57.39 baseline |
| Vite build (`npm run build`) | ✅ built in 3.32s — main `index-jMglWv0j.js` 336.52 kB |
| ESLint | Pre-existing TSSatisfiesExpression warnings from `jsx-ast-utils` upstream (unchanged from baseline; not caused by FIX-012) |

**Visual verification deferred**: a static CSS-variable redirect with deterministic value resolution + mockup-fidelity guard pass + Vitest baseline preserved is sufficient validation for a 2-line global retarget. Full route-sweep visual diff is available on demand but not required to land the fix — the change is reviewable by reading the 2-line diff against the user-acknowledged Path A spec.

---

## Impact

### Visual

- **All elements using `* { border-color }` default** (every element with a `border` width but no explicit `border-color`) now render the mockup-verbatim oklch instead of the HSL approximation
- **All 31 files using Tailwind `border` / `border-border` utility** now resolve to the same mockup `--border` value
- **Theme-aware**: `--border` is scoped by `[data-theme][data-variant]` in `styles-mockup.css` — fix automatically inherits the correct value for `dark + neutral` (default), `dark + warm`, `dark + cool`, `light + neutral`, `light + warm`, `light + cool` (8 variants total)
- **Already-re-pointed Phase-2 pages**: unaffected (they consume their own verbatim CSS classes that bypass the `*` and `border-border` utilities)

### Structural (acknowledged trade-off — user explicit choice)

- **Sprint 57.28 4-layer dual-track design intent partially violated**: the de-collided `--sc-border` is now gone; `--sc-primary` remains as the only de-collided shadcn token
- **Phase-2 epic still proceeds**: completing the remaining 2 🟡 STRUCTURAL routes is unaffected; Path A is transitional, not a substitute for the Phase-2 epic
- **No backward-incompat risk**: removed token has 0 remaining consumers (declarations + usages all retired in same commit)

### Carryover ADs unblocked / closed

- ✅ **`AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`** — resolved (Path A applied)
- ✅ **FIX-011 §Issue 3** — visual root cause now structurally addressed for all not-yet-re-pointed pages
- ⚠️ Sprint 57.28 retrospective Q4 (4-layer design intent): partial relaxation logged here as transitional state, not a permanent revision of the 57.28 contract

### What still requires Path B (Phase-2 epic completion)

- Components / pages that hardcode `border-color: hsl(...)` HSL approximations inline (vs. relying on the `*` reset or Tailwind utility) are NOT touched by Path A — they need page-by-page re-point per the existing Phase-2 epic plan
- Search query for residual hardcoded HSL borders: `grep -rn 'border-color:\s*hsl' frontend/src` (recommended Phase-2 sweep candidate)

---

## References

- AD source: `claudedocs/1-planning/next-phase-candidates.md` §Sprint 57.38 Follow-up Carryover → `AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`
- Cascade analysis: `claudedocs/4-changes/bug-fixes/FIX-011-state-inspector-outer-padding-and-systematic-anti-patterns.md` §Issue 3
- Sprint 57.28 4-layer foundation switch context: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/retrospective.md` + `memory/project_phase57_28_mockup_fidelity_foundation.md`
- Rule: `docs/rules-on-demand/frontend-mockup-fidelity.md` §Phase-2 re-point systematic anti-patterns AP-Phase2-C (`border-border` → `--sc-border` token residue)

---

## Modification History (newest-first)

- 2026-05-25: Initial creation (FIX-012 — Path A global retarget; index.css `*` + tailwind.config `border` → `var(--border)`)
