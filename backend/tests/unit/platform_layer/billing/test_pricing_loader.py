"""PricingLoader tests (Sprint 56.3 Day 2 / US-3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from platform_layer.billing.pricing import PricingLoader

# Project-rooted yaml fixture (the real config file).
# test_pricing_loader.py is at:
# backend/tests/unit/platform_layer/billing/test_pricing_loader.py
# parents[0]=billing parents[1]=platform_layer parents[2]=unit parents[3]=tests
# parents[4]=backend → backend/config/llm_pricing.yml
_PRICING_YAML = Path(__file__).resolve().parents[4] / "config" / "llm_pricing.yml"


def test_pricing_loader_load_from_yaml_parses_3_providers() -> None:
    """yaml has azure_openai (3 models) + anthropic (1 model)."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)

    azure_mini = loader.get_llm_pricing("azure_openai", "gpt-4o-mini")
    assert azure_mini is not None
    assert azure_mini.input_per_million == 0.15
    assert azure_mini.output_per_million == 0.60
    assert azure_mini.cached_input_per_million == 0.075

    azure_54 = loader.get_llm_pricing("azure_openai", "gpt-5.4")
    assert azure_54 is not None
    assert azure_54.input_per_million == 2.50

    anthropic_sonnet = loader.get_llm_pricing("anthropic", "claude-3.7-sonnet")
    assert anthropic_sonnet is not None
    assert anthropic_sonnet.output_per_million == 15.00


def test_pricing_loader_get_tool_pricing_returns_default_when_unknown() -> None:
    """Unknown tool name → default_per_call applied."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)

    unknown = loader.get_tool_pricing("totally_unknown_tool")
    assert unknown.per_call == 0.0001  # default_per_call from yaml


def test_pricing_loader_get_tool_pricing_overrides_for_known() -> None:
    """Known tool override wins over default."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)

    salesforce = loader.get_tool_pricing("salesforce_query")
    assert salesforce.per_call == 0.001
    assert salesforce.per_call != 0.0001  # not the default

    d365 = loader.get_tool_pricing("d365_create")
    assert d365.per_call == 0.0005


def test_pricing_loader_unknown_provider_returns_none() -> None:
    """Bonus: unknown provider → None (defensive)."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)
    assert loader.get_llm_pricing("nonexistent_provider", "any_model") is None


def test_pricing_loader_missing_file_raises() -> None:
    """Bonus: missing yaml path raises FileNotFoundError."""
    loader = PricingLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_from_yaml(Path("/nonexistent/path/pricing.yml"))


# --- Sprint 57.79: date-suffix normalize (C-11 billing gap 1) ---------------


def test_pricing_loader_gpt52_exact_key() -> None:
    """gpt-5.2 base key prices exactly (Sprint 57.79 — added to yaml)."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)
    p = loader.get_llm_pricing("azure_openai", "gpt-5.2")
    assert p is not None
    assert p.input_per_million == 1.75
    assert p.output_per_million == 14.00
    assert p.cached_input_per_million == 0.175


def test_pricing_loader_date_suffix_normalizes_to_base() -> None:
    """A deployment model id with -YYYY-MM-DD suffix prices off the base key."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)
    # gpt-5.2-2025-12-11 (Azure deployment id) → base gpt-5.2
    p = loader.get_llm_pricing("azure_openai", "gpt-5.2-2025-12-11")
    assert p is not None
    assert p.input_per_million == 1.75
    assert p.output_per_million == 14.00


def test_pricing_loader_date_suffixed_unknown_base_returns_none() -> None:
    """A date-suffixed model whose stripped base is unknown still → None."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)
    assert loader.get_llm_pricing("azure_openai", "gpt-9.9-2025-12-11") is None


def test_pricing_loader_non_date_suffix_no_false_normalize() -> None:
    """A non-date suffix is NOT stripped (no false base match) → None."""
    loader = PricingLoader()
    loader.load_from_yaml(_PRICING_YAML)
    # "gpt-5.2-preview" has no -YYYY-MM-DD; must NOT normalize to gpt-5.2
    assert loader.get_llm_pricing("azure_openai", "gpt-5.2-preview") is None
