# Sprint 57.36 — Retrospective

**Sprint**: 57.36 — AD-Loop-Debug-Verbatim-Repoint
**Closed**: 2026-05-24
**Class**: `frontend-verbatim-css-repoint` 0.50 (7th application; 3rd shape-validation data point; 2nd consecutive above-band)
**PR**: (pending push)
**Outcome**: 🎉 `/loop-debug` LoopVisualizer.tsx flipped from Sprint 57.18-57.27 vintage HSL-translation → mockup verbatim PARITY. Dual-mount preserved (chat-v2 inline cascade ε within tolerance). 22-route sweep 19 IDENTICAL / 3 CHANGED (all expected). **3rd shape data point reveals variance is multi-dimensional — bimodal-by-shape AND scale-overhead BOTH weakened further.**

---

## Q1 — What went well?

1. **Single-file scope clean execution** — only `LoopVisualizer.tsx` touched as planned; no scope creep into chat-v2 page or shell.
2. **Day 0 三-prong caught 7 drift findings BEFORE Day 1 code** — particularly D-DAY0-2 (BackendGapBanner API correction `{reason}` not `{title, body, href}`) saved agent ~15 min of API confusion.
3. **Agent-delegation pattern 3rd consecutive success** — code-implementer completed Day 1-2 in ~80 min wall-clock with all gates green (TS 0 errors / Vitest 456/456 / mockup-fidelity 41/41 unchanged / lint clean).
4. **Dual-mount cascade verified safe** — `/chat-v2` after-screenshot delta = +18 B (well within ε); inline mount preserved Sprint 57.30 ship state.
5. **22-route sweep verdict crisp** — 19 IDENTICAL byte-for-byte + 1 expected structural (loop-debug +22,512 B) + 2 within ε (chat-v2 +18 B cascade; overview +70 B unrelated noise from time-text or anti-aliasing).
6. **AP-2 honesty maintained** — BackendGapBanner + EmptyInspectorPlaceholder explicitly defer playback / scrubber / filter / inspector pane to Phase 58+ with named root cause (SSE event persistence per Sprint 57.12 AP-6).
7. **Mockup classes adopted verbatim** — `.loop-canvas` / `.loop-track` / `.loop-inspector` / `.loop-turn` / `.loop-turn-head` / `.loop-turn-body` / `.turn-no` / `.event-row` / `.ev-dot` / `.ev-type` / `.ev-detail` / `.ev-timing` all consume Sprint 57.28 byte-identical foundation; zero new `oklch(from var(--X) l c h / X)` literals (baseline 41 preserved).
8. **`eventTone()` adapter elegant** — production LoopEvent schema's type-based severity (is_error / verification_failed / guardrail_triggered / approval_requested) mapped cleanly to mockup token vocabulary (`--danger` / `--warning` / `--tool` / `--thinking` / `--success` / `--primary` / `--fg-muted`).

---

## Q2 — Calibration

| Metric | Value |
|--------|-------|
| Bottom-up estimate | ~4.75 hr (285 min) |
| Calibrated commit (×0.50) | ~2.4 hr (144 min) |
| Day 0 actual | ~55 min (plan + checklist + 三-prong + before sweep + 2 baseline checks) |
| Day 1-2 actual | ~80 min (agent wall-clock) |
| Day 3 actual | ~10 min (after sweep + diff + visual verify) |
| Day 4 actual | ~60 min (retro + memory subfile + matrix update + next-phase + CLAUDE.md + commit + push + PR) |
| **Total actual** | **~205 min (~3.42 hr)** |
| `actual / committed` ratio | **~1.42** — **ABOVE [0.85, 1.20] band by 0.22** |
| `actual / bottom-up` ratio | **~0.72** — bottom-up was 28% generous; 0.50 multiplier was insufficient haircut for AP-2 + dual-mount scope |

### 3rd shape-validation data point evaluation

| Sprint | Shape | Sub-shape | Files | AP-2 banner | Dual-mount | Ratio | Band |
|--------|-------|-----------|-------|-------------|------------|-------|------|
| 57.29-32 | rich | dashboard | 7-ish each | — | — | 3-pt mean ≈ 0.40 | ❌ below |
| 57.34 | non-rich | config/tabbed-forms | 1 | no | no | ≈ 1.0 | ✅ in band |
| 57.35 | non-rich | auth-flow batched | 8 | no | no | ~1.7 | ❌ above |
| **57.36** | **non-rich** | **dual-mount + AP-2** | **1** | **yes** | **yes** | **~1.42** | **❌ above** |

**Critical insight — variance is MULTI-DIMENSIONAL** (both prior hypotheses weakened further):
- **Bimodal-by-shape**: 3 non-rich points (1.0 + 1.7 + 1.42) mean 1.37 — not a clean shape signal.
- **Scale-overhead**: Sprint 57.36 was 1-file (same as 57.34) but ratio diverged (1.0 vs 1.42). File-count alone insufficient.
- **Emerging variance drivers** observed across 57.34-57.36:
  1. **AP-2 banner addition** (57.36 yes; 57.34 no) — adds scope beyond pure re-point
  2. **Dual-mount preservation** (57.36 yes; 57.34 no) — adds mode-branching complexity
  3. **Spec file existence** (57.36 had test file caught Day 1 by agent; 57.34 had none)
  4. **Day 0 三-prong overhead** (57.36 ~55 min vs 57.34 ~30 min — 7 drifts caught)

### Decision per `When to adjust` 3-sprint window rule

- 2 consecutive sprints above band (57.35 ~1.7 + 57.36 ~1.42); 3-pt window needs 1 more for trigger condition (3+ consecutive > 1.20 → lift multiplier).
- **KEEP 0.50 baseline this iteration** — 2-data-point insufficient for adjustment.
- **NEW AD**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch` — variance is no longer captured by a single 1-D hypothesis (shape OR scale); multiple drivers (AP-2 + dual-mount + spec + drift overhead) compound. If Sprint 57.37+ also > 1.20, propose either (a) baseline lift 0.50 → 0.60, or (b) class split `frontend-verbatim-css-repoint-simple` (0.50) vs `frontend-verbatim-css-repoint-with-ap2-or-dual-mount` (0.65).
- **Update**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch` (Sprint 57.34 NEW) — REJECTED bimodal hypothesis; close.
- **Update**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` (Sprint 57.35 NEW) — WEAKENED scale-as-sole-driver hypothesis; broaden to multi-dimensional.

---

## Q3 — What didn't go as planned?

1. **Day 0 Prong 1 glob scope too narrow** — D-DAY1-1 revealed `LoopVisualizer.test.tsx` exists at `frontend/tests/unit/orchestrator-loop/` but Day 0 Prong 1 glob was `frontend/src/**/LoopVisualizer*.test.*` (missed `frontend/tests/**`). Caught by agent Day 1 (~5 min lost re-discovering scope). **Lesson**: future Prong 1 globs MUST cover BOTH `frontend/src/**` AND `frontend/tests/**` for spec-existence claims (test files conventionally live outside `src/`).
2. **D-DAY1-2 ESLint `no-restricted-syntax` body-blind matcher** — agent had to apply Sprint 57.24 BarTrack STYLE.md §3 escape hatch (module-scope style constants + per-site `eslint-disable-next-line`) to handle `style={CONSTANT_REF}` which lint flagged identically to `style={{...inline}}`. This is a known limitation of the JSXAttribute selector; documenting in Sprint 57.36 retro carries the precedent forward.
3. **Ratio ~1.42 above band** — bottom-up est was reasonably accurate (~285 min actual vs ~285 min planned) but 0.50 haircut was too aggressive for the actual scope (AP-2 banner + dual-mount + spec adapt + drift handling all compound). Future sprints with similar scope shape should anticipate higher calibration.
4. **`/overview` +70 B delta unexplained** — not a regression (file unchanged) but the noise is within ε tolerance. Possible cause: time-relative text (e.g. "Last updated X min ago") or PNG anti-aliasing variance. Documented as ε; not flagged for further investigation.

---

## Q4 — What would I do differently next time?

1. **Day 0 Prong 1 glob coverage rule**: extend Prong 1 globs to include both `frontend/src/**` and `frontend/tests/**` for spec-existence claims. Add to `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 1 — Path Verify as a "spec file convention note". Saves ~5-10 min per sprint where spec discovery would otherwise drift.
2. **AP-2 banner scope premium in calibration**: when sprint includes AP-2 BackendGapBanner addition (vs pure re-point), apply a ~10-15% surcharge to the calibration multiplier. E.g. Sprint 57.36 should have been calibrated at 0.55-0.60 not 0.50.
3. **Dual-mount premium**: when sprint touches a dual-mount component (LoopVisualizer; potentially others), apply additional ~5-10% surcharge for mode-branching verification. E.g. 0.55 → 0.60.
4. **Combined**: future sprints with **both AP-2 + dual-mount** scope (like 57.36 was) should baseline at ~0.60-0.65 not 0.50. This is the multi-dimensional variance correction the new AD captures.

---

## Q5 — Next sprint pickup candidates

Per Phase-2 epic backlog (Sprint 57.22 audit + Sprint 57.35-36 carryover):

1. **`/state-inspector` Phase-2 verbatim CSS re-point** — operations admin shape; mockup likely in `page-extras.jsx` or `page-platform*.jsx` (verify Day 0); should be 1-file scope similar to 57.34; clean 4th shape data point (no AP-2 / no dual-mount → tests "simple" variance baseline).
2. **`/memory` Phase-2 verbatim CSS re-point** — operator memory inspection; per Sprint 57.22 audit Unit 13-14 likely needs structural rebuild not just re-point; defer until classification verified.
3. **`/governance` Phase-2 verbatim CSS re-point** — admin shape; multi-page (governance + governance/approvals + governance/audit-log) — would be multi-file like 57.35 (test scale-overhead hypothesis 2nd data point).
4. **`/admin-tenants` Phase-2 verbatim CSS re-point** — admin shape; potentially multi-file similar to /governance.
5. **`/tenant-settings` Phase-2 verbatim CSS re-point** — Sprint 57.22 Unit 31 6-tab architectural finding; biggest structural sprint candidate; should be flagged as `frontend-mockup-strict-rebuild` not re-point.

**Recommendation**: pick `/state-inspector` for 57.37 — provides cleanest 4th data point isolating "simple non-rich 1-file" baseline (no AP-2 / no dual-mount), discriminating multi-dimensional variance hypothesis.

User to pick direction. Rolling planning §6 — Sprint 57.37 plan **NOT pre-written**.

---

## Q6 — Open items / Carryover

- 🆕 **NEW**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch` — variance is multi-dimensional (file count + AP-2 + dual-mount + spec + drift overhead all compound); 1-D hypotheses (shape OR scale) insufficient.
- 🔚 **CLOSED**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch` (Sprint 57.34 NEW; Sprint 57.35 weakened; Sprint 57.36 REJECTED — 3 non-rich pts spread 1.0/1.4/1.7 = not bimodal).
- 🔄 **Updated → WEAKENED**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` (Sprint 57.35 NEW) — 1-file (57.36) also above band; file-count not sole driver.
- 🔄 **Updated**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (Sprint 57.31 NEW) — 4th validation logged; baseline 0.50 holds for simple non-rich (57.34 only data point in band); above-band trend (57.35 + 57.36) needs 1 more sprint to trigger formal lift candidate.
- 🆕 **Lesson**: extend Day 0 Prong 1 glob coverage to BOTH `src/**` AND `tests/**` for spec-existence claims; codify into `sprint-workflow.md` §Step 2.5 Prong 1.
- 🆕 **Lesson**: AP-2 banner addition + dual-mount preservation are calibration-surcharge candidates (~10-15% each beyond pure re-point baseline).
- 🆕 **Lesson**: ESLint `no-restricted-syntax` JSXAttribute style matcher is body-blind; module-scope constants + `eslint-disable-next-line` per Sprint 57.24 BarTrack STYLE.md §3 precedent is the workaround.
- **Unchanged**: `AD-Tabs-Migration-To-MockupUi` (Sprint 57.34 low priority) / `AD-IAM-Block-B-RBAC` / `AD-WebAuthn-Roll-Own-UI` (Phase 58+).

Full updates posted to `claudedocs/1-planning/next-phase-candidates.md` Sprint 57.36 Carryover section.

---

## Q7 — Design note extract (spike sprint only)

**N/A** — Sprint 57.36 is a Phase-2 epic continuation, not a spike. No design note required.

---
