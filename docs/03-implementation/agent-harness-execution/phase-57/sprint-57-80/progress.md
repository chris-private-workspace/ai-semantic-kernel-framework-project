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
