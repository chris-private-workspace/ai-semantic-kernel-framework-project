"""
File: backend/src/agent_harness/guardrails/tool/risky_action_detector.py
Purpose: RiskyActionDetector — TOOL-chain guardrail screening sandbox code + tenant patterns.
Category: 範疇 9 (Guardrails & Safety)
Scope: Sprint 57.106 (C3 — per-tenant harness policy + risky-action detector)

Description:
    The server-side equivalent of Claude Code's bashSecurity check: before a
    tool_call executes, screen it for risky patterns and ESCALATE (never BLOCK)
    into the existing Cat 9 HITL approval flow — a human decides, the agent run
    pauses instead of silently failing. Two scopes per check:

    1. python_sandbox code screening — the sandbox executes arbitrary code with
       hitl_policy=AUTO today (exec_tools.py — zero approval); the builtin
       deny-list catches process/filesystem/network/dynamic-exec primitives.
    2. Tenant extra patterns — per-tenant regexes (from HarnessPolicy via the
       chat handler) matched against the serialized arguments of ANY tool.

    Per-tenant off-switch is handler-level: a disabled tenant simply does not
    register this guardrail (zero-cost off). Patterns are pre-compiled at ctor;
    the admin PUT validates compile + count/length caps before they reach here.

Security model (Sprint 57.137 reframe — AD-Guardrail-Detect-To-Restrict / research #3):
    This regex deny-list is an ESCALATE-for-VISIBILITY layer, NOT the security
    boundary. A blocklist of code patterns is a losing cat-and-mouse (57.110's
    drive-through caught a child rewriting a blocked os.system as os.popen → a new
    pattern had to be added; equivalent encodings — getattr / importlib / split
    literals / unlisted egress primitives like urllib/http.client — are unbounded;
    measured escape rate 60% in benchmark_sandbox_escape). The actual boundary is
    the STRUCTURAL python_sandbox isolation (DockerSandbox: network none / read-only
    rootfs / cap-drop ALL / non-root / no bind mounts — measured 100% containment),
    made MANDATORY by the SANDBOX_REQUIRE_ISOLATION fail-closed gate (sandbox.py /
    default_sandbox). This detector's residual value is (a) a human SEES a flagged
    attempt (ESCALATE → HITL) and (b) per-tenant extra_patterns flag tenant-specific
    args — neither is a containment guarantee. Do NOT treat the patterns as a
    primary defense or expand them in a pattern-chasing arms race.

Key Components:
    - RiskyActionDetector: Guardrail (guardrail_type=TOOL); ctor takes extra_patterns
    - DEFAULT_SANDBOX_PATTERNS: conservative builtin deny-list (regex, word-bounded)

Created: 2026-06-12 (Sprint 57.106)
Last Modified: 2026-06-24

Modification History (newest-first):
    - 2026-06-24: Sprint 57.137 — reframe as ESCALATE-visibility not boundary (no behavior change)
    - 2026-06-13: Sprint 57.110 B4 — +os.popen/os.spawn*/os.exec* (dt found the popen bypass)
    - 2026-06-12: Initial creation (Sprint 57.106 C3) — risky-action TOOL guardrail

Related:
    - agent_harness/guardrails/_abc.py — Guardrail ABC + GuardrailResult/Action
    - agent_harness/guardrails/input/escalation_keyword_detector.py — mirrored ctor pattern
    - agent_harness/tools/exec_tools.py — python_sandbox spec (the screened tool)
    - platform_layer/governance/harness_policy.py — extra_patterns source (via handler)
    - api/v1/chat/handler.py — registration site (priority 8, before ToolGuardrail)
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

from agent_harness._contracts import TraceContext
from agent_harness.guardrails._abc import (
    Guardrail,
    GuardrailAction,
    GuardrailResult,
    GuardrailType,
)

# === DEFAULT_SANDBOX_PATTERNS: builtin deny-list for python_sandbox code ========
# Why: conservative, word-bounded patterns over the raw code string. Each entry
# targets a primitive that lets sandbox code touch the host process / filesystem /
# network or evade static review (dynamic exec). False positives are acceptable by
# design — the detector ESCALATEs into a human approval, it never BLOCKs, so a
# legitimate hit costs one click. Near-misses (evaluate(, execute_query() do NOT
# match (\b + literal '(' anchoring); see test_risky_action_detector.py.
# NOTE (Sprint 57.137): this list is intentionally INCOMPLETE — a visibility
# tripwire, NOT an exhaustive boundary (measured 60% escape; see module docstring
# §Security model). Containment is DockerSandbox's job; do NOT pattern-chase here.
DEFAULT_SANDBOX_PATTERNS: tuple[str, ...] = (
    r"\bos\.system\s*\(",
    # Sprint 57.110 (B4 dt D-DAY3-1): the 57.110 drive-through showed a child
    # agent rewriting a blocked os.system call as os.popen — cover the whole
    # process-exec family, not just os.system.
    r"\bos\.popen\s*\(",
    r"\bos\.(?:spawn|exec)\w*\s*\(",
    r"\bos\.(?:remove|unlink|rmdir|removedirs)\s*\(",
    r"\bsubprocess\b",
    r"\bshutil\.rmtree\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__",
    r"\bsocket\b",
    r"\bctypes\b",
)

_SANDBOX_TOOL_NAME = "python_sandbox"


class RiskyActionDetector(Guardrail):
    """Tool guardrail: ESCALATE risky python_sandbox code / tenant-flagged args.

    Args:
        extra_patterns: tenant-supplied regexes matched against the serialized
            arguments of ANY tool (pre-validated by the admin PUT). Empty → only
            the builtin sandbox screening runs.
        sandbox_tool_name: the code-exec tool the builtin deny-list applies to.
    """

    guardrail_type = GuardrailType.TOOL

    def __init__(
        self,
        *,
        extra_patterns: Sequence[str] = (),
        sandbox_tool_name: str = _SANDBOX_TOOL_NAME,
    ) -> None:
        self._sandbox_tool_name = sandbox_tool_name
        self._sandbox_patterns: tuple[re.Pattern[str], ...] = tuple(
            re.compile(p) for p in DEFAULT_SANDBOX_PATTERNS
        )
        # Invalid tenant patterns are skipped defensively (the PUT validates
        # compile, but a hand-written meta_data row must not break the chain).
        compiled: list[re.Pattern[str]] = []
        for raw in extra_patterns:
            try:
                compiled.append(re.compile(raw))
            except re.error:
                continue
        self._extra_patterns: tuple[re.Pattern[str], ...] = tuple(compiled)

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        name = getattr(content, "name", None)
        arguments = getattr(content, "arguments", None)
        if not isinstance(name, str) or not isinstance(arguments, dict):
            return GuardrailResult(action=GuardrailAction.PASS)

        # Scope 1: builtin deny-list over the sandbox tool's code argument.
        if name == self._sandbox_tool_name:
            code = arguments.get("code")
            if isinstance(code, str):
                for pattern in self._sandbox_patterns:
                    if pattern.search(code):
                        return GuardrailResult(
                            action=GuardrailAction.ESCALATE,
                            reason=(f"risky_action: sandbox code matched " f"{pattern.pattern!r}"),
                            risk_level="HIGH",
                        )

        # Scope 2: tenant extra patterns over ANY tool's serialized arguments.
        if self._extra_patterns:
            try:
                serialized = json.dumps(arguments, ensure_ascii=False, default=str)
            except (TypeError, ValueError):
                serialized = str(arguments)
            for pattern in self._extra_patterns:
                if pattern.search(serialized):
                    return GuardrailResult(
                        action=GuardrailAction.ESCALATE,
                        reason=(
                            f"risky_action: tool {name!r} arguments matched "
                            f"tenant pattern {pattern.pattern!r}"
                        ),
                        risk_level="HIGH",
                    )

        return GuardrailResult(action=GuardrailAction.PASS)
