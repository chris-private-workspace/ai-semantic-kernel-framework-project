# Sprint 57.22 — Plan

**Sprint ID**: 57.22
**Theme**: AD-Mockup-Fidelity-Comprehensive-Audit
**Phase**: 57+ Frontend SaaS
**Scope class**: NEW `frontend-mockup-fidelity-audit` 0.85 multiplier (1st application; pure investigative work — bottom-up high accuracy / low variance per Sprint 57.5 `reality-check` 0.85 prior art)
**Days**: 5 (Day 0/1/2/3 audit + Day 4 closeout) — revised Day 0 per D-PRE-2 scope correction
**Created**: 2026-05-18 (Day 0 of Sprint 57.22)
**Status**: Active

**Modification History**:
- 2026-05-18: Day 0 D-PRE-2 scope correction — mockup actual page count ~40 (not 15; `page-*.jsx` are monolithic bundles with 4-14 sub-pages each); user 2026-05-18 AskUserQuestion: extend 57.22 to 5 days one-shot complete (NOT split)
- 2026-05-18: Initial creation (Sprint 57.22 Day 0) — pivot from Sprint 57.21 retrospective user-surfaced gap

---

## Sprint Goal

Produce a **comprehensive, evidence-based mockup-fidelity audit** comparing all 15 mockup pages (`reference/design-mockups/page-*.jsx` + `shell.jsx` + `topbar-overlays.jsx`) against current production pages, with per-page side-by-side Playwright MCP screenshots + classified diff matrix + Strict 1:1 ±2px scoring + prioritized action matrix to drive Sprint 57.23+ multi-sprint AD-Mockup-Full-Rebuild-Round-2 execution.

**NOT a code-change sprint** — output is `AUDIT-REPORT-COMPREHENSIVE.md` + screenshot library + execution-priority matrix.

---

## Background

Sprint 57.20 was framed as "AD-Mockup-Direct-Port Foundation" but Sprint 57.21 closeout user review (2026-05-18) surfaced 3 critical reality gaps:

1. **`/auth/login` 100% legacy Sprint 57.7 architecture** — never ported from mockup; predates Sprint 57.18 mockup-integration foundation
2. **Page non-responsive + font/size variance** — AppShellV2 IS `h-screen w-screen` grid ✓ but inner `<main p-6>` inset by default (only chat-v2 uses fullBleed); per-page micro-typography (11.5px/12.5px mockup micro-sizes) NOT applied — most production pages use Tailwind default text-sm/text-base
3. **`/overview` ~60% fidelity only** — Sprint 57.19 commit `f8949504` did 1:1 layout port; Sprint 57.20 commit `d6cc70bd` only did 8 find/replace token rename (`bg-card → bg-bg-1` etc.) — **NO** typography / spacing / card radius / shadow / sparkline color rework

Sprint 57.20 paper claim "Mockup-Direct-Port Foundation" conflated **token migration** + **shell infrastructure** with **page rebuild**. True 1:1 mockup-direct rebuilds are limited to:
- Operations 4 pages (Sprint 57.19 US-C1-C4: /overview + /orchestrator + /subagents + /state-inspector) — layout 1:1 only; visual ~60%
- Chat-v2 Phase-1 (Sprint 57.21: Turn Block Model + 3-col + Inspector frame) — structural rewrite Phase-1 but Phase-2 widgets are ComingSoon
- AppShellV2 V3 grid (Sprint 57.20) ✓
- Topbar overlays (Sprint 57.19: CommandPalette + Notifications + UserMenu) ✓

**Legacy pages NEVER ported** (7 pre-mockup architecture): /auth/login + /auth/callback + /cost-dashboard + /sla-dashboard + /admin-tenants + /governance ×3 + /memory + /verification + /tenant-settings.

**PROP stubs** (18): /tools, /agents, /models, /sse, /pricing, /jit-retrieval, /compaction, /cache-manager, /loop-debug, /rbac, /devui, /incidents, /redaction, /error-policy, /audit-log, /tenant-onboarding, /subagent-tree, /role-permissions.

This Sprint 57.22 = the **dedicated audit sprint** to produce data-driven priority matrix BEFORE committing to AD-Mockup-Full-Rebuild-Round-2 multi-sprint epic, per user 2026-05-18 AskUserQuestion decision (Strategy C: audit-first).

---

## User Stories

**US-A1** (Day 0 三-prong + scope verify):
*As an audit sprint operator, I want* three-prong verify (path / content / schema) before any audit work begins so that the AUDIT-REPORT scope reflects real repo state at branch creation time and prevents Sprint 57.5/57.17/57.20 reality-vs-paper cascade pattern from recurring within Sprint 57.22 itself.

**US-A2** (Day 1 — Auth + Operations dashboards audit):
*As an audit sprint operator, I want* per-page Playwright MCP screenshots at 1440×900 for both mockup http server `:8080/#<route>` and production dev server `:3007<route>` for 9 pages (auth login/register/invite/mfa/expired + overview + cost-dashboard + sla-dashboard + memory) side-by-side compared with classified diff matrix entries (cosmetic / structural / functional) + Strict 1:1 ±2px scoring (computed via Playwright `boundingBox()` + visual diff).

**US-A3** (Day 1 — Auth + Operations diff catalogue assembly):
*As an audit sprint operator, I want* `AUDIT-REPORT-COMPREHENSIVE.md` skeleton + 9 page sections (auth × 5 + ops × 4) populated with screenshot links + per-page severity score + estimated rebuild hours per page so that priority matrix data is available for Day 2 chat-v2 Phase-2 + Day 2 governance work.

**US-B1** (Day 2 — Governance + chat-v2 Phase-2 + remaining mockup pages audit):
*As an audit sprint operator, I want* Playwright MCP screenshots + diff matrix for governance ×3 (approvals + redaction + error-policy + audit-log) + chat-v2 Phase-2 widget gaps (Memory Block / HITL FourAction / Composer richness / Inspector Trace+Memory+SubagentTree tab content) + remaining mockup pages (agents + tools + models + sse + admin + platform + verification + incidents + tenant-settings) so audit covers all 15 mockup pages + 25 production pages comprehensively.

**US-B2** (Day 2 — Priority matrix + Sprint 57.23+ recommendation):
*As an audit sprint operator, I want* `AUDIT-REPORT-COMPREHENSIVE.md` final priority matrix + 4-page-group execution-order recommendation (Auth / Operations / Governance / Chat-v2 Phase-2 — all 4 in scope per user 2026-05-18 alignment) + per-page calibrated hour estimate at Strict 1:1 ±2px bar + Sprint 57.23+ first-execution-sprint scope-class proposal (NEW `frontend-mockup-strict-rebuild` 0.55-0.65 estimate).

**US-C1** (Day 2 closeout):
*As an audit sprint operator, I want* retrospective.md Q1-Q7 + memory snapshot + MEMORY.md +1 + CLAUDE.md V2 Refactor Status table row update (Latest = 57.22 audit) + sprint-workflow.md calibration matrix +1 row (`frontend-mockup-fidelity-audit` 0.85 1st app baseline) + PR open.

---

## Technical Specifications

### Audit methodology (canonical)

For **each mockup page**:

1. **Setup**:
   - `python -m http.server 8080` running in `reference/design-mockups/` directory
   - `npm run dev` running in `frontend/` (port :3007)
   - Both dark theme active (`html.className === "dark"`)

2. **Mockup capture**:
   - Playwright MCP `browser_navigate http://localhost:8080/#<route>` (mockup hash router)
   - Playwright MCP `browser_resize 1440×900`
   - Playwright MCP `browser_take_screenshot filename=audit/mockup/<route>.png fullPage=false`

3. **Production capture**:
   - Playwright MCP `browser_navigate http://localhost:3007/<route>`
   - Playwright MCP `browser_resize 1440×900` (same viewport)
   - Playwright MCP `browser_take_screenshot filename=audit/prod/<route>.png fullPage=false`

4. **Side-by-side diff** (per-page entry in AUDIT-REPORT):
   ```markdown
   ### Page: /<route>
   - Mockup screenshot: `audit/mockup/<route>.png`
   - Production screenshot: `audit/prod/<route>.png`
   - Last ported: Sprint XX.Y commit `<sha>` (or NEVER if pre-mockup)
   - **Diff matrix**:
     - Layout: PASS / PARTIAL / FAIL
     - Typography: PASS / PARTIAL / FAIL (mockup uses 11.5px/12.5px micro-sizes)
     - Spacing: PASS / PARTIAL / FAIL (±2px tolerance)
     - Shadow / radius: PASS / PARTIAL / FAIL
     - Color tokens: PASS / PARTIAL / FAIL
     - Interactivity: PASS / PARTIAL / FAIL (hover / focus / disabled states)
   - **Severity**: cosmetic / structural / functional (worst of above)
   - **Strict 1:1 score**: NN% (compute weighted: layout 30% + typography 20% + spacing 20% + shadow/radius 10% + color 10% + interactivity 10%)
   - **Estimated rebuild cost**: X hr at Strict 1:1 ±2px bar
   - **Action items** (for Sprint 57.23+ execution):
     1. <action item 1>
     2. <action item 2>
   ```

5. **Priority matrix** (after all 15 pages audited):
   ```markdown
   | Priority | Page | Score | Rebuild hr | Group | Dependencies |
   |----------|------|-------|-----------|-------|--------------|
   | P0 | /auth/login | 30% | 4 hr | Auth | None |
   | P0 | /overview | 60% | 3 hr | Ops | recharts config |
   | P1 | /chat-v2 (Phase-2) | 50% | 8 hr | ChatV2 | Backend wire |
   | ... | ... | ... | ... | ... | ... |
   ```

### Audit scope (~40 audit units; revised Day 0 per D-PRE-2)

**Day 0 finding**: `reference/design-mockups/page-*.jsx` files are **monolithic bundles** — each file contains 4-14 distinct page components. Real audit unit count ~40 (not 15 as planned originally). Per Sprint workflow Step 2.5 §Decide go/no-go (>50% scope shift), user 2026-05-18 AskUserQuestion chose "Extend 57.22 to 5 days one-shot complete" (NOT split into 57.22+57.23).

### Audit unit breakdown (~40 units; route-level not component-level)

| Mockup file | Sub-pages (within file) | Production counterpart | Audit unit count |
|-------------|------------------------|-----------------------|------------------|
| `page-auth-extras.jsx` | login / register / invite / mfa / expired | /auth/login + /auth/callback (+ 3 PROP) | 5 |
| `page-overview.jsx` | overview | /overview | 1 |
| `page-chat.jsx` | chat (Phase-2 widgets) | /chat-v2 | 1 (+ Phase-2 widget delta sub-units) |
| `page-platform.jsx` | orchestrator + state-inspector | /orchestrator + /state-inspector | 2 |
| `page-platform2.jsx` | subagents | /subagents | 1 |
| `page-governance.jsx` | approvals / redaction / error-policy / audit-log | /governance + /redaction (PROP) + /error-policy (PROP) + /audit-log (PROP) | 4 |
| `page-tools.jsx` | tools | /tools (PROP) | 1 |
| `page-agents.jsx` | agents | /agents (PROP) | 1 |
| `page-models.jsx` | models | /models (PROP) | 1 |
| `page-sse.jsx` | sse | /sse (PROP) | 1 |
| `page-admin.jsx` | admin-tenants + tenant-settings | /admin-tenants + /tenant-settings | 2 |
| `page-extras.jsx` | cost-dashboard / sla-dashboard / memory / verification / incidents | /cost-dashboard + /sla-dashboard + /memory + /verification + /incidents (PROP) | 5 |
| `shell.jsx` | AppShellV2 layout | `frontend/src/components/AppShellV2.tsx` + Sidebar + Topbar | 1 (already ported Sprint 57.20 — audit only verifies fidelity) |
| `topbar-overlays.jsx` | CommandPalette + Notifications + UserMenu | (3 components in `frontend/src/components/topbar/`) | 1 (already ported Sprint 57.19 — audit only verifies fidelity) |

**Total**: ~40 audit units (Day 0 D-PRE-2 revision; each ~10-15 min capture + diff write):

| Group | Routes | Count |
|-------|--------|-------|
| Auth | login / callback / register / invite / mfa / expired | 6 |
| Operations dashboards | overview / cost-dashboard / sla-dashboard / memory / verification | 5 |
| Chat-v2 | chat-v2 + Phase-2 widgets (Memory Block / HITL FourAction / Composer / Inspector Trace/Memory/Tree) | 1 + 6 widgets = 7 |
| Governance | approvals / redaction / loop-debug / audit-log | 4 |
| Operations (platform) | orchestrator (+ 6 tabs counted as 1) / subagents / state-inspector / compaction / workflows / error-policy / rbac | 7 |
| Admin | tenants list / tenant-settings / feature-flags / quotas / hitl-policies / members / danger-zone / tenant-onboarding / pricing / domain-detail | 10 |
| Misc | models / tools / sse / devui (+ matrix/cat12/sse 3 sub) / a11y-audit / incidents / subagent-tree / jit-retrieval / cache-manager | 7 |
| Shell / Topbar | AppShellV2 + Topbar overlays (already ported Sprint 57.20; audit only verifies fidelity) | (excluded — already in baseline) |
| **Total** | | **~46 → consolidated ~40** |

### AUDIT-REPORT-COMPREHENSIVE.md structure

- Header: methodology + scope + bar definition (Strict 1:1 ±2px / ≥95%)
- Section per audit unit (27 sections; each ~30-40 lines)
- Final priority matrix (P0 / P1 / P2 / P3 with rebuild hours + group)
- Sprint 57.23+ first-execution-sprint scope-class proposal
- Estimated total epic hours
- Open invariants (gaps the audit cannot resolve)

Estimated total report length: ~800-1000 lines.

---

## File Change List (summary)

**NEW (Sprint 57.22 deliverables)**:
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-22-plan.md` (this file)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-22-checklist.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/artifacts/mockup-fidelity-audit/AUDIT-REPORT-COMPREHENSIVE.md` (~800-1000 lines)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/artifacts/mockup-fidelity-audit/screenshots/mockup/*.png` (~27 files)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/artifacts/mockup-fidelity-audit/screenshots/prod/*.png` (~27 files)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/progress.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/retrospective.md`
- `memory/project_phase57_22_mockup_fidelity_audit.md`

**EDIT**:
- `MEMORY.md` (+1 line)
- `CLAUDE.md` V2 Refactor Status table 5-row shift (Latest = 57.22 / Prev = 57.21 / Prev-Prev = 57.20 / Prev-Prev-Prev = 57.19 / Prev⁴ = 57.18; 57.17 dropped) + Phase row 18/N→19/N + Roadmap row + Next Phase 候選 row + 3 footer line prepends
- `.claude/rules/sprint-workflow.md` calibration matrix +1 row (`frontend-mockup-fidelity-audit` 0.85 1st app)
- `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分 prepend Sprint 57.22 closeout + add `#### Phase 57.22 carryover` section with AD-Mockup-Full-Rebuild-Round-2 multi-sprint epic + per-page sub-AD entries

**ZERO production code changes** — pure audit sprint.

---

## Acceptance Criteria

- [ ] 27 audit units (1 mockup page sub-unit + 1 production page sub-unit each) captured via Playwright MCP at 1440×900
- [ ] AUDIT-REPORT-COMPREHENSIVE.md ≥ 800 lines with all 27 sections populated + per-section diff matrix + severity + Strict 1:1 score + rebuild hour estimate + action items
- [ ] Priority matrix with P0/P1/P2/P3 classification covering all 4 user-selected page groups (Auth + Operations + Governance + Chat-v2 Phase-2)
- [ ] Sprint 57.23+ first-execution-sprint scope-class proposal + estimated total epic hours
- [ ] Retrospective Q1-Q7 + calibration matrix +1 row + memory snapshot + CLAUDE.md V2 status sync
- [ ] Anti-Pattern 11/11 PASS (AP-1 not applicable — no LLM call; AP-4 not applicable — no Potemkin feature added; etc.)
- [ ] ZERO production code change (`git diff --stat main..HEAD` shows only `claudedocs/` + `docs/` + `memory/` + `CLAUDE.md` + `.claude/rules/sprint-workflow.md` + `MEMORY.md` + `SITUATION-V2-SESSION-START.md`)
- [ ] ZERO Vitest / pytest baseline change (no test added or removed)
- [ ] PR opens against main + all CI checks green (visual-regression should PASS unchanged since 0 production code changes)

---

## Workload

Bottom-up est ~25-30 hr → calibrated commit ~22-25 hr (multiplier 0.85) — Day 0 D-PRE-2 revision

- Day 0 (1.5 hr): plan + checklist + 三-prong (mockup http server :8080 verify + dev server :3007 verify + Playwright MCP install verify) + branch + progress.md skeleton + D-PRE-1+2 scope correction
- Day 1 (5-6 hr): audit Auth 6 + Operations dashboards 5 + Chat-v2 page-level 1 + AUDIT-REPORT skeleton + 12 sections populated
- Day 2 (5-6 hr): audit Chat-v2 Phase-2 widget gaps 6 + Governance 4 + Operations (platform) 7 = 17 sections
- Day 3 (5-6 hr): audit Admin 10 + Misc 7 = 17 sections
- Day 4 (3-4 hr): AUDIT-REPORT priority matrix assembly + Sprint 57.23+ recommendation + Σ rebuild hours estimate
- Day 4 closeout (2-3 hr): retrospective + memory snapshot + MEMORY.md + CLAUDE.md V2 status sync + sprint-workflow.md calibration matrix + SITUATION update + PR

**Calibration class**: NEW `frontend-mockup-fidelity-audit` 0.85 (HYBRID weighted blend: 40 capture units × 0.90 mechanical ~70% weight + AUDIT-REPORT writing × 0.75 ~15% + closeout × 0.80 ~15% = ~0.85 mid-band). Prior art: Sprint 57.5 `reality-check` 0.85 (same investigative work class, 1-data-point ratio 1.04 ✅ in band). Single data point KEEP 0.85 per `When to adjust` 3-sprint window rule. **Risk**: 5-day audit sprint is largest Phase 57+ scope; calibration outlier risk elevated.

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Mockup http server :8080 not running mid-sprint | Medium | Block Day 1 capture | Day 0 三-prong verify both servers running + auto-restart command in progress.md |
| Playwright MCP screenshot capture flaky on dark theme | Medium | Re-capture cost | Wait for `document.fonts.ready` + `waitForLoadState networkidle` before screenshot; document pattern in AUDIT-REPORT methodology |
| 27 capture units too aggressive for 2 days | High | Audit incomplete | Time-box per-unit to 12 min; if Day 2 EOD < 90% complete, defer remaining stubs (PROP pages) to Sprint 57.23 retrospective |
| User changes priority mid-sprint (e.g. dropping a page group) | Low | Scope shrink | Per-page audit units are independent — drop without cascade |
| AUDIT-REPORT severity scoring subjective | High | Inconsistent priority matrix | Use objective measures: layout pass = bounding box ±2px / typography pass = computed font-size ±0.5px / color pass = computed color RGB exact match |
| Per-page rebuild hour estimate inaccurate | Medium | Sprint 57.23+ over/under-commit | Document estimate methodology + revisit per-page actuals during execution sprints; AUDIT-REPORT estimates are baseline NOT contract |

---

## Dependencies

- **Playwright MCP** plugin must be active for Day 1+2 screenshot capture
- **Mockup http server** running at `:8080` (mockup hash router: `http://localhost:8080/#<route>`)
- **Dev server** running at `:3007` (production routes)
- **Dark theme + Geist font + dark background** active in both (Sprint 57.21 D-DAY4-6/7/8 baseline)
- NO backend dependency (audit is pure frontend visual)
- NO database dependency

---

## Cross-Sprint Carryovers

**Inherited from Sprint 57.21**:
- 10 NEW Phase-2+ ADs (AD-ChatV2-Full-Mockup-Fidelity Phase-2 epic + Memory-Block + HITL-FourAction + Composer-Richness+Wire + Inspector-{Trace,Memory,SubagentTree} + SessionList-Backend + Cat12-SSE-Trace-Id) — audited as part of US-B1 chat-v2 Phase-2 widget gaps; Sprint 57.22 confirms or refines

**Inherited from Sprint 57.20**:
- AD-Mockup-Direct-Port-Round-2 (16 R2 findings + 8 ship pages token migration) — audited Sprint 57.22 as part of Operations + Governance + Admin sub-units; expected to merge into AD-Mockup-Full-Rebuild-Round-2 Phase-2 epic
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 US-F1 DRIFT-REPORT 9-page Tier 1 ~10.5 hr bottom-up = ~5.8 hr calibrated) — Sprint 57.22 supersedes with comprehensive audit + Strict 1:1 ±2px bar

**Sprint 57.22 NEW carryovers (Phase 57.23+ expected)**:
- 🔴 **AD-Mockup-Full-Rebuild-Round-2** multi-sprint epic — 4 page groups (Auth ×5 + Operations ×9 + Governance ×4 + Chat-v2 Phase-2 ×N widgets) at Strict 1:1 ±2px bar; estimated total ~30-50 hr calibrated
- **AD-Sprint-Plan-NEW `frontend-mockup-strict-rebuild` 0.55-0.65 class proposal** — NEW calibration class for Strict 1:1 ±2px rebuild work (1st app Sprint 57.23+)
- Per-page sub-ADs (1 per audit unit with severity ≥ structural; ~15-20 expected)

---

## Out of Scope (Explicit)

- **Production code changes** — Sprint 57.22 produces audit + plan; Sprint 57.23+ executes rebuild
- **Backend changes** — pure frontend audit (any backend gap surfaced becomes Phase-2 carryover AD, not Sprint 57.22 deliverable)
- **PROP stub deep-audit** — PROP stubs (18 pages) get header-level audit only (page exists + ComingSoonPlaceholder renders + nav badge correct); full mockup capture deferred to first sprint that promotes the stub to active
- **AppShellV2 / Topbar / Sidebar re-audit** — Sprint 57.20 V3 grid rewrite considered baseline; only audit if Day 1/2 surface visible drift
- **Chat-v2 Phase-1 (Sprint 57.21 work) re-audit** — Turn Block Model + 3-col + Inspector frame considered Phase-1 baseline shipped; only audit Phase-2 widget gaps
- **Tailwind v4 config migration** (AD-Tailwind-v4-Config-Migration carryover) — separate track; not in audit scope
- **A11y structural nits** (AD-A11y-Structural-Nits carryover) — separate track; not in audit scope
- **Lighthouse hard-gate** (AD-Lighthouse-Visual-Hard-Gate carryover) — separate track; not in audit scope

---

## Definition of Sprint Complete

Sprint 57.22 is complete when:

1. AUDIT-REPORT-COMPREHENSIVE.md ≥ 800 lines exists at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/artifacts/mockup-fidelity-audit/AUDIT-REPORT-COMPREHENSIVE.md`
2. ~27 mockup screenshots + ~27 production screenshots saved at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/artifacts/mockup-fidelity-audit/screenshots/`
3. Priority matrix covers all 4 user-selected page groups (Auth + Operations + Governance + Chat-v2 Phase-2)
4. Sprint 57.23+ first-execution-sprint scope-class proposal documented
5. ZERO production code change verified via `git diff --stat main..HEAD`
6. Vitest 348/348 unchanged (no test touched)
7. pytest backend baseline unchanged
8. retrospective.md Q1-Q7 + memory snapshot + CLAUDE.md V2 status sync + sprint-workflow.md calibration matrix +1 row + SITUATION update
9. PR opens against main with all CI checks green (visual-regression unchanged baselines should PASS)
10. Anti-Pattern 11/11 PASS (audit sprint by definition has no Potemkin / LLM call / cross-directory scatter / sole-mutator violation potential)
