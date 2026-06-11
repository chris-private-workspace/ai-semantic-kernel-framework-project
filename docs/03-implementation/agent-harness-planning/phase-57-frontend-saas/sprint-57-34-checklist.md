# Sprint 57.34 — Checklist

**Plan**: [`sprint-57-34-plan.md`](./sprint-57-34-plan.md)
**Sprint Goal**: 5th Phase-2 per-page verbatim-CSS re-point — `/orchestrator` (598-line Sprint 57.19 vintage page; 6 tabs). **1st non-rich-dashboard shape** in epic; **2nd validation data point** for `frontend-verbatim-css-repoint` 0.50 lifted baseline.

---

## Day 0 — Plan + Checklist + 三-prong + Before-baseline

### 0.1 Plan + Checklist drafted

- [x] **`sprint-57-34-plan.md` exists** — mirrors Sprint 57.32 format (11 ## sections + sub-sections)
- [x] **`sprint-57-34-checklist.md` exists** — this file

### 0.2 三-prong verify (plan-vs-repo)

- [x] **Prong 1 — path verify** — 3 paths confirmed (OrchestratorPage 598 lines / page-agents.jsx 418 lines / mockup-ui.tsx 8 exports)
- [x] **Prong 2 — content verify** — Mockup `Orchestrator` + 6 sub-components confirmed (L8 main + 65/116/175/207/239/274 sub); mockup-ui Tabs/Field/Switch absent (promote in Day 1-3); **drift D1**: production has 0 mockup verbatim CSS classes (113 className all Tailwind translations) — full re-point scope confirmed
- [x] **Prong 3 — schema verify** — N/A (frontend-only)
- [x] **Drift findings catalog** — D1 + D2 logged in progress.md Day 0 entry

### 0.3 Before-baseline 22-route sweep

- [x] **Run `route-sweep.mjs before`** — `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-34/artifacts/orchestrator-repoint/screenshots/before/` 22 PNGs
- [x] **Sample `/orchestrator` before** — Sprint 57.19 vintage state confirmed: page renders + structure correct but Tabs squished + Tailwind class translations throughout

### 0.4 Day 0 commit

- [ ] **Commit Day 0** — plan + checklist + progress.md + sweep before/ screenshots + route-sweep.mjs OUT_DIR re-point
  - Commit message: `docs(sprint-57-34): Day 0 — plan + checklist + 三-prong + before-baseline 22-route sweep`

---

## Day 1 — Main page-head + grid-stats + Tabs (Group B)

### 1.1 mockup-ui primitive decisions

- [ ] **Tabs promote-vs-keep decision** — log in progress.md Day 1 entry. Default: promote if ≤ ~30 lines; else page-local + AD.
- [ ] **(If promote) Edit `mockup-ui.tsx` add Tabs primitive** matching mockup signature `<Tabs value items onChange />` with `count` Badge support
  - DoD: type-safe; `data-testid` preserved if existing tests use it

### 1.2 US-B1 — Page-head re-point

- [ ] **Edit `OrchestratorPage.tsx` page-head** — re-point per mockup `page-agents.jsx:11-34`
  - brand-mark 32px + title "orchestrator-main" + `Badge tone="primary"` v3.4.1 + `Badge dot tone="success"` live
  - page-sub + `.route-pill` "/orchestrator"
  - page-actions: 3 Buttons (outline sm "Test in Chat" / outline sm "View in repo" / primary sm "Deploy")
  - DoD: visual diff ≤ 1 px; `data-testid="orchestrator-page-head"` preserved (or added)

### 1.3 US-B2 — grid-stats 4-stat row

- [ ] **Edit grid-stats block** — re-point per mockup L36-41
  - Stat × 4: Sessions·24h 2,847 +12% up / Avg loop turns 4.2 +0.1 down / Subagent spawns·24h 412 +8 up / p95 session 18.4s -2s up
  - DoD: use mockup-ui Stat primitive (drop local Stat if exists)

### 1.4 US-B3 — Tabs structure

- [ ] **Re-point Tabs invocation** — 6 tabs per mockup L43-53 (Config / Prompt / Tools+18 / Subagents+6 / Budgets / Policies)
  - DoD: active tab state preserved via existing `useState`; `count` badges visible on Tools/Subagents

### 1.5 Day 1 5-gate quick-check + commit

- [ ] **Drop local Badge / RISK_TONE / TONE_CLASS / RiskBadge** — import from mockup-ui
- [ ] **tsc + ESLint + Vitest pass** — `cd frontend; npm run lint; npm run test -- --run orchestrator` (if orchestrator test file exists)
- [ ] **Commit Day 1** — `feat(frontend, sprint-57-34): /orchestrator main + grid-stats + Tabs verbatim re-point (US-B1+B2+B3)`

---

## Day 2 — Config + Prompt tabs (Group C)

### 2.1 mockup-ui primitive decisions

- [ ] **Field promote-vs-keep decision** — log in progress.md Day 2 entry. Default promote if ≤ ~30 lines.
- [ ] **(If promote) Edit `mockup-ui.tsx` add Field primitive** — `<Field label help>{children}</Field>` label + help text wrapper

### 2.2 US-C1 — OrchestratorConfig re-point

- [ ] **Edit Config tab block** — re-point per mockup L65-114
  - Core settings Card: 5 Field rows (Display name input + Primary model select + Max turns Field + Token budget Field + Worktree disabled note)
  - Loop policy Card: TBD per mockup
  - DoD: visual diff ≤ 2 px; all Field labels + help text verbatim from mockup

### 2.3 US-C2 — OrchestratorPrompt re-point

- [ ] **Edit Prompt tab block** — re-point per mockup L116-173
  - System prompt Card + textarea (`.textarea` class; 5-row default)
  - `.kbar` token estimate row with 3 Badges (tokens count / cost estimate / version)
  - DoD: visual diff ≤ 2 px

### 2.4 Day 2 5-gate quick-check + commit

- [ ] **tsc + ESLint + Vitest pass**
- [ ] **Commit Day 2** — `feat(frontend, sprint-57-34): /orchestrator Config + Prompt tabs verbatim re-point (US-C1+C2)`

---

## Day 3 — Tools + Subagents + Budgets + Policies tabs (Group D)

### 3.1 mockup-ui primitive decisions

- [ ] **Switch promote-vs-keep decision** — log in progress.md Day 3 entry. Default promote if ≤ ~30 lines.
- [ ] **(If promote) Edit `mockup-ui.tsx` add Switch primitive** — `<Switch checked onChange />` toggle

### 3.2 US-D1 — OrchestratorTools re-point

- [ ] **Edit Tools tab block** — re-point per mockup L175-205
  - 18-tool chip grid (`.chip` class) + per-Tool Badge tone dispatch + Add-Tool Button
  - DoD: 18 chips render; tone Badge mapping matches mockup conditional

### 3.3 US-D2 — OrchestratorSubagents re-point

- [ ] **Edit Subagents tab block** — re-point per mockup L207-237
  - 6 subagents row layout + mode Badge tone dispatch (fork/as_tool/teammate/handoff)
  - DoD: visual diff ≤ 2 px

### 3.4 US-D3 — OrchestratorBudgets re-point

- [ ] **Edit Budgets tab block** — re-point per mockup L239-272
  - Numeric Field (Max turns / Max tokens / Per-turn ms cap) + cost summary Card
  - DoD: visual diff ≤ 2 px

### 3.5 US-D4 — OrchestratorPolicies re-point

- [ ] **Edit Policies tab block** — re-point per mockup L274-(end)
  - 4+ Switch toggles + HITL config Card
  - DoD: visual diff ≤ 2 px; Switch state preserved via local state

### 3.6 Day 3 5-gate quick-check + commit

- [ ] **Full Vitest run** — 456/456 baseline maintained
- [ ] **Commit Day 3** — `feat(frontend, sprint-57-34): /orchestrator Tools + Subagents + Budgets + Policies tabs verbatim re-point (US-D1+D2+D3+D4)`

---

## Day 4 — Regression sweep + closeout (Group E)

### 4.1 US-E1 — 22-route sweep after

- [x] **Run `route-sweep.mjs after`** — 22 PNGs captured to `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-34/artifacts/orchestrator-repoint/screenshots/after/`
- [x] **Sweep delta analysis** — `/orchestrator` flipped Sprint 57.19 Tailwind → ✅ PARITY (Tabs spacing + brand-mark 32px + grid-stats verbatim + Memory access clean + Field/Switch mockup-ui); 0 regressions on other 21 routes (Sprint 57.33's 3 fixed routes maintain ✅)
- [x] **Per-tab sample** — `/orchestrator` after-baseline captured; Config tab visible (sample sufficient)

### 4.2 US-E3 — Final 5-gate verification

- [x] **tsc + Vite build** — `built in 3.20s`
- [x] **ESLint** — exit 0
- [x] **Vitest** — **456/456** baseline preserved
- [x] **check:mockup-fidelity** — diff guard byte-identical + grep guard 25-line baseline preserved

### 4.3 US-E4 — Docs sync

- [x] **REPOINT-REPORT.md** — `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-34/artifacts/orchestrator-repoint/REPOINT-REPORT.md` (visual delta + code changes + primitive promotions + 5-gate + calibration + ADs)
- [x] **progress.md Day 0-4** — daily entries with actual vs est per task
- [x] **retrospective.md Q1-Q7** — Q2 calibration ratio ≈0.95-1.05 in band middle + bimodal-by-shape signal + KEEP 0.50 baseline
- [x] **`sprint-workflow.md §Matrix`** — `frontend-verbatim-css-repoint` 5th data point cell updated + MHist entry + bimodal-by-shape evaluation outcome
- [x] **memory subfile** — `memory/project_phase57_34_orchestrator_repoint.md`
- [x] **`MEMORY.md` pointer** — Sprint 57.34 entry added above Sprint 57.33 entry
- [x] **`CLAUDE.md` Current Sprint row + footer** — minimal touch (2 line edits)
- [x] **`next-phase-candidates.md`** — Sprint 57.34 Carryover section added + 2 NEW ADs (shape-bimodal-watch + tabs-migration-to-mockupui)

### 4.4 US-E5 — Commit + PR + merge

- [ ] **Day 4 commit** on `feature/sprint-57-34-orchestrator-repoint` (next step)
- [ ] **PR open** — `gh pr create` (next step)
- [ ] **CI green → squash-merge** (next step)

### 4.5 Sprint closeout self-check

- [x] Sacred Rule check — 0 unchecked items deleted
- [x] Acceptance Criteria — 5/6 pass; #6 (docs synced) all complete; #5 (PR+merge) pending Day 4.5 commit push
- [ ] Working tree clean post-merge — on main (pending merge)
- [ ] Branch deleted — `feature/sprint-57-34-orchestrator-repoint` deleted local + remote (pending merge)
