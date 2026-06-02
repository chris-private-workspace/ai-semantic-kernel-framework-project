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
- [x] `test_chat_handoff.py` EXTEND (+1) — HANDOFF with non-trivial `messages` → child `meta_data["carried_context"]` populated + tenant-scoped + capped; `loop_end` frame has NO `handoff_context` (server-side only); follow-up `resolve_session_persona` returns a prompt embedding the carried block; 57.68 assertions still pass (done in Stage 1)
- [x] `run_all.py` 10/10 (no codegen drift — `WIRE_SCHEMA` 19); codegen `--check` 0; mypy src 0/325 (Stage 1)

### 2.2 FE pivot action + agent_handoff case (US-4)
- [x] `chatStore.ts` `pivotSession` + shared `applyPivot` helper — preserve `sessions`/`mode`, keep `rawEvents`, reset turns/status/stopReason/errorMessage/totalTurns/approvals/verifications/subagents; set `sessionId = activeSessionId = newSessionId`; set `handoffBanner`
- [x] `handoffBanner: HandoffBanner | null` state (+ `_initial` + Pick<> union); cleared on `loop_start` + `dismissHandoffBanner`
- [x] `agent_handoff` case (`:466`): record rawEvent + `applyPivot(...)`; comment updated (drops DEFERRED); exhaustive `never` switch stays type-safe

### 2.3 FE banner + i18n + render (US-4)
- [x] `HandoffBanner.tsx` (NEW) — reads `handoffBanner` + `dismissHandoffBanner`; `.badge info` + `.btn ghost` primitives + `var(--info)`-derived tint; dismissible; AP-2 honesty docstring + `no-restricted-syntax` escape comment
- [x] `ChatLayout.tsx` renders `<HandoffBanner>` above the conversation
- [x] i18n: chat_v2 has NO keyed i18n system (siblings use inline strings) → local `COPY` map in 繁中 (`已交棒給 {agent}` / `原因` / `關閉`); documented in component docstring

### 2.4 FE tests + sweep (US-5)
- [x] `chatStore.mergeEvent.test.ts` (+8) — `agent_handoff` pivots (turns reset, `sessionId`+`activeSessionId` set, `handoffBanner` set, rawEvent recorded, `sessions` preserved); `loop_start` clears banner; `dismissHandoffBanner`; `pivotSession` direct
- [x] `HandoffBanner.test.tsx` (NEW, 3) — null→nothing, render target/reason, dismiss
- [x] `eventSchema.generated.test.ts` unchanged (no wire change); lint exit 0; Vitest 709 passed (+11); `npm run build` ✓
- [x] **mockup-fidelity (parent re-verify catch)**: FE agent ran lint/build/test but NOT `check:mockup-fidelity` → +2 `oklch(from var(--info) ...)` tints exceeded `HEX_OKLCH_BASELINE` (48→51, incl. 1 comment false-positive). Fixed: reworded the escape comment to drop the `oklch(` literal (count 50) + bumped baseline 48→50 + MHist (precedent 57.30/57.35/57.37/57.38/57.40). check `✓ 50=50` (AD-silent-constraint-delta caught pre-PR)

---

## Day 3 — Full sweep + edge cases

- [x] Full `pytest tests/unit tests/integration` → **2015 passed / 4 skipped / 0 failed** (= 57.68 baseline 1999 + 16 new; integration no regression); tenant-scoping + budget-cap + handler-seed asserted
- [x] Edge: empty parent conversation (no `carried_context` key, 57.68 backward-compat); over-budget (drop-oldest last-20); malformed carried_context (nested fail-open, persona preserved); pivot order vs loop_end (post-stream — integration asserts `loop_end` has no `handoff_context`)
- [x] Parent decisive re-verify: pytest full 2015; `mypy src/` 0/325; `run_all.py` 10/10; codegen `--check` 0; FE check:mockup-fidelity ✓ 50=50; lint exit 0; Vitest 709; build ✓
- [x] Drift catalogued: D-DAY2-1 (mockup-fidelity baseline bump) in progress.md Day 2; plan §3.2/§3.3 refinements (D-DAY0-3/4) in progress.md Day 0 (not silently rewritten)

---

## Day 4 — Design note (8-point gate) + Closeout

### 4.1 Design note extension (US-5)
- [x] `18-handoff-design.md` EXTEND — NEW §8 (slice 2: §8.1 stories / §8.2 C-1/C-2/C-3 decision matrix + persistence reframe / §8.3 6 verified invariants w/ file:line / §8.4 copy-vs-summarize tradeoff / §8.5 rollback / §8.6 verify commands / §8.7 17.md cross-ref) + §5 open-invariant update (agent-side carry + FE pivot ✅; transcript continuity still deferred + why) + header/MHist; 8-point gate ALL ✅; verified-ratio ≥95%
- [x] retrospective.md §Design Note Extract record (8-point self-check)

### 4.2 Closeout
- [x] Full validation (parent re-verified): pytest 2015 / mypy src 0/325 / run_all 10/10 / codegen --check 0 / FE check:mockup-fidelity ✓ 50=50 / lint exit 0 / Vitest 709 / build ✓
- [x] 17.md §4.1 unchanged (design note §8.7 notes `LoopCompleted.handoff_context` is an in-process carrier, not a wire contract — intentionally not registered); `CHANGE-037` created
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7 + Design Note Extract)
- [x] Calibration: `handoff-context-carry-spike` 0.55 (NEW, 1 pt) + `agent_factor mechanical-greenfield-design-decisions` 0.65 (CAVEATED — 7th consecutive no-clean-wall-clock 57.63→69); recorded `calibration-log.md §3`
- [x] Area-A: A-3b slice 2 (agent-side carry + FE pivot) shipped; user-visible transcript continuity (needs message-persistence subsystem) + summarize-carry + target auto-first-turn + multi-hop + real catalog + dedicated columns = carryover (design note §5/§8.4)
- [x] MEMORY.md pointer + `project_phase57_69_handoff_context_carry_pivot.md` subfile + CLAUDE.md lean (Current Sprint row + footer)
- [x] **Final-commit `black --check`** (per `AD-Final-Commit-Black-Check`, 57.68 lesson): black All done (597 files unchanged) + isort clean + flake8 exit 0
- [ ] commit (Day 4 closeout) + push + PR — **user-authorized** (push/PR pending user approval)
