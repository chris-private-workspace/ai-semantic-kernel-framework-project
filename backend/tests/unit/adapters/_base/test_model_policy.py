"""
File: backend/tests/unit/adapters/_base/test_model_policy.py
Purpose: Unit tests for the ModelPolicy value object (from_dict / to_dict / is_empty).
Category: Tests / Adapters / _base
Scope: Phase 57 / Sprint 57.104 (C1)

Created: 2026-06-11
"""

from __future__ import annotations

from adapters._base.model_policy import ModelPolicy


def test_empty_policy_is_empty() -> None:
    assert ModelPolicy().is_empty()


def test_from_dict_none_or_empty_is_empty() -> None:
    assert ModelPolicy.from_dict(None).is_empty()
    assert ModelPolicy.from_dict({}).is_empty()


def test_from_dict_parses_all_fields() -> None:
    p = ModelPolicy.from_dict(
        {
            "action_deployment": "ad",
            "action_model": "am",
            "cheap_deployment": "cd",
            "cheap_model": "cm",
        }
    )
    assert (p.action_deployment, p.action_model, p.cheap_deployment, p.cheap_model) == (
        "ad",
        "am",
        "cd",
        "cm",
    )
    assert not p.is_empty()


def test_from_dict_strips_and_drops_empty_strings() -> None:
    p = ModelPolicy.from_dict(
        {"action_deployment": "  ad  ", "action_model": "", "cheap_deployment": "   "}
    )
    assert p.action_deployment == "ad"  # stripped
    assert p.action_model is None  # empty string → None
    assert p.cheap_deployment is None  # whitespace-only → None


def test_from_dict_ignores_non_str_values() -> None:
    p = ModelPolicy.from_dict({"action_deployment": 123, "action_model": None})
    assert p.action_deployment is None
    assert p.action_model is None


def test_to_dict_drops_none_fields() -> None:
    p = ModelPolicy(action_deployment="ad", cheap_model="cm")
    assert p.to_dict() == {"action_deployment": "ad", "cheap_model": "cm"}


def test_to_dict_empty() -> None:
    assert ModelPolicy().to_dict() == {}


def test_round_trip_from_dict_to_dict() -> None:
    p = ModelPolicy(action_deployment="ad", cheap_deployment="cd")
    assert ModelPolicy.from_dict(p.to_dict()) == p
