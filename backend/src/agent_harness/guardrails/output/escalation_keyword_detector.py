"""
File: backend/src/agent_harness/guardrails/output/escalation_keyword_detector.py
Purpose: Output guardrail — ESCALATE on a phrase in a FINAL answer (pre-delivery HITL pause).
Category: 範疇 9 (Guardrails & Safety)
Scope: Phase 57.93 / Sprint 57.93 (地基 A Slice 3 output-guardrail leg)

Description:
    The output analogue of KeywordEscalationGuardrail (input, Sprint 57.91). When
    the loop's pre-delivery output gate runs this guardrail on a FINAL answer and
    the answer contains any configured (case-insensitive, substring) trigger
    phrase, it returns GuardrailAction.ESCALATE → the loop's
    _cat9_output_escalate_pause pauses durably BEFORE the answer is delivered
    (before LLMResponded renders it) for human approval of the answer itself
    (Sprint 57.93 output-ESCALATE pause point) instead of streaming it to the
    user. Any non-matching answer PASSes (so the rest of the output chain —
    Toxicity / SensitiveInfo — runs normally). REAL detection (not a Potemkin
    trigger); single responsibility — does NOT touch ToxicityDetector /
    SensitiveInfoDetector. The chat handler registers it at priority=5 (before
    the default p10/p20 output detectors) so the ESCALATE wins for the demo
    phrase; production per-tenant escalation phrases would source from a
    per-tenant policy (deferred AD).

Key Components:
    - OutputKeywordEscalationGuardrail(Guardrail): guardrail_type = OUTPUT

Created: 2026-06-08 (Sprint 57.93)
Last Modified: 2026-06-08

Modification History (newest-first):
    - 2026-06-08: Initial creation (Sprint 57.93) — output-ESCALATE pre-delivery pause trigger

Related:
    - guardrails/_abc.py — Guardrail ABC contract + GuardrailType.OUTPUT
    - guardrails/input/escalation_keyword_detector.py — the input sibling (mirror)
    - orchestrator_loop/loop.py — _cat9_output_escalate_pause + _cat9_output_hitl_pause
    - 19-pause-resume-design.md §5 — generalized pause points
"""

from __future__ import annotations

from typing import Any

from agent_harness._contracts import TraceContext
from agent_harness.guardrails._abc import (
    Guardrail,
    GuardrailAction,
    GuardrailResult,
    GuardrailType,
)


class OutputKeywordEscalationGuardrail(Guardrail):
    """Output guardrail: ESCALATE when a final answer contains a trigger phrase.

    Args:
        phrases: trigger phrases; a case-insensitive substring match against the
            (flattened) answer text returns ESCALATE. Empty set → always PASS.
    """

    guardrail_type = GuardrailType.OUTPUT

    def __init__(self, phrases: frozenset[str]) -> None:
        # Normalize to lowercase once; drop empties so a stray "" never matches all.
        self._phrases: frozenset[str] = frozenset(p.lower() for p in phrases if p)

    async def check(
        self,
        *,
        content: Any,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        text = self._extract_text(content).lower()
        for phrase in self._phrases:
            if phrase in text:
                return GuardrailResult(
                    action=GuardrailAction.ESCALATE,
                    reason=f"output matched escalation phrase: {phrase!r}",
                    risk_level="HIGH",
                )
        return GuardrailResult(action=GuardrailAction.PASS)

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Flatten str / Message-like / content-block list to plain text.

        Same flatten contract as the input KeywordEscalationGuardrail — kept
        independent to avoid cross-detector coupling.
        """
        if isinstance(content, str):
            return content
        inner = getattr(content, "content", None)
        if inner is not None:
            if isinstance(inner, str):
                return inner
            if isinstance(inner, list):
                parts: list[str] = []
                for block in inner:
                    if isinstance(block, dict):
                        for key in ("text", "content"):
                            value = block.get(key)
                            if isinstance(value, str):
                                parts.append(value)
                                break
                    elif isinstance(block, str):
                        parts.append(block)
                return " ".join(parts)
        return str(content)
