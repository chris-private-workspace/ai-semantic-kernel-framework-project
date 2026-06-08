"""
File: backend/src/agent_harness/guardrails/between_turns/keyword_detector.py
Purpose: Between-turns guardrail — ESCALATE on a phrase in a completed turn's output.
Category: 範疇 9 (Guardrails & Safety)
Scope: Phase 57.92 / Sprint 57.92 (地基 A Slice 3 leg 2)

Description:
    The between-turns analogue of the input/tool ESCALATE triggers. The Cat 1
    loop runs the BETWEEN_TURNS chain at the loop top — after ≥1 completed turn,
    BEFORE the next LLM call — on the just-completed turn's output (the last
    assistant/tool message text). When that text contains any configured
    (case-insensitive, substring) trigger phrase this returns
    GuardrailAction.ESCALATE → the loop's _cat9_between_turns_check pauses
    durably for human approval of CONTINUING the loop (Sprint 57.92 between-turns
    pause point) before the next turn runs. Non-matching output PASSes. REAL
    detection (not a Potemkin trigger); single responsibility — does NOT touch
    the OUTPUT-chain detectors (toxicity / sensitive_info). Production per-tenant
    between-turns phrases would source from a per-tenant policy (deferred AD); the
    chat handler wires a deterministic demo phrase for the drive-through.

Key Components:
    - BetweenTurnsKeywordGuardrail(Guardrail): guardrail_type = BETWEEN_TURNS

Created: 2026-06-08 (Sprint 57.92)
Last Modified: 2026-06-08

Modification History (newest-first):
    - 2026-06-08: Initial creation (Sprint 57.92) — between-turns ESCALATE pause trigger

Related:
    - guardrails/_abc.py — Guardrail ABC contract + GuardrailType.BETWEEN_TURNS
    - guardrails/input/escalation_keyword_detector.py — the input-ESCALATE sibling (Sprint 57.91)
    - orchestrator_loop/loop.py _cat9_between_turns_check + _hitl_pause — the pause path
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


class BetweenTurnsKeywordGuardrail(Guardrail):
    """Between-turns guardrail: ESCALATE when a completed turn's output matches a phrase.

    Args:
        phrases: trigger phrases; a case-insensitive substring match against the
            (flattened) just-completed turn output returns ESCALATE. Empty set →
            always PASS.
    """

    guardrail_type = GuardrailType.BETWEEN_TURNS

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
                    reason=f"output matched between-turns escalation phrase: {phrase!r}",
                    risk_level="HIGH",
                )
        return GuardrailResult(action=GuardrailAction.PASS)

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Flatten str / Message-like / content-block list to plain text.

        Same flatten contract as KeywordEscalationGuardrail — kept independent to
        avoid cross-detector coupling.
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
