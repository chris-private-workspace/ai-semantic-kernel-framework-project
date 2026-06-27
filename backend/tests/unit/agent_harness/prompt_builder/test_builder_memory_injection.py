"""Unit tests for DefaultPromptBuilder._inject_memory_layers. Sprint 52.2 Day 2.2 — 8 tests.

4 functional + 4 red-team (W3-2 audit carryover):
- 5_layers_all_injected
- 3_time_scales_ordered_long_term_first
- memory_retrieval_failure_degrades_gracefully
- layer_metadata_records_used_layers
- red-team 1: cross_tenant_no_leak
- red-team 2: cross_user_no_leak
- red-team 3: cross_session_no_leak
- red-team 4: no_process_wide_cache (each build() invokes search; no in-builder cache)
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from agent_harness.context_mgmt.cache_manager import InMemoryCacheManager
from agent_harness.context_mgmt.token_counter.generic_approx import (
    GenericApproxCounter,
)
from agent_harness.memory.retrieval import MemoryRetrieval
from agent_harness.prompt_builder.builder import DefaultPromptBuilder
from tests.unit.agent_harness.prompt_builder.conftest import (
    make_memory_hint,
    make_state,
    msg,
)


@pytest.fixture
def builder_and_search() -> tuple[DefaultPromptBuilder, AsyncMock]:
    retrieval = MemoryRetrieval(layers={})
    mock_search = AsyncMock(return_value=[])
    retrieval.search = mock_search  # type: ignore[method-assign]
    builder = DefaultPromptBuilder(
        memory_retrieval=retrieval,
        cache_manager=InMemoryCacheManager(),
        token_counter=GenericApproxCounter(),
    )
    return builder, mock_search


@pytest.mark.asyncio
async def test_5_layers_all_injected(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    mock_search.return_value = [
        make_memory_hint(layer="system", summary="sys note"),
        make_memory_hint(layer="tenant", summary="tenant rule"),
        make_memory_hint(layer="role", summary="role pref"),
        make_memory_hint(layer="user", summary="user history"),
        make_memory_hint(layer="session", summary="session ctx"),
    ]
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "query")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    used = artifact.layer_metadata["memory_layers_used"]
    assert set(used) == {"system", "tenant", "role", "user", "session"}


@pytest.mark.asyncio
async def test_3_time_scales_ordered_long_term_first(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    mock_search.return_value = [
        make_memory_hint(layer="user", time_scale="short_term", summary="recent"),
        make_memory_hint(layer="user", time_scale="long_term", summary="durable"),
        make_memory_hint(layer="user", time_scale="semantic", summary="vector"),
    ]
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    user_memory_msg = next(m for m in artifact.messages if m.metadata.get("memory_layer") == "user")
    content = str(user_memory_msg.content)
    long_idx = content.index("durable")
    sem_idx = content.index("vector")
    short_idx = content.index("recent")
    assert long_idx < sem_idx < short_idx


@pytest.mark.asyncio
async def test_memory_retrieval_failure_degrades_gracefully(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    mock_search.side_effect = RuntimeError("DB connection lost")
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    assert artifact.layer_metadata["memory_layers_used"] == []
    assert any(m.role == "system" for m in artifact.messages)


@pytest.mark.asyncio
async def test_layer_metadata_records_used_layers(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    mock_search.return_value = [
        make_memory_hint(layer="tenant", summary="rule"),
        make_memory_hint(layer="user", summary="history"),
    ]
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    used = artifact.layer_metadata["memory_layers_used"]
    assert set(used) == {"tenant", "user"}
    assert "system" not in used
    assert "role" not in used


@pytest.mark.asyncio
async def test_cross_tenant_no_leak(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    tenant_a = uuid4()
    tenant_b = uuid4()

    async def per_tenant_search(**kwargs: object) -> list[object]:
        tid = kwargs.get("tenant_id")
        if tid == tenant_a:
            return [make_memory_hint(layer="tenant", summary="TENANT-A-SECRET")]
        if tid == tenant_b:
            return [make_memory_hint(layer="tenant", summary="TENANT-B-PUBLIC")]
        return []

    mock_search.side_effect = per_tenant_search

    state_a = make_state(messages=[msg("user", "a")], tenant_id=tenant_a)
    artifact_a = await builder.build(state=state_a, tenant_id=tenant_a)
    a_content = " ".join(str(m.content) for m in artifact_a.messages)

    state_b = make_state(messages=[msg("user", "b")], tenant_id=tenant_b)
    artifact_b = await builder.build(state=state_b, tenant_id=tenant_b)
    b_content = " ".join(str(m.content) for m in artifact_b.messages)

    assert "TENANT-A-SECRET" in a_content
    assert "TENANT-A-SECRET" not in b_content
    assert "TENANT-B-PUBLIC" in b_content
    assert "TENANT-B-PUBLIC" not in a_content


@pytest.mark.asyncio
async def test_cross_user_no_leak(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    tenant_id = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    async def per_user_search(**kwargs: object) -> list[object]:
        uid = kwargs.get("user_id")
        if uid == user_a:
            return [make_memory_hint(layer="user", summary="USER-A-NOTE")]
        if uid == user_b:
            return [make_memory_hint(layer="user", summary="USER-B-NOTE")]
        return []

    mock_search.side_effect = per_user_search

    state_a = make_state(messages=[msg("user", "a")], tenant_id=tenant_id, user_id=user_a)
    artifact_a = await builder.build(state=state_a, tenant_id=tenant_id, user_id=user_a)
    a_content = " ".join(str(m.content) for m in artifact_a.messages)

    state_b = make_state(messages=[msg("user", "b")], tenant_id=tenant_id, user_id=user_b)
    artifact_b = await builder.build(state=state_b, tenant_id=tenant_id, user_id=user_b)
    b_content = " ".join(str(m.content) for m in artifact_b.messages)

    assert "USER-A-NOTE" in a_content
    assert "USER-A-NOTE" not in b_content
    assert "USER-B-NOTE" in b_content


@pytest.mark.asyncio
async def test_cross_session_no_leak(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    tenant_id = uuid4()

    state_a = make_state(messages=[msg("user", "a")], tenant_id=tenant_id)
    state_b = make_state(messages=[msg("user", "b")], tenant_id=tenant_id)
    session_a = state_a.durable.session_id
    session_b = state_b.durable.session_id

    async def per_session_search(**kwargs: object) -> list[object]:
        sid = kwargs.get("session_id")
        if sid == session_a:
            return [make_memory_hint(layer="session", summary="SESSION-A-CTX")]
        if sid == session_b:
            return [make_memory_hint(layer="session", summary="SESSION-B-CTX")]
        return []

    mock_search.side_effect = per_session_search

    artifact_a = await builder.build(state=state_a, tenant_id=tenant_id)
    a_content = " ".join(str(m.content) for m in artifact_a.messages)
    artifact_b = await builder.build(state=state_b, tenant_id=tenant_id)
    b_content = " ".join(str(m.content) for m in artifact_b.messages)

    assert "SESSION-A-CTX" in a_content
    assert "SESSION-A-CTX" not in b_content
    assert "SESSION-B-CTX" in b_content


@pytest.mark.asyncio
async def test_no_process_wide_cache(
    builder_and_search: tuple[DefaultPromptBuilder, AsyncMock],
) -> None:
    builder, mock_search = builder_and_search
    mock_search.return_value = []
    tenant_id = uuid4()

    state1 = make_state(messages=[msg("user", "first")], tenant_id=tenant_id)
    state2 = make_state(messages=[msg("user", "second")], tenant_id=tenant_id)
    state3 = make_state(messages=[msg("user", "third")], tenant_id=tenant_id)

    await builder.build(state=state1, tenant_id=tenant_id)
    await builder.build(state=state2, tenant_id=tenant_id)
    await builder.build(state=state3, tenant_id=tenant_id)

    assert mock_search.call_count == 3


# ---------------------------------------------------------------------------
# Sprint 57.148 (memory-formation Slice 1): always-on user-profile injection.
# search() is ILIKE query-gated — it surfaces a user fact ONLY when the current
# message keyword-matches it, so a "who am I?" question retrieves nothing.
# profile() pulls the user's standing durable facts regardless of the query.
# ---------------------------------------------------------------------------


@pytest.fixture
def builder_with_profile() -> tuple[DefaultPromptBuilder, AsyncMock, AsyncMock]:
    """Builder whose search() AND profile() are mocked independently."""
    retrieval = MemoryRetrieval(layers={})
    mock_search = AsyncMock(return_value=[])
    mock_profile = AsyncMock(return_value=[])
    retrieval.search = mock_search  # type: ignore[method-assign]
    retrieval.profile = mock_profile  # type: ignore[method-assign]
    builder = DefaultPromptBuilder(
        memory_retrieval=retrieval,
        cache_manager=InMemoryCacheManager(),
        token_counter=GenericApproxCounter(),
    )
    return builder, mock_search, mock_profile


@pytest.mark.asyncio
async def test_profile_injected_even_when_query_mismatches(
    builder_with_profile: tuple[DefaultPromptBuilder, AsyncMock, AsyncMock],
) -> None:
    """The headline fix: identity surfaces although the message shares no keyword."""
    builder, mock_search, mock_profile = builder_with_profile
    mock_search.return_value = []  # query-gated path finds nothing for "who am I?"
    mock_profile.return_value = [
        make_memory_hint(layer="user", summary="name is Chris, building the knowledge connector"),
    ]
    tenant_id = uuid4()
    user_id = uuid4()
    state = make_state(
        messages=[msg("user", "你知道我是誰嗎?")], tenant_id=tenant_id, user_id=user_id
    )

    artifact = await builder.build(state=state, tenant_id=tenant_id, user_id=user_id)

    content = " ".join(str(m.content) for m in artifact.messages)
    assert "name is Chris" in content
    mock_profile.assert_awaited_once()
    assert mock_profile.await_args.kwargs["user_id"] == user_id
    assert mock_profile.await_args.kwargs["tenant_id"] == tenant_id


@pytest.mark.asyncio
async def test_profile_not_pulled_without_user_id(
    builder_with_profile: tuple[DefaultPromptBuilder, AsyncMock, AsyncMock],
) -> None:
    """No user_id (anonymous / legacy caller) → profile() never dispatched."""
    builder, _mock_search, mock_profile = builder_with_profile
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "hi")], tenant_id=tenant_id)  # user_id None

    await builder.build(state=state, tenant_id=tenant_id)

    mock_profile.assert_not_awaited()


@pytest.mark.asyncio
async def test_profile_deduped_against_query_gated_hints(
    builder_with_profile: tuple[DefaultPromptBuilder, AsyncMock, AsyncMock],
) -> None:
    """A fact returned by BOTH search and profile renders once (dedup by hint_id)."""
    builder, mock_search, mock_profile = builder_with_profile
    shared = make_memory_hint(layer="user", summary="name is Chris")
    mock_search.return_value = [shared]
    mock_profile.return_value = [shared]
    tenant_id = uuid4()
    user_id = uuid4()
    state = make_state(messages=[msg("user", "Chris")], tenant_id=tenant_id, user_id=user_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id, user_id=user_id)

    user_msg = next(m for m in artifact.messages if m.metadata.get("memory_layer") == "user")
    assert str(user_msg.content).count("name is Chris") == 1


@pytest.mark.asyncio
async def test_profile_failure_degrades_gracefully(
    builder_with_profile: tuple[DefaultPromptBuilder, AsyncMock, AsyncMock],
) -> None:
    """profile() raising must not crash build() (W3-2 degrade theme)."""
    builder, mock_search, mock_profile = builder_with_profile
    mock_search.return_value = []
    mock_profile.side_effect = RuntimeError("DB down")
    tenant_id = uuid4()
    user_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id, user_id=user_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id, user_id=user_id)

    assert any(m.role == "system" for m in artifact.messages)
