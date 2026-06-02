# Sprint 57.69 — Checklist (HANDOFF Agent-Side Context Carry + FE Session-Pivot — A-3b slice 2)

**Plan**: [`sprint-57-69-plan.md`](./sprint-57-69-plan.md)
**Created**: 2026-06-02
**Status**: Draft (commit/push/PR user-gated)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> SPIKE → Day-4 design-note extension (`18-handoff-design.md`) + 8-point gate. Scope: C-1 agent-side carry (1 sprint); user-visible transcript continuity deferred (plan §9).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: `loop.py:1073-1094` HANDOFF branch; `_contracts/events.py:124-157` `LoopCompleted` (frozen, all-default); `Message` @ `chat.py:75-95`; `platform_layer/handoff/{service.py:87-174,persona_registry.py}` (context_carry.py absent ✓); `router.py` post-loop hook; `handler.py:369-399` resolve_session_persona; `session_repository.py` create_session (meta_data ✓ 57.68); FE `chatStore.ts:408-414` agent_handoff passthrough + `:69-103` state + `:105-132` _initial + `:193-201` loop_start + `:571` reset
- [x] **Prong 2 (content)**: `LoopCompleted` frozen all-default → `handoff_context` additive (D-DAY0-1); `sse.py:208-217` loop_end maps only 4 fields → no wire leak (D-DAY0-2); `resolve_session_persona` returns system-prompt str → seed as text block there, NOT LoopState.messages (D-DAY0-3, scope-reducing); token counting is async `ChatClient.count_tokens` → message-COUNT cap (D-DAY0-4, scope-reducing); `Message.content` = `str | list[ContentBlock]` → render both (D-DAY0-7)
- [x] **Prong 3 (schema)**: NO migration (`carried_context` rides `meta_data` JSONB; `create_session` accepts `meta_data` since 57.68); `WIRE_SCHEMA` stays 19 (no codegen); no new RLS (D-DAY0-5)
- [x] **Doc-location**: `18-handoff-design.md` (extend — §context-carry + §FE pivot + §5 update); 17.md §4.1 unchanged (event unchanged); CHANGE-037
- [x] Catalogued D-DAY0-1..7 in progress.md; **go/no-go = GO** (D-DAY0-3/4 simplify; <20% net change, same deliverables/AC → continue, no re-confirm)

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-69-handoff-context-carry-pivot` from `2a872210`; plan+checklist commit `26b2cf3d`; Day-0 progress commit
- [x] Decisions: carry = in-memory snapshot (not DB — D1); storage = message-count-capped verbatim in `meta_data["carried_context"]` (no migration — D-DAY0-4/5); summarize = design alternative (deferred); seed = text block in persona system prompt (D-DAY0-3); FE pivot post-stream + banner from oklch primitives (AP-2); **Agent-delegated: yes** (Stage-1 backend / Stage-2 frontend; design note parent-authored)

---

## Day 1 — Backend context-carry (Stage 1)

### 1.1 Loop context snapshot (US-1)
- [x] `_contracts/events.py` `LoopCompleted` += in-process `handoff_context: list[Message] | None = None` (additive, NOT wire-mapped; `from agent_harness._contracts.chat import Message`)
- [x] `loop.py:1090` HANDOFF branch snapshots `list(messages)` (shallow copy) onto the `LoopCompleted` it already builds; no control-flow change
- [x] Confirmed `sse.py:208-217` `loop_end` serializer maps only 4 fields (ignores `handoff_context`) — server-side only, no client leak (D-DAY0-2; integration test asserts)

### 1.2 Context-carry budget helper (US-2)
- [x] `platform_layer/handoff/context_carry.py` (NEW) — `cap_and_serialize(messages, *, max_messages=20) -> list[dict]`: serialize neutral `Message` shape → drop-OLDEST over **message-count** cap (D-DAY0-4: count not token budget → ChatClient-free) → JSON-able list; `_render_content` (str | list[ContentBlock]); `render_carried_context_block`; LLM-neutral
- [x] Unit (`test_context_carry.py`, 10): under/over budget, empty/None, drop-oldest order, str + list[ContentBlock] content, render block header
- [x] **NOTE (D-DAY0-4)**: budget = last-N message COUNT (not token budget) so `boot_handoff` stays ChatClient-free/neutral; refined from plan §3.2 wording (progress.md Day 0)

### 1.3 Boot-handoff carry storage (US-2)
- [x] `service.py` `boot_handoff` += `parent_context: list[Message] | None = None`; inside the atomic txn, set child `meta_data={"agent_role":…, "carried_context": cap_and_serialize(parent_context)}` when non-empty (else 57.68-identical `{"agent_role":…}`)
- [x] Unit (`test_service.py` +2): with/without `parent_context` (backward-compat); carried context tenant-scoped (parent tenant); cross-tenant still rejected (57.68 guard)

### 1.4 Router wiring (US-2)
- [x] `router.py:504-510` post-loop hook passes `event.handoff_context` → `boot_handoff(parent_context=…)`; fail-soft unchanged

### 1.5 Handler seeds carried context (US-3)
- [x] `handler.py:398-418` `resolve_session_persona` reads `meta_data["carried_context"]` → `render_carried_context_block` → appends to the resolved persona **system prompt** (D-DAY0-3: text block in the persona prompt, NOT LoopState.messages — simpler + avoids tool_call_id fragility; delivers agent-side context); nested fail-open on malformed
- [x] Unit (`test_chat_handoff_unit.py` +3): seed present (block in prompt) / absent (plain persona) / malformed (fail-open, no crash)
- [x] Backend green: black/isort/flake8 0; `mypy src/` 0/325; `run_all.py` 10/10 (`check_llm_sdk_leak` 0); 35 handoff tests + full unit 1439 pass (parent independently re-verified)

---

## Day 2 — Backend integration + FE session-pivot (Stage 2)

### 2.1 Backend integration (US-5)
- [ ] `test_chat_handoff.py` EXTEND — HANDOFF with non-trivial `state.messages` → child `meta_data["carried_context"]` populated + tenant-scoped + capped (drop-oldest); follow-up request to `new_session_id` boots a child loop whose initial `LoopState.messages` contains the carried prior turns; `loop_end` frame has NO `handoff_context`; 57.68 assertions still pass
- [ ] `run_all.py` 10/10 (no codegen drift — `WIRE_SCHEMA` 19); codegen `--check` 0; mypy src 0

### 2.2 FE pivot action + agent_handoff case (US-4)
- [ ] `chatStore.ts` `pivotSession(newSessionId, banner)` action — reset turns/status/stopReason/errorMessage/approvals/verifications/subagents; set `sessionId = activeSessionId = newSessionId`; set `handoffBanner`
- [ ] `handoffBanner: {targetAgent, reason} | null` state (cleared on next `loop_start`/`send`)
- [ ] `agent_handoff` case (`:408-414`): record rawEvent + `pivotSession(ev.data.new_session_id, {targetAgent, reason})`; exhaustive `never` switch stays type-safe

### 2.3 FE banner + i18n + render (US-4)
- [ ] `HandoffBanner.tsx` (NEW) — reads `handoffBanner`, renders target/reason from existing oklch primitives (`.badge.info`/`.hitl-card`), dismissible; AP-2 honesty comment (no mockup source)
- [ ] `ChatLayout.tsx` renders `<HandoffBanner>` above `TurnList`
- [ ] i18n handoff banner copy keys (繁中 user-facing; no mockup `i18n.jsx` source — documented)

### 2.4 FE tests + sweep (US-5)
- [ ] `chatStore.mergeEvent.test.ts` — `agent_handoff` pivots (turns reset, `sessionId`+`activeSessionId` set, `handoffBanner` set, rawEvent recorded)
- [ ] `HandoffBanner.test.tsx` (NEW) — render target/reason + dismiss
- [ ] `eventSchema.generated.test.ts` unchanged (no wire change); tsc 0; Vitest green; `npm run build` ✓ (NO `--silent`)

---

## Day 3 — Full sweep + edge cases

- [ ] Full `pytest tests/unit tests/integration` green (carry + 57.68 + no regression); tenant-scoping + budget-cap + handler-seed asserted
- [ ] Edge: empty parent conversation (no carry, backward-compat); over-budget (drop-oldest); malformed carried_context (fail-open); pivot order vs loop_end (post-stream)
- [ ] Parent decisive re-verify: pytest full count; `mypy src/` 0; `run_all.py` 10/10; codegen `--check` 0; tsc 0; Vitest count; build ✓
- [ ] If any drift from plan → catalog in progress.md + adjust (do NOT silently rewrite plan)

---

## Day 4 — Design note (8-point gate) + Closeout

### 4.1 Design note extension (US-5)
- [ ] `18-handoff-design.md` EXTEND — NEW §context-carry (agent-side, in-process carrier, capped verbatim, copy-vs-summarize tradeoff, seed placement) + NEW §FE session-pivot (pivot action, post-stream, banner AP-2) + §5 open-invariant update (agent-side carried ✅; user-visible transcript continuity still deferred + why); 8-point gate ALL ✅; verified-ratio ≥95%
- [ ] retrospective.md §Design Note Extract record (8-point self-check)

### 4.2 Closeout
- [ ] Full validation (parent re-verified): pytest full / mypy src 0 / run_all 10/10 / codegen --check 0 / Vitest / build
- [ ] 17.md §4.1 unchanged (note in design note that `LoopCompleted.handoff_context` is an in-process carrier, not a wire contract); `CHANGE-037`
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [ ] Calibration: `handoff-context-carry-spike` 0.55 (NEW, 1 pt) + `agent_factor mechanical-greenfield-design-decisions` 0.65 (CAVEATED — 7th consecutive no-clean-wall-clock); `AD-Day0-Codegen-Existing-Shape-Capture` watch; recorded `calibration-log.md §3`
- [ ] Area-A: A-3b slice 2 (agent-side carry + FE pivot) shipped; user-visible transcript continuity + summarize-carry + target auto-first-turn + multi-hop + real catalog = carryover (design note §5)
- [ ] MEMORY.md pointer + `project_phase57_69_*.md` subfile + CLAUDE.md lean (per §Sprint Closeout policy)
- [ ] commit (Day 1-4) + push + PR — user-authorized
- [ ] **Final-commit `black --check`** (per `AD-Final-Commit-Black-Check`, 57.68 lesson) before push
