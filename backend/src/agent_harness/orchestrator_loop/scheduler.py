"""
File: src/agent_harness/orchestrator_loop/scheduler.py
Purpose: Cross-burst auto-continue — re-run the loop for the next burst when a plan is unfinished.
Category: 範疇 1 (Orchestrator Loop)
Scope: Phase 57.157 / Sprint 57.157

Description:
    The pure decision half of the Scheduler feature (cross-burst auto-continue).
    When a chat send's loop burst ends at the per-send max_turns ceiling
    (stop_reason="max_turns") but the durable task plan (write_todos) still has
    unfinished todos, the router SSE generator re-invokes loop.run() for the next
    burst instead of closing the stream and forcing a manual "continue".

    This module is the pure, I/O-free predicate + the continuation-nudge constant;
    the router (api/v1/chat/router.py) owns the outer-loop control flow, the
    billing-every-burst / closeout-only-final split, and the DBTodoStore load.
    Keeping the decision here makes it unit-testable in isolation and keeps the
    router seam minimal (loop.py stays untouched — a re-run of run() self-rehydrates
    the ledger + Active Plan for free, Sprint 57.127 + 57.156).

Key Components:
    - should_continue_plan(): the 4-condition AND predicate
    - CONTINUATION_NUDGE: the user-turn text a continuing burst is driven with

Created: 2026-07-06 (Sprint 57.157)
Last Modified: 2026-07-06

Modification History (newest-first):
    - 2026-07-06: Initial creation (Sprint 57.157) — cross-burst auto-continue predicate

Related:
    - 01-eleven-categories-spec.md §範疇1 — Orchestrator Loop
    - api/v1/chat/router.py _stream_loop_events — the outer-loop consumer
    - orchestrator_loop/termination.py — TerminationReason.MAX_TURNS
    - _contracts/todo.py — Todo.status (plan completeness)
    - 60-scheduler-cross-burst-design.md
"""

from __future__ import annotations

from collections.abc import Sequence

from agent_harness._contracts.todo import Todo
from agent_harness.orchestrator_loop.termination import TerminationReason

# The user-turn text a continuing burst is driven with. It lands in the Cat-3
# rehydration ledger (loop.py:2005/2009) as a real user turn so the next burst's
# rehydrated context reads coherently, but NOT in the 57.126 replay transcript
# (that persists only the inbound prompt) → replay shows the clean original
# conversation while the agent internally sees the nudge.
CONTINUATION_NUDGE = "Continue executing the plan. Work the next ready step(s)."


def should_continue_plan(
    *,
    enabled: bool,
    stop_reason: str,
    todos: Sequence[Todo],
    bursts_used: int,
    max_bursts: int,
) -> bool:
    """Return True iff the SSE generator should auto-run another burst.

    Cross-burst auto-continue fires only when ALL of these hold:
      - ``enabled``: the CHAT_SCHEDULER_AUTO_CONTINUE lever is on (default OFF).
      - the burst hit the per-send turn ceiling (``stop_reason == "max_turns"``) —
        NOT a natural end_turn, NOT token_budget (conservative: token exhaustion is
        the main runaway path and deliberately does not auto-continue), NOT a
        handoff / approval / error / cancelled terminal.
      - ``bursts_used < max_bursts``: the bound that prevents infinite continuation.
      - the durable plan still has unfinished work (any todo != "completed"). An
        empty plan (no write_todos) → nothing to continue → False.

    Pure + I/O-free: the router loads ``todos`` (DBTodoStore) and owns the outer loop.
    """
    if not enabled:
        return False
    if stop_reason != TerminationReason.MAX_TURNS.value:
        return False
    if bursts_used >= max_bursts:
        return False
    return any(todo.status != "completed" for todo in todos)
