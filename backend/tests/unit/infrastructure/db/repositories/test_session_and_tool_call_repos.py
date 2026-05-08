"""
File: backend/tests/unit/infrastructure/db/repositories/test_session_and_tool_call_repos.py
Purpose: Unit tests for Sprint 57.7 US-R1 SessionRepository + ToolCallRepository.
Category: Tests / Infrastructure / Repositories (Sprint 57.7 US-R1)
Scope: Phase 57 / Sprint 57.7 Day 3 Tier 2

Description:
    6 unit tests covering both repos with mocked AsyncSession (no real DB):

    SessionRepository:
    1. create_session INSERTs Session with given session_id + user_id + tenant_id
    2. create_session with title sets the title field

    ToolCallRepository:
    3. create INSERTs ToolCall with session_id + tenant_id + tool_name + arguments
    4. create with duration_ms persists wall-clock duration
    5. create with pending status defers duration_ms

    Cross-cutting:
    6. Both repos call db.add + await db.flush exactly once (transaction discipline)

    Tests intentionally use AsyncMock to verify CALL CONTRACT (no real DB),
    matching test_oidc.py pattern. Integration tests for FK violations +
    SAVEPOINT isolation deferred Phase 58+ (real Postgres).

Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 2)
Last Modified: 2026-05-10

Modification History:
    - 2026-05-10: Initial creation (Sprint 57.7 US-R1 — AD-Reality-3a/3b)

Related:
    - infrastructure/db/repositories/session_repository.py
    - infrastructure/db/repositories/tool_call_repository.py
    - api/v1/chat/router.py (consumer)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from infrastructure.db.models.sessions import Session
from infrastructure.db.models.tools import ToolCall
from infrastructure.db.repositories import SessionRepository, ToolCallRepository

# =====================================================================
# SessionRepository tests
# =====================================================================


class TestSessionRepository:
    @pytest.mark.asyncio
    async def test_create_session_inserts_row(self) -> None:
        """1. create_session calls db.add + flush with Session keyed correctly."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        repo = SessionRepository(mock_db)
        session_id = uuid4()
        user_id = uuid4()
        tenant_id = uuid4()

        result = await repo.create_session(
            session_id=session_id, user_id=user_id, tenant_id=tenant_id
        )

        assert isinstance(result, Session)
        assert result.id == session_id
        assert result.user_id == user_id
        assert result.tenant_id == tenant_id
        assert result.status == "active"
        mock_db.add.assert_called_once_with(result)
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_session_with_title(self) -> None:
        """2. create_session sets title when provided."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        repo = SessionRepository(mock_db)
        result = await repo.create_session(
            session_id=uuid4(),
            user_id=uuid4(),
            tenant_id=uuid4(),
            title="First chat about pricing",
        )
        assert result.title == "First chat about pricing"


# =====================================================================
# ToolCallRepository tests
# =====================================================================


class TestToolCallRepository:
    @pytest.mark.asyncio
    async def test_create_inserts_completed_call(self) -> None:
        """3. create INSERTs ToolCall with completed status + arguments dict."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        repo = ToolCallRepository(mock_db)
        session_id = uuid4()
        tenant_id = uuid4()
        args = {"query": "SELECT *"}

        result = await repo.create(
            session_id=session_id,
            tenant_id=tenant_id,
            tool_name="incident_query",
            arguments=args,
        )

        assert isinstance(result, ToolCall)
        assert result.session_id == session_id
        assert result.tenant_id == tenant_id
        assert result.tool_name == "incident_query"
        assert result.arguments == args
        assert result.status == "completed"
        assert result.permission_check_passed is True
        mock_db.add.assert_called_once_with(result)
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_with_duration_ms(self) -> None:
        """4. create persists duration_ms when supplied."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        repo = ToolCallRepository(mock_db)
        result = await repo.create(
            session_id=uuid4(),
            tenant_id=uuid4(),
            tool_name="echo_tool",
            arguments={"text": "hi"},
            duration_ms=42,
        )
        assert result.duration_ms == 42

    @pytest.mark.asyncio
    async def test_create_with_pending_status_no_duration(self) -> None:
        """5. create with pending status leaves duration_ms None (running tool)."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        repo = ToolCallRepository(mock_db)
        result = await repo.create(
            session_id=uuid4(),
            tenant_id=uuid4(),
            tool_name="long_running",
            arguments={},
            status="pending",
        )
        assert result.status == "pending"
        assert result.duration_ms is None

    @pytest.mark.asyncio
    async def test_create_with_permission_denied(self) -> None:
        """6. create persists permission_check_passed=False (Cat 9 guardrail block)."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        repo = ToolCallRepository(mock_db)
        result = await repo.create(
            session_id=uuid4(),
            tenant_id=uuid4(),
            tool_name="dangerous_tool",
            arguments={},
            status="failed",
            permission_check_passed=False,
        )
        assert result.permission_check_passed is False
        assert result.status == "failed"
