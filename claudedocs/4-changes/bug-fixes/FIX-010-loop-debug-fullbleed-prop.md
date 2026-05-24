# FIX-010: `/loop-debug` excessive left/right padding (`fullBleed` prop missing)

**Date**: 2026-05-24
**Sprint**: 57.37+ hotfix (not a sprint — single-commit micro-fix on hotfix branch)
**Scope**: Frontend / pages / loop-debug + AppShellV2 prop usage
**Branch**: `fix/loop-debug-fullbleed-prop`
**PR**: (filled after open)
**Class**: Layout-class prop drop (NOT a CSS-translation drift like Sprint 57.18-57.27)

---

## Problem

User report (2026-05-24, screenshot `Screenshot 2026-05-24 181736.png`): the production `/loop-debug` page has visibly more left/right padding than the mockup; the mockup `loop-canvas` sits closer to the viewport edge. User flagged the concern that this might be **another CSS-translation misdirection** like the Sprint 57.18-57.27 epic root cause (`claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md`).

Visual delta: production has ~28-50px extra horizontal whitespace on each side of the loop-canvas before the events start.

---

## Root Cause

**Not** a CSS-translation drift. The 4-layer verbatim CSS protocol (Sprint 57.28 foundation + 57.29-57.37 per-page re-points) is intact:

- Layer 2: `frontend/src/styles-mockup.css` byte-identical copy of `reference/design-mockups/styles.css` ✅
- Layer 4: `LoopVisualizer.tsx` standalone mode correctly renders mockup classes `loop-canvas` (grid `1fr 360px`) + `loop-track` (inner padding `20px`) ✅
- `AppShellV2` already implements the `fullBleed` opt-in prop (Sprint 57.21 Day 4 D-DAY4-7, added for chat-v2) ✅

The actual root cause is in `frontend/src/pages/loop-debug/index.tsx`:

```tsx
<AppShellV2 pageTitle="Loop Debug">   {/* ← fullBleed missing */}
  <LoopVisualizer mode="standalone" />
</AppShellV2>
```

The `AppShellV2` `<main>` element receives the default mockup class `content` whose padding is `24px 28px 60px` (`reference/design-mockups/styles.css:409-413`). Combined with `loop-track`'s own `padding: 20px`, the visual horizontal inset becomes `28px + 20px = 48px` — versus the mockup's `0 + 20px = 20px`.

**Why this is a layout-class prop drop, not a translation drift**:

| Sprint 57.18-57.27 root cause | This bug |
|-------------------------------|----------|
| `index.css` translated mockup `oklch` colors to HSL approximations by hand → entire CSS layer drifted | Mockup CSS is verbatim-copied; `content.fullbleed { padding: 0; overflow: hidden; }` escape hatch exists and is wired in `AppShellV2` |
| Affected every page (foundation-level) | Affects only fullbleed-class pages (`/loop-debug`, potentially `/state-inspector`, `/orchestrator` etc.) when their page module forgets the prop |
| Required Sprint 57.28 4-layer protocol rebuild | 1-line prop addition |

The mockup `LoopDebug` (`reference/design-mockups/page-governance.jsx:33-116`) returns `<div className="loop-canvas">` directly — designed as a **fullbleed page** that fills the entire `<main>` viewport with its own grid (`1fr` track + `360px` inspector). Pages of this class must opt into `fullBleed`; the existing reference implementation is `chat-v2/index.tsx:52` (`<AppShellV2 pageTitle="Chat (V2)" fullBleed>`).

---

## Solution

Edit `frontend/src/pages/loop-debug/index.tsx`:

```diff
-      <AppShellV2 pageTitle="Loop Debug">
+      <AppShellV2 pageTitle="Loop Debug" fullBleed>
         <LoopVisualizer mode="standalone" />
       </AppShellV2>
```

Plus a `Modification History` entry for the file header.

Height chain verification (confirmed before edit):
- `.app { display: grid; grid-template-columns: 232px 1fr; height: 100vh }` (mockup styles.css:198+)
- `.main { display: flex; flex-direction: column; overflow: hidden }` (styles.css:340-345)
- `.content.fullbleed { padding: 0; overflow: hidden }` (styles.css:414)
- `.loop-canvas { height: 100%; overflow: hidden }` (styles.css:940-947) — correctly inherits from `.content.fullbleed`

Without `fullBleed`, `.content` is `flex: 1; overflow-y: auto; padding: 24px 28px 60px` — gives the loop-canvas a non-zero box plus inset padding, which is the wrong layout class for this page's design intent.

---

## Verification

- `npm run lint` — clean (3 pre-existing `jsx-ast-utils TSSatisfiesExpression` warnings unrelated)
- `npm test -- --reporter=dot` — **Vitest 464/464 passed** (preserves Sprint 57.37 baseline)
- `npm run build` — success in 3.32s; LoopVisualizer chunk unchanged at 20.56 kB / 6.41 kB gz
- `npm run typecheck` — pre-existing `tsconfig.json:25 TS6310` (skipped per user; unrelated to this edit)

Manual visual: per user re-screenshot after PR merge, `/loop-debug` `loop-canvas` should now flush to the edge of the `<main>` column with only the `loop-track`'s 20px inner padding remaining — matching the mockup `localhost:8080/#loop-debug`.

---

## Impact

- **Scope**: 1 file (`frontend/src/pages/loop-debug/index.tsx`), 1 effective-line change (+ 1 MHist entry)
- **Cascade risk**: 0 — affects only the `/loop-debug` route mount; LoopVisualizer's internal structure (loop-canvas grid `1fr 360px`, loop-track padding 20px) was already correct and unchanged
- **Inline mode**: unaffected — LoopVisualizer `mode="inline"` (used by chat-v2 Inspector panel) returns the compact `.loop-track` without `loop-canvas` wrapper
- **Other Phase-2 routes**: not changed by this fix — if any other route is later found to be in the fullbleed class but missing the prop, it gets its own micro-fix (or a one-shot audit AD: `AD-FullBleed-Pages-Audit`)

---

## Follow-up Audit Candidate (deferred)

Suggested next-sprint AD: **`AD-FullBleed-Pages-Audit`** — grep `frontend/src/pages/**/index.tsx` for `<AppShellV2` mounts and cross-check against mockup `loop-canvas` / `chat-shell` / similar full-viewport layout classes in `page-*.jsx`. Candidates worth checking: `/state-inspector`, `/orchestrator`, `/memory`. Single-commit audit + per-page fixes; not a full sprint.

---

## References

- `reference/design-mockups/page-governance.jsx:33-116` — mockup `LoopDebug` source
- `reference/design-mockups/styles.css:409-414` — `.content` + `.content.fullbleed` rule
- `reference/design-mockups/styles.css:940-998` — `.loop-canvas` / `.loop-track` rules
- `frontend/src/components/AppShellV2.tsx:75,86,121` — `fullBleed` prop definition + `<main>` className branch
- `frontend/src/pages/chat-v2/index.tsx:52` — reference fullbleed-prop usage (Sprint 57.21 Day 4 D-DAY4-7)
- `claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md` — the Sprint 57.18-57.27 translation drift this fix is **not** an instance of
