"""
File: backend/tests/e2e/test_agent_loop_with_mock_patrol.py
Purpose: Sprint 51.0 acceptance e2e — agent loop drives mock_patrol_check_servers via real httpx + mock_services subprocess.  # noqa: E501
Category: Tests / e2e / Sprint 51.0 acceptance gate
Scope: Phase 51 / Sprint 51.0 Day 4.5

Description:
    Sprint 51.0 acceptance criterion (per sprint-51-0-plan.md §US-1, §US-4):
        user message "patrol web-01" -> AgentLoop.run() ->
        MockChatClient yields tool_call mock_patrol_check_servers ->
        registered handler calls PatrolMockExecutor via real httpx ->
        mock_services subprocess returns mock JSON for web-01 ->
        loop reaches END_TURN with summary content.

    Unlike test_business_tools_via_registry (in-process ASGI), THIS test runs
    a real uvicorn subprocess on port 8001 to verify the full deployment chain
    works as Phase 55 真實 enterprise integration would.

    Marked `slow` — startup ~3s; not part of fast unit suite.

Created: 2026-04-30 (Sprint 51.0 Day 4)
Last Modified: 2026-04-30
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    LoopCompleted,
    StopReason,
    ToolCall,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
)
from agent_harness.orchestrator_loop import AgentLoopImpl, TerminationReason
from agent_harness.output_parser import OutputParserImpl
from business_domain._register_all import make_default_executor

PORT = 8001
HEALTH_URL = f"http://localhost:{PORT}/health"
BACKEND_SRC = Path(__file__).resolve().parents[2] / "src"


@pytest.fixture(scope="module")
def mock_services_subprocess() -> Iterator[None]:
    """Spawn `uvicorn mock_services.main:app --port 8001` for the test module."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_SRC) + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mock_services.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=BACKEND_SRC,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0),
    )

    # Poll /health for up to 15s
    started = False
    for _ in range(30):
        try:
            with urlopen(HEALTH_URL, timeout=1) as resp:
                if resp.status == 200:
                    started = True
                    break
        except URLError:
            pass
        except Exception:
            pass
        time.sleep(0.5)

    if not started:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        pytest.fail("mock_services did not become healthy within 15s")

    try:
        yield
    finally:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.mark.slow
@pytest.mark.asyncio
async def test_agent_loop_calls_mock_patrol_via_real_subprocess(
    mock_services_subprocess: None,
) -> None:
    """Sprint 51.0 acceptance: TAO loop -> mock_patrol_check_servers -> real HTTP -> mock JSON -> END_TURN."""  # noqa: E501
    registry, executor = make_default_executor()

    # Pre-scripted MockChatClient: turn 1 calls patrol, turn 2 ends with summary
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="m",
                content="Calling patrol on web-01.",
                tool_calls=[
                    ToolCall(
                        id="call_p1",
                        name="mock_patrol_check_servers",
                        arguments={"scope": ["web-01"]},
                    )
                ],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(
                model="m",
                content="web-01 is healthy.",
                stop_reason=StopReason.END_TURN,
            ),
        ]
    )

    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        system_prompt="You are an SRE agent.",
        max_turns=5,
        token_budget=10_000,
    )

    sid = uuid4()
    events = [ev async for ev in loop.run(session_id=sid, user_input="please patrol server web-01")]

    # ToolCallRequested fires for mock_patrol_check_servers
    requested = [e for e in events if isinstance(e, ToolCallRequested)]
    assert len(requested) == 1
    assert requested[0].tool_name == "mock_patrol_check_servers"
    assert requested[0].arguments == {"scope": ["web-01"]}

    # ToolCallExecuted carries mock JSON; result content includes web-01 + health
    failed = [e for e in events if isinstance(e, ToolCallFailed)]
    assert failed == [], f"unexpected ToolCallFailed events: {failed}"
    executed = [e for e in events if isinstance(e, ToolCallExecuted)]
    assert len(executed) == 1
    result_str = executed[0].result_content or ""
    parsed = json.loads(result_str)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["server_id"] == "web-01"
    assert parsed[0]["health"] in ("ok", "warning", "critical")

    # Loop terminates END_TURN. Sprint 57.75 (A-5c): the loop now trails the
    # public LoopCompleted with a diagnostic SpanEnded(LOOP) (span closes in the
    # finally after the body), so select LoopCompleted explicitly, not events[-1].
    completed = next(e for e in events if isinstance(e, LoopCompleted))
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.END_TURN.value


@pytest.mark.slow
def test_mock_services_health_via_subprocess(mock_services_subprocess: None) -> None:
    """Sanity: subprocess fixture really brought up port 8001 with seed loaded."""
    with urlopen(HEALTH_URL, timeout=2) as resp:
        assert resp.status == 200
        payload = json.loads(resp.read().decode())
        assert payload["status"] == "ok"
        assert payload["db_stats"]["customers"] == 10
        assert payload["db_stats"]["incidents"] == 5
