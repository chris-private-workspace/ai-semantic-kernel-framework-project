# Sprint 57.80 Progress — chat real_llm orphan-tool-message fix

**Branch**: `feature/sprint-57-80-orphan-tool-adjacency` (from `main` `88911c95`)
**Closes**: `AD-Chat-RealLLM-Orphan-Tool-Message`

---

## Day 0 — 2026-06-04 — Plan-vs-Repo Verify + Branch + Decisions

### Accomplishments
- Root-cause investigation of the Sprint 57.79 carryover (real_llm chat 400 `messages[3] role 'tool' must follow tool_calls`).
- AskUserQuestion (2026-06-04): fix approach **B** (builder-level adjacency invariant) + real Azure e2e re-verify this sprint.
- Plan + checklist drafted (mirror 57.79 9-section / Day 0-4 format).
- Branch created.

### Day-0 verify (Prong 1 path + Prong 2 content; Prong 3 N/A — no schema change)
- **Prong 1 (path)** ✅ — `prompt_builder/builder.py`, all 4 strategy files + `_abc.py`, `orchestrator_loop/loop.py`, `_contracts/chat.py`, `api/v1/chat/handler.py`, `adapters/_testing/mock_clients.py`, `test_loop_with_prompt_builder.py`, `tests/unit/agent_harness/prompt_builder/` dir all confirmed present.
- **Prong 2 (content)** ✅ — D-DAY0-1..7 (plan §0):
  - **D-DAY0-2 (ROOT CAUSE)**: `LostInMiddleStrategy.arrange()` (`lost_in_middle.py:64-76`) splits conversation into `recent_assistants` (appended at tail) vs `mid_history` (incl. `role='tool'` results, appended before). For `[system, user, assistant(tool_calls), tool]` → arranged `[new_system, echo, old_system, tool, assistant(tool_calls), user]` — tool (idx3) BEFORE its assistant (idx4). `messages[3]=tool` exactly matches the 400.
  - real_llm uses `artifact.messages` (`loop.py:1052`, prompt_builder injected via `handler.py:258`); echo_demo uses loop's correct-order `messages` (`loop.py:982`, no builder) → bug is real_llm-only.
  - `naive` + `tools_at_end` `result.extend(sections.conversation)` in order → no orphan; bug specific to LostInMiddle (the chat default).
  - `Message` (`chat.py:76-95`): `tool_calls: list[ToolCall]|None` + `tool_call_id: str|None`; `ToolCall.id: str` → adjacency enforceable by id match; strategies rearrange same Message refs (no copy) → object identity stable.
  - AP-10 + AP-4: existing loop+builder tests only single-turn-no-tool + MockChatClient doesn't validate adjacency → bug invisible until real Azure (57.79 Day-3).
  - `MockChatClient.last_request.messages` retains the turn-2 assembly → regression test capture point, no infra change.
  - config.model_name aligned (57.79 `.env` `AZURE_OPENAI_MODEL_NAME=gpt-5.2`; gpt-5.x token-param + pricing normalize live #245).
- **Prong 3 (schema)** N/A — no DB table / migration / ORM change.

### Drift findings
- **D1 (no drift — confirms surgical scope)**: fix is a post-`arrange()` normalization in `build()`; no strategy / loop / adapter change. Approach B (builder single-enforcement) confirmed feasible against real code.
- **D2 (test capture point confirmed)**: `MockChatClient` has `last_request` (not `last_call_messages`), but `last_request.messages` carries the assembled list → integration assertion needs no test-infra addition.
- No scope shift (≤20%). GO for Day 1.

### Decisions locked
- Fix **B**: `_enforce_tool_adjacency` static method in `DefaultPromptBuilder`, called right after `strategy.arrange()`. Protects ALL strategies (AP-8 single enforcement); LostInMiddle untouched.
- Approach A (fix LostInMiddle only) rejected — doesn't make adjacency a guaranteed invariant; C (also stop user re-anchor) rejected — user-after-tool is valid, out of scope.
- **parent-direct** (NOT agent-delegated — assembly correctness + real-LLM verify is parent/user collab). agent_factor 1.0.
- real-LLM Azure verify THIS sprint (user `.env` live key).

### Blockers / dependencies
- **D1 (live Azure `.env`)**: Day-3 verification needs user env. Confirmed available (`AZURE_OPENAI_MODEL_NAME=gpt-5.2` set 57.79).

### Remaining for Day 1+
- Day 1: `_enforce_tool_adjacency` + call site in build().
- Day 2: unit tests (a)-(e) + build()-through-LostInMiddle + integration 2-turn tool script.
- Day 3: real-LLM Azure verify (clean restart + POST /chat real_llm no-400 + loop_end + cost_ledger write).
- Day 4: sweep + closeout.

### Notes
- Bottom-up est ~5.5 hr → calibrated ~4.4 hr (medium-backend 0.80, parent-direct).

---

## Day 1-2 — 2026-06-04 — Fix + tests

### Accomplishments
- **Fix (US-1/US-2)**: `DefaultPromptBuilder._enforce_tool_adjacency` static method + call site in `build()` immediately after `strategy.arrange()`. Re-anchors every `role='tool'` after its owning `assistant(tool_calls)` (id match), preserves other order, leaves orphan tools in place, no-op when no tool turn. Builder-level single enforcement (AP-8) — protects all strategies; LostInMiddleStrategy untouched.
- **Tests (US-3)**: NEW `test_builder_tool_adjacency.py` (5 `_enforce` cases (a)-(e) + build()-through-LostInMiddle) + extended `test_loop_with_prompt_builder.py` with a 2-turn tool-script integration assertion on `chat_client.last_request.messages` (AP-10 closure).

### Verification
- `pytest tests/unit/agent_harness/prompt_builder/ tests/integration/agent_harness/prompt_builder/` → 69 passed.
- `mypy src/agent_harness/prompt_builder/builder.py` → clean.
- **Regression guard CONFIRMED**: temporarily disabled the `_enforce_tool_adjacency` call → `test_build_through_lost_in_middle_keeps_tool_after_assistant` FAILED `assistant@4, tool@3` (exactly the real Azure `messages[3] role 'tool'` 400 shape) → restored → all green.

### Commit
- `29879147` fix(prompt_builder, sprint-57-80): tool-call adjacency invariant.

---

## Day 3 — 2026-06-04 — real-LLM Azure verification

### Accomplishments
- **Clean restart (Risk Class E)**: :8000 was free (no stale process); started fresh single no-reload uvicorn (PID 37220). Startup log `pricing loader wired (...llm_pricing.yml)` + `startup complete` confirmed (FIX-022 fired).
- **real-LLM chat (fresh tenant `sk5780`, clean session — 57.79 repro condition)**: `POST /chat {mode: real_llm, message: "echo hello"}`.

### Result — orphan-tool 400 FIXED ✅
- `chat status: 200` (not 400/503).
- **`"must follow tool_calls" in stream: False`** — the orphan-tool 400 is GONE.
- SSE ran the full tool turn: `tool_call_request` (echo_tool) → `tool_call_result` (result="hello") → ... → `loop_end`. `models seen: ['gpt-5.2']` (real Azure deployment).
- `cost_ledger` delta=8 (incl. `azure_openai_gpt-5.2-2025-12-11_output` 11 tokens + `echo_tool` rows). Cost rows written.
- ⇒ **Acceptance criteria met**: HTTP 200 (no orphan-tool 400) + SSE `loop_end` + cost_ledger rows written. `AD-Chat-RealLLM-Orphan-Tool-Message` (the 400) is closed by the structural fix.

### NEW finding (surfaced once the 400 no longer short-circuits the loop)
- `loop_end` shows **`"stop_reason":"max_turns","total_turns":8`** — the model re-called `echo_tool` every turn and never emitted END_TURN.
- **Root cause (confirmed by code, not Azure)**: `LostInMiddleStrategy.arrange()` always appends `sections.user_message` at the tail (`lost_in_middle.py:79-80`); `_enforce_tool_adjacency` does not move it ⇒ on a tool turn the assembled prompt ALWAYS ends with the user message (after the tool result). The model sees "echo hello" as the final instruction each turn → re-calls echo_tool → never converges. This is exactly the **user-message re-anchoring (Approach C)** that Sprint plan §9 deferred as "valid, not a 400, out of scope."
- **Honest reassessment**: the plan under-sold C as cosmetic. The real-LLM run shows C is functionally required for tool-calling real_llm chat to CONVERGE (END_TURN), not just for tidiness. B alone removes the 400 but leaves tool-chat looping to max_turns. (Severity nuance: the DEMO_SYSTEM_PROMPT is a worst case — "echo when asked to echo" + re-anchored "echo hello" → always echo; a real conversational persona may converge despite re-anchoring, but the re-anchor is still wrong for tool turns.)
- **Decision pending (user)**: extend this sprint with a targeted C fix (don't re-anchor the user message when the conversation ends with a pending tool result → prompt ends with the tool result → model produces the final answer) + re-verify Azure converges; OR close now (AD/acceptance met) + carryover the convergence issue as a focused Approach-C AD.

### Evidence (B-only run, before C)
- response.model = `gpt-5.2-2025-12-11`; SSE `loop_end stop_reason=max_turns total_turns=8`; cost_ledger delta=8.

### User decision (AskUserQuestion, 2026-06-04)
- **Extend this sprint with a targeted C fix** (don't re-anchor the user message when the conversation ends with a pending tool result → prompt ends with the tool result → model converges).

---

## Day 3.5 — 2026-06-04 — targeted C fix + real-LLM re-verify

### Accomplishments
- **Targeted C fix** in `build()`: detect a pending tool turn (`state.transient.messages[-1].role == "tool"`) → use the full conversation in chronological order + `user_message=None` (no tail re-anchor / no top echo) → the prompt ends with the tool result. A normal (non-tool / fresh) turn keeps the lost-in-middle echo + tail re-anchor unchanged. Builder-level (consistent with B's single-enforcement philosophy); LLM-neutral; all strategies benefit.
- **Tests**: +2 in `test_builder_tool_adjacency.py` — pending tool turn ends with `tool` (not re-anchored user, user still in history); fresh non-tool turn still ends with `user` (no regression). 71 passed (was 69).

### Re-verify — CONVERGED ✅ (clean restart PID killed → fresh PID, `pricing loader wired`)
- Fresh tenant `sk5780b`, clean session. `POST /chat {mode: real_llm, message: "echo hello"}`:
  - `chat status: 200`; `"must follow tool_calls": False` (400 still gone).
  - **`loop_end stop_reason: "end_turn"`** (was `max_turns`) — CONVERGED. Final `llm_response content="hello", tool_calls=[]`.
  - Final `prompt_built messages_count: 5` = `[new_system, old_system, user, assistant(tool_calls), tool]` — the C-fix arrangement (ends with the tool result, user in chronological position, NOT re-anchored). `models seen: ['gpt-5.2']`. cost_ledger delta=3 (gpt-5.2 input/output + echo_tool).
- ⇒ **B (orphan-tool 400 removed) + C (tool-chat converges to END_TURN) both verified end-to-end against real Azure.**

### Evidence
- Before C: `stop_reason=max_turns total_turns=8`. After C: `stop_reason=end_turn`, final content `"hello"`, last prompt 5 messages ending with tool.
- Backend left running (fresh PID, B+C code) pending Day-4 closeout cleanup.
