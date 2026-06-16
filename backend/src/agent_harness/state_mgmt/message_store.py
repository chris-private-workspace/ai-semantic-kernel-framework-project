"""
File: backend/src/agent_harness/state_mgmt/message_store.py
Purpose: Concrete DBMessageStore — per-session Cat-3 Message ledger for live multi-turn rehydration.
Category: 範疇 7 (State Management)
Scope: Phase 57 / Sprint 57.127

Description:
    Implements the MessageStore ABC (state_mgmt/_abc.py) against the Sprint 49.2
    `messages` table (partitioned, tenant-scoped). Closes
    `AD-ChatV2-Live-MultiTurn-Context`: a follow-up chat send rehydrates the prior
    conversation into the live loop so the LLM keeps multi-turn context.

    Bound to one (session_id, tenant_id) at construction (mirrors DBCheckpointer).
    The loop self-loads at run() start (`load()`) and appends the run's NEW
    messages at clean completion (`append()`). This is the verbatim Cat-3 Message
    ledger — distinct from `state_snapshots` (Checkpointer, which EXCLUDES the
    message buffer per the US-3 split) and from `message_events` (57.125/126, the
    SSE-replay ledger for the frontend history UI). It is the "production should
    use a dedicated messages table" path the loop.py 57.88 SPIKE NOTE called for.

    Best-effort: a persistence failure (append) or a read failure (load) MUST NOT
    break the loop — append swallows + logs (a missed ledger write only costs the
    next send some context), load returns [] (degrades to single-turn, today's
    behavior). The None-store case (legacy / test callers without db/session/
    tenant) is handled by the factory returning None, so this impl always holds a
    real AsyncSession (mirrors DBCheckpointer).

Key Components:
    - DBMessageStore: production impl of the MessageStore ABC

Created: 2026-06-16 (Sprint 57.127)
Last Modified: 2026-06-16

Modification History (newest-first):
    - 2026-06-16: Initial creation (Sprint 57.127) — messages-table ledger (load + append)

Related:
    - state_mgmt/_abc.py §MessageStore — the ABC this implements
    - _contracts/message_serde.py — _message_to_dict / _message_from_dict row serde
    - infrastructure/db/models/sessions.py §Message — the partitioned ORM table
    - api/v1/chat/_category_factories.py §make_chat_message_store — the wiring factory
    - 09-db-schema-design.md Group 2 (messages table) + multi-tenant-data.md (tenant 鐵律)
"""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import Message
from agent_harness._contracts.message_serde import _message_from_dict, _message_to_dict
from agent_harness.state_mgmt._abc import MessageStore
from infrastructure.db.models.sessions import Message as MessageRow

logger = logging.getLogger(__name__)


# === DBMessageStore: per-session Message ledger ===
# Why: the loop builds `messages` from scratch each send (system + new user_input
# only) → a follow-up in an existing session loses prior context (the 57.126
# drive-through found turn 2 "its population?" could not resolve "it"→Paris).
# This persists each turn's Cat-3 Message objects + reloads them on the next send.
#
# Alternative considered:
#   - Reconstruct from message_events (SSE frames) — rejected: tool calls / system
#     are lossy (~80% fidelity), a silent looks-done-but-incomplete fix.
#   - Checkpoint-metadata (resume_messages) for normal sessions — rejected:
#     O(turns²) state_snapshots bloat; conflates the durable snapshot with the
#     message ledger (the 57.88 SPIKE NOTE wants them separate).
# Reference: AD-ChatV2-Live-MultiTurn-Context; design note 38; loop.py 57.88 SPIKE NOTE.
class DBMessageStore(MessageStore):
    """DB-backed MessageStore; bound to one (session_id, tenant_id).

    Mirrors DBCheckpointer's bound-instance pattern — load()/append() always
    scope to the bound session + tenant (multi-tenant 鐵律), so the ABC needs no
    session_id/tenant_id per call.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        *,
        session_id: UUID,
        tenant_id: UUID,
    ) -> None:
        self._db = db_session
        self._session_id = session_id
        self._tenant_id = tenant_id

    async def load(self) -> list[Message]:
        """Return the bound session's prior messages oldest-first (best-effort)."""
        try:
            stmt = (
                select(MessageRow)
                .where(
                    MessageRow.session_id == self._session_id,
                    MessageRow.tenant_id == self._tenant_id,
                )
                .order_by(MessageRow.sequence_num)
            )
            result = await self._db.execute(stmt)
            rows = result.scalars().all()
            return [_message_from_dict(row.content) for row in rows]
        except (
            Exception
        ):  # noqa: BLE001 — a read failure degrades to no prior context, never breaks the send
            logger.exception(
                "DBMessageStore.load failed (best-effort; degrading to no prior context)"
            )
            return []

    async def append(self, messages: list[Message], *, turn_num: int) -> None:
        """Append NEW messages; sequence_num continues from the session MAX (best-effort)."""
        if not messages:
            return
        try:
            # SAVEPOINT — a ledger-write failure must not poison the outer SSE
            # transaction (mirrors router._persist_main_event).
            async with self._db.begin_nested():
                start = await self._next_sequence_num()
                for offset, msg in enumerate(messages):
                    self._db.add(
                        MessageRow(
                            id=uuid4(),
                            session_id=self._session_id,
                            tenant_id=self._tenant_id,
                            sequence_num=start + offset,
                            turn_num=turn_num,
                            role=msg.role,
                            content_type="text" if isinstance(msg.content, str) else "blocks",
                            content=_message_to_dict(msg),
                        )
                    )
        except (
            Exception
        ):  # noqa: BLE001 — a ledger-write failure only costs the next send some context
            logger.exception("DBMessageStore.append failed (best-effort)")

    async def _next_sequence_num(self) -> int:
        """The next sequence_num for the bound session (MAX + 1; 1 for a fresh session)."""
        stmt = select(func.coalesce(func.max(MessageRow.sequence_num), 0)).where(
            MessageRow.session_id == self._session_id,
            MessageRow.tenant_id == self._tenant_id,
        )
        result = await self._db.execute(stmt)
        return int(result.scalar_one()) + 1
