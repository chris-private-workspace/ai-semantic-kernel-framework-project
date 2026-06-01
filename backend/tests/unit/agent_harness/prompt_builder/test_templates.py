"""Unit tests for templates. Sprint 52.2 Day 1.8 — 3 tests."""

from __future__ import annotations

from agent_harness.prompt_builder.templates import (
    MEMORY_SECTION_HEADER,
    SYSTEM_ROLE_TEMPLATE,
    _format_hint_line,
    _memory_as_messages,
)
from tests.unit.agent_harness.prompt_builder.conftest import make_memory_hint


def test_system_role_template_format() -> None:
    assert isinstance(SYSTEM_ROLE_TEMPLATE, str)
    assert len(SYSTEM_ROLE_TEMPLATE) > 0
    assert "agent" in SYSTEM_ROLE_TEMPLATE.lower()


def test_memory_section_header() -> None:
    rendered = MEMORY_SECTION_HEADER.format(layer="Tenant")
    assert "Tenant Memory" in rendered
    # The same template applied to different layer name gives different output
    assert MEMORY_SECTION_HEADER.format(layer="User") != rendered
    # Hint line renders summary + confidence (Sprint 57.65 A-1 Tier2 enrichment)
    line = _format_hint_line(make_memory_hint(summary="abc", confidence=0.7))
    assert line == "- abc (confidence 0.70)"


def test_memory_as_messages_groups_by_layer() -> None:
    layers = {
        "tenant": [make_memory_hint(layer="tenant", summary="tenant policy")],
        "user": [
            make_memory_hint(layer="user", summary="user pref 1"),
            make_memory_hint(layer="user", summary="user pref 2"),
        ],
        "session": [],  # empty layer should be skipped
    }
    result = _memory_as_messages(layers)
    assert len(result) == 2  # tenant + user; session empty skipped
    assert result[0].metadata.get("memory_layer") == "tenant"
    assert "tenant policy" in str(result[0].content)
    assert result[1].metadata.get("memory_layer") == "user"
    assert result[1].metadata.get("hint_count") == 2
    assert "user pref 1" in str(result[1].content)
    assert "user pref 2" in str(result[1].content)
