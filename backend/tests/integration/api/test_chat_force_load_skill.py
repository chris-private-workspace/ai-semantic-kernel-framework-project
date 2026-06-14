"""
File: backend/tests/integration/api/test_chat_force_load_skill.py
Purpose: Integration — force-load injects the picked skill via the per-tenant overlay (57.115).
Category: Tests / Integration / API (Skills System slash-command)
Scope: Sprint 57.115 / US-1 + US-3

Proves the force-load path works WITH the 57.114 per-tenant resolver (not just the
bundled set): the picked skill's FULL instructions land in the "## Active Skill"
system-prompt section deterministically, a tenant override is honored, and an
unknown name degrades gracefully. Azure-call-free (the 57.113/57.114 keystone
fake-env pattern): build_handler builds the adapter config with no network; we
only read loop._system_prompt.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.chat.handler import build_handler
from platform_layer.skills import reset_skill_registry_cache
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
def _reset_caches() -> object:
    from core.config import get_settings

    reset_skill_registry_cache()
    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    reset_skill_registry_cache()
    get_settings.cache_clear()  # type: ignore[attr-defined]


async def test_force_load_per_tenant_custom_skill_body(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_fake_azure(monkeypatch)
    tenant = await seed_tenant(db_session, code="SK_FL_CUSTOM")
    await tenant_skill_service.create(
        db_session,
        tenant_id=tenant.id,
        name="release-notes",
        description="d",
        instructions="TENANT-RELEASE-NOTES-BODY",
    )
    registry = await resolve_tenant_skill_registry(db_session, tenant.id)
    loop = build_handler(
        "real_llm", "go", skill_registry=registry, force_load_skill="release-notes"
    )
    system_prompt = loop._system_prompt  # type: ignore[attr-defined]
    assert "## Active Skill" in system_prompt
    assert 'selected the "release-notes" skill' in system_prompt
    assert "TENANT-RELEASE-NOTES-BODY" in system_prompt  # the per-tenant body, deterministically


async def test_force_load_overridden_skill_uses_overlay_body(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_fake_azure(monkeypatch)
    tenant = await seed_tenant(db_session, code="SK_FL_OVR")
    await tenant_skill_service.create(
        db_session,
        tenant_id=tenant.id,
        name="code-review",  # shadows the bundled code-review
        description="d",
        instructions="OVERRIDDEN-CHECKLIST-ONLY",
    )
    registry = await resolve_tenant_skill_registry(db_session, tenant.id)
    loop = build_handler(
        "real_llm", "review", skill_registry=registry, force_load_skill="code-review"
    )
    system_prompt = loop._system_prompt  # type: ignore[attr-defined]
    assert "## Active Skill" in system_prompt
    # Force-load respects the per-tenant override (not the bundled code-review body).
    assert "OVERRIDDEN-CHECKLIST-ONLY" in system_prompt


async def test_force_load_unknown_name_graceful_no_block(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_fake_azure(monkeypatch)
    tenant = await seed_tenant(db_session, code="SK_FL_UNK")
    registry = await resolve_tenant_skill_registry(db_session, tenant.id)
    loop = build_handler("real_llm", "x", skill_registry=registry, force_load_skill="nope-not-real")
    # An unknown / stale pick → no "## Active Skill" block (graceful; chat still runs).
    assert "## Active Skill" not in loop._system_prompt  # type: ignore[attr-defined]
