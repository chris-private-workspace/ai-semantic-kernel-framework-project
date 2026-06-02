# Sprint 57.69 Plan — HANDOFF Agent-Side Context Carry + FE Session-Pivot (A-3b slice 2)

**Purpose**: Ship the second slice of the user-chosen full HANDOFF model (Option B): (a) **agent-side context carry** — when a parent agent hands off, snapshot the parent's in-memory conversation and seed it into the child session so the **target agent runs with the prior conversation in its prompt** (it "remembers" what was discussed); and (b) **FE session-pivot** — when the client receives the `agent_handoff` SSE event (shipped 57.68), it pivots the active chat session to `new_session_id` and shows a handoff transition banner. Slice 1 (Sprint 57.68) shipped the backend control transfer + platform session-boot + the `agent_handoff` event but carried only the parent→child FK **linkage** (no conversation context) and left the FE as a rawEvents-only passthrough (no UI). This slice closes the agent-side half of "context carry" + the FE pivot. **This is a SPIKE** (context-carry copy-vs-summarize is a new mechanism) → Day-4 design-note extension to `18-handoff-design.md` + 8-point quality gate (per `sprint-workflow.md §Step 5.5`).
**Category / Scope**: Cat 11 (Subagent Orchestration — HANDOFF) + Cat 1 (loop context snapshot on the HANDOFF branch) + platform-layer handoff service (context-carry storage) + Cat 5 (handler seeds the carried context into the child's prompt) + Frontend (chat_v2 session-pivot + banner); Phase 57.69
**Created**: 2026-06-02
**Status**: Draft (user-approved scope: Option C-1 "agent-side carry, 1 sprint" after a >50% Day-0 reality drift reshaped Option C — see §0; code execution gated on Day-0 GO)
**Source**: Area-A capstone (A-3b slice 2) + 57.68 design note `18-handoff-design.md §5` open invariants (FE session-pivot + full message-context carry) + **two-round Day-0 reality audit (2 codebase-researchers, 2026-06-02)** (backend message-persistence map + frontend chat_v2 pivot-surface map) + user AskUserQuestion decisions 2026-06-02 (Option C "FE pivot + full message-context carry" → reshaped to C-1 "agent-side carry" after the persistence-gap finding)

> **Modification History**
> - 2026-06-02: Initial creation — A-3b slice 2; SPIKE (design-note extension); folds the Day-0 reality drift (no message persistence exists → context-carry must source the in-memory loop state, not the DB) into §0; backend-first + FE-pivot decomposition per server-side-first discipline

---

## 0. Background

Sprint 57.68 (A-3b slice 1) shipped HANDOFF as a real control transfer: `loop.py` ends the parent with `stop_reason="handoff"`, `HandoffService.boot_handoff` atomically boots a persisted, tenant-scoped, **linked** (`handoff_parent_id`), audited child session under a resolved persona, and an `agent_handoff` SSE event (`{target_agent, reason, parent_session_id, new_session_id}`) makes it observable. `18-handoff-design.md §5` listed the deferred half: **FE session-pivot** + **full message-context carry**. The user chose to do both next (AskUserQuestion 2026-06-02 → "FE pivot + full message-context carry").

### ⚠️ Day-0 reality drift (>50% — reshaped the chosen option; folded per `sprint-workflow.md §Step 2.5`)

Two researcher rounds (backend persistence map + FE pivot-surface map) surfaced a single finding that breaks the original Option-C premise:

- **D1 — conversation messages are NEVER persisted.** The `Message` ORM (`infrastructure/db/models/sessions.py:141-195`, JSONB `content`, monthly-partitioned, composite PK `(id, created_at)`) exists but is **never written** on the chat path (grep: zero `Message(` writers, no `MessageRepository`, no reader). The conversation lives ONLY in the in-memory `LoopState.messages` during the loop; the **FE rebuilds the transcript purely from the live SSE stream** into `turns` (no history-fetch endpoint, `chatStore.ts`). → "copy persisted parent messages into the child" has **nothing to copy**.
- **D2 — "context carry" splits into two reality-separated meanings.** (i) **Agent-side context** — the target agent's prompt includes the prior conversation; achievable by snapshotting the in-memory `LoopState.messages` at the handoff point (no new persistence infra). (ii) **User-visible transcript continuity** — the pivoted UI shows the old messages; requires a whole message-persistence subsystem (writer + `MessageRepository` + `GET sessions/{id}/messages` + FE loader + partitioned-table writes + `sequence_num`/`turn_num` regen) = 2+ sprints.
- **D3 — user decision (AskUserQuestion 2026-06-02, after the drift):** **Option C-1 "agent-side carry, 1 sprint"** (over C-2 "build persistence first, 2+ sprints" and C-3 "pivot-only"). This slice carries agent-side context from the in-memory loop state; user-visible transcript continuity stays deferred (design-note open question; needs the persistence subsystem).
- **D4 — the carry source is the in-memory `LoopState.messages` at `loop.py`'s HANDOFF branch** (`loop.py:1073-1091`, shipped 57.68 — `state.messages` is in scope there). The router post-loop hook calls `boot_handoff`; the message snapshot must flow loop → router → service. 57.68's precedent: the loop carries `handoff_target`/`handoff_reason` on `LoopCompleted` and the router reads them post-loop. → carry the snapshot the same way on an **in-process-only** `LoopCompleted` field (NOT mapped to the `loop_end` wire schema → stays server-side; no client leak). Day-0 Prong-2 reads the exact `LoopCompleted` shape + how the router accesses it before the edit (`AD-Day0-Codegen-Existing-Shape-Capture` lesson).
- **D5 — `boot_handoff` stays LLM-neutral; storage = `meta_data` JSONB (no migration).** The carried context is stored as capped verbatim messages in the child's `meta_data["carried_context"]` (the `meta_data` JSONB column already exists; `create_session` already accepts `meta_data` — 57.68). The budget cap reuses the 57.65 `_apply_memory_budget` pattern (neutral `token_counter`, drop-oldest over budget). **No Alembic migration, no new wire-type, no codegen regen** this slice (unlike 57.68). Summarize-via-Cat-4 `SemanticCompactor` (`context_mgmt/compactor/semantic.py:67`, LLM-neutral, `LoopState`-shaped) is the **design alternative** (open question) — not built this slice.
- **D6 — handler seeds the carried context on the child's first turn.** The child runs on the NEXT chat request to `new_session_id` (57.68 — "runs on next request"); `handler.py` already resolves persona from `meta_data["agent_role"]` (`handler.py:369`). It additionally reads `meta_data["carried_context"]` → seeds the child's initial `LoopState.messages` (prior messages) so the target agent sees the conversation. Day-0 Prong-2 reads how `handler.py` builds the initial loop state.
- **D7 — FE pivot is post-stream (no mid-stream race).** `agent_handoff` is emitted by the router post-loop hook AFTER `LoopCompleted`/`loop_end` (57.68), so it arrives as the parent stream is ending — the FE pivot resets to the child session cleanly with no abort race. Store gaps (researcher): `sessionId` (`chatStore.ts:71`, set only by `loop_start`) ≠ `activeSessionId` (`:83`); no session-switch action; `mergeEvent` exhaustive `never` switch; `agent_handoff` is a rawEvents-only passthrough (`:408-414`). → add a `pivotSession(newId)` action (reset turns/slices + set BOTH ids) + change the `agent_handoff` case to pivot + set a banner.
- **D8 — no mockup for handoff UI.** `reference/design-mockups/` has no handoff/transition/banner markup (researcher #7). Compose the banner from existing oklch primitives (`.badge.info` `styles.css:527` / `.hitl-card` `:845-892`); document as production-only honesty (AP-2 — no verbatim mockup source). i18n: add handoff copy keys (no mockup copy to mirror).

**Net**: a coherent 2-part vertical — (backend) the loop snapshots `state.messages` on the HANDOFF branch → carried in-process on `LoopCompleted` → the router passes it to `boot_handoff` → stored capped-verbatim in the child's `meta_data["carried_context"]` → `handler.py` seeds it into the child's first-turn loop state so the target agent runs with the prior conversation; (frontend) the `agent_handoff` event pivots the active session to `new_session_id` + shows a banner. Non-Potemkin (the target agent demonstrably receives the prior context; the pivot is observable). User-visible transcript continuity + summarize-carry + multi-hop deferred (§9).

---

## 1. Sprint Goal

Carry the parent's conversation to the handoff target (agent-side) and pivot the client to the new session: on a HANDOFF the loop snapshots the parent's in-memory `LoopState.messages` and carries it (in-process, non-wire) on `LoopCompleted`; the chat router passes the snapshot to `HandoffService.boot_handoff`, which stores a token-budget-capped verbatim copy in the child session's `meta_data["carried_context"]` (LLM-neutral, no migration); `handler.py` seeds that carried context into the child's first-turn loop state so the target agent runs with the prior conversation in its prompt. On the frontend, the `agent_handoff` SSE event pivots the active chat session to `new_session_id` (resetting turns + setting `sessionId` and `activeSessionId`) and renders a handoff transition banner. Prove it with backend integration tests (HANDOFF → child `meta_data["carried_context"]` populated, tenant-scoped, capped; handler seeds it) + FE store/component tests (pivot resets to the child + banner) + a Day-4 design-note extension (8-point gate). **Multi-tenant 鐵律: the carried context is the parent's tenant's data, stored on a same-tenant child; never cross-tenant.** User-visible transcript continuity deferred (§9).

---

## 2. User Stories

- **US-1 (loop context snapshot)** — As the agent loop, when the LLM emits a HANDOFF, I want to snapshot the current `LoopState.messages` and carry it (in-process, NOT on the client wire) on `LoopCompleted` alongside the existing `handoff_target`/`handoff_reason`, so the platform can seed the target with the prior conversation. → `loop.py:1073-1091` (extend the 57.68 branch); `_contracts/events.py` `LoopCompleted` += in-process `handoff_context`.
- **US-2 (platform context-carry storage)** — As the platform, when booting the child handoff session, I want to store a token-budget-capped verbatim copy of the carried messages in the child's `meta_data["carried_context"]` (drop-oldest over budget, neutral token_counter), so the carry is durable + bounded without a schema change or an LLM call. → `HandoffService.boot_handoff` += `parent_context` param; new `platform_layer/handoff/context_carry.py` budget/serialize helper.
- **US-3 (handler seeds carried context)** — As the booted child session's first turn, I want `handler.py` to read `meta_data["carried_context"]` and seed it into my initial loop state (prior messages before the new user input), so the target agent actually runs with the prior conversation. → `handler.py` (near the persona resolution at `:369`) seeds carried context into the initial `LoopState.messages`.
- **US-4 (FE session-pivot + banner)** — As a client, when I receive an `agent_handoff` event, I want to pivot the active session to `new_session_id` (reset the conversation, set `sessionId` + `activeSessionId`) and see a handoff transition banner (e.g. "已交棒給 {target_agent}"), so the handover is visible and the next message goes to the child session. → `chatStore.ts` `pivotSession` action + `agent_handoff` case → pivot + banner state; new `HandoffBanner` component (oklch primitives); i18n copy.
- **US-5 (validation + design note)** — As a reviewer, I want backend integration tests (HANDOFF → child `carried_context` populated/tenant-scoped/capped; handler seeds it into the first turn) + FE tests (pivot resets to child + banner) + a Day-4 `18-handoff-design.md` extension (8-point gate) capturing the agent-side context-carry design + copy-vs-summarize tradeoff + the still-deferred transcript-continuity, so the spike's learnings are extracted.

---

## 3. Technical Specifications

### 3.0 Architecture (agent-side carry + FE pivot slice)

```
LLM emits HANDOFF → loop.py:1073-1091 (57.68 branch)
   → snapshot state.messages (US-1)
   → LoopCompleted(stop_reason="handoff", handoff_target, handoff_reason, handoff_context=<snapshot>)
        (handoff_context is in-process only — NOT in the loop_end wire schema → no client leak)
        ▼
router.py _stream_loop_events post-loop hook (57.68)
   → boot_handoff(..., parent_context=event.handoff_context)            [US-2]
        └─ context_carry.cap_and_serialize(messages, token_budget)       (drop-oldest, neutral counter)
        └─ create_session(child, ..., meta_data={"agent_role":…, "carried_context":[…capped…]})
   → yield AgentHandoff event (unchanged — agent_handoff wire-type already shipped 57.68)
        ▼
(next chat request to new_session_id) handler.py (~:369)               [US-3]
   → resolve persona from meta_data["agent_role"] (57.68)
   → seed meta_data["carried_context"] into the initial LoopState.messages (prior turns)
        ▼ (frontend)
SSE agent_handoff frame → chatStore.mergeEvent → pivotSession(new_session_id)  [US-4]
   → reset turns/status/slices, set sessionId AND activeSessionId = new_session_id, set handoffBanner
   → <HandoffBanner> renders ("已交棒給 {target_agent}")
```

`boot_handoff` stays LLM-neutral (stores data only — no ChatClient, no summarize this slice). The carried context is the parent's tenant's data on a same-tenant child (鐵律). `loop.py` changes only add a snapshot to the existing 57.68 HANDOFF branch (no control-flow rewrite).

### 3.1 Loop context snapshot (US-1) — `loop.py` (~:1073-1091) + `_contracts/events.py`
- At the existing 57.68 HANDOFF branch, snapshot `state.messages` (the in-memory conversation) into the `LoopCompleted` the branch already builds. Add an **in-process-only** optional field `handoff_context: list[Message] | None = None` to `LoopCompleted` (`_contracts/events.py`). Day-0 Prong-2 reads the exact `LoopCompleted` shape + the `Message` type used in `state.messages` + confirms the `sse.py` `loop_end` serializer does NOT map the new field (so it never reaches the client).
- The snapshot is a shallow copy of the message list at handoff time; no transformation in the loop (copy-vs-summarize decided in the platform layer — server-side-first; the loop owns state, the platform owns the carry policy).

### 3.2 Platform context-carry storage (US-2) — `boot_handoff` + `context_carry.py` (NEW)
- `HandoffService.boot_handoff(*, parent_session_id, target_agent, reason, tenant_id, user_id, db, parent_context: list[Message] | None = None)` — extend the 57.68 signature with `parent_context`.
- NEW `platform_layer/handoff/context_carry.py`: `cap_and_serialize(messages, *, token_budget, token_counter) -> list[dict]` — serialize messages to JSON-able dicts (the `Message` neutral shape — role/content), apply a token budget (drop OLDEST over budget, mirroring 57.65 `builder._apply_memory_budget`), return the capped list. Default `token_budget` a module constant (e.g. 4000 — a conservative slice of the child's context; documented + tunable). LLM-neutral (uses the neutral `token_counter`, no provider SDK).
- In `boot_handoff`, inside the existing atomic transaction (after persona resolve, within `create_session`): set `meta_data={"agent_role": target_agent, "carried_context": cap_and_serialize(parent_context, …)}` when `parent_context` is non-empty (else just `{"agent_role": …}` — backward-compatible with 57.68). No migration (JSONB).
- **Multi-tenant 鐵律**: the carried context is part of the same atomic, parent-tenant-scoped child boot; cross-tenant is already rejected by the 57.68 tenant guard (`get_session(parent, tenant_id)`).

### 3.3 Handler seeds carried context (US-3) — `handler.py` (~:369)
- Where `resolve_session_persona` reads `meta_data["agent_role"]` (57.68), also read `meta_data["carried_context"]` (if present) → deserialize to `Message`s → seed them as the prior messages in the child's initial `LoopState.messages` (before the new user input). Day-0 Prong-2 reads how `handler.py`/the builder constructs the initial loop state (where messages are first assembled) so the seed lands in the right place. Fail-open: a missing/malformed `carried_context` → empty seed (the child runs without prior context, never crashes).

### 3.4 FE session-pivot + banner (US-4) — `chatStore.ts` + `HandoffBanner` + i18n
- `chatStore.ts`: NEW `pivotSession(newSessionId, banner)` action — reset `turns`/`status`/`stopReason`/`errorMessage`/`approvals`/`verifications`/`subagents` (reuse the `reset()` slice clearing at `:571`), set `sessionId = activeSessionId = newSessionId`, set `handoffBanner = {targetAgent, reason}`. Add `handoffBanner: {targetAgent, reason} | null` to the store state (cleared on the next `loop_start`/`send`).
- Change the `agent_handoff` case (`:408-414`) from rawEvents-only passthrough to: still record the rawEvent + call `pivotSession(ev.data.new_session_id, {targetAgent: ev.data.target_agent, reason: ev.data.reason})`. Keep the exhaustive `never` switch type-safe.
- NEW `HandoffBanner` component (under `chat_v2/components/`): renders the banner from existing oklch primitives (`.badge.info`/`.hitl-card`), reads `handoffBanner` from the store, dismissible. Rendered in `ChatLayout.tsx` (above `TurnList`). **AP-2 honesty**: no mockup source exists for this widget → documented as production-only, composed from existing design-system classes (no new `styles-mockup.css` class unless unavoidable; if added, byte-additive + documented).
- i18n: add handoff banner copy keys (繁中 user-facing per project convention; no mockup `i18n.jsx` source to mirror — documented).

### 3.5 No wire / schema / migration change (D5/D7)
- `agent_handoff` wire-type, `AgentHandoffEvent` TS type, `event_wire_schema.py`, the codegen, and the parity test are ALL unchanged (shipped 57.68 — this slice consumes them). No Alembic migration (`carried_context` rides the existing `meta_data` JSONB). `WIRE_SCHEMA` stays 19; codegen `--check` stays green with no regen.

### 3.6 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (`context_carry.py` + `boot_handoff` are provider-free — they store data with a neutral token_counter, no SDK; `agent_harness/**` only gets the `loop.py` snapshot + the in-process `LoopCompleted` field). `check_rls_policies` green (no new table/column). All 10 V2 lints green (no codegen drift — `check_event_schema_sync` green with no regen).
- **Doc single-source**: 17.md §4.1 `AgentHandoff` emit-ownership unchanged (the event is unchanged); the in-process `LoopCompleted.handoff_context` field is NOT a cross-category wire contract (server-side carrier) — noted in the design note, not 17.md. The Day-4 `18-handoff-design.md` extension is the context-carry design authority.

### 3.7 Validation (US-5)
- **Backend integration** (`test_chat_handoff.py` EXTEND): drive a loop emitting HANDOFF with a non-trivial `state.messages` → assert (a) the child `meta_data["carried_context"]` is populated with the (capped) parent messages; (b) it is tenant-scoped (the child is the parent's tenant — 鐵律); (c) over-budget input is dropped-oldest to the cap; (d) a follow-up chat request to `new_session_id` boots a child loop whose initial `LoopState.messages` contains the carried prior turns (handler seed). + the 57.68 assertions still pass (linkage, handed_off, audit, agent_handoff frame).
- **Backend unit**: `context_carry.cap_and_serialize` (under/over budget, empty, drop-oldest order); `boot_handoff` with/without `parent_context` (backward-compat); `handler.py` carried-context seed (present / absent / malformed → fail-open).
- **Frontend**: `chatStore.mergeEvent.test.ts` — `agent_handoff` now pivots (turns reset, `sessionId` + `activeSessionId` = `new_session_id`, `handoffBanner` set, rawEvent still recorded); `HandoffBanner` component test (renders target/reason, dismiss). `eventSchema.generated.test.ts` unchanged (no wire change).

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** (~:1073-1091) — snapshot `state.messages` onto the 57.68 HANDOFF branch's `LoopCompleted` (US-1) |
| `backend/src/agent_harness/_contracts/events.py` | **EDIT** — `LoopCompleted` += in-process `handoff_context: list[Message] | None` (NOT wire-mapped) (US-1) |
| `backend/src/platform_layer/handoff/context_carry.py` | **NEW** — `cap_and_serialize(messages, token_budget, token_counter)` drop-oldest budget helper (US-2) |
| `backend/src/platform_layer/handoff/service.py` | **EDIT** — `boot_handoff` += `parent_context`; store capped carry in child `meta_data["carried_context"]` (US-2) |
| `backend/src/api/v1/chat/router.py` | **EDIT** (`_stream_loop_events` post-loop hook) — pass `event.handoff_context` to `boot_handoff` (US-2) |
| `backend/src/api/v1/chat/handler.py` | **EDIT** (~:369) — seed `meta_data["carried_context"]` into the child's initial `LoopState.messages` (US-3) |
| `frontend/src/features/chat_v2/store/chatStore.ts` | **EDIT** — `pivotSession` action + `handoffBanner` state + `agent_handoff` case → pivot (US-4) |
| `frontend/src/features/chat_v2/components/HandoffBanner.tsx` | **NEW** — transition banner (oklch primitives; AP-2 honesty) (US-4) |
| `frontend/src/features/chat_v2/components/ChatLayout.tsx` | **EDIT** — render `<HandoffBanner>` (US-4) |
| `frontend/src/features/chat_v2/i18n/*` (or existing i18n location) | **EDIT** — handoff banner copy keys (US-4) |
| `backend/tests/integration/api/test_chat_handoff.py` | **EXTEND** — carried_context populated/tenant-scoped/capped + handler seed (US-5) |
| `backend/tests/unit/...` | **NEW/extend** — `context_carry` budget + `boot_handoff` parent_context + handler seed (US-5) |
| `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` | **EDIT** — `agent_handoff` pivot behavior (US-5) |
| `frontend/tests/unit/chat_v2/components/HandoffBanner.test.tsx` | **NEW** — banner render/dismiss (US-5) |
| `docs/03-implementation/agent-harness-planning/18-handoff-design.md` | **EDIT (Day-4 extract)** — §context-carry (agent-side, copy-vs-summarize) + §FE session-pivot + §5 open-invariant update (8-point gate) |
| `claudedocs/4-changes/feature-changes/CHANGE-037-handoff-context-carry-pivot.md` | **NEW** — change record |

**No Alembic migration, no new wire-type, no codegen regen, no Azure-adapter change.** `event_wire_schema.py` / generated FE files unchanged.

---

## 5. Acceptance Criteria

- A HANDOFF snapshots the parent's `state.messages` and carries it in-process on `LoopCompleted`; the field is NOT serialized to the `loop_end` client wire (server-side only).
- `boot_handoff` stores a token-budget-capped verbatim copy of the carried messages in the child's `meta_data["carried_context"]` (drop-oldest over budget); LLM-neutral; no migration; the 57.68 atomic boot (linkage, handed_off, audit, event) still holds; cross-tenant rejected.
- A follow-up chat request to `new_session_id` boots a child loop whose initial `LoopState.messages` contains the carried prior turns (handler seed); a missing/malformed `carried_context` fails open (no prior context, no crash).
- The FE `agent_handoff` event pivots the active session to `new_session_id` (turns reset, `sessionId` + `activeSessionId` set) and renders a handoff banner; the rawEvent is still recorded; the exhaustive switch stays type-safe.
- All existing tests green; `mypy --strict src/` 0; 10/10 V2 lints (LLM SDK leak 0; `check_event_schema_sync` green with NO regen — `WIRE_SCHEMA` stays 19); codegen `--check` green; Vitest green (new banner/store tests added). Day-4 `18-handoff-design.md` extension passes the 8-point gate.

---

## 6. Deliverables

- [ ] `loop.py` HANDOFF context snapshot + `events.py` in-process `LoopCompleted.handoff_context` (US-1)
- [ ] `context_carry.py` budget helper (US-2)
- [ ] `boot_handoff` `parent_context` → child `meta_data["carried_context"]` (US-2)
- [ ] `router.py` passes `handoff_context` to `boot_handoff` (US-2)
- [ ] `handler.py` seeds carried context into the child's first-turn loop state (US-3)
- [ ] `chatStore.ts` `pivotSession` + `handoffBanner` + `agent_handoff` pivot case (US-4)
- [ ] `HandoffBanner` component + `ChatLayout` render + i18n copy (US-4)
- [ ] backend integration + unit tests + FE store/component tests (US-5)
- [ ] `18-handoff-design.md` Day-4 extension (8-point gate) (US-5)
- [ ] CHANGE-037 + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: **`handoff-context-carry-spike` (0.55, NEW — pending validation)** — a mixed backend-spike (in-memory context snapshot + capped-carry storage + handler seed; copy-vs-summarize design decision + Day-4 design note) + FE slice (session-pivot action + banner, no mockup source). Sibling of 57.68's `backend-control-transfer-spike` 0.55 (same HANDOFF feature family) but lighter (NO migration / NO new wire-type / NO codegen regen — D5). **Agent-delegated: yes** (staged: Stage-1 backend — loop snapshot + `context_carry` + `boot_handoff` + handler seed + backend tests; Stage-2 frontend — `pivotSession` + `HandoffBanner` + i18n + FE tests; design note parent-authored). `agent_factor` **`mechanical-greenfield-design-decisions` 0.65** (genuine design: in-process carrier field, budget policy, seed placement, pivot/banner UX).

> Bottom-up est ~13 hr → class-calibrated commit ~7.2 hr (mult 0.55) → agent-adjusted commit ~4.7 hr (agent_factor 0.65).

Caveat (carried 57.63-57.68): agent-delegated sprints have no clean wall-clock (`AD-Calibration-AgentDelegated-WallClock-Measure`; would be 7th consecutive). The NEW `handoff-context-carry-spike` class is a single unvalidated data point — record caveated, do NOT generalize. If Day-1 proves the handler-seed (where carried context enters the child's loop state) is larger than read, slice (defer the handler seed to a stub + carry-storage-only) and re-confirm.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **D1 — no message persistence; "DB copy" impossible** | carry the in-memory `LoopState.messages` snapshot at the HANDOFF branch (not the DB); user-visible transcript continuity deferred (§9) — this is the user-chosen C-1 |
| **In-process field leaks to the client wire** | `LoopCompleted.handoff_context` is NOT added to the `event_wire_schema.py`/`sse.py` `loop_end` mapping; Day-0 Prong-2 confirms the serializer ignores it; an integration test asserts no `handoff_context` in the `loop_end` frame |
| **Carried context blows the child's token budget** | `cap_and_serialize` applies a conservative token budget (drop-oldest), reusing the 57.65 `_apply_memory_budget` pattern with the neutral `token_counter` |
| **`boot_handoff` neutrality** | storage-only (capped verbatim JSON in `meta_data`); NO ChatClient/summarize this slice; `check_llm_sdk_leak` gates; summarize-via-Cat-4 is a design-note alternative (§9) |
| **Handler seed lands in the wrong place** (target doesn't actually see the context) | Day-0 Prong-2 reads how `handler.py`/the builder assembles the initial `LoopState.messages`; an integration test boots the child loop and asserts the prior turns are present |
| **FE pivot mid-stream race** | `agent_handoff` arrives AFTER `loop_end` (57.68 post-loop hook) — the parent stream is ending; pivot is post-stream; store test asserts the order |
| **`sessionId` ≠ `activeSessionId`** | `pivotSession` sets BOTH to `new_session_id` (researcher D7) |
| **No mockup for the banner (AP-2)** | compose from existing oklch primitives (`.badge.info`/`.hitl-card`); document production-only honesty; no fabricated mockup source |
| **`LoopCompleted` / `Message` / handler shapes** | Day-0 Prong-2 reads the real shapes before edits (`AD-Day0-Codegen-Existing-Shape-Capture` — read the real shape, esp. after 57.68's `handoff_request`→tool_call correction) |
| **Multi-tenant** | carried context is part of the same atomic parent-tenant child boot; cross-tenant rejected by the 57.68 guard; test asserts tenant scoping |
| **Scope > 1 sprint** | this slice = agent-side carry + FE pivot only; transcript continuity + summarize + multi-hop + real catalog deferred (§9); Day-1 slice further if the handler-seed proves larger |

---

## 9. Out of Scope (this sprint; carryover toward full Option B)

- **User-visible transcript continuity** — the pivoted UI showing the parent's prior messages. Requires a message-persistence subsystem (writer + `MessageRepository` + `GET sessions/{id}/messages` + FE history loader + partitioned-table writes + `sequence_num`/`turn_num` regen) = 2+ sprints (the Day-0 D1/D2 finding). This slice carries agent-side context only; the pivoted UI starts visually empty + a banner.
- **Summarize-carry (copy-vs-summarize)** — verbatim capped copy this slice; summarizing the parent conversation via the Cat-4 `SemanticCompactor` (`context_mgmt/compactor/semantic.py`) is the design-note alternative (open question — needs a `LoopState` adapter + an LLM call in the carry path).
- **Target auto-first-turn** — the target agent runs on the NEXT client request to `new_session_id` (57.68); auto-running a turn on boot is still deferred.
- **Multi-hop handoff chains** (A→B→C) + cycle/loop guards — design-note open question.
- **Real agent/persona catalog** — `persona_registry.py` is a 3-entry hardcoded stand-in (57.68); a DB-backed per-tenant catalog is future work.
- **`sessions.agent_role` / `carried_context` dedicated columns** — persona + carried context in `meta_data` JSONB this slice (YAGNI; columns are a future refinement if querying-by-agent / large-context offloading is needed).
- **Message persistence subsystem** — explicitly NOT bootstrapped by this handoff slice (it is its own epic; the `messages` table stays dormant this sprint).
