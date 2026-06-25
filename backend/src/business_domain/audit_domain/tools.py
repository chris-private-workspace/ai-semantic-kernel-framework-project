"""
File: backend/src/business_domain/audit_domain/tools.py
Purpose: 3 ToolSpec stubs + register_audit_tools() entry.
Category: Business domain / audit_domain / tool layer adaptation
Scope: Phase 51 / Sprint 51.0 Day 3.2 (per 08b-business-tools-spec.md §Domain 4)

Description:
    Three mock_audit_* tools — query_logs (read-only) / generate_report
    (read-only + open_world) / flag_anomaly (destructive + ask_once).

Sprint 55.2 Day 2.2 (US-1): register_audit_tools() now accepts a `mode` kwarg.
    mode='mock' keeps the 51.0 HTTP path via AuditMockExecutor.
    mode='service' uses BusinessServiceFactory; only query_logs maps to a
    real service method (AuditService.query_logs; ISO date → ms conversion +
    drops user_id_filter which has no service equivalent — D7 finding).
    generate_report / flag_anomaly return service_path_pending sentinel.

Created: 2026-04-30 (Sprint 51.0 Day 3)
Last Modified: 2026-05-04

Modification History:
    - 2026-05-04: (Sprint 55.2 Day 2.2) Add mode kwarg + service-backed handlers
      (1 real: query_logs with ISO→ms conversion; 2 sentinel: generate_report / flag_anomaly).
    - 2026-04-30: Initial creation (Sprint 51.0 Day 3).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime

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

from .mock_executor import DEFAULT_BASE_URL, AuditMockExecutor

SPEC_QUERY_LOGS = ToolSpec(
    name="mock_audit_query_logs",
    description=("Query audit logs by optional time_range / action_filter / user_id_filter."),
    input_schema={
        "type": "object",
        "properties": {
            "time_range_start": {
                "type": "string",
                "format": "date-time",
                "description": "Optional ISO 8601 start of the time range.",
            },
            "time_range_end": {
                "type": "string",
                "format": "date-time",
                "description": "Optional ISO 8601 end of the time range.",
            },
            "action_filter": {
                "type": "string",
                "description": "Optional action-type filter.",
            },
            "user_id_filter": {
                "type": "string",
                "description": "Optional user id filter.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 200,
                "default": 20,
                "description": "Max number of log entries to return (1-200).",
            },
        },
    },
    annotations=ToolAnnotations(read_only=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:audit",),
)

SPEC_GENERATE_REPORT = ToolSpec(
    name="mock_audit_generate_report",
    description=("Generate an audit report from a template (e.g., compliance_quarterly)."),
    input_schema={
        "type": "object",
        "properties": {
            "template": {
                "type": "string",
                "description": "Report template name (e.g., compliance_quarterly).",
            },
            "params": {
                "type": "object",
                "additionalProperties": True,
                "description": "Optional template parameters.",
            },
        },
        "required": ["template"],
    },
    annotations=ToolAnnotations(read_only=True, open_world=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.MEDIUM,
    tags=("domain:audit",),
)

SPEC_FLAG_ANOMALY = ToolSpec(
    name="mock_audit_flag_anomaly",
    description=("Flag an audit record as anomalous; records reason for human review."),
    input_schema={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "Id of the audit record to flag.",
            },
            "reason": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500,
                "description": "Reason the record is flagged for human review.",
            },
        },
        "required": ["record_id", "reason"],
    },
    annotations=ToolAnnotations(destructive=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.ASK_ONCE,
    risk_level=RiskLevel.MEDIUM,
    tags=("domain:audit",),
)

AUDIT_SPECS: tuple[ToolSpec, ...] = (
    SPEC_QUERY_LOGS,
    SPEC_GENERATE_REPORT,
    SPEC_FLAG_ANOMALY,
)


def _build_handlers(executor: AuditMockExecutor) -> dict[str, ToolHandler]:
    async def h_query(call: ToolCall) -> str:
        result = await executor.query_logs(
            time_range_start=call.arguments.get("time_range_start"),
            time_range_end=call.arguments.get("time_range_end"),
            action_filter=call.arguments.get("action_filter"),
            user_id_filter=call.arguments.get("user_id_filter"),
            limit=call.arguments.get("limit", 20),
        )
        return json.dumps(result)

    async def h_report(call: ToolCall) -> str:
        result = await executor.generate_report(
            template=call.arguments["template"],
            params=call.arguments.get("params", {}),
        )
        return json.dumps(result)

    async def h_flag(call: ToolCall) -> str:
        result = await executor.flag_anomaly(
            record_id=call.arguments["record_id"],
            reason=call.arguments["reason"],
        )
        return json.dumps(result)

    return {
        "mock_audit_query_logs": h_query,
        "mock_audit_generate_report": h_report,
        "mock_audit_flag_anomaly": h_flag,
    }


def _iso_to_ms(s: str | None) -> int | None:
    """Convert ISO 8601 date-time string → epoch ms (None passthrough)."""
    if s is None:
        return None
    # Accept trailing Z; convert to +00:00 for fromisoformat compatibility
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)


def _build_service_handlers(
    factory_provider: Callable[[], BusinessServiceFactory],
) -> dict[str, ToolHandler]:
    """Service-mode handlers: factory per-call → AuditService.

    Sprint 55.2 D7 (signature mismatch): tool spec uses ISO date strings +
    action_filter + user_id_filter; service uses int ms + operation. Handler
    converts ISO → ms; user_id_filter ignored (no service equivalent;
    AD-BusinessDomainPartialSwap-1 partial closure; full filter parity →
    Phase 56+ when service.py extends).
    """

    async def h_query(call: ToolCall) -> str:
        svc = factory_provider().get_audit_service()
        result = await svc.query_logs(
            start_ms=_iso_to_ms(call.arguments.get("time_range_start")),
            end_ms=_iso_to_ms(call.arguments.get("time_range_end")),
            operation=call.arguments.get("action_filter"),
            limit=call.arguments.get("limit", 20),
        )
        return json.dumps(result)

    async def h_report(call: ToolCall) -> str:
        factory_provider().get_audit_service()
        return json.dumps({"status": "service_path_pending", "method": "generate_report"})

    async def h_flag(call: ToolCall) -> str:
        factory_provider().get_audit_service()
        return json.dumps({"status": "service_path_pending", "method": "flag_anomaly"})

    return {
        "mock_audit_query_logs": h_query,
        "mock_audit_generate_report": h_report,
        "mock_audit_flag_anomaly": h_flag,
    }


def register_audit_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    mock_url: str = DEFAULT_BASE_URL,
    mode: str = "mock",
    factory_provider: Callable[[], BusinessServiceFactory] | None = None,
) -> None:
    """Register 3 mock_audit_* ToolSpecs + handlers per mode.

    Sprint 55.2: mode-aware. See module docstring + register_patrol_tools for full doc.

    Raises:
        ValueError: invalid mode OR mode='service' without factory_provider.
    """
    for spec in AUDIT_SPECS:
        registry.register(spec)
    if mode == "mock":
        executor = AuditMockExecutor(base_url=mock_url)
        handlers.update(_build_handlers(executor))
    elif mode == "service":
        if factory_provider is None:
            raise ValueError("register_audit_tools(mode='service') requires factory_provider")
        handlers.update(_build_service_handlers(factory_provider))
    else:
        raise ValueError(f"register_audit_tools: invalid mode {mode!r}")
