"""
File: backend/tests/integration/api/conftest.py
Purpose: Shared fixtures for api/v1 integration tests.
Category: Tests / integration / api
Scope: Phase 53 / Sprint 53.6 (US-5 ServiceFactory test isolation)

Description:
    Resets module-level singletons between tests so each test gets a fresh
    instance bound to its own pytest-asyncio event loop. Without this, the
    first test caches resources bound to its loop, and subsequent tests in
    the same process hit "Event loop is closed".

    Singletons reset (per testing.md §Module-level Singleton Reset Pattern):
    - ServiceFactory (53.6) — governance HITL/Risk/AuditQuery
    - SLAMetricRecorder (56.3 US-1) — Cat 12 SLA recording
    - PricingLoader (56.3 US-3) — LLM + tool pricing yaml cache
    - CostLedgerService (56.3 US-3) — per-event Cost Ledger writer

Modification History:
    - 2026-05-06: Sprint 56.3 Day 3 — add reset_cost_ledger (US-3)
    - 2026-05-06: Sprint 56.3 Day 2 — add reset_pricing_loader (US-3)
    - 2026-05-06: Sprint 56.3 Day 1 — add reset_sla_recorder (US-1)
    - 2026-05-04: Initial (Sprint 53.6 Day 4)
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# Sprint 57.6 Day 4 (AD-Reality-FlakeEventLoop deferred Phase 57.7+):
# Disable Day 2 audit_log chat observer in integration tests until proper
# connection-pool isolation is added to tests/conftest.py db_session fixture
# (estimated ~1-2 hr). Without this, db.begin_nested()+append_audit()+session
# flush leaves connection-pool state bound to chat_e2e tests' asyncio loop
# → cascades into "attached to a different loop" cross-test failure pattern.
os.environ.setdefault("AUDIT_LOG_CHAT_OBSERVER", "false")

# Sprint 57.7 US-R1 D19: same pattern for sessions+tool_calls observers
# (closed AD-Reality-3a + 3b backend wiring; same loop-isolation concern as
# audit_log above; defer real test fixture refactor to AD-Reality-FlakeEventLoop).
os.environ.setdefault("SESSIONS_CHAT_OBSERVER", "false")
os.environ.setdefault("TOOL_CALLS_CHAT_OBSERVER", "false")

from platform_layer.billing.cost_ledger import reset_cost_ledger  # noqa: E402
from platform_layer.billing.pricing import reset_pricing_loader  # noqa: E402
from platform_layer.governance.service_factory import reset_service_factory  # noqa: E402
from platform_layer.observability import reset_sla_recorder  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_module_singletons() -> Iterator[None]:
    """Clear module-level singletons before + after each test."""
    reset_service_factory()
    reset_sla_recorder()
    reset_pricing_loader()
    reset_cost_ledger()
    yield
    reset_service_factory()
    reset_sla_recorder()
    reset_pricing_loader()
    reset_cost_ledger()
