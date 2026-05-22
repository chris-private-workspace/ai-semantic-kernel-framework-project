# Sprint 57.28 Retrospective — AD-Mockup-Fidelity-Foundation-Switch

**Sprint**: 57.28 — verbatim-CSS 4-layer sync protocol, Phase 1 (foundation only)
**Class**: `frontend-verbatim-css-foundation` 0.55 (NEW class; 1st application)
**Closed**: 2026-05-22
**Branch**: `feature/sprint-57-28-mockup-fidelity-foundation` (5 commits from main `d4461141`)
**Outcome**: ✅ verbatim-CSS foundation switched; 22-route sweep — 0 catastrophic / 0 structural regression

---

## Q1 — What was delivered

The production frontend's CSS delivery switched from the lossy "translate mockup CSS into Tailwind/shadcn" pipeline (the verified root cause of the Sprint 57.18-57.27 10-sprint mockup drift) to the **verbatim-CSS 4-layer sync protocol**:

| Layer | Change |
|-------|--------|
| **2** | NEW `frontend/src/styles-mockup.css` = byte-identical copy of `reference/design-mockups/styles.css` (1123 lines); imported in `main.tsx` after `index.css` |
| **3** | `index.css` slimmed 170→~95 lines — retired the Sprint 57.18/57.20 HSL mockup-token approximations; kept the shadcn-system set + `html{font-size:13px}` (D-PRE-3 mockup px-only) |
| **4** | `tailwind.config.ts` bridge rework — mockup tokens `hsl(var(--X))`→`var(--X)` (oklch); shadcn `--primary`/`--border` de-collided → `--sc-*` |
| theme | `ThemeProvider` drives the mockup `[data-theme]` attribute (light+dark both kept — D-PRE-1); `.dark` class kept in sync for the Phase-1 shadcn transition |
| CI guard | NEW `check-mockup-fidelity.mjs` (diff + grep guard) + `package.json` script + `frontend-ci.yml` step |

- **D-DAY1-2 un-translation** — 15 files / ~35 `hsl(var(--mockup-token))` → `var(--X)` occurrences (user-approved Option X).
- 22-route before/after regression sweep: **0 catastrophic, 0 structural regression** from the switch (FOUNDATION-SWITCH-REPORT §3).
- Vitest **457/457** (0 regression — `AuthShell.test.tsx` ThemeProvider test strengthened with `data-theme` assertions); lint clean; build green; 0 backend changes; 0 LLM SDK leak.

## Q2 — Calibration (1st `frontend-verbatim-css-foundation` data point)

- **Plan §Workload**: bottom-up ~11.0 hr → calibrated commit ~6.2 hr (multiplier 0.55).
- **Actual**: ≈ 6.5 hr-equivalent (estimated — agent-assisted compressed session, not rigorously per-day hour-tracked; same caveat as the Sprint 57.13 / 57.27 matrix rows). Day 1 over-ran (Layer 4 pulled in per D-DAY1-1 atomic resequencing + 15-file un-translation vs the ~10-file estimate); Day 2 under-ran (theme wire only — small); Day 3+4 on-track.
- **Ratio actual/committed ≈ 1.05** — ✅ in `[0.85, 1.20]` band.
- **Ratio actual/bottom-up ≈ 0.59** — bottom-up ~1.7× generous; the 0.55 multiplier landed close.
- **1st data point** — KEEP 0.55 baseline regardless (1 data point insufficient to adjust per the `When to adjust` 3-sprint window rule). Matrix row + MHist added to `.claude/rules/sprint-workflow.md`.

## Q3 — What went well

- **Method-switch isolated cleanly** — doing the foundation switch as its own sprint behind one 22-route regression sweep proved 0 catastrophic / 0 structural breakage; every subsequent Phase-2 re-point now consumes mockup classes directly and gets CSS fidelity for free.
- **Day-0 三-prong caught the plan's wrong premise early** — D-PRE-1 found the mockup HAS a full light theme, correcting the plan's "dark-only" US-C2 premise before any Day-2 code (surfaced to the user; theme = light+dark both kept).
- **Atomic resequencing handled honestly** — D-DAY1-1 (Layer 2/3/4 are atomic; the mid-state is invalid `hsl(oklch())` CSS app-wide) was recorded as a drift finding and Layer 4 pulled into Day 1, not silently reshuffled.
- **Triage discipline** — the 3 error-boundary routes were checked against the Day-0 before-baseline; identical before+after error proved a pre-existing route-sweep harness mock gap, NOT a switch regression — recorded truthfully rather than mislabelled as catastrophic.
- **CI guard makes the protocol self-enforcing** — `check-mockup-fidelity.mjs` diff guard means a future hand-edit / re-translation of `styles-mockup.css` fails CI; the grep guard baselines the 18 pre-existing hardcoded-colour offenders so only NEW drift fails.

## Q4 — What to improve

- **Plan §Technical Specifications carried a wrong premise** — the "theme toggle alignment / dark-only" section was written from imprecise investigation reports (02/03 said "no light theme"). Day-0 Prong 2 caught it, but a plan that greps the mockup `styles.css` theme selectors *before* drafting §Technical Specifications would have started correct. Minor — the §Step 2.5 process worked as designed (the R3 row is the audit trail).
- **The un-translation scope estimate was low** — Day 0 estimated ~10 files needing `hsl(var())` un-translation; the real count was 15 (the first grep was `head`-truncated). A full (non-truncated) grep at plan time would have sized D-DAY1-2 correctly.
- **Playwright MCP still browser-stuck** — the Day-2 runtime spot-check fell back to the standalone `route-sweep.mjs` harness because the MCP browser is locked (the recurring `AD-Playwright-MCP-Recovery-Phase58` blocker — 4+ sprints). The fallback works; the MCP recovery remains a Phase-58 item.

## Q5 — Discipline check (V2 紀律 9 項)

1. Server-Side First ✅ frontend-only · 2. LLM Neutrality ✅ N/A (frontend-only; 0 SDK leak) · 3. CC Reference ✅ N/A · 4. 17.md single-source ✅ no new contract · 5. 11+1 範疇 ✅ all Frontend · 6. anti-patterns ✅ (no orphan code; D-DAY1-1 resequencing recorded not silent) · 7. Sprint workflow ✅ plan→checklist→三-prong→code→progress→retro · 8. File header ✅ (MHist updated on every touched file; 1-line entries) · 9. Multi-tenant ✅ N/A.

Rolling-planning ✅ — no future sprint plan pre-written; no unchecked `[ ]` deleted (§2.2 + §3.2 task text corrected per §Step 2.5, not deleted — plan R3 row + report §3c are the audit trail); this retrospective contains no concrete future-sprint tasks.

## Q6 — Carryover

- 🆕 **AD-RouteSweep-Object-Mock-Gap** — extend `route-sweep.mjs` with object-shaped mocks for `/api/v1/subagents` + `/api/v1/memory/recent` + the verification endpoint (same D-DAY1-1 class as cost/sla) so those 3 routes become sweep-assessable. Harness maintenance; pick up in a Phase-2 re-point sprint touching those pages.
- **Phase-2 per-page re-point epic** — 19 transition-drift routes' markup still consumes shadcn utilities on top of the verbatim foundation; re-point per-route to mockup classes (the `frontend-mockup-strict-rebuild` epic continues — now with the foundation correct).
- **`HEX_OKLCH_BASELINE = 18`** — governance + chat_v2 risk-colour maps still use hardcoded `bg-[#hex]`/`text-[#hex]`; each Phase-2 re-point should migrate to mockup `--risk-*` tokens and lower the baseline.
- **shadcn-system tokens** still in `index.css` — retired page-by-page as Phase 2 progresses.

## Q7 — Commits

| Commit | Scope |
|--------|-------|
| `af546fc4` | Day 0 — plan + checklist + 三-prong + before-baseline + FOUNDATION-SWITCH-REPORT skeleton |
| `2d6745b9` | Day 1 — Layer 2+3+4 verbatim-CSS foundation switch + `hsl(var())` un-translation (15 files) |
| `a530187c` | Day 2 — theme toggle drives mockup `[data-theme]` attr (light+dark) |
| `1865c15b` | Day 3 — CI mockup-fidelity guards + 22-route regression sweep + triage |
| _(pending)_ | Day 4 — closeout (report §5 final + retro + memory + calibration + PR) |
