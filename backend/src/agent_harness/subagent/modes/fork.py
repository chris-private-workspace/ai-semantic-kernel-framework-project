"""
File: backend/src/agent_harness/subagent/modes/fork.py
Purpose: ForkExecutor — runs a FORK subagent as a REAL child agent loop (multi-turn, tool-capable).
Category: 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-2 → Sprint 57.94 (real child loop) → Sprint 57.96 (TAO forward)

Description:
    FORK mode executor. Sprint 57.94 (地基 A payoff) replaced the Sprint 54.2
    single-shot ChatClient call with a REAL child AgentLoop. The executor builds
    a fresh child loop via the injected ChildLoopFactory (supplied at composition,
    where the full Cat 1 dep-set is in scope), drives child.run(user_input=task),
    and DRAINS the child's LoopEvent stream into a SubagentResult (the last
    LLMResponded.content -> summary; LoopCompleted.total_tokens -> tokens_used).
    Sprint 57.96 (Scope B): while draining, it also FORWARDS the child's per-turn
    TAO subset (TurnStarted / LLMResponded / ToolCall*) wrapped in
    SubagentChildEvent (tagged with this subagent_id) to the injected emitter, so
    the chat-v2 Inspector Tree node expands to the child's per-turn loop.
    The child reuses the parent run()/_run_turns (re-enterable since Sprint 57.89)
    with ZERO loop.py change; it carries a recursion-safe tool subset (no
    task_spawn / handoff) so a child cannot itself spawn (depth structurally
    bounded at 1).

    Budget enforcement:
    - max_tokens -> child loop's token_budget (via the factory)
    - max_duration_s -> wall-clock timeout via asyncio.wait_for around the drive
    - max_concurrent -> enforced by caller (DefaultSubagentDispatcher)
    - summary cap -> BudgetEnforcer.truncate_summary on the final answer

    Failure modes (all return SubagentResult(success=False) — fail-closed; execute()
    never raises, since a raise would propagate through wait_for and crash the turn):
    - child_loop_factory is None -> error="child_loop_factory_unavailable"
    - asyncio.TimeoutError on max_duration_s -> error="timeout: {N}s"
    - empty final answer -> error="empty_response"
    - any child-loop exception -> error="child_loop_error: {type}: {msg}"

Created: 2026-05-04 (Sprint 54.2)
Last Modified: 2026-06-09

Modification History:
    - 2026-06-09: Sprint 57.96 — forward child TAO events (SubagentChildEvent) via emitter
    - 2026-06-09: Real child loop via ChildLoopFactory + LoopEvent drain (Sprint 57.94)
    - 2026-05-04: Initial creation (Sprint 54.2 US-2)

Related:
    - subagent/dispatcher.py — DefaultSubagentDispatcher threads child_loop_factory
    - _contracts/subagent.py — ChildLoopFactory / SubagentBudget / SubagentResult
    - orchestrator_loop/_abc.py — AgentLoop.run() (the child reuses it, unchanged)
    - 01-eleven-categories-spec.md §範疇 11 / 20-subagent-child-loop-design.md
"""

from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from agent_harness._contracts import (
    ChildLoopFactory,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    SubagentBudget,
    SubagentChildEvent,
    SubagentMode,
    SubagentResult,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
    TraceContext,
    TurnStarted,
)
from agent_harness.subagent.budget import BudgetEnforcer

# Sprint 57.96 (Cat 11 Scope B): the TAO-essentials subset of child loop events
# forwarded (wrapped in SubagentChildEvent) so the chat-v2 Inspector Tree node
# expands to the child's per-turn loop. Deliberately EXCLUDES low-signal events
# (LLMRequested / PromptBuilt / MemoryAccessed / Span* / Metric* / Checkpoint /
# ContextCompacted) to keep the Tree high-signal (locked scope 2026-06-09).
_TAO_CHILD_EVENT_TYPES: tuple[type[LoopEvent], ...] = (
    TurnStarted,
    LLMResponded,
    ToolCallRequested,
    ToolCallExecuted,
    ToolCallFailed,
)


class ForkExecutor:
    """Runs a FORK subagent as a real child AgentLoop (Sprint 57.94)."""

    def __init__(
        self,
        *,
        child_loop_factory: ChildLoopFactory | None = None,
        enforcer: BudgetEnforcer | None = None,
        event_emitter: Callable[[LoopEvent], Awaitable[None]] | None = None,
    ) -> None:
        self._child_loop_factory = child_loop_factory
        self._enforcer = enforcer or BudgetEnforcer()
        # Sprint 57.96 (Cat 11 Scope B): best-effort emitter used to FORWARD the
        # child loop's per-turn TAO events (wrapped in SubagentChildEvent). The
        # dispatcher passes its own `_emit_safely` here (already try/except-isolated
        # + reads the live _event_emitter at call time), so a forward never breaks
        # the child loop. None = no forwarding (non-chat paths / unit tests).
        self._event_emitter = event_emitter

    async def execute(
        self,
        *,
        subagent_id: UUID,
        task: str,
        budget: SubagentBudget,
        trace_context: TraceContext | None = None,
    ) -> SubagentResult:
        """Run task as a real child loop; drain its events into SubagentResult (fail-closed)."""
        start = time.monotonic()
        # US-5: no single-shot fallback — without a factory FORK cannot run.
        # Fail closed (do NOT raise; execute()'s contract is to always return a
        # SubagentResult — a raise would propagate through wait_for + crash the turn).
        factory = self._child_loop_factory
        if factory is None:
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.FORK,
                success=False,
                summary="",
                error="child_loop_factory_unavailable",
            )

        final_answer = ""
        tokens_used = 0
        emitter = self._event_emitter

        async def _drive() -> None:
            nonlocal final_answer, tokens_used
            child = factory(budget)  # fresh child loop instance per spawn
            child_session_id = uuid4()
            async for ev in child.run(
                session_id=child_session_id,
                user_input=task,
                trace_context=trace_context,
            ):
                # Sprint 57.96 (Cat 11 Scope B): forward the child's per-turn TAO
                # events tagged with THIS subagent_id (NOT child_session_id) so the
                # frontend routes them to the node the spawn already created. The
                # emitter is the dispatcher's _emit_safely (best-effort isolated).
                if emitter is not None and isinstance(ev, _TAO_CHILD_EVENT_TYPES):
                    await emitter(SubagentChildEvent(subagent_id=subagent_id, inner=ev))
                if isinstance(ev, LLMResponded) and ev.content:
                    final_answer = ev.content  # last assistant answer wins
                elif isinstance(ev, LoopCompleted):
                    tokens_used = ev.total_tokens

        try:
            await asyncio.wait_for(_drive(), timeout=budget.max_duration_s)
        except asyncio.TimeoutError:
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.FORK,
                success=False,
                summary="",
                duration_ms=(time.monotonic() - start) * 1000.0,
                error=f"timeout: {budget.max_duration_s}s",
            )
        except Exception as exc:  # noqa: BLE001 — fail-closed catches all
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.FORK,
                success=False,
                summary="",
                duration_ms=(time.monotonic() - start) * 1000.0,
                error=f"child_loop_error: {type(exc).__name__}: {exc}",
            )

        duration_ms = (time.monotonic() - start) * 1000.0
        if not final_answer:
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.FORK,
                success=False,
                summary="",
                duration_ms=duration_ms,
                error="empty_response",
            )
        summary, _ = self._enforcer.truncate_summary(final_answer, cap_words=500)
        return SubagentResult(
            subagent_id=subagent_id,
            mode=SubagentMode.FORK,
            success=True,
            summary=summary,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
