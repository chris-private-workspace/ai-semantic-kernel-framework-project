"""
File: backend/tests/unit/adapters/azure_openai/test_max_tokens_param.py
Purpose: Unit tests for _max_tokens_param_name (Sprint 57.79 — C-11 billing gap 2).
Category: Tests / Unit / Adapters
Created: 2026-06-04

gpt-5.x rejects ``max_tokens`` (HTTP 400: use ``max_completion_tokens``);
gpt-4.x and earlier accept ``max_tokens``. The adapter keys the param name off
config.model_name.
"""

from __future__ import annotations

import pytest

from adapters.azure_openai.adapter import _max_tokens_param_name


@pytest.mark.parametrize(
    ("model_name", "expected"),
    [
        ("gpt-5.2", "max_completion_tokens"),
        ("gpt-5.2-2025-12-11", "max_completion_tokens"),
        ("gpt-5.4", "max_completion_tokens"),
        ("gpt-5", "max_completion_tokens"),
        ("gpt-4o", "max_tokens"),
        ("gpt-4o-mini", "max_tokens"),
        ("gpt-4", "max_tokens"),
        ("gpt-3.5-turbo", "max_tokens"),
    ],
)
def test_max_tokens_param_name(model_name: str, expected: str) -> None:
    """gpt-5.x → max_completion_tokens; older → max_tokens."""
    assert _max_tokens_param_name(model_name) == expected
