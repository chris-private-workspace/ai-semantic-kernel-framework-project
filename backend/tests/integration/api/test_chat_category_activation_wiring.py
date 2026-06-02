"""
File: backend/tests/integration/api/test_chat_category_activation_wiring.py
Purpose: Integration tests proving Sprint 57.63 chat-path category activation —
    build_real_llm_handler injects Cat 4 / 7 / 8 / 10 deps into AgentLoopImpl,
    and the Cat 7 chat-path factory persists a real StateSnapshot row with
    cross-tenant isolation.
Category: Tests / integration / api
Scope: Phase 57 / Sprint 57.63 Day 3

Description:
    Two groups, both deterministic and Azure-call-free:

    Group A (handler injection completeness) — monkeypatches fake AZURE_OPENAI_*
        env so build_real_llm_handler constructs an AzureOpenAIAdapter config
        object (no network) and wires the loop. Asserts the loop carries the
        Cat 4 compactor, Cat 7 reducer+checkpointer+tenant_id, and Cat 8 5-dep
        chain, and that the returned verifier_registry follows
        chat_verification_mode (None when disabled, real LLMJudgeVerifier when
        enabled). These guard against silent un-wiring (AP-4 Potemkin).

    Group B (Cat 7 real DB persistence + tenant isolation) — uses the real
        db_session fixture + seed_tenant/seed_user + a Session row, builds the
        Cat 7 deps via the SAME chat-path factory (make_chat_state_deps), and
        asserts DBCheckpointer.save() writes a StateSnapshot row, and that a
        second tenant's checkpointer cannot load the first tenant's snapshot.

    NOT covered here (requires real Azure key): the full real_llm SSE e2e
    (StateCheckpointed / ContextCompacted / VerificationPassed events on the
    streaming path). That is the `-m real_llm` test, deferred to an env with
    AZURE_OPENAI_* configured. echo_demo SSE intentionally does NOT inject these
    categories (predictable fixtures), so it cannot prove activation.

Created: 2026-05-31 (Sprint 57.63 Day 3)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import (
    DurableState,
    LoopState,
    StateVersion,
    TransientState,
)
from agent_harness.state_mgmt import DBCheckpointer, StateNotFoundError
from agent_harness.verification.llm_judge import LLMJudgeVerifier
from api.v1.chat._category_factories import make_chat_state_deps
from api.v1.chat.handler import build_real_llm_handler
from infrastructure.db.models import Session as SessionModel
from infrastructure.db.models import StateSnapshot
from tests.conftest import seed_tenant, seed_user

# ---- fake Azure env (config object only; no network) ------------------------

_FAKE_AZURE_ENV = {
    "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "fake-key-not-used",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "fake-deploy",
}


def _set_fake_azure(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _FAKE_AZURE_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    """Clear get_settings lru_cache before+after each test.

    The Group A tests toggle CHAT_VERIFICATION_MODE via env; without clearing the
    @lru_cache, an earlier test's build_real_llm_handler() call caches a Settings
    instance and later mode-switch tests read the stale value (cross-test
    pollution). Mirrors the conftest module-level singleton-reset pattern.
    """
    from core.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


# ============================================================
# Group A — handler injection completeness (no DB, no network)
# ============================================================


def test_real_handler_injects_cat4_compactor(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake_azure(monkeypatch)
    loop, _registry = build_real_llm_handler()
    # Cat 4: compactor present → loop.py:828 compaction branch is live.
    assert loop._compactor is not None  # type: ignore[attr-defined]


def test_real_handler_injects_cat8_five_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake_azure(monkeypatch)
    loop, _registry = build_real_llm_handler()
    # Cat 8: all 5 error-handling deps present → _handle_tool_error chain live.
    assert loop._error_policy is not None  # type: ignore[attr-defined]
    assert loop._retry_policy is not None  # type: ignore[attr-defined]
    assert loop._circuit_breaker is not None  # type: ignore[attr-defined]
    assert loop._error_budget is not None  # type: ignore[attr-defined]
    assert loop._error_terminator is not None  # type: ignore[attr-defined]


def test_real_handler_cat7_noop_without_db(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake_azure(monkeypatch)
    # No db/session_id/tenant_id → Cat 7 all-three-or-nothing → no-op (baseline).
    loop, _registry = build_real_llm_handler()
    assert loop._reducer is None  # type: ignore[attr-defined]
    assert loop._checkpointer is None  # type: ignore[attr-defined]


def test_real_handler_cat7_wired_with_db(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake_azure(monkeypatch)
    from unittest.mock import MagicMock

    tid = uuid4()
    sid = uuid4()
    loop, _registry = build_real_llm_handler(db=MagicMock(), session_id=sid, tenant_id=tid)
    # Cat 7: all three present → loop.py:1350 checkpoint branch is live.
    assert loop._reducer is not None  # type: ignore[attr-defined]
    assert loop._checkpointer is not None  # type: ignore[attr-defined]
    assert loop._tenant_id == tid  # type: ignore[attr-defined]


def test_real_handler_cat10_disabled_returns_no_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.config import get_settings

    _set_fake_azure(monkeypatch)
    monkeypatch.setenv("CHAT_VERIFICATION_MODE", "disabled")
    # Clear the lru_cache AFTER setenv (not only in the autouse fixture): another
    # autouse fixture (e.g. conftest _reset_module_singletons) may call
    # get_settings() during setup — after the fixture's pre-clear but before this
    # env change — re-caching the default. Clearing here makes the test hermetic.
    get_settings.cache_clear()
    loop, registry = build_real_llm_handler()
    # Cat 10 disabled (default) → wrapper passthrough → registry is None.
    assert registry is None


def test_real_handler_cat10_enabled_registers_llm_judge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.config import get_settings

    _set_fake_azure(monkeypatch)
    monkeypatch.setenv("CHAT_VERIFICATION_MODE", "enabled")
    # Clear the lru_cache AFTER setenv (hermetic — see disabled test above for why).
    get_settings.cache_clear()
    loop, registry = build_real_llm_handler()
    # Cat 10 enabled → registry with exactly one real LLMJudgeVerifier.
    assert registry is not None
    assert len(registry) == 1
    verifier = registry.get_all()[0]
    assert isinstance(verifier, LLMJudgeVerifier)


def test_real_handler_tracer_defaults_to_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sprint 57.71 (A-4 Tier 0): without an injected tracer, the loop falls
    back to NoOpTracer (pre-57.71 baseline — no spans exported)."""
    from agent_harness.observability import NoOpTracer

    _set_fake_azure(monkeypatch)
    loop, _registry = build_real_llm_handler()
    assert isinstance(loop._tracer, NoOpTracer)  # type: ignore[attr-defined]


def test_real_handler_injects_real_tracer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sprint 57.71 (A-4 Tier 0): when the router threads its real OTelTracer in,
    the loop runs on THAT tracer (not NoOp), so the root + per-turn span tree is
    real. Guards against the Cat 12 Potemkin (AP-4): a NoOp loop emits no
    reconstructable trace tree even though the root span code exists."""
    from agent_harness.observability import NoOpTracer, OTelTracer

    _set_fake_azure(monkeypatch)
    real_tracer = OTelTracer()
    loop, _registry = build_real_llm_handler(tracer=real_tracer)
    assert loop._tracer is real_tracer  # type: ignore[attr-defined]
    assert not isinstance(loop._tracer, NoOpTracer)  # type: ignore[attr-defined]


# ============================================================
# Group B — Cat 7 real DB persistence + tenant isolation
# ============================================================


def _state_for(session_id, tenant_id, *, version: int = 0, current_turn: int = 0) -> LoopState:
    return LoopState(
        transient=TransientState(current_turn=current_turn),
        durable=DurableState(session_id=session_id, tenant_id=tenant_id),
        version=StateVersion(
            version=version,
            parent_version=None if version == 0 else version - 1,
            created_at=datetime.now(timezone.utc),
            created_by_category="orchestrator_loop",
        ),
    )


@pytest.mark.asyncio
async def test_chat_factory_checkpointer_persists_snapshot(db_session: AsyncSession) -> None:
    """The Cat 7 deps built by the chat-path factory write a real StateSnapshot."""
    tenant = await seed_tenant(db_session, code="CHAT_CAT7")
    user = await seed_user(db_session, tenant, email="chat_cat7@test.com")
    session_row = SessionModel(tenant_id=tenant.id, user_id=user.id)
    db_session.add(session_row)
    await db_session.flush()
    await db_session.refresh(session_row)

    # SAME factory the production handler uses.
    reducer, checkpointer = make_chat_state_deps(db_session, session_row.id, tenant.id)
    assert reducer is not None
    assert checkpointer is not None

    state = _state_for(session_row.id, tenant.id, version=0, current_turn=1)
    persisted = await checkpointer.save(state)
    # append_snapshot assigns version starting at 1 (DB sequence), not the
    # caller's state.version.version (0). First snapshot for a session = v1.
    assert persisted.version == 1

    rows = (
        (
            await db_session.execute(
                select(StateSnapshot).where(StateSnapshot.session_id == session_row.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].tenant_id == tenant.id


@pytest.mark.asyncio
async def test_chat_factory_checkpointer_tenant_isolation(db_session: AsyncSession) -> None:
    """A second tenant's checkpointer cannot load the first tenant's snapshot."""
    tenant_a = await seed_tenant(db_session, code="CHAT_CAT7_A")
    user_a = await seed_user(db_session, tenant_a, email="a_cat7@test.com")
    session_a = SessionModel(tenant_id=tenant_a.id, user_id=user_a.id)
    db_session.add(session_a)
    await db_session.flush()
    await db_session.refresh(session_a)

    _, cp_a = make_chat_state_deps(db_session, session_a.id, tenant_a.id)
    assert cp_a is not None
    await cp_a.save(_state_for(session_a.id, tenant_a.id, version=0, current_turn=1))

    # Tenant B checkpointer bound to the SAME session_id but a different tenant_id
    # must not find tenant A's snapshot (load() uses the ctor-bound tenant_id).
    tenant_b_id = uuid4()
    cp_b = DBCheckpointer(db_session, session_id=session_a.id, tenant_id=tenant_b_id)
    with pytest.raises(StateNotFoundError):
        await cp_b.load(version=0)
