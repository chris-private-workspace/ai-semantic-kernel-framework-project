"""
File: backend/tests/integration/api/test_skills_wiring.py
Purpose: Integration tests for Skills wiring (executor + prompt + read_skill / run_skill_script).
Category: Tests / integration / api
Scope: Phase 57 / Sprint 57.113 (read_skill) + 57.118 (run_skill_script)

Description:
    Azure-call-free (the 57.64 keystone pattern): monkeypatch fake AZURE_OPENAI_*
    so build_handler/build_real_llm_handler constructs an AzureOpenAIAdapter config
    object (no network), then swap loop._chat_client for a MockChatClient before
    run() so the SSE flow is scripted.

    - Executor opt-in: make_default_executor(skill_registry=reg) registers read_skill
      + run_skill_script (in registry.list()); without a registry both are absent
      (AP-2/AP-4 negative guard).
    - read_skill executes through the real ToolExecutorImpl returning the framed
      instructions.
    - run_skill_script (57.118) runs the bundled 'digest' skill's script in a REAL
      SubprocessSandbox and returns the computed sha256 (provably script-produced).
    - build_handler(skill_registry=reg) appends the catalog block to the loop's
      system prompt; build_handler(no registry) leaves it byte-identical (regression).
    - A scripted read_skill tool call ToolCallExecuted carries the skill instructions
      on the live chat SSE flow (the model-invoked lazy-load, end-to-end).

Created: 2026-06-13 (Sprint 57.113)
Last Modified: 2026-06-15

Modification History (newest-first):
    - 2026-06-15: Sprint 57.118 — run_skill_script registration + real-sandbox demo-script run
    - 2026-06-13: Initial creation (Sprint 57.113)
"""

from __future__ import annotations

import hashlib
import json
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
from agent_harness.skills.tool import make_run_skill_script_handler
from agent_harness.tools.memory_tools import MEMORY_FORMATION_NUDGE
from agent_harness.tools.sandbox import SubprocessSandbox
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


def test_make_default_executor_registers_run_skill_script_when_given() -> None:
    # Sprint 57.118: the skill_registry opt-in also registers run_skill_script.
    registry, _executor = make_default_executor(skill_registry=_small_registry())
    assert registry.get("run_skill_script") is not None
    assert any(s.name == "run_skill_script" for s in registry.list())


def test_make_default_executor_no_run_skill_script_without_registry() -> None:
    # AP-2/AP-4 negative guard: run_skill_script is present ONLY when a registry is wired.
    registry, _executor = make_default_executor()
    assert registry.get("run_skill_script") is None


@pytest.mark.asyncio
async def test_read_skill_executes_through_executor() -> None:
    _registry, executor = make_default_executor(skill_registry=_small_registry())
    res = await executor.execute(
        ToolCall(id="r", name="read_skill", arguments={"name": "code-review"})
    )
    assert res.success is True
    assert "# Skill: code-review" in res.content
    assert "Do the review." in res.content


@pytest.mark.asyncio
async def test_run_skill_script_runs_bundled_digest_in_real_sandbox() -> None:
    """The bundled 'digest' skill's script runs in a REAL SubprocessSandbox and returns
    the computed sha256 — a value the model cannot fabricate (the execution proof).

    An explicit SubprocessSandbox is injected (runs on Windows + Docker-less CI,
    deterministic) rather than the lazy default_sandbox() process-wide singleton.
    """
    handler = make_run_skill_script_handler(
        get_default_skill_registry(), sandbox=SubprocessSandbox()
    )
    out = await handler(
        ToolCall(id="d", name="run_skill_script", arguments={"skill_name": "digest"})
    )
    payload = json.loads(out)
    expected = hashlib.sha256(b"agent-harness-bundled-skill").hexdigest()
    assert payload["exit_code"] == 0
    assert payload["stdout"].strip() == expected  # provably script-produced


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
    # Regression: with no skill registry, NO skills catalog block is appended (the base
    # is unchanged). Sprint 57.148: the memory-formation nudge IS appended on the real_llm
    # path (memory tools are always wired) so the prompt is DEMO + nudge, NOT byte-identical
    # to DEMO — the skills block specifically must stay absent.
    _set_fake_azure(monkeypatch)
    loop = build_handler("real_llm", "hello")
    sp = loop._system_prompt  # type: ignore[attr-defined]
    assert sp.startswith(DEMO_SYSTEM_PROMPT)  # base role unchanged
    assert "## Available Skills" not in sp  # no skills catalog block
    assert "read_skill(name)" not in sp
    assert MEMORY_FORMATION_NUDGE in sp  # 57.148: memory-formation nudge expected on real path


# ============================================================
# Sprint 57.115 — force-load (/skill-name slash command): the "## Active Skill"
# block injects the picked skill's FULL instructions deterministically.
# ============================================================


def test_build_handler_force_load_appends_active_skill_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_fake_azure(monkeypatch)
    loop = build_handler(
        "real_llm",
        "review this",
        skill_registry=get_default_skill_registry(),
        force_load_skill="code-review",
    )
    system_prompt = loop._system_prompt  # type: ignore[attr-defined]
    # The deterministic force-load section + the full instruction body.
    assert "## Active Skill" in system_prompt
    assert 'selected the "code-review" skill' in system_prompt
    assert "# Skill: code-review" in system_prompt
    # The catalog block stays (force-load is additive, not a replacement).
    assert "## Available Skills" in system_prompt


def test_build_handler_force_load_none_no_active_block(monkeypatch: pytest.MonkeyPatch) -> None:
    # No force_load_skill → catalog block only, no "## Active Skill" (byte-identical
    # to the 57.113 model-invoked path).
    _set_fake_azure(monkeypatch)
    loop = build_handler(
        "real_llm",
        "review this",
        skill_registry=get_default_skill_registry(),
    )
    assert "## Active Skill" not in loop._system_prompt  # type: ignore[attr-defined]
    assert "## Available Skills" in loop._system_prompt  # type: ignore[attr-defined]


def test_build_handler_force_load_unknown_name_graceful(monkeypatch: pytest.MonkeyPatch) -> None:
    # An unknown / stale force_load_skill → no "## Active Skill" block (graceful;
    # build_handler defensively re-checks the registry even though the router pre-validates).
    _set_fake_azure(monkeypatch)
    loop = build_handler(
        "real_llm",
        "review this",
        skill_registry=get_default_skill_registry(),
        force_load_skill="does-not-exist",
    )
    assert "## Active Skill" not in loop._system_prompt  # type: ignore[attr-defined]
    assert "## Available Skills" in loop._system_prompt  # type: ignore[attr-defined]


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
