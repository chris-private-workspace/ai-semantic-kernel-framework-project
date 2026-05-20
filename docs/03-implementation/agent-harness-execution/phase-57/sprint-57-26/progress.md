# Sprint 57.26 Progress — AD-Foundation-Fidelity-Token-Correction

**Class**: `frontend-foundation-token-correction` 0.55 (NEW class; 1st application)
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-26-plan.md`
**Checklist**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-26-checklist.md`

---

## Day 0 — Plan + Checklist + 三-prong + baseline capture — 2026-05-20

### Today's Accomplishments

- Plan + checklist drafted (mirror Sprint 57.25 13-section / Day 0-3 structure)
- Feature branch `feature/sprint-57-26-foundation-fidelity` created from main `08f762fa`
- Day 0 三-prong verify complete (see Drift findings)
- `frontend/scripts/route-sweep.mjs` standalone Playwright sweep harness authored (supersedes temp `frontend/diagnose-render.mjs`, deleted Day 3)
- Day 0 before-baseline sweep — 22 routes captured at 1440×900 to `screenshots/before/`
- FOUNDATION-DRIFT-REPORT skeleton landed (5 foundation drifts + 22-route matrix skeleton)

### Drift findings (Day 0 三-prong — Step 2.5)

| ID | Prong | Finding | Implication |
|----|-------|---------|-------------|
| D-PRE-1 | 2 content | `index.css` has exactly ONE rem-valued custom property: `--radius: 0.5rem` (L51) | rem→px correction scope = 1 token → `8px` |
| D-PRE-2 | 2 content | 9 shell components carry 43 Tailwind arbitrary-px (`[NNpx]`) values | arbitrary-px is mockup-faithful + does NOT rem-scale; rem-scaling pulls inflated `text-*`/`p-*` utilities back to align with this already-correct px world — confirms approach A is sound |
| D-PRE-3 | 4 test selector | 0 Vitest specs assert literal `240px`/`p-6`/`bg-background`/`grid-cols-[` (only 1 a11y comment) | Vitest adapt workload ≈ 0; scope slightly reduced vs plan estimate |
| D-PRE-4 | 1 path | `index.css` / `AppShellV2.tsx` / `AuthShell.tsx` / `tailwind.config.ts` all present | 4 edit targets confirmed; 0 create-collisions |

**Go/no-go**: findings shift scope < 20% (D-PRE-3 slightly reduces) → **GO for Day 1**.

### Notes

- The original "not centered / not full-screen" 2026-05-20 report was confirmed to be **browser-cache staleness** (production code correct — a multi-viewport Playwright probe showed `/auth/login` perfectly centered at 900/1100/1300 heights). The 5 cataloged drifts are the **real** foundation gaps surfaced by the same investigation.
- 22-route sweep set: 8 public (Home + 7 AuthShell) + 14 AppShellV2 (13 real + 1 PROP-stub representative `/compaction`; the other 13 PROP stubs share the same ComingSoonPlaceholder).

### Remaining for Next Day (Day 1 — Group B)

- US-B1 font-size approach spike (`13px` vs `81.25%`) + `index.css` baseline + `--radius` rem→px
- US-B2 `AppShellV2` sidebar 232px + `bg-bg`/`text-fg` + `<main>` padding
- US-B3 `AuthShell` backdrop + `index.css` body block alignment

### Day 0 commit

- Commit: _recorded after Day 0 commit_
