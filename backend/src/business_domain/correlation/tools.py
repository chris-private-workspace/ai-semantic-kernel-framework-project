"""
File: backend/src/business_domain/correlation/tools.py
Purpose: 3 ToolSpec stubs + register_correlation_tools() entry.
Category: Business domain / correlation / tool layer adaptation
Scope: Phase 51 / Sprint 51.0 Day 2.5 (per 08b-business-tools-spec.md §Domain 2)

Sprint 55.2 Day 1.2 (US-1): register_correlation_tools() now accepts a `mode` kwarg.
    mode='mock' keeps the 51.0 HTTP path via CorrelationMockExecutor.
    mode='service' uses BusinessServiceFactory to build a per-call CorrelationService;
    only get_related maps to a real service method (CorrelationService.get_related);
    analyze / find_root_cause return service_path_pending sentinel
    (AD-BusinessDomainPartialSwap-1 partial closure; full impl → Phase 56+).

Created: 2026-04-30 (Sprint 51.0 Day 2)
Last Modified: 2026-05-04

Modification History:
    - 2026-05-04: (Sprint 55.2 Day 1.2) Add mode kwarg + service-backed handlers
      (1 real: get_related; 2 sentinel: analyze / find_root_cause).
    - 2026-04-30: Initial creation (Sprint 51.0 Day 2).
"""

from __future__ import annotations

import json
from collections.abc import Callable

from agent_harness._contracts import (
    ConcurrencyPolicy,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)

# Sprint 52.5 P0 #18: use Union ToolHandler from tools.__init__
from agent_harness.tools import ToolHandler  # noqa: E402
from agent_harness.tools import ToolRegistry
from business_domain._service_factory import BusinessServiceFactory

from .mock_executor import DEFAULT_BASE_URL, CorrelationMockExecutor

SPEC_ANALYZE = ToolSpec(
    name="mock_correlation_analyze",
    description=(
        "Analyze a set of alert ids and return correlation chains "
        "(primary + related alerts within 5-minute time window on same server)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "alert_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Alert ids to analyze for correlation chains.",
            },
        },
        "required": ["alert_ids"],
    },
    annotations=ToolAnnotations(read_only=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:correlation",),
)

SPEC_FIND_ROOT_CAUSE = ToolSpec(
    name="mock_correlation_find_root_cause",
    description="Return root-cause candidates ranked by confidence for an incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "Id of the incident to find root-cause candidates for.",
            },
        },
        "required": ["incident_id"],
    },
    annotations=ToolAnnotations(read_only=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:correlation",),
)

SPEC_GET_RELATED = ToolSpec(
    name="mock_correlation_get_related",
    description="Return alerts related to a given alert within a depth (1-3).",
    input_schema={
        "type": "object",
        "properties": {
            "alert_id": {
                "type": "string",
                "description": "Id of the alert to find related alerts for.",
            },
            "depth": {
                "type": "integer",
                "minimum": 1,
                "maximum": 3,
                "default": 1,
                "description": "Traversal depth for related alerts (1-3).",
            },
        },
        "required": ["alert_id"],
    },
    annotations=ToolAnnotations(read_only=True, idempotent=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:correlation",),
)

CORRELATION_SPECS: tuple[ToolSpec, ...] = (
    SPEC_ANALYZE,
    SPEC_FIND_ROOT_CAUSE,
    SPEC_GET_RELATED,
)


def _build_handlers(executor: CorrelationMockExecutor) -> dict[str, ToolHandler]:
    async def h_analyze(call: ToolCall) -> str:
        result = await executor.analyze(alert_ids=call.arguments["alert_ids"])
        return json.dumps(result)

    async def h_find_rc(call: ToolCall) -> str:
        result = await executor.find_root_cause(incident_id=call.arguments["incident_id"])
        return json.dumps(result)

    async def h_get_related(call: ToolCall) -> str:
        result = await executor.get_related(
            alert_id=call.arguments["alert_id"],
            depth=call.arguments.get("depth", 1),
        )
        return json.dumps(result)

    return {
        "mock_correlation_analyze": h_analyze,
        "mock_correlation_find_root_cause": h_find_rc,
        "mock_correlation_get_related": h_get_related,
    }


def _build_service_handlers(
    factory_provider: Callable[[], BusinessServiceFactory],
) -> dict[str, ToolHandler]:
    """Service-mode handlers: factory per-call → CorrelationService.

    Sprint 55.2 D1: CorrelationService only has `get_related` from 55.1; other
    2 methods (analyze / find_root_cause) return service_path_pending sentinel
    (AD-BusinessDomainPartialSwap-1 partial closure; full impl → Phase 56+).
    """

    async def h_analyze(call: ToolCall) -> str:
        factory_provider().get_correlation_service()
        return json.dumps({"status": "service_path_pending", "method": "analyze"})

    async def h_find_rc(call: ToolCall) -> str:
        factory_provider().get_correlation_service()
        return json.dumps({"status": "service_path_pending", "method": "find_root_cause"})

    async def h_get_related(call: ToolCall) -> str:
        svc = factory_provider().get_correlation_service()
        result = await svc.get_related(
            alert_id=call.arguments["alert_id"],
            depth=call.arguments.get("depth", 1),
        )
        return json.dumps(result)

    return {
        "mock_correlation_analyze": h_analyze,
        "mock_correlation_find_root_cause": h_find_rc,
        "mock_correlation_get_related": h_get_related,
    }


def register_correlation_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    mock_url: str = DEFAULT_BASE_URL,
    mode: str = "mock",
    factory_provider: Callable[[], BusinessServiceFactory] | None = None,
) -> None:
    """Register 3 mock_correlation_* ToolSpecs + handlers per mode.

    Sprint 55.2: mode-aware. See module docstring + register_patrol_tools for full doc.

    Raises:
        ValueError: invalid mode OR mode='service' without factory_provider.
    """
    for spec in CORRELATION_SPECS:
        registry.register(spec)
    if mode == "mock":
        executor = CorrelationMockExecutor(base_url=mock_url)
        handlers.update(_build_handlers(executor))
    elif mode == "service":
        if factory_provider is None:
            raise ValueError("register_correlation_tools(mode='service') requires factory_provider")
        handlers.update(_build_service_handlers(factory_provider))
    else:
        raise ValueError(f"register_correlation_tools: invalid mode {mode!r}")
