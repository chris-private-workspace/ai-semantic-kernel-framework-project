---
sprint: 57.20
phase: Phase 57+ Frontend SaaS 17/N (pending close)
title: AD-Mockup-Existing-Pages-Retrofit Tier 1 + Sprint 57.19 Runtime Visual Verification
class: mockup-fidelity-retrofit (NEW 0.55 1st application; HYBRID weighted blend)
duration_days: 4-5 (Day 0 setup + Day 1-3 retrofit + Day 4 verification + closeout)
related:
  - Sprint 57.19 retrospective Q4 (10 NEW carryover ADs; TOP = AD-Mockup-Existing-Pages-Retrofit per user 2026-05-17 directive)
  - docs/03-implementation/agent-harness-execution/phase-57/sprint-57-19/artifacts/existing-pages-drift-audit/DRIFT-REPORT.md (Tier 1 ~10.5 hr ground truth)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17 directive)
  - .claude/rules/sprint-workflow.md calibration matrix
---

# Sprint 57.20 — AD-Mockup-Existing-Pages-Retrofit Tier 1 + Sprint 57.19 Runtime Visual Verification

## Sprint Goal

Close two related fidelity gaps for Phase 57+ Frontend SaaS in one focused sprint:

1. **Retrofit 5 Tier 1 existing ship pages** (cost-dashboard / chat-v2 / memory / verification / governance) to mockup parity per `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-19/artifacts/existing-pages-drift-audit/DRIFT-REPORT.md` Tier 1 prioritization (~10.5 hr bottom-up).

2. **Verify Sprint 57.19's 7 mockup-port outputs (4 Operations pages + 3 Topbar overlays) at runtime** via Playwright MCP screenshot pair capture against mockup target — closing the L3 verification gap deferred from Sprint 57.19 per Sprint 57.5 dual-scoring framework.

Both objectives serve the same user 2026-05-17 hard directive: **「最最最基本是要完全按照mockup的版本去實作」**.

## Background

### 為什麼這個 sprint 存在（per Sprint 57.19 retrospective Q4 + Q5 + user 2026-05-17 hard directive）

Sprint 57.19 shipped Operations 4 + Topbar 3 mockup ports at code-level mockup-fidelity, but **runtime visual fidelity was deferred** per Sprint 57.5 dual-scoring (code-level audit serves SCOPE; runtime verification belongs in EXECUTION sprint). At the same time, Sprint 57.19 US-F1 produced a `DRIFT-REPORT.md` cataloguing 9 existing ship pages (Sprint 57.1-57.12) with known drift from mockup, totaling ~17.5-18 hr Tier 1+2+3 work.

Sprint 57.19 retrospective Q5 + user 2026-05-17 「100% mockup-fidelity」 directive together identify Sprint 57.20 = TOP candidate = AD-Mockup-Existing-Pages-Retrofit Tier 1 (~5.8 hr calibrated commit). User selected **Option A** on 2026-05-17 post-Sprint-57.19-merge: 先校準既有 9 頁 + 補 runtime verification.

### 為什麼 Tier 1 only (vs Tier 1+2)

Per DRIFT-REPORT.md §Sprint 57.20 Scope Recommendation:
- **Tier 1 (~10.5 hr)**: cost-dashboard (3 hr structural) + chat-v2 (3 hr structural) + memory (2 hr structural) + verification (2 hr structural) + governance (1.5 hr cosmetic) — highest user-visible value
- Tier 2 (~5.5 hr): admin/tenants list + tenant-settings + sla-dashboard → Sprint 57.21+
- Tier 3 (~1 hr cosmetic + Round 3 functional) → folds into AD-Mockup-Page-X-Port-Round-3 multi-sprint epic

Tier 1 calibrated at NEW class `mockup-fidelity-retrofit` 0.55 = ~5.8 hr committed; adding Playwright MCP pipeline (US-A1) + Sprint 57.19 runtime verification (US-C1) + closeout (US-D1) brings sprint commit to ~9 hr.

### 17.md / V2 紀律對齊

- **約束 1（單一範疇歸屬）**: 純 frontend sprint;每個 retrofit 涉及的 page features 已對應 Cat 1/3/7/8/9/11/12 read facades from Sprint 57.19 NEW features layer.
- **約束 2（主流量驗證）**: Tier 1 pages 都在 UnifiedChat-V2 + AppShellV2 主流量內;runtime visual verification 直接證明.
- **約束 3（LLM Provider Neutrality）**: frontend 無 SDK import;preserved.
- **約束 4（Anti-Pattern checklist）**: 每個 PR commit 必須通過 11 條 self-check;特別關注 AP-4 Potemkin Features（每 retrofit 必須是 real fidelity gain，不是 token rename）+ AP-2 Phantom code（runtime verification screenshot 必須 reproducibly captured，不可宣稱 verified without artifact）.
- **約束 5（測試優先）**: Vitest baseline preserved（277/277）;新增 Vitest cases per retrofit page；Playwright MCP fidelity verdict recorded as audit artifact.

## User Stories

### Group A — Playwright MCP Pipeline + 9-page Triplet Capture (US-A1) — Day 0

**US-A1**: As a Sprint 57.20 retrofit owner, I want a reproducible Playwright MCP screenshot pipeline that captures 9 page triplets (PRE-brand baseline / POST-brand production / mockup target) at 1440×900 viewport so that all retrofit work has visual ground truth artifacts AND Sprint 57.19's 7 mockup-port outputs get runtime visual fidelity verification.

**Why**: This is the artifact infrastructure for both Group B retrofit (need PRE/POST/target triplets for each Tier 1 page) AND Group C verification (need POST/target pairs for Sprint 57.19 7 outputs). Spin-up cost (~30-45 min for dev server + mockup http.server) amortizes across all Day 1-4 work.

### Group B — Tier 1 Existing Pages Retrofit (US-B1 + US-B2 + US-B3 + US-B4 + US-B5) — Day 1-3

**US-B1** (Day 1, ~3 hr structural — cost-dashboard widget redesign): As an operator viewing cost burn, I want the production `/cost-dashboard` to render mockup's 30-day spend-vs-budget area chart with $4,200 budget marker line + recharts palette aligned to mockup tokens (NOT recharts default).
- Mockup analog: `page-platform.jsx` Cost section + `page-overview.jsx` cost-burn widget
- Current state: simple month-picker + KPI cards
- Drift class: Structural (widget redesign)

**US-B2** (Day 2, ~3 hr structural — chat-v2 InputBar + MessageList polish): As an operator using chat-v2, I want InputBar status pill layout + MessageList bubble styling + ToolCallCard collapsed-detail UX to match mockup `page-chat.jsx` canonical reference.
- Mockup analog: `page-chat.jsx`
- Current state: Sprint 57.17 hotfix verified AppShellV2 + Cards + dropdown; InputBar layout + MessageList bubble + ToolCallCard need mockup-fidelity polish
- Drift class: Structural

**US-B3** (Day 3, ~2 hr structural — memory matrix view): As an operator browsing memory layers, I want `/memory` to render a 5-scope × 3-time-scale matrix view matching mockup `page-extras.jsx` Memory section (NOT the current simpler list view).
- Mockup analog: `page-extras.jsx` Memory section
- Current state: Sprint 57.12 ship; pre-mockup-integration list view
- Drift class: Structural (matrix UX)

**US-B4** (Day 3, ~2 hr structural — verification timeline UX): As an operator reviewing verification corrections, I want `/verification` to render a correction-trace timeline + LLM-judge verdict card per mockup `page-extras.jsx` Verification section.
- Mockup analog: `page-extras.jsx` Verification section
- Current state: Sprint 57.11 ship; tabs OK but lacks timeline UX
- Drift class: Structural

**US-B5** (Day 1 batch with US-B1 OR Day 3 batch with US-B3/B4, ~1.5 hr cosmetic — governance literal hex → semantic tokens sweep): As a maintainer of governance UI, I want the 4 governance routes (approvals / redaction / error-policy / audit-log) to use Sprint 57.18 semantic tokens (`text-danger` / `text-warning` / `text-info` / `text-success`) instead of literal `text-[#hex]` from pre-Sprint-57.18 ship code.
- Mockup analog: `page-governance.jsx`
- Current state: Sprint 57.9 + Sprint 57.15 inline-style sweep — vocabulary partially aligned
- Drift class: Cosmetic (mechanical token substitution)

### Group C — Sprint 57.19 7-output Runtime Visual Fidelity Verification (US-C1) — Day 4

**US-C1**: As a Sprint 57.19 author closing the L3 verification gap, I want Playwright MCP screenshot pairs (production POST-Sprint-57.19 / mockup target) for the 4 Operations pages + 3 Topbar overlays so that Sprint 57.19's mockup-fidelity claim is verified at runtime (not just code-level), per Sprint 57.5 dual-scoring framework.

7 outputs to verify:
- `/overview`, `/orchestrator`, `/subagents`, `/state-inspector` (page captures)
- CommandPalette ⌘K modal (via Cmd+K → captured open state)
- NotificationsPanel (via bell click → captured open state)
- UserMenu extended (via avatar click → captured open state)

### Group D — Closeout (US-D1) — Day 4

**US-D1**: As a Sprint 57.20 owner, I want commits + retrospective.md + memory snapshot + in-sprint doc syncs landed so that Sprint 57.20 = COMPLETE and Phase 57+ Frontend 17/N opens cleanly.

## Technical Specifications

### Playwright MCP screenshot pipeline (US-A1)

```bash
# Pre-flight: spin up dev server + mockup http.server in 2 background terminals
cd frontend && npm run dev &  # serves on :3005 or :3007
cd reference/design-mockups && python -m http.server 8080 &

# Capture pipeline (driven via Playwright MCP tool):
# - viewport: 1440×900
# - format: PNG full-page
# - artifact dir: docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/artifacts/tier-1-retrofit/screenshots/
#   - existing-pages/{cost-dashboard,chat-v2,memory,verification,governance}-{pre,post,mockup}.png
#   - sprint-57-19-verification/{overview,orchestrator,subagents,state-inspector,command-palette,notifications-panel,user-menu}-{post,mockup}.png
```

PRE-brand baselines for 9 existing pages: Sprint 57.18 had brand color = dark slate (pre-US-A1). Sprint 57.19 US-A1 already flipped to indigo. Therefore PRE-brand captures = synthetic (revert brand temporarily OR document "PRE-brand reference: Sprint 57.18 main HEAD `b5dc8a17` rendering — visually similar in layout, differs only in primary color"). Decision: skip synthetic PRE-brand capture; POST-brand is the current production reality + mockup is the target.

### Tier 1 retrofit pattern (US-B1-B5)

For each page:
1. Read mockup analog (e.g. `reference/design-mockups/page-platform.jsx`) — extract widget vocabulary + layout grid + token usage
2. Side-by-side compare with current production `src/pages/<id>/index.tsx` (or feature components)
3. Identify minimum diff to reach mockup parity (NOT a full rewrite if cosmetic; full structural rebuild if widget layout differs)
4. Use Sprint 57.18 semantic tokens (success/warning/danger/thinking/tool/memory/info) + 4 risk levels — NOT literal hex
5. Vitest cases for new structural elements; preserve existing test coverage
6. Playwright MCP fidelity check after each page commit (capture POST + diff vs mockup target)

### Calibration class

**NEW class `mockup-fidelity-retrofit`** 0.55 1st application — HYBRID weighted blend per DRIFT-REPORT.md proposal:

| Component | Class | Weight |
|-----------|-------|--------|
| Cosmetic mechanical refactor (US-B5 governance hex sweep + minor color/padding) | 0.45 | 40% |
| Structural design (US-B1/B2/B3/B4 widget rebuild + matrix view + timeline UX) | 0.65 | 40% |
| Closeout (commits + retrospective + doc syncs + PR) | 0.80 | 20% |

Mid-band: **0.55** (1st application — pending 2-3 sprint validation per `When to adjust` rule)

Differs from `frontend-refactor-mechanical` 0.50/0.80 because retrofit requires DESIGN decision per widget (which tokens / which Tailwind class / which structural pattern matches mockup), not just mechanical class substitution.

### Bottom-up estimate per US

| US | Scope | Hours |
|----|-------|-------|
| US-A1 | Playwright MCP pipeline + dev+mockup server setup + 9-page POST-brand capture + 9-page mockup target capture | ~2 |
| US-B1 | cost-dashboard widget redesign (cost-burn line chart + budget marker) | ~3 |
| US-B2 | chat-v2 InputBar + MessageList + ToolCallCard polish | ~3 |
| US-B3 | memory 5-scope × 3-time matrix view rewrite | ~2 |
| US-B4 | verification correction-trace timeline UX | ~2 |
| US-B5 | governance literal hex → semantic tokens sweep (4 sub-routes) | ~1.5 |
| US-C1 | Sprint 57.19 7-output runtime visual fidelity verification + diff report | ~1 |
| US-D1 | Closeout (commits + retrospective + memory + 3 doc syncs + PR + closeout PR) | ~2 |
| **TOTAL** | | **~16.5 hr bottom-up** |

### Calibrated commit

`16.5 hr × 0.55 = ~9 hr calibrated commit` (1.5-2 day sprint at solo-dev pace; ~ same Day count as Sprint 57.19 `mockup-page-port-with-backend-pairing-and-audit` 18.5 hr / 6 days = ~3.1 hr/day equivalent)

## File Change List

### MODIFIED Frontend — src (5 page files + N feature components, ~+800 lines net)
- `src/pages/cost-dashboard/index.tsx` (US-B1 widget redesign)
- `src/pages/chat-v2/index.tsx` + `src/features/chat-v2/components/{InputBar,MessageList,ToolCallCard}.tsx` (US-B2)
- `src/pages/memory/index.tsx` + `src/features/memory/components/*` (US-B3 matrix view)
- `src/pages/verification/index.tsx` + `src/features/verification/components/*` (US-B4 timeline)
- `src/pages/governance/*` + `src/features/governance/components/{ApprovalList,ApprovalCard}.tsx` (US-B5 hex sweep)

### NEW Frontend — src (potentially 3-5 new sub-components if widget rebuild needs encapsulation)
- TBD per US-B1-B4 design pass (cost-burn chart / memory matrix cell / verification timeline event card / etc.)

### MODIFIED Frontend — i18n (2 files)
- `src/i18n/locales/en/common.json` + `src/i18n/locales/zh-TW/common.json` (additional keys for retrofitted UX elements)

### NEW Frontend — tests (~+5-10 Vitest cases per retrofitted page)
- `tests/unit/pages/cost-dashboard/*.test.tsx` (extend existing)
- `tests/unit/pages/chat-v2/*.test.tsx` (extend existing)
- `tests/unit/pages/memory/MatrixView.test.tsx` (NEW)
- `tests/unit/pages/verification/Timeline.test.tsx` (NEW)
- `tests/unit/pages/governance/*.test.tsx` (extend existing)

### NEW Audit artifacts
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/artifacts/tier-1-retrofit/screenshots/existing-pages/*.png` (5 POST + 5 mockup pairs)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/artifacts/tier-1-retrofit/screenshots/sprint-57-19-verification/*.png` (7 POST + 7 mockup pairs)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/artifacts/tier-1-retrofit/FIDELITY-REPORT.md` (final pair-by-pair fidelity verdict + diff classification + remaining-drift list for Sprint 57.21+)

### NOT touched (intentional scope hold)
- Backend (`backend/`) — pure frontend sprint; backend baseline preserved
- Sprint 57.18 routes.config / Sidebar / AppShellV2 / topbar overlays (Sprint 57.19 deliverables stable)
- Tier 2 pages (admin/tenants list / tenant-settings / sla-dashboard) — Sprint 57.21+
- Tier 3 (auth/login functional drift) — folds into AD-Mockup-Page-X-Port-Round-3 multi-sprint epic
- Backend wire ADs (10 NEW Sprint 57.19 carryover) — orthogonal; Sprint 57.21+

### Doc syncs (in-sprint)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/artifacts/tier-1-retrofit/FIDELITY-REPORT.md` (NEW)
- `.claude/rules/sprint-workflow.md` calibration matrix +1 row `mockup-fidelity-retrofit` 0.55 1st app + MHist
- `design/operator-portal/INTEGRATION-LOG.md` 5 rows Status update (existing pages retrofit complete)

### Doc syncs (deferred post-merge via `chore/closeout-57-20` PR)
- `CLAUDE.md` Phase 16/N → 17/N + Latest/Prev Sprint shift + main HEAD + Next Phase 候選 update
- `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八 carryover update
- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` Sprint Timeline +1 row (Sprint 57.20 retrofit)
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` REST surface (deferred Sprint 57.19 carryover; ship if scope allows)

## Acceptance Criteria

### Functional
1. ✅ 5 Tier 1 pages render mockup-fidelity content (visual + functional + i18n axes)
2. ✅ Sprint 57.19 7 outputs (4 Operations + 3 Topbar overlays) have runtime visual fidelity diff documented per output in FIDELITY-REPORT.md
3. ✅ Vitest baseline preserved (Sprint 57.19 baseline 277 + N NEW; 0 regression)
4. ✅ Existing functional tests still pass for retrofitted pages (no breaking change to data flow / event handlers)

### Non-functional
1. ✅ tsc --noEmit: 0 errors
2. ✅ ESLint silent (or only suppressed with documented reason)
3. ✅ Build: main bundle delta ≤ +20 kB (retrofit is mostly Tailwind class changes; widget rebuilds may add 5-10 kB)
4. ✅ Backend pytest baseline preserved (pure frontend sprint)
5. ✅ LLM SDK leak: 0 (`agent_harness/` neutrality intact)
6. ✅ Anti-pattern 11/11 PASS per PR

### Sprint workflow discipline
1. ✅ Plan + checklist exist BEFORE code (this plan = Step 1)
2. ✅ Day 0 三-prong scope verify (per Sprint-workflow §Step 2.5)
3. ✅ Per-day actuals in progress.md, NOT in checklist (per Sprint 53.7 AD-Lint-2)
4. ✅ Unchecked `[ ]` items preserved as `[x] 🚧 deferred + reason` per sacred rule
5. ✅ Rolling planning: NO pre-draft of Sprint 57.21 plan

### V2 Anti-pattern 11 項 self-check (each commit + PR)
- AP-1 not applicable (pure UI sprint)
- AP-2 phantom code avoided — all retrofit work has Playwright MCP visual diff artifact
- AP-3 LLM SDK leak: 0
- AP-4 Potemkin avoided — each retrofit must produce visible fidelity gain (NOT token rename or class shuffle with same render)
- AP-5/6/7/8/9/10/11 N/A or PASS

## Deliverables (checklist mapping)

- [ ] US-A1 Playwright MCP pipeline + 9 page triplet captures (Day 0)
- [ ] US-B1 cost-dashboard widget redesign (Day 1)
- [ ] US-B2 chat-v2 InputBar + MessageList polish (Day 2)
- [ ] US-B3 memory matrix view (Day 3)
- [ ] US-B4 verification timeline UX (Day 3)
- [ ] US-B5 governance literal hex → tokens sweep (Day 1 batch with B1 OR Day 3 batch with B3/B4)
- [ ] US-C1 Sprint 57.19 7-output runtime visual verification (Day 4)
- [ ] US-D1 Closeout (Day 4) — commits + retrospective + memory + 3 in-sprint doc syncs + PR + closeout PR

## Dependencies & Risks

### Dependencies
- Sprint 57.19 ports already merged into main `24d554f6` (closeout `23e61603`) ✅
- DRIFT-REPORT.md serves as ground truth for Tier 1 scope (Sprint 57.19 US-F1 output) ✅
- Sprint 57.18 semantic tokens (`success`/`warning`/`danger`/`thinking`/`tool`/`memory`/`info` + 4 risk levels) already in `tailwind.config.ts` ✅

### Risks (per `.claude/rules/sprint-workflow.md` Common Risk Classes)
- **Risk A (Playwright MCP pipeline reliability)**: dev server boot + mockup http.server + Playwright MCP all need to coordinate. If any spin-up flake → US-A1 budget overruns → US-B/C/D cascade. Mitigation: Day 0 validate pipeline with single page (e.g. /overview) before batch capture.
- **Risk B (mockup-fidelity ambiguity)**: 5 retrofit pages each have multiple mockup interpretation choices (e.g. cost-burn chart could be line/area/bar; memory matrix could be 5×3 grid or 15-card stack). Mitigation: read mockup source as canonical reference; if interpretation conflict, default to most explicit mockup vocabulary.
- **Risk C (recharts vs mockup palette)**: cost-dashboard widget redesign needs recharts custom theming. Mitigation: use Sprint 57.18 semantic tokens for chart colors; document if recharts requires escape-hatch literal hex.
- **Risk D (POST-brand vs PRE-brand baseline)**: Sprint 57.19 US-A1 already shipped brand indigo, so PRE-brand baseline = Sprint 57.18 main HEAD `b5dc8a17` (synthetic). Mitigation: skip PRE-brand capture; document POST vs mockup directly.

## Workload (calibrated)

> Bottom-up est ~16.5 hr → calibrated commit ~9 hr (multiplier 0.55)

Per `.claude/rules/sprint-workflow.md` §Workload Calibration:
- **X = 16.5 hr** (sum of US-A1 + US-B1-B5 + US-C1 + US-D1 bottom-up)
- **Z = 0.55** (NEW class `mockup-fidelity-retrofit` mid-band — 1st application)
- **Y = X × Z = ~9 hr calibrated commit**

If Day 4 retrospective Q2 ratio outside [0.85, 1.20]:
- < 0.7 → AD-Sprint-Plan-N propose 0.55 → 0.40 (bottom-up too generous;遵循 Sprint 57.19 NEW class pattern)
- > 1.2 → AD-Sprint-Plan-N propose 0.55 → 0.70 (under-estimating)
- single data-point insufficient; 3-sprint window per `When to adjust` rule

## Open questions for user

1. **PRE-brand baseline capture**: skip synthetic capture (default A); OR temporarily revert brand to capture PRE-brand reality (~20 min extra cost). **Default A** unless user says otherwise.

2. **US-B5 placement**: bundle with Day 1 (US-B1 cost-dashboard) for mechanical batch; OR bundle with Day 3 (US-B3+B4 structural mix) for context-load reduction on Day 1. **Default Day 1** (early mechanical close to free Day 3 for hard structural).

3. **Sprint 57.19 6 visual-regression baseline routes**: regenerate via `gh workflow run playwright-e2e.yml` after retrofit lands? Default = YES Day 4 closeout (baselines will be stale otherwise). User confirm?

4. **Closeout-PR scope**: stick to Sprint 57.19 pattern (CLAUDE.md + SITUATION only)? Or expand to include 16-frontend-design.md + 17-cross-category-interfaces.md REST surface (Sprint 57.19 carryover)? **Default Sprint 57.19 pattern** (CLAUDE.md + SITUATION only; 16/17.md kept as defer-forward).

---

**Sprint 57.20 plan COMPLETE.** Awaiting user review + checklist draft + Day 0 三-prong + Day 1 code start.
