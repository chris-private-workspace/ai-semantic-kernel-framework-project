"""
File: backend/tests/unit/agent_harness/observability/test_category_span.py
Purpose: AD-Cat12-Helpers-1 closure — verify category_span primitive behaves as no-op-or-span.
Category: Tests / 範疇 12 (Observability — cross-cutting)
Scope: Sprint 55.3

Description:
    `category_span` is the cross-cutting span primitive owned by Cat 12;
    `verification_span` (54.2) and `business_service_span` (55.1) delegate
    here. Tests verify:
      1. tracer=None → no-op (yields without exception, no span emit attempt)
      2. tracer present → start_span called with correct name + category;
         body executes within ctx mgr; span recorded
      3. Sequential calls accumulate spans in tracer in order

Created: 2026-05-04 (Sprint 55.3)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest

from agent_harness._contracts import SpanCategory, TraceContext
from agent_harness.observability import Tracer, category_span


class _RecordingTracer(Tracer):
    """Test tracer recording every span name + category (mirrors verification test pattern).

    Sprint 57.71: start_span now matches the full Tracer ABC signature
    (trace_context + attributes kwargs) since category_span always forwards
    `attributes=` after the loop-span-tree extension. The recorded tuple is
    still (name, category) — the extra kwargs are accepted but not asserted here.
    """

    def __init__(self) -> None:
        self.spans: list[tuple[str, SpanCategory]] = []
        self.metrics: list[object] = []

    @asynccontextmanager
    async def start_span(  # type: ignore[override]
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> AsyncIterator[None]:
        self.spans.append((name, category))
        yield

    def record_metric(self, event: object) -> None:  # type: ignore[override]
        self.metrics.append(event)

    def get_current_context(self) -> object | None:  # type: ignore[override]
        return None


@pytest.mark.asyncio
async def test_category_span_noop_when_tracer_is_none() -> None:
    """tracer=None → ctx mgr yields cleanly; no exception, no recording."""
    body_executed = False
    async with category_span(None, "subagent.task_spawn", SpanCategory.SUBAGENT):
        body_executed = True
    assert body_executed is True


@pytest.mark.asyncio
async def test_category_span_emits_span_when_tracer_present() -> None:
    """Tracer present → start_span called with given name + category; body runs inside."""
    tracer = _RecordingTracer()
    body_executed = False
    async with category_span(tracer, "verifier.foo", SpanCategory.VERIFICATION):
        # Body runs inside the span ctx (after start_span recorded)
        assert tracer.spans == [("verifier.foo", SpanCategory.VERIFICATION)]
        body_executed = True
    assert body_executed is True
    # Span list unchanged after exit (no double-record)
    assert tracer.spans == [("verifier.foo", SpanCategory.VERIFICATION)]


@pytest.mark.asyncio
async def test_category_span_sequential_calls_accumulate_in_order() -> None:
    """Multiple sequential calls accumulate spans in tracer; ordering preserved."""
    tracer = _RecordingTracer()
    async with category_span(tracer, "first", SpanCategory.TOOLS):
        pass
    async with category_span(tracer, "second", SpanCategory.VERIFICATION):
        pass
    async with category_span(tracer, "third", SpanCategory.SUBAGENT):
        pass
    assert tracer.spans == [
        ("first", SpanCategory.TOOLS),
        ("second", SpanCategory.VERIFICATION),
        ("third", SpanCategory.SUBAGENT),
    ]
