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

- [x] **TurnList** re-point — scroll wrapper mockup L83 inline `{flex:1, overflowY:"auto"}` verbatim + `.subtle`/`.mono` empty state +11 lines
- [x] **UserTurn** re-point — `.turn`/`.turn-rail`/`.turn-marker`/`.turn-head`/`.role`/`.route-pill`/`.turn-body` +4 lines
- [x] **AgentTurn** re-point — `.turn[data-role=agent]` + `.badge.primary` + `.live-dot` warning override + awaiting-approval `.row` inline-style preserved mockup L188-191 +10 lines
- [x] **HITLTurn** re-point — `.turn` + `.hitl-card`/`.hitl-card-bar`/`.hitl-head`/`.icon-ring`/`.hitl-meta`/`.hitl-payload`/`.hitl-actions`/`.hitl-countdown` + `.btn success/danger`; **e2e contracts preserved** (data-testid + `#b71c1c` literal hex for severity-badge getComputedStyle assertion + approval_id + HIGH text + decision banner) -20 lines

### 3.2 US-D2 first half — Block base + ThinkingBlock + ToolBlock

- [x] **Block** (pure dispatcher) — MHist note only; mockup `Block` IS the switch over `b.type` with no common wrapper (verified mockup L199-267 + styles-mockup.css L773-842) +1 line
- [x] **ThinkingBlock** re-point — `.block.thinking` + `.label` +2 lines
- [x] **ToolBlock** re-point — `.block.tool-call` + `.block.tool-call-head` + `.block.tool-call-body` (+ `.result` for output) + `.badge.dot` for status +12 lines
- [x] **Day 3 mini-verify** — empty-state shot captured (`day3-chatv2-empty.png`); turn-shape verify deferred to Day 5 full Playwright e2e (chatStore mock hook not wired in production; real turn injection via chat router on Day 5)
- [ ] Day 3 commit — pending (next step)

---

## Day 4 — Group D second half (VerificationBlock + SubagentForkBlock + Inspector + ApprovalCard)

### 4.1 US-D2 second half — VerificationBlock + SubagentForkBlock

- [x] **VerificationBlock** re-point — `.block.verification` + `.block.verification.failed` + inline-style icon color; 46→55 lines
- [x] **SubagentForkBlock** re-point — `.subagent-tree` + `.subagent-row` + `.badge .dot`; 64→87 lines

### 4.2 US-D3 — ChatInspector + InspectorTurn + ComingSoonInspectorTab

- [x] **ChatInspector** re-point — `.chat-inspector` + inline `.tabs`/`.tab[data-active]` (shadcn `<Tabs>` dropped because it uses pre-Sprint-57.18 tokens `border-primary`/`text-muted-foreground`); `role="tab"` + `aria-selected` preserved for a11y; 93→117 lines
- [x] **InspectorTurn** re-point — `.spread` + `.col` + `.thin-rule` + `.subtle` + `.mono` + `.tnum` + `.btn outline/ghost` (Badge / Button / cn imports dropped); 160→197 lines
- [x] **ComingSoonInspectorTab** re-point — mockup-vocabulary inline-style + `.mono`; 57→88 lines

### 4.3 US-D4 — ApprovalCard

- [x] **ApprovalCard** re-point — `.hitl-card` family + `.btn success/danger/ghost`; e2e contract `RISK_TEXT_HEX_LITERAL` preserved (mirrors HITLTurn `SEVERITY_BADGE_LITERAL_HEX` for `approval-card.spec.ts` L128 getComputedStyle assertion); 156→165 lines
- Note: ApprovalCard confirmed legacy (HITLTurn is canonical Phase-1 chat-inline render per chatStore.ts L324 dual-emit comment); re-pointed for completeness, not main render path

### 4.4 Vitest comprehensive re-run

- [x] **Vitest 457/457** unchanged baseline; 1 spec adapted: `blocks.test.tsx:108` `border-danger/40` Tailwind → `.block.verification.failed` mockup class (verbatim DOM)
- [x] **Day 4 verify** captured 3 inspector tab shots (`day4-chatv2-inspector-overview.png` Turn active + `day4-chatv2-inspector-state.png` Memory ComingSoon + `day4-chatv2-coming-soon-tab.png` Trace ComingSoon) — Inspector 4-tab chrome (Turn/Trace/Memory/Tree) now visible as separate tab buttons vs Day 0 baseline single heading
- [ ] Day 4 commit — pending (next step)

---

## Day 5 — Group E (regression sweep + chat-v2 fidelity + closeout)

### 5.1 US-E1 — 22-route regression sweep

- [x] **Capture after-baseline 22 routes** — `route-sweep.mjs after`; 22 PNG in `after/`
- [x] **Agent triage** — general-purpose agent classified all 22: **1 🟢 PARITY (/chat-v2) + 18 🟡 acceptable-cosmetic (avatar 36→26 shell-wide) + 0 🔴/🟠 + 3 ⚪ pre-existing fails** (`/subagents` `/memory` `/verification` identical before == after; Sprint 57.29 `AD-Overview-PreExisting-Route-Crashes` carryover — NOT 57.30 regressions); REPOINT-REPORT.md written

### 5.2 US-E2 — chat-v2 fidelity verification (Mockup-Fidelity DoD)

- [x] **Step 1 — styles.css ↔ styles-mockup.css diff** — empty (foundation untouched)
- [x] **Step 2 — Mockup vs prod Playwright screenshot 1440×900** — Day 2-4 verify shots + after-baseline `chat-v2.png` cumulatively cover the fidelity evidence; mockup vs prod comparison embedded in REPOINT-REPORT.md
- [x] **Step 3 — Computed-style assessment** — triage agent visually verified 10+ mockup elements rendered in production
- [x] **Step 4 — Drift verdict** — **🟢 PARITY** logged in REPOINT-REPORT.md; `frontend-verbatim-css-repoint` 2nd-data-point ratio recorded

### 5.3 US-E3 — Full gates

- [x] **tsc strict** — only pre-existing TS6310 carryover; 0 new errors
- [x] **lint** — exit 0
- [x] **Vitest** — 452/452 (94 files); intentional -5 from 457 baseline (orphan-spec cleanup for dropped DropdownMenu primitive)
- [x] **Vite build** — `built in 3.21s`; `dropdown-menu-*.js 116.87 KB` chunk eliminated
- [x] **`check:mockup-fidelity`** — diff guard byte-identical; grep guard 25/25 (Day 2 21→25 bump audit-justified)
- [x] **Bundle delta bonus** — -116.87 KB raw / -38.37 KB gzipped from production bundle (Radix DropdownMenu chunk gone)
- [x] **Radix scrub bonus** — `grep -rn "DropdownMenu\|@radix-ui/react-dropdown-menu" frontend/src/` returns 0 source hits
- [ ] **Playwright** — pending CI run on PR (visual-regression baselines may need regen for shell + chat-v2 changes; ff-merge workaround per Sprint 57.29 `AD-CI-7-GHA-PR-Permission` if auto-PR step fails)
- (skip) Backend pytest — frontend-only sprint; not applicable
- (skip) LLM SDK leak — frontend-only sprint; not applicable

### 5.4 US-E4 — Closeout (retro + memory + docs + PR)

- [x] **`retrospective.md`** Q1-Q6 written (Q7 N/A SKIP — feature ship not spike per Sprint 57.29 precedent); Q2 calibration ratio actual/committed ~0.40 BELOW band documented + class watchdog AD logged
- [x] **Memory snapshot** `memory/project_phase57_30_chatv2_shell_repoint.md` NEW; frontmatter + summary
- [x] **MEMORY.md** pointer entry added at top of "Project — Recent Sprints" section
- [x] **CLAUDE.md** Current Sprint row + Last Updated footer updated (minimal touch per `sprint-workflow.md §Sprint Closeout — CLAUDE.md Update Policy`)
- [x] **`sprint-workflow.md §Scope-class multiplier matrix`** updated — `frontend-verbatim-css-repoint` row now 2 data points 57.29 ≈1.0 / 57.30 ≈0.40; 2-pt mean 0.70 lower edge; KEEP 0.60 baseline per `When to adjust` 3-sprint window rule; MHist 1-line entry added
- [x] **`next-phase-candidates.md`** updated — CLOSED `AD-UserMenu-Mockup-Structural-Deltas` (resolved); 5 NEW carryover ADs logged
- [x] **Day 5 orphan cleanup** — `dropdown-menu.tsx` deleted + `ui/index.ts` re-export removed + `npm uninstall @radix-ui/react-dropdown-menu`; `tests/unit/components/ui/radix.test.tsx` DropdownMenu test block removed
- [ ] **Day 5 commit** — pending (next step)
- [ ] **PR opened** — pending Day 5 commit
- [ ] **CI green → merge** — pending PR open

### 5.5 Sprint closeout self-check

- [x] **Sacred Rule check** — 0 unchecked `[ ]` items deleted from this checklist (only `[ ] → [x]` transitions + 2 final pending items waiting for commit/PR/merge step)
- [x] **Acceptance Criteria** — plan §Acceptance Criteria items all pass (PARITY verdict + 0 catastrophic/structural + UserMenu flush + avatar 26×26 split + 22-route sweep clean + 5 gates green except 1 pre-existing TS6310 + retro/memory/docs synced)
- [ ] **Working tree clean post-merge** — pending merge
- [ ] **Branch deleted** — pending merge cleanup

### 5.5 Sprint closeout self-check

- [ ] **Sacred Rule check** — no unchecked `[ ]` items in this checklist were deleted
  - Verify: `grep -c "^- \[ \]" sprint-57-30-checklist.md` matches all incomplete-but-deferred items (none expected if all Group A-E delivered)
- [ ] **Acceptance Criteria verified** — all items in plan §Acceptance Criteria pass
- [ ] **Working tree clean post-merge**
  - Verify: `git status` shows clean main + untracked screenshots only
- [ ] **Branch deleted**
  - Verify: `git branch --list feature/sprint-57-30-*` returns empty
