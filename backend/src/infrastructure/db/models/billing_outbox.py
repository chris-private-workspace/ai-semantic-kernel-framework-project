"""
File: backend/src/infrastructure/db/models/billing_outbox.py
Purpose: BillingOutboxEvent ORM — transactional outbox for durable, idempotent cost events.
Category: Infrastructure / ORM (platform_layer.billing — C-15 billing-write-atomicity)
Scope: Sprint 57.84 / US-1 + US-2

Description:
    Transactional-outbox row capturing a chargeable LLM/tool event. The chat
    request observer enqueues one row PER chargeable event in the SAME request
    transaction (atomic with session/audit writes) instead of writing
    cost_ledger best-effort. A background drainer (BillingOutboxDrainer) then
    materializes cost_ledger from `payload` idempotently, so a ledger-write
    flake can no longer silently drop a charge (漏扣) and a retry/replay never
    double-charges (雙扣).

    `payload` carries the LLM-provider-neutral args of the existing
    CostLedgerService.record_llm_call / record_tool_call (provider / model /
    input_tokens / output_tokens / cached_input_tokens / sub_type_suffix /
    tool_name / session_id) — pricing stays single-source in CostLedgerService
    (C-11 / Sprint 57.79 unchanged). No SDK import (neutrality).

    Idempotency: UNIQUE(tenant_id, idempotency_key) — a redelivered event is a
    no-op enqueue; the drain claims + materializes + marks done in one txn so a
    crash mid-row re-claims rather than double-charges.

Key Components:
    - OutboxStatus / OutboxEventType: enum mirrors of the CHECK constraints
    - BillingOutboxEvent: ORM (TenantScopedMixin)

Created: 2026-06-05 (Sprint 57.84)

Modification History:
    - 2026-06-05: Initial creation (Sprint 57.84 / US-1 + US-2)

Related:
    - 09-db-schema-design.md §outbox (notification design — NOT reused; D1)
    - migrations/versions/0025_billing_outbox.py
    - platform_layer/billing/billing_outbox.py (BillingOutboxService + Drainer)
    - platform_layer/billing/cost_ledger.py (drain target — pricing single-source)
    - .claude/rules/multi-tenant-data.md 鐵律 1 (tenant_id NN + RLS)
"""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base, TenantScopedMixin


class OutboxStatus(str, enum.Enum):
    """billing_outbox.status — matches CHECK constraint."""

    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class OutboxEventType(str, enum.Enum):
    """billing_outbox.event_type — matches CHECK constraint."""

    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"


class BillingOutboxEvent(Base, TenantScopedMixin):
    """Transactional outbox row for a durable, idempotent cost event."""

    __tablename__ = "billing_outbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'")
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[PyUUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_billing_outbox_idem",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'done', 'failed')",
            name="ck_billing_outbox_status",
        ),
        CheckConstraint(
            "event_type IN ('llm_call', 'tool_call')",
            name="ck_billing_outbox_event_type",
        ),
        # Drainer claim path: due rows are pending OR failed-and-retry-due.
        Index(
            "idx_billing_outbox_due",
            "next_retry_at",
            postgresql_where=text("status IN ('pending', 'failed')"),
        ),
        Index("idx_billing_outbox_tenant", "tenant_id"),
    )


__all__ = [
    "BillingOutboxEvent",
    "OutboxStatus",
    "OutboxEventType",
]
