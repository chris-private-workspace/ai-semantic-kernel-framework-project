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
- [ ] Commit Day 0 artifacts: `chore(sprint-57-21, Day 0): plan + checklist + Day 0 三-prong + Playwright MCP reference captures`

---

## Day 1 — Turn block data model rewrite (US-B1 + US-B2 + US-B3)

### 1.1 US-B1 types.ts refactor — Turn discriminated union (~1-2 hr)
- [ ] Read `reference/design-mockups/page-chat.jsx` L14-70 (TURNS data shape) + L199-267 (Block switch) end-to-end
- [ ] **REWRITE** `frontend/src/features/chat_v2/types.ts`:
  - Preserve: 14 SSE event types + `KNOWN_LOOP_EVENT_TYPES` set + `ChatStatus` + `ChatMode` + `ChatSession`
  - Add NEW: `Block` discriminated union (thinking / tool / verification / subagent_fork) — 4 of 5 mockup types; memory deferred
  - Add NEW: `Turn` discriminated union (user / agent / hitl) per mockup data shape
  - Add NEW: `Session` interface (id / title / agent / turns / status / time / domain) for fixture
  - Replace: `Message` type → mark as `@deprecated; use Turn` and add compat alias `export type Message = Turn` if needed for external consumers
  - Add file-header Modification History 1-line entry
- [ ] `npm run tsc` — confirm 0 type errors
- [ ] Commit: `refactor(chat-v2, sprint-57-21, Day 1): types.ts Message → Turn discriminated union with 4 Block types`

### 1.2 US-B2 chatStore.mergeEvent rewrite (~3-4 hr)
- [ ] Read current `chatStore.ts` `mergeEvent` end-to-end; enumerate each event-type case's existing behavioral contract
- [ ] **REWRITE** `chatStore.ts`:
  - State shape change: `{ messages: Message[] }` → `{ turns: Turn[], sessions: Session[], activeSessionId: string | null }` (sessions populated from fixture in Day 3)
  - mergeEvent per plan §Technical Spec table (loop_start / turn_start / llm_request / llm_response / tool_call_request / tool_call_result / verification_passed / verification_failed / subagent_spawned / subagent_completed / loop_end / approval_requested / approval_received / guardrail_triggered)
  - Each event-type case must preserve existing behavioral side effects (status update / approval entry / rawEvents append for unhandled)
  - Add active-turn metadata aggregation for Inspector Turn tab data (tokens_in / tokens_out / tokens_thinking / cost / trace_id / span_id — placeholder "—" for trace_id/span_id if not in SSE)
  - Add file-header Modification History 1-line entry
- [ ] **DO NOT TOUCH**: `useLoopEventStream` hook signature; `chatService` API contract; `governanceService.decide` usage
- [ ] Commit: `refactor(chat-v2, sprint-57-21, Day 1): chatStore.mergeEvent SSE event → block sequence append (preserve 14 event-type behavior)`

### 1.3 US-B3 Vitest mergeEvent block-sequence coverage (~1-2 hr)
- [ ] Update existing chat-v2 Vitest specs (~3-4 files) adapting to new state shape:
  - Selector: `messages[i].content` → `turns[i].blocks[j]` or `turns[i].text`
  - Behavioral assertion preserve: SSE event dispatch order; approval entry insertion; status transitions
- [ ] **NEW Vitest spec** `frontend/src/features/chat_v2/store/chatStore.mergeEvent.test.ts`:
  - ~15-20 NEW cases:
    - turn_start emits new agent Turn with empty blocks
    - llm_response with thinking emits thinking block
    - tool_call_request + tool_call_result pair emits + updates single tool block (toolCallId pairing)
    - verification_passed emits verification block ok=true
    - verification_failed emits verification block ok=false with reason/suggested_correction
    - subagent_spawned creates/extends subagent_fork block with new agent entry
    - subagent_completed updates agent entry status
    - approval_requested emits new hitl Turn with severity from risk_level
    - approval_received updates hitl turn decision
    - loop_end no block emit (only session status update)
    - guardrail_triggered routes to rawEvents (Phase-1 — no block UI)
- [ ] `npm run test` Vitest 277+ PASS (baseline + new cases; no regression)
- [ ] Commit: `test(chat-v2, sprint-57-21, Day 1): mergeEvent block-sequence Vitest coverage + chat-v2 spec selector adapt`

### 1.4 Day 1 closeout
- [ ] `npm run tsc` 0 errors
- [ ] `npm run test` (Vitest) baseline preserved + grown
- [ ] `npm run lint` silent (`--max-warnings 0`)
- [ ] `npm run build` succeeds + main bundle within +30 KB
- [ ] **Behavioral preservation smoke test**: dev server send a message in chat-v2; observe SSE stream renders Turn-with-blocks (verification + tool call should appear inline now); approve HITL request — workflow unbroken
- [ ] Progress.md Day 1 entry + Day 1 drift findings if any

---

## Day 2 — Turn renderer + Block components (US-C1 + US-C2 + US-C3)

### 2.1 US-C1 TurnList + 3 Turn role components (~2 hr)
- [ ] **NEW** `frontend/src/features/chat_v2/components/turns/UserTurn.tsx` (~40 lines per mockup L165-176)
- [ ] **NEW** `frontend/src/features/chat_v2/components/turns/AgentTurn.tsx` (~80 lines per mockup L178-197)
- [ ] **NEW** `frontend/src/features/chat_v2/components/turns/HITLTurn.tsx` (~120 lines per mockup L270-313) — wraps existing ApprovalCard.tsx (preserve 2-action decide() wiring; visual rewrite only)
- [ ] **NEW** `frontend/src/features/chat_v2/components/TurnList.tsx` (~120 lines):
  - Role dispatcher: turn.role === "user" → `<UserTurn>`; "agent" → `<AgentTurn>`; "hitl" → `<HITLTurn>`
  - Replaces `MessageList.tsx`; thin compat re-export if MessageList used externally
- [ ] All NEW files have file-header per `.claude/rules/file-header-convention.md`
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 2): TurnList + 3 Turn role components per mockup`

### 2.2 US-C2 4 Block components (~2-3 hr)
- [ ] **NEW** `frontend/src/features/chat_v2/components/blocks/ThinkingBlock.tsx` (~30 lines per mockup L200-207)
  - Use `bg-thinking/16 text-thinking` tokens (Sprint 57.18) or `bg-bg-2 text-fg-muted` (Sprint 57.20)
- [ ] **NEW** `frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx` (~70 lines per mockup L208-223)
  - Head: tool icon + name + status badge (success/danger) + duration
  - Body: input pre-block (JSON) + output pre-block (result)
  - Replaces `ToolCallCard.tsx`; thin compat re-export if used externally
- [ ] **NEW** `frontend/src/features/chat_v2/components/blocks/VerificationBlock.tsx` (~50 lines per mockup L234-244)
  - check/x icon + claim + evidence
  - Failed variant: `border-danger` tone
- [ ] **NEW** `frontend/src/features/chat_v2/components/blocks/SubagentForkBlock.tsx` (~60 lines per mockup L245-264)
  - Head: fork icon + "Fork · concurrent" + spawned N count
  - Rows: chevron + agent name + task + status badge + turns count
- [ ] Each block component has Vitest spec (~3-5 cases each: render + props + status variants)
- [ ] Wire blocks into `AgentTurn.tsx`: `turn.blocks.map(b => <Block key={b.id} b={b} />)` where `<Block>` dispatches per `b.type`
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 2): 4 block components (thinking/tool/verification/subagent_fork) per mockup`

### 2.3 US-C3 ApprovalCard visual rewrite (preserve 2-action backend wiring) (~1 hr)
- [ ] **REWRITE in-place** `frontend/src/features/chat_v2/components/ApprovalCard.tsx`:
  - Visual: severity badge (`risk-low/medium/high/critical`) + tool name + policy badge + scope badge + rationale + payload pre-block + 4-button bar (Approve & continue / Approve with edits [disabled coming-soon] / Reject / Escalate to L2 [disabled coming-soon]) + audit_id footer per mockup L280-309
  - Preserve: existing `governanceService.decide(APPROVED | REJECTED)` wiring on Approve / Reject buttons
  - Disabled coming-soon buttons: `disabled` + tooltip "Sprint 57.22+ (AD-ChatV2-HITL-FourAction-Phase2)"
- [ ] Update existing ApprovalCard Vitest spec + Playwright e2e selectors (preserve behavioral assertions)
- [ ] Commit: `feat(chat-v2, sprint-57-21, Day 2): ApprovalCard visual rewrite per mockup HITLTurn (preserve 2-action backend)`

### 2.4 Day 2 closeout
- [ ] `npm run tsc` 0 errors
- [ ] `npm run test` Vitest 277+N PASS
- [ ] `npm run lint` silent
- [ ] `npm run build` succeeds
- [ ] Playwright MCP capture POST-Day-2 chat-v2 at 1440×900 → `screenshots/blocks/prod-chat-v2-day2.png` + sub-zooms
- [ ] Pair-verify vs `screenshots/mockup-chat-v2.png` — DRIFT verdict for Turn renderer + 4 blocks (parity / cosmetic / structural)
- [ ] Progress.md Day 2 entry + cosmetic gaps logged for Day 4 closeout

---

## Day 3 — SessionList sidebar + ChatLayout 3-column rewrite (US-D1 + US-D2 + US-D3)

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
