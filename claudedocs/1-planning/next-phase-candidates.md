# Next Phase 候選 (Phase 57.22+)

**Purpose**: Open items / pending decisions / carryover ADs accumulated from prior sprint retrospectives. Single-source for "what could be next sprint". CLAUDE.md / MEMORY.md no longer carry this list per §Sprint Closeout policy ([`.claude/rules/sprint-workflow.md`](../../.claude/rules/sprint-workflow.md)).

**Selection Rule**: User explicitly selects → draft plan kicks off Sprint XX.Y; otherwise items wait here indefinitely until selected or archived.

**Updated**: 2026-05-24 (Sprint 57.37 closeout — 2-domain batched: /loop-debug full rebuild closes 57.36 mockup-fidelity gap + /state-inspector Phase-2 re-point; user-reported empty-state RESOLVED; **3-consecutive-above-band lift trigger MET** for `frontend-verbatim-css-repoint` → NEW class-split-proposal AD candidate for Sprint 57.38)

---

## 🆕 Sprint 57.37 Carryover (2026-05-24 — 2-domain batched: /loop-debug full rebuild + /state-inspector Phase-2)

Sprint 57.37 (`AD-LoopDebug-Full-Rebuild-And-StateInspector-Repoint`) closed: 2-domain batched. **Domain A /loop-debug full mockup-fidelity rebuild** closes Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap — 18-event fixture (`_fixtures/demoLoopEvents.ts` NEW) + playback strip (cursor/play/pause/scrubber/speed 1×/4×/8×/16×) + filter pills (6 categories) + LoopInspector right pane (KvRow + HITL Policy + Raw payload) + corrected AP-2 DEMO DATA banner. **User-reported `/loop-debug` empty-state issue FULLY RESOLVED** (after.png shows visual parity with mockup `localhost:8080/#loop-debug`). **Domain B /state-inspector** Phase-2 verbatim CSS re-point per `page-platform.jsx:21-155` preserves Sprint 57.19 US-B3 backend wiring. 22-route sweep **18 IDENTICAL + 4 CHANGED** (loop-debug +63,405 B fixture-rich +66%; state-inspector -14,681 B verbatim simpler; chat-v2 **0 B PERFECT cascade**; auth-callback -68 B + overview +138 B noise). 4 gates green. Vitest **464/464** (+8 NEW Domain A specs; D-DAY3-1 Domain B spec class-swap-resilient — NO update needed). HEX_OKLCH_BASELINE 41→50 within Day 0 D-DAY0-6 estimate. Sprint total ratio ~1.0 IN BAND middle (2-domain HYBRID averaging). Agent-assisted Day 1-3 (4th consecutive code-implementer; ~4.5 hr wall-clock). Updates:

- ✅ **RESOLVED: Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap on /loop-debug** — fixture demo + 4 mockup widgets shipped per CLAUDE.md rule "後端尚未支援的 widget → 仍依 mockup 視覺實作，data 用 fixture"
- ✅ **RESOLVED: User-reported `/loop-debug` empty-state UX issue 2026-05-24** — page now visually parity with mockup

- 🆕 **NEW DECISION CANDIDATE: `AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal`** — Domain B 4th non-rich data point 1.33 ABOVE band; **3-consecutive-above-band lift trigger MET** (57.35=1.7 + 57.36=1.42 + 57.37B=1.33; 4-pt non-rich mean 1.36). Per `When to adjust` rule (3+ consecutive > 1.20 → raise multiplier). **Two options for Sprint 57.38 retro decision**:
  - **Option 1**: class-wide baseline lift 0.50 → 0.60 (simpler; over-corrects truly simple 57.34 baseline)
  - **Option 2 (recommended)**: class split `-simple` (0.50): pure 1-file CSS swap no extras (Sprint 57.34 baseline 1.0 in-band) vs `-with-extras` (0.65): + any of {AP-2 banner, dual-mount, playback/filter/inspector widgets, verbatim oklch-heavy port with HEX_OKLCH_BASELINE bumps, multi-file batched > 3 files} (Sprints 57.35/57.36/57.37B mean 1.48)

- 🔄 **Updated: `AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch`** (Sprint 57.36 NEW) — 4th non-rich data point empirically confirms multi-D hypothesis; closed either Option 1 or Option 2 in Sprint 57.38

- 🔄 **Updated: `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** (Sprint 57.31 NEW) — alternative lift path; closed either Option 1 or Option 2 in Sprint 57.38

- 🆕 **Convention candidate (D-DAY3-1 positive surprise)**: Vitest spec class-swap-resilience — prefer `getByText` / `getByRole` / `data-testid` over class-name selectors. Codify in `.claude/rules/sprint-workflow.md` OR `docs/rules-on-demand/frontend-react.md`. StateInspectorPage spec needed NO update during Sprint 57.37 Day 3 verbatim port — saved ~10-15 min spec adapt time.

- 🆕 **Lesson**: Calibration ratio formula clarification — `actual / calibrated` (NOT `actual / bottom-up`); codify in sprint-workflow.md to prevent agent prediction errors like Sprint 57.37 Day 3 estimate

- 🆕 **Tracking**: `/overview` + `/auth-callback` recurring noise pattern in route-sweep PNGs (overview +138 B Sprint 57.37 / +70 B Sprint 57.36; auth-callback -68 B Sprint 57.37 first occurrence) — investigate if persists 3+ sprints; likely time-relative text or PNG AA variance

- 🎯 **Phase-2 epic progress**: 7+1 routes shipped (7 Phase-2 routes + AuthShell + LoopVisualizer dual-mount + StateInspectorPage full re-point) / **7 🟡 routes remaining** (governance / admin-tenants / tenant-settings STRUCTURAL Phase 58+ / memory STRUCTURAL Phase 58+ / compaction + 3 unblocked-by-57.33 PROP stubs)

- 🔍 **Drift findings** (Day 0-3): D-DAY0-1..7 (Day 0 verifications) / D-DAY1-1 (TS forEach→for-loop) / D-DAY2-1..3 (17 lint fixes + baseline +3 + fixture 18 events) / D-DAY3-1..3 (spec NO update positive surprise + baseline +6 + KvLine helper <10 line creep)

## 🆕 Sprint 57.36 Carryover (2026-05-24 — /loop-debug Phase-2)

Sprint 57.36 (`AD-Loop-Debug-Verbatim-Repoint`) closed: `frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx` single-file re-pointed to mockup verbatim per `reference/design-mockups/page-governance.jsx:33-212`. **7th Phase-2 epic app; 3rd shape-validation data point.** 22-route sweep **19 IDENTICAL + 3 CHANGED** (loop-debug +22,512 B expected structural; chat-v2 +18 B cascade ε; overview +70 B time-text noise). 4 gates green (TS 0 / lint 0 / Vitest 456/456 / mockup-fidelity 41/41 unchanged). Agent-assisted Day 1-2 via code-implementer agent (3rd consecutive validated; ~80 min wall-clock). AP-2 BackendGapBanner + EmptyInspectorPlaceholder explicitly defer playback/scrubber/filter/inspector pane to Phase 58+ per Sprint 57.12 AP-6. Dual-mount preserved (Sprint 57.30 chat-v2 inline ship safe). ~205 min total human-equivalent. Ratio actual/committed ~1.42 ABOVE band by 0.22. Updates:

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch** — Sprint 57.36 is 3rd shape data point: 1-file non-rich AGAIN (like 57.34) but ratio diverged sharply (1.0 vs 1.42). Both prior 1-D hypotheses (bimodal-by-shape AND scale-overhead) insufficient. Emerging compound drivers: file count + AP-2 banner addition + dual-mount complexity + spec adapt + drift handling. If Sprint 57.37+ continues > 1.20, propose either (a) baseline lift 0.50 → 0.60, or (b) class split `frontend-verbatim-css-repoint-simple` (0.50, no AP-2 / no dual-mount) vs `frontend-verbatim-css-repoint-with-ap2-or-dual-mount` (0.65). KEEP 0.50 this iteration per `When to adjust` 3-sprint window rule (3-pt non-rich: 1.0/1.7/1.42 needs 1 more above-band for formal lift trigger).

- 🔚 **CLOSED: AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** (Sprint 57.34 NEW; Sprint 57.35 weakened) — 3 non-rich data points (57.34=1.0 / 57.35=1.7 / 57.36=1.42) span the whole band; not bimodal. REJECTED.

- 🔄 **Updated → WEAKENED: AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch** (Sprint 57.35 NEW) — 1-file (57.36) ALSO above band (1.42); file-count alone is not the variance driver. Broaden into multi-dimensional-variance-watch.

- 🔄 **Updated: AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 4th validation data point logged. 0.50 baseline still appropriate for **simple non-rich 1-file** sprints (57.34 only in-band data point); above-band trend (57.35 + 57.36) needs 1 more above-band sprint for formal lift trigger.

- 📚 **Lessons logged**:
  - Day 0 Prong 1 glob coverage rule: extend to BOTH `frontend/src/**` AND `frontend/tests/**` for spec-existence claims (test files conventionally live outside `src/`). D-DAY1-1 cost ~5 min in agent re-discovery. Codify in `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 1.
  - AP-2 BackendGapBanner addition: ~10-15% calibration surcharge candidate.
  - Dual-mount preservation (mode-branching): ~5-10% surcharge candidate.
  - Combined sprints (AP-2 + dual-mount) should baseline ~0.60-0.65 not 0.50.
  - ESLint `no-restricted-syntax` JSXAttribute style matcher is body-blind for `style={CONSTANT_REF}`; Sprint 57.24 BarTrack STYLE.md §3 escape hatch (module-scope constants + per-site `eslint-disable-next-line`) is the documented workaround.

- 🔍 **Drift findings** (Day 0-1): D-DAY0-1..7 catalogued in progress.md; D-DAY1-1 (test file location) + D-DAY1-2 (ESLint body-blind) caught by agent.

- 🎯 **Phase-2 epic progress**: 6 routes shipped (+ AuthShell + LoopVisualizer dual-mount) / 8 routes remaining (state-inspector, memory STRUCTURAL Phase 58+, governance multi-page, admin-tenants, tenant-settings STRUCTURAL, compaction, 3 unblocked-by-57.33 PROP stubs).

## Sprint 57.35 Carryover (2026-05-24 — AuthShell + 7 auth routes Phase-2)

Sprint 57.35 (`AD-Auth-Shell-And-Pages-Verbatim-Repoint`) closed: 8 files (1 AuthShell + 7 auth routes) re-pointed to mockup verbatim — **6th Phase-2 epic app**; user-reported `/auth/login` drift 2026-05-24 (SSO unstyled / Continue no fill / `dev-login` orange missing) **fully RESOLVED**; **closes Sprint 57.23 vintage HSL-translation epic gap** on auth routes (CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint warning). 22-route sweep **0 regressions** on other 14 routes. 5 gates green. Vitest **456/456 baseline preserved** (4 spec files updated `getByLabelText` → `getByText`+id selectors for mockup-ui Field DOM change; behavioral test intent preserved). Agent-assisted Day 1-3 via code-implementer agent. ~7-7.5 hr human-equivalent effort. Updates:

- ✅ **RESOLVED — Sprint 57.23 vintage HSL-translation epic gap on auth routes** (CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint warning) — fully closed by this sprint.

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch** — Sprint 57.35 ratio ~1.65-1.75 ABOVE [0.85, 1.20] band by ~0.45-0.55 (8-file batched sprint). Combined with 57.34 (1-file ≈1.0 in band) + 57.35 (8-file ~1.7 above band), both non-rich-dashboard but vastly different ratios — **file-count + Vitest-spec-update overhead emerging as 2nd variance driver** (not pure shape-driven). If Sprint 57.36+ multi-file sprints again > 1.20 → propose **file-count surcharge** in calibration multiplier (e.g. 0.50 + 0.05/extra-file beyond ~3). KEEP 0.50 baseline this iteration per `When to adjust` 3-sprint window rule (3-pt span 0.40/1.0/1.7 inconclusive).

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** (Sprint 57.34 NEW) — bimodal-by-shape hypothesis **WEAKENED but not REJECTED**. 2 non-rich data points (57.34 vs 57.35) span ratio 1.0 to 1.7, suggesting shape is NOT the dominant variance driver; file-count is. Broaden to **scale-and-shape watch**; don't propose class split until 4th data point discriminates.

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 3rd validation data point logged. 0.50 baseline still appropriate for typical 1-file re-points.

- 📚 **Lessons logged**:
  - File-count + Vitest-spec-update overhead may be 2nd variance driver beyond shape; budget per-file linearly for multi-file sprints
  - Vitest spec update budget when primitive API changes (e.g. `<label>` → `<div>`); 30-60 min per primitive switch
  - Mockup-internal drift: `page-extras.jsx:13` AuthShell width 400px vs sibling `page-auth-extras.jsx:13` AuthShellX 420px — designate canonical source in `reference/design-mockups/AGENTS.md`

- 🔍 **Drift findings** (Day 1-3): D-DAY1-1 (AuthShell width 420→400 mockup truth) / D-DAY2-1 (register plan label a11y aria-label added) / D-DAY2-2 (register demo banner recast as `.hitl-card[data-severity="risk-medium"]`) / D-DAY3-1 (expired Badge tone="warning" per mockup)

## Sprint 57.34 Carryover (2026-05-24 — /orchestrator Phase-2)

Sprint 57.34 (`AD-Orchestrator-Verbatim-Repoint`) closed: `/orchestrator` re-pointed to mockup verbatim — **1st non-rich-dashboard shape** in the Phase-2 epic (prior 4 = rich operator dashboards). 22-route sweep **0 regressions** on other 21 routes. 5 gates green. Vitest 456/456 baseline preserved. Agent-assisted Day 1-3 via code-implementer agent (per CLAUDE.md Tool Optimization). 3 mockup-ui primitives promoted (Tabs / Field / Switch). OrchestratorPage 644 → 605 net –39 lines (drop ~150 lines of local primitives + Tailwind translations; add mockup-ui imports + verbatim CSS classes + data-testid hooks). ~3-4 hr human-equivalent effort. Carryover updates:

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** — Sprint 57.34 ratio ≈0.95-1.05 lands in [0.85, 1.20] band middle. Combined with prior 4 rich-dashboard apps (3-pt mean ≈0.40 below band ex-57.29 anchor), **bimodal-by-shape pattern emerging** — rich-dashboard ratios consistently below band; non-rich-dashboard (1st data point) in band middle. 2-data-point span (57.32 rich + 57.34 non-rich) suggestive but insufficient per `When to adjust` 3-sprint window rule. **KEEP 0.50 baseline this iteration.** If Sprint 57.35 (another non-rich-dashboard shape — `/loop-debug` / `/state-inspector` / `/admin-tenants` / `/governance` / `/tenant-settings`) confirms in-band → propose class split `-rich-dashboard` (0.40) vs `-config-form` (0.50). If lands below band → class-wide variance after all → 0.50 → 0.40 lift.

- 🆕 **AD-Tabs-Migration-To-MockupUi** (low priority) — `frontend/src/components/ui/tabs.tsx` Sprint 57.19 vintage primitive still imported by other consumers (governance/loop-debug/state-inspector candidates); out-of-scope this sprint. Future Phase-2 re-point of those routes will naturally migrate them to mockup-ui Tabs, then `ui/tabs.tsx` can be deleted.

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 2nd validation data point logged. 0.50 baseline still appropriate but bimodal-by-shape signal emerging. If 57.35 confirms, may close this AD in favor of class split.

- 📚 **Atomic primitive promotion lesson** — when primitive promotions span multiple Days but consumer components consume them together, atomic Day 1 promotion is the right call (vs staggered across Days). Agent correctly identified this build-dep; Day 2/3 commits became cycle housekeeping. Plan structure looks "off" in retrospect but result was clean.

## Sprint 57.33 Carryover (2026-05-24 — Page Bug Fix Sweep)

Sprint 57.33 (`AD-Page-Bug-Fix-Sweep`) closed: 3 ⚪ pre-existing crash routes (`/subagents` + `/memory` + `/verification`) fixed by adding defensive `(query.data.X ?? []).length/map` across 5 files / 11 sites including 4 drift sites D1-D4 (`.map` × 3 + `_groupByTurn(items)` × 1) found by widening Day 0 grep beyond `.length`. 22-route sweep: **3 ⚪ → ✅ flip + 0 regressions** on other 19 routes. Vitest 452 → 456 (4 NEW defensive specs). NEW class `frontend-page-bug-fix` 0.45 1st application; ratio actual/committed **1.24** top edge of [0.85, 1.20] band +0.04 over. ~2.8 hr wall-clock. Closes `AD-Overview-PreExisting-Route-Crashes` carryover from Sprint 57.29-32. Updates:

- ✅ **RESOLVED — AD-Overview-PreExisting-Route-Crashes** (Sprint 57.29-32 carryover) — fully closed. 3 ⚪ routes now render proper UI (subagents = full Registry + 4 KPI cards + table; memory = Recent + By Scope tabs + empty state; verification = Recent + Correction Trace tabs + filter form + empty state).

- 🆕 **AD-Sprint-Plan-frontend-page-bug-fix-1st-data-point** — KEEP 0.45 baseline per `When to adjust` 3-sprint window rule. If next 2-3 applications show ratio > 1.20 consistently → propose **0.45 → 0.55-0.60 lift** (mechanical-class-like trend, parallel to Sprint 57.16 AD-Sprint-Plan-13 `frontend-refactor-mechanical` 0.50 → 0.80 evidence).

- 🆕 **AD-CorrectionTraceView-Defensive-Spec** (low priority) — defensive Vitest spec for `CorrectionTraceView` deliberately skipped this sprint per US-D3 "1-2 new specs" scope discipline. Crash path is indirect (via `_groupByTurn(entries)` for…of); covered by Day 4 manual smoke + 22-route sweep flip. Add in future maintenance sprint if `/verification` structural rebuild is scheduled.

- 📚 **Lesson logged in retrospective Q4** — for "undefined-field" / "missing property" crash classes, Day 0 Prong 2 grep should query **all access patterns** on the at-risk field (`\.length`, `\.map`, `\.filter`, `\.forEach`, bare references as function args), not just the access pattern surfaced in the bug repro. 4 drift sites D1-D4 in this sprint are evidence.

- 🔓 **Unblocks** — Phase-2 verbatim CSS re-point candidates for `/subagents`, `/memory`, `/verification` (sweep `after` baselines now meaningful; visual fidelity audit can proceed). `/memory` STRUCTURAL rebuild Phase 58+ remains unchanged scope (independent of crash-fix).

## Sprint 57.32 Carryover (2026-05-24 — /sla-dashboard Phase-2)

Sprint 57.32 (`AD-Sla-Dashboard-Verbatim-Repoint`) closed: `/sla-dashboard` 7 files re-pointed — fidelity verdict **PARITY**, 22-route sweep **cleanest yet** (17 🟢 PARITY shell + 1 🟢 PARITY target + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails). 4th data point for `frontend-verbatim-css-repoint` 0.50 (lifted) class; **cleanest mockup mapping of any Phase-2 sprint** (0 production-only widgets — distinct from Sprint 57.31 cost-dashboard which had 3). ~3 hr total wall-clock. Carryover updates:

- **AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW; **1st validation data point this sprint**) — Sprint 57.32 ratio actual/committed ~0.40-0.55 (lower band edge). 4-pt mean ≈0.55 lower edge; 3-pt mean ≈0.40 excluding 57.29 anchor (below band by 0.30). Per `When to adjust` 3-sprint window rule, 1 validation data point insufficient to adjust further → **KEEP 0.50 baseline this iteration**. If Sprint 57.33 + 57.34 also < 0.7 → propose 0.50 → 0.40 in Sprint 57.34 retrospective.

- **Hybrid Tailwind+inline color bridge pattern matured across 5 files** (Sprint 57.29 carryover `AD-Inline-Style-Rule-vs-Verbatim-Method` partial exercise) — applied across SLAOverview, LatencyChart, SLOStatusCard, TopSlowOpsTable, ErrorRateByServiceCard. Day 2 SLOStatusCard caught 2 spec drift; Day 3 applied bridge preemptively → 0 spec drift. Pattern documented as standard for Sprint 57.25+ dashboards being Phase-2 re-pointed. Lesson: any color-tone Tailwind class (`text-warning`, `text-danger`, `text-fg-muted`) used in Sprint 57.25 spec contracts should be preserved alongside inline `style={{ color: var(--*) }}` for verbatim.

## Sprint 57.31 Carryover (2026-05-23 — /cost-dashboard Phase-2)

Sprint 57.31 (`AD-Cost-Dashboard-Verbatim-Repoint`) closed: `/cost-dashboard` 7 components batched Day 1 single agent delegation — fidelity verdict **PARITY**, 22-route sweep **cleanest yet** (18 🟢 PARITY + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails — shell unchanged from 57.30 + cost-dashboard gain internal). 3rd data point for `frontend-verbatim-css-repoint` 0.60 class. New carryover:

- **AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Day 4 calibration) — replaces CLOSED `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` (Sprint 57.30 carryover). Bimodal hypothesis REJECTED — 57.29 + 57.31 same rich-dashboard shape with vastly different ratios (1.0 vs 0.35), so shape NOT the driver of variance. Driver IS estimate generosity diminishing as class iteration matures. Per `When to adjust` 3+ consecutive < 0.7 rule (57.30 + 57.31 + the 0.45+ below-band magnitude on 2 of 3 = clear signal) → LOWER baseline 0.60 → 0.50. Validate 0.50 across next 2-3 sprints; if continues < 0.5 → consider 0.40 next iteration.
- **AD-CostBreakdownTable-Backend-Tenant-Scope** (Day 1 D4 finding) — `CostBreakdownTable.tsx` shows real backend `by_type` 2-level drill-down (`cost_type/sub_type/quantity/total_cost_usd/entry_count`) for current authenticated tenant; distinct from `TenantTopTable` (cross-tenant admin fixture). Document data ownership to prevent accidental merge in future sprints; consider adding ARCHITECTURE.md section on cost-dashboard data flows.

**3 production-only widget patterns identified** (generalizable for future Phase-2 sprints):
1. **Mockup token vocabulary only** (MonthPicker D5) — `var(--*)` inline; no AP-2 banner; UI affordance.
2. **Mockup `.table` vocabulary verbatim** (CostBreakdownTable D4 decision c) — real backend; no AP-2; same vocabulary as if mockup had it.
3. **Mockup vocabulary + AP-2 BackendGapBanner** (e.g. Sprint 57.30 InputBar error) — fixture data; AP-2 honesty banner.

---

## Sprint 57.30 Carryover (2026-05-23 — chat-v2 Phase-2 + shell hotfix; AD-Sprint-Plan-frontend-verbatim-bimodal-watch CLOSED in 57.31)

Sprint 57.30 (`AD-Chatv2-Verbatim-Repoint + Shell-Hotfix-UserMenu-Avatar`) closed: `/chat-v2` 19 components re-pointed to verbatim mockup CSS + Day 1 shell hotfix (UserMenu Radix-drop + verbatim `useDismiss` port + avatar trigger 36→26 split + topbar icon audit 0 drift) — fidelity verdict **PARITY**, 22-route sweep 0 catastrophic / 0 structural; Day 5 orphan cleanup deletes `dropdown-menu.tsx` + `npm uninstall @radix-ui/react-dropdown-menu` → bundle **-116.87 KB / -38.37 KB gzipped**. Closed `AD-UserMenu-Mockup-Structural-Deltas` (Sprint 57.29 carryover). New carryover:

- ✅ **CLOSED Sprint 57.31**: **AD-Sprint-Plan-frontend-verbatim-bimodal-watch** — Sprint 57.31 3rd data point evaluation rejected bimodal hypothesis; replaced by `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` above.
- **AD-Tsconfig-Node-NoEmit** (Day 1 finding) — `tsc --strict` reports pre-existing `TS6310: referenced project tsconfig.node.json may not disable emit` since baseline `5c0ce0dd`. Not introduced by Sprint 57.30. Defer to tooling cleanup sprint or separate PR.
- **AD-Topbar-Use-Button-Primitive** (Day 0 D4 finding) — production Topbar uses raw `<button className="btn ghost" data-size="sm">` instead of mockup-ui `<Button>` primitive. Rendered DOM byte-identical; cosmetic-code-style refactor, low ROI. Defer.
- **AD-Topbar-Tweaks-Panel-Phase58+** (Day 0 D5 finding) — mockup `shell.jsx:218` has `<Button icon="sliders" onToggleTweaks>` Tweaks button; production omits it (no Tweaks panel implementation). Defer to Phase 58+ when Tweaks panel ships.
- **AD-ApprovalCard-Legacy-Phase58-Migrate** (Day 4 finding) — `ApprovalCard` confirmed legacy per `chatStore.ts:L324` dual-emit comment; HITLTurn is canonical Phase-1 chat-inline render. Re-pointed this sprint for completeness; 0 main render path. Migrate governance integration to HITLTurn-only in Phase 58+, then delete.

---

## 🆕 Sprint 57.29 Carryover (2026-05-22 — Phase-2 per-page re-point opens; partially closed in 57.30)

Sprint 57.29 (`AD-Overview-Verbatim-Repoint`) closed: `/overview` + app shell + 3 topbar overlays + 7 widgets re-pointed to verbatim mockup CSS — fidelity verdict **PARITY**, 22-route regression sweep 0 catastrophic / 0 structural. The Phase-2 per-page re-point template is validated (`frontend-verbatim-css-repoint` 0.60 class). Carryover:

- **AD-Inline-Style-Rule-vs-Verbatim-Method** — the `no-restricted-syntax` ESLint inline-`style=` ban (Sprint 57.15/57.16) conflicts with the verbatim method's required mockup inline-style literals; currently handled per-file with `eslint-disable` + rationale. Decide: scope the rule to exclude verbatim-re-pointed dirs, or retire it.
- **AD-UserMenu-Mockup-Structural-Deltas** — ✅ **CLOSED in Sprint 57.30 Day 1**: Radix `<DropdownMenu>` dropped entirely; `useDismiss` hook ported verbatim from mockup `topbar-overlays.jsx:9-27`; avatar trigger 36→26 split via `.avatar` CSS class; dropdown now flush against topbar bottom edge (`top:50; right:12` verbatim positioning honoured).
- **AD-MockupFidelity-Guard-TokenRelative-Oklch** — `frontend/scripts/check-mockup-fidelity.mjs` grep counts token-relative `oklch(from var(--token) …)` literals as "hardcoded"; refine the grep to exclude them so faithful verbatim re-points don't grow `HEX_OKLCH_BASELINE` (raised 18→21 in 57.29; 21→25 in 57.30).
- ~~**AD-Overview-PreExisting-Route-Crashes** — `/subagents`, `/memory`, `/verification` render an error boundary (`Cannot read properties of undefined (reading 'length')`) — pre-existing (Day-0 baseline == after sweep on both 57.29 and 57.30); NOT a regression. Separate FIX sprint candidate (Sprint 57.31+ "frontend-page-bug-fix" class at ~0.45 mid-band).~~ **✅ RESOLVED Sprint 57.33** — see Sprint 57.33 Carryover section above.
- **Next Phase-2 per-page re-point** — Sprint 57.30 picked `/chat-v2`. Remaining 12 🟡 AppShellV2 routes: orchestrator / loop-debug / memory / state-inspector / governance / verification / cost-dashboard / sla-dashboard / admin-tenants / tenant-settings / compaction (+ subagents / memory / verification but those need crash fix first).

---

## 🔴 Top Candidates (User-Aligned Priority)

### 1. AD-ChatV2-Full-Mockup-Fidelity Phase-2

Multi-sprint epic continuation. Sprint 57.21 Phase-1 already shipped:
- Turn Block Model
- SessionList fixture
- Inspector 4-tab frame
- Composer visual scaffolding

**Phase-2 carryover ADs** (from Sprint 57.21 retro):
- AD-ChatV2-Memory-Block-Phase2
- AD-ChatV2-HITL-FourAction-Phase2
- AD-ChatV2-Composer-Richness-Phase2
- AD-ChatV2-Composer-Wire-Phase2
- AD-ChatV2-Inspector-{Trace, Memory, SubagentTree}-Phase2
- AD-ChatV2-SessionList-Backend
- AD-Cat12-SSE-Trace-Id-Phase2

**Mode**: Pick subset for Phase-2 first sprint depending on backend dependency ordering. Likely structural-rewrite mode → `frontend-mockup-direct-port` ratio ~1.0-1.2 predicted.

### 2. 🆕 AD-Mockup-Direct-Port-Round-2

NEW Sprint 57.20 Day 4 DRIFT-REPORT-ROUND-2 (16 R2 findings).

**Scope** — Token migration sweep for **8 remaining ship pages**:
- cost-dashboard / memory / verification / governance + 4 governance sub-routes / sla-dashboard / admin-tenants / tenant-settings

Plus:
- 3 overlay backend wiring
- R2-A 5 cosmetic Card visual polish

**Class**: Same `frontend-mockup-direct-port` 0.55 class likely.

### 3. AD-Mockup-Existing-Pages-Retrofit Tier 1

Sprint 57.19 US-F1 DRIFT-REPORT; partially closed Sprint 57.20 via `/overview` + `/chat-v2` token migration; **folds INTO Round-2 above**.

**Scope**: 9-page retrofit Tier 1 ~10.5 hr bottom-up = ~5.8 hr calibrated commit at NEW class `mockup-fidelity-retrofit` 0.55 1st app (HYBRID: cosmetic mechanical 0.45 + structural design 0.65 + closeout 0.80).

**5 priority pages**:
- cost-dashboard (3 hr)
- chat-v2 (3 hr)
- memory (2 hr)
- verification (2 hr)
- governance (1.5 hr)

**Tier 2**: ~5.5 hr → Sprint 57.21+
**Tier 3**: ~1 hr + Round 3 epic

---

## 🟡 Mockup-Page-Port Continuation

### 4. AD-Mockup-Page-X-Port Round 3 — Auth 4

Sprint 57.19 carryover. Pages:
- register / invite / mfa / expired

**Pairing**: IAM Block B (WorkOS SCIM/SAML/org-level RBAC) per 用戶 2026-05-16 Q3 alignment「前後端同 sprint」.

### 5. AD-Mockup-Page-X-Port Round 4 — Governance 3

Sprint 57.19 carryover. Pages:
- redaction / error-policy / audit-log (DRAFT → active promote)

**Pairing**: Cat 9 endpoint extensions.

---

## 🟢 Backend Wire Bundle

### 6. AD-Backend-Wire Bundle

Sprint 57.19 4 NEW ADs:
- Subagent-RealList-Phase58
- Loop-Session-Enrich-Phase58
- Overview-Backend-Wire
- Orchestrator-Backend-Wire

**Scope**: Backend persistence + aggregation for Operations 4 pages (current fixture/stub). Can pair with retrofit work.

### 7. 🆕 AD-CommandPalette-Backend-Wire

NEW Sprint 57.19 US-D1. Tenants + sessions groups currently fixture; wire Cat 1 sessions list + Cat 12 tenants index.

### 8. 🆕 AD-NotificationsPanel-Backend-Feed

NEW Sprint 57.19 US-D2. 6 mockup items local state; Cat 12 SSE/poll feed spec TBD.

### 9. 🆕 AD-UserMenu-Tenant-Switch

NEW Sprint 57.19 US-D3. Wire tenant switching paired with Round 2 WorkOS SCIM.

---

## 🛠️ Tooling / Infrastructure / Style

### 10. AD-Tailwind-v4-Config-Migration

Sprint 57.17 carryover. Full v4 idiomatic `@theme inline {}` block 取代 `@config "../tailwind.config.ts"` + 刪 legacy v3 config file. ~6-8 hr standalone sprint, same class `frontend-css-engine-hotfix`.

### 11. AD-Post-Hotfix-Token-Audit

NEW Sprint 57.17 contrast-ratio portion. **Folds INTO** AD-Mockup-Existing-Pages-Retrofit Tier 1 work (same shadcn slate base sub-AA pairs).

### 12. 🆕 AD-Brand-Primary-Color-Decision

Sprint 57.18 D-PRE-1. Partially actioned by Sprint 57.19 US-A1 mockup indigo; finalization decision pending.

### 13. 🆕 AD-Theme-Variant-Mechanism

Sprint 57.18 D-PRE-2.

### 14. 🆕 AD-Density-Variant-Mechanism

Sprint 57.18 D-PRE-3.

### 15. AD-CI-7-GHA-PR-Permission

Sprint 57.17 carryover. `playwright-e2e.yml:163-188` auto-PR-create blocked by repo setting.

### 16. AD-Lighthouse-Visual-Hard-Gate

Baselines reliable post-57.17; required CI check.

### 17. AD-Bundle-Size code-split

### 18. AD-i18n-Feature-Namespaces

### 19. AD-A11y-Structural-Nits

Sprint 57.16 carryover. `/chat-v2` 的 `heading-order` + duplicate `<main>` landmarks moderate/minor；`/auth/callback?error` `page-has-heading-one`.

---

## 🏢 Enterprise / SaaS Stage 2

### 20. IAM Block B Spike

~12-18 hr — WorkOS SCIM/SAML/org-level. Pairs with #4 Auth 4.

### 21. Tier 1 IaC + DR Drill

~15-20 hr.

### 22. SOC 2 + SBOM

~12-15 hr.

---

## 🟣 Sprint 57.23 Auth Page Rebuild Carryovers (NEW 2026-05-18)

7 ADs from Sprint 57.23 AD-Auth-Page-Full-Rebuild-Round-2 closeout. Frontend rebuild shipped 8/8 USs with stub-501 demo banners; backend wiring deferred to Phase 58+ IAM Block B/C per Q2 frontend-only decision.

### 23. AD-Auth-Register-Backend-IAM-Block-B-Phase58
`POST /api/v1/tenants/register` real implementation. Currently 501 stub. Frontend `/auth/register` 4-step wizard fully shipped + i18n + Vitest 5 cases. Phase 58+ IAM Block B scope.

### 24. AD-Auth-Invite-Backend-IAM-Block-B-Phase58
`GET /api/v1/invites/:token` (metadata) + `POST /api/v1/invites/:token/accept`. Currently 501 stubs; frontend falls back to fixture metadata silently for GET, surfaces explicit error for POST. Frontend `/auth/invite/:token` shipped + Vitest 4 cases. Phase 58+ IAM Block B scope.

### 25. AD-Auth-MFA-Backend-IAM-Block-C-Phase58
`POST /api/v1/mfa/verify` + TOTP secret enrollment + WebAuthn credential registration backend. Currently 501 stub. Frontend `/auth/mfa` Roll-own UI shipped (TOTP 6-digit grid + WebAuthn conic ring + Simulate button) + Vitest 7 cases. Phase 58+ IAM Block C scope.

### 26. AD-Auth-MFA-Recovery-Page-Phase58
`/auth/mfa/recovery` page wire — currently displayed as `<span pointer-events-none>` with tooltip "Recovery flow pending Phase 58+ IAM Block C". Backend recovery-code generation + verification. Phase 58+ IAM Block C scope.

### 27. AD-Auth-Callback-Loading-UX-Phase58
Replace static 3-step `setTimeout` (800/1800/2800ms) with real backend SSE per-step events when WorkOS OIDC callback wiring exists. Frontend already has 3-step UI + parallel-bootstrap + min-2800ms-enforce mechanism. Phase 58+ IAM Block B scope.

### 28. AD-WorkOS-Multi-IdP-Phase58
Wire actual SAML / Microsoft / Google SSO via WorkOS. Currently 3 buttons disabled with "Enterprise SSO via WorkOS roadmap" tooltip per mockup. Backend WorkOS Multi-IdP integration. Phase 58+ IAM Block B scope. (Existed pre-57.23 as design intent; now actively blocks Sprint 57.23 login button enablement.)

### 29. AD-Sprint-57-23-Playwright-MCP-Visual-Verify-Followup
Re-run Playwright MCP visual pair-verify on Sprint 57.23 12 page-states. Day 4 closeout encountered stuck browser state from prior Sprint 57.22 session (`Error: Browser is already in use ... use --isolated`). Closure via code-level audit + Sprint 57.22 baseline + visual-regression CI mechanism. Re-run in future session with fresh browser instance. **Low priority** — line-by-line port discipline + DRIFT-REPORT verdicts (all PARITY or COSMETIC; 0 STRUCTURAL/FUNCTIONAL) already cover fidelity gate.

### 30. AD-I18n-Symmetric-Keys-Lint-Phase58
Implement automated symmetric-keys lint at `frontend/tests/unit/i18n/` that runs `jq paths(scalars)` diff between en/<namespace>.json and zh-TW/<namespace>.json on every PR. Sprint 57.23 verified manually for `auth.json`; this AD generalizes for `chat-v2.json` / `governance.json` / `tenant-settings.json` etc. ~2-3 hr.

---

## 🔵 Sprint 57.24 Decision Carryovers (NEW 2026-05-19)

### 31. AD-Memory-Structural-Rebuild-Phase58
`/memory` page rebuild — Sprint 57.22 Unit 10 audit identified STRUCTURAL severity drift: production has simple 2-tab UI (Recent / By Scope) + 3 backend-wired scopes (system/tenant/user); mockup `page-governance.jsx:462-598` has full 5-scope × 3-time-scale matrix grid + time-travel scrubber + memory-ops timeline + per-memory CRUD.

**Scope**: Frontend rebuild ~12-15 hr + backend Cat 3 NEW SSE event `memory_op_emitted` ~3-4 hr + Cat 12 audit log ~2 hr + role/session backend scopes (currently Phase 58+ stubs) ~6-8 hr. **Total ~25-30 hr**.

**Class candidate**: NEW `frontend-mockup-structural-rebuild` (parallel to Sprint 57.23 NEW `frontend-mockup-strict-rebuild` 0.60 1st app; or HYBRID with backend wire).

**Defer rationale (Sprint 57.24 Q2 decision 2026-05-19)**: STRUCTURAL retrofit exceeds Sprint 57.24 `mockup-fidelity-retrofit` 0.55 scope (which is cosmetic-only by class definition). Memory structural rebuild needs dedicated sprint with backend pairing per Sprint 57.22 §Sprint 57.23+ Recommendation Tier 2 priority.

**Phase**: 58+ (after Auth Block B/C IAM backend lands; role/session memory scopes are part of IAM).

---

## 🟢 Sprint 57.24 v2 Cost Dashboard Rebuild Carryovers (NEW 2026-05-19)

7 ADs from Sprint 57.24 v2 AD-Cost-Dashboard-Full-Mockup-Fidelity-Rebuild closeout. Frontend rebuild shipped 6 widget groups + 7 reusable primitives (PageHead/Spark/StatCard/AreaChart/BarTrack/CardShell/BackendGapBanner) for Sprint 57.25-57.28 epic; 3 of 6 widgets ship fixture + visible BackendGapBanner per AP-2 honesty (backend wiring deferred).

### 32. ✅ CLOSED — AD-Mockup-Fidelity-Rebuild-Sla-Dashboard (shipped Sprint 57.25 2026-05-19)
~~Rebuild `/sla-dashboard` per mockup `reference/design-mockups/page-admin.jsx:31-199` (SlaPage).~~ **Shipped Sprint 57.25**: 6 widget groups (page-head + TimeRangeTabs / 4-stat sparkline / 24h LatencyChart 3-series / 5-row SLO status / Top slow ops table / Error rate by service); reused 7 Sprint 57.24 v2 primitives without API change validating Karpathy §2 ROI; 1 NEW feature-scoped LatencyChart inline; SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER (see #41). See `memory/project_phase57_25_sla_dashboard_rebuild.md` for detail.

### 33. AD-Mockup-Fidelity-Rebuild-Admin-Tenants-Phase58
Rebuild `/admin/tenants` list per mockup `page-admin.jsx:322-410` (AdminTenants section). Existing filters/table/pagination preserved; mockup-fidelity polish + admin context widgets added (avatar rendering / row-level actions / status badges per mockup). Sprint 57.27 candidate (foundation-fidelity Sprint 57.26 was inserted ahead as a user-directed sprint, shifting this +1).

### 34. AD-Mockup-Fidelity-Rebuild-Verification-Phase58
Rebuild `/verification` per mockup `page-extras.jsx:817-927` (VerificationPage). 2-tab structure (Recent / Correction Trace) preserved; inner widget mockup-fidelity port pending. Sprint 57.28 candidate.

### 35. AD-Mockup-Fidelity-Rebuild-Tenant-Settings-Phase58
Rebuild `/admin/tenants/settings` per mockup `page-admin.jsx:411+` (TenantSettings 6-tab) + lift `/feature-flags` out per Sprint 57.22 Unit 31 architectural finding + page-extras.jsx:928 comment "/feature-flags (lifted out of /tenant-settings)". Architectural-level refactor + new standalone `/feature-flags` route. Sprint 57.29 candidate.

### 36. AD-Cost-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.24 v2 fixture-driven widgets:
- Cross-tenant aggregation endpoint (`GET /api/v1/admin/cost-summary/by-tenant` returning top-N tenant rows; platform-admin-scoped) — drives TenantTopTable
- Cross-provider aggregation endpoint (`GET /api/v1/admin/cost-summary/by-provider`; platform-admin-scoped) — drives ProviderMixCard with LLM-neutrality redacted labels
- 30-day daily history endpoint (`GET /api/v1/admin/cost-summary/history?days=30`) — drives AreaChart
- Harmonize category taxonomy: mockup 6 flat categories (Inference input/output / Thinking tokens / Tool runs / Embeddings / Sandbox compute) ≠ current backend `by_type` 2-level dict shape (cost_type → sub_type → AggregatedSlice); decision: either backend reshape OR define explicit aggregation mapping in spec

Drives Sprint 57.24 BackendGapBanner removal for 3 of 6 widgets + flips fixture data to real. ~8-12 hr backend + ~2-3 hr frontend wire-up. Phase 58+ backend-led; could pair with Sprint 57.25 sla-dashboard rebuild if scope permits.

### 37. AD-Playwright-MCP-Recovery-Phase58
**3-consecutive-sprint blocker** (Sprint 57.22 + 57.23 + 57.24 v2): Playwright MCP browser-stuck on every visual pair-verify attempt. `browser_close` returns "Browser is already in use for ...mcp-chrome-... use --isolated to run multiple instances of the same browser". Root cause: Claude Code session-process management — prior session's chrome instance not released to next session.

**Mitigation today**: code-level audit + Vitest spec coverage + Playwright CLI (separate from MCP) cover verification; visual baselines regen via CI workflow_dispatch + cherry-pick (Sprint 57.14 + 57.23 PR #156 + 57.24 v2 PR pattern).

**Phase 58+ resolution paths**:
- Option A: pass `--isolated` flag to MCP browser per session
- Option B: explicit cleanup hook on Claude Code session end (`process.kill` on chrome PID)
- Option C: contribute fix upstream to Anthropic Playwright MCP plugin

Cost: ~2-4 hr investigation + fix. Phase 58+; meanwhile workaround acceptable.

### 38. AD-Sprint-Plan-Audit-Cross-Ref-Prong5
**Plan-draft discipline addition** (Sprint 57.24 v1 abort lesson):

Sprint 57.24 v1 plan misclassified 3 of 5 retrofit targets (cost / sla / tenant-settings) as "cosmetic-feasible Tier 1" when Sprint 57.22 AUDIT-REPORT had already marked them P0 full-rebuild. Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 3 schema + Prong 4 test selector) didn't catch this because they verify code-vs-plan drift, NOT plan-vs-audit-classification mismatch.

**Proposed Prong 5: Audit Cross-Reference**:
Before drafting Tier-N retrofit/rebuild plan, grep AUDIT-REPORT(s) for each target's prior classification:
```bash
# Example for Sprint 57.24 v1
for target in cost-dashboard sla-dashboard verification admin/tenants tenant-settings; do
  grep -l "Unit.*$target" claudedocs/4-changes/sprint-57-*-audit/AUDIT-REPORT*.md
done
```
If any target is already audit-classified as P0 / structural-rebuild → lift conflicting entries into structural-rebuild scope before drafting cosmetic-retrofit batch.

**Scope**: Add to `.claude/rules/sprint-workflow.md` §Step 2.5 as new Prong 5; ~30 min doc edit. Phase 58+ when next Tier-N retrofit/rebuild batch is drafted.

---

## 🟢 Sprint 57.25 SLA Dashboard Rebuild Carryovers (NEW 2026-05-19)

3 ADs from Sprint 57.25 AD-Mockup-Fidelity-Rebuild-Sla-Dashboard closeout. Frontend rebuild shipped 6 widget groups reusing 7 Sprint 57.24 v2 primitives without API change + 1 NEW feature-scoped LatencyChart (Karpathy §2 inline); SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER pending 4th data point.

### 39. AD-SLA-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.25 fixture-driven widgets:
- 24h time-series aggregation endpoint (`GET /api/v1/sla/latency-history?range=24h`) returning per-time-bucket {p50, p95, p99} — drives LatencyChart 24h
- Cross-operation p99 aggregation endpoint (`GET /api/v1/sla/slow-operations?range=24h&limit=N`) — drives TopSlowOpsTable
- Per-service error rate aggregation endpoint (`GET /api/v1/sla/error-rates?range=1h`) — drives ErrorRateByServiceCard
- Dedicated SLO threshold metrics (`tool_success_pct` / `hitl_response_p95_min` / `subagent_depth_max` / `cost_per_run_usd`) — drives SLOStatusCard 4 of 5 fixture rows
- Existing `useSLAReport` SLAReportResponse extension: `latency_p50_ms` + `latency_p95_ms` + `error_budget_pct` fields (currently fixture per D-PRE-2)

Drives Sprint 57.25 BackendGapBanner removal for 3 widgets (LatencyChart 24h / cross-op p99 / per-service error rate) + flips 3 stat cards (p50/p95/error_budget) + 4 of 5 SLO rows from fixture to real. ~10-14 hr backend + ~3-4 hr frontend wire-up. Phase 58+ backend-led; pairs with Sprint 57.26-57.28 backend extensions for cost-dashboard #36.

### 40. AD-LatencyChart-Extraction-Phase58
Extract `LatencyChart` from `frontend/src/features/sla-dashboard/components/` to `frontend/src/components/charts/` as generalizable 3-series multi-line primitive **IF 2nd consumer arises** per Karpathy §2 "extract on 2nd consumer" rule.

Current state (Sprint 57.25): inline feature-scoped (~110 lines); single consumer = SLA dashboard 24h LatencyChart. Sprint 57.26+ may have 2nd consumer if `/admin/tenants` rebuild needs similar multi-series visualization OR Sprint 57.27 `/verification` correction-trace shows latency distribution.

**Extraction trigger criteria**:
- 2 distinct production consumers with comparable 3-series multi-line shape (NOT just any chart need)
- API generalizable beyond hardcoded p50/p95/p99 series → e.g. `<MultiLineChart series={[{key, stroke, width, opacity}]} data />`
- Estimate: ~2 hr extraction + Vitest update

If 4th data point sprint (57.26+) doesn't surface 2nd consumer → DROP this AD entirely (Karpathy §2 rule applied correctly).

### 41. AD-Sprint-Plan-rich-dashboard-sub-class-DEFER — ✅ RESOLVED (Sprint 57.27 — DROPPED)
Sub-classification proposal logged Sprint 57.24 v2 retro Q4 (rich-dashboard ratio 1.19 vs auth-flow 0.59) deferred per Sprint 57.25 3rd data point ratio 0.88. 2-data-point rich-dashboard mean (57.24 v2 + 57.25) = ~1.04 sits in-band middle of [0.85, 1.20] — does NOT justify split.

**Resolution path** (original):
- Sprint 57.27 = 4th data point (admin-tenants list rebuild; rich-dashboard shape — foundation-fidelity Sprint 57.26 was inserted ahead, shifting it +1)
- If 57.27 ratio in band → **DROP** sub-class proposal (3-of-3 rich in band; KEEP 0.60 baseline)
- If 57.27 ratio > 1.20 → reconsider rich sub-class higher (~0.70-0.75); 2-of-3 rich above band
- If 57.27 ratio < 0.85 → drop rich-dashboard pattern entirely; KEEP 0.60 baseline accepts auth-flow + rich mixed

**✅ RESOLVED 2026-05-21 (Sprint 57.27 closeout — DROPPED)**: Sprint 57.27 became the `/overview` full rebuild (user-directed; superseded the planned admin-tenants 57.27 candidate, but `/overview` is itself a rich operator dashboard — 2 charts + 4-stat KPI + 4 cards — so it serves as the 4th rich data point). 57.27 ratio ≈0.95 — **IN BAND**. Rich-subset 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 → 3-pt mean ~1.01 in-band middle → **sub-class proposal DROPPED, no split**; KEEP the single `frontend-mockup-strict-rebuild` 0.60 baseline for the whole class. Matrix row + MHist updated in `.claude/rules/sprint-workflow.md`.

---

## 🟡 Sprint 57.26 Foundation-Fidelity Carryover (NEW 2026-05-21)

1 AD from Sprint 57.26 post-closeout CI investigation. PR #159's first `Frontend E2E` run failed — `visual-regression.spec.ts` 5 `toHaveScreenshot()` baselines (auth-login / cost-dashboard / governance / verification-recent / admin-tenants) mismatched because the foundation-token correction deliberately moved the visuals. Resolved by regenerating baselines via the Sprint 57.14 `playwright-e2e.yml` workflow_dispatch mechanism (baseline commit `f0b24bd2`); CI then green, `state: CLEAN`. The gap is a planning-discipline miss, not a code defect.

### 42. AD-Day0-Prong4-Visual-Baseline-Scope
Sprint 57.26 plan §Risks listed the "22-route blast radius" of changing `html` font-size but scoped it only to the sprint's own route-sweep harness — it missed CI's pre-existing Playwright `visual-regression.spec.ts` screenshot baselines. Day 0 三-prong Prong 4 (test selector verify) checks only **Vitest** specs asserting literal foundation values; it does not cover `tests/e2e/visual/*-snapshots/` PNG baselines, which are a second class of "asserts the visuals" test. Visual-baseline regen is a known pattern (Sprint 57.14 mechanism, used in 57.23 + 57.24) but was not pre-adopted into the 57.26 plan.

**Fix proposal**: extend `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 4 — when a sprint plan touches global CSS / foundation tokens / shell layout / any broad visual change, Day 0 must (a) `Glob tests/e2e/visual/**/*-snapshots/*.png` to confirm baselines exist + assess visual blast radius, and (b) if visuals will move, plan §Risks must pre-list "visual baseline regen via `playwright-e2e.yml` workflow_dispatch" as a known closeout step rather than a post-CI surprise.

**Cross-ref**: AD GHA-PR-create-blocked (line 131 — `playwright-e2e.yml` `gh pr create` step failed for the 3rd time across 57.23 / 57.24 / 57.26; the bot pushes the baseline branch fine but cannot open the PR, so the manual `fetch + ff-merge` is the working path). Effort: ~15 min rule edit; no code change.

---

## 🟢 Sprint 57.27 Overview Rebuild Carryover (NEW 2026-05-21)

2 ADs from Sprint 57.27 `AD-Mockup-Fidelity-Rebuild-Overview` closeout. `/overview` operator dashboard rebuilt 1:1 from `reference/design-mockups/page-overview.jsx` — 9 widgets, OverviewPage 728→~215-line assembly (AP-3 reversal complete), DRIFT-REPORT verdict PARITY. 8 of 9 widgets are fixture-backed (declared via `<BackendGapBanner>`); ActiveLoopsCard targets real data but its endpoint 404s.

### 43. AD-Overview-Backend-Extensions-Phase58
The 9 `/overview` widgets need real backend data. Currently 8 are fixture-backed (HITL Queue / Providers / Incidents / Error Trend / Cost Burn + the 4-stat KPI row), declared honestly via `<BackendGapBanner>`. ActiveLoopsCard targets real data via `useActiveLoops` → `fetchLoops` → `GET /api/v1/loops?status=running` — but that endpoint returns **404 (does not exist)**, so the widget always renders its error state in production (pre-existing; the hook + `loopsService` predate Sprint 57.27). Phase 58 scope: (a) build the `GET /api/v1/loops` list endpoint — closes ActiveLoopsCard live data + folds in D15 (`maxTurns` hardcoded; `Session` ORM enrich = existing `AD-Loop-Session-Enrich-Phase58`); (b) aggregation endpoints for HITL-queue / providers-health / incidents / error-trend / cost-burn / KPI stats. Pairs with cost-dashboard #36 + sla-dashboard #39 backend-extension ADs (same Phase 58+ backend-led batch).

### 44. AD-CardShell-Title-Crossverify-cost-sla
Sprint 57.27 R9 (user decision) changed the shared `CardShell` card-title `text-sm` → `text-[12.5px]` (closes D8 toward mockup `.card-title` 12.5px). `/cost-dashboard` (57.24) + `/sla-dashboard` (57.25) also consume `CardShell` → both shifted toward the mockup (they carried the same D8 drift unnoticed). Pure mockup-fidelity correction, NOT a regression — but a light Playwright pair-verify pass on those 2 pages should confirm the 12.5px title renders right. Fold into the next dashboard-touching sprint, or a small shared-primitive token-audit pass. ~15 min.

---

## 🟢 Sprint 57.28 Foundation-Switch Carryover (NEW 2026-05-22)

Sprint 57.28 `AD-Mockup-Fidelity-Foundation-Switch` switched the production frontend CSS delivery to the verbatim-CSS 4-layer sync protocol (Phase 1 — foundation only; Option B). The 22-route sweep verified 0 catastrophic / 0 structural regression. The Phase-2 per-page re-point epic (the `frontend-mockup-strict-rebuild` candidates #2 / #33-35 etc.) now re-points page markup on a **correct foundation** — CSS colour fidelity comes "for free" per re-point.

### 45. AD-RouteSweep-Object-Mock-Gap

NEW Sprint 57.28 D-DAY3-2. The `route-sweep.mjs` harness's generic `[]` API mock crashes the object-shaped data hooks of `/subagents`, `/memory`, `/verification` (AppErrorBoundary `undefined.length` — identically in before/ + after/ sweeps, so NOT a foundation-switch regression). Extend `route-sweep.mjs` with object-shaped mocks for `/api/v1/subagents` + `/api/v1/memory/recent` + the verification endpoint (mirroring the Sprint 57.26 D-DAY1-1 `cost-summary` / `sla-report` object mocks) so those 3 routes become sweep-assessable. Harness maintenance ~1 hr; fold into a Phase-2 re-point sprint touching those pages.

### 46. AD-Mockup-Fidelity-HexBaseline-Migration

NEW Sprint 57.28. `check-mockup-fidelity.mjs` grep guard baselines `HEX_OKLCH_BASELINE = 18` — 18 hardcoded `bg-[#hex]`/`text-[#hex]` lines in the governance + chat_v2 risk-colour maps (DecisionModal / AuditChainBadge / ApprovalList / ApprovalCard / HITLTurn). Each Phase-2 re-point of those pages should migrate the literals to mockup `--risk-*` tokens and lower `HEX_OKLCH_BASELINE` accordingly. Not a standalone sprint — folds into the governance + chat-v2 re-point work.

---

## Maintenance Notes

- New carryover ADs from each sprint retrospective should be **appended here**, NOT to CLAUDE.md table cells (per §Sprint Closeout policy).
- When a candidate becomes the selected next sprint, leave the entry marked `→ Sprint XX.Y` until that sprint closes; then move to "Closed" section or delete.
- Cross-references: see `memory/MEMORY.md` index + per-sprint memory subfile + retrospective.md for sprint-by-sprint detail.

---

## Modification History

- 2026-05-22: Sprint 57.28 Day 4 closeout — verbatim-CSS foundation switch SHIPPED (22-route sweep 0 catastrophic / 0 structural regression); +2 ADs (#45 `AD-RouteSweep-Object-Mock-Gap` + #46 `AD-Mockup-Fidelity-HexBaseline-Migration`); the Phase-2 per-page re-point epic now runs on a correct verbatim foundation
- 2026-05-21: Sprint 57.27 Day 3 closeout — `/overview` rebuild SHIPPED (DRIFT verdict PARITY); +2 ADs (#43 `AD-Overview-Backend-Extensions-Phase58` + #44 `AD-CardShell-Title-Crossverify-cost-sla`); RESOLVED #41 (rich-dashboard sub-class DROPPED — 57.27 `/overview` 4th `frontend-mockup-strict-rebuild` data point ratio ≈0.95 in-band; rich-subset 3-pt mean ~1.01 → no split, KEEP single 0.60 baseline)
- 2026-05-21: Sprint 57.26 post-closeout CI fix — +1 AD #42 (`AD-Day0-Prong4-Visual-Baseline-Scope`); PR #159's first CI run failed on 5 stale `visual-regression.spec.ts` baselines (foundation-token correction deliberately moved the visuals); baselines regenerated via `playwright-e2e.yml` workflow_dispatch (`f0b24bd2`), CI re-run green / `state: CLEAN`
- 2026-05-21: Sprint 57.26 Day 3 closeout — foundation-fidelity sprint (global token correction across 22 routes; user-directed insertion, NOT drawn from this candidate list) shipped with 0 regression; 0 new carryover ADs at closeout (later +1 AD #42 post-closeout CI fix — see entry above); 3 FOUNDATION-APPLIED routes folded into the existing rebuild epic per DRIFT-REPORT §5; #33/#34/#35 candidate sprint numbers shifted +1 (→ 57.27/57.28/57.29) + #41 4th-data-point sprint → 57.27 (foundation-fidelity took the 57.26 slot)
- 2026-05-19: Sprint 57.25 Day 3 closeout — close #32 (sla-dashboard rebuild SHIPPED) + +3 ADs (#39-#41) SLA Dashboard Rebuild carryovers (backend extensions + LatencyChart extraction trigger + rich-dashboard sub-class DEFER decision)
- 2026-05-19: Sprint 57.24 v2 Day 3 closeout — +7 ADs (#32-#38) Cost Dashboard Rebuild carryovers (4 page rebuilds 57.25-57.28 + 1 backend extension + 1 Playwright MCP recovery + 1 plan-draft Prong 5 discipline addition)
- 2026-05-19: Sprint 57.24 Day 0 — +1 AD #31 Memory STRUCTURAL Rebuild carryover (Q2 decision: defer from 57.24 cosmetic retrofit to dedicated Phase 58+ sprint)
- 2026-05-18: Sprint 57.23 Day 4 closeout — +8 ADs (#23-#30) Auth Page Rebuild Round 2 carryovers (Phase 58+ IAM Block B/C + Playwright MCP followup + i18n lint)
- 2026-05-18: Initial creation (REFACTOR-001 Step 3; extracted from CLAUDE.md V2 Refactor Status table 20-bullet `Next Phase 候選` row per §Sprint Closeout policy)
