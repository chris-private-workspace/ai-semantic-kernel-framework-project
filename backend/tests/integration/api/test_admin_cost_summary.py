"""
File: backend/tests/integration/api/test_admin_cost_summary.py
Purpose: Integration test — GET /admin/tenants/{tid}/cost-summary endpoint.
Category: Tests / Integration / API (Phase 56 SaaS Stage 1)
Scope: Sprint 56.3 / Day 3 / 1 integration US-3.

Description:
    Admin auth happy path: seed CostLedger entries → call endpoint → assert
    response shape includes by_type breakdown + total_cost_usd > 0.

Created: 2026-05-06 (Sprint 56.3 Day 3)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.cost_summary import router as admin_cost_summary_router
from infrastructure.db.session import get_db_session
from platform_layer.billing.cost_ledger import CostLedgerService
from platform_layer.billing.pricing import PricingLoader, set_pricing_loader
from platform_layer.identity.auth import require_tenant_match_or_platform_admin
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio

_PRICING_YAML = Path(__file__).resolve().parents[3] / "config" / "llm_pricing.yml"


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_cost_summary_router, prefix="/api/v1")

    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        async def _override_admin() -> UUID:
            return UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_tenant_match_or_platform_admin] = _override_admin
    return app


async def test_admin_cost_summary_endpoint_returns_aggregated(
    db_session: AsyncSession,
) -> None:
    """Admin auth → 200 + total_cost_usd > 0 + by_type breakdown."""
    t = await seed_tenant(db_session, code="CS_EP_1")

    pl = PricingLoader()
    pl.load_from_yaml(_PRICING_YAML)
    set_pricing_loader(pl)

    svc = CostLedgerService(db=db_session, pricing_loader=pl)
    # Sprint 57.2: input/output token split (closes AD-Cost-Ledger-Token-Split).
    await svc.record_llm_call(
        tenant_id=t.id,
        provider="azure_openai",
        model="gpt-5.4",
        input_tokens=600,
        output_tokens=400,
    )
    await svc.record_tool_call(tenant_id=t.id, tool_name="salesforce_query")
    await db_session.flush()

    # Compute month from the latest entry to align with DB timestamp.
    from sqlalchemy import select

    from infrastructure.db.models.cost_ledger import CostLedger as CL

    most_recent = (
        await db_session.execute(
            select(CL.recorded_at)
            .where(CL.tenant_id == t.id)
            .order_by(CL.recorded_at.desc())
            .limit(1)
        )
    ).scalar_one()
    month = most_recent.strftime("%Y-%m")

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/v1/admin/tenants/{t.id}/cost-summary?month={month}",
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenant_id"] == str(t.id)
    assert body["month"] == month
    assert Decimal(str(body["total_cost_usd"])) > 0
    assert "llm" in body["by_type"]
    assert "tool" in body["by_type"]
    # Sprint 57.2: split sub_types replace combined "_total".
    assert "azure_openai_gpt-5.4_input" in body["by_type"]["llm"]
    assert "azure_openai_gpt-5.4_output" in body["by_type"]["llm"]
    assert "salesforce_query" in body["by_type"]["tool"]
