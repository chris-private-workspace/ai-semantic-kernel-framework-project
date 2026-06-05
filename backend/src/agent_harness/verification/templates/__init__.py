"""
File: backend/src/agent_harness/verification/templates/__init__.py
Purpose: Judge prompt template loader for LLMJudgeVerifier.
Category: 範疇 10 (Verification Loops)
Scope: Sprint 54.1 US-2

Description:
    `load_template(name)` reads `<name>.txt` from this directory and returns
    its contents. Templates contain `{output}` placeholder that LLMJudgeVerifier
    substitutes with the LLM output being verified.

    Default templates:
    - output_quality: general final-output quality — helpful/complete/accurate/on-topic (DEFAULT)
    - factual_consistency: source-vs-output consistency check
    - format_compliance: markdown / JSON / XML format check
    - safety_review: harmful / unsafe content check (Cat 9 fallback)
    - pii_leak_check: PII disclosure check (Cat 9 PII detector fallback)

Owner: 01-eleven-categories-spec.md §範疇 10

Created: 2026-05-04 (Sprint 54.1 Day 2)
Last Modified: 2026-06-05

Modification History:
    - 2026-06-05: Sprint 57.83 — add output_quality general judge to default templates list (B-8)
    - 2026-05-04: Initial creation (Sprint 54.1 US-2) — closes AD-Cat9-1 fallback
"""

from __future__ import annotations

from pathlib import Path


def load_template(name: str) -> str:
    """Load a judge prompt template by name.

    Args:
        name: Template basename without extension (e.g., "factual_consistency").

    Returns:
        Template content as string.

    Raises:
        FileNotFoundError: If `<name>.txt` does not exist in templates/.
    """
    template_path = Path(__file__).parent / f"{name}.txt"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Judge template '{name}' not found at {template_path}. "
            f"Available templates: {sorted(p.stem for p in template_path.parent.glob('*.txt'))}"
        )
    return template_path.read_text(encoding="utf-8")


__all__ = ["load_template"]
