"""
File: backend/tests/integration/api/test_chat_e2e.py
Purpose: End-to-end SSE round-trip — POST /api/v1/chat/ → multi-event echo flow,
    plus multi-tenant isolation + trace_id propagation acceptance.
Category: tests / integration
Scope: Phase 50 / Sprint 50.2 (Day 4.6) — Sprint 52.5 Day 2.5 (P0 #11+#12+#16)

Modification History (newest-first):
    - 2026-05-01: Sprint 52.5 Day 2.5 (P0 #11 + #12 + #16) — replaced
        skip-tenant-middleware fixture with dependency_overrides for
        get_current_tenant; added MultiTenantE2E + TraceIdE2E classes;
        switched registry reset from `_entries.clear()` (V1 attribute name)
        to `_tenants.clear()` (post-refactor attribute name).
    - 2026-04-30: Initial creation (Sprint 50.2 Day 4.6)
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.chat import router as chat_router
from api.v1.chat.session_registry import get_default_registry
from platform_layer.identity import get_current_tenant, get_current_user_id

# Module-level deterministic tenant for single-tenant tests.
DEFAULT_TENANT = UUID("11111111-1111-1111-1111-111111111111")
DEFAULT_USER_ID = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def app() -> FastAPI:
    """E2E app with chat router + dep override that pins tenant_id.

    Sprint 52.5 P0 #11: instead of skipping tenant middleware (V1 pattern),
    we override the FastAPI dep so the router still goes through the
    Depends(get_current_tenant) path and registry calls receive a real
    tenant_id. The full TenantContextMiddleware path (JWT decode) is
    exercised by tests/integration/api/test_jwt_auth.py.
    """
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
    reg = get_default_registry()
    reg._tenants.clear()  # type: ignore[attr-defined]  # noqa: SLF001
    yield
    reg._tenants.clear()  # type: ignore[attr-defined]  # noqa: SLF001


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
# Existing 50.2 Day 4.6 tests (refactored: signatures + clear key)
# ============================================================


def test_e2e_echo_demo_full_loop_event_sequence(client: TestClient) -> None:
    """End-to-end: POST echo_demo → 8-event stream including
    new TurnStarted / LLMRequested / LLMResponded events from Day 2."""
    with client.stream(
        "POST",
        "/api/v1/chat/",
        json={"message": "zebra", "mode": "echo_demo"},
    ) as resp:
        assert resp.status_code == 200
        body = b"".join(chunk for chunk in resp.iter_bytes())

    events = _parse_sse(body)
    types = [e["type"] for e in events]

    # Sprint 50.2 Day 2 expanded event sequence:
    #   loop_start
    #   turn_start, llm_request, llm_response (turn 1)
    #     tool_call_request, tool_call_result
    #   turn_start, llm_request, llm_response (turn 2)
    #   loop_end
    assert types[0] == "loop_start"
    assert types[-1] == "loop_end"
    assert types.count("turn_start") == 2
    assert types.count("llm_request") == 2
    assert types.count("llm_response") == 2
    assert types.count("tool_call_request") == 1
    assert types.count("tool_call_result") == 1

    # The tool_call_result must echo the user's text.
    tool_result = next(e for e in events if e["type"] == "tool_call_result")
    assert tool_result["data"]["is_error"] is False
    assert tool_result["data"]["result"] == "zebra"
    assert tool_result["data"]["tool_name"] == "echo_tool"

    # llm_response on the last turn carries the echoed text.
    final_llm = [e for e in events if e["type"] == "llm_response"][-1]
    assert final_llm["data"]["content"] == "zebra"

    # loop_end carries total_turns + stop_reason.
    end = events[-1]
    assert end["data"]["stop_reason"] == "end_turn"
    assert end["data"]["total_turns"] == 1


def test_e2e_session_id_in_response_header(client: TestClient) -> None:
    """Every POST /chat returns X-Session-Id so frontend can poll session state."""
    with client.stream(
        "POST", "/api/v1/chat/", json={"message": "hi", "mode": "echo_demo"}
    ) as resp:
        sid = resp.headers["x-session-id"]
        for _ in resp.iter_bytes():
            pass

    # Session marked completed after stream drains.
    get_resp = client.get(f"/api/v1/chat/sessions/{sid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "completed"


def test_e2e_cancellation_marks_session_cancelled(client: TestClient) -> None:
    """Cancel endpoint flips status without needing the stream to finish."""
    import asyncio

    sid_uuid = UUID("12345678-1234-5678-1234-567812345678")
    reg = get_default_registry()
    asyncio.run(reg.register(DEFAULT_TENANT, sid_uuid))

    cancel_resp = client.post(f"/api/v1/chat/sessions/{sid_uuid}/cancel")
    assert cancel_resp.status_code == 204

    get_resp = client.get(f"/api/v1/chat/sessions/{sid_uuid}")
    assert get_resp.json()["status"] == "cancelled"


# ============================================================
# Sprint 52.5 P0 #12 acceptance — TraceContext propagation E2E
# ============================================================


class TestTraceIdPropagationE2E:
    """End-to-end TraceContext.create_root() coverage:
    - X-Trace-Id response header set
    - Every emitted SSE event carries data.trace_id matching the header
    """

    def test_x_trace_id_header_present_and_uuid_hex(self, client: TestClient) -> None:
        with client.stream(
            "POST", "/api/v1/chat/", json={"message": "ping", "mode": "echo_demo"}
        ) as resp:
            assert resp.status_code == 200
            trace_id = resp.headers["x-trace-id"]
            for _ in resp.iter_bytes():
                pass
        # TraceContext.create_root() default is uuid4().hex → 32 hex chars
        assert isinstance(trace_id, str) and len(trace_id) == 32
        int(trace_id, 16)  # raises if non-hex

    def test_every_sse_event_carries_matching_trace_id(self, client: TestClient) -> None:
        """All 8+ SSE frames must share the same trace_id as X-Trace-Id."""
        with client.stream(
            "POST",
            "/api/v1/chat/",
            json={"message": "ping", "mode": "echo_demo"},
        ) as resp:
            assert resp.status_code == 200
            header_tid = resp.headers["x-trace-id"]
            body = b"".join(chunk for chunk in resp.iter_bytes())

        events = _parse_sse(body)
        assert events, "no SSE events received"
        for ev in events:
            data = ev["data"]
            assert data is not None, f"event {ev['type']} has no data"
            assert "trace_id" in data, (
                f"event {ev['type']} missing trace_id field — sse.py wrapper "
                "should have injected it"
            )
            assert data["trace_id"] == header_tid, (
                f"event {ev['type']} trace_id={data['trace_id']!r} != " f"X-Trace-Id={header_tid!r}"
            )


# ============================================================
# Sprint 52.5 P0 #11 acceptance — multi-tenant isolation E2E
# ============================================================


class TestMultiTenantE2E:
    """End-to-end cross-tenant isolation:
    - Tenant A creates a session via POST /chat
    - Tenant B GET /sessions/{sid} → 404 (never reveal existence)
    - Tenant B POST /sessions/{sid}/cancel → 404
    - Tenant B's cancel attempt does NOT flip Tenant A's session
    """

    def _make_tenant_app(self, tenant: UUID) -> FastAPI:
        inst = FastAPI()
        inst.include_router(chat_router, prefix="/api/v1")
        inst.dependency_overrides[get_current_tenant] = lambda t=tenant: t
        inst.dependency_overrides[get_current_user_id] = lambda: DEFAULT_USER_ID
        return inst

    def test_tenant_b_cannot_read_tenant_a_session(self) -> None:
        tenant_a = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        tenant_b = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

        # Tenant A creates session
        app_a = self._make_tenant_app(tenant_a)
        with TestClient(app_a) as tc_a:
            with tc_a.stream(
                "POST",
                "/api/v1/chat/",
                json={"message": "secret-A", "mode": "echo_demo"},
            ) as resp:
                sid = resp.headers["x-session-id"]
                for _ in resp.iter_bytes():
                    pass
            # Sanity: tenant A sees status=completed
            assert tc_a.get(f"/api/v1/chat/sessions/{sid}").json()["status"] == "completed"

        # Tenant B tries to read same session_id
        app_b = self._make_tenant_app(tenant_b)
        with TestClient(app_b) as tc_b:
            resp_b = tc_b.get(f"/api/v1/chat/sessions/{sid}")
        assert resp_b.status_code == 404

    def test_tenant_b_cannot_cancel_tenant_a_session(self) -> None:
        import asyncio

        tenant_a = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        tenant_b = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        sid = uuid4()

        # Pre-register a running session under tenant A directly.
        reg = get_default_registry()
        entry_a = asyncio.run(reg.register(tenant_a, sid))

        # Tenant B attempts to cancel
        app_b = self._make_tenant_app(tenant_b)
        with TestClient(app_b) as tc_b:
            resp_b = tc_b.post(f"/api/v1/chat/sessions/{sid}/cancel")
        assert resp_b.status_code == 404

        # Tenant A's entry must remain running (not flipped to cancelled).
        assert entry_a.status == "running"
        assert entry_a.cancel_event.is_set() is False

    def test_two_tenants_share_session_id_without_collision(self) -> None:
        """Same generated session_id → two independent registry entries."""
        tenant_a = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        tenant_b = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        forced_sid = "12345678-1234-1234-1234-123456789012"

        for tenant, app_inst in (
            (tenant_a, self._make_tenant_app(tenant_a)),
            (tenant_b, self._make_tenant_app(tenant_b)),
        ):
            with TestClient(app_inst) as tc:
                with tc.stream(
                    "POST",
                    "/api/v1/chat/",
                    json={
                        "message": "hi",
                        "mode": "echo_demo",
                        "session_id": forced_sid,
                    },
                ) as resp:
                    assert resp.status_code == 200
                    for _ in resp.iter_bytes():
                        pass

        # Each tenant sees their own session as completed; the other tenant
        # does not see it via the API.
        for tenant, app_inst in (
            (tenant_a, self._make_tenant_app(tenant_a)),
            (tenant_b, self._make_tenant_app(tenant_b)),
        ):
            with TestClient(app_inst) as tc:
                resp = tc.get(f"/api/v1/chat/sessions/{forced_sid}")
                assert resp.status_code == 200
                assert resp.json()["status"] == "completed"


# ============================================================
# Sprint 52.5 P0 #16 acceptance — adapter LLM-call span sanity
# ============================================================


class TestAdapterTracerSpanIntegration:
    """Echo demo uses MockChatClient (no adapter spans), but the
    contract that adapters MUST emit `llm_chat` spans is validated
    structurally by direct adapter unit tests + the tracer fixture
    pattern. This integration test is a sanity check that the
    adapter constructor still accepts the new tracer kwarg under
    the standard `build_real_llm_handler` env-var-gated path
    (skipped without Azure env). Documenting here so the audit has
    a concrete pointer for issue #16.
    """

    def test_adapter_constructor_accepts_tracer_kwarg_signature(self) -> None:
        """Signature regression test: AzureOpenAIAdapter(config, tracer=...)
        is the new V2 contract; this guards against accidental removal."""
        import inspect

        from adapters.azure_openai.adapter import AzureOpenAIAdapter

        sig = inspect.signature(AzureOpenAIAdapter.__init__)
        params = sig.parameters
        assert "tracer" in params, (
            "AzureOpenAIAdapter.__init__ must accept a tracer kwarg "
            "(P0 #16 — adapter LLM-call span)."
        )
        assert params["tracer"].kind == inspect.Parameter.KEYWORD_ONLY


# ============================================================
# Sprint 57.66 (A-5a+) acceptance — diagnostic events reach client E2E
# ============================================================


class TestDiagnosticEventsE2E:
    """End-to-end proof (honors AP-4 — prove events reach the client through the
    full router pipeline, not just the isolated serializer):

    Before Sprint 57.66 Stage 1, ContextCompacted / PromptBuilt /
    StateCheckpointed / TripwireTriggered were yielded on the chat path but
    silently dropped at ``router.py`` (``except NotImplementedError: continue``,
    L354-359). Stage 1 added their ``sse.py`` isinstance branches; this test
    drives the real router pipeline (``run_with_verification`` →
    ``serialize_loop_event`` → ``format_sse_message`` → SSE frame) with a mocked
    loop and asserts the 4 events now surface as wire frames, plus the two 57.65
    cache fields are carried on ``llm_response`` / ``loop_end``.

    The loop generator is replaced by patching
    ``api.v1.chat.router.run_with_verification`` (patched where used, not where
    defined). Finalization deps (quota / SLA / cost_ledger / db) default to None
    in the minimal ``app`` fixture, so the fake LoopCompleted skips those gated
    branches.
    """

    def test_four_diagnostic_events_plus_cache_fields_reach_client(
        self, client: TestClient
    ) -> None:
        from unittest.mock import patch

        from agent_harness._contracts import (
            ContextCompacted,
            LLMResponded,
            LoopCompleted,
            LoopStarted,
            PromptBuilt,
            StateCheckpointed,
            TraceContext,
            TripwireTriggered,
        )

        sid = uuid4()
        tc = TraceContext(tenant_id=DEFAULT_TENANT, session_id=sid, user_id=DEFAULT_USER_ID)

        async def _fake_run_with_verification(**_kwargs: object):  # type: ignore[no-untyped-def]
            """Deterministic fake loop — ignores agent_loop / other kwargs.

            Yields a fixed sequence including the 4 previously-dropped
            diagnostic events plus the 57.65 cache carriers.
            """
            yield LoopStarted(session_id=sid, trace_context=tc)
            yield PromptBuilt(
                messages_count=5,
                estimated_input_tokens=1000,
                cache_breakpoints_count=2,
                memory_layers_used=("session", "tenant"),
                position_strategy_used="lost_in_middle",
                duration_ms=2.0,
                trace_context=tc,
            )
            yield ContextCompacted(
                tokens_before=9000,
                tokens_after=3500,
                compaction_strategy="summarize",
                messages_compacted=10,
                duration_ms=5.0,
                trace_context=tc,
            )
            yield StateCheckpointed(version=3, trace_context=tc)
            yield TripwireTriggered(
                violation_type="pii_leak", detail="ssn detected", trace_context=tc
            )
            yield LLMResponded(content="ok", cached_input_tokens=128, trace_context=tc)
            yield LoopCompleted(
                stop_reason="end_turn",
                total_turns=1,
                cached_input_tokens=256,
                cache_hit_rate=0.5,
                trace_context=tc,
            )

        with patch(
            "api.v1.chat.router.run_with_verification",
            side_effect=_fake_run_with_verification,
        ):
            with client.stream(
                "POST",
                "/api/v1/chat/",
                json={"message": "x", "mode": "echo_demo"},
            ) as resp:
                assert resp.status_code == 200
                body = b"".join(chunk for chunk in resp.iter_bytes())

        events = _parse_sse(body)
        types = [e["type"] for e in events]

        # The 4 events silently dropped before Stage 1 now appear as frames.
        for diag_type in (
            "prompt_built",
            "context_compacted",
            "state_checkpointed",
            "tripwire_triggered",
        ):
            assert diag_type in types, f"{diag_type} frame missing from SSE stream"

        # prompt_built: scope-key list (no memory-content leak) + trace_id carried.
        prompt_built = next(e for e in events if e["type"] == "prompt_built")
        assert prompt_built["data"]["memory_layers_used"] == ["session", "tenant"]
        assert prompt_built["data"]["trace_id"] == tc.trace_id

        # llm_response carries the 57.65 cached_input_tokens.
        llm_response = next(e for e in events if e["type"] == "llm_response")
        assert llm_response["data"]["cached_input_tokens"] == 128

        # loop_end carries the 57.65 cache fields.
        loop_end = next(e for e in events if e["type"] == "loop_end")
        assert loop_end["data"]["cached_input_tokens"] == 256
        # FIX-025 (same sprint): `_jsonable` now str-coerces only UUID, not
        # float, so cache_hit_rate round-trips as a JSON number (was "0.5").
        assert loop_end["data"]["cache_hit_rate"] == 0.5
        assert isinstance(loop_end["data"]["cache_hit_rate"], float)
