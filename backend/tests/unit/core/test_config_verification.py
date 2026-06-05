"""
File: backend/tests/unit/core/test_config_verification.py
Purpose: Unit tests for Settings.chat_verification_mode pydantic Literal validation.
Category: 範疇 10 (Verification Loops) / Tests
Scope: B-10 (AD-Cat10-VerifierFactory-Disposition) — migrated from test_verification_wire.py

Description:
    Validates `core.config.Settings.chat_verification_mode` accepts only the
    2-mode Literal["disabled", "enabled"] and rejects 3-mode legacy values.

    Migrated verbatim from `tests/unit/api/v1/chat/test_verification_wire.py`
    (Sprint 55.5) when `_verifier_factory.py` was removed (B-10): the factory
    tests were retired with the deleted code, but this Settings-validation test
    is independent of the factory and is preserved here per Never-Delete-Tests.

Created: 2026-05-31 (B-10)
Last Modified: 2026-05-31

Modification History (newest-first):
    - 2026-06-05: Sprint 57.83 — add judge_template default test (output_quality; B-8 leg-2)
    - 2026-05-31: B-10 migrate test_invalid_mode_raises (AD-Cat10-VerifierFactory)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.config import Settings


class TestChatVerificationModeValidation:
    """Settings.chat_verification_mode — pydantic Literal["disabled", "enabled"]."""

    def test_default_is_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default mode is 'disabled' (safe rollout — production unchanged)."""
        monkeypatch.delenv("CHAT_VERIFICATION_MODE", raising=False)
        assert Settings().chat_verification_mode == "disabled"

    def test_enabled_mode_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """'enabled' is a valid 2-mode value."""
        monkeypatch.setenv("CHAT_VERIFICATION_MODE", "enabled")
        assert Settings().chat_verification_mode == "enabled"

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """3-mode legacy value 'shadow' rejected by pydantic Literal validation.

        Sprint 55.5 D4+D5 drift response: real run_with_verification supports
        only 2 modes via registry-presence dispatch; no shadow/enforce. Settings
        Literal must enforce this at construction time.
        """
        monkeypatch.setenv("CHAT_VERIFICATION_MODE", "shadow")
        with pytest.raises(ValidationError):
            Settings()


class TestChatVerificationJudgeTemplate:
    """Settings.chat_verification_judge_template default (Sprint 57.83 B-8 leg-2)."""

    def test_default_is_output_quality(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default judge template is the general 'output_quality' judge (was
        'safety_review' — Cat 9-fitted, lean-unsafe; swapped Sprint 57.83 blocker B)."""
        monkeypatch.delenv("CHAT_VERIFICATION_JUDGE_TEMPLATE", raising=False)
        assert Settings().chat_verification_judge_template == "output_quality"
