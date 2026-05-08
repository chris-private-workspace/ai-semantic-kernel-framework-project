"""
File: backend/src/infrastructure/db/repositories/session_repository.py
Purpose: SessionRepository — DAO for sessions table (chat session lifecycle).
Category: Infrastructure / Repositories (Sprint 57.7 US-R1 / AD-Reality-3a)
Scope: Phase 57 / Sprint 57.7 Day 3 Tier 2

Description:
    Encapsulates Session ORM operations for chat router observer wiring.
    Sprint 57.6 left sessions/tool_calls deferred (AD-Reality-3a/3b) under
    the assumption that JWT user_id extraction infra was missing. Day 3
    探勘 found `TenantContextMiddleware.dispatch` at tenant_context.py:174
    already populates `request.state.user_id` from JWT claim.sub UUID
    parsing → unblocked.

    create_session():
        Best-effort INSERT — caller wraps in try/except so DB flake doesn't
        cascade into chat 503. Uses Session.user_id (NOT NULL FK to users.id)
        + tenant_id (TenantScopedMixin) + provided session_id (PK).

Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 2)
Last Modified: 2026-05-10

Modification History (newest-first):
    - 2026-05-10: Initial creation (Sprint 57.7 US-R1 — AD-Reality-3a closure)

Related:
    - infrastructure/db/models/sessions.py (Session ORM)
    - api/v1/chat/router.py (consumer at chat POST entry)
    - tests/unit/infrastructure/db/repositories/test_session_repository.py
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.sessions import Session

logger = logging.getLogger(__name__)


class SessionRepository:
    """DAO for sessions table — chat lifecycle persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_session(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        title: str | None = None,
    ) -> Session:
        """INSERT a new session row.

        Caller responsible for transaction lifecycle (commit / rollback /
        SAVEPOINT). Returns the Session instance with server-generated
        timestamps populated AFTER `await self._db.flush()`.

        Args:
            session_id: Session UUID (caller-generated; matches SSE X-Session-Id header).
            user_id: Authenticated user from request.state.user_id.
            tenant_id: Multi-tenant scope from request.state.tenant_id.
            title: Optional session title (e.g. derived from first message).

        Returns:
            Session: ORM instance with id + tenant_id + user_id committed.

        Raises:
            sqlalchemy.exc.IntegrityError: FK violation (user_id missing
                in users table; tenant_id missing in tenants table).
        """
        session = Session(
            id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            title=title,
            status="active",
        )
        self._db.add(session)
        await self._db.flush()
        logger.debug(
            "session_repository.create_session ok",
            extra={
                "session_id": str(session_id),
                "user_id": str(user_id),
                "tenant_id": str(tenant_id),
            },
        )
        return session


__all__ = ["SessionRepository"]
