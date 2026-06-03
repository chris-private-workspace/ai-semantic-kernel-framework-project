"""
File: backend/tests/integration/api/test_admin_tenants_stats.py
Purpose: Integration tests — GET /admin/tenants/stats fleet aggregate (Sprint 57.74).
Category: Tests / Integration / API (Phase 57+ SaaS Frontend)
Scope: Sprint 57.74 / US-1/US-2/US-6 (closes AD-AdminTenants-Stats-Aggregate-Endpoint)

Description:
    Verifies the GET /admin/tenants/stats fleet aggregate endpoint:
    - 403 when role is not admin/platform_admin
    - fleet counts correct (active_tenants / total_seats / agents_deployed)
      via baseline-delta assertions (shared test DB may carry sibling rows)
    - per_tenant map: a tenant with N active agents → agents=N (inactive
      excluded); a session started within 24h → counted in runs24; a session
      started 2 days ago → NOT counted
    - empty/no-data path → zeros + present gapped list

    Mirrors test_admin_tenant_list.py patterns (FastAPI test app with
    X-Test-User / X-Test-Roles middleware + dependency_overrides for
    get_db_session + require_admin_platform_role). The endpoint is read-only
    (no commit), so seeded rows roll back at db_session teardown; no conftest
    cleanup sweep is required (Risk Class C: the suite's get_db_session
    override covers the new endpoint via _build_app).

Created: 2026-06-03 (Sprint 57.74)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.agent_catalog import AgentCatalog
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState, User
from infrastructure.db.models.sessions import Session
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    """Build app with admin tenants router + role middleware + DB override.

    Mirrors test_admin_tenant_list.py._build_app: the DB override + admin
    override are applied together so the new /stats endpoint runs against the
    seeded db_session (Risk Class C — the suite override covers it).
    """
    app = FastAPI()
    app.include_router(admin_tenants_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        roles_header = request.headers.get("X-Test-Roles")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        return await call_next(request)

    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        async def _override_admin() -> UUID:
            return UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_admin_platform_role] = _override_admin

    return app


async def _seed_tenant(
    session: AsyncSession,
    *,
    code: str,
    state: TenantState = TenantState.ACTIVE,
    seats: int = 5,
) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=state,
        plan=TenantPlan.ENTERPRISE,
        seats=seats,
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


async def _seed_user(session: AsyncSession, *, tenant_id: UUID, email: str) -> User:
    u = User(tenant_id=tenant_id, email=email, display_name="Test User")
    session.add(u)
    await session.flush()
    await session.refresh(u)
    return u


async def _seed_agent(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    key: str,
    is_active: bool = True,
) -> AgentCatalog:
    a = AgentCatalog(
        tenant_id=tenant_id,
        key=key,
        name=f"Agent {key}",
        system_prompt="test prompt",
        is_active=is_active,
    )
    session.add(a)
    await session.flush()
    return a


async def _seed_session(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    started_at: datetime,
) -> Session:
    s = Session(tenant_id=tenant_id, user_id=user_id, started_at=started_at)
    session.add(s)
    await session.flush()
    return s


async def _fetch_stats(db_session: AsyncSession) -> dict:
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants/stats")
    assert resp.status_code == 200, resp.text
    return resp.json()


# =====================================================================
# US-6 — auth
# =====================================================================
async def test_stats_403_wrong_role() -> None:
    """tenant_admin role insufficient → 403 (real require_admin_platform_role)."""
    app = _build_app()  # no DB override → real role dep runs
    user_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/admin/tenants/stats",
            headers={
                "X-Test-User": str(user_id),
                "X-Test-Roles": json.dumps(["tenant_admin"]),
            },
        )
    assert resp.status_code == 403


async def test_stats_401_without_auth() -> None:
    """No X-Test-User header → require_admin_platform_role 401."""
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants/stats")
    assert resp.status_code == 401


# =====================================================================
# US-1 — fleet counts (baseline-delta; shared test DB may carry sibling rows)
# =====================================================================
async def test_stats_fleet_counts_correct(db_session: AsyncSession) -> None:
    """Seed 2 ACTIVE + 1 SUSPENDED tenant + active/inactive agents → fleet deltas.

    Uses baseline-delta assertions so the test is independent of any rows
    seeded by sibling fixtures in the shared test DB.
    """
    baseline = await _fetch_stats(db_session)
    base_active = baseline["fleet"]["active_tenants"]
    base_seats = baseline["fleet"]["total_seats"]
    base_agents = baseline["fleet"]["agents_deployed"]

    t1 = await _seed_tenant(db_session, code="STATS_FLEET_A1", state=TenantState.ACTIVE, seats=10)
    t2 = await _seed_tenant(db_session, code="STATS_FLEET_A2", state=TenantState.ACTIVE, seats=7)
    # SUSPENDED tenant: counted in total_seats (sum over all tenants) but NOT
    # in active_tenants.
    await _seed_tenant(db_session, code="STATS_FLEET_S1", state=TenantState.SUSPENDED, seats=3)

    # 2 active agents on t1, 1 inactive on t1, 1 active on t2 → +3 deployed.
    await _seed_agent(db_session, tenant_id=t1.id, key="a1", is_active=True)
    await _seed_agent(db_session, tenant_id=t1.id, key="a2", is_active=True)
    await _seed_agent(db_session, tenant_id=t1.id, key="a3", is_active=False)
    await _seed_agent(db_session, tenant_id=t2.id, key="a1", is_active=True)

    body = await _fetch_stats(db_session)
    fleet = body["fleet"]

    assert fleet["active_tenants"] - base_active == 2
    assert fleet["total_seats"] - base_seats == 10 + 7 + 3
    assert fleet["agents_deployed"] - base_agents == 3
    assert body["gapped"] == ["anomalies", "deltas"]


# =====================================================================
# US-2 — per-tenant map (agents + runs24 window)
# =====================================================================
async def test_stats_per_tenant_map(db_session: AsyncSession) -> None:
    """Per-tenant agents = active-agent count; runs24 = sessions within 24h."""
    t = await _seed_tenant(db_session, code="STATS_PT_T1", state=TenantState.ACTIVE)
    u = await _seed_user(db_session, tenant_id=t.id, email="pt1@test.com")

    # 3 active agents + 1 inactive → agents=3.
    await _seed_agent(db_session, tenant_id=t.id, key="r", is_active=True)
    await _seed_agent(db_session, tenant_id=t.id, key="p", is_active=True)
    await _seed_agent(db_session, tenant_id=t.id, key="w", is_active=True)
    await _seed_agent(db_session, tenant_id=t.id, key="x", is_active=False)

    now = datetime.now(timezone.utc)
    # 2 sessions inside the 24h window → runs24=2.
    await _seed_session(
        db_session, tenant_id=t.id, user_id=u.id, started_at=now - timedelta(hours=1)
    )
    await _seed_session(
        db_session, tenant_id=t.id, user_id=u.id, started_at=now - timedelta(hours=23)
    )
    # 1 session 2 days ago → NOT counted.
    await _seed_session(
        db_session, tenant_id=t.id, user_id=u.id, started_at=now - timedelta(days=2)
    )

    body = await _fetch_stats(db_session)
    by_id = {row["tenant_id"]: row for row in body["per_tenant"]}
    assert str(t.id) in by_id, "seeded tenant should appear in per_tenant map"
    row = by_id[str(t.id)]
    assert row["agents"] == 3
    assert row["runs24"] == 2


async def test_stats_per_tenant_runs_only_excludes_old_sessions(
    db_session: AsyncSession,
) -> None:
    """A tenant with only an out-of-window session is absent from the map.

    No active agents + the only session is older than 24h → the tenant does
    not appear in either GROUP BY → absent from per_tenant (frontend renders
    the subtle "—").
    """
    t = await _seed_tenant(db_session, code="STATS_PT_OLD", state=TenantState.ACTIVE)
    u = await _seed_user(db_session, tenant_id=t.id, email="ptold@test.com")
    now = datetime.now(timezone.utc)
    await _seed_session(
        db_session, tenant_id=t.id, user_id=u.id, started_at=now - timedelta(days=3)
    )

    body = await _fetch_stats(db_session)
    by_id = {row["tenant_id"]: row for row in body["per_tenant"]}
    assert str(t.id) not in by_id


# =====================================================================
# US-1/US-2 — shape + empty-data path
# =====================================================================
async def test_stats_shape_and_zero_floor(db_session: AsyncSession) -> None:
    """Response shape is well-formed; fleet counts are non-negative ints; gapped present.

    Cannot assert all-zeros on a shared test DB, but the response must always
    carry the fleet block (3 int fields), a list per_tenant, and the gapped
    list — and every count is a non-negative int (coalesce floor).
    """
    body = await _fetch_stats(db_session)
    assert set(body.keys()) == {"fleet", "per_tenant", "gapped"}
    fleet = body["fleet"]
    assert set(fleet.keys()) == {"active_tenants", "total_seats", "agents_deployed"}
    for key in ("active_tenants", "total_seats", "agents_deployed"):
        assert isinstance(fleet[key], int)
        assert fleet[key] >= 0
    assert isinstance(body["per_tenant"], list)
    assert body["gapped"] == ["anomalies", "deltas"]
    # Every per_tenant row has the 3 fields with int counts.
    for row in body["per_tenant"]:
        assert set(row.keys()) == {"tenant_id", "agents", "runs24"}
        assert isinstance(row["agents"], int) and row["agents"] >= 0
        assert isinstance(row["runs24"], int) and row["runs24"] >= 0
