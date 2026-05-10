"""
File: backend/src/api/v1/telemetry.py
Purpose: Anonymous frontend telemetry sink — Web Vitals beacons + frontend error reports → Cat 12.
Category: 範疇 12 (Observability / Tracing) — cross-cutting; HTTP boundary in api/v1
Scope: Phase 57 / Sprint 57.13 / US-B4

Description:
    Two unauthenticated POST endpoints the SPA beacons to (navigator.sendBeacon /
    fetch keepalive). They're in TenantContextMiddleware.EXEMPT_PATH_PREFIXES
    (`/api/v1/telemetry`) so no JWT is required — these fire before/around auth
    and from anonymous pages. Both return 204 (no body) and never error on bad
    input beyond Pydantic validation (a malformed beacon is dropped, not retried).

    Cat 12 emit path: this app has no app-level OpenTelemetry meter (only the
    auto-instrumentation from setup_opentelemetry). The established Cat 12 emit
    here is the structured JSON logger (configure_json_logging at startup), which
    the OTel log pipeline picks up. So each beacon becomes one structured log line
    — `event=frontend.web_vitals` / `event=frontend.error` — with the metric /
    error fields as structured extras.

    PII: the error `message` / `stack` and the Web-Vitals `url` are user-agent
    strings; they're logged via the JSON logger which applies PIIRedactor at the
    formatter level. We do not store request bodies anywhere else.

Key Components:
    - WebVitalIn / FrontendErrorIn — request DTOs (camelCase navigationType per the web-vitals lib)
    - POST /api/v1/telemetry/frontend       — one Core Web Vital metric
    - POST /api/v1/telemetry/frontend-error — one uncaught frontend error

Created: 2026-05-10 (Sprint 57.13 Day 6)

Related:
    - frontend/src/lib/observability.ts (the beacon producer)
    - platform_layer/middleware/tenant_context.py — EXEMPT_PATH_PREFIXES includes /api/v1/telemetry
    - platform_layer/observability/logger.py — get_json_logger + PIIRedactor
    - 01-eleven-categories-spec.md §範疇12
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import Response
from pydantic import BaseModel

from platform_layer.observability import get_json_logger

logger = get_json_logger("frontend.telemetry")

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# 204 No Content — the SPA doesn't read the response (sendBeacon ignores it).
_NO_CONTENT = Response(status_code=status.HTTP_204_NO_CONTENT)


class WebVitalIn(BaseModel):
    """One Core Web Vital sample as emitted by the web-vitals lib (onCLS/onLCP/...)."""

    name: str  # "CLS" | "FCP" | "LCP" | "INP" | "TTFB"
    value: float
    id: str
    rating: str | None = None  # "good" | "needs-improvement" | "poor"
    navigationType: str | None = None  # noqa: N815 — matches web-vitals lib field name
    url: str | None = None


class FrontendErrorIn(BaseModel):
    """An uncaught frontend error (ErrorBoundary / network / 5xx / mutation)."""

    message: str
    stack: str | None = None
    url: str | None = None
    user_agent: str | None = None
    context: dict[str, object] | None = None


@router.post("/frontend", status_code=status.HTTP_204_NO_CONTENT)
async def report_web_vital(payload: WebVitalIn) -> Response:
    """Record one Core Web Vital as a structured log line (Cat 12)."""
    logger.info(
        "frontend.web_vitals",
        extra={
            "event": "frontend.web_vitals",
            "metric_name": payload.name,
            "metric_value": payload.value,
            "metric_id": payload.id,
            "rating": payload.rating,
            "navigation_type": payload.navigationType,
            "url": payload.url,
        },
    )
    return _NO_CONTENT


@router.post("/frontend-error", status_code=status.HTTP_204_NO_CONTENT)
async def report_frontend_error(payload: FrontendErrorIn) -> Response:
    """Record one uncaught frontend error as a structured log line (Cat 12)."""
    logger.warning(
        "frontend.error",
        extra={
            "event": "frontend.error",
            "error_message": payload.message,
            "error_stack": payload.stack,
            "url": payload.url,
            "user_agent": payload.user_agent,
            "context": payload.context,
        },
    )
    return _NO_CONTENT
