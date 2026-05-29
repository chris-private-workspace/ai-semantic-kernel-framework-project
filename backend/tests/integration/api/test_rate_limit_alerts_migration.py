"""
File: backend/tests/integration/api/test_rate_limit_alerts_migration.py
Purpose: Tests for the 0021 migration — rate_limit_alerts table + RLS + check exist.
Category: Tests / Integration / API (Phase 58.x RateLimits usage alerting)
Scope: Sprint 57.62 Track A / US-1 (RateLimits 80% usage alerting)

Description:
    Exercises the 0021 migration's DDL by introspecting the real test DB (which is
    at head, i.e. 0021 already applied by `alembic upgrade head`):
    1. upgrade-state: the rate_limit_alerts table + both RLS policies + the
       severity CHECK constraint exist.
    2. downgrade then re-upgrade: drop the table + policies, assert gone, then
       restore — proving the migration is reversible (mirrors the symmetry the
       0019/0020 migration tests assert, but DDL-only since 0021 has no data leg).

    The downgrade/upgrade runs the migration module's own downgrade()/upgrade()
    under an Alembic op context bound to the test session's connection, so the
    exact migration SQL path is exercised (not a hand-rolled copy).

Created: 2026-05-29 (Sprint 57.62 Track A)

Modification History (newest-first):
    - 2026-05-29: Initial creation (Sprint 57.62 Track A / US-1)
"""

from __future__ import annotations

import importlib

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = __import__("pytest").mark.asyncio

# Import the migration module by its file revision name to drive its own
# upgrade()/downgrade() (the op global is bound per-call via Operations context).
_migration = importlib.import_module("infrastructure.db.migrations.versions.0021_rate_limit_alerts")


async def _table_exists(session: AsyncSession) -> bool:
    return (
        await session.execute(text("SELECT to_regclass('rate_limit_alerts')"))
    ).scalar() is not None


async def _policy_names(session: AsyncSession) -> set[str]:
    rows = await session.execute(
        text("SELECT policyname FROM pg_policies WHERE tablename = 'rate_limit_alerts'")
    )
    return set(rows.scalars().all())


async def _check_exists(session: AsyncSession) -> bool:
    return (
        await session.execute(
            text("SELECT 1 FROM pg_constraint WHERE conname = 'ck_rate_limit_alerts_severity'")
        )
    ).scalar() is not None


def _run_migration_sync(sync_conn: object, func_name: str) -> None:
    """Bind an Alembic Operations context to sync_conn and call upgrade/downgrade."""
    ctx = MigrationContext.configure(sync_conn)  # type: ignore[arg-type]
    with Operations.context(ctx):
        getattr(_migration, func_name)()


async def test_migration_upgrade_state(db_session: AsyncSession) -> None:
    """At head (0021 applied) the table + 2 policies + severity CHECK all exist."""
    assert await _table_exists(db_session) is True
    assert await _policy_names(db_session) == {
        "tenant_isolation_rate_limit_alerts",
        "tenant_insert_rate_limit_alerts",
    }
    assert await _check_exists(db_session) is True


async def test_migration_downgrade_drops_then_upgrade_restores(db_session: AsyncSession) -> None:
    """downgrade() drops table + policies; upgrade() restores them (reversible).

    Runs in a SAVEPOINT-free flush boundary on the function-scoped db_session;
    the fixture rolls back at teardown so the head schema is left intact for
    other tests in the same worker.
    """
    conn = await db_session.connection()

    # downgrade: table + policies gone.
    await conn.run_sync(lambda c: _run_migration_sync(c, "downgrade"))
    assert await _table_exists(db_session) is False
    assert await _policy_names(db_session) == set()

    # re-upgrade: restored.
    await conn.run_sync(lambda c: _run_migration_sync(c, "upgrade"))
    assert await _table_exists(db_session) is True
    assert await _policy_names(db_session) == {
        "tenant_isolation_rate_limit_alerts",
        "tenant_insert_rate_limit_alerts",
    }
    assert await _check_exists(db_session) is True
