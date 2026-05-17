# Sprint 57.21 — Checklist

**Plan**: `sprint-57-21-plan.md`
**Calibration**: `frontend-mockup-direct-port` 0.55 (2nd application; HYBRID weighted blend) — bottom-up ~16-20 hr → calibrated commit ~9-11 hr (Sprint 57.20 1st app ratio 0.45-0.55 below band by 0.30-0.40; KEEP 0.55 per 3-sprint window rule)
**Day count**: 5 (Day 0 setup + Day 1 types/mergeEvent rewrite + Day 2 TurnList + Block components + Day 3 SessionList + ChatLayout 3-col + Day 4 Inspector + Composer skeleton + closeout)
**Branch**: `feature/sprint-57-21-chatv2-mockup-fidelity-phase-1`

---

## Day 0 — Setup + Day 0 三-prong + Playwright MCP reference captures

### 0.1 Plan + checklist landed
- [x] Plan drafted at `sprint-57-21-plan.md` (Option C frontend-first; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
- [x] Checklist drafted at `sprint-57-21-checklist.md` (this file)
- [x] User approval to proceed Day 0 三-prong + Day 1 code (2026-05-17 「直接開 Day 0」)

### 0.2 Branch + initial doc files
- [x] Verify main HEAD: was `1a55e314` (PR #149) locally; `origin/main` had `ebc0dc60` (PR #151 closeout merge) → local main fast-forwarded to `ebc0dc60`
- [x] Switch from `chore/closeout-57-20` to `main` (working tree had 2 untracked plan+checklist files — survived branch switch)
- [x] Pull latest `main` — fast-forwarded `1a55e314..ebc0dc60` (2 files changed: CLAUDE.md + SITUATION-V2-SESSION-START.md)
- [x] Create feature branch `feature/sprint-57-21-chatv2-mockup-fidelity-phase-1` from main `ebc0dc60`
- [x] Create `progress.md` at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-21/progress.md` (Day 0 entry + 4 D-PRE findings + Playwright captures table)
- [x] Create `claudedocs/4-changes/sprint-57-21-chatv2-fidelity-phase-1/{screenshots/{mockup-chat-v2, prod-chat-v2-pre, blocks, sessions-sidebar, inspector-turn}/, DRIFT-REPORT-PHASE1.md}` skeleton

### 0.3 Day 0 三-prong scope verify (per sprint-workflow.md §Step 2.5)
- [x] **Prong 1 (Path verify)** — confirm each plan §File Change List entry:
  - `frontend/src/features/chat_v2/types.ts` exists ✅ (read content verified Day 0 探勘)
  - `frontend/src/features/chat_v2/store/chatStore.ts` exists ✅
  - `frontend/src/features/chat_v2/services/chatService.ts` exists ✅
  - `frontend/src/features/chat_v2/hooks/useLoopEventStream.ts` exists ✅
  - `frontend/src/features/chat_v2/components/{ApprovalCard,ChatLayout,InputBar,MessageList,ToolCallCard}.tsx` exist ✅
  - `frontend/src/features/chat_v2/components/blocks/` directory does NOT exist (will create Day 2)
  - `frontend/src/features/chat_v2/components/inspector/` directory does NOT exist (will create Day 4)
  - `frontend/src/features/chat_v2/components/turns/` directory does NOT exist (will create Day 2)
  - `frontend/src/features/chat_v2/fixtures/` directory may not exist (will create Day 3)
  - `reference/design-mockups/page-chat.jsx` exists ✅ (533 lines confirmed)
- [x] **Prong 2 (Content verify)** — grep each plan §Technical Spec assertion:
  - `types.ts` `Message` type currently `user | assistant` (✅ confirmed Day 0 探勘 L231-239)
  - `types.ts` 14 SSE event types: `LoopStartEvent` / `TurnStartEvent` / `LLMRequestEvent` / `LLMResponseEvent` / `ToolCallRequestEvent` / `ToolCallResultEvent` / `LoopEndEvent` / `ApprovalRequestedEvent` / `ApprovalReceivedEvent` / `GuardrailTriggeredEvent` / `VerificationPassedEvent` / `VerificationFailedEvent` / `SubagentSpawnedEvent` / `SubagentCompletedEvent` (✅ confirmed L188-202)
  - `KNOWN_LOOP_EVENT_TYPES` set lists 14 entries (✅ confirmed L205-222)
  - `chatStore.ts` `mergeEvent` function exists + uses discriminated union switch on event.type
  - `useLoopEventStream.ts` consumes SSE; passes events to `mergeEvent`
  - `governanceService.decide` exists (governance feature) for HITL workflow preservation
  - `STYLE.md §3` `text-[#hex]` risk color mapping exists for HITL severity rendering
- [x] **Prong 3 (Schema verify)**: N/A this sprint (pure frontend, 0 DB schema work, 0 backend changes)
- [x] Catalog Day 0 drift findings as `D-PRE-1` through `D-PRE-4` in `progress.md` (D-PRE-1 risk tokens; D-PRE-2 ChatHeader; D-PRE-3 RiskBadge; D-PRE-4 auth race condition)
- [x] Go/no-go decision: scope shift verdict = **0%** (all 4 findings are clarifications, in-scope additions, or env notes) → **GO Day 1**

### 0.4 Playwright MCP reference captures (US-A1)
- [x] Mockup http.server still running at port 8080 (verified PID 44700)
- [x] Dev server running at port 3007 (verified PID 50796; not killed per CLAUDE rule)
- [x] Playwright MCP capture mockup `#chat` route at 1440×900 → `screenshots/mockup-chat-v2/mockup-chat-v2-1440x900.png` (full viewport; sub-zooms deferred to Day 2+ when component-level work needs them)
- [x] Playwright MCP capture pre-rewrite production `/chat-v2` at 1440×900 — 5 attempts captured (D-PRE-4 auth race condition: 3 redirected to login, 1 home page authenticated, 1 chat-v2 attempt with race redirect); files in `screenshots/prod-chat-v2-pre/`
- [x] Commit Day 0 artifacts: `chore(sprint-57-21, Day 0): plan + checklist + Day 0 三-prong + Playwright MCP reference captures` (commit landed)

---

## Day 1 — Turn block data model rewrite (US-B1 + US-B2 + US-B3) ✅ COMPLETED

**Commit consolidation note**: 1.1 + 1.2 + 1.3 done in one session without broken intermediate states; consolidated into ONE Day 1 commit at 1.4 closeout to avoid tsc-broken intermediate commits (types.ts rewrite alone would break tsc until chatStore + MessageList adapted).

### 1.1 US-B1 types.ts refactor — Turn discriminated union ✅
- [x] Read `reference/design-mockups/page-chat.jsx` L14-70 (TURNS data shape) + L199-267 (Block switch) end-to-end (Day 0 already)
- [x] **REWRITE** `frontend/src/features/chat_v2/types.ts`:
  - Preserved: 14 SSE event types + `KNOWN_LOOP_EVENT_TYPES` set + `ChatStatus` + `ChatMode` + `ChatSession` + `ToolCallEntry` + `ApprovalEntry`
  - Added NEW: `Block` discriminated union (4 types: thinking / tool / verification / subagent_fork); memory deferred to Phase-2+
  - Added NEW: `Turn` discriminated union (user / agent / hitl) per mockup; AgentTurn has Inspector Turn tab metadata fields (tokensIn/Out/Thinking, costUsd, traceId, spanId — all nullable)
  - Added NEW: `Session` interface + `SessionDomain` + `SessionStatusUI` for Day 3 fixture sidebar
  - Added NEW: `RiskSeverity` token type aligned to Sprint 57.18 `risk-{low,medium,high,critical}` (per D-PRE-1)
  - Added NEW: `SubagentEntry` + `ToolBlockStatus` helper types
  - Removed `Message` type (clean removal; tsc gate surfaces consumers — only `MessageList.tsx` + `chatStore.ts` touched, both rewritten same Day 1; `useLoopEventStream.ts` only uses `pushUserMessage` action name, no TYPE)
  - File-header Modification History 1-line entry added
- [x] `npx tsc --noEmit` — exit 0, 0 type errors ✅

### 1.2 US-B2 chatStore.mergeEvent rewrite ✅
- [x] Read current `chatStore.ts` `mergeEvent` end-to-end; enumerated each event-type case (L120-340)
- [x] **REWRITE** `chatStore.ts`:
  - State shape: `{ messages: Message[] }` → `{ turns: Turn[], sessions: Session[], activeSessionId: string | null }`
  - Dual-emit mergeEvent: all 14 SSE event types preserve existing slices (rawEvents/approvals/verifications/subagents) AND emit blocks/turns into new `turns[]` array
  - Helper functions: `nextTurnId()` / `nowIso()` / `mapRiskLevel()` (HIGH→risk-high mapping) / `updateLastAgentTurn()` (immutable pure update)
  - turn lifecycle: loop_start → status running; turn_start → push empty AgentTurn with null metadata; llm_response → ThinkingBlock + ToolBlock per tool_call (thinking-before-tools order per mockup); tool_call_request defensive; tool_call_result → ToolBlock status/output/durationMs update; verification_* → VerificationBlock; subagent_spawned → find-or-create SubagentForkBlock; subagent_completed → update agent entry status; approval_requested → push HITLTurn; loop_end → status completed + turn stopReason + waiting flag (tool_use → waiting=true)
  - File-header Modification History 1-line entry added
- [x] **NOT TOUCHED**: `useLoopEventStream` hook signature; `chatService` API contract; `governanceService.decide` usage ✅

### 1.3 US-B3 Vitest mergeEvent block-sequence coverage ✅
- [x] Existing chat-v2 Vitest specs verified — 0 file references `messages` array or `Message` type (per grep); 2 existing chatStore-touching specs (`subagents.test.ts` + `verifications.test.ts`) STILL PASS without modification (dual-emit preserves Sprint 57.11/57.12 slice behavior)
- [x] `MessageList.tsx` Day 1 stub: consumes `turns[]` + `ToolBlock → ToolCallCard` adapter inline; skips HITLTurn render (existing approvals dict path preserved). Day 2 replaces with proper TurnList + components/blocks/
- [x] **NEW Vitest spec** `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` — **22 NEW cases**:
  - Lifecycle: pushUserMessage → UserTurn; turn_start → empty AgentTurn; llm_request → tokensIn populate
  - llm_response: thinking-only / tool_calls-only / both (order); ToolBlock status=pending
  - Tool flow: tool_call_request defensive + dedup; tool_call_result success/error
  - Verification: passed/failed dual-emit (turn block + slice)
  - Subagent: spawned single/multi + completed → done; dual-emit (turn block + slice)
  - Approval: requested → HITLTurn + dict; received → decision update both; risk_level mapping low/medium/high/critical
  - loop_end: end_turn (waiting=false) / tool_use (waiting=true)
  - guardrail_triggered: rawEvents only, no turn changes
  - End-to-end: user → turn_start → llm_response → tool_result → loop_end full sequence assert
- [x] `npx vitest run` Vitest **299/299 PASS** (Sprint 57.20 baseline 277 + 22 NEW; 0 regression) ✅

### 1.4 Day 1 closeout ✅
- [x] `npx tsc --noEmit` 0 errors ✅
- [x] `npx vitest run` 299/299 PASS; 64 test files (Sprint 57.20 was 63; +1 NEW chatStore.mergeEvent.test.ts) ✅
- [x] `npm run lint` silent (--max-warnings 0 enforced) ✅
- [x] `npx vite build` succeeds 3.12s; main bundle **320.76 kB byte-identical** to Sprint 57.20 baseline (type-shape change + mergeEvent expansion absorbed by tree-shaking) ✅
- [ ] **Behavioral preservation smoke test**: dev server manual verify (deferred to Day 2 closeout once TurnList is in to validate full visual + behavioral baseline)
- [x] Progress.md Day 1 entry + Day 1 drift findings recorded ✅
- [x] Day 1 commit: `feat(chat-v2, sprint-57-21, Day 1): Turn block data model rewrite (types + chatStore + adapter + 22 Vitest)` — consolidated 1.1+1.2+1.3 to avoid broken intermediate

---

## Day 2 — Turn renderer + Block components (US-C1 + US-C2 + US-C3) — **Option C cp+convert workflow**

**Workflow pivot (2026-05-17 Day 1 EOD per user directive)**: Option C copy-then-convert per plan §Day 1 EOD strategy pivot section.

### 2.0 Copy mockup baseline + scaffold target directories (~30 min)
- [ ] Create directories: `frontend/src/features/chat_v2/components/{turns,blocks,inspector}/` + ensure `fixtures/` ready for Day 3
- [ ] cp `reference/design-mockups/page-chat.jsx` → `frontend/src/features/chat_v2/components/_mockup-source.jsx.bak` (per-section reference; .bak extension keeps tsc/eslint from scanning; deleted Day 4 closeout)
- [ ] Identify per-section line ranges in mockup (record in DRIFT-REPORT-PHASE1.md §Section Mapping):
  - L73-91 ChatV2 shell (Day 3 target)
  - L93-121 ChatHeader (Day 3 target, inside ChatLayout)
  - L123-156 SessionList (Day 3 target)
  - L153-156 DomainDot helper (Day 3 fixture)
  - L159-163 TurnRender dispatcher (Day 2 — TurnList.tsx)
  - L165-176 UserTurn (Day 2)
  - L178-197 AgentTurn (Day 2)
  - L199-267 Block switch (Day 2 — split into 4 block files)
  - L270-313 HITLTurn + HITL approval card (Day 2 — ApprovalCard visual rewrite)
  - L316-368 Composer (Day 4 skeleton — full Phase-2+)
  - L371-390 ChatInspector (Day 4)
  - L392-417 InspectorTurn (Day 4)
  - L419-432 KV + EventLine helpers (Day 4)
  - L434-466 InspectorTrace (Day 4 — coming-soon)
  - L468-487 InspectorMemory (Day 4 — coming-soon)
  - L489-531 InspectorTree (Day 4 — coming-soon)

### 2.1 US-C1 TurnList + 3 Turn role components (cp+convert; ~2.5-3 hr)
- [ ] **EXTRACT + CONVERT** mockup L165-176 → `frontend/src/features/chat_v2/components/turns/UserTurn.tsx`:
  - useCs/useEcs imports → standard react
  - Inline `style={{...}}` → Tailwind utility classes (turn-rail / turn-marker / turn-head / turn-body equivalents via flex + border tokens)
  - `<span className="role">Jamie Liu</span>` → consume `authStore.user.name`
  - File-header w/ mockup line range cited
- [ ] **EXTRACT + CONVERT** mockup L178-197 → `frontend/src/features/chat_v2/components/turns/AgentTurn.tsx`:
  - Same conversion pattern
  - `<Badge tone="primary">turn {turn.id.replace("t", "")}</Badge>` → shadcn Badge variant
  - `<span className="live-dot">` → small `bg-warning rounded-full animate-pulse` element
  - Block dispatcher: `turn.blocks.map(b => <Block key={...} b={b} />)` referencing Day 2.2 block components
- [ ] **EXTRACT + CONVERT** mockup L270-313 → `frontend/src/features/chat_v2/components/turns/HITLTurn.tsx`:
  - Wraps existing ApprovalCard.tsx (preserves 2-action decide() wiring; visual rewrite handled by 2.3)
  - Pass `severity` / `payload` / `rationale` / `tool` etc. props from HITLTurn type
- [ ] **NEW** `frontend/src/features/chat_v2/components/TurnList.tsx` (~80 lines):
  - Consume `chatStore.turns`
  - Role dispatcher: turn.role === "user" → `<UserTurn>`; "agent" → `<AgentTurn>`; "hitl" → `<HITLTurn>`
  - Auto-scroll to bottom (preserve Sprint 57.20 baseline behavior)
  - Replaces `MessageList.tsx` consumers Day 3 (MessageList.tsx becomes thin re-export Day 2 EOD)
- [ ] All NEW files have file-header per `.claude/rules/file-header-convention.md` w/ mockup line range cited
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 2): TurnList + 3 Turn role components per mockup (cp+convert)`

### 2.2 US-C2 4 Block components (cp+convert; ~3-4 hr)
- [ ] **EXTRACT + CONVERT** mockup L200-207 → `frontend/src/features/chat_v2/components/blocks/ThinkingBlock.tsx`:
  - `bg-thinking/16 text-thinking` (Sprint 57.18 token) for label + body container
- [ ] **EXTRACT + CONVERT** mockup L208-223 → `frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx`:
  - Head + body + result sections; `bg-tool/16 text-tool` for icon + name; status badge variant per ok/error
  - Replaces `ToolCallCard.tsx` consumers Day 3 (ToolCallCard.tsx becomes thin re-export Day 2 EOD)
- [ ] **EXTRACT + CONVERT** mockup L234-244 → `frontend/src/features/chat_v2/components/blocks/VerificationBlock.tsx`:
  - check/x icon + claim + evidence; success/danger token; failed → border-danger
- [ ] **EXTRACT + CONVERT** mockup L245-264 → `frontend/src/features/chat_v2/components/blocks/SubagentForkBlock.tsx`:
  - Head + agent rows; chevron + name + task + status badge + turns count
- [ ] **NEW** `frontend/src/features/chat_v2/components/blocks/Block.tsx` dispatcher (~30 lines):
  - Discriminated union switch on block.type → render matching block component
- [ ] Vitest specs (~3-5 cases each block; total ~15-20 NEW cases)
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 2): 4 block components (thinking/tool/verification/subagent_fork) per mockup (cp+convert)`

### 2.3 US-C3 ApprovalCard visual rewrite (cp+convert; preserve 2-action backend) (~1.5 hr)
- [ ] **EXTRACT + CONVERT** mockup L280-309 (HITL approval card body) → REWRITE in-place `frontend/src/features/chat_v2/components/ApprovalCard.tsx`:
  - `hitl-card` CSS → Tailwind: `relative rounded-xl border border-warning/40 bg-bg-1 p-4 shadow-warning/10`
  - `hitl-card-bar` (left rail color) → `absolute left-0 top-0 bottom-0 w-0.5 bg-warning` (severity-tinted via Sprint 57.18 `risk-*` tokens)
  - severity → `<RiskBadge level={severity} />` (D-PRE-3: create `frontend/src/components/ui/RiskBadge.tsx` ~30 lines per STYLE.md §3 pattern OR inline within ApprovalCard for now; decide Day 2 start)
  - 4-button bar: Approve & continue (real wire) / Approve with edits (disabled coming-soon) / Reject (real wire) / Escalate to L2 (disabled coming-soon)
  - Preserve: existing `governanceService.decide(APPROVED | REJECTED)` wiring
  - Disabled coming-soon buttons: tooltip "Sprint 57.22+ AD-ChatV2-HITL-FourAction-Phase2"
- [ ] Update existing ApprovalCard Vitest spec + Playwright e2e selectors (D-PRE-1: `approval-card.spec.ts` sentinel `#b71c1c` — decide token vs hex literal at Day 2 time)
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 2): ApprovalCard visual rewrite per mockup HITLTurn (preserve 2-action backend)`

### 2.4 Day 2 closeout
- [ ] `npm run tsc` 0 errors
- [ ] `npm run test` Vitest 299+N PASS
- [ ] `npm run lint` silent (note: NEW components must have NO inline style — Sprint 57.16 guard remains active codebase-wide)
- [ ] `npm run build` succeeds; main bundle within +30 KB of Sprint 57.20 baseline
- [ ] Playwright MCP capture POST-Day-2 chat-v2 at 1440×900 → `screenshots/blocks/prod-chat-v2-day2.png` + per-block sub-zooms
- [ ] Pair-verify each block vs mockup section — DRIFT verdict per component (parity / cosmetic / structural) recorded in DRIFT-REPORT-PHASE1.md §Verification
- [ ] Progress.md Day 2 entry + cosmetic gaps logged for Day 4 retrospective

---

## Day 3 — SessionList sidebar + ChatLayout 3-column rewrite (US-D1 + US-D2 + US-D3)

**Workflow**: continues Day 2 Option C cp+convert. Source baseline: `_mockup-source.jsx.bak` (per §2.0). Each component file's MHist cites mockup line range.

### 3.1 US-D1 SessionList + fixtures (~2 hr)
- [ ] **NEW** `frontend/src/features/chat_v2/fixtures/sessions.ts` (~50 lines):
  - 6 fixture sessions verbatim from mockup `SESSIONS` L5-12 (id / title / agent / turns / status / time / domain)
- [ ] **NEW** `frontend/src/features/chat_v2/components/SessionList.tsx` (~150 lines per mockup L123-156):
  - "New session" button + filter button at top
  - "Sessions" + count label
  - Session item rendering: DomainDot (color map: incident/audit/patrol/rca) + title + status indicator (running/hitl/done) + agent + turns + time
  - Active session highlight (`data-active`)
  - onSelect → chatStore.setActiveSessionId
- [ ] Vitest spec for SessionList (~5 cases: 6 sessions render / DomainDot color map / active highlight / status indicator variants / click → setActiveSessionId)
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 3): SessionList sidebar + 6-session fixture per mockup`

### 3.2 US-D2 ChatLayout 2-col → 3-col (~1-2 hr)
- [ ] **REWRITE** `frontend/src/features/chat_v2/components/ChatLayout.tsx`:
  - 3-column grid: `[sessions-list 280px | chat-stream 1fr | inspector 360px]` per mockup `chat-shell`
  - State: `listOpen` + `inspOpen` toggles (default both `true` at 1440×900)
  - `data-list` + `data-insp` attributes for collapsing CSS
  - Mobile responsive: hide both side rails at <768px (per Sprint 57.13 a11y standards)
  - Left rail mount: `<SessionList />`
  - Center: existing TurnList + Composer
  - Right rail mount: `<ChatInspector />` (placeholder until Day 4 Inspector ships)
- [ ] Update existing ChatLayout Vitest spec selectors (preserve assertion structure)
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 3): ChatLayout 2-col → 3-col with collapsible side rails per mockup`

### 3.3 US-D3 Demo banner above SessionList (AP-2 compliance) (~30 min)
- [ ] **EDIT** SessionList.tsx to render a yellow `bg-warning/16 text-warning-foreground` banner above sessions list:
  - Text: "Demo data — backend list endpoint pending Sprint 57.22+ (AD-ChatV2-SessionList-Backend)"
  - i18n key: `chat.session.demoBanner` (en + zh-TW)
- [ ] i18n key add: `frontend/src/i18n/en/common.json` + `zh-TW/common.json`
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 3): SessionList demo banner for AP-2 compliance + i18n keys`

### 3.4 Day 3 closeout
- [ ] `npm run tsc` 0 errors
- [ ] `npm run test` Vitest 277+N PASS
- [ ] `npm run lint` silent
- [ ] `npm run build` succeeds
- [ ] Playwright MCP capture POST-Day-3 chat-v2 at 1440×900 → `screenshots/sessions-sidebar/prod-chat-v2-day3.png`
- [ ] Pair-verify SessionList + 3-col layout vs mockup — DRIFT verdict
- [ ] **Behavioral preservation smoke test**: open chat-v2, click each fixture session → state updates but stream stays on current session (no backend wire — expected)
- [ ] Progress.md Day 3 entry + cosmetic gaps logged

---

## Day 4 — Inspector Turn tab + Composer skeleton + closeout (US-E1 + US-E2 + US-E3)

**Workflow**: continues Day 2 Option C cp+convert. Source baseline: `_mockup-source.jsx.bak`. Day 4 final closeout deletes the `.bak` file.

### 4.1 US-E1 ChatInspector + InspectorTurn tab (~2-3 hr)
- [ ] **NEW** `frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx` (~80 lines per mockup L371-390):
  - 4-tab frame: Turn / Trace / Memory / Tree
  - State: `tab` selector (default "turn")
  - Render: tab === "turn" → `<InspectorTurn>`; else → `<ComingSoonInspectorTab name={...}>`
- [ ] **NEW** `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx` (~120 lines per mockup L392-417):
  - KV pairs (selectActiveTurn from chatStore): stop_reason / duration / tokens.in / tokens.out / tokens.thinking / cost / trace_id (placeholder "—" if SSE missing) / span_id (placeholder "—" if SSE missing)
  - "Block sequence" EventLine list (each block.type as colored dot + label + tone)
  - 2 buttons: "Open audit entry" + "Open in Loop Debug"
- [ ] **NEW** `frontend/src/features/chat_v2/components/inspector/ComingSoonInspectorTab.tsx` (~40 lines):
  - Empty state with mockup file hint + "Defer to Sprint 57.22+ AD-ChatV2-Inspector-{Trace,Memory,SubagentTree}-Phase2"
- [ ] Vitest spec for ChatInspector + InspectorTurn (~5-7 cases: tab switching / KV pairs render / EventLine list / trace_id placeholder fallback / buttons exist)
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 4): ChatInspector 4-tab frame + InspectorTurn populated + 3 coming-soon placeholders`

### 4.2 US-E2 Composer skeleton (~1-2 hr)
- [ ] **NEW** `frontend/src/features/chat_v2/components/Composer.tsx` (~100 lines per mockup L316-368 simplified):
  - Textarea + Send button (preserve InputBar state machine logic underneath — extract or proxy)
  - 3 disabled coming-soon buttons: Attach + Tools(24) + Memory scope
  - Model badge (claude-haiku-4-5) + "provider: neutral" indicator
- [ ] Decision: **extract InputBar state machine into a shared `useInputBarState()` hook OR proxy via prop pass-through?** — pick lower-risk option (proxy via composition probably; final call at Day 4 start based on InputBar.tsx complexity)
- [ ] **REWRITE in-place** `frontend/src/features/chat_v2/components/InputBar.tsx`: extract reusable state machine logic; render compat-shim wrapping Composer.tsx OR mark as deprecated re-export
- [ ] Update existing InputBar Vitest spec + chat-v2 Playwright e2e (selector adapt; behavioral assertions preserve — 5 status states + send button + keyboard shortcuts)
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 4): Composer skeleton + 3 disabled coming-soon buttons + InputBar state machine preserve`

### 4.3 Test + build + behavior sanity (~30 min)
- [ ] `pytest backend/tests/` 0 regression (pure frontend sprint; backend untouched)
- [ ] `npm run test` Vitest 277+N PASS
- [ ] `npm run build` < 3s + main bundle within +30 KB of Sprint 57.20 baseline (320.76 kB)
- [ ] `npm run lint` silent
- [ ] LLM SDK leak check `grep -rn "import openai\|import anthropic" frontend/src/` = 0
- [ ] `npx playwright test tests/e2e/chat-v2/` 10/10 PASS (selectors adapted; behavioral assertions preserved)
- [ ] CI 7 checks projected green (verify after PR opens)
- [ ] Playwright MCP capture POST-Day-4 chat-v2 at 1440×900 → `screenshots/inspector-turn/prod-chat-v2-day4.png` overall + sub-zooms (3 columns + Inspector tabs + Composer)
- [ ] Pair-verify final vs `screenshots/mockup-chat-v2.png` — overall DRIFT verdict for Phase-1 (parity for shipped pieces; deferred items listed)

### 4.4 Retrospective + memory + doc syncs (US-E3) (~1-2 hr)
- [ ] Create `retrospective.md` Q1-Q7 + Anti-Pattern 11/11 self-check + calibration analysis (2nd app of `frontend-mockup-direct-port` 0.55 class — compute `actual/committed` ratio + 2-data-point trend comment)
- [ ] Update `memory/project_phase57_21_chatv2_fidelity_phase_1.md` (new file)
- [ ] Update `memory/MEMORY.md` (+1 line for Sprint 57.21)
- [ ] Update `.claude/rules/sprint-workflow.md` calibration matrix (`frontend-mockup-direct-port` 2nd app row update + 2-data-point trend evaluation)
- [ ] Update CLAUDE.md V2 Refactor Status table:
  - Phase 57+ Frontend 17/N → 18/N
  - Latest Sprint row = 57.21 detail
  - Prev Sprint row shift (57.20 → Prev)
  - main HEAD update (after merge)
  - Next Phase 候選 row update (Sprint 57.22+ candidates: AD-ChatV2-Full-Mockup-Fidelity Phase-2+ / AD-Mockup-Direct-Port-Round-2 / Backend wire bundle)
- [ ] Update SITUATION-V2-SESSION-START.md §第八部分 (recent sprints + Phase 57.21 carryovers)
- [ ] Update `claudedocs/CLAUDE.md` index if needed
- [ ] Update `claudedocs/4-changes/sprint-57-21-chatv2-fidelity-phase-1/DRIFT-REPORT-PHASE1.md` (Phase 58+ epic gap catalogue: 6+ NEW carryover ADs)

### 4.5 PR + closeout
- [ ] PR: `feat(frontend, sprint-57-21): AD-ChatV2-Full-Mockup-Fidelity Phase-1 — Turn Block Model + SessionList + Inspector Turn Tab (Frontend-Only Spike)`
- [ ] CI 7 checks green
- [ ] PR merged to main (squash)
- [ ] If 4 doc syncs not bundled into main PR → Closeout PR (chore) with doc syncs
- [ ] Closeout PR merged to main

---

## Anti-Pattern self-check (per `.claude/rules/anti-patterns-checklist.md`)

- [ ] **AP-1 No god component**: NEW components stay under 200 lines each (TurnList ~120 / Composer ~100 / SessionList ~150 / InspectorTurn ~120 / 4 blocks ~30-70 each)
- [ ] **AP-2 No Potemkin**: SessionList ships fixture data with visible "Demo data — backend wire pending Sprint 57.22+" banner; coming-soon tabs render explicit empty-state placeholder; disabled buttons have tooltip explaining defer
- [ ] **AP-3 No cross-directory scattering**: blocks/* + inspector/* + turns/* + Composer + SessionList + fixtures all under `features/chat_v2/`
- [ ] **AP-4 No rename-only refactor**: every rewrite (types.ts + mergeEvent + ChatLayout + ApprovalCard) delivers visible mockup-fidelity gain (Playwright MCP pair-verify artifact required)
- [ ] **AP-5 No hardcoded secrets**: 0 changes to .env / config / token storage
- [ ] **AP-6 No silent backend assumptions**: 0 backend changes; existing hooks consume existing endpoints + 14 SSE event types
- [ ] **AP-7 No prop drilling > 2 levels**: Turn role components consume chatStore via hooks (NOT props from ChatLayout)
- [ ] **AP-8 No event handler swallowing errors**: SSE / HITL handlers preserved verbatim in chatStore.mergeEvent
- [ ] **AP-9 No race conditions**: TanStack Query handles refetch; no manual `useEffect` data loops added; chatStore mergeEvent is synchronous reducer
- [ ] **AP-10 No untested critical path**: NEW components have Vitest specs; chat-v2 Playwright e2e 10/10 preserved
- [ ] **AP-11 No TypeScript `any` leak**: Turn + Block discriminated unions fully typed; 0 new `any`; tsc 0 errors required

---

## Carryover (preserve per CLAUDE sacred rule: 🚧 marker + reason)

🚧 **AD-ChatV2-Memory-Block-Phase2** (NEW Sprint 57.21) — Cat 3 backend `memory_accessed` SSE event emission + frontend memory block component; Sprint 57.22+
🚧 **AD-ChatV2-HITL-FourAction-Phase2** (NEW Sprint 57.21) — governance approve-with-edits backend + Escalate to L2 + SLA countdown + frontend 4-action UX; Sprint 57.22+
🚧 **AD-ChatV2-Composer-Richness-Phase2** (NEW Sprint 57.21) — attachments upload + Tools(24) menu wire + Memory scope filter; Sprint 57.22+
🚧 **AD-ChatV2-Inspector-Trace-Phase2** (NEW Sprint 57.21) — Cat 12 OTel spans per session endpoint + waterfall UI; Sprint 57.22+
🚧 **AD-ChatV2-Inspector-Memory-Phase2** (NEW Sprint 57.21) — Cat 3 memory ops list per session endpoint + UI; Sprint 57.22+
🚧 **AD-ChatV2-Inspector-SubagentTree-Phase2** (NEW Sprint 57.21) — Cat 11 subagent live feed endpoint + tree UI; Sprint 57.22+
🚧 **AD-ChatV2-SessionList-Backend** (NEW Sprint 57.21) — GET /api/v1/sessions list endpoint; Sprint 57.22+
🚧 **AD-Cat12-SSE-Trace-Id-Phase2** (potential NEW Sprint 57.21) — if Inspector Turn tab placeholder for trace_id/span_id proves common: Sprint 57.22+
🚧 **AD-Composer-StateMachine-Migration-Phase2** (potential NEW Sprint 57.21) — if InputBar state machine extraction proves complex: Sprint 57.22+
🚧 **AD-Mockup-Direct-Port-Round-2** (Sprint 57.20 carryover) — 8 remaining ship pages + 11 R2 findings; Sprint 57.22+ or Sprint 57.23+
🚧 **AD-Geist-Font-Asset-Bundling** (Sprint 57.20 carryover) — Phase 58+
🚧 **Sprint 57.19 backend wire ADs bundle** (8 total) — Sprint 57.22+
🚧 **AD-Tailwind-v4-Config-Migration** (Sprint 57.17 carryover) — Sprint 57.22+ or later
🚧 **AD-CI-7-GHA-PR-Permission** (Sprint 57.17 carryover) — independent infra track
🚧 **AD-Lighthouse-Visual-Hard-Gate** (longstanding carryover) — Sprint 57.22+ candidate
🚧 **AD-A11y-Structural-Nits** (Sprint 57.16 carryover) — may be partially closed by ChatLayout 3-col rewrite if heading-order / landmark-main duplication addressed; verify Day 4 Playwright a11y scan
