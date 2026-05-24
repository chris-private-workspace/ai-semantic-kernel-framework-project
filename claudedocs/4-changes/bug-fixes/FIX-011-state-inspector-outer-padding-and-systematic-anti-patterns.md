# FIX-011: `/state-inspector` excessive outer padding + 3 systematic Phase-2 re-point anti-patterns codified

**Date**: 2026-05-24
**Sprint**: 57.38 follow-up (not a sprint — single-commit micro-fix on hotfix branch + rule additions)
**Scope**: Frontend page wrapper (1-line code) + frontend-mockup-fidelity.md rule additions + 3 NEW carryover ADs
**Branch**: `fix/state-inspector-outer-padding-and-systematic-lessons`
**PR**: (filled after open)
**Class**: Layout-class production-only wrapper drop + systematic Phase-2 re-point lesson codification

---

## Problem (3 user-reported issues, 2026-05-24)

User-reported via screenshots / observations after Sprint 57.38 PR #176 merged:

1. **`/state-inspector` left/right padding visibly more than mockup** (mockup `localhost:8080/#state-inspector` content hugs viewport edge more tightly)
2. **`[v18 by orchestrator_loop]` baseline misalignment** in `/state-inspector` detail card title — `by` text sits visibly lower than `v18` + `orchestrator_loop` mono tokens
3. **All page buttons show black borders** but mockup uses light grey borders — user concern this is another CSS-translation drift like Sprint 57.18-57.27

---

## Root Cause Analysis

### Issue 1 — outer padding wrapper

**File**: `frontend/src/pages/state-inspector/StateInspectorPage.tsx:54+247`

```tsx
const STATE_PAGE_WRAPPER_STYLE = {
  display: "flex",
  flexDirection: "column",
  gap: 14,
  padding: 18,   // ← Sprint 57.19 production-only addition
};
// ...
<div style={STATE_PAGE_WRAPPER_STYLE}>   // ← wrapper not in mockup
  <div className="page-head">...
```

**Mockup truth**: `reference/design-mockups/page-platform.jsx:25-145` `StateInspector` returns `<>` fragment starting directly with `<div className="page-head">`. No outer wrapper, no extra padding.

**Cascade**: `.content` (mockup styles.css:412) provides `padding: 24px 28px 60px`. Production's extra `padding: 18` stacked on top → effective horizontal inset 28 + 18 = **46 px** vs mockup's intended **28 px**.

**Origin**: Sprint 57.19 vintage decision. Sprint 57.37 Day 3 Domain B verbatim CSS re-point **preserved this wrapper** (line 247 comment: *"preserves Sprint 57.19 outer padding inside verbatim mockup"*) — the comment misread the wrapper as "backend wiring" worth preserving when it was actually a translation-era visual artifact that should have been deleted.

### Issue 2 — `by` baseline misalignment

**File**: `frontend/src/pages/state-inspector/StateInspectorPage.tsx:400-407` — detail card title

```tsx
// inline span row: <span>v18</span> <span className="subtle">by</span> <span className="mono">orchestrator_loop</span>
```

**Mockup design** (page-platform.jsx:97-102) intentionally mixes 3 fonts inline:
- `<span>` regular Noto Sans TC
- `<span className="subtle">` regular Noto Sans TC smaller
- `<span className="mono">` Geist Mono

**Cascade**: Default `vertical-align: baseline` on inline `<span>` means each font's metric box's baseline aligns. Geist Mono and Noto Sans TC have different `ascender:descender` ratios — visual baseline drift is **mockup-inherent** but mockup's reference renderer (system mono `Menlo` + system sans) shows smaller drift than production's Geist Mono + Noto Sans TC combo.

**Not a bug in production code** — this is a font-pairing visual artifact that needs an explicit `align-items: baseline` hint to compensate. **Codified as AP-Phase2-B** (not fixed in this hotfix — deferred to AD).

### Issue 3 — black button borders

**Cascade analysis**:

| Layer | Token | Dark theme value | Light theme value |
|-------|-------|------------------|-------------------|
| Mockup `.btn.outline` (styles.css:448-452) | `border-color: var(--border)` | `oklch(0.26 0.008 260)` (mid-grey L=26%) | `oklch(0.91 0.006 260)` (light grey L=91%) |
| Production `index.css:92` `* { border-color: hsl(var(--sc-border)) }` global default | `--sc-border` | `hsl(217.2 32.6% 17.5%)` (dark grey-blue L=17.5% — near-black visually) | `hsl(214.3 31.8% 91.4%)` (light grey) |

**Production default theme** (`frontend/index.html:2`): `<html class="dark" data-theme="dark">` — dark mode is the default.

**Cause matrix**:
- Buttons using **mockup-ui `Button`** → `.btn.outline` class → `var(--border)` (mockup token) → in dark mode `oklch(0.26 ...)` mid-grey ✅ mockup design intent
- Buttons using **Tailwind utility `border-border`** → resolves to `hsl(var(--sc-border))` → in dark mode `hsl(... 17.5%)` near-black ❌ doesn't match mockup design intent
- Plain `<button>` with no `.btn` class → falls through to `* { border-color: hsl(var(--sc-border)) }` → same near-black in dark mode

**31 files** still use Tailwind utility `border-border` (per `grep -rln 'border-border'` in `frontend/src`). These are the not-yet-re-pointed pages from the Phase-2 epic (`/governance`, `/admin-tenants`, `/memory`, `/verification`, etc. — 6 🟡 routes remaining).

**Not a CSS-translation drift** (Sprint 57.18-57.27 class). This is **Phase-2 epic incomplete migration**: the dual-token system (mockup `--border` + shadcn `--sc-border`) is intentional per Sprint 57.28 4-layer foundation, but the value gap between them (L=26% vs L=17.5% in dark) makes shadcn-system pages look "black-bordered" vs mockup "grey-bordered".

---

## Solution

### Issue 1 — fixed in this PR (1-line code)

`frontend/src/pages/state-inspector/StateInspectorPage.tsx:54`:

```diff
- const STATE_PAGE_WRAPPER_STYLE = { display: "flex", flexDirection: "column" as const, gap: 14, padding: 18 };
+ // FIX-011 (Sprint 57.38 follow-up 2026-05-24): dropped `padding: 18` — production-only
+ // Sprint 57.19 vintage outer padding artifact; mockup page-platform.jsx:25-145 has NO
+ // outer wrapper. .content already provides 24px 28px 60px padding; the extra 18px
+ // stacked on top added ~46px effective left/right inset vs mockup's intended 28px.
+ // `gap: 14` kept to preserve vertical rhythm between page-head + grid-stats + grid-2
+ // children (mockup relies on per-class margins which we conservatively reinforce here).
+ const STATE_PAGE_WRAPPER_STYLE = { display: "flex", flexDirection: "column" as const, gap: 14 };
```

Plus MHist entry at file header.

### Issue 2 — NOT fixed in this PR; tracked as AD-Phase2-B-Inline-Font-Baseline-Alignment

Codified as systematic AP-Phase2-B in `docs/rules-on-demand/frontend-mockup-fidelity.md`. Recommended fix shape: add `display: inline-flex; align-items: baseline` to the outer row span (page-platform.jsx:97 style). Defer to dedicated typography audit sprint OR include in next /state-inspector re-touch.

### Issue 3 — NOT fixed in this PR; tracked as AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup

Codified as systematic AP-Phase2-C in `docs/rules-on-demand/frontend-mockup-fidelity.md`. Two recommended paths:

- **Path A (1-line global fix)**: align `--sc-border` value to `--border` in `index.css`. Pros: every shadcn-system page instantly looks closer to mockup. Cons: violates Sprint 57.28 dual-track design intent.
- **Path B (completeness)**: continue Phase-2 epic re-point until all 6 🟡 routes done; shadcn token usage naturally disappears. Recommended.

---

## Verification

- ✅ `npm run lint` — clean (only pre-existing jsx-ast-utils warnings)
- ✅ `npm test -- --reporter=dot` — **Vitest 464/464 passed** (Sprint 57.38 baseline preserved)
- ✅ `npm run build` — success
- ✅ `node scripts/check-mockup-fidelity.mjs` — byte-identical + 51/51 baseline preserved
- ✅ Visual inspection (user): `/state-inspector` left/right padding now matches mockup intent ~28 px (was ~46 px)

---

## Impact

| Scope | Detail |
|-------|--------|
| Files changed | 1 production source (`StateInspectorPage.tsx`) + 1 rule doc (`frontend-mockup-fidelity.md`) + 1 FIX record (this file) + 1 memory subfile + 1 candidates file edit |
| Effective production code | 1 line edit (`padding: 18` removed; 6-line comment added explaining why) + 1 MHist entry |
| Cascade risk | 0 — affects only `/state-inspector` outer padding; LoopVisualizer / Card / KPI grid internals untouched |
| Visual regression | Only `/state-inspector` route changes; ~18 px tighter left/right inset matching mockup |
| Issue 2 + 3 | NOT touched in this PR — codified as systematic anti-patterns for future Phase-2 sprints; new ADs added to next-phase-candidates.md |

---

## Follow-up (deferred — not in this PR)

3 NEW carryover ADs added to `claudedocs/1-planning/next-phase-candidates.md`:

1. **`AD-State-Inspector-Outer-Padding-Wrapper-Fix`** — RESOLVED by this PR. (Logged for trace.)
2. **`AD-Inline-Font-Baseline-Alignment`** — needs typography audit + targeted fix(es) on mockup pages with mixed font-family inline spans. Estimated ~2-3 hr; mid-priority.
3. **`AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`** — decide Path A vs Path B; if A, 1-line `index.css` change; if B, accelerate Phase-2 epic 6 🟡 routes.

---

## References

- `frontend/src/pages/state-inspector/StateInspectorPage.tsx:54+247` — wrapper definition + usage
- `reference/design-mockups/page-platform.jsx:25-145` — mockup `StateInspector` truth (no outer wrapper)
- `reference/design-mockups/styles.css:412` — `.content` padding `24px 28px 60px`
- `frontend/src/index.css:92` — `* { border-color: hsl(var(--sc-border)) }` global default
- `frontend/src/styles-mockup.css:46,62,81,100,120,133,145,159` — `--border` per-theme values (mockup tokens)
- `docs/rules-on-demand/frontend-mockup-fidelity.md` §Phase-2 re-point systematic anti-patterns — codified 3 new AP entries (AP-Phase2-A/B/C)
- `claudedocs/4-changes/bug-fixes/FIX-010-loop-debug-fullbleed-prop.md` — sibling layout-class production drift (sister bug; `/loop-debug` was fullBleed prop drop; this one is outer padding wrapper)
- Sprint 57.18-57.27 epic (`claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md`) — distinct from this issue class; THIS bug is NOT a CSS-translation drift
