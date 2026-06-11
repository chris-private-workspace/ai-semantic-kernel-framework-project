"""
File: backend/src/adapters/azure_openai/profile.py
Purpose: build_azure_model_profile — build the {action, cheap} ModelProfile for Azure.
Category: Adapters / Azure OpenAI
Scope: Phase 57 / Sprint 57.97

Description:
    Builds a ModelProfile pairing the (already-constructed) strong `action`
    Azure client with a `cheap` Azure client. The cheap client is a SECOND
    AzureOpenAIAdapter on AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME, reusing the SAME
    endpoint / api_key / api_version (loaded from the shared AZURE_OPENAI_* env)
    and overriding only the deployment + model name.

    Fallback: when AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME is unset, `cheap` IS the
    strong client (same instance) → byte-identical behavior. Safe to ship
    without a 2nd deployment.

    Cost attribution note: the cost-ledger (platform_layer/billing/cost_ledger.py)
    prices an LLM call via config/llm_pricing.yml keyed by (provider, model) — NOT
    by the adapter's config pricing field (which the cost-ledger ignores for the
    strong tier too). So the cheap tier's saving becomes visible in the cost-ledger
    purely because the cheap deployment returns its OWN model name: the verification
    call records a distinct `azure_openai_<cheap-model>_verification_*` sub_type
    (vs the main turn's `azure_openai_<strong-model>_*`). The model-attribution
    difference is visible regardless of pricing; for a $ delta, both the cheap and
    the strong model must be priced in config/llm_pricing.yml.

Key Components:
    - build_azure_model_profile(policy=None) -> ModelProfile
    - _azure_config(deployment, model) -> AzureOpenAIConfig (override only the set fields)

Created: 2026-06-09 (Sprint 57.97)
Last Modified: 2026-06-11

Modification History (newest-first):
    - 2026-06-11: Sprint 57.104 C1 — take a ModelPolicy; build action+cheap from policy ∪ env
    - 2026-06-09: Initial creation (Sprint 57.97) — Azure cheap-tier ModelProfile builder

Related:
    - adapters/_base/model_profile.py — the neutral ModelProfile type
    - api/v1/chat/handler.py — the sole caller (build_real_llm_handler)
    - platform_layer/billing/cost_ledger.py — prices via config/llm_pricing.yml (model-keyed)
    - 24-multi-model-profile-design.md — design note
"""

from __future__ import annotations

import os

from adapters._base.chat_client import ChatClient
from adapters._base.model_policy import ModelPolicy
from adapters._base.model_profile import ModelProfile
from adapters.azure_openai.adapter import AzureOpenAIAdapter
from adapters.azure_openai.config import AzureOpenAIConfig


def build_azure_model_profile(policy: ModelPolicy | None = None) -> ModelProfile:
    """Build the {action, cheap} ModelProfile for Azure from an optional tenant policy.

    The action client is built on the tenant's `action_deployment` / `action_model`
    when set, else the system AZURE_OPENAI_* env default. The cheap client is built
    on the tenant's `cheap_deployment` / `cheap_model` when set, else the
    AZURE_OPENAI_CHEAP_* env, else (no cheap configured anywhere) `cheap` IS `action`
    (the SAME instance → byte-identical behavior + cost). A None / all-None policy is
    byte-identical to the Sprint 57.97 env-only path.

    Cost attribution: the per-tier saving is visible in the cost ledger purely
    because each deployment returns its OWN model name (the ledger keys sub_type by
    model, not by the adapter config) — see the module docstring.
    """
    pol = policy or ModelPolicy()

    # Action tier: the tenant override OR the AZURE_OPENAI_* env default. The shared
    # endpoint / api_key / api_version always load from env (never passed here).
    action_client: ChatClient = AzureOpenAIAdapter(
        _azure_config(pol.action_deployment, pol.action_model)
    )

    # Cheap tier: the tenant override OR the AZURE_OPENAI_CHEAP_* env. When neither
    # is set, cheap IS action (the same instance) → byte-identical (57.97 fallback).
    cheap_deployment = (
        pol.cheap_deployment or os.environ.get("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", "").strip()
    )
    if not cheap_deployment:
        return ModelProfile(action=action_client, cheap=action_client)

    cheap_model = (
        pol.cheap_model
        or os.environ.get("AZURE_OPENAI_CHEAP_MODEL_NAME", "").strip()
        or cheap_deployment
    )
    cheap_client: ChatClient = AzureOpenAIAdapter(_azure_config(cheap_deployment, cheap_model))
    return ModelProfile(action=action_client, cheap=cheap_client)


def _azure_config(deployment: str | None, model: str | None) -> AzureOpenAIConfig:
    """Build an AzureOpenAIConfig overriding ONLY the set fields.

    Day-0 D3 (Sprint 57.104): AzureOpenAIConfig is a BaseSettings (env_prefix
    "AZURE_OPENAI_"); explicit kwargs WIN over env and passing None overrides to
    None. So include `deployment_name` / `model_name` ONLY when a concrete value is
    given; omitting the kwarg lets BaseSettings load the env default — keeping one
    definition of "the default deployment" (the env). The shared endpoint / api_key /
    api_version are never passed here, so they always load from env.
    """
    if deployment and model:
        return AzureOpenAIConfig(deployment_name=deployment, model_name=model)
    if deployment:
        return AzureOpenAIConfig(deployment_name=deployment)
    if model:
        return AzureOpenAIConfig(model_name=model)
    return AzureOpenAIConfig()
