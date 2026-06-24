"""
File: backend/src/agent_harness/state_mgmt/todo_store.py
Purpose: Concrete DBTodoStore — per-session durable todo list for the task primitive.
Category: 範疇 7 (State Management)
Scope: Phase 57 / Sprint 57.140

Description:
    Implements the TodoStore ABC (state_mgmt/_abc.py) against the Sprint 57.140
    `session_todos` table (1 row/session, tenant-scoped, NOT partitioned). Backs
    the explicit task primitive (CC `TodoWrite`-like): the agent writes a whole
    structured plan via the Cat-2 `write_todos` tool; this persists it so a
    follow-up send rehydrates "what's left / what's done" — the durable task spine
    the multi-send long-running model was missing.

    Bound to one (session_id, tenant_id) at construction (mirrors DBMessageStore /
    DBCheckpointer). `replace` upserts the whole list on session_id (CC replace-
    whole-list semantics); `load` returns the current list. This is structured,
    durable TASK STATE — distinct from the MessageStore conversation ledger and
    from Cat-11 `task_spawn` (subagent dispatch; the name avoids `task` on purpose).

    Best-effort: a persistence failure (replace) or a read failure (load) MUST NOT
    break the loop — replace swallows + logs (a missed write only costs the next
    send a stale plan), load returns [] (degrades to no plan, today's baseline).
    The None-store case (legacy / test callers without db/session/tenant) is
    handled by the factory returning None, so this impl always holds a real
    AsyncSession (mirrors DBMessageStore).

Key Components:
    - DBTodoStore: production impl of the TodoStore ABC

Created: 2026-06-24 (Sprint 57.140)
Last Modified: 2026-06-24

Modification History (newest-first):
    - 2026-06-24: Initial creation (Sprint 57.140) — session_todos upsert (load + replace)

Related:
    - state_mgmt/_abc.py §TodoStore — the ABC this implements
    - _contracts/todo.py — Todo + todos_to_jsonb / todos_from_jsonb row serde
    - infrastructure/db/models/sessions.py §SessionTodos — the ORM table
    - api/v1/chat/_category_factories.py §make_chat_todo_store — the wiring factory
    - multi-tenant-data.md (tenant 鐵律 — every query scoped by tenant_id)
"""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from agent_harness._contracts.todo import Todo, todos_from_jsonb, todos_to_jsonb
from agent_harness.state_mgmt._abc import TodoStore
from infrastructure.db.models.sessions import SessionTodos as SessionTodosRow

logger = logging.getLogger(__name__)


# === DBTodoStore: per-session durable todo list ===
# Why: the chat loop's plan is emergent free text — no structure, no durable state,
# no cross-send survival (the 57.140 spike gap). A follow-up send / compaction loses
# "what's left". This persists the whole structured list (replace-whole-list, CC
# TodoWrite semantics) keyed on session_id + reloads it on the next send.
#
# Alternative considered:
#   - DurableState.metadata (Pattern A) — rejected: only written on pause checkpoint,
#     so clean-end multi-send does NOT persist (eval §3.1-A "insufficient").
#   - reuse a memory layer — rejected: memory = "remember facts" semantics, not
#     "current task state"; a dedicated table keeps the spine architecturally clear
#     (user-confirmed eval option C).
# Reference: research #1 task-primitive-thin-spike-eval-20260618.md §3.1; design note 44.
class DBTodoStore(TodoStore):
    """DB-backed TodoStore; bound to one (session_id, tenant_id).

    Mirrors DBMessageStore's bound-instance pattern — load()/replace() always
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

    async def load(self) -> list[Todo]:
        """Return the bound session's current todo list (best-effort; [] on miss/error)."""
        try:
            stmt = select(SessionTodosRow).where(
                SessionTodosRow.session_id == self._session_id,
                SessionTodosRow.tenant_id == self._tenant_id,
            )
            result = await self._db.execute(stmt)
            row = result.scalar_one_or_none()
            return todos_from_jsonb(row.todos) if row is not None else []
        except (
            Exception
        ):  # noqa: BLE001 — a read failure degrades to no plan, never breaks the send
            logger.exception("DBTodoStore.load failed (best-effort; degrading to no plan)")
            return []

    async def replace(self, todos: list[Todo]) -> None:
        """Overwrite the bound session's whole todo list (upsert on session_id; best-effort)."""
        payload = todos_to_jsonb(todos)
        try:
            # SAVEPOINT — an upsert failure must not poison the outer SSE
            # transaction (mirrors DBMessageStore.append).
            async with self._db.begin_nested():
                stmt = (
                    pg_insert(SessionTodosRow)
                    .values(
                        id=uuid4(),
                        tenant_id=self._tenant_id,
                        session_id=self._session_id,
                        todos=payload,
                    )
                    .on_conflict_do_update(
                        constraint="uq_session_todos_session",
                        set_={"todos": payload, "updated_at": func.now()},
                    )
                )
                await self._db.execute(stmt)
        except Exception:  # noqa: BLE001 — an upsert failure only costs the next send a stale plan
            logger.exception("DBTodoStore.replace failed (best-effort)")
