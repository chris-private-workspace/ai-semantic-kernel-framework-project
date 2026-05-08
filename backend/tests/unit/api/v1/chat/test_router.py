"""
File: backend/tests/unit/api/v1/chat/test_router.py
Purpose: Unit tests for /api/v1/chat router — POST SSE + sessions endpoints.
Category: tests
Scope: Phase 50 / Sprint 50.2 (Day 1.5) — Sprint 52.5 Day 2 (P0 #11+#12 dep + tenant)

Modification History (newest-first):
    - 2026-05-01: Sprint 52.5 Day 2 (P0 #11+#12) — every test exercises
        Depends(get_current_tenant) via dependency_overrides; storage
        reset uses _tenants.clear(); register() calls carry tenant_id;
        new TestMultiTenantIsolation class verifies cross-tenant 404.
    - 2026-04-30: Initial creation (Sprint 50.2 Day 1.5)
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
from platform_layer.identity import get_current_tenant
from platform_layer.identity.auth import get_current_user_id

# Fixed UUID per test module — most single-tenant tests share it. Multi-tenant
# tests build their own pair via uuid4() inside the test body.
DEFAULT_TENANT = UUID("11111111-1111-1111-1111-111111111111")
# Sprint 57.7 US-R1: get_current_user_id added to chat() Depends — provide
# a deterministic override matching DEFAULT_TENANT's namespace.
DEFAULT_USER_ID = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def app() -> FastAPI:
    """Minimal app — chat router only, no real tenant middleware / OTel.

    Override `get_current_tenant` to return `DEFAULT_TENANT` deterministically
    so unit tests don't need to mint JWT tokens or install middleware. The
    full middleware path is exercised by integration tests.
    """
    inst = FastAPI()
    inst.include_router(chat_router, prefix="/api/v1")
    inst.dependency_overrides[get_current_tenant] = lambda: DEFAULT_TENANT
    # Sprint 57.7 US-R1: chat() now Depends(get_current_user_id);
    # mirror the tenant override so unit tests don't need real JWT.
    inst.dependency_overrides[get_current_user_id] = lambda: DEFAULT_USER_ID
    return inst


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as tc:
        yield tc


@pytest.fixture(autouse=True)
def _reset_default_registry() -> Iterator[None]:
    """Each test starts with an empty default registry."""
    reg = get_default_registry()
    reg._tenants.clear()  # type: ignore[attr-defined]  # noqa: SLF001
    yield
    reg._tenants.clear()  # type: ignore[attr-defined]  # noqa: SLF001


@pytest.fixture(autouse=True)
def _disable_db_observers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sprint 57.7 US-R1: disable sessions/tool_calls/audit observers in unit
    tests since the test FastAPI app has no real DB session factory wired.
    Production default is "true"; integration tests override per-suite."""
    monkeypatch.setenv("SESSIONS_CHAT_OBSERVER", "false")
    monkeypatch.setenv("TOOL_CALLS_CHAT_OBSERVER", "false")
    monkeypatch.setenv("AUDIT_LOG_CHAT_OBSERVER", "false")


def _parse_sse(body: bytes) -> list[dict]:
    """Parse `event:\\ndata:\\n\\n` frames into list of {type, data}."""
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


class TestPostChat:
    def test_echo_demo_streams_loop_events(self, client: TestClient) -> None:
        with client.stream(
            "POST",
            "/api/v1/chat/",
            json={"message": "zebra", "mode": "echo_demo"},
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            headers_lower = {k.lower(): v for k, v in resp.headers.items()}
            assert "x-session-id" in headers_lower
            # P0 #12: chat router exposes the root trace_id via header for
            # frontend correlation with Jaeger / log search.
            assert "x-trace-id" in headers_lower
            body = b"".join(chunk for chunk in resp.iter_bytes())

        events = _parse_sse(body)
        types = [e["type"] for e in events]
        # echo demo emits: loop_start, llm_response (turn 1 thinking),
        # tool_call_request, llm_response (turn 2), loop_end
        assert types[0] == "loop_start"
        assert "tool_call_request" in types
        assert "loop_end" == types[-1]
        # tool_call_request should carry the user's message as echo_tool args
        tool_req = next(e for e in events if e["type"] == "tool_call_request")
        assert tool_req["data"]["tool_name"] == "echo_tool"
        assert tool_req["data"]["args"] == {"text": "zebra"}
        # final llm_response should echo the message back
        last_thinking = [e for e in events if e["type"] == "llm_response"][-1]
        assert last_thinking["data"]["content"] == "zebra"
        # P0 #12: every emitted event carries trace_id matching the X-Trace-Id header.
        header_trace = headers_lower["x-trace-id"]
        for ev in events:
            assert ev["data"]["trace_id"] == header_trace, (
                f"trace_id mismatch on event {ev['type']}: "
                f"got {ev['data']['trace_id']!r}, header {header_trace!r}"
            )

    def test_empty_message_rejected_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/chat/", json={"message": "", "mode": "echo_demo"})
        assert resp.status_code == 422

    def test_invalid_mode_rejected_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/chat/", json={"message": "x", "mode": "bogus"})
        assert resp.status_code == 422

    def test_missing_message_rejected_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/chat/", json={"mode": "echo_demo"})
        assert resp.status_code == 422

    def test_real_llm_without_env_returns_503(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
        resp = client.post("/api/v1/chat/", json={"message": "x", "mode": "real_llm"})
        assert resp.status_code == 503

    def test_session_id_persisted_after_stream(self, client: TestClient) -> None:
        with client.stream(
            "POST", "/api/v1/chat/", json={"message": "x", "mode": "echo_demo"}
        ) as resp:
            sid_header = resp.headers["x-session-id"]
            # drain
            for _ in resp.iter_bytes():
                pass

        sid = UUID(sid_header)
        # GET sessions/{id} should now report completed
        get_resp = client.get(f"/api/v1/chat/sessions/{sid}")
        assert get_resp.status_code == 200
        body = get_resp.json()
        assert body["status"] == "completed"


class TestGetSession:
    def test_returns_404_for_unknown_session(self, client: TestClient) -> None:
        resp = client.get(f"/api/v1/chat/sessions/{uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_running_after_register(self, app: FastAPI, client: TestClient) -> None:
        sid = uuid4()
        reg = get_default_registry()
        await reg.register(DEFAULT_TENANT, sid)
        resp = client.get(f"/api/v1/chat/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"


class TestCancelSession:
    @pytest.mark.asyncio
    async def test_cancel_running_session(self, app: FastAPI, client: TestClient) -> None:
        sid = uuid4()
        reg = get_default_registry()
        await reg.register(DEFAULT_TENANT, sid)
        resp = client.post(f"/api/v1/chat/sessions/{sid}/cancel")
        assert resp.status_code == 204
        # GET reflects cancelled
        get_resp = client.get(f"/api/v1/chat/sessions/{sid}")
        assert get_resp.json()["status"] == "cancelled"

    def test_cancel_unknown_returns_404(self, client: TestClient) -> None:
        resp = client.post(f"/api/v1/chat/sessions/{uuid4()}/cancel")
        assert resp.status_code == 404


class TestMultiTenantIsolation:
    """P0 #11 — cross-tenant session lookups must 404 (never reveal existence).

    Why this matters: V1 W3-2 audit confirmed chat router was 0-tenant-aware.
    These tests would have been impossible to write pre-refactor.
    """

    @pytest.mark.asyncio
    async def test_get_session_404_when_session_belongs_to_other_tenant(self, app: FastAPI) -> None:
        # Tenant A registers a session directly via registry; client uses
        # default override (DEFAULT_TENANT) which differs → expect 404.
        other_tenant = uuid4()
        sid = uuid4()
        reg = get_default_registry()
        await reg.register(other_tenant, sid)
        with TestClient(app) as tc:
            resp = tc.get(f"/api/v1/chat/sessions/{sid}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_session_404_when_session_belongs_to_other_tenant(
        self, app: FastAPI
    ) -> None:
        other_tenant = uuid4()
        sid = uuid4()
        reg = get_default_registry()
        entry = await reg.register(other_tenant, sid)
        with TestClient(app) as tc:
            resp = tc.post(f"/api/v1/chat/sessions/{sid}/cancel")
        assert resp.status_code == 404
        # The other tenant's entry must remain untouched.
        assert entry.status == "running"
        assert entry.cancel_event.is_set() is False

    def test_two_tenants_can_have_same_session_id_via_separate_clients(self, app: FastAPI) -> None:
        """Two tenants run chats with the SAME generated session_id but stays isolated."""
        tenant_a = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        tenant_b = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        forced_sid = UUID("12345678-1234-1234-1234-123456789012")

        # Build two apps each pinned to one tenant.
        def _make_app(tenant: UUID) -> FastAPI:
            inst = FastAPI()
            inst.include_router(chat_router, prefix="/api/v1")
            inst.dependency_overrides[get_current_tenant] = lambda t=tenant: t
            # Sprint 57.7 US-R1: chat() Depends(get_current_user_id) too.
            inst.dependency_overrides[get_current_user_id] = lambda: DEFAULT_USER_ID
            return inst

        for tenant, app_inst in (
            (tenant_a, _make_app(tenant_a)),
            (tenant_b, _make_app(tenant_b)),
        ):
            with TestClient(app_inst) as tc:
                with tc.stream(
                    "POST",
                    "/api/v1/chat/",
                    json={
                        "message": "hi",
                        "mode": "echo_demo",
                        "session_id": str(forced_sid),
                    },
                ) as resp:
                    assert resp.status_code == 200
                    for _ in resp.iter_bytes():
                        pass

        # Both tenants now have an entry under same forced_sid.
        reg = get_default_registry()
        # Sprint 53.2 US-7 fix: use asyncio.run() per call to spawn a fresh
        # event loop. The previous `asyncio.get_event_loop().run_until_complete`
        # was fragile in full-suite runs (after async tests close their loops,
        # get_event_loop returns a closed/stale loop in pytest-asyncio AUTO
        # mode under Python 3.12+). asyncio.run is the supported pattern for
        # running a single async call from sync code.
        import asyncio

        a_entry = asyncio.run(reg.get(tenant_a, forced_sid))
        b_entry = asyncio.run(reg.get(tenant_b, forced_sid))
        assert a_entry is not None and b_entry is not None
        assert a_entry is not b_entry  # independent entries
