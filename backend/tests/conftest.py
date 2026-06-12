"""
File: backend/tests/conftest.py
Purpose: Shared pytest fixtures + seed helpers for V2 backend tests.
Category: Tests / Infrastructure
Scope: Sprint 49.2 Day 2.3 (initial conftest + db_session + seed helpers)

Description:
    Provides:
        db_session: per-test AsyncSession with rollback at end (real docker
                    compose PostgreSQL — AP-10 對策, no SQLite).
        seed_tenant: helper to create + flush a Tenant.
        seed_user: helper to create + flush a User under a tenant.

    Pre-requisite for tests using db_session:
        docker compose -f docker-compose.dev.yml up -d postgres
        cd backend && alembic upgrade head

Created: 2026-04-29 (Sprint 49.2 Day 2.3)
Last Modified: 2026-04-29

Modification History:
    - 2026-04-29: Initial creation (Sprint 49.2 Day 2.3)

Related:
    - .claude/rules/testing.md (testing rules + AP-10 對策)
    - infrastructure/db/engine.py (singleton factory)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import dispose_engine, get_session_factory
from infrastructure.db.models import Tenant, User

# Sprint 57.84 (C-15): keep the background billing-outbox drainer OUT of test
# event loops. It starts in api.main._lifespan, which TestClient triggers
# (test_main_lifespan / test_health). Read as a plain env flag (not Settings)
# to dodge the get_settings() lru_cache timing trap — mirrors
# AUDIT_LOG_CHAT_OBSERVER (tests/integration/api/conftest.py).
os.environ.setdefault("BILLING_OUTBOX_DRAINER_ENABLED", "false")


@pytest.fixture(autouse=True)
def _reset_billing_outbox_singleton() -> Iterator[None]:
    """Reset the billing_outbox enqueue singleton around every test (Risk Class C).

    api.main._lifespan (driven by TestClient in test_main_lifespan) calls
    set_billing_outbox(); the lifespan shutdown does NOT unset it (correct for
    production — the singleton lives for the app's life). Without this reset it
    leaks into later tests, and a chat-path test that consumes
    maybe_get_billing_outbox() then enqueues on the global engine (binding it to
    that test's loop with no dispose) → a downstream db_session test hits
    'Event loop is closed'. Mirrors testing.md §Module-level Singleton Reset.
    """
    from platform_layer.billing.billing_outbox import set_billing_outbox

    set_billing_outbox(None)
    yield
    set_billing_outbox(None)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncIterator[AsyncSession]:
    """Per-test AsyncSession with rollback + engine disposal at end.

    Why dispose_engine() per-test:
        pytest-asyncio defaults to per-test event loops. The singleton
        AsyncEngine in infrastructure.db.engine is bound to whichever
        loop first created it; subsequent tests run in new loops and
        hit RuntimeError('Event loop is closed') on pooled connections.
        Disposing the engine after each test forces a fresh engine on
        the next test's loop. Slight perf cost (~10 ms / test) is the
        right trade for correctness + isolation.

    Caller may flush + use ORM normally; pending changes are rolled
    back at fixture teardown so each test sees a clean DB state.

    FIX-032: dispose at SETUP too (not only teardown). Teardown-only disposal
    leaks the engine into the next test if a prior test touched the engine WITHOUT
    this fixture (no teardown dispose) OR if its teardown dispose raised on a dead
    loop. Disposing at setup forces a fresh engine bound to THIS test's loop
    regardless of what ran before — the robust complement to dispose_engine's
    always-reset (so the cross-loop `Event loop is closed` cascade that flaked
    incident/test_service.py under CI's collection order cannot recur).
    """
    await dispose_engine()
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
    await dispose_engine()


async def seed_tenant(
    session: AsyncSession, *, code: str = "TEST_TENANT", display_name: str | None = None
) -> Tenant:
    """Create + flush a Tenant. Caller must NOT commit — fixture rollback handles cleanup."""
    t = Tenant(code=code, display_name=display_name or f"Tenant {code}")
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


async def seed_user(
    session: AsyncSession,
    tenant: Tenant,
    *,
    email: str = "user@test.com",
    display_name: str | None = None,
) -> User:
    """Create + flush a User scoped to the given tenant."""
    u = User(
        tenant_id=tenant.id,
        email=email,
        display_name=display_name or email.split("@")[0],
    )
    session.add(u)
    await session.flush()
    await session.refresh(u)
    return u
