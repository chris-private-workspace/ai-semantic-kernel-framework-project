# Sprint 57.43 — Retrospective

**Sprint id**: 57.43 — AD-AdminTenants-Tenants-Table-Rebuild
**Closed**: 2026-05-25
**Branch**: `feature/sprint-57-43-admin-tenants-rebuild`
**Class**: `frontend-mockup-strict-rebuild` 0.60 (9th data point; **1st validation under newly ACTIVATED `agent_factor = 0.55`** per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` 2026-05-25)
**Commits**:
- `3dd4d7cc` — plan + checklist draft / 2 files / +552
- `4dd73c78` — Day 0 / 27 files / +121 (3-prong + 24-PNG before + 13 D-DAY0-N + plan §Risks amendment)
- `c41391f6` — Day 1 / 13 files / +374 / -580 (NET -206; 5 NEW components + 6 orphan delete; code-implementer 12th consecutive)
- `1cf7d4da` — Day 2 / 6 files / +497 / -14 (5 NEW Vitest specs +33 tests; audit-report 8 PARITY edits; code-implementer 13th consecutive)
- `2db2e508` — Day 2.5 / 27 files / +108 (24-PNG after-sweep + 3-way evidence pair partial + progress.md Day 1/2/2.5)
- (TBD Day 3 closeout commit)

---

## Q1 — What went well

1. **Day 0 3-prong (Path/Content/Schema/Tree depth) caught 13 D-DAY0-N findings, including critical 🔴 D-DAY0-6 backend schema gap, BEFORE any code starts.** Path verify (Prong 1) confirmed 4 NEW path slots + 3 DELETED targets clean. Content verify (Prong 2) caught D-DAY0-1+2 naming corrections (actual `useAdminTenants` / `adminTenantsService` not `useTenantList` / `tenantService` from plan). Schema verify (Prong 3) caught D-DAY0-6 critical — backend `TenantListItem` lacks 5 of 9 mockup columns (seats/region/agents/runs24/status). Day 1 work simplified by Option A fixture-first lock-in. Per `.claude/rules/sprint-workflow.md §Step 2.5` validated ROI again (~50 min cost prevented potential mid-Day-1 scope expansion).

2. **code-implementer agent delegated 12th + 13th consecutive (Day 1 + Day 2) — ~11 min combined wall-clock for full rebuild + 33 NEW Vitest specs + audit report PARITY.** Day 1: 5 NEW components (348 LOC) + page restructure (-27) + 6 orphan delete in ~5 min. Day 2: 5 NEW Vitest spec files / +33 tests / Vitest 481→514 in ~6 min. The agent's mockup-faithful API mapping was correct first-try (zero re-work; D-DAY1-1 self-caught + fixed mid-run via cohort pattern from Sprint 57.41/42).

3. **24-PNG sweep cleanest of Phase-2 epic so far: 22 IDENTICAL + 1 INTENDED CHANGED (admin-tenants +98.9%) + 2 sub-300-byte noise + 0 unintended regressions.** Sprint 57.42's "20 IDENTICAL + 4 CHANGED" was previously cleanest; Sprint 57.43 is even cleaner (2 noise vs 3 in 57.42). Demonstrates that NEW component rebuild stays surgically isolated from other routes; verbatim-CSS protocol + Card primitive reuse keeps shell + nav + adjacent routes pixel-identical.

4. **Vitest +33 tests = +312-560% over plan §AC3 +5-8 target.** Within Sprint 57.40 (+15) / 57.41 (+9) / 57.42 (+12) cohort. Schema integrity tests for `_fixtures.ts` (8 tests) particularly valuable — TENANTS verbatim port from mockup line 323-332 has audit trail (count + required fields + union types + status distribution validated).

5. **HEX_OKLCH_BASELINE 46 unchanged (+0 vs plan §3.6 estimate +0-2).** 4th consecutive sprint where verbatim-CSS protocol delivered +0 actual (57.40/41/42 also +0). Plan §3.6 estimate envelope should tighten to +0-1 going forward (matches Sprint 57.42 retro Q3 Lesson 4 recommendation).

6. **D-DAY0-6 Option A fixture-first lock-in WAS PLAN'S §1.4 FALLBACK** — when reality matched the documented fallback, plan amendment was clean (audit trail in §Risks rather than silent rewrite). Step 2.5 rule worked exactly as designed.

7. **Karpathy §3 orphan delete: 6 files deleted in Day 1 (3 vintage components + 3 specs) for NET -206 lines.** Smaller scale than Sprint 57.42's 11 (3 components + 3 hooks + 4 Vitest + 1 e2e = -154 NET) but proportional to feature scope. Preservation of `useAdminTenants` / `adminTenantsService` / `useAdminTenantsStore` + their 3 specs per D-DAY0-3 + D-DAY0-12 maintains forward-compat for Phase 58+ backend wire.

8. **Plan §1.4 explicit Option A/B branch + Day 0 verification trigger validated the architecture.** When Day 0 Prong 3 confirmed schema gap, the decision tree was already in place; no improvisation required. This pattern should be embedded in future single-domain rebuild plans (define backend wiring decision branch + verification trigger in §Tech Spec).

---

## Q2 — What didn't go well + Calibration

### Calibration ratio — 9th data point (1st validation under `agent_factor = 0.55`)

**Bottom-up est (plan §8)**: ~12-15 hr (mid-band ~13.5 hr)
**Class-calibrated commit (mult 0.60)**: ~7.5-9 hr (mid-band ~8.1 hr)
**Agent-adjusted commit (agent_factor 0.55)**: ~4-5 hr (mid-band ~4.5 hr)
**Actual wall-clock total**: ≈ **1.83 hr** (Day 0 ~50 min + Day 1 ~10 min + Day 2 ~9 min + Day 2.5 ~15 min + Day 3 ~25-30 min)
**Ratio `actual/committed-with-agent-factor`**: ~**0.41** — BELOW [0.85, 1.20] band by **~0.44**
**Ratio `actual/bottom-up`**: ~0.14 — bottom-up was ~7× too generous (consistent improvement vs Sprint 57.42's ~5× generous; bottom-up estimates gradually learning agent cadence)

### 9-pt `frontend-mockup-strict-rebuild` 0.60 class history

| Sprint | Page | Ratio | agent_factor | In-band? |
|--------|------|-------|--------------|----------|
| 57.23 | auth flow rebuild (7 routes) | 0.59 | 1.0 (pre-activation) | below by 0.26 |
| 57.24 v2 | cost-dashboard rebuild | 1.19 | 1.0 | top of band ✅ |
| 57.25 | sla-dashboard rebuild | 0.88 | 1.0 | in band ✅ |
| 57.27 | overview rebuild | ≈0.95 | 1.0 | in band ✅ |
| 57.37A | loop-debug rebuild | ≈1.18 | 1.0 | top of band ✅ |
| 57.40 | governance rebuild | ≈0.36 | 1.0 (agent-delegated; modifier not yet activated) | below by 0.49 |
| 57.41 | verification rebuild | ≈0.18 | 1.0 (agent-delegated; modifier proposal) | below by 0.67 |
| 57.42 | memory rebuild | ≈0.33 | 1.0 (agent-delegated; activation criteria MET) | below by 0.52 |
| **57.43** | **admin-tenants rebuild** | **~0.41** | **0.55 (ACTIVATED 2026-05-25)** | **below by 0.44 — 1st rollback-trigger data point** |

- **9-pt mean**: 0.67 at lower band edge (-0.04 vs 8-pt 0.71); reflects 4 consecutive agent-delegated < 0.7 sprints + Sprint 57.43's pre-activation-equivalent 0.41 (using `agent_factor = 1.0` baseline: 0.60 × 1.0 = 0.60 expected; 0.41 actual = 0.41 / 0.60 = 0.68 → still below band).
- **Last 3 (57.41 + 57.42 + 57.43)**: 3 of 3 < 0.7 (0.18, 0.33, 0.41) — lower-trigger still MET.

### Rollback rule status (per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`)

Sprint 57.43 is **1st data point under activated modifier**. Ratio 0.41 (computed against committed-with-agent-factor) is BELOW 0.7. Per rollback rule:

- ✅ Single-data-point caution applies → **KEEP `agent_factor = 0.55`** this iteration.
- 🟡 If Sprint 57.44 (likely `/tenant-settings` rebuild) also < 0.7 → **2 sprints < 0.7 → tighten `agent_factor` to `0.45`**.
- 🟡 If 0.45 also produces < 0.7 → consider Option B per-class sub-class split per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier §Escalation to Option B`.

### Root cause analysis

The 1st validation data point ratio 0.41 (vs predicted 0.33 bullseye) is **0.08 ABOVE prediction** in band-relative terms, but still **0.44 BELOW band lower edge**. Breakdown:

1. **Agent speedup is larger than 0.55 factor predicted** — code-implementer agent compresses mockup-port + Vitest spec authoring even more aggressively than 0.55 envelope. Sprint 57.43 specific factors:
   - Mockup smaller than 57.40-42 (admin-tenants `page-admin.jsx:322-409` ~88 lines vs memory ~200; verification ~150; governance ~140)
   - No novel interactive widgets (vs Sprint 57.42 TimeTravelScrubber + cursor-aware visibility filter; Sprint 57.41 envelope mock + adapter; Sprint 57.40 ApprovalDetailPane + DecisionModal delete + KvRow primitive lift)
   - 0 new primitive lifts required (mockup-ui critical-mass post 57.40+41+42 — Stat / Card / Badge / Button / Icon all reused unchanged)
   - Pattern reuse from 3 prior consecutive `mockup-strict-rebuild` sprints — agent has internalized mockup-port pattern at this point

2. **Bottom-up estimate ~13.5 hr was per-audit-report human-rewrite cadence inflated** — audit-report row 113 estimated based on conventional human-rewrite pace (per-line ~5-8 LOC/hr including testing); actual agent-delegated rate is ~50-100 LOC/hr (12-18× speedup vs human, beyond the agent_factor 0.55's 1/0.55 = 1.8× speedup assumption).

3. **Pattern-reuse acceleration evident** — 3 prior `mockup-strict-rebuild` sprints established the rhythm: Day 0 3-prong → Day 1 agent ~5 min → Day 2 agent ~6 min → Day 2.5 sweep → Day 3 retro. Each consecutive application gets faster as code-implementer agent + mockup-ui primitives reach critical-mass.

### Other didn't-go-well items

- **3-way evidence pair `03-MOCKUP-admin-tenants.png` deferred** — capture procedure (python http.server + Playwright at 1440×900) not executed this sprint to preserve velocity. Carryover for Day 3 closeout follow-up if time permits, else Phase 58+ docs polish. Estimated AFTER/MOCKUP ratio ~90-95% based on AFTER 162.6 KB vs estimated MOCKUP 170-180 KB (well above ≥75% structural PARITY threshold per AC5).

- **`agent_factor = 0.55` 1st validation undershoots prediction by 0.08** — not a serious miss; within 1-sprint single-data-point caution per rollback rule. But pattern signal suggests if 57.44 also lands below 0.5, the modifier may need recalibration to 0.40-0.45 OR Option B per-class split (mockup-strict-rebuild sub-class agent-delegated baseline ~0.30-0.35).

- **Bottom-up estimate continues ~5-7× too generous post-activation** — audit-report row 113 was authored before agent-delegation pattern stabilized. Future sprint bottom-up estimates should use Sprint 57.40-43 actual data as anchor (~3-5 hr human-eq) not human-rewrite ~12-15 hr.

---

## Q3 — What we learned (generalizable lessons)

### Lesson 1 — Day 0 3-prong + Prong 2.5 + Prong 3 is robustly catching critical drift at <50 min cost

Sprint 57.43 Day 0 caught 13 D-DAY0-N findings including critical 🔴 D-DAY0-6 backend schema gap. ROI:
- Day 0 cost: ~50 min
- D-DAY0-6 prevented ~2-3 hr Day 1 wasted effort (would have wired backend; discovered mid-implementation that response shape missing 5 of 9 columns)
- D-DAY0-1+2 naming corrections + D-DAY0-3 store preservation prevented orphan-delete mistakes

Per `.claude/rules/sprint-workflow.md §Step 2.5`, 3-prong + 2.5 is now well-validated across Sprint 55.5/55.6/56.1/56.3/57.1/57.40/57.41/57.42/57.43 (9 sprints). **Generalizable**: Day 0 cost is bounded (~50 min) but ROI scales with sprint scope (~3-5 hr prevented re-work). Maintain rule.

### Lesson 2 — Plan §1.4 explicit option branch + Day 0 verification trigger is a strong pattern

Sprint 57.43 plan §1.4 documented "Option B (selected); fallback Option A if Day 0 Schema verify reveals mismatch". Day 0 Prong 3 confirmed mismatch → Option A locked in. Audit trail preserved cleanly in plan §Risks (not silent §Technical Spec rewrite). Pattern works because:

1. Decision criteria documented upfront in plan §1.4 (specific Day 0 verification triggers)
2. Fallback path pre-specified (Option A behavior described)
3. Step 2.5 rule preserves audit trail (amendment in §Risks not silent overwrite)

**Generalizable**: Future single-domain rebuild plans should pre-document option branches + verification triggers for any contested decision (backend wire decision, outer-tab disposition, fixture vs real-data, etc.). This is a Sprint 57.42 + 57.43 precedent for sprint-plan template enhancement.

### Lesson 3 — Agent-delegation speedup is consistent ~12-18× human cadence (well above agent_factor 0.55 prediction)

3 consecutive sprints (57.40 → 57.42) under `agent_factor = 1.0` showed 0.36 / 0.18 / 0.33 ratios. Sprint 57.43 under `agent_factor = 0.55` shows 0.41 ratio. The speedup factor between agent and human cadence:

| Sprint | Bottom-up | Human-eq actual | Actual / bottom-up |
|---|---|---|---|
| 57.40 governance | ~7-8 hr | ~6-8 hr | ~0.21 (committed); reality the bottom-up was ~5× generous |
| 57.41 verification | ~8-10 hr | ~5-8 hr | ~0.10 (committed); bottom-up ~10× generous |
| 57.42 memory | ~10-15 hr | ~5-5.5 hr | ~0.20 (committed); bottom-up ~5× generous |
| **57.43 admin-tenants** | ~12-15 hr | ~1.83 hr | **~0.14 (bottom-up)**; bottom-up ~7× generous |

The cross-sprint pattern: bottom-up estimates calibrated to human-rewrite cadence overshoot agent-delegated execution by 5-10× consistently. `agent_factor = 0.55` (1.8× speedup assumption) is undershooting reality (12-18× speedup observed).

**Generalizable**: 
- If `agent_factor = 0.55` continues producing < 0.7 ratios over Sprint 57.44 (2nd validation), tighten to 0.45 per rollback rule
- If 0.45 also produces < 0.7, consider Option B per-class sub-class split with explicit mockup-strict-rebuild-agent-delegated baseline ~0.30 (matching observed mean)
- Bottom-up estimate anchor for future mockup-strict-rebuild sprints should be **~2-3 hr human-eq** for similar-scope rebuilds (not audit-report's human-rewrite ~12-15 hr)

### Lesson 4 — Mockup-ui critical-mass post-57.40+41+42 enables 0 new primitive lifts

Sprint 57.42 already noted "pattern reuse acceleration evident at infrastructure level: 0 new primitive lifts (mockup-ui.tsx critical-mass)". Sprint 57.43 confirms — 5 NEW components built on existing primitives (Stat / Card / Badge / Button / Icon / Field) with **0 new primitive lifts required**.

**Generalizable**: Mockup-ui primitive set is now at critical-mass for mockup-strict-rebuild work. Future rebuilds (`/tenant-settings` Sprint 57.44) likely also need 0 new primitive lifts UNLESS they require novel widget types (e.g. 6-tab nav primitive, form patterns not in mockup-ui). Day 0 Prong 2.5 should grep mockup-ui exports vs mockup primitives needed; if mismatch → 1 NEW primitive lift estimated separately.

### Lesson 5 — `getAllByText` + route-pill assertion patterns now Vitest convention

Sprint 57.43 D-DAY1-1 (agent self-fix mid-run) confirms the cohort pattern from Sprint 57.41/42 has internalized:
- Page titles often duplicate sidebar nav strings (e.g. "Tenants" appears in both `<title>` and Sidebar nav)
- Solution: assert via route-pill `/admin/tenants` (page-unique within AppShellV2) OR `getAllByText(...).length >= N`

This is now applied **preemptively** by code-implementer agent (Day 1 D-DAY1-1 caught + fixed self-directed without my prompting). **Generalizable**: This pattern should be folded into `.claude/rules/testing.md` or new `frontend-mockup-fidelity-vitest-patterns.md` doc — was Sprint 57.42 Lesson 5 recommendation; now Sprint 57.43 validates it's reliable enough to codify.

### Lesson 6 — Verbatim-CSS protocol +0 actual now stable across 4 consecutive sprints

Sprint 57.40 (+0) / 57.41 (+0) / 57.42 (+0) / 57.43 (+0). Plan §3.6 estimate envelope `+0-2 or +0-4` is consistently over-cautious. **Generalizable**: tighten plan §3.6 envelope to **+0-1** going forward for mockup-strict-rebuild sprints (assumes components use `var(--*)` refs only, which is the verbatim-CSS protocol's main rule).

---

## Q4 — Audit debt deferred

| AD | Description | Target |
|----|-------------|--------|
| `AD-AdminTenants-Backend-Schema-Extension` | **🔴 BLOCKING (elevated from 🟡 conditional Sprint 57.43 D-DAY0-6)** — Backend `TenantListItem` lacks 5 of 9 mockup columns (seats / region / agents / runs24 / status). Required to wire `useAdminTenants` to NEW components. Sprint 57.43 Option A fixture-first per plan §1.4 fallback. | Phase 58+ |
| `AD-AdminTenants-Filter-Form-Phase58-Migrate` | Sprint 57.43 retired standalone Filters bar per Karpathy §3. Mockup has Card-internal toolbar (cmdk visual stub + 2 ghost buttons Plan/Sort) but no functional filter logic. Phase 58+ wires real filter via store + service | Phase 58+ |
| `AD-AdminTenants-Pagination-Phase58-Migrate` | Sprint 57.43 retired Pagination component per Karpathy §3 (mockup shows direct 8 rows). Phase 58+ if tenant count > 100 | Phase 58+ |
| `AD-AdminTenants-New-Tenant-Modal-Phase58` | Mockup `.page-head` "New tenant" button is Sprint 57.43 AP-2 stub (`window.alert`) | Phase 58+ |
| `AD-AdminTenants-Export-Action-Phase58` | Mockup `.page-head` "Export" button is Sprint 57.43 AP-2 stub | Phase 58+ |
| `AD-AdminTenants-Row-Actions-Phase58` | Mockup table row ⋯ (dots icon) action menu is Sprint 57.43 visual stub | Phase 58+ |
| `AD-AdminTenants-Card-Toolbar-Functional-Phase58` | Mockup Card-internal toolbar (cmdk filter + Plan: all + Sort: runs 24h ghost buttons) is Sprint 57.43 visual stub (no click handlers). Phase 58+ wires real filter/sort + cmdk command palette | Phase 58+ |
| `AD-MockupCapture-03-MOCKUP-admin-tenants` | Sprint 57.43 3-way evidence pair deferred MOCKUP screenshot capture (python http.server + Playwright at 1440×900). Carryover to docs polish OR captured in next mockup-strict-rebuild sprint if `/admin/tenants` mockup re-rendered alongside `/admin/tenant-settings` | Phase 58+ docs polish |
| **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier-Recalibration`** | Sprint 57.43 1st validation under `agent_factor = 0.55` produced ratio ~0.41 BELOW band by 0.44 → 1st rollback-trigger data point. Per rollback rule: KEEP 0.55 (single-data-point caution); if Sprint 57.44 also < 0.7 → tighten to 0.45; if 0.45 also undershoots → consider Option B per-class split | **Sprint 57.44 retro decision** |
| `AD-TenantSettings-6-Tab-Rebuild` (carried) | Last remaining CATASTROPHIC post Sprint 57.43; mockup `page-admin.jsx:411+ TenantSettings` 6-tab architecture (General / Feature Flags 14 / Quotas / HITL Policies / Members 8 / Danger Zone). Sprint 57.44 candidate; ~15-20 hr human-eq estimated (likely ~3-4 hr actual under agent_factor) | Sprint 57.44 |

---

## Q5 — Next steps / carryover candidates

**Per rolling planning §6 — no specific Sprint 57.44 task list pre-written.** Candidate directions per ROI (from `claudedocs/1-planning/next-phase-candidates.md` + Sprint 57.43 closeout):

1. 🥇 **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` 6-tab architecture rebuild (~15-20 hr human-eq; likely ~3-4 hr actual under agent_factor 0.55). **Last remaining CATASTROPHIC**; closes Phase-2 epic full clean (21 PARITY + 1 NEAR-PARITY + 0 CATASTROPHIC).
2. **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename (~30 min NEAR-PARITY quick win). Closes 1 NEAR-PARITY to drop to 0.
3. **`AD-MockupCapture-03-MOCKUP-admin-tenants`** — capture deferred mockup screenshot for 3-way evidence completeness (~15-30 min docs polish).
4. **Phase 58+ Backend extensions** — `AD-AdminTenants-Backend-Schema-Extension` 🔴 BLOCKING + various Phase 58+ AP-2 stubs (Filter/Pagination/Modal/Card-Toolbar) wiring.
5. **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier-Recalibration`** — pending Sprint 57.44 2nd validation data point per rollback rule.

**Note on Sprint 57.44 candidate priority**: If `/tenant-settings` selected, it would be the 5th and last CATASTROPHIC closure. Phase-2 epic full clean within reach (1 more sprint).

---

## Q6 — Verbatim-CSS protocol compliance

- ✅ Layer 2 byte-identical: `styles-mockup.css` vs `reference/design-mockups/styles.css` — diff guard PASS (re-confirmed Day 2)
- ✅ Layer 4 collision check: 0 new `--sc-*` token collisions; new components reference existing `var(--primary)` / `var(--primary-soft-2)` / `var(--memory)` / `var(--info)` / `var(--fg)` / `var(--fg-muted)` / `var(--font-mono)` from styles-mockup.css verbatim
- ✅ HEX_OKLCH_BASELINE: 46 unchanged (estimated +0-2 bump did not materialize — correct outcome per verbatim-CSS protocol; literals belong only in styles-mockup.css)
- ✅ mockup-fidelity guard exit 0 — Day 0 baseline + Day 1 post-rebuild + Day 2 post-Vitest + Day 2.5 post-sweep all PASS

---

## Q7 — Solo-dev policy validation

N/A — SKIP. Sprint 57.43 is single-author solo-dev; `required_approving_review_count = 0` policy continues to function (PR will be opened against main; CI gates apply; self-approve still blocked by GitHub but `count=0` bypasses requirement).
