"""
File: backend/tests/integration/api/test_admin_tenant_harness_policy.py
Purpose: Integration tests — PUT/GET /admin/tenants/{id}/harness-policy (Sprint 57.106 C3).
Category: Tests / Integration / API (config tiering)
Scope: Sprint 57.106 (C3 — per-tenant harness policy admin write/read)

Description:
    Verifies the harness-policy admin endpoints:
    - PUT: 401/403 without admin, 404 missing/cross-tenant, 422 unknown field
      (extra=forbid) + 422 unknown template / bad-or-oversize regex / bad mode,
      200 persists to meta_data["harness_policy"] + composite-replace + []-off
      override + audit chain + multi-tenant isolation
    - GET: 404 missing, 200 stored overrides (sparse), empty when unset

Created: 2026-06-12 (Sprint 57.106 C3)

Modification History (newest-first):
    - 2026-06-12: Initial creation (Sprint 57.106 C3)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.audit import AuditLog
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_tenants_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        roles_header = request.headers.get("X-Test-Roles")
        tenant_header = request.headers.get("X-Test-Tenant")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        request.state.tenant_id = UUID(tenant_header) if tenant_header else None
        return await call_next(request)

    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        async def _override_admin() -> UUID:
            return UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_admin_platform_role] = _override_admin

    return app


async def _seed_tenant(session: AsyncSession, *, code: str) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=TenantState.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


def _unique_code() -> str:
    """Unique tenant code to survive committed-row leakage (conftest sweeps HARNESSPOL_PUT_%)."""
    return f"HARNESSPOL_PUT_{uuid4().hex[:8]}"


_BASE_URL = "http://test"


# === PUT: auth + 404 ===========================================================


async def test_put_requires_admin_role() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{uuid4()}/harness-policy",
            json={"escalate_tools": ["x"]},
        )
    assert resp.status_code in (401, 403)


async def test_put_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{uuid4()}/harness-policy",
            json={"escalate_tools": ["x"]},
        )
    assert resp.status_code == 404


# === PUT: persistence + composite-replace + []-off override =====================


async def test_put_creates_policy(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload = {
        "escalate_tools": ["mock_patrol_check_servers"],
        "verification_mode": "disabled",
        "risky_action_enabled": False,
    }
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(f"/api/v1/admin/tenants/{tenant.id}/harness-policy", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["escalate_tools"] == ["mock_patrol_check_servers"]
    assert body["verification_mode"] == "disabled"
    assert body["risky_action_enabled"] is False
    assert body["escalate_input_phrases"] is None

    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert row.meta_data["harness_policy"] == payload


async def test_put_empty_list_is_off_override(db_session: AsyncSession) -> None:
    """escalate_tools=[] is a real OFF override (kept), not a clear."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"escalate_tools": []},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["escalate_tools"] == []
    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert row.meta_data["harness_policy"] == {"escalate_tools": []}


async def test_put_composite_replace(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        first = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"escalate_tools": ["a"], "verification_mode": "disabled"},
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"escalate_tools": ["b"]},
        )
    assert first.status_code == 200 and second.status_code == 200
    body = second.json()
    assert body["escalate_tools"] == ["b"]
    assert body["verification_mode"] is None  # cleared


async def test_put_empty_clears_policy(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"escalate_tools": ["x"]},
        )
        clear = await ac.put(f"/api/v1/admin/tenants/{tenant.id}/harness-policy", json={})
    assert clear.status_code == 200, clear.text
    assert clear.json()["escalate_tools"] is None
    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert "harness_policy" not in (row.meta_data or {})


# === PUT: validation ===========================================================


async def test_put_extra_field_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"escalate_tools": ["x"], "unknown_field": "leak"},
        )
    assert resp.status_code == 422


async def test_put_unknown_template_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"verification_judge_template": "not-a-real-template"},
        )
    assert resp.status_code == 422, resp.text
    assert "not-a-real-template" in resp.text


async def test_put_known_template_accepted(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"verification_judge_template": "safety_review"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["verification_judge_template"] == "safety_review"


async def test_put_bad_regex_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"risky_action_extra_patterns": ["[unclosed"]},
        )
    assert resp.status_code == 422, resp.text


async def test_put_too_many_patterns_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"risky_action_extra_patterns": [f"p{i}" for i in range(21)]},
        )
    assert resp.status_code == 422, resp.text


async def test_put_bad_mode_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"verification_mode": "sometimes"},
        )
    assert resp.status_code == 422, resp.text


async def test_put_bad_failure_policy_rejected(db_session: AsyncSession) -> None:
    """Sprint 57.110 (B4): subagent_failure_policy must be a known literal → 422."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"subagent_failure_policy": "fail_sometimes"},
        )
    assert resp.status_code == 422, resp.text


async def test_put_failure_policy_persists(db_session: AsyncSession) -> None:
    """Sprint 57.110 (B4): a valid failure policy persists + round-trips on GET."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        put_resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"subagent_failure_policy": "fail_fast"},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/harness-policy")
    assert put_resp.status_code == 200, put_resp.text
    assert put_resp.json()["subagent_failure_policy"] == "fail_fast"
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["subagent_failure_policy"] == "fail_fast"
    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert row.meta_data["harness_policy"] == {"subagent_failure_policy": "fail_fast"}


# === PUT: isolation + audit ====================================================


async def test_put_multi_tenant_isolation(db_session: AsyncSession) -> None:
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp_a = await ac.put(
            f"/api/v1/admin/tenants/{tenant_a.id}/harness-policy",
            json={"escalate_tools": ["a-tool"]},
        )
        resp_b = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/harness-policy",
            json={"verification_mode": "disabled"},
        )
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    row_a = (await db_session.execute(select(Tenant).where(Tenant.id == tenant_a.id))).scalar_one()
    row_b = (await db_session.execute(select(Tenant).where(Tenant.id == tenant_b.id))).scalar_one()
    assert row_a.meta_data["harness_policy"] == {"escalate_tools": ["a-tool"]}
    assert row_b.meta_data["harness_policy"] == {"verification_mode": "disabled"}


async def test_put_audit_chain_emitted(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"escalate_tools": ["audit-tool"]},
        )
    assert resp.status_code == 200, resp.text
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant.id)
        .where(AuditLog.operation == "tenant_harness_policy_upsert")
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    audit = entries[0]
    assert audit.resource_type == "tenant"
    assert audit.resource_id == str(tenant.id)
    assert audit.operation_data["policy"] == {"escalate_tools": ["audit-tool"]}
    assert audit.operation_result == "success"


# === GET =======================================================================


async def test_get_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{uuid4()}/harness-policy")
    assert resp.status_code == 404


async def test_get_empty_when_unset(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="HARNESSPOL_GET_UNSET")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/harness-policy")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert all(value is None for value in body.values())


async def test_get_reflects_put(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"escalate_tools": ["t1"], "risky_action_enabled": False},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/harness-policy")
    assert get_resp.status_code == 200, get_resp.text
    body = get_resp.json()
    assert body["escalate_tools"] == ["t1"]
    assert body["risky_action_enabled"] is False


# === handoff governance fields (Sprint 57.107 B3) ==============================


async def test_put_handoff_fields_round_trip(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload = {"handoff_enabled": True, "handoff_target_allowlist": ["planner", "reviewer"]}
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(f"/api/v1/admin/tenants/{tenant.id}/harness-policy", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["handoff_enabled"] is True
    assert body["handoff_target_allowlist"] == ["planner", "reviewer"]

    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert row.meta_data["harness_policy"] == payload


async def test_put_handoff_empty_allowlist_rejected(db_session: AsyncSession) -> None:
    """[] is rejected — disabling handoff is handoff_enabled=false, not allowlist=[]."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"handoff_target_allowlist": []},
        )
    assert resp.status_code == 422
    assert "handoff_enabled=false" in resp.json()["detail"]


async def test_put_handoff_too_many_targets_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"handoff_target_allowlist": [f"agent-{i}" for i in range(21)]},
        )
    assert resp.status_code == 422
    assert "exceeds" in resp.json()["detail"]


async def test_put_handoff_blank_target_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=_BASE_URL) as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/harness-policy",
            json={"handoff_target_allowlist": ["   "]},
        )
    assert resp.status_code == 422
    assert "invalid handoff target" in resp.json()["detail"]
