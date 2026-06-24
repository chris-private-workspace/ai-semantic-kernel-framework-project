"""
File: backend/tests/unit/business_domain/test_shared_sandbox.py
Purpose: _get_shared_sandbox() threads SANDBOX_REQUIRE_ISOLATION into default_sandbox().
Category: Tests / 範疇 2 wiring (Sprint 57.137 AD-Guardrail-Detect-To-Restrict)
Created: 2026-06-24
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest

import business_domain._register_all as reg


@pytest.fixture(autouse=True)
def _reset_sandbox_singleton() -> Iterator[None]:
    # Risk Class C: the python_sandbox backend is a module-level process-wide
    # singleton; reset it around each test so the setting read is exercised fresh.
    reg._shared_sandbox_singleton = None
    yield
    reg._shared_sandbox_singleton = None


@pytest.mark.parametrize("require", [True, False])
def test_get_shared_sandbox_threads_require_isolation(
    monkeypatch: pytest.MonkeyPatch, require: bool
) -> None:
    """_get_shared_sandbox() passes get_settings().sandbox_require_isolation through."""
    captured: dict[str, object] = {}

    def _fake_default_sandbox(*, require_isolation: bool = False) -> object:
        captured["require_isolation"] = require_isolation
        return object()  # any backend stand-in

    monkeypatch.setattr(reg, "default_sandbox", _fake_default_sandbox)
    # _get_shared_sandbox imports get_settings inline from core.config → patch there.
    monkeypatch.setattr(
        "core.config.get_settings",
        lambda: SimpleNamespace(sandbox_require_isolation=require),
    )

    reg._get_shared_sandbox()
    assert captured["require_isolation"] is require


def test_get_shared_sandbox_caches_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    """The backend is resolved once; a 2nd call returns the same instance (no re-probe)."""
    calls = {"n": 0}

    def _fake_default_sandbox(*, require_isolation: bool = False) -> object:
        calls["n"] += 1
        return object()

    monkeypatch.setattr(reg, "default_sandbox", _fake_default_sandbox)
    monkeypatch.setattr(
        "core.config.get_settings",
        lambda: SimpleNamespace(sandbox_require_isolation=False),
    )

    first = reg._get_shared_sandbox()
    second = reg._get_shared_sandbox()
    assert first is second
    assert calls["n"] == 1
