"""
File: backend/src/agent_harness/verification/cat9_mutator.py
Purpose: Cat 9 wrapper returning SANITIZE with judge-suggested mutation (closes AD-Cat9-2).
Category: 範疇 10 (Verification Loops; Cat 9 bridge)
Scope: Sprint 54.1 US-4; closes AD-Cat9-2 (SANITIZE actually mutates output)

Description:
    Companion to LLMJudgeFallbackGuardrail (cat9_fallback.py) but for
    SANITIZE semantics instead of BLOCK:
    - wrapped detector PASS → judge runs → if judge says NOT passed, return
      `GuardrailResult(action=SANITIZE, sanitized_content=judge.suggested_correction)`
    - wrapped detector PASS → judge says passed → return PASS
    - wrapped detector non-PASS → propagate as-is (skip judge)

    **Closes AD-Cat9-2**: previously, GuardrailAction.SANITIZE was a stub
    declared in 53.3 but no detector actually populated `sanitized_content`
    via an LLM-driven mutation. This wrapper provides the mechanism: ANY
    Cat 9 detector + a Cat 10 LLMJudgeVerifier configured with a template
    that returns suggested_correction → SANITIZE with mutated output.

    **AD-Cat9-3 (REROLL replays LLM call)** is closed conceptually by the
    in-loop Cat 10 self-correction gate (loop.py _cat10_verify_gate, Sprint
    57.98): operators can post-process Cat 9 SANITIZE results by feeding the
    mutated output back through the loop's verify→correct cycle instead of
    accepting the mutation directly.

    **Design parity with cat9_fallback.py (Drift D8 wrapper pattern)**:
    No modifications to GuardrailEngine / GuardrailResult / 17.md. The
    wrapper is a Guardrail that registers normally; operators opt in
    per-detector by wrapping the detector at registration time.

    **Observability Design (54.2 D19 + 55.5 AD-Cat10-Obs-Cat9Wrappers validation)**:
    This wrapper REUSES the inner judge's `verification_span` — it does NOT
    emit an independent wrapper-level span. Rationale identical to
    cat9_fallback.py (single span per verify invocation; minimal-overhead per
    Cat 12 helpers; avoids double-instrumentation noise). Verified by
    sentinel: tests/unit/agent_harness/verification/test_cat9_wrappers_obs.py
    (asserts `verification_span` is NOT imported in this module).
    Decision recorded by Sprint 55.5 (audit cycle Mini-Sprint #3 closes AD-Cat10-Obs-Cat9Wrappers).

Owner: 範疇 10 (verification/) — bridges to Cat 9 Guardrail ABC

Created: 2026-05-04 (Sprint 54.1 Day 4)
Last Modified: 2026-05-05

Modification History:
    - 2026-05-05: Sprint 55.5 — Observability Design D19 (closes AD-Cat10-Obs-Cat9Wrappers)
    - 2026-05-04: Initial (Sprint 54.1 US-4; closes AD-Cat9-2; pattern AD-Cat9-3)

Related:
    - cat9_fallback.py — companion BLOCK-mode wrapper
    - llm_judge.py — LLMJudgeVerifier dependency
    - guardrails/_abc.py — Guardrail / GuardrailResult / GuardrailAction
"""

from __future__ import annotations

from typing import Any

from agent_harness._contracts import TraceContext
from agent_harness.guardrails import (
    Guardrail,
    GuardrailAction,
    GuardrailResult,
    GuardrailType,
)
from agent_harness.verification.llm_judge import LLMJudgeVerifier


class LLMVerifyMutateGuardrail(Guardrail):
    """Wrap a Guardrail with LLM-judge mutation (SANITIZE on judge fail)."""

    def __init__(
        self,
        *,
        wrapped: Guardrail,
        judge: LLMJudgeVerifier,
        name: str | None = None,
    ) -> None:
        self._wrapped = wrapped
        self._judge = judge
        self._name = name or f"{wrapped.__class__.__name__}+mutate"
        self.guardrail_type: GuardrailType = wrapped.guardrail_type

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        """Wrapped → if PASS, run judge → if judge fail, return SANITIZE with mutation."""
        wrapped_result = await self._wrapped.check(content=content, trace_context=trace_context)

        if wrapped_result.action != GuardrailAction.PASS:
            # Deterministic detector caught something; propagate (skip judge)
            return wrapped_result

        # PASS path: ask judge whether output should be mutated
        output_str = self._content_to_str(content)
        judge_result = await self._judge.verify(
            output=output_str,
            state=None,  # no loop state in the Cat 9 mutator layer (A3: judge → empty trace)
            trace_context=trace_context,
        )

        if judge_result.passed:
            # Judge approves; pass through
            return GuardrailResult(action=GuardrailAction.PASS)

        # Judge says mutate. If it provided a suggested_correction, use it
        # as sanitized_content. Otherwise fail-safe to BLOCK (don't ship
        # something we know is bad without knowing how to mutate).
        if judge_result.suggested_correction:
            return GuardrailResult(
                action=GuardrailAction.SANITIZE,
                reason=f"{self._name}: {judge_result.reason or 'judge-mutated'}",
                sanitized_content=judge_result.suggested_correction,
                risk_level="MEDIUM",
            )
        # No mutation available → block instead (fail-safe)
        return GuardrailResult(
            action=GuardrailAction.BLOCK,
            reason=f"{self._name}: {judge_result.reason or 'judge flagged; no correction'}",
            risk_level="MEDIUM",
        )

    @staticmethod
    def _content_to_str(content: Any) -> str:
        if isinstance(content, str):
            return content
        msg_content = getattr(content, "content", None)
        if isinstance(msg_content, str):
            return msg_content
        return repr(content)
