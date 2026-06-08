"""
File: backend/src/agent_harness/guardrails/engine.py
Purpose: GuardrailEngine — composes multiple Guardrails per type with fail-fast chain.
Category: 範疇 9 (Guardrails & Safety)
Scope: Phase 53.3 / Sprint 53.3 Day 1 (US-1)

Description:
    Single coordinator owning per-type Guardrail chains. Each chain runs
    in priority order (lower = higher priority); first non-PASS result
    short-circuits and returns. Cat 1 Loop wires the engine at four cut
    points (input start / between turns / per tool_call / output end), per
    plan §US-7 (between-turns added Sprint 57.92).

    Why fail-fast: a BLOCK / ESCALATE / REROLL decision should not be
    overruled by a later PASS — one detector saying "stop" is enough.
    Multiple detectors of the same type complement each other (PII
    regex + jailbreak pattern); they don't vote.

    `batch_check_tool_calls()` runs the tool chain in parallel across N
    tool calls in a single turn. The chain itself is sequential (fail-fast)
    inside each call, but multiple calls fan out via asyncio.gather. This
    matches the spec SLO `tool guardrail p95 < 50ms per call` while not
    serializing N calls behind one chain.

Key Components:
    - GuardrailEngine: register(guardrail, priority) + 3 check methods + batch
    - _RegisteredGuardrail: internal sort key

Owner: 01-eleven-categories-spec.md §範疇 9
Single-source: 17.md §1.1 (Guardrail / GuardrailResult dataclasses)

Created: 2026-05-03 (Sprint 53.3 Day 1)

Modification History (newest-first):
    - 2026-06-08: Sprint 57.92 — add check_between_turns (BETWEEN_TURNS chain)
    - 2026-05-03: Initial creation (Sprint 53.3 US-1) — engine framework

Related:
    - guardrails/_abc.py — Guardrail / GuardrailResult / GuardrailAction / GuardrailType
    - _contracts/events.py — GuardrailTriggered event (emitted by Loop, not engine)
    - sprint-53-3-plan.md §US-1 / §US-7
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from agent_harness._contracts import TraceContext
from agent_harness.guardrails._abc import (
    Guardrail,
    GuardrailAction,
    GuardrailResult,
    GuardrailType,
)


@dataclass(frozen=True)
class _RegisteredGuardrail:
    """Internal: pairs a Guardrail with its priority for sort stability."""

    priority: int
    guardrail: Guardrail


@dataclass
class GuardrailEngine:
    """Composes multiple Guardrails per type; runs each chain with fail-fast.

    Usage:
        engine = GuardrailEngine()
        engine.register(PIIDetector(), priority=10)
        engine.register(JailbreakDetector(), priority=20)
        result = await engine.check_input(user_message)
        if result.action != GuardrailAction.PASS:
            # Loop emits GuardrailTriggered + handles per-action policy
            ...
    """

    # Per-type chains. Sorted ascending by priority (0 = highest).
    _chains: dict[GuardrailType, list[_RegisteredGuardrail]] = field(
        default_factory=lambda: {gt: [] for gt in GuardrailType}
    )

    def register(self, guardrail: Guardrail, *, priority: int = 100) -> None:
        """Register a Guardrail in its declared `guardrail_type` chain.

        Lower priority values run first. Re-registering the same instance
        appends a duplicate entry (caller's responsibility to dedupe);
        this matches the simplest-correct behavior for pluggable detectors
        loaded from YAML config.
        """
        gtype = guardrail.guardrail_type
        self._chains[gtype].append(_RegisteredGuardrail(priority=priority, guardrail=guardrail))
        self._chains[gtype].sort(key=lambda r: r.priority)

    def _registered_for(self, gtype: GuardrailType) -> list[Guardrail]:
        """Return the active chain for inspection (read-only view)."""
        return [r.guardrail for r in self._chains[gtype]]

    async def _run_chain(
        self,
        gtype: GuardrailType,
        content: Any,
        *,
        trace_context: TraceContext | None,
    ) -> GuardrailResult:
        """Run a per-type chain in priority order; fail-fast on first non-PASS."""
        for entry in self._chains[gtype]:
            result = await entry.guardrail.check(
                content=content,
                trace_context=trace_context,
            )
            if result.action != GuardrailAction.PASS:
                return result
        return GuardrailResult(action=GuardrailAction.PASS)

    async def check_input(
        self,
        content: Any,
        *,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        """Run input chain (loop start). Defaults to PASS when chain empty."""
        return await self._run_chain(GuardrailType.INPUT, content, trace_context=trace_context)

    async def check_output(
        self,
        content: Any,
        *,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        """Run output chain (loop end). Defaults to PASS when chain empty."""
        return await self._run_chain(GuardrailType.OUTPUT, content, trace_context=trace_context)

    async def check_between_turns(
        self,
        content: Any,
        *,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        """Run between-turns chain (loop top, after ≥1 completed turn).

        Sprint 57.92 (地基 A Slice 3 leg 2): the Cat 1 loop runs this on the
        just-completed turn's output BEFORE the next LLM call. Distinct from the
        OUTPUT chain so it does NOT double-fire with the per-LLM-response output
        check. Defaults to PASS when the chain is empty (backward-compat no-op).
        """
        return await self._run_chain(
            GuardrailType.BETWEEN_TURNS, content, trace_context=trace_context
        )

    async def check_tool_call(
        self,
        content: Any,
        *,
        trace_context: TraceContext | None = None,
    ) -> GuardrailResult:
        """Run tool chain (per tool_call). Defaults to PASS when chain empty."""
        return await self._run_chain(GuardrailType.TOOL, content, trace_context=trace_context)

    async def batch_check_tool_calls(
        self,
        contents: list[Any],
        *,
        trace_context: TraceContext | None = None,
    ) -> list[GuardrailResult]:
        """Parallelize per-tool_call checks across many tool_calls in one turn.

        Each call's chain still runs sequentially (fail-fast); calls fan
        out via asyncio.gather. Honors SLO `tool guardrail p95 < 50ms per
        call` without serializing N calls behind one chain.
        """
        if not contents:
            return []
        return list(
            await asyncio.gather(
                *(self.check_tool_call(c, trace_context=trace_context) for c in contents)
            )
        )
