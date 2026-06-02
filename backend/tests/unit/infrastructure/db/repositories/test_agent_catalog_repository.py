"""
File: backend/tests/unit/infrastructure/db/repositories/test_agent_catalog_repository.py
Purpose: Tests for AgentCatalogRepository (Sprint 57.70 Stage-1a) — CRUD round-trip,
    tenant filter, UNIQUE(tenant_id, key), and RLS enforcement on agent_catalog.
Category: Tests / Infrastructure / Repositories (Sprint 57.70 Stage-1a)
Scope: Phase 57 / Sprint 57.70 Stage-1a

Description:
    Uses the real `db_session` fixture (docker-compose PostgreSQL, AP-10 對策 —
    no SQLite) because the repo's value is the tenant-scoped SQL + the
    UNIQUE(tenant_id, key) constraint + RLS, none of which a mock can exercise.
    The RLS test mirrors test_rls_enforcement.py: SET LOCAL ROLE rls_app_role
    (no superuser / no BYPASSRLS) + SET LOCAL app.tenant_id to prove the policy
    actually filters cross-tenant rows.

Created: 2026-06-02 (Sprint 57.70 Stage-1a)
Last Modified: 2026-06-02

Related:
    - infrastructure/db/repositories/agent_catalog_repository.py
    - infrastructure/db/models/agent_catalog.py
    - tests/unit/infrastructure/db/test_rls_enforcement.py (RLS test pattern)
    - sprint-57-70-plan.md §3.6
"""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.agent_catalog import AgentCatalog
from infrastructure.db.repositories import AgentCatalogRepository
from tests.conftest import seed_tenant

# === CRUD round-trip + tenant filter =======================================


@pytest.mark.asyncio
async def test_create_and_get_by_key_round_trip(db_session: AsyncSession) -> None:
    """create() persists a row; get_by_key() fetches it back with all fields."""
    tenant = await seed_tenant(db_session, code="AGCAT_RT")
    repo = AgentCatalogRepository(db_session)

    created = await repo.create(
        tenant_id=tenant.id,
        key="researcher",
        name="Researcher",
        system_prompt="Investigate thoroughly.",
        model="gpt-4o",
        allowed_modes=["handoff", "fork"],
        status="live",
        meta_data={"budget": {"max_tokens": 1000}, "tools": ["search"]},
    )
    assert isinstance(created, AgentCatalog)
    assert created.id is not None

    fetched = await repo.get_by_key(tenant_id=tenant.id, key="researcher")
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.key == "researcher"
    assert fetched.name == "Researcher"
    assert fetched.model == "gpt-4o"
    assert fetched.system_prompt == "Investigate thoroughly."
    assert fetched.allowed_modes == ["handoff", "fork"]
    assert fetched.status == "live"
    assert fetched.meta_data == {"budget": {"max_tokens": 1000}, "tools": ["search"]}
    assert fetched.is_active is True


@pytest.mark.asyncio
async def test_create_defaults_when_optionals_omitted(db_session: AsyncSession) -> None:
    """Omitted optionals fall to model None / allowed_modes [] / status live / meta {}."""
    tenant = await seed_tenant(db_session, code="AGCAT_DEF")
    repo = AgentCatalogRepository(db_session)

    created = await repo.create(
        tenant_id=tenant.id,
        key="planner",
        name="Planner",
        system_prompt="Plan it.",
    )
    fetched = await repo.get_by_key(tenant_id=tenant.id, key="planner")
    assert fetched is not None
    assert fetched.model is None
    assert fetched.allowed_modes == []
    assert fetched.status == "live"
    assert fetched.meta_data == {}
    assert fetched.is_active is True
    assert created.id == fetched.id


@pytest.mark.asyncio
async def test_list_by_tenant_returns_all(db_session: AsyncSession) -> None:
    """list_by_tenant() returns every row for the tenant."""
    tenant = await seed_tenant(db_session, code="AGCAT_LIST")
    repo = AgentCatalogRepository(db_session)
    for key in ("researcher", "reviewer", "planner"):
        await repo.create(
            tenant_id=tenant.id, key=key, name=key.title(), system_prompt=f"{key} prompt"
        )

    rows = await repo.list_by_tenant(tenant_id=tenant.id)
    assert {r.key for r in rows} == {"researcher", "reviewer", "planner"}


@pytest.mark.asyncio
async def test_update_mutates_only_allowed_fields(db_session: AsyncSession) -> None:
    """update() changes name/system_prompt/status/is_active; key + tenant stay."""
    tenant = await seed_tenant(db_session, code="AGCAT_UPD")
    repo = AgentCatalogRepository(db_session)
    created = await repo.create(
        tenant_id=tenant.id, key="reviewer", name="Reviewer", system_prompt="old"
    )

    updated = await repo.update(
        tenant_id=tenant.id,
        agent_id=created.id,
        name="Reviewer v2",
        system_prompt="new prompt",
        status="staging",
        is_active=False,
        # An immutable identifier passed in is ignored (not in the allowed set).
        key="hacked",
    )
    assert updated is not None
    assert updated.name == "Reviewer v2"
    assert updated.system_prompt == "new prompt"
    assert updated.status == "staging"
    assert updated.is_active is False
    assert updated.key == "reviewer"  # unchanged
    assert updated.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_delete_removes_row(db_session: AsyncSession) -> None:
    """delete() removes the tenant's row and returns 1; a re-get returns None."""
    tenant = await seed_tenant(db_session, code="AGCAT_DEL")
    repo = AgentCatalogRepository(db_session)
    created = await repo.create(tenant_id=tenant.id, key="researcher", name="R", system_prompt="p")

    deleted = await repo.delete(tenant_id=tenant.id, agent_id=created.id)
    assert deleted == 1
    assert await repo.get_by_key(tenant_id=tenant.id, key="researcher") is None


@pytest.mark.asyncio
async def test_tenant_filter_isolates_rows(db_session: AsyncSession) -> None:
    """A row created for tenant A is NOT returned for tenant B (repo tenant filter)."""
    tenant_a = await seed_tenant(db_session, code="AGCAT_TA")
    tenant_b = await seed_tenant(db_session, code="AGCAT_TB")
    repo = AgentCatalogRepository(db_session)
    a_row = await repo.create(
        tenant_id=tenant_a.id, key="researcher", name="A", system_prompt="A prompt"
    )

    # Tenant B sees nothing for the same key / id.
    assert await repo.get_by_key(tenant_id=tenant_b.id, key="researcher") is None
    assert await repo.get_by_id(tenant_id=tenant_b.id, agent_id=a_row.id) is None
    assert await repo.list_by_tenant(tenant_id=tenant_b.id) == []

    # A cross-tenant update / delete affects 0 rows (no-op).
    no_op = await repo.update(tenant_id=tenant_b.id, agent_id=a_row.id, name="hijack")
    assert no_op is None
    assert await repo.delete(tenant_id=tenant_b.id, agent_id=a_row.id) == 0

    # A's row is intact.
    assert (await repo.get_by_key(tenant_id=tenant_a.id, key="researcher")).name == "A"


@pytest.mark.asyncio
async def test_unique_constraint_on_tenant_key(db_session: AsyncSession) -> None:
    """Two rows with the same (tenant_id, key) violate the UNIQUE constraint."""
    tenant = await seed_tenant(db_session, code="AGCAT_UQ")
    repo = AgentCatalogRepository(db_session)
    await repo.create(tenant_id=tenant.id, key="researcher", name="first", system_prompt="p1")

    with pytest.raises(IntegrityError):
        await repo.create(tenant_id=tenant.id, key="researcher", name="dup", system_prompt="p2")


# === RLS enforcement (mirrors test_rls_enforcement.py) =====================

_RLS_TABLES = ("tenants", "agent_catalog")


async def _ensure_rls_app_role(session: AsyncSession) -> None:
    """Create rls_app_role NOLOGIN (no superuser / no BYPASSRLS) if absent."""
    await session.execute(text("""
            DO $$
            BEGIN
                CREATE ROLE rls_app_role NOLOGIN;
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END
            $$;
            """))
    grants = ", ".join(_RLS_TABLES)
    await session.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {grants} TO rls_app_role"))
    await session.execute(text("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO rls_app_role"))


async def _set_app_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    """SET LOCAL app.tenant_id (scoped to current tx)."""
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )


@pytest.mark.asyncio
async def test_rls_select_scoped_to_tenant(db_session: AsyncSession) -> None:
    """As rls_app_role with app.tenant_id=A, only tenant A's agent rows are visible."""
    await _ensure_rls_app_role(db_session)
    t_a = await seed_tenant(db_session, code="AGCAT_RLS_A")
    t_b = await seed_tenant(db_session, code="AGCAT_RLS_B")
    db_session.add_all(
        [
            AgentCatalog(tenant_id=t_a.id, key="researcher", name="A", system_prompt="A"),
            AgentCatalog(tenant_id=t_b.id, key="researcher", name="B", system_prompt="B"),
        ]
    )
    await db_session.flush()

    await db_session.execute(text("SET LOCAL ROLE rls_app_role"))
    await _set_app_tenant(db_session, t_a.id)

    rows = list((await db_session.execute(select(AgentCatalog))).scalars().all())
    assert len(rows) == 1
    assert rows[0].tenant_id == t_a.id
    assert rows[0].name == "A"


@pytest.mark.asyncio
async def test_rls_insert_with_check_blocks_wrong_tenant(db_session: AsyncSession) -> None:
    """As rls_app_role, INSERT with tenant_id != app.tenant_id raises (WITH CHECK)."""
    from sqlalchemy.exc import DBAPIError

    await _ensure_rls_app_role(db_session)
    t_a = await seed_tenant(db_session, code="AGCAT_RLS_INS_A")
    t_b = await seed_tenant(db_session, code="AGCAT_RLS_INS_B")
    await db_session.flush()

    await db_session.execute(text("SET LOCAL ROLE rls_app_role"))
    await _set_app_tenant(db_session, t_a.id)

    db_session.add(
        AgentCatalog(tenant_id=t_b.id, key="researcher", name="hijack", system_prompt="x")
    )
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.flush()
    assert "row-level security" in str(exc_info.value).lower()
