"""
File: backend/src/agent_harness/verification/_abc.py
Purpose: Category 10 ABC — Verifier (output verification + self-correction).
Category: 範疇 10 (Verification Loops)
Scope: Phase 49 / Sprint 49.1 (stub; impl in Phase 54.1)

Description:
    Verifier checks LLM output before it leaves the loop.
    Implementations may be rules-based (regex / schema check),
    LLM-judge (subagent verifies), or external (call to API).

    On failure, the loop may trigger self-correction (max 2 attempts
    per spec) by feeding suggested_correction back to LLM.

Owner: 01-eleven-categories-spec.md §範疇 10
Single-source: 17.md §2.1

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-06-13

Modification History (newest-first):
    - 2026-06-13: Sprint 57.111 A3 — widen state to LoopState | None (trace-aware; was cast(None) at every call site)
    - 2026-04-29: Initial creation (Sprint 49.1)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_harness._contracts import LoopState, TraceContext, VerificationResult


class Verifier(ABC):
    """Verify LLM output before completing the loop."""

    @abstractmethod
    async def verify(
        self,
        *,
        output: str,
        state: LoopState | None = None,
        trace_context: TraceContext | None = None,
    ) -> VerificationResult:
        """Verify `output`. `state` (Sprint 57.111 A3) carries the loop trace
        (recent turns + tool errors via `state.transient.messages`) so a judge can
        critique trace-aware; `None` when no loop state is available (the Cat 9
        fallback judge paths) → string-only critique. Was non-optional + `cast(None)`
        at every call site pre-A3; the Optional makes the truth explicit."""
        ...
