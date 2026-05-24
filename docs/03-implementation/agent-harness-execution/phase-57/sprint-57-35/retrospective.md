# Sprint 57.35 — Retrospective

**Sprint**: 57.35 — AD-Auth-Shell-And-Pages-Verbatim-Repoint
**Closed**: 2026-05-24
**Class**: `frontend-verbatim-css-repoint` 0.50 (6th application; 3rd validation; 2nd bimodal data point)
**PR**: (pending push)
**Outcome**: 🎉 8 auth files (AuthShell + 7 routes) flipped from Sprint 57.23 vintage → mockup verbatim PARITY. User-reported `/auth/login` drift RESOLVED. 22-route sweep 0 regressions. **Bimodal-by-shape signal WEAKENED — file-count scale emerges as 2nd variance driver.**

---

## Q1 — What went well?

1. **User-reported drift fully resolved** — `/auth/login` now matches mockup verbatim (SSO `.btn-outline` styling + Continue `.btn-primary .btn-block` solid blue + `dev-login` `.mono` orange link with `var(--warning)`).
2. **Closes Sprint 57.23 vintage epic gap** — CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint warning addressed for 7 auth routes + AuthShell.
3. **Agent-assisted Day 1-3 efficient** — 8 production files + 4 Vitest spec updates + 4 drift findings (D-DAY1-1, D-DAY2-1, D-DAY2-2, D-DAY3-1) all handled in ~20-min agent wall-clock; correctly preserved auth flow integrity (data-testid, useAuthStore, WebAuthn UI, 6-digit TOTP grid).
4. **22-route sweep clean** — 0 regressions; 5 prior Phase-2 routes (overview/chat-v2/cost/sla/orchestrator) maintained PARITY.
5. **AuthShell width drift caught** — Day-1 D-DAY1-1 found Sprint 57.23 used 420px vs mockup `page-extras.jsx:13` truth 400px. Verbatim restored.
6. **Vitest 456/456 baseline preserved** — 4 spec files updated (mockup-ui `Field` emits `<div class="field-label">` not `<label htmlFor>`; spec contracts updated `getByLabelText` → `getByText` + id selectors; behavioral intent preserved).
7. **Single agent execution covered 8 files / 7 routes in one session** — vs hypothetical 7 separate single-route sprints, dramatic efficiency win.

---

## Q2 — Calibration

| Metric | Value |
|--------|-------|
| Bottom-up estimate | ~8.5 hr (510 min) |
| Calibrated commit (×0.50) | ~4.25 hr (255 min) |
| Actual (effective human-equivalent) | **~7-7.5 hr** (agent-assisted; Day 1-3 ~20 min agent wall-clock representing ~5-6 hr human work + Day 0 ~63 min + Day 4 ~50 min) |
| `actual / committed` ratio | **~1.65-1.75** — **ABOVE [0.85, 1.20] band by ~0.45-0.55** |
| `actual / bottom-up` ratio | **~0.85-0.90** — bottom-up estimate accurate; **0.50 multiplier too aggressive for 8-file scope** |

### Bimodal-by-Shape Evaluation (2nd non-rich data point)

| Sprint | Shape | Sub-shape | Files | Ratio | Band |
|--------|-------|-----------|-------|-------|------|
| 57.29-32 | rich | dashboard | 7-ish each | 3-pt mean ≈ 0.40 | ❌ below |
| 57.34 | non-rich | config/tabbed-forms | **1 file** | ≈ 0.95-1.05 | ✅ in band |
| **57.35** | **non-rich** | **auth-flow** | **8 files** | **~1.65-1.75** | **❌ ABOVE** |

**Critical insight — bimodal hypothesis WEAKENED**:
- 57.34 + 57.35 both non-rich-dashboard but ratios diverge by ~0.7 (1.0 vs 1.7).
- File-count + Vitest-spec-update overhead is plausibly the dominant variance driver, NOT shape per se.
- 0.50 multiplier optimized for typical 1-file re-points; multi-file sprints need surcharge.

**Revised hypothesis**: Class baseline 0.50 is correct for typical 1-page re-points; multi-file batched sprints need a **file-count surcharge** (e.g. 0.50 + 0.05/extra-file beyond ~3).

**Decision per `When to adjust` 3-sprint window rule**:
- **KEEP 0.50 baseline** this iteration (3-pt data is now: 1 in-band [57.34] + 1 below band [57.32 rich] + 1 above band [57.35 multi-file] — insufficient to split or shift).
- **NEW AD: `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch`** — if Sprint 57.36+ multi-file sprints again > 1.20 band → propose file-count surcharge.
- **Update AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** → broaden to scale-and-shape; don't propose class split yet.

---

## Q3 — What didn't go as planned?

1. **8-file scope under-estimated** — Sprint 57.34 was 1-file `/orchestrator`; Sprint 57.35 was 8 files. Plan §Workload bottom-up was reasonably accurate (~8.5 hr) but the 0.50 haircut produced calibrated 4.25 hr which was unrealistic for the scope. Future multi-file batched sprints should anticipate file-count overhead.
2. **Vitest spec update overhead not budgeted in Day-time** — agent correctly identified the `Field` DOM change and updated 4 spec files (7 tests). This adds ~30-40 min of work not allocated to any User Story. Future plans should budget Vitest spec update time when changing primitive APIs.
3. **Mockup-internal drift discovered** — `page-extras.jsx:13` (canonical AuthShell) uses 400px but sibling `page-auth-extras.jsx:13` (re-export) uses 420px. Agent chose canonical correctly but this is a noteworthy mockup inconsistency that user/maintainer may want to reconcile.

---

## Q4 — What would I do differently next time?

1. **File-count surcharge in calibration**: for multi-file batched re-point sprints (>3 files), apply 0.50 + ~0.05/extra-file surcharge as initial calibration estimate. Validate with `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` 2-3 data points.
2. **Vitest spec update budget**: when re-pointing changes primitive API (e.g. label → div), budget 30-60 min per primitive for spec updates that preserve behavioral intent. Add explicit US for this.
3. **Mockup canonical source designation**: when two mockup files have re-exports (e.g. `page-extras.jsx` AuthShell + `page-auth-extras.jsx` AuthShellX), designate canonical source in `reference/design-mockups/AGENTS.md` (or similar) to prevent future ambiguity.

---

## Q5 — Next sprint pickup candidates

Per Phase-2 epic backlog + Sprint 57.35 bimodal-and-scale-watch ADs:

1. **`/loop-debug` Phase-2 verbatim CSS re-point** — operator-facing debug UI; non-rich-dashboard shape; single-file 3rd validation for shape hypothesis.
2. **`/state-inspector` Phase-2 verbatim CSS re-point** — operations admin shape; single-file 3rd validation.
3. **`/admin-tenants` Phase-2 verbatim CSS re-point** — admin shape; potentially multi-file.
4. **`/governance` Phase-2 verbatim CSS re-point** — governance config shape.
5. **`/tenant-settings` Phase-2 verbatim CSS re-point** — tenant admin shape (Sprint 57.22 Unit 31 architectural finding).

User to pick direction. Rolling planning §6 — next sprint plan **NOT pre-written**.

---

## Q6 — Open items / Carryover

- ✅ **RESOLVED: Sprint 57.23 vintage HSL-translation epic gap on auth routes** — fully closed
- 🆕 **NEW**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` — file-count + Vitest-spec-update overhead may be additional variance driver
- 🔄 **Updated**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch` (Sprint 57.34 NEW) — bimodal WEAKENED but not REJECTED; broaden to scale-and-shape
- 🔄 **Updated**: `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (Sprint 57.31 NEW) — 3rd validation logged; 0.50 baseline OK for typical 1-file re-points
- 📚 **Lesson logged**: file-count surcharge for multi-file batched sprints; Vitest spec update budget; mockup canonical source designation
- **Unchanged**: `AD-IAM-Block-B-RBAC` / `AD-WebAuthn-Roll-Own-UI` (Phase 58+)

Full updates posted to `claudedocs/1-planning/next-phase-candidates.md` Sprint 57.35 Carryover section.

---

## Q7 — Design note extract (spike sprint only)

**N/A** — Sprint 57.35 is a Phase-2 epic continuation, not a spike. No design note required.
