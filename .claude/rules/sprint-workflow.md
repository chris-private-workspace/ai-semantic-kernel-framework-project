# Sprint Workflow Rules

**Purpose**: Enforce sprint execution discipline; prevent Phase 35-38 shortcut lessons from repeating.

**Category**: Development Process
**Created**: 2026-04-28
**Last Modified**: 2026-05-25
**Status**: Active

> **Modification History**
> - 2026-05-25: Bundle Item #4 — propose Agent Delegation Factor Modifier (matrix proposal, pending 2-3 sprint validation) + §Before Commit lint must be non-silent (closes AD-Sprint-Plan-Agent-Delegation-Factor-Modifier as proposal + AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern)
> - 2026-05-25: AD-Plan-5 fold-in §Step 2.5 Prong 2.5 Child Component Tree Depth Audit (closes AD-Day0-Prong2-Child-Component-Tree-Depth-Audit; Sprint 57.39 D-DAY1-1 + FIX-015 evidence)
> - 2026-05-18: Sprint 57.22 — add §Sprint Closeout CLAUDE.md+MEMORY.md update policy (closes REFACTOR-001 Step 2)
> - 2026-05-06: Sprint 57.1 — fold-in §Step 2.5 Prong 3 Schema Verify (closes AD-Plan-4 promotion)
> - 2026-05-05: Sprint 55.6 — promote AD-Plan-3 (Prong 2 content verify + ROI + grep patterns)
> - 2026-05-04: Sprint 55.3 — add §Step 2.5 Day-0 plan-vs-repo grep verify (closes AD-Plan-1) + drop per-day "Estimated X hours" headers from checklist template (closes AD-Lint-2)
> - 2026-05-04: Sprint 53.7 — add §Workload Calibration sub-section under Step 1 (closes AD-Sprint-Plan-1) + new §Common Risk Classes top-level section (closes AD-CI-4) + Pre-Push reference `python scripts/lint/run_all.py` wrapper (closes AD-Lint-1 doc portion)
> - 2026-04-28: Initial creation (V2 foundation) — enforce 5-step workflow + change record conventions

---

## Overview

This document enforces the **mandatory 5-step sprint execution flow** used in V2 (Phase 49+). Phase 35-38 violated this flow by skipping plan + checklist, leading to scattered implementation and poor traceability.

**Golden Rule**: `Phase README → Sprint Plan → Sprint Checklist → Code → Update Checklist → Progress Doc`

---

## Mandatory 5-Step Workflow

### Step 1: Create Plan File

**Before writing any code**, create sprint plan at `docs/03-implementation/agent-harness-planning/phase-XX-name/sprint-XX-Y-plan.md`.

**Required Sections**:
- **Sprint Goal**: One sentence. What does this sprint deliver?
- **User Stories**: 3-5 stories in "As a / I want / So that" format
- **Technical Specifications**: Design decisions, architecture rationale, technology choices
- **File Change List**: Explicit list of all files to be created/modified (with counts)
- **Acceptance Criteria**: Measurable, testable definition of done
- **Deliverables**: `- [ ]` checkbox list mapping to stories
- **Dependencies & Risks**: What could block? What's the mitigation?

**Reference Template**: **The most recent completed sprint's plan** (NOT a fixed reference like 49.1; always the latest closed sprint). As of 2026-04-30, that's `phase-51-tools-memory/sprint-51-2-plan.md` (9 sections, 0-9). Mirror its section count, naming, and detail level exactly. Sprint scope differences must be expressed through **content** (more stories / more files), **never through structure** (don't add sections, don't rename §5/§6/§7).

**Why**: Prevents vague scope. Forces thinking before coding. Becomes sprint contract. Format consistency lets reviewer / next-session AI navigate any sprint plan with the same mental map.

**Violation Pattern** ❌: "I'll start coding and see what happens" → scattered PRs → unclear scope → Phase 35-38 repeat.

**Violation Pattern** ❌ (Sprint 52.1 v1 — 2026-04-30): Drafted plan with 10 sections + 6 days + custom section names without consulting most recent (51.2) plan format. User had to point out inconsistency; 3 rewrites (v1→v2→v3) before format aligned. **Lesson**: Read prior sprint plan FIRST, then mirror exactly.

#### Workload Calibration (Sprint 53.7+ — closes AD-Sprint-Plan-1)

Plan §Workload (or equivalent header) **must** state estimate in this three-segment form:

> Bottom-up est ~X hr → calibrated commit ~Y hr (multiplier Z)

- **X** = sum of per-task / per-US bottom-up estimates (raw, no calibration applied)
- **Z** = calibration multiplier in [0.4, 1.0]; default **0.5–0.6** (mid-band 0.55) per 53.4 + 53.5 + 53.6 retrospectives Q2 evidence (3 consecutive ~50% over-estimate; ~7-14 hr banked across 3 sprints)
- **Y** = X × Z = number you actually commit to (PR description / sprint goal acceptance / Day 4 retrospective Q2 baseline)

**When to adjust the multiplier**:
- 3+ consecutive sprints with `actual / committed > 1.2` → raise multiplier (e.g. 0.55 → 0.70) — under-estimating
- 3+ consecutive sprints with `actual / committed < 0.7` → lower multiplier (e.g. 0.55 → 0.40) — buffer too generous
- Single-sprint outliers: ignore; 3-sprint moving evidence required

**Day 4 retrospective Q2 must verify the multiplier**:
- Compute `actual_total_hr / committed_total_hr` ratio
- Document delta vs expected `≈ 1.0`
- If `|delta| > 30%`: log `AD-Sprint-Plan-N+1` to revisit multiplier in next plan template iteration

**Why**: Three consecutive ~50% over-estimate sprints (53.4 + 53.5 + 53.6) showed bottom-up estimates consistently double actual; without calibration, sprint commitments were inflated and "banked" hours obscured velocity tracking.

**First plan to apply**: Sprint 53.7 itself (`sprint-53-7-plan.md` §Workload).

#### Scope-class multiplier matrix (Sprint 57.6+ — closes AD-Reality-10 + AD-Sprint-Plan-7)

Per AD-Sprint-Plan-4 (logged Sprint 55.3) + 4-sprint window evidence,one-multiplier-fits-all approach loses signal when scope class differs。Below matrix記錄 active classes per scope。`mid-band` value 0.55 for default unclassified scopes;diversification per evidence。

| Scope class | Multiplier (mid-band) | Data points (sprint=ratio) | 3-sprint mean | Status |
|-------------|----------------------|----------------------------|---------------|--------|
| `mixed` (greenfield + reuse) | 0.60 | 53.7=1.01 / 56.2=1.17 / 57.3=0.57 / 57.4=0.42 (4) | mean **0.79** ⬇️ below band | AD-Sprint-Plan-6 propose split `mixed-greenfield` 0.60 vs `mixed-pattern-reuse` 0.40 |
| `medium-backend` | 0.80 (0.65 base + 0.05 audit-cycle surcharge + Day 0 fixed offset) | 55.5=1.14 / 55.6=0.92 (2) | mean **1.03** ✅ in band | KEEP 0.80 — 2-data-point sufficient |
| `medium-frontend` | 0.65 | 57.1=0.85 (1) | n/a 1-data-point | KEEP 0.65 baseline opens |
| `large multi-domain` | 0.55 | 56.1=1.00 / 56.3=1.04 / 57.2=0.77 / 57.11=0.47 / 57.12=0.75 (5) | 5-pt mean **0.81** (last-3 mean 0.66) — at/below lower edge of [0.85, 1.20] band | KEEP 0.55 baseline; `When to adjust` lower-trigger (3+ consecutive < 0.7) NOT met (only 57.11=0.47 of last 3); if 57.13 continues under 0.7 → AD-Sprint-Plan-N to split `large multi-domain` greenfield-heavy vs reuse-heavy (parallel to AD-Sprint-Plan-6 `mixed` split) |
| **`reality-check` (NEW Sprint 57.5)** | **0.85** | **57.5=1.04 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes AD-Sprint-Plan-7);pending 2-3 sprint window evidence** |
| **`reality-gap-fix` (NEW Sprint 57.6)** | **0.50** | **57.6=0.54 (1)** | **n/a 1-data-point** | **NEW class baseline opens;ratio below [0.85, 1.20] band by 0.31 → AD-Sprint-Plan-8 propose pending 2-3 sprint validation;potentially adjust to 0.35** |
| **`iam-frontend-spike` (NEW Sprint 57.7)** | **0.60** (HYBRID weighted blend: IAM × 0.60 + Frontend × 0.65 + Reality × 0.50 + closeout × 0.80) | **57.7=~0.92 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes AD-Sprint-Plan-9);1st app projected ~0.92 in [0.85, 1.20] band at lower edge;KEEP 0.60 baseline per `When to adjust` 3-sprint window rule;pending 2-3 sprint validation** |
| **`frontend-arch-spike` (NEW Sprint 57.8)** | **0.50** (HYBRID weighted blend: architecture × 0.55 + frontend × 0.65 + reuse-ship × 0.30) | **57.8=~1.50 (1)** | **n/a 1-data-point** | **NEW class baseline opens;1st app actual ~1.50 OVER [0.85, 1.20] band by 0.30 → AD-Sprint-Plan-10 propose split into `frontend-arch-greenfield` (0.45) vs `frontend-arch-reuse-ship` (0.35) after 2-3 more data points;KEEP 0.50 this sprint per 3-sprint window rule** |
| **`frontend-feature-with-migration` (NEW Sprint 57.9)** | **0.50** (HYBRID weighted blend: governance ship × 0.55 + 4-page TanStack pattern-reuse × 0.35 + 5 hook tests × 0.65) | **57.9=1.00 (1)** | **n/a 1-data-point** | **NEW class baseline opens;1st app ratio 1.00 ✅ bullseye in [0.85, 1.20] band;KEEP 0.50 baseline per `When to adjust` 3-sprint window rule;extends AD-Sprint-Plan-10 split proposal (vs 57.8 `frontend-arch-spike` 0.50 over band by 0.30 — pattern-reuse-heavy hits target)** |
| **`audit-cycle / docs / template` (NEW Sprint 57.10)** | **0.40** (per AD-Sprint-Plan-4 proposal Sprint 55.3) | **57.10=~1.63 (1)** | **n/a 1-data-point** | **NEW class baseline opens (folds in AD-Sprint-Plan-4 proposal);1st app ratio ~1.63 OVER [0.85, 1.20] band by 0.43 → AD-Sprint-Plan-12 propose 0.40 → 0.50 lift after 2-3 sprint validation per `When to adjust` rule;over band cause: Day 0.5 unplanned pivot from prior verification ship scope + Day 4 D-PRE-DAY4-1 dev DB cleanup overhead + 1114 lines NEW docs (CONVENTION 667 + STYLE 447) over-delivered vs 700 acceptance threshold +59%** |
| **`frontend-foundation-spike` (NEW Sprint 57.13)** | **0.50** (HYBRID weighted blend: auth-flow IAM-ish × 0.55 + design-system greenfield × 0.50 + obs/i18n/a11y/Lighthouse infra × 0.45 + auth-page reuse-ship × 0.30 + closeout × 0.80) | **57.13=~0.95–1.0 (1)** | **n/a 1-data-point** | **NEW class baseline opens;1st app ratio ~0.95–1.0 ✅ in [0.85, 1.20] band (actual hours estimated — not rigorously per-day-tracked; 13/15 USs full + 2 minimal-viable in 10 days matches the ~25-32 hr commit);KEEP 0.50 baseline per `When to adjust` 3-sprint window rule;pending 2-3 sprint validation** |
| **`frontend-e2e-sweep` (NEW Sprint 57.14)** | **0.50** (HYBRID weighted blend: test-maintenance-mechanical × 0.45 ~0.65 weight + ci-infra-new × 0.55 ~0.20 + closeout × 0.80 ~0.15) | **57.14=~1.05 (1)** | **n/a 1-data-point** | **NEW class baseline opens;1st app ratio ~1.05 ✅ in [0.85, 1.20] band; aggregate ratio bang-on even though US-A1/A2 over-estimated badly (regression was 1 test not broad churn — 1 hr vs ~5-8 hr bottom-up) — the fixed Day-0-plan + Day-N-closeout overhead the per-US bottom-up under-counts offsets it;KEEP 0.50 baseline per `When to adjust` 3-sprint window rule;pending 2-3 sprint validation — `AD-Frontend-E2E-Sweep` is a recurring shape whenever a large feature sprint outpaces its e2e specs** |
| **`frontend-refactor-mechanical` (NEW Sprint 57.15)** | **0.50** for 57.15+57.16; **0.80 for the 3rd+ application** (AD-Sprint-Plan-13) — HYBRID weighted blend: mechanical-refactor × 0.40-0.45 ~0.70 weight + ci-config+a11y × 0.55 ~0.10-0.15 + closeout × 0.80 ~0.15-0.20 | 57.15=~1.7 / **57.16=~1.9** (2) | 2-data-point mean **~1.8** ⬆️ OVER [0.85, 1.20] band | **2/2 over band on `actual/committed` (~1.7 then ~1.9) BUT both `actual/bottom-up` ≈ 0.89-0.96 — consistent: the bottom-up estimate IS accurate (mechanical refactors are low-variance/predictable), the 0.50 haircut doubled the committed estimate twice. Per `When to adjust` matrix note ("if next 1-2 also > 1.2 → AD-Sprint-Plan-N propose 0.50→0.70-0.80") → **AD-Sprint-Plan-13: the NEXT (3rd+) `frontend-refactor-mechanical` sprint uses 0.80** (near the top of the band like `medium-backend` 0.80 — a mechanical class belongs near the top, not the cautious mid-band; cf. `audit-cycle/docs/template` 0.40 over band in 57.10). KEEP 0.50 was the iteration rule for 57.15+57.16; the 0.80 lift applies forward. validated (2 consistent data points).** |
| **`frontend-css-engine-hotfix` (NEW Sprint 57.17)** | **0.60** (single-domain CSS config hotfix; not HYBRID since 1-line fix + targeted cascade fix + full-blast-radius validation are all in one config-engine class) | **57.17=0.75 (1)** | **n/a 1-data-point** | **NEW class baseline opens;1st app ratio 0.75 BELOW [0.85, 1.20] band by 0.10 (bottom-up was too conservative for a 1-line hotfix even with cascade fixes); ratio actual/bottom-up = 0.45;KEEP 0.60 baseline per `When to adjust` 3-sprint window rule (single below-band reading noted, not yet actionable);next data point likely AD-Tailwind-v4-Config-Migration (same class, larger scope — full v4 @theme inline migration ~6-8 hr standalone)** |
| **`mockup-integration-foundation` (NEW Sprint 57.18)** | **0.55** (HYBRID weighted blend: design-ref/mockup-cp × 0.40 ~15% + tailwind-tokens/HSL × 0.55 ~20% + routes-refactor 6-cat × 0.50 ~25% + stub-pages × 0.50 ~15% + sidebar-refactor × 0.65 ~15% + closeout × 0.80 ~10% = ~0.55 mid-band) | **57.18=1.10 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes Sprint 57.18 retrospective Q2 calibration);1st app ratio 1.10 ✅ bullseye in [0.85, 1.20] band;ratio actual/bottom-up = 0.58 (0.55 multiplier validated within ±5%);KEEP 0.55 baseline per `When to adjust` 3-sprint window rule;next data point likely Sprint 57.19+ if rolling port work uses same HYBRID blend shape (mockup design ref + new tokens + new routes + new components + sidebar updates)** |
| **`mockup-page-port-with-backend-pairing-and-audit` (NEW Sprint 57.19)** | **0.60** (HYBRID weighted blend: backend Cat 1/3/7/11 ABC stubs × 0.55 ~25% + frontend mockup-port pages × 0.55 ~50% + audit pass × 0.85 ~15% + closeout × 0.80 ~10%) | **57.19=0.56 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes Sprint 57.19 retrospective Q2 calibration);1st app ratio actual/committed 0.56 BELOW [0.85, 1.20] band by 0.29 (ratio actual/bottom-up = 0.34 → bottom-up 2× too generous, 0.60 haircut insufficient);KEEP 0.60 baseline per `When to adjust` 3-sprint window rule;next data point likely Sprint 57.21+ if Round 3 (Auth 4 paired with IAM Block B) uses same class blend;if ratio < 0.7 pattern recurs 2-3× → AD-Sprint-Plan-NEW propose 0.60 → 0.40** |
| **`frontend-mockup-direct-port` (NEW Sprint 57.20)** | **0.55** (HYBRID weighted blend: shell rewrite × 0.55 ~35% + per-page mockup-direct port × 0.50 ~50% + closeout × 0.80 ~15%) | 57.20=0.50 / **57.21=1.20** (2) | 2-data-point mean **0.85** at lower band edge — **bimodal pattern** | **2nd app (Sprint 57.21) ratio 1.20 ✅ top of [0.85, 1.20] band — validates Sprint 57.20 retro footer prediction "if 57.21+ hits structural rewrite → ratio swings back into band". Bimodal pattern confirmed**: token-sweep apps (57.20) ratio ~0.50 below band; structural-rewrite apps (57.21 — types.ts + chatStore.ts mergeEvent + 9 NEW Day 2 components + Inspector 4-tab) ratio ~1.20 top of band. `actual/bottom-up` ratios: 57.20=0.27 vs 57.21=0.67 (bottom-up systematically 1.5-2× generous regardless of sub-mode). **KEEP 0.55 baseline** per `When to adjust` 3-sprint window rule (2 data points insufficient for split). **If 3rd app continues bimodal** → AD-Sprint-Plan-NEW propose split into `frontend-mockup-direct-port-token-sweep` (0.40) vs `frontend-mockup-direct-port-structural` (0.85, near top of band like `medium-backend` 0.80 + Sprint 57.16 AD-Sprint-Plan-13 mechanical-class rule). Next data point: Sprint 57.22+ AD-Mockup-Direct-Port-Round-2 (token-sweep predicted) or AD-ChatV2-Full-Mockup-Fidelity Phase-2 (structural predicted). |
| **`frontend-mockup-fidelity-audit` (NEW Sprint 57.22)** | **0.85** (single-class audit-only sprint — code-level diff + mockup excerpt Read + per-unit severity + score + rebuild estimate; no production code changes) | **57.22=0.51 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes Sprint 57.22 retrospective Q2 calibration);1st app ratio actual/committed 0.51 SIGNIFICANTLY BELOW [0.85, 1.20] band by 0.34;ratio actual/bottom-up = 0.44 (bottom-up was 2× generous, 0.85 haircut insufficient);KEEP 0.85 baseline per `When to adjust` 3-sprint window rule (1-data-point insufficient for adjustment);if pattern recurs 2-3× propose 0.85 → 0.45-0.55 to reflect methodology speedup (Day 1 Playwright screenshot vs Day 2-3 code-level audit + PROP stub triage 2-2.5× faster per unit);Phase 57.23+ rebuild sprints proposed NEW class `frontend-mockup-strict-rebuild` 0.55-0.65 (distinct from audit class) per Sprint 57.22 AUDIT-REPORT §Sprint 57.23+ Recommendation |
| **`frontend-mockup-strict-rebuild` (NEW Sprint 57.23)** | **0.60** (HYBRID weighted blend per Sprint 57.22 AUDIT-REPORT §Sprint 57.23+ Recommendation: auth-flow IAM-ish × 0.55 ~25% + mockup-direct-port-structural × 0.85 ~30% + 4-step wizard × 0.50 ~15% + 6-digit input grid × 0.55 ~15% + AP-2 banner reuse × 0.40 ~15% = ~0.60 mid-band) | 57.23=0.59 / 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 / 57.37A≈1.18 / 57.40≈0.36 / **57.41≈0.18** (7) | 7-pt mean **0.76** at lower band edge | **7th app (Sprint 57.41 /verification recent view full rebuild — closes drift audit 2026-05-25 #2 priority CATASTROPHIC verdict: 6 NEW components VerificationPageHeader/StatsStrip/RunsTable/FailureKindsCard/FlakyChecksCard/View + VerificationList.tsx orphan-delete 299 lines per Karpathy §3 + 9 NEW Vitest specs +112-225% over +5-8 target + route-sweep `/verification/recent` envelope mock 2nd application + drift audit report PARITY update + 3-way evidence pair) ratio actual/committed ~0.18 BELOW [0.85, 1.20] band by 0.67 — **deepest below-band of class history**. 7-pt mean 0.76 at lower band edge (-0.10 vs prior 6-pt 0.86). Per `When to adjust` 3-sprint window rule: last 3 ratios 57.37A~1.18 + 57.40~0.36 + 57.41~0.18 → 2 of last 3 < 0.7 → **lower-trigger NOT yet met** (need 3+ consecutive) but very close → KEEP 0.60 per rule; flag for Sprint 57.42 retro 8th data point check. Root cause: code-implementer agent-delegation 8th+9th consecutive ~25-30 min wall-clock per day (~1.5 hr full sprint) for 6 NEW + 9 NEW specs + e2e adapt + envelope mock (human-equivalent ~8-10 hr) not modeled in baseline — **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` now has 4 data points across 2 classes** (57.39=0.41 + FIX-015 outlier + 57.40=0.36 + 57.41=0.18 all agent-delegated < 0.7) — **activation criteria technically met** (3+ cross-class points); propose Sprint 57.42 retro structural evaluation (Option A multiplicative `agent_factor` 0.55 OR Option B per-class sub-class split). Pattern-reuse acceleration: 2 of Sprint 57.40's 5 NEW components transferred via mild rename (ApprovalsPageHeader→VerificationPageHeader; ApprovalsStatsStrip→VerificationStatsStrip with Pass rate compute swap) — only 4 NEW unique components required + 6th VerificationView container. **/verification drift-audit verdict 🔴 CATASTROPHIC → ✅ PARITY** confirmed via 3-way evidence pair (BEFORE 79.9 KB / AFTER 133.0 KB / MOCKUP 207.2 KB). 22-route sweep: 22 IDENTICAL + 1 expected CHANGED (verification +66.4%) + 1 noise CHANGED (overview -44 bytes sub-300 envelope) + 0 unintended regressions — **cleanest sweep of Phase-2 epic**. Prior 6-app data: 57.23=0.59 / 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 / 57.37A≈1.18 / 57.40=0.36 — 6-pt mean 0.86.** |
| **`frontend-mockup-strict-rebuild` (NEW Sprint 57.23) — historical** | (same — 4-pt mean was 0.90 in band lower-middle; rich-only 3-pt mean 1.01 in-band middle) | n/a (collapsed into row above for compactness) | n/a | **4th app (Sprint 57.27 /overview rebuild) ratio ≈0.95 ✅ in [0.85, 1.20] band (estimated — agent-assisted compressed session, not rigorously per-day-tracked; same caveat as Sprint 57.13). 4-pt mean 0.90 well in-band. **#41 rich-dashboard sub-class DECISION = DROPPED (no split)**: /overview is a rich operator dashboard (2 charts + 4-stat KPI + 4 cards); rich-subset 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 → 3-pt mean ~1.01 squarely in-band middle → no distinct rich-dashboard cost signal to justify a separate multiplier. `AD-Sprint-Plan-rich-dashboard-sub-class-DEFER` #41 RESOLVED. KEEP the single `frontend-mockup-strict-rebuild` 0.60 baseline for the whole class per `When to adjust` 3-sprint window rule. Reasons for 57.27 ≈0.95: 9 widgets but heavy reuse of CardShell/_primitives/BackendGapBanner + the Day-1-established widget pattern (no primitive extraction cost); 2 code-implementer agent delegations did the bulk; `actual/bottom-up` ≈ 0.57 (bottom-up ~1.7× generous; 0.60 multiplier landed close).** |
| **`frontend-foundation-token-correction` (NEW Sprint 57.26)** | **0.55** (HYBRID weighted blend: css-token-edit × 0.60 ~25% + 22-route regression sweep × 0.50 ~50% + shell-component edit × 0.50 ~15% + closeout × 0.80 ~10% ≈ 0.55) | **57.26=0.91 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes Sprint 57.26 retrospective Q2 calibration); 1st app ratio actual/committed 0.91 ✅ in [0.85, 1.20] band; ratio actual/bottom-up = 0.50 (bottom-up 2× generous; 0.55 multiplier close to right); KEEP 0.55 baseline per `When to adjust` 3-sprint window rule (1-data-point insufficient for adjustment); sprint = global foundation-token correction across 22 routes (font 13px baseline + sidebar 232 + main padding + bg hue + radius px), distinct from the `frontend-mockup-strict-rebuild` rebuild epic; next data point if another global-CSS / foundation-correction sprint runs** |
| **`frontend-verbatim-css-foundation` (NEW Sprint 57.28)** | **0.55** (HYBRID weighted blend: Layer-2 verbatim-copy × 0.40 ~10% + Layer-3 index.css slim × 0.55 ~15% + Layer-4 bridge+collision × 0.60 ~20% + theme toggle × 0.55 ~10% + CI guard authoring × 0.55 ~15% + 22-route regression sweep × 0.50 ~20% + closeout × 0.80 ~10% ≈ 0.55) | **57.28≈1.05 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes Sprint 57.28 retrospective Q2 calibration); 1st app ratio actual/committed ≈1.05 ✅ in [0.85, 1.20] band (estimated — agent-assisted compressed session, not rigorously per-day-tracked; same caveat as Sprint 57.13/57.27); ratio actual/bottom-up ≈0.59 (bottom-up ~1.7× generous; 0.55 multiplier close to right); KEEP 0.55 baseline per `When to adjust` 3-sprint window rule (1-data-point insufficient); sprint = verbatim-CSS 4-layer foundation switch (Layer 2 byte-identical copy + Layer 3 index.css slim + Layer 4 tailwind bridge + theme + CI guard), distinct from `frontend-foundation-token-correction` (57.26 — corrected token values in place) — this switches the CSS delivery method** |
| **`frontend-verbatim-css-repoint -simple` (Sprint 57.38 Option 2 split — applies when ALL hold: single/few files ≤3 / no AP-2 banner / no dual-mount / no playback/filter widgets / HEX_OKLCH_BASELINE bump < 4)** | **0.50** | 57.34≈1.0 (/orchestrator config/6-tab) / **57.38B≈0.91-1.09 estimated** (/subagents single-file KPI+2-col+Tabs+table+1 oklch; agent-assisted ~30 min wall-clock; human-equivalent ~2.5-3 hr solo) (2 total) | 2-pt mean **~1.0** ✅ in band middle | **2nd app (Sprint 57.38 Domain B) Day 0 D5 originally reclassified `-with-extras` (cautious) but Day 3 closeout re-evaluated: 0/5 strict `-with-extras` criteria met → classified `-simple` 2nd app. KEEP 0.50 per `When to adjust` 3-sprint window rule (2-pt mean 1.0 in-band middle; healthy). Class-split decision per Sprint 57.37 NEW `AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal` (CLOSED Sprint 57.38).** |
| **`frontend-verbatim-css-repoint -with-extras` (Sprint 57.38 Option 2 split — applies when ANY hold: multi-file batched >3 / AP-2 BackendGapBanner addition / dual-mount preservation / playback/filter/inspector widgets / HEX_OKLCH_BASELINE bump ≥4)** | **0.65** | 57.35≈1.7 / 57.36≈1.42 / 57.37B≈1.33 (3 historical pre-split at 0.50; equivalent ~1.31/~1.09/~1.02 at 0.65) + **57.39≈0.41 (1st deliberate-test at 0.65)** — 4-domain batched (A /governance + B /verification re-point + C /redaction + D /error-policy PROP→real); agent-delegated Day 1+Day 2 ~13 min wall-clock; +14 NEW Vitest specs; HEX_OKLCH_BASELINE 51 unchanged (4 total) | historical 3-pt mean **1.48 at 0.50** → equivalent **~1.14 at 0.65** in band; **Sprint 57.39 1st deliberate-test 0.41 BELOW band [0.85, 1.20] by 0.44**; combined 4-pt mean ~1.04 lower-band-edge | **1st deliberate-test data point** Sprint 57.39 ratio 0.41 significantly below band. Root cause: code-implementer agent-delegation (6th+7th consecutive) ~3-5× speedup vs human-rewrite estimates not modeled in 0.65 baseline. Per `When to adjust` 3-sprint window rule (3+ consecutive < 0.7 required), **KEEP 0.65 this iteration** (1-data-point insufficient). NEW `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` proposes quantifying agent-delegation as multiplier-on-multiplier (~0.30-0.40 effective for `-with-extras + agent-delegated` sub-class); defer 2-3 sprint validation. If 57.40+ continues < 0.7 → propose 0.65 → 0.35-0.40 lift OR sub-class split. |
| **`frontend-verbatim-css-repoint` historical (Sprint 57.29-57.37 single-baseline pre-split)** | (collapsed; superseded by `-simple` + `-with-extras` rows above per Sprint 57.38 Day 3 retro Option 2 decision) | rich (1-file each): 57.29≈1.0 / 57.30≈0.40 / 57.31≈0.35 / 57.32~0.40-0.55; non-rich/-simple: 57.34≈1.0; non-rich/-with-extras: 57.35~1.7 / 57.36~1.42 / 57.37B~1.33 (8 total pre-split) | 8-pt span 0.35-1.75 | **Class CLOSED Sprint 57.38** via Option 2 split. All 3 carryover ADs CLOSED: `class-split-proposal` (57.37 NEW) / `multi-dimensional-variance-watch` (57.36 NEW) / `baseline-lift` (57.31 NEW). Historical data preserved for traceability. Use `-simple` (0.50) or `-with-extras` (0.65) per criteria rules above for new sprints. |
| **`frontend-page-bug-fix` (NEW Sprint 57.33)** | **0.45** (HYBRID weighted blend: audit-cycle × 0.85 ~15% + mechanical defensive-guard × 0.45 ~50% + medium-frontend Vitest spec × 0.65 ~20% + 22-route sweep × 0.50 ~10% + closeout × 0.80 ~5% ≈ 0.52; anchored slightly below at 0.45 since mechanical-refactor majority weight) | **57.33=1.24 (1)** | **n/a 1-data-point** | **NEW class baseline opens (closes `AD-Overview-PreExisting-Route-Crashes` Sprint 57.29-32 carryover; 1st application). 1st app ratio actual/committed 1.24 ✅ top edge of [0.85, 1.20] band +0.04 over (essentially at top); ratio actual/bottom-up = 0.57 (bottom-up 1.75× generous; 0.45 multiplier close-but-slightly-tight); KEEP 0.45 baseline per `When to adjust` 3-sprint window rule (1-data-point insufficient). Sprint = 3 ⚪ crash routes fix (subagents + memory + verification — defensive `(query.data.X ?? []).length/map` guard across 5 files / 11 sites including drift D1-D4 found by widening Day 0 grep from `.length` only to `.map` + function-arg passing). 4 NEW Vitest defensive specs across SubagentsPage/MemoryRecentList/MemoryByScopeBrowser/VerificationList (Vitest 452→456). 22-route sweep: 3 ⚪ → ✅ flip + 0 regressions. Unblocks future Phase-2 re-point on these 3 routes. If next 2-3 applications show consistent ratio > 1.20 → propose 0.45 → 0.55-0.60 lift (mechanical-class-like trend, parallel to Sprint 57.16 AD-Sprint-Plan-13 `frontend-refactor-mechanical` 0.50 → 0.80 evidence). Next data point Sprint 57.34+ if more `length/map crash` or similar shape-divergence bug-fix sprints occur.** |

**Modification History**:
- 2026-05-25: Sprint 57.41 Day 3 — `frontend-mockup-strict-rebuild` 7th data point 57.41≈0.18 BELOW band by 0.67 (deepest below-band of class history; single-domain /verification recent view full rebuild: 6 NEW components incl. 2 Sprint-57.40-renames + VerificationList.tsx orphan delete 299 lines + 9 NEW Vitest specs + envelope mock 2nd application + 3-way evidence pair); 7-pt mean **0.76** at lower band edge (-0.10 vs 6-pt 0.86); last 3 only 2 < 0.7 → lower-trigger NOT yet met (need 3+) → KEEP 0.60 per 3-sprint window rule; root cause = code-implementer agent-delegation 8th+9th consecutive ~25-30 min wall-clock per day (~1.5 hr full sprint vs ~8-10 hr human-equivalent) not modeled; **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` now 4 data points across 2 classes** (57.39 -with-extras 0.41 + FIX-015 outlier + 57.40 mockup-strict-rebuild 0.36 + 57.41 mockup-strict-rebuild 0.18) — **activation criteria met** (3+ cross-class points); propose Sprint 57.42 retro structural evaluation (Option A `agent_factor` 0.55 OR Option B per-class split); 22-route sweep cleanest of Phase-2 epic (22 IDENTICAL + 1 expected + 1 sub-300-byte noise + 0 unintended); 18 PARITY + 1 NEAR-PARITY + 3 CATASTROPHIC remaining (/memory + /admin-tenants + /tenant-settings).
- 2026-05-25: Sprint 57.40 Day 3 — `frontend-mockup-strict-rebuild` 6th data point 57.40≈0.36 BELOW band by 0.49 (single-domain /governance Approvals view full rebuild: 5 NEW components + KvRow primitive + ApprovalsPage restructure 73→115 + ApprovalList 6→7-col + DecisionModal Karpathy §3 delete + 15 NEW Vitest specs + envelope mock fix + drift audit /governance ✅ PARITY); 6-pt mean **0.86** at lower band edge (-0.10 vs 5-pt 0.96); last 3 only 1 < 0.7 → lower-trigger NOT met → KEEP 0.60 per 3-sprint window rule; root cause = code-implementer agent-delegation 7th consecutive ~40 min wall-clock for 5 NEW + 1 primitive + 2 restructures (human ~6-8 hr) not modeled; **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` now 3 data points across 2 classes** (57.39 -with-extras 0.41 + FIX-015 outlier + 57.40 mockup-strict-rebuild 0.36) — activation rule technically met but spans classes; defer 1 more sprint for 4th data point; Phase-2 epic progress 15/17 → audit-corrected reality 17 PARITY + 1 NEAR-PARITY + 4 CATASTROPHIC remaining (drift audit 2026-05-25 #3 /governance closed)
- 2026-05-24: Sprint 57.39 Day 3 — `frontend-verbatim-css-repoint -with-extras` **1st deliberate-test data point** 57.39≈0.41 BELOW band by 0.44 (4-domain batched: A /governance + B /verification re-point + C /redaction + D /error-policy PROP→real; agent-delegated Day 1+Day 2 ~13 min wall-clock for all 4 routes; +14 NEW Vitest specs; HEX_OKLCH_BASELINE 51 unchanged); 4-pt combined mean ~1.04 lower-band-edge; KEEP 0.65 this iteration per 3-sprint window rule (1-data-point insufficient); root cause = code-implementer agent-delegation 6th+7th consecutive ~3-5× speedup not modeled in baseline; NEW `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` proposes quantifying speedup as multiplier-on-multiplier (~0.30-0.40 for `-with-extras + agent-delegated` sub-class) — defer 2-3 sprint validation; if 57.40+ continues < 0.7 → propose 0.65 → 0.35-0.40 lift OR sub-class split; Phase-2 epic 11/17 → 15/17 routes shipped / 2 🟡 Phase 58+ STRUCTURAL remaining; 5 NEW carryover ADs (child-component re-point + Day 0 Prong 2 depth + sweep coverage extend + cwd-relative OUT_DIR fix + agent-delegation modifier).
- 2026-05-24: Sprint 57.38 Day 3 — **Option 2 class split applied** for `frontend-verbatim-css-repoint`: → `-simple` (0.50; criteria 0/5 extras) + `-with-extras` (0.65; criteria ANY/5 extras: multi-file>3 / AP-2 banner / dual-mount / playback widgets / HEX_OKLCH_BASELINE bump≥4). Sprint 57.38 Domain B `/subagents` classified `-simple` 2nd app (0/5 criteria; KPI+2-col+Tabs+table+1 oklch literal does NOT meet strict criteria); ratio ≈0.91-1.09 estimated (agent-assisted). 3 carryover ADs CLOSED: `class-split-proposal` (57.37 NEW) / `multi-dimensional-variance-watch` (57.36 NEW) / `baseline-lift` (57.31 NEW). Domain C `AD-FullBleed-Pages-Audit` (FIX-010 follow-up) found 0 sites missing — not a calibration data point. Sprint blended HYBRID ratio ≈0.95-1.05 in band middle.
- 2026-05-24: Sprint 57.37 Day 4 — 2-domain batched (Sprint 57.36 user-reported `/loop-debug` empty-state RESOLVED + `/state-inspector` Phase-2 re-point); **Domain A `frontend-mockup-strict-rebuild` 5th data point 57.37A~1.18 IN BAND top edge** (5-pt mean 0.96 in-band middle; class healthy; KEEP 0.60); **Domain B `frontend-verbatim-css-repoint` 8th data point + 4th non-rich 57.37B~1.33 ABOVE band by 0.13** → **3-consecutive-above-band lift trigger MET** (57.35+57.36+57.37B all > 1.20); Sprint 57.38 retro decision needed — Option 1 class-wide lift 0.50→0.60 OR Option 2 class split `-simple` (0.50) vs `-with-extras` (0.65); D-DAY3-1 positive surprise: StateInspector spec NO update needed (class-swap-resilient text-based assertions); HEX_OKLCH_BASELINE 41→50 (within Day 0 D-DAY0-6 +5-10 estimate); Vitest 464/464 (+8 NEW Domain A); 22-route sweep 18 IDENTICAL + 4 CHANGED (chat-v2 0 B PERFECT cascade); sprint total HYBRID ratio ~1.0 IN BAND middle (2-domain batching averaged class-level variance cleanly); agent-assisted Day 1-3 (4th consecutive code-implementer)
- 2026-05-24: Sprint 57.36 Day 4 — `frontend-verbatim-css-repoint` 7th data point 57.36~1.42 ABOVE band by 0.22 (/loop-debug LoopVisualizer.tsx single-file dual-mount + AP-2 BackendGapBanner); CLOSE `AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch` REJECTED (3 non-rich pts 1.0/1.7/1.42 not bimodal); WEAKENED `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` (1-file 57.36 also above band; file-count not sole driver); NEW `AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch` — emerging compound drivers (file count + AP-2 + dual-mount + drift overhead) require multi-D treatment; if 57.37+ continues > 1.20 → propose 0.50 → 0.60 lift OR class split simple/with-ap2-or-dual-mount; KEEP 0.50 this iteration per `When to adjust` 3-sprint window rule; agent-assisted Day 1-2 (3rd consecutive)
- 2026-05-24: Sprint 57.35 Day 4 — `frontend-verbatim-css-repoint` 6th data point 57.35~1.65-1.75 ABOVE band by ~0.45-0.55 (AuthShell + 7 auth routes 8-file batched re-point + 4 Vitest spec updates; user-reported /auth/login drift 2026-05-24 fully RESOLVED; closes Sprint 57.23 vintage HSL-translation epic gap); 6-pt span 0.35-1.75 — bimodal-by-shape hypothesis WEAKENED (57.34 1-file non-rich ≈1.0 in band vs 57.35 8-file non-rich ~1.7 above band), file-count + spec-update overhead emerging as 2nd variance driver; KEEP 0.50 per 3-sprint window rule; NEW `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` (propose file-count surcharge 0.50 + 0.05/extra-file beyond 3 if 57.36+ multi-file > 1.20); update shape-bimodal-watch AD to broaden scale-and-shape — don't propose class split until 4th data point discriminates
- 2026-05-24: Sprint 57.34 Day 4 — `frontend-verbatim-css-repoint` 5th data point 57.34≈0.95-1.05 in band middle (1st non-rich-dashboard shape — /orchestrator config/tabbed-forms; agent-assisted Day 1-3 via code-implementer); bimodal-by-shape signal emerging (rich 3-pt mean ≈0.40 below band vs non-rich 1-pt ≈1.0 in band middle); 2-data-point span insufficient per 3-sprint window rule; KEEP 0.50; NEW `AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch` — if Sprint 57.35 (another non-rich shape) confirms in-band → propose class split `-rich-dashboard` (0.40) vs `-config-form` (0.50); if below-band → class-wide variance → 0.50 → 0.40 lift
- 2026-05-24: Sprint 57.33 Day 4 — +1 NEW row `frontend-page-bug-fix` 0.45 HYBRID weighted blend (audit-cycle 0.85 ~15% + mechanical-defensive-guard 0.45 ~50% + medium-frontend Vitest 0.65 ~20% + sweep 0.50 ~10% + closeout 0.80 ~5%) 1-data-point ratio actual/committed 1.24 ✅ top edge [0.85, 1.20] band +0.04 over (essentially at top); ratio actual/bottom-up 0.57 (bottom-up 1.75× generous; 0.45 multiplier close to right); KEEP 0.45 baseline per `When to adjust` 3-sprint window rule (1-data-point insufficient for adjustment); sprint = 3 ⚪ crash routes fix (/subagents + /memory + /verification — defensive `?? []` on `query.data.{items,entries}` access), distinct from epic re-point work — unblocks future Phase-2 re-point on these 3 routes
- 2026-05-24: Sprint 57.32 Day 4 — `frontend-verbatim-css-repoint` 4th data point 57.32~0.40-0.55 (1st validation of lifted 0.50 baseline; /sla-dashboard 7 files; 0 production-only widgets cleanest mockup mapping); 4-pt mean ≈0.55 lower band edge; KEEP 0.50 per `When to adjust` 3-sprint window rule (1 validation pt insufficient); if 57.33+57.34 also < 0.7 → propose 0.50 → 0.40 in 57.34 retro
- 2026-05-23: Sprint 57.31 Day 4 — `frontend-verbatim-css-repoint` 3rd data point 57.31≈0.35 BELOW band by 0.55 (cost-dashboard 7 components batched Day 1); 3-pt mean ≈0.58 lower edge; bimodal hypothesis REJECTED (57.29 + 57.31 same shape ≠ same ratio); LIFT baseline 0.60 → 0.50; CLOSE `AD-Sprint-Plan-frontend-verbatim-bimodal-watch`; NEW `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` validates 0.50 next 2-3 sprints
- 2026-05-23: Sprint 57.30 Day 5 — `frontend-verbatim-css-repoint` 2nd data point 57.30≈0.40 BELOW band by 0.45 (chat-v2 19 components + Day 1 hotfix bundled); 2-pt mean 0.70 lower edge; KEEP 0.60 per 3-sprint window rule (2 pts insufficient); NEW `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` — if 3rd low, propose split structural-heavy 0.65 vs css-swap-only 0.40
- 2026-05-22: Sprint 57.29 Day 5 — +1 NEW row `frontend-verbatim-css-repoint` 0.60 HYBRID weighted blend 1-data-point ratio ≈1.0 ✅ in [0.85, 1.20] band (estimated, agent-assisted session); KEEP 0.60 baseline per `When to adjust` 3-sprint window rule; sprint = first Phase-2 per-page verbatim-CSS re-point (/overview + shell + overlays + 7 widgets), distinct from 57.28 foundation-only switch
- 2026-05-22: Sprint 57.28 Day 4 — +1 NEW row `frontend-verbatim-css-foundation` 0.55 HYBRID weighted blend 1-data-point ratio ≈1.05 ✅ in [0.85, 1.20] band (estimated, agent-assisted session); ratio actual/bottom-up ≈0.59; KEEP 0.55 baseline per `When to adjust` 3-sprint window rule; sprint = verbatim-CSS 4-layer foundation switch, distinct from 57.26 token-value correction
- 2026-05-21: Sprint 57.27 Day 3 — `frontend-mockup-strict-rebuild` 4th data point 57.27≈0.95 ✅ in [0.85, 1.20] band (estimated, agent-assisted session); 4-pt mean 0.90; **#41 rich-dashboard sub-class DROPPED (no split)** — rich-subset 57.24/57.25/57.27 3-pt mean ~1.01 in-band middle, no distinct cost signal; `AD-Sprint-Plan-rich-dashboard-sub-class-DEFER` #41 RESOLVED; KEEP single 0.60 baseline
- 2026-05-21: Sprint 57.26 Day 3 — +1 NEW row `frontend-foundation-token-correction` 0.55 HYBRID weighted blend (css-token-edit 0.60 + 22-route sweep 0.50 + shell-edit 0.50 + closeout 0.80) 1-data-point ratio 0.91 ✅ in [0.85, 1.20] band (ratio actual/bottom-up = 0.50, bottom-up 2× generous, 0.55 multiplier close to right); KEEP 0.55 baseline per `When to adjust` 3-sprint window rule; sprint = global foundation-token correction across 22 routes (font 13px baseline + shell layout), distinct from the rebuild epic — corrects the shared baseline so future rebuild sprints start from a mockup-faithful foundation
- 2026-05-19: Sprint 57.25 Day 3 — `frontend-mockup-strict-rebuild` 3rd data point 57.25=0.88 ✅ in-band lower edge of [0.85, 1.20] band; rich-dashboard 2-pt mean 1.04 (57.24 v2 1.19 + 57.25 0.88) in-band middle → rich-dashboard sub-class hypothesis from Sprint 57.24 v2 retro Q4 NOT confirmed; **KEEP 0.60 baseline + DEFER sub-classification (AD-Sprint-Plan-rich-dashboard-sub-class-DEFER #41)** per `When to adjust` 3-sprint window rule; reasons for 0.88: reuses 7 Sprint 57.24 v2 primitives without API change validating Karpathy §2 ROI ~1.5 hr saved; ratio actual/bottom-up = 0.53 (bottom-up 1.9× generous); next data point Sprint 57.26 admin-tenants rebuild — if 4th rich ratio in band → DROP sub-class proposal entirely; if > 1.20 → reconsider rich at 0.70-0.75
- 2026-05-19: Sprint 57.24 v2 Day 3 — `frontend-mockup-strict-rebuild` 2nd data point 57.24=1.19 ✅ top of [0.85, 1.20] band; 2-point span 0.59→1.19 crosses entire band (auth-flow 7 small routes vs 1 rich dashboard page); KEEP 0.60 baseline per `When to adjust` 3-sprint window rule (2 data points insufficient); if 3rd app (Sprint 57.25 sla-dashboard rebuild — same rich-dashboard shape) continues high variance → propose split into `-auth-flow` (0.55) vs `-dashboard-rich` (0.65); ratio actual/bottom-up = 0.71 (bottom-up 1.4× generous; 0.60 haircut close to right size)
- 2026-05-18: Sprint 57.23 Day 4 — +1 NEW row `frontend-mockup-strict-rebuild` 0.60 HYBRID weighted blend 1-data-point ratio 0.59 BELOW [0.85, 1.20] band by 0.26 (ratio actual/bottom-up = 0.36 — bottom-up 2.8× too generous, 0.60 haircut insufficient); reasons: mockup line-by-line port discipline + Sprint 57.18 tokens pre-aligned + AP-2 banner + AuthShell footer pattern reuse 3-7× each; KEEP 0.60 baseline per `When to adjust` 3-sprint window rule; if pattern recurs 2-3× propose 0.60 → 0.40-0.45 (mechanical-class lift parallel to Sprint 57.16 AD-Sprint-Plan-13)
- 2026-05-18: Sprint 57.22 Day 4 — +1 NEW row `frontend-mockup-fidelity-audit` 0.85 HYBRID single-class audit-only 1-data-point ratio 0.51 SIGNIFICANTLY BELOW [0.85, 1.20] band by 0.34 (ratio actual/bottom-up = 0.44 — bottom-up 2× too generous, 0.85 haircut insufficient); methodology shift Day 1→Day 2 explains speedup (Playwright screenshot ~30 min/unit → code-level audit + PROP stub triage ~10-15 min/unit); KEEP 0.85 baseline per `When to adjust` 3-sprint window rule; if pattern recurs 2-3× propose 0.85 → 0.45-0.55; Phase 57.23+ rebuild sprints proposed distinct NEW class `frontend-mockup-strict-rebuild` 0.55-0.65 per AUDIT-REPORT §Sprint 57.23+ Recommendation
- 2026-05-18: Sprint 57.21 Day 4 — `frontend-mockup-direct-port` 2nd data point 57.21=1.20 ✅ top of band (validates Sprint 57.20 retro footer); 2-data-point bimodal pattern (57.20=0.50 token-sweep / 57.21=1.20 structural-rewrite); KEEP 0.55 baseline; if 3rd app continues bimodal → AD-Sprint-Plan-NEW split into `-token-sweep` (0.40) vs `-structural` (0.85)
- 2026-05-17: Sprint 57.19 Day 5 — +1 NEW row `mockup-page-port-with-backend-pairing-and-audit` 0.60 HYBRID weighted blend 1-data-point ratio 0.56 BELOW [0.85, 1.20] band by 0.29 (ratio actual/bottom-up = 0.34 — bottom-up 2× too generous, 0.60 haircut insufficient); KEEP 0.60 baseline per `When to adjust` 3-sprint window rule; if pattern recurs 2-3× propose 0.60 → 0.40
- 2026-05-16: Sprint 57.18 Day 3 — +1 NEW row `mockup-integration-foundation` 0.55 HYBRID weighted blend 1-data-point ratio 1.10 ✅ bullseye in [0.85, 1.20] band (ratio actual/bottom-up = 0.58 validates 0.55 multiplier within ±5%); KEEP 0.55 baseline per `When to adjust` 3-sprint window rule
- 2026-05-15: Sprint 57.17 Day 3 — +1 NEW row `frontend-css-engine-hotfix` 0.60 1-data-point ratio 0.75 below band by 0.10 (bottom-up too conservative for 1-line hotfix + targeted cascade); KEEP 0.60 baseline per `When to adjust` 3-sprint window rule; next data point likely AD-Tailwind-v4-Config-Migration (same class)
- 2026-05-11: Sprint 57.16 Day 3 — `frontend-refactor-mechanical` 2nd data point 57.16=~1.9 (over band again; `actual/bottom-up` ≈ 0.96 — bottom-up accurate); 2/2 over band → AD-Sprint-Plan-13: 0.50→0.80 for the 3rd+ application (KEEP 0.50 was the rule for 57.15+57.16)
- 2026-05-11: Sprint 57.15 Day 3 — +1 NEW row `frontend-refactor-mechanical` 0.50 1-data-point ratio ~1.7 OVER band (bottom-up was accurate; 0.50 haircut too aggressive for a low-variance class); KEEP 0.50 (1 data point) — if recurs propose 0.70-0.80
- 2026-05-10: Sprint 57.14 Day 3 — +1 NEW row `frontend-e2e-sweep` 0.50 1-data-point ratio ~1.05 in band; KEEP 0.50 baseline
- 2026-05-10: Sprint 57.13 Day 9 — +1 NEW row `frontend-foundation-spike` 0.50 1-data-point ratio ~0.95–1.0 in band; KEEP 0.50 baseline
- 2026-05-10: Sprint 57.12 Day 4 — `large multi-domain` 5th data point 57.12=0.75; 5-pt mean 0.81 (stable vs 4-pt 0.82); KEEP 0.55 — lower-trigger (3+ consecutive < 0.7) not met (only 57.11 of last 3); if 57.13 drifts → AD-Sprint-Plan-N split greenfield vs reuse-heavy
- 2026-05-10: Sprint 57.11 Day 4 — `large multi-domain` 4th data point 57.11=0.47; 4-data-point mean 0.82 (down from 0.94; lower edge of band); KEEP 0.55 baseline this iteration (pending 2-3 sprint window validation per `When to adjust` rule; if continued under 0.7 → propose 0.55→0.40 lift)
- 2026-05-09: Sprint 57.10 Day 4 — +1 NEW row `audit-cycle / docs / template` 0.40 1-data-point ratio ~1.63 OVER band (folds in AD-Sprint-Plan-4 proposal Sprint 55.3;NEW AD-Sprint-Plan-12 propose 0.50 lift after 2-3 sprint validation)
- 2026-05-09: Sprint 57.9 Day 4 — +1 NEW row `frontend-feature-with-migration` 0.50 1-data-point ratio 1.00 bullseye
- 2026-05-09: Sprint 57.8 Day 4 — +1 NEW row `frontend-arch-spike` 0.50 HYBRID weighted blend 1-data-point baseline (NEW AD-Sprint-Plan-10 propose split greenfield/reuse-ship)
- 2026-05-10: Sprint 57.7 Day 4 — +1 NEW row `iam-frontend-spike` 0.60 HYBRID weighted blend 1-data-point baseline (closes AD-Sprint-Plan-9)
- 2026-05-08: Sprint 57.6 Day 4 — add scope-class multiplier matrix (closes AD-Reality-10);+2 NEW rows `reality-check` 0.85 1-data-point baseline (closes AD-Sprint-Plan-7) + `reality-gap-fix` 0.50 1-data-point baseline (NEW AD-Sprint-Plan-8 pending 2-3 sprint validation)

#### Proposed Agent Delegation Factor Modifier (PENDING VALIDATION — 2026-05-25 Item #4 of post-Sprint-57.39 4-AD micro-fix sequence)

**Status**: **PROPOSAL — NOT yet active**. Logged per `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` (Sprint 57.39 retro Q4 #4); requires 2-3 sprint validation before applying to any active baseline. Existing matrix entries above are UNCHANGED by this proposal.

**Hypothesis**: code-implementer agent-delegated frontend work shows ~3-5× speedup vs the human-rewrite cadence the bottom-up estimates assume. Existing per-class multipliers (0.45-0.85) bake in a human-cadence haircut; agent-delegated sprints consistently undershoot the calibrated band lower edge because the haircut isn't enough.

**Evidence accumulating** (2 data points):

| Sprint / FIX | Class | Delegation | Ratio actual/committed | Ratio actual/bottom-up | Implied agent vs human speedup |
|--------------|-------|------------|------------------------|------------------------|--------------------------------|
| Sprint 57.39 | `-with-extras` (0.65 baseline) | 6th+7th consecutive code-implementer (4-domain batched) | **0.41** (BELOW [0.85, 1.20] band by 0.44) | 0.27 | ~3.7× |
| FIX-015 (post-hoc) | bundled FIX (no calibration class) | code-implementer 6 child re-point | n/a (no class) | bottom-up 6-10 hr / actual ~25 min ≈ 0.04 | ~24-40× (outlier — surgical token-swap) |

**Proposed embedding (Option A then B fallback)**:

**Option A — Multiplicative agent_factor coefficient** (1 new global coefficient; cleanest):

```
effective_calibrated_hours = bottom_up × scope_class_multiplier × agent_factor

where agent_factor = {
  human (default):      1.0
  agent-delegated:      0.50-0.60  (proposed start at 0.55 mid-band)
}
```

Equivalent combined ratio for `-with-extras` 0.65 base × 0.55 agent_factor ≈ **0.36** (close to AD spec's "0.30-0.40 effective" target).

Pros: 1 new global coefficient; doesn't require splitting every active class; trivial matrix change
Cons: assumes uniform speedup across classes; reality may differ by file count / structural complexity / mockup-truth availability

**Option B — Per-class sub-class split** (fallback if Option A undershoots for specific classes):

Add `+ agent-delegated` sub-row for each high-volume class:
- `-with-extras` (0.65; human) + `-with-extras + agent-delegated` (0.30-0.40)
- `frontend-mockup-strict-rebuild` (0.60; human) + `... + agent-delegated` (0.25-0.35)
- `frontend-verbatim-css-repoint -simple` (0.50; human) + `... + agent-delegated` (0.25-0.30)

Pros: per-class precision; matches existing matrix granularity
Cons: doubles row count for active classes; higher maintenance overhead

**Recommended**: Option A first (1 conservative coefficient, 1 sprint validation), fallback to Option B if Option A produces ratio < 0.7 or > 1.20 for ≥ 2 specific classes.

**Activation rule** (3-sprint window — parallel to existing `When to adjust the multiplier` discipline):
- ≥ 3 consecutive sprints with agent-delegated ratio < 0.7 AND consistent delegation pattern (≥ 80% of Day 1 work via agent) → **activate Option A** with `agent_factor = 0.55` (mid-band conservative start)
- If activated factor produces 2 sprints with ratio < 0.7 → tighten to 0.45
- If activated factor produces 1 sprint with ratio > 1.20 → roll back to 0.65 (single-data-point caution); ≥ 2 sprints > 1.20 → roll back to 1.0 (drop the modifier — agent delegation didn't actually accelerate that class)

**Current state**: **2 data points (57.39 + FIX-015) — INSUFFICIENT for activation**. Continue accumulating evidence per Sprint 57.39 retro Q4 #4 deferral.

**Tracking discipline going forward**: each future agent-delegated sprint MUST record in retrospective Q2:
1. `actual/bottom-up` ratio (existing)
2. `actual/committed` ratio (existing)
3. **NEW**: explicit `agent-delegated: yes / no / partial` tag (the running window can then be computed without ambiguity)

**Why this proposal matters**: 5 of the last 6 sprints (57.34 / 57.35 / 57.36 / 57.37B / 57.39) used code-implementer agent delegation as the primary Day 1 mechanism. The current matrix treats them as human-rewrite work, producing systematic ratio-below-band signals that look like "calibration drift" when they're actually "missing agent_factor coefficient". Activating Option A would correctly attribute the speedup AND reset the matrix to track real calibration drift (not delegation-vs-human-cadence drift).

---

### Step 2: Create Checklist File

**Immediately after plan approval**, create sprint checklist at `docs/03-implementation/agent-harness-planning/phase-XX-name/sprint-XX-Y-checklist.md`.

**Required Format**:
```markdown
# Sprint XX.Y — Checklist

[Link to plan]

## Day N — Task Group

### N.M Task Description
- [ ] **Specific deliverable**
  - DoD: Measurable definition of done
  - Command: `git ...` or `pytest ...`
- [ ] **Next deliverable**
  - ...
```

**Key Rules**:
- Use `- [ ]` format
- Each task should be a single logical unit (break down if checklist entry covers >1 commit's worth of work)
- Include DoD (Definition of Done) — how to verify
- Map each task to plan's acceptance criteria
- Assign to days (Day 1-5 for typical sprint)
- **DO NOT include time estimates in checklist** (since Sprint 55.3 / AD-Lint-2):
  - ❌ ~~`## Day N — Task Group (Estimated X hours)`~~ — drop "(Estimated X hours)" header
  - ❌ ~~`### N.M Task Description (Y min)`~~ — drop "(Y min)" suffix
  - ❌ ~~`- Estimated: Y min`~~ sub-bullets — drop entirely
  - ✅ Sprint-aggregate `Bottom-up est ~X hr → calibrated commit ~Y hr` lives in plan §Workload only
  - ✅ Per-day / per-task actuals (with informal estimates if useful) → progress.md Day entries (individual record, non-binding)
  - **Why** (Sprint 53.7 retrospective Q4 evidence): Day-level estimates have higher variance than sprint-level (banking offset Day N over-runs against budget). Per-day calibrated targets create false precision and trigger anxiety mid-sprint when Day N slips. Sprint-aggregate calibration is the only signal that survives 3-sprint moving evidence (per §Workload Calibration above).

**Reference Template**: **The most recent completed sprint's checklist** (NOT a fixed reference; always the latest closed sprint). As of 2026-04-30, that's `phase-51-tools-memory/sprint-51-2-checklist.md` (~351 lines, Day 0-4, 5 days, ~34 task groups, each task has 3-6 sub-bullets with specific cases/DoD/Verify commands).

**Format Consistency Rule**: Same Day count (5 days, Day 0-4), same per-task detail depth, same DoD/Verify command patterns. Scope differences expressed through **content** (more checkboxes inside a Day), **not structure** (don't add Day 5 / Day 6).

**Violation Pattern** ❌ (Phase 42 Sprint 147): Deleting unchecked `[ ]` items when scope shrinks. This hides what was planned vs. what shipped.

**Violation Pattern** ❌ (Sprint 52.1 v1-v2 — 2026-04-30): First draft used 6 days (Day 0-5); second draft was 27% shorter than 51.2 with insufficient per-task detail. Both required rewrites. **Lesson**: Match prior sprint's day count + detail depth before drafting.

✅ **Correct behavior**: Only change `[ ]` → `[x]`. If scope cuts, leave `[ ]` and note reason in progress.md.

---

### Step 2.5: Day-0 Plan-vs-Repo Verify (Sprint 55.3+ — closes AD-Plan-1; AD-Plan-3 promoted Sprint 55.6; AD-Plan-4 Schema-Grep promoted Sprint 57.1)

**Mandatory** between plan/checklist drafting and Day 1 code start. Plans drafted from session memory + retrospective context **drift from real repo** because:

- Class names get renamed between sprints (e.g. `_obs.py` may already exist when plan assumes new file)
- Table names change in Alembic migrations between PR drafts
- Test fixture paths shift when `conftest.py` is restructured
- Service/method signatures evolve in unrelated PRs while plan was being written
- **Wrong-content drift**: file exists but body diverged from plan's claim (e.g. plan asserts `_retry_policy` is dead but path verify alone can't see the body's call sites; or plan asserts ABC `ToolErrorDecision` exists but the ABC was never created)

**Cost when skipped**:
- Sprint 53.7 retrospective Q4 — 5 path-drift findings (D4-D12) cost ~1 hr Day 1+ re-work
- Sprint 55.3 Day 0 — 3 path-drift findings (D1-D3) caught in ~30 min before code starts
- Sprint 55.5 Day 0-2 — **5 wrong-content drifts** (D1+D2+D4+D5+D7) caught via AD-Plan-3 first application; ~55 min cost prevented ~3-4 hr re-work (4-8× ROI)
- Sprint 55.6 Day 0-3 — **11 wrong-content drifts** (D1-D11) caught via AD-Plan-3 second through sixth applications; ~75 min cost prevented ~9-10 hr re-work + 2 production-grade bugs (7-8× quantitative + 2 critical correctness saves)

#### Required actions (Day 0, before Day 1 code)

The verify is a **three-prong grep pass** (+ optional Prong 2.5 sub-prong for frontend page sprints); all prongs are mandatory when applicable (Prong 2.5 only when sprint involves frontend page re-point / restructure with existing child-component tree; Prong 3 only when sprint touches DB schema / migration / ORM models):

##### Prong 1 — Path Verify (AD-Plan-2 from Sprint 55.3)

Every file path mentioned in plan §File Change List or §Technical Spec → `Glob` or `ls` to confirm exists / does not exist as expected.

- New files (creates): `Glob("path/to/new_file.py")` returns 0 results
- Edited files (edits): `Glob("path/to/existing.py")` returns 1 result
- DB tables: check `infrastructure/db/models/*.py` + `alembic/versions/*.py`
- Fixture paths: check `tests/**/conftest.py`
- Imports / re-exports: confirm package-level `__init__.py` if plan asserts exposure
- Public ABC methods: read the actual ABC file to confirm signature

##### Prong 2 — Content Verify (AD-Plan-3 promoted Sprint 55.6)

Every plan §Technical Spec / §Background factual claim about existing code → **Grep** for the asserted symbol/pattern in real source. Path-verify alone (Prong 1) is **insufficient**: the file exists, but its body may have diverged from the plan's claim.

Common drift classes and matching grep query patterns:

| Drift class | Plan claim pattern | Grep verify pattern |
|-------------|--------------------|---------------------|
| **Claimed-but-unwired entry points** | "X is dead state" / "Y attribute is unused" | `grep -n "self\._{attribute}\b" {target_file}` — count call sites vs assignments (≥1 assignment / 0 call → confirmed dead) |
| **Claimed-but-missing imports** | "Z is publicly re-exported" / "consumer uses A" | `grep -rn "import {symbol}\|from .* import .*{symbol}" {target_dir}` — confirm import sites |
| **Claimed-but-renamed symbols** | "B was renamed to C" / "D class extends E" | `grep -rn "{old_name}\|{new_name}\|class .* {parent}" {target_dir}` — detect rename / inheritance drift |
| **Claimed-but-non-existent ABCs** | "extend ABC F" / "add G enum case" | `grep -rn "class F\|class G\|F\.{member}" {target_dir}` — confirm ABC actually exists before planning extension |
| **Claimed-but-wrong-units fields** | "uses backoff_seconds" / "stored as float" | `grep -n "{field_name}: " {target_file}` + read 1-3 lines — confirm unit / type assumption |

##### Prong 2.5 — Child Component Tree Depth Audit (frontend page sprints only; AD-Plan-5 fold-in Sprint 57.40 — `chore/rules` ship via Item #2 of post-Sprint-57.39 4-AD micro-fix sequence)

**Applies when**: sprint plan involves frontend page re-point / restructure where the **entry component** (e.g. `frontend/src/pages/<route>/index.tsx`) and its **child components** (e.g. `frontend/src/features/<area>/components/*.tsx`) may carry DIFFERENT vintages of styling / structure. Prong 2 scopes only to the entry component file; this sub-prong extends grep depth into the child-component tree.

**Why this matters** (Sprint 57.39 D-DAY1-1 evidence): `/governance` + `/verification` entry components were migrated to mockup-ui `Tabs` primitive (closing the shell-level NEAR-PARITY), but the child components they import (`AuditLogViewer` / `VerificationList` / `CorrectionTraceView` / etc.) retained Sprint 57.5 / 57.9 / 57.11-vintage Tailwind shadcn-utility patterns. Day 0 plan-grep (Prong 2) only checked the entry component file → child drift was invisible until Day 1 code → mid-sprint scope expansion required (FIX-015 follow-up PR #183: +347 lines / 9 files).

**Required grep depth-2 sweep**:

For each target frontend page in plan §Technical Spec:

1. **Enumerate child component tree** (depth-1): `grep -nE "import.*from.*@/features/<area>" frontend/src/pages/<route>/index.tsx` → list child component file paths
2. **Per child file — anti-pattern grep**: run plan-relevant pattern greps against each enumerated child file. Common drift class queries:

| Drift class | Plan claim pattern (in §Technical Spec) | Grep verify pattern (on each child component file) |
|-------------|------------------------------------------|---------------------------------------------------|
| **Shadcn-utility token residue** (AP-Phase2-C) | "page is verbatim-CSS aligned" / "Phase-2 re-pointed" | `grep -E "bg-card\|text-foreground\|border-border\|bg-muted\|text-muted-foreground" {child_file}` — non-zero = residue (FIX-012 retired `--sc-border`; FIX-015 closed governance + verification residue) |
| **Inline `style=` missing escape comment** (STYLE.md §1 + §3) | "no inline style violations" / "STYLE.md §3 escape used" | `grep -E "style=\{\{" {child_file}` + verify each match has adjacent `eslint-disable-next-line no-restricted-syntax` comment (FIX-015 CI fail lesson: 28 sites missed by agent) |
| **Outer wrapper artifact** (AP-Phase2-A) | "mockup has no outer wrapper" / "matches mockup root" | `grep -nE "<div style=\{\{[^}]*padding" {child_file}` — production-only padding wrappers (FIX-011 lesson — Sprint 57.19 vintage drift) |
| **Layout-class fullBleed drop** (AP-FullBleed) | "preserves AppShellV2 chrome" / "fullBleed prop intact" | `grep -nE "fullBleed\|chat-shell\|loop-canvas\|page-head" {child_file}` (FIX-010 lesson) |
| **Tab-shell vs monolithic structural divergence** | "matches mockup tab structure" | compare entry component's `<Tabs>` children vs mockup file's `<>` fragment / `.tabs-shell` structure — structural mirror mismatch = production tab-shell wraps mockup-monolithic content (Sprint 57.39 D-DAY1-1 root cause) |

**Recursion depth**: typical N = 2 (entry → direct children). Recurse to N = 3 only when the page architecture involves nested feature-area imports (rare; e.g. `chat-v2` blocks-of-blocks).

**Cost / benefit**:
- Per-page cost: ~5-10 min (1 import-grep + N anti-pattern greps per child component)
- Benefit: catches Sprint 57.39-class scope expansion at Day 0 instead of Day 1+ (1-5 hr saved per drift caught, depending on child count)
- **Skip when**: scope is non-frontend, first-time scaffolding (no existing tree to audit), or pages with no `import.*@/features/` consumers (single-file pages)

##### Prong 3 — Schema Verify (AD-Plan-4 promoted Sprint 57.1)

**Applies when**: sprint plan introduces NEW DB tables / Alembic migrations / ORM models / DB schema fields. Path verify (Prong 1) confirms file existence; content verify (Prong 2) confirms code patterns. Neither catches **column-level schema drift** between plan-time assumed schema and reality.

For every new table / migration / ORM model in plan §Technical Spec → grep DB column declarations against asserted schema before Day 1 starts:

- New table columns: `grep -A 30 "CREATE TABLE {table_name}\|class {ORM}\|table_args" backend/src/infrastructure/db/` — list every column + type + nullable
- Cross-table FK references: `grep -rn "ForeignKey.*{ref_table}\|REFERENCES {ref_table}" backend/src/infrastructure/db/` — confirm referenced table.column exists with matching type
- Migration head version: `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3` — confirm next available number not already occupied
- RLS policy presence: `grep -A 3 "ENABLE ROW LEVEL SECURITY\|tenant_isolation_{table}" {migration_file}` — multi-tenant rule check (per `.claude/rules/multi-tenant-data.md` 鐵律)
- Plan-asserted column drift catch: re-read plan §Technical Spec column list; for each column → grep ORM file to confirm field name + type + nullable + default match exactly

Common schema drift classes:

| Drift class | Plan claim pattern | Schema-grep verify pattern |
|-------------|--------------------|----------------------------|
| **Claimed-but-missing column** | "table X has column Y" | `grep -n "{column_name}" {orm_file}` — 0 results = drift |
| **Claimed-but-wrong-type column** | "column Z is VARCHAR(64)" / "is NUMERIC(20, 4)" | `grep -A 1 "{column_name}" {migration_file}` — type mismatch |
| **Claimed-but-renamed table** | "INSERT into table_a" / FK to "table_b" | `grep -rn "table_a\|table_b" backend/src/infrastructure/db/` — actual name drift |
| **Claimed-but-occupied migration head** | "Alembic 0014_xxx" | `ls migrations/versions/ | sort -V | tail -3` — 0014 already exists → use 0015 |
| **Missing RLS policy** | new tenant_id table without RLS | `grep "ENABLE ROW LEVEL SECURITY\|tenant_isolation_{table}" {migration}` — 0 results = lint will fail |

##### Catalog drift findings

In `progress.md` Day 0 entry under "Drift findings" header:

- Format: `D{N}` ID + Finding + Implication
- Cross-reference to plan §Risks (where finding may shift scope or risk profile)
- **Do NOT silently update plan §Technical Spec** — instead, add finding to plan §Risks. This preserves audit trail of what was originally planned vs. what reality forced. (See `anti-patterns-checklist.md` AP-2 — "no orphan code".)

##### Decide go/no-go for Day 1

- Findings shift scope by ≤ 20% → continue Day 1 with risk noted in §Risks
- Findings shift scope by 20-50% → revise plan §Acceptance Criteria + §Workload, re-confirm with user
- Findings shift scope by > 50% → abort sprint; redraft plan with reality baseline

#### ROI evidence (Sprint 55.6 promotion validation)

AD-Plan-3 was logged Sprint 55.4 candidate, validated Sprint 55.5 first application (5 drifts → 4-8× ROI), and **promoted to validated rule via Sprint 55.6 fold-in** based on cumulative evidence:

| Sprint | Application count | Drifts caught | Cost | Benefit prevented | ROI |
|--------|-------------------|---------------|------|-------------------|-----|
| 55.5 | 1st (Day 0 + 1 + 2) | 5 (D1+D2+D4+D5+D7) | ~55 min | ~3-4 hr re-work | 4-8× |
| 55.6 | 2nd-6th (Day 0-3) | 11 (D1-D11) | ~75 min | ~9-10 hr re-work + 2 production-grade bugs | 7-8× + 2 saves |

**D3 critical scope reduction in Sprint 55.6 alone**: AD-Cat8-2 dropped from "design + wire ~10-12 hr" to "wire-only ~5-6 hr" — caught via content grep (Prong 2), invisible to path verify (Prong 1).

**AD-Plan-4 Schema-Grep promotion ROI (Sprint 57.1 fold-in based on cumulative evidence)**:

| Sprint | Schema-Grep application | Drifts caught | Cost | Benefit prevented | ROI |
|--------|-------------------------|---------------|------|-------------------|-----|
| 56.1 | 1st (Day 0) | 2 (D26+D27 column-level) | ~30 min | ~1-2 hr re-work | 2-4× |
| 56.3 | 2nd (Day 0) | 1 (D6 sessions.total_cost_usd column) | ~20 min | ~1 hr re-work | 3× |
| **Cumulative** | **2 sprints** | **3 column drifts caught Day-0** | ~50 min | ~2-3 hr re-work | 3-4× |

Schema-Grep extends Prong 2 from code-pattern level to DB-column level. Without it, column drift surfaces at first migration / first ORM test run, costing 1-2 hr re-work per occurrence. With it, drift surfaces in Day 0 plan-verify pass at <30 min cost.

**AD-Plan-5 Frontend-Tree-Depth promotion ROI (Sprint 57.40 fold-in based on Sprint 57.39 + FIX-015 evidence)**:

| Sprint / FIX | Prong 2.5 application | Drifts caught | Cost | Benefit prevented | ROI |
|-------------|------------------------|---------------|------|-------------------|-----|
| Sprint 57.39 D-DAY1-1 | (pre-Prong-2.5 escape — Day 0 grep only checked entry component) | 1 drift surfaced mid-Day-1 (governance + verification child shadcn residue) | n/a (escape) | ~3-5 hr scope-expansion absorbed into follow-up PR #183 | (negative — what Prong 2.5 was designed to prevent) |
| FIX-015 post-hoc | Manual Day 0 grep across 6 child components | 6 drift files (4 confirmed AD-list + 2 NEW: ApprovalList + DecisionModal) | ~5 min | ~3-5 hr scope-creep avoided in original Sprint 57.39 | 36-60× |
| **Cumulative** | **2 applications** | **6 files (~28 inline-style sites secondary)** | ~5-10 min per Day 0 | scope-expansion avoidance | **20-60×** |

Frontend-Tree-Depth extends Prong 2 from entry-component grep to child-component-tree grep (depth N = 2). Without it, child drift surfaces at Day 1+ during code → either mid-sprint scope expansion OR follow-up FIX PR (Sprint 57.39 → FIX-015 pattern). With it, drift surfaces at Day 0 at <10 min cost, allowing scope adjustment in plan §Technical Spec before code starts.

#### Examples

**Sprint 53.7 D4-D12** (9 path-drift findings cost ~1 hr re-work — _why Prong 1 exists_):
- D4: Plan referenced `check_promptbuilder.py --root` arg behavior that did not match script
- D7-D8: Plan assumed lint scripts would silently accept missing `--root` flag; reality = silent-OK or exit 2
- D10-D12: Plan-stated `pytest` count baselines off by 2-5 tests vs. real repo at branch-creation time

**Sprint 55.3 D1-D3** (3 path-drift findings caught _before_ Day 1 code — _Prong 1 ROI validation_):
- D1: Plan assumed sole-mutator refactor needed for `agent_harness/`; grep showed three target patterns already grep-zero → AD-Cat7-1 scope 收斂 to enforcement test + lint
- D2: Plan assumed `verification_span` would be created; `verification/_obs.py` already had it → AD-Cat12-Helpers-1 became `extract` (non-create)
- D3: Plan assumed DB-backed `HITLPolicy` already partially wired; `DefaultHITLManager.default_policy` was in-memory only → AD-Hitl-7 baseline confirmed cleanly

**Sprint 55.6 D3 critical catch** (Prong 2 content-verify — _why AD-Plan-3 promotion exists_):
- 55.4 retro Q4 + 55.5 retro Q4 both narrated "AD-Cat8-2 needs full retry-with-backoff design"
- Day-0 content grep on `loop.py:_handle_tool_error` revealed: ABC implemented, called from main exec, error_policy/error_budget/circuit_breaker ALL wired — **only `_retry_policy` attribute is dead**
- Scope dropped from ~10-12 hr to ~5-6 hr; saved ~5-6 hr scope-creep design work
- Path verify (Prong 1) alone could not catch this: all referenced files exist; content gap requires Prong 2 grep

#### Cross-references

- `anti-patterns-checklist.md` AP-2 (no orphan / phantom code references — drift findings preserve audit trail vs. silent plan rewrite)
- `.claude/rules/file-header-convention.md` §Modification History (drift findings during refactor go in MHist; AD-Lint-MHist-Verbosity char-count budget complements this rule)
- §Common Risk Classes below (recurring drift patterns deserve catalog entries)

✅ **Correct flow**: Plan drafted → Checklist drafted → **Day-0 探勘 grep (Prong 1 path-verify + Prong 2 content-verify + Prong 3 schema-verify when DB schema in scope) + drift findings catalogued in progress.md** → Day 1 code starts.

❌ **Wrong flow** (Sprint 53.7 pre-AD-Plan-1): Plan drafted → Day 1 code → discover plan-vs-repo gaps mid-implementation → re-work checklist + plan + commits.

❌ **Wrong flow** (Sprint 55.5 pre-AD-Plan-3 first application): Path verify only (Prong 1) → Day 1 code → discover content gaps mid-implementation (file exists but body wrong; ABC doesn't exist; field uses wrong units).

❌ **Wrong flow** (Sprint 56.1 pre-AD-Plan-4 first observation): Path + content verify only (Prong 1+2) → Day 1 migration / ORM code → discover column drift at first migration test run (D26+D27 — column type / nullable mismatch).

---

### Step 3: Implement Code

**Only after both plan + checklist exist**.

**Workflow**:
1. Review sprint plan + checklist
2. Create feature branch: `git checkout -b feature/sprint-XX-Y-<scope>` (use scope from git-workflow.md)
3. Code against checklist deliverables (one at a time)
4. Commit frequently (one logical unit per commit)

**Prohibited** ❌:
- Starting code before plan/checklist approved
- Committing without checklist entry
- Scope creep without updating plan + checklist

---

### Step 4: Update Checklist During Implementation

**Daily workflow**:
- Morning: Review today's checklist tasks
- As you complete: `[ ]` → `[x]` (change, never delete)
- If blocked: Add notation `🚧 阻塞：<reason>` below the task, continue working or escalate
- End of day: Commit checklist updates

**Sacred Rule** (Phase 42 Sprint 147 violation):
- ❌ **Never delete** `[ ]` items that weren't done
- ❌ **Never hide** scope cuts by removing lines
- ✅ **Always mark**: `[x]` when done, `[ ]` when not (or abandon formally)

**Why**: Traceability. In retrospective, we see what was planned vs. shipped.

---

### Step 5: Create Progress & Documentation

**Daily (evening)**:
- Update `docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/progress.md`

#### 🆕 Step 5.5: Spike Sprint Design Note Extract Pattern（2026-05-08+ — closes doc-level rolling discipline）

**When to apply**:
若 sprint 是 **spike sprint**（用於探索新領域 / 新 gap fill — 例：Phase 57.7 IAM Block A spike / 57.8 SOC 2 + SBOM spike / 57.9 Status Page + APAC compliance spike）：**Day 4 closeout 必須額外產出 1 份 design note**（extract from real implementation）。

**When NOT to apply**:
若 sprint 是 **feature continuation sprint**（單純擴充已驗證範疇 — 例：Phase 57.4 admin tenants list 是延伸 57.3 tenant settings pattern reuse）：**不需** design note；只需 progress.md + retrospective.md。

#### 8-Point Quality Gate（design note submission checklist）

每個 spike-extract design note **必須**通過下列 8 條（reviewer 逐點驗證）：

- [ ] **1. Section header 對應 spike user story**
  - ❌ Generic：「OIDC overview」/「Authentication design」
  - ✅ Specific：「US-A2: OIDC PKCE Flow as wired in Sprint 57.7」

- [ ] **2. 每個技術 claim 有 file:line**
  - ❌「we use RS256」/「JWT validated via JWKS」
  - ✅「`JWTManager.encode()` at `backend/src/platform_layer/identity/jwt.py:42-58`」

- [ ] **3. Decision rationale 含比較矩陣**
  - ❌「Best practice」/「industry standard」
  - ✅ 三/四欄 vendor matrix + Cost / SCIM / SAML / Decision + 否決原因

- [ ] **4. Verification command（reproducible）**
  - ✅ `pytest tests/integration/auth/test_oidc_flow.py::test_real_entra_callback`
  - ✅ 或具體 manual reproduce step（curl + expected response）

- [ ] **5. Test fixture reference**
  - ✅ Link 到實際 test data / mock setup file
  - ✅ 若 real-LLM 測試，標明 `pytest -m real_llm` 與 cost 估算

- [ ] **6. Open invariant 明確分界**
  - ✅「Verified in this spike: A, B, C」+「Deferred to Phase XX.Y (NOT verified): D, E, F」
  - ❌ 將 deferred 內容寫入主 section 偽裝 verified

- [ ] **7. Rollback / fallback 路徑**
  - ✅「若設計後續證明錯，revert API routes at `auth.py` + DB column `external_id`；估 1-2 day」
  - ✅ 識別 sentinel / fallback 是否已存在
  - ❌ 假設「不會錯」

- [ ] **8. Cross-reference 17.md single-source**
  - ✅ 任何新 contract 必須在 `17-cross-category-interfaces.md` 對應 §section 登記
  - ✅ 若新增 ABC，標明 owner category
  - ❌ 在 design note 平行定義 contract（違反 single-source）

#### Quality 不是頁數，是 verified ratio

| 維度 | 14.md 風格（high page low quality） | Spike-extract 風格（mid page high quality） |
|------|-------------------------------|------------------------------------------|
| Verified ratio | 10.6% (91/862 行) | ≥ 95% |
| 每 claim 對應 file:line | ❌ 大部分 pseudo-code | ✅ 強制 |
| Decision rationale | ❌ 「primary IdP = Entra」無矩陣 | ✅ vendor comparison matrix |
| Verification reproducibility | ❌ 無 | ✅ pytest command + fixture |
| Maintenance | ❌ 半年內過時（57.5 揭示） | ✅ 隨 PR 同步 |
| 結果頁數 | 800+ 行 | 通常 200-500（outcome，非 cap） |

**禁止**：用「regulated 200-300 行」當品質替代品。重點是**禁止 speculation 充頁數**，不是壓縮 verified content。若 spike 真的學到 600 行 worth verified invariants，就寫 600 行。

#### Template

每個 spike-extract design note 使用 `claudedocs/templates/spike-design-note-template.md` 結構（含 8 sections：Spike Summary / Decision Matrix / Verified Invariants / Cross-Category Contracts / Open Invariants / Rollback / References / Modification History）。

#### Day 4 closeout 自查 record

retrospective.md 必須記錄：

```markdown
## Design Note Extract（spike sprint only）

**File**: `docs/03-implementation/agent-harness-planning/<doc-number>-<topic>.md`
**Verified ratio (estimated)**: __%
**8-Point Quality Gate**:
- [ ] 1. Section header
- [ ] 2. file:line 引用
- [ ] 3. Decision matrix
- [ ] 4. Verification command
- [ ] 5. Test fixture
- [ ] 6. Open invariant 分界
- [ ] 7. Rollback path
- [ ] 8. 17.md cross-ref

**Reviewer pass**: <user / self-review>
```


- Format:
  ```markdown
  # Sprint XX.Y Progress — YYYY-MM-DD

  ## Today's Accomplishments
  - Task X.Y completed (approx. Z min under/over estimate)
  - Issue: blockers, discoveries

  ## Remaining for Next Day
  - Task X.Z (pre-work done)

  ## Notes
  - Learning / decision / risk
  ```

**Sprint end**:
- Create `retrospective.md` covering: did well / improve next sprint / action items + estimate accuracy %

**Per-day estimates live here** (Sprint 55.3+ — AD-Lint-2 follow-on):
- Since checklist no longer carries "(Estimated X hours)" / "(Y min)" headers, **progress.md is the single home for per-day / per-task time tracking**.
- Format inside "Today's Accomplishments": `Task X.Y — actual Z min (est ~W min, delta ±N%)`
- Sprint-aggregate ratio computed in retrospective.md Q2 from sum of progress.md actuals vs. plan §Workload committed hours.
- Per-task estimates here are **non-binding individual record** — they help calibrate next sprint's bottom-up estimates but do not gate Day N completion.

**What NOT to do** ❌:
- "We'll update docs after the sprint" → too late, details lost
- Skip retrospective → patterns repeat
- Generic notes ("worked on stuff") → no data for future planning

---

## Sprint Closeout: CLAUDE.md + MEMORY.md Update Policy (Sprint 57.22+ — closes REFACTOR-001 Step 2)

**Trigger**: After Day N retrospective.md written, before opening next sprint plan. The 5-step workflow (§Mandatory 5-Step Workflow above) writes sprint execution artifacts (plan / checklist / progress / retrospective / memory subfile); this policy governs the **navigator files** (CLAUDE.md / MEMORY.md) — keep them lean, never archive sprint records inside them.

### Core Principle

| File | Role | What belongs |
|------|------|-------------|
| **CLAUDE.md** | Navigator / Principle / Rule | Timeless statements (mission / 11+1 範疇 / 5 大約束 / Mockup-Fidelity rule / Sprint Workflow rules / Karpathy / file-header convention); navigators to authoritative sources (V2 規劃文件導航 21 份 / ClaudeDocs structure / V1 reference table); current-phase milestone (1 line, principle-level) |
| **MEMORY.md** | Quality Pointer Index | Per-topic 1 pointer entry: subfile link + 1-sentence topic + keywords for future retrieval |
| **Memory subfile** (`memory/project_phase57_XX_*.md`) | Per-sprint detail | Full retro highlights / calibration / carryover ADs / file change list |
| **Retrospective** (`docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/retrospective.md`) | Authoritative full Q1-Q7 retro | Sprint-level truth source |
| **Sprint plan §Workload** | Calibration source-of-truth | Multiplier / ratio per scope class |
| **`claudedocs/1-planning/next-phase-candidates.md`** | Open items / pending decisions | Next Phase 候選 / carryover AD list |
| **Git log + PR description** | Commit-level + sprint-level ground truth | Authoritative |

**Single-source rule**: Sprint detail lives in **memory subfile + retrospective.md** only. CLAUDE.md / MEMORY.md are pointers, NOT archive.

### CLAUDE.md Update at Sprint Closeout — Minimal Touch

**Allowed** ✅:
- Update `Current Sprint` row (next sprint id + branch name) — 1 line
- Update `Last Updated` footer line — 1 line: `**Last Updated**: YYYY-MM-DD (Sprint XX.YY — short goal); see memory/ for sprint history`
- Update `Phase` / `Roadmap` row IF milestone reached (e.g. V2 22/22 → SaaS Stage 1 1/3, Phase 57+ Frontend N/N+1)
- Update `Tech Stack` / `Architecture` / `Branch Protection` rows IF actually changed (rare; e.g. CI policy change)
- Add new principle / rule sections (e.g. Sprint 57.19's new "Frontend Mockup-Fidelity Hard Constraint" — that's a timeless rule, belongs here)

**Forbidden** ❌:
- Add `Latest Sprint` / `Prev Sprint` / `Prev-Prev Sprint` / `Prev³` / `Prev⁴` rows packed with retro detail
- Pack carryover ADs / calibration ratios / commit SHAs / PR numbers / Vitest counts / bundle KB sizes / file change lists into any table cell
- Add multi-paragraph history blocks to `Last Updated` footer
- Add `[Sprint XX historical row preserved below]` archive blocks at end of CLAUDE.md
- Inline `Next Phase 候選` 20-bullet pending lists into a table cell

**Violation Pattern** ❌ (pre-cleanup state captured by REFACTOR-001 audit 2026-05-18): CLAUDE.md grew from ~30 KB foundation to **77 KB** over 20+ Phase 57+ sprints; ~58 KB was duplicate sprint records (table cells × 6 sprints + footer multi-paragraph history + `[historical row preserved]` blocks + 20-bullet `Next Phase 候選`).

### MEMORY.md Update at Sprint Closeout — Quality Pointer

**Allowed** ✅ — Add 1 entry of this shape (~250-300 char total, 3-4 lines):
```markdown
- [project_phase57_XX_<topic>.md](project_phase57_XX_<topic>.md) — Sprint XX.YY closed YYYY-MM-DD; <1-sentence what>; <1 phrase distinguishing feature or anomaly>.
  Keywords: <feature/AD/class/anomaly names for future retrieval>
```

Example (good pointer):
```markdown
- [project_phase57_21_chatv2_mockup_fidelity_phase_1.md](project_phase57_21_chatv2_mockup_fidelity_phase_1.md) — Sprint 57.21 closed 2026-05-18; Chat-v2 Turn Block Model + 3-col shell + Inspector 4-tab + Composer scaffolding; bimodal calibration pattern emerging.
  Keywords: chatv2, mockup-fidelity Phase-1, Turn Block, Inspector 4-tab, frontend-mockup-direct-port class, bimodal ratio
```

**Forbidden** ❌:
- Dump retro Q1-Q7 content into the entry
- List specific calibration ratio numbers (those live in subfile + `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`)
- List commit SHAs / PR numbers / Vitest counts / bundle KB sizes (in subfile + retrospective)
- Make entry >500 char (~300 is comfortable ceiling; quality matters more than rigid limit per user 2026-05-18 — but >500 signals you're packing summary instead of pointing)

**Quality Criteria** — Does the pointer let future AI / dev find this sprint when they search by keyword?

| Quality | Example |
|---------|---------|
| ✅ Good keywords | feature name (`chatv2`, `mockup-fidelity`) / AD ID (`AD-Tailwind-v4`) / class name (`frontend-mockup-direct-port`) / anomaly pattern (`bimodal`, `silent CSS no-op`) |
| ❌ Bad keywords | generic terms ("frontend", "refactor") / date-only / sprint-id-only / numbers without context |

**Header rule statement** (in MEMORY.md opening): the prior「每行 ≤ 200 字符」hard limit is updated to「**quality pointer principle**: topic + keywords + subfile path; detail single-source in subfile; ~300 char comfortable ceiling, but quality matters more than character count」per user clarification 2026-05-18.

### Open Items / Pending Decisions Destination

**Forbidden** ❌:
- `Next Phase 候選` 20-bullet lists in CLAUDE.md table cells (was pre-cleanup case)
- Pending AD candidates / unresolved issues in CLAUDE.md table cells
- Time-bound TODOs / schedule notes in CLAUDE.md

**Allowed** ✅:
- Maintain `claudedocs/1-planning/next-phase-candidates.md` as **single-source** for open / pending items
- Sprint plan §Carryover section (in `docs/03-implementation/agent-harness-planning/phase-XX-*/sprint-XX-Y-plan.md`) lists carryover ADs for next sprint pickup
- Sprint retrospective.md §Carryover section accumulates per-sprint additions to the candidate pool
- `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix` tracks cross-sprint calibration trends

### Self-Check at Sprint Closeout (Pre-Commit)

Before commit closeout MHist, verify:

- [ ] **CLAUDE.md changes**: Only navigator / principle / rule level? (NO sprint-by-sprint history record additions)
- [ ] **MEMORY.md new entry**: ~250-300 char quality pointer (topic + keywords + subfile link)? (NOT a packed retro summary)
- [ ] **Sprint detail preserved**: Memory subfile + retrospective.md updated with full content? (YES — single-source preserved elsewhere)
- [ ] **Carryover / open items**: Documented in next sprint plan §Carryover or `claudedocs/1-planning/next-phase-candidates.md`? (NOT in CLAUDE.md table cell)
- [ ] **Calibration ratio**: Tracked in `sprint-workflow.md §Scope-class multiplier matrix`? (NOT in CLAUDE.md / MEMORY.md prose)

### Why This Policy Exists (REFACTOR-001 root cause analysis 2026-05-18)

V2 evolved organic CLAUDE.md + MEMORY.md bloat pattern over Phase 57+ ship sprints (20+ sprints accumulated):
- **CLAUDE.md** grew from ~30 KB foundation to **77 KB**; ~58 KB ≈ duplicate sprint records
- **MEMORY.md** exceeded its own ≤24.4 KB system limit (actual 28 KB); 12 entries violated own ≤200 char rule (worst: 57.17 entry at ~3000 char = 15× over)
- ~9-12% session context window consumed by duplicates at session start
- **Triple-source for same sprint detail**: CLAUDE.md table cell + CLAUDE.md footer + MEMORY.md entry + memory subfile + retrospective.md (5 copies of overlapping content)

**Root cause**:
1. AI sprint-closeout pattern dumped full retro Q1-Q7 highlights into "index" entries (forgot single-source principle)
2. Sprint table cells accumulated history without archive cutoff or policy
3. No enforcement (no lint, no review checkpoint)
4. "捨不得刪" mentality: each prev sprint row felt "still useful" → kept indefinitely

**Fix**: This policy (§Sprint Closeout) + REFACTOR-001 Step 3 cleanup execution.

### Cross-References

- `claudedocs/4-changes/refactoring/REFACTOR-001-claude-md-memory-md-bloat-audit.md` — initial trigger audit (Step 1/4)
- `.claude/rules/file-header-convention.md` §Modification History char-budget rules — sibling philosophy (MHist 1-line max, detail in commit body / 4-changes record)
- MEMORY.md header rule statement — quality pointer principle (post-2026-05-18 rewording)
- `claudedocs/1-planning/next-phase-candidates.md` — open items / Next Phase 候選 single-source (created in REFACTOR-001 Step 3)

---

## Common Risk Classes (Sprint 53.7+ — closes AD-CI-4)

When drafting plan §Risks, consider these recurring risk classes (V2 carryover evidence). Each entry: `Symptom → Workaround → Long-term fix`.

### Risk Class A: Paths-filter vs `required_status_checks` (CI infra)

**Symptom**: PR只動 `docs/` 或 `.gitignore`（不動 `backend/**` 或 `.github/workflows/**`），導致 GitHub Actions paths-filter 不觸發 backend-ci / V2 Lint。Branch protection `required_status_checks` 仍要求這些 contexts 通過 → mergeStateStatus = `BLOCKED` even though PR is logically clean.

**Source**: Sprint 53.2.5 retrospective (AD-CI-2 / AD-CI-3 origin); Sprint 53.6 Day 2-3 (frontend-only commits had Backend CI skipped — looked like CI broke; required PR-description note).

**Workaround**: 加一個 commit 觸碰 `.github/workflows/backend-ci.yml`（例如 header comment 註記改動原因），就會觸發 backend-ci + V2 Lint → 必填 contexts 滿足 → PR mergeable. Documented inline in `.github/workflows/backend-ci.yml` header (since 53.2.5).

**Long-term fix**: AD-CI-5 (`required_status_checks` paths-filter design revisit; possibly switch to GitHub Actions "fall through" / use `if: always()` aggregator job). Independent infra track.

### Risk Class B: Cross-platform `mypy --strict` `unused-ignore` (Python tooling)

**Symptom**: 同一 import / Optional unwrap 在 Linux runner 與 Windows 開發機 mypy 行為不同（缺 stub 包 vs 有 stub 包）。`# type: ignore[X]` 在一邊需要、在另一邊變 `unused-ignore` 報錯（`warn_unused_ignores=true` strict 模式下）。

**Source**: Sprint 52.6 retrospective Q4.

**Workaround**: 雙 ignore code → `# type: ignore[X, unused-ignore]`. 兩邊都不報錯. Documented in `.claude/rules/code-quality.md` §Cross-platform mypy pattern.

**Long-term fix**: Pin Python stub package versions in `pyproject.toml` so both platforms behave identically. Independent.

### Risk Class C: Module-level Singleton Across Test Event Loops (test isolation)

**Symptom**: TestClient-based integration tests 共用 module-level singletons (e.g. `service_factory` cache / `RiskPolicy` DB cache / `MetricsRegistry`) → 第二次 fixture activate 拿到上一個 event loop 的 cached instance → 「event loop closed」cascade fail.

**Source**: Sprint 53.6 Day 4 (US-5 ServiceFactory consolidation introduced; 5 governance / audit tests failed until autouse `reset_service_factory` fixture added).

**Workaround**: Per-suite `conftest.py` autouse fixture calling `reset_*()` for affected singletons. Pattern documented in `.claude/rules/testing.md` §Module-level Singleton Reset Pattern (since 53.7).

**Long-term fix**: Refactor singletons to be DI-injected per-request (no module-level cache); avoids root cause. Per-singleton scope; track as needed.

### How to use this section

When drafting plan §Risks, scan this catalog. If any class applies to your sprint scope, copy the symptom + workaround text into your plan §Risks table. Add new classes here when 2+ sprints hit the same root cause.

---

## Change Record Conventions

When fixing bugs or implementing features, create corresponding document in `claudedocs/4-changes/`:

| Type | Directory | Naming | When |
|------|-----------|--------|------|
| Bug Fix | `4-changes/bug-fixes/` | `FIX-XXX-description.md` | Any bug fix |
| Feature Change | `4-changes/feature-changes/` | `CHANGE-XXX-description.md` | Feature enhancement |
| Refactoring | `4-changes/refactoring/` | `REFACTOR-XXX-description.md` | Code restructure |

**Format** (1 page):
```markdown
# FIX-123: <Description>

**Date**: 2026-05-15
**Sprint**: 50.2
**Scope**: <11+1 category or cross-cutting>

## Problem
2-3 sentences. What was broken?

## Root Cause
Analysis. Why did it happen?

## Solution
What we changed. Code location. PR reference.

## Verification
How we confirmed it's fixed (test name, manual steps).

## Impact
Scope of fix (backend-only? frontend? integration?).
```

**Daily Workflow**:
1. **Morning**: Check `claudedocs/3-progress/daily/` latest log
2. **When fixing bug**: Create `claudedocs/4-changes/bug-fixes/FIX-XXX-<issue>`
3. **When changing feature**: Create `claudedocs/4-changes/feature-changes/CHANGE-XXX-<feature>`
4. **End of day**: Use SITUATION-5 to save progress (which creates daily log entry)

---

## Sprint Naming & Directory Structure

**Standard format** (from 06-phase-roadmap.md):

```
phase-XX-name/
├── sprint-XX-Y-plan.md           ← Must exist before coding
├── sprint-XX-Y-checklist.md      ← Must exist before coding
└── ...

agent-harness-execution/
└── phase-XX/
    └── sprint-XX-Y/
        ├── progress.md           ← Daily entries during sprint
        ├── retrospective.md      ← End of sprint
        └── artifacts/            ← Evidence files
```

**Branch naming** (from git-workflow.md):
```
feature/sprint-XX-Y-<scope>
```

**Commit messages**:
```
feat(<scope>, sprint-XX-Y): <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Common Violation Patterns & Consequences

| Pattern | Evidence | Why Bad | Fix |
|---------|----------|---------|-----|
| **Skip Plan** | Code appears without plan.md | Unknown scope → unclear PR → rework | Always: plan → checklist → code |
| **Skip Checklist** | Implementation doesn't track tasks | Can't measure progress; retro blind | Checklist = truth table; mandatory |
| **Delete `[ ]` items** | Checklist shrinks mid-sprint | Hides scope cuts; retro can't diagnose (Phase 42) | Only mark `[x]` or note `[阻塞]` |
| **Update checklist after sprint** | Checklist retroactively filled in | Data quality → estimates useless | Update daily, during work |
| **Skip progress.md** | "Will write at end" | Details lost; retro weak | Write daily 10-min entry |
| **No Change records** | Bugs fixed in silence | No audit trail; same bug reappears | FIX/CHANGE/REFACTOR every time |
| **Vague DoD** | "Implement X" → what counts as done? | Infinite rework; unclear when to stop | DoD: testable + measurable |
| 🆕 **Format inconsistency** (Sprint 52.1 v1) | New plan has different section count / naming / Day count than prior completed sprint | Hard to navigate; mental overhead; user must matrix-correct | Read prior sprint's plan + checklist BEFORE drafting; mirror structure; scope differences expressed through content, not structure |

---

## Error Flow: Phase 35-38 Shortcut (DO NOT REPEAT)

```
❌ WRONG:
Phase README → Code (skip plan + checklist) → Progress Doc (scatter, incomplete)
            → Pull request with unclear scope
            → Retro says "we don't know what was planned"
```

```
✅ RIGHT:
Phase README → Sprint Plan (user stories + technical spec)
            → Sprint Checklist (task breakdown + DoD)
            → Code (implement against checklist)
            → Update Checklist (daily: [ ] → [x])
            → Progress Doc (daily progress + retrospective)
            → Pull request with full traceability
            → Retro: "estimate accuracy 85%; unblock story X.Y for next sprint"
```

---

## Daily Workflow Example

**Morning (9 AM)**:
1. Review `claudedocs/3-progress/daily/` latest entry
2. Open sprint checklist (e.g., `sprint-49-1-checklist.md`)
3. Today's tasks: **Day 2.1 — 2.4** (estimated 6 hours)
4. Create feature branch if first day

**During work**:
- Per-task estimate vs actual; mark `[x]` immediately upon completion
- If blocked, add `🚧 阻塞 (HH:MM): <reason>` and switch to another task
- Commit per logical unit with sprint scope in message

**End of day (4 PM)**:
1. Update checklist (today's done tasks `[x]`)
2. Commit checklist changes
3. Write `progress.md` entry (estimate vs actual + notes)
4. Create FIX/CHANGE/REFACTOR record if applicable

---

## Before Commit Checklist

Every commit must pass:

1. **Correspond to Sprint Checklist**
   - Commit message matches task ID
   - Checklist `[ ]` → `[x]` done before or immediately after commit

2. **Lint + Format** (from code-quality.md)
   - Backend (per-file format + type chain): `black . && isort . && flake8 . && mypy .`
   - Backend (V2 architecture lints — 6 scripts; closes AD-Lint-1 since Sprint 53.7): `python scripts/lint/run_all.py`
     - One-stop wrapper invokes 6 V2 lints with correct `--root` args (check_ap1: `backend/src` / check_promptbuilder: default `backend/src/agent_harness` / 4 auto-discover)
     - Exit 0 = all 6 green; non-zero = `<failed>/6` with per-script line summary
     - Replaces the prior 6 separate invocations (which silently mis-passed when `--root` arg mismatched script expectation — see Sprint 53.7 Day 0 drift D1)
   - Frontend: `npm run lint && npm run build` — **MUST run WITHOUT `--silent` flag** (Sprint 57.40 closes AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern). FIX-015 PR #183 CI failed in 30s with 28 ESLint `no-restricted-syntax` errors that local `npm run lint --silent` swallowed; the `--silent` flag suppresses lint error output along with package-manager noise. **Never** use `--silent` for the pre-push lint check; if you want clean output, redirect with `2>&1 | tail -20` instead (preserves errors while trimming noise).

3. **Tests Passing**
   - Backend: `pytest` (>= 80% coverage for new code)
   - Frontend: `npm run test` (>= 80% coverage)

4. **Sprint Workflow Compliance** (anti-patterns-checklist.md 11 points)

5. **No Prohibited Imports**
   - Backend agent_harness: no direct `import openai` / `import anthropic`

6. **File Headers Updated** (file-header-convention.md)

---

## Prohibited Actions

- ❌ Force push to main
- ❌ Commit without corresponding checklist entry
- ❌ Delete unchecked `[ ]` items from checklist
- ❌ Skip progress.md updates (update daily)
- ❌ Skip FIX/CHANGE/REFACTOR records for bug/feature changes
- ❌ Code before plan + checklist exist
- ❌ Commit secrets, large binaries, generated files
- ❌ Scope creep without updating plan

---

## References

| Document | Purpose |
|----------|---------|
| CLAUDE.md §Sprint Execution Workflow | High-level discipline |
| CLAUDE.md §ClaudeDocs — Change Records | FIX/CHANGE/REFACTOR conventions |
| 06-phase-roadmap.md | 22 sprint overview + naming |
| sprint-49-1-plan.md | Plan template |
| sprint-49-1-checklist.md | Checklist template |
| git-workflow.md | Commit message format + scope |
| anti-patterns-checklist.md | 11-point code review checklist |
| category-boundaries.md | 11+1 scope isolation rules |
| file-header-convention.md | Header + Modification History format |

---

**Applies To**: V2 Phase 49+ (all 22 sprints)
