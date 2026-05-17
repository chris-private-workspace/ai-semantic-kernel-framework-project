# Sprint 57.21 — Progress

**Sprint**: 57.21 — AD-ChatV2-Full-Mockup-Fidelity Phase-1
**Branch**: `feature/sprint-57-21-chatv2-mockup-fidelity-phase-1`
**Plan**: [sprint-57-21-plan.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-21-plan.md)
**Checklist**: [sprint-57-21-checklist.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-21-checklist.md)
**Base commit**: `ebc0dc60` (main HEAD after Sprint 57.20 closeout PR #151 merge)

---

## Day 0 — 2026-05-17 — Setup + 三-prong + Playwright MCP reference captures

### Accomplishments

- Sprint 57.21 plan landed (~600 lines; mirrors Sprint 57.20 format: 12 sections; YAML frontmatter; Group A-E user stories; calibration class `frontend-mockup-direct-port` 0.55 2nd application)
- Sprint 57.21 checklist landed (Day 0-4 + Anti-Pattern self-check + Carryover; 5 sub-sections per Day matching Sprint 57.20 cadence)
- Feature branch created: `feature/sprint-57-21-chatv2-mockup-fidelity-phase-1` from main `ebc0dc60`
- Progress.md + claudedocs skeleton + DRIFT-REPORT-PHASE1.md skeleton created
- Day 0 三-prong verify (see below)
- Playwright MCP reference captures (see below)

### Drift findings (Day 0 三-prong)

_Catalogued via plan-vs-repo grep before Day 1 code starts._

**Prong 1 — Path verify** ✅ all confirmed:

- `frontend/src/features/chat_v2/components/blocks/` does NOT exist (✅ plan expects create Day 2)
- `frontend/src/features/chat_v2/components/inspector/` does NOT exist (✅ plan expects create Day 4)
- `frontend/src/features/chat_v2/components/turns/` does NOT exist (✅ plan expects create Day 2)
- `frontend/src/features/chat_v2/fixtures/` does NOT exist (✅ plan expects create Day 3)
- `reference/design-mockups/page-chat.jsx` = 533 lines ✅
- 9 existing chat_v2 files (types.ts / chatStore.ts / chatService.ts / useLoopEventStream.ts / 5 components) ✅

**Prong 2 — Content verify** ✅ key assertions confirmed:

- `chatStore.ts` `mergeEvent` confirmed at L72 (signature) + L120 (impl) + discriminated union switch with cases for `loop_start` (L125) / `turn_start` (L135) / `approval_requested` (L215) / `approval_received` (L235) ✅
- `useLoopEventStream` hook at L38 of `hooks/useLoopEventStream.ts` ✅
- `governanceService.decide` confirmed at `features/governance/services/governanceService.ts:71` → wraps `POST /api/v1/governance/approvals/{id}/decide` ✅ — HITL workflow preservation viable
- `STYLE.md §3` confirms risk color palette + Sprint 57.18 4 risk tokens (`text-risk-{low,medium,high,critical}`)

**Prong 3 — Schema verify** N/A this sprint (pure frontend; 0 DB schema work).

**D-PRE-1** (scope confirmation, NOT shift): Sprint 57.18 wired 4 risk tokens (`text-risk-{low,medium,high,critical}` at `hsl(150 60% 45%)`/`hsl(38 92% 50%)`/`hsl(20 90% 55%)`/`hsl(0 70% 40%)`) per STYLE.md §2 table L128-131. **Plan should use these tokens** for HITLTurn severity rendering instead of arbitrary `text-[#hex]`. Caveat: `approval-card.spec.ts` sentinel `#b71c1c` (`hsl(0 70% 40%)` ≈ `text-risk-critical`) — token version may break exact hex literal assertion. Mitigation: Day 2 ApprovalCard rewrite either (a) updates spec to assert `text-risk-critical` class, OR (b) preserves `#b71c1c` arbitrary literal for sentinel via `text-[#b71c1c]` per STYLE.md §3 escape hatch. Decision at Day 2 time.

**D-PRE-2** (in-scope clarification): Mockup `ChatHeader` (page-chat.jsx L93-121) has chat-specific elements NOT covered by Sprint 57.20 NEW global Topbar:
- Severity icon (gradient red→orange)
- Session title + agent badge + model badge + "provider: neutral" + N turns label
- Streaming live dot
- Loop / Audit buttons (right-side ghost buttons)
- Panel-toggle buttons (left: toggle SessionList; right: toggle Inspector)

Plan §Technical Spec ChatLayout.tsx 3-col rewrite (Day 3) **includes ChatHeader** within ChatLayout — NOT in global Topbar. Update plan §File Change List to explicitly list ChatHeader component (NEW or inlined into ChatLayout.tsx).

**D-PRE-3** (in-scope addition): Mockup `HITLTurn` uses `<RiskBadge level="high" />` (page-chat.jsx L291) — does not exist in current chat_v2 codebase. STYLE.md §3 shows pattern `<span className={cn("font-bold", RISK_TEXT_CLASS[risk] ?? "text-muted-foreground")}>{risk}</span>` (L87). Day 2 HITLTurn either:
- (a) Create `components/ui/RiskBadge.tsx` (~30 lines) reusable across HITL + governance pages, OR
- (b) Inline the styling pattern from STYLE.md §3 within HITLTurn.tsx

Decision at Day 2 time — preference (a) for reusability if governance/ApprovalList also benefits.

**D-PRE-4** (env / out-of-scope but noted): Day 0 Playwright MCP attempts to capture authenticated `/chat-v2` repeatedly redirected to `/auth/login` despite valid JWT in `localStorage.ipa-auth-storage`. Likely cause: RequireAuth's async `/auth/me` check fails (backend `/auth/me` returns 401 → handleAuthExpired → redirect). NOT a Sprint 57.21 scope issue — it's an env setup issue. Day 0 baseline screenshots show login page; mockup capture (`mockup-chat-v2-1440x900.png`) is the critical visual target. Day 4 post-state capture will need fresh dev-login + immediate screenshot, OR `await page.waitForSelector('[data-testid="chat-v2-root"]')` to bypass race condition. Document in DRIFT-REPORT-PHASE1 §Verification table.

**Go/no-go**: Scope shift verdict = **0%** (all 4 findings are clarifications, in-scope additions, or env notes; no scope reduction or expansion). → **GO Day 1**.

### Playwright MCP reference captures (Day 0.4) — completed

| Artifact | Path |
|----------|------|
| ✅ **Mockup chat 1440×900 (CRITICAL)** | `claudedocs/4-changes/sprint-57-21-chatv2-fidelity-phase-1/screenshots/mockup-chat-v2/mockup-chat-v2-1440x900.png` |
| ⚠️ Prod-pre attempt 1 (redirect to login) | `screenshots/prod-chat-v2-pre/prod-chat-v2-pre-attempt1-redirect-to-login.png` |
| ⚠️ Prod-pre attempt 2 (redirect to login after dev-login) | `screenshots/prod-chat-v2-pre/prod-chat-v2-pre-attempt2-redirect-to-login.png` |
| ✅ Prod root post-dev-login (authenticated home page baseline) | `screenshots/prod-chat-v2-pre/prod-root-post-dev-login.png` |
| ⚠️ Prod chat-v2 attempt 3 (race redirect) | `screenshots/prod-chat-v2-pre/prod-chat-v2-attempt3-race-redirect.png` |

The mockup screenshot is the canonical visual target for Day 1-4 fidelity verification.

### Notes / decisions

- **Anti-stop rule**: Per `memory/feedback_tool_result_is_not_turn_boundary.md`, tool result is progress signal NOT turn boundary. Day 0 will batch sub-tasks where possible.
- **Mockup-Fidelity Hard Constraint**: All UI work must 1:1 mockup; functional gaps via fixture + AP-2 demo banner; backend gaps deferred per Sprint 57.21 plan §Out of Scope.

### Estimate vs actual

(populated at Day 0 EOD)

---

## Day 1 — 2026-05-17 — Turn block data model rewrite (US-B1 + US-B2 + US-B3)

### Accomplishments

- **US-B1 types.ts refactor** ✅:
  - `Block` discriminated union (4 of 5 mockup types: thinking / tool / verification / subagent_fork; memory defer)
  - `Turn` discriminated union (user / agent / hitl) with role-specific fields + Inspector metadata aggregation fields (tokensIn/Out/Thinking, costUsd, traceId, spanId — all nullable)
  - `Session` interface + `SessionDomain` + `SessionStatusUI` for Day 3 fixture sidebar
  - `RiskSeverity` token type aligned to Sprint 57.18 `risk-{low,medium,high,critical}` tokens (D-PRE-1)
  - `SubagentEntry` + `ToolBlockStatus` helper types
  - Removed `Message` type (replaced by Turn); preserved 14 SSE event types + KNOWN_LOOP_EVENT_TYPES + ChatStatus/ChatMode/ChatSession + ToolCallEntry + ApprovalEntry
  - MHist 1-line compliant
- **US-B2 chatStore.mergeEvent rewrite** ✅:
  - State shape: `messages: Message[]` → `turns: Turn[]`; added `sessions: Session[]` + `activeSessionId` (Day 3 populates)
  - mergeEvent dual-emit pattern: all 14 SSE event types preserve existing slices (rawEvents/approvals/verifications/subagents) AND emit blocks/turns into new `turns[]` array
  - Helper functions: `nextTurnId()` / `nowIso()` / `mapRiskLevel()` (HIGH→risk-high mapping) / `updateLastAgentTurn()` (immutable pure update of last agent turn)
  - turn lifecycle: loop_start → status running; turn_start → push empty AgentTurn; llm_response → ThinkingBlock + ToolBlock per tool_call (thinking-before-tools order per mockup); tool_call_request/result → ToolBlock pairing; verification_* → VerificationBlock (claim from reason; evidence from suggested_correction); subagent_spawned → find-or-create SubagentForkBlock + append agent entry; subagent_completed → update agent entry status; approval_requested → push HITLTurn; approval_received → update HITLTurn decision; loop_end → status completed + turn stopReason + waiting flag (tool_use → waiting=true)
- **US-B3 Vitest mergeEvent coverage** ✅:
  - NEW `tests/unit/chat_v2/chatStore.mergeEvent.test.ts` — **22 NEW cases** covering all 14 SSE event types' Phase-1 behavior + lifecycle + dual-emit preservation + end-to-end turn flow
  - Existing 2 chatStore-touching specs (chatStore.subagents.test.ts + chatStore.verifications.test.ts) STILL PASS without modification — dual-emit preserves Sprint 57.11/57.12 slice behavior
  - `MessageList.tsx` Day 1 stub: consumes `turns[]` + ToolBlock→ToolCallCard adapter (Day 2 replaces with proper TurnList + components/blocks/)
  - `useLoopEventStream.ts` UNCHANGED — only uses `pushUserMessage` action name, no Message TYPE

### Quality gates (Day 1 EOD)

| Gate | Sprint 57.20 baseline | Sprint 57.21 Day 1 | Verdict |
|------|----------------------|---------------------|---------|
| tsc errors | 0 | 0 | ✅ |
| Vitest tests | 277 | **299** (+22 NEW) | ✅ 0 regression |
| Vitest files | 63 | 64 (+1 NEW) | ✅ |
| Lint | silent (--max-warnings 0) | silent | ✅ |
| Build time | 2.69-2.79s | 3.12s | ✅ |
| Main bundle | 320.76 kB | **320.76 kB byte-identical** | ✅ (type-shape change is 0-runtime cost) |
| Backend changes | — | 0 | ✅ (Option W preserved) |

### Notes / decisions

- **mergeEvent dual-emit decision**: rather than migrate Sprint 57.11/57.12 components off `verifications` / `subagents` slices immediately (which would expand Phase-1 scope significantly), the new mergeEvent emits BOTH paths — preserving legacy slice consumers (VerificationPanel, SubagentTree) AND feeding the new Turn block render. This adds ~30 lines of duplicate emit logic but defers component migration to Phase-2+.
- **`MessageList.tsx` kept temporarily**: Day 1 stub adapts ToolBlock→ToolCallCard so existing visual baseline preserved. Day 2 replaces with `TurnList.tsx` + `components/blocks/` + `components/turns/` proper components.
- **HITLTurn dual-emit defers UI consolidation**: Sprint 57.21 Day 1 pushes BOTH approvals dict entry AND HITLTurn into turns[]. MessageList Day 1 skips HITLTurn render (keeps existing approvals dict path) — Day 2 TurnList renders HITLTurn inline + drops the separate approvals dict loop.

### Estimate vs actual

- Bottom-up estimate: 4-5 hr (types refactor + chatStore rewrite + Vitest)
- Actual: ~2.5 hr (types + chatStore + adapter + 22 Vitest cases ran continuously without backtracking)
- Delta: ~50% under estimate. Reason: Day 0 三-prong already discovered chatStore.ts mergeEvent structure (L120-340) + types.ts contract was clear from mockup capture; design decisions (dual-emit / adapter pattern) crystallized during draft. No churn.

### Day 1 EOD strategy pivot — Option C: copy-mockup-then-convert

User 2026-05-17 directive post-Day-1 closeout: Day 2-4 workflow pivots from **"write fresh TS reading mockup as spec"** (Sprint 57.20 pattern that produced 16 R2 drift findings DRIFT-REPORT-ROUND-2) to **"copy mockup JSX + mechanical conversion + Tailwind utility conversion"** (Option C). Rationale: visual fidelity at first paint approaches 1:1 by removing the manual-mapping step that introduced 57.20's drift.

**Pivot scope**: Day 2-4 only. Day 1 (data-layer rewrite) and Day 0 (setup) unaffected.

**Workflow changes** (plan §Day 1 EOD strategy pivot + checklist Day 2 §2.0):

1. cp `reference/design-mockups/page-chat.jsx` → `_mockup-source.jsx.bak` (per-section reference)
2. Mechanical conversion: useCs→useState / Object.assign→export / hardcoded TURNS→chatStore.turns / Icon/Button→shadcn + lucide-react
3. **Inline `style={{...}}` → Tailwind utility classes** using Sprint 57.18 semantic tokens + Sprint 57.20 layout tokens (NOT taking ESLint guard relaxation shortcut)
4. Per-component Playwright MCP pair-verify; record DRIFT verdict in DRIFT-REPORT-PHASE1.md

**Cost impact**: Option C conversion overhead ~30-50% above original Option A budget. Day 1 came in 50% under estimate (~2.5 hr actual vs 4-5 hr est = ~2 hr buffer saved). Saved buffer absorbs Day 2-4 extension; sprint envelope (5 days / ~9-11 hr calibrated commit) holds.

**Audit trail**: each NEW component file-header MHist cites source mockup line range (e.g. "extracted from page-chat.jsx L165-176 + tailwind convert"). DRIFT-REPORT-PHASE1.md §Section Mapping pre-records per-section line ranges (checklist §2.0).

## Day 2 — _pending_

## Day 3 — _pending_

## Day 4 — _pending_
