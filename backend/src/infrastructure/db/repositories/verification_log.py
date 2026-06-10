"""
File: backend/src/infrastructure/db/repositories/verification_log.py
Purpose: VerificationLogRepository — DAO for verification_log table (Cat 10 persistence).
Category: Infrastructure / Repositories (Sprint 57.11 US-1)
Scope: Phase 57 / Sprint 57.11 Day 1

Description:
    DAO encapsulating verification_log INSERT + paginated SELECT operations
    consumed by:
        - the in-loop Cat 10 gate's persist hook (verification/persistence.py,
          US-2 §1.6) — best-effort INSERT after every VerificationPassed /
          VerificationFailed yield
        - GET /api/v1/verification/recent (US-2 §1.5) — paginated list with
          session_id / verifier_type / passed filters
        - GET /api/v1/verification/{session_id}/correction-trace (US-2 §1.5)
          — chronologically-sorted full trace for one session

    All queries auto-scope by tenant_id via the WHERE clause; RLS at storage
    layer is the secondary defense (per multi-tenant 鐵律 + plan §US-1).

Created: 2026-05-10 (Sprint 57.11 Day 1 / US-1)

Modification History (newest-first):
    - 2026-05-10: Initial creation (Sprint 57.11 Day 1 / US-1)

Related:
    - infrastructure/db/models/verification_log.py (VerificationLog ORM)
    - api/v1/verification.py (REST consumer)
    - agent_harness/verification/persistence.py (write hook)
    - tests/integration/api/test_verification.py
    - tests/unit/agent_harness/verification/test_inloop_gate_persist.py
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.verification_log import VerificationLog

logger = logging.getLogger(__name__)


class VerificationLogRepository:
    """DAO for verification_log table — Cat 10 verifier execution persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def insert(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        turn_index: int,
        verifier_name: str,
        verifier_type: str,
        passed: bool,
        score: float | None,
        reason: str | None,
        suggested_correction: str | None,
        correction_attempt: int,
    ) -> int:
        """INSERT one verification_log row.

        Caller responsible for transaction lifecycle (commit / rollback).
        Returns the BIGSERIAL id post-flush.

        Args:
            tenant_id: Multi-tenant scope (required NN per TenantScopedMixin).
            session_id: Chat session UUID this verification ran under.
            turn_index: Agent loop turn index (0 = first turn).
            verifier_name: Verifier instance identifier.
            verifier_type: Verifier kind — must match ck_verification_log_verifier_type.
            passed: Verifier outcome.
            score: Optional numeric score.
            reason: Failure reason (typically populated when passed=False).
            suggested_correction: Correction guidance for next agent_loop run.
            correction_attempt: Attempt counter (0 first, 1+ post-correction).

        Returns:
            int: Inserted id (BIGSERIAL).
        """
        row = VerificationLog(
            tenant_id=tenant_id,
            session_id=session_id,
            turn_index=turn_index,
            verifier_name=verifier_name,
            verifier_type=verifier_type,
            passed=passed,
            score=score,
            reason=reason,
            suggested_correction=suggested_correction,
            correction_attempt=correction_attempt,
        )
        self._db.add(row)
        await self._db.flush()
        logger.debug(
            "verification_log_repository.insert ok",
            extra={
                "tenant_id": str(tenant_id),
                "session_id": str(session_id),
                "verifier_name": verifier_name,
                "passed": passed,
                "verification_log_id": row.id,
            },
        )
        return row.id

    async def list_recent(
        self,
        *,
        tenant_id: UUID,
        session_id_filter: UUID | None = None,
        verifier_type_filter: str | None = None,
        passed_filter: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[VerificationLog], int, bool]:
        """Paginated list of verification log entries.

        Args:
            tenant_id: Multi-tenant scope.
            session_id_filter: Optional — narrow to one session.
            verifier_type_filter: Optional — narrow to one verifier kind.
            passed_filter: Optional — True/False filter on outcome.
            limit: Max items returned (page size).
            offset: Skip count (cursor).

        Returns:
            Tuple of (items, total, has_more):
                items: VerificationLog rows ordered created_at DESC, id DESC
                total: COUNT(*) matching filters (for UI total display)
                has_more: True if offset+limit < total
        """
        base = select(VerificationLog).where(VerificationLog.tenant_id == tenant_id)
        if session_id_filter is not None:
            base = base.where(VerificationLog.session_id == session_id_filter)
        if verifier_type_filter is not None:
            base = base.where(VerificationLog.verifier_type == verifier_type_filter)
        if passed_filter is not None:
            base = base.where(VerificationLog.passed == passed_filter)

        total_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._db.execute(total_stmt)).scalar_one()

        page_stmt = (
            base.order_by(
                VerificationLog.created_at.desc(),
                VerificationLog.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        items = list((await self._db.execute(page_stmt)).scalars().all())
        has_more = offset + len(items) < total
        return items, total, has_more

    async def list_correction_trace(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
    ) -> list[VerificationLog]:
        """Full sorted trace of verifications for one session.

        Sort: turn_index ASC, correction_attempt ASC, created_at ASC, id ASC.
        UI consumption: chat-v2 inline `<VerificationPanel />` (US-5) +
        admin `/verification` page detail drill-down (US-4).

        Args:
            tenant_id: Multi-tenant scope.
            session_id: Chat session UUID.

        Returns:
            list[VerificationLog]: All entries for the session, sorted
            chronologically + by attempt.
        """
        stmt = (
            select(VerificationLog)
            .where(
                VerificationLog.tenant_id == tenant_id,
                VerificationLog.session_id == session_id,
            )
            .order_by(
                VerificationLog.turn_index.asc(),
                VerificationLog.correction_attempt.asc(),
                VerificationLog.created_at.asc(),
                VerificationLog.id.asc(),
            )
        )
        rows = list((await self._db.execute(stmt)).scalars().all())
        return rows


__all__ = ["VerificationLogRepository"]
