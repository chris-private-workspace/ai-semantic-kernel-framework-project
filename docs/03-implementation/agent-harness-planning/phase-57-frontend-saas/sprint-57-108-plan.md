# Sprint 57.108 Plan — UX slice: chat-v2 HITL approval card renders the real tool name + reason (additive `approval_requested` wire fields from the 5 escalate sites) and the Inspector turn metadata goes live (trace_id from the frame, span_id from the spans slice, tokens in/out via additive `llm_response` wire fields) — cost stays an honest "—" by design

**Status**: Draft (pending user approval)
**Branch**: `feature/sprint-57-108-chatv2-hitl-inspector-wire`
**Base**: `main` HEAD `a42ed717` (post-#282 merge)
**Slice**: 1 UX slice per the interleave decision (RBAC → C3 → B3 ✅ → **UX** → C2 → B4) — chat-v2 bundle picked by user 2026-06-12: `AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5)
**Scope decisions**: wire BOTH `tool_name` + `reason` onto `approval_requested` (both are in scope at every emission site — the AD names both); tokens in/out ride additive `llm_response` fields (the dataclass already carries them); `cost` + `tokens.thinking` stay honest "—" (cost is post-loop by design — see §3.4).

---

## 0. Background

The 2026-06-06 35-page drive-through audit (ISSUE-5) + the 57.106 drive-through left two honest-but-unwired chat-v2 surfaces. Neither is a Potemkin (both render "—" instead of fake values — FIX-030 Deferred analysis), but both block the reviewer workflow: an approver cannot see WHICH tool wants approval, and the Inspector turn pane shows no trace/span/token reality.

### Design decision (additive wire fields only; event count stays 24; no new event type; loop.py touched at yield sites only)

- **`ApprovalRequested` +2 sparse fields** (`tool_name: str | None` + `reason: str`): the DB-side `ApprovalRequest.payload` ALREADY stores both (loop.py:794-796/:1015/:1415-1417/:1579-1581) — the LoopEvent simply never carried them to the wire. `tool_name` is populated ONLY at the tool-escalate site (`tc.name` in scope at :1048); the other 4 kinds send None. `reason` is in scope at every site. This mirrors 57.100's additive-`kind` precedent exactly (no event-count bump, codegen regen, FE projection).
- **`llm_response` +2 fields** (`input_tokens` + `output_tokens`): `LLMResponded` (events.py:95-121) already carries both; the wire entry (event_wire_schema.py:97-102) already serializes `cached_input_tokens` — adding the pair is completing an existing pattern, not a new design.
- **`trace_id` is a pure FE fix**: sse.py:108-128 injects `data.trace_id` into EVERY frame; chatStore.ts:394 hardcodes `traceId: null` at `turn_start` instead of reading it.
- **`span_id` is a pure FE fix**: the store already tracks `spans` (57.75 A-5, chatStore.ts:147 + `span_started`/`span_ended` handlers :633+/:651+); the gap is linking the turn's span to `AgentTurn.spanId`.
- **`cost` stays "—" BY DESIGN**: cost is computed post-loop in the router observer (cost_ledger.py:107-141 — pricing lookup + 2-entry split, Sprint 56.3 D3); emitting it in-stream would mean a hot-path pricing lookup duplicating the ledger. Cost reality lives in the cost dashboard; the Inspector keeps the honest fallback (documented, not deferred-silently).
- **Rejected**: a new `turn_metadata` event type (24→25 bump + codegen churn for data that fits existing events); in-stream cost (above); reusing the audit-log content as the FE source (audit is compliance surface, not UI wire); wiring `payload`/arguments onto the card (tc.arguments can be large; the ToolBlock already renders them — YAGNI here).

### Ground truth (Day-0 head-start — 2 Explore recon agents + direct greps, file:line anchors on `main` HEAD `a42ed717`)

- **`ApprovalRequested`**: dataclass `_contracts/events.py:402-407` (`approval_request_id`/`risk_level`/`kind` — NO tool/reason); wire `event_wire_schema.py:121-125` (same 3); generated TS `loopEvents.generated.ts:79-87`.
- **5 emission sites (loop.py)**: :831 input (reason@:827) · :1048 tool (`tc.name` + `guardrail_reason`@:1044) · :1452 between_turns (reason@:1448) · :1616 output (reason@:1612) · :1833 verification (reason availability = Day-0 anchor). Resume keyed by `request_id` via `HITLManager.wait_for_decision` :1101-1105 — untouched.
- **FE approval flow**: chatStore.ts:533-571 `approval_requested` case — `tool: "—"` HARDCODED at :546, `rationale: "—"` also hardcoded; the `approvals` slice stores only `{approvalRequestId, riskLevel, decision}` (:562-567). Canonical render = `HITLTurn.tsx`; legacy fallback `ApprovalCard.tsx:135-137` (risk-only header). Decision POST via `governanceService.ts:71-84` — untouched.
- **InspectorTurn**: `inspector/InspectorTurn.tsx:167-181` — 8 KV rows with "—" fallbacks (stop_reason/duration/tokens.in/tokens.out/tokens.thinking/cost/trace_id/span_id). `AgentTurn` shape `types.ts:138-153`; `traceId`(:151)/`spanId`(:152) initialized null and NEVER set.
- **Tokens**: `LLMResponded` events.py:95-121 (`input_tokens`/`output_tokens`/`cached_input_tokens`); `llm_response` wire :97-102 carries `cached_input_tokens` only; FE handler chatStore.ts:433+ (`updateLastAgentTurn`, blocks only — no token mapping). `LoopCompleted` totals (events.py:130-179) → `loop_end` wire :115-120; cost post-loop only (cost_ledger.py:107-141).
- **Codegen chain**: `scripts/codegen/generate_event_schemas.py:70-77` → `frontend/src/features/chat_v2/generated/events.json` + `loopEvents.generated.ts`; parity test `test_event_wire_schema_parity.py:144-145` asserts `len(WIRE_SCHEMA) == 24` (additive FIELDS don't bump); `check_event_schema_sync.py:59-114` diffs field-level (regen + commit both artifacts or lint fails).
- **Tests today**: `ChatInspector.test.tsx` 10 tests (the "—" placeholder test :96-113 — CONVERT); `approval-card.spec.ts` e2e 4 tests; NO unit suite for the approval card (ADD). FE Vitest baseline 828 (137 files); full pytest 2460+4skip; mockup-fidelity 51.

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

Verification-escalate site (:1833) reason-in-scope · `ApprovalRequested` consumers beyond sse (subagent relay `_TAO_CHILD_EVENT_TYPES`? observer? resume replay path 57.99 — do any re-construct the event?) · loop unit tests asserting `ApprovalRequested(...)` call shapes (convert list) · `llm_response` serializer body (sse.py:161-170+ — where `cached_input_tokens` is read) · `turn_start` FE handler exact shape (:382-398) + whether `stop_reason`/`durationMs` are already wired by `turn_end`/`loop_end` handlers · span event payload shape (name/kind fields — which span is "the turn's span") · multiple `llm_response` per AgentTurn? (accumulate vs overwrite decision) · HITLTurn.tsx render lines for tool/rationale · `events.json` committed shape (codegen-shape drift class — nested `{type, data:{...}}` envelope).

## 1. Sprint Goal

A chat-v2 reviewer sees WHICH tool wants approval and WHY (real `tool_name` + `reason` on the HITL card, from additive `approval_requested` wire fields fed by all 5 escalate sites), and the Inspector turn pane shows live `trace_id` / `span_id` / `tokens.in` / `tokens.out` (frame trace_id + spans-slice linkage + additive `llm_response` token fields) — `cost` + `tokens.thinking` stay honest "—" by documented design; proven by a drive-through (real LLM + real tool-escalate approval + Inspector reality check). Closes `AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire`.

## 2. User Stories

- **US-1**: 作為 platform，我希望 `ApprovalRequested` 增加 `tool_name`（tool-escalate site 填 `tc.name`，其餘 kind 為 None）+ `reason`（全部 5 site 填既有 in-scope reason），上 wire（additive，event count 不變）並 regen codegen，以便 FE 能渲染真實核准上下文。
- **US-2**: 作為 chat-v2 reviewer，我希望 HITL 卡（HITLTurn 主渲染 + ApprovalCard legacy）顯示真實 `tool` + `rationale`（store 捕捉新欄位，取代 :546 寫死的 "—"），以便核准時知道在核准什麼（關閉 `AD-ChatV2-HITL-Card-Tool-Name`）。
- **US-3**: 作為 chat-v2 使用者，我希望 Inspector turn pane 的 `trace_id`（讀 frame `data.trace_id`）、`span_id`（spans slice 連回 AgentTurn）、`tokens.in/out`（additive `llm_response` 欄位 → store 映射）渲染真值，`cost`/`tokens.thinking` 維持誠實 "—"（設計如此，文件化），以便 turn 級觀測落地（關閉 `AD-ChatV2-Inspector-Turn-Metadata-Wire`）。
- **US-4**: 作為 reviewer，我希望 drive-through 證明：真 LLM 觸發 tool-escalate（57.106 harness_policy escalate-phrase / risky-detector 為觸發桿）→ 卡片顯示真 tool 名 + reason → approve 後 run 繼續；Inspector 顯示真 trace_id/span_id/tokens——全程真 UI + 真後端 + 真 LLM。

## 3. Technical Specifications

### 3.0 Architecture (additive wire fields only; event count 24 UNCHANGED; no DB / no migration; loop.py yield-site edits only)

```
loop.py 5 escalate sites: yield ApprovalRequested(..., tool_name=tc.name | None, reason=<in-scope reason>)
event_wire_schema.py: approval_requested += {tool_name: string|null, reason: string}
                      llm_response     += {input_tokens: number, output_tokens: number}
sse.py: serializers read the new dataclass fields (LLMResponded already has the tokens)
codegen regen → events.json + loopEvents.generated.ts (check_event_schema_sync field-level)
chatStore.ts: approval_requested case → tool/rationale real (drop the :546 hardcode) + approvals slice += toolName/reason
              turn_start case → traceId: ev.data.trace_id (drop the :394 hardcode)
              span_started case → link the turn's span id to the active AgentTurn.spanId
              llm_response case → tokensIn/tokensOut accumulate from ev.data
InspectorTurn / HITLTurn / ApprovalCard: render paths unchanged — they already consume the store fields
```

### 3.1 `ApprovalRequested` additive fields + emission (US-1)

`_contracts/events.py` `ApprovalRequested` += `tool_name: str | None = None` + `reason: str = ""` (frozen dataclass, defaulted — all existing constructors stay valid). loop.py: the 5 yield sites pass `reason=` from the already-in-scope local (`reason` / `guardrail_reason`); the tool site (:1048) additionally passes `tool_name=tc.name`. `event_wire_schema.py` `approval_requested` += 2 entries; `sse.py` approval serializer reads them. Codegen regen (both artifacts committed). Existing loop pause/escalate unit tests asserting event shape: CONVERT (0 deletions). Parity test: field assertions extended; count stays 24.

### 3.2 HITL card real tool + reason (US-2)

chatStore.ts `approval_requested` case: `tool: ev.data.tool_name ?? "—"` + `rationale: ev.data.reason || "—"` (honest fallback preserved for old frames / non-tool kinds); `approvals[id]` += `toolName`/`reason` (the decision flow stays keyed by `approvalRequestId` — untouched). `HITLTurn.tsx` + `ApprovalCard.tsx` render the real values (their KV rows already exist — verify at Day-0 whether any render line needs un-hardcoding beyond the store). FE Vitest: ADD approval-card/HITLTurn unit cases (tool name renders; non-tool kind falls back to "—"); e2e `approval-card.spec.ts` extended assertion.

### 3.3 Inspector turn metadata wire (US-3)

- **trace_id**: `turn_start` handler reads `ev.data.trace_id ?? null` (replaces the :394 hardcode). One-line + type already optional on every generated event.
- **span_id**: `span_started` handler — when a span starts while an AgentTurn is active and the turn has `spanId === null`, set it (first-span-of-turn rule; Day-0 verifies whether span events carry a name/kind that identifies the turn-root span — if yes, prefer the explicit match).
- **tokens**: `llm_response` handler maps `tokensIn: (t.tokensIn ?? 0) + ev.data.input_tokens` / `tokensOut: (t.tokensOut ?? 0) + ev.data.output_tokens` (accumulate — a TAO turn may carry multiple LLM calls; Day-0 confirms multiplicity).
- **NOT wired** (stay "—"): `cost` (post-loop by design — §3.4) + `tokens.thinking` (no server-side thinking-token count exists). `stop_reason`/`duration` expected already-wired — Day-0 confirms; wire if trivially broken, else note.
- FE Vitest: `ChatInspector.test.tsx` CONVERT (the "—" placeholder test narrows to cost/thinking) + ADD real-value cases; store unit tests for the 3 new captures.

### 3.4 What is explicitly NOT done

In-stream cost (pricing lookup stays post-loop in cost_ledger — the Inspector documents "cost: — (post-run; see cost dashboard)" via title/tooltip only if trivial, else bare "—"); thinking-token counts; HITL card payload/arguments row (ToolBlock already renders args); approval decision flow changes; sidechain transcript READ API; any new event type; any DB change.

### 3.5 Validation (US-1..US-4)

Unit (backend): `ApprovalRequested` field defaults + 5-site emission shapes (tool site carries tc.name; others None) · sse serializer reads both new pairs · parity test fields + count 24. Unit (FE Vitest): store captures (approval tool/reason; turn_start trace_id; span linkage; token accumulation) · HITLTurn/approval card render + fallback · InspectorTurn real-value + narrowed "—" cases. Integration: existing chat pause/approve e2e extended (approval frame carries tool_name) — no new suite needed. Gates: mypy strict 0 · run_all 10/10 (count 24 UNCHANGED; check_event_schema_sync green post-regen) · full pytest 0 del · FE lint/build/Vitest · mockup-fidelity 51 (no CSS change expected) · wire schema diff = additive-only.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/_contracts/events.py` | EDIT — `ApprovalRequested` +2 defaulted fields |
| 2 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT — 5 yield sites pass reason (+ tool_name at :1048) |
| 3 | `backend/src/api/v1/chat/event_wire_schema.py` | EDIT — approval_requested +2 / llm_response +2 |
| 4 | `backend/src/api/v1/chat/sse.py` | EDIT — 2 serializers read new fields |
| 5 | `frontend/src/features/chat_v2/generated/events.json` + `loopEvents.generated.ts` | REGEN (codegen) |
| 6 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT — 4 handler captures (approval / turn_start / span_started / llm_response) |
| 7 | `frontend/src/features/chat_v2/store/types.ts` | EDIT — ApprovalEntry +toolName/reason (AgentTurn unchanged — fields exist) |
| 8 | `HITLTurn.tsx` + `ApprovalCard.tsx` | EDIT — render real tool/rationale (as needed per Day-0) |
| 9 | backend tests: loop escalate shapes / sse serializer / parity | CONVERT + EDIT (0 deletions) |
| 10 | FE Vitest: ChatInspector CONVERT + approval card ADD + store tests | EDIT/NEW |
| — | `loop.py` control flow / resume path / HITLManager / DB / migrations | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `approval_requested` wire frames from a tool-escalate carry `tool_name` + `reason`; the other 4 kinds carry `tool_name: null` + their reason; event count stays 24; codegen artifacts committed in the same commit (check_event_schema_sync green).
2. Real-LLM drive-through: escalate-phrase/risky-tool ask → HITL card shows the REAL tool name + reason (not "—") → approve → run continues; non-tool escalate (e.g. input phrase) → card falls back to "—" for tool, real reason shown.
3. Inspector turn pane on a live run: `trace_id` + `span_id` + `tokens.in` + `tokens.out` render real values; `cost` + `tokens.thinking` stay "—"; the narrowed Vitest placeholder test green.
4. All gates green; 0 test deletions; `loop.py` diff limited to the 5 yield sites; no DB/migration; mockup-fidelity 51 unchanged.
5. Closes `AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire` in next-phase-candidates (cost carve-out documented, not silently dropped).

## 6. Deliverables

- [x] US-1 `ApprovalRequested` +2 fields + 5-site emission + wire/serializer + codegen regen + test conversions
- [x] US-2 HITL card real tool/reason (store capture + renders + Vitest)
- [x] US-3 Inspector trace_id/span_id/tokens wired (3 store captures + llm_response wire pair + Vitest convert)
- [x] US-4 drive-through PASS (tool-escalate card reality + Inspector reality; screenshots + observed-vs-intended)
- [x] CHANGE-075 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates)

## 7. Workload Calibration

- Scope class **`frontend-feature-with-event-wire-addition` 0.55** — 2nd data point (57.100 precedent ratio ~1.0 IN band: same shape — additive fields on existing events + codegen regen + chat-v2 FE wiring + cross-stack parity; no new event type, no DB).
- **Agent-delegated: no** — parent-direct (57.100 precedent; loop.py yield-site edits are correctness-sensitive; FE captures are small and entangled with store semantics); `agent_factor = 1.0`, 3-segment form.
- Bottom-up est ~11 hr (US-1 ~2.5 + US-2 ~2 + US-3 ~3 + drive-through ~1.5 + docs/closeout ~2) → class-calibrated commit ~6 hr (mult 0.55). Day 4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Real LLM may not trigger a tool-escalate on cue | 57.106 drive-through lever proven: per-tenant `harness_policy` escalate-phrase / risky-action detector (`os.system` deny-list) reliably forces kind="tool" ESCALATE |
| Frozen-dataclass field additions break positional constructors | fields are defaulted + keyword-style at all 5 sites; grep all `ApprovalRequested(` constructors (tests incl.) at Day-0 |
| Verification site (:1833) may lack an in-scope reason | Day-0 Prong-2 read; worst case that site sends `reason=""` (honest) |
| `ApprovalRequested` re-constructed elsewhere (resume replay 57.99 / subagent relay) | Day-0 Prong-2 grep ALL constructors + relay type sets |
| Codegen-shape drift (AD-Day0-Codegen-Existing-Shape-Capture) | additive fields land INSIDE the nested `data` envelope; regen via the script (never hand-edit); commit both artifacts same commit |
| Multiple `llm_response` per AgentTurn double-counts tokens | accumulate (+=) semantics + a 2-call store unit test; Day-0 confirms turn multiplicity |
| Span→turn linkage picks the wrong span | Day-0 reads span event payload (name/kind); prefer explicit turn-root match, fallback first-span-of-turn; Vitest pins the rule |
| `stop_reason`/`duration` assumed already-wired | Day-0 confirms via handler read; if broken, they're 1-line same-pattern fixes (fold in) |
| Risk Class E — stale backend masks new wire fields at drive-through | clean no-reload restart + startup probe of one `approval_requested` frame before driving |
| FE Vitest placeholder test narrows incorrectly | the "—" test (:96-113) narrows to cost/thinking ONLY — keep asserting honest fallbacks exist |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- In-stream cost emission (post-loop by design; cost reality = cost dashboard; only carve `AD-ChatV2-Inspector-Cost-InStream` if a real consumer demands it — YAGNI).
- Thinking-token counts (no server-side counter exists).
- HITL card payload/arguments row; approval decision flow / HITLManager changes; HITL policy read-side (`AD-HITL-Policy-ReadSide-Potemkin-Phase58` — own slice per user decision).
- Sidechain transcript READ API + Inspector replay (`AD-Sidechain-Transcript-Read-API`).
- `AD-FE-Tenant-Display-Fixture-Phase58` (separate UX slice).
- Any new event type / DB change / migration.
