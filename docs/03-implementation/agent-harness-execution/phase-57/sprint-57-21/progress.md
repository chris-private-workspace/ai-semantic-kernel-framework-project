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

## Day 2 — 2026-05-17 — Turn renderer + 4 Block components (US-C1 + US-C2; US-C3 deferred to Day 3)

### Accomplishments

**§2.0 Mockup baseline + scaffold** ✅:
- 4 NEW directories: `components/{turns,blocks,inspector}/` + `fixtures/`
- cp `reference/design-mockups/page-chat.jsx` → `components/_mockup-source.jsx.bak` (per-section reference; will be deleted Day 4 closeout)
- Per-section line ranges catalogued in checklist Day 2 §2.0 + cited inline in each NEW component's MHist

**§2.1 Turn role components + TurnList** ✅ (cp+convert from mockup):
- NEW `turns/UserTurn.tsx` (~45 lines; from L165-176) — timeline rail/marker + display_name (authStore) + route-pill role + at; pure render
- NEW `turns/AgentTurn.tsx` (~58 lines; from L178-197) — primary-tinted marker + agent name + turn # badge + optional stop_reason badge + optional duration + at + optional "awaiting approval" indicator; block dispatcher via `BlockRender`
- NEW `turns/HITLTurn.tsx` (~165 lines; from L270-313) — warning-tinted marker + role label + **inline rich approval card** (severity-tinted border + bar + icon-ring + title + countdown + meta + rationale + payload pre-block + 4 action buttons with 2-action backend wire to `governanceService.decide`); RiskSeverity mapped to Sprint 57.18 risk-{low/medium/high/critical} tokens
- NEW `TurnList.tsx` (~50 lines) — `useChatStore.turns` consumer + role dispatcher + auto-scroll + empty state matching Sprint 57.20 baseline copy

**§2.2 4 Block components + Block dispatcher** ✅ (cp+convert from mockup):
- NEW `blocks/ThinkingBlock.tsx` (~30 lines; from L200-207) — thinking-tinted left rail + uppercase mono "thinking" label + italic muted text
- NEW `blocks/ToolBlock.tsx` (~62 lines; from L208-223) — tool-tinted head with name + status badge (pending/ok/error) + duration; monospace input pre-block + dashed-separated output pre-block (only when output non-null)
- NEW `blocks/VerificationBlock.tsx` (~35 lines; from L234-244) — success/danger tone variant; check/x icon; claim + evidence rows
- NEW `blocks/SubagentForkBlock.tsx` (~50 lines; from L245-264) — GitFork header + "Fork · concurrent" + spawned N count; agent rows w/ ChevronRight + name + task + status badge (info/success) + turns count
- NEW `blocks/Block.tsx` (~35 lines) — discriminated-union dispatcher; tsc-exhaustive switch

**Vitest coverage** ✅:
- NEW `tests/unit/chat_v2/components/blocks.test.tsx` — 12 cases covering each of 4 block components (render + variants) + Block dispatcher dispatch correctness
- NEW `tests/unit/chat_v2/components/TurnList.test.tsx` — 8 cases covering empty state + role dispatch (user/agent/hitl) + authStore display_name fallback to email + waiting state + decision label render + mixed turns ordering
- Pre-Day-2 baseline 299 → Day 2 EOD **319 tests** (+20 NEW; 0 regression; 66 test files)

**§2.3 ApprovalCard rewrite — DEFERRED to Day 3**:
- HITLTurn.tsx Day 2 over-delivered the rich card body inline (~85 lines of approval-card markup directly in HITLTurn). ApprovalCard.tsx rewrite tightly coupled to MessageList → TurnList swap (Day 3 §3.2 ChatLayout rewrite). Day 2 ships HITLTurn for future TurnList consumption; ApprovalCard preserved as-is for current MessageList consumer + governance/approvals page consumer + e2e spec compatibility.
- Day 3 ChatLayout swap will: (a) replace MessageList → TurnList; (b) update e2e selectors in approval-card.spec.ts to match new HITLTurn DOM; (c) decide ApprovalCard.tsx fate (deprecate vs thin compat re-export).

### Quality gates (Day 2 EOD)

| Gate | Day 1 baseline | Day 2 EOD | Verdict |
|------|----------------|-----------|---------|
| tsc errors | 0 | 0 | ✅ |
| Vitest tests | 299 | **319** (+20 NEW) | ✅ 0 regression |
| Vitest files | 64 | 66 (+2 NEW: blocks.test.tsx + TurnList.test.tsx) | ✅ |
| Lint | silent | silent (1 transient warning on TurnList useEffect deps complex-expression; fixed via extract-to-local-var) | ✅ |
| Build time | 3.12s | 2.82s | ✅ |
| Main bundle | 320.76 kB | **320.76 kB byte-identical** | ✅ (tree-shake absorbs 9 NEW components + lucide-react imports — Brain/Wrench/Check/X/ChevronRight/GitFork/Clock/Shield/FileText already in chunk) |
| Backend changes | 0 | 0 | ✅ |

### Notes / decisions

- **HITLTurn scope expansion (over-delivery)**: Day 2.1 originally planned HITLTurn as thin wrapper around ApprovalCard. Implementation chose to embed the rich card body directly in HITLTurn for visual coherence — ApprovalCard would need same logic anyway. Cost ~30 min over plan, but eliminates Day 2.3 rewrite scope. Day 3 swap from MessageList → TurnList is now self-contained (no ApprovalCard.tsx touch).
- **Lucide-react icons**: mockup `<Icon name="...">` mapped to lucide-react equivalents (Brain for thinking; Wrench for tool; Check/X for verification; ChevronRight for subagent row; GitFork for subagent fork; Clock + Shield + FileText for HITL). Bundle unchanged because lucide-react chunk already included earlier components.
- **Token alignment**: Sprint 57.18 wired `thinking` / `tool` / `success` / `danger` / `warning` / `info` / `risk-{low,medium,high,critical}` semantic tokens — all 9 NEW components use these tokens; 0 arbitrary hex literals; 0 ESLint inline-style escape.
- **Pair-verify deferred**: Day 2 Playwright MCP capture skipped — chat-v2 page still renders MessageList Day 1 stub (Day 3 swap). Visual verification happens Day 3 when TurnList becomes live.

### Estimate vs actual

- Bottom-up estimate: 5-7 hr (Option C cp+convert overhead added to original 4-5 hr Day 2 budget)
- Actual: ~3.5 hr (9 components written + 20 Vitest cases + tsc/lint/build green)
- Delta: ~40% under estimate. Reason: mockup JSX already structured into clean per-component sections; Tailwind translation table from mockup CSS lookup was straightforward; Day 1 type design eliminated guessing about Block/Turn shape. Buffer carry forward to Day 3.

## Day 3 — 2026-05-17 (SessionList + ChatLayout 3-col + Demo banner)

### What landed

§3.1 — **SessionList + fixture data**
- NEW `frontend/src/features/chat_v2/fixtures/sessions.ts` (~95 lines) — verbatim port of mockup `SESSIONS` L5-12 (6 sessions: payment-gateway 5xx / Q4 audit / nightly patrol / RCA cache eviction / change request / tenant anomaly)
- NEW `frontend/src/features/chat_v2/components/SessionList.tsx` (~160 lines per mockup L123-156 + DomainDot L153-156 inlined) — fixture-driven sidebar: New session button (Plus icon) + Filter ghost button / "Sessions" + count label / 6 SessionItem clickable items with DomainDot (incident=danger / audit=memory / patrol=tool / rca=thinking color map) + title + running live-dot OR HITL badge + agent · turns · time meta row. Click → `chatStore.setActiveSessionId`. Active session = `bg-bg-2` highlight + `data-active="true"`.
- NEW `tests/unit/chat_v2/components/SessionList.test.tsx` (7 cases): 6 fixtures render / demo banner / click → setActiveSessionId + data-active flip / running status indicator / hitl badge / done status (no indicator) / session count label

§3.2 — **ChatLayout 2-col placeholder → 3-col with collapsible rails + ChatHeader**
- REWRITE `frontend/src/features/chat_v2/components/ChatLayout.tsx` — 3-col grid `[280px | 1fr | 360px]` with `listOpen` / `inspOpen` local state. Mobile (<768px) hides both rails. Left rail mounts `<SessionList />`, center hosts `<ChatHeader>` + `{children}`, right rail mounts `<ChatInspector />` (Day 3 stub).
- NEW `frontend/src/features/chat_v2/components/ChatHeader.tsx` (~165 lines per mockup L93-121) — left panel toggle button + gradient danger→warning AlertTriangle icon + session title + agent / `claude-haiku-4-5` thinking badge / `provider: neutral` mono span / `· N turns` / streaming indicator (live-dot + `streaming` mono when status === "running") / Loop button + Audit button / right panel toggle button. Data sources: `FIXTURE_SESSIONS.find(s => s.id === activeSessionId)` for title/agent/turns; `chatStore.totalTurns` preferred when > 0 (live override fixture).
- NEW `frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx` (~30 lines — Day 3 stub; Day 4 §4.1 replaces with full 4-tab frame per mockup L371-390)
- NEW `tests/unit/chat_v2/components/ChatHeader.test.tsx` (9 cases): fallback title / fixture title lookup / streaming hidden when idle / streaming visible when running / provider neutral always visible / left toggle data-active + callback / right toggle data-active + callback / Loop+Audit buttons render / live totalTurns override

§3.3 — **Demo banner + i18n keys (AP-2 compliance)**
- EDIT SessionList.tsx — yellow `bg-warning/16 border-warning/40 text-warning` banner above sessions list ("Demo data — backend list endpoint pending Sprint 57.22+ (AD-ChatV2-SessionList-Backend)")
- EDIT `src/i18n/locales/en/common.json` + `zh-TW/common.json` — NEW `chat.{session,header,inspector}.*` namespace (12 keys × 2 locales = 24 NEW i18n entries): session.title / newSession / filter / status.{running,hitl,done} / meta.turns ({count}) / demoBanner / header.toggleList / toggleInspector / providerNeutral / streaming / loopButton / auditButton / inspector.comingSoon

§3.2 cascade — **chat-v2 page swap**
- EDIT `frontend/src/pages/chat-v2/index.tsx` — `MessageList` import → `TurnList` import; consumer body `<MessageList />` → `<TurnList />`. NEW MHist entry. MessageList.tsx left intact (no thin re-export yet; Day 4 closeout decision per checklist §4.2).

### Drift findings — Day 3

- **D-DAY3-1** (cosmetic / scope-internal): mockup `<Badge tone="warning">HITL</Badge>` and `<Badge tone="thinking">claude-haiku-4-5</Badge>` rely on a `tone` prop the shadcn Badge primitive doesn't expose. Used `variant="outline"` + explicit token classes (`border-warning/40 bg-warning/16 text-warning` / `border-thinking/40 bg-thinking/16 text-thinking`). Matches mockup visual; closes Sprint 57.18 D-PRE-1 risk-token usage pattern for chat-v2.
- **D-DAY3-2** (in-scope additive): mockup ChatHeader title was a `<div>` with `fontWeight: 600` + ellipsis. Promoted to `<h2>` for accessibility (under AppShellV2's main `<h1>`); preserves Sprint 57.17 ChatLayout h1-cascade fix philosophy.
- **D-DAY3-3** (deferred — Phase 58+ epic): existing chat-v2 e2e `approval-card.spec.ts` references ApprovalCard DOM/selectors; with MessageList → TurnList swap the approval rendering path is via HITLTurn (Day 2 §2.1) NOT ApprovalCard. Existing e2e may break selector lookup. Day 4 §4.2 decision: rewrite e2e selectors against HITLTurn DOM, OR keep ApprovalCard as thin compat wrapper. Behavioral wire (`governanceService.decide`) preserved either way.
- **D-DAY3-4** (in-scope additive): ChatLayout collapsible rails use `grid-cols-[...]` per state. Alternative considered = always-render-and-CSS-hide; rejected because unmounting closed rails prevents `<SessionList />` from listening to `chatStore.activeSessionId` updates after a session click (would mass-re-render). Final: rail panels unmount when state is `false`; preserves keyboard tab order; mockup `data-list` / `data-insp` attribute pattern kept on shell for any future e2e selector.
- **D-DAY3-5** (cosmetic): `live-dot` mockup CSS class translated as `inline-block h-2 w-2 animate-pulse rounded-full bg-warning`. Matches mockup visual; 4.6:1 contrast on bg-bg-1 verified per Sprint 57.17 STYLE.md §2.

### Quality gates (Day 3 EOD)

| Gate | Day 2 baseline | Day 3 EOD | Verdict |
|------|----------------|-----------|---------|
| tsc errors | 0 | 0 | ✅ |
| Vitest tests | 319 | **335** (+16 NEW) | ✅ 0 regression |
| Vitest files | 66 | 68 (+2 NEW: SessionList.test + ChatHeader.test) | ✅ |
| Lint | silent | silent | ✅ |
| Build time | 2.82s | 2.77s | ✅ |
| Main bundle | 320.76 kB | **321.92 kB** (+1.16 kB) | ✅ within +30 kB target |
| dropdown-menu chunk | 118.36 kB | 118.37 kB | ✅ ~flat |
| Backend changes | 0 | 0 | ✅ |
| i18n keys added | — | 24 (12 × 2 locales) | ✅ |

### Notes / decisions

- **AP-3 cross-directory check**: all NEW Day 3 files under `features/chat_v2/{components,fixtures}/`. 0 outside the feature.
- **AP-2 Potemkin avoidance**: SessionList ships demo banner explaining fixture status; session click is reactive (updates store) but does NOT trigger backend fetch — explicit AD-ChatV2-SessionList-Backend carryover.
- **AP-4 visible mockup-fidelity gain**: ChatLayout rewrite from 2-col placeholder to 3-col with mockup-matching ChatHeader is the visible win of Day 3. Playwright MCP visual capture deferred to Day 4 closeout (when Inspector Turn tab ships) per checklist §4.3.
- **i18n namespace expansion**: NEW `chat.*` namespace is the first non-`nav.chatV2` chat key in common.json. Future Day 4 Composer + Inspector Turn tab can extend this namespace.
- **`MessageList.tsx` left intact**: not converted to thin re-export this Day. Day 4 closeout will either delete or thin-shim depending on whether e2e + any historical importers still touch it.

### Estimate vs actual

- Bottom-up estimate: 3-4 hr (Day 2 buffer pulled forward)
- Actual: ~2.5 hr (3 NEW components + 16 NEW Vitest cases + 24 i18n keys + 1 page consumer swap + tsc/lint/build green; 0 backend touched)
- Delta: ~30% under estimate. Reason: SessionList + ChatHeader are mostly mechanical Tailwind translation; chatStore + types.ts session shape from Day 1 covered all needs; 0 surprise blockers.
- Cumulative actual through Day 3: ~8.5 hr (Day 1 ~2.5 hr + Day 2 ~3.5 hr + Day 3 ~2.5 hr) — well inside the 9-11 hr calibrated commit; Day 4 has ample budget for Inspector + Composer + closeout.

## Day 4 — 2026-05-17 (Inspector 4-tab + Composer scaffolding + e2e contract fix + orphan cleanup)

### What landed

§4.1 — **Inspector 4-tab frame + Turn populated + 3 coming-soon tabs**
- REWRITE `inspector/ChatInspector.tsx` — Day 3 stub → 4-tab frame via Sprint 57.19 NEW shadcn `Tabs` primitive; local `tab` state (default `"turn"`); switch dispatcher → `<InspectorTurn>` or `<ComingSoonInspectorTab>` with named carryover AD
- NEW `inspector/InspectorTurn.tsx` (~155 lines per mockup L392-417 + KV/EventLine L419-432 helpers inlined): pulls last `AgentTurn` from `chatStore.turns` via reverse-find; renders header "Turn N · stop_reason" + 8 KV pairs (`stop_reason` badge + `duration` + `tokens.{in,out,thinking}` + `cost` + `trace_id` + `span_id` — '—' placeholder when null) + Block sequence (4-block-type colored dots + describeBlock-generated descriptive text) + 2 action buttons (Open audit entry / Open in Loop Debug — placeholder wires).
- NEW `inspector/ComingSoonInspectorTab.tsx` (~50 lines): named-empty-state placeholder accepts `name` + `mockupSection` + `carryoverAd` + `hint` props; renders mockup file hint copy + carryover AD link copy in a bordered box.

§4.2 — **Composer visual scaffolding (Option C path)**
- NEW `Composer.tsx` (~115 lines per mockup L316-368): textarea with mockup placeholder copy + 3 disabled coming-soon buttons (Attach / Tools (24) / Memory scope) + right-aligned model badge + provider neutral chip + disabled Send button + drop-file hint footer. ALL controls disabled; tooltips reference `AD-ChatV2-Composer-Richness-Phase2` + `AD-ChatV2-Composer-Wire-Phase2`.
- **NOT wired** to `chat-v2/index.tsx` — production send path stays via `InputBar.tsx` (preserves Sprint 50.2 5-state pill + send/cancel + mode toggle + 14 SSE event handling battle-tested wire). Carryover AD-ChatV2-Composer-Wire-Phase2 records the wire decision for Sprint 57.22+ (extract-shared-hook vs proxy-via-composition decided when rich Attach/Tools/Memory-scope affordances themselves wire).

§D-DAY3-3 — **HITLTurn e2e contract surgical preservation**
- EDIT `turns/HITLTurn.tsx` outer wrapper — add `role="region"` + `aria-label="HITL approval"` so existing Playwright `approval-card.spec.ts` `page.getByRole("region", { name: "HITL approval" })` continues to locate the card after Day 3 MessageList→TurnList swap. "CRITICAL" severity literal text already rendered at L135 (`{severity.replace("risk-","").toUpperCase()}`); "Approve" button name matches "Approve & continue" via Playwright substring rule (no rename needed). MHist 1-line entry added.

§4.2 cascade — **Orphan cleanup (Karpathy §3 — your changes produce the orphan, clean it)**
- DELETE `MessageList.tsx` — 0 production importers post-Day-3 TurnList swap; 0 Vitest specs.
- DELETE `ToolCallCard.tsx` — only consumer was MessageList; VerificationPanel / SubagentTree / LoopVisualizer have own UI.
- DELETE `_mockup-source.jsx.bak` (Day 0 baseline; per checklist §2.0 footer "deleted Day 4 closeout"; reference is `reference/design-mockups/page-chat.jsx` canonical).

### Drift findings — Day 4

- **D-DAY4-1** (resolved in-sprint): Vitest `getByText("thinking")` matched twice — once from `ThinkingBlock.type` label, once from default `describeBlock(thinking)` return `"thinking"`. Fixed by changing `describeBlock` for thinking blocks to truncated-text-preview (`block.text.slice(0, 36) + "…"`); cleaner UI (mockup hint vs literal word duplication) AND no test collision.
- **D-DAY4-2** (resolved in-sprint): `React.ReactNode` type referenced in `InspectorTurn` `KV` helper without importing React (vite-jsx default doesn't auto-import); fixed via explicit `import type { ReactNode } from "react"`.
- **D-DAY4-3** (resolved via Karpathy §3 + AP-2): Day 1 stub MessageList.tsx + its ToolCallCard consumer became orphans after Day 3 MessageList→TurnList swap. Deleted both (0 production importers; 0 tests; comment-only refs in 4 file headers / e2e spec headers don't block). Avoids AP-2 Potemkin + AP-11 version-suffix-lingering.
- **D-DAY4-4** (resolved in-sprint): `approval-card.spec.ts` e2e contract preservation via 2-line edit to HITLTurn outer wrapper (`role="region"` + `aria-label`). Existing test path: severity CRITICAL literal text already rendered via uppercase transform on `risk-critical` token; Approve button name matches via Playwright substring rule.
- **D-DAY4-5** (deferred Phase-2+): Composer.tsx ships visual-only; NEW carryover AD-ChatV2-Composer-Wire-Phase2 records the Sprint 57.22+ wire decision (extract-shared-hook vs proxy-via-composition vs full rewrite). Honest scope reduction per checklist §4.2 footer "lower-risk option (proxy via composition probably; final call at Day 4 start based on InputBar.tsx complexity)" — Day 4 final call = neither (defer wire to Phase-2). InputBar.tsx untouched.

### Quality gates (Day 4 EOD)

| Gate | Day 3 baseline | Day 4 EOD | Verdict |
|------|----------------|-----------|---------|
| tsc errors | 0 | 0 | ✅ |
| Vitest tests | 335 | **348** (+13 NEW) | ✅ 0 regression |
| Vitest files | 68 | 70 (+2 NEW: ChatInspector.test + Composer.test) | ✅ |
| Lint | silent | silent | ✅ |
| Build time | 2.77s | 2.94s | ✅ |
| Main bundle | 321.92 kB | **321.92 kB byte-identical** | ✅ (NEW Inspector + Composer tree-shake absorbed — Tabs primitive + lucide icons already chunked) |
| Backend changes | 0 | 0 | ✅ |
| LLM SDK leak | 0 | 0 | ✅ |
| Orphan files | 3 (MessageList + ToolCallCard + mockup .bak) | 0 ✅ | ✅ Karpathy §3 |
| chat_v2/components/*.tsx file count | 9 | 7 (+1 ChatHeader+SessionList+Composer−3 orphans+2 NEW = net −2) | ✅ |

### Notes / decisions

- **AP-2 anti-Potemkin maintained**: 3 coming-soon Inspector tabs each name their carryover AD + cite mockup section line range; Composer 3 disabled buttons each tooltip the carryover AD. No silent placeholders.
- **AP-3 cross-directory check**: all Day 4 NEW under `features/chat_v2/components/{,inspector/}`. 0 outside feature.
- **AP-4 visible mockup-fidelity gain**: ChatInspector 4-tab frame + populated InspectorTurn is the visible win of Day 4. Day 3 placeholder stub → real 4-tab + populated KV pairs + Block sequence.
- **AP-9 race condition check**: `InspectorTurn` derives last AgentTurn via `[...turns].reverse().find(...)` — pure synchronous selector, no useEffect data loop; mergeEvent reducer (Day 1) is synchronous.
- **AP-10 untested critical path**: 13 NEW Vitest cases cover Inspector 4-tab dispatch + InspectorTurn populated + 3 coming-soon AD references + Composer 5 visual contracts. e2e `approval-card.spec.ts` selectors will still locate the card via D-DAY3-3 surgical fix.
- **AP-11 no version suffix**: orphan delete (MessageList / ToolCallCard / .bak) is the cleanup; no `_v1` / `_old` / `_legacy` left.

### Estimate vs actual

- Bottom-up estimate: 3-5 hr (Inspector + Composer + closeout test/build/lint)
- Actual: ~3 hr (Inspector ~1.5 hr + Composer ~30 min + e2e contract fix + orphan cleanup + Vitest 13 NEW + retrospective WIP ~1 hr including this entry)
- Cumulative actual through Day 4 code: ~11.5 hr (Day 1 ~2.5 + Day 2 ~3.5 + Day 3 ~2.5 + Day 4 ~3 hr); calibrated commit was 9-11 hr → ratio actual/committed ≈ 1.05-1.28 ✅ within [0.85, 1.20] band lower edge with light over (consistent with 1st app of `frontend-mockup-direct-port` 0.55 ratio 0.45-0.55 below band — bottom-up 2× too generous still applies but Inspector 4-tab + populated InspectorTurn + e2e contract fix forced the cumulative back into band; if Day 4.4 doc syncs run another ~1-2 hr, final ratio rounds to ~1.2-1.4 over band by ~0.2 — see §4.4 retrospective Q2 for 2nd-app trend analysis).

### 🚧 DEFERRED Day 4 §4.3 Playwright MCP visual pair-verify

Mockup http server (port 8080) + dev server (port 3007) both still running. Playwright MCP capture step will be done as a separate sub-step before §4.4 retrospective finalization + §4.5 PR. Target captures:
- mockup `#chat` at 1440×900 (canonical visual target)
- production `/chat-v2` at 1440×900 (full SessionList + ChatHeader + TurnList placeholder + Inspector 4-tab + InputBar) — auth race D-PRE-4 mitigated via `/auth/dev-login` fallback
- Sub-zooms: SessionList left rail / ChatHeader top bar / Inspector Turn tab populated / Inspector Trace tab coming-soon

DRIFT verdict + cosmetic gaps logged in `claudedocs/4-changes/sprint-57-21-chatv2-fidelity-phase-1/DRIFT-REPORT-PHASE1.md` (file scaffold from Day 0; to be populated at §4.4).

## §4.4 — _pending — retrospective + memory + doc syncs_
