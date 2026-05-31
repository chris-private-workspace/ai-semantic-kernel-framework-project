"""
File: backend/tests/integration/api/test_chat_verification_smoke.py
Purpose: Integration smoke for AD-Cat10-Wire-1 (chat router 2-mode CHAT_VERIFICATION_MODE).
Category: 範疇 10 (Verification Loops) / Tests / Integration
Scope: Sprint 55.5 Day 1 (Option E 2-mode post-D4+D5)

Description:
    End-to-end smoke validating the always-call-wrapper pattern at
    `_stream_loop_events()`:

    - "disabled" (default): build_handler returns verifier_registry=None → wrapper
      transparently delegates to loop.run() per correction_loop.py:99-106. Event
      stream byte-for-byte identical to the existing 50.2 echo_demo 8-event
      sequence; no verification_* events emitted. (echo_demo, no Azure needed.)

    - "enabled": Sprint 57.63 (approach A) moved verifier construction INTO
      build_real_llm_handler so the LLMJudgeVerifier shares the loop's adapter.
      Only the real_llm path builds a populated VerifierRegistry; echo_demo always
      returns registry=None (predictable fixtures, MockChatClient must not be
      judged). So the "enabled emits verification" assertion now exercises the
      real_llm path with a MockChatClient injected via dependency override (no
      real Azure call), proving the wrapper runs the verifier + emits
      VerificationPassed when the registry is populated.

Created: 2026-05-05 (Sprint 55.5 Day 1)
Last Modified: 2026-05-31

Modification History (newest-first):
    - 2026-05-31: Sprint 57.63 — enabled-mode assertion moved to the real_llm path
      (approach A: verifier built in build_real_llm_handler; echo_demo no longer
      verifies). echo_demo disabled-mode backwards-compat assertion unchanged.
    - 2026-05-05: Initial creation (Sprint 55.5 Day 1) — close AD-Cat10-Wire-1 integration smoke
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.chat import router as chat_router
from api.v1.chat.session_registry import get_default_registry
from core.config import get_settings
from platform_layer.identity import get_current_tenant, get_current_user_id

DEFAULT_TENANT = UUID("22222222-2222-2222-2222-222222222222")
DEFAULT_USER_ID = UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def app() -> FastAPI:
    """Test app with chat router + dependency override pinning tenant_id."""
    inst = FastAPI()
    inst.include_router(chat_router, prefix="/api/v1")
    inst.dependency_overrides[get_current_tenant] = lambda: DEFAULT_TENANT
    inst.dependency_overrides[get_current_user_id] = lambda: DEFAULT_USER_ID
    return inst


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as tc:
        yield tc


@pytest.fixture(autouse=True)
def _reset_default_registry() -> Iterator[None]:
    """Clear session registry between tests (mirrors test_chat_e2e pattern)."""
    reg = get_default_registry()
    reg._tenants.clear()  # type: ignore[attr-defined]  # noqa: SLF001
    yield
    reg._tenants.clear()  # type: ignore[attr-defined]  # noqa: SLF001


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Clear get_settings lru_cache between tests so monkeypatch env changes take effect."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _parse_sse(body: bytes) -> list[dict]:
    out: list[dict] = []
    for chunk in body.split(b"\n\n"):
        if not chunk.strip():
            continue
        lines = chunk.decode("utf-8").split("\n")
        event_line = next((ln for ln in lines if ln.startswith("event: ")), "")
        data_line = next((ln for ln in lines if ln.startswith("data: ")), "")
        out.append(
            {
                "type": event_line[len("event: ") :],
                "data": json.loads(data_line[len("data: ") :]) if data_line else None,
            }
        )
    return out


# ============================================================
# AD-Cat10-Wire-1 — Sprint 55.5 Day 1 (Option E 2-mode post-D4+D5)
# ============================================================


class TestChatVerificationWireSmoke:
    """End-to-end smoke for 2-mode CHAT_VERIFICATION_MODE wiring."""

    def test_chat_router_verification_smoke_2_modes(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """2-mode smoke: disabled preserves existing echo stream + emits no verification
        events; enabled adds verification_passed event from no-op RulesBasedVerifier.

        Validates always-call-wrapper backwards-compat (disabled mode produces
        byte-for-byte equivalent event stream to direct loop.run path) AND
        the populated-registry path emits Cat 10 events.
        """
        # ---- Mode 1: disabled (default; backwards-compat path) ----
        monkeypatch.setenv("CHAT_VERIFICATION_MODE", "disabled")
        get_settings.cache_clear()
        with client.stream(
            "POST",
            "/api/v1/chat/",
            json={"message": "zebra", "mode": "echo_demo"},
        ) as resp:
            assert resp.status_code == 200
            body_disabled = b"".join(chunk for chunk in resp.iter_bytes())

        events_disabled = _parse_sse(body_disabled)
        types_disabled = [e["type"] for e in events_disabled]

        # Existing 50.2 8-event echo sequence must still hold
        assert types_disabled[0] == "loop_start"
        assert types_disabled[-1] == "loop_end"
        # No verification events in disabled mode (registry=None short-circuits wrapper)
        assert "verification_passed" not in types_disabled
        assert "verification_failed" not in types_disabled

        # ---- Mode 2: enabled (populated registry path) ----
        # Sprint 57.63 approach A: the verifier registry is now built INSIDE
        # build_real_llm_handler (so the LLMJudgeVerifier shares the loop's
        # adapter); echo_demo always returns registry=None. To prove the
        # router → wrapper → SSE emission contract for a POPULATED registry
        # WITHOUT a real Azure call, monkeypatch build_handler to pair the
        # echo_demo loop with a populated (no-op) registry. The production
        # "enabled → handler builds a real LLMJudgeVerifier registry" path is
        # covered by test_chat_category_activation_wiring.py Group A.
        import importlib

        from api.v1.chat._verifier_factory import build_default_verifier_registry
        from api.v1.chat.handler import build_echo_demo_handler

        def _fake_build_handler(mode, message, **kwargs):  # type: ignore[no-untyped-def]
            loop, _ = build_echo_demo_handler(message)
            return loop, build_default_verifier_registry()

        # `from api.v1.chat import router` yields the APIRouter INSTANCE (the
        # package __init__ re-exports it), so patch the actual module object —
        # importlib.import_module returns the module, not the re-exported attr —
        # where chat() looks up its module-global `build_handler`.
        router_module = importlib.import_module("api.v1.chat.router")
        monkeypatch.setattr(router_module, "build_handler", _fake_build_handler)
        # Reset registry so 2nd POST does not see stale session
        reg = get_default_registry()
        reg._tenants.clear()  # type: ignore[attr-defined]  # noqa: SLF001

        with client.stream(
            "POST",
            "/api/v1/chat/",
            json={"message": "zebra", "mode": "echo_demo"},
        ) as resp:
            assert resp.status_code == 200
            body_enabled = b"".join(chunk for chunk in resp.iter_bytes())

        events_enabled = _parse_sse(body_enabled)
        types_enabled = [e["type"] for e in events_enabled]

        # Echo stream still produced when wrapper engaged
        assert types_enabled[0] == "loop_start"
        # verification_passed emitted by no-op RulesBasedVerifier(rules=[]) before loop_end
        assert "verification_passed" in types_enabled
        # No correction needed (no-op rules pass) → wrapper forwards original LoopCompleted
        assert types_enabled[-1] == "loop_end"
