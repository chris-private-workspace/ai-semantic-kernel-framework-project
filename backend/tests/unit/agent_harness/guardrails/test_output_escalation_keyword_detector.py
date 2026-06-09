"""
File: backend/tests/unit/agent_harness/guardrails/test_output_escalation_keyword_detector.py
Purpose: Unit tests for OutputKeywordEscalationGuardrail (output pre-delivery, Sprint 57.93).
Category: Tests / 範疇 9
Created: 2026-06-08 (Sprint 57.93)
Modified: 2026-06-08
"""

from __future__ import annotations

import pytest

from agent_harness._contracts import Message
from agent_harness.guardrails._abc import GuardrailAction, GuardrailType
from agent_harness.guardrails.output.escalation_keyword_detector import (
    OutputKeywordEscalationGuardrail,
)

pytestmark = pytest.mark.asyncio


def _guard() -> OutputKeywordEscalationGuardrail:
    return OutputKeywordEscalationGuardrail(frozenset({"confidential", "for your eyes only"}))


async def test_guardrail_type_is_output() -> None:
    assert OutputKeywordEscalationGuardrail(frozenset()).guardrail_type is GuardrailType.OUTPUT


async def test_match_returns_escalate() -> None:
    result = await _guard().check(content="the report is marked confidential")
    assert result.action is GuardrailAction.ESCALATE
    assert result.risk_level == "HIGH"
    assert result.reason and "confidential" in result.reason


async def test_match_is_case_insensitive() -> None:
    result = await _guard().check(content="this is FOR YOUR EYES ONLY")
    assert result.action is GuardrailAction.ESCALATE


async def test_no_match_passes() -> None:
    result = await _guard().check(content="a perfectly ordinary public answer")
    assert result.action is GuardrailAction.PASS


async def test_empty_phrases_always_pass() -> None:
    guard = OutputKeywordEscalationGuardrail(frozenset())
    result = await guard.check(content="confidential for your eyes only")
    assert result.action is GuardrailAction.PASS


async def test_blank_phrase_dropped_never_matches_all() -> None:
    # A stray "" in the set must NOT make every answer match.
    guard = OutputKeywordEscalationGuardrail(frozenset({"", "confidential"}))
    result = await guard.check(content="a totally ordinary public answer")
    assert result.action is GuardrailAction.PASS


async def test_extracts_text_from_message_content() -> None:
    msg = Message(role="assistant", content="here is the confidential summary")
    result = await _guard().check(content=msg)
    assert result.action is GuardrailAction.ESCALATE
