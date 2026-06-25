"""
File: backend/src/business_domain/incident/tools.py
Purpose: 5 ToolSpec stubs + register_incident_tools() entry. close is HIGH risk + ALWAYS_ASK.
Category: Business domain / incident / tool layer adaptation
Scope: Phase 51 / Sprint 51.0 Day 3.4 (per 08b-business-tools-spec.md §Domain 5)

Description:
    Five mock_incident_* tools spanning the full incident lifecycle:
      create / update_status / close / get / list

    `close` is the highest-risk operation in this domain — closes an incident
    record permanently. Per 08b spec §Domain 5: hitl_policy=ALWAYS_ASK,
    risk_level=HIGH. Encoded in tags (CARRY-021 first-class fields in 51.1).

Sprint 55.1 Day 3.4 (US-4): register_incident_tools() now accepts a
    `mode` kwarg. mode='mock' keeps the 51.0 HTTP path via IncidentMockExecutor.
    mode='service' uses BusinessServiceFactory (Day 3.6) to build a per-call
    IncidentService instance backed by the production incidents table
    (Day 1 schema + Day 2 service class). Caller must pass `factory_provider`
    when mode='service'.

Created: 2026-04-30 (Sprint 51.0 Day 3)
Last Modified: 2026-05-04

Modification History:
    - 2026-05-04: (Sprint 55.1 Day 3.4) Add mode kwarg + service-backed handlers.
    - 2026-04-30: Initial creation (Sprint 51.0 Day 3).
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
from infrastructure.db.models.business import Incident

from .mock_executor import DEFAULT_BASE_URL, IncidentMockExecutor

SPEC_CREATE = ToolSpec(
    name="mock_incident_create",
    description="Create a new incident record (title + severity + linked alert_ids).",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "minLength": 1,
                "maxLength": 512,
                "description": "Short incident title.",
            },
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "default": "high",
                "description": "Incident severity (low / medium / high / critical).",
            },
            "alert_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional alert ids to link to this incident.",
            },
        },
        "required": ["title"],
    },
    annotations=ToolAnnotations(destructive=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.ASK_ONCE,
    risk_level=RiskLevel.MEDIUM,
    tags=("domain:incident",),
)

SPEC_UPDATE_STATUS = ToolSpec(
    name="mock_incident_update_status",
    description="Update an incident's status (open / investigating / resolved / closed).",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "Id of the incident to update.",
            },
            "status": {
                "type": "string",
                "enum": ["open", "investigating", "resolved", "closed"],
                "description": "New status (open / investigating / resolved / closed).",
            },
        },
        "required": ["incident_id", "status"],
    },
    annotations=ToolAnnotations(destructive=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.ASK_ONCE,
    risk_level=RiskLevel.MEDIUM,
    tags=("domain:incident",),
)

SPEC_CLOSE = ToolSpec(
    name="mock_incident_close",
    description=(
        "HIGH-RISK: Close an incident permanently with a resolution note. "
        "Requires ALWAYS_ASK HITL approval; mock returns 'closed_pending_review'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "Id of the incident to close.",
            },
            "resolution": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1000,
                "description": "Resolution note describing how the incident was resolved.",
            },
        },
        "required": ["incident_id", "resolution"],
    },
    annotations=ToolAnnotations(destructive=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.ALWAYS_ASK,
    risk_level=RiskLevel.HIGH,
    tags=("domain:incident",),
)

SPEC_GET = ToolSpec(
    name="mock_incident_get",
    description="Fetch a single incident by id.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "Id of the incident to fetch.",
            }
        },
        "required": ["incident_id"],
    },
    annotations=ToolAnnotations(read_only=True, idempotent=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:incident",),
)

SPEC_LIST = ToolSpec(
    name="mock_incident_list",
    description="List incidents with optional severity / status filter.",
    input_schema={
        "type": "object",
        "properties": {
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "description": "Optional severity filter (low / medium / high / critical).",
            },
            "status": {
                "type": "string",
                "enum": ["open", "investigating", "resolved", "closed"],
                "description": "Optional status filter (open / investigating / resolved / closed).",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 20,
                "description": "Max number of incidents to return (1-100).",
            },
        },
    },
    annotations=ToolAnnotations(read_only=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("domain:incident",),
)

INCIDENT_SPECS: tuple[ToolSpec, ...] = (
    SPEC_CREATE,
    SPEC_UPDATE_STATUS,
    SPEC_CLOSE,
    SPEC_GET,
    SPEC_LIST,
)


def _build_mock_handlers(executor: IncidentMockExecutor) -> dict[str, ToolHandler]:
    async def h_create(call: ToolCall) -> str:
        result = await executor.create(
            title=call.arguments["title"],
            severity=call.arguments.get("severity", "high"),
            alert_ids=call.arguments.get("alert_ids", []),
        )
        return json.dumps(result)

    async def h_update(call: ToolCall) -> str:
        result = await executor.update_status(
            incident_id=call.arguments["incident_id"],
            status=call.arguments["status"],
        )
        return json.dumps(result)

    async def h_close(call: ToolCall) -> str:
        result = await executor.close(
            incident_id=call.arguments["incident_id"],
            resolution=call.arguments["resolution"],
        )
        return json.dumps(result)

    async def h_get(call: ToolCall) -> str:
        result = await executor.get(incident_id=call.arguments["incident_id"])
        return json.dumps(result)

    async def h_list(call: ToolCall) -> str:
        result = await executor.list(
            severity=call.arguments.get("severity"),
            status=call.arguments.get("status"),
            limit=call.arguments.get("limit", 20),
        )
        return json.dumps(result)

    return {
        "mock_incident_create": h_create,
        "mock_incident_update_status": h_update,
        "mock_incident_close": h_close,
        "mock_incident_get": h_get,
        "mock_incident_list": h_list,
    }


def _serialize_incident(inc: Incident) -> dict[str, object]:
    """ORM Incident → JSON-friendly dict (avoids leaking SQLAlchemy state)."""
    return {
        "id": str(inc.id),
        "tenant_id": str(inc.tenant_id),
        "user_id": str(inc.user_id) if inc.user_id else None,
        "title": inc.title,
        "severity": inc.severity,
        "status": inc.status,
        "alert_ids": inc.alert_ids,
        "resolution": inc.resolution,
        "created_at": inc.created_at.isoformat(),
        "updated_at": inc.updated_at.isoformat(),
        "closed_at": inc.closed_at.isoformat() if inc.closed_at else None,
    }


def _build_service_handlers(
    factory_provider: Callable[[], BusinessServiceFactory],
) -> dict[str, ToolHandler]:
    """Service-mode handlers: pull factory per-call, build IncidentService, call method."""

    async def h_create(call: ToolCall) -> str:
        svc = factory_provider().get_incident_service()
        inc = await svc.create(
            title=call.arguments["title"],
            severity=call.arguments.get("severity", "high"),
            alert_ids=call.arguments.get("alert_ids", []),
        )
        return json.dumps(_serialize_incident(inc))

    async def h_update(call: ToolCall) -> str:
        svc = factory_provider().get_incident_service()
        inc = await svc.update_status(
            incident_id=UUID(call.arguments["incident_id"]),
            status=call.arguments["status"],
        )
        return json.dumps(_serialize_incident(inc))

    async def h_close(call: ToolCall) -> str:
        svc = factory_provider().get_incident_service()
        inc = await svc.close(
            incident_id=UUID(call.arguments["incident_id"]),
            resolution=call.arguments["resolution"],
        )
        return json.dumps(_serialize_incident(inc))

    async def h_get(call: ToolCall) -> str:
        svc = factory_provider().get_incident_service()
        inc = await svc.get(incident_id=UUID(call.arguments["incident_id"]))
        return json.dumps(_serialize_incident(inc) if inc else None)

    async def h_list(call: ToolCall) -> str:
        svc = factory_provider().get_incident_service()
        rows = await svc.list(
            severity=call.arguments.get("severity"),
            status=call.arguments.get("status"),
            limit=call.arguments.get("limit", 20),
        )
        return json.dumps([_serialize_incident(r) for r in rows])

    return {
        "mock_incident_create": h_create,
        "mock_incident_update_status": h_update,
        "mock_incident_close": h_close,
        "mock_incident_get": h_get,
        "mock_incident_list": h_list,
    }


def register_incident_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    mock_url: str = DEFAULT_BASE_URL,
    mode: str = "mock",
    factory_provider: Callable[[], BusinessServiceFactory] | None = None,
) -> None:
    """Register 5 incident ToolSpecs + handlers per mode.

    Args:
        registry: ToolRegistry to register specs into.
        handlers: dict of name → ToolHandler closures (mutated in place).
        mock_url: mode='mock' only — base URL for mock_services backend.
        mode: 'mock' (51.0 HTTP path) or 'service' (55.1 DB-backed via factory).
        factory_provider: required when mode='service'; per-call sync callable
            returning a BusinessServiceFactory bound to (db, tenant_id, tracer).

    Raises:
        ValueError: invalid mode OR mode='service' without factory_provider.
    """
    for spec in INCIDENT_SPECS:
        registry.register(spec)
    if mode == "mock":
        executor = IncidentMockExecutor(base_url=mock_url)
        handlers.update(_build_mock_handlers(executor))
    elif mode == "service":
        if factory_provider is None:
            raise ValueError("register_incident_tools(mode='service') requires factory_provider")
        handlers.update(_build_service_handlers(factory_provider))
    else:
        raise ValueError(f"register_incident_tools: invalid mode {mode!r}")
