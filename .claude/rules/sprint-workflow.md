# Sprint Workflow Rules

**Purpose**: Enforce sprint execution discipline; prevent Phase 35-38 shortcut lessons from repeating.

**Category**: Development Process
**Created**: 2026-04-28
**Last Modified**: 2026-05-31
**Status**: Active

> **Modification History**
> - 2026-06-03: chore(rules) — Area-A (57.66-73) lessons fold-in: Prong-1 test-infra verify (AD-Day0-Prong1-TestInfra-File-Verify) + Prong-2 +2 drift rows (codegen-shape AD-Day0-Codegen-Existing-Shape-Capture / no-live-producer) + Risk Class E (stale --reload masks wiring; C-11 cost_ledger) + Risk Class C reinforce (AD-Source-DB-Call-Test-Isolation) + Before-Commit item 7 (agent-delegation: all gates + pin language + parent re-verify)
> - 2026-05-31: REFACTOR-005 — extract per-sprint calibration history (matrix per-cell narration + §Scope-class MHist list + agent_factor activation history 57.42→57.62 + top calibration-retro entries) to calibration-log.md; kept active multiplier table + agent_factor Formula/Rollback/Escalation/Tracking rules (always-loaded file ~90k→~25k tok)
> - 2026-05-29: Sprint 57.62 follow-up chore — mark §Common Risk Classes Risk Class A **RETIRED Sprint 55.6** (paths filter removed → docs-only PRs run full CI; stale touch-backend-ci.yml workaround description corrected; residual webhook-miss edge case noted)
> - 2026-05-26: Sprint 57.52 — Drift Class table +2 rows (closes AD-Day0-Prong2-Oklch-Delta-Grep + AD-Stale-Docstring-Karpathy-3)
> - 2026-05-26: Sprint 57.51 — add §Common Risk Classes Risk Class D ORM File Path Reference Style (closes AD-Plan-Risk-ORM-File-Path-Reference-Style #82; Sprint 57.50 D-DAY0-2 lesson)
> - 2026-05-25: Bundle Item #4 — propose Agent Delegation Factor Modifier (matrix proposal, pending 2-3 sprint validation) + §Before Commit lint must be non-silent (closes AD-Sprint-Plan-Agent-Delegation-Factor-Modifier as proposal + AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern)
> - 2026-05-25: AD-Plan-5 fold-in §Step 2.5 Prong 2.5 Child Component Tree Depth Audit (closes AD-Day0-Prong2-Child-Component-Tree-Depth-Audit; Sprint 57.39 D-DAY1-1 + FIX-015 evidence)
> - 2026-05-18: Sprint 57.22 — add §Sprint Closeout CLAUDE.md+MEMORY.md update policy (closes REFACTOR-001 Step 2)
> - 2026-05-06: Sprint 57.1 — fold-in §Step 2.5 Prong 3 Schema Verify (closes AD-Plan-4 promotion)
> - 2026-05-05: Sprint 55.6 — promote AD-Plan-3 (Prong 2 content verify + ROI + grep patterns)
> - 2026-05-04: Sprint 55.3 — add §Step 2.5 Day-0 plan-vs-repo grep verify (closes AD-Plan-1) + drop per-day "Estimated X hours" headers from checklist template (closes AD-Lint-2)
> - 2026-05-04: Sprint 53.7 — add §Workload Calibration sub-section under Step 1 (closes AD-Sprint-Plan-1) + new §Common Risk Classes top-level section (closes AD-CI-4) + Pre-Push reference `python scripts/lint/run_all.py` wrapper (closes AD-Lint-1 doc portion)
> - 2026-04-28: Initial creation (V2 foundation) — enforce 5-step workflow + change record conventions
>
> Per-sprint calibration-retro entries (Sprint 57.42→57.62, dropped here per REFACTOR-005) → [calibration-log.md §3](../../docs/03-implementation/agent-harness-execution/calibration-log.md).

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

#### Four-segment form when `agent_factor` applies (Sprint 57.43+ — ACTIVATED 2026-05-25 per Sprint 57.42 retro)

When the sprint anticipates code-implementer agent-delegation as the primary Day 1 mechanism (≥ 80% of Day 1 work via agent), Plan §Workload **must** use the four-segment form:

> Bottom-up est ~X hr → class-calibrated commit ~Y hr (mult Z) → agent-adjusted commit ~Y' hr (agent_factor 0.55)

where `Y' = Y × 0.55 = X × Z × 0.55`. See §Active Agent Delegation Factor Modifier below for full formula, evidence, rollback rule, and tracking discipline.

**MANDATORY plan-time `Agent-delegated:` field** (Sprint 57.57+ — codified via `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification` PROMOTION; 5-data-point evidence Sprint 57.53+57.54+57.55+57.56+57.57 consecutive usage):

Plan §Workload section MUST include an explicit `Agent-delegated:` field at plan-time (NOT just retrospective Q2). Acceptable values:

- **`yes`** — ≥ 80% of Day 1 work via code-implementer agent. Apply 4-segment form with appropriate `agent_factor` sub-class baseline. Required for sprints generating validation data points under the tier-4 agent_factor sub-class table.
- **`partial`** — 20-79% via agent. Apply `agent_factor = 0.75` linear interpolation per §Active block formula. Sprint plan §Workload still uses 4-segment form.
- **`no`** — < 20% via agent (parent-assistant-direct execution). Apply `agent_factor = 1.0`. Sprint plan §Workload uses 3-segment form (no agent-adjusted commit line; class-calibrated commit IS the final commit).
- **`TBD-Day-1-decision`** — when delegation choice is contingent on Day 0 三-prong findings or Day 1 scope clarification (e.g. Sprint 57.45 Path A vs Path B branch). MUST resolve to `yes`/`no`/`partial` by Day 1 start; recorded as final value in retrospective Q2.

**Rationale** (5-data-point evidence base): plan-time `Agent-delegated:` field surfaced calibration class selection decisions upfront (Sprint 57.53 parent-direct → `agent_factor = 1.0` applied retroactively per Sprint 57.45 Path B precedent; Sprint 57.54-57.57 all delegated-yes pre-declared and consistently honored). Without this field, the `agent_factor` row in §Active block was inconsistently applied — some sprints retroactively classified, some pre-declared. Pre-declaration prevents retro confusion AND surfaces sub-class baseline selection (mechanical-pattern-reuse-heavy 0.30 vs -greenfield-port-style 0.45 vs -design-decisions 0.65) in plan §Workload §Sub-class declaration. Per AD-Plan-2/3/4/5 promotion precedent: 3-data-point evidence sufficient; Sprint 57.57 = 5th consecutive consistent usage.

**Tracking discipline cross-ref**: §Active Agent Delegation Factor Modifier §Tracking discipline (MANDATORY from Sprint 57.43+) §3 row reads "**NEW**: explicit `agent-delegated: yes / no / partial` tag" — Sprint 57.57 codification clarifies this is PLAN-TIME tag (was ambiguous between plan-time vs retro-time in original wording).

#### Scope-class multiplier matrix (Sprint 57.6+ — closes AD-Reality-10 + AD-Sprint-Plan-7)

Per AD-Sprint-Plan-4 (logged Sprint 55.3) + 4-sprint window evidence,one-multiplier-fits-all approach loses signal when scope class differs。Below matrix記錄 active classes per scope。`mid-band` value 0.55 for default unclassified scopes;diversification per evidence。

> **Per-class data-point history + per-cell narration + the matrix change log moved** (REFACTOR-005, 2026-05-31) → [`calibration-log.md` §1](../../docs/03-implementation/agent-harness-execution/calibration-log.md). The table below = current multiplier + 3-sprint mean + 1-line status only. Adjustment rule = §Workload Calibration §When to adjust the multiplier above (3-sprint moving window).

| Scope class | Mult | 3-sprint mean | Status (1-line) |
|-------------|------|---------------|-----------------|
| `mixed` (greenfield + reuse) | 0.60 | 0.79 ⬇ | KEEP; AD-Sprint-Plan-6 propose split greenfield 0.60 / pattern-reuse 0.40 |
| `medium-backend` | 0.80 | ~0.61 (last-3 ~0.44) | KEEP — 3-consec <0.7 but agent-confound resolved at agent_factor sub-class layer; AD-MediumBackend-AICadence-Recalibration needs human-factor data |
| `medium-frontend` | 0.65 | ~0.54 | KEEP — confound-resolved-at-sub-class-layer; AD-medium-frontend-Baseline-Recalibration |
| `large multi-domain` | 0.55 | 0.81 | KEEP — lower-trigger (3+ consec <0.7) not met |
| `reality-check` | 0.85 | n/a (1 pt) | KEEP pending 2-3 sprint validation |
| `reality-gap-fix` | 0.50 | n/a (1 pt) | KEEP; AD-Sprint-Plan-8 maybe →0.35 |
| `iam-frontend-spike` | 0.60 | n/a (1 pt) | KEEP pending validation |
| `iam-backend-spike` | 0.65 | ~1.08 (3 pt) | KEEP — 57.87 ≈1.0 + 57.105 ≈0.95 (IN band) + 57.112 ≈1.28 (slightly over — the FE component + the D13 drive-through detour vs the prior two's purer-backend shape); single over-point, 3-pt mean ≈1.08 IN band → KEEP; if the next IAM-backend spike WITH an FE component also runs >1.20 propose an `iam-backend-with-fe` sub-class ~0.75 |
| `frontend-arch-spike` | 0.50 | n/a (1 pt) | KEEP; AD-Sprint-Plan-10 maybe split greenfield/reuse-ship |
| `frontend-feature-with-migration` | 0.50 | n/a (1 pt) | KEEP |
| `audit-cycle / docs / template` | 0.40 | 1.13 | KEEP — 3-sprint window complete |
| `frontend-foundation-spike` | 0.50 | n/a (1 pt) | KEEP pending validation |
| `frontend-e2e-sweep` | 0.50 | n/a (1 pt) | KEEP pending validation |
| `frontend-refactor-mechanical` | 0.50 → **0.80** (3rd+ app, AD-Sprint-Plan-13) | ~1.7 | KEEP 0.80; flag 4th data point; if >1.20 →0.90 |
| `frontend-css-engine-hotfix` | 0.60 | n/a (1 pt) | KEEP pending validation |
| `mockup-integration-foundation` | 0.55 | n/a (1 pt) | KEEP |
| `mockup-page-port-with-backend-pairing-and-audit` | 0.60 | n/a (1 pt) | KEEP; if <0.7 recurs →0.40 |
| `frontend-mockup-direct-port` | 0.55 | 0.85 (bimodal) | KEEP; if 3rd bimodal → split token-sweep 0.40 / structural 0.85 |
| `frontend-mockup-fidelity-audit` | 0.85 | n/a (1 pt) | KEEP; if recurs →0.45-0.55 |
| `frontend-mockup-strict-rebuild` | 0.60 | ~0.63 | KEEP — agent-confound resolved at agent_factor sub-class layer |
| `frontend-foundation-token-correction` | 0.55 | n/a (1 pt) | KEEP |
| `frontend-verbatim-css-foundation` | 0.55 | n/a (1 pt) | KEEP |
| `frontend-verbatim-css-repoint -simple` | 0.50 | ~1.0 | KEEP (criteria: ≤3 files / no AP-2 banner / no dual-mount / no playback widgets / oklch bump <4) |
| `frontend-verbatim-css-repoint -with-extras` | 0.65 | ~1.04 | KEEP (criteria: any of multi-file >3 / AP-2 banner / dual-mount / playback widgets / oklch bump ≥4) |
| `frontend-page-bug-fix` | 0.45 | n/a (1 pt) | KEEP; if >1.20 recurs →0.55-0.60 |
| `mixed-multidomain-bundle` | 0.65 | ~0.8-0.9 (latest 57.107) | KEEP — 57.107 B3 (4 tracks) ratio ≈0.8-0.9 IN band, first clean point post-confound (agent-delegated partial: FE delegated + parent re-verified, backend parent-direct); prior 0.42 mean was the agent-confound era |
| `subagent-child-loop-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.94 ratio ~0.93 IN band; Cat 11 new-domain spike, parent-direct) |
| `subagent-sse-relay-wiring` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.95 ratio ~0.9-1.0 IN band; Cat 11→12 backend composition wiring, parent-direct) |
| `subagent-child-turnstream-nesting` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.96 ratio ~0.9-1.1 IN band; Cat 11×12 multi-layer feature — new wrapper event + executor forward + frontend store/render, parent-direct) |
| `multi-model-profile-spike` | 0.55 | ~1.0 (2 pt) | KEEP — 57.97 ~0.93 + 57.109 ~1.1-1.2 both IN band (2-consec). Shape: a ChatClient consumer retiered to cheap + cost attribution + drive-through, parent-direct (57.109 C2: compaction retier + `_compaction` ledger mirror + 2 env knobs; the upper-edge ratio = the dt discovery loop — D-DAY3-1 semantic-unreachable finding forced a knob pivot) |
| `subagent-child-governance` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.110 B4 ratio ~1.1-1.2 IN band upper edge; Cat 11×9×8 composition over the proven child-loop machinery — engine injection via closure (`loop.py` diff 0) + failure-policy contract field + C3-policy mirror + thin FE label + 2-leg dt, parent-direct agent_factor 1.0; the upper-edge over-run = the dt discovery loop: D-DAY3-1 popen deny-list fix-forward + re-drive + D-DAY3-2 LoopTerminated terminal-shape pin — same dt-loop shape as 57.109) |
| `verification-in-loop-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.98 ratio ~0.92 IN band; Cat 1×10×7×12 loop.py-core new-domain spike — in-loop verify gate + durable counter on checkpoint metadata + wrapper retire + drive-through, parent-direct; agent_factor 1.0) |
| `verification-trace-and-benchmark-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.111 ratio ~1.0-1.1 IN band upper edge; A3 — Cat 1×10 loop.py trace-threading (the gate builds a `trace_state` vs `cast(LoopState,None)`; diff 25/3 threading-only) + a greenfield eval harness (`scripts/benchmark_judge.py` + a 28-case golden fixture + `@pytest.mark.benchmark`), parent-direct agent_factor 1.0; the over-edge = the dt+tooling discovery loop — D12 `tests.unit.scripts` importlib shadow + D-DAY3-1 cp950 print + the `api.main:app` startup fix + 2 MHist E501 — same shape as 57.109/110) |
| `loop-pause-point-feature` | 0.50 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.99 ratio ~0.93 IN band; the 4th pause leg — A2 verification-ESCALATE: conditional escalate pause + resume APPROVE-replay/REJECT-coach-one-turn + durable flag, Cat 1×10×9×7, parent-direct agent_factor 1.0; honours the 57.92/93 proposed `loop-pause-point-feature` ~0.40 but set 0.50 for the bounded REJECT continuation + held-answer snapshot beyond a pure pause leg) |
| `frontend-feature-with-event-wire-addition` | 0.55 | ~1.05 (2 pt) | KEEP — 57.100 ~1.0 + 57.108 ~1.05-1.1 both IN band (2-consec). Shape: additive fields on EXISTING events (count unchanged) + codegen regen + chat-v2 FE wiring + cross-stack parity, parent-direct agent_factor 1.0 (57.108: approval tool_name/reason + llm_response token actuals + 4 store captures, ZERO component edits — D5 store-driven render dividend) |
| `loop-injection-primitive-spike` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.101 B1 — cross-stack new-domain primitive: NEW Cat 1 `MessageInbox` ABC + NEW `_run_turns` drain seam + NEW `MessageInjected` event TYPE (codegen 23→24) + module-level `InjectionRegistry` + new `POST /{id}/inject` + FE composer-mid-run + store/render; Cat 1×12×9×frontend, parent-direct agent_factor 1.0; larger surface than 57.96 but each layer thin over the 57.88-99 pause/resume + 57.96 codegen machinery → 0.55 like 57.96; D-DAY1-1 input-guardrail-not-between-turns-gate correction caught Day-1) |
| `subagent-teammate-multiturn-spike` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.102 B2a ratio ~0.95-1.0 IN band; Cat 11×1×12 composition spike — TEAMMATE single-shot → real child loop (mirror 57.94 FORK) + `send_to_parent` tool + `TeammateChildLoopFactory` + B1 inbox wiring (reuse 57.96 relay + 57.101 inbox), backend-only, no new wire event / DB / FE, parent-direct agent_factor 1.0; lighter than 57.94's `subagent-child-loop-spike` 0.60 because it reuses 3 proven assets vs building the child-loop machinery) |
| `subagent-inject-to-teammate` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.103 B2b ratio ~1.15-1.25 slightly OVER; cross-stack — `POST /subagents/{sid}/inject` endpoint + `TeammateInboxScope` register/unregister lifecycle + `MessageInjected`-in-relay + US-5 inline mode-aware label, parent-direct agent_factor 1.0; the over-run = a build-then-revert tax: the drive-through found the inject UI un-drivable under the buffered relay + await-completion → US-4/6 built then removed per Option A (the backend primitive + US-5 kept). A sprint whose user-facing half is architecture-blocked carries a hidden build-then-revert cost the bottom-up didn't price) |
| `config-tiering-model-policy-spike` | 0.60 | ~0.98 (2 pt) | KEEP — C1 57.104 ~0.9-0.95 + C3 57.106 ~1.02 both IN band (2-consec) → validated. Full-stack config-tiering family (value object + TTL resolver Risk Class C + admin PUT/GET + tenant-settings tab + per-request wiring); backend parent-direct + FE agent-delegated-then-parent-re-verified = blended full-stack so NO single agent_factor; loop.py diff 0, no migration, no new event. C3 (57.106) widened it with a NEW Cat 9 `RiskyActionDetector` (only non-mirror piece) + a 9-field richer policy + `list_templates()` NAME allow-list; drive-through PASS proved per-tenant escalate-phrase + risky-detector on/off via cache invalidation |

> Collapsed/closed historical classes (`frontend-mockup-strict-rebuild — historical`; `frontend-verbatim-css-repoint` pre-57.38 single-baseline, CLOSED Sprint 57.38) → calibration-log.md §1. For verbatim-css-repoint use `-simple` (0.50) or `-with-extras` (0.65) per criteria above.

#### Active Agent Delegation Factor Modifier (ACTIVATED 2026-05-25 — Sprint 57.42 retro structural decision per `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`)

> **Per-sprint activation/validation history moved** (REFACTOR-005, 2026-05-31): activation evidence, tier-2/3/4 split evolution, per-sprint history (Sprint 57.42→57.62), deprecated baselines → [`calibration-log.md` §2](../../docs/03-implementation/agent-harness-execution/calibration-log.md). Below = active rules only (Status + Formula tier-4 table + When + Rollback + Escalation + Tracking discipline).

**Status**: **ACTIVE — Option A multiplicative `agent_factor` coefficient with mid-band start `0.55`**. Closes `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`. Activation criteria FULLY MET at Sprint 57.42 retro Q4 (5 cross-class data points + 4 consecutive `mockup-strict-rebuild` agent-delegated < 0.7).

**Hypothesis (validated)**: code-implementer agent-delegated frontend work shows ~3-5× speedup vs the human-rewrite cadence the bottom-up estimates assume. Existing per-class multipliers (0.45-0.85) bake in a human-cadence haircut; agent-delegated sprints consistently undershoot the calibrated band lower edge because the haircut isn't enough. Validated by 5 data points (full activation evidence → calibration-log.md §2).

**Formula** (applies from Sprint 57.43+ onwards):

```
effective_calibrated_hours = bottom_up × scope_class_multiplier × agent_factor

where agent_factor = {
  human (default):      1.0
  agent-delegated (tier-4 sub-class table — Sprint 57.55 retro Q4 tier-4 SPLIT ACTIVATED effective 2026-05-28 onwards):
    mechanical-pattern-reuse-heavy:               0.30   (≥ 4 mechanical repetitions of same template in 1 sprint; evidence: Sprint 57.49 retroactive — 5-tab+1-drawer migration ratio 0.21 under 0.30 vs 0.14 under 0.45; Sprint 57.60 1st DELIBERATE FORWARD application ratio ~1.09 IN BAND ✅ — backend 5-site fallback removal + 0020 cleanup migration + test conversions; KEEP 0.30 single forward-data-point; counterfactual `-port-style` 0.45 → ~0.73 below band so 0.30 better fit; shape-variance: 57.49 high-repetition ~24× ratio 0.21 vs 57.60 moderate-repetition ratio 1.09 — if a future ≥20× sprint at 0.30 lands < 0.7 again consider tier refinement `-high-repetition` ~0.20 vs `-moderate` 0.30, defer until 2+ such data points)
    mechanical-greenfield-port-style:             0.45   (single NEW component-pair via mirror-port of existing service shape; predecessor template ≥ 95% internalized; NO NEW Pydantic schema design / UX state design — RESERVED for future port-only sprints)
    mechanical-greenfield-design-decisions:       0.65   (single NEW component-pair WITH NEW Pydantic schema design + NEW UX state design — e.g. edit-mode draft state — design decisions add ~30-50% wall-clock vs pure port; evidence: Sprint 57.54 HITLPolicies WRITE ratio ~1.37-2.0 at 0.50 / Sprint 57.55 FeatureFlags WRITE ratio ~1.57 at 0.50 — 2 consec > 1.20 → tier-4 SPLIT ACTIVATED; equivalent ratios under 0.65 = 1.05-1.55 / 1.21 → band top edge / IN band; Sprint 57.56=1.02 + 57.57=1.15 both IN band 2-consec → SPLIT FULLY VALIDATED; **Sprint 57.61 3rd validation 1st BACKEND-ONLY ratio ~0.74 BELOW band by 0.11** — single BELOW point vs 2 IN → rollback rule needs 2 consec same-direction → KEEP 0.65 single-data-point caution; backend-only validator+422-envelope runs faster than the backend+frontend pair the 0.65 was calibrated on, counterfactual `-port-style` 0.45 → ~1.06 IN band → NEW carryover `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch` needs 2nd backend-only point before any sub-class refinement; **Sprint 57.62 4th validation BACK TO PAIR SHAPE ratio ~0.77 BELOW band by 0.08** — pair sub-seq 57.56=1.02 + 57.57=1.15 + 57.62=0.77 mean ~0.98 IN band → KEEP 0.65 single-data-point-per-shape; **R6 WEAKENS** — 57.61 backend-only 0.74 + 57.62 pair 0.77 = 2 consec below regardless of shape → likely agent over-delivers generally; `AD-AgentFactor-DesignDecisions-Below-Band-Watch` broadens cross-shape: next `-design-decisions` (either shape) < 0.85 → tighten 0.65 → 0.55)
    mixed-multidomain-bundle-mechanical:          0.45   (3+ independent tracks WITH mechanical pattern reuse component — e.g. backend ORM + Pydantic + tests bundle; History: Sprint 57.46 ratio 1.60 at 0.45→rollback 0.65 (Option B); Sprint 57.58 tier-3 1st validation ~0.49 BELOW band single-data-point KEEP 0.65; Sprint 57.59 tier-3 2nd validation ~0.34 BELOW band → 2 consec < 0.7 ROLLBACK RULE MET → **tighten 0.65 → 0.45 effective Sprint 57.60+**; note even 0.45 ≈ 0.49 still below band — if Sprint 57.60 1st validation under 0.45 also < 0.7 → escalate 0.30 OR fold into mechanical-pattern-reuse-heavy 0.30)
    mixed-multidomain-bundle-non-mechanical:      1.0    (3+ independent tracks of pure audit/docs/rules — NO mechanical pattern reuse; e.g. Sprint 57.51 + 57.52 both ratios > 1.20 at 0.65 = 2nd rollback-trigger MET; tier-3 SPLIT Sprint 57.52 retro effective 2026-05-27 onwards)
  partial (20-79% via agent):          0.75   (linear interpolation)
  human (<20% via agent):              1.0
  History: 0.55 (Sprint 57.42 activated) → 0.45 (Sprint 57.44 tighten) → 0.65 (Sprint 57.46 rollback) → Option B sub-class split (Sprint 57.48; mechanical-single-domain 0.45 + mixed-multidomain-bundle 0.65) → Option B tier-2 split (Sprint 57.50; closes AD-AgentFactor-Tier-2-Refinement-Proposal; mechanical-single-domain split into pattern-reuse-heavy 0.30 + greenfield 0.50; parallel Sprint 57.38 `-simple/-with-extras` precedent + Sprint 57.48 Option B precedent) → Option B tier-3 split (Sprint 57.52; mixed-multidomain-bundle split into -mechanical 0.65 unchanged + -non-mechanical 1.0 NEW; closes AD-AgentFactor-Tier-2-MixedBundle-Validation-Sprint-57.52; rollback rule "2 sprints with ratio > 1.20 → mandatory structural action" MET via Sprint 57.51=1.49 + Sprint 57.52=~1.85) → Option B tier-4 split (Sprint 57.55; mechanical-greenfield split into -port-style 0.45 RESERVED + -design-decisions 0.65 NEW; closes AD-Sub-Class-Greenfield-Port-vs-Design-Refinement Sprint 57.54 CONDITIONAL carryover; rollback rule MET via Sprint 57.54 ratio ~1.37-2.0 + Sprint 57.55 ratio ~1.57 — both > 1.20 at 0.50 baseline)
}
```

**When `agent-delegated` applies**: ≥ 80% of Day 1 work via code-implementer agent (or equivalent). 20-79% = `partial` (apply `agent_factor = 0.75` linear interpolation; record explicit tag in retro Q2). < 20% = `human` (apply `agent_factor = 1.0`; existing class multiplier alone).

**Rollback rule** (3-sprint window — parallel to existing `When to adjust the multiplier` discipline):
- If activated factor produces **2 sprints with `actual/committed-with-agent-factor` ratio < 0.7** → tighten to `0.45`
- If activated factor produces **1 sprint with ratio > 1.20** → roll back to `0.65` (single-data-point caution)
- If activated factor produces **≥ 2 sprints with ratio > 1.20** → roll back to `1.0` (drop the modifier — agent delegation didn't actually accelerate; class-multiplier alone sufficient)

**Escalation to Option B** (per-class sub-class split — fallback if Option A undershoots specific classes):
- If `0.55` produces ratio < 0.7 OR > 1.20 for **≥ 2 specific classes** over 3-sprint window → switch from Option A to Option B per-class split (add `+ agent-delegated` sub-row for each high-volume class; proposed baseline ranges: `-with-extras` 0.30-0.40 / `mockup-strict-rebuild` 0.25-0.35 / `verbatim-css-repoint -simple` 0.25-0.30; matches existing matrix granularity)

**Tracking discipline** (MANDATORY from Sprint 57.43+):

Each agent-delegated sprint MUST record in retrospective Q2:
1. `actual/bottom-up` ratio (existing)
2. `actual/committed` ratio (now `committed = bottom_up × scope_class_mult × agent_factor`)
3. **NEW**: explicit `agent-delegated: yes / no / partial` tag (≥ 80% = `yes`; 20-79% = `partial`; < 20% = `no`)

Sprint plan §Workload Calibration MUST state estimate in the **four-segment form** when agent delegation is anticipated:

> Bottom-up est ~X hr → class-calibrated commit ~Y hr (mult Z) → agent-adjusted commit ~Y' hr (agent_factor 0.55)

where `Y' = Y × 0.55 = X × Z × 0.55`. See §Workload Calibration §Four-segment form above.

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
- Test-infra files (pytest markers, fixtures, e2e specs) cited in plan §Technical Spec / §Acceptance — Glob-verify they exist, NOT just product files. Sprint 57.66 D-DAY0: a phantom `test_chat_e2e_real_llm.py` + `real_llm` marker propagated across 3 plans before a Prong-1 sweep caught they never existed (`AD-Day0-Prong1-TestInfra-File-Verify`).

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
| **Claimed-but-silent-constraint-delta** | "frontend re-point shipped" / "+N tests added" / "bundle size unchanged" | `git diff $(git merge-base main HEAD)..HEAD -- 'frontend/src/**' \| grep -cE '^\+[^+].*oklch\('` — count delta against `HEX_OKLCH_BASELINE` in `check-mockup-fidelity.mjs`; same pattern applies to AP-N detector counts, Vite bundle size byte delta, pytest/Vitest count deltas. In agent-delegated migration sprints, the agent typically nails the visual/code change BUT silently exceeds baseline-constrained metrics (HEX_OKLCH literal count, AP-N count, bundle KB). Day 0 grep surfaces the delta upfront so baseline bump lands in same Day 1 commit (instead of next PR's CI hotfix). ROI evidence: Sprint 57.49 silent HEX_OKLCH +1 → PR #200 hotfix `74ed8a2f` post-merge fix-forward; AUDIT-001 (Sprint 57.51 Track C) Verdict A confirmed intended verbatim port + this rule extraction. |
| **Stale-docstring-Karpathy-3** | docstring/MHist claims "X uses Y" / "TODO remove Z next sprint" / "deprecated since Sprint N" | `grep -nE '"""\|^#\|^//\|^/\*' {target_file}` to find docstring/comment regions; then cross-grep the referenced symbol/file against repo reality. Docstrings + module-level comments + MHist entries are "code" for the dead-code rule (Karpathy §3) — when they reference symbols/features that have been removed, they're orphan claims that mislead Day 0 reviewers. ROI evidence: Sprint 57.50 D-DAY0-8 — `_fixtures.ts` L21 docstring referenced SEATS_FIXTURE which Sprint 57.49 had already removed; Day 0 caught the stale comment, Sprint 57.50 task 1.2.4 scope shrunk from ~5 min Day 1 surprise rework to ~1 min docstring cleanup. |
| **Claimed-but-missing-storage-path** (Sprint 57.57 PROMOTION) | "tenant overrides stored at `Tenant.<col>`" / "<Resource>OverrideStore table exists" / "PUT writes to dedicated `tenant_<resource>` table" | `grep -rn "meta_data\[.<key>.\]\|<Resource>Service\|class .*<Resource>.*Store\|tenant_<resource>" backend/src/` — discover actual storage architecture (dedicated table vs JSONB-on-registry-table vs JSONB-on-tenants-meta_data) BEFORE plan §4.1 commits to a Pydantic write shape. ROI evidence (3-data-point): Sprint 57.55 D-DAY0-B 🔴 RED (plan assumed `tenants.meta_data["tenant_overrides"]` → reality `feature_flags.tenant_overrides[str(tid)]` JSONB ON registry table; pivot saved ~30-45 min); Sprint 57.56 D-DAY0-A 🔴 RED (plan assumed Quotas has override storage → reality PlanQuota per-Plan template immutable; Option B `tenants.meta_data["quota_overrides"]` JSONB direct write; pivot saved ~60 min vs plan v0 abort); Sprint 57.57 D-DAY0-A ✅ GREEN inverse-validation (storage path `tenant.meta_data["rate_limits"]` established Sprint 57.48 Track D → no plan pivot needed; rule produces actionable outcome in BOTH directions). Codified Sprint 57.57 closeout per `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` PROMOTION. |
| **Claimed-but-missing-canonical-service** (Sprint 57.57 PROMOTION) | "extend `<Resource>Service.set_override` method" / "add `<Resource>Store.put()` upsert" / "call canonical service for audit chain auto-emit" | `grep -rn "class .*<Resource>Service\|class .*<Resource>Store\|def set_\|def put_\|def update_" backend/src/<scope>/` — discover canonical service availability (exists → use canonical method for cleaner audit chain + cache invalidation; doesn't exist → direct ORM UPDATE + manual `append_audit` pattern Sprint 57.3 + 57.56 precedent). ROI evidence (2-data-point both directions actionable): Sprint 57.55 D-DAY0-T 🆕 NOTABLE positive direction (`FeatureFlagsService.set_tenant_override` Sprint 56.1 IS canonical setter auto-emitting audit chain → clean V2 service path; REMOVED `AD-FeatureFlags-PerFlag-AuditLog-Phase58` carryover positive side-effect); Sprint 57.56 D-DAY0-D 🆕 NOTABLE inverse direction (NO canonical service for Quotas → architectural simplification path = direct ORM UPDATE + manual `append_audit`; Sprint 57.3 PATCH precedent); Sprint 57.57 D-DAY0-B inverse continued (NO canonical service for RateLimits → same direct ORM path as Sprint 57.56). Both directions produce actionable plan pivots — codified Sprint 57.57 closeout per `AD-Day0-Prong2-CanonicalService-Grep` PROMOTION. |
| **Claimed-but-nested-shape-mismatch** (Sprint 57.60 PROMOTION) | "stored as `{resource, window, limit}`" / "config items are typed objects" / "the JSONB holds `{key: value}` dicts" | when the plan asserts the NESTED shape of a stored blob (JSONB / dict / list-of-dicts), READ the actual Pydantic model / dataclass / TypedDict BODY — do NOT infer from the key name alone. `grep -rn "class .*<Model>\|<field>:" backend/src/` to locate, THEN Read the model body to confirm the real nested shape. ROI evidence (2-data-point): Sprint 57.58 D-DAY1-1 (stored `meta_data["rate_limits"]` shape is UI display strings `{label, value}` e.g. `{"label":"API requests","value":"100 / min"}` NOT the assumed `{resource, window, limit}` — the runtime gate had to normalize via `parse_rate_limit_item`; caught mid-Day-1); Sprint 57.59 reinforced (both the live normalizer + the inline `0019` migration parser keyed off the `{label, value}` shape, not the assumed typed object). Reading the model body at Day 0 surfaces the real shape before plan §4 commits to a parse/write contract. Codified Sprint 57.60 closeout per `AD-Day0-Prong2-Nested-Shape-Read` PROMOTION. |
| **Claimed-but-flat-codegen-shape** (Sprint 57.67 — 4 data points, fold-in) | "codegen TS event/DTO types from existing Python types" / "interface mirrors the dataclass" | when GENERATING consumer types/schemas from existing producer types, capture the STRUCTURAL SHAPE (envelope nesting), NOT just field names — Read the producer/serializer body first. Sprint 57.67 stage-1 emitted flat `{type, ...fields}` but the wire is nested `{type, data:{...}}`; recurred 4× → `AD-Day0-Codegen-Existing-Shape-Capture`. Verify the wire envelope nesting before drafting the consumer type. |
| **Claimed-but-no-live-producer** ("fill/wrap/instrument every X" scopes; Sprint 57.71 + 57.72) | "wrap every loop span" / "fill all N Inspector tabs" / "instrument every call site" | for "fill/wrap/instrument every X" scopes, grep that EACH X has a live producer / call-site BEFORE planning to surface it — else the slot is an AP-4 Potemkin. Sprint 57.71: 2 of 6 tracer spans had no loop-level call site (deferred, not faked); 57.72: only 1 of 3 Inspector tabs had a live event producer (Tree shipped; Trace/Memory → ComingSoon). |

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
| **Physical-column-vs-ORM-alias** (Sprint 57.60 PROMOTION) | "raw SQL `UPDATE tenants SET meta_data ...`" / "migration reads the `meta_data` column" | when a migration / raw SQL touches a column whose ORM attribute is an ALIAS (`mapped_column("physical_name", ...)`), the raw SQL MUST use the PHYSICAL column name, not the ORM attr. `grep -n "mapped_column(\"" backend/src/infrastructure/db/models/*.py` — any `mapped_column("X", ...)` where `X` ≠ the Python attr name = alias; raw SQL must quote `"X"`. ROI evidence (2-data-point): Sprint 57.59 D-DAY1-1 (tenants JSONB ORM attr `meta_data` is `mapped_column("metadata", ...)` in `identity.py`; the `0019` data-migration raw SQL had to use `"metadata"` not `meta_data` — caught mid-Day-1); Sprint 57.60 D-DAY0-M (applied pre-emptively at plan-time — `0020` raw SQL uses `"metadata"` from the start; 0 mid-sprint surprise). Codified Sprint 57.60 closeout per `AD-Day0-Prong3-Physical-Column-Read` PROMOTION. |

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

### Risk Class A: Paths-filter vs `required_status_checks` (CI infra) — ⚠️ RETIRED Sprint 55.6

**Status**: **NO LONGER APPLIES.** Sprint 55.6 removed the `paths` filter from `.github/workflows/backend-ci.yml` (Option Z, closes AD-CI-5) → **every PR now runs full backend CI + v2-lints**, including docs-only / `.gitignore`-only PRs. There is no paths-filter `BLOCKED` situation and **no touch-`backend-ci.yml` workaround is needed**. The `backend-ci.yml` header is the authoritative source.

**Historical (53.2.5 – 55.6, audit trail)**: docs-only PRs once didn't trigger the path-filtered backend-ci → required contexts never reported → `mergeStateStatus = BLOCKED`. Interim fix was a header-comment touch on `backend-ci.yml` (53.2.5). Retired permanently in 55.6 by dropping the paths filter (trade-off ~+1.5 min CI per docs-only PR; acceptable for solo-dev volume).

**Residual edge case (NOT paths-filter)**: a rare GitHub webhook miss/delay can still leave checks unreported (e.g. PR #203, Sprint 57.53) — a header touch re-triggers, but that is a webhook quirk, not the retired paths-filter issue.

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

**Related (Sprint 57.68 reinforcement, `AD-Source-DB-Call-Test-Isolation`)**: Adding a NEW DB call to a previously DB-free endpoint can surface a latent isolation leak — TestClient overrides auth but NOT `get_db_session`, so the endpoint hits a non-test session. Symptom: tests that passed pre-change fail only after the endpoint gains a query. Fix: ensure the suite's `get_db_session` dependency override (or autouse session fixture) covers the newly-DB-touching endpoint.

### Risk Class D: ORM File Path Reference Style (sprint planning)

**Symptom**: Plan §8 Risks row references an ORM model with a speculation-based path like `backend/src/infrastructure/db/models/<table_name>.py` (e.g. `tenant.py`); Day 0.8 Prong 2 then wastes 3-5 min discovering the model lives elsewhere (e.g. `identity.py` per domain cohesion grouping).

**Source**: Sprint 57.50 D-DAY0-2 — plan referenced `Tenant.meta_data` JSONB; AI initially looked at `tenant.py` (did not exist); Prong 2 grep resolved to `identity.py` per `09-db-schema-design.md` Group 1 (Identity & Tenancy domain groups User + Role + OIDCProvider + Tenant in one file). Verified in Sprint 57.51 Day 0.8 D-DAY0-3.

**Workaround**: Cite `09-db-schema-design.md §Group N <Domain Name>` in plan §Risks rows touching ORM models, not the speculation-based `.py` path. Example: "Risk: `Tenant.X` field doesn't exist — mitigation: Day 0.8 Prong 2 read `Tenant` ORM in `09-db-schema-design.md §Group 1 Identity & Tenancy` (note: file is `identity.py`, not `tenant.py`)."

**Long-term fix**: Codify in Plan template stub (when Plan template doc is formalized as part of `.claude/rules/`).

### Risk Class E: Stale long-running `--reload` backend masks a wiring/startup fix (local verification)

**Symptom**: A fix that only takes effect at process startup (lifespan wiring, env load, DI singleton construction) appears NOT to work when verified against an already-running dev backend — because the running process started BEFORE the fix landed (or its `--reload` worker reloaded module code but did NOT re-run lifespan startup). Looks like a code bug; is actually process-state.

**Source**: 2026-06-03 C-11 `cost_ledger Δ=0` (`AD-RealLLM-CostLedger-ProcessState-Verify`). FIX-022 pricing-loader wiring was on disk, but the running backend had `cost_ledger_service=None` from its own stale startup → router gate skipped every cost row. A clean restart → startup log `pricing loader wired` (`main.py:149`) → `cost_ledger Δ=2`. Compounded by 2 stale `--reload` reloaders sharing :8000 via SO_REUSEADDR (Errno 10048 on re-bind).

**Workaround**: When verifying startup/wiring behavior locally, do a CLEAN restart first: kill ALL stale uvicorn reloader+worker processes on the port (not just the listener — a `--reload` worker is a `multiprocessing.spawn` child whose cmdline lacks `uvicorn`), confirm the port is free + your new process is the sole owner (no Errno 10048), then re-verify and capture the startup log line proving the wiring fired.

**Reinforcement (Sprint 57.97, D-DAY3-1 — orphaned spawn-worker)**: The drive-through verifying cheap-tier verification recorded the STRONG model on the first 2 chats despite a `dev.py restart` reporting a fresh PID — and it was NOT a code bug (a reproduce-script proved the builder built the cheap client). The real culprit: an orphaned `multiprocessing.spawn` worker (a child of a long-DEAD reloader from a PRIOR sprint) was STILL ALIVE serving :8000 via SO_REUSEADDR with old code + old `.env`. `dev.py stop` + `netstat` + `taskkill /PID <port-owner>` ALL missed it because the socket was attributed to the dead PARENT and the worker's cmdline is `python -c "from multiprocessing..."` (no "uvicorn"). **A clean restart must verify the LIVE serving process, not the port-owner PID.** The reliable check on Windows: `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` → inspect PID / PPID / StartTime → `Stop-Process -Force` any worker whose parent is dead or whose StartTime predates the current restart. For startup-only/env-loaded behavior (the cheap client is built at startup from `.env`), set the env BEFORE the restart and confirm the fresh PID is the SOLE live worker.

**Long-term fix**: Prefer `python scripts/dev.py restart backend` (kills by port owner) over assuming the running process is current; for one-off wiring checks, a no-`--reload` single process with log redirect gives a deterministic startup log. When SO_REUSEADDR orphans recur, fall back to the `Win32_Process` PID/PPID/StartTime sweep above (port-owner kills are insufficient against spawn-worker orphans).

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

7. **Agent-delegated work — run ALL gates yourself; don't trust the agent's report** (Sprint 57.69 + 57.73)
   - Delegated FE work MUST run the FULL gate set incl. `npm run check:mockup-fidelity` (not just lint/build/test). Sprint 57.69: a delegated agent ran lint/build/test but skipped `check:mockup-fidelity`; 2 `oklch(...)` tints would have silently failed `HEX_OKLCH_BASELINE` at PR — parent re-verify caught it pre-PR.
   - Pin language / convention in the agent prompt: user-facing copy follows the codebase convention (English state strings, not 繁中). Sprint 57.73: a delegated agent wrote 繁中 state copy the parent had to rewrite.
   - Parent independent re-verify: re-run every gate yourself; treat the agent's "all green" as unverified until reproduced (57.66 stringified-float / 57.67 flat-vs-nested / 57.68 wrong isolation culprit were all caught this way).
   - Tooling: if Bash `grep` output looks corrupted (e.g. token substitution), re-read via a dedicated reader (Read/Grep tool) before acting on it (Sprint 57.70).

8. **Drive-Through Acceptance — user-facing features must be DRIVEN, not just gated** (2026-06-06; closes AD-Drive-Through-Acceptance; full rationale CLAUDE.md §Drive-Through Acceptance Hard Constraint + `memory/feedback_drive_through_over_paper_metrics.md`)
   - Any feature a human reaches through the UI MUST be verified by actually driving the real UI (dev server) + real backend + real LLM (NOT echo/mock) through its primary path BEFORE it can be marked done. Gate-pass + curl prove the parts work / the API responds; NEITHER proves the car drives.
   - Walk every control on the path: clickable? has an effect? label real (not hardcoded / fixture)? does the result actually render? (chat-v2 escape 2026-06-06: dead "New session" button + fixture session list + hardcoded `claude-haiku-4-5` badge + agent answer never rendered — all AP-4 Potemkin sitting on the 主流量, all green on every gate. PR #253 also wrote "~80-85% working" off curl-only verification with "UI 驅動未做" self-noted — exactly the trap.)
   - Do NOT write "verified" / "~X% working" for anything whose drive-through layer wasn't actually run — write "未驗證 (gate-only)" instead. Backend-not-ready widgets: render per mockup with fixture data BUT label DEMO (or leave blank) — never let fixture masquerade as real.
   - Evidence: screenshot + "observed vs intended flow" diff into progress.md / CHANGE record.
   - Scope: applies to any task touching a user-facing surface (frontend page / SSE-driven flow / API a human drives via UI). Pure-backend / pure-infra tasks that no human drives through a UI are exempt — but their reports MUST say "gate-only verified", not imply usability.

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
- ❌ Mark a user-facing feature done — or report it "verified / ~X% working" — without an actual drive-through (real UI + real backend + real LLM); gate-pass / curl is NOT drive-through (AD-Drive-Through-Acceptance; see Before Commit item 8)

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
