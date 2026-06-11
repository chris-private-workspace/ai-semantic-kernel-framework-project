"""
File: backend/src/adapters/_base/model_policy.py
Purpose: ModelPolicy — provider-neutral per-tenant model override (resolves to a ModelProfile).
Category: Adapters / _base (provider-neutral model selection)
Scope: Phase 57 / Sprint 57.104 (C1 — per-tenant model policy)

Description:
    A thin, provider-neutral value object carrying a tenant's OPTIONAL model
    overrides for the {action, cheap} tiers (deployment + canonical model name).
    Every field is optional: an absent field falls back to the system env default
    at build time, so an all-None policy is byte-identical to the Sprint 57.97
    env-only path. The Azure builder (adapters/azure_openai/profile.py) consumes
    this to construct the per-tenant ModelProfile; the resolver
    (platform_layer/billing/model_policy.py) produces it from
    tenant.meta_data["model_policy"].

    Pure config — references no ChatClient / SDK, so BOTH the adapters layer (the
    builder) and the platform_layer (the resolver) import it freely without a
    provider-neutrality concern.

Key Components:
    - ModelPolicy: frozen dataclass {action_deployment, action_model, cheap_deployment, cheap_model}

Created: 2026-06-11 (Sprint 57.104)
Last Modified: 2026-06-11

Modification History (newest-first):
    - 2026-06-11: Initial creation (Sprint 57.104 C1) — per-tenant model override value object

Related:
    - adapters/_base/model_profile.py — the {action, cheap} ChatClient pairing this resolves to
    - adapters/azure_openai/profile.py — the Azure builder consuming this
    - platform_layer/billing/model_policy.py — the tenant resolver producing this
    - api/v1/admin/tenants.py — the admin PUT/GET persisting it to meta_data["model_policy"]
    - 17-cross-category-interfaces.md §2.1 — ChatClient/ModelProfile contracts (this feeds them)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

# The meta_data["model_policy"] JSONB schema v1 keys — single source for the
# round-trip (from_dict / to_dict) + the admin endpoint's request shape.
_FIELDS = ("action_deployment", "action_model", "cheap_deployment", "cheap_model")


def _clean(value: Any) -> str | None:
    """Coerce a raw JSONB value to a non-empty stripped str, else None."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class ModelPolicy:
    """A tenant's optional {action, cheap} model overrides (deployment + model name).

    Every field is optional — an absent field falls back to the system env default
    at build time. An all-None policy (`is_empty()`) is byte-identical to the
    env-only path (Sprint 57.97).
    """

    action_deployment: str | None = None
    action_model: str | None = None
    cheap_deployment: str | None = None
    cheap_model: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> ModelPolicy:
        """Build from a raw meta_data["model_policy"] mapping (None / empty → all-None)."""
        if not data:
            return cls()
        return cls(
            action_deployment=_clean(data.get("action_deployment")),
            action_model=_clean(data.get("action_model")),
            cheap_deployment=_clean(data.get("cheap_deployment")),
            cheap_model=_clean(data.get("cheap_model")),
        )

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSONB-ready dict, dropping None fields (sparse storage)."""
        out: dict[str, str] = {}
        for field_name in _FIELDS:
            value = getattr(self, field_name)
            if value:
                out[field_name] = value
        return out

    def is_empty(self) -> bool:
        """True when no field is set (→ the env-only build path)."""
        return not any(getattr(self, field_name) for field_name in _FIELDS)
