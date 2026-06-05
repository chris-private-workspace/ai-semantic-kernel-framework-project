"""
infrastructure.db.models — All ORM models registered against `Base.metadata`.

Sprint 49.2 builds these incrementally:
    Day 1.5: identity.py     — Tenant / User / Role / UserRole / RolePermission
    Day 2.1: sessions.py     — Session / Message / MessageEvent
    Day 3.1: tools.py        — ToolRegistry / ToolCall / ToolResult
    Day 4.1: state.py        — StateSnapshot / LoopState

Sprint 49.3 adds:
    Day 1.1: audit.py        — AuditLog (append-only, hash chain)
    Day 2.1: api_keys.py     — ApiKey / RateLimit
    Day 2.3: memory.py       — MemorySystem / MemoryTenant / MemoryRole / MemoryUser / MemorySessionSummary  # noqa: E501
    Day 3.1-3: governance.py — Approval / RiskAssessment / GuardrailEvent

Importing this package registers all ORM tables with Base.metadata, which
the Alembic env.py uses as `target_metadata`.

Per .claude/rules/multi-tenant-data.md 鐵律 1, all session-scoped tables
inherit `TenantScopedMixin` from `infrastructure.db.base`.
"""

from __future__ import annotations

# Sprint 57.70 — AgentCatalog (per-tenant AgentSpec definitions, Cat 11)
from infrastructure.db.models.agent_catalog import AgentCatalog

# Day 2.1 (Sprint 49.3) — API auth + quotas
# Sprint 57.59 — RateLimitConfig (config two-table split; AP-4 close)
# Sprint 57.62 — RateLimitAlert (80%-threshold usage alert log)
from infrastructure.db.models.api_keys import (
    ApiKey,
    RateLimit,
    RateLimitAlert,
    RateLimitConfig,
)

# Day 1.1 (Sprint 49.3) — Audit
from infrastructure.db.models.audit import AuditLog

# Sprint 57.84 — BillingOutboxEvent (transactional outbox; C-15 billing leg)
from infrastructure.db.models.billing_outbox import (
    BillingOutboxEvent,
    OutboxEventType,
    OutboxStatus,
)

# Sprint 55.1 — Business domain (incident production table)
from infrastructure.db.models.business import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
)

# Sprint 56.3 Day 2 — Cost Ledger (US-3)
from infrastructure.db.models.cost_ledger import CostLedger, CostType

# Sprint 56.1 Day 3 — Feature Flags (US-4)
from infrastructure.db.models.feature_flag import FeatureFlag

# Day 3.1-3 (Sprint 49.3) — Governance
from infrastructure.db.models.governance import (
    Approval,
    GuardrailEvent,
    RiskAssessment,
)

# Day 1.5 — Identity
from infrastructure.db.models.identity import (
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
)

# Day 2.3 (Sprint 49.3) — Memory layers
# Sprint 57.76 — MemoryOp (append-only memory_ops ops log)
from infrastructure.db.models.memory import (
    MemoryOp,
    MemoryRole,
    MemorySessionSummary,
    MemorySystem,
    MemoryTenant,
    MemoryUser,
)

# Day 2.1 — Sessions
from infrastructure.db.models.sessions import (
    Message,
    MessageEvent,
    Session,
)

# Sprint 56.3 Day 2 — SLA Monitoring (US-2)
from infrastructure.db.models.sla import (
    SLAMetricType,
    SLAReport,
    SLASeverity,
    SLAViolation,
)

# Day 4.1 — State
from infrastructure.db.models.state import (
    LoopState,
    StateSnapshot,
    append_snapshot,
    compute_state_hash,
)

# Day 3.1 — Tools
from infrastructure.db.models.tools import (
    ToolCall,
    ToolRegistry,
    ToolResult,
)

# Sprint 57.11 Day 1 — Verification Log (US-1)
from infrastructure.db.models.verification_log import (
    VerificationLog,
    VerifierType,
)

__all__ = [
    # Identity
    "Tenant",
    "User",
    "Role",
    "UserRole",
    "RolePermission",
    # Sessions
    "Session",
    "Message",
    "MessageEvent",
    # Tools
    "ToolRegistry",
    "ToolCall",
    "ToolResult",
    # State + helpers
    "StateSnapshot",
    "LoopState",
    "append_snapshot",
    "compute_state_hash",
    # Audit (Sprint 49.3)
    "AuditLog",
    # API auth + quotas (Sprint 49.3)
    "ApiKey",
    "RateLimit",
    # RateLimits config (Sprint 57.59 — config two-table split; AP-4 close)
    "RateLimitConfig",
    # RateLimits alert log (Sprint 57.62 — 80%-threshold usage alert)
    "RateLimitAlert",
    # Memory layers (Sprint 49.3)
    "MemorySystem",
    "MemoryTenant",
    "MemoryRole",
    "MemoryUser",
    "MemorySessionSummary",
    # Memory ops log (Sprint 57.76 — append-only memory_ops)
    "MemoryOp",
    # Governance (Sprint 49.3)
    "Approval",
    "RiskAssessment",
    "GuardrailEvent",
    # Business domain (Sprint 55.1)
    "Incident",
    "IncidentSeverity",
    "IncidentStatus",
    # Feature Flags (Sprint 56.1 Day 3)
    "FeatureFlag",
    # SLA Monitoring (Sprint 56.3 Day 2 — US-2)
    "SLAViolation",
    "SLAReport",
    "SLASeverity",
    "SLAMetricType",
    # Cost Ledger (Sprint 56.3 Day 2 — US-3)
    "CostLedger",
    "CostType",
    # Billing Outbox (Sprint 57.84 — transactional outbox, C-15 billing leg)
    "BillingOutboxEvent",
    "OutboxStatus",
    "OutboxEventType",
    # Verification Log (Sprint 57.11 Day 1 — US-1)
    "VerificationLog",
    "VerifierType",
    # Agent Catalog (Sprint 57.70 — per-tenant AgentSpec definitions, Cat 11)
    "AgentCatalog",
]
