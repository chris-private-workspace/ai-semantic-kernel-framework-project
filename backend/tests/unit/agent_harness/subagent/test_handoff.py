"""
File: backend/tests/unit/agent_harness/subagent/test_handoff.py
Purpose: Unit tests for the spec-only handoff trigger (make_handoff_spec) + dispatcher posture.
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-4 → converted Sprint 57.107 (B3 — HandoffExecutor stub retired)

Created: 2026-05-04 (Sprint 54.2)
Modified: 2026-06-12 (Sprint 57.107 — convert from HandoffExecutor/dispatcher.handoff tests)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import SubagentMode
from agent_harness.subagent import (
    DefaultSubagentDispatcher,
    SubagentLaunchError,
    make_handoff_spec,
)


@pytest.mark.asyncio
async def test_handoff_spec_handler_raises_if_invoked() -> None:
    """The handoff handler must never run — the loop classifier intercepts the
    tool_call (stop_reason='handoff') BEFORE execution. Reaching the handler
    means the interception was bypassed → loud RuntimeError (AP-4 guard)."""
    _, handler = make_handoff_spec(suggested_targets=["researcher"])
    with pytest.raises(RuntimeError, match="loop-intercepted"):
        await handler({"target_agent": "researcher"})


def test_handoff_spec_description_lists_targets() -> None:
    """The spec description enumerates the suggested targets (LLM guidance)."""
    spec, _ = make_handoff_spec(suggested_targets=["researcher", "planner"])
    assert "researcher" in spec.description
    assert "planner" in spec.description


def test_handoff_spec_empty_targets_hint() -> None:
    """No suggested targets → the description says none are configured."""
    spec, _ = make_handoff_spec(suggested_targets=[])
    assert "none configured" in spec.description


@pytest.mark.asyncio
async def test_dispatcher_spawn_handoff_mode_raises() -> None:
    """HANDOFF is not dispatcher-served (Sprint 57.107 convergence): spawn()
    with SubagentMode.HANDOFF raises SubagentLaunchError pointing at the
    loop-intercepted path."""
    dispatcher = DefaultSubagentDispatcher(chat_client=MockChatClient())
    with pytest.raises(SubagentLaunchError, match="loop-intercepted"):
        await dispatcher.spawn(
            mode=SubagentMode.HANDOFF,
            task="transfer control",
            parent_session_id=uuid4(),
        )
