"""
File: backend/tests/integration/api/conftest.py
Purpose: Shared fixtures for api/v1 integration tests.
Category: Tests / integration / api
Scope: Phase 53 / Sprint 53.6 (US-5 ServiceFactory test isolation)

Description:
    Resets module-level singletons between tests so each test gets a fresh
    instance bound to its own pytest-asyncio event loop. Without this, the
    first test caches resources bound to its loop, and subsequent tests in
    the same process hit "Event loop is closed".

    Singletons reset (per testing.md §Module-level Singleton Reset Pattern):
    - ServiceFactory (53.6) — governance HITL/Risk/AuditQuery
    - SLAMetricRecorder (56.3 US-1) — Cat 12 SLA recording
    - PricingLoader (56.3 US-3) — LLM + tool pricing yaml cache
    - CostLedgerService (56.3 US-3) — per-event Cost Ledger writer
    - DB Engine (Sprint 57.11 fix AD-Governance-RBAC-Flake) — async engine pool
      futures bind to first-test event loop; without explicit dispose between
      tests, subsequent tests hit "Future attached to a different loop" / "Event
      loop is closed" failures (e.g. test_list_rejects_non_approver_role on CI).

    DB test-tenant cleanup (Sprint 57.12 fix AD-AdminTenant-Patch-Flake):
      A few admin endpoints (PATCH /tenants/{id}, POST /tenants onboarding)
      call `await db.commit()` internally. When the test injects its own
      db_session as the route session, that commit persists the seeded
      tenant row past the db_session fixture's teardown rollback (rollback
      is a no-op after commit). Subsequent runs then collide on
      `uq_tenants_code` (e.g. code='BOTH_FIELDS' already exists). Per 53.7
      §Risk Class C SAVEPOINT pattern, the autouse fixture clears stale
      committed test-tenant rows at setup so each run starts clean.
      The test DB role owns the schema → RLS does not FORCE on owners, so a
      plain DELETE without SET LOCAL app.tenant_id is permitted; CASCADE
      handles dependent rows (memory_*, users, conversations, ...).

Modification History (newest-first):
    - 2026-05-27: Sprint 57.56 — add QUOTA_PUT_% LIKE sweep (Sprint 57.55 FF_PUT_% precedent)
    - 2026-05-26: Sprint 57.55 — sweep FF_PUT_% tenants (PUT /feature-flags tests)
    - 2026-05-26: Sprint 57.54 Track A — sweep HITL_PUT_% tenants (committed by store.put)
    - 2026-05-10: Sprint 57.12 — _clear_committed_test_tenants (AD-AdminTenant-Patch-Flake)
    - 2026-05-10: Sprint 57.11 — add dispose_engine() autouse (closes AD-Governance-RBAC-Flake)
    - 2026-05-06: Sprint 56.3 Day 3 — add reset_cost_ledger (US-3)
    - 2026-05-06: Sprint 56.3 Day 2 — add reset_pricing_loader (US-3)
    - 2026-05-06: Sprint 56.3 Day 1 — add reset_sla_recorder (US-1)
    - 2026-05-04: Initial (Sprint 53.6 Day 4)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest

# Sprint 57.6 Day 4 (AD-Reality-FlakeEventLoop deferred Phase 57.7+):
# Disable Day 2 audit_log chat observer in integration tests until proper
# connection-pool isolation is added to tests/conftest.py db_session fixture
# (estimated ~1-2 hr). Without this, db.begin_nested()+append_audit()+session
# flush leaves connection-pool state bound to chat_e2e tests' asyncio loop
# → cascades into "attached to a different loop" cross-test failure pattern.
os.environ.setdefault("AUDIT_LOG_CHAT_OBSERVER", "false")

# Sprint 57.7 US-R1 D19: same pattern for sessions+tool_calls observers
# (closed AD-Reality-3a + 3b backend wiring; same loop-isolation concern as
# audit_log above; defer real test fixture refactor to AD-Reality-FlakeEventLoop).
os.environ.setdefault("SESSIONS_CHAT_OBSERVER", "false")
os.environ.setdefault("TOOL_CALLS_CHAT_OBSERVER", "false")

from sqlalchemy import text  # noqa: E402

from infrastructure.db.engine import dispose_engine  # noqa: E402
from infrastructure.db.session import get_session_factory  # noqa: E402
from platform_layer.billing.cost_ledger import reset_cost_ledger  # noqa: E402
from platform_layer.billing.pricing import reset_pricing_loader  # noqa: E402
from platform_layer.governance.service_factory import reset_service_factory  # noqa: E402
from platform_layer.observability import reset_sla_recorder  # noqa: E402

# Tenant codes used by tests that hit committing endpoints (PATCH /tenants/{id},
# POST /tenants onboarding). Listed explicitly so the cleanup is surgical (does
# NOT touch tenants seeded by non-committing tests, which roll back cleanly).
# When a new committing test adds a code, add it here too.
_COMMITTING_TEST_TENANT_CODES: tuple[str, ...] = (
    # test_admin_tenant_patch.py — PATCH route commits
    "IMMUTABLE_TEST",
    "TOO_LONG_TEST",
    "DN_ONLY",
    "META_ONLY",
    "BOTH_FIELDS",
    "NO_OP",
    "META_RT",
    "SHAPE_TEST",
    # test_admin_onboarding.py / test_admin_tenants_rbac.py — POST routes commit
    "GET_HAPPY",
    "admin",
)


async def _clear_committed_test_tenants() -> None:
    """Delete stale committed test-tenant rows so each run starts clean.

    Per 53.7 §Risk Class C: the test DB role owns the schema, so a plain DELETE
    (no SET LOCAL app.tenant_id — `tenants` is a global no-RLS table per
    migration 0009) is allowed. FK CASCADE from `tenants` reaches `audit_log`,
    which carries the WORM trigger `audit_log_no_update_delete` (raises
    "audit_log is append-only" on any DELETE). So we toggle that trigger off for
    the duration of this housekeeping DELETE inside a single transaction — on
    commit the net effect is trigger ENABLED + stale rows gone; on any error the
    rollback leaves the trigger ENABLED + nothing deleted (best-effort cleanup).
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            await session.execute(
                text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_update_delete")
            )
            await session.execute(
                text("DELETE FROM tenants WHERE code = ANY(:codes)"),
                {"codes": list(_COMMITTING_TEST_TENANT_CODES)},
            )
            # Sprint 57.54 Track A — sweep uuid4-suffixed PUT /hitl-policies test tenants
            await session.execute(text("DELETE FROM tenants WHERE code LIKE 'HITL_PUT_%'"))
            # Sprint 57.55 Track A — sweep uuid4-suffixed PUT /feature-flags test tenants
            await session.execute(text("DELETE FROM tenants WHERE code LIKE 'FF_PUT_%'"))
            # Sprint 57.56 Track A — sweep uuid4-suffixed PUT /quotas test tenants
            await session.execute(text("DELETE FROM tenants WHERE code LIKE 'QUOTA_PUT_%'"))
            # Sprint 57.55 — sweep uuid4-suffixed feature_flags rows seeded by PUT tests
            # (feature_flags is a global no-RLS registry; rows persist past test
            # rollback once any PUT test commits to make the row visible to the
            # endpoint session — same committed-row leakage pattern as tenants).
            await session.execute(text("DELETE FROM feature_flags WHERE name LIKE 'ff.%'"))
            await session.execute(
                text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_update_delete")
            )
            await session.commit()
        except Exception:  # noqa: BLE001 — cleanup is best-effort; never fail the test setup
            await session.rollback()
    await dispose_engine()


@pytest.fixture(autouse=True)
async def _reset_module_singletons() -> AsyncIterator[None]:
    """Clear module-level singletons + dispose async engine + clear stale test tenants.

    Sprint 57.11 fix (AD-Governance-RBAC-Flake): added await dispose_engine()
    to prevent cross-loop Future leak when one test's connection-pool futures
    are still pending when the next test's pytest-asyncio loop starts.

    Sprint 57.12 fix (AD-AdminTenant-Patch-Flake): added
    _clear_committed_test_tenants() so committing endpoints' persisted rows
    don't collide on uq_tenants_code across runs.
    """
    reset_service_factory()
    reset_sla_recorder()
    reset_pricing_loader()
    reset_cost_ledger()
    await dispose_engine()
    await _clear_committed_test_tenants()
    yield
    reset_service_factory()
    reset_sla_recorder()
    reset_pricing_loader()
    reset_cost_ledger()
    await dispose_engine()
    await _clear_committed_test_tenants()
