# FIX-009: Sidebar Collapsed-State Toggle Button Invisible

**Date**: 2026-05-24
**Sprint**: post-57.32 (hotfix on main)
**Scope**: Frontend / `components/Sidebar.tsx` (production-only widget styling)
**Severity**: 🟠 UX-blocking (user permanently stuck in collapsed state across F5 / sessions)

---

## Problem

After clicking the sidebar collapse toggle, the sidebar shrinks to 56px icon-only width as designed — but **the toggle button itself becomes invisible**, leaving no UI affordance to expand back.

Compounding the issue, `sidebarCollapsed` is persisted to `localStorage` (`ipa-ui-state`) via `zustand/middleware persist`, so the user is permanently stuck in the unrecoverable state across:

- Page refreshes (F5)
- New tabs
- New browser sessions

**Reported by**: User screenshot 2026-05-24 — `/overview` route with collapsed sidebar showing only nav-item icons in a narrow column, no chevron toggle visible.

---

## Root Cause

The toggle button in `Sidebar.tsx:118-128` is unconditionally rendered (correct intent — production-only "collapse toggle has no counterpart in mockup, kept for usability" per the in-file comment at L14). However, in the collapsed state the button gets visually displaced **outside the sidebar viewport** by a chain of CSS layout constraints:

| Layer | Value (verbatim mockup CSS) | Effect when collapsed |
|-------|------------------------------|------------------------|
| `.app[data-collapsed="true"]` grid | `grid-template-columns: 56px 1fr` | Sidebar column = **56px** |
| `.sidebar-head` | `padding: 12px 14px; display: flex; gap: 10px` | Usable inner width = **56 − 28 = 28px** |
| `.brand-mark` (always shown) | `width: 26px; flex-shrink: 0` | Occupies **26px** of the 28px |
| Toggle button | `marginLeft: "auto"` (Sidebar.tsx:123) | Pushed beyond right edge into the 1fr `.main` column, visually covered by main content |

Net result: brand-mark fills nearly the entire `.sidebar-head`; toggle button is shoved past the 56px boundary and clipped or overlaid by the adjacent main column. The chevron icon is technically in the DOM but not visible/clickable.

`styles-mockup.css` is the verbatim mockup copy locked in by Sprint 57.28's 4-layer fidelity protocol (any edit fails `frontend/scripts/check-mockup-fidelity.mjs`), so the row-flex layout of `.sidebar-head` cannot be relaxed there. The toggle button is a production-only widget (the mockup has none), so a production-only inline-style override on `Sidebar.tsx` is the compliant path per `docs/rules-on-demand/frontend-mockup-fidelity.md` STYLE.md §1 escape-hatch.

---

## Solution

In `Sidebar.tsx`, switch `.sidebar-head` to vertical-stack layout **only when collapsed**, via a conditional inline `style` prop on the `<div>`:

```tsx
<div
  className="sidebar-head"
  style={
    sidebarCollapsed
      ? { flexDirection: "column", height: "auto", padding: 8, gap: 6 }
      : undefined
  }
>
```

Effects:
- `flexDirection: "column"` stacks brand-mark above toggle button (inherited `align-items: center` from the base `.sidebar-head` rule centers them horizontally within the 56px column)
- `height: "auto"` replaces fixed `52px` so both elements fit (≈ 8 + 26 + 6 + ~26 + 8 = ~74px)
- `padding: 8` (8px all-around) replaces `12px 14px` to leave the 40px-wide inner space for the 26px elements
- `gap: 6` tightens the vertical gap between brand-mark and button
- `marginLeft: "auto"` on the button is a row-flex idiom → no-op under column flex, so left in place (no second conditional needed)

Mockup expanded layout is **untouched** (style is `undefined` when not collapsed).

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/Sidebar.tsx` | +5 line conditional inline `style` on `.sidebar-head` div; +Modification History entry |

No CSS file touched. `styles-mockup.css` verbatim check still passes.

---

## Verification

| Gate | Command | Expected |
|------|---------|----------|
| TypeScript | `cd frontend && npx tsc --noEmit -p tsconfig.app.json` | 0 errors (no new) |
| ESLint | `cd frontend && npm run lint` | exit 0 |
| Vitest | `cd frontend && npm run test -- --run` | 452/452 baseline (no behavioural change) |
| Vite build | `cd frontend && npm run build` | success |
| `styles-mockup.css` fidelity | `cd frontend && npm run check:mockup-fidelity` | diff empty + grep clean (CSS file untouched) |
| Manual | Open `/overview` → collapse sidebar → F5 → toggle button visible below brand-mark → click → sidebar expands | ✅ |

---

## Impact

- **Scope**: Frontend only (no backend, no API, no schema)
- **User-visible**: collapse toggle now always reachable in both states
- **Breaking**: none — expanded layout unchanged; mockup-fidelity guard unchanged
- **Persisted state**: existing users already stuck in collapsed state will see the toggle on next reload and can expand again (no localStorage migration needed)

---

## Related

- `frontend/src/components/Sidebar.tsx:118-128` — toggle button definition
- `frontend/src/store/uiStore.ts` — `sidebarCollapsed` persist
- `frontend/src/styles-mockup.css:205,218-251` — collapse grid + sidebar-head + collapsed-children rules
- `docs/rules-on-demand/frontend-mockup-fidelity.md` — production-only escape-hatch policy
- Sprint 57.28 PR #162 — verbatim-CSS foundation switch (the constraint we honor)
