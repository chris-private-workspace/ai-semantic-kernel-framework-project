"""
File: backend/tests/unit/api/v1/chat/test_loop_start_active_skill.py
Purpose: Unit tests for the Sprint 57.116 additive `active_skill` field on loop_start.
Category: tests
Scope: Phase 57 / Sprint 57.116 (Skills Inspector affordance)

Description:
    The opening loop_start SSE event gains an additive `active_skill: string | null`
    field so chat-v2 can chip the user turn with a force-loaded skill. The Cat-1
    loop has no concept of "skill" → the sse.py serializer defaults it null; the
    chat router (router._stream_loop_events) injects the validated force-load name
    on the loop_start frame. These tests lock: the serializer default is present
    (required by the WIRE_SCHEMA parity guard), the registry declares the field,
    and the 24 wire-TYPE count is unchanged (additive field, not a new type).

Created: 2026-06-14 (Sprint 57.116)
"""

from __future__ import annotations

from uuid import uuid4

from agent_harness._contracts import LoopStarted
from api.v1.chat.event_wire_schema import WIRE_SCHEMA
from api.v1.chat.sse import serialize_loop_event


class TestLoopStartActiveSkill:
    def test_serializer_defaults_active_skill_null(self) -> None:
        """The Cat-1 loop never sets a skill → the serializer defaults it None.

        The router overrides this for a force-load run; absent that, the field is
        present-and-null (the WIRE_SCHEMA parity guard requires the key to exist).
        """
        out = serialize_loop_event(LoopStarted(session_id=uuid4()))
        assert "active_skill" in out["data"]
        assert out["data"]["active_skill"] is None

    def test_serializer_active_skill_null_without_session(self) -> None:
        out = serialize_loop_event(LoopStarted())
        assert out["data"]["active_skill"] is None

    def test_wire_schema_declares_active_skill(self) -> None:
        assert WIRE_SCHEMA["loop_start"]["active_skill"] == "string | null"

    def test_wire_type_count_unchanged_24(self) -> None:
        """active_skill is a FIELD on loop_start, not a new top-level wire type."""
        assert len(WIRE_SCHEMA) == 24
        assert "active_skill" not in WIRE_SCHEMA  # it is a field, not a type key
