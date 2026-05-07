"""
File: backend/tests/integration/api/test_governance_endpoints.py
Purpose: Integration tests for GET /api/v1/governance/approvals + POST /decide.
Category: Tests / Integration / API / Governance
Scope: Phase 53 / Sprint 53.5 US-1

Description:
    Mounts the governance router on a minimal FastAPI app and overrides
    identity deps with synthetic tenant/user. Verifies:

    - RBAC: non-approver → 403; approver / admin / manager → 200
    - Tenant isolation: tenant A cannot see / decide tenant B approvals
    - List returns ApprovalSummaryDTO shape with all required fields
    - Decide: APPROVED / REJECTED / ESCALATED happy path
    - Decide: cross-tenant request_id → 404
    - Decide: nonexistent request_id → 404
    - Decide: invalid decision label → 422

Created: 2026-05-04 (Sprint 53.5 Day 3)

Modification History:
    - 2026-05-04: Initial creation (Sprint 53.5 US-1)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.governance import router as governance_router
from infrastructure.db.models import Approval, Session, Tenant, User
from platform_layer.governance.hitl.state_machine import ApprovalState
from platform_layer.identity.auth import (
    get_current_tenant,
    require_approver_role,
)
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_session(
    db: AsyncSession, tenant: Tenant, user: User, *, title: str = "test-session"
) -> Session:
    sess = Session(tenant_id=tenant.id, user_id=user.id, title=title)
    db.add(sess)
    await db.flush()
    await db.refresh(sess)
    return sess


async def _seed_pending_approval(
    db: AsyncSession,
    *,
    session_id: UUID,
    tool_name: str = "sensitive_tool",
    risk_level: str = "high",
) -> Approval:
    """Insert a PENDING approval row tied to an existing session."""
    request_id = uuid4()
    row = Approval(
        id=request_id,
        session_id=session_id,
        action_type="guardrails",
        action_summary=f"approve tool call: {tool_name}",
        action_payload={
            "tool_name": tool_name,
            "tool_arguments": {"x": 1},
            "reason": "policy escalation",
            "summary": f"approve tool call: {tool_name}",
        },
        risk_level=risk_level,
        status=ApprovalState.PENDING.value,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


def _build_app(
    *,
    tenant_id: UUID,
    approver_user_id: UUID | None,
) -> FastAPI:
    """Build a FastAPI app with governance router and overridden identity deps.

    approver_user_id=None simulates non-approver role rejection (403);
    a UUID grants approver access.
    """
    app = FastAPI()
    app.include_router(governance_router, prefix="/api/v1")

    async def _override_tenant() -> UUID:
        return tenant_id

    async def _override_approver_role() -> UUID:
        if approver_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Approver role required",
            )
        return approver_user_id

    app.dependency_overrides[get_current_tenant] = _override_tenant
    app.dependency_overrides[require_approver_role] = _override_approver_role
    return app


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# /governance/approvals — list
# ---------------------------------------------------------------------------


async def test_list_rejects_non_approver_role(db_session: AsyncSession) -> None:
    """Non-approver → 403."""
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_LIST403_{suffix}")
    app = _build_app(tenant_id=tenant.id, approver_user_id=None)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/governance/approvals")
    assert resp.status_code == 403
    assert "Approver role required" in resp.json()["detail"]


async def test_list_returns_pending_for_tenant(db_session: AsyncSession) -> None:
    """Approver sees own-tenant pending; cross-tenant pending invisible."""
    suffix = uuid4().hex[:6]
    tenant_a = await seed_tenant(db_session, code=f"GV_LA_{suffix}")
    tenant_b = await seed_tenant(db_session, code=f"GV_LB_{suffix}")
    user_a = await seed_user(db_session, tenant_a, email=f"a_{suffix}@gv.com")
    user_b = await seed_user(db_session, tenant_b, email=f"b_{suffix}@gv.com")
    sess_a = await _seed_session(db_session, tenant_a, user_a)
    sess_b = await _seed_session(db_session, tenant_b, user_b)
    await _seed_pending_approval(db_session, session_id=sess_a.id, tool_name="tool_A1")
    await _seed_pending_approval(db_session, session_id=sess_a.id, tool_name="tool_A2")
    await _seed_pending_approval(db_session, session_id=sess_b.id, tool_name="tool_B1")
    await db_session.commit()

    app = _build_app(tenant_id=tenant_a.id, approver_user_id=user_a.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/governance/approvals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    tool_names = {item["payload"]["tool_name"] for item in body["items"]}
    assert tool_names == {"tool_A1", "tool_A2"}


async def test_list_returns_dto_shape(db_session: AsyncSession) -> None:
    """ApprovalSummaryDTO must expose all reviewer-UI fields."""
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_DTO_{suffix}")
    user = await seed_user(db_session, tenant, email=f"dto_{suffix}@gv.com")
    sess = await _seed_session(db_session, tenant, user)
    await _seed_pending_approval(db_session, session_id=sess.id)
    await db_session.commit()

    app = _build_app(tenant_id=tenant.id, approver_user_id=user.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/governance/approvals")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    expected = {
        "request_id",
        "tenant_id",
        "session_id",
        "requester",
        "risk_level",
        "payload",
        "sla_deadline",
        "context_snapshot",
    }
    assert expected.issubset(item.keys())
    assert item["risk_level"] == "HIGH"
    assert item["requester"] == "guardrails"


async def test_list_empty_when_no_pending(db_session: AsyncSession) -> None:
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_EMPTY_{suffix}")
    user = await seed_user(db_session, tenant, email=f"empty_{suffix}@gv.com")
    app = _build_app(tenant_id=tenant.id, approver_user_id=user.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/governance/approvals")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "count": 0}


# ---------------------------------------------------------------------------
# /governance/approvals/{id}/decide
# ---------------------------------------------------------------------------


async def test_decide_rejects_non_approver_role(db_session: AsyncSession) -> None:
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_DC403_{suffix}")
    app = _build_app(tenant_id=tenant.id, approver_user_id=None)
    async with await _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/governance/approvals/{uuid4()}/decide",
            json={"decision": "approved"},
        )
    assert resp.status_code == 403


async def test_decide_approves_pending_request(db_session: AsyncSession) -> None:
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_APP_{suffix}")
    user = await seed_user(db_session, tenant, email=f"app_{suffix}@gv.com")
    sess = await _seed_session(db_session, tenant, user)
    approval = await _seed_pending_approval(db_session, session_id=sess.id)
    await db_session.commit()

    app = _build_app(tenant_id=tenant.id, approver_user_id=user.id)
    async with await _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/governance/approvals/{approval.id}/decide",
            json={"decision": "approved", "reason": "test approve"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "APPROVED"
    assert body["reviewer"] == str(user.id)


async def test_decide_rejects_pending_request(db_session: AsyncSession) -> None:
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_REJ_{suffix}")
    user = await seed_user(db_session, tenant, email=f"rej_{suffix}@gv.com")
    sess = await _seed_session(db_session, tenant, user)
    approval = await _seed_pending_approval(db_session, session_id=sess.id)
    await db_session.commit()

    app = _build_app(tenant_id=tenant.id, approver_user_id=user.id)
    async with await _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/governance/approvals/{approval.id}/decide",
            json={"decision": "rejected", "reason": "policy violation"},
        )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "REJECTED"


async def test_decide_escalates_pending_request(db_session: AsyncSession) -> None:
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_ESC_{suffix}")
    user = await seed_user(db_session, tenant, email=f"esc_{suffix}@gv.com")
    sess = await _seed_session(db_session, tenant, user)
    approval = await _seed_pending_approval(db_session, session_id=sess.id)
    await db_session.commit()

    app = _build_app(tenant_id=tenant.id, approver_user_id=user.id)
    async with await _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/governance/approvals/{approval.id}/decide",
            json={"decision": "escalated"},
        )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "ESCALATED"


async def test_decide_cross_tenant_returns_404(db_session: AsyncSession) -> None:
    """Tenant A reviewer cannot decide tenant B's pending → 404."""
    suffix = uuid4().hex[:6]
    tenant_a = await seed_tenant(db_session, code=f"GV_CTA_{suffix}")
    tenant_b = await seed_tenant(db_session, code=f"GV_CTB_{suffix}")
    user_a = await seed_user(db_session, tenant_a, email=f"cta_{suffix}@gv.com")
    user_b = await seed_user(db_session, tenant_b, email=f"ctb_{suffix}@gv.com")
    sess_b = await _seed_session(db_session, tenant_b, user_b)
    approval_b = await _seed_pending_approval(db_session, session_id=sess_b.id)
    await db_session.commit()

    app = _build_app(tenant_id=tenant_a.id, approver_user_id=user_a.id)
    async with await _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/governance/approvals/{approval_b.id}/decide",
            json={"decision": "approved"},
        )
    assert resp.status_code == 404


async def test_decide_nonexistent_returns_404(db_session: AsyncSession) -> None:
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_NX_{suffix}")
    user = await seed_user(db_session, tenant, email=f"nx_{suffix}@gv.com")
    app = _build_app(tenant_id=tenant.id, approver_user_id=user.id)
    async with await _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/governance/approvals/{uuid4()}/decide",
            json={"decision": "approved"},
        )
    assert resp.status_code == 404


async def test_decide_invalid_decision_returns_422(db_session: AsyncSession) -> None:
    """Pydantic Literal validation rejects unknown decision strings."""
    suffix = uuid4().hex[:6]
    tenant = await seed_tenant(db_session, code=f"GV_INV_{suffix}")
    user = await seed_user(db_session, tenant, email=f"inv_{suffix}@gv.com")
    app = _build_app(tenant_id=tenant.id, approver_user_id=user.id)
    async with await _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/governance/approvals/{uuid4()}/decide",
            json={"decision": "MAYBE"},
        )
    assert resp.status_code == 422
