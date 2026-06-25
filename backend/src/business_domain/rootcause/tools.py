"""
File: backend/src/business_domain/rootcause/tools.py
Purpose: 3 ToolSpec stubs + register_rootcause_tools() entry. apply_fix is HIGH risk + ALWAYS_ASK.
Category: Business domain / rootcause / tool layer adaptation
Scope: Phase 51 / Sprint 51.0 Day 2.7 (per 08b-business-tools-spec.md §Domain 3)

Description:
    `mock_rootcause_apply_fix` is the single highest-risk mock tool. Per 08b spec
    §Domain 3, hitl_policy MUST be ALWAYS_ASK and risk_level MUST be HIGH. Encoded
    in tags for Sprint 51.0 (CARRY-021 ToolSpec extension lands in 51.1).

Sprint 55.2 Day 2.1 (US-1): register_rootcause_tools() now accepts a `mode` kwarg.
    mode='mock' keeps the 51.0 HTTP path via RootcauseMockExecutor.
    mode='service' uses BusinessServiceFactory; only diagnose maps to a real
    service method (RootCauseService.diagnose; UUID conversion in handler);
    suggest_fix returns service_path_pending sentinel; apply_fix returns
    approval_pending sentinel matching HITL ALWAYS_ASK enforcement at Cat 9.

Created: 2026-04-30 (Sprint 51.0 Day 2)
Last Modified: 2026-05-04

Modification History:
    - 2026-05-04: (Sprint 55.2 Day 2.1) Add mode kwarg + service-backed handlers
      (1 real: diagnose; 1 sentinel: suggest_fix; 1 approval_pending sentinel: apply_fix).
    - 2026-04-30: Initial creation (Sprint 51.0 Day 2).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from uuid import UUID

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

from .mock_executor import DEFAULT_BASE_URL, RootcauseMockExecutor

SPEC_DIAGNOSE = ToolSpec(
    name="mock_rootcause_diagnose",
    description="Return top RCA finding for an incident (highest-confidence hypothesis).",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "Id of the incident to diagnose.",
            },
        },
        "required": ["incident_id"],
    },
    annotations=ToolAnnotations(read_only=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:rootcause",),
)

SPEC_SUGGEST_FIX = ToolSpec(
    name="mock_rootcause_suggest_fix",
    description="Generate a mock fix proposal (fix_id + risk_level + ETA) for an incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "Id of the incident to propose a fix for.",
            },
        },
        "required": ["incident_id"],
    },
    annotations=ToolAnnotations(read_only=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:rootcause",),
)

SPEC_APPLY_FIX = ToolSpec(
    name="mock_rootcause_apply_fix",
    description=(
        "HIGH-RISK: Apply a previously suggested fix to an incident. "
        "dry_run=true (default) records intent but performs no mutation. "
        "Live runs (dry_run=false) require ALWAYS_ASK HITL approval."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "fix_id": {
                "type": "string",
                "description": "Id of the previously suggested fix to apply.",
            },
            "dry_run": {
                "type": "boolean",
                "default": True,
                "description": "If true (default), record intent without mutating.",
            },
        },
        "required": ["fix_id"],
    },
    annotations=ToolAnnotations(destructive=True, open_world=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.ALWAYS_ASK,
    risk_level=RiskLevel.HIGH,
    tags=("domain:rootcause",),
)

ROOTCAUSE_SPECS: tuple[ToolSpec, ...] = (
    SPEC_DIAGNOSE,
    SPEC_SUGGEST_FIX,
    SPEC_APPLY_FIX,
)


def _build_handlers(executor: RootcauseMockExecutor) -> dict[str, ToolHandler]:
    async def h_diagnose(call: ToolCall) -> str:
        result = await executor.diagnose(incident_id=call.arguments["incident_id"])
        return json.dumps(result)

    async def h_suggest(call: ToolCall) -> str:
        result = await executor.suggest_fix(incident_id=call.arguments["incident_id"])
        return json.dumps(result)

    async def h_apply(call: ToolCall) -> str:
        result = await executor.apply_fix(
            fix_id=call.arguments["fix_id"],
            dry_run=call.arguments.get("dry_run", True),
        )
        return json.dumps(result)

    return {
        "mock_rootcause_diagnose": h_diagnose,
        "mock_rootcause_suggest_fix": h_suggest,
        "mock_rootcause_apply_fix": h_apply,
    }


def _build_service_handlers(
    factory_provider: Callable[[], BusinessServiceFactory],
) -> dict[str, ToolHandler]:
    """Service-mode handlers: factory per-call → RootCauseService.

    Sprint 55.2 D1: RootCauseService only has `diagnose` from 55.1; suggest_fix
    returns service_path_pending sentinel; apply_fix returns approval_pending
    sentinel (HIGH-RISK; HITL ALWAYS_ASK at Cat 9 prevents real execution).
    """

    async def h_diagnose(call: ToolCall) -> str:
        svc = factory_provider().get_rootcause_service()
        result = await svc.diagnose(incident_id=UUID(call.arguments["incident_id"]))
        return json.dumps(result)

    async def h_suggest(call: ToolCall) -> str:
        factory_provider().get_rootcause_service()
        return json.dumps({"status": "service_path_pending", "method": "suggest_fix"})

    async def h_apply(call: ToolCall) -> str:
        factory_provider().get_rootcause_service()
        return json.dumps(
            {
                "status": "approval_pending",
                "fix_id": call.arguments["fix_id"],
                "dry_run": call.arguments.get("dry_run", True),
                "method": "apply_fix",
            }
        )

    return {
        "mock_rootcause_diagnose": h_diagnose,
        "mock_rootcause_suggest_fix": h_suggest,
        "mock_rootcause_apply_fix": h_apply,
    }


def register_rootcause_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    mock_url: str = DEFAULT_BASE_URL,
    mode: str = "mock",
    factory_provider: Callable[[], BusinessServiceFactory] | None = None,
) -> None:
    """Register 3 mock_rootcause_* ToolSpecs + handlers per mode.

    Sprint 55.2: mode-aware. See module docstring + register_patrol_tools for full doc.

    Raises:
        ValueError: invalid mode OR mode='service' without factory_provider.
    """
    for spec in ROOTCAUSE_SPECS:
        registry.register(spec)
    if mode == "mock":
        executor = RootcauseMockExecutor(base_url=mock_url)
        handlers.update(_build_handlers(executor))
    elif mode == "service":
        if factory_provider is None:
            raise ValueError("register_rootcause_tools(mode='service') requires factory_provider")
        handlers.update(_build_service_handlers(factory_provider))
    else:
        raise ValueError(f"register_rootcause_tools: invalid mode {mode!r}")
