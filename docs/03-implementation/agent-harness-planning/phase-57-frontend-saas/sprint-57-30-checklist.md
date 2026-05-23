# Sprint 57.30 — Checklist

> Plan: [`sprint-57-30-plan.md`](./sprint-57-30-plan.md)
>
> AD-Chatv2-Verbatim-Repoint + Shell-Hotfix-UserMenu-Avatar.
>
> Day 0-5; mirror 57.29 5-day structure. Format consistency rule per `.claude/rules/sprint-workflow.md` — checklist depth + per-task DoD + Verify command depth match 57.29 checklist.

---

## Day 0 — Plan + Checklist + 三-prong + before-baseline (PRE-WORK)

### 0.1 Plan + Checklist drafted

- [x] **Plan file** `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-30-plan.md` exists with 11 sections (Sprint Goal / Background / User Stories / Technical Specifications / File Change List / Acceptance Criteria / Deliverables / Dependencies & Risks / Workload / Sequencing-Day plan / + MHist footer)
  - DoD: `Glob` returns 1 result for the plan path
  - Verify: read plan §Sprint Goal — Shell hotfix + chat-v2 verbatim re-point per Option B
- [x] **Checklist file** (this file) drafted mirroring Sprint 57.29 checklist format (Day 0-5 + Group A-E + per-task DoD + Verify)
  - DoD: this file exists with Day 0-5 sections
  - Verify: `Glob` returns 1 result for `sprint-57-30-checklist.md`

### 0.2 Day-0 三-prong verify

- [x] **Prong 1 — Path verify** (all §File Change List paths in real repo) — 0 drift; 23 MODIFIED found / 1 NEW absent as expected
- [x] **Prong 2 — Content verify** (grep for plan-time factual assertions in real code) — 6 findings catalogued D1-D6 in progress.md; D2 🔴 (avatarStyle reuse) confirmed; D1+D3+D6 🟢; D4+D5 🟡 deferred
- [x] **Prong 3 — Schema verify** — N/A (frontend-only)
- [x] **Prong 4 — Visual baseline scope** — decision: accept Day 5 regen overhead (same as 57.29 workaround per `AD-CI-7-GHA-PR-Permission`)

### 0.3 Before-baseline screenshot capture

- [x] **22 AppShellV2 route screenshots** — `route-sweep.mjs before` mode (OUT_DIR re-pointed to sprint-57-30-* dir) → all 22 PNG in `before/`; ✅
- [x] **UserMenu states** — `sprint-57-30-day0-extras.mjs` captured `extra-usermenu-closed-overview.png` + `extra-usermenu-open-overview.png` (the latter visually confirms the drift gap user reported)
- [x] **chat-v2 states** — same script captured `extra-chatv2-inspector-default.png` + `extra-chatv2-inspector-toggled.png`
- [x] **Day 0 commit** — `5c0ce0dd` on `feature/sprint-57-30-chatv2-shell-repoint` (base `2d9d9e9f`); 26 PNG in `before/`

---

## Day 1 — Group B (Shell hotfix: UserMenu Radix-drop + avatar split + icon audit)

### 1.1 US-B1 — UserMenu Radix-drop verbatim port

- [x] **Port `useDismiss` hook verbatim** from mockup `topbar-overlays.jsx:9-27` — inlined inside `UserMenu.tsx` (Karpathy §2 — defer extraction until 2nd consumer)
- [x] **Drop Radix `<DropdownMenu>` wrapper** — 0 active references remain (4 mentions all in docstring breadcrumbs)
- [x] **Verify mockup-canonical positioning works** — Playwright `day1-usermenu-flush.png` confirms dropdown flush with topbar bottom edge; ESC + click-outside + item-click all close

### 1.2 US-B2 — Avatar trigger 36→26 split

- [x] **Split `avatarStyle` into trigger + identity** — trigger now uses `className="avatar"` CSS class (26×26); in-panel renamed `identityAvatarStyle` (36×36)
- [x] **Verify with Playwright screenshot** — `day1-usermenu-trigger-26.png` shows visibly smaller trigger; identity card avatar inside dropdown still 36×36

### 1.3 US-B3 — Topbar icon size audit (D3 Day-0 closure)

- [x] **Audit each topbar icon vs mockup** — Day 0 Prong 2 found 0 drift (search 13 / globe 12 / theme 14 / bell 14 all match mockup `Button size="sm"` default `Icon size={14}` per mockup-ui.tsx L436)
- [x] **No fix needed** — only MHist note added to `Topbar.tsx`

### 1.4 US-B4 — Vitest + UserMenu spec adaptation

- [x] **UserMenu spec preserved** — Vitest 457/457 (no adapt needed; spec asserts `aria-haspopup="menu"` + `aria-expanded` + `role="menuitem"` which the hand-rolled verbatim version preserves)
- [x] **ESLint a11y fix** — added `onMenuItemKey` handler on 5 menuitem `<div>`s (Enter/Space → click) to maintain keyboard parity after Radix drop without re-importing Radix focus-trap
- [x] Day 1 commit — pending (next step)

---

## Day 2 — Group C (chat-v2 shell + composer)

### 2.1 US-C1 — ChatLayout 3-col grid verbatim

- [x] **Read mockup `page-chat.jsx:79`** — outer `.chat-shell` consumes `styles-mockup.css` L669-708 grid template + responsive
- [x] **Re-point `ChatLayout.tsx`** to verbatim `.chat-shell` class + `data-list`/`data-insp` attrs — Tailwind grid-cols-[…] dropped; -33 / +24 lines

### 2.2 US-C2 — ChatHeader + SessionList + Composer + InputBar + page index

- [x] **ChatHeader** re-point — `.panel-toggle` + `.badge agent/thinking` + `.provider-neutral` + `.live-dot` + Loop/Audit `.btn ghost data-size="sm"` (shadcn Badge + Button dropped) -78 / +101
- [x] **SessionList** re-point — `.chat-list`/`.session-item`/`.session-title`/`.session-meta` + DomainDot + AP-2 banner preserved + `.btn primary New session` -80 / +84
- [x] **Composer** re-point — `.composer`/`.composer-inner`/`.composer-input`/`.composer-tools` + mockup L362 drop hint inline-style -63 / +71
- [x] **InputBar** re-point — `.composer` shell + `.btn primary/.btn danger`; production status pill / mode toggle / error banner use mockup token vocabulary (4 NEW verbatim oklch tints) -64 / +103
- [x] **pages/chat-v2/index.tsx** — MHist only (AppShellV2 wrap preserved) +1
- [x] **Day 2 mini-verify** — `day2-chatv2-shell.png` + `day2-chatv2-list-hidden.png` + `day2-chatv2-insp-hidden.png` capture; Day 1 UserMenu verify re-run no regression
- [x] **`check:mockup-fidelity` baseline** — HEX_OKLCH_BASELINE 21→25 with audit note (precedent: 57.29 18→21; same legitimate-verbatim-oklch case)
- [ ] Day 2 commit — pending (next step)

---

## Day 3 — Group D first half (TurnList + 3 turn shapes + 3 blocks)

### 3.1 US-D1 — TurnList + UserTurn + AgentTurn + HITLTurn

- [ ] **TurnList** re-point
  - Sub: verbatim mockup port; preserve scroll behaviour + virtualization (if any)
  - Sub: header MHist
- [ ] **UserTurn** re-point
  - Sub: verbatim mockup user-turn shape
  - Sub: preserve content rendering + timestamp + edit affordance
  - Sub: header MHist
- [ ] **AgentTurn** re-point
  - Sub: verbatim mockup agent-turn shape (includes block routing for ThinkingBlock / ToolBlock / VerificationBlock / SubagentForkBlock)
  - Sub: preserve discriminated-union routing from Sprint 57.21 Turn Block Model
  - Sub: header MHist
- [ ] **HITLTurn** re-point
  - Sub: verbatim mockup HITL turn (the largest turn file — 229 lines today)
  - Sub: preserve approval flow + governance integration
  - Sub: header MHist

### 3.2 US-D2 first half — Block base + ThinkingBlock + ToolBlock

- [ ] **Block** (base wrapper) re-point
  - Sub: verbatim mockup block base style
  - Sub: header MHist
- [ ] **ThinkingBlock** re-point
  - Sub: verbatim mockup thinking-block (collapsed + expanded states)
  - Sub: preserve markdown rendering
  - Sub: header MHist
- [ ] **ToolBlock** re-point
  - Sub: verbatim mockup tool-block (input args + output + status indicator)
  - Sub: preserve JSON syntax highlighting
  - Sub: header MHist
- [ ] **Day 3 mini-verify**
  - Sub: `/chat-v2` turn list renders with new turn frames + 3 block types
  - Sub: Sprint 57.21 Vitest behavioural specs still pass
- [ ] Day 3 commit

---

## Day 4 — Group D second half (VerificationBlock + SubagentForkBlock + Inspector + ApprovalCard)

### 4.1 US-D2 second half — VerificationBlock + SubagentForkBlock

- [ ] **VerificationBlock** re-point
  - Sub: verbatim mockup verification-block (rule list + pass/fail + correction loop UI)
  - Sub: header MHist
- [ ] **SubagentForkBlock** re-point
  - Sub: verbatim mockup subagent-fork (subagent tree + spawn/return events)
  - Sub: header MHist

### 4.2 US-D3 — ChatInspector + InspectorTurn + ComingSoonInspectorTab

- [ ] **ChatInspector** re-point
  - Sub: verbatim mockup 4-tab chrome (Overview / State / Tools / Verification)
  - Sub: preserve tab state + tab-switch behaviour
  - Sub: header MHist
- [ ] **InspectorTurn** re-point
  - Sub: verbatim mockup inspector-turn detail view
  - Sub: preserve turn data binding
  - Sub: header MHist
- [ ] **ComingSoonInspectorTab** re-point
  - Sub: verbatim mockup coming-soon placeholder
  - Sub: header MHist

### 4.3 US-D4 — ApprovalCard

- [ ] **ApprovalCard** re-point
  - Sub: verbatim mockup HITL approval card visual
  - Sub: preserve approve / deny / escalate handlers + governance integration
  - Sub: header MHist

### 4.4 Vitest comprehensive re-run

- [ ] **Run all chat-v2 Vitest** + adapt any new spec drift
  - Sub: `npm run test -- chat-v2`
  - Sub: any failure → adapt to verbatim structure (not to Radix / Tailwind assertions)
  - DoD: 100% pass
- [ ] Day 4 commit
  - Sub: `git commit -m "feat(frontend, sprint-57-30): Day 4 Group D second half — Inspector + ApprovalCard + last 2 blocks verbatim re-point\n\n..."`

---

## Day 5 — Group E (regression sweep + chat-v2 fidelity + closeout)

### 5.1 US-E1 — 22-route regression sweep

- [ ] **Capture after-baseline 22 routes** via `route-sweep.mjs`
  - Sub: `node scripts/visual/route-sweep.mjs --tag=after`
  - Sub: writes to `claudedocs/4-changes/sprint-57-30-chatv2-shell-repoint/screenshots/after/`
  - DoD: 22 PNG in `after/`
- [ ] **Agent triage** before vs after
  - Sub: launch `general-purpose` (or `code-reviewer`) agent with all 22 pairs; classify each as PARITY / 🟡 acceptable-cosmetic / 🔴 catastrophic / 🟠 structural-regression
  - Sub: triage report → REPOINT-REPORT.md
  - DoD: 0 🔴 catastrophic / 0 🟠 structural-regression; any 🟡 cosmetic documented with reason
  - DoD: pre-existing-fail routes (`/subagents` `/memory` `/verification` per Sprint 57.29 carryover `AD-Overview-PreExisting-Route-Crashes`) classified explicitly as **not Sprint 57.30 regressions** (before == after baseline)

### 5.2 US-E2 — chat-v2 fidelity verification (Mockup-Fidelity DoD)

- [ ] **Step 1 — `styles.css` ↔ `styles-mockup.css` diff**
  - Sub: `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → empty
  - DoD: diff empty (foundation untouched)
- [ ] **Step 2 — Mockup vs prod Playwright screenshot at 1440×900**
  - Sub: spin up mockup `python -m http.server` from `reference/design-mockups/`
  - Sub: capture mockup `/chat-v2` equivalent page
  - Sub: capture prod `/chat-v2` (Inspector closed + open)
  - DoD: 2-3 screenshot pairs saved
- [ ] **Step 3 — Computed-style measurement**
  - Sub: pick ~10 representative elements (ChatLayout grid, ChatHeader, SessionList row, Composer, AgentTurn frame, ThinkingBlock, ToolBlock, Inspector tab, ApprovalCard)
  - Sub: read `getComputedStyle()` for each on both mockup + prod; diff
  - DoD: drift items each classified as PARITY / cosmetic / structural
- [ ] **Step 4 — Drift classification + parity verdict**
  - Sub: write REPOINT-REPORT.md final verdict section
  - Sub: if PARITY → log as `frontend-verbatim-css-repoint` 2nd-app validated
  - Sub: if non-PARITY → log finding as next sprint carryover AD
  - DoD: verdict in REPOINT-REPORT.md

### 5.3 US-E3 — Full gates

- [ ] **tsc** — `npm run typecheck` → 0 errors
  - Verify: exit code 0
- [ ] **lint** — `npm run lint` → 0 errors
  - Verify: exit code 0
- [ ] **Vitest** — `npm run test` → all pass
  - Sub: log new count vs Sprint 57.29 baseline 457
  - Verify: exit code 0; count delta logged in progress.md
- [ ] **Playwright** — `npm run test:e2e` → all pass
  - Sub: visual-regression baseline regen if Day 4 changes invalidated 57.29 baselines (ff-merge per Sprint 57.29 workaround)
  - Verify: green
- [ ] **Build** — `npm run build` → successful
  - Sub: log bundle size delta vs Sprint 57.29
  - Verify: exit code 0
- [ ] **`check:mockup-fidelity`** — `npm run check:mockup-fidelity`
  - Sub: if new oklch literals added by Day 1-4 work, update `HEX_OKLCH_BASELINE` per US-E1 pre-authorisation (Day 0 catalogue any expected delta)
  - Verify: green
- [ ] **LLM SDK leak check** — `python scripts/lint/check_llm_sdk_leak.py backend/src/agent_harness/` → 0
  - Verify: exit code 0 (sanity check; shouldn't change frontend-only sprint)
- [ ] **Backend pytest** — sanity that no incidental backend change crept in
  - Sub: `cd backend && pytest -x --timeout=60` (if affordable; else skip)
  - DoD: green or skipped with reason in progress.md

### 5.4 US-E4 — Closeout (retro + memory + docs + PR)

- [ ] **`retrospective.md`** Q1-Q7 written
  - Sub: Q1 What went well / Q2 What didn't go well + calibration ratio / Q3 What we learned / Q4 Audit Debt deferred / Q5 Next steps + carryover AD list / Q6 Solo-dev policy validation / Q7 (N/A — feature ship not spike)
  - Sub: Q2 must include `actual / committed` ratio and judge against [0.85, 1.20] band per `sprint-workflow.md §Workload Calibration`
  - DoD: file `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-30/retrospective.md` exists with all 6 sections (Q7 N/A SKIP)
- [ ] **Memory snapshot** `memory/project_phase57_30_chatv2_shell_repoint.md` (NEW)
  - Sub: ~250-300 char per `sprint-workflow.md §Sprint Closeout — MEMORY.md Update Policy` quality pointer rule
  - Sub: subfile detail in `memory/project_phase57_30_*.md`
  - DoD: file exists with frontmatter + sprint summary
- [ ] **MEMORY.md** index entry added
  - Sub: 1 pointer entry per quality pointer principle (topic + keywords + subfile path; ~300 char ceiling)
  - DoD: MEMORY.md has new pointer at top of "Project — Recent Sprints" section
- [ ] **CLAUDE.md** Current Sprint row + footer updated
  - Sub: Current Sprint row → next sprint candidate or "ready for next"
  - Sub: Last Updated footer → `2026-MM-DD (Sprint 57.30 — Chat-v2 + Shell Hotfix Verbatim Re-Point)`
  - DoD: minimal touch per `sprint-workflow.md §Sprint Closeout — CLAUDE.md Update Policy`
- [ ] **`.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`** updated
  - Sub: `frontend-verbatim-css-repoint` row — 2nd data point (Sprint 57.30 ratio)
  - Sub: KEEP 0.60 per `When to adjust` 3-sprint window rule
  - Sub: MHist entry added (1-line per char-budget rule)
  - DoD: matrix row reflects 2 data points
- [ ] **`claudedocs/1-planning/next-phase-candidates.md`** updated
  - Sub: CLOSE `AD-UserMenu-Mockup-Structural-Deltas` (resolved this sprint)
  - Sub: ADD any new carryover ADs from retrospective Q4 + Q5
  - Sub: KEEP `AD-Overview-PreExisting-Route-Crashes` + `AD-CI-7-GHA-PR-Permission` (Sprint 57.31+)
  - DoD: candidates file synced
- [ ] **PR opened**
  - Sub: `gh pr create --title "feat(frontend, sprint-57-30): chat-v2 Phase-2 verbatim CSS re-point + shell hotfix (UserMenu Radix-drop + avatar 36→26 split + topbar icon audit)" --body "..."`
  - Sub: PR body links plan + REPOINT-REPORT.md + retrospective
  - DoD: PR number assigned
- [ ] **CI green → merge**
  - Sub: if visual-regression baseline stale (likely on shell + chat-v2 changes), trigger baseline-regen workflow → ff-merge baseline commit per Sprint 57.29 `AD-CI-7-GHA-PR-Permission` workaround
  - Sub: squash-merge to main when all 5 required CI checks green
  - Sub: delete feature branch + any throwaway baseline-regen branch
  - DoD: PR squash-merged to main; branch cleanup done

### 5.5 Sprint closeout self-check

- [ ] **Sacred Rule check** — no unchecked `[ ]` items in this checklist were deleted
  - Verify: `grep -c "^- \[ \]" sprint-57-30-checklist.md` matches all incomplete-but-deferred items (none expected if all Group A-E delivered)
- [ ] **Acceptance Criteria verified** — all items in plan §Acceptance Criteria pass
- [ ] **Working tree clean post-merge**
  - Verify: `git status` shows clean main + untracked screenshots only
- [ ] **Branch deleted**
  - Verify: `git branch --list feature/sprint-57-30-*` returns empty
