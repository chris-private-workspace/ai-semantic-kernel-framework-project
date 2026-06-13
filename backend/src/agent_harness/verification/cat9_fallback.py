"""
File: backend/src/agent_harness/verification/cat9_fallback.py
Purpose: Cat 9 Guardrail wrapper that adds Cat 10 LLM-judge defense-in-depth fallback.
Category: 範疇 10 (Verification Loops; Cat 9 bridge)
Scope: Sprint 54.1 US-2; closes AD-Cat9-1

Description:
    Wraps an existing Cat 9 Guardrail and adds an LLMJudgeVerifier (Cat 10)
    that runs WHEN the underlying deterministic detector returns PASS. This
    is defense-in-depth for cases where regex/rule-based detectors miss
    edge cases (international PII formats, meta-discussion vs real
    jailbreak attempts, etc.).

    **Cost-vs-safety trade-off**: every PASS triggers an LLM call. The
    wrapper is opt-in — operators register `LLMJudgeFallbackGuardrail(
    wrapped=PIIDetector(), judge=...)` ONLY for the chains that need it.
    Default Cat 9 chains (without wrappers) keep their existing cheap
    behavior.

    **Why a wrapper, not engine.py modification (Drift D8 from Day 2 探勘)**:
    Modifying GuardrailEngine to thread judge fallback would require adding
    a `confidence` field to GuardrailResult (touches 17.md single-source
    rule + 4 detector implementations). The wrapper pattern keeps the blast
    radius local — no contract changes, no modifications to the 4 detectors,
    no engine.py changes. The cost is one new class.

    **Behavior**:
    - wrapped.check() → BLOCK / SANITIZE / ESCALATE / REROLL → propagate as-is
      (the deterministic detector caught something; judge unnecessary)
    - wrapped.check() → PASS → run LLMJudgeVerifier on content
      - judge.passed=True → return PASS (defense-in-depth confirmed clean)
      - judge.passed=False → return BLOCK with judge.reason as Guardrail reason

    **Observability Design (54.2 D19 + 55.5 AD-Cat10-Obs-Cat9Wrappers validation)**:
    This wrapper REUSES the inner judge's `verification_span` — it does NOT
    emit an independent wrapper-level span. Rationale:
    - Single span per verify invocation matches Cat 12 helpers minimal-overhead
      philosophy (see observability/helpers.py + AD-Cat12-Helpers-1)
    - Wrapper logic (judge fallback decision) does not warrant a separate span;
      inner judge's span attributes already capture verifier identity + result
    - Avoids double-instrumentation noise in distributed traces
    - Verified by sentinel: tests/unit/agent_harness/verification/test_cat9_wrappers_obs.py
      (asserts `verification_span` is NOT imported in this module; reuse-inner
      invariant enforced at static-import level)
    Decision recorded by Sprint 55.5 (audit cycle Mini-Sprint #3 closes AD-Cat10-Obs-Cat9Wrappers).

Owner: 範疇 10 (verification/) — bridges to Cat 9 Guardrail ABC
Single-source: reuses existing GuardrailResult + Verifier ABC + LLMJudgeVerifier

Created: 2026-05-04 (Sprint 54.1 Day 2)
Last Modified: 2026-05-05

Modification History:
    - 2026-05-05: Sprint 55.5 — Observability Design D19 (closes AD-Cat10-Obs-Cat9Wrappers)
    - 2026-05-04: Initial (Sprint 54.1 US-2; closes AD-Cat9-1) — wrapper pattern per Drift D8

Related:
    - llm_judge.py — LLMJudgeVerifier dependency
    - guardrails/_abc.py — Guardrail / GuardrailResult / GuardrailAction
    - guardrails/engine.py — registration target (engine accepts any Guardrail)
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


class LLMJudgeFallbackGuardrail(Guardrail):
    """Wrap a Guardrail with LLM-judge defense-in-depth fallback.

    The wrapper IS-A Guardrail (registers normally in GuardrailEngine).
    Inherits the wrapped detector's `guardrail_type` so the engine routes
    it to the right chain.

    Args:
        wrapped: The underlying deterministic Guardrail (e.g., PIIDetector).
        judge: LLMJudgeVerifier configured with an appropriate template
            (e.g., `pii_leak_check` for PII fallback, `safety_review` for
            jailbreak fallback).
        name: Optional display name (defaults to wrapped's class name + "+judge").
    """

    def __init__(
        self,
        *,
        wrapped: Guardrail,
        judge: LLMJudgeVerifier,
        name: str | None = None,
    ) -> None:
        self._wrapped = wrapped
        self._judge = judge
        self._name = name or f"{wrapped.__class__.__name__}+judge"
        # Inherit guardrail_type from the wrapped detector so engine routing works
        self.guardrail_type: GuardrailType = wrapped.guardrail_type

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        """Run wrapped detector → if PASS, run judge → return judge verdict as GuardrailResult."""
        wrapped_result = await self._wrapped.check(content=content, trace_context=trace_context)

        # If deterministic detector caught something, propagate immediately (skip judge cost)
        if wrapped_result.action != GuardrailAction.PASS:
            return wrapped_result

        # PASS path: run judge on the content as defense-in-depth
        # Judge expects str output; coerce content for cases where it's a Message / ToolCall
        output_str = self._content_to_str(content)
        judge_result = await self._judge.verify(
            output=output_str,
            state=None,  # no loop state in the Cat 9 fallback layer (A3: judge → empty trace)
            trace_context=trace_context,
        )

        if judge_result.passed:
            return GuardrailResult(action=GuardrailAction.PASS)

        # Judge says block; map to BLOCK with the judge's reason
        return GuardrailResult(
            action=GuardrailAction.BLOCK,
            reason=f"{self._name}: {judge_result.reason or 'judge flagged content'}",
            risk_level="MEDIUM",
        )

    @staticmethod
    def _content_to_str(content: Any) -> str:
        """Coerce Cat 9 content (str / Message / ToolCall / etc.) to a string for the judge."""
        if isinstance(content, str):
            return content
        # Message has .content; fall back to repr otherwise
        msg_content = getattr(content, "content", None)
        if isinstance(msg_content, str):
            return msg_content
        return repr(content)
