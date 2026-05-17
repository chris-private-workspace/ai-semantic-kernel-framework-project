---
sprint: 57.21
phase: Phase 57+ Frontend SaaS 18/N (pending close)
title: AD-ChatV2-Full-Mockup-Fidelity Phase-1 — Turn Block Model + SessionList + Inspector Turn Tab (Frontend-Only Spike)
class: frontend-mockup-direct-port 0.55 (2nd application; HYBRID weighted blend)
duration_days: 5 (Day 0 setup + Day 1 types/mergeEvent rewrite + Day 2 TurnList + Block components + Day 3 SessionList + ChatLayout 3-col + Day 4 Inspector + Composer skeleton + closeout)
related:
  - Sprint 57.20 plan + retrospective (AD-Mockup-Direct-Port Foundation Option W)
  - Sprint 57.20 D-DAY3-1 finding (mockup page-chat.jsx ~10× richer UX than current)
  - Sprint 57.19 retrospective Q4 + Q5 (10 NEW carryover ADs)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17)
  - memory/feedback_frontend_mockup_fidelity_hard_constraint.md
  - reference/design-mockups/page-chat.jsx (533L target UX)
  - .claude/rules/sprint-workflow.md calibration matrix (§Scope-class multiplier matrix)
  - 01-eleven-categories-spec.md §Cat 1 (loop) + Cat 3 (memory) + Cat 10 (verification) + Cat 11 (subagent) + Cat 12 (observability)
  - 17-cross-category-interfaces.md §SSE LoopEvent contracts
---

# Sprint 57.21 — AD-ChatV2-Full-Mockup-Fidelity Phase-1

## Sprint Goal

Establish the **Turn-block data model + 3-column chat shell** as the canonical chat-v2 rendering foundation, validated by 4 of 5 block types rendered 1:1 from mockup `page-chat.jsx`, while reusing 100% of existing chat-v2 behavioral logic (SSE event handler / HITL approval workflow / InputBar state machine / Cat 9 audit logging path / TanStack Query / authStore).

**Two-line philosophy** (continued from Sprint 57.20 Option W):

1. **Frontend leads** — presentation + data-shape layer rewritten 1:1 from mockup; no incremental patching.
2. **Backend follows** — existing functional layer reused; backend SSE event additions (memory_accessed) + new endpoints (GET /api/v1/sessions list) + HITL 4-action backend deferred to Sprint 57.22+ wire ADs.

## Background

### Why Phase-1 (this sprint)

Sprint 57.20 Day 3 (D-DAY3-1) discovered the mockup `page-chat.jsx` (533 lines) has ~10× richer UX than current `features/chat_v2/`:

| Layer | Mockup target | Current baseline | Phase-1 shipping? |
|-------|---------------|------------------|-------------------|
| Data model | Turn `{ role, at, id, stopReason, duration, blocks: Block[] }` with 5 block types | Flat `Message = user \| assistant` + thinking + flat `toolCalls[]` | ✅ Refactor (4/5 block types ship; memory defer) |
| SessionList sidebar | 6 sessions w/ DomainDot + status + agent + turns + time | None | ✅ Fixture-driven |
| HITL approval | 4-action (Approve / Approve with edits / Reject / Escalate to L2) + SLA countdown + severity badge + payload + rationale | 2-action (decide APPROVED/REJECTED) | ❌ Defer Sprint 57.22+ (AD-ChatV2-HITL-FourAction-Phase2) |
| Composer | Attachments + Tools(24) menu + Memory scope menu + model badge + Send | Plain InputBar | ✅ Skeleton only (Composer.tsx replaces InputBar visual; richness defer) |
| Inspector right rail | 4 tabs (Turn / Trace / Memory / Subagent tree) | None | ✅ Frame + Turn tab populated; 3 other tabs coming-soon |
| Block types | thinking / tool / memory / verification / subagent_fork | thinking text + tool call cards (verification + subagent SSE events route to rawEvents but no UI) | ✅ 4 of 5 (memory defers — needs NEW Cat 3 SSE event) |

This is **Phase-1 of a multi-sprint epic** (Phase 58+; estimated 5-6 sprints total). Phase-1 establishes the **data model + presentation foundation**. Phase-2+ adds backend wire bundle + remaining 3 Inspector tabs + memory block + HITL 4-action + Composer richness.

### What is preserved (NOT rewritten)

| Layer | Specific | Reuse mechanism |
|-------|----------|-----------------|
| Auth | `RequireAuth` + `authStore` + WorkOS OIDC | Pages stay wrapped |
| API client | `fetchWithAuth` + tenant_id header | chatService unchanged for stream endpoint |
| SSE event handler | `useLoopEventStream` hook | Internal `mergeEvent` rewritten but hook signature preserved |
| HITL approval workflow | `governanceService.decide` + optimistic store update + SSE ApprovalReceived overwrite | ApprovalCard internal logic unchanged (2-action UX stays this sprint; visual rewrite per mockup partial) |
| InputBar state machine | 5 statuses (idle/sending/streaming/awaiting_approval/error) | Logic preserved; visual subsumed into Composer skeleton |
| Cat 9 audit logging path | Loop emits audit events via backend | Frontend doesn't change |
| Mode toggle | echo_demo / real_llm | Preserved |
| Keyboard shortcuts | Enter / Shift+Enter / ⌘K | Preserved |
| Risk level color mapping | `STYLE.md §3` `text-[#hex]` | Preserved |
| TanStack Query | invalidation + retry | Provider stays at app root |
| 14 backward-compat pages | All other routes | NOT touched (chat-v2 isolated work) |

### What gets rewritten (this sprint scope)

| Layer | Specific | Approach |
|-------|----------|----------|
| `types.ts` Message → Turn | discriminated union `{ role: "user" \| "agent" \| "hitl", blocks: Block[] }` with 4 Block types | Mockup `page-chat.jsx` L14-70 data model |
| `chatStore.mergeEvent` | SSE events → block sequence append by arrival order | Preserve all 14 known event types' behavior; emit blocks instead of flat fields |
| `MessageList.tsx` → `TurnList.tsx` | Turn renderer dispatching to `Block` component per type | Mockup `TurnRender` + `Block` L159-267 |
| NEW `components/blocks/{ThinkingBlock,ToolBlock,VerificationBlock,SubagentForkBlock}.tsx` | 4 Block components | Mockup `Block` switch arms |
| NEW `SessionList.tsx` | Left rail 6-session fixture sidebar | Mockup `SessionList` L123-156 |
| `ChatLayout.tsx` | 2-column → 3-column collapsible | Mockup `ChatV2` shell L73-91 |
| NEW `inspector/ChatInspector.tsx` | 4-tab frame | Mockup `ChatInspector` L371-390 |
| NEW `inspector/InspectorTurn.tsx` | KV pairs + EventLine list | Mockup `InspectorTurn` L392-417 |
| NEW `Composer.tsx` | Textarea + Send button skeleton (richness defer) | Mockup `Composer` L316-368 simplified |
| NEW `fixtures/sessions.ts` | 6 fixture sessions matching mockup data | Mockup `SESSIONS` L5-12 |

### 17.md / V2 紀律對齊

- **約束 1 單一範疇歸屬**: 純 frontend sprint; all changes in `frontend/src/features/chat_v2/`
- **約束 2 主流量驗證**: chat-v2 is UnifiedChat-V2 main path; runtime Playwright MCP pair-verify required at Day 2 + Day 4 closeout
- **約束 3 LLM Provider Neutrality**: 0 SDK import; preserved
- **約束 4 Anti-Pattern checklist**:
  - AP-2 (no Potemkin): SessionList ships fixture data — must visibly mark as "demo" coming-soon banner; NOT silently mocked production
  - AP-4 (rename-only refactors prohibited): every rewrite delivers visible mockup-fidelity gain (Playwright MCP pair-verify artifact required)
  - AP-3 (cross-directory scattering): new block components stay in `features/chat_v2/components/blocks/`; inspector stays in `features/chat_v2/components/inspector/`
- **約束 5 測試優先**: Vitest baseline 277 preserved; new components add Vitest specs; chat-v2 Playwright e2e baseline 10/10 preserved (selector adapt only)

## User Stories

### Group A — Setup + Day 0 三-prong + Playwright MCP reference captures (Day 0)

**US-A1**: As a Sprint 57.21 owner, I want plan/checklist landed + feature branch created + Day 0 三-prong path/content/schema verify + Playwright MCP screenshot pipeline confirmed + mockup `page-chat.jsx` reference capture at 1440×900 saved so that Day 1+ work has visual ground truth artifacts.

### Group B — Turn block data model rewrite (Day 1)

**US-B1**: As a developer, I want `types.ts` refactored from flat `Message = user | assistant` to Turn-based discriminated union `{ role, blocks: Block[] }` with 4 Block types (thinking / tool / verification / subagent_fork) so that the data model expresses the mockup's block-sequence semantics.

**US-B2**: As a developer, I want `chatStore.mergeEvent` rewritten to append blocks in SSE event arrival order (thinking from LLMResponse.thinking + tool from ToolCallRequest+Result pairing + verification from VerificationPassed/Failed events + subagent_fork from SubagentSpawned event) while preserving all 14 known event types' existing behavioral contracts (no regression in HITL approval workflow, InputBar state machine, Cat 9 audit path).

**US-B3**: As a tester, I want Vitest coverage on `mergeEvent` block-sequence logic (~15-20 NEW cases covering each event type's block emission) so that future Phase-2+ refactor doesn't silently regress.

### Group C — Turn renderer + Block components (Day 2)

**US-C1**: As an operator viewing a chat session, I want `TurnList.tsx` (replacing `MessageList.tsx`) to render Turn role dispatcher (UserTurn / AgentTurn / HITLTurn) 1:1 per mockup `page-chat.jsx` L159-197 so that the conversation thread matches mockup visual.

**US-C2**: As an operator, I want 4 block components (`ThinkingBlock` / `ToolBlock` / `VerificationBlock` / `SubagentForkBlock`) rendered inline within AgentTurn body 1:1 per mockup `Block` switch arms (L199-267) so that thinking text + tool calls + verification claims + subagent fork lists display per design.

**US-C3**: As an operator, I want existing `ApprovalCard` HITL render path preserved (2-action UX; 4-action defer to Sprint 57.22+) with visual updated per mockup `HITLTurn` L270-313 (countdown + severity + payload + rationale + buttons) so that approval critical path is visually mockup-faithful even though backend action set is unchanged.

### Group D — SessionList sidebar + ChatLayout 3-column rewrite (Day 3)

**US-D1**: As an operator, I want `SessionList.tsx` (NEW left rail) rendering 6 fixture sessions (mockup `SESSIONS` L5-12 verbatim) with DomainDot + title + status (running/hitl/done) + agent + turns + time + active highlight + "New session" button + filter button 1:1 per mockup so that session navigation UI ships even though backend list endpoint is deferred to Sprint 57.22+ (AD-ChatV2-SessionList-Backend).

**US-D2**: As an operator, I want `ChatLayout.tsx` rewritten from 2-column to **3-column** with collapsible left rail (SessionList) + center (Turn thread + Composer) + collapsible right rail (Inspector) per mockup `ChatV2` shell (L73-91) so that the chat page layout matches mockup at 1440×900.

**US-D3**: As an operator, I want a visible "Demo data — backend wire pending Sprint 57.22+" banner above SessionList while sessions are fixture-driven so that AP-2 (no Potemkin) is honored.

### Group E — Inspector Turn tab + Composer skeleton + closeout (Day 4)

**US-E1**: As an operator inspecting a turn's details, I want `ChatInspector.tsx` (NEW right rail) with 4-tab frame (Turn / Trace / Memory / Subagent tree) where the Turn tab is populated 1:1 per mockup `InspectorTurn` L392-417 (KV pairs: stop_reason / duration / tokens.in / tokens.out / tokens.thinking / cost / trace_id / span_id + block sequence EventLine list + "Open audit entry" + "Open in Loop Debug" buttons) and the 3 other tabs render coming-soon empty state placeholder.

**US-E2**: As an operator, I want `Composer.tsx` (NEW; replaces `InputBar.tsx` visually) rendering textarea + Send button per mockup `Composer` L316-368 simplified, while preserving InputBar state machine behavioral logic (5 statuses) underneath; Attachments + Tools(24) menu + Memory scope menu buttons render as disabled coming-soon UI.

**US-E3**: As a Sprint 57.21 owner, I want commits + retrospective.md + memory snapshot + in-sprint doc syncs (CLAUDE.md / MEMORY.md / sprint-workflow.md calibration matrix +1 row for 2nd app + SITUATION §第八部分) landed so that Sprint 57.21 = COMPLETE and Phase 57+ Frontend 18/N opens cleanly.

## Technical Specifications

### types.ts refactor — Turn block discriminated union

```typescript
// NEW Turn-based model (mockup page-chat.jsx L17-70 data shape)
export type Block =
  | { type: "thinking"; text: string }
  | { type: "tool"; name: string; status: "ok" | "error"; durationMs: number; input: string; output: string; toolCallId: string }
  | { type: "verification"; ok: boolean; claim: string; evidence: string; verifier: string }
  | { type: "subagent_fork"; agents: Array<{ id: string; name: string; task: string; status: "running" | "done"; turns: number }> };

export type Turn =
  | { role: "user"; id: string; at: string; text: string }
  | {
      role: "agent";
      id: string;
      at: string;
      stopReason: string | null;
      durationMs: number | null;
      blocks: Block[];
      waiting?: boolean;
    }
  | {
      role: "hitl";
      id: string;
      at: string;
      title: string;
      severity: "risk-low" | "risk-medium" | "risk-high" | "risk-critical";
      tool: string;
      payload: string;
      rationale: string;
      approvalRequestId: string;
      decision: string | null;
    };

// PRESERVED: ChatStatus / ChatMode / ChatSession (no shape change)
// REMOVED: Message type (replaced by Turn) — but emit a backward-compat alias for any consumer outside chat_v2/
```

### chatStore.mergeEvent rewrite

Current flat `Message` shape → Turn-with-blocks shape:

| SSE Event | Block emission |
|-----------|----------------|
| `loop_start` | Reset turns array; init session metadata |
| `turn_start` | Append new Turn `{ role: "agent", id, at, blocks: [], stopReason: null }` |
| `llm_request` | Update active turn metadata (tokens_in tracking — feeds Inspector Turn tab) |
| `llm_response` | If `data.thinking` non-empty → append `{ type: "thinking", text }` to active turn's blocks |
| `tool_call_request` | Append `{ type: "tool", name, status: "pending", input: stringify(args), toolCallId }` to active turn's blocks |
| `tool_call_result` | Find matching toolCallId block, set `status: ok/error`, `output`, `durationMs` |
| `verification_passed` | Append `{ type: "verification", ok: true, claim, evidence: "", verifier }` (mockup shows claim+evidence; current SSE has only score — defer evidence enrichment) |
| `verification_failed` | Append `{ type: "verification", ok: false, claim: reason ?? "", evidence: suggested_correction ?? "", verifier }` |
| `subagent_spawned` | Find-or-create `{ type: "subagent_fork", agents: [] }` block in active turn; append agent entry `{ id, name: subagent_id, task: "spawned", status: "running", turns: 0 }` |
| `subagent_completed` | Find subagent entry by id; update `status: "done"`, `turns: tokens_used` (proxy) |
| `loop_end` | Mark session status; no block emit |
| `approval_requested` | Append NEW Turn `{ role: "hitl", ... }` with severity from `risk_level` |
| `approval_received` | Find HITL turn by approvalRequestId; update `decision` field |
| `guardrail_triggered` | Append to active turn's blocks (NEW visual: gated by Phase-2 — for Phase-1, route to rawEvents only as today) |

### Component file change list

**NEW files**:

- `frontend/src/features/chat_v2/components/SessionList.tsx` (~150 lines; mockup L123-156 + DomainDot helper)
- `frontend/src/features/chat_v2/components/TurnList.tsx` (~120 lines; replaces MessageList.tsx role dispatch)
- `frontend/src/features/chat_v2/components/turns/UserTurn.tsx` (~40 lines; mockup L165-176)
- `frontend/src/features/chat_v2/components/turns/AgentTurn.tsx` (~80 lines; mockup L178-197)
- `frontend/src/features/chat_v2/components/turns/HITLTurn.tsx` (~120 lines; mockup L270-313 — visual rewrite of ApprovalCard wrapping)
- `frontend/src/features/chat_v2/components/blocks/ThinkingBlock.tsx` (~30 lines)
- `frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx` (~70 lines; replaces ToolCallCard or co-exists)
- `frontend/src/features/chat_v2/components/blocks/VerificationBlock.tsx` (~50 lines)
- `frontend/src/features/chat_v2/components/blocks/SubagentForkBlock.tsx` (~60 lines)
- `frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx` (~80 lines; 4-tab frame)
- `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx` (~120 lines; KV + EventLine list)
- `frontend/src/features/chat_v2/components/Composer.tsx` (~100 lines; skeleton — textarea + Send + 3 coming-soon buttons)
- `frontend/src/features/chat_v2/fixtures/sessions.ts` (~50 lines; 6 fixture sessions verbatim from mockup)

**REWRITE files**:

- `frontend/src/features/chat_v2/types.ts` (Message → Turn discriminated union; preserve ChatStatus / ChatMode / ChatSession / LoopEvent union)
- `frontend/src/features/chat_v2/store/chatStore.ts` (mergeEvent → block append; new state shape with `sessions: Session[]` + `activeSessionId` + `turns: Turn[]`)
- `frontend/src/features/chat_v2/components/ChatLayout.tsx` (2-col → 3-col with collapsible rails; state `listOpen` + `inspOpen`)

**MARKED FOR REMOVAL** (after Day 2 TurnList ship):

- `frontend/src/features/chat_v2/components/MessageList.tsx` — replaced by TurnList; keep thin re-export `export { TurnList as MessageList }` if external consumer found, else delete
- `frontend/src/features/chat_v2/components/ToolCallCard.tsx` — replaced by `blocks/ToolBlock.tsx`; keep thin re-export if needed, else delete
- `frontend/src/features/chat_v2/components/ApprovalCard.tsx` — REWRITE in-place to render new HITLTurn visual; preserve existing decide() wiring

**EDIT files**:

- `frontend/src/i18n/en/common.json` + `zh-TW/common.json` — add `chat.session.*` / `chat.inspector.*` / `chat.block.*` / `chat.composer.*` keys (~30-40 per locale)
- `frontend/src/features/chat_v2/components/InputBar.tsx` — wrap/extract state machine logic into Composer.tsx; thin compat re-export for external consumers
- existing Vitest specs for chat-v2 components (adapt selectors per new DOM; preserve behavioral assertions)
- existing Playwright e2e specs `tests/e2e/chat-v2/*.spec.ts` (adapt selectors only)

### File header convention

Every NEW or REWRITTEN file requires standard TypeScript header per `.claude/rules/file-header-convention.md` (Purpose / Category / Scope / Created / Modification History 1-line max ≤100 chars including blockquote prefix).

### Backend impact

**0 backend changes this sprint** (Option W mode preserved). All wiring uses existing 14 SSE event types + existing `/loops` list endpoint (Sprint 57.19 US-B1). Backend wire ADs remain Sprint 57.22+ deferred:

- AD-ChatV2-SessionList-Backend (GET /api/v1/sessions list — NEW; today only fixture)
- AD-ChatV2-Memory-Block-Phase2 (Cat 3 memory_accessed SSE event emission — NEW; defer memory block UI to Phase-2)
- AD-ChatV2-HITL-FourAction-Phase2 (governance approve-with-edits backend action + ApprovalRequestedEvent payload enrichment)
- AD-ChatV2-Inspector-Trace-Phase2 (Cat 12 OTel spans per session endpoint)
- AD-ChatV2-Inspector-Memory-Phase2 (Cat 3 memory ops list per session endpoint)
- AD-ChatV2-Inspector-SubagentTree-Phase2 (Cat 11 subagent live feed endpoint)

## File Change List (summary)

- **NEW** components: 13 files (SessionList + TurnList + 3 turn role components + 4 block components + 2 inspector components + Composer + fixtures/sessions)
- **REWRITE**: 3 files (types.ts + chatStore.ts + ChatLayout.tsx)
- **REWRITE in-place** (visual only, behavior preserved): ApprovalCard.tsx
- **MARKED FOR REMOVAL** (or thin compat re-export): MessageList.tsx + ToolCallCard.tsx
- **EDIT**: ~6-10 files (InputBar.tsx wrap + i18n × 2 + existing chat-v2 Vitest specs ~3-4 + Playwright e2e ~2)
- **NEW docs**: progress.md + retrospective.md + `claudedocs/4-changes/sprint-57-21-chatv2-fidelity-phase-1/{screenshots/, DRIFT-REPORT-PHASE1.md}` (~3 files + artifacts)
- **EDIT docs**: CLAUDE.md (Phase 17/N→18/N + Latest/Prev Sprint shift + main HEAD + Next Phase 候選) + MEMORY.md (+1 line) + sprint-workflow.md calibration matrix (+1 row 2nd app) + SITUATION §第八部分 (~4 files)

Sprint total: ~25-30 file touches.

## Acceptance Criteria

1. `types.ts` Message → Turn discriminated union with 4 Block types compiles + tsc 0
2. `chatStore.mergeEvent` block-sequence logic preserves all 14 known SSE event types' existing behavioral contracts (HITL workflow / InputBar state machine / Cat 9 audit / mode toggle) — Vitest behavioral tests pass
3. `TurnList.tsx` renders 3 Turn role dispatch (user / agent / hitl) 1:1 per mockup at 1440×900 — Playwright MCP pair-verify
4. 4 Block components (thinking / tool / verification / subagent_fork) render 1:1 per mockup Block switch arms at 1440×900 — Playwright MCP pair-verify
5. `SessionList.tsx` renders 6 fixture sessions 1:1 per mockup at 1440×900 + visible "Demo data — backend pending" banner (AP-2 compliance)
6. `ChatLayout.tsx` 3-column with collapsible left + right rails (state `listOpen` + `inspOpen` toggles); 1440×900 default = all 3 rails visible
7. `ChatInspector.tsx` Turn tab populated 1:1 per mockup (KV pairs + EventLine list + 2 buttons); 3 other tabs render coming-soon empty state
8. `Composer.tsx` skeleton renders textarea + Send button; Attachments + Tools(24) + Memory scope buttons show disabled coming-soon UI; InputBar state machine logic preserved underneath
9. Vitest 277 baseline grown to 277+N (NEW: ~15-20 mergeEvent block-sequence cases + ~5-10 block component cases + ~5 SessionList cases + ~5 InspectorTurn cases); 0 regression
10. Playwright e2e chat-v2 baseline 10/10 preserved (selector adapt only; behavioral assertions intact)
11. Build < 3s + main bundle within +30 KB of Sprint 57.20 baseline (320.76 kB)
12. 0 backend changes ✅ (verified by `git diff --stat main..HEAD` showing only `frontend/` + `docs/` + `claudedocs/` + `memory/` + `.claude/rules/sprint-workflow.md` paths)
13. 0 LLM SDK leak in frontend (`grep -rn "import openai\|import anthropic" frontend/src/` = 0)
14. Anti-Pattern checklist 11/11 PASS
15. AD-ChatV2-Full-Mockup-Fidelity Phase-2+ candidates catalogued (memory block + HITL 4-action + Composer richness + 3 Inspector tabs + 6 backend wire ADs) in Sprint 57.21 retrospective Q5/Q6

## Workload

- Bottom-up estimate: ~16-20 hr (Day 0 setup + 三-prong 2 hr + Day 1 types/mergeEvent rewrite + Vitest 4-5 hr + Day 2 TurnList + 4 block components + Vitest 4-5 hr + Day 3 SessionList + ChatLayout 3-col 3-4 hr + Day 4 Inspector + Composer skeleton + closeout 3-4 hr)
- Calibration multiplier: **0.55** (`frontend-mockup-direct-port` 2nd application; Sprint 57.20 1st app ratio 0.45-0.55 below band by 0.30-0.40)
- Calibrated commit: ~9-11 hr (matches Sprint 57.20 pace = 5-day solo-dev sprint)

**Calibration note**: 2nd application of class `frontend-mockup-direct-port` 0.55. Sprint 57.20 first app ratio actual/committed = 0.45-0.55 BELOW [0.85, 1.20] band by 0.30-0.40 (KEEP 0.55 per 3-sprint window rule). Sprint 57.21 should validate or refute the pattern:

- If Sprint 57.21 ratio also < 0.7 (2/2 below band) → AD-Sprint-Plan-NEW propose 0.55 → 0.35-0.40 in Sprint 57.22+
- If Sprint 57.21 ratio in [0.85, 1.20] (band hit) → maintain 0.55; Sprint 57.20 was 1st-app artifact of inherited foundation
- Note: Sprint 57.21 has **less inherited foundation** than 57.20 (chat-v2 data model rewrite is genuinely structural; not just token migration), so ratio may swing higher than 57.20

## Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R1 | `chatStore.mergeEvent` rewrite breaks behavioral preservation (SSE handler / HITL approval workflow / InputBar state machine) | High | High | Day 1 EOD: run full Vitest chatStore suite + chat-v2 Playwright e2e before Day 2 starts; if regression → revert types.ts + mergeEvent + iterate |
| R2 | Turn block model fails to express existing 14 event types (e.g., `loop_end` has no block analog) | Medium | Medium | Day 1 grep all 14 SSE event types' current mergeEvent handling; each event must have explicit Phase-1 block-emit decision (emit / metadata-only / rawEvents only); document in progress.md Day 1 |
| R3 | SessionList fixture data violates AP-2 (no Potemkin) without clear demo banner | Medium | Medium | Day 3 first action = render visible "Demo data — backend wire Sprint 57.22+" banner above SessionList; document fixture status in i18n key `chat.session.demoBanner` |
| R4 | Vitest 277 baseline regression from selector changes in existing chat-v2 specs | High | Low | Day 1+2+3: each new component ships with selector update commits in same PR; CI must hit 277+ before Day 4 closeout |
| R5 | chat-v2 Playwright e2e 10/10 regression | Medium | High | Day 3 EOD: full Playwright chat-v2 suite must pass; preserve behavioral assertions (SSE / HITL / error retry) — selector adapt only |
| R6 | Inspector Turn tab data aggregation requires per-turn metadata not currently in chatStore (e.g., tokens_thinking + cost + trace_id + span_id) | Medium | Medium | Day 1 mergeEvent must thread these from LLMRequest/LLMResponse events into Turn metadata; if Cat 12 trace_id not in SSE → display "—" placeholder; document AD-Cat12-SSE-Trace-Id-Phase2 |
| R7 | AP-4 violation (rewriting JSX without real fidelity gain) | Low | High | Each new component ships with Playwright MCP pair-verify artifact at `claudedocs/4-changes/sprint-57-21-chatv2-fidelity-phase-1/screenshots/` + DRIFT verdict (parity / cosmetic / structural) in progress.md |
| R8 | InputBar.tsx state machine logic extraction into Composer.tsx introduces subtle state coupling bugs | Medium | High | Day 4 first action = run InputBar state machine Vitest cases (existing ~10 cases) against Composer.tsx; if fail → keep InputBar.tsx as-is + render Composer skeleton beside it; document AD-Composer-StateMachine-Migration-Phase2 |
| R9 | Module-level chatStore singleton across Vitest tests causes "store leaked between tests" | Medium | Medium | Verify `conftest.ts` (or Vitest setup) `beforeEach` resets chatStore — Common Risk Class C pattern from sprint-workflow.md |

### Common Risk Classes referenced (sprint-workflow.md)

- **Risk Class A (paths-filter)**: N/A — pure frontend, no CI yml changes expected
- **Risk Class B (mypy unused-ignore)**: N/A — no Python changes
- **Risk Class C (singleton across test loops)**: chatStore singleton — R9 mitigation pattern

## Dependencies

- Sprint 57.20 merged (✅ main HEAD `1a55e314`) + closeout PR #151 merged
- Mockup `page-chat.jsx` (✅ confirmed exists at `reference/design-mockups/page-chat.jsx` 533 lines)
- Sprint 57.20 NEW tokens (`bg-bg-1` / `text-fg-muted` / `border-strong` / `primary-soft`) available (✅ Sprint 57.20 wired)
- Sprint 57.18 semantic tokens (`thinking` / `tool` / `memory` / `verification`-via-success/danger) available (✅ Sprint 57.18 wired)
- Sprint 57.20 dark default + Geist font wire active (✅ Sprint 57.20 wired)
- 14 known SSE event types defined in `types.ts` (✅ Sprint 57.12 last extension)
- Dev server port 3007 runnable (✅ confirmed Sprint 57.20)
- Mockup http.server runnable at port 8080 (✅ confirmed Sprint 57.20)

## Cross-Sprint Carryovers

**Preserved from Sprint 57.20** (3 NEW carryover ADs):

- 🔴 **AD-ChatV2-Full-Mockup-Fidelity Phase-2+** — REMAINING multi-sprint epic work after Phase-1 ships this sprint
- 🆕 **AD-Mockup-Direct-Port-Round-2** — 8 remaining ship pages + 11 R2 findings (Sprint 57.22+ candidate)
- 🆕 **AD-Geist-Font-Asset-Bundling** (Phase 58+)

**Preserved from Sprint 57.19** (8 backend wire ADs reaffirmed):

- AD-Subagent-RealList-Phase58 / AD-Loop-Session-Enrich-Phase58 / AD-Overview-Backend-Wire / AD-Orchestrator-Backend-Wire / AD-State-VersionChain-Phase58 / AD-CommandPalette-Backend-Wire / AD-NotificationsPanel-Backend-Feed / AD-UserMenu-Tenant-Switch — all Sprint 57.22+ backend wire deferred

**Opens this sprint** (likely):

- AD-ChatV2-Memory-Block-Phase2 (Cat 3 backend SSE `memory_accessed` event emission)
- AD-ChatV2-HITL-FourAction-Phase2 (governance approve-with-edits backend action + frontend 4-action UX)
- AD-ChatV2-Composer-Richness-Phase2 (attachments upload backend + tools menu wire + memory scope filter)
- AD-ChatV2-Inspector-Trace-Phase2 (Cat 12 OTel spans per session endpoint + waterfall UI)
- AD-ChatV2-Inspector-Memory-Phase2 (Cat 3 memory ops list per session endpoint + UI)
- AD-ChatV2-Inspector-SubagentTree-Phase2 (Cat 11 subagent live feed endpoint + tree UI)
- AD-ChatV2-SessionList-Backend (GET /api/v1/sessions list endpoint — Sprint 57.22+ wire fixture → real backend)
- AD-Cat12-SSE-Trace-Id-Phase2 (potential: if Inspector Turn tab needs trace_id from SSE that doesn't currently emit)
- AD-Composer-StateMachine-Migration-Phase2 (potential: if InputBar state machine extraction proves complex)

## Out of Scope (Explicit)

- ❌ Backend `GET /api/v1/sessions` list endpoint (defer to Sprint 57.22+; SessionList ships fixture data with demo banner)
- ❌ NEW Cat 3 SSE event `memory_accessed` (defer; memory block defer to Phase-2)
- ❌ HITL 4-action UX expansion (Approve with edits + Escalate to L2 + SLA countdown enrichment + payload editor) — Sprint 57.22+ AD-ChatV2-HITL-FourAction-Phase2
- ❌ Composer richness (Attachments upload + Tools(24) menu wire + Memory scope filter dropdown) — Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2
- ❌ Inspector Trace tab (Cat 12 OTel spans waterfall) — Sprint 57.22+ AD-ChatV2-Inspector-Trace-Phase2
- ❌ Inspector Memory tab (Cat 3 memory ops list) — Sprint 57.22+ AD-ChatV2-Inspector-Memory-Phase2
- ❌ Inspector Subagent tree tab (Cat 11 live feed) — Sprint 57.22+ AD-ChatV2-Inspector-SubagentTree-Phase2
- ❌ ChatHeader (mockup top toolbar with title + agent badge + model badge + provider-neutral + N turns + streaming dot + Loop / Audit buttons) — covered by Sprint 57.20 NEW Topbar.tsx already; Sprint 57.21 keeps existing chat-v2 page-level header
- ❌ Sprint 57.20 Round-2 page-level cosmetic patching (8 remaining ship pages) — Sprint 57.22+
- ❌ Backend wire ADs bundle (8 total carryover from Sprint 57.19) — Sprint 57.22+
- ❌ Visual regression baseline regeneration in CI (Sprint 57.14 mechanism; can run end-of-sprint if needed but not required deliverable)

## Definition of Sprint Complete

- [ ] All Acceptance Criteria 1-15 met
- [ ] Anti-Pattern checklist 11/11 PASS
- [ ] 4 doc syncs landed (CLAUDE.md / MEMORY.md / sprint-workflow.md calibration matrix +1 row / SITUATION §第八部分)
- [ ] PR opened against main + CI 7 checks green
- [ ] Closeout PR (chore) opened with doc syncs if not bundled into main PR
- [ ] Phase 57+ Frontend status updated 17/N → 18/N
- [ ] 7+ NEW carryover ADs catalogued in retrospective for Sprint 57.22+
