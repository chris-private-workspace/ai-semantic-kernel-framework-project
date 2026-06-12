"""
File: backend/src/agent_harness/subagent/dispatcher.py
Purpose: DefaultSubagentDispatcher — production class implementing SubagentDispatcher ABC.
Category: 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-1 → US-2 (FORK + AsTool) → US-3 (TEAMMATE); US-4 HANDOFF

Description:
    DefaultSubagentDispatcher implements the 3-method ABC (spawn /
    wait_for / handoff) using a fire-and-forget asyncio pattern:

    - spawn(mode=FORK|TEAMMATE, task, parent_session_id, budget) -> UUID
        Launches an asyncio.Task in the background; returns subagent_id
        immediately. Future is stored in self._in_flight for retrieval.
    - wait_for(subagent_id, timeout_s) -> SubagentResult
        Blocks until the future resolves (or timeout). Returns
        success=False / error=... on BudgetExceededError or timeout.
    - handoff(target_agent, context) -> UUID (new session_id)
        Synchronous transfer; returns new session_id directly. (US-4)

    AS_TOOL mode is NOT routed through spawn(). It uses the separate
    `as_tool_factory(spec)` method (Option A from Day 0 D1-followup),
    which returns (ToolSpec, handler) for Cat 2 ToolRegistry. spawn(mode=AS_TOOL)
    raises SubagentLaunchError.

    Concurrency: spawn() pre-checks budget.max_concurrent against the count
    of in-flight subagents (per AD-Test-1 53.6: per-request DI; not module
    singleton). Depth check is left to the caller (parent loop tracks current
    depth; passes via context).

US-2 deliverable (this file): wires FORK via ForkExecutor + as_tool_factory
    via AsToolWrapper. TEAMMATE / HANDOFF still raise NotImplementedError.

Created: 2026-05-04 (Sprint 54.2)

Modification History:
    - 2026-06-12: Sprint 57.107 (B3) — retire HandoffExecutor stub + handoff() method
    - 2026-06-11: Sprint 57.103 (B2b) — inbox_factory → inbox_scope (register child queue)
    - 2026-06-11: Sprint 57.102 (B2a) — TEAMMATE real child loop (teammate factory + inbox)
    - 2026-06-09: Sprint 57.96 — pass _emit_safely → ForkExecutor (forward child TAO events)
    - 2026-06-09: Sprint 57.94 — thread child_loop_factory → ForkExecutor (real FORK child loop)
    - 2026-05-10: Sprint 57.12 US-1 — emit SubagentSpawned/Completed (closes AD-Cat11-SSEEvents)
    - 2026-05-04: Wire HANDOFF via HandoffExecutor (US-4)
    - 2026-05-04: Wire TEAMMATE via TeammateExecutor + MailboxStore injection (US-3)
    - 2026-05-04: Wire FORK via ForkExecutor + as_tool_factory via AsToolWrapper (US-2)
    - 2026-05-04: Initial skeleton creation (Sprint 54.2 US-1)

Related:
    - subagent/_abc.py — SubagentDispatcher ABC (3 methods)
    - subagent/modes/fork.py — ForkExecutor (US-2)
    - subagent/modes/as_tool.py — AsToolWrapper (US-2)
    - _contracts/subagent.py — SubagentBudget / SubagentResult / SubagentMode / AgentSpec
    - 17-cross-category-interfaces.md §2.1 (SubagentDispatcher owner)
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Awaitable, Callable
from uuid import UUID, uuid4

from adapters._base.chat_client import ChatClient
from agent_harness._contracts import (
    AgentSpec,
    ChildLoopFactory,
    LoopEvent,
    SubagentBudget,
    SubagentCompleted,
    SubagentMode,
    SubagentResult,
    SubagentSpawned,
    TeammateChildLoopFactory,
    TraceContext,
)
from agent_harness.subagent._abc import SubagentDispatcher
from agent_harness.subagent.budget import BudgetEnforcer
from agent_harness.subagent.exceptions import (
    BudgetExceededError,
    SubagentLaunchError,
)
from agent_harness.subagent.mailbox import MailboxStore
from agent_harness.subagent.modes.as_tool import AsToolWrapper
from agent_harness.subagent.modes.fork import ForkExecutor
from agent_harness.subagent.modes.teammate import TeammateExecutor

if TYPE_CHECKING:
    # Tool handler return type — see modes/as_tool.py for ToolHandler alias.
    from agent_harness._contracts import TeammateInboxScope, ToolSpec
    from agent_harness.subagent.modes.as_tool import ToolHandler

logger = logging.getLogger(__name__)

# Sprint 57.12 US-1: best-effort event emitter; exception isolated from tool path.
SubagentEventEmitter = Callable[[LoopEvent], Awaitable[None]]


class DefaultSubagentDispatcher(SubagentDispatcher):
    """Production dispatcher; routes by SubagentMode to mode executors.

    Per Day 0 D1 / D10: 3-method ABC (spawn / wait_for / handoff) + 1 extra
    method (as_tool_factory) for AS_TOOL wrapping. Mode executors (Fork in
    US-2, Teammate in US-3, Handoff in US-4) injected via __init__.

    Per AD-Test-1 (53.6) lesson: this class is per-request DI, NOT
    module-level singleton. AgentLoop holds a fresh instance per request.
    """

    def __init__(
        self,
        *,
        chat_client: ChatClient,
        mailbox: MailboxStore | None = None,
        event_emitter: SubagentEventEmitter | None = None,
        child_loop_factory: ChildLoopFactory | None = None,
        teammate_child_loop_factory: TeammateChildLoopFactory | None = None,
        inbox_scope: "TeammateInboxScope | None" = None,
    ) -> None:
        # Sprint 57.102 (B2a): `chat_client` is vestigial for TEAMMATE now (TEAMMATE
        # runs a real child loop via teammate_child_loop_factory, like FORK). Retained
        # as a ctor param for caller compatibility (make_chat_subagent_dispatcher + the
        # FORK/AS_TOOL adapter still pass it) + a potential future single-shot mode.
        self._chat = chat_client
        self._enforcer = BudgetEnforcer()
        # Mailbox is per-request DI (NOT module-level singleton; AD-Test-1 53.6).
        # If caller does not inject one, create a fresh instance scoped to this dispatcher.
        self._mailbox = mailbox or MailboxStore()
        # Sprint 57.94: FORK runs a REAL child loop via child_loop_factory (built at
        # composition where the Cat 1 dep-set is in scope). None = FORK fails closed
        # (no single-shot fallback — US-5).
        # Sprint 57.96 (Cat 11 Scope B): pass _emit_safely so ForkExecutor FORWARDS
        # the child loop's per-turn TAO events (wrapped in SubagentChildEvent). The
        # bound method reads self._event_emitter at CALL time (set below), so there
        # is no __init__ ordering issue; None emitter → _emit_safely no-ops → no
        # forwarding. AS_TOOL shares this _fork instance → inherits forwarding free.
        self._fork = ForkExecutor(
            child_loop_factory=child_loop_factory,
            enforcer=self._enforcer,
            event_emitter=self._emit_safely,
        )
        # Sprint 57.102 (B2a): TEAMMATE now runs a REAL multi-turn child loop via
        # teammate_child_loop_factory (mirror FORK) + carries the B1 MessageInbox + a
        # send_to_parent tool. None factory → TEAMMATE fails closed (mirror FORK).
        # Shares _emit_safely so the teammate's per-turn TAO + send_to_parent ToolCall
        # relay to the Inspector Tree (57.96) for free.
        # Sprint 57.103 (B2b): inbox_scope (an async CM keyed by subagent_id) registers
        # the child's InjectionRegistry queue while it runs so a chat-user inject reaches
        # a LIVE teammate; None scope = no inbox.
        self._teammate = TeammateExecutor(
            teammate_child_loop_factory=teammate_child_loop_factory,
            mailbox=self._mailbox,
            enforcer=self._enforcer,
            event_emitter=self._emit_safely,
            inbox_scope=inbox_scope,
        )
        self._as_tool_wrapper = AsToolWrapper(fork_executor=self._fork)
        # In-flight subagent tasks for wait_for() lookup. Per-instance state;
        # NOT module-level — fresh dispatcher per request.
        self._in_flight: dict[UUID, asyncio.Task[SubagentResult]] = {}
        # Sprint 57.12 US-1: optional best-effort SSE event emitter (closes
        # AD-Cat11-SSEEvents 54.2 carryover). None = no-op for unit-test
        # backwards compat. Emission errors logged but never propagate.
        self._event_emitter = event_emitter

    async def _emit_safely(self, event: LoopEvent) -> None:
        """Best-effort emission; warns on failure but never raises (tool path stays clean)."""
        if self._event_emitter is None:
            return
        try:
            await self._event_emitter(event)
        except Exception as exc:  # noqa: BLE001 — emission MUST NOT break tool execution
            logger.warning("Subagent event emission failed (%s): %s", type(exc).__name__, exc)

    async def spawn(
        self,
        *,
        mode: SubagentMode,
        task: str,
        parent_session_id: UUID,
        budget: SubagentBudget | None = None,
        trace_context: TraceContext | None = None,
    ) -> UUID:
        """Launch a subagent in FORK or TEAMMATE mode; return subagent_id.

        AS_TOOL mode raises SubagentLaunchError — use as_tool_factory() instead.
        HANDOFF mode raises SubagentLaunchError — it is not dispatcher-served:
        the loop's output classifier terminates the run with
        stop_reason="handoff" and the platform layer boots the child session
        (Sprint 57.107 B3 convergence; the HandoffExecutor stub is retired).

        US-2 fills FORK; US-3 fills TEAMMATE.
        """
        if mode == SubagentMode.AS_TOOL:
            raise SubagentLaunchError(
                "AS_TOOL mode does not use spawn(); call as_tool_factory(spec) "
                "to get (ToolSpec, handler) for Cat 2 ToolRegistry."
            )
        if mode == SubagentMode.HANDOFF:
            raise SubagentLaunchError(
                "HANDOFF mode is not dispatcher-served: the `handoff` tool_call is "
                "loop-intercepted (stop_reason='handoff') and the platform layer "
                "boots the child session."
            )

        budget = budget or SubagentBudget()
        # Concurrency guard — count active futures (not yet done).
        active = sum(1 for t in self._in_flight.values() if not t.done())
        try:
            self._enforcer.check_concurrent(active_count=active, budget=budget)
        except BudgetExceededError as exc:
            # Budget exceeded surfaces as a synchronous launch failure (no
            # subagent_id allocated). Caller catches SubagentLaunchError and
            # converts to its own error path.
            raise SubagentLaunchError(f"spawn rejected: {exc}") from exc

        subagent_id = uuid4()

        # Sprint 57.12 US-1: emit SubagentSpawned BEFORE the asyncio.Task
        # creates the subagent execution. Awaited inline so the SSE Spawned
        # event reaches the consumer before the Completed event (ordering
        # guarantee for SubagentTree UI parent→child rendering).
        await self._emit_safely(
            SubagentSpawned(
                subagent_id=subagent_id,
                mode=mode.value,
                parent_session_id=parent_session_id,
                trace_context=trace_context,
            )
        )

        if mode == SubagentMode.FORK:
            inner_coro = self._fork.execute(
                subagent_id=subagent_id,
                task=task,
                budget=budget,
                trace_context=trace_context,
            )
        elif mode == SubagentMode.TEAMMATE:
            # Per Day 3 D15: role defaults to "teammate"; ABC has no role kwarg.
            # Phase 55+ may extend ABC or thread role via trace_context.
            inner_coro = self._teammate.execute(
                subagent_id=subagent_id,
                parent_session_id=parent_session_id,
                role="teammate",
                task=task,
                budget=budget,
                trace_context=trace_context,
            )
        else:  # pragma: no cover — Enum exhausted by branches above
            raise SubagentLaunchError(f"Unknown mode: {mode}")

        # Sprint 57.12 US-1: wrap inner coro to emit SubagentCompleted when
        # the subagent's asyncio.Task resolves (success OR exception). This
        # decouples the Completed event timing from when callers invoke
        # wait_for() — the event always fires at actual termination, which
        # is what SubagentTree UI expects for live status update.
        async def _track_and_emit() -> SubagentResult:
            try:
                result = await inner_coro
            except BaseException:
                # On exception path, emit Completed with empty summary so
                # the UI can transition the subagent node to terminal state
                # (failure indicated by empty summary + 0 tokens; richer
                # error metadata is a future contract extension — see
                # AD-Cat11-Completed-ErrorFields carryover).
                await self._emit_safely(
                    SubagentCompleted(
                        subagent_id=subagent_id,
                        summary="",
                        tokens_used=0,
                        trace_context=trace_context,
                    )
                )
                raise
            await self._emit_safely(
                SubagentCompleted(
                    subagent_id=subagent_id,
                    summary=result.summary,
                    tokens_used=result.tokens_used,
                    trace_context=trace_context,
                )
            )
            return result

        self._in_flight[subagent_id] = asyncio.create_task(_track_and_emit())
        return subagent_id

    async def wait_for(
        self,
        subagent_id: UUID,
        *,
        timeout_s: int | None = None,
        trace_context: TraceContext | None = None,
    ) -> SubagentResult:
        """Block until subagent completes; return SubagentResult (fail-closed)."""
        task = self._in_flight.get(subagent_id)
        if task is None:
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.FORK,  # placeholder — unknown
                success=False,
                summary="",
                error=f"unknown_subagent_id: {subagent_id}",
            )
        try:
            if timeout_s is None:
                return await task
            return await asyncio.wait_for(asyncio.shield(task), timeout=timeout_s)
        except asyncio.TimeoutError:
            # Don't cancel — caller may still want to retrieve later via wait_for again.
            return SubagentResult(
                subagent_id=subagent_id,
                mode=SubagentMode.FORK,
                success=False,
                summary="",
                error=f"wait_for_timeout: {timeout_s}s",
            )

    def as_tool_factory(self, spec: AgentSpec) -> tuple["ToolSpec", "ToolHandler"]:
        """Wrap AgentSpec into a Cat 2 ToolSpec + handler pair.

        Per Day 0 D1-followup Option A: AS_TOOL is OUT-OF-BAND from spawn()
        because it returns a ToolSpec (not a SubagentResult). Callers register
        the returned (ToolSpec, handler) with Cat 2 ToolRegistry; the LLM then
        invokes the wrapped subagent like any tool.

        US-2 wires this to AsToolWrapper.
        """
        return self._as_tool_wrapper.wrap(spec)
