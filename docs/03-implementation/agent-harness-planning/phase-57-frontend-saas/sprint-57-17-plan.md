---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-17-plan.md
Purpose: Sprint 57.17 plan — AD-Tailwind-v4-Directive-Hotfix. Replace the dead Tailwind v3 directives (`@tailwind base/components/utilities`) in `frontend/src/index.css:6-8` with the Tailwind v4 syntax (`@import "tailwindcss"; @config "../tailwind.config.ts";`). The v3 directives have been silently no-op'd since Sprint 57.7 US-B1 installed Tailwind v4.2.4 + `@tailwindcss/postcss` — for ~9 ship sprints the entire frontend has rendered as **unstyled browser-default HTML** (Times-Roman serif, default `<ul>` bullets, raw `<input>` borders, NO Tailwind utility emitted) while e2e + a11y + visual-regression passed because they only inspect ARIA/DOM/text-content, NOT computed CSS. Regenerate the 6 `visual-regression.spec.ts` baselines (now they capture a real shadcn-rendered shell, not an unstyled skeleton), re-run the full e2e suite (anticipate `approval-card.spec.ts` CRITICAL→`#b71c1c` colour-literal sentinel needs re-confirmation now that `text-[#hex]` arbitrary-value classes actually emit CSS), and verify all 9 gated routes + 2 auth pages render the AppShellV2 + shadcn design system. Phase 57+ Frontend SaaS — single-line config hotfix sprint with full-blast-radius validation.
Category: Frontend / build config (Tailwind PostCSS pipeline)
Scope: Phase 57 / Sprint 57.17

Description:
    Sprint 57.16 closeout discovery (2026-05-15 post-merge dev session): when the
    user opened http://localhost:3007/ to begin manual smoke-testing the just-shipped
    Phase 57+ Frontend 13/N stack, **every page rendered as unstyled HTML** — black
    Times-Roman serif text, default `<ul>` bullet markers, raw browser `<input>`
    borders, no rounded buttons, no AppShellV2 grid, no sidebar styling, no shadcn
    card surfaces. The DOM was correct (AppShellV2 3-column layout present in
    accessibility snapshot, 13 sidebar route links, `<main>` regions, `<dialog>`
    `<button role>` ARIA all wired) — `e2e` passes 40 / 7 skip, `a11y-scan` runs
    full axe rules on 9 / 9 gated routes (closes Sprint 57.16 US-B1), `visual-regression`
    snapshots 6 / 6 match baseline — but **zero Tailwind utility classes were
    actually applying any style at runtime**.

    Root cause in one line:

        frontend/src/index.css:6-8 uses Tailwind v3 syntax
            @tailwind base;
            @tailwind components;
            @tailwind utilities;
        but frontend/package.json has tailwindcss@^4.2.4 + @tailwindcss/postcss@^4.2.4
        and frontend/postcss.config.cjs uses `@tailwindcss/postcss` (the v4 plugin).
        The v4 PostCSS plugin SILENTLY IGNORES v3 `@tailwind` directives — they
        emit nothing. The output bundle contains ONLY the literal :root CSS
        variables from index.css (so `body { background-color: hsl(var(--background)) }`
        works = white background) and the `@layer base { * { border-color: ... } }`
        block. NO utility classes (`.flex`, `.p-8`, `.rounded-md`, `.bg-primary`,
        `.text-2xl`, `.font-sans`, `.grid-cols-3` etc.) are generated. Browser
        falls back to its UA stylesheet defaults for everything else.

    The v4 migration path that should have been taken at Sprint 57.7 US-B1 (install
    Tailwind v4.2.4):

        // BEFORE (v3 — what Sprint 57.7 actually wrote):
        @tailwind base;
        @tailwind components;
        @tailwind utilities;

        // AFTER (v4 — what should have been written):
        @import "tailwindcss";
        @config "../tailwind.config.ts";

    The `@config` directive is the v4 mechanism for loading a legacy v3-style
    JS/TS config (`content: [...]` + `theme.extend.colors` + `darkMode: 'class'`)
    — see Tailwind v4 migration guide. This preserves the existing
    `frontend/tailwind.config.ts` (52 lines, shadcn CSS variable bridge for
    border/input/ring/background/foreground/primary/secondary/destructive/muted +
    borderRadius lg/md/sm) without forcing a full v4 `@theme` block migration.
    A future `AD-Tailwind-v4-Config-Migration` sprint can convert to the
    CSS-only `@theme inline { --color-*: hsl(var(--*)); }` pattern (which is
    Tailwind v4 idiomatic + what shadcn v4 docs now recommend), but that's out
    of scope here — this sprint is the minimum-blast-radius hotfix to restore
    the design system to a functional state.

    This sprint:

    A. CSS directive fix (US-A1) — 1-line edit to `frontend/src/index.css:6-8`
       replacing the three `@tailwind` directives with `@import "tailwindcss";`
       + `@config "../tailwind.config.ts";`. Confirm `npm run build` succeeds +
       inspect generated `dist/assets/index-*.css` size (expect significant
       increase from current ~14 kB to ~50-80 kB compiled). MHist +1 line per
       `.claude/rules/file-header-convention.md` budget. Update `vite.config.ts`
       header comment if it references Tailwind v3.

    B. Validation sweep (US-B1 + US-B2) — Full restart of dev server, manual
       browser inspection of 9 gated routes + 2 auth pages via Playwright MCP
       screenshot (target: AppShellV2 sidebar visible, shadcn buttons rounded
       with slate base, Card surfaces visible, font-sans applied). Re-run full
       `npm run e2e` (40 pass / 7 skip baseline) — anticipate that the
       `approval-card.spec.ts` CRITICAL→`#b71c1c` colour-literal sentinel test
       MAY behave differently now: with v3 directives dead, the `text-[#b71c1c]`
       arbitrary-value class emitted nothing, so the test (which asserts
       computed color matches the hex) was likely passing on a different path
       (UA defaults, or hex literal already matched another reason). With v4
       directives working, `text-[#b71c1c]` will emit `.text-\[\#b71c1c\] {
       color: #b71c1c }` and the assertion should pass cleanly. If a regression
       surfaces, debug + fix the consuming component (NOT the spec). Re-run
       `npm run e2e -- a11y/a11y-scan.spec.ts` (9 gated routes + auth pages
       full axe rule set from 57.16) — expect 0 new violations + potentially
       FEWER violations than 57.16's 4 moderate/minor `/chat-v2` structural
       nits (`heading-order` / `landmark-*`) because those landmark detections
       may have been confused by unstyled DOM previously. Re-run
       `npm run e2e -- visual-regression.spec.ts` — expect ALL 6 baselines to
       FAIL (they captured unstyled state); regenerate them via the 57.14
       `visual-baseline` workflow_dispatch (Linux runner) → 6 fresh PNGs auto-
       committed via the 57.14 PR-not-push pattern (FIX-008).

    C. Closeout (US-C1) — retrospective Q1-Q7 + memory snapshot + doc syncs
       (16-frontend-design.md timeline / sprint-workflow.md calibration +1 row
       — NEW `frontend-css-engine-hotfix` scope class 1st application / STYLE.md
       update if §2 token coverage changes after the fix lets `tailwind.config.ts`
       tokens actually emit / CONVENTION.md §10 design-system if it gained
       Tailwind v4 syntax guidance / SITUATION + CLAUDE.md deferred post-merge)
       + PR.

    Deferred OUT of this sprint (explicitly):

    - **AD-Tailwind-v4-Config-Migration** (NEW from this sprint) — full v4-idiomatic
      migration: replace `tailwind.config.ts` + `@config "..."` with a single
      `@import "tailwindcss"; @theme inline { --color-*: hsl(var(--*)); ... }`
      block in `index.css`. Closes the legacy v3 config file. Out of scope here
      because it's a separate refactor with its own blast radius (deletes a
      52-line config file + needs every utility class shadcn touches to be
      mapped in `@theme`). Estimate ~6-8 hr standalone sprint.
    - **AD-Style-Token-Config-Audit** (carryover from 57.16) — tokens documented
      in `STYLE.md §2` but missing from `tailwind.config.ts`: `success` / `warning`
      / `danger` / `card` / `accent` / `thinking` / `tool` / `memory`. Before
      this hotfix, none of these worked anyway (v3 directives dead). After this
      hotfix, the tokens IN the config (`background` / `foreground` / `primary`
      / `secondary` / `destructive` / `muted`) will WORK; the missing ones will
      STILL be silent no-ops. The Sprint 57.15+16 code that uses `bg-success` /
      `bg-warning` / `bg-danger` etc. will visually fall back to inherited
      colour. This sprint observes + documents the per-class fallout in
      progress.md but does NOT fix it. Closes in a follow-up audit sprint.
    - **AD-A11y-Structural-Nits** (carryover from 57.16) — the 4 moderate/minor
      `/chat-v2` axe violations (`heading-order` / `landmark-main-is-top-level`
      / `landmark-no-duplicate-main` / `landmark-unique` + `/auth/callback?error`
      `page-has-heading-one`). May be partially reduced by this fix (working
      shadcn AppShellV2 + proper `<main>` styling could change landmark
      detection); confirm in Day 2 a11y re-run. If still red → still a
      follow-up sprint.
    - **AD-Lighthouse-Visual-Hard-Gate** (carryover from 57.15+57.16) — turn
      `visual-regression.spec.ts` + `frontend-lighthouse.yml` from advisory to
      required CI checks. This sprint REGENERATES baselines but does NOT flip
      the CI gate. After 57.17 the baselines are reliable (captured from real
      shadcn UI), making this AD finally actionable. Promote to top of Phase
      57.18 候選 list post-merge.

## Sprint Goal

Fix the dead Tailwind v3 directive in `frontend/src/index.css:6-8` (Tailwind v4 PostCSS plugin silently no-op'd them since Sprint 57.7 US-B1, leaving 9 ship sprints' worth of pages rendering as unstyled browser-default HTML), regenerate the 6 visual-regression baselines to capture the real shadcn-styled AppShellV2 + 9 gated routes, re-run full e2e (anticipating `approval-card.spec.ts` `text-[#b71c1c]` sentinel needs re-verification), and confirm all 11 frontend routes (9 gated + `/auth/login` + `/`) render the design system. Single-line config hotfix, full-blast-radius validation.

## Background

### 為什麼這個 sprint 存在（Sprint 57.16 closeout dev-session discovery）

Sprint 57.16 merged PR #139 on 2026-05-11 with all CI gates green: pytest 1676+4 / Vitest 236 / Playwright e2e 40 pass / 7 skip / 0 fail / chat-v2 10/10 / `a11y-scan` 9/9 gated routes + auth pages full axe rule / `visual-regression` 6/6 baselines match. Sprint scoring: code 95% / runtime estimated 80%+. CLAUDE.md updated to claim "Phase 57+ Frontend 13/N — frontend/src is now inline-style-clean".

2026-05-15 post-merge dev session opened http://localhost:3007/ for manual smoke testing. **All pages rendered as unstyled HTML**. Investigation (this sprint's pre-flight):

1. `main.tsx:25` imports `./index.css` ✅
2. `index.css:1-8` uses `@tailwind base; @tailwind components; @tailwind utilities;` — **v3 syntax**
3. `package.json` deps: `tailwindcss@^4.2.4` + `@tailwindcss/postcss@^4.2.4` — **v4 installed**
4. `postcss.config.cjs` uses `@tailwindcss/postcss` — **v4 plugin**
5. `tailwind.config.ts` uses v3-style `content[] + theme.extend.colors` — never wired into v4

→ **Tailwind v4 PostCSS plugin silently ignores `@tailwind` directives.** No utilities emitted. The `:root` CSS variables in `@layer base` still bind (so body bg + border-color work via `border-color: hsl(var(--border))`), but `.flex` / `.p-8` / `.bg-primary` / `.rounded-md` / `.text-2xl` / `.font-sans` etc. = empty rules. Browser renders UA defaults.

This is precisely the "dual scoring code 95% / runtime 40%" gap that Sprint 57.5 (V2 Reality Check) was designed to catch. The gap got worse because:

- e2e tests inspect ARIA roles, button labels, text content — never `getComputedStyle()`
- a11y `axe-core` rules check semantic structure + colour-contrast on EXPLICIT colour assertions (not on default UA fallback)
- visual-regression baselines were captured AFTER the dead-directive state was already in place (Sprint 57.14 US-A3) — they pixel-match the unstyled-HTML baseline, so they pass when re-run

The cascade lesson: **Sprint 57.7 US-B1 design-system install was paper-shipped, never runtime-verified.** Sprints 57.8 / 57.9 / 57.11 / 57.12 / 57.13 / 57.14 / 57.15 / 57.16 all built on top of an unstyled foundation. Functional behaviour shipped (chat-v2 SSE works, approval flow works, governance TanStack works, memory CRUD works) but the **visual design system never ran**.

### 為什麼這個 sprint *不* 在 Phase 57.17+ 候選 list（突發 hotfix）

CLAUDE.md Phase 57.17+ 候選 row lists 8 alternatives: AD-Lighthouse-Visual-Hard-Gate / IAM Block B WorkOS spike / Bundle-Size code-split / Tier 1 IaC + DR drill / SOC 2 + SBOM / i18n Feature Namespaces / AD-Style-Token-Config-Audit / AD-A11y-Structural-Nits. **None of these would have surfaced the dead Tailwind v3 directive** — they all assume the design system is functional. This sprint preempts all 8 candidates because without working Tailwind, all 8 cannot be validated against real UI.

Promote to top: closes the foundation bug + restores baseline assumptions for the original 8 candidates. After this sprint, AD-Lighthouse-Visual-Hard-Gate becomes the natural follow-up (its precondition — reliable baselines — is met for the first time).

### 17.md / V2 紀律對齊

- **Cat 12 Observability**: design-system runtime validation IS in scope (frontend telemetry includes Web Vitals — LCP / CLS — both of which are affected by working CSS). Sprint 57.13 US-B4 wired `reportWebVitals()` but the metrics emitted so far are from unstyled rendering. Post-hotfix the baseline shifts.
- **Frontend Foundation 1/N (Sprint 57.13)**: marked "COMPLETE" in CLAUDE.md. After this hotfix, mark as **really complete** (the design-system US-B3 deliverable is now actually running). Update Sprint 57.13 retrospective.md with a 2026-05-15 cross-reference + this sprint's PR link.
- **Sprint 57.5 Reality Check methodology**: extend the "dual scoring" template — add "computed-style spot-check" to the runtime score column (currently the runtime score relies on functional e2e + a11y + visual; this sprint proves all three can simultaneously pass on broken-CSS). One row in `claudedocs/1-planning/v2-reality-check-template.md` if it exists; otherwise note in retrospective.

## User Stories

### Group A — Tailwind v4 directive fix

- **US-A1**: As a developer, I want `frontend/src/index.css` to use Tailwind v4 syntax so the PostCSS plugin actually emits utility classes.
  - AC1: `@tailwind base;` / `@tailwind components;` / `@tailwind utilities;` replaced with `@import "tailwindcss";` + `@config "../tailwind.config.ts";`
  - AC2: `npm run build` succeeds + `dist/assets/index-*.css` size **> 40 kB** (was ~14 kB pre-fix)
  - AC3: grep `frontend/src/**/*.css` for any other `@tailwind` directive → 0 remaining
  - AC4: Vite dev server (`npm run dev`) restarts cleanly + browser DevTools shows `.flex` / `.p-8` / `.bg-primary` etc. as defined rules in computed CSS
  - AC5: MHist +1 line in `index.css` per `.claude/rules/file-header-convention.md` budget (≤ 100 chars effective)

### Group B — Validation sweep

- **US-B1**: As a developer, I want full e2e + a11y + visual confidence post-fix.
  - AC1: `npm run e2e` baseline 40 pass / 7 skip / 0 fail → post-fix expectation: **40 pass / 7 skip / 0 fail** (or note any regressions)
  - AC2: `approval-card.spec.ts` CRITICAL→`#b71c1c` colour-literal sentinel: investigate computed-style behaviour. If pre-fix this passed by accident (UA default colour happened to be `rgb(0,0,0)` not asserting strict `#b71c1c`), post-fix it should pass strict assertion. Document the delta in retro Q3.
  - AC3: `npm run e2e -- a11y/a11y-scan.spec.ts` (9 gated + auth pages full axe per 57.16) → expect **0 new violations**. Compare to 57.16 baseline (4 moderate/minor on `/chat-v2`): observe whether structural landmark issues decrease (proper AppShellV2 styling may resolve `landmark-no-duplicate-main` etc.).
  - AC4: `npm run e2e -- visual-regression.spec.ts` → expect **6/6 FAIL** (pre-fix baselines were captured on unstyled HTML). This is the trigger for US-B2.

- **US-B2**: As a developer, I want fresh visual-regression baselines that capture the real shadcn UI.
  - AC1: `gh workflow run visual-baseline` (the 57.14 PR-not-push pattern) → produces a PR with 6 regenerated PNGs from Linux runner
  - AC2: Manual review of the 6 PNGs: AppShellV2 sidebar visible / shadcn rounded buttons / Card surfaces / proper `font-sans` (not UA Times-Roman) / proper colour tokens (slate base per `components.json`)
  - AC3: Merge the regenerated baseline PR into 57.17 feature branch BEFORE the hotfix PR
  - AC4: Re-run `npm run e2e -- visual-regression.spec.ts` against the new baselines → 6/6 pass

### Group C — Closeout

- **US-C1**: As a maintainer, I want full closeout discipline (retro + memory + doc syncs + PR).
  - AC1: `retrospective.md` Q1-Q7 with at least Q3 detailing the dead-directive root cause investigation + Q4 listing follow-up ADs
  - AC2: `memory/project_phase57_17_tailwind_v4_hotfix.md` + `MEMORY.md` index +1 line
  - AC3: Doc syncs in-sprint: `16-frontend-design.md` timeline / `sprint-workflow.md` calibration matrix +1 row (NEW `frontend-css-engine-hotfix` class, 0.60 mid-band) / `STYLE.md §2` if token coverage observation worth recording / `CONVENTION.md §10` if Tailwind v4 directive guidance worth adding
  - AC4: Doc syncs deferred post-merge: CLAUDE.md (Phase 12/N → 14/N + Latest/Prev Sprint + main HEAD + Next Phase 候選 + footer) / SITUATION-V2-SESSION-START.md (§第八部分 carryover update)
  - AC5: PR open + CI green + merge → `chore/closeout-57-17` follow-up PR for CLAUDE.md/SITUATION sync

## Technical Specifications

### Tailwind v4 directive migration (US-A1)

Tailwind v4 reference: https://tailwindcss.com/docs/upgrade-guide

Mandatory changes to `frontend/src/index.css`:

```css
// BEFORE (lines 6-8):
@tailwind base;
@tailwind components;
@tailwind utilities;

// AFTER (lines 6-7):
@import "tailwindcss";
@config "../tailwind.config.ts";
```

Why preserve `tailwind.config.ts`:

- `tailwind.config.ts` has 52 lines of shadcn CSS variable bridge mapping (`border: hsl(var(--border))` etc.) + `darkMode: "class"` + `borderRadius` extensions.
- Migrating to v4-idiomatic `@theme inline {}` block requires re-expressing every mapping in CSS-only syntax + handling the `darkMode: "class"` via `@variant dark (&:is(.dark *))` in CSS.
- Out of scope: separate sprint **AD-Tailwind-v4-Config-Migration** (logged in deferred OUT list).
- `@config` directive is the official v4 escape hatch for legacy v3 configs. Documented in https://tailwindcss.com/docs/upgrade-guide#using-a-javascript-config-file.

Verify post-fix:

```bash
cd frontend && npm run build
ls -lh dist/assets/index-*.css   # expect > 40 kB (was ~14 kB pre-fix)
grep -r "@tailwind" src/         # expect 0 matches
```

### Visual baseline regeneration approach (US-B2)

Use the Sprint 57.14 `visual-baseline.yml` workflow_dispatch path. Sprint 57.14 already validated:

- Linux-runner-only (the spec has `existsSync && platform==="linux"` guard per FIX-008)
- PR-not-push (FIX-008 — opens a PR with the 6 regenerated PNGs instead of pushing directly to protected `main`)
- `frontend/tests/e2e/visual/__screenshots__/*.png` — 6 baselines:
  - `app-shell.png`
  - `auth-login.png`
  - `verification-recent.png`
  - `cost-dashboard.png`
  - `governance.png`
  - `admin-tenants.png`

Procedure:

```bash
gh workflow run visual-baseline.yml --ref feature/sprint-57-17-tailwind-v4-hotfix
gh run list --workflow=visual-baseline.yml --limit 1
# wait for completion, the workflow opens a PR like "chore(visual-baseline): regenerate 6 PNGs (sprint-57-17)"
gh pr view <pr-number>
gh pr merge <pr-number> --merge --auto    # merges into the feature branch, NOT main
```

After the baseline PR merges:

```bash
git pull origin feature/sprint-57-17-tailwind-v4-hotfix
npm run e2e -- visual-regression.spec.ts    # expect 6/6 pass
```

### e2e regression risk analysis (US-B1)

Pre-fix passing state breakdown:

| Spec | Why it passed pre-fix |
|------|----------------------|
| `chat-v2/*.spec.ts` (10 specs) | DOM-driven assertions: `getByRole('button', { name: '...' })`, `getByText(...)`, `expect(locator).toBeVisible()` — `toBeVisible` only checks `visibility:visible` / `display: !==none`, not `opacity` or computed colour |
| `governance/*.spec.ts` | TanStack 4-page navigation: route+queryString assertions, not visual |
| `cost-dashboard.spec.ts` / `sla-dashboard.spec.ts` / `verification.spec.ts` / `memory.spec.ts` / `loop-debug.spec.ts` / `tenants.spec.ts` / `tenant-settings.spec.ts` | Same DOM-only pattern |
| `approval-card.spec.ts` CRITICAL→`#b71c1c` sentinel | **UNCERTAIN** — may have passed via UA `rgb(0,0,0)` luck, or via `text-[#hex]` partial-rule emission, or via inline `style=` fallback. **Investigate in Day 1 via DevTools computed-style inspection BEFORE the fix; document, then re-verify post-fix.** |
| `a11y-scan.spec.ts` (9 routes + 2 auth) | axe-core requires explicit colour assertions to flag `color-contrast`. UA defaults (black-on-white) trivially pass 21:1 contrast. The 4 moderate/minor `/chat-v2` violations are landmark-structure related (NOT colour). |
| `visual-regression.spec.ts` (6 baselines) | Pixel-match against PNGs captured AT the dead-directive state. They match because both render-time and baseline-time produce identical unstyled HTML. |

Expected post-fix delta:

- `chat-v2/*`: **no change expected**, but check that `approval-card` colour sentinel resolves cleanly.
- `governance/*`: **no change expected**.
- `cost-dashboard` / `sla-dashboard` / `verification` / `memory` / `loop-debug` / `tenants` / `tenant-settings`: **no change expected**.
- `a11y-scan`: violations should **decrease or stay same** (working AppShellV2 + sidebar styling may resolve landmark structural issues; will NOT introduce new colour violations because shadcn slate base is AA-compliant by design).
- `visual-regression`: **6/6 FAIL** initially → regenerate via workflow_dispatch (US-B2) → **6/6 pass** post-regeneration.

### Calibration class

NEW scope class: **`frontend-css-engine-hotfix`** — single-line CSS config change + full-blast-radius validation. Mid-band 0.60. 1st application baseline opens this sprint.

Distinct from existing classes:

- Not `frontend-refactor-mechanical` (0.80 for 3rd+ app per AD-Sprint-Plan-13) — this is NOT mechanical refactoring; it's a config-syntax migration that affects 100% of frontend rendering.
- Not `audit-cycle / docs / template` (0.40) — has runtime impact, not just docs.
- Not `mixed` (0.60 mid-band) — pure single-domain config change, not greenfield mix.
- Not `frontend-feature-with-migration` (0.50) — no feature work.

If recurs (e.g. AD-Tailwind-v4-Config-Migration becomes the 2nd `frontend-css-engine-hotfix` data point), evaluate matrix lift per the 3-sprint moving evidence rule.

Bottom-up estimate per US:

| US | Bottom-up | Notes |
|----|-----------|-------|
| US-A1 | ~1.5 hr | 1-line edit + build verify + MHist + branch + Day-0 三-prong overhead |
| US-B1 | ~3.5 hr | Full e2e suite re-run (~15 min) + investigate approval-card sentinel via DevTools + a11y re-run + visual-regression confirmation of fail + screenshot 11 routes manually |
| US-B2 | ~2 hr | Workflow_dispatch + wait for runner + PR review + merge to feature branch + re-run visual-regression |
| US-C1 | ~3 hr | retrospective Q1-Q7 + memory snapshot + 3 in-sprint doc syncs + open PR + smoke CI |

Bottom-up total: ~10 hr. Calibrated commit @ 0.60: **~6 hr** (Day 0 + 1 + 2 + 3 days, ~1.5 hr/day average).

## File Change List

### MODIFIED Frontend — src (1 file, ~2 lines net)

- `frontend/src/index.css:6-8` — replace v3 directives with v4 `@import` + `@config` + MHist +1 line

### MODIFIED Frontend — visual baselines (6 PNG)

- `frontend/tests/e2e/visual/__screenshots__/app-shell-{linux,win32}.png`
- `frontend/tests/e2e/visual/__screenshots__/auth-login-{linux,win32}.png`
- `frontend/tests/e2e/visual/__screenshots__/verification-recent-{linux,win32}.png`
- `frontend/tests/e2e/visual/__screenshots__/cost-dashboard-{linux,win32}.png`
- `frontend/tests/e2e/visual/__screenshots__/governance-{linux,win32}.png`
- `frontend/tests/e2e/visual/__screenshots__/admin-tenants-{linux,win32}.png`

(Per FIX-008: only `-linux.png` regenerated via the workflow; `-win32` baselines are platform-gated by the spec.)

### NOT touched (intentional scope hold)

- `frontend/tailwind.config.ts` — preserved via `@config` directive (full v4 migration deferred to AD-Tailwind-v4-Config-Migration)
- `frontend/postcss.config.cjs` — already correct (v4 plugin)
- `frontend/vite.config.ts` — may need header comment update if it references Tailwind v3 (verify in Day 0 三-prong)
- `frontend/package.json` — versions are correct
- `STYLE.md §2` token table — observation only this sprint (full audit = AD-Style-Token-Config-Audit follow-up)
- `eslint.config.js` — no changes (no-restricted-syntax guard from 57.15 still applies)
- `backend/**` — 0 changes

### Doc syncs (in-sprint)

- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` — Sprint Timeline row +1 (57.17)
- `.claude/rules/sprint-workflow.md` — Calibration matrix +1 row (`frontend-css-engine-hotfix` 0.60 1st app)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-13/retrospective.md` — cross-reference note (Frontend Foundation 1/N is **now actually running**)
- `STYLE.md §2` — observation note (post-fix token visibility)
- `frontend/CONVENTION.md §10` — Tailwind v4 directive guidance (if not already documented)

### Doc syncs (deferred post-merge)

- `CLAUDE.md` (Phase 12/N → 14/N + Latest/Prev Sprint + main HEAD + Next Phase 候選 row + footer)
- `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` (§第八部分 carryover update + new "session-start sanity check: open http://localhost:3007/ before reporting frontend state" warning)

## Acceptance Criteria

### Functional

- [ ] `frontend/src/index.css` uses v4 syntax + builds without warnings
- [ ] `dist/assets/index-*.css` > 40 kB (was ~14 kB pre-fix)
- [ ] All 9 gated routes + `/auth/login` render shadcn-styled (AppShellV2 sidebar visible / rounded buttons / `font-sans` applied / Card surfaces visible)
- [ ] `npm run e2e`: 40 pass / 7 skip / 0 fail (post-baseline regen)
- [ ] `npm run e2e -- a11y/a11y-scan.spec.ts`: 0 NEW violations vs 57.16 baseline
- [ ] `npm run e2e -- visual-regression.spec.ts`: 6/6 pass (post-baseline regen)

### Non-functional

- [ ] Bundle size delta documented (compiled CSS expected ~50-80 kB; main JS ~flat)
- [ ] 11 manual route screenshots captured in `claudedocs/4-changes/feature-changes/CHANGE-XXX-tailwind-v4-hotfix.md` (or attached to PR description) — visual proof
- [ ] Retrospective Q3 documents the `approval-card` colour sentinel pre/post-fix behaviour

### Sprint workflow discipline

- [ ] Plan file exists before any code change (this file)
- [ ] Checklist file exists before Day 1 code
- [ ] Day 0 三-prong (path + content + N/A schema) drift findings catalogued
- [ ] Per-day progress.md entries
- [ ] Day 3 retrospective Q1-Q7 complete
- [ ] No deletion of unchecked `[ ]` items (only `[ ]→[x]` or `🚧` annotation)

### V2 紀律 9 項 self-check (each commit + PR)

- [ ] AP-1 (Pipeline-vs-Loop): N/A (frontend config change)
- [ ] AP-2 (Side-track code): N/A (single-file change)
- [ ] AP-3 (Cross-directory scattering): N/A
- [ ] AP-4 (Potemkin Features): **PASSED** — this sprint CLOSES a Potemkin (Sprint 57.7-57.16 design system shipped but never ran)
- [ ] AP-5 (PoC accumulation): N/A
- [ ] AP-6 (Hybrid Bridge Debt): N/A
- [ ] AP-7 (Context Rot): N/A
- [ ] AP-8 (No Centralized PromptBuilder): N/A
- [ ] AP-9 (No Verification Loop): N/A
- [ ] AP-10 (Mock-vs-Real Divergence): **PASSED** — closes a divergence (e2e mocks passed on broken-CSS; real browser observation revealed truth)
- [ ] AP-11 (Naming version suffix): N/A

## Deliverables (checklist mapping)

- [ ] **Group A (US-A1)** — `index.css` v4 syntax migration
- [ ] **Group B (US-B1)** — full e2e + a11y + visual-regression validation sweep (pre-baseline-regen)
- [ ] **Group B (US-B2)** — visual baseline regeneration via 57.14 workflow_dispatch + merge to feature branch
- [ ] **Group C (US-C1)** — retrospective + memory + in-sprint doc syncs + PR
- [ ] **Deferred post-merge** — CLAUDE.md + SITUATION sync via `chore/closeout-57-17` PR

## Dependencies & Risks

### External dependencies

- **Tailwind v4 `@config` directive**: documented at https://tailwindcss.com/docs/upgrade-guide#using-a-javascript-config-file. Stable since v4.0.0 (released 2025). Project is on v4.2.4. No version bump needed.
- **57.14 `visual-baseline.yml` workflow**: already validated via Sprint 57.14 dispatch run `25644392922` (0 changes that run, but mechanism works). FIX-008 PR-not-push pattern proven.
- **`@tailwindcss/postcss` v4.2.4**: matches `tailwindcss` v4.2.4. No upgrade needed.

### Risk matrix

| Risk | Severity | Mitigation |
|------|----------|------------|
| `@config` directive doesn't load `tailwind.config.ts` correctly (path resolution from `src/index.css` → `../tailwind.config.ts`) | Medium | Verify in Day 1 via `npm run build` output + DevTools rule inspection. If broken → fall back to inlining the config as `@theme inline {...}` block in `index.css` (closer to AD-Tailwind-v4-Config-Migration scope; logs follow-up) |
| `darkMode: "class"` strategy not honoured by `@config` (v4 has different dark-mode wiring) | Medium | Test by toggling `html.dark` via DevTools. If broken → add `@variant dark (&:is(.dark *))` after `@import` |
| 6 visual baselines regenerate to "wrong" styled state (e.g. some routes missing the AuthBootstrap suspense fallback) | Low | Manual review the workflow PR before merging (US-B2 AC2). Reject if any route looks visually wrong |
| `approval-card.spec.ts` CRITICAL→`#b71c1c` sentinel breaks post-fix (assertion was passing by coincidence pre-fix) | Medium | Investigate Day 1 via DevTools; if regression, fix the consuming component (NOT the spec); commit fix in same PR |
| Bundle size jumps so much it triggers `frontend-lighthouse.yml` perf budget | Low | Expected delta: +~40-70 kB compiled CSS. Lighthouse perf budget is per-bundle; CSS is a separate budget. If breached → split design-system CSS into a deferred-load chunk |
| 9 ship sprints' worth of inline-style cleanup (57.15+57.16) becomes visible as unnecessary churn | Negligible | Those sprints DID improve compliance with the no-restricted-syntax guard — value preserved even though visual impact was hidden pre-fix |

### Day 0 三-prong drift findings (added <DATE> — per sprint-workflow.md §Step 2.5; full catalog in progress.md Day 0)

**To be filled in Day 0 of execution.** Expected categories:

- **Prong 1 (path verify)**: every file in §File Change List exists/doesn't-exist as expected
- **Prong 2 (content verify)**: every Background claim (`@tailwindcss/postcss^4.2.4` / `tailwind.config.ts` content / etc.) grep-verified against actual repo state
- **Prong 3 (schema verify)**: N/A (no DB schema changes)

### Roll-back plan

If `@config` directive doesn't work + `@theme inline` fallback also fails:

1. `git revert <hotfix-commit>` to restore the v3 directives
2. Frontend goes back to unstyled rendering (current Sprint 57.16 main state)
3. File `AD-Tailwind-v4-Full-Migration` as a 1-week sprint replacement
4. e2e baseline (40/7/0) unaffected by revert
5. Production deploy gate (deploy-production.yml is DISABLED per AD-CI-6) unaffected

## Workload (calibrated)

### Bottom-up estimate by US

| US | Bottom-up | Why |
|----|-----------|-----|
| US-A1 | ~1.5 hr | 1-line edit + build verify + grep verify + MHist + Day 0 三-prong overhead |
| US-B1 | ~3.5 hr | Full e2e re-run (~15 min wall + investigation) + a11y re-run + visual-regression confirm fail + manual screenshot 11 routes + investigate approval-card sentinel |
| US-B2 | ~2 hr | Workflow_dispatch (~10 min) + wait for runner + PR review + merge + re-run visual-regression |
| US-C1 | ~3 hr | retrospective + memory + 3 in-sprint doc syncs + open PR + smoke CI + handle CI feedback |

**Bottom-up total: ~10 hr**

### Calibrated commit

Bottom-up est ~10 hr → calibrated commit ~6 hr (multiplier 0.60 — NEW class `frontend-css-engine-hotfix` 1st application, mid-band)

Day distribution:
- Day 0: ~1.5 hr (US-A1 partial + 三-prong + plan/checklist + branch)
- Day 1: ~2 hr (US-A1 completion + US-B1 start)
- Day 2: ~1.5 hr (US-B2 baseline regen + US-B1 completion)
- Day 3: ~1 hr (US-C1 closeout)

## Open questions for user

1. **Calibration class name** — propose `frontend-css-engine-hotfix` (NEW, 0.60 mid-band, 1st app). Alternatives: `mixed` (0.60, same multiplier but loses class specificity) / `frontend-refactor-mechanical` (0.80, but this isn't a mechanical refactor). Confirm class name or propose better.

2. **`@config` vs `@theme inline`** — Plan defaults to `@config "../tailwind.config.ts"` (minimal blast radius, preserves the 52-line config file). Full v4 migration to `@theme inline` is deferred. Confirm or override to do full migration now (+ ~4 hr scope).

3. **Visual baseline regeneration timing** — Plan opens a sub-PR (57.14 pattern) from the feature branch. Alternative: regenerate locally on Linux WSL2 + commit directly (faster but loses the CI-verified clean-runner baseline). Confirm.

4. **`approval-card.spec.ts` CRITICAL→`#b71c1c` sentinel** — Plan investigates pre-fix vs post-fix behaviour and documents in retro. If the sentinel was passing by accident pre-fix and breaks post-fix, the fix lives in the consuming component, not the spec. Confirm this contract.

5. **PR scope** — Plan opens 1 hotfix PR + 1 baseline-regen PR (merges into feature branch first) + 1 chore/closeout PR (post-merge). Confirm this triple-PR pattern or collapse.
