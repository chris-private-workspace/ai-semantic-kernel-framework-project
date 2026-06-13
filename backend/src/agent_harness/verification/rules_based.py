"""
File: backend/src/agent_harness/verification/rules_based.py
Purpose: RulesBasedVerifier — fail-fast Rules runner; cheap verifier (p95 < 200ms).
Category: 範疇 10 (Verification Loops)
Scope: Sprint 54.1 US-1

Description:
    Concrete Verifier that delegates to a list of Rule instances. Returns
    VerificationResult on the first failing rule (fail-fast); returns
    passed=True when all rules pass.

    State / trace_context parameters required by Verifier ABC are accepted
    but unused — RulesBasedVerifier is stateless by design (no LLM call,
    no external IO). The 200ms SLO is achievable because each Rule.check()
    is a sync local operation (regex / json / callable).

Owner: 01-eleven-categories-spec.md §範疇 10
Single-source: 17.md §2.1 (Verifier ABC)

Created: 2026-05-04 (Sprint 54.1 Day 1)
Last Modified: 2026-05-04

Modification History:
    - 2026-05-04: AD-Cat10-Obs-1 — accept optional Tracer (Sprint 54.2 US-5)
    - 2026-05-04: Initial creation (Sprint 54.1 US-1)
"""

from __future__ import annotations

from agent_harness._contracts import LoopState, TraceContext, VerificationResult
from agent_harness.observability import Tracer
from agent_harness.verification._abc import Verifier
from agent_harness.verification._obs import verification_span
from agent_harness.verification.types import Rule


class RulesBasedVerifier(Verifier):
    """Run Rules in order; first failure short-circuits."""

    def __init__(
        self,
        rules: list[Rule],
        name: str = "rules_based",
        *,
        tracer: Tracer | None = None,
    ) -> None:
        self._rules = rules
        self._name = name
        self._tracer = tracer

    async def verify(
        self,
        *,
        output: str,
        state: LoopState | None = None,
        trace_context: TraceContext | None = None,
    ) -> VerificationResult:
        # Rules are string-only by design (regex / schema / format on `output`);
        # `state` (the A3 trace) is intentionally ignored here — only the LLM judge
        # is trace-aware.
        async with verification_span(self._tracer, self._name):
            for rule in self._rules:
                passed, reason, suggestion = rule.check(output)
                if not passed:
                    return VerificationResult(
                        passed=False,
                        verifier_name=self._name,
                        verifier_type="rules_based",
                        reason=reason,
                        suggested_correction=suggestion,
                    )
            return VerificationResult(
                passed=True,
                verifier_name=self._name,
                verifier_type="rules_based",
            )
