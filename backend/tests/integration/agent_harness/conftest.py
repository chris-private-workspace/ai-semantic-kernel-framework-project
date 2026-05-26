"""
File: backend/tests/integration/agent_harness/conftest.py
Purpose: Autouse cleanup fixture for committed-row leaks in agent_harness integration tests
         (sibling to tests/integration/api/conftest.py §Committed-Row Cleanup Pattern).
Category: Tests / 范疇 7 (state_mgmt)
Scope: Phase 57 / Sprint 57.53

Description:
    Sibling pattern to `tests/integration/api/conftest.py` §Committed-Row Cleanup
    (Sprint 57.12 — closes AD-AdminTenant-Patch-Flake) — at agent_harness integration
    scope. State_mgmt tests (`test_checkpointer_db.py`) use predictable tenant codes
    (ISO_A, RT, TT, MM_SID, MM_TID, MISSING, SIZE, CHKPT_TEST, TEST_TENANT) that can
    collide with leaked rows from prior runs if any committing test path (e.g.
    interleaved api tests) persists rows past the db_session rollback contract.

    The autouse fixture clears stale committed test-tenant rows before+after each
    test so each run starts clean. Uses the WORM-trigger-toggle DELETE pattern
    (DISABLE → DELETE → ENABLE → COMMIT) verbatim from Sprint 57.12 to bypass the
    `audit_log_no_update_delete` trigger CASCADE on `audit_log` (reached via FK
    CASCADE from `tenants` deletion).

    Sprint 57.53 root cause investigation:
        Day 1.1.1 query found 1 stale row `tenants.code='ISO_A'` from
        `test_tenant_isolation` test path, created 2026-05-26 02:14:29 UTC.
        H1 (committing test caller) refuted in state_mgmt scope (0 .commit() calls);
        H3 (WORM trigger on tenants) refuted (TRIGGER_COUNT=0);
        H4 (seed_tenant refactor migration gap) refuted (no history);
        H5 (crashed run leaking all codes) refuted (only 1/9 codes leaked);
        H6 (DBCheckpointer.save commits) refuted (no .commit() in checkpointer.py).
        Most likely cause: concurrent test interleaving with api tests that commit
        (Sprint 57.12 root cause pattern) OR H2 manual psql leftover.

    Per Sprint 57.12 §Committed-Row Cleanup Pattern explicit anti-patterns:
        - REJECTED Option D (UUID-suffixed codes) → loses predictable test IDs
        - REJECTED `DELETE FROM tenants` without trigger toggle → FK CASCADE fails

Key Components:
    - _COMMITTING_STATE_MGMT_TENANT_CODES: tuple of test-tenant codes to allowlist
    - _clear_committed_state_mgmt_tenants(): cleanup function with trigger toggle
    - _reset_state_mgmt_test_state: autouse fixture (before+after yield)

Created: 2026-05-26 (Sprint 57.53)
Last Modified: 2026-05-26

Modification History:
    - 2026-05-26: Sprint 57.53 — initial creation (closes AD-Checkpointer-Tenant-Isolation)

Related:
    - tests/integration/api/conftest.py (Sprint 57.12 parent pattern)
    - docs/rules-on-demand/testing.md §Committed-Row Cleanup Pattern
    - .claude/rules/sprint-workflow.md §Common Risk Classes
"""

from __future__ import annotations

from typing import AsyncIterator

import pytest
from sqlalchemy import text

from infrastructure.db.engine import dispose_engine, get_session_factory

# Allowlist of test-tenant codes used by `tests/integration/agent_harness/` integration
# tests. Extend per new committing test path that surfaces. Keep alphabetically grouped
# by test file for readability.
_COMMITTING_STATE_MGMT_TENANT_CODES: tuple[str, ...] = (
    # test_checkpointer_db.py — per-test codes used by _build_session(tenant_code=...)
    "CHKPT_TEST",  # _build_session default
    "ISO_A",  # test_tenant_isolation (Sprint 57.53 root cause: stale row found Day 1.1.1)
    "MISSING",  # test_load_unknown_version_raises
    "MM_SID",  # test_state_mismatch_session_id_raises
    "MM_TID",  # test_state_mismatch_tenant_id_raises
    "RT",  # test_save_load_round_trip
    "SIZE",  # test_db_row_size_under_5kb
    "TT",  # test_save_multiple_versions_then_time_travel
    # seed_tenant default (defensive — should never be used directly in tests but
    # included so accidental defaults don't leak)
    "TEST_TENANT",
)


async def _clear_committed_state_mgmt_tenants() -> None:
    """Delete stale committed test-tenant rows from state_mgmt tests so each run starts clean.

    Sibling to `tests/integration/api/conftest.py::_clear_committed_test_tenants`
    (Sprint 57.12 §Committed-Row Cleanup Pattern). FK CASCADE from `tenants` reaches
    `audit_log` which has the WORM trigger `audit_log_no_update_delete`; toggle it
    off inside ONE transaction so commit => trigger ENABLED + rows gone; any error
    => rollback => trigger ENABLED + nothing deleted.

    The test DB role owns the schema → RLS does not FORCE on owners, so a plain
    DELETE without `SET LOCAL app.tenant_id` is permitted; CASCADE handles dependent
    rows (memory_*, users, conversations, sessions, state_snapshots, ...).
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            await session.execute(
                text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_update_delete")
            )
            await session.execute(
                text("DELETE FROM tenants WHERE code = ANY(:codes)"),
                {"codes": list(_COMMITTING_STATE_MGMT_TENANT_CODES)},
            )
            await session.execute(
                text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_update_delete")
            )
            await session.commit()
        except Exception:  # noqa: BLE001 — cleanup is best-effort; never fail the test setup
            await session.rollback()
    await dispose_engine()


@pytest.fixture(autouse=True)
async def _reset_state_mgmt_test_state() -> AsyncIterator[None]:
    """Clear stale committed test-tenant rows before+after each agent_harness integration test.

    Lighter-weight than `tests/integration/api/conftest.py::_reset_module_singletons`
    (Sprint 57.12) — agent_harness integration tests don't rely on api-test module
    singletons (service_factory / sla_recorder / pricing_loader / cost_ledger), so
    those resets are omitted. Cleanup runs before+after yield to defend against
    leaks from prior pytest sessions AND any commits within the current session.
    """
    await _clear_committed_state_mgmt_tenants()
    yield
    await _clear_committed_state_mgmt_tenants()
