"""
File: backend/src/agent_harness/guardrails/input/escalation_keyword_detector.py
Purpose: Input guardrail — ESCALATE (HITL pause) on a configured trigger phrase in the user input.
Category: 範疇 9 (Guardrails & Safety)
Scope: Phase 57.91 / Sprint 57.91 (地基 A Slice 3 leg 1)

Description:
    The input analogue of the tool-path ESCALATE trigger (Sprint 57.88's
    echo_tool → requires_approval). When the loop-start input chain runs this
    guardrail and the user input contains any configured (case-insensitive,
    substring) trigger phrase, it returns GuardrailAction.ESCALATE → the loop's
    _cat9_input_check pauses durably for human approval of the input itself
    (Sprint 57.91 input-ESCALATE pause point) instead of calling the LLM. Any
    non-matching input PASSes (so the rest of the input chain — PII / Jailbreak —
    runs normally). REAL detection (not a Potemkin trigger); single responsibility
    — does NOT touch PIIDetector / JailbreakDetector. Production per-tenant
    escalation phrases would source from a per-tenant policy (deferred AD); the
    chat handler wires a deterministic demo phrase for the drive-through.

Key Components:
    - KeywordEscalationGuardrail(Guardrail): guardrail_type = INPUT

Created: 2026-06-08 (Sprint 57.91)
Last Modified: 2026-06-08

Modification History (newest-first):
    - 2026-06-08: Initial creation (Sprint 57.91) — input-ESCALATE pause trigger

Related:
    - guardrails/_abc.py — Guardrail ABC contract
    - orchestrator_loop/loop.py _cat9_input_check / _cat9_input_hitl_pause — the pause path
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


class KeywordEscalationGuardrail(Guardrail):
    """Input guardrail: ESCALATE when the input contains a trigger phrase.

    Args:
        phrases: trigger phrases; a case-insensitive substring match against the
            (flattened) input text returns ESCALATE. Empty set → always PASS.
    """

    guardrail_type = GuardrailType.INPUT

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
                    reason=f"input matched escalation phrase: {phrase!r}",
                    risk_level="HIGH",
                )
        return GuardrailResult(action=GuardrailAction.PASS)

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Flatten str / Message-like / content-block list to plain text.

        Same flatten contract as JailbreakDetector — kept independent to avoid
        cross-detector coupling.
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
