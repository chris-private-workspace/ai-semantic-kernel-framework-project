---
sprint: 57.28
phase: Phase 57+ Frontend SaaS 24/N (pending close)
title: AD-Mockup-Fidelity-Foundation-Switch — Verbatim-CSS 4-Layer Sync Protocol Adoption
class: frontend-verbatim-css-foundation 0.55 (NEW class; 1st application; HYBRID weighted blend — Layer-2 verbatim-copy ×0.40 ~10% + Layer-3 index.css slim ×0.55 ~15% + Layer-4 bridge+collision ×0.60 ~20% + theme toggle ×0.55 ~10% + CI guard authoring ×0.55 ~15% + 22-route regression sweep ×0.50 ~20% + closeout ×0.80 ~10% ≈ 0.55)
duration_days: 5 (Day 0 setup + guidance-PR merge + 三-prong + before-baseline / Day 1 Layer 2+3 / Day 2 Layer 4 + theme / Day 3 CI guards + 22-route sweep / Day 4 Vitest + closeout)
related:
  - docs/rules-on-demand/frontend-mockup-fidelity.md (authoritative 4-layer sync protocol + 7 鐵律 + DoD — this sprint executes Phase 1 of it)
  - claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md §5 Phase 1 (this sprint's blueprint) + §3 (4-layer protocol) + §6 (risk caveats)
  - claudedocs/5-status/v2-investigation-20260522/02-frontend-status.md (31-route inventory + epic trajectory)
  - investigation/mockup-fidelity-poc branch (commit 53ca61fc — reference implementation; styles-mockup.css + pages/overview-poc/; NOT merged)
  - Sprint 57.26 plan + checklist (frontend-foundation-token-correction 0.55; closest prior class; route-sweep.mjs harness reused)
  - Sprint 57.20 plan (mockup `--bg`/`--bg-1`/... token tree first added — Layer 3 retires these HSL approximations)
  - Sprint 57.18 plan (semantic + risk token wiring — Layer 3 retires the HSL approximations)
  - Sprint 57.17 plan (frontend-css-engine-hotfix; Tailwind v4 directive — related CSS-engine class)
  - reference/design-mockups/styles.css (Layer 1 canonical — verbatim source for Layer 2)
  - reference/design-mockups/AGENTS.md §整合到 production (mockup two-layer definition)
  - .claude/rules/sprint-workflow.md §Scope-class multiplier matrix + §Step 2.5 (Day-0 three-prong verify)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-22 verbatim-CSS rewrite)
---

# Sprint 57.28 — AD-Mockup-Fidelity-Foundation-Switch

## Sprint Goal

Switch the production frontend's CSS delivery from the lossy **"translate mockup CSS into Tailwind/shadcn"** pipeline — the verified root cause of the Sprint 57.18-57.27 10-sprint mockup drift — to the **verbatim-CSS 4-layer sync protocol** proven byte-identical by the `/overview-poc` PoC (`investigation/mockup-fidelity-poc`). This sprint lands **Phase 1** of `claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md` §5: the **foundation layer only** — Layer 2 verbatim copy + Layer 3 `index.css` slim-down + Layer 4 `tailwind.config.ts` bridge rework + theme-toggle alignment + CI guards. Per-route content re-point is **Phase 2** (later sprints). A 22-route before/after regression sweep proves the switch ships with **0 catastrophic breakage**.

**Two-line philosophy**:

1. **Change the method, not the pages** — the 10-sprint drift was not poor execution; it was the CSS-translation step injecting drift every rebuild (report 03 §1-2). This sprint removes that step at the foundation: mockup `styles.css` is **copied byte-identical**, never re-expressed. Per-page markup is untouched this sprint (Option B — user-approved 2026-05-22).
2. **Sweep to prove no catastrophic breakage** — globally loading `styles-mockup.css` (251 classes + `*`/`body`/`button` reset) plus retiring the HSL token tree has a 22-route blast radius. Every route is screenshotted before vs after; pages that crash / become unusable are fixed in-sprint; expected transition drift (the 13 not-yet-re-pointed pages shifting toward mockup truth) is **catalogued for the Phase-2 re-point epic**, not silently shipped and not fixed here.

## Background

### Why Sprint 57.28 (this sprint)

The 2026-05-22 investigation (3 reports + `/overview-poc` PoC) established: "mockup" is **two layers with opposite copyability** — the visual layer (`styles.css`, 1123 lines / 251 classes / oklch) **can and must be copied verbatim**; only the component-logic layer (`page-*.jsx`, UMD React) needs rewriting. Sprint 57.18-57.27 applied "rewrite" to **both** layers, so the CSS was translated — and translation (oklch→HSL eyeballing + per-page Tailwind re-composition) is lossy by construction. The PoC proved verbatim copy reaches byte-identical computed style on Vite + Tailwind v4.

`docs/rules-on-demand/frontend-mockup-fidelity.md` (created 2026-05-22) is now the authoritative method; CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint was rewritten the same day. This sprint operationalises that rule's 4-layer protocol — **Phase 1, foundation only**.

**Σ bottom-up**: ~11 hr (mid) before calibration
**Calibrated commit**: ~11 hr × 0.55 ≈ ~6 hr (NEW class baseline)

### Why a foundation method-switch sprint (not folded into the rebuild epic)

The `frontend-mockup-strict-rebuild` epic (57.23+) rebuilds routes one at a time, each still translating CSS — so each rebuild re-injects drift (`/overview` rebuilt 3×, `/cost-dashboard` 4×). Switching the **delivery method once, at the foundation, before the bulk of the epic runs** means every subsequent re-point consumes mockup classes directly and gets CSS fidelity **for free** — collapsing the Sprint 57.22 audit's ~297 hr estimate (most of which was CSS translation labour). Doing the switch as its own sprint isolates the 22-route blast radius behind one regression sweep.

### Scope decision — Option B (user-approved 2026-05-22)

The foundation switch produces token collisions / baseline shift on the 13 already-shipped `active` routes. Per user decision (AskUserQuestion 2026-05-22): **Option B — Foundation-only this sprint + full 22-route regression sweep; per-page re-point deferred to Phase 2 (separate sprints).** This sprint guarantees **0 catastrophic breakage** (every route still renders and is usable); expected transition drift is catalogued in the FOUNDATION-SWITCH-REPORT as the Phase-2 epic backlog; structural regressions become carryover ADs. This aligns with report 03 §5's explicit phasing and Sprint 57.26's proven regression-sweep model, and respects CLAUDE.md scope discipline + rolling-planning 紀律 (Option A — same-sprint re-point of all 13 pages — would merge Phase 1+2 into a multi-week mega-sprint and was rejected).

### Class baseline — NEW class `frontend-verbatim-css-foundation` 0.55

No prior class fits cleanly:
- `frontend-foundation-token-correction` 0.55 (Sprint 57.26) — closest, but that corrected token *values* in place; this sprint switches the CSS *delivery method* (verbatim copy + bridge rework + CI guard authoring + theme toggle) — a structurally larger scope.
- `frontend-css-engine-hotfix` 0.60 (Sprint 57.17) — a 1-line v4 directive fix; far smaller.
- `frontend-e2e-sweep` 0.50 (Sprint 57.14) — fits only the regression-sweep portion.

→ NEW class `frontend-verbatim-css-foundation` 0.55, HYBRID weighted blend: Layer-2 verbatim-copy ×0.40 (~10%) + Layer-3 `index.css` slim ×0.55 (~15%) + Layer-4 bridge+collision ×0.60 (~20%) + theme toggle ×0.55 (~10%) + CI guard authoring ×0.55 (~15%) + 22-route regression sweep ×0.50 (~20%) + closeout ×0.80 (~10%) ≈ 0.55. 1st application; Day 4 retrospective Q2 records the actual/committed ratio as the 1st data point; KEEP 0.55 regardless (1 data point insufficient to adjust per `When to adjust` 3-sprint window rule).

### What is preserved (NOT changed)

| Layer | Specific | Reason |
|-------|----------|--------|
| Per-route page content | Every `active`/PROP route's body markup + components | Option B — foundation-only sprint; per-page re-point = Phase 2 epic |
| shadcn-system tokens | `--background`/`--foreground`/`--card`/`--muted`/`--ring`/... (the shadcn standard set the 13 pages still consume) | Kept through the transition (de-collided by rename where they clash with mockup names); retired page-by-page in Phase 2 |
| mockup-system token *values* | The verbatim oklch values now sourced from `styles-mockup.css` | The verbatim copy IS the source of truth; this sprint changes where they come from, not their values |
| Routing / auth | `App.tsx` routes, `RequireAuth`, `authStore` | Untouched |
| Backend | `backend/**` | 0 backend changes |
| i18n | `frontend/src/i18n/**` | 0 copy changes — no i18n keys touched |
| `frontend/scripts/route-sweep.mjs` | The Sprint 57.26 sweep harness | Reused as-is (minor mock tweak only if Day 0 finds it needed) |

### What gets changed (this sprint scope)

| Layer | File | Approach |
|-------|------|----------|
| Layer 2 | NEW `frontend/src/styles-mockup.css` | Byte-identical copy of `reference/design-mockups/styles.css`; imported in `main.tsx` AFTER `index.css` |
| Layer 2 | `frontend/src/main.tsx` | `+1` import line `import "./styles-mockup.css"` after `import "./index.css"` |
| Layer 3 | `frontend/src/index.css` | Slim-down: retire the eye-matched HSL mockup-token approximations (`--bg`/`--bg-1`/.../semantic/risk — Sprint 57.18+57.20) now provided verbatim by Layer 2; `html{font-size:13px}` hack handled per Day-0 grep (see §Technical Specifications); body block aligned |
| Layer 4 | `frontend/tailwind.config.ts` | Bridge rework: mockup-consumed tokens `hsl(var(--X))` → `var(--X)` (var already holds full `oklch()`); shadcn-system token name collisions de-collided (see §Technical Specifications Layer 4) |
| theme | `frontend/src/components/ThemeProvider.tsx` (+ `index.html` if needed) | Align to the mockup's dark-only design (mockup has no light theme); retire the light branch — see §Technical Specifications + §Key Decisions |
| CI guard | NEW `frontend/scripts/check-mockup-fidelity.mjs` + `frontend/package.json` script | `diff` guard (`styles-mockup.css` vs `styles.css`) + grep guard (no hardcoded hex/oklch in `features/`+`pages/`) |
| CI guard | `.github/workflows/<frontend workflow>.yml` | `+1` step running `npm run check:mockup-fidelity` (in-scope per this approved plan — additive guard only) |
| Vitest | `frontend/tests/unit/**` token/theme specs | Adapt selector/assertion if any asserts a retired token or the light theme path (NOT delete) |

## User Stories

### Group A — Day 0 setup + guidance-PR merge + 三-prong + before-baseline (PRE-WORK)

**US-A1**: As a Sprint 57.28 owner, I want plan + checklist landed, the `chore/frontend-mockup-fidelity-guidance` PR opened + CI-green + merged to main (so the corrected guidance is the epic's foundation), a feature branch cut from the updated main, Day 0 三-prong (Prong 1 path verify on `index.css` / `main.tsx` / `tailwind.config.ts` / `ThemeProvider.tsx` / `styles-mockup.css`-absent + Prong 2 content verify enumerating the `styles.css :root` ∩ `index.css :root` token-name collision set + `rem` usage in mockup `styles.css` + `html{font-size}` current state + Prong 4 test-selector verify on token/theme Vitest specs), a before-baseline 1440×900 screenshot of all ~22 routes via the reused `route-sweep.mjs`, and a FOUNDATION-SWITCH-REPORT skeleton — so that Day 1+ builds on a verified baseline and the before/after sweep has a fixed reference set.

### Group B — Layer 2 + Layer 3 (Day 1)

**US-B1**: As a frontend operator, I want Layer 2 landed — `frontend/src/styles-mockup.css` as a byte-identical copy of `reference/design-mockups/styles.css`, imported in `main.tsx` after `index.css` — so that the production app loads the mockup's 251 classes + design tokens verbatim, with `diff` confirming zero divergence (the single non-translation point).

**US-B2**: As a frontend operator, I want Layer 3 landed — `index.css` slimmed to retire the eye-matched HSL mockup-token approximations (now sourced verbatim from Layer 2) and the `html{font-size:13px}` rem-scaling hack handled per the Day-0 grep finding — so that the production CSS no longer carries a parallel translated token tree and the foundation has a single source of truth.

### Group C — Layer 4 + theme toggle (Day 2)

**US-C1**: As a frontend operator, I want Layer 4 landed — `tailwind.config.ts` bridge reworked so mockup-consumed tokens resolve as `var(--X)` (not `hsl(var(--X))`, since the var holds full `oklch()`) and every `styles.css` ∩ `index.css` token-name collision from the Day-0 enumeration resolved (shadcn-only tokens de-collided by rename; shared-intent tokens let the verbatim value win) — so that no `bg-primary`/`bg-bg`/... utility renders invalid CSS and the 13 not-yet-re-pointed pages keep working.

**US-C2**: As a frontend operator, I want the theme toggle aligned to the mockup's dark-only design — `ThemeProvider` light branch retired, `<html>` carrying the mockup-expected dark default — so that the globally-loaded `styles-mockup.css :root` (dark-linear) renders consistently and there is no dead light-theme path. (Production is already dark-default since Sprint 57.21 D-DAY4-6, so this is a small step — see §Key Decisions.)

### Group D — CI guards + 22-route regression sweep (Day 3)

**US-D1**: As a Sprint 57.28 owner, I want CI guards added — a `check-mockup-fidelity.mjs` script + `npm run check:mockup-fidelity` doing the `diff` guard (`styles-mockup.css` byte-identical to `styles.css`) and the grep guard (no hardcoded hex/oklch in `features/`+`pages/`), wired into the frontend CI workflow as one additive step — so that future drift (a re-translated CSS, a hardcoded colour) fails CI instead of shipping silently.

**US-D2**: As a Sprint 57.28 owner, I want all ~22 routes re-screenshotted at 1440×900 after the foundation switch and diffed against the Day-0 before-baseline, plus compared against their mockup-equivalent page (`:8080`) — so that every visual change is catalogued in the FOUNDATION-SWITCH-REPORT as intended-improvement vs transition-drift vs unintended-regression.

**US-D3**: As a Sprint 57.28 owner, I want the sweep findings triaged — catastrophic breakage (page crash / unusable) fixed in-sprint; expected transition drift (the 13 pages shifting toward mockup truth) catalogued as the Phase-2 re-point epic backlog; structural regressions logged as carryover ADs — so that the foundation switch lands without breaking any route and the Phase-2 backlog is accurate (NOT silently shipped).

### Group E — Vitest + closeout (Day 4)

**US-E1**: As a Sprint 57.28 owner, I want the Vitest baseline (430/430 from Sprint 57.26+) preserved — adapting any spec that asserts a retired token or the light theme path — plus `npm run lint` exit 0, `npm run build` green, and the bundle KB delta recorded (Layer 2 adds ~40 KB CSS), so that the switch ships without test or build regression.

**US-E2**: As a Sprint 57.28 owner, I want the FOUNDATION-SWITCH-REPORT finalised with a per-route verdict + the Phase-2 epic backlog, commits + retrospective Q1-Q7 with the 1st-data-point calibration ratio for the NEW `frontend-verbatim-css-foundation` class, memory snapshot + MEMORY.md +1 quality pointer, `.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row, CLAUDE.md Current Sprint row + Last Updated footer (minimal touch), and `next-phase-candidates.md` updated — so that Sprint 57.28 = COMPLETE and the Phase-2 re-point epic opens cleanly.

## Technical Specifications

### Layer 2 — verbatim copy (US-B1)

```
cp reference/design-mockups/styles.css frontend/src/styles-mockup.css
```

`main.tsx` — add the import AFTER `index.css` so its 251 classes win the cascade at equal specificity:

```ts
import "./index.css";
import "./styles-mockup.css";   // Layer 2 — verbatim mockup CSS; NEVER hand-edit
```

DoD: `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` is empty (line-ending tolerant — see Risk R6). The PoC (`investigation/mockup-fidelity-poc` `53ca61fc`) already proved this exact wiring; Day 0 reads the PoC `main.tsx`/`styles-mockup.css` to confirm. `styles-mockup.css` carries a 1-line header comment marking it auto-synced + never-hand-edit (the only deviation permitted from byte-identical — Day 0 confirms whether the rule allows a header or requires pure byte-identical; **default: pure byte-identical, the never-edit notice lives in `main.tsx` import comment + the CI guard**).

### Layer 3 — index.css slim-down (US-B2)

`index.css` currently carries (per report 02 §4.3 + Sprint 57.18/57.20): `@import "tailwindcss"`, shadcn-system tokens (`:root`/`.dark` HSL triples), the mockup-system HSL **approximations** (`--bg`/`--bg-1`/`--bg-2`/`--fg`/... + 7 semantic + 4 risk — added 57.18/57.20), `--radius`, and the `html{font-size:13px}` baseline (added Sprint 57.26).

**Retire** (now sourced verbatim from Layer 2): the mockup-system HSL approximation block. Their names are re-defined verbatim (oklch) by `styles-mockup.css`, which loads later — so consumers keep resolving, now to the correct value.

**Keep**: `@import "tailwindcss"` + the shadcn-system token set (the 13 not-yet-re-pointed pages still consume `bg-card`/`bg-muted`/`text-muted-foreground`/...; retired page-by-page in Phase 2).

**`html{font-size:13px}` hack — Day-0-grep-conditional decision**: this hack was Sprint 57.26's Tailwind-rem-scaling compensation. In the verbatim model `styles-mockup.css` sets its own `body{font-size}` baseline and mockup classes are predominantly px-based.
- **Day 0 Prong 2 greps `reference/design-mockups/styles.css` for `rem` usage.**
- If mockup is effectively **px-only** → `html{font-size:13px}` is harmless to mockup classes and still keeps the 13 not-yet-re-pointed (Tailwind-rem-based) pages compact → **default: KEEP the hack through Phase 1**, mark it for retirement in the Phase-2 final page re-point.
- If mockup **uses `rem`** → `html{font-size:13px}` would distort verbatim mockup classes → **retire the hack now**; accept the 13 rem-based pages' text growing ~23% as catalogued transition drift (not a structural regression under Option B).
- Decision + grep evidence recorded in progress.md Day 0 + Day 1.

Body block: align `font-family`/`line-height` to the mockup form only if `styles-mockup.css`'s own `body` rule does not already cover it (it loads later and should win — verify Day 1).

### Layer 4 — tailwind.config.ts bridge rework + token collision resolution (US-C1)

`tailwind.config.ts` currently bridges colours as `hsl(var(--X))`. Mockup tokens (from `styles-mockup.css`) hold a full `oklch(...)` value — wrapping that in `hsl()` yields invalid CSS. **Day 0 Prong 2 enumerates the collision set**: `{names in styles.css :root}` ∩ `{names in index.css :root}`. Each collision is classified and resolved:

| Class | Example token names | Resolution |
|-------|---------------------|------------|
| **Shared-intent** (mockup token the 13 pages already consume via 57.18/57.20 approximations) | `--bg`, `--bg-1`, `--bg-2`, `--fg`, semantic (`--success`/`--warning`/...), risk levels, density | Retire the index.css HSL approximation (Layer 3); `styles-mockup.css` verbatim oklch is the single source; tailwind bridge for these → `var(--X)` |
| **shadcn-only, collides by name** (mockup also defines the name with different intent) | `--primary`, `--background`, `--foreground`, `--border`, `--ring`, `--input`, `--accent`, `--muted`, `--card`, `--popover`, `--destructive`, `--radius` | De-collide: rename the shadcn-system var in `index.css` (e.g. `--primary` → `--sc-primary`) and update **only** that token's `tailwind.config.ts` bridge entry to `hsl(var(--sc-X))`. The 13 pages consume the Tailwind *utility* (`bg-primary`) which the config still maps — no page-file edit needed |
| **No collision** | mockup-only or shadcn-only unique names | Bridge per its value form: `var(--X)` if oklch, `hsl(var(--X))` if HSL |

Output: `tailwind.config.ts` ends with two bridge styles co-existing — mockup tokens `var(--X)`, shadcn tokens `hsl(var(--sc-X))` — the deliberate transition state. Phase 2 removes shadcn bridge entries as pages re-point off shadcn utilities. The **exact** collision set + per-token class is a Day 0 Prong 2 deliverable feeding Day 2.

### theme toggle alignment (US-C2)

Mockup `styles.css :root` is **dark-linear by default**; mockup theme variation is `[data-theme][data-variant]` — and the mockup has **no light theme** (report 02 §4.1: "3 個 dark variant"). Production `ThemeProvider` toggles a `.dark` class on `<html>` and still carries a light branch.

**Decision (default — see §Key Decisions)**: align to the mockup = **dark-only**. The `ThemeProvider` light branch is retired; `<html>` carries the mockup-expected default state; `styles-mockup.css :root` (no selector) applies unconditionally so dark renders out of the box. Production is already dark-default since Sprint 57.21 D-DAY4-6 (matchMedia OS-preference path dropped), so this removes a dead/inconsistent path rather than changing the shipped look. `ThemeProvider` is **simplified, not deleted** — it stays as the mount point for future variant/density switching (`[data-variant]`/`[data-density]`), which mockup supports. If the user wants to retain a true light mode at plan approval, that becomes a "build beyond mockup" scope addition (the mockup has no light design to be faithful to).

### CI guards (US-D1)

NEW `frontend/scripts/check-mockup-fidelity.mjs` (Node ESM, placed in `frontend/scripts/` per V2 file-org — same location as `route-sweep.mjs`):
1. **diff guard** — read `reference/design-mockups/styles.css` + `frontend/src/styles-mockup.css`; normalise line endings (Risk R6); exit 1 with a clear message if they diverge.
2. **grep guard** — scan `frontend/src/features/**` + `frontend/src/pages/**` for hardcoded `#RRGGBB` / `oklch(` literals; exit 1 listing offenders. Allow-list: legitimate mockup-inline-style references (Day 3 calibrates the allow-list against current state — pre-existing offenders from not-yet-re-pointed pages are recorded as a Phase-2-backlog count, NOT a hard failure this sprint; the guard hard-fails only on **new** offenders → Day 3 sets the baseline count).

`frontend/package.json` — `+1` script `"check:mockup-fidelity": "node scripts/check-mockup-fidelity.mjs"`.
`.github/workflows/<frontend workflow>.yml` (exact file confirmed Day 0 Prong 1) — `+1` step `npm run check:mockup-fidelity` after the existing lint step. This is an additive guard within this approved plan's scope.

### 22-route regression sweep (US-D2/D3)

Reuse `frontend/scripts/route-sweep.mjs` (Sprint 57.26). Day 0 = before-baseline (`screenshots/before/`); Day 3 = after-switch (`screenshots/after/`). Fresh Playwright contexts (no cache — avoids the 2026-05-20 false-alarm class). Triage rule:
- **Catastrophic** (page crashes / blank / unusable) → fix in-sprint (Day 3).
- **Transition drift** (page renders + usable, visuals shifted toward mockup truth or away pending re-point) → catalogue in FOUNDATION-SWITCH-REPORT as Phase-2 epic backlog. Expected and accepted under Option B.
- **Structural regression** (a previously-correct route now structurally broken by the switch) → carryover AD `AD-Foundation-Switch-Regression-<route>` (do NOT silently ship).

### Affected route inventory (Day 0 Prong 1 confirms exact list)

~22 routes across 2 shells (per report 02 §3 + Sprint 57.26 inventory):
- **AuthShell** (~7): `/auth/login` `/auth/callback` `/auth/register` `/auth/invite/:token` `/auth/mfa` `/auth/expired` `/auth/dev`
- **AppShellV2** (~15): `/overview` `/chat-v2` `/orchestrator` `/subagents` `/loop-debug` `/state-inspector` `/memory` `/verification` `/governance` `/cost-dashboard` `/sla-dashboard` `/admin/tenants` `/admin/tenants/settings` + PROP/coming-soon stub routes

## File Change List

### NEW files (~3)

1. `frontend/src/styles-mockup.css` — Layer 2; byte-identical copy of `reference/design-mockups/styles.css`
2. `frontend/scripts/check-mockup-fidelity.mjs` — CI diff guard + grep guard
3. `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/artifacts/mockup-fidelity-foundation/FOUNDATION-SWITCH-REPORT.md` — Day 0 skeleton → Day 3 before/after + vs-mockup matrix → Day 4 final verdict + Phase-2 backlog
   + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/artifacts/mockup-fidelity-foundation/screenshots/` — before/ + after/ captures (local evidence, not committed — per Sprint 57.26 pattern)

### MODIFIED files (~6-7)

1. `frontend/src/main.tsx` — `+1` import `./styles-mockup.css` after `./index.css`
2. `frontend/src/index.css` — Layer 3 slim-down (retire mockup-system HSL approximations; `html{font-size}` per Day-0 grep; body block)
3. `frontend/tailwind.config.ts` — Layer 4 bridge rework (`hsl(var(--X))` → `var(--X)` for mockup tokens; de-collide shadcn token names)
4. `frontend/src/components/ThemeProvider.tsx` — dark-only alignment (light branch retired; simplified, not deleted)
5. `frontend/index.html` — only if the dark default needs the class/attribute set there (Day 2 confirms)
6. `frontend/package.json` — `+1` script `check:mockup-fidelity`
7. `.github/workflows/<frontend workflow>.yml` — `+1` step `npm run check:mockup-fidelity` (exact file from Day 0 Prong 1)
8. Token/theme Vitest spec(s) — adapt assertions for retired tokens / light path (exact files from Day 0 Prong 4)

### DELETED files (0)

None. `frontend/diagnose-render.mjs` was already deleted by Sprint 57.26; `route-sweep.mjs` is reused.

### PRESERVED (not touched)

- All ~22 route page files (Option B — foundation-only)
- `backend/**` — 0 backend changes
- `App.tsx` / `RequireAuth` / `authStore` — routing + auth untouched
- `frontend/src/i18n/**` — 0 i18n keys
- shadcn-system token *values* in `index.css` — kept (only renamed to de-collide; values unchanged)
- `frontend/scripts/route-sweep.mjs` — reused as-is
- `investigation/mockup-fidelity-poc` branch — left as reference; NOT merged

## Acceptance Criteria

1. ✅ `chore/frontend-mockup-fidelity-guidance` PR merged to main; Sprint 57.28 feature branch cut from the updated main
2. ✅ `frontend/src/styles-mockup.css` exists; `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` empty (line-ending tolerant); imported in `main.tsx` after `index.css`
3. ✅ `index.css` slimmed — mockup-system HSL approximation tokens retired; `html{font-size:13px}` resolved per Day-0 grep with decision documented
4. ✅ `tailwind.config.ts` bridge reworked — mockup tokens `var(--X)`; every Day-0-enumerated token collision resolved; no `bg-*` utility renders invalid CSS
5. ✅ theme aligned to mockup dark-only — `ThemeProvider` light branch retired (simplified, not deleted); no dead light path
6. ✅ `check-mockup-fidelity.mjs` (diff + grep guard) authored + `npm run check:mockup-fidelity` wired into frontend CI; guard passes (grep baseline count recorded)
7. ✅ All ~22 routes screenshotted before (Day 0) + after (Day 3) at 1440×900; before/after diff catalogued in FOUNDATION-SWITCH-REPORT
8. ✅ All ~22 routes compared after-switch vs mockup-equivalent; transition drift catalogued as Phase-2 epic backlog
9. ✅ 0 catastrophic breakage shipped — catastrophic issues fixed in-sprint; structural regressions logged as carryover ADs (NOT silently shipped)
10. ✅ Vitest 430/430 preserved (token/theme specs adapted, NOT deleted); `npm run lint` exit 0; `npm run build` green; bundle KB delta recorded (Layer 2 ≈ +40 KB CSS expected)
11. ✅ FOUNDATION-SWITCH-REPORT final — per-route verdict + accurate Phase-2 re-point epic backlog
12. ✅ Commits + retrospective Q1-Q7 with 1st-data-point calibration ratio for NEW `frontend-verbatim-css-foundation` class + memory snapshot + MEMORY.md +1 + sprint-workflow.md calibration matrix +1 NEW class row + CLAUDE.md minimal touch + next-phase-candidates.md update + PR landed

## Deliverables

- [ ] Plan + checklist drafted (this sprint Day 0)
- [ ] `chore/frontend-mockup-fidelity-guidance` PR opened + CI green + merged to main
- [ ] Sprint 57.28 feature branch cut from updated main
- [ ] Day 0 三-prong (Prong 1 path + Prong 2 content/collision-enumeration + Prong 4 test-selector) + before-baseline sweep + FOUNDATION-SWITCH-REPORT skeleton
- [ ] Layer 2 — `styles-mockup.css` verbatim copy + `main.tsx` import
- [ ] Layer 3 — `index.css` slim-down
- [ ] Layer 4 — `tailwind.config.ts` bridge rework + token collision resolution
- [ ] theme toggle dark-only alignment
- [ ] CI guards — `check-mockup-fidelity.mjs` + `package.json` script + CI step
- [ ] Day 3 after-switch 22-route sweep + before/after + vs-mockup matrix + triage
- [ ] Catastrophic breakage fixed in-sprint; transition drift catalogued; structural regressions → carryover AD
- [ ] Vitest 430/430 preserved; token/theme specs adapted; lint + build green; bundle delta recorded
- [ ] FOUNDATION-SWITCH-REPORT final verdict + Phase-2 epic backlog
- [ ] Retrospective Q1-Q7 + 1st-data-point calibration + memory snapshot + MEMORY.md +1 + calibration matrix NEW class row + CLAUDE.md minimal touch + next-phase-candidates.md update
- [ ] PR opened + CI green + merge + post-merge cleanup

## Dependencies & Risks

### Dependencies

- Mockup `:8080` http server reachable (Day 0 + Day 3 vs-mockup comparison) — `cd reference/design-mockups && python -m http.server 8080`
- Production dev server `:3007` running
- `reference/design-mockups/styles.css` present + current (Layer 1 — verbatim source)
- `frontend/scripts/route-sweep.mjs` present on main (Sprint 57.26 — verified Day 0 Prong 1)
- `investigation/mockup-fidelity-poc` branch (`53ca61fc`) readable as the reference implementation
- `chore/frontend-mockup-fidelity-guidance` PR merged before the feature branch is cut (US-A1 sequencing)

### Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R1** | Token name collision set larger / more entangled than expected — `--primary`/`--background`/... resolution cascades into many `tailwind.config.ts` + `index.css` edits | HIGH | Day 0 Prong 2 enumerates the **exact** `styles.css :root` ∩ `index.css :root` set before any Day 2 code; each collision pre-classified (shared-intent / shadcn-only / none); if the set is unexpectedly large (>~15 collisions) re-confirm Day 2 scope with user before proceeding |
| **R2** | Retiring `html{font-size:13px}` regresses the 13 not-yet-re-pointed Tailwind-rem pages (text grows ~23%) | MEDIUM | Day 0 Prong 2 greps mockup `styles.css` for `rem`; default KEEP the hack through Phase 1 if mockup is px-only; if retired, the 13-page growth is catalogued transition drift (Option B), not a structural regression |
| **R3** | Theme approach — **Day 0 D-PRE-1 found the plan premise WRONG**: mockup `styles.css` HAS a full light theme (`[data-theme="light"]` ×4 variants, L114-164). US-C2 cannot be "dark-only / retire light branch" as the §Technical Specifications section assumed. | MEDIUM | Revised US-C2 approach: **keep light support**; `ThemeProvider` toggles the mockup `[data-theme]` attribute (dark↔light) instead of the shadcn `.dark` class. D-PRE-2: production `<html>` must carry `data-theme`+`data-variant` for the verbatim bg/fg tokens to resolve at all (Day 1 sets static attrs; Day 2 wires the toggle). Surfaced to user in the Day 0 report — confirm the revised approach before Day 2. Scope shift <20% (same US, corrected mechanism) → continue per sprint-workflow §Step 2.5 (the §Technical Specifications "theme toggle alignment" section is NOT silently rewritten — this R3 row is the audit-trail record per Step 2.5). |
| **R4** | `styles-mockup.css` global reset (`*`/`body`/`button` + 251 classes) shifts every route's baseline at once | MEDIUM | Expected — it becomes the foundation; the 22-route before/after sweep catalogues every shift; Option B explicitly accepts transition drift; only catastrophic breakage is in-sprint work |
| **R5** | A token/theme Vitest spec asserts a retired token or the light theme path and breaks | LOW | Day 0 Prong 4 greps test files for retired-token names + light-theme assertions; adapt (NOT delete) |
| **R6** | `cp` on Windows introduces CRLF → `diff` guard false-positive | LOW | Copy preserves LF (or `.gitattributes`/`--strip-trailing-cr`); the `check-mockup-fidelity.mjs` diff normalises line endings before comparing |
| **R7** | Browser-cache staleness masks the switch during verification (the 2026-05-20 false alarm) | LOW | Sweep harness uses fresh Playwright contexts; PR body carries a hard-refresh / new-tab verification note |
| **R8** | 22-route sweep finds many transition regressions → Day 3 over-runs | MEDIUM | Sweep batch-screenshots in one ~2-3 min run; triage by severity; only catastrophic fixed in-sprint; transition drift is catalogue-only |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Risk Class A** (paths-filter vs `required_status_checks`): APPLIES — the `chore/frontend-mockup-fidelity-guidance` PR is docs/rules-only → backend-ci paths-filter may skip → mergeStateStatus BLOCKED. Workaround: touch `.github/workflows/backend-ci.yml` header per the documented pattern, or PR-body note. The Sprint 57.28 PR itself touches `.github/workflows/**` so backend-ci fires normally.
- **Risk Class B** (cross-platform mypy unused-ignore): N/A — frontend-only.
- **Risk Class C** (module-level singleton across test event loops): N/A — frontend Vitest.

## Workload

| Group | Bottom-up est | Class haircut 0.55 | Day allocation |
|-------|---------------|--------------------|----------------|
| Group A (Day 0 setup + guidance-PR + 三-prong + before-baseline) | ~1.0 hr | ~0.6 hr | Day 0 |
| Group B (Layer 2 + Layer 3) | ~2.0 hr | ~1.1 hr | Day 1 |
| Group C (Layer 4 + theme toggle) | ~4.0 hr | ~2.2 hr | Day 2 |
| Group D (CI guards + 22-route sweep + triage) | ~3.0 hr | ~1.7 hr | Day 3 |
| Group E (Vitest + closeout) | ~1.0 hr | ~0.6 hr | Day 4 |
| **Σ Bottom-up** | **~11.0 hr** | **~6.2 hr** | **5 working days (Day 0-4)** |

**Bottom-up est ~11.0 hr → calibrated commit ~6.2 hr (multiplier 0.55 — NEW class baseline)**

Day 4 retrospective Q2: record actual / committed ratio as the **1st data point** for the NEW `frontend-verbatim-css-foundation` class. Expected band [0.85, 1.20]; KEEP 0.55 baseline regardless (1 data point insufficient to adjust per `When to adjust` 3-sprint window rule).

## Sequencing / Day plan

### Day 0 — Plan + Checklist + guidance-PR merge + 三-prong + before-baseline

- [ ] Plan + checklist drafted (mirror Sprint 57.26 structure)
- [ ] `chore/frontend-mockup-fidelity-guidance` PR opened → CI green → merged to main
- [ ] Feature branch `feature/sprint-57-28-mockup-fidelity-foundation` cut from updated main
- [ ] Day 0 三-prong — Prong 1 path verify (`index.css` / `main.tsx` / `tailwind.config.ts` / `ThemeProvider.tsx` exist; `styles-mockup.css` absent; `route-sweep.mjs` present; exact frontend CI workflow file) + Prong 2 content verify (enumerate `styles.css :root` ∩ `index.css :root` collision set; grep mockup `styles.css` for `rem`; confirm current `html{font-size}` + mockup HSL approximation block) + Prong 4 test-selector verify (token/theme Vitest specs)
- [ ] Read PoC `investigation/mockup-fidelity-poc` `main.tsx` + `styles-mockup.css` wiring as reference
- [ ] Before-baseline sweep — all ~22 routes at 1440×900 via `route-sweep.mjs before`
- [ ] FOUNDATION-SWITCH-REPORT skeleton + D-PRE findings catalogued in progress.md Day 0
- [ ] Day 0 commit

### Day 1 — Group B (Layer 2 + Layer 3)

- [ ] US-B1 Layer 2 — `cp` `styles.css` → `styles-mockup.css`; `main.tsx` import after `index.css`; `diff` confirms byte-identical
- [ ] US-B2 Layer 3 — `index.css` retire mockup-system HSL approximations; `html{font-size}` decision per Day-0 grep; body block
- [ ] Day 1 spot-check (`/overview` + `/auth/login`) + commit

### Day 2 — Group C (Layer 4 + theme toggle)

- [ ] US-C1 Layer 4 — `tailwind.config.ts` bridge `hsl(var(--X))` → `var(--X)` for mockup tokens; resolve every Day-0-enumerated collision (de-collide shadcn names)
- [ ] US-C2 theme — `ThemeProvider` dark-only alignment; `index.html` if needed
- [ ] Day 2 spot-check (`/overview` + `/cost-dashboard` + `/auth/login`) + commit

### Day 3 — Group D (CI guards + 22-route sweep)

- [ ] US-D1 `check-mockup-fidelity.mjs` (diff + grep guard) + `package.json` script + CI workflow step
- [ ] US-D2 after-switch sweep — all ~22 routes; before/after diff + vs-mockup comparison catalogued
- [ ] US-D3 triage — catastrophic fixed in-sprint; transition drift catalogued; structural → carryover AD
- [ ] FOUNDATION-SWITCH-REPORT before/after + vs-mockup matrix populated
- [ ] Day 3 commit

### Day 4 — Group E + closeout

- [ ] US-E1 Vitest 430/430 (adapt token/theme specs) + lint + build + bundle delta
- [ ] US-E2 FOUNDATION-SWITCH-REPORT final verdict + Phase-2 epic backlog
- [ ] retrospective.md Q1-Q7 + Q2 1st-data-point calibration ratio
- [ ] memory snapshot `memory/project_phase57_28_mockup_fidelity_foundation.md` + MEMORY.md +1 quality pointer
- [ ] `.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row (`frontend-verbatim-css-foundation` 0.55) + MHist
- [ ] `claudedocs/1-planning/next-phase-candidates.md` update (Phase 1 closed; Phase-2 re-point epic backlog referenced)
- [ ] CLAUDE.md Current Sprint row + Last Updated footer (REFACTOR-001 §Sprint Closeout minimal touch)
- [ ] PR open + CI green + merge + post-merge cleanup

---

**Plan drafted**: 2026-05-22 Day 0
**Sprint duration target**: 5 working days from Day 0 plan/checklist commit to PR merged
**Class**: `frontend-verbatim-css-foundation` 0.55 (NEW class; 1st application; HYBRID weighted blend)
