"""
File: backend/tests/unit/platform_layer/tenant/test_rate_limit_parser_consistency.py
Purpose: Unit guard — admin-store / runtime-counter / validator parsers agree on validity.
Category: Tests / Unit / platform_layer.tenant (Phase 58.x RateLimits SyntaxValidation)
Scope: Sprint 57.61 Day 1 / US-2 (closes AD-RateLimits-SyntaxValidation-Phase58)

Description:
    Locks the three {label,value} parse entry points so a future edit to one
    window-alias table can't let the PUT validator accept a rate the runtime gate
    silently won't enforce:
      - store parse_config_item        (rate_limit_config_store)
      - counter parse_rate_limit_item  (rate_limit_counter)
      - validator is_recognized_rate_limit_value (rate_limit_config_store)

    Asserts over a shared input matrix:
      - RATE_OK     → store/counter not-None AND validator (True, None)
      - RATE_BAD    → store/counter None AND validator False
      - CONCURRENCY → validator True (display-only) BUT store/counter None
                      (documented intentional asymmetry — not enforced)
      - GARBAGE     → all three reject
    Plus an explicit assertion that the counter _WINDOW_TO_SECONDS key set equals
    the store _WINDOW_ALIASES key set, so a divergence fails loudly here.

Created: 2026-05-29 (Sprint 57.61 Day 1)

Modification History (newest-first):
    - 2026-05-29: Initial creation (Sprint 57.61 Day 1 / US-2 — parser-consistency guard)
"""

from __future__ import annotations

import pytest

from platform_layer.tenant import rate_limit_config_store as store
from platform_layer.tenant import rate_limit_counter as counter
from platform_layer.tenant.rate_limit_config_store import (
    is_recognized_rate_limit_value,
    parse_config_item,
)
from platform_layer.tenant.rate_limit_counter import parse_rate_limit_item

# Enforceable rates — every window alias + thousands separator covered.
RATE_OK = [
    "1 / sec",
    "100 / min",
    "1,000 / minute",
    "50 / hour",
    "9 / hr",
    "1 / day",
    "10 / second",
]
# Looks rate-ish but rejected (unsupported window / non-positive / non-numeric / shape).
RATE_BAD = ["50 / week", "0 / min", "-5 / min", "abc / min", "100 /", "/ min", "100", ""]
# Display-only concurrency — validator accepts, runtime parsers skip.
CONCURRENCY = ["50 concurrent", "1,000 concurrent", "5 CONCURRENT"]
# Pure garbage — all three reject.
GARBAGE = ["foo", "100 bananas", "concurrent", "min / 100"]

_LABEL = "API requests"


def _store_ok(value: str) -> bool:
    return parse_config_item({"label": _LABEL, "value": value}) is not None


def _counter_ok(value: str) -> bool:
    return parse_rate_limit_item({"label": _LABEL, "value": value}) is not None


@pytest.mark.parametrize("value", RATE_OK)
def test_rate_ok_all_three_recognize(value: str) -> None:
    """Enforceable rate → store + counter parse AND validator (True, None)."""
    assert _store_ok(value), value
    assert _counter_ok(value), value
    assert is_recognized_rate_limit_value(value) == (True, None), value


@pytest.mark.parametrize("value", RATE_BAD + GARBAGE)
def test_rate_bad_and_garbage_all_three_reject(value: str) -> None:
    """Malformed / garbage → store + counter None AND validator False."""
    assert not _store_ok(value), value
    assert not _counter_ok(value), value
    ok, reason = is_recognized_rate_limit_value(value)
    assert ok is False, value
    assert reason is not None, value


@pytest.mark.parametrize("value", CONCURRENCY)
def test_concurrency_validator_accepts_but_parsers_skip(value: str) -> None:
    """'N concurrent' → validator True (display-only) BUT store + counter None."""
    ok, reason = is_recognized_rate_limit_value(value)
    assert ok is True, value
    assert reason is None, value
    # Documented intentional asymmetry: not time-windowed → not enforceable.
    assert not _store_ok(value), value
    assert not _counter_ok(value), value


def test_window_alias_key_sets_match() -> None:
    """Counter _WINDOW_TO_SECONDS keys == store _WINDOW_ALIASES keys (fail loudly on drift).

    If a future edit adds a window alias to one table only, the PUT validator and
    the runtime gate would disagree on what's enforceable — caught here, not by a
    tenant silently losing enforcement.
    """
    assert set(counter._WINDOW_TO_SECONDS.keys()) == set(store._WINDOW_ALIASES.keys())
