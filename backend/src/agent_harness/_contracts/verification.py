"""
File: backend/src/agent_harness/_contracts/verification.py
Purpose: Single-source verification result type (VerificationResult).
Category: cross-category single-source contracts (per 17.md §1)
Scope: Phase 49 / Sprint 49.1

Description:
    Verifier.verify() returns a VerificationResult. If passed=False, the
    loop may trigger self-correction (max 2 attempts per spec).

Owner: 01-eleven-categories-spec.md §範疇 10
Single-source: 17.md §1.1

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-06-05

Modification History:
    - 2026-06-05: Sprint 57.82 — add judge token fields (input/output_tokens, model) for cost-ledger
    - 2026-04-29: Initial creation (Sprint 49.1)

Related:
    - 01-eleven-categories-spec.md §範疇 10 (Verification Loops)
    - 17-cross-category-interfaces.md §1.1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class VerificationResult:
    """Verifier.verify() output."""

    passed: bool
    verifier_name: str
    verifier_type: Literal["rules_based", "llm_judge", "external"]
    score: float | None = None  # 0.0-1.0 if applicable
    reason: str | None = None  # for failures
    suggested_correction: str | None = None
    # Sprint 57.82 (B-8 leg-1): judge LLM token usage, captured by LLMJudgeVerifier
    # so the wrapper can bubble it to LoopCompleted for cost-ledger/quota accounting.
    # Default 0/None — rules_based / external verifiers make no LLM call.
    input_tokens: int = 0
    output_tokens: int = 0
    model: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
