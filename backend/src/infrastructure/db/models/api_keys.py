"""
File: backend/src/infrastructure/db/models/api_keys.py
Purpose: ApiKey + RateLimit ORM (external API auth + quota tracking).
Category: Infrastructure / ORM (API auth & limits)
Scope: Sprint 49.3 (Day 2.1 - api_keys + rate_limits)
Owner: infrastructure/db owner

Description:
    External-tenant API key management + per-tenant rate limit accounting.

    Schema authority: 09-db-schema-design.md L869-919.

    Why a separate module (not identity.py):
        identity.py owns RBAC (Tenant/User/Role/junctions). API keys and
        rate limits are a distinct concern (external system auth + quota),
        so they live in their own file. The plan called for "extending
        identity.py" — same intent, cleaner separation.

    api_keys notes:
        - key_hash stores bcrypt hash (VARCHAR(128)) — NOT the raw key.
        - key_prefix is the displayable first 8 chars (e.g. "ipa_abcd...")
          for user identification only; never enough to authenticate with.
        - permissions JSONB lists scope strings (e.g. ["read:sessions"]).
        - status transitions: active → revoked / active → expired.
          revoked_at + last_used_at are advisory; status is the source of truth.

    rate_limits notes:
        - Per (tenant, resource_type, window_type, window_start) row.
        - quota / used counter; window_end is informational (= start + window).
        - UNIQUE constraint per the spec ensures idempotent upserts.
        - resource_type / window_type kept as VARCHAR (not enum) for forward
          compatibility; validation lives in service layer.

    rate_limit_configs notes (Sprint 57.59):
        - Per (tenant, resource_type, window_type) durable quota config — the
          window-instance-agnostic config that rate_limits (usage) cannot hold
          because its unique key forces window_start NOT NULL.
        - Replaces the Sprint 57.48-57.58 tenant.meta_data["rate_limits"] JSONB
          ({label, value}) as the config source of truth (AP-4 Potemkin close:
          activates a queryable, RLS-enforced config table).
        - resource_type / window_type kept as VARCHAR (not enum) — same forward-
          compat stance as rate_limits; validation lives in the service layer.

Created: 2026-04-29 (Sprint 49.3 Day 2.1)
Last Modified: 2026-05-28

Modification History:
    - 2026-05-29: Sprint 57.62 — add RateLimitAlert ORM (80%-threshold usage alert log)
    - 2026-05-28: Sprint 57.59 — add RateLimitConfig ORM (config two-table split; AP-4 close)
    - 2026-04-29: Initial creation (Sprint 49.3 Day 2.1)

Related:
    - 09-db-schema-design.md L869-919 (api_keys + rate_limits)
    - 14-security-deep-dive.md (API auth + rate limit hardening)
    - .claude/rules/multi-tenant-data.md 鐵律 1 (TenantScopedMixin)
    - sprint-49-3-plan.md §Story 49.3-3
    - sprint-57-59-plan.md §4.1 (RateLimitConfig two-table split)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base, TenantScopedMixin


class ApiKey(Base, TenantScopedMixin):
    """External tenant API key. Per 09-db-schema-design.md L869-896."""

    __tablename__ = "api_keys"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Human-readable purpose label.",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="Display-only first 8 chars (e.g. 'ipa_abcd'); cannot authenticate with this alone.",
    )
    key_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="bcrypt hash of the full key. Never store the raw key.",
    )

    permissions: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        doc="Scope strings, e.g. ['read:sessions','write:tools'].",
    )
    rate_limit_tier: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'standard'"),
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'active'"),
        doc="active / revoked / expired. Source of truth for usability.",
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[PyUUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        doc="User who minted this key (null for system-created).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # NOTE: TenantScopedMixin already adds ix_api_keys_tenant_id (the
    # idx_api_keys_tenant in 09.md). We add the other two indexes.
    __table_args__ = (
        Index(
            "idx_api_keys_active",
            "status",
            postgresql_where=text("status = 'active'"),
        ),
        Index("idx_api_keys_prefix", "key_prefix"),
    )


class RateLimit(Base, TenantScopedMixin):
    """Per-tenant resource quota window. Per 09-db-schema-design.md L902-919."""

    __tablename__ = "rate_limits"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="llm_tokens / tool_calls / api_requests (validation in service layer).",
    )
    window_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="minute / hour / day / month.",
    )

    quota: Mapped[int] = mapped_column(Integer, nullable=False)
    used: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "resource_type",
            "window_type",
            "window_start",
            name="uq_rate_limits_tenant_window",
        ),
        # 09.md L918 — desc index on window_end for "latest window" lookup.
        Index(
            "idx_rate_limits_lookup",
            "tenant_id",
            "resource_type",
            text("window_end DESC"),
        ),
    )


# === RateLimitConfig: durable per-(tenant,resource,window) quota config ===
# Why: Sprint 57.48-57.58 stored config in tenant.meta_data["rate_limits"] JSONB
# (opaque {label, value} display strings). This normalises it to a queryable,
# RLS-enforced table — separate from the rate_limits usage table, whose unique
# key forces window_start NOT NULL (every row is a live window instance) so it
# cannot hold window-agnostic config. Closes the AP-4 Potemkin on the dormant
# rate_limits subsystem by giving config a real, queried home.
# Alternative considered (C2): a nullable window_start single table — rejected
# for semantic overload (a row is config-or-usage by null-ness); the C1
# two-table split is the cleaner normalisation.
# Reference: sprint-57-59-plan.md §4.1 / 09-db-schema-design.md §rate limits
class RateLimitConfig(Base, TenantScopedMixin):
    """Per-tenant resource quota config (window-agnostic). Sprint 57.59."""

    __tablename__ = "rate_limit_configs"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="api_requests / tool_calls / sse_connections (validation in service layer).",
    )
    window_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="sec / min / hour / day (the display window unit; validation in service layer).",
    )

    quota: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "resource_type",
            "window_type",
            name="uq_rate_limit_configs_tenant_resource_window",
        ),
    )


# === RateLimitAlert: durable 80%-threshold usage alert log =================
# Why: Sprint 57.62 surfaces rate-limit pressure BEFORE tenants hit a hard 429.
# The enforcement point (rate_limit_counter._write_through) records a durable row
# the first time a tenant's usage for a (resource, window) crosses 80% of its
# configured quota, so breaches are captured even when no admin is polling the
# live-usage endpoint. Mirrors the SLAViolation append-only breach log (sla.py):
# lowercase severity + CHECK constraint, but threshold_pct/actual_pct are plain
# int (rate-limit pct is integer-grained — deliberately NOT Numeric).
# The unique (tenant, resource, window, window_start) key makes the alert
# idempotent per window instance: repeated crossings in the same window upsert the
# SAME row (actual_pct = peak, triggered_at = first-crossing time preserved).
# Reference: sprint-57-62-plan.md / 09-db-schema-design.md §rate limits /
#   infrastructure/db/models/sla.py:SLAViolation (alert-log precedent)
class RateLimitAlert(Base, TenantScopedMixin):
    """Per-window rate-limit 80%-threshold breach alert. Sprint 57.62."""

    __tablename__ = "rate_limit_alerts"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="api_requests / tool_calls / sse_connections (validation in service layer).",
    )
    window_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="sec / min / hour / day — same label the rate_limits usage row uses.",
    )

    threshold_pct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="The crossing threshold this row records (currently always 80).",
    )
    actual_pct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Observed usage pct at crossing time; upsert keeps the per-window peak.",
    )
    used: Mapped[int] = mapped_column(Integer, nullable=False)
    quota: Mapped[int] = mapped_column(Integer, nullable=False)

    severity: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="warning (>=80%) / critical (>=100%) — lowercase, mirrors SLAViolation.",
    )

    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "resource_type",
            "window_type",
            "window_start",
            name="uq_rate_limit_alerts_window",
        ),
        CheckConstraint(
            "severity IN ('warning', 'critical')",
            name="ck_rate_limit_alerts_severity",
        ),
        Index(
            "ix_rate_limit_alerts_tenant_recent",
            "tenant_id",
            "triggered_at",
        ),
    )


__all__ = ["ApiKey", "RateLimit", "RateLimitAlert", "RateLimitConfig"]
