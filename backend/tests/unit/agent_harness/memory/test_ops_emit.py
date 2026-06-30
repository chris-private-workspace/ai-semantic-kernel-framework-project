"""
File: backend/tests/unit/agent_harness/memory/test_ops_emit.py
Purpose: Unit tests for memory_ops emit on write/evict (user + tenant layers).
Category: Tests / 範疇 3
Scope: Phase 57 / Sprint 57.76 (US-2 / US-3 / US-6)

Description:
    Mock-factory tests (mirroring test_user_layer.py) proving:
      - user/tenant write() emits a MemoryOp(WRITE) with value_snapshot=content
        on the SAME session as the underlying row, before the single commit
        (Risk Class C — no separate session, no double-commit).
      - user/tenant evict() SELECT-before-DELETE captures old content and emits
        a MemoryOp(EVICT); absent row → no op row (no fabrication).
      - role write/evict raise NotImplementedError → no op row recorded.

    Real-DB Risk-C rollback atomicity is covered in the integration RLS test
    (test_memory_ops_rls.py) where a real transaction can be rolled back.

Created: 2026-06-04 (Sprint 57.76)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from agent_harness.memory.layers.role_layer import RoleLayer
from agent_harness.memory.layers.tenant_layer import TenantLayer
from agent_harness.memory.layers.user_layer import UserLayer
from infrastructure.db.models.memory import MemoryOp, MemoryUser


def _factory_with_select(first_row: object | None) -> MagicMock:
    """async_sessionmaker mock; session.execute().first() returns first_row.

    Tracks every session.add() target so tests can find the emitted MemoryOp.
    """
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = first_row
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.add = MagicMock()
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    factory = MagicMock(return_value=cm)
    factory._mock_session = session
    return factory


def _added_ops(session: MagicMock) -> list[MemoryOp]:
    return [c.args[0] for c in session.add.call_args_list if isinstance(c.args[0], MemoryOp)]


# ---------------------------------------------------------------------------
# WRITE emit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_write_emits_write_op_same_session() -> None:
    factory = _factory_with_select(None)
    layer = UserLayer(factory)
    tenant, user = uuid4(), uuid4()

    await layer.write(
        content="prefers brevity", tenant_id=tenant, user_id=user, time_scale="long_term"
    )

    session = factory._mock_session  # type: ignore[attr-defined]
    ops = _added_ops(session)
    assert len(ops) == 1
    op = ops[0]
    assert op.operation == "WRITE"
    assert op.scope == "user"
    assert op.value_snapshot == "prefers brevity"
    assert op.tenant_id == tenant
    assert op.user_id == user
    assert op.actor == str(user)
    assert op.time_scale == "long_term"
    # Risk C: the MemoryUser upsert + the op row run on the SAME session with
    # exactly ONE commit (no separate session / double-commit). Sprint 57.150 made
    # write() an ON CONFLICT upsert → the MemoryUser is now an execute(), not add().
    session.execute.assert_awaited()
    targets = [c.args[0] for c in session.add.call_args_list]
    assert any(isinstance(t, MemoryOp) for t in targets)
    assert not any(isinstance(t, MemoryUser) for t in targets)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tenant_write_emits_write_op() -> None:
    factory = _factory_with_select(None)
    layer = TenantLayer(factory)
    tenant = uuid4()

    await layer.write(content="playbook step 1", tenant_id=tenant, time_scale="long_term")

    session = factory._mock_session  # type: ignore[attr-defined]
    ops = _added_ops(session)
    assert len(ops) == 1
    assert ops[0].operation == "WRITE"
    assert ops[0].scope == "tenant"
    assert ops[0].value_snapshot == "playbook step 1"
    assert ops[0].user_id is None
    assert ops[0].actor == "system"
    session.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# EVICT emit (SELECT-before-DELETE)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_evict_emits_evict_op_with_old_value() -> None:
    old_user = uuid4()
    # SELECT-before-DELETE returns (content, user_id)
    factory = _factory_with_select(("old fact", old_user))
    layer = UserLayer(factory)
    tenant = uuid4()

    await layer.evict(entry_id=uuid4(), tenant_id=tenant)

    session = factory._mock_session  # type: ignore[attr-defined]
    ops = _added_ops(session)
    assert len(ops) == 1
    assert ops[0].operation == "EVICT"
    assert ops[0].scope == "user"
    assert ops[0].value_snapshot == "old fact"
    assert ops[0].user_id == old_user
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tenant_evict_emits_evict_op_with_old_value() -> None:
    factory = _factory_with_select(("old playbook", "hint-abc"))
    layer = TenantLayer(factory)
    tenant = uuid4()

    await layer.evict(entry_id=uuid4(), tenant_id=tenant)

    session = factory._mock_session  # type: ignore[attr-defined]
    ops = _added_ops(session)
    assert len(ops) == 1
    assert ops[0].operation == "EVICT"
    assert ops[0].scope == "tenant"
    assert ops[0].value_snapshot == "old playbook"
    assert ops[0].key == "hint-abc"


@pytest.mark.asyncio
async def test_user_evict_absent_row_records_no_op() -> None:
    """Row already gone (SELECT → None) → no op row (no fabrication)."""
    factory = _factory_with_select(None)
    layer = UserLayer(factory)
    await layer.evict(entry_id=uuid4(), tenant_id=uuid4())
    session = factory._mock_session  # type: ignore[attr-defined]
    assert _added_ops(session) == []


@pytest.mark.asyncio
async def test_tenant_evict_absent_row_records_no_op() -> None:
    factory = _factory_with_select(None)
    layer = TenantLayer(factory)
    await layer.evict(entry_id=uuid4(), tenant_id=uuid4())
    session = factory._mock_session  # type: ignore[attr-defined]
    assert _added_ops(session) == []


# ---------------------------------------------------------------------------
# No emit when no live path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_write_raises_no_op_recorded() -> None:
    """RoleLayer write is admin-managed (raises) → no live path, no op row."""
    factory = _factory_with_select(None)
    layer = RoleLayer(factory)
    with pytest.raises(NotImplementedError):
        await layer.write(content="x", tenant_id=uuid4())
    session = factory._mock_session  # type: ignore[attr-defined]
    assert _added_ops(session) == []


@pytest.mark.asyncio
async def test_user_evict_no_op_without_tenant() -> None:
    factory = _factory_with_select(("c", uuid4()))
    layer = UserLayer(factory)
    await layer.evict(entry_id=uuid4(), tenant_id=None)
    session = factory._mock_session  # type: ignore[attr-defined]
    # no DB touched at all when tenant missing
    session.execute.assert_not_called()
    assert _added_ops(session) == []
