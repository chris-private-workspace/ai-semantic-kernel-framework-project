# Sprint 57.80 Retrospective — chat real_llm orphan-tool-message fix

**Sprint**: 57.80
**Closed**: 2026-06-04
**Branch**: `feature/sprint-57-80-orphan-tool-adjacency`
**Closes**: `AD-Chat-RealLLM-Orphan-Tool-Message`

---

## Q1. Goal achieved?

✅ Yes, and extended. The orphan-tool 400 is fixed AND the tool-chat now converges:
- **B (planned)**: `DefaultPromptBuilder._enforce_tool_adjacency` after `strategy.arrange()` — every `role='tool'` message re-anchored after its owning `assistant(tool_calls)`. Closes the real_llm chat 400.
- **C (in-sprint extension, user-approved)**: pending-tool-turn user re-anchor suppression — when the conversation ends with a tool result, don't re-append the user message at the tail; the prompt ends with the tool result so the model produces its final answer.
- Real Azure (fresh tenant, gpt-5.2): HTTP 200, no `must follow tool_calls`, `loop_end stop_reason=end_turn` (was `max_turns`), cost_ledger written.
- Gates: mypy src/ 0 (331) / pytest 2130 (+9) / run_all 10/10.

## Q2. Estimate accuracy

- Plan: bottom-up ~5.5 hr → class-calibrated commit ~4.4 hr (`medium-backend` 0.80, `agent_factor` 1.0 parent-direct).
- Actual: ~3.5-4 hr. The B fix + tests was small/fast (~1.5 hr). The unplanned C extension (root-cause was already known by code, so the fix itself was ~45 min + 2 tests) + the two real-Azure runs + a clean restart added ~1.5 hr. Closeout ~1 hr.
- Ratio ~0.85. `medium-backend` 0.80 held for a parent-direct prompt-assembly fix even with the in-sprint C extension. **NOT agent-delegated** → the 16-consecutive-agent-delegated wall-clock caveat does not apply.

## Q3. What went well

- **Day-0 root cause by code read, no Azure needed**: traced the LostInMiddle `recent_assistants` split → `mid_history` tool orphan purely from `lost_in_middle.py` + the loop's `artifact.messages` path. The 400 shape (`messages[3]=tool`) was predicted before any real run.
- **Regression guard proven, not asserted**: temporarily disabled the invariant → the build()-through-LostInMiddle test FAILED `assistant@4, tool@3` (the exact real Azure 400 shape) → restored. The test demonstrably catches the bug.
- **Real-LLM caught what no test could**: the C non-convergence (`max_turns` loop) is a behavioral property only observable on the real path — every mock script predetermines `stop_reason`. Running real Azure (per the user's Q2 decision) surfaced it.
- **Honest reassessment / professional pushback**: the plan framed C as "cosmetic, valid-not-a-400, out of scope". The real-LLM run proved C is functionally required for convergence; I corrected my own framing and surfaced it rather than shipping a 400-fixed-but-unusable chat.

## Q4. Lessons

- **AP-10 is real for prompt assembly**: `MockChatClient` returns scripted responses without validating message adjacency, so a structurally-invalid prompt (orphan tool) passed every loop+builder test until real Azure. Prompt-assembly tests must assert the structural invariant (adjacency / ordering) directly, not rely on the mock to reject — this sprint's new tests do exactly that. (Candidate rule fold-in: "Cat 5 / message-assembly tests assert provider structural constraints, not mock acceptance.")
- **"Valid but odd" ≠ "harmless" when it touches LLM behavior**: the user-message re-anchor was waved off as cosmetic; it actually broke tool-turn convergence. When a structural oddity feeds the model, verify with real-LLM before declaring it out of scope.
- **Convergence (`stop_reason`) is only observable on the real path**: no-400 is necessary but not sufficient; a real-LLM DoD for agent-loop prompt changes should check `stop_reason=end_turn` (converges), not just HTTP 200.

## Q5. Improvements next sprint

- When a sprint touches prompt assembly on the agent-loop path, the real-LLM DoD should include a **convergence** check (`stop_reason=end_turn` on a tool turn), not only "no 400 / loop_end present". This sprint's first real-LLM run passed "200 + loop_end" while still looping to max_turns — the convergence signal is the one that mattered.

## Q6. Carryover

- None blocking — the carryover that opened this sprint (`AD-Chat-RealLLM-Orphan-Tool-Message`) is CLOSED, and the 57.79 chat-router e2e leg it blocked is now verified (200 + end_turn + cost rows).
- B-7 (ErrorBudget Redis) / B-8 (Verification default-enable) / C-15 — billing/verification bundle, unrelated, separate sprints.
- Compaction × tool-turn interaction (Cat 4 dropping an assistant while keeping its tool) — non-occurring today; the adjacency invariant degrades safely (orphan left in place); not designed here.

## Q7. Risks

- Low. Backend-only, builder-level (Cat 5), LLM-neutral (neutral `Message` contract only), no schema / migration / contract change. The C conditional is gated on a simple signal (`transient.messages[-1].role == "tool"`); the fresh / non-tool path is unchanged (regression-tested: fresh turn still ends with user). Real Azure converged. The adjacency rebuild relies on Message object identity (strategies don't copy) — covered by the build()-through-real-strategy test, which would catch a future copy regression.

---

## Design Note Extract

NO — bug fix in an existing category (Cat 5 PromptBuilder); no new contract / no 17.md change / no new domain.
