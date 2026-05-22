# Sprint 57.28 Progress — AD-Mockup-Fidelity-Foundation-Switch

**Class**: `frontend-verbatim-css-foundation` 0.55 (NEW; 1st application)
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-28-plan.md`
**Checklist**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-28-checklist.md`

---

## Day 0 — 2026-05-22 — Plan + Checklist + guidance-PR merge + 三-prong + before-baseline

### Today's Accomplishments

- **Plan + checklist drafted** (mirror Sprint 57.26 structure; 11 sections / Day 0-4) — user-approved 2026-05-22 incl. Option B scope decision (foundation-only; per-page re-point = Phase 2).
- **guidance PR #161 merged** — `chore/frontend-mockup-fidelity-guidance` (`19f31443`) → opened PR #161 → behind origin/main (PR #160 Sprint 57.27 merged in the interim) → merged `origin/main` into the branch (clean, 0 conflict — disjoint file sets) → all 8 CI checks green → squash-merged to main `d4461141`, remote branch deleted.
- **Feature branch cut** — `feature/sprint-57-28-mockup-fidelity-foundation` from updated main `d4461141`.
- **Day 0 三-prong** complete (Prong 1 path + Prong 2 content/collision-enumeration + Prong 4 test-selector) — see Drift findings below; 0 path drift, 6 D-PRE findings catalogued.
- **`route-sweep.mjs` re-pointed** — OUT_DIR `sprint-57-26-foundation-fidelity` → `sprint-57-28-mockup-fidelity-foundation` + header MHist (reused harness, minor tweak per plan).
- **Before-baseline sweep** — 22 routes captured 1440×900 → `claudedocs/4-changes/sprint-57-28-mockup-fidelity-foundation/screenshots/before/` (22 PNGs; all ✓).
- **FOUNDATION-SWITCH-REPORT skeleton** written — 4-layer summary + token-collision table (filled) + 22-route matrix skeleton + D-PRE catalogue.

### Drift findings (Day 0 三-prong — per sprint-workflow §Step 2.5)

| ID | Sev | Finding | Implication / cross-ref |
|----|-----|---------|-------------------------|
| D-PRE-1 | 🟠 | Mockup `styles.css` HAS a full light theme (`[data-theme="light"]` ×4 variants, L114-164). Plan US-C2 premise "mockup has no light design → dark-only" is WRONG (reports 02/03 imprecise). | Plan §Risks R3 updated. Revised US-C2: keep light; `ThemeProvider` toggles mockup `[data-theme]`. **Surfaced to user — confirm before Day 2.** Scope shift <20% (same US, corrected approach) → continue per Step 2.5. |
| D-PRE-2 | 🟠 | Mockup bg/fg/border/shadow/radius tokens are `[data-theme][data-variant]`-scoped, NOT `:root`. | Production `<html>` MUST carry `data-theme="dark" data-variant="linear"` for verbatim CSS to resolve. Day 1 sets static attrs on `index.html`; Day 2 wires toggle. |
| D-PRE-3 | 🟢 | Mockup `styles.css` uses 0 `rem` — fully px. | `html{font-size:13px}` hack KEPT through Phase 1 (plan R2 default confirmed). |
| D-PRE-4 | 🟢 | Token-collision set enumerated — ~28 collisions: 2 tricky (`--primary`/`--border` de-collide) + ~26 shared-intent/identical. | Day 2 Layer 4 resolution table ready — see FOUNDATION-SWITCH-REPORT §2. |
| D-PRE-5 | 🟢 | `--radius`/`--row-h`/`--pad`/`--gap` mockup values == production. | Retiring production's = 0 value change (safe). |
| D-PRE-6 | 🟢 | 4 Vitest files reference theme/token literals (`AuthShell`/`AppShellV2`/`UserMenu`/`adminTenantsRoleGate`). | Day 4 US-E1 adapt as needed (NOT delete). |

**Prong 1**: 0 path drift. `index.css`/`main.tsx`/`tailwind.config.ts`/`ThemeProvider.tsx` exist (edits); `styles-mockup.css` absent (create); `route-sweep.mjs` present (reuse); frontend CI = `.github/workflows/frontend-ci.yml`.
**PoC reference**: `investigation/mockup-fidelity-poc` confirmed — `main.tsx` imports `./styles-mockup.css` after `./index.css`.

### Decisions taken

- `html{font-size:13px}` → **KEEP** through Phase 1 (D-PRE-3 — mockup px-only; transition-safe for the 13 not-re-pointed pages).
- Theme → **revised** from "dark-only" to "keep light + `ThemeProvider` toggles `[data-theme]`" (D-PRE-1). Pending user confirmation before Day 2.

### Remaining for next day (Day 1 — Group B Layer 2 + Layer 3)

- US-B1 Layer 2: `cp styles.css → styles-mockup.css`; `main.tsx` import; `diff` byte-identical; add `data-theme="dark" data-variant="linear"` to `index.html` (D-PRE-2 prerequisite for spot-check).
- US-B2 Layer 3: `index.css` retire mockup-system HSL approximations; keep `html{font-size:13px}`; body block.

### Notes

- Workload Day 0 est ~0.6 hr (calibrated) — actual ~ on track (guidance PR merge + 三-prong + sweep).
- Day 0 commit: `af546fc4` (5 files; screenshots/ kept local). Day 0 三-prong + sweep ~on track.

---

## Day 1 — 2026-05-22 — Group B+C (Layer 2 + 3 + 4 + theme confirm) — atomic CSS foundation switch

### Today's Accomplishments

- **Theme decision confirmed by user**: light + dark BOTH retained (mockup has both — D-PRE-1). `ThemeProvider` `[data-theme]` toggle wiring = Day 2.
- **Layer 2** — `frontend/src/styles-mockup.css` = byte-identical copy of `reference/design-mockups/styles.css` (1123 lines; `diff` empty); `main.tsx` imports it after `index.css` (PoC-confirmed order) + MHist.
- **Layer 3** — `index.css` rewritten (170→~95 lines): retired the Sprint 57.18/57.20 mockup-system HSL approximations (`--bg`/`--fg`/`--success`/.../`--risk-*`/density/`--radius`/`--shadow`); kept the shadcn-system set; removed the dead `body` block (styles-mockup.css's unlayered `body` fully supersedes it); kept `html{font-size:13px}` (D-PRE-3).
- **Layer 4** — `tailwind.config.ts` bridge rework: mockup tokens `hsl(var(--X))`→`var(--X)` (var holds full oklch); shadcn `--primary`/`--border` de-collided → `--sc-primary`/`--sc-border` (index.css + config + `* { border-color }`).
- **index.html** — `<html>` gains `data-theme="dark"` (D-PRE-2 — required for `styles-mockup.css` `[data-theme][data-variant]` bg/fg tokens to resolve); `class="dark"` + `data-variant="linear"` + `data-density` kept.
- **D-DAY1-2 un-translation** (user-approved Option X 2026-05-22) — 15 files / ~35 occurrences `hsl(var(--mockup-token))` → `var(--X)`; 2 alpha cases → mockup `--primary-soft`/`--primary-soft-2`. Sweep confirms cost-dashboard charts + auth backdrops restored.
- **Quality gates**: `npm run build` green (3.52s; main 337.01 kB); `npm run lint` clean (`--max-warnings 0`); Vitest **457/457 pass** (94 files; 0 regression — 457 is the post-57.27 baseline).

### Drift findings (Day 1)

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| D-DAY1-1 | 🟢 | Layer 2 + 3 + 4 are **atomic** — done separately the mid-state produces `hsl(oklch())` invalid CSS app-wide. The plan's Day 1=Layer 2+3 / Day 2=Layer 4 split is not a checkable boundary. | Resequenced: Layer 2+3+4 landed together as the Day 1 session. No scope change (Layer 4 was already in-sprint). Day 2 now = theme toggle only. |
| D-DAY1-2 | 🟠 | 15 files / ~35 occurrences directly consume `hsl(var(--mockup-token))` (the translation anti-pattern). After the switch `--primary`/etc. are oklch → `hsl(oklch())` invalid → cost/sla/overview charts blank + all 7 /auth/* backdrops flat-black (screenshot-confirmed). Initial Day-0 estimate (~10 files) was low — first grep was `head`-truncated. | User chose Option X (in-sprint fix) via AskUserQuestion. Un-translated `hsl(var(--X))`→`var(--X)` (mockup tokens are complete oklch colours). `CostBurnChart`/`ErrorTrendChart` used bare `var(--X)` already → became correct automatically. |

### Decisions taken

- Theme: light + dark both kept (user-confirmed 2026-05-22).
- D-DAY1-2: in-sprint fix (Option X) — un-translation is the sprint's core purpose, not Phase-2 page re-point; avoids shipping ~5 broken parity routes + a visual-regression CI failure.

### Remaining for next day (Day 2 — theme toggle)

- US-C2: `ThemeProvider` wire to toggle the mockup `[data-theme]` attribute (dark↔light) instead of the shadcn `.dark` class; both themes functional. (Day 3 = CI guards + 22-route sweep; Day 4 = Vitest re-confirm + closeout.)

### Notes

- D-DAY1-1 resequencing means "Day 1" absorbed plan-Day-2's Layer 4. Day labels flex; checklist tracks tasks.
- Day 1 commit: `<hash>` (recorded post-commit).
