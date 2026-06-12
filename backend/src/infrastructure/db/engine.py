"""
File: backend/src/infrastructure/db/engine.py
Purpose: Module-level lazy AsyncEngine + async_sessionmaker singletons.
Category: Infrastructure / ORM core
Scope: Sprint 49.2 (initial engine + session factory)
Owner: infrastructure/db owner

Description:
    Provides:
        get_engine()           -> AsyncEngine (lazy, cached)
        get_session_factory()  -> async_sessionmaker[AsyncSession] (lazy, cached)
        dispose_engine()       -> teardown for tests / app shutdown

    Pool configuration is read from `core.config.Settings`:
        db_pool_size            (default 10)
        db_pool_max_overflow    (default 20)
        db_pool_recycle_sec     (default 300)
        db_echo                 (default False; True in dev for SQL logging)

    pool_pre_ping is hardcoded to True (always-on health check at checkout).

Key Components:
    - get_engine: returns the singleton AsyncEngine
    - get_session_factory: returns the singleton async_sessionmaker
    - dispose_engine: disposes engine + resets singletons (test fixture / shutdown)

Created: 2026-04-29 (Sprint 49.2 Day 1.4)
Last Modified: 2026-04-29

Modification History:
    - 2026-06-12: FIX-032 — dispose_engine always resets singletons even if close raises
    - 2026-04-29: Initial creation (Sprint 49.2 Day 1.4)

Related:
    - backend/src/core/config/__init__.py (Settings.database_url + db_pool_*)
    - backend/src/infrastructure/db/session.py (FastAPI dependency)
    - backend/src/infrastructure/db/migrations/env.py (separate engine; uses NullPool)
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the singleton AsyncEngine, creating it on first call."""
    global _engine
    if _engine is None:
        s = get_settings()
        _engine = create_async_engine(
            s.database_url,
            pool_size=s.db_pool_size,
            max_overflow=s.db_pool_max_overflow,
            pool_pre_ping=True,
            pool_recycle=s.db_pool_recycle_sec,
            echo=s.db_echo,
            future=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the singleton async_sessionmaker bound to the engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def dispose_engine() -> None:
    """
    Dispose the engine + reset module singletons.

    Use in pytest teardown fixtures and FastAPI lifespan shutdown.
    Safe to call multiple times.

    FIX-032: the singleton reset MUST happen even if ``_engine.dispose()`` raises.
    A stale engine whose pooled asyncpg connection belongs to an already-closed
    event loop (per-test loops in pytest-asyncio) makes asyncpg's graceful close
    do `create_task` on that dead loop → ``RuntimeError('Event loop is closed')``.
    If that exception propagated, ``_engine``/``_session_factory`` stayed set and
    the NEXT test reused the stale, cross-loop engine (the cascade that flaked
    `incident/test_service.py::test_create_returns_incident` under CI's collection
    order). Swallowing the close error here (the connection's loop is gone — there
    is nothing left to clean) and always nulling the singletons forces a fresh
    engine on the next loop.
    """
    global _engine, _session_factory
    if _engine is not None:
        try:
            await _engine.dispose()
        except Exception:  # noqa: BLE001 — best-effort close; a dead loop can't be cleaned
            pass
    _engine = None
    _session_factory = None


__all__ = ["get_engine", "get_session_factory", "dispose_engine"]
