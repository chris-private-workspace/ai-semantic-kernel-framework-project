# Sprint 57.80 — Checklist (chat real_llm orphan-tool-message fix: PromptBuilder tool-call adjacency invariant)

**Plan**: `sprint-57-80-plan.md`
**Branch**: `feature/sprint-57-80-orphan-tool-adjacency` (from `main` `88911c95`)
**Closes**: `AD-Chat-RealLLM-Orphan-Tool-Message`

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (parent grep + code read, main `88911c95`)
- [x] **Prong 1 (path)** — confirm: `prompt_builder/builder.py`, `strategies/lost_in_middle.py` + `naive.py` + `tools_at_end.py` + `_abc.py`, `orchestrator_loop/loop.py`, `_contracts/chat.py`, `api/v1/chat/handler.py`, `adapters/_testing/mock_clients.py`, `tests/.../prompt_builder/test_loop_with_prompt_builder.py`, `tests/unit/agent_harness/prompt_builder/` dir.
- [x] **Prong 2 (content)** — D-DAY0-1..7 in plan §0 (real_llm uses artifact.messages / LostInMiddle split root cause / naive+tools_at_end preserve order / Message tool_calls+tool_call_id linkage + identity-stable / AP-10+AP-4 why-invisible / last_request.messages capture point / config.model_name aligned 57.79).
- [x] **Prong 3 (schema)** — N/A (no DB table / migration / ORM change).
- [x] **go/no-go** — GO; user-locked (AskUserQuestion 2026-06-04): approach B (builder-level adjacency invariant) + real Azure e2e re-verify this sprint. No scope shift (≤20%).

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-80-orphan-tool-adjacency`
- [x] **Decisions locked**: fix B (`_enforce_tool_adjacency` in builder after `strategy.arrange()`, protects all strategies — NOT a strategy rewrite); parent-direct (NOT agent-delegated — assembly correctness + real-LLM collab); real-LLM verify THIS sprint.
- [x] **Day-0 commit** plan + checklist + progress.md Day 0

---

## Day 1 — Tool-call adjacency invariant (US-1/US-2)

### 1.1 `_enforce_tool_adjacency` static method
- [ ] **add `_enforce_tool_adjacency(messages) -> list[Message]`** in `builder.py` (DefaultPromptBuilder)
  - build `owner_by_id` (ToolCall.id → emitting assistant); no-op return when no assistant carries tool_calls
  - bucket `role='tool'` msgs (resolved owner) under `id(owner)`, preserve order, mark held; unresolved-owner tool left in place (no silent drop)
  - rebuild: skip held tools; after each assistant emit its held tools → tool always directly after owning assistant
  - DoD: mypy clean ✅; docstring states the provider hard-constraint + orphan-left-in-place rationale

### 1.2 call site in build()
- [ ] **insert `messages = self._enforce_tool_adjacency(messages)`** immediately after `messages = strategy.arrange(sections)` (`builder.py:269`)
  - DoD: mypy clean; no other build() logic changed; MHist 1-line entry added to builder.py header

### 1.3 read changed code
- [ ] **re-read** builder.py change — confirm no strategy / loop / adapter touched; LLM-neutral (only neutral `Message` contract used); identity-rebuild correct

---

## Day 2 — Tests (US-3)

### 2.1 unit: `_enforce_tool_adjacency` + build()-through-LostInMiddle
- [ ] **NEW `test_builder_tool_adjacency.py`** in `tests/unit/agent_harness/prompt_builder/`
  - (a) tool already after assistant → unchanged; (b) tool before assistant (bug shape) → re-anchored after; (c) 2 assistants × 1 tool scrambled → each tool after own assistant; (d) orphan tool (no owner) → left in place; (e) no tool msgs → unchanged
  - `build()` through default `LostInMiddleStrategy`: state.transient.messages = `[system, user, assistant(tool_calls), tool]` → assert `artifact.messages` tool immediately after assistant (the case that 400s pre-fix)

### 2.2 integration: loop+builder 2-turn tool script (AP-10 closure)
- [ ] **extend `test_loop_with_prompt_builder.py`** — 2-turn MockChatClient (turn1 tool_calls → turn2 END_TURN) + tool executor returning a result + registry exposing the tool + prompt_builder injected
  - after run, assert `chat_client.last_request.messages` (turn-2 assembly) has every `role='tool'` immediately after its owning `assistant(tool_calls)`
  - DoD: test FAILS on pre-fix builder (regression guard confirmed) → PASSES with fix

### 2.3 regression gate
- [ ] **targeted pytest** — `pytest tests/unit/agent_harness/prompt_builder/ tests/integration/agent_harness/prompt_builder/` green; confirm pre-existing builder/strategy tests unchanged (LostInMiddle strategy untouched → its own tests still pass)

---

## Day 3 — real-LLM Azure verification (US-4) — user `.env`

### 3.1 clean restart + startup log (Risk Class E)
- [ ] **clean start backend** — kill stale `--reload` workers on :8000; confirm port sole-owner (no Errno 10048); started fresh
- [ ] **confirm startup log** `pricing loader wired` (FIX-022 wiring fired)

### 3.2 real-LLM chat main-flow (local `.env`, NOT GitHub secrets)
- [ ] **dev-login** → v2_jwt cookie (fresh tenant + clean session — the 57.79 repro condition)
- [ ] **POST /chat real_llm** `{mode: real_llm, message: "echo hello"}` → **HTTP 200, no orphan-tool 400** + SSE contains `loop_end` + real Azure reply
- [ ] **cost_ledger write** — newest rows written (row-count Δ≥2); evidence captured

### 3.3 evidence
- [ ] **record** SSE outcome + cost row evidence + the exact `response.model` in progress.md Day 3

---

## Day 4 — Sweep + Closeout

### 4.1 Full sweep
- [ ] **Backend gates** — `mypy src/` 0 + `pytest` (new + regression, expect +~8) + `python scripts/lint/run_all.py` 10/10 (check_llm_sdk_leak green; check_rls_policies unchanged — no schema)
- [ ] **No frontend** — 0 frontend changes (backend-only sprint)
- [ ] **Read all changed code** — builder fix LLM-neutral + identity-rebuild correct; tests assert the structural invariant (not mock-reliant)

### 4.2 Closeout docs
- [ ] **CHANGE-048** in `claudedocs/4-changes/feature-changes/`
- [ ] **progress.md** Day 0-4 (incl. Day 3 real-LLM evidence) + **retrospective.md** Q1-Q7
- [ ] **Checklist** all `[x]` (note any 🚧 carryover with reason)
- [ ] **Calibration** record (medium-backend 0.80; agent_factor 1.0 parent-direct; ratio)
- [ ] **AD status**: `AD-Chat-RealLLM-Orphan-Tool-Message` CLOSED; next-phase-candidates.md updated
- [ ] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [ ] **Design note?** — NO (feature-continuation / bug fix; no new contract / no 17.md change)

### 4.3 Ship
- [ ] **Commit mapping** Day-0 / fix+tests / closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
