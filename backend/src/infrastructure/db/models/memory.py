"""
File: backend/src/infrastructure/db/models/memory.py
Purpose: 5-layer memory ORM (system / tenant / role / user / session_summary).
Category: Infrastructure / ORM (Memory group, 範疇 3 schema layer)
Scope: Sprint 49.3 (Day 2.3 - 5 memory tables)
Owner: infrastructure/db owner

Description:
    5-layer memory schema per 09-db-schema-design.md L383-498. Phase 51.2
    (範疇 3 Memory) consumes these tables; 49.3 only ships the schema.

    Layer / scope summary:
        Layer 1  memory_system           — Global system rules / policies (NO tenant_id)
        Layer 2  memory_tenant           — Tenant-level knowledge (TenantScopedMixin)
        Layer 3  memory_role             — Role-level (FK role_id; tenant via role chain)
        Layer 4  memory_user             — User-level (TenantScopedMixin + user_id;
                                            denormalised tenant for query speed)
        Layer 5  memory_session_summary  — Per-session (FK session_id UNIQUE; tenant via session)

    Tenant rule alignment (.claude/rules/multi-tenant-data.md 鐵律 1):
        TenantScopedMixin direct: memory_tenant, memory_user
        Junction (tenant via FK chain, no direct column): memory_role, memory_session_summary
        Global (intentionally no tenant): memory_system

        memory_role + memory_session_summary follow the same junction
        pattern that 49.2 used for user_roles / role_permissions /
        tool_results — tenant resolved via the FK chain when querying.

    Vector embeddings (vector_id columns) reference Qdrant payload IDs;
    Sprint 49.3 Day 5.1 ships the QdrantNamespaceStrategy abstraction
    (no client integration; that lands in Phase 51.2).

Created: 2026-04-29 (Sprint 49.3 Day 2.3)
Last Modified: 2026-06-30

Modification History:
    - 2026-06-30: Sprint 57.150 — add dedup_key + uq_memory_user_dedup (write-side upsert)
    - 2026-06-04: Sprint 57.76 — add MemoryOp (append-only memory_ops ops log)
    - 2026-04-29: Initial creation (Sprint 49.3 Day 2.3)

Related:
    - 09-db-schema-design.md Group 3 Memory (L383-498)
    - 17-cross-category-interfaces.md §範疇 3 contracts
    - .claude/rules/multi-tenant-data.md 鐵律 1 (junction-table exemptions)
    - sprint-49-3-plan.md §Story 49.3-4
    - infrastructure/vector/qdrant_namespace.py (Day 5.1)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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


# ============================================================================
# Layer 1 — memory_system  (global, no tenant_id)
# ============================================================================
class MemorySystem(Base):
    """Global system rules / policies. Per 09.md L386-400."""

    __tablename__ = "memory_system"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    key: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="safety / policy / compliance",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# Layer 2 — memory_tenant  (TenantScopedMixin)
# ============================================================================
class MemoryTenant(Base, TenantScopedMixin):
    """Tenant-level knowledge / playbooks. Per 09.md L405-426."""

    __tablename__ = "memory_tenant"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    key: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="playbook / domain_knowledge",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vector_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="Qdrant payload reference; populated by Phase 51.2 ingestion.",
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_memory_tenant_key"),
        # NOTE: TenantScopedMixin already provides ix_memory_tenant_tenant_id;
        # 09.md L424's idx_memory_tenant_tenant is satisfied by that.
        Index("idx_memory_tenant_category", "tenant_id", "category"),
    )


# ============================================================================
# Layer 3 — memory_role  (junction via role_id; no direct tenant_id)
# ============================================================================
class MemoryRole(Base):
    """Role-level memory. Per 09.md L432-447.

    Junction-style table: tenant is resolved via role_id → roles.tenant_id
    chain. Same pattern as user_roles / role_permissions in Sprint 49.2.
    """

    __tablename__ = "memory_role"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    role_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="workflow / approval_rule",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("role_id", "key", name="uq_memory_role_key"),
        Index("idx_memory_role_role", "role_id"),
    )


# ============================================================================
# Layer 4 — memory_user  (TenantScopedMixin + user_id, denormalised)
# ============================================================================
class MemoryUser(Base, TenantScopedMixin):
    """User-level memory (preferences / facts / past decisions). Per 09.md L453-479."""

    __tablename__ = "memory_user"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="preference / fact / decision",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vector_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Write-side dedup key: md5(normalize(content)). The (tenant_id, user_id,
    # dedup_key) unique constraint makes UserLayer.write an idempotent upsert so a
    # repeated durable fact UPDATEs one row instead of accumulating duplicates that
    # dilute profile() top-k (Sprint 57.150 — closes AD-Memory-User-Upsert-By-Key).
    dedup_key: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        doc="md5(normalize(content)) — write-side dedup conflict key (Sprint 57.150)",
    )

    # Provenance
    source: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="extracted / manual / system",
    )
    source_session_id: Mapped[PyUUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=True,
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # Write-side dedup conflict target (Sprint 57.150). Nullable dedup_key →
        # PG permits multiple NULLs; UserLayer.write always sets it.
        UniqueConstraint("tenant_id", "user_id", "dedup_key", name="uq_memory_user_dedup"),
        Index("idx_memory_user_user", "user_id"),
        Index("idx_memory_user_category", "user_id", "category"),
        Index(
            "idx_memory_user_expires",
            "expires_at",
            postgresql_where=text("expires_at IS NOT NULL"),
        ),
    )


# ============================================================================
# Layer 5 — memory_session_summary  (junction via session_id; UNIQUE)
# ============================================================================
class MemorySessionSummary(Base):
    """Per-session post-conversation summary. Per 09.md L485-498.

    Junction-style table: tenant resolved via session_id → sessions.tenant_id.
    UNIQUE on session_id ensures at most one summary per session.
    """

    __tablename__ = "memory_session_summary"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_decisions: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    unresolved_issues: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    extracted_to_user_memory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    extraction_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# memory_ops  (append-only ops log; TenantScopedMixin)  — Sprint 57.76
# ============================================================================
# Why a dedicated table (not audit_log): the memory page's RecentOps +
# TimeTravel widgets need a value snapshot per op (Option B per user 2026-06-03).
# audit_log (Option A) carries no value snapshot and serialises per-tenant via a
# hash chain; an ops log is append-only WITHOUT a chain (not tamper-evident audit
# — see plan §0 D-DAY0-6) so it avoids that write-serialisation cost. Each
# DB-backed layer's write/evict inserts a row in the SAME transaction (Risk C).
class MemoryOp(Base, TenantScopedMixin):
    """Append-only record of a memory write/evict (user / tenant / role layers).

    Populated by the layer write/evict paths via _record_memory_op() in the
    layer's own session/transaction. Read back by GET /memory/ops (time-ordered
    DESC per tenant). No UPDATE path; no hash-chain.
    """

    __tablename__ = "memory_ops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # tenant_id provided by TenantScopedMixin (NOT NULL + FK CASCADE + index)
    user_id: Mapped[PyUUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
        doc="Set for user-layer ops; NULL for tenant/role-layer ops.",
    )
    scope: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Memory layer that produced the op: user / tenant / role.",
    )
    key: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        doc="Memory key / category touched by the op (NULL when not applicable).",
    )
    operation: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="WRITE / EVICT.",
    )
    time_scale: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        doc="short_term / long_term / semantic (NULL when not applicable).",
    )
    value_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Content written (WRITE) or old content removed (EVICT).",
    )
    actor: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="Who triggered the op: user_id str or 'system'.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # Read path is time-ordered DESC per tenant.
        Index("idx_memory_ops_tenant_created", "tenant_id", text("created_at DESC")),
    )


__all__ = [
    "MemorySystem",
    "MemoryTenant",
    "MemoryRole",
    "MemoryUser",
    "MemorySessionSummary",
    "MemoryOp",
]
