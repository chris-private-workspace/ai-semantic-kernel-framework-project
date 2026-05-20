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

- Commit `a16c248f` — `chore(sprint-57-26, Day 0): plan + checklist + 三-prong + route-sweep harness + before-baseline` (5 files; 751 insertions)
- `screenshots/before/` (22 PNG) kept as local evidence — not committed (binary; Day 2 after/ + mockup/ join it for the regression diff)

---

## Day 1 — Group B (token correction + shell alignment) — 2026-05-21

### Today's Accomplishments

- **US-B1 font-size approach decision**: `html { font-size: 13px }` (approach A). The spike was resolved by reasoning rather than two equivalent screenshot runs: `13px` and `81.25%` are numerically identical in a default browser (13/16 = 0.8125) — they differ ONLY in a11y user-font-scaling. Chose absolute `13px` per CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (mockup `styles.css:184` body uses absolute `13px`; the operator portal is a fixed-design app, not responsive-to-preference). Karpathy §2 simplicity — eliminate an unknown by reasoning when the two options are provably equivalent.
- **US-B1 `index.css`**: added `html { font-size: 13px }` in `@layer base`; `--radius` `0.5rem` → `8px` (the only rem-valued custom property per D-PRE-1); body block gained `line-height: 1.45` (mockup `styles.css:185`).
- **US-B1 `tailwind.config.ts` borderRadius audit**: `borderRadius.md/sm` use `calc(var(--radius) - Npx)` — px-arithmetic-safe with px `--radius`; **no change needed**.
- **US-B2 `AppShellV2.tsx`**: sidebar grid `240px` → `232px`; root `bg-background text-foreground` → `bg-bg text-fg`; `<main>` `p-6` → `pt-[24px] px-[28px] pb-[60px]` (arbitrary-px, matches mockup `.content` padding `24px 28px 60px` at `styles.css:412`; arbitrary-px is rem-scale-immune so it stays exact).
- **US-B3 `AuthShell.tsx`**: radial-gradient backdrop base `hsl(var(--background))` → `hsl(var(--bg))` (mockup token tree; hue consistent with authed routes).
- **US-B3 `index.css` body**: `line-height: 1.45` added (above); `font-family` value already correct (Geist chain) — kept as-is (Karpathy §3 — not adding a `--font-sans` token the production CSS never defined just for "token form").
- **3 file headers** updated (`index.css` / `AppShellV2.tsx` / `AuthShell.tsx`): `Last Modified` + Modification History entry.
- **Day 1 after-sweep**: ran `route-sweep.mjs after` — 22 routes captured to `screenshots/after/`.

### Day 1 spot-check (3 representative routes)

| Route | after vs before | Verdict |
|-------|-----------------|---------|
| `/overview` | font ~23% smaller, layout compact, sidebar narrower, base hue neutral-grey — visibly closer to mockup | ✅ correction effective, no breakage |
| `/auth/login` | backdrop hue shifted to `--bg` neutral, card font scaled down, still centered | ✅ correction effective, no breakage |
| `/cost-dashboard` | before AND after both render `AppErrorBoundary` ("Cannot convert undefined or null to object") | ⚠️ see D-DAY1-1 — NOT a Sprint 57.26 regression |

### Drift findings (Day 1)

| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY1-1 | `/cost-dashboard` renders `AppErrorBoundary` in **both** the Day 0 before-sweep and the Day 1 after-sweep. Sprint 57.26 changes are pure CSS/className — they cannot produce a JS `Cannot convert undefined or null to object` runtime error; the before-sweep (pre-change) already showing the same error proves it. Root cause: `route-sweep.mjs` mocks every `/api/v1/` call with a generic empty `[]`, but cost-dashboard's data hook expects an object-shaped cost-report payload → an `Object.*` call on `[]`/`undefined` crashes. | Day 2 — fix the harness to return endpoint-specific object-shaped mocks for cost-report / sla-report (and any other object-shaped endpoint) so the rebuilt dashboards render real content for the before/after + vs-mockup comparison. The 5-foundation-token correction itself is unaffected. |

### Remaining for Next Day (Day 2 — Group C)

- Fix `route-sweep.mjs` endpoint-specific mocks (D-DAY1-1); re-run before/after for cost-dashboard + sla-dashboard
- Full 22-route before/after diff + vs-mockup matrix in FOUNDATION-DRIFT-REPORT
- Cosmetic regressions iterated to parity; structural → carryover

### Day 1 commit

- Commit `2e6f1a72` — `feat(frontend, sprint-57-26, Day 1, Group B): font-size baseline + rem-to-px tokens + AppShellV2 + AuthShell foundation alignment` (5 files; +77 / -20)

---

## Day 2 — Group C (22-route regression sweep) — 2026-05-21

### Today's Accomplishments

- **Harness fix (D-DAY1-1)**: `route-sweep.mjs` gained endpoint-specific object mocks for `cost-summary` + `sla-report` (shapes mirror `features/{cost,sla}-dashboard/types.ts`). The generic `[]` mock crashed those rebuilt dashboards' object-shaped data hooks.
- **Clean before/after re-sweep**: to make the only variable the foundation correction, re-ran BOTH sweeps with the Day-2 fixed harness — `before` against Day 0 source (`git checkout a16c248f -- index.css AppShellV2.tsx AuthShell.tsx`), `after` against Day 1 source (`git checkout 2e6f1a72 -- ...`). Working tree restored to Day 1 (HEAD) after.
- **22-route review** complete; FOUNDATION-DRIFT-REPORT §3 matrix populated.

### 22-route sweep result

| Bucket | Count | Routes |
|--------|-------|--------|
| 🟢 render OK + foundation applied + 0 regression | 19 | home + 7 auth (login/register directly verified, 5 extrapolated as AuthShell family) + overview / chat-v2 / orchestrator / loop-debug / state-inspector / governance / cost-dashboard / sla-dashboard / admin-tenants / tenant-settings / compaction(PROP rep) |
| ⚪ harness-unrenderable (before==after; NOT a regression) | 3 | memory / subagents / verification — data hooks expect object payloads; sweep harness `[]` mock → `undefined.length` AppErrorBoundary in BOTH before and after |
| 🟡 cosmetic regression | 0 | — |
| 🔴 structural regression | 0 | — |

- **R1 outcome**: rebuilt routes (auth 57.23 / cost 57.24 / sla 57.25) all re-verified — render correctly post-correction; the font-size rescale tightened them toward mockup fidelity, did not break them. R1 risk closed; no `AD-Rebuilt-Route-Refidelity` carryover needed.
- **US-C3**: 0 cosmetic + 0 structural regression → nothing to iterate, no carryover AD. The foundation correction is clean.

### Drift findings (Day 2)

| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY2-1 | memory / subagents / verification render AppErrorBoundary (`Cannot read properties of undefined (reading 'length')`) under the sweep harness in BOTH before and after | Pre-existing harness data-mock limitation (same class as D-DAY1-1 cost/sla, but those were fixed because they are R1-critical rebuilt routes). before==after proves no Sprint 57.26 regression. Foundation CSS (`html` font-size + shell tokens) applies globally regardless of whether the page body renders. Visual confirmation of these 3 routes' foundation parity is deferred to their own `frontend-mockup-strict-rebuild` rebuild sprint (real backend / correct fixture available then). NOT fixing the harness further — out of foundation-sprint scope (Karpathy §3). |
| D-DAY2-2 | vs-mockup comparison done by representative method, not a per-route mockup sweep | The 4 foundation dimensions (font 13px / sidebar 232 / main padding / bg hue) are GLOBAL CSS — identical across every route. Per-route mockup screenshots add zero signal for foundation-layer verification, and PROP routes have no mockup counterpart. `compare-overview-{prod,mockup}.png` (Sprint 57.25 diagnosis) + the global-CSS deduction cover it. Per-route residual CONTENT drift is already enumerated by the Sprint 57.22 41-route audit (DRIFT-REPORT §5 cross-references it). |

### Remaining for Next Day (Day 3 — Group D)

- Vitest 430/430 (adapt any shell/layout spec) + lint + build + bundle delta
- FOUNDATION-DRIFT-REPORT §4 final verdict + §5 epic-backlog cross-ref
- Delete `frontend/diagnose-render.mjs`
- Retrospective + memory snapshot + calibration matrix NEW class row + CLAUDE.md minimal touch + next-phase-candidates.md

### Day 2 commit

- Commit: _recorded after Day 2 commit_
