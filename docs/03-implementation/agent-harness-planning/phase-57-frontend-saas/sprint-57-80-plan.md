# Sprint 57.80 Plan — chat real_llm orphan-tool-message fix (PromptBuilder tool-call adjacency invariant) (closes AD-Chat-RealLLM-Orphan-Tool-Message)

**Branch**: `feature/sprint-57-80-orphan-tool-adjacency` (from `main` `88911c95`)
**Closes**: `AD-Chat-RealLLM-Orphan-Tool-Message` — the pre-existing real_llm chat 400 surfaced by the Sprint 57.79 Day-3 real-LLM run (it blocked the chat-router e2e leg; 57.79 bypassed it via the direct cost_ledger record path).
**Scope**: Backend (Cat 5 PromptBuilder tool-call adjacency invariant) + real-LLM Azure verification (user `.env` has live key). NOT frontend; NOT a strategy rewrite.

---

## 0. Background

Sprint 57.79 Day-3 real-LLM run found that `POST /api/v1/chat/` in `mode=real_llm` returns a 400 from Azure: **`messages[3] role 'tool' must follow tool_calls`** (orphan tool message). A fresh tenant + clean session reproduces it (`messages_count:4`), proving it is NOT session-history pollution — it is a per-turn prompt-assembly defect on the real_llm path. 57.79 logged it as carryover `AD-Chat-RealLLM-Orphan-Tool-Message` and bypassed it (the billing fix was verified at the DB level via the direct `CostLedgerService.record_llm_call` path instead of the full chat router). This sprint fixes the root cause and re-verifies the chat main-flow against real Azure.

**User decision (AskUserQuestion, 2026-06-04)**: fix approach **B** (builder-level tool-call adjacency invariant) AND run real Azure e2e re-verification of the chat main flow this sprint.

### Day-0 ground-truth (parent grep + code read, main `88911c95`)
- **D-DAY0-1 (real_llm uses artifact.messages, echo_demo does not)**: the loop sends `chat_messages = list(messages)` when no prompt_builder (`loop.py:982`), but `chat_messages = list(artifact.messages)` (`loop.py:1052`) when a prompt_builder is injected. `build_real_llm_handler` injects `DefaultPromptBuilder` (`handler.py:258`, keystone Sprint 57.64); `build_echo_demo_handler` does NOT. ⇒ the bug is real_llm-only (echo_demo bypasses the builder and keeps the loop's correct chronological order) — matches the carryover's "real_llm mode" note.
- **D-DAY0-2 (root cause — LostInMiddleStrategy splits assistant from its tool result)**: `DefaultPromptBuilder.build()` (`builder.py:269`) calls `strategy.arrange(sections)`; the default strategy is `LostInMiddleStrategy` (`builder.py:200`). Its `arrange()` (`lost_in_middle.py:64-76`) splits the conversation into `recent_assistants` (last N assistant messages, appended at the **tail**) vs `mid_history` (everything else, incl. the `role='tool'` results, appended **before** the recent assistants). For a tool-calling turn `[system, user, assistant(tool_calls), tool]` this yields `[new_system, echo, old_system, tool, assistant(tool_calls), user]` — the `tool` (idx 3) precedes its `assistant` (idx 4), violating the OpenAI/Azure hard constraint that a `role='tool'` message MUST immediately follow the `assistant` bearing the matching `tool_calls`. `messages[3]=tool` exactly matches the reported 400.
- **D-DAY0-3 (other strategies preserve order)**: `NaiveStrategy` (`naive.py:32`) + `ToolsAtEndStrategy` (`tools_at_end.py:37`) both `result.extend(sections.conversation)` in original order ⇒ they do NOT orphan tool results. The bug is specific to `LostInMiddleStrategy` (the default on the chat path). (The user-message re-anchor-to-tail is shared by all three, but `user` after `tool` is valid for OpenAI — not a 400; out of scope per approach B.)
- **D-DAY0-4 (Message contract carries the linkage)**: `Message` (`_contracts/chat.py:76-95`) has `tool_calls: list[ToolCall] | None` (on assistant) + `tool_call_id: str | None` (on tool); `ToolCall.id: str` (`chat.py:67-72`). The loop builds `Message(role="assistant", tool_calls=parsed.tool_calls)` (`loop.py:1329-1335`) and `Message(role="tool", tool_call_id=tc.id, ...)` (`loop.py:1373-1379`). ⇒ adjacency can be enforced by matching `tool_msg.tool_call_id` → `assistant.tool_calls[*].id`. Strategies rearrange the same Message object references (no copy), so object identity is stable for the rebuild.
- **D-DAY0-5 (why invisible until real Azure — AP-10 + AP-4)**: the existing loop+builder integration tests (`test_loop_with_prompt_builder.py`) only run **single-turn, no-tool** scripts (`_final_response()` returns END_TURN immediately) AND use `MockChatClient`, which returns scripted responses **without validating message adjacency** (`mock_clients.py:93-109`). So the malformed turn-2 ordering was never assembled in a test, and even if it were, the mock would not reject it. Only the real Azure adapter enforces the constraint. Classic AP-10 (mock vs real divergence) + AP-4 (no negative coverage of the tool-turn assembly).
- **D-DAY0-6 (test capture point exists)**: `MockChatClient.last_request: ChatRequest` (`mock_clients.py:88,101`) retains the most recent call; `ChatRequest.messages` carries the assembled list. After a 2-turn (tool then final) run, `last_request.messages` = the turn-2 assembly (the one that 400s today) ⇒ a regression test can assert adjacency on it with NO test-infra change.
- **D-DAY0-7 (config.model_name already aligned)**: Sprint 57.79 added `.env` `AZURE_OPENAI_MODEL_NAME=gpt-5.2` (deployment returns `gpt-5.2-2025-12-11`); the gpt-5.x `max_completion_tokens` adapter param + pricing normalize are already live (#245). ⇒ Day-3 real-LLM verify of the chat router should now exercise the full corrected path (no 400 from this fix, no 400 from token cap, cost_ledger priced).

---

## 1. Sprint Goal

Make tool-call adjacency a hard invariant of `DefaultPromptBuilder.build()` so that no PositionStrategy (current or future) can emit a `role='tool'` message that does not immediately follow its owning `assistant(tool_calls)` — closing the real_llm chat 400 — then re-verify the chat main flow against real Azure (no 400 + `loop_end` + cost_ledger priced).

---

## 2. User Stories

- **US-1** — 作為平台使用者，我希望 `POST /chat` 在 `real_llm` 模式下的多輪工具呼叫不再回 400，以便 real_llm 聊天主流量真正可用（不再被 orphan-tool message 擋住）。
- **US-2** — 作為 Cat 5 維護者，我希望 tool-call 相鄰性是 PromptBuilder 的不變式（單一強制點），以便任何 PositionStrategy（含未來新增）都不會破壞 provider 的硬約束。
- **US-3** — 作為 QA，我希望 unit + 整合測試覆蓋「tool-turn 經 builder 組裝後 tool 緊跟其 assistant」，以便回歸保護（關閉 AP-10/AP-4 測試缺口：既有測試從不跑 tool-turn 經 builder，且 mock 不驗 adjacency）。
- **US-4** — 作為 release owner，我希望實際 real-LLM Azure 驗證 chat router `real_llm` 端到端（無 400 + SSE `loop_end` + cost_ledger 寫入），以便確認 orphan-tool 修好後 chat 主流量真的通（非僅 mock）。

---

## 3. Technical Specifications

### 3.0 Architecture
Single backend fix in Cat 5 (`prompt_builder/builder.py`) + a real-LLM verification leg. The fix is a post-`arrange()` normalization pass inside `build()` — a single enforcement point (AP-8 philosophy) that protects ALL strategies. It does NOT modify any PositionStrategy (LostInMiddle stays a pure "lost-in-middle" arranger; the builder corrects the tool-adjacency it cannot know about). LLM-neutral: operates only on the neutral `Message` contract (no provider import). Does NOT touch `loop.py`, the adapters layer, or the strategies.

### 3.1 Tool-call adjacency invariant (US-1/US-2) — `prompt_builder/builder.py`
- New private static method `_enforce_tool_adjacency(messages: list[Message]) -> list[Message]`:
  - Build `tool_calls_by_id: dict[str, Message]` mapping each `ToolCall.id` → the assistant message that emitted it (scan `m.role == "assistant" and m.tool_calls`).
  - If no assistant carries tool_calls → return `messages` unchanged (no tool turn; zero overhead for plain chat).
  - Bucket every `role='tool'` message (with a non-None `tool_call_id` that resolves to an owner) under `id(owner_assistant)`, preserving their relative order; mark them "held".
  - A tool message whose `tool_call_id` resolves to no owner (defensive — should not happen on the loop path; e.g. an assistant dropped by future compaction) is left in place (NOT dropped — never silently lose a message).
  - Rebuild: iterate the arranged list; skip held tool messages; after appending each assistant, immediately append its held tool messages. ⇒ every tool ends up directly after its owning assistant, all other ordering preserved.
  ```python
  @staticmethod
  def _enforce_tool_adjacency(messages: list[Message]) -> list[Message]:
      owner_by_id: dict[str, Message] = {}
      for m in messages:
          if m.role == "assistant" and m.tool_calls:
              for tc in m.tool_calls:
                  owner_by_id[tc.id] = m
      if not owner_by_id:
          return messages
      held_tools: dict[int, list[Message]] = {}
      held_ids: set[int] = set()
      for m in messages:
          if m.role == "tool" and m.tool_call_id is not None:
              owner = owner_by_id.get(m.tool_call_id)
              if owner is not None:
                  held_tools.setdefault(id(owner), []).append(m)
                  held_ids.add(id(m))
      if not held_ids:
          return messages
      result: list[Message] = []
      for m in messages:
          if id(m) in held_ids:
              continue
          result.append(m)
          if m.role == "assistant" and id(m) in held_tools:
              result.extend(held_tools[id(m)])
      return result
  ```
- Call site: in `build()` immediately after `messages = strategy.arrange(sections)` (`builder.py:269`):
  ```python
  messages = strategy.arrange(sections)
  messages = self._enforce_tool_adjacency(messages)
  ```
- **Design rationale**: builder-level (single enforcement) chosen over fixing LostInMiddleStrategy in isolation (Approach A) — tool-call adjacency is a hard provider constraint that NO strategy should be able to violate; enforcing once centrally protects current + future strategies and matches AP-8 (centralized prompt assembly). Approach C (also stop the user-message re-anchor for tool turns) rejected for scope: `user` after `tool` is valid for OpenAI (not a 400) and the re-anchor is the deliberate lost-in-middle design — out of scope for an orphan-tool 400 fix.

### 3.2 Tests (US-3) — NEW `test_builder_tool_adjacency.py` + extend integration test
- NEW `backend/tests/unit/agent_harness/prompt_builder/test_builder_tool_adjacency.py`:
  - `_enforce_tool_adjacency` direct unit cases: (a) tool already after its assistant → unchanged; (b) tool reordered before its assistant (the bug shape) → re-anchored after; (c) two assistants each with one tool, interleaved/scrambled → each tool ends after its own assistant; (d) orphan tool (tool_call_id with no owner) → left in place; (e) no tool messages → unchanged (identity / same list).
  - `build()` end-to-end through `LostInMiddleStrategy`: feed a `LoopState` whose `transient.messages` = `[system, user, assistant(tool_calls), tool]`; assert the returned `artifact.messages` has the `tool` immediately after the `assistant(tool_calls)` (this is the case that 400s today before the fix).
- EXTEND `backend/tests/integration/agent_harness/prompt_builder/test_loop_with_prompt_builder.py`:
  - NEW test: a 2-turn `MockChatClient` script — turn 1 returns a `tool_calls` response (echo-style), turn 2 returns END_TURN — run the loop with `prompt_builder` injected + a tool executor that returns a result + a registry exposing the tool. After the run, assert `chat_client.last_request.messages` (the turn-2 assembly) has every `role='tool'` immediately after its owning `assistant(tool_calls)`. This is the AP-10 closure: it exercises the FULL Cat1→Cat5 chain on a tool turn and asserts the structural invariant (not relying on the mock to reject).

### 3.3 real-LLM verification (US-4) — manual, user `.env`
- Clean restart backend (Risk Class E — kill stale `--reload` workers on :8000 first; confirm startup log `pricing loader wired`).
- `POST /api/v1/auth/dev-login` → v2_jwt cookie → `POST /api/v1/chat/` `{mode: real_llm, message: "echo hello"}` (the DEMO_SYSTEM_PROMPT instructs `echo_tool` use → triggers a tool turn → the previously-400'ing turn-2 assembly).
- Assert: HTTP 200 (no 400), SSE contains `loop_end`, real Azure reply, `cost_ledger` newest rows written (row-count Δ≥2). Fresh tenant + clean session (the 57.79 repro condition).
- Record the SSE outcome + cost row evidence in progress.md Day 3.

### 3.4 Lint / validation
`mypy src/` + `pytest` (new + regression) + `python scripts/lint/run_all.py` (10/10 — no schema change, no LLM-SDK leak: the fix uses only the neutral `Message` contract). NO frontend / migration / wire-schema / ORM change.

---

## 4. File Change List

**NEW (1)**
- `backend/tests/unit/agent_harness/prompt_builder/test_builder_tool_adjacency.py` (adjacency unit + build()-through-LostInMiddle case)

**EDIT (2)**
- `backend/src/agent_harness/prompt_builder/builder.py` (`_enforce_tool_adjacency` static method + 1 call site in `build()` after `strategy.arrange()`)
- `backend/tests/integration/agent_harness/prompt_builder/test_loop_with_prompt_builder.py` (NEW 2-turn tool-script test asserting `last_request.messages` adjacency)

**NO frontend / migration / wire-schema / ORM / strategy / loop / adapter change.**

---

## 5. Acceptance Criteria

- `_enforce_tool_adjacency` re-anchors every `role='tool'` message immediately after its owning `assistant(tool_calls)`, preserves all other order, leaves orphan tools in place, and is a no-op when no tool turn exists — verified by unit tests (a)-(e).
- `DefaultPromptBuilder.build()` through `LostInMiddleStrategy` emits a valid sequence (tool after assistant) for a `[system, user, assistant(tool_calls), tool]` conversation.
- The loop+builder integration test (2-turn tool script) asserts `chat_client.last_request.messages` has tool-after-assistant adjacency; the test would FAIL on the pre-fix builder (regression guard).
- real-LLM chat (`mode=real_llm`, fresh tenant): HTTP 200 (no orphan-tool 400), SSE `loop_end`, cost_ledger rows written.
- Gates: backend mypy 0 + pytest (new + regression) green + run_all 10/10. No frontend.

---

## 6. Deliverables

- [ ] `_enforce_tool_adjacency` static method + call site in `build()` after `strategy.arrange()`
- [ ] Unit tests: `_enforce_tool_adjacency` (a)-(e) + `build()`-through-LostInMiddle tool-turn case
- [ ] Integration test: loop+builder 2-turn tool script asserting `last_request.messages` adjacency (AP-10 closure)
- [ ] real-LLM Azure verification (clean restart + `pricing loader wired` + `POST /chat` real_llm no-400 + SSE loop_end + cost_ledger write) — evidence in progress.md Day 3
- [ ] All gates green; closeout (CHANGE-048 + progress + retro + MEMORY + CLAUDE lean; AD CLOSED → chat real_llm main-flow unblocked)

---

## 7. Workload Calibration

Scope class `medium-backend` (0.80 — one focused Cat 5 fix + tests + real-LLM verification leg; same shape as 57.79). **Agent-delegated: no** (parent-direct — message-assembly correctness needs care + real-LLM verification is a parent/user collaboration). `agent_factor` = 1.0 → 3-segment form.

Bottom-up est ~5.5 hr (fix ~1.5 + unit tests ~1.5 + integration test ~0.5 + real-LLM verify ~1 + closeout ~1) → class-calibrated commit ~4.4 hr (mult 0.80).

---

## 8. Dependencies & Risks

- **Dependency D1 (live Azure `.env`)**: real-LLM verification (§3.3) needs the user's local `.env` with a working `AZURE_OPENAI_*` key + `AZURE_OPENAI_MODEL_NAME=gpt-5.2` (added Sprint 57.79). User confirmed available.
- **Risk Class E (stale `--reload` masks the fix)**: real-LLM verify must clean-restart backend (kill stale reloader+worker on :8000, confirm `pricing loader wired` startup log) — a stale process running pre-fix code gives a false negative. Per `sprint-workflow.md §Common Risk Classes E`.
- **Risk: object-identity rebuild assumption**: `_enforce_tool_adjacency` matches owners by `id(message)`. This holds because strategies rearrange the same Message references (no copy) — verified D-DAY0-4. If a future strategy deep-copies messages, identity breaks; mitigation: the unit test feeds the real `LostInMiddleStrategy` output (catches a copy regression), and the fallback (tool with unresolved owner left in place) degrades safely rather than crashing.
- **Risk: orphan tool left in place could still 400**: if a tool's owning assistant is genuinely absent (not the loop's normal flow), leaving it in place keeps the 400. Accepted: the loop always emits the assistant before its tool (D-DAY0-4), so this cannot occur on the main path; dropping a message silently would be worse (AP — no silent data loss). Documented in the method docstring.
- **Risk: real-LLM verify hits a DIFFERENT pre-existing issue**: if the chat router 400 had a second cause beyond ordering, the real run would still fail. Mitigation: the unit + integration tests prove the assembly is now valid independently; if real Azure still 400s for another reason, that is a new finding (logged separately) and the structural fix still stands.
- **Dependency**: PromptBuilder keystone wiring (Sprint 57.64) + real_llm handler + cost_ledger record path (56.3) all live (#245). No new infra.

---

## 9. Out of Scope (this sprint; carryover)

- **PositionStrategy user-message re-anchor for tool turns** (Approach C) — `user` after `tool` is valid (not a 400); the re-anchor is the deliberate lost-in-middle design. Not changed this sprint.
- **B-7 ErrorBudget Redis wiring** / **B-8 Verification default-enable** / **C-15 DevOps billing** — the billing/verification bundle; separate sprints.
- **GitHub Secrets + scheduled e2e gate** (`AD-CI-6`) — real-LLM CI stays manual workflow_dispatch + local `.env`; production-launch concern.
- **Conversation compaction interaction with tool turns** — Cat 4 compaction dropping an assistant while keeping its tool is a separate (currently non-occurring) concern; the adjacency invariant degrades safely if it ever happens, but compaction-aware tool grouping is not designed here.

---

## 10. In-Sprint Scope Extension — targeted C (added 2026-06-04, supersedes §9 "Approach C out of scope" for the pending-tool-turn slice)

**Trigger**: Day-3 real-LLM run found that B alone (the adjacency invariant) removed the 400 but the chat then looped to `max_turns` (`stop_reason=max_turns total_turns=8`) — the model re-called echo_tool every turn and never converged. **Root cause (confirmed by code)**: every PositionStrategy appends `sections.user_message` at the tail (`lost_in_middle.py:79-80` etc.) and `_enforce_tool_adjacency` does not move it, so on a tool turn the assembled prompt ALWAYS ends with the user message (after the tool result). The model treats the re-anchored "echo hello" as a fresh request each turn → re-calls the tool. §9's framing of C as "valid, not a 400, cosmetic" was an under-assessment: the re-anchor is functionally required for tool-calling chat to CONVERGE.

**User decision (AskUserQuestion, 2026-06-04)**: extend this sprint with a targeted C fix.

**Targeted C fix** (`builder.py` `build()`, builder-level — same single-enforcement philosophy as B): detect a PENDING tool turn (`state.transient.messages[-1].role == "tool"`) → pass the full conversation in chronological order + `user_message=None` (no tail re-anchor, no top echo) so the prompt ends with the tool result and the model produces its final answer. A normal (non-tool / fresh) turn is unchanged (keeps the lost-in-middle echo + tail re-anchor). No strategy / loop / adapter change.

**Verification**: re-ran real Azure (fresh tenant) → `loop_end stop_reason=end_turn` (was `max_turns`), final `llm_response content="hello" tool_calls=[]`, last `prompt_built messages_count=5` = `[new_system, old_system, user, assistant(tool_calls), tool]` (ends with tool). Tests +2 (pending-tool-turn ends with tool; fresh turn still ends with user).

**File change delta vs §4**: still only `builder.py` (EDIT — the C conditional added alongside the B method) + `test_builder_tool_adjacency.py` (EDIT — +2 C tests). No new files beyond §4.

**Remaining out of scope**: B-7 / B-8 / C-15 billing bundle; GitHub Secrets e2e gate; compaction×tool-turn interaction.
