# Sprint 57.41 — Retrospective

**Sprint id**: 57.41 — AD-Verification-Catastrophic-Rebuild
**Closed**: 2026-05-25
**Branch**: `feature/sprint-57-41-verification-full-rebuild`
**Class**: `frontend-mockup-strict-rebuild` 0.60 (7th data point)
**Commits**:
- `44459b30` — Day 1 / 37 files / +1296 / -443
- `5abe98f6` — Day 2 / 9 files / +413 / -102
- `26bc64cf` — Day 2.5 / 28 files / +51 / -1
- (TBD Day 3 closeout commit)

---

## Q1 — What went well

1. **Day 0 Prong 2.5 child-component-tree-depth audit prevented mid-sprint surprises (0 drift in Day 1).** The new AD-Plan-5 (folded into `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2.5` in Sprint 57.40 closeout) caught all 5 drift candidates at Day 0 before code start: 2 factual corrections (D-DAY0-1 BackendGapBanner location + D-DAY0-2 type name) + 1 small scope addition (D-DAY0-3 e2e adapt) + 2 informational out-of-scope residue notes (D-DAY0-4/5). Day 1 agent invocation completed first-try with 0 re-work.

2. **Pattern reuse from Sprint 57.40 governance primitives validated at scale.** 2 of Sprint 57.40's 5 NEW components transferred via mild rename (ApprovalsPageHeader → VerificationPageHeader; ApprovalsStatsStrip → VerificationStatsStrip with Pass rate computation swap). This validates the `frontend-mockup-strict-rebuild` class's claimed pattern-reuse-ROI; Sprint 57.41 needed only 4 NEW unique components (RunsTable + FailureKindsCard + FlakyChecksCard + VerificationView container) on top of the 2 rename clones.

3. **Vitest grew +9 NEW tests (vs +5-8 target = +112-225% over).** All 5 NEW spec files written first-try; only 1 drift (D-DAY2-1 adapter projects-into-multiple-cells `getByText` → `getAllByText`) auto-resolved by agent. Final count 498/498 vs 493 baseline.

4. **22 IDENTICAL + 2 CHANGED (1 expected + 1 sub-300-byte noise) sweep with 0 unintended regressions.** Cleanest sweep result of the Phase-2 epic. `/overview` -44 byte drift identical-pattern to Sprint 57.40 §2.5.2 precedent (live-clock topbar variation; well within envelope).

5. **Day 2 envelope-mock convention validated for 2nd application.** `AD-RouteSweep-Envelope-Mock-Convention` (NEW Sprint 57.40) applied cleanly to `/api/v1/verification/recent` with same `{items, total, has_more, next_offset, page_size}` envelope shape — confirms this is a generalizable cross-endpoint convention not a 1-off governance fix.

6. **Verbatim-CSS protocol kept HEX_OKLCH_BASELINE 46 unchanged.** Day 1 components reference `var(--success)` / `var(--danger)` / `var(--warning)` / `var(--memory)` / `var(--info)` CSS variables (NOT inline oklch literals). Mockup-fidelity guard PASS at 46 without baseline lift — plan §3.6 estimated +2-4 bump did not materialize, which is the **correct** outcome (literals belong only in `styles-mockup.css` per 4-layer protocol).

7. **3-way evidence pair structural fidelity confirmed at empty-list rendering layer.** AFTER 133.0 KB byte-equivalent to MOCKUP minus data-driven row count; gap explained by empty `items=[]` mock vs hardcoded 8-row VERIFY_CLAIMS. Mirror Sprint 57.40 §2.5.4 interpretation pattern.

---

## Q2 — What didn't go well + Calibration

### Calibration ratio — 7th data point

**Bottom-up est (plan §8)**: ~14 hr
**Calibrated commit (0.60 multiplier)**: ~8.5 hr
**Actual wall-clock total**: ≈ **1.5 hr** (Day 0 ~30-40 min + Day 1 ~25-30 min + Day 2 ~20-25 min + Day 2.5 ~5-10 min + Day 3 closeout ~20-30 min TBD)
**Ratio actual/committed**: **~0.18** — significantly BELOW [0.85, 1.20] band by **~0.67**
**Ratio actual/bottom-up**: ~0.11 — bottom-up was ~9× too generous

### 7-pt window stats for `frontend-mockup-strict-rebuild` 0.60

| Sprint | Ratio | In-band? |
|--------|-------|----------|
| 57.23 | 0.59 | below by 0.26 |
| 57.24 v2 | 1.19 | top of band ✅ |
| 57.25 | 0.88 | in band ✅ |
| 57.27 | ≈0.95 | in band ✅ |
| 57.37A | ≈1.18 | top of band ✅ |
| 57.40 | ≈0.36 | below by 0.49 |
| **57.41** | **~0.18** | **below by 0.67 — deepest of class history** |

- **7-pt mean**: (0.59 + 1.19 + 0.88 + 0.95 + 1.18 + 0.36 + 0.18) / 7 = **0.76** at lower band edge (down from 6-pt mean 0.86 = -0.10)
- **Last 3 (57.37A + 57.40 + 57.41)**: 2 of 3 < 0.7 — `When to adjust` lower-trigger (3+ consecutive < 0.7) **NOT yet met** but very close
- **Decision per matrix rule**: KEEP 0.60 baseline this iteration; flag for Sprint 57.42 retro if 8th data point also < 0.7 → 3-consecutive-below-band trigger would activate baseline lift OR class split proposal

### Root cause (per Q3 below)

Agent-delegation factor — code-implementer 8th + 9th consecutive invocations completed Day 1 + Day 2 at ~25-30 min wall-clock vs human-rewrite cadence the bottom-up estimates assume. Per plan §1.5 + `.claude/rules/sprint-workflow.md §Proposed Agent Delegation Factor Modifier`:

**Sprint 57.41 is the 4th cross-class data point** for `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`:

| Sprint / FIX | Class | Ratio | Agent-delegated |
|--------------|-------|-------|-----------------|
| Sprint 57.39 | `-with-extras` (0.65) | 0.41 | 6th+7th consecutive |
| FIX-015 (post-hoc) | bundled FIX | ~0.04 (outlier) | code-implementer 6 child re-point |
| Sprint 57.40 | mockup-strict-rebuild | 0.36 | 7th consecutive |
| **Sprint 57.41** | **mockup-strict-rebuild** | **0.18** | **8th+9th consecutive** |

**Activation rule status**: 3+ data points across multiple classes — **technically met** (4 data points across 2 classes). Per plan §9 carryover, propose Sprint 57.42 retro structural evaluation of Option A (multiplicative `agent_factor` coefficient = 0.55) vs Option B (per-class sub-class split) per `.claude/rules/sprint-workflow.md §Proposed Agent Delegation Factor Modifier`.

### Other didn't-go-well items

- **Bottom-up estimates remain ~9× too generous for agent-delegated frontend work.** This is now a 7-sprint pattern across the Phase-2 epic (57.34 / 57.35 / 57.36 / 57.37B / 57.39 / 57.40 / 57.41). Calibration matrix discipline alone (per-class baseline) cannot capture the agent-vs-human cadence delta. Needs structural modifier.

---

## Q3 — What we learned (generalizable lessons)

### Lesson 1 — Pattern-reuse component count converges to a small irreducible-NEW core

Sprint 57.40 created 5 NEW; Sprint 57.41 transferred 2 via rename + needed only 4 NEW unique. As the `frontend-mockup-strict-rebuild` epic ships more pages, the marginal NEW-component count per rebuild drops because earlier rebuilds (cost-dashboard / sla-dashboard / overview / governance) seed reusable primitives. The 6-pt history shows: 57.23 ~7 NEW, 57.24 ~7, 57.25 ~6, 57.27 ~5, 57.40 ~5, 57.41 ~4. Future rebuilds (`/memory` / `/admin-tenants` / `/tenant-settings`) likely need only 3-5 NEW unique.

### Lesson 2 — Day 0 Prong 2.5 child-tree-depth audit ROI scales with rebuild count

Sprint 57.39 D-DAY1-1 (governance + verification child shadcn residue surfaced mid-Day-1; ~3-5 hr scope expansion) → Sprint 57.40 promoted AD-Plan-5 → Sprint 57.41 first deliberate full application → **0 mid-sprint surprises**. The ~5-10 min cost per Day 0 Prong 2.5 application avoids 1-5 hr scope expansion per drift. ROI ~20-60×.

### Lesson 3 — Envelope-mock convention generalizes cross-endpoint

Sprint 57.40 `/governance/approvals` envelope mock (1st app of `AD-RouteSweep-Envelope-Mock-Convention`) → Sprint 57.41 `/api/v1/verification/recent` (2nd app, same `{items, total, has_more}` shape). 2 different routes / 2 different feature areas / same envelope class. The convention is now validated as cross-endpoint generalizable — recommend folding into `.claude/rules/sprint-workflow.md §Common Risk Classes` as Risk Class D (route-sweep default `[]` fallback vs TanStack envelope assertion).

### Lesson 4 — Verbatim-CSS protocol naturally limits HEX_OKLCH_BASELINE bumps

Plan estimated +2-4 bump for Sprint 57.41; actual = 0. The discipline of using `var(--success)` / `var(--danger)` etc. CSS variables for color references — instead of inline `oklch(...)` literals — keeps the baseline static across rebuilds. Plan §3.6 envelope estimate should be reduced going forward (the +2-4 was over-cautious; verbatim-CSS protocol consistently hits +0 for color refs).

### Lesson 5 — `getAllByText` over `getByText` for adapter-projects-into-multiple-cells

D-DAY2-1: VerificationRunsTable's `adaptItem()` puts `reason` text in BOTH `claim` AND `evidence` cells (with evidence sliced 80 chars). First-pass Vitest spec used `getByText` and threw on duplicate. Pattern recurs from Sprint 57.40 D-DAY2-X (ApprovalDetailPane payload.reason in subtitle + Agent rationale field). Generalizable: when an adapter projects one input field into multiple output cells, prefer `getAllByText(...).length >= 1` (or `getAllByText(/.../i)[0]`). Candidate addition to a new "Common Vitest Spec Patterns" doc or `.claude/rules/testing.md`.

---

## Q4 — Audit debt deferred

| AD | Description | Target |
|----|-------------|--------|
| `AD-Verification-Filter-Form-Phase58-Migrate` | Sprint 57.41 retired VerificationList filter form per Karpathy §3 (mockup has none). If admin filter UI is needed, surface on `/verification/admin` separate route OR re-introduce as collapsible `<details>` panel above runs table | Phase 58+ |
| `AD-Verification-Backend-Claim-Evidence-Extension` | Backend `VerificationLogItem` currently has only `reason` text; mockup expects structured `claim` + `evidence` + `kind` fields. Sprint 57.41 maps best-effort via fallback in `adaptItem()`. Phase 58+ backend can extend schema for cleaner mapping | Phase 58+ |
| `AD-Verification-All-Kinds-Filter-Dropdown` | Mockup header "All kinds" outline button is Sprint 57.41 AP-2 stub; deferred kind-filter dropdown wiring | Phase 58+ |
| `AD-Verification-Failure-Kinds-Aggregation-Endpoint` | Sprint 57.41 sidebar Failure kinds is AP-2 fixture. Backend `GET /verifications/stats/failure-kinds` endpoint required for real data | Phase 58+ |
| `AD-Verification-Flaky-Checks-Aggregation-Endpoint` | Same as above for Flaky checks sidebar | Phase 58+ |
| `AD-Verification-Out-Of-Scope-Components-Phase2-C-Mop-Up` | 2 AP-Phase2-C residue sites remain in VerificationPanel.tsx (chat-v2 inline panel) + CorrectionTraceView.tsx (`/timeline` tab) — both out-of-scope for Sprint 57.41 | Phase 58+ |
| **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** | **Activation criteria now met** (4 cross-class data points: 57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 — all < 0.7 agent-delegated). Propose Sprint 57.42 retro structural evaluation: Option A multiplicative `agent_factor` coefficient (start 0.55) OR Option B per-class sub-class split (`-with-extras + agent-delegated` 0.30-0.40 etc.) | **Sprint 57.42 retro** |

---

## Q5 — Next steps / carryover candidates

**Per rolling planning §6 — no specific Sprint 57.42 task list pre-written.** Candidate directions per ROI (from `claudedocs/1-planning/next-phase-candidates.md` + post-Sprint-57.41 audit report):

1. 🥇 **`AD-Verification-Catastrophic-Rebuild`** — ✅ CLOSED by this Sprint 57.41
2. **`AD-Memory-Layers-Matrix-Rebuild`** — `/memory` matrix grid rebuild ~10-15 hr (3rd CATASTROPHIC route)
3. **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` tenants table rebuild ~12-15 hr (4th CATASTROPHIC route)
4. **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` 6-tab rebuild ~15-20 hr (5th CATASTROPHIC route; largest scope)
5. **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename ~30 min (NEAR-PARITY quick win)
6. **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — structural calibration matrix evaluation (activated; Sprint 57.42 retro)

**Other carryover ADs** added by Sprint 57.41 (5 new Phase-58 ADs per Q4 above).

---

## Q6 — Verbatim-CSS protocol compliance

- ✅ Layer 2 byte-identical: `styles-mockup.css` vs `reference/design-mockups/styles.css` — diff guard PASS (re-confirmed Day 2)
- ✅ Layer 4 collision check: 0 new `--sc-*` token collisions; new components reference existing `var(--success)` / `var(--danger)` / `var(--warning)` / `var(--memory)` / `var(--info)` / `var(--fg-muted)` / `var(--font-mono)` from styles-mockup.css verbatim
- ✅ HEX_OKLCH_BASELINE: 46 unchanged (estimated +2-4 bump did not materialize — correct outcome per verbatim-CSS protocol; literals belong only in styles-mockup.css)
- ✅ mockup-fidelity guard exit 0 — Day 0 baseline + Day 2 post-implementation + Day 2.5 post-rebuild all PASS

---

## Q7 — Solo-dev policy validation

N/A — SKIP. Sprint 57.41 is single-author solo-dev; `required_approving_review_count = 0` policy continues to function (PR will be opened against main; CI gates apply; self-approve still blocked by GitHub but `count=0` bypasses requirement).
