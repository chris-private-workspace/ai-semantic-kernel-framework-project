"""
File: backend/src/agent_harness/observability/tracer.py
Purpose: Tracer concrete impls — NoOpTracer (tests / dev) + OTelTracer (production).
Category: 範疇 12 (Observability — cross-cutting)
Scope: Phase 49 / Sprint 49.4 Day 3

Description:
    Two implementations satisfy the Tracer ABC:

    - NoOpTracer: zero side effects; used by unit tests and dev environments
      without an OTel collector running. Still propagates TraceContext correctly
      so downstream code paths see consistent IDs.

    - OTelTracer: thin wrapper over OpenTelemetry SDK. Translates our neutral
      TraceContext / MetricEvent / SpanCategory into OTel native primitives.
      The SDK is initialized once per process via platform_layer/observability/setup.py.

    Both implementations honor:
    - TraceContext propagation (parent_span_id linkage)
    - Tenant baggage (tenant_id / user_id / session_id attached as span attributes)
    - SpanCategory attribution (one of 13 enum values)

    Why a NoOp variant exists: agent_harness/ tests must not require an OTel
    collector. NoOpTracer is the default test fixture.

Created: 2026-04-29 (Sprint 49.4 Day 3)
Last Modified: 2026-06-25

Modification History (newest-first):
    - 2026-06-25: Sprint 57.142 — _span_cm bespoke→gen_ai.* map at start+close (fixes token loss)
    - 2026-04-29: Initial creation (Sprint 49.4 Day 3) — NoOp + OTel concrete

Related:
    - _abc.py — Tracer ABC owner
    - _genai_semconv.py — bespoke→CNCF gen_ai.* mapping (Sprint 57.142, applied OTelTracer-only)
    - metrics.py — MetricRegistry (sibling)
    - platform_layer/observability/setup.py — process-wide SDK init
    - .claude/rules/observability-instrumentation.md — 5 must-have spans
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import uuid4

from agent_harness._contracts import MetricEvent, SpanCategory, TraceContext
from agent_harness.observability._abc import Tracer
from agent_harness.observability._genai_semconv import to_genai_span

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NoOpTracer — default for tests + dev without OTel collector
# ---------------------------------------------------------------------------


class NoOpTracer(Tracer):
    """Tracer that does no I/O. Propagates TraceContext only.

    Use this in unit tests and in dev when no OTel collector is running.
    """

    def __init__(self) -> None:
        self._current: TraceContext | None = None
        self.recorded_metrics: list[MetricEvent] = []
        self.spans_started: list[tuple[str, SpanCategory]] = []

    @asynccontextmanager
    async def _span_cm(
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None,
        attributes: dict[str, Any] | None,
    ) -> AsyncIterator[TraceContext]:
        parent = trace_context or self._current or TraceContext.create_root()
        child = TraceContext(
            trace_id=parent.trace_id,
            span_id=uuid4().hex[:16],
            parent_span_id=parent.span_id,
            tenant_id=parent.tenant_id,
            user_id=parent.user_id,
            session_id=parent.session_id,
            baggage=dict(parent.baggage),
        )
        self.spans_started.append((name, category))
        previous = self._current
        self._current = child
        try:
            yield child
        finally:
            self._current = previous

    def start_span(
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        return self._span_cm(
            name=name,
            category=category,
            trace_context=trace_context,
            attributes=attributes,
        )

    def record_metric(self, event: MetricEvent) -> None:
        self.recorded_metrics.append(event)

    def get_current_context(self) -> TraceContext | None:
        return self._current


# ---------------------------------------------------------------------------
# OTelTracer — production (wraps OpenTelemetry SDK)
# ---------------------------------------------------------------------------


class OTelTracer(Tracer):
    """Production tracer wrapping OpenTelemetry SDK.

    Lazy-imports the SDK so test / lint paths don't require it loaded.
    """

    def __init__(self, *, service_name: str = "ipa-v2-backend") -> None:
        self.service_name = service_name
        self._current: TraceContext | None = None
        self._otel_tracer: Any = None  # lazy
        self._otel_meter: Any = None  # lazy
        self._counters: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}
        self._gauges: dict[str, Any] = {}

    def _get_otel_tracer(self) -> Any:
        if self._otel_tracer is None:
            from opentelemetry import trace as ot_trace

            self._otel_tracer = ot_trace.get_tracer(self.service_name)
        return self._otel_tracer

    def _get_otel_meter(self) -> Any:
        if self._otel_meter is None:
            from opentelemetry import metrics as ot_metrics

            self._otel_meter = ot_metrics.get_meter(self.service_name)
        return self._otel_meter

    @asynccontextmanager
    async def _span_cm(
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None,
        attributes: dict[str, Any] | None,
    ) -> AsyncIterator[TraceContext]:
        parent = trace_context or self._current or TraceContext.create_root()

        # Enterprise / governance attrs (always str). Merged with caller attrs, then
        # translated to CNCF gen_ai.* via to_genai_span (Sprint 57.142, research #5).
        # Caller attrs are passed RAW (not str()-coerced) so gen_ai.usage.* export as int.
        base_attrs: dict[str, Any] = {
            "category": category.value,
            "trace_id_neutral": parent.trace_id,
        }
        if parent.tenant_id:
            base_attrs["tenant_id"] = str(parent.tenant_id)
        if parent.user_id:
            base_attrs["user_id"] = str(parent.user_id)
        if parent.session_id:
            base_attrs["session_id"] = str(parent.session_id)

        # START: translate the start-time snapshot. Token + finish_reason attrs arrive
        # post-response → re-translated at CLOSE (the start snapshot can't see the
        # caller's post-start dict mutation; that was a latent loss — Sprint 57.142).
        mapped_name, start_attrs = to_genai_span(name, {**base_attrs, **(attributes or {})})

        otel_tracer = self._get_otel_tracer()
        previous = self._current

        with otel_tracer.start_as_current_span(mapped_name, attributes=start_attrs) as otel_span:
            otel_ctx = otel_span.get_span_context()
            child = TraceContext(
                trace_id=parent.trace_id,
                span_id=format(otel_ctx.span_id, "016x"),
                parent_span_id=parent.span_id,
                tenant_id=parent.tenant_id,
                user_id=parent.user_id,
                session_id=parent.session_id,
                baggage=dict(parent.baggage),
            )
            self._current = child
            try:
                yield child
            except Exception as exc:  # noqa: BLE001
                otel_span.record_exception(exc)
                otel_span.set_status(_status_error(str(exc)))
                raise
            finally:
                # CLOSE: re-read the caller attrs ref (now carrying post-response usage
                # tokens + finish_reason) → translate → set on the still-open span. This
                # is what makes gen_ai.usage.* + finish_reasons actually export (the start
                # snapshot missed them — the fixed latent loss). Sprint 57.142.
                if attributes:
                    _, close_attrs = to_genai_span(name, {**base_attrs, **attributes})
                    otel_span.set_attributes(close_attrs)
                self._current = previous

    def start_span(
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        return self._span_cm(
            name=name,
            category=category,
            trace_context=trace_context,
            attributes=attributes,
        )

    def record_metric(self, event: MetricEvent) -> None:
        meter = self._get_otel_meter()
        labels = {**event.labels, "category": event.category.value}
        if event.metric_type == "counter":
            counter = self._counters.get(event.metric_name)
            if counter is None:
                counter = meter.create_counter(event.metric_name)
                self._counters[event.metric_name] = counter
            counter.add(event.value, labels)
        elif event.metric_type == "histogram":
            hist = self._histograms.get(event.metric_name)
            if hist is None:
                hist = meter.create_histogram(event.metric_name)
                self._histograms[event.metric_name] = hist
            hist.record(event.value, labels)
        elif event.metric_type == "gauge":
            # OTel Python uses ObservableGauge — for simplicity we model gauge
            # as last-value histogram bucket; real gauges happen via callbacks
            # (Phase 50+). For now, route to histogram with explicit name suffix.
            hist = self._histograms.get(f"{event.metric_name}_gauge")
            if hist is None:
                hist = meter.create_histogram(f"{event.metric_name}_gauge")
                self._histograms[f"{event.metric_name}_gauge"] = hist
            hist.record(event.value, labels)

    def get_current_context(self) -> TraceContext | None:
        return self._current


def _status_error(message: str) -> Any:
    """Lazy-build OTel Status object only when needed."""
    from opentelemetry.trace import Status, StatusCode

    return Status(StatusCode.ERROR, description=message)


__all__ = ["NoOpTracer", "OTelTracer"]
