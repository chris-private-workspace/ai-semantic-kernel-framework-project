"""
File: backend/tests/unit/agent_harness/guardrails/test_between_turns_keyword_detector.py
Purpose: Unit tests for BetweenTurnsKeywordGuardrail (between-turns ESCALATE trigger, Sprint 57.92).
Category: Tests / 範疇 9
Created: 2026-06-08 (Sprint 57.92)
Modified: 2026-06-08
"""

from __future__ import annotations

import pytest

from agent_harness._contracts import Message
from agent_harness.guardrails._abc import GuardrailAction, GuardrailType
from agent_harness.guardrails.between_turns.keyword_detector import (
    BetweenTurnsKeywordGuardrail,
)

pytestmark = pytest.mark.asyncio


def _guard() -> BetweenTurnsKeywordGuardrail:
    return BetweenTurnsKeywordGuardrail(frozenset({"checkpoint", "needs review"}))


async def test_guardrail_type_is_between_turns() -> None:
    assert BetweenTurnsKeywordGuardrail(frozenset()).guardrail_type is GuardrailType.BETWEEN_TURNS


async def test_match_returns_escalate() -> None:
    result = await _guard().check(content="the result reached a checkpoint")
    assert result.action is GuardrailAction.ESCALATE
    assert result.risk_level == "HIGH"
    assert result.reason and "checkpoint" in result.reason


async def test_match_is_case_insensitive() -> None:
    result = await _guard().check(content="this output NEEDS REVIEW before continuing")
    assert result.action is GuardrailAction.ESCALATE


async def test_no_match_passes() -> None:
    result = await _guard().check(content="a perfectly ordinary intermediate result")
    assert result.action is GuardrailAction.PASS


async def test_empty_phrases_always_pass() -> None:
    guard = BetweenTurnsKeywordGuardrail(frozenset())
    result = await guard.check(content="checkpoint needs review")
    assert result.action is GuardrailAction.PASS


async def test_blank_phrase_dropped_never_matches_all() -> None:
    # A stray "" in the set must NOT make every output match.
    guard = BetweenTurnsKeywordGuardrail(frozenset({"", "checkpoint"}))
    result = await guard.check(content="a totally unrelated tool result")
    assert result.action is GuardrailAction.PASS


async def test_extracts_text_from_message_content() -> None:
    msg = Message(role="tool", content="the tool reached a checkpoint")
    result = await _guard().check(content=msg)
    assert result.action is GuardrailAction.ESCALATE
