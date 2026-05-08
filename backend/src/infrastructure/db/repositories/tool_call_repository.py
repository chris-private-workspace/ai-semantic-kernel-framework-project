"""
File: backend/src/infrastructure/db/repositories/tool_call_repository.py
Purpose: ToolCallRepository — DAO for tool_calls table (tool invocation persistence).
Category: Infrastructure / Repositories (Sprint 57.7 US-R1 / AD-Reality-3b)
Scope: Phase 57 / Sprint 57.7 Day 3 Tier 2

Description:
    Encapsulates ToolCall ORM operations for chat router ToolCallExecuted
    observer. Each tool invocation that fires within an AgentLoop run gets
    one row per invocation (matches Cost Ledger granularity at chat
    router.py L431-444 — same event hook).

    Schema highlights (per tools.py:131):
    - session_id FK to sessions.id (CASCADE)
    - status: pending → running → completed/failed
    - duration_ms computed from ToolCallExecuted event
    - sandbox_used + permission_check_passed pulled from event when present

Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 2)
Last Modified: 2026-05-10

Modification History (newest-first):
    - 2026-05-10: Initial creation (Sprint 57.7 US-R1 — AD-Reality-3b closure)

Related:
    - infrastructure/db/models/tools.py (ToolCall ORM at L131)
    - api/v1/chat/router.py (consumer in _stream_loop_events)
    - agent_harness/_contracts/events.py (ToolCallExecuted event shape)
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.tools import ToolCall

logger = logging.getLogger(__name__)


class ToolCallRepository:
    """DAO for tool_calls table — per-invocation persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        session_id: UUID,
        tenant_id: UUID,
        tool_name: str,
        arguments: dict[str, Any],
        status: str = "completed",
        duration_ms: int | None = None,
        permission_check_passed: bool = True,
    ) -> ToolCall:
        """INSERT a tool_call row.

        Caller responsible for transaction lifecycle. Best-effort callers
        wrap in `db.begin_nested()` SAVEPOINT to isolate FK violations.

        Args:
            session_id: Parent session FK (must exist in sessions before INSERT).
            tenant_id: Multi-tenant scope from request.state.tenant_id.
            tool_name: e.g. "echo_tool" / "incident_query".
            arguments: JSONB dict captured from ToolCallExecuted event.
            status: "pending" / "running" / "completed" / "failed".
            duration_ms: Wall-clock duration if known; None for pending/running.
            permission_check_passed: From Cat 9 guardrail engine; default True
                when no engine configured (matches handler.py echo_demo path).

        Returns:
            ToolCall ORM instance with server-generated id + created_at.

        Raises:
            sqlalchemy.exc.IntegrityError: FK violation on session_id.
        """
        call = ToolCall(
            session_id=session_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            arguments=arguments,
            permission_check_passed=permission_check_passed,
            status=status,
            duration_ms=duration_ms,
        )
        self._db.add(call)
        await self._db.flush()
        logger.debug(
            "tool_call_repository.create ok",
            extra={
                "session_id": str(session_id),
                "tool_name": tool_name,
                "status": status,
            },
        )
        return call


__all__ = ["ToolCallRepository"]
