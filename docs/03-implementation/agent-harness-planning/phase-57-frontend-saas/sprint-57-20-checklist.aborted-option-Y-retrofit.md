# Sprint 57.20 — Checklist

**Plan**: `sprint-57-20-plan.md`
**Calibration**: NEW class `mockup-fidelity-retrofit` 0.55 (HYBRID weighted blend: cosmetic mechanical 0.45 ~40% + structural design 0.65 ~40% + closeout 0.80 ~20%) — bottom-up ~16.5 hr → calibrated commit ~9 hr (1st application; pending 2-3 sprint validation)
**Day count**: Day 0 (setup + 三-prong + Playwright pipeline) + Day 1-3 (Tier 1 retrofit) + Day 4 (Sprint 57.19 verification + closeout)
**Branch**: `feature/sprint-57-20-mockup-existing-pages-retrofit`

---

## Day 0 — Setup + 三-prong + Playwright MCP pipeline

### 0.1 Plan + checklist landed (this checklist)
- [x] Plan drafted at `sprint-57-20-plan.md` (10 top-level sections per Sprint 57.19 format consistency)
- [x] Checklist drafted at `sprint-57-20-checklist.md` (this file)
- [ ] User approval to proceed with Day 0 三-prong + Day 1 code

### 0.2 Branch + initial doc files
- [ ] **Create feature branch**: `git checkout -b feature/sprint-57-20-mockup-existing-pages-retrofit`
- [ ] **Create progress.md skeleton** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/progress.md` (Day 0 entry + Sprint 57.19 carryover notes from Q4)
- [ ] **Create screenshot artifact dir** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/artifacts/tier-1-retrofit/screenshots/{existing-pages,sprint-57-19-verification}/`

### 0.3 Day 0 三-prong scope verify (per sprint-workflow §Step 2.5)
- [ ] **Prong 1 (Path verify)**: confirm 5 Tier 1 page files exist at expected paths:
  - `src/pages/cost-dashboard/index.tsx` ✅ (Sprint 57.1)
  - `src/pages/chat-v2/index.tsx` + `src/features/chat-v2/` ✅ (Sprint 57.8)
  - `src/pages/memory/index.tsx` ✅ (Sprint 57.12)
  - `src/pages/verification/index.tsx` ✅ (Sprint 57.11)
  - `src/pages/governance/index.tsx` + 3 sub-routes ✅ (Sprint 57.9)
- [ ] **Prong 2 (Content verify)**: grep each Tier 1 page for `text-\[#` literal hex usage + inline `style=` usage + Sprint 57.18 semantic token adoption — record baseline per page in progress.md Day 0
- [ ] **Prong 3 (Schema verify)**: N/A this sprint (pure frontend, no DB schema work)
- [ ] **Catalog Day 0 drift findings** as D-PRE-1, D-PRE-2, ... in progress.md
- [ ] **Go/no-go decision**: if drift findings shift scope by ≤ 20% → proceed Day 1; if 20-50% → revise plan + checklist; if > 50% → abort + redraft

### 0.4 Playwright MCP pipeline (US-A1)
- [ ] **Verify dev server can boot**: `npm run dev` from `frontend/` — confirm port 3005 or 3007 listens
- [ ] **Verify mockup server can boot**: `cd reference/design-mockups && python -m http.server 8080` — confirm port 8080 listens + sidebar renders at http://localhost:8080/
- [ ] **Verify Playwright MCP browser_navigate + browser_take_screenshot tools** loadable via ToolSearch
- [ ] **Single-page pilot capture**: navigate Playwright MCP to /overview at 1440×900 → capture POST + mockup target → store at `sprint-57-19-verification/overview-{post,mockup}.png` → verify artifact size + visual sanity
- [ ] **Batch capture 5 Tier 1 POST + 5 mockup target pairs** at 1440×900:
  - `existing-pages/cost-dashboard-{post,mockup}.png`
  - `existing-pages/chat-v2-{post,mockup}.png`
  - `existing-pages/memory-{post,mockup}.png`
  - `existing-pages/verification-{post,mockup}.png`
  - `existing-pages/governance-{post,mockup}.png`
- [ ] **Batch capture 7 Sprint 57.19 output POST + 7 mockup target pairs** at 1440×900:
  - `sprint-57-19-verification/{overview,orchestrator,subagents,state-inspector}-{post,mockup}.png`
  - `sprint-57-19-verification/command-palette-{post,mockup}.png` (trigger via Cmd+K)
  - `sprint-57-19-verification/notifications-panel-{post,mockup}.png` (trigger via bell click)
  - `sprint-57-19-verification/user-menu-{post,mockup}.png` (trigger via avatar click)
- [ ] **Commit Day 0 artifacts**: `chore(sprint-57-20, Day 0): plan + checklist + 三-prong + Playwright MCP pipeline + screenshot triplets`

---

## Day 1 — US-B1 cost-dashboard structural retrofit + US-B5 governance hex sweep

### 1.1 US-B1 cost-dashboard widget redesign (~3 hr structural)
- [ ] **Read mockup analog**: `reference/design-mockups/page-platform.jsx` Cost section + `page-overview.jsx` cost-burn widget — extract widget vocabulary + layout grid + token usage
- [ ] **Side-by-side compare** with current `src/pages/cost-dashboard/index.tsx` — identify minimum structural diff to reach mockup parity
- [ ] **Redesign cost-burn widget**:
  - 30-day spend-vs-budget area chart with $4,200 budget marker line
  - recharts custom theming using Sprint 57.18 semantic tokens (`stroke-primary`/`fill-primary/16`/`stroke-warning` for budget marker)
  - Drop simple month-picker if not in mockup; OR retain if mockup has equivalent
  - i18n keys for new copy ("30-day spend vs $4,200 budget" / "projected $X,XXX" / "X% of budget")
- [ ] **Update / extend Vitest cases** at `tests/unit/pages/cost-dashboard/index.test.tsx`
- [ ] **Playwright MCP fidelity check**: capture POST-retrofit + diff vs mockup target → record verdict (parity / minor / structural-remaining) in FIDELITY-REPORT.md draft
- [ ] **Verify sanity**: `tsc --noEmit` 0 / Vitest related tests PASS / ESLint silent
- [ ] **Commit US-B1**: `feat(frontend-retrofit, sprint-57-20): /cost-dashboard mockup-fidelity widget redesign (US-B1)`

### 1.2 US-B5 governance literal hex → semantic tokens sweep (~1.5 hr cosmetic)
- [ ] **Grep governance for literal hex**: `grep -rn "text-\[#\|bg-\[#" src/pages/governance/ src/features/governance/` — record affected files + line counts
- [ ] **Mechanical substitution** per Sprint 57.18 semantic token map:
  - `#b71c1c` / `#dc2626` / `#ef4444` → `text-danger` (per token availability)
  - `#f59e0b` / `#fb923c` → `text-warning`
  - `#3b82f6` / `#0ea5e9` → `text-info`
  - `#22c55e` / `#16a34a` → `text-success`
  - Preserve `#b71c1c` literal where Sprint 57.15+57.16 sentinel test asserts (e.g. ApprovalCard CRITICAL color regression test) — document carve-out in MHist
- [ ] **Verify no test regression**: chat-v2 e2e approval-card CRITICAL sentinel still PASS (Sprint 57.15 D-DAY2-1 hotfix lineage)
- [ ] **Update affected file headers MHist +1 line each** per file-header-convention
- [ ] **Playwright MCP fidelity check**: capture POST-retrofit governance pages + diff vs mockup
- [ ] **Commit US-B5**: `refactor(frontend-retrofit, sprint-57-20): /governance literal hex → semantic tokens sweep (US-B5)`

### 1.3 Day 1 doc updates
- [ ] **Update progress.md** Day 1 entry with US-B1 + US-B5 actuals + drift findings (if any) + calibration partial

---

## Day 2 — US-B2 chat-v2 InputBar + MessageList polish

### 2.1 US-B2 chat-v2 structural retrofit (~3 hr structural)
- [ ] **Read mockup analog**: `reference/design-mockups/page-chat.jsx` — extract InputBar status pill layout + MessageList bubble styling + ToolCallCard collapsed-detail UX
- [ ] **Side-by-side compare** with current production `src/features/chat-v2/components/{InputBar,MessageList,ToolCallCard}.tsx` (post-Sprint 57.16 Round 2 inline-style cleanup + Sprint 57.17 ChatLayout AA cascade)
- [ ] **InputBar polish**:
  - Status pill layout (mockup uses specific position + sizing)
  - Mode toggle (echo_demo/real_llm) styling alignment
  - Send button styling alignment
- [ ] **MessageList polish**:
  - Bubble styling (border radius + padding + color tokens)
  - Role-based color tokens (user vs assistant vs tool)
- [ ] **ToolCallCard polish**:
  - Collapsed-detail UX (mockup may have specific expand/collapse interaction)
  - Tool name + args display alignment
- [ ] **Extend Vitest cases** at `tests/unit/features/chat-v2/` (preserve existing approval-card CRITICAL sentinel)
- [ ] **Playwright MCP fidelity check**: capture POST-retrofit /chat-v2 in 3 states (empty / mid-session / approval-card visible) + diff vs mockup
- [ ] **Verify sanity**: tsc 0 / Vitest related PASS / ESLint silent / approval-card sentinel PASS
- [ ] **Commit US-B2**: `feat(frontend-retrofit, sprint-57-20): /chat-v2 InputBar + MessageList + ToolCallCard mockup-fidelity polish (US-B2)`

### 2.2 Day 2 doc updates
- [ ] **Update progress.md** Day 2 entry with US-B2 actuals + drift findings

---

## Day 3 — US-B3 memory matrix view + US-B4 verification timeline UX

### 3.1 US-B3 memory matrix view rewrite (~2 hr structural)
- [ ] **Read mockup analog**: `reference/design-mockups/page-extras.jsx` Memory section — extract 5-scope × 3-time-scale matrix vocabulary
- [ ] **Replace current list view** with matrix view:
  - 5 scopes (system / tenant / role / user / session)
  - 3 time scales (永久 / 季 / 天) per scope
  - 15 cells (or per mockup grid)
  - Per-cell: count + recent-activity indicator + click-through to scope detail
- [ ] **NEW component** (likely `src/features/memory/components/MemoryMatrix.tsx`) — encapsulate matrix layout
- [ ] **i18n keys** for new copy (scope labels + time-scale labels + empty-state)
- [ ] **NEW Vitest** at `tests/unit/pages/memory/MatrixView.test.tsx` (5+ cases: render / 15 cells / click-through / empty / loading)
- [ ] **Playwright MCP fidelity check**: capture POST-retrofit /memory + diff
- [ ] **Commit US-B3**: `feat(frontend-retrofit, sprint-57-20): /memory 5-scope × 3-time matrix view (US-B3)`

### 3.2 US-B4 verification correction-trace timeline UX (~2 hr structural)
- [ ] **Read mockup analog**: `reference/design-mockups/page-extras.jsx` Verification section — extract correction-trace timeline + LLM-judge verdict card
- [ ] **Add timeline view** to current production /verification:
  - Per-correction event card (timestamp + trigger + outcome)
  - LLM-judge verdict card (verdict + confidence + reasoning excerpt)
  - Visual timeline thread connecting events
- [ ] **Preserve existing tabs**: "Recent" / "Correction Trace" (Sprint 57.13 i18n confirmed already there)
- [ ] **NEW component** (likely `src/features/verification/components/CorrectionTimeline.tsx`)
- [ ] **i18n keys** for new copy
- [ ] **NEW Vitest** at `tests/unit/pages/verification/Timeline.test.tsx` (5+ cases)
- [ ] **Playwright MCP fidelity check**
- [ ] **Commit US-B4**: `feat(frontend-retrofit, sprint-57-20): /verification correction-trace timeline UX (US-B4)`

### 3.3 Day 3 doc updates
- [ ] **Update progress.md** Day 3 entry with US-B3 + US-B4 actuals

---

## Day 4 — US-C1 Sprint 57.19 runtime verification + US-D1 Closeout

### 4.1 US-C1 Sprint 57.19 7-output runtime visual fidelity verification (~1 hr)
- [ ] **Re-capture Sprint 57.19 7 outputs** (in case retrofit work shifted layout — unlikely but verify): /overview + /orchestrator + /subagents + /state-inspector + CommandPalette open + NotificationsPanel open + UserMenu open
- [ ] **Pair-by-pair diff vs mockup target** (already captured Day 0):
  - For each output: classify diff as **parity** / **minor cosmetic** / **structural remaining** / **functional drift**
  - Record per-output verdict + diff details
- [ ] **FIDELITY-REPORT.md write-up** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/artifacts/tier-1-retrofit/FIDELITY-REPORT.md`:
  - Header: scope (5 retrofit pages + 7 Sprint 57.19 outputs) + methodology + Sprint 57.20 US-C1 verdict
  - Part A: 5 retrofit pages pair-by-pair (PRE-retrofit code-level state from Day 0 三-prong + POST-retrofit screenshot + mockup target + diff verdict + remaining-drift list)
  - Part B: 7 Sprint 57.19 outputs pair-by-pair (POST-Sprint-57.19 screenshot + mockup target + diff verdict + remaining-drift list)
  - Summary table: per-output diff classification + total remaining-drift hours for Sprint 57.21+
  - Cross-references to all screenshot artifact paths
- [ ] **Commit US-C1**: `docs(audit, sprint-57-20): Sprint 57.19 7-output runtime visual verification + FIDELITY-REPORT.md (US-C1)`

### 4.2 Validation sweep
- [ ] **Full Vitest**: `npm run test` → expect ~277+N PASS (Sprint 57.19 baseline 277 + ~10-20 NEW for retrofit pages; 0 regression)
- [ ] **tsc --noEmit**: 0 errors
- [ ] **ESLint**: silent (or document any new suppressions)
- [ ] **Build**: `npm run build` → main bundle delta documented (expect +5-15 kB from widget rebuilds; recharts theming may add up to +20 kB)
- [ ] **Backend pytest baseline preserved** (pure frontend sprint — verify `git diff --stat main..HEAD -- backend/` = 0 lines)
- [ ] 🚧 **Full e2e** (`npm run e2e`) — **DEFER if not needed** (per Sprint 57.19 pattern); decide at Day 4
- [ ] 🚧 **Axe a11y scan** — defer to Sprint 57.21+ if no new a11y violations introduced

### 4.3 In-sprint doc syncs (per US-D1 AC)
- [ ] **Edit `.claude/rules/sprint-workflow.md`** — Calibration matrix +1 row `mockup-fidelity-retrofit` 0.55 HYBRID (cosmetic 0.45 + structural 0.65 + closeout 0.80) — ratio recorded post-Day 4 retrospective Q2 + MHist +1 line
- [ ] **Edit `design/operator-portal/INTEGRATION-LOG.md`** — 5 rows Status update (cost-dashboard / chat-v2 / memory / verification / governance retrofit complete)
- [ ] 🚧 **Edit `docs/03-implementation/agent-harness-planning/16-frontend-design.md`** — DEFER to `chore/closeout-57-20` PR (Sprint 57.18+19 pattern)
- [ ] 🚧 **Edit `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md`** — DEFER to closeout PR

### 4.4 US-D1 Closeout (commits + retrospective + memory)
- [ ] **NEW retrospective.md** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-20/retrospective.md` (Q1-Q7 per sprint-workflow.md):
  - Q1 What went well
  - Q2 Calibration ratio (`actual/committed` for `mockup-fidelity-retrofit` 0.55 1st app — record from Day 0-4 progress.md actuals)
  - Q3 Reality Check dual scoring (code: lint+build+test+pytest; runtime: 12 Playwright MCP pair verdicts in FIDELITY-REPORT.md)
  - Q4 Follow-up ADs (Tier 2 retrofit candidates / Sprint 57.19 remaining-drift / FIDELITY-REPORT remaining-drift items / etc.)
  - Q5 Next sprint candidates (per Rolling Planning — list only, no draft)
  - Q6 What to improve next sprint
  - Q7 Anti-pattern 11 self-check
- [ ] **NEW memory snapshot** at `memory/project_phase57_20_existing_pages_retrofit_tier1.md`
- [ ] **Edit `memory/MEMORY.md`** — +1 row at top for Sprint 57.20
- [ ] **Commit Day 4 closeout**: `chore(sprint-57-20, Day 4): retrospective + memory snapshot + 2 in-sprint doc syncs`

### 4.5 PR + closeout
- [ ] 🚧 **Push branch + Open PR + CI + Merge** — PENDING user authorization per CLAUDE.md「Confirmation on Destructive Only」: `git push` requires explicit confirmation
- [ ] 🚧 **`chore/closeout-57-20` PR** — defer post-merge (Sprint 57.18+19 pattern)

---

## Carryover for Sprint 57.21+

(Each item per Rolling Planning 紀律: log here for next sprint plan-draft consideration; do NOT pre-write 57.21 plan tasks.)

### Tier 2 retrofit (~5.5 hr) — Sprint 57.21+ candidate
- `/admin/tenants` list cosmetic (~1.5 hr)
- `/admin/tenants/{id}/settings` structural sections (~2 hr)
- `/sla-dashboard` grid alignment (~2 hr)

### Tier 3 (covered by Round 3 Auth 4 epic) — Sprint 57.22+ candidate
- `/auth/login` cosmetic (~1 hr) + functional drift covered by AD-Mockup-Page-X-Port-Round-3 epic

### Sprint 57.19 carryover ADs (10 NEW; still pending)
- Backend wire bundle (5 ADs): Subagent-RealList-Phase58 / Loop-Session-Enrich-Phase58 / Overview-Backend-Wire / Orchestrator-Backend-Wire / State-VersionChain-Phase58
- Topbar backend feeds (3 ADs): CommandPalette-Backend-Wire / NotificationsPanel-Backend-Feed / UserMenu-Tenant-Switch
- AD-Sprint-Plan-NEW-mockup-port-class (after 2-3 sprint validation propose 0.60→0.40)

### Other open carryover (from Sprint 57.17/57.18)
- AD-Tailwind-v4-Config-Migration (~6-8 hr standalone candidate)
- AD-CI-7-GHA-PR-Permission
- AD-Lighthouse-Visual-Hard-Gate (post-retrofit baselines stable)
- AD-A11y-Structural-Nits

### Remaining-drift from FIDELITY-REPORT.md (Sprint 57.20 output)
- TBD per Day 4 US-C1 output — items classified as "structural-remaining" or "functional-drift" feed Sprint 57.21+ scope

---

**Sprint 57.20 checklist drafted. Awaiting user approval for Day 0 三-prong start.**
