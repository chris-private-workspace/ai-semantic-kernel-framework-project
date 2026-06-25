"""
File: backend/src/business_domain/patrol/tools.py
Purpose: 4 ToolSpec stubs + register_patrol_tools() entry for the patrol domain.
Category: Business domain / patrol / tool layer adaptation
Scope: Phase 51 / Sprint 51.0 Day 2.3 (per 08b-business-tools-spec.md §Domain 1)

Description:
    Defines 4 mock_patrol_* ToolSpecs and the register entry that wires both:
    1. ToolSpec into a ToolRegistry (specs)
    2. ToolHandler closures into a handlers dict (callable adapters that
       translate ToolCall -> typed PatrolMockExecutor method args)

    HITL policy + risk_level encoded in ToolSpec.tags as Sprint 51.0 workaround;
    Sprint 51.1 will extend ToolSpec with first-class fields (per retro CARRY-021).

Sprint 55.2 Day 1.1 (US-1): register_patrol_tools() now accepts a `mode` kwarg.
    mode='mock' keeps the 51.0 HTTP path via PatrolMockExecutor.
    mode='service' uses BusinessServiceFactory to build a per-call PatrolService;
    only get_results maps to a real service method (PatrolService.get_results);
    check_servers / schedule / cancel return service_path_pending sentinel
    (AD-BusinessDomainPartialSwap-1 partial closure; full impl → Phase 56+).
    Caller must pass `factory_provider` when mode='service'.

Created: 2026-04-30 (Sprint 51.0 Day 2)
Last Modified: 2026-05-04

Modification History:
    - 2026-05-04: (Sprint 55.2 Day 1.1) Add mode kwarg + service-backed handlers
      (1 real: get_results; 3 sentinel: check_servers / schedule / cancel).
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

from .mock_executor import DEFAULT_BASE_URL, PatrolMockExecutor

# === ToolSpec definitions =================================================

SPEC_CHECK_SERVERS = ToolSpec(
    name="mock_patrol_check_servers",
    description=(
        "Run health check on a list of server ids. Returns per-server "
        "PatrolResult (health + metrics)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "scope": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Server ids to check (e.g., ['web-01', 'db-01']).",
            },
        },
        "required": ["scope"],
    },
    annotations=ToolAnnotations(read_only=True, idempotent=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:patrol",),
)

SPEC_GET_RESULTS = ToolSpec(
    name="mock_patrol_get_results",
    description="Fetch a stored PatrolResult by patrol_id.",
    input_schema={
        "type": "object",
        "properties": {
            "patrol_id": {
                "type": "string",
                "description": "Id of the stored patrol result to fetch.",
            },
        },
        "required": ["patrol_id"],
    },
    annotations=ToolAnnotations(read_only=True, idempotent=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:patrol",),
)

SPEC_SCHEDULE = ToolSpec(
    name="mock_patrol_schedule",
    description=("Schedule a recurring patrol via cron expression. Returns schedule_id."),
    input_schema={
        "type": "object",
        "properties": {
            "cron": {"type": "string", "description": "Cron expression."},
            "scope": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Server ids to patrol on this schedule.",
            },
        },
        "required": ["cron", "scope"],
    },
    annotations=ToolAnnotations(destructive=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.ASK_ONCE,
    risk_level=RiskLevel.MEDIUM,
    tags=("domain:patrol",),
)

SPEC_CANCEL = ToolSpec(
    name="mock_patrol_cancel",
    description="Cancel a scheduled patrol by schedule_id.",
    input_schema={
        "type": "object",
        "properties": {
            "schedule_id": {
                "type": "string",
                "description": "Id of the scheduled patrol to cancel.",
            },
        },
        "required": ["schedule_id"],
    },
    annotations=ToolAnnotations(destructive=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.ASK_ONCE,
    risk_level=RiskLevel.MEDIUM,
    tags=("domain:patrol",),
)

PATROL_SPECS: tuple[ToolSpec, ...] = (
    SPEC_CHECK_SERVERS,
    SPEC_GET_RESULTS,
    SPEC_SCHEDULE,
    SPEC_CANCEL,
)


# === Handler factory + register entry =====================================


def _build_handlers(executor: PatrolMockExecutor) -> dict[str, ToolHandler]:
    async def h_check(call: ToolCall) -> str:
        result = await executor.check_servers(scope=call.arguments["scope"])
        return json.dumps(result)

    async def h_get(call: ToolCall) -> str:
        result = await executor.get_results(patrol_id=call.arguments["patrol_id"])
        return json.dumps(result)

    async def h_schedule(call: ToolCall) -> str:
        result = await executor.schedule(cron=call.arguments["cron"], scope=call.arguments["scope"])
        return json.dumps(result)

    async def h_cancel(call: ToolCall) -> str:
        result = await executor.cancel(schedule_id=call.arguments["schedule_id"])
        return json.dumps(result)

    return {
        "mock_patrol_check_servers": h_check,
        "mock_patrol_get_results": h_get,
        "mock_patrol_schedule": h_schedule,
        "mock_patrol_cancel": h_cancel,
    }


def _build_service_handlers(
    factory_provider: Callable[[], BusinessServiceFactory],
) -> dict[str, ToolHandler]:
    """Service-mode handlers: factory per-call → PatrolService.

    Sprint 55.2 D1: PatrolService only has `get_results` from 55.1; other 3
    methods (check_servers / schedule / cancel) return service_path_pending
    sentinel (AD-BusinessDomainPartialSwap-1 partial closure; full impl →
    Phase 56+ enterprise integration).
    """

    async def h_check(call: ToolCall) -> str:
        # Touch factory to maintain factory_provider invariant.
        factory_provider().get_patrol_service()
        return json.dumps({"status": "service_path_pending", "method": "check_servers"})

    async def h_get(call: ToolCall) -> str:
        svc = factory_provider().get_patrol_service()
        result = await svc.get_results(patrol_id=call.arguments["patrol_id"])
        return json.dumps(result)

    async def h_schedule(call: ToolCall) -> str:
        factory_provider().get_patrol_service()
        return json.dumps({"status": "service_path_pending", "method": "schedule"})

    async def h_cancel(call: ToolCall) -> str:
        factory_provider().get_patrol_service()
        return json.dumps({"status": "service_path_pending", "method": "cancel"})

    return {
        "mock_patrol_check_servers": h_check,
        "mock_patrol_get_results": h_get,
        "mock_patrol_schedule": h_schedule,
        "mock_patrol_cancel": h_cancel,
    }


def register_patrol_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    mock_url: str = DEFAULT_BASE_URL,
    mode: str = "mock",
    factory_provider: Callable[[], BusinessServiceFactory] | None = None,
) -> None:
    """Register 4 mock_patrol_* ToolSpecs + handlers per mode.

    Args:
        registry: ToolRegistry to register specs into.
        handlers: dict of name → ToolHandler closures (mutated in place).
        mock_url: mode='mock' only — base URL for mock_services backend.
        mode: 'mock' (51.0 HTTP path) or 'service' (55.2 partial DB-backed via factory).
        factory_provider: required when mode='service'; per-call sync callable
            returning a BusinessServiceFactory bound to (db, tenant_id, tracer).

    Raises:
        ValueError: invalid mode OR mode='service' without factory_provider.
    """
    for spec in PATROL_SPECS:
        registry.register(spec)
    if mode == "mock":
        executor = PatrolMockExecutor(base_url=mock_url)
        handlers.update(_build_handlers(executor))
    elif mode == "service":
        if factory_provider is None:
            raise ValueError("register_patrol_tools(mode='service') requires factory_provider")
        handlers.update(_build_service_handlers(factory_provider))
    else:
        raise ValueError(f"register_patrol_tools: invalid mode {mode!r}")
