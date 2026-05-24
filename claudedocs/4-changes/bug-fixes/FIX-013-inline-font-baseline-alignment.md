# FIX-013: `/state-inspector` card title row — `align-items: baseline` for mixed-font inline content

**Date**: 2026-05-25
**Sprint**: AD `AD-Inline-Font-Baseline-Alignment` application (not a sprint — single-commit micro-fix on hotfix branch)
**Scope**: 1-line inline style override on `CARD_TITLE_ROW_STYLE` constant + WHY comment + MHist
**Branch**: `fix/inline-font-baseline-alignment`
**PR**: (filled after open)
**Class**: Typography visual-fidelity micro-fix (closes FIX-011 §Issue 2 deferred AP-Phase2-B fix)

---

## Problem

FIX-011 §Issue 2 (2026-05-24) documented but deferred the fix for:

> **`/state-inspector` `[v18 by orchestrator_loop]` baseline misalignment** in detail card title — `by` text sits visibly lower than `v18` + `orchestrator_loop` mono tokens.

The misalignment is a **font-pairing visual artifact**: 3 inline spans (`v18` Geist Mono / `by` Noto Sans TC / `orchestrator_loop` Geist Mono) sitting inside a flex row centered along the vertical axis. Geist Mono and Noto Sans TC have different `ascender:descender` ratios, so vertical centers (used by `align-items: center`) do NOT coincide with glyph baselines. Result: the `by` text appears lower than its mono siblings.

The mockup reference renderer (system mono Menlo + system sans) shows smaller drift because the metric-box ratios of those fonts are closer. Production's font choices (Geist Mono + Noto Sans TC) exacerbate the drift to user-visible levels.

FIX-011 codified this as **AP-Phase2-B** (Inline mixed-font span baseline misalignment) in `docs/rules-on-demand/frontend-mockup-fidelity.md` and deferred the fix to a typography audit AD. FIX-013 closes that deferred fix for the documented case.

---

## Root Cause

`StateInspectorPage.tsx:407` renders the title row as:

```tsx
<span className="row" style={CARD_TITLE_ROW_STYLE}>
  <span style={CARD_TITLE_MONO_STYLE}>v{selected}</span>             {/* Geist Mono */}
  <span className="subtle">by</span>                                  {/* Noto Sans TC */}
  <span className="mono" style={{ ...CURRENT_BY_MONO_STYLE, ... }}>   {/* Geist Mono */}
    {current.by}
  </span>
</span>
```

`.row` mockup class (`styles-mockup.css:613`) is:

```css
.row { display: flex; align-items: center; gap: 8px; }
```

The outer `<span className="row">` is therefore a **flex container with `align-items: center`**. For mixed-font children, `center` aligns each child by its **metric-box vertical center** — but Geist Mono's metric box center sits at a different vertical position than Noto Sans TC's metric box center. Glyph baselines drift accordingly.

`CARD_TITLE_ROW_STYLE` previously only overrode `gap`:

```ts
const CARD_TITLE_ROW_STYLE = { gap: 6 };
```

No `align-items` override → `.row` default `center` applied → drift visible.

---

## Solution (1-line scope per AD recommendation)

Add `alignItems: "baseline"` to the inline style override on the specific row span — does NOT modify the global `.row` class (preserves verbatim styles-mockup.css + does not affect IncidentsCard / other compound flex rows where `center` is correct):

```diff
-const CARD_TITLE_ROW_STYLE = { gap: 6 };
+// FIX-013: alignItems: "baseline" overrides .row's default `align-items: center` so
+// mixed-font children (Geist Mono "v18" + Noto Sans TC "by" + Geist Mono "<by-user>")
+// align by glyph baseline instead of metric-box center — fixes visual drift on mockup
+// page-platform.jsx:97 title row when production's Geist Mono + Noto Sans TC pairing
+// (different ascender:descender ratios from mockup's reference Menlo + system sans).
+const CARD_TITLE_ROW_STYLE = { gap: 6, alignItems: "baseline" };
```

`align-items: baseline` makes flex children align by their **first baseline** instead of metric-box center. All 3 spans now share the same alignment line at the glyph baseline level — drift eliminated regardless of font metric differences.

---

## Audit scope decision (Karpathy §3 — surgical scope)

3 mixed-font inline patterns were enumerated in the Day 0 audit:

| Candidate | Location | Decision | Rationale |
|-----------|----------|----------|-----------|
| **A** (documented) | `StateInspectorPage.tsx:407-414` card title row | ✅ Fix | Pure all-text 3-span mixed mono/non-mono inside `.row` flex+center → exhibits documented drift |
| **B** | `CostBurnChart.tsx:168, 170` legend `<span><span className="mono">$X</span> {t(...)}</span>` | ❌ Skip | Outer is plain `<span>` (inline layout, not flex) — default inline baseline already aligns glyph baselines |
| **C** | `IncidentsCard.tsx:70-92` incident row `<div className="row">` | ❌ Skip | Contains compound `RiskBadge` + `Badge` siblings alongside text — `align-items: center` is correct for badge+text composition; switching to `baseline` would visibly worsen badge alignment |

Per Karpathy §3 (don't refactor sibling code that isn't broken): only Candidate A's narrow scope is touched. Other patterns may be audited independently in future if user reports drift.

---

## Verification

| Check | Result |
|-------|--------|
| TypeScript strict (`npx tsc --noEmit`) | 0 errors |
| Mockup-fidelity guard (`node scripts/check-mockup-fidelity.mjs`) | ✅ pass — HEX_OKLCH_BASELINE 51 unchanged (no oklch literals added) |
| Vitest (`npx vitest run`) | (verified after edit — see commit body) |
| Vite build (`npm run build`) | (verified after edit — see commit body) |
| ESLint | Pre-existing TSSatisfiesExpression warnings from `jsx-ast-utils` upstream (unchanged from baseline; not caused by FIX-013) |

**Why this passes mockup-fidelity guard**: the change is a JSX inline style override on a single React component — `styles-mockup.css` and `reference/design-mockups/styles.css` are unchanged (byte-identical diff still passes). The `.row` class definition itself is NOT modified — only one specific consumer adds an inline `alignItems` override.

**Why no Vitest spec needed**: `align-items: baseline` is a visual/typographic adjustment with no behavioural / accessibility / routing impact. No existing Vitest spec asserts on the inline style of this constant; adding one would be over-engineering for a single CSS property.

---

## Impact

### Visual

- `/state-inspector` detail card title `[v18 by orchestrator_loop]` row now renders with all 3 spans aligned by glyph baseline — `by` no longer sits visibly lower than the mono siblings
- All other `.row` consumers (Sidebar items, IncidentsCard, ActiveLoopsCard, ProvidersCard, HITLQueueCard, etc.) are **unaffected** — they keep `.row`'s default `align-items: center`, which is correct for their badge+text / icon+text / multi-row layouts

### Structural

- `.row` mockup class definition unchanged (verbatim styles-mockup.css preserved)
- No tailwind config or token changes
- No backend / API surface changes

### AD lifecycle

- ✅ **`AD-Inline-Font-Baseline-Alignment`** — RESOLVED for the FIX-011 §Issue 2 documented case
- ✅ **AP-Phase2-B deferred fix** (codified in `docs/rules-on-demand/frontend-mockup-fidelity.md` from FIX-011) — closed for the documented case; the rule itself remains as the systematic anti-pattern reference for future Phase-2 re-point sprints

### What's NOT included

- Broader typography audit beyond the documented case (B/C dispositioned to skip per Karpathy §3); if future user reports other drift cases, individual fixes apply the same `alignItems: "baseline"` pattern at the specific row, NOT globally on `.row`
- No `vertical-align` baseline fix attempted for non-flex inline contexts (Candidate B) — default inline baseline alignment is acceptable for plain `<span>` mixed-font content

---

## References

- AD source: `claudedocs/1-planning/next-phase-candidates.md` §Sprint 57.38 Follow-up Carryover → `AD-Inline-Font-Baseline-Alignment`
- Cascade analysis: `claudedocs/4-changes/bug-fixes/FIX-011-state-inspector-outer-padding-and-systematic-anti-patterns.md` §Issue 2
- Rule: `docs/rules-on-demand/frontend-mockup-fidelity.md` §Phase-2 re-point systematic anti-patterns AP-Phase2-B (inline mixed-font span baseline misalignment)
- Mockup truth: `reference/design-mockups/page-platform.jsx:97-102` (title row mixed-font span structure)
- CSS spec: `.row` defined at `frontend/src/styles-mockup.css:613` (verbatim from mockup)

---

## Modification History (newest-first)

- 2026-05-25: Initial creation (FIX-013 — alignItems: baseline on CARD_TITLE_ROW_STYLE)
