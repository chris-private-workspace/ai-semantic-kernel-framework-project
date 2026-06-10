"""
File: backend/src/agent_harness/verification/persistence.py
Purpose: persist_verification_event — best-effort verification_log INSERT (never raises).
Category: 範疇 10 (Verification Loops)
Scope: Sprint 57.98 A1 (extracted from correction_loop.py for the in-loop gate)

Description:
    Best-effort persistence of a single verifier result to verification_log
    (Sprint 57.11 US-1/US-2). Extracted here so BOTH the legacy wrapper
    (correction_loop.py, retired Sprint 57.98) AND the in-loop verification
    gate (loop.py `_cat10_verify_gate`, Sprint 57.98 A1) share one writer —
    the persistence outlives the wrapper. Never raises: a DB failure logs at
    WARNING and is swallowed so the agent loop event stream is never broken.

Key Components:
    - persist_verification_event(): best-effort INSERT; kill-switch + tenant gate

Created: 2026-06-10 (Sprint 57.98 A1) — extracted verbatim from correction_loop.py
Last Modified: 2026-06-10

Modification History (newest-first):
    - 2026-06-10: Initial extraction (Sprint 57.98 A1) — shared by wrapper + in-loop gate

Related:
    - agent_harness/orchestrator_loop/loop.py — `_cat10_verify_gate` calls this
    - infrastructure/db/repositories/verification_log.py (Sprint 57.11 US-1)
    - core/config.verification_log_persist_enabled (Sprint 57.11 US-2 kill switch)
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text

from core.config import get_settings
from infrastructure.db import get_session_factory
from infrastructure.db.repositories.verification_log import VerificationLogRepository

logger = logging.getLogger(__name__)


async def persist_verification_event(
    *,
    tenant_id: UUID | None,
    session_id: UUID,
    turn_index: int,
    verifier_name: str,
    verifier_type: str,
    passed: bool,
    score: float | None,
    reason: str | None,
    suggested_correction: str | None,
    correction_attempt: int,
) -> None:
    """Best-effort INSERT into verification_log; never raises.

    Skip conditions (return without error):
        - Settings.verification_log_persist_enabled = False (kill switch)
        - tenant_id is None (no multi-tenant context — typically smoke tests
          / unit tests without TraceContext.create_with_tenant; row would
          violate NN constraint anyway)

    DB failure conditions (logged at WARNING, swallowed):
        - Connection / network / timeout
        - RLS / FK / check-constraint violation
        - Any other SQLAlchemy exception

    Per Sprint 57.11 §US-2: persistence must NEVER break the agent loop event stream.
    """
    settings = get_settings()
    if not settings.verification_log_persist_enabled:
        return
    if tenant_id is None:
        logger.debug(
            "verification_log persist skipped — no tenant_id in TraceContext",
            extra={
                "session_id": str(session_id),
                "verifier_name": verifier_name,
            },
        )
        return

    try:
        factory = get_session_factory()
        async with factory() as db:
            # SET LOCAL app.tenant_id so RLS policy permits INSERT.
            await db.execute(
                text("SELECT set_config('app.tenant_id', :tid, true)"),
                {"tid": str(tenant_id)},
            )
            repo = VerificationLogRepository(db)
            await repo.insert(
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
            await db.commit()
    except Exception as exc:
        logger.warning(
            "verification_log persist failed; agent loop continues",
            extra={
                "tenant_id": str(tenant_id),
                "session_id": str(session_id),
                "verifier_name": verifier_name,
                "error": str(exc),
            },
        )
