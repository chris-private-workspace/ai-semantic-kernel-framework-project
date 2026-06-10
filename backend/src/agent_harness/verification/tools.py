"""
File: backend/src/agent_harness/verification/tools.py
Purpose: verify tool factory — let LLM self-trigger verification via ToolRegistry.
Category: 範疇 10 (Verification Loops; tool-layer bridge per 17.md §3.1)
Scope: Sprint 54.1 US-5

Description:
    Provides `make_verify_tool(registry)` factory returning a ToolSpec for
    the `verify` tool registered to Cat 2 ToolRegistry per 17.md §3.1.

    The LLM may invoke this tool mid-loop to ask for verification of a
    candidate output WITHOUT waiting for the loop's post-completion in-loop
    Cat 10 verify gate. Useful when the LLM wants to self-check
    before producing a final answer.

    Handler signature follows Cat 2 conventions:
      handler(args: dict[str, Any]) -> dict[str, Any]
    Returns:
      {
        "passed": bool,
        "results": [
          {"verifier": str, "passed": bool, "score": float | None,
           "reason": str | None, "suggested_correction": str | None,
           "verifier_type": str}, ...
        ]
      }

Owner: 範疇 10 (verification/) — registers into Cat 2 ToolRegistry per 17.md §3.1

Created: 2026-05-04 (Sprint 54.1 Day 4)
Last Modified: 2026-05-04

Modification History:
    - 2026-05-04: Initial (Sprint 54.1 US-5)

Related:
    - 17-cross-category-interfaces.md §3.1 — verify tool registry entry
    - registry.py — VerifierRegistry (provides the verifiers)
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, cast

from agent_harness._contracts import LoopState, RiskLevel
from agent_harness._contracts.tools import (
    ConcurrencyPolicy,
    ToolAnnotations,
    ToolHITLPolicy,
    ToolSpec,
)
from agent_harness.verification.registry import VerifierRegistry

VerifyToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


def make_verify_tool(
    registry: VerifierRegistry,
) -> tuple[ToolSpec, VerifyToolHandler]:
    """Build the `verify` tool spec + handler closure.

    Returns:
        (ToolSpec, handler) — caller registers spec into ToolRegistry and
        wires handler into the executor.
    """
    spec = ToolSpec(
        name="verify",
        description=(
            "Run all registered verifiers on the given output. Returns per-"
            "verifier verdicts (passed / score / reason / suggested_correction). "
            "Use this to self-check a candidate output before finalizing."
        ),
        input_schema={
            "type": "object",
            "required": ["output"],
            "properties": {
                "output": {
                    "type": "string",
                    "description": "The text to verify.",
                },
            },
        },
        annotations=ToolAnnotations(read_only=True, idempotent=True),
        concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
        hitl_policy=ToolHITLPolicy.AUTO,
        risk_level=RiskLevel.LOW,
        version="1.0",
        tags=("verification", "category_10"),
    )

    async def handler(args: dict[str, Any]) -> dict[str, Any]:
        output = str(args.get("output", ""))
        results: list[dict[str, Any]] = []
        all_passed = True
        for verifier in registry.get_all():
            result = await verifier.verify(
                output=output,
                state=cast(LoopState, None),  # verifier doesn't deref state
            )
            results.append(
                {
                    "verifier": result.verifier_name,
                    "verifier_type": result.verifier_type,
                    "passed": result.passed,
                    "score": result.score,
                    "reason": result.reason,
                    "suggested_correction": result.suggested_correction,
                }
            )
            if not result.passed:
                all_passed = False

        return {"passed": all_passed, "results": results}

    return (spec, handler)
