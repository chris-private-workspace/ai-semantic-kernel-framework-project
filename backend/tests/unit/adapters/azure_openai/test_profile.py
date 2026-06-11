"""
File: backend/tests/unit/adapters/azure_openai/test_profile.py
Purpose: Unit tests for build_azure_model_profile (cheap-tier + per-tenant policy builder).
Category: Tests / Adapters / Azure OpenAI
Scope: Phase 57 / Sprint 57.97 (cheap tier) + 57.104 (C1 per-tenant policy)

Created: 2026-06-09
Modified: 2026-06-11

Modification History:
    - 2026-06-11: Sprint 57.104 C1 — convert to the (policy) signature; the builder now
      BUILDS the action client (was passed in). Add per-tenant override + D3-omit cases.
    - 2026-06-09: Initial creation (Sprint 57.97)
"""

from __future__ import annotations

import pytest

from adapters._base.model_policy import ModelPolicy
from adapters.azure_openai.adapter import AzureOpenAIAdapter
from adapters.azure_openai.profile import build_azure_model_profile


@pytest.fixture
def _azure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Minimal Azure connection env so the action adapter constructs (placeholders).

    The builder now BUILDS the action client (Sprint 57.104), so every test needs a
    constructible connection. Cheap is unset by default (→ cheap IS action).
    """
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://placeholder.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "placeholder-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "system-deploy")
    monkeypatch.setenv("AZURE_OPENAI_MODEL_NAME", "system-model")
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_MODEL_NAME", raising=False)


def test_no_policy_unset_cheap_falls_back_to_action(_azure_env: None) -> None:
    """No policy + unset cheap env → cheap IS action (byte-identical 57.97 path)."""
    profile = build_azure_model_profile()
    assert isinstance(profile.action, AzureOpenAIAdapter)
    assert profile.cheap is profile.action  # same instance, no 2nd adapter
    assert profile.action.config.deployment_name == "system-deploy"
    assert profile.action.config.model_name == "system-model"


def test_empty_policy_is_byte_identical_to_none(_azure_env: None) -> None:
    """An all-None ModelPolicy resolves identically to no policy (env-only path)."""
    profile = build_azure_model_profile(ModelPolicy())
    assert isinstance(profile.action, AzureOpenAIAdapter)
    assert profile.cheap is profile.action
    assert profile.action.config.deployment_name == "system-deploy"


def test_env_cheap_deployment_builds_distinct_cheap_adapter(
    _azure_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Env cheap deployment (no policy) → distinct cheap adapter (57.97 behavior preserved)."""
    monkeypatch.setenv("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", "cheap-deploy")
    monkeypatch.setenv("AZURE_OPENAI_CHEAP_MODEL_NAME", "cheap-model")

    profile = build_azure_model_profile()

    assert profile.cheap is not profile.action
    cheap = profile.cheap
    assert isinstance(cheap, AzureOpenAIAdapter)
    assert cheap.config.deployment_name == "cheap-deploy"
    assert cheap.config.model_name == "cheap-model"


def test_env_cheap_defaults_model_name_to_deployment(
    _azure_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unset AZURE_OPENAI_CHEAP_MODEL_NAME → cheap model_name defaults to the deployment."""
    monkeypatch.setenv("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", "mini-deploy")
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_MODEL_NAME", raising=False)

    profile = build_azure_model_profile()
    cheap = profile.cheap
    assert isinstance(cheap, AzureOpenAIAdapter)
    assert cheap.config.deployment_name == "mini-deploy"
    assert cheap.config.model_name == "mini-deploy"  # falls back to the deployment name


# === Sprint 57.104 (C1) — per-tenant policy overrides ==========================


def test_policy_action_override_builds_action_on_tenant_deployment(_azure_env: None) -> None:
    """A policy action_deployment + action_model overrides the action adapter identity."""
    policy = ModelPolicy(action_deployment="tenant-deploy", action_model="tenant-model")
    profile = build_azure_model_profile(policy)
    action = profile.action
    assert isinstance(action, AzureOpenAIAdapter)
    assert action.config.deployment_name == "tenant-deploy"
    assert action.config.model_name == "tenant-model"
    # No cheap override + unset cheap env → cheap IS the (overridden) action.
    assert profile.cheap is profile.action


def test_policy_action_deployment_omits_model_uses_env_default(_azure_env: None) -> None:
    """D3: action_deployment set + action_model None → model_name OMITTED → env default.

    Passing model_name=None would override to None (BaseSettings); the builder omits
    the kwarg so AzureOpenAIConfig reads AZURE_OPENAI_MODEL_NAME (the env default).
    """
    policy = ModelPolicy(action_deployment="tenant-deploy")  # no action_model
    profile = build_azure_model_profile(policy)
    action = profile.action
    assert isinstance(action, AzureOpenAIAdapter)
    assert action.config.deployment_name == "tenant-deploy"
    assert action.config.model_name == "system-model"  # env default, NOT None


def test_policy_cheap_override_builds_distinct_cheap(_azure_env: None) -> None:
    """A policy cheap_deployment builds a distinct cheap adapter (no env cheap needed)."""
    policy = ModelPolicy(cheap_deployment="tenant-cheap", cheap_model="tenant-cheap-model")
    profile = build_azure_model_profile(policy)
    assert profile.cheap is not profile.action
    cheap = profile.cheap
    assert isinstance(cheap, AzureOpenAIAdapter)
    assert cheap.config.deployment_name == "tenant-cheap"
    assert cheap.config.model_name == "tenant-cheap-model"


def test_policy_overrides_both_tiers(_azure_env: None) -> None:
    """A full policy overrides both the action and the cheap tier independently."""
    policy = ModelPolicy(
        action_deployment="act-deploy",
        action_model="act-model",
        cheap_deployment="chp-deploy",
        cheap_model="chp-model",
    )
    profile = build_azure_model_profile(policy)
    action = profile.action
    cheap = profile.cheap
    assert isinstance(action, AzureOpenAIAdapter)
    assert isinstance(cheap, AzureOpenAIAdapter)
    assert action.config.deployment_name == "act-deploy"
    assert action.config.model_name == "act-model"
    assert cheap.config.deployment_name == "chp-deploy"
    assert cheap.config.model_name == "chp-model"
    assert cheap is not action
