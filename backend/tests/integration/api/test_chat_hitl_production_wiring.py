"""
File: backend/tests/integration/api/test_chat_hitl_production_wiring.py
Purpose: Verify Sprint 53.6 US-4 — chat handler wires AgentLoopImpl with the
    production HITLManager from ServiceFactory. Closes AD-Front-2.
Category: Tests / integration / api
Scope: Phase 53 / Sprint 53.6 US-4

Description:
    Drives `build_handler` (chat router's single entry-point) under three
    configurations:

      1. service_factory + default env → hitl_manager wired (production path)
      2. service_factory + HITL_ENABLED=false → hitl_manager NOT wired
         (53.3 baseline preserved; lets ops disable Stage 3 escalation)
      3. service_factory=None (legacy callers, tests that haven't migrated)
         → hitl_manager NOT wired

    Each case asserts on the resulting AgentLoopImpl's `_hitl_manager` attr —
    direct contract verification. Full SSE-driven Stage 3 escalation flow is
    covered by Sprint 53.5 US-3's `test_stage3_escalation_e2e.py` (uses
    FakeHITLManager for canned decisions); this test focuses solely on the
    wiring boundary.

Created: 2026-05-04 (Sprint 53.6 Day 4)

Related:
    - backend/src/api/v1/chat/handler.py (build_handler, _hitl_enabled)
    - backend/src/platform_layer/governance/service_factory.py (factory under test)
    - tests/integration/agent_harness/governance/test_stage3_escalation_e2e.py
      (Sprint 53.5 US-3 — full Stage 3 e2e with FakeHITLManager)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agent_harness.hitl import HITLManager
from api.v1.chat.handler import build_handler
from platform_layer.governance.service_factory import ServiceFactory


@asynccontextmanager
async def _fake_session_factory() -> Any:
    yield MagicMock()


def _factory() -> ServiceFactory:
    """Construct a ServiceFactory with no notifier config (Noop fallback)."""
    return ServiceFactory(
        session_factory=_fake_session_factory,
        notification_config_path=None,
        risk_policy_config_path=None,
    )


class TestChatHITLProductionWiring:
    def test_build_handler_with_factory_wires_hitl_manager(self) -> None:
        """Default production path: factory present, HITL_ENABLED unset → wired."""
        # Ensure env clean (no HITL_ENABLED override).
        with patch.dict("os.environ", {}, clear=False):
            # Remove any pre-existing HITL_ENABLED so default ON applies.
            import os as _os

            _os.environ.pop("HITL_ENABLED", None)

            loop = build_handler("echo_demo", "test message", service_factory=_factory())

        assert loop._hitl_manager is not None  # type: ignore[attr-defined]
        assert isinstance(loop._hitl_manager, HITLManager)  # type: ignore[attr-defined]

    def test_build_handler_with_factory_but_hitl_disabled_skips_wiring(self) -> None:
        """Feature toggle off: HITL_ENABLED=false → no hitl_manager wired."""
        with patch.dict("os.environ", {"HITL_ENABLED": "false"}, clear=False):
            loop = build_handler("echo_demo", "test message", service_factory=_factory())
        assert loop._hitl_manager is None  # type: ignore[attr-defined]

    def test_build_handler_without_factory_skips_wiring(self) -> None:
        """Legacy path: no factory passed → hitl_manager stays None (53.3 baseline)."""
        loop = build_handler("echo_demo", "test message")
        assert loop._hitl_manager is None  # type: ignore[attr-defined]

    def test_build_handler_passes_hitl_timeout(self) -> None:
        """Custom timeout flows through to AgentLoopImpl."""
        with patch.dict("os.environ", {}, clear=False):
            import os as _os

            _os.environ.pop("HITL_ENABLED", None)
            loop = build_handler(
                "echo_demo",
                "test",
                service_factory=_factory(),
                hitl_timeout_s=1800,
            )
        assert loop._hitl_timeout_s == 1800  # type: ignore[attr-defined]

    def test_build_handler_factory_uses_singleton_hitl_manager(self) -> None:
        """Two build_handler calls on the same factory share the cached HITL manager."""
        with patch.dict("os.environ", {}, clear=False):
            import os as _os

            _os.environ.pop("HITL_ENABLED", None)
            f = _factory()
            loop1 = build_handler("echo_demo", "msg1", service_factory=f)
            loop2 = build_handler("echo_demo", "msg2", service_factory=f)
        # Same HITLManager instance — factory caches as singleton.
        assert loop1._hitl_manager is loop2._hitl_manager  # type: ignore[attr-defined]


class TestHitlEnabledToggleParsing:
    """Dedicated tests for the env-flag parser to lock down accepted values."""

    @pytest.mark.parametrize(
        "value, expected_enabled",
        [
            (None, True),  # unset → default ON
            ("true", True),
            ("True", True),
            ("yes", True),  # anything non-"false" → ON
            ("false", False),
            ("FALSE", False),
            ("False", False),
            ("  false  ", False),  # whitespace tolerated
        ],
    )
    def test_hitl_enabled_parser(self, value: str | None, expected_enabled: bool) -> None:
        from api.v1.chat.handler import _hitl_enabled

        env_patch: dict[str, str] = {}
        if value is not None:
            env_patch["HITL_ENABLED"] = value
        with patch.dict("os.environ", env_patch, clear=False):
            import os as _os

            if value is None:
                _os.environ.pop("HITL_ENABLED", None)
            assert _hitl_enabled() is expected_enabled
