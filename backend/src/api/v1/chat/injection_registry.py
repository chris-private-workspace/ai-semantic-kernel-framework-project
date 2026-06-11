"""
File: backend/src/api/v1/chat/injection_registry.py
Purpose: Tenant-scoped in-memory (tenant_id, session_id) → mid-run message inbox queue.
Category: api/v1/chat
Scope: Phase 57 / Sprint 57.101 (B1 — between-turns message injection primitive)

Description:
    Bridges TWO separate HTTP requests for a between-turns injection:
      - the streaming RUN request (POST /chat/): registers a queue at run start,
        unregisters it when the SSE stream closes; the loop drains the queue at
        each turn boundary via a QueueMessageInbox.
      - the inject POST request (POST /chat/{id}/inject): puts a Message onto the
        queue (after the endpoint gates tenant + active-session via SessionRegistry).

    A per-request mailbox (subagent/mailbox.py) cannot bridge two requests — its
    state dies with the request — so this is a process-level singleton, exactly
    like SessionRegistry (session_registry.py). Storage is tenant-scoped
    (`dict[tenant_id, dict[session_id, asyncio.Queue[Message]]]`) so a cross-tenant
    put can never reach another tenant's queue (defense-in-depth — the inject
    endpoint ALSO gates via SessionRegistry.get).

    Thread-safety: a single asyncio.Lock guards the nested-dict structure (queue
    creation / lookup / removal). The asyncio.Queue itself is event-loop-safe for
    the put_nowait/get_nowait used here; both run on the FastAPI app loop, so a
    queue created by the run request is drained by the same loop and fed by the
    inject request on that loop.

Key Components:
    - InjectionRegistry: register / put / drain / unregister, keyed by (tenant, session)
    - QueueMessageInbox: a MessageInbox (Cat 1 contract) view over one session's queue
    - get_default_injection_registry(): the module singleton (tests reset it — Risk Class C)

Created: 2026-06-11 (Sprint 57.101)
Last Modified: 2026-06-11

Modification History (newest-first):
    - 2026-06-11: Initial creation (Sprint 57.101) — injection channel + QueueMessageInbox

Related:
    - agent_harness/_contracts/inbox.py (MessageInbox ABC the loop drains)
    - api/v1/chat/session_registry.py (tenant-scoped singleton pattern + active-session gate)
    - api/v1/chat/router.py (registers/unregisters the queue + the POST /{id}/inject endpoint)
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant-scoped storage)
    - claudedocs/1-planning/harness-deepening-proposal-20260610.md §2.2 (B1)
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from agent_harness._contracts import Message, MessageInbox


# === InjectionRegistry: cross-request mid-run message channel ================
# Why: the inject POST and the streaming run are SEPARATE HTTP requests; a
# per-request mailbox cannot carry a message from one to the other. A
# process-level singleton (the SessionRegistry precedent) keyed by
# (tenant_id, session_id) bridges them while preserving the multi-tenant 鐵律.
class InjectionRegistry:
    """Tenant-scoped in-memory injection queues. DEPRECATED-IN: when a durable
    queue backend lands (mirrors SessionRegistry's deprecation note)."""

    def __init__(self) -> None:
        self._tenants: dict[UUID, dict[UUID, asyncio.Queue[Message]]] = {}
        self._lock = asyncio.Lock()

    async def register(self, tenant_id: UUID, session_id: UUID) -> None:
        """Create an empty queue for a starting run. Idempotent on an existing one."""
        async with self._lock:
            self._tenants.setdefault(tenant_id, {}).setdefault(session_id, asyncio.Queue())

    async def put(self, tenant_id: UUID, session_id: UUID, message: Message) -> bool:
        """Enqueue a mid-run message. Returns False if the session has no live queue
        (the run never started or already ended → the caller surfaces 409)."""
        async with self._lock:
            sessions = self._tenants.get(tenant_id)
            queue = sessions.get(session_id) if sessions is not None else None
            if queue is None:
                return False
            queue.put_nowait(message)  # unbounded queue → never QueueFull
            return True

    async def drain(self, tenant_id: UUID, session_id: UUID) -> list[Message]:
        """Return all currently-queued messages (non-blocking). [] if none/unregistered."""
        async with self._lock:
            sessions = self._tenants.get(tenant_id)
            queue = sessions.get(session_id) if sessions is not None else None
            if queue is None:
                return []
            drained: list[Message] = []
            while True:
                try:
                    drained.append(queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            return drained

    async def unregister(self, tenant_id: UUID, session_id: UUID) -> None:
        """Drop a session's queue when its run ends; idempotent. Prunes empty tenants."""
        async with self._lock:
            sessions = self._tenants.get(tenant_id)
            if sessions is None:
                return
            sessions.pop(session_id, None)
            if not sessions:
                del self._tenants[tenant_id]


# === QueueMessageInbox: the loop's view over one session's queue =============
# Why: the loop depends only on the MessageInbox ABC (Cat 1); this binds the ABC
# to one session's InjectionRegistry queue so the loop can drain without knowing
# the registry shape. B2 will provide a different MessageInbox backed by the
# TEAMMATE mailbox — the loop seam is identical.
class QueueMessageInbox(MessageInbox):
    """A MessageInbox over an InjectionRegistry queue for a single (tenant, session)."""

    def __init__(self, registry: InjectionRegistry, tenant_id: UUID, session_id: UUID) -> None:
        self._registry = registry
        self._tenant_id = tenant_id
        self._session_id = session_id

    async def drain(self) -> list[Message]:
        return await self._registry.drain(self._tenant_id, self._session_id)


# Module-level singleton — shared across router handlers within a single FastAPI
# app instance (the run request registers; the inject request puts). Tests reset
# it via an autouse fixture to avoid cross-test / cross-event-loop leakage
# (Risk Class C — the SessionRegistry / service_factory precedent).
_default_injection_registry = InjectionRegistry()


def get_default_injection_registry() -> InjectionRegistry:
    return _default_injection_registry
