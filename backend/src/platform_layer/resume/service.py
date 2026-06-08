"""
File: backend/src/platform_layer/resume/service.py
Purpose: ResumeService — load a paused HITL checkpoint + rebuild a resumable loop.
Category: platform_layer (resume orchestration; crosses Cat 7 checkpoint + Cat 9 HITL + auth)
Scope: Phase 57 / Sprint 57.88 (US-4)

Description:
    Orchestrates the RUN-2 side of durable HITL pause-resume (the RUN-1 pause is
    in agent_harness loop.py `_cat9_hitl_branch` deferred branch). When a chat
    loop ESCALATEs a tool in deferred mode, it persists a `state_snapshots` row
    (reason="orchestrator_loop:hitl_pause") carrying, in its DurableState
    metadata: the `pending_approval` block (pending tool call + approval_request_id
    + turn) AND the `resume_messages` buffer (decision B — no `messages` table in
    this codebase, so the pause checkpoint self-contains the conversation).

    resume_session():
        1. Find the LATEST `hitl_pause` snapshot for (session_id, tenant_id).
           Not found (incl. cross-tenant — the query filters by tenant_id, and a
           foreign tenant simply sees no row) → return None → endpoint 404
           (multi-tenant 鐵律: never reveal cross-tenant existence).
        2. Rebuild the LoopState from that snapshot version via DBCheckpointer.load
           (durable + metadata round-trip), then overlay transient.messages from
           metadata["resume_messages"] (the checkpointer split drops the buffer).
        3. Build a fully-wired loop via the injected `build_loop` (defaults to the
           real chat-path builder, so the resumed loop mirrors the original chat
           loop's deps — same adapter / tools / hitl_manager / checkpointer — with
           ZERO divergence). The endpoint then drives `loop.resume(state=state)`.

    LLM-neutrality: provider-free. The loop's adapter is built by the injected
    builder (the chat builder constructs the AzureOpenAIAdapter); this service
    imports no provider SDK.

Key Components:
    - PAUSE_CHECKPOINT_REASON: the snapshot.reason sentinel for a paused loop
    - ResumeResult: (loop, state) pair the endpoint streams
    - ResumeService.resume_session(): load + tenant-guard + rebuild

Created: 2026-06-08 (Sprint 57.88 Day 2 — US-4)
Last Modified: 2026-06-08

Modification History (newest-first):
    - 2026-06-08: Sprint 57.88 Day-4 — wire HITLManager into default builder (resume get_decision)
    - 2026-06-08: Initial creation (Sprint 57.88 US-4) — durable pause-resume orchestration

Related:
    - agent_harness/orchestrator_loop/loop.py (deferred pause branch + resume() + msg helper)
    - agent_harness/state_mgmt/checkpointer.py (DBCheckpointer load + metadata round-trip)
    - api/v1/chat/handler.py (build_real_llm_handler — default loop builder)
    - api/v1/chat/router.py (POST /chat/{session_id}/resume consumer)
    - 17-cross-category-interfaces.md §resume() + checkpoint pending_approval
    - sprint-57-88-plan.md §3.4
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Awaitable, Callable
from uuid import UUID

from sqlalchemy import select

from agent_harness._contracts import LoopState
from agent_harness.orchestrator_loop import AgentLoop, messages_from_metadata
from agent_harness.state_mgmt import DBCheckpointer
from infrastructure.db.models import StateSnapshot

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# The snapshot.reason (created_by_category) written by loop.py's deferred
# ESCALATE branch when it pauses for approval. ResumeService keys off this to
# find the resumable checkpoint (single-source with loop.py `_cat9_hitl_branch`).
PAUSE_CHECKPOINT_REASON = "orchestrator_loop:hitl_pause"


# A loop builder: (db, session_id, tenant_id, user_id) -> a wired AgentLoop.
# Defaults to the real chat-path builder (build_real_llm_handler) so a resumed
# loop is byte-for-byte the same wiring as the original chat loop — no divergence.
# Tests inject a builder returning a mock loop (no Azure env needed).
LoopBuilder = Callable[
    ["AsyncSession", UUID, UUID, UUID],
    Awaitable[AgentLoop],
]


@dataclass(frozen=True)
class ResumeResult:
    """A loop ready to `resume()` plus the rebuilt LoopState the endpoint passes in."""

    loop: AgentLoop
    state: LoopState


async def _default_build_loop(
    db: "AsyncSession",
    session_id: UUID,
    tenant_id: UUID,
    user_id: UUID,
) -> AgentLoop:
    """Default loop builder — the real chat-path builder (zero divergence).

    Imported lazily to avoid an import cycle (api → platform_layer → api) and to
    keep azure-adapter weight out of unit tests that inject their own builder.
    `build_real_llm_handler` returns (loop, verifier_registry); resume drives the
    loop directly (verification is the normal-run wrapper's concern), so the
    registry is discarded here.

    Sprint 57.88 (Day-4 drive-through fix): wire the SAME process-singleton
    HITLManager the chat path used to REQUEST the approval. `resume()` reads the
    recorded decision via `HITLManager.get_decision(request_id)`; without a wired
    manager the resumed loop's `_hitl_manager` is None → resume() fails closed
    with LoopCompleted(ERROR) BEFORE executing the approved tool. The integration
    test masked this by injecting a mock loop that already had a hitl_manager;
    only the real drive-through surfaced the gap. `get_service_factory()` is the
    same process-singleton the chat endpoint resolves via Depends, so request
    (pause) and resume share one HITLManager → consistent approvals view.
    """
    from api.v1.chat.handler import build_real_llm_handler
    from platform_layer.governance.service_factory import get_service_factory

    hitl_manager = get_service_factory().get_hitl_manager()
    loop, _registry = build_real_llm_handler(
        db=db,
        session_id=session_id,
        tenant_id=tenant_id,
        user_id=user_id,
        hitl_manager=hitl_manager,
    )
    return loop


class ResumeService:
    """Load a paused HITL checkpoint and rebuild a resumable loop (Sprint 57.88).

    Args:
        build_loop: factory that wires the AgentLoop to resume. Defaults to the
            real chat-path builder so the resumed loop mirrors the original chat
            loop's dependency graph exactly. Tests inject a mock-loop builder.
    """

    def __init__(self, *, build_loop: LoopBuilder | None = None) -> None:
        self._build_loop = build_loop or _default_build_loop

    async def resume_session(
        self,
        *,
        session_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        db: "AsyncSession",
    ) -> ResumeResult | None:
        """Find the paused checkpoint for (session, tenant) and rebuild a resumable loop.

        Returns None when there is no paused checkpoint for this tenant's session
        (incl. cross-tenant — the query filters by tenant_id so a foreign tenant
        sees no row). The endpoint maps None → 404 (multi-tenant 鐵律: do not
        reveal cross-tenant existence).

        On success: returns ResumeResult(loop, state). The endpoint drives
        `loop.resume(state=state, trace_context=...)` and streams its events.
        Whether the approval was actually decided is checked inside `resume()`
        (non-blocking `HITLManager.get_decision`); an un-decided approval yields a
        terminal ERROR event rather than a 404 (the checkpoint exists — it just
        isn't ready), so the client gets a clear stream rather than a silent 404.
        """
        # 1. Latest paused snapshot for THIS tenant's session (tenant-scoped).
        #    DESC by version → the most recent pause wins (one pause per slice).
        result = await db.execute(
            select(StateSnapshot)
            .where(
                (StateSnapshot.session_id == session_id)
                & (StateSnapshot.tenant_id == tenant_id)
                & (StateSnapshot.reason == PAUSE_CHECKPOINT_REASON)
            )
            .order_by(StateSnapshot.version.desc())
            .limit(1)
        )
        snapshot: StateSnapshot | None = result.scalar_one_or_none()
        if snapshot is None:
            # No paused checkpoint for this tenant's session (or cross-tenant) → 404.
            return None

        # 2. Rebuild the LoopState from that snapshot version. DBCheckpointer is
        #    bound to (session_id, tenant_id) so load() is tenant-scoped too. The
        #    checkpointer drops the messages buffer (US-3 split), so overlay
        #    transient.messages from metadata["resume_messages"] (decision B).
        checkpointer = DBCheckpointer(db, session_id=session_id, tenant_id=tenant_id)
        loaded = await checkpointer.load(version=snapshot.version)
        rehydrated_messages = messages_from_metadata(loaded.durable.metadata)
        state = replace(
            loaded,
            transient=replace(loaded.transient, messages=rehydrated_messages),
        )

        # 3. Wire the loop (default: the real chat builder → zero divergence).
        loop = await self._build_loop(db, session_id, tenant_id, user_id)
        return ResumeResult(loop=loop, state=state)
