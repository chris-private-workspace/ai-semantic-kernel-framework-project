# 20 — Subagent FORK Child-Loop Design (Cat 11, 地基 A payoff)

**Purpose**: Design note extracted from the Sprint 57.94 spike that made Cat 11 FORK run a REAL child `AgentLoop` (multi-turn, tool-capable) instead of a single-shot chat call. Records the verified architecture, the decision matrix for HOW the child loop is built, and the explicit verified-vs-deferred boundary.
**Category / Scope**: Cat 11 (Subagent Orchestration) — Phase 57.94 spike extract
**Created**: 2026-06-09
**Status**: Active (spike-extract; ≥95% verified ratio)
**Source**: Sprint 57.94 implementation (`sprint-57-94-plan.md` + retrospective). Authority: this note describes WHAT WAS BUILT + VERIFIED; the live code is the source of truth.

> **Modification History**
> - 2026-06-09: Initial creation — FORK real child-loop spike extract (Sprint 57.94)

---

## 1. Spike Summary — US-1..US-6 (what shipped + verified)

The 地基 A lifecycle (durable pause-resume + re-enterable `_run_turns`, Sprint 57.88-93) was built to feed Cat 11. This spike consumes it: a FORK subagent is now a real child `AgentLoopImpl` that reuses the parent's `run()`/`_run_turns` with **ZERO `loop.py` change**.

- **US-1 (real child loop)**: `ForkExecutor.execute` builds a fresh child via an injected `ChildLoopFactory` and drives `child.run(user_input=task)` — `backend/src/agent_harness/subagent/modes/fork.py:100-121`.
- **US-2 (recursion-safe subset)**: the child tool pair is built by `make_default_executor(subagent_dispatcher=None)` which omits `task_spawn` + the `agent_researcher` AS_TOOL (`backend/src/business_domain/_register_all.py:262-279`) → a child cannot itself spawn → depth bounded at 1.
- **US-3 (real result, mapping unchanged)**: the child `LoopEvent` stream is drained into a `SubagentResult` (last `LLMResponded.content` → summary; `LoopCompleted.total_tokens` → tokens) — `fork.py:106-149`. `wait_for` + the `task_spawn` handler dict mapping are byte-identical (`subagent/tools.py:117-123`).
- **US-4 (tenant + Cat 12)**: the factory threads `tenant_id` + `tracer` into the child `AgentLoopImpl`; the child opens its OWN `agent_loop.run` LOOP span (`backend/src/agent_harness/orchestrator_loop/loop.py:1563`).
- **US-5 (no divergent path)**: `None` factory → fail-closed (no single-shot fallback; `fork.py:91-99`); existing FORK/AS_TOOL tests converted to a mock-LLM child loop (no AP-10).
- **US-6 (drive-through)**: real chat-v2 + real Azure gpt-5.2 → `task_spawn` → child uses `echo_tool` → `{success: true, summary: "child loop is real", tokens_used: 3684}` + 2389ms TOOL_EXEC span (impossible under the old single-shot).

## 2. Decision Matrix — how the child loop is built

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| **A. Child-loop factory at composition (CHOSEN)** | `_make_child_loop` closure in `build_real_llm_handler` (`handler.py`) captures the local Cat 1 deps; injected into the dispatcher → `ForkExecutor` | ✅ All deps already local in one function (`handler.py:228-396` builds BOTH parent loop + dispatcher); `loop.py` untouched; clean isolation (fresh child instance per spawn) |
| B. Override `_run_turns` per-child | Pass child registry/system_prompt as `_run_turns` params | ❌ `_run_turns` reads `self._tool_registry`/`self._system_prompt`/`self._max_turns`/`self._tenant_id` (`loop.py:1645,1857,1708`) — a child MUST be its OWN instance; parameterizing the shared loop is invasive + risks the most-tested file |
| C. Keep single-shot as fallback | `child_loop_factory` optional; fall back to `chat()` when absent | ❌ Two code paths = AP-10 Mock-vs-Real divergence + the single-shot is the very Potemkin this spike removes. Rejected → `None` factory fails closed instead |

**Recursion guard decision**: rather than thread `max_subagent_depth`, the child registry simply **excludes** `task_spawn`/`handoff` (free via `make_default_executor(subagent_dispatcher=None)`) → a child is structurally unable to spawn → no depth field needed this slice.

## 3. Verified Invariants (file:line + verification)

- **`loop.py` diff = 0** — the child reuses `run()`/`_run_turns` byte-identical (the 57.89 re-entrancy payoff). Verify: `git diff $(git merge-base main HEAD)..HEAD -- backend/src/agent_harness/orchestrator_loop/loop.py` → empty.
- **Drain → SubagentResult** — `fork.py:106-118` collects `LLMResponded.content` (final answer) + `LoopCompleted.total_tokens`; `LLMResponded`/`LoopCompleted` defined `_contracts/events.py:92,127`.
- **Fail-closed, never raises** — `fork.py:91-99` (None factory) + `:122-141` (timeout/exception) all return `SubagentResult(success=False)`; a raise would propagate through `dispatcher.wait_for` (`dispatcher.py:266-269`, catches only `TimeoutError`) and crash the parent turn.
- **AS_TOOL inherits for free** — `dispatcher.py:114,121` build ONE `ForkExecutor` shared by `self._fork` + `self._as_tool_wrapper`.
- Verify: `pytest backend/tests/unit/agent_harness/subagent/test_subagent_child_loop.py -q` (4 pass) + full `pytest -q` = 2271 passed.

## 4. Cross-Category Contracts

- **`ChildLoopFactory`** (`_contracts/subagent.py`) — `Callable[[SubagentBudget], "AgentLoop"]`. A composition detail, NOT a new `SubagentDispatcher` ABC method (the ABC is unchanged). Registered in `17-cross-category-interfaces.md` Cat 11 section.
- Cat 11 → Cat 1 reference is TYPE_CHECKING-only (no runtime import cycle; `check_cross_category_import` green).
- No new `LoopEvent` (child events drained, not relayed); no new DB table / migration / `/resume` change.

## 5. Open Invariants (NOT verified this spike — deferred)

| Deferred | AD | Why |
|----------|-----|-----|
| TEAMMATE / HANDOFF real loops | (separate slices) | FORK + AS_TOOL only this spike |
| `HandoffService` (boot child session on `stop_reason="handoff"`) | (separate) | loop-side terminator wired (57.68/69); consumer absent |
| SSE-relay of child / subagent events | `AD-Subagent-Child-Event-SSE-Relay` | `LoopEvent` base has no `parent_session_id`/`depth`; the chat dispatcher has no `event_emitter` → Inspector Tree shows "no subagents"; the child runs **headless** (drive-through confirmed) |
| Child LOOP-span nesting under parent | `AD-Subagent-Child-Span-Nesting` | the `task_spawn` handler passes `trace_context=None` to `spawn` → the child span is not explicitly parented (best-effort via ambient tracer); the parent trace shows only the wrapping `task_spawn` TOOL_EXEC span |
| Recursion depth > 1 / nested spawning | (future) | child has no `task_spawn` (bounded at 1) |
| parentUuid transcript chain / child checkpoint | `AD-Subagent-Transcript-Isolation` | child is ephemeral (no checkpointer) |
| Child-internal governance (Cat 9/10 in the child) | `AD-Subagent-Child-Governance` | lean child this slice (no guardrail/verifier) |
| Failure policies (FAIL_FAST/SOFT/PARTIAL) | (future) | `SubagentBudget` has no `failure_policy` |

## 6. Rollback / Fallback

- The change is confined to `subagent/` + the `handler.py` factory closure + tests; `loop.py` is untouched. Revert = `git revert` the Sprint 57.94 commits → FORK reverts to the single-shot `chat()` (the prior `ForkExecutor` shape). No DB / migration / contract change to unwind.
- Runtime fallback: when `session_id` is absent (legacy / non-chat callers) the dispatcher is not built → no FORK path exercised. When the factory is absent (mis-wiring) FORK fails closed (`child_loop_factory_unavailable`), surfacing to the parent LLM as a tool error — no crash.

## 7. References

- `01-eleven-categories-spec.md §範疇 11` — Cat 11 spec (4 modes, 無 worktree)
- `17-cross-category-interfaces.md` — Cat 11 `SubagentDispatcher` single-source + the new `ChildLoopFactory` composition note
- `sprint-57-94-plan.md` + `sprint-57-94-checklist.md` + `agent-harness-execution/phase-57/sprint-57-94/{progress,retrospective}.md`
- `claudedocs/4-changes/feature-changes/CHANGE-061-subagent-fork-child-loop.md`
- `claudedocs/5-status/agent-harness-cc-parity-20260607.md §3 #7` (the "child-loop executor hollow stub" this spike closes)

## 8. 8-Point Quality Gate (self-check)

- [x] 1. Section headers ↔ US (§1 maps US-1..US-6)
- [x] 2. Each claim has file:line (§1/§3)
- [x] 3. Decision matrix with rejected-option rationale (§2)
- [x] 4. Verification command (§3 — git diff + pytest)
- [x] 5. Test fixture reference (`_child_loop_helpers.py` + `test_subagent_child_loop.py`)
- [x] 6. Verified-vs-deferred boundary explicit (§5)
- [x] 7. Rollback path (§6)
- [x] 8. 17.md cross-ref (§4/§7 — no parallel contract definition)
