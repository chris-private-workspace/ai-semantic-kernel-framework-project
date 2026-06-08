"""Tests for scripts/lint/check_ap1_pipeline_disguise.py — V2 Lint #5."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_lint_module() -> object:
    repo_root = Path(__file__).resolve().parents[5]
    script = repo_root / "scripts" / "lint" / "check_ap1_pipeline_disguise.py"
    spec = importlib.util.spec_from_file_location("check_ap1", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_loop_file(tmp: Path, body: str) -> Path:
    """Write a fake loop.py under tmp/agent_harness/orchestrator_loop/."""
    target = tmp / "agent_harness" / "orchestrator_loop" / "loop.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    # Need an __init__.py so the package looks real (not strictly required by
    # the lint, but matches production layout).
    (target.parent / "__init__.py").write_text("", encoding="utf-8")
    return target


VALID_LOOP_BODY = '''
"""fake loop"""
from collections.abc import AsyncIterator


class AgentLoopImpl:
    async def run(self) -> AsyncIterator[object]:
        turn = 0
        while True:
            if turn >= 5:
                break
            messages = []
            messages.append(Message(role="tool", tool_call_id="x", content=""))  # noqa
            turn += 1
        yield None


class Message:
    def __init__(self, **_kw): ...
'''

PIPELINE_FOR_BODY = '''
"""fake pipeline"""
from collections.abc import AsyncIterator


class AgentLoopImpl:
    async def run(self) -> AsyncIterator[object]:
        for step in [step1, step2, step3]:
            await step()
        messages = []
        messages.append(Message(role="tool", tool_call_id="x", content=""))  # noqa
        yield None


def step1(): ...
def step2(): ...
def step3(): ...
class Message:
    def __init__(self, **_kw): ...
'''

CONDITIONAL_WHILE_BODY = '''
"""while-conditional variant"""
from collections.abc import AsyncIterator


class StreamingAgentLoopImpl:
    async def run(self) -> AsyncIterator[object]:
        turn_count = 0
        max_turns = 5
        while turn_count < max_turns:
            turn_count += 1
            messages = []
            messages.append(Message(role="tool", tool_call_id="x", content=""))  # noqa
        yield None


class Message:
    def __init__(self, **_kw): ...
'''

NO_TOOL_FEEDBACK_BODY = '''
"""while loop but tool feedback intentionally absent"""
from collections.abc import AsyncIterator


class AgentLoopImpl:
    async def run(self) -> AsyncIterator[object]:
        while True:
            # tool feedback line intentionally absent (AP-1 part b violation)
            break
        yield None
'''

# Sprint 57.89: run() drives the while via a delegated re-enterable helper
# (_run_turns) — the loop lives one delegation hop away but still satisfies AP-1.
DELEGATED_WHILE_BODY = '''
"""run() delegates the while-loop to a re-enterable _run_turns helper (Sprint 57.89)."""
from collections.abc import AsyncIterator


class AgentLoopImpl:
    async def run(self) -> AsyncIterator[object]:
        async for ev in self._run_turns():
            yield ev

    async def _run_turns(self) -> AsyncIterator[object]:
        turn = 0
        while True:
            if turn >= 5:
                break
            messages = []
            messages.append(Message(role="tool", tool_call_id="x", content=""))  # noqa
            turn += 1
        yield None


class Message:
    def __init__(self, **_kw): ...
'''

# Sprint 57.89: delegation must NOT over-broaden — a run() that delegates to a
# helper with NO while loop (a real for-pipeline behind a helper) still fails.
DELEGATED_NO_WHILE_BODY = '''
"""run() delegates to a helper that has NO while loop → still AP-1 (pipeline)."""
from collections.abc import AsyncIterator


class AgentLoopImpl:
    async def run(self) -> AsyncIterator[object]:
        async for ev in self._run_steps():
            yield ev

    async def _run_steps(self) -> AsyncIterator[object]:
        for step in [step1, step2]:
            await step()
        messages = []
        messages.append(Message(role="tool", tool_call_id="x", content=""))  # noqa
        yield None


def step1(): ...
def step2(): ...
class Message:
    def __init__(self, **_kw): ...
'''


def test_pos_valid_while_loop_passes(tmp_path: Path) -> None:
    """AgentLoopImpl with `while True` + tool-message feedback → no violations."""
    mod = _load_lint_module()
    _write_loop_file(tmp_path, VALID_LOOP_BODY)
    target_file = tmp_path / "agent_harness" / "orchestrator_loop" / "loop.py"
    violations = mod.check_file(target_file)  # type: ignore[attr-defined]
    assert violations == []


def test_neg_for_step_pipeline_fails(tmp_path: Path) -> None:
    """Pipeline-style `for step in steps:` → AP-1 violation reported."""
    mod = _load_lint_module()
    _write_loop_file(tmp_path, PIPELINE_FOR_BODY)
    target_file = tmp_path / "agent_harness" / "orchestrator_loop" / "loop.py"
    violations = mod.check_file(target_file)  # type: ignore[attr-defined]
    assert any("must drive a `while` loop" in v for v in violations)


def test_variant_while_conditional_passes(tmp_path: Path) -> None:
    """`while turn_count < max_turns:` is a valid while form (not just `while True`)."""
    mod = _load_lint_module()
    _write_loop_file(tmp_path, CONDITIONAL_WHILE_BODY)
    target_file = tmp_path / "agent_harness" / "orchestrator_loop" / "loop.py"
    violations = mod.check_file(target_file)  # type: ignore[attr-defined]
    assert violations == []


def test_neg_missing_tool_feedback_fails(tmp_path: Path) -> None:
    """`while True` present but no `Message(role="tool"` → tool-feedback AP-1 violation."""
    mod = _load_lint_module()
    _write_loop_file(tmp_path, NO_TOOL_FEEDBACK_BODY)
    target_file = tmp_path / "agent_harness" / "orchestrator_loop" / "loop.py"
    violations = mod.check_file(target_file)  # type: ignore[attr-defined]
    assert any("Message(role" in v and "tool" in v for v in violations)


def test_pos_delegated_while_loop_passes(tmp_path: Path) -> None:
    """run() driving the while via a delegated _run_turns helper → no violations (Sprint 57.89)."""
    mod = _load_lint_module()
    _write_loop_file(tmp_path, DELEGATED_WHILE_BODY)
    target_file = tmp_path / "agent_harness" / "orchestrator_loop" / "loop.py"
    violations = mod.check_file(target_file)  # type: ignore[attr-defined]
    assert violations == []


def test_neg_delegated_no_while_still_fails(tmp_path: Path) -> None:
    """run() delegating to a helper with NO while is still a pipeline → AP-1 violation."""
    mod = _load_lint_module()
    _write_loop_file(tmp_path, DELEGATED_NO_WHILE_BODY)
    target_file = tmp_path / "agent_harness" / "orchestrator_loop" / "loop.py"
    violations = mod.check_file(target_file)  # type: ignore[attr-defined]
    assert any("must drive a `while` loop" in v for v in violations)
