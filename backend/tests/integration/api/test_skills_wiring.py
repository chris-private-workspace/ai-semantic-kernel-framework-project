"""
File: backend/tests/integration/api/test_skills_wiring.py
Purpose: Integration tests for Sprint 57.113 Skills wiring (executor + prompt block + read_skill).
Category: Tests / integration / api
Scope: Phase 57 / Sprint 57.113

Description:
    Azure-call-free (the 57.64 keystone pattern): monkeypatch fake AZURE_OPENAI_*
    so build_handler/build_real_llm_handler constructs an AzureOpenAIAdapter config
    object (no network), then swap loop._chat_client for a MockChatClient before
    run() so the SSE flow is scripted.

    - Executor opt-in: make_default_executor(skill_registry=reg) registers read_skill
      (in registry.list()); without a registry it is absent (AP-2/AP-4 negative guard).
    - read_skill executes through the real ToolExecutorImpl returning the framed
      instructions.
    - build_handler(skill_registry=reg) appends the catalog block to the loop's
      system prompt; build_handler(no registry) leaves it byte-identical (regression).
    - A scripted read_skill tool call ToolCallExecuted carries the skill instructions
      on the live chat SSE flow (the model-invoked lazy-load, end-to-end).

Created: 2026-06-13 (Sprint 57.113)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    StopReason,
    TokenUsage,
    ToolCall,
)
from agent_harness._contracts.events import ToolCallExecuted
from agent_harness.skills.registry import Skill, SkillRegistry, get_default_skill_registry
from api.v1.chat.handler import DEMO_SYSTEM_PROMPT, build_handler
from business_domain._register_all import make_default_executor

_FAKE_AZURE_ENV = {
    "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "fake-key-not-used",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "fake-deploy",
}


def _set_fake_azure(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _FAKE_AZURE_ENV.items():
        monkeypatch.setenv(k, v)
    # Disable the in-loop verifier (its own ChatClient is the fake-Azure adapter) so
    # the scripted MockChatClient drives the flow (the 57.64/57.98 keystone pattern).
    monkeypatch.setenv("CHAT_VERIFICATION_MODE", "disabled")
    from core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    from core.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


def _final_response(text: str = "done") -> ChatResponse:
    return ChatResponse(
        model="mock",
        content=text,
        stop_reason=StopReason.END_TURN,
        tool_calls=None,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


def _tool_call_response(name: str, arguments: dict, call_id: str) -> ChatResponse:
    return ChatResponse(
        model="mock",
        content="",
        stop_reason=StopReason.TOOL_USE,
        tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


def _small_registry() -> SkillRegistry:
    reg = SkillRegistry()
    reg.register(
        Skill(name="code-review", description="Review code", instructions="Do the review.")
    )
    return reg


# ============================================================
# Executor opt-in — read_skill registered only when a registry is supplied
# ============================================================


def test_make_default_executor_registers_read_skill_when_given() -> None:
    registry, _executor = make_default_executor(skill_registry=_small_registry())
    assert registry.get("read_skill") is not None
    assert any(s.name == "read_skill" for s in registry.list())


def test_make_default_executor_no_read_skill_without_registry() -> None:
    # AP-2/AP-4 negative guard: read_skill is present ONLY when a registry is wired.
    registry, _executor = make_default_executor()
    assert registry.get("read_skill") is None


@pytest.mark.asyncio
async def test_read_skill_executes_through_executor() -> None:
    _registry, executor = make_default_executor(skill_registry=_small_registry())
    res = await executor.execute(
        ToolCall(id="r", name="read_skill", arguments={"name": "code-review"})
    )
    assert res.success is True
    assert "# Skill: code-review" in res.content
    assert "Do the review." in res.content


# ============================================================
# build_handler — the catalog block rides the system_prompt seam
# ============================================================


def test_build_handler_appends_skills_block_to_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_fake_azure(monkeypatch)
    loop = build_handler("real_llm", "review this", skill_registry=get_default_skill_registry())
    system_prompt = loop._system_prompt  # type: ignore[attr-defined]
    assert "## Available Skills" in system_prompt
    assert "code-review" in system_prompt
    assert "summarize" in system_prompt
    assert "read_skill(name)" in system_prompt


def test_build_handler_no_block_without_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    # Regression: with no skill registry the system prompt is byte-identical (no block).
    _set_fake_azure(monkeypatch)
    loop = build_handler("real_llm", "hello")
    assert loop._system_prompt == DEMO_SYSTEM_PROMPT  # type: ignore[attr-defined]
    assert "## Available Skills" not in loop._system_prompt  # type: ignore[attr-defined]


# ============================================================
# Chat SSE flow — a scripted read_skill call executes end-to-end (lazy-load)
# ============================================================


@pytest.mark.asyncio
async def test_chat_path_read_skill_executes(monkeypatch: pytest.MonkeyPatch) -> None:
    """A model-emitted read_skill tool call returns the skill instructions on the SSE flow."""
    _set_fake_azure(monkeypatch)
    session_id = uuid4()
    tenant_id = uuid4()
    loop = build_handler(
        "real_llm",
        "review my code",
        session_id=session_id,
        tenant_id=tenant_id,
        skill_registry=get_default_skill_registry(),
    )
    loop._chat_client = MockChatClient(  # type: ignore[attr-defined]
        responses=[
            _tool_call_response("read_skill", {"name": "code-review"}, "call_r"),
            _final_response("review done"),
        ]
    )

    events = [ev async for ev in loop.run(session_id=session_id, user_input="review my code")]
    executed = [ev for ev in events if isinstance(ev, ToolCallExecuted)]
    read = [ev for ev in executed if ev.tool_name == "read_skill"]
    assert len(read) == 1
    assert "# Skill: code-review" in read[0].result_content
    assert "Follow these instructions" in read[0].result_content
