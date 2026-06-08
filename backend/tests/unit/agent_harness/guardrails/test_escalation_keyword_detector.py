"""
File: backend/tests/unit/agent_harness/guardrails/test_escalation_keyword_detector.py
Purpose: Unit tests for KeywordEscalationGuardrail (input-ESCALATE trigger, Sprint 57.91).
Category: Tests / 範疇 9
Created: 2026-06-08 (Sprint 57.91)
Modified: 2026-06-08
"""

from __future__ import annotations

import pytest

from agent_harness._contracts import Message
from agent_harness.guardrails._abc import GuardrailAction, GuardrailType
from agent_harness.guardrails.input.escalation_keyword_detector import (
    KeywordEscalationGuardrail,
)

pytestmark = pytest.mark.asyncio


def _guard() -> KeywordEscalationGuardrail:
    return KeywordEscalationGuardrail(frozenset({"approval required", "escalate me"}))


async def test_guardrail_type_is_input() -> None:
    assert KeywordEscalationGuardrail(frozenset()).guardrail_type is GuardrailType.INPUT


async def test_match_returns_escalate() -> None:
    result = await _guard().check(content="please, approval required for this")
    assert result.action is GuardrailAction.ESCALATE
    assert result.risk_level == "HIGH"
    assert result.reason and "approval required" in result.reason


async def test_match_is_case_insensitive() -> None:
    result = await _guard().check(content="ESCALATE ME right now")
    assert result.action is GuardrailAction.ESCALATE


async def test_no_match_passes() -> None:
    result = await _guard().check(content="just a normal question about the weather")
    assert result.action is GuardrailAction.PASS


async def test_empty_phrases_always_pass() -> None:
    guard = KeywordEscalationGuardrail(frozenset())
    result = await guard.check(content="approval required escalate me")
    assert result.action is GuardrailAction.PASS


async def test_blank_phrase_dropped_never_matches_all() -> None:
    # A stray "" in the set must NOT make every input match.
    guard = KeywordEscalationGuardrail(frozenset({"", "escalate me"}))
    result = await guard.check(content="a totally unrelated message")
    assert result.action is GuardrailAction.PASS


async def test_extracts_text_from_message_content() -> None:
    msg = Message(role="user", content="kindly, approval required here")
    result = await _guard().check(content=msg)
    assert result.action is GuardrailAction.ESCALATE
