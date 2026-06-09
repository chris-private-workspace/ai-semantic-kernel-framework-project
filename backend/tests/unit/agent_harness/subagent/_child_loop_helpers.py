"""
File: backend/tests/unit/agent_harness/subagent/_child_loop_helpers.py
Purpose: Shared helpers for Sprint 57.94 FORK-child-loop tests — a mock-LLM-backed
    ChildLoopFactory + a span-recording tracer.
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 57.94

Description:
    Sprint 57.94 makes ForkExecutor drive a REAL child AgentLoop via an injected
    ChildLoopFactory (no single-shot fallback). These helpers let the FORK / AS_TOOL
    tests inject a child loop backed by a MockChatClient — the SAME real-loop path
    production runs, with a mock LLM at the ChatClient ABC boundary (no AP-10 divergence).

Created: 2026-06-09 (Sprint 57.94)
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from adapters._base.chat_client import ChatClient
from agent_harness._contracts import (
    ChildLoopFactory,
    SpanCategory,
    SubagentBudget,
    TraceContext,
)
from agent_harness.observability import NoOpTracer
from agent_harness.observability._abc import Tracer
from agent_harness.orchestrator_loop import AgentLoopImpl
from agent_harness.orchestrator_loop._abc import AgentLoop
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools.executor import ToolExecutorImpl
from agent_harness.tools.registry import ToolRegistryImpl


def make_child_loop_factory(
    chat: ChatClient,
    *,
    registry: ToolRegistryImpl | None = None,
    executor: ToolExecutorImpl | None = None,
    tenant_id: UUID | None = None,
    tracer: Tracer | None = None,
    max_turns: int = 4,
) -> ChildLoopFactory:
    """Return a ChildLoopFactory that builds a real child AgentLoopImpl on `chat`.

    Default registry/executor are EMPTY (tool-less child). Pass a real pair (e.g.
    from make_default_executor()) for a tool-capable child loop.
    """

    def factory(budget: SubagentBudget) -> AgentLoop:
        reg = registry if registry is not None else ToolRegistryImpl()
        exe = executor if executor is not None else ToolExecutorImpl(registry=reg, handlers={})
        return AgentLoopImpl(
            chat_client=chat,
            output_parser=OutputParserImpl(),
            tool_executor=exe,
            tool_registry=reg,
            tenant_id=tenant_id,
            tracer=tracer,
            max_turns=max_turns,
            token_budget=budget.max_tokens,
        )

    return factory


class RecordingTracer(NoOpTracer):
    """NoOpTracer that records span names — for the child-LOOP-span assertion (Sprint 57.94)."""

    def __init__(self) -> None:
        super().__init__()
        self.span_names: list[str] = []

    def start_span(
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        self.span_names.append(name)
        return super().start_span(
            name=name,
            category=category,
            trace_context=trace_context,
            attributes=attributes,
        )
