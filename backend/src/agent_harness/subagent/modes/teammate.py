"""
File: backend/src/agent_harness/subagent/modes/teammate.py
Purpose: TeammateExecutor — runs a TEAMMATE peer as a REAL multi-turn child loop that
    reports to the parent (send_to_parent) + carries the B1 between-turns inbox.
Category: 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-3 → Sprint 57.102 (B2a: real child loop)

Description:
    TEAMMATE mode (per CC peer-pane pattern): a subagent runs with its own fresh
    context (unlike FORK's parent-copy) but can communicate with its parent.

    Sprint 57.102 (B2a) replaced the Sprint 54.2 single-shot ChatClient call with a
    REAL child AgentLoop (the same 57.94 FORK ChildLoopFactory pattern): the executor
    builds a fresh child loop via the injected TeammateChildLoopFactory, drives
    child.run(user_input=task), and DRAINS the child's LoopEvent stream into a
    SubagentResult (last LLMResponded.content -> summary; LoopCompleted.total_tokens).
    Two differences from FORK: (a) the child loop carries a `send_to_parent` tool + a
    MessageInbox (the B1 between-turns inbox, Sprint 57.101 — wired here; the live
    producer = B2b); (b) after the child completes, the executor drains the parent's
    mailbox for any `send_to_parent` reports and folds them into the summary so the
    parent integrates them via the existing task_spawn channel (await-completion: the
    reports surface when the teammate finishes — live streaming to a busy parent needs
    a non-blocking / detached teammate, deferred per proposal §2.5).

    While draining, it FORWARDS the child's per-turn TAO subset (TurnStarted /
    LLMResponded / ToolCall*) wrapped in SubagentChildEvent to the injected emitter
    (the Sprint 57.96 relay), so the chat-v2 Inspector Tree node expands to the
    teammate's per-turn loop (incl. the send_to_parent tool call) for free.

    The child reuses the parent run()/_run_turns (re-enterable since Sprint 57.89)
    with ZERO loop.py change; it carries a recursion-safe tool subset (no task_spawn /
    handoff) so a teammate cannot itself spawn (depth structurally bounded at 1).

    Failure modes (all return SubagentResult(success=False) — fail-closed; execute()
    never raises, since a raise would propagate through wait_for and crash the turn):
    - teammate_child_loop_factory is None -> error="teammate_child_loop_factory_unavailable"
    - asyncio.TimeoutError on max_duration_s -> error="timeout: {N}s"
    - empty final answer -> error="empty_response" (or "child_guardrail_blocked"
      when the child run terminated guardrail_blocked — Sprint 57.110 truthful label)
    - any child-loop exception -> error="child_loop_error: {type}: {msg}"

Created: 2026-05-04 (Sprint 54.2)
Last Modified: 2026-06-13

Modification History:
    - 2026-06-13: Sprint 57.110 B4 — blocked label + fail_partial salvage (mirror fork.py)
    - 2026-06-11: Sprint 57.103 (B2b) — inbox_factory → inbox_scope (register/unregister the
      child's queue around the child run so a chat-user inject reaches a LIVE teammate)
    - 2026-06-11: Sprint 57.102 (B2a) — single-shot → real child loop (mirror 57.94 FORK)
      + send_to_parent report fold + B1 inbox wiring + TAO forward
    - 2026-05-04: Initial creation (Sprint 54.2 US-3)

Related:
    - subagent/modes/fork.py — ForkExecutor pattern + _TAO_CHILD_EVENT_TYPES
    - subagent/mailbox.py — MailboxStore (send_to_parent delivery + drain)
    - subagent/tools.py — make_send_to_parent_tool
    - _contracts/subagent.py — TeammateChildLoopFactory / SubagentBudget / SubagentResult
    - _contracts/inbox.py — MessageInbox (the B1 between-turns inbox; producer = B2b)
    - 01-eleven-categories-spec.md §範疇 11 / 20-subagent-child-loop-design.md
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Awaitable, Callable
from uuid import UUID, uuid4

from agent_harness._contracts import (
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    SubagentBudget,
    SubagentChildEvent,
    SubagentMode,
    SubagentResult,
    TraceContext,
)
from agent_harness.subagent.budget import BudgetEnforcer
from agent_harness.subagent.mailbox import MailboxStore
from agent_harness.subagent.modes.fork import _TAO_CHILD_EVENT_TYPES

if TYPE_CHECKING:
    from agent_harness._contracts import (
        MessageInbox,
        TeammateChildLoopFactory,
        TeammateInboxScope,
    )


class TeammateExecutor:
    """Runs a TEAMMATE subagent as a real child AgentLoop (Sprint 57.102 B2a).

    Like ForkExecutor, but the child loop ALSO carries a send_to_parent tool + a
    MessageInbox (the B1 between-turns inbox; live producer = B2b), and the executor
    folds any send_to_parent reports into the summary the parent integrates.
    """

    def __init__(
        self,
        *,
        teammate_child_loop_factory: "TeammateChildLoopFactory | None" = None,
        mailbox: MailboxStore,
        enforcer: BudgetEnforcer | None = None,
        event_emitter: Callable[[LoopEvent], Awaitable[None]] | None = None,
        inbox_scope: "TeammateInboxScope | None" = None,
    ) -> None:
        self._child_loop_factory = teammate_child_loop_factory
        self._mailbox = mailbox
        self._enforcer = enforcer or BudgetEnforcer()
        # Sprint 57.96 relay: forward the child's TAO events (best-effort; the
        # dispatcher passes its own _emit_safely so a forward never breaks the loop).
        self._event_emitter = event_emitter
        # Sprint 57.103 (B2b): a lifecycle-scoped inbox. An async CM keyed by
        # subagent_id that REGISTERS the child's InjectionRegistry queue on enter
        # (so a concurrent chat-user inject POST can reach it) + yields the child's
        # MessageInbox + UNREGISTERS on exit. None = no inbox (byte-identical to the
        # pre-B2b no-inbox path). The concrete CM lives in the api layer (handler).
        self._inbox_scope = inbox_scope

    async def execute(
        self,
        *,
        subagent_id: UUID,
        parent_session_id: UUID,
        role: str,
        task: str,
        budget: SubagentBudget,
        trace_context: TraceContext | None = None,
    ) -> SubagentResult:
        """Run task as a real child loop; drain its events + send_to_parent reports
        into a SubagentResult (fail-closed)."""
        start = time.monotonic()
        # Fail closed (no single-shot fallback — mirror FORK US-5). A raise would
        # propagate through wait_for + crash the parent turn, so always RETURN.
        factory = self._child_loop_factory
        if factory is None:
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.TEAMMATE,
                success=False,
                summary="",
                error="teammate_child_loop_factory_unavailable",
            )

        final_answer = ""
        tokens_used = 0
        stop_reason = ""
        emitter = self._event_emitter

        async def _drive(inbox: "MessageInbox | None") -> None:
            nonlocal final_answer, tokens_used, stop_reason
            child = factory(budget, inbox)  # fresh child loop instance per spawn
            child_session_id = uuid4()
            async for ev in child.run(
                session_id=child_session_id,
                user_input=task,
                trace_context=trace_context,
            ):
                # Sprint 57.96 relay: forward the child's per-turn TAO events tagged
                # with THIS subagent_id (incl. the send_to_parent ToolCall + the B2b
                # MessageInjected) so the frontend routes them to the Tree node the
                # spawn created.
                if emitter is not None and isinstance(ev, _TAO_CHILD_EVENT_TYPES):
                    await emitter(SubagentChildEvent(subagent_id=subagent_id, inner=ev))
                if isinstance(ev, LLMResponded) and ev.content:
                    final_answer = ev.content  # last assistant answer wins
                elif isinstance(ev, LoopCompleted):
                    tokens_used = ev.total_tokens
                    stop_reason = ev.stop_reason

        # Sprint 57.103 (B2b): bracket the child drive in the inbox scope so the
        # child's InjectionRegistry queue is registered ONLY while the teammate runs
        # (a concurrent chat-user inject POST reaches it via the module registry) and
        # unregistered on EVERY exit (success / timeout / exception via async-with).
        # None scope = no inbox (byte-identical to the pre-B2b no-inbox path).
        def _salvaged_summary() -> str:
            # Sprint 57.110 (B4) fail_partial: salvage the child's partial work
            # (mirror fork.py — the nonlocal survives the wait_for cancellation).
            if budget.failure_policy == "fail_partial" and final_answer:
                summary, _ = self._enforcer.truncate_summary(final_answer, cap_words=500)
                return summary
            return ""

        scope = self._inbox_scope
        try:
            if scope is not None:
                async with scope(subagent_id) as inbox:
                    await asyncio.wait_for(_drive(inbox), timeout=budget.max_duration_s)
            else:
                await asyncio.wait_for(_drive(None), timeout=budget.max_duration_s)
        except asyncio.TimeoutError:
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.TEAMMATE,
                success=False,
                summary=_salvaged_summary(),
                duration_ms=(time.monotonic() - start) * 1000.0,
                error=f"timeout: {budget.max_duration_s}s",
                metadata={"failure_policy": budget.failure_policy},
            )
        except Exception as exc:  # noqa: BLE001 — fail-closed catches all
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.TEAMMATE,
                success=False,
                summary=_salvaged_summary(),
                duration_ms=(time.monotonic() - start) * 1000.0,
                error=f"child_loop_error: {type(exc).__name__}: {exc}",
                metadata={"failure_policy": budget.failure_policy},
            )

        duration_ms = (time.monotonic() - start) * 1000.0
        if not final_answer:
            # Sprint 57.110 (B4): truthful label for a guardrail-blocked child run
            # (mirror fork.py; wire-stable stop_reason string, no Cat 1 enum import).
            blocked = stop_reason == "guardrail_blocked"
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.TEAMMATE,
                success=False,
                summary="",
                duration_ms=duration_ms,
                error="child_guardrail_blocked" if blocked else "empty_response",
            )

        # Sprint 57.102 (B2a): drain any send_to_parent reports the teammate delivered
        # mid-loop + fold them into the summary so the parent integrates them via the
        # existing task_spawn channel (await-completion: they surface now, at finish).
        reports = await self._mailbox.drain(parent_session_id, "parent")
        if reports:
            report_block = "\n".join(str(r.content) for r in reports)
            final_answer = f"[teammate reports]\n{report_block}\n[final answer]\n{final_answer}"

        summary, _ = self._enforcer.truncate_summary(final_answer, cap_words=500)
        return SubagentResult(
            subagent_id=subagent_id,
            mode=SubagentMode.TEAMMATE,
            success=True,
            summary=summary,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
