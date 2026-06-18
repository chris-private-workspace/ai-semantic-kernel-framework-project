"""
File: backend/src/agent_harness/tools/exec_tools.py
Purpose: python_sandbox built-in tool (ToolSpec + handler).
Category: 範疇 2 (Tool Layer)
Scope: Phase 51 / Sprint 51.1 Day 3.4
Created: 2026-04-30
Last Modified: 2026-06-18

Modification History (newest-first):
    - 2026-06-18: FIX-033 — description: script-not-REPL must-print() + numpy-available hint
    - 2026-04-30: Initial creation (Sprint 51.1 Day 3.4)
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from agent_harness._contracts import (
    ConcurrencyPolicy,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)

from .sandbox import SandboxBackend, SubprocessSandbox

ToolHandler = Callable[[ToolCall], Awaitable[str]]

PYTHON_SANDBOX_SPEC: ToolSpec = ToolSpec(
    name="python_sandbox",
    description=(
        "Execute Python code in an isolated, wall-time / memory-limited sandbox "
        "(Docker container when available). Returns JSON with stdout / stderr / "
        "exit_code / duration_seconds / killed_by_timeout. IMPORTANT: the code "
        "runs as a SCRIPT (python <file>), NOT a REPL — a bare final expression "
        "is NOT shown. You MUST call print() on any value you want to read back "
        "in stdout. numpy is available. Use for ad-hoc computation; not for "
        "filesystem or network side-effects."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to execute. Must be self-contained.",
                "minLength": 1,
            },
            "timeout_seconds": {
                "type": "number",
                "description": "Wall-time limit (default 5).",
                "minimum": 0.1,
                "maximum": 30,
                "default": 5,
            },
            "memory_mb": {
                "type": "integer",
                "description": "Memory cap in MiB (POSIX only; default 256).",
                "minimum": 16,
                "maximum": 1024,
                "default": 256,
            },
        },
        "required": ["code"],
    },
    annotations=ToolAnnotations(
        read_only=False,
        destructive=False,  # subprocess is sandboxed; not directly destructive to host
        idempotent=False,
        open_world=False,
    ),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.MEDIUM,  # arbitrary code execution = medium risk even sandboxed
    tags=("builtin", "exec"),
)


def make_python_sandbox_handler(backend: SandboxBackend | None = None) -> ToolHandler:
    """Factory returning an async handler bound to a SandboxBackend."""
    sandbox = backend or SubprocessSandbox()

    async def _handler(call: ToolCall) -> str:
        code = str(call.arguments["code"])
        timeout = float(call.arguments.get("timeout_seconds", 5))
        memory = int(call.arguments.get("memory_mb", 256))
        result = await sandbox.execute(
            code,
            timeout_seconds=timeout,
            memory_mb=memory,
            network_blocked=True,
        )
        return json.dumps(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "duration_seconds": round(result.duration_seconds, 3),
                "killed_by_timeout": result.killed_by_timeout,
            }
        )

    return _handler
