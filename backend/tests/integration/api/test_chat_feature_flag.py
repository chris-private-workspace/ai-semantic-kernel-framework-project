"""
File: backend/tests/integration/api/test_chat_feature_flag.py
Purpose: Integration test — chat handler-style FeatureFlagsService lookup with per-tenant override.
Category: Tests / Integration / API (Phase 56 SaaS Stage 1)
Scope: Sprint 56.1 / Day 3 / 1 integration US-4 per checklist 3.6.

Description:
    Simulates how a chat handler will consult FeatureFlagsService:
        1. seed_defaults() seeds the 4 baseline flags
        2. Tenant A overrides thinking_enabled=False
        3. Tenant A's is_enabled('thinking_enabled') returns False
        4. Tenant B's is_enabled('thinking_enabled') still returns True
        5. Audit chain row recorded for the override

    The actual chat handler wiring of feature flags is Phase 56.x carryover
    (the chat router currently doesn't consult FeatureFlagsService). This
    integration test exercises the full DB path that the chat handler will
    eventually use, ensuring the per-tenant override semantics are correct.

Created: 2026-05-06 (Sprint 56.1 Day 3 / US-4)
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.feature_flags import FeatureFlagsService
from infrastructure.db.models.audit import AuditLog
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


async def test_chat_handler_thinking_enabled_per_tenant_override(
    db_session: AsyncSession,
) -> None:
    """Tenant A override=False; Tenant B sees default=True."""
    tenant_a = await seed_tenant(db_session, code="ff-int-a")
    tenant_b = await seed_tenant(db_session, code="ff-int-b")

    svc = FeatureFlagsService(db_session)
    inserted = await svc.seed_defaults()
    assert inserted >= 1  # at least thinking_enabled

    # Default lookup.
    assert await svc.is_enabled("thinking_enabled", tenant_id=tenant_a.id) is True
    assert await svc.is_enabled("thinking_enabled", tenant_id=tenant_b.id) is True

    # Tenant A flips it off.
    await svc.set_tenant_override(
        "thinking_enabled",
        tenant_id=tenant_a.id,
        enabled=False,
        actor_user_id=None,
    )

    # Tenant A now sees False; Tenant B still sees default True.
    assert await svc.is_enabled("thinking_enabled", tenant_id=tenant_a.id) is False
    assert await svc.is_enabled("thinking_enabled", tenant_id=tenant_b.id) is True

    # Audit row exists for tenant A's override.
    audit_rows = (
        (
            await db_session.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == tenant_a.id,
                    AuditLog.operation == "feature_flag_override_set",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    assert audit_rows[0].operation_data["new_value"] is False
    assert audit_rows[0].operation_data["flag_name"] == "thinking_enabled"
