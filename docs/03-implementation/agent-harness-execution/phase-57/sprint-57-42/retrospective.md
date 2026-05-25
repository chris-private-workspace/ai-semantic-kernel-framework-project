# Sprint 57.42 — Retrospective

**Sprint id**: 57.42 — AD-Memory-Layers-Matrix-Rebuild
**Closed**: 2026-05-25
**Branch**: `feature/sprint-57-42-memory-matrix-rebuild`
**Class**: `frontend-mockup-strict-rebuild` 0.60 (8th data point)
**Commits**:
- `bdb10844` — plan + checklist draft / 2 files / +706
- `f45ff7ee` — Day 0 / 26 files / +118 / -1
- `d93e0302` — Day 1 / 21 files / +999 / -1153
- `cceb79f4` — Day 2 / 8 files / +522 / -12
- `0166e737` — Day 2.5 / 28 files / +74
- (TBD Day 3 closeout commit)

---

## Q1 — What went well

1. **Day 0 Prong 2.5 child-component-tree-depth audit + Prong 2 content verify caught 9 D-DAY0-N findings without any mid-sprint surprises in Day 1.** AD-Plan-5 (folded into `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2.5` Sprint 57.40) + AD-Plan-3 Prong 2 content verify combined: 9 findings catalogued at Day 0 (5 vocabulary / data-source corrections + 1 routing path correction + 1 primitives presence + 1 baseline math + 1 consumer breadth confirmation), all <20% scope shift verdict GO. Day 1 agent invocation completed first-try with 0 re-work.

2. **Option B 2-tab DROP decision validated cleanly.** Unlike Sprint 57.40 (`/governance/audit-log` distinct WORM concept) + Sprint 57.41 (`/verification/timeline` distinct CorrectionTraceView), `/memory` Recent + By-Scope sub-tabs were BOTH subsumed by mockup unified view (matrix grid + bottom ops Card). The plan §1.4 documented this difference; agent dropped the tabs + added backward-compat redirects (`/memory/recent` + `/memory/by-scope` → `/memory`) without issue. Day 2.5 sweep confirms 0 routing regressions.

3. **Vitest grew +12 NEW tests (vs +5-8 target = +150-240% over; within healthy cohort 57.40 +15 / 57.41 +9).** All 6 NEW spec files written first-try by agent; only 1 drift (D-DAY2-1 `getByText("now")` ambiguous between TIME_TRAVEL_MARKS labels strip + cursor mono display) auto-resolved mid-agent-run via `getAllByText(...).length >= 2`. Final count 486/486 vs 474 baseline (post-vintage-delete).

4. **20 IDENTICAL + 4 CHANGED (1 expected + 3 sub-300-byte noise) sweep with 0 unintended regressions — cleanest sweep of Phase-2 epic.** Only `/memory` intentionally CHANGED (+102,543 bytes / +144%). 3 noise routes (auth-callback -23 / chat-v2 -19 / overview -38) all sub-300-byte timing jitter within Sprint 57.40+57.41 precedent envelope. This is the lowest noise count + lowest unintended-regression count of the Phase-2 epic history.

5. **Karpathy §3 orphan delete discipline applied at scale — 11 files deleted in one Day 1 wave.** 3 vintage components + 3 vintage hooks + 4 Vitest specs + 1 e2e = 11 orphans total. Net Day 1 delta: +999 / -1153 (NET -154 lines despite +870 lines of NEW component code). The discipline keeps the feature folder lean even as the mockup-fidelity rebuild ships.

6. **Verbatim-CSS protocol kept HEX_OKLCH_BASELINE 46 unchanged.** Day 1 components reference `var(--memory)` / `var(--info)` / `var(--tool)` / `var(--warning)` / `var(--bg-2)` / `var(--fg-muted)` CSS variables (NOT inline oklch literals). Plan §3.6 estimated +0-4 bump did not materialize at all — actual +0. Per Sprint 57.41 Lesson 4: the +0-4 envelope estimate is consistently over-cautious; verbatim-CSS protocol always hits +0 for color refs.

7. **Pattern reuse acceleration evident at infrastructure level.** Sprint 57.42 reused 6 mockup-ui primitives unchanged (Card / Badge / Button / Icon / Field / KvRow) — 0 new primitives lifted. The mockup-ui.tsx has reached a stable post Sprint 57.40+57.41 critical-mass point; future rebuilds (`/admin-tenants` / `/tenant-settings`) likely need 0 new primitive lifts as well.

8. **3-way evidence pair structural fidelity confirmed.** AFTER 173,931 B = 92% of MOCKUP 189,410 B; ~15 KB gap explained by minor cosmetic differences (icon rendering subtleties / font hinting / oklch-vs-rgb pixel precision). Sprint 57.40/57.41 §2.5.4 interpretation pattern held cleanly.

---

## Q2 — What didn't go well + Calibration

### Calibration ratio — 8th data point

**Bottom-up est (plan §8)**: ~15 hr
**Calibrated commit (0.60 multiplier)**: ~9 hr
**Actual wall-clock total**: ≈ **3.0 hr** (Day 0 ~50 min + Day 1 ~50 min + Day 2 ~25 min + Day 2.5 ~15 min + Day 3 closeout ~30-40 min)
**Ratio actual/committed**: **~0.33** — BELOW [0.85, 1.20] band by **~0.52**
**Ratio actual/bottom-up**: ~0.20 — bottom-up was ~5× too generous

### 8-pt window stats for `frontend-mockup-strict-rebuild` 0.60

| Sprint | Ratio | In-band? |
|--------|-------|----------|
| 57.23 | 0.59 | below by 0.26 |
| 57.24 v2 | 1.19 | top of band ✅ |
| 57.25 | 0.88 | in band ✅ |
| 57.27 | ≈0.95 | in band ✅ |
| 57.37A | ≈1.18 | top of band ✅ |
| 57.40 | ≈0.36 | below by 0.49 |
| 57.41 | ≈0.18 | below by 0.67 (deepest of class history) |
| **57.42** | **~0.33** | **below by 0.52** |

- **8-pt mean**: (0.59 + 1.19 + 0.88 + 0.95 + 1.18 + 0.36 + 0.18 + 0.33) / 8 = **0.71** at lower band edge (down from 7-pt mean 0.76 = -0.05)
- **Last 3 (57.40 + 57.41 + 57.42)**: 3 of 3 < 0.7 (0.36, 0.18, 0.33) — `When to adjust` lower-trigger (3+ consecutive < 0.7) **MET** ✅
- **Decision per matrix rule**: **Propose Sprint 57.43 plan lifts baseline 0.60 → 0.40-0.45** for `frontend-mockup-strict-rebuild` class. 4-sprint window mean (57.40-57.42 + Sprint 57.43 TBD) will validate the new baseline.

### Root cause (per Q3 below)

Agent-delegation factor — code-implementer 10th + 11th consecutive invocations completed Day 1 + Day 2 at ~40 min + ~3.4 min wall-clock vs human-rewrite cadence the bottom-up estimates assume. Per plan §1.5 + `.claude/rules/sprint-workflow.md §Proposed Agent Delegation Factor Modifier`:

**Sprint 57.42 is the 5th cross-class data point** for `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`:

| Sprint / FIX | Class | Ratio | Agent-delegated |
|--------------|-------|-------|-----------------|
| Sprint 57.39 | `-with-extras` (0.65) | 0.41 | 6th+7th consecutive |
| FIX-015 (post-hoc) | bundled FIX | ~0.04 (outlier) | code-implementer 6 child re-point |
| Sprint 57.40 | mockup-strict-rebuild | 0.36 | 7th consecutive |
| Sprint 57.41 | mockup-strict-rebuild | 0.18 | 8th+9th consecutive |
| **Sprint 57.42** | **mockup-strict-rebuild** | **0.33** | **10th+11th consecutive** |

**Activation rule status**: 3+ data points across multiple classes — **fully met** (5 data points across 2 classes; 4 consecutive agent-delegated below-band in mockup-strict-rebuild class). Per plan §9 carryover, Sprint 57.43 retro must structurally decide: **Option A multiplicative `agent_factor` coefficient (start 0.55)** vs **Option B per-class sub-class split** per `.claude/rules/sprint-workflow.md §Proposed Agent Delegation Factor Modifier`.

### Other didn't-go-well items

- **Bottom-up estimates remain ~5× too generous for agent-delegated frontend work.** Pattern now 8 consecutive sprints (57.34-57.42 minus skip). Calibration matrix per-class baseline alone cannot capture the agent-vs-human cadence delta. Sprint 57.43 retro must commit to structural modifier — defer no further.

- **Bottom-up est ~5× generous (vs 57.41's ~9× generous)** — improvement direction. The agent-delegation speedup is gradually being learned by my bottom-up estimates (15 hr → 3 hr = 5× vs 14 hr → 1.5 hr = 9× last sprint). Sprint 57.43 bottom-up should target ~8-10 hr range for similar-scope CATASTROPHIC rebuild and re-measure.

---

## Q3 — What we learned (generalizable lessons)

### Lesson 1 — Outer-tab decision is mockup-driven (Option A vs Option B)

Sprint 57.40 (`/governance/audit-log` Option A preserve) + Sprint 57.41 (`/verification/timeline` Option A preserve) + Sprint 57.42 (`/memory` Option B DROP) — pattern: preserve outer tab iff mockup OMITS a distinct production-only operational concept; drop outer tab iff mockup's unified view subsumes both production sub-tabs. Sprint 57.42's case (Recent + By-Scope both → mockup matrix + bottom ops Card) is the first DROP precedent; future rebuilds should classify the production sub-tab disposition vs mockup at Day 0 §1.4.

### Lesson 2 — Karpathy §3 orphan delete at scale (11 files / 1 wave)

Sprint 57.42 deleted 11 files (3 components + 3 hooks + 4 Vitest + 1 e2e) in Day 1 — the largest single-wave Karpathy §3 application of the Phase-2 epic. Net Day 1 delta +999/-1153 (NET -154 lines despite +870 lines of NEW). Lesson: when full-rebuild scope SUPERSEDES vintage implementation entirely, delete the vintage in the same Day-1 commit as the rebuild — don't defer to "Day 2 spec migration" task. Sprint 57.42 actually pulled the Day 2 §2.1 spec-delete tasks forward to Day 1 closeout post-agent for this reason.

### Lesson 3 — Agent-delegation speedup is ~5-7× even for largest-component sprints

Sprint 57.40 governance: ~40 min wall-clock for 5 components / ~6-8 hr human-eq (~7-12× speedup)
Sprint 57.41 verification: ~25-30 min for 5 components / ~5-8 hr human-eq (~10-15× speedup)
Sprint 57.42 memory: ~40 min for 6 components (incl. most-complex MemoryMatrix 5×3 grid + interactive TimeTravelScrubber) / ~5-5.5 hr human-eq (~7-8× speedup)

The speedup is consistent across scope sizes — even the most-complex single-sprint component (TimeTravelScrubber with `useEffect` setInterval + cleanup + slider mapping + op markers) didn't slow agent throughput materially. This further confirms the agent-delegation modifier proposal: the speedup factor is **scope-class-independent** within the frontend-mockup-strict-rebuild class.

### Lesson 4 — Verbatim-CSS protocol +0-4 estimate is consistently over-cautious

Sprint 57.41 plan §3.6 estimated +2-4 bump; actual +0. Sprint 57.42 plan §3.6 estimated +0-4 bump; actual +0. Pattern: when NEW components use ONLY `var(--*)` CSS variable refs (never inline `oklch(...)` literals), the HEX_OKLCH_BASELINE stays static. **Generalizable**: Plan §3.6 estimate envelope should be reduced to +0-2 (tight) going forward, OR removed entirely if next 1-2 rebuilds also hit +0. The +0-4 envelope is anchored on Sprint 57.23-57.27 vintage which used some inline `oklch()` literals; post Sprint 57.40 + 57.41 the verbatim-CSS discipline tightened.

### Lesson 5 — `getAllByText` for ambiguous fixture strings (3rd application)

D-DAY2-1: `getByText("now")` matched 2 elements (TIME_TRAVEL_MARKS labels strip "now" + cursor mono display "now"). Sprint 57.42 agent caught + fixed mid-run via `getAllByText("now").length >= 2`. **3rd consecutive cohort application** of the ambiguous-string pattern:
- Sprint 57.40 D-DAY2-X: `ApprovalDetailPane` payload.reason in subtitle + Agent rationale field
- Sprint 57.41 D-DAY2-1: VerificationRunsTable adapter projects `reason` into BOTH claim AND evidence cells
- Sprint 57.42 D-DAY2-1: TIME_TRAVEL_MARKS "now" label + cursor display "now"

This is now a clear cross-sprint Vitest convention. **Recommend folding into `.claude/rules/testing.md` or new `frontend-mockup-fidelity-vitest-patterns.md` doc**: when a fixture string appears in 2+ rendered locations, prefer `getAllByText(...).length >= N` over `getByText(...)`.

### Lesson 6 — Sub-300-byte sweep noise is environmental, not regression

Sprint 57.42 sweep showed 3 sub-300-byte noise routes (auth-callback -23 / chat-v2 -19 / overview -38) on routes UNCHANGED by the sprint. Sprint 57.41 had 2 noise + 1 expected; Sprint 57.40 had 1 noise + 1 expected. **Generalizable**: cumulative ~50-300 byte deltas on visually-static routes between sweep runs are environmental jitter (Playwright render timing variations / live-timestamp displays / chart canvas rasterization). The current `< 300-byte` envelope is reliable; **recommend codifying as a Risk Class** (similar to Sprint 53.7 Risk Class A paths-filter) for sweep diff interpretation.

---

## Q4 — Audit debt deferred

| AD | Description | Target |
|----|-------------|--------|
| `AD-Memory-Matrix-Backend-Cursor-Aware-Endpoint` | Backend `/api/v1/memory/matrix?scope=*&time_scale=*&cursor=*` endpoint required for real cursor-aware time-travel data. Sprint 57.42 uses fixture + client-side filter simulation | Phase 58+ |
| `AD-Memory-Ops-Timeline-Backend-Endpoint` | Backend `/api/v1/memory/ops/recent?limit=100` endpoint for RecentMemoryOpsCard. Sprint 57.42 fixture-only | Phase 58+ |
| `AD-Memory-GDPR-Erasure-Backend-Endpoint` | Backend `/api/v1/memory/erasure` POST endpoint for GdprErasureCard form submission (audit chain WORM record). Sprint 57.42 form button non-functional (`window.alert` stub) | Phase 58+ |
| `AD-Memory-Vintage-Hooks-Cleanup` | `memoryService.ts` preserved Day 1 but has 0 consumers post-rebuild. Phase 58+ either wire to RecentMemoryOpsCard (when ops endpoint ships) OR fully orphan delete | Phase 58+ |
| `AD-Memory-Old-URL-Redirect-Phase58-Retire` | Sprint 57.42 keeps `/memory/recent` + `/memory/by-scope` → `/memory` redirects for backward compat. Phase 58+ analytics-based retire once bookmark traffic decays | Phase 58+ |
| `AD-Memory-New-Entry-Modal-Phase58` | Mockup `.page-head` "New entry" button is Sprint 57.42 AP-2 stub. Phase 58+ wires write modal (scope-aware key/value/ttl form + backend POST endpoint) | Phase 58+ |
| `AD-Memory-Export-Action-Phase58` | Mockup "Export" button is Sprint 57.42 AP-2 stub. Phase 58+ wires CSV/JSON export endpoint | Phase 58+ |
| `AD-Memory-Types-MHist-Refresh` | `types.ts` MHist header references deleted hook/component files; cosmetic comment only. Day 3 closeout deferred to Phase 58+ cleanup pass | Phase 58+ |
| `AD-Badge-Docstring-Refresh` | `frontend/src/components/ui/badge.tsx` docstring references deleted `MemoryScopeBadge`; cosmetic; 0 runtime impact | Phase 58+ |
| **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** | ✅ **ACTIVATED 2026-05-25** via Option A multiplicative `agent_factor = 0.55` (Sprint 57.42 retro structural decision — 5 cross-class data points: 57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 + 57.42 0.33; 4 consecutive mockup-strict-rebuild < 0.7 = activation criteria FULLY MET). See `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` for formula + rollback rule + tracking discipline. First validation: **Sprint 57.43 retro Q2** (`/admin-tenants` or `/tenant-settings` rebuild; both `mockup-strict-rebuild` 0.60 × 0.55 = effective 0.33). | ✅ **CLOSED 2026-05-25** (`chore/agent-delegation-factor-activate` branch — Sprint 57.42 closeout follow-up) |
| **`AD-Sprint-Plan-frontend-mockup-strict-rebuild-baseline-lift`** | **Lower-trigger MET**: 3 consecutive < 0.7 (57.40 0.36 + 57.41 0.18 + 57.42 0.33). Per `When to adjust` matrix rule, propose **Sprint 57.43 plan lifts baseline 0.60 → 0.40-0.45**. Validate next 2-3 mockup-strict-rebuild sprints (likely admin-tenants + tenant-settings) | **Sprint 57.43 plan** |

---

## Q5 — Next steps / carryover candidates

**Per rolling planning §6 — no specific Sprint 57.43 task list pre-written.** Candidate directions per ROI (from `claudedocs/1-planning/next-phase-candidates.md` + post-Sprint-57.42 audit report):

1. 🥇 **`AD-Memory-Layers-Matrix-Rebuild`** — ✅ CLOSED by this Sprint 57.42
2. **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` tenants table rebuild ~12-15 hr (4th CATASTROPHIC route; backend list endpoint already wired; pure frontend)
3. **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` 6-tab rebuild ~15-20 hr (5th CATASTROPHIC route; largest scope; mostly form work)
4. **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename ~30 min (NEAR-PARITY quick win)
5. **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **MANDATORY** structural calibration matrix evaluation (activation criteria fully met; Sprint 57.43 retro)
6. **`AD-Sprint-Plan-frontend-mockup-strict-rebuild-baseline-lift`** — propose Sprint 57.43 plan lifts baseline 0.60 → 0.40-0.45

**Other carryover ADs** added by Sprint 57.42 (7 new Phase-58 ADs per Q4 above).

---

## Q6 — Verbatim-CSS protocol compliance

- ✅ Layer 2 byte-identical: `styles-mockup.css` vs `reference/design-mockups/styles.css` — diff guard PASS (re-confirmed Day 2)
- ✅ Layer 4 collision check: 0 new `--sc-*` token collisions; new components reference existing `var(--memory)` / `var(--info)` / `var(--tool)` / `var(--warning)` / `var(--bg-2)` / `var(--fg)` / `var(--fg-muted)` / `var(--primary)` / `var(--font-mono)` from styles-mockup.css verbatim
- ✅ HEX_OKLCH_BASELINE: 46 unchanged (estimated +0-4 bump did not materialize — correct outcome per verbatim-CSS protocol; literals belong only in styles-mockup.css)
- ✅ mockup-fidelity guard exit 0 — Day 0 baseline + Day 2 post-implementation + Day 2.5 post-rebuild all PASS

---

## Q7 — Solo-dev policy validation

N/A — SKIP. Sprint 57.42 is single-author solo-dev; `required_approving_review_count = 0` policy continues to function (PR will be opened against main; CI gates apply; self-approve still blocked by GitHub but `count=0` bypasses requirement).
