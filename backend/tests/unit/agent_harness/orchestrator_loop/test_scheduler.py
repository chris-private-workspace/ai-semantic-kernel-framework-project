"""
File: tests/unit/agent_harness/orchestrator_loop/test_scheduler.py
Purpose: Unit tests for should_continue_plan — Sprint 57.157 cross-burst auto-continue predicate.
Category: Tests
Scope: Phase 57.157 / Sprint 57.157
Created: 2026-07-06 (Sprint 57.157)
Modified: 2026-07-06
"""

from __future__ import annotations

from agent_harness._contracts.todo import Todo
from agent_harness.orchestrator_loop.scheduler import (
    CONTINUATION_NUDGE,
    should_continue_plan,
)


def _pending(id_: str = "1") -> Todo:
    return Todo(id=id_, title=f"step {id_}", status="pending")


def _completed(id_: str = "1") -> Todo:
    return Todo(id=id_, title=f"step {id_}", status="completed")


class TestShouldContinuePlan:
    def test_happy_path_continues(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="max_turns",
                todos=[_completed("1"), _pending("2")],
                bursts_used=0,
                max_bursts=3,
            )
            is True
        )

    def test_disabled_never_continues(self) -> None:
        assert (
            should_continue_plan(
                enabled=False,
                stop_reason="max_turns",
                todos=[_pending("1")],
                bursts_used=0,
                max_bursts=3,
            )
            is False
        )

    def test_end_turn_does_not_continue(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="end_turn",
                todos=[_pending("1")],
                bursts_used=0,
                max_bursts=3,
            )
            is False
        )

    def test_token_budget_does_not_continue(self) -> None:
        # Conservative: token exhaustion is the main runaway path → never auto-continue.
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="token_budget",
                todos=[_pending("1")],
                bursts_used=0,
                max_bursts=3,
            )
            is False
        )

    def test_handoff_does_not_continue(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="handoff",
                todos=[_pending("1")],
                bursts_used=0,
                max_bursts=3,
            )
            is False
        )

    def test_max_bursts_reached_stops(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="max_turns",
                todos=[_pending("1")],
                bursts_used=3,
                max_bursts=3,
            )
            is False
        )

    def test_max_bursts_exceeded_stops(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="max_turns",
                todos=[_pending("1")],
                bursts_used=5,
                max_bursts=3,
            )
            is False
        )

    def test_below_max_bursts_continues(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="max_turns",
                todos=[_pending("1")],
                bursts_used=2,
                max_bursts=3,
            )
            is True
        )

    def test_all_completed_stops(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="max_turns",
                todos=[_completed("1"), _completed("2")],
                bursts_used=0,
                max_bursts=3,
            )
            is False
        )

    def test_empty_plan_stops(self) -> None:
        # No write_todos → nothing to continue.
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="max_turns",
                todos=[],
                bursts_used=0,
                max_bursts=3,
            )
            is False
        )

    def test_in_progress_counts_as_unfinished(self) -> None:
        assert (
            should_continue_plan(
                enabled=True,
                stop_reason="max_turns",
                todos=[Todo(id="1", title="x", status="in_progress")],
                bursts_used=0,
                max_bursts=3,
            )
            is True
        )


def test_continuation_nudge_is_nonempty_str() -> None:
    assert isinstance(CONTINUATION_NUDGE, str)
    assert CONTINUATION_NUDGE.strip()
