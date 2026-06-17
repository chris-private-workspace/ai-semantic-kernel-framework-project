# Diagnostic — `AD-Subagent-Child-Event-SSE-Relay` is fully resolved/YAGNI (CLOSED)

**Date**: 2026-06-17
**Type**: Status / diagnostic snapshot (drive-through + Day-0 feasibility)
**Verdict**: The AD's literal symptom is ALREADY FIXED (57.95 + 57.96); the only "residual" (recursion depth > 1) is bounded by design = YAGNI. **AD fully CLOSED — no code sprint.**

## Why this diagnostic ran

`AD-Subagent-Child-Event-SSE-Relay` was selected as a next direction, described (per the stale line-469 framing in `next-phase-candidates.md`) as: *"chat `DefaultSubagentDispatcher` built WITHOUT an `event_emitter` → child HEADLESS → Inspector Tree shows 'no subagents'; key blocker."* Per the 57.132/57.134 lesson (verify the premise before building), a diagnostic drive-through ran first.

## Drive-through: the literal symptom is GONE (resolved by 57.95 + 57.96)

Real chat-v2 UI (Playwright) + real Azure gpt-5.2 + real backend, dan@acme.com/acme-prod, fresh session. Prompt: *"Use the task_spawn tool to spawn a subagent … fun fact about the number 7 … tell me what it returned."*

- The agent called `task_spawn` (mode=fork) → child loop ran → returned summary "Seven is the only number from 1–10 whose English name has two syllables." (1,826 tok) → parent reported it (turn 3, verification 0.99).
- SSE relay frames present: `subagent_spawned` ×1, `subagent_completed` ×1, `subagent_child` ×2.
- **Inspector "Tree" tab** rendered (NOT "no subagents"):
  ```
  SUBAGENT TREE · LIVE
  b6a11c09-… (root) · "Seven is the only number…" · completed
  turn 0 · LLM · Seven is the only number…
  Mode: fork · Depth: 1 · Concurrency: 0 · Tokens (subtree): 1,826
  ```

So the chat dispatcher IS wired with the emitter (`handler.py:440`, comment "Sprint 57.95: the chat path now wires the emitter"); the relay (buffer/drain `router.py:299-302,744`) works; `SubagentSpawned.parent_session_id` + `depth` render. The line-469 "built WITHOUT emitter" framing is the pre-57.95 problem statement that lingered uncleaned.

Evidence screenshot: `subagent-tree-relay-diagnostic-20260617.jpeg`.

## Day-0 feasibility: depth>1 is bounded by design (YAGNI)

The only genuine residual (per the more-accurate line-438 framing) was **recursion depth > 1** (a subagent whose child itself spawns). Day-0 read of the child-loop factory shows this is **unreachable by design**:

- `handler.py:354-356` (comment): *"The child carries a recursion-safe tool subset — `make_default_executor` WITHOUT a `subagent_dispatcher` omits `task_spawn` … so a child cannot itself spawn (depth bounded at 1)."*
- `handler.py:363` (`_make_child_loop` / fork) + `handler.py:401` (`_make_teammate_child_loop`): both pass `subagent_dispatcher=None` → children have NO `task_spawn` tool.

Building depth>1 would require FIRST removing this deliberate recursion-safety bound (unbounded recursion / cost-explosion risk) with no product need — textbook YAGNI / AP-6. The frontend Tree already renders `depth`; 2nd-level routing would be speculative.

## Outcome

- node-level relay (57.95) ✅ · depth-1 child turn-stream (57.96) ✅ (drive-through proven) · depth>1 = **design-bounded YAGNI**.
- `AD-Subagent-Child-Event-SSE-Relay` **fully CLOSED** in `next-phase-candidates.md`.
- (Untested, separate: TEAMMATE/HANDOFF-mode Tree relay — only `fork` was driven. Those modes are separate 🟡 carryovers.)
- Lesson (3rd consecutive, after 57.132 + 57.134): a candidate-pool AD's stale framing can describe an already-fixed or by-design-bounded state — drive-through + Day-0 feasibility BEFORE planning.
