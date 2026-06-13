"""
File: backend/tests/integration/api/test_skills_per_tenant_wiring.py
Purpose: Per-tenant Skills overlay → build_handler wiring tests (Sprint 57.114 / US-3+US-4).
Category: Tests / Integration / API (Skills System per-tenant catalog)
Scope: Sprint 57.114

Description:
    Proves the per-tenant overlay reaches the chat main flow (the router swaps
    get_default_skill_registry() for resolve_tenant_skill_registry()). Azure-call-free
    (the 57.64/57.113 keystone fake-env pattern): build_handler constructs the adapter
    config object with no network; we only read loop._system_prompt + run read_skill
    through the real executor.

    - The resolver overlays a tenant's custom skill on the bundled set; build_handler's
      "## Available Skills" block carries it.
    - A no-custom tenant is byte-identical to the bundled path (regression).
    - A tenant override of a bundled skill name (code-review) returns the OVERRIDDEN
      body through read_skill.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import ToolCall
from agent_harness.skills.registry import get_default_skill_registry
from api.v1.chat.handler import build_handler
from business_domain._register_all import make_default_executor
from platform_layer.skills.service import resolve_tenant_skill_registry, tenant_skill_service
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio

_FAKE_AZURE_ENV = {
    "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "fake-key-not-used",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "fake-deploy",
}


def _set_fake_azure(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _FAKE_AZURE_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("CHAT_VERIFICATION_MODE", "disabled")
    from core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> object:
    from core.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


async def test_resolver_overlay_reaches_system_prompt(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_fake_azure(monkeypatch)
    tenant = await seed_tenant(db_session, code="SK_WIRE_OVL")
    await tenant_skill_service.create(
        db_session,
        tenant_id=tenant.id,
        name="release-notes",
        description="Turn commits into a release note",
        instructions="Heading / Highlights / Upgrade notes",
    )
    registry = await resolve_tenant_skill_registry(db_session, tenant.id)
    assert registry.get("release-notes") is not None
    assert registry.get("code-review") is not None  # bundled still present

    loop = build_handler("real_llm", "write release notes", skill_registry=registry)
    system_prompt = loop._system_prompt  # type: ignore[attr-defined]
    assert "## Available Skills" in system_prompt
    assert "release-notes" in system_prompt
    assert "code-review" in system_prompt  # bundled


async def test_no_custom_tenant_matches_bundled(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_fake_azure(monkeypatch)
    tenant = await seed_tenant(db_session, code="SK_WIRE_NONE")
    registry = await resolve_tenant_skill_registry(db_session, tenant.id)
    bundled_names = {s.name for s in get_default_skill_registry().list()}
    assert {s.name for s in registry.list()} == bundled_names

    loop = build_handler("real_llm", "hi", skill_registry=registry)
    bundled_loop = build_handler("real_llm", "hi", skill_registry=get_default_skill_registry())
    # Byte-identical to the bundled path (no per-tenant drift for an un-customized tenant).
    assert loop._system_prompt == bundled_loop._system_prompt  # type: ignore[attr-defined]


async def test_tenant_override_read_skill_returns_overridden_body(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_fake_azure(monkeypatch)
    tenant = await seed_tenant(db_session, code="SK_WIRE_OVR")
    await tenant_skill_service.create(
        db_session,
        tenant_id=tenant.id,
        name="code-review",  # shadows the bundled code-review
        description="Tenant override",
        instructions="RESPOND ONLY WITH A NUMBERED CHECKLIST.",
    )
    registry = await resolve_tenant_skill_registry(db_session, tenant.id)
    _reg, executor = make_default_executor(skill_registry=registry)
    res = await executor.execute(
        ToolCall(id="r", name="read_skill", arguments={"name": "code-review"})
    )
    assert res.success is True
    assert "# Skill: code-review" in res.content
    assert "RESPOND ONLY WITH A NUMBERED CHECKLIST." in res.content
