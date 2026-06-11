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
- **Before-baseline sweep** — 22 routes captured 1440×900 → `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/artifacts/mockup-fidelity-foundation/screenshots/before/` (22 PNGs; all ✓).
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
- Day 1 commit: `2d6745b9` (22 files; +1300 / -219; styles-mockup.css NEW 1123 lines).

---

## Day 2 — 2026-05-22 — Group C theme toggle (US-C2) — mockup `[data-theme]` drive

### Today's Accomplishments

- **§2.1 Layer 4** — confirmed already done Day 1 §1.3 (D-DAY1-1 atomic resequencing); no Day 2 work.
- **US-C2 theme toggle** — `ThemeProvider.tsx` reworked: `applyHtmlClass` → `applyHtmlTheme` now sets the mockup `<html data-theme>` attribute (`dark`↔`light`) AND keeps the shadcn `.dark` class in sync. The dual-mechanism is the deliberate Phase 1 transition state — the 13 not-yet-re-pointed pages still consume `index.css` shadcn `:root`/`.dark` tokens; Phase 2 drops the `.dark` line as pages re-point off shadcn. Public API (`theme`/`toggleTheme`/`setTheme`/`useTheme`) unchanged — 0 consumer edits.
- **Theme = light + dark both kept** (D-PRE-1 / plan §Risks R3 — mockup `styles.css` has a full light theme `[data-theme="light"]` ×4 variants, L113-165). The §Technical Specifications "dark-only" premise was wrong; checklist §2.2 task text corrected per sprint-workflow §Step 2.5 (plan R3 row = audit trail; §Technical Specifications NOT silently rewritten).
- **Test strengthened (not deleted)** — `AuthShell.test.tsx` `ThemeProvider` test + `data-theme` attribute assertions (dark default + light after toggle) + `beforeEach`/`afterEach` `data-theme` cleanup; docstring §3 + MHist updated. Verifies the US-C2 core deliverable durably.
- **Quality gates** — `npm run lint` clean (`--max-warnings 0`); `npm run build` green (3.26s; main 337.06 kB, +0.05 kB vs Day 1 — negligible); Vitest **457/457 pass** (0 regression; AuthShell 4/4 with the new assertions).
- **Runtime spot-check** — `route-sweep.mjs after` 22/22 routes ✓ (0 ✗ crash). Read-verified `/overview` + `/cost-dashboard` + `/auth/login` — all render correctly dark with the verbatim foundation (sidebar + topbar + widgets / Cost Ledger charts + tables / AuthShell centered card all coherent). `screenshots/after/` refreshed (Day 3 re-runs fresh).

### Drift findings (Day 2)

- None new. (The D-PRE-1 / R3 theme-has-light finding was caught Day 0; resolved this day.)

### Decisions taken

- Theme toggle drives BOTH `data-theme` (mockup mechanism) + `.dark` (shadcn transition) — deliberate Phase 1 dual-mechanism; Phase 2 removes the `.dark` toggle.
- `index.html` unchanged — already carries `data-theme="dark" data-variant="linear"` from Day 1 §1.3.
- Playwright MCP browser stuck (known issue — `route-sweep.mjs` header AD #37) → used the standalone `route-sweep.mjs` harness for the runtime spot-check.

### Remaining for next day (Day 3 — CI guards + 22-route sweep)

- US-D1: `check-mockup-fidelity.mjs` (diff guard + grep guard) + `package.json` script + frontend CI workflow step.
- US-D2: fresh after-switch 22-route sweep + before/after + vs-mockup matrix in FOUNDATION-SWITCH-REPORT.
- US-D3: triage — catastrophic fix in-sprint / transition drift catalogue / structural → carryover AD.

### Notes

- Workload Day 2 est ~2.2 hr calibrated — actual well under (Layer 4 was pre-done Day 1; Day 2 = theme wire only — a small, well-scoped change).
- Day 2 commit: `a530187c` (4 files; +92 / -30; screenshots/ kept local). This hash-record line lands with the Day 3 commit.

---

## Day 3 — 2026-05-22 — Group D (CI guards + 22-route regression sweep + triage)

### Today's Accomplishments

- **US-D1 CI guards** — NEW `frontend/scripts/check-mockup-fidelity.mjs`; `package.json` `+1` script `check:mockup-fidelity`; `.github/workflows/frontend-ci.yml` `+1` step `Mockup-fidelity guard` after the ESLint step (in approved plan scope — additive guard).
  - **diff guard** — `styles-mockup.css` vs `reference/design-mockups/styles.css`, line-ending normalised → byte-identical ✓
  - **grep guard** — no NEW hardcoded `#hex`/`oklch()` in `src/features/**`+`src/pages/**`; comment lines skipped; `HEX_OKLCH_BASELINE = 18` (governance + chat_v2 risk-colour maps — DecisionModal 5 / AuditChainBadge 1 / ApprovalList 4 / ApprovalCard 4 / HITLTurn 4); hard-fails only above baseline. `pages/` = 0 offenders.
  - `npm run check:mockup-fidelity` exits 0 ✓
- **US-D2 after-switch sweep** — `route-sweep.mjs after` 22/22 routes captured ✓ (0 harness `✗`). FOUNDATION-SWITCH-REPORT §3 before/after matrix populated (all 22 after/ PNGs read; 5 before/ PNGs opened for direct comparison).
- **US-D3 triage** (report §3a):
  - **0 catastrophic** breakage from the switch — no route that rendered before is broken after.
  - **0 structural regression** from the switch — no `AD-Foundation-Switch-Regression-*`.
  - **19 routes 🟡 transition-drift** — every renderable route loads the verbatim foundation; colour fidelity improved, spacing/layout shifts on not-yet-re-pointed pages (Phase-2 re-point backlog).
  - **3 routes ⚪ not-assessable** (`/subagents` `/memory` `/verification`) — AppErrorBoundary `undefined.length` IDENTICALLY in before/ + after/ → pre-existing route-sweep harness mock-shape gap (generic `[]` mock vs object-shaped data hooks; same D-DAY1-1 class as cost/sla). A CSS-only switch cannot cause a JS `.length` error → NOT a regression.

### Drift findings (Day 3)

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| D-DAY3-1 | 🟢 | grep guard found 0 hardcoded hex/oklch in `pages/` but 18 lines in `features/` (governance + chat_v2 risk-colour maps still use `bg-[#hex]`/`text-[#hex]` literals, not mockup `--risk-*` tokens). | Captured as `HEX_OKLCH_BASELINE = 18`; the guard absorbs them as Phase-2 backlog, hard-fails only on NEW offenders. |
| D-DAY3-2 | 🟢 | `/subagents` `/memory` `/verification` error identically in before/ + after/ — route-sweep generic `[]` mock incompatible with their object-shaped data hooks. | NEW `AD-RouteSweep-Object-Mock-Gap` (harness maintenance — report §3b). Not a switch regression; not fixed this sprint (out of foundation-switch scope; needs data-shape investigation). |

### Decisions taken

- grep guard skips comment lines (trimmed start `*`/`//`/`/*`) → the 3 comment-only hex/oklch mentions (HITLQueueCard docstring, 2 MHist `#666`) are NOT counted; baseline 18 = real offenders only.
- vs-mockup per-route pixel comparison deferred to Phase-2 re-point sprints (Option B — no markup re-pointed; report §3c). Day 3 matrix = before/after regression detection (the actual Day 3 purpose).
- route-sweep harness NOT extended for subagents/memory/verification object mocks this sprint — out of foundation-switch scope; logged as `AD-RouteSweep-Object-Mock-Gap`.

### Remaining for next day (Day 4 — Vitest + closeout)

- US-E1: Vitest 457/457 re-confirm + lint + build + bundle KB delta.
- US-E2: FOUNDATION-SWITCH-REPORT §5 final verdict; retrospective Q1-Q7 + calibration 1st-data-point; memory snapshot + MEMORY.md +1; sprint-workflow.md calibration matrix +1 NEW class row; next-phase-candidates.md update (incl. `AD-RouteSweep-Object-Mock-Gap`); CLAUDE.md minimal touch; PR.

### Notes

- Workload Day 3 est ~1.7 hr calibrated — actual on track (CI guard authoring + sweep + 27-image triage read).
- Day 3 commit: `1865c15b` (6 files; +243 / -50; screenshots/ kept local). Hash-record line lands with the Day 4 commit.

---

## Day 4 — 2026-05-22 — Group E + closeout

### Today's Accomplishments

- **US-E1 quality gates** — `npm run lint` clean; `npm run build` green (3.54s; main JS 337.06 kB; CSS bundle `index-BLrq1zPz.css` 592 KB incl. verbatim `styles-mockup.css` ~39 KB raw — matches plan "~40 KB CSS"); Vitest **457/457 pass** (0 regression); `npm run check:mockup-fidelity` passes.
- **US-E1 Vitest spec adaptation** — `AuthShell.test.tsx` ThemeProvider test was strengthened with `data-theme` assertions on Day 2 §2.2 (the actual closeout adaptation). The other 3 D-PRE-6 specs (`AppShellV2`/`UserMenu`/`adminTenantsRoleGate`) use `<ThemeProvider>` only as a render wrapper — assert no retired token / light path → no change needed.
- **US-E2 closeout** —
  - FOUNDATION-SWITCH-REPORT §5 final verdict + Phase-2 epic backlog written.
  - retrospective.md Q1-Q7 created — Q2 calibration 1st data point.
  - memory snapshot `memory/project_phase57_28_mockup_fidelity_foundation.md` + MEMORY.md +1 quality pointer.
  - `.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row + MHist.
  - `next-phase-candidates.md` +Sprint 57.28 carryover section (#45 `AD-RouteSweep-Object-Mock-Gap` + #46 `AD-Mockup-Fidelity-HexBaseline-Migration`).
  - CLAUDE.md Current Sprint row + Last Updated footer (REFACTOR-001 minimal touch).

### Calibration — 1st data point, NEW `frontend-verbatim-css-foundation` 0.55 class

- Plan committed ~6.2 hr (0.55 × bottom-up ~11.0 hr).
- Actual ≈6.5 hr-equivalent (estimated — agent-assisted compressed session, not rigorously per-day-tracked; same caveat as Sprint 57.13/57.27). Day 1 over-ran (Layer 4 pulled in + 15-file un-translation vs ~10 estimate); Day 2 under-ran (theme wire only); Day 3+4 on-track.
- **Ratio actual/committed ≈1.05 ✅ in [0.85, 1.20] band.** Ratio actual/bottom-up ≈0.59.
- 1-data-point → KEEP 0.55 baseline per `When to adjust` 3-sprint window rule.

### Discipline self-check (rolling planning)

- ☑ No future sprint plan pre-written.
- ☑ No unchecked `[ ]` deleted — §2.2 + §3.2 task text corrected per §Step 2.5 (not deleted; plan R3 + report §3c are the audit trail); §4.3 PR/CI/merge items left `[ ]` (post-commit process).
- ☑ retrospective.md contains no concrete future-sprint tasks.

### Remaining (Day 4 §4.3)

- PR open → CI green → merge (after user approval — push / PR / merge require confirmation) → post-merge branch cleanup.

### Notes

- Workload Day 4 est ~0.6 hr calibrated — actual on track (gates + closeout docs).
- Day 4 closeout commit: `<hash>` (7 repo files: FOUNDATION-SWITCH-REPORT + retrospective.md NEW + progress.md + checklist + sprint-workflow.md + next-phase-candidates.md + CLAUDE.md; memory subfile + MEMORY.md live in the AI memory dir, not the repo; screenshots/ kept local).
