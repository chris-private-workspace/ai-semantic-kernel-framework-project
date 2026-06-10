"""
File: backend/src/infrastructure/db/models/verification_log.py
Purpose: VerificationLog ORM — append-only Cat 10 verifier execution audit log.
Category: Infrastructure / ORM (Cat 10 Verification Loops persistence)
Scope: Sprint 57.11 / Day 1 / US-1

Description:
    Append-only ledger of every verifier execution emitted by the in-loop
    Cat 10 gate (`loop.py _cat10_verify_gate`, Sprint 57.98):
        - One row per `VerificationPassed` / `VerificationFailed` LoopEvent
        - Captures verifier identity (name + type), outcome (passed + score),
          failure metadata (reason + suggested_correction), and correction
          attempt counter (0 = first attempt, 1+ = post-correction re-runs)

    Source-of-truth for:
        - GET /api/v1/verification/recent (US-2 list view; Day 4 admin page US-4)
        - GET /api/v1/verification/{session_id}/correction-trace (US-2 trace
          view; Day 3 chat-v2 inline panel US-5)

    BIGSERIAL primary key (matching audit_log pattern at audit.py:77-80) —
    single global sequence acceptable because the table is append-only,
    insert-only from `verification/persistence.py persist_verification_event()`
    write hook, and queried in tenant-scoped time order. RLS enforces tenant
    isolation at storage layer; partitioning may be added later if volume
    requires.

Key Components:
    - VerifierType: enum mirror of CHECK constraint (rules_based / llm_judge / external)
    - VerificationLog: ORM (Base, TenantScopedMixin)

Created: 2026-05-10 (Sprint 57.11 Day 1 / US-1)

Modification History:
    - 2026-05-10: Initial creation (Sprint 57.11 Day 1 / US-1)

Related:
    - sprint-57-11-plan.md §US-1 (12 columns + 3 indexes + RLS)
    - migrations/versions/0017_verification_log.py (Alembic 0017)
    - infrastructure/db/repositories/verification_log.py (DAO)
    - api/v1/verification.py (REST endpoints)
    - agent_harness/verification/persistence.py (persist_verification_event write hook)
    - agent_harness/_contracts/events.py (VerificationPassed / VerificationFailed)
    - .claude/rules/multi-tenant-data.md 鐵律 1 (tenant_id NN + RLS)
    - 01-eleven-categories-spec.md §Cat 10 Verification Loops
"""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base, TenantScopedMixin


class VerifierType(str, enum.Enum):
    """Verifier kind — matches CHECK constraint on verification_log.verifier_type."""

    RULES_BASED = "rules_based"
    LLM_JUDGE = "llm_judge"
    EXTERNAL = "external"


class VerificationLog(Base, TenantScopedMixin):
    """Per-tenant per-verifier append-only execution log."""

    __tablename__ = "verification_log"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        doc="Chat session this verification ran under (no FK; session may be ephemeral).",
    )
    turn_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        doc="Agent loop turn index (0 = first turn).",
    )
    verifier_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Verifier instance identifier (e.g. 'pii_redaction', 'response_quality').",
    )
    verifier_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Verifier kind — see VerifierType enum.",
    )
    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        doc="True iff verifier accepted output; False triggers correction loop.",
    )
    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Optional numeric score (e.g. LLM-judge confidence 0.0-1.0).",
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Failure reason (typically populated when passed=False).",
    )
    suggested_correction: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Correction guidance fed back into next agent_loop run.",
    )
    correction_attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        doc="Attempt counter — 0 for first attempt, 1+ for post-correction re-runs.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "verifier_type IN ('rules_based', 'llm_judge', 'external')",
            name="ck_verification_log_verifier_type",
        ),
        Index(
            "idx_verification_log_tenant_session_created",
            "tenant_id",
            "session_id",
            "created_at",
        ),
        Index(
            "idx_verification_log_tenant_created",
            "tenant_id",
            "created_at",
        ),
        Index(
            "idx_verification_log_tenant_passed_failed",
            "tenant_id",
            "created_at",
            postgresql_where=text("passed = false"),
        ),
    )


__all__ = [
    "VerificationLog",
    "VerifierType",
]
